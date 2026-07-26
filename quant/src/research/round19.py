"""Giro 19 — VWAP long/short multi-asset su crypto.

Perche' le crypto cambiano il problema:
  - OHLCV libero e completo, niente muro anti-bot
  - lo SHORT e' eseguibile senza prestito titoli: su un perpetuo si vende
    come si compra. Nell'azionario la gamba corta era il vincolo che
    uccideva meta' delle anomalie del giro 10.
  - mercato 24/7, nessun gap di apertura
  - e' il dominio su cui Kronos e' stato addestrato e mostrato

Cio' che NON cambia:
  - in Irlanda le cripto sono un asset ai fini CGT: 33% sul realizzato, e con
    la rotazione di queste strategie si va dritti verso il 52%
  - i costi sono PIU' ALTI dell'azionario. Uso 0,20% round-trip (taker 0,10%
    per lato su OKX/Kraken) invece dello 0,15% usato finora, e lo dichiaro.

Asset: BTC, ETH, SOL, XRP, DOGE, LTC, ADA (2017-2026, storia disuguale).
Segnali VWAP ancorati a settimana / mese / trimestre, in tre forme:
long-only, short-only, long-short.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
from research import lab
from research.round16 import anchored_vwap

ROUND = 19
DATA = Path(__file__).resolve().parents[2] / "data"
OUT = Path(__file__).resolve().parents[2] / "out"
COST_CRYPTO = 0.0020        # 0,20% round-trip: taker 0,10% per lato
SYMS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "LTCUSDT",
        "ADAUSDT"]


def load_crypto(sym):
    d = pd.read_csv(DATA / f"okx_{sym}_1d.csv", parse_dates=["datetime"])
    return d.set_index("datetime").sort_index()


def evaluate_ls(ret, pos, ppy=365, cost=COST_CRYPTO):
    """Come evaluate(), ma la posizione puo' essere negativa."""
    pos = pos.reindex(ret.index).fillna(0.0)
    turn = pos.diff().abs().fillna(pos.abs())
    net = pos * ret - turn * cost / 2.0
    yrs = len(ret) / ppy
    curve = (1 + net).cumprod()
    tot = float(curve.iloc[-1])
    return dict(cagr=(tot ** (1 / yrs) - 1) * 100 if tot > 0 else -100.0,
                sharpe=float(net.mean() / net.std() * np.sqrt(ppy))
                if net.std() > 0 else np.nan,
                dd=float((curve / curve.cummax() - 1).min()) * 100,
                ops=float((pos.diff().abs() > 0).sum()) / yrs,
                net=net)


def main():
    data = {}
    for s in SYMS:
        try:
            data[s] = load_crypto(s)
        except FileNotFoundError:
            pass
    print(f"Asset caricati: {len(data)}  ({', '.join(data)})")
    print(f"Costi: {COST_CRYPTO*100:.2f}% round-trip (crypto, piu' alti "
          f"dell'azionario)\n")

    rows = []
    for s, df in data.items():
        ret = df.close.pct_change().fillna(0.0)
        bh = evaluate_ls(ret, pd.Series(1.0, index=ret.index))
        rows.append(dict(sym=s, anchor="—", mode="buy&hold", **
                         {k: bh[k] for k in ("cagr", "sharpe", "dd", "ops")},
                         vs=0.0, n=len(ret)))
        for aname, freq in (("settimana", "W"), ("mese", "ME"),
                            ("trimestre", "QE")):
            vw = anchored_vwap(df, freq)
            above = (df.close > vw).astype(float).shift(1).fillna(0.0)
            variants = {
                "long-only": above,
                "short-only": -(1.0 - above),
                "long-short": above * 2.0 - 1.0,
            }
            for mode, pos in variants.items():
                m = evaluate_ls(ret, pos)
                rows.append(dict(sym=s, anchor=aname, mode=mode,
                                 **{k: m[k] for k in ("cagr", "sharpe", "dd",
                                                      "ops")},
                                 vs=m["cagr"] - bh["cagr"], n=len(ret)))

    d = pd.DataFrame(rows)
    act = d[d["mode"] != "buy&hold"]

    print(f"{'asset':<10}{'buy&hold':>10}  |  migliore variante VWAP")
    print("-" * 74)
    for s in data:
        b = d[(d["sym"] == s) & (d["mode"] == "buy&hold")].iloc[0]
        a = act[act["sym"] == s].sort_values("cagr", ascending=False).iloc[0]
        print(f"{s:<10}{b['cagr']:>9.1f}%  |  {a['anchor']:<11}{a['mode']:<12}"
              f"{a['cagr']:>9.1f}%  ({a['vs']:+.1f} vs B&H, Sharpe {a['sharpe']:.2f})")

    print(f"\n--- Aggregato per modo e ancoraggio (mediana sui {len(data)} asset) ---")
    print(f"{'ancoraggio':<14}{'modo':<14}{'CAGR med.':>11}{'vs B&H med.':>13}"
          f"{'Sharpe med.':>13}{'op/anno med.':>14}")
    agg = (act.groupby(["anchor", "mode"])
              .agg(cagr=("cagr", "median"), vs=("vs", "median"),
                   sharpe=("sharpe", "median"), ops=("ops", "median"),
                   wins=("vs", lambda x: int((x > 0).sum())))
              .reset_index())
    for _, r in agg.iterrows():
        print(f"{r['anchor']:<14}{r['mode']:<14}{r['cagr']:>10.1f}%"
              f"{r['vs']:>+12.1f}%{r['sharpe']:>13.2f}{r['ops']:>14.0f}")

    print(f"\n--- Quante varianti battono il buy&hold del proprio asset ---")
    for mode in ("long-only", "short-only", "long-short"):
        sub = act[act["mode"] == mode]
        print(f"  {mode:<14}{int((sub['vs'] > 0).sum()):>3}/{len(sub)}   "
              f"Sharpe mediano {sub['sharpe'].median():+.2f}")

    # portafoglio equipesato sui 7 asset, per ciascuna variante
    print(f"\n--- Portafoglio equipesato sui {len(data)} asset ---")
    print(f"{'ancoraggio':<14}{'modo':<14}{'CAGR':>10}{'Sharpe':>9}{'DD':>9}")
    common = None
    for s, df in data.items():
        idx = df.index
        common = idx if common is None else common.intersection(idx)
    port_rows = []
    for aname, freq in (("settimana", "W"), ("mese", "ME"), ("trimestre", "QE")):
        for mode in ("buy&hold", "long-only", "short-only", "long-short"):
            nets = []
            for s, df in data.items():
                ret = df.close.pct_change().fillna(0.0)
                if mode == "buy&hold":
                    pos = pd.Series(1.0, index=ret.index)
                else:
                    vw = anchored_vwap(df, freq)
                    above = (df.close > vw).astype(float).shift(1).fillna(0.0)
                    pos = {"long-only": above, "short-only": -(1.0 - above),
                           "long-short": above * 2.0 - 1.0}[mode]
                nets.append(evaluate_ls(ret, pos)["net"].reindex(common))
            pnet = pd.concat(nets, axis=1).mean(axis=1).dropna()
            yrs = len(pnet) / 365
            curve = (1 + pnet).cumprod()
            tot = float(curve.iloc[-1])
            cg = (tot ** (1 / yrs) - 1) * 100 if tot > 0 else -100.0
            sh = float(pnet.mean() / pnet.std() * np.sqrt(365))
            dd = float((curve / curve.cummax() - 1).min()) * 100
            port_rows.append(dict(anchor=aname, mode=mode, cagr=cg, sharpe=sh,
                                  dd=dd))
            if mode != "buy&hold" or aname == "settimana":
                print(f"{aname if mode!='buy&hold' else '—':<14}{mode:<14}"
                      f"{cg:>9.1f}%{sh:>9.2f}{dd:>8.1f}%")

    lab.log_trials([dict(round=ROUND, hypothesis="H20 VWAP long/short crypto",
                         config=f"{r['sym']}|{r['anchor']}|{r['mode']}",
                         window="2017-2026", sharpe=r["sharpe"], irr=r["cagr"],
                         bh_irr="", excess=r["vs"], n_obs=r["n"],
                         note="OKX, costi 0,20% RT")
                    for _, r in act.iterrows()])
    d.to_csv(OUT / "round19_crypto_vwap.csv", index=False)
    pd.DataFrame(port_rows).to_csv(OUT / "round19_crypto_port.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")
    return d


if __name__ == "__main__":
    main()

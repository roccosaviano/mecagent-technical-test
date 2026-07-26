"""Giro 16 — VWAP ancorato a finestre piu' lunghe della seduta.

Il giro 15 ha bocciato il VWAP intraday su tutte e otto le varianti, e il motivo
era aritmetico prima che statistico: 237-495 operazioni l'anno a 0,15%
round-trip fanno 36-74% di costi annui. Nessun segnale sopravvive a quello.

Ancorare il VWAP alla SETTIMANA invece che alla seduta cambia il problema:
  - il segnale si azzera il lunedi' invece che ogni mattina
  - la rotazione scende di un ordine di grandezza
  - si puo' testare su tutta la storia giornaliera 2006-2026 (5000 barre)
    invece che sui 9 mesi di dati a 15 minuti

Testo quattro ancoraggi (settimana, due settimane, mese, trimestre) x quattro
segnali, su QQQ e AAPL. Il VWAP e' calcolato sul prezzo tipico (H+L+C)/3
ponderato per volumi, cumulato dall'inizio della finestra di ancoraggio.
Tutti i segnali hanno shift(1).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
from research import lab
from research.round15 import load, evaluate

ROUND = 16
ANCHORS = {"settimana": "W", "due settimane": "2W", "mese": "ME",
           "trimestre": "QE"}


def anchored_vwap(df, freq):
    """VWAP cumulato dall'inizio di ogni periodo di ancoraggio."""
    tp = (df.high + df.low + df.close) / 3.0
    grp = df.index.to_period({"W": "W", "2W": "W", "ME": "M", "QE": "Q"}[freq])
    if freq == "2W":
        # raggruppa le settimane a coppie
        wk = pd.Series(df.index.to_period("W").astype(str), index=df.index)
        codes = pd.factorize(wk)[0] // 2
        grp = pd.Index(codes)
    pv = (tp * df.volume).groupby(grp).cumsum()
    vv = df.volume.groupby(grp).cumsum()
    return pd.Series((pv / vv.replace(0, np.nan)).to_numpy(), index=df.index)


def signals(df, vw):
    dev = (df.close - vw) / vw
    band = dev.rolling(100).std()
    return {
        "long sopra VWAP": (df.close > vw).astype(float),
        "long sotto VWAP": (df.close < vw).astype(float),
        "breakout +1 dev.std": (dev > band).astype(float),
        "rientro -1 dev.std": (dev < -band).astype(float),
    }


def main():
    rows = []
    for sym in ("QQQ", "AAPL"):
        df = load(sym, "1day")
        r = df.close.pct_change().fillna(0.0)
        bh = evaluate(r, pd.Series(1.0, index=r.index), 252)
        print(f"\n{'='*92}")
        print(f"{sym} giornaliero {df.index[0].date()} -> {df.index[-1].date()} "
              f"({len(df)} barre)")
        print(f"  buy&hold: CAGR {bh['cagr']:.2f}%  Sharpe {bh['sharpe']:.2f}  "
              f"DD {bh['dd']:.1f}%")
        print(f"\n{'ancoraggio':<16}{'segnale':<24}{'CAGR':>9}{'vs B&H':>9}"
              f"{'Sharpe':>8}{'DD':>9}{'op/an':>8}{'%mkt':>7}")
        print("-" * 90)
        for aname, freq in ANCHORS.items():
            vw = anchored_vwap(df, freq)
            for sname, raw in signals(df, vw).items():
                pos = raw.shift(1).fillna(0.0)
                m = evaluate(r, pos, 252)
                rows.append(dict(sym=sym, anchor=aname, sig=sname,
                                 cagr=m["cagr"], vs=m["cagr"] - bh["cagr"],
                                 sharpe=m["sharpe"], dd=m["dd"],
                                 ops=m["trades"], inmkt=m["inmkt"]))
                print(f"{aname:<16}{sname:<24}{m['cagr']:>8.2f}%"
                      f"{m['cagr']-bh['cagr']:>+8.2f}%{m['sharpe']:>8.2f}"
                      f"{m['dd']:>8.1f}%{m['trades']:>8.1f}{m['inmkt']:>6.0f}%")
        rows.append(dict(sym=sym, anchor="—", sig="buy&hold", cagr=bh["cagr"],
                         vs=0.0, sharpe=bh["sharpe"], dd=bh["dd"],
                         ops=0.0, inmkt=100.0))

    d = pd.DataFrame(rows)
    act = d[d["sig"] != "buy&hold"]
    print(f"\n{'='*92}")
    print(f"Varianti testate: {len(act)}   che battono il buy&hold: "
          f"{int((act['vs'] > 0).sum())}")
    best = act.sort_values("vs", ascending=False).head(5)
    print(f"\nLe cinque migliori:")
    print(f"{'sym':<6}{'ancoraggio':<16}{'segnale':<24}{'vs B&H':>9}"
          f"{'Sharpe':>8}{'op/an':>8}")
    for _, x in best.iterrows():
        print(f"{x['sym']:<6}{x['anchor']:<16}{x['sig']:<24}{x['vs']:>+8.2f}%"
              f"{x['sharpe']:>8.2f}{x['ops']:>8.1f}")

    print(f"\nConfronto con l'intraday del giro 15 (stesso segnale, stesso ETF):")
    intr = act[(act["sym"] == "QQQ") & (act["sig"] == "long sopra VWAP")]
    for _, x in intr.iterrows():
        print(f"  ancoraggio {x['anchor']:<14} {x['ops']:>6.1f} op/anno  "
              f"vs B&H {x['vs']:>+7.2f}%")
    print(f"  ancoraggio seduta (1h)      237.1 op/anno  vs B&H  -47.81%")
    print(f"  ancoraggio seduta (15min)   495.3 op/anno  vs B&H  -71.74%")

    lab.log_trials([dict(round=ROUND, hypothesis="H17 VWAP ancorato multi-periodo",
                         config=f"{x['sym']}|{x['anchor']}|{x['sig']}",
                         window="2006-2026", sharpe=x["sharpe"], irr=x["cagr"],
                         bh_irr="", excess=x["vs"], n_obs=5000,
                         note="OHLCV Twelve Data")
                    for _, x in act.iterrows()])
    d.to_csv(Path(__file__).resolve().parents[2] / "out" / "round16_vwap.csv",
             index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")
    return d


if __name__ == "__main__":
    main()

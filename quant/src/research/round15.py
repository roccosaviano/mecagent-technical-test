"""Giro 15 — Cio' che finora era 'non testabile': ATR vero e VWAP intraday.

Dati nuovi: OHLCV reali da Twelve Data.
  QQQ giornaliero  5000 barre, 2006-09 -> 2026-07  (ETF sul NASDAQ-100)
  AAPL giornaliero 5000 barre, stessa finestra
  QQQ 1 ora        5000 barre, 2023-09 -> 2026-07
  QQQ 15 minuti    5000 barre, 2025-10 -> 2026-07

Due cose che avevo dichiarato non testabili diventano testabili:

  1. ATR VERO. Il gruppo A usava uno stop a N deviazioni standard perche' senza
     High/Low l'ATR non e' calcolabile. Ora lo e'.
  2. VWAP INTRADAY. Richiede prezzi e volumi infragiornalieri. Ora ci sono.

Sul VWAP, l'onesta' impone di dire cosa si sta testando: il VWAP nasce come
BENCHMARK DI ESECUZIONE (misura se un ordine e' stato eseguito meglio o peggio
del prezzo medio ponderato per volumi), non come segnale predittivo. Qui lo
testo come segnale perche' e' quello che viene chiesto, con quattro varianti
standard usate dai day trader. La finestra e' corta: 9 mesi a 15 minuti, 3 anni
a un'ora. Non basta per una conclusione forte, e lo dichiaro nel risultato.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
from research import lab

DATA = Path(__file__).resolve().parents[2] / "data"
ROUND = 15


def load(sym, iv):
    d = pd.read_csv(DATA / f"td_{sym}_{iv}.csv")
    d["datetime"] = pd.to_datetime(d["datetime"])
    d = d.sort_values("datetime").set_index("datetime")
    for c in ("open", "high", "low", "close", "volume"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()


# ------------------------------------------------------------------ ATR vero
def atr(df, n=14):
    tr = pd.concat([df.high - df.low,
                    (df.high - df.close.shift()).abs(),
                    (df.low - df.close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def s_atr_stop(df, trend, mult):
    """La strategia 4 del gruppo A, finalmente con l'ATR vero.
    Decisione su t-1, esecuzione a t: lo shift(1) e' in fondo."""
    ma = df.close.rolling(trend).mean()
    a = atr(df, 14)
    pos, on, peak = [], False, 0.0
    c = df.close.to_numpy(); m = ma.to_numpy(); av = a.to_numpy()
    for i in range(len(df)):
        if not on:
            if not np.isnan(m[i]) and c[i] > m[i]:
                on, peak = True, c[i]
        else:
            peak = max(peak, c[i])
            if not np.isnan(av[i]) and c[i] < peak - mult * av[i]:
                on = False
        pos.append(1.0 if on else 0.0)
    return pd.Series(pos, index=df.index).shift(1).fillna(0.0)


# ------------------------------------------------------------------ VWAP
def session_vwap(df):
    """VWAP ancorato all'apertura di ogni seduta: e' la definizione usata dai
    day trader (si azzera ogni mattina), non una media mobile ponderata."""
    tp = (df.high + df.low + df.close) / 3.0
    day = df.index.normalize()
    pv = (tp * df.volume).groupby(day).cumsum()
    vv = df.volume.groupby(day).cumsum()
    return pv / vv.replace(0, np.nan)


def vwap_signals(df):
    """Quattro varianti standard, tutte con shift(1)."""
    vw = session_vwap(df)
    dev = (df.close - vw) / vw
    band = dev.rolling(50).std()
    return {
        "long sopra VWAP": (df.close > vw).astype(float).shift(1),
        "long sotto VWAP (mean rev.)": (df.close < vw).astype(float).shift(1),
        "breakout +1 dev.std": (dev > band).astype(float).shift(1),
        "rientro -1 dev.std": (dev < -band).astype(float).shift(1),
    }


def evaluate(ret, pos, ppy, cost_rt=C.COST_ROUND_TRIP):
    pos = pos.reindex(ret.index).fillna(0.0)
    turn = pos.diff().abs().fillna(pos.abs())
    net = pos * ret - turn * cost_rt / 2.0
    yrs = len(ret) / ppy
    curve = (1 + net).cumprod()
    tot = float(curve.iloc[-1])
    return dict(
        cagr=(tot ** (1 / yrs) - 1) * 100 if tot > 0 else -100.0,
        sharpe=float(net.mean() / net.std() * np.sqrt(ppy)) if net.std() > 0 else np.nan,
        dd=float((curve / curve.cummax() - 1).min()) * 100,
        trades=float((pos.diff() > 0).sum()) / yrs,
        inmkt=float((pos > 0).mean()) * 100,
        net=net)


def main():
    rows = []

    # ---------------------------------------------------- 1. ATR vero su QQQ
    qd = load("QQQ", "1day")
    ad = load("AAPL", "1day")
    print(f"QQQ giornaliero: {qd.index[0].date()} -> {qd.index[-1].date()} "
          f"({len(qd)} barre, OHLCV reale)")
    for name, df in (("QQQ", qd), ("AAPL", ad)):
        r = df.close.pct_change().fillna(0.0)
        bh = evaluate(r, pd.Series(1.0, index=r.index), 252)
        print(f"\n--- ATR vero su {name} (strategia 4 del gruppo A, finalmente "
              f"nella sua forma originale) ---")
        print(f"{'parametri':<26}{'CAGR':>9}{'vs B&H':>9}{'Sharpe':>8}{'DD':>9}"
              f"{'op/an':>7}{'%mkt':>7}")
        print(f"{'buy&hold':<26}{bh['cagr']:>8.2f}%{0.0:>+8.2f}%{bh['sharpe']:>8.2f}"
              f"{bh['dd']:>8.1f}%{0.0:>7.1f}{100.0:>6.0f}%")
        for trend in (50, 100, 200):
            for mult in (2, 3, 4):
                pos = s_atr_stop(df, trend, mult)
                m = evaluate(r, pos, 252)
                rows.append(dict(gruppo=f"ATR vero {name}",
                                 metodo=f"MA{trend} + stop {mult}xATR",
                                 **{k: m[k] for k in ("cagr", "sharpe", "dd",
                                                      "trades", "inmkt")},
                                 vs=m["cagr"] - bh["cagr"], ppy=252,
                                 n=len(r), finestra="2006-2026"))
                print(f"{'MA' + str(trend) + ' + stop ' + str(mult) + 'xATR':<26}"
                      f"{m['cagr']:>8.2f}%{m['cagr']-bh['cagr']:>+8.2f}%"
                      f"{m['sharpe']:>8.2f}{m['dd']:>8.1f}%{m['trades']:>7.1f}"
                      f"{m['inmkt']:>6.0f}%")
        rows.append(dict(gruppo=f"ATR vero {name}", metodo="buy&hold",
                         **{k: bh[k] for k in ("cagr", "sharpe", "dd", "trades",
                                               "inmkt")},
                         vs=0.0, ppy=252, n=len(r), finestra="2006-2026"))

    # ---------------------------------------------------- 2. VWAP intraday
    for iv, ppy, lbl in (("1h", 252 * 7, "1 ora"), ("15min", 252 * 26, "15 minuti")):
        df = load("QQQ", iv)
        r = df.close.pct_change().fillna(0.0)
        bh = evaluate(r, pd.Series(1.0, index=r.index), ppy)
        print(f"\n--- VWAP di seduta su QQQ a {lbl}: "
              f"{df.index[0].date()} -> {df.index[-1].date()} ({len(df)} barre) ---")
        print(f"{'segnale':<30}{'CAGR':>9}{'vs B&H':>9}{'Sharpe':>8}{'DD':>9}"
              f"{'op/an':>8}{'%mkt':>7}")
        print(f"{'buy&hold (sempre investito)':<30}{bh['cagr']:>8.2f}%{0.0:>+8.2f}%"
              f"{bh['sharpe']:>8.2f}{bh['dd']:>8.1f}%{0.0:>8.0f}{100.0:>6.0f}%")
        for sname, sig in vwap_signals(df).items():
            m = evaluate(r, sig, ppy)
            rows.append(dict(gruppo=f"VWAP QQQ {lbl}", metodo=sname,
                             **{k: m[k] for k in ("cagr", "sharpe", "dd",
                                                  "trades", "inmkt")},
                             vs=m["cagr"] - bh["cagr"], ppy=ppy, n=len(r),
                             finestra=f"{df.index[0].date()}/{df.index[-1].date()}"))
            print(f"{sname:<30}{m['cagr']:>8.2f}%{m['cagr']-bh['cagr']:>+8.2f}%"
                  f"{m['sharpe']:>8.2f}{m['dd']:>8.1f}%{m['trades']:>8.0f}"
                  f"{m['inmkt']:>6.0f}%")
        rows.append(dict(gruppo=f"VWAP QQQ {lbl}", metodo="buy&hold",
                         **{k: bh[k] for k in ("cagr", "sharpe", "dd", "trades",
                                               "inmkt")},
                         vs=0.0, ppy=ppy, n=len(r),
                         finestra=f"{df.index[0].date()}/{df.index[-1].date()}"))

        # quanto costa davvero operare cosi' spesso
        worst = max((x for x in rows if x["gruppo"] == f"VWAP QQQ {lbl}"),
                    key=lambda x: x["trades"])
        print(f"  Operazioni/anno del segnale piu' attivo: {worst['trades']:.0f}. "
              f"A 0,15% round-trip sono {worst['trades']*0.15:.0f}% di costi annui.")

    lab.log_trials([dict(round=ROUND, hypothesis="H16 ATR vero + VWAP intraday",
                         config=f"{x['gruppo']}|{x['metodo']}", window=x["finestra"],
                         sharpe=x["sharpe"], irr=x["cagr"], bh_irr="",
                         excess=x["vs"], n_obs=x["n"], note="OHLCV Twelve Data")
                    for x in rows])
    pd.DataFrame([{k: v for k, v in x.items() if k != "net"} for x in rows]).to_csv(
        Path(__file__).resolve().parents[2] / "out" / "round15_ohlcv.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")
    return rows


if __name__ == "__main__":
    main()

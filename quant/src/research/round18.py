"""Giro 18 — Kronos de-polarizzato, VWAP, e i due combinati.

Il giro 17 ha trovato una cosa che merita di essere sfruttata invece che
scartata. Kronos su QQQ:

  tasso di correttezza direzionale  46,80%   (sotto il 50%, z = -1,01)
  correlazione previsto/realizzato  +0,0855
  RankIC (Spearman)                 +0,0670
  quota di previsioni rialziste     24,8%  contro 58,8% di realizzati rialzisti

Le prime due righe sembrano contraddirsi e non lo fanno. Il modello ha una
POLARIZZAZIONE RIBASSISTA fortissima: prevede rialzo un quarto delle volte
mentre il mercato sale sei volte su dieci. Questo distrugge l'accuratezza
direzionale del segno grezzo. Ma l'ordinamento RELATIVO delle previsioni
conserva un po' d'informazione (RankIC +0,067), e quella si puo' usare.

Quindi: invece di "long se previsione > 0", uso "long se la previsione sta
nel quantile alto delle previsioni RECENTI". La soglia si muove con la
polarizzazione e la neutralizza. E' il modo corretto di usare un forecaster
distorto, ed e' anche il modo in cui il paper misura se stesso (RankIC, non
accuratezza del segno).

Poi combino con il VWAP, come richiesto.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
from research import lab
from research.round15 import load, evaluate
from research.round16 import anchored_vwap

ROUND = 18
OUT = Path(__file__).resolve().parents[2] / "out"
HORIZON = 5


def load_preds():
    for f in ("round17_kronos.csv", "round17_kronos_250.csv"):
        p = OUT / f
        if p.exists():
            d = pd.read_csv(p, parse_dates=["date"])
            print(f"previsioni da {f}: {len(d)} righe, "
                  f"{d['date'].iloc[0].date()} -> {d['date'].iloc[-1].date()}")
            return d
    raise FileNotFoundError("nessun file di previsioni Kronos")


def build_pos(px, preds, mask):
    """Posizione 0/1 dai record di previsione, tenuta per HORIZON sedute."""
    pos = pd.Series(0.0, index=px.index)
    for (_, row), on in zip(preds.iterrows(), mask):
        i = int(row["i"])
        pos.iloc[i:i + HORIZON] = 1.0 if on else 0.0
    return pos


def main():
    preds = load_preds()
    px = load("QQQ", "1day")
    ret = px.close.pct_change().fillna(0.0)
    span = slice(int(preds["i"].iloc[0]), int(preds["i"].iloc[-1]) + HORIZON)
    rr = ret.iloc[span]
    bh = evaluate(rr, pd.Series(1.0, index=rr.index), 252)

    print(f"\nFinestra: {rr.index[0].date()} -> {rr.index[-1].date()} "
          f"({len(rr)} sedute)")
    print(f"buy&hold QQQ: CAGR {bh['cagr']:.2f}%  Sharpe {bh['sharpe']:.2f}  "
          f"DD {bh['dd']:.1f}%")

    rows = []

    def rec(nome, pos, nota=""):
        p = pos.reindex(ret.index).fillna(0.0)
        m = evaluate(rr, p.iloc[span], 252)
        rows.append(dict(metodo=nome, cagr=m["cagr"], vs=m["cagr"] - bh["cagr"],
                         sharpe=m["sharpe"], dd=m["dd"], ops=m["trades"],
                         inmkt=m["inmkt"], nota=nota))
        return m

    # ---------------------------------------------------- 1. segno grezzo
    rec("Kronos, segno grezzo (previsione > 0)",
        build_pos(px, preds, preds["pred"] > 0),
        "polarizzato: 24,8% di previsioni rialziste")

    # ---------------------------------------------------- 2. de-polarizzato
    print(f"\n--- Kronos con soglia relativa mobile ---")
    print(f"{'quantile di ingresso':<28}{'CAGR':>9}{'vs B&H':>9}{'Sharpe':>8}"
          f"{'DD':>9}{'op/an':>8}{'%mkt':>7}")
    for q in (0.3, 0.4, 0.5, 0.6, 0.7):
        # soglia = quantile q delle ultime 60 previsioni, nota al momento della
        # decisione: uso shift(1) sulla serie delle previsioni, non il futuro
        thr = preds["pred"].shift(1).rolling(60, min_periods=20).quantile(q)
        mask = (preds["pred"] > thr).fillna(False).to_numpy()
        m = rec(f"Kronos, quantile mobile {q:.0%}",
                build_pos(px, preds, mask), "soglia relativa a 60 previsioni")
        print(f"{'quantile ' + f'{q:.0%}':<28}{m['cagr']:>8.2f}%"
              f"{m['cagr']-bh['cagr']:>+8.2f}%{m['sharpe']:>8.2f}"
              f"{m['dd']:>8.1f}%{m['trades']:>8.1f}{m['inmkt']:>6.0f}%")

    # ---------------------------------------------------- 3. VWAP da solo
    print(f"\n--- VWAP ancorato, stessa finestra di Kronos ---")
    print(f"{'ancoraggio':<28}{'CAGR':>9}{'vs B&H':>9}{'Sharpe':>8}{'DD':>9}"
          f"{'op/an':>8}{'%mkt':>7}")
    vwap_pos = {}
    for aname, freq in (("settimana", "W"), ("mese", "ME"), ("trimestre", "QE")):
        vw = anchored_vwap(px, freq)
        p = (px.close > vw).astype(float).shift(1).fillna(0.0)
        vwap_pos[aname] = p
        m = rec(f"VWAP {aname}, long sopra", p)
        print(f"{'VWAP ' + aname:<28}{m['cagr']:>8.2f}%"
              f"{m['cagr']-bh['cagr']:>+8.2f}%{m['sharpe']:>8.2f}"
              f"{m['dd']:>8.1f}%{m['trades']:>8.1f}{m['inmkt']:>6.0f}%")

    # ---------------------------------------------------- 4. combinati
    print(f"\n--- Kronos + VWAP combinati ---")
    print(f"{'combinazione':<40}{'CAGR':>9}{'vs B&H':>9}{'Sharpe':>8}"
          f"{'DD':>9}{'%mkt':>7}")
    thr = preds["pred"].shift(1).rolling(60, min_periods=20).quantile(0.5)
    kmask = (preds["pred"] > thr).fillna(False).to_numpy()
    kpos = build_pos(px, preds, kmask).reindex(ret.index).fillna(0.0)
    for aname, vp in vwap_pos.items():
        vp = vp.reindex(ret.index).fillna(0.0)
        for lbl, comb in (("AND (entrambi d'accordo)", kpos * vp),
                          ("OR (basta uno)", ((kpos + vp) > 0).astype(float)),
                          ("media (mezza posizione)", 0.5 * (kpos + vp))):
            m = rec(f"Kronos q50 {lbl} VWAP {aname}", comb)
            print(f"{('K + VWAP ' + aname + ' ' + lbl)[:39]:<40}"
                  f"{m['cagr']:>8.2f}%{m['cagr']-bh['cagr']:>+8.2f}%"
                  f"{m['sharpe']:>8.2f}{m['dd']:>8.1f}%{m['inmkt']:>6.0f}%")

    # ---------------------------------------------------- riepilogo
    d = pd.DataFrame(rows)
    d.loc[len(d)] = dict(metodo="buy&hold QQQ", cagr=bh["cagr"], vs=0.0,
                         sharpe=bh["sharpe"], dd=bh["dd"], ops=0.0,
                         inmkt=100.0, nota="benchmark")
    print(f"\n{'='*80}")
    print(f"Varianti provate: {len(d)-1}   che battono il buy&hold: "
          f"{int((d['vs'] > 0).sum())}")
    best = d[d["metodo"] != "buy&hold QQQ"].sort_values("vs", ascending=False)
    print(f"\nLe tre migliori:")
    for _, r in best.head(3).iterrows():
        print(f"  {r['metodo'][:52]:<54}{r['vs']:>+7.2f}%  Sharpe {r['sharpe']:.2f}")
    print(f"\nLa piu' alta per Sharpe:")
    b2 = best.sort_values("sharpe", ascending=False).iloc[0]
    print(f"  {b2['metodo'][:52]:<54}Sharpe {b2['sharpe']:.2f} "
          f"contro {bh['sharpe']:.2f} del buy&hold")

    lab.log_trials([dict(round=ROUND, hypothesis="H19 Kronos de-polarizzato + VWAP",
                         config=r["metodo"][:60], window="QQQ",
                         sharpe=r["sharpe"], irr=r["cagr"], bh_irr=bh["cagr"],
                         excess=r["vs"], n_obs=len(rr), note=r["nota"])
                    for _, r in d.iterrows()])
    d.to_csv(OUT / "round18_kronos_vwap.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")
    return d


if __name__ == "__main__":
    main()

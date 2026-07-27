"""Giro 40 — C1 (cointegrazione sui 49 settori) e C2 (breadth).

DUE VOCI DELLA CODA, predizioni verbatim.

C1 — Pairs trading / cointegrazione sui 49 settori
  Test di Engle-Granger su tutte le coppie, trading dello spread sulle coppie
  cointegrate nel periodo di stima.
  PREDIZIONE: molte coppie risultano cointegrate in-sample per puro caso (1.176
  coppie testate al 5% danno ~59 falsi positivi), e la cointegrazione non
  persiste fuori campione.
  FALSIFICATA SE: la quota di coppie che restano cointegrate fuori campione
  supera significativamente il 5%.

C2 — Breadth / partecipazione come segnale di mercato
  Quota di settori sopra la propria media a 200 giorni.
  PREDIZIONE: correlato al trend dell'indice stesso oltre 0,8, quindi non
  aggiunge informazione a un semplice filtro di trend.
  FALSIFICATA SE: correlazione col filtro di trend sotto 0,6 E migliora l'IRR.

SUL TEST DI C1. La condizione parla di "supera significativamente il 5%", quindi
serve un test, non un occhio: sotto ipotesi nulla il numero di coppie cointegrate
fuori campione e' binomiale(n, 0,05), e riporto il p-value esatto. E' l'unica
voce della coda la cui falsificazione e' statistica invece che economica.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import coint

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from research import lab, bench as B

ROUND = 40
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 57
ALPHA = 0.05


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ff = dataio.ff_factors_monthly()
    rf_all = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()

    # =============================================================== C1
    print(f"{'='*92}\nC1 — cointegrazione fra i 49 settori\n{'='*92}")
    logp = np.log((1 + ind).cumprod())
    half = len(logp) // 2
    A, Bh = logp.iloc[:half], logp.iloc[half:]
    cols = list(logp.columns)
    pairs = [(i, j) for i in range(len(cols)) for j in range(i + 1, len(cols))]
    print(f"   {len(pairs)} coppie · stima {A.index[0].date()}-{A.index[-1].date()}"
          f" · verifica {Bh.index[0].date()}-{Bh.index[-1].date()}")
    print(f"   Engle-Granger al {ALPHA:.0%}\n")

    coint_in = []
    for i, j in pairs:
        try:
            p = coint(A.iloc[:, i], A.iloc[:, j])[1]
        except Exception:
            continue
        if p < ALPHA:
            coint_in.append((i, j))
    print(f"   Cointegrate IN-SAMPLE: {len(coint_in)}/{len(pairs)} "
          f"({len(coint_in)/len(pairs):.1%})")
    print(f"   Attese per solo caso al {ALPHA:.0%}: "
          f"{int(ALPHA*len(pairs))} coppie")

    still = 0
    for i, j in coint_in:
        try:
            if coint(Bh.iloc[:, i], Bh.iloc[:, j])[1] < ALPHA:
                still += 1
        except Exception:
            pass
    n = len(coint_in)
    frac = still / n if n else 0.0
    # test binomiale esatto: sotto H0 la persistenza e' casuale al 5%
    pv = stats.binomtest(still, n, ALPHA, alternative="greater").pvalue if n else 1.0
    print(f"   Di queste, ancora cointegrate FUORI CAMPIONE: {still}/{n} "
          f"({frac:.1%})")
    print(f"   Test binomiale contro H0 = 5%: p = {pv:.4g}")
    c1_fals = pv < 0.05 and frac > ALPHA
    print(f"   -> ipotesi C1 {'FALSIFICATA' if c1_fals else 'CONFERMATA'}")

    # se la persistenza c'e', vale la pena vedere se si traduce in soldi
    if n:
        sel = coint_in[:60]
        rets = ind.loc[Bh.index]
        pnl = []
        for i, j in sel:
            sp = (logp.iloc[:, i] - logp.iloc[:, j])
            z = ((sp - sp.rolling(36).mean()) / sp.rolling(36).std()).shift(1)
            pos = (-z.clip(-2, 2) / 2.0).reindex(rets.index).fillna(0.0)
            pnl.append(pos * (rets.iloc[:, i] - rets.iloc[:, j]))
        strat = pd.concat(pnl, axis=1).mean(axis=1)
        turn = pd.concat([p.diff().abs() for p in
                          [(-((logp.iloc[:, i] - logp.iloc[:, j] -
                               (logp.iloc[:, i] - logp.iloc[:, j]).rolling(36).mean())
                              / (logp.iloc[:, i] - logp.iloc[:, j]).rolling(36).std()
                              ).clip(-2, 2) / 2).reindex(rets.index).fillna(0.0)
                           for i, j in sel]], axis=1).mean(axis=1)
        rfc = rf_all.reindex(strat.index).fillna(0.0)
        r = B.eval_stream(f"spread trading su {len(sel)} coppie",
                          strat.dropna() - turn.reindex(strat.index).fillna(0) * C.COST_ROUND_TRIP,
                          rfc, turn)
        bh = B.eval_stream("azionario (benchmark)", mkt.reindex(strat.index).dropna(),
                           rfc)
        print()
        B.table([r, bh])
        print(f"   (lo spread trading e' riportato per completezza: la condizione")
        print(f"    di falsificazione di C1 e' statistica, non economica)")
        rows1 = [r, bh]
    else:
        rows1 = []

    # =============================================================== C2
    print(f"\n{'='*92}\nC2 — breadth: quota di settori sopra la media a 200 "
          f"giorni\n{'='*92}")
    dind = dataio.ff_ind49_daily().dropna(axis=1, how="all")
    dind = dind.replace([-99.99, -999], np.nan).dropna(how="all")
    dpx = (1 + dind.fillna(0.0)).cumprod()
    above = (dpx > dpx.rolling(200).mean()).mean(axis=1)
    bre = above.resample("ME").last()
    bre.index = bre.index.to_period("M").to_timestamp("M")

    idx = mkt.index.intersection(bre.index)
    ret = mkt.reindex(idx)
    rf = rf_all.reindex(idx).fillna(0.0)
    bre = bre.reindex(idx)
    px = (1 + ret).cumprod()
    trend = B.ma_filter(px, 10)
    print(f"   Finestra {idx[0].date()} -> {idx[-1].date()} ({len(idx)} mesi)")

    rows2 = [B.eval_stream("azionario buy&hold", ret, rf)]
    bh2 = rows2[0]
    for thr in (0.4, 0.5, 0.6):
        e = (bre.shift(1) > thr).astype(float)
        rows2.append(B.eval_exposure(f"breadth > {thr:.0%}", ret, rf, e))
    rows2.append(B.eval_exposure("filtro di trend MA10", ret, rf, trend))
    print()
    B.table(rows2)

    corrs = {}
    for thr in (0.4, 0.5, 0.6):
        e = (bre.shift(1) > thr).astype(float)
        corrs[thr] = float(e.corr(trend))
    print(f"\n   Correlazione fra il segnale di breadth e il filtro di trend:")
    for k, v in corrs.items():
        print(f"     soglia {k:.0%}: {v:.3f}")
    cmax = max(corrs.values())
    best2 = max(rows2[1:-1], key=lambda r: r["irr"])
    improves = best2["irr"] > bh2["irr"]
    c2_fals = cmax < 0.6 and improves
    print(f"   Correlazione massima {cmax:.3f} "
          f"({'sopra' if cmax > 0.8 else 'sotto'} 0,8 come previsto)")
    print(f"   Il breadth migliora l'IRR? {'SI' if improves else 'NO'} "
          f"({best2['irr']:.2f}% contro {bh2['irr']:.2f}%)")
    print(f"   -> ipotesi C2 {'FALSIFICATA' if c2_fals else 'CONFERMATA'}")

    allr = rows1 + rows2
    if allr:
        best = max(allr, key=lambda r: r["irr"])
        d = lab.deflated_sharpe(best["gross"], N_PREREG, round_id=ROUND)
        print(f"\n   DSR del migliore ({best['label']}) su N={N_PREREG}: "
              f"{d['dsr']:.3f}")
    lab.log_trials([dict(round=ROUND,
                         hypothesis=("C1 cointegrazione" if r in rows1
                                     else "C2 breadth"),
                         config=r["label"], window="varie", sharpe=r["sharpe"],
                         irr=r["irr"], bh_irr=bh2["irr"],
                         excess=r["irr_ref"] - bh2["irr"], n_obs=r["n"],
                         note=f"turn={r['turn']:.2f}x") for r in allr])
    pd.DataFrame([{k: v for k, v in r.items() if k != "gross"}
                  for r in allr]).to_csv(OUT / "round40_c1c2.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

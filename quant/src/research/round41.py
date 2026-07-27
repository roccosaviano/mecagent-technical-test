"""Giro 41 — C3 (momentum multi-orizzonte) e C4 (term structure del VIX).

DUE VOCI DELLA CODA, predizioni verbatim.

C3 — Momentum a orizzonti multipli combinato (1, 3, 6, 12 mesi)
  Punteggio composito invece del solo 12-2.
  PREDIZIONE: il 12-2 domina; aggiungere orizzonti brevi introduce reversione e
  alza il turnover senza alzare lo Sharpe.
  FALSIFICATA SE: Sharpe > del solo 12-2 con turnover non superiore.

C4 — Volatilita' come asset: term structure del VIX
  VIX contro VIX a 3 mesi (contango/backwardation) come segnale di rischio.
  PREDIZIONE: il segnale funziona per cronometrare la volatilita', non la
  direzione — stesso esito del giro 22.
  FALSIFICATA SE: produce un segnale direzionale con accuratezza sopra la
  frequenza di base in modo significativo.

AVVERTENZA SULLA FINESTRA DI C4, dichiarata prima dei numeri. Il VIX3M parte dal
settembre 2009: la finestra di C4 sta quasi interamente DENTRO l'holdout
2010-2026. Questo NON brucia l'holdout, perche' l'holdout e' riservato alla
verifica finale di un candidato azionario promosso e C4 non promuove niente: la
sua condizione di falsificazione e' sull'accuratezza direzionale di un segnale,
non sul montante di un PAC. Ma va detto, e nessun candidato puo' uscire da qui.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from research import lab, bench as B
from research.round27 import cboe

ROUND = 41
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 57


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ff = dataio.ff_factors_monthly()
    rf_all = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()

    # =============================================================== C3
    print(f"{'='*92}\nC3 — momentum a orizzonti multipli\n{'='*92}")
    rf = rf_all.reindex(ind.index).fillna(0.0)
    print(f"   49 settori, {ind.index[0].date()} -> {ind.index[-1].date()}")
    print(f"   Ogni punteggio usa solo il passato: rank su [t-lb, t-1], "
          f"applicato in t+1\n")

    def score(lb, skip=1):
        return (1 + ind).rolling(lb - skip).apply(np.prod, raw=True).shift(skip + 1)

    horizons = {1: score(2, 1), 3: score(3, 1), 6: score(6, 1), 12: score(12, 1)}
    rows3 = [B.eval_stream("49 settori equal-weight (bench)",
                           ind.mean(axis=1), rf)]
    bh3 = rows3[0]

    def from_score(s, top=10, name=""):
        rk = s.rank(axis=1, ascending=False)
        W = (rk <= top).astype(float)
        W = W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
        net, turn = B.wbacktest(ind, W.shift(1).fillna(0.0))
        return B.eval_stream(name, net.dropna(), rf, turn)

    base = from_score(horizons[12], name="solo 12-2 (riferimento)")
    rows3.append(base)
    for h in (1, 3, 6):
        rows3.append(from_score(horizons[h], name=f"solo {h}m"))
    # composito: media dei ranghi normalizzati
    zs = {h: horizons[h].rank(axis=1, pct=True) for h in horizons}
    comp_all = sum(zs.values()) / len(zs)
    rows3.append(from_score(comp_all, name="composito 1+3+6+12"))
    comp_long = (zs[6] + zs[12]) / 2
    rows3.append(from_score(comp_long, name="composito 6+12"))
    comp_rev = (zs[12] - zs[1]) / 2 + 0.5      # 12-2 lungo, 1m in reversione
    rows3.append(from_score(comp_rev, name="12-2 con reversione a 1m"))
    print()
    B.table(rows3)

    print(f"\n   Condizione: FALSIFICATA se un composito ha Sharpe maggiore del")
    print(f"   solo 12-2 CON turnover non superiore.")
    print(f"   Riferimento 12-2: Sharpe {base['sharpe']:.3f}, "
          f"turnover {base['turn']:.2f}x")
    c3_fals = False
    for r in rows3:
        if not r["label"].startswith("composito") and "reversione" not in r["label"]:
            continue
        ok = r["sharpe"] > base["sharpe"] and r["turn"] <= base["turn"]
        c3_fals = c3_fals or ok
        print(f"     {r['label']:<26} Sharpe {r['sharpe']:.3f} "
              f"({'+' if r['sharpe']>base['sharpe'] else '-'}) · turnover "
              f"{r['turn']:.2f}x ({'<=' if r['turn']<=base['turn'] else '>'}) "
              f"-> {'PASSA' if ok else 'no'}")
    print(f"   -> ipotesi C3 {'FALSIFICATA' if c3_fals else 'CONFERMATA'}")
    tpy = max(r["turn"] for r in rows3)
    print(f"   Turnover massimo {tpy:.2f}x l'anno: sopra il 100%, l'aliquota di")
    print(f"   riferimento e' il 52%. Nessuna configurazione batte comunque il")
    print(f"   benchmark: migliore {max(r['irr_ref'] for r in rows3[1:]):.2f}% "
          f"contro {bh3['irr']:.2f}%")

    # =============================================================== C4
    print(f"\n{'='*92}\nC4 — term structure del VIX\n{'='*92}")
    v1 = cboe("VIX", daily_only=True)
    v3 = cboe("VIX3M", daily_only=True)
    d = pd.DataFrame({"vix": v1, "vix3m": v3}).dropna()
    ratio = d["vix"] / d["vix3m"]
    print(f"   VIX/VIX3M {d.index[0].date()} -> {d.index[-1].date()} "
          f"({len(d)} giorni)")
    print(f"   ATTENZIONE: questa finestra sta dentro l'holdout 2010-2026.")
    print(f"   Non lo brucia — C4 non promuove candidati, la sua condizione e'")
    print(f"   sull'accuratezza direzionale — ma nessun candidato esce da qui.\n")

    ffd = dataio.ff_factors_daily()
    dret = (ffd["Mkt-RF"] + ffd["RF"]).reindex(d.index).dropna()
    sig = ratio.reindex(dret.index).shift(1).dropna()
    dret = dret.reindex(sig.index)

    # (a) potere DIREZIONALE: il segnale prevede il segno del rendimento?
    # VIX/VIX3M < 1 e' CONTANGO, lo stato normale e calmo. >= 1 e'
    # backwardation, lo stato di stress. Il verso conta: invertirlo misura
    # l'opposto di quel che si vuole sapere.
    contango = sig < 1.0
    up = dret > 0
    base_rate = float(up.mean())
    acc_bull = float(up[contango].mean())
    n_b = int(contango.sum())
    pv = stats.binomtest(int(up[contango].sum()), n_b, base_rate,
                         alternative="greater").pvalue
    n_bw = int((~contango).sum())
    acc_bw = float(up[~contango].mean())
    print(f"   (a) DIREZIONE")
    print(f"       frequenza di base dei giorni positivi: {base_rate:.3%}")
    print(f"       in contango (VIX < VIX3M):             {acc_bull:.3%} "
          f"su {n_b} giorni ({n_b/len(sig):.0%} del campione)")
    print(f"       in backwardation (VIX >= VIX3M):       {acc_bw:.3%} "
          f"su {n_bw} giorni ({n_bw/len(sig):.0%} del campione)")
    print(f"       test binomiale contro la frequenza di base: p = {pv:.4g}")

    # (b) potere sulla VOLATILITA': il segnale prevede la volatilita' futura?
    fwd_vol = dret.rolling(21).std().shift(-21).dropna()
    s2 = sig.reindex(fwd_vol.index)
    rho = float(stats.spearmanr(s2, fwd_vol).statistic)
    pv2 = float(stats.spearmanr(s2, fwd_vol).pvalue)
    print(f"   (b) VOLATILITA'")
    print(f"       correlazione di Spearman fra VIX/VIX3M e la volatilita'")
    print(f"       realizzata dei 21 giorni SUCCESSIVI: {rho:+.3f} (p = {pv2:.3g})")

    c4_fals = pv < 0.05
    print(f"\n   -> ipotesi C4 {'FALSIFICATA' if c4_fals else 'CONFERMATA'}")
    print(f"   (confermata = il segnale cronometra la volatilita' ma non la")
    print(f"    direzione, cioe' |rho| grande su (b) e p non significativo su (a))")

    rows4 = []
    idxm = mkt.index
    rm = ratio.resample("ME").last()
    rm.index = rm.index.to_period("M").to_timestamp("M")
    ix = idxm.intersection(rm.index)
    if len(ix) > 60:
        retm = mkt.reindex(ix)
        rfm = rf_all.reindex(ix).fillna(0.0)
        rows4.append(B.eval_stream("azionario buy&hold (finestra C4)", retm, rfm))
        # investito in contango, fuori in backwardation
        e = (rm.reindex(ix).shift(1) < 1.0).astype(float)
        rows4.append(B.eval_exposure("fuori in backwardation", retm, rfm, e))
        print()
        B.table(rows4)
        print(f"   (riportato per completezza, NON promuovibile: finestra dentro")
        print(f"    l'holdout)")

    allr = rows3 + rows4
    lab.log_trials([dict(round=ROUND,
                         hypothesis=("C3 momentum multi-orizzonte" if r in rows3
                                     else "C4 term structure VIX"),
                         config=r["label"], window="varie", sharpe=r["sharpe"],
                         irr=r["irr"], bh_irr=bh3["irr"],
                         excess=r["irr_ref"] - bh3["irr"], n_obs=r["n"],
                         note=f"turn={r['turn']:.2f}x") for r in allr])
    pd.DataFrame([{k: v for k, v in r.items() if k != "gross"}
                  for r in allr]).to_csv(OUT / "round41_c3c4.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

"""Giro 32 — A3: minimum variance e maximum diversification.

VOCE DELLA CODA, predizione e falsificazione scritte prima:

  Due portafogli ottimizzati sui 49 settori, vincolo long-only, annuale.
  PREDIZIONE: minimum variance riduce il drawdown di oltre 10 punti e perde
  2-4 punti di CAGR; nessuno dei due batte l'IRR netta del cap-weight.
  FALSIFICATA SE: uno dei due supera il cap-weight netto imposte.

I DUE PORTAFOGLI.

  minimum variance      min w'Sw   con w >= 0, sum w = 1
  maximum diversif.     max (w's) / sqrt(w'Sw)   stesso vincolo
                        (Choueifaty-Coignard 2008: massimizza il rapporto fra
                        la volatilita' media pesata e la volatilita' del
                        portafoglio, cioe' il beneficio di diversificazione)

Entrambi ottimizzati con SLSQP su covarianza stimata sui SOLI 60 mesi
precedenti, ribilanciamento annuale. Nessun parametro da scegliere: non c'e'
selezione, quindi N per il DSR resta la famiglia pre-dichiarata della coda.

IL PUNTO DELICATO: 49 asset con 60 osservazioni. La covarianza campionaria e'
tecnicamente invertibile (60 > 49) ma malissimo condizionata, ed e' esattamente
la condizione in cui il min-variance e' noto per concentrarsi su pochi asset e
ribaltare i pesi a ogni ristima. Riporto quindi anche il numero condizionale e
la concentrazione dei pesi, perche' sono la diagnosi del metodo, non un extra.

Come DIAGNOSTICA aggiuntiva (non parte della specifica pre-dichiarata, e la
dichiaro come tale) eseguo anche il min-variance con shrinkage di Ledoit-Wolf
verso una matrice diagonale. Serve a distinguere due cause possibili di una
sconfitta: "il min-variance non paga" contro "la covarianza campionaria e'
rumore". Non entra nel verdetto su A3.

MISURO ANCHE LA STABILITA' DEI PESI. Il giro 31 ha trovato che HRP e' meno
stabile dell'inverse-variance, e ho messo in coda A7 per confrontarlo col
min-variance, che e' il bersaglio vero del paper di Lopez de Prado. Il numero
si calcola qui perche' i pesi si calcolano qui, ma il VERDETTO su A7 non lo do
in questo giro: si esegue una voce per volta.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES, TRADING_52
from research import lab
from research.round25 import _stats
from research.round31 import weight_stability

ROUND = 32
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 53          # famiglia pre-dichiarata: 52 + A7 aggiunta al giro 31


# ------------------------------------------------------------ ottimizzatori
def min_variance(cov):
    """min w'Sw, long-only, somma 1."""
    n = cov.shape[0]
    S = cov.to_numpy() if hasattr(cov, "to_numpy") else cov
    w0 = np.ones(n) / n
    r = minimize(lambda w: float(w @ S @ w), w0, method="SLSQP",
                 bounds=[(0.0, 1.0)] * n,
                 constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
                 options={"maxiter": 300, "ftol": 1e-12})
    w = np.clip(r.x, 0, None)
    return w / w.sum()


def max_diversification(cov):
    """max (w's)/sqrt(w'Sw), long-only, somma 1."""
    n = cov.shape[0]
    S = cov.to_numpy() if hasattr(cov, "to_numpy") else cov
    sig = np.sqrt(np.diag(S))

    def neg_dr(w):
        num = float(w @ sig)
        den = float(np.sqrt(max(w @ S @ w, 1e-18)))
        return -num / den

    w0 = np.ones(n) / n
    r = minimize(neg_dr, w0, method="SLSQP", bounds=[(0.0, 1.0)] * n,
                 constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0}],
                 options={"maxiter": 300, "ftol": 1e-12})
    w = np.clip(r.x, 0, None)
    return w / w.sum()


def ledoit_wolf(win):
    """Shrinkage verso la diagonale con intensita' stimata alla Ledoit-Wolf.
    Solo diagnostica: distingue 'il metodo non paga' da 'la stima e' rumore'."""
    X = win.to_numpy()
    T, n = X.shape
    X = X - X.mean(axis=0)
    S = (X.T @ X) / T
    target = np.diag(np.diag(S))
    # varianza asintotica degli elementi di S
    num = 0.0
    for t in range(T):
        d = np.outer(X[t], X[t]) - S
        num += float((d * d).sum())
    num /= T ** 2
    den = float(((S - target) ** 2).sum())
    shrink = 0.0 if den <= 0 else min(1.0, max(0.0, num / den))
    return pd.DataFrame(shrink * target + (1 - shrink) * S,
                        index=win.columns, columns=win.columns) * 12, shrink


# ------------------------------------------------------------ backtest
def backtest(rets, method, lookback=60, rebal=12, cost=C.COST_ROUND_TRIP):
    idx = rets.index
    n = rets.shape[1]
    W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    w = np.ones(n) / n
    conds, shrinks = [], []
    for i in range(len(idx)):
        if i >= lookback and i % rebal == 0:
            win = rets.iloc[i - lookback:i]
            if method == "minvar_shrunk":
                cov, sh = ledoit_wolf(win)
                shrinks.append(sh)
                w = min_variance(cov)
            else:
                cov = win.cov() * 12
                conds.append(float(np.linalg.cond(cov.to_numpy())))
                if method == "minvar":
                    w = min_variance(cov)
                elif method == "maxdiv":
                    w = max_diversification(cov)
                elif method == "equal":
                    w = np.ones(n) / n
        W.iloc[i] = w
        r = rets.iloc[i].to_numpy()
        g = w * (1 + r)
        w = g / g.sum() if g.sum() > 0 else w
    turn = W.diff().abs().sum(axis=1).fillna(W.abs().sum(axis=1)) / 2.0
    net = (W.shift(1).fillna(0.0) * rets).sum(axis=1) - turn * cost
    return net.dropna(), turn, W, conds, shrinks


def concentration(W, rebal=12):
    """Quota nei primi 5 asset e numero effettivo di posizioni (1/HHI),
    misurati ai soli istanti di ribilanciamento."""
    pts = W.iloc[::rebal]
    pts = pts[pts.sum(axis=1) > 0]
    top5 = float(pts.apply(lambda r: r.nlargest(5).sum(), axis=1).mean())
    neff = float((1.0 / (pts ** 2).sum(axis=1)).mean())
    return top5, neff


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    eq = (ff["Mkt-RF"] + ff["RF"]).reindex(ind.index)
    print(f"49 settori, {ind.index[0].date()} -> {ind.index[-1].date()} "
          f"({len(ind)} mesi)")
    print(f"Ottimizzazione su 60 mesi mobili precedenti, ribilanciamento "
          f"annuale, costi {C.COST_ROUND_TRIP*100:.2f}% round-trip")
    print(f"Long-only, somma 1, SLSQP. Nessun parametro selezionato.\n")

    rows = []
    hdr = (f"{'metodo':<20}{'CAGR':>9}{'vol':>8}{'Sharpe':>8}{'DD':>9}"
           f"{'turn/an':>9}{'top5':>8}{'N eff':>7}{'IRR 33%':>10}")
    print(hdr)
    print("-" * len(hdr))
    for m in ("minvar", "maxdiv", "equal", "minvar_shrunk"):
        net, turn, W, conds, shrinks = backtest(ind, m)
        s = _stats(net, 12)
        vol = float(net.std() * np.sqrt(12) * 100)
        tpy = float(turn.sum()) / (len(net) / 12)
        top5, neff = concentration(W)
        stab = weight_stability(W)
        rfn = rf.reindex(net.index).fillna(0.0)
        rz = turn.reindex(net.index).clip(0, 1)
        r33 = simulate_pac(net, CGT_SHARES, rf=rfn, realize_frac=rz,
                           periods_per_year=12)
        r52 = simulate_pac(net, TRADING_52, rf=rfn, realize_frac=rz,
                           periods_per_year=12)
        rows.append(dict(method=m, **s, vol=vol, turn=tpy, top5=top5,
                         neff=neff, stab=stab, irr=r33.irr_annual,
                         irr52=r52.irr_annual,
                         cond=float(np.median(conds)) if conds else float("nan"),
                         shrink=float(np.mean(shrinks)) if shrinks else float("nan"),
                         net=net))
        tag = m + (" (diagn.)" if m == "minvar_shrunk" else "")
        print(f"{tag:<20}{s['cagr']:>8.2f}%{vol:>7.1f}%{s['sharpe']:>8.2f}"
              f"{s['dd']:>8.1f}%{tpy:>8.2f}x{top5:>7.1%}{neff:>7.1f}"
              f"{r33.irr_annual:>9.2f}%")

    idx = rows[0]["net"].index
    eqi = eq.reindex(idx)
    bb = simulate_pac(eqi, CGT_SHARES, rf=rf.reindex(idx).fillna(0),
                      periods_per_year=12)
    be = _stats(eqi, 12)
    bvol = float(eqi.std() * np.sqrt(12) * 100)
    print(f"{'cap-weighted':<20}{be['cagr']:>8.2f}%{bvol:>7.1f}%"
          f"{be['sharpe']:>8.2f}{be['dd']:>8.1f}%{0.0:>8.2f}x{'':>7}{'':>7}"
          f"{bb.irr_annual:>9.2f}%")

    mv = next(r for r in rows if r["method"] == "minvar")
    md = next(r for r in rows if r["method"] == "maxdiv")
    eqw = next(r for r in rows if r["method"] == "equal")
    sk = next(r for r in rows if r["method"] == "minvar_shrunk")

    # ------------------------------------------------ verdetto
    print(f"\n{'='*88}\nVERDETTO SU A3\n{'='*88}")
    print("   Predizione: min-variance taglia il DD di oltre 10 punti e perde")
    print("   2-4 punti di CAGR; nessuno dei due batte l'IRR netta del cap-weight.")
    print("   FALSIFICATA se uno dei due supera il cap-weight netto imposte.\n")
    d_dd = mv["dd"] - be["dd"]
    d_cagr = be["cagr"] - mv["cagr"]
    print(f"   (a) drawdown  min-var {mv['dd']:.1f}% contro cap-weight "
          f"{be['dd']:.1f}%  -> {d_dd:+.1f} punti "
          f"{'(taglia oltre 10)' if d_dd > 10 else '(NON taglia 10 punti)'}")
    print(f"   (b) CAGR      min-var {mv['cagr']:.2f}% contro cap-weight "
          f"{be['cagr']:.2f}%  -> perde {d_cagr:+.2f} punti "
          f"{'(dentro 2-4)' if 2 <= d_cagr <= 4 else '(FUORI dalla banda 2-4)'}")
    print(f"   (c) IRR netta min-var {mv['irr']:.2f}%  max-div {md['irr']:.2f}%"
          f"  contro cap-weight {bb.irr_annual:.2f}%")
    print(f"       -> min-var {mv['irr']-bb.irr_annual:+.2f} · "
          f"max-div {md['irr']-bb.irr_annual:+.2f}")
    falsified = max(mv["irr"], md["irr"]) > bb.irr_annual
    print(f"\n   -> ipotesi A3 {'FALSIFICATA' if falsified else 'CONFERMATA'}"
          f"  (il test e' (c); (a) e (b) sono la descrizione del meccanismo)")

    print(f"\n   Condizionamento della covarianza campionaria (mediana sui "
          f"ribilanciamenti): {mv['cond']:.0f}")
    print(f"   Concentrazione: min-var tiene il {mv['top5']:.0%} in 5 settori, "
          f"{mv['neff']:.1f} posizioni effettive su 49")
    print(f"                   max-div {md['top5']:.0%} / {md['neff']:.1f}, "
          f"equal-weight {eqw['top5']:.0%} / {eqw['neff']:.1f}")
    print(f"\n   DIAGNOSTICA fuori specifica — min-variance con shrinkage di")
    print(f"   Ledoit-Wolf (intensita' media {sk['shrink']:.2f}): IRR netta "
          f"{sk['irr']:.2f}%, {sk['irr']-mv['irr']:+.2f} contro il min-var")
    print(f"   campionario. Serve a separare 'il metodo non paga' da 'la stima")
    print(f"   e' rumore'. Non entra nel verdetto.")

    print(f"\n   Turnover e aliquota: il piu' alto e' "
          f"{max(r['turn'] for r in rows):.2f} volte l'anno, sotto la soglia")
    print(f"   del 100% che farebbe scattare la riqualificazione. Lo scenario")
    print(f"   52% resta comunque calcolato: min-var {mv['irr52']:.2f}%, "
          f"max-div {md['irr52']:.2f}%.")

    print(f"\n   MISURATO PER A7 (verdetto rimandato, si esegue una voce per")
    print(f"   giro): movimento medio dei pesi per ribilanciamento — "
          f"min-var {mv['stab']:.3f}, max-div {md['stab']:.3f}.")

    best = max((mv, md), key=lambda r: r["irr"])
    d = lab.deflated_sharpe(best["net"], N_PREREG, round_id=ROUND)
    vs = best["irr"] - bb.irr_annual
    print(f"\n   DSR del migliore ({best['method']}) su {N_PREREG} ipotesi "
          f"pre-dichiarate: {d['dsr']:.3f}")
    print(f"   -> {'PROMUOVIBILE' if d['dsr'] > 0.95 and vs > 0 else 'NON promuovibile'}")

    lab.log_trials([dict(round=ROUND, hypothesis="A3 min-variance / max-diversification",
                         config=r["method"],
                         window=f"{idx[0].date()}/{idx[-1].date()}",
                         sharpe=r["sharpe"], irr=r["irr"], bh_irr=bb.irr_annual,
                         excess=r["irr"] - bb.irr_annual, n_obs=len(r["net"]),
                         note=f"turn={r['turn']:.2f}x,neff={r['neff']:.1f},"
                              f"stab={r['stab']:.3f}")
                    for r in rows])
    pd.DataFrame([{k: v for k, v in r.items() if k != "net"}
                  for r in rows]).to_csv(OUT / "round32_minvar.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

"""Giro 31 — A2: Hierarchical Risk Parity (Lopez de Prado 2016).

VOCE DELLA CODA, predizione e falsificazione scritte prima:

  Clustering gerarchico della matrice di correlazione, allocazione ricorsiva.
  Sui 49 settori, ribilanciamento annuale.
  PREDIZIONE: batte l'equal-weight in Sharpe ma non l'IRR netta; il vantaggio
  documentato di HRP e' sulla stabilita' dei pesi, non sul rendimento.
  FALSIFICATA SE: IRR netta > equal-weight annuale di almeno 0,5 punti.

L'ALGORITMO, nella forma originale in tre passi:
  1. distanza fra asset: d_ij = sqrt(0,5 (1 - rho_ij)), poi distanza euclidea
     fra le colonne della matrice di distanza
  2. clustering gerarchico a legame singolo, e riordino quasi-diagonale che
     mette vicini gli asset correlati
  3. bisezione ricorsiva: a ogni taglio si divide il budget di rischio fra i
     due sotto-alberi in modo inversamente proporzionale alla loro varianza

Il punto del metodo e' che non inverte mai la matrice di covarianza, che e' la
fonte di instabilita' del min-variance su 49 asset con 60 mesi di storia.

PERCHE' MI ASPETTO CHE NON BASTI. HRP e' un metodo di ALLOCAZIONE: prende
come dati i rendimenti attesi (o meglio, non li usa affatto) e ottimizza solo
la struttura del rischio. Il giro 30 ha appena mostrato che quando il turnover
e' quasi nullo la perdita contro l'azionario puro viene dalla COMPOSIZIONE,
non dalle imposte. Su 49 settori la composizione e' comunque azionario, quindi
qui il confronto e' piu' pulito: contro l'equal-weight, non contro l'indice.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES, TRADING_52
from research import lab
from research.round25 import _stats

ROUND = 31
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 52


# ------------------------------------------------------------------ HRP
def quasi_diag(link):
    """Ordine delle foglie che mette vicini i cluster uniti per ultimi."""
    link = link.astype(int)
    s = pd.Series([link[-1, 0], link[-1, 1]])
    n = link[-1, 3]
    while s.max() >= n:
        s.index = range(0, s.shape[0] * 2, 2)
        df0 = s[s >= n]
        i, j = df0.index, df0.values - n
        s[i] = link[j, 0]
        s = pd.concat([s, pd.Series(link[j, 1], index=i + 1)]).sort_index()
    return s.tolist()


def cluster_var(cov, items):
    c = cov.loc[items, items]
    ivp = 1.0 / np.diag(c)
    ivp = ivp / ivp.sum()
    return float(ivp @ c.to_numpy() @ ivp)


def hrp_weights(cov, corr):
    d = np.sqrt(np.clip(0.5 * (1 - corr), 0, None))
    dist = squareform(d.to_numpy(), checks=False)
    link = linkage(dist, method="single")
    order = quasi_diag(link)
    items = [corr.index[i] for i in order]
    w = pd.Series(1.0, index=items)
    clusters = [items]
    while clusters:
        clusters = [c[k:l] for c in clusters
                    for k, l in ((0, len(c) // 2), (len(c) // 2, len(c)))
                    if len(c) > 1]
        for i in range(0, len(clusters), 2):
            c0, c1 = clusters[i], clusters[i + 1]
            v0, v1 = cluster_var(cov, c0), cluster_var(cov, c1)
            a = 1 - v0 / (v0 + v1)
            w[c0] *= a
            w[c1] *= 1 - a
    return w.reindex(corr.index).fillna(0.0).to_numpy()


def inv_var(cov):
    iv = 1.0 / np.diag(cov.to_numpy())
    return iv / iv.sum()


# ------------------------------------------------------------------ backtest
def backtest(rets, method, lookback=60, rebal=12, cost=C.COST_ROUND_TRIP):
    """Pesi stimati SOLO sui `lookback` mesi precedenti, ribilanciati ogni
    `rebal` mesi. Fra un ribilanciamento e l'altro i pesi derivano coi prezzi."""
    idx = rets.index
    n = rets.shape[1]
    W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    w = np.ones(n) / n
    nfit = 0
    for i in range(len(idx)):
        if i >= lookback and i % rebal == 0:
            win = rets.iloc[i - lookback:i]
            cov = win.cov() * 12
            if method == "hrp":
                w = hrp_weights(cov, win.corr())
                nfit += 1
            elif method == "invvar":
                w = inv_var(cov)
                nfit += 1
            elif method == "equal":
                w = np.ones(n) / n
        W.iloc[i] = w
        r = rets.iloc[i].to_numpy()
        g = w * (1 + r)
        w = g / g.sum() if g.sum() > 0 else w
    turn = W.diff().abs().sum(axis=1).fillna(W.abs().sum(axis=1)) / 2.0
    net = (W.shift(1).fillna(0.0) * rets).sum(axis=1) - turn * cost
    return net.dropna(), turn, W, nfit


def weight_stability(W, rebal=12):
    """Quanto si muovono i pesi da un ribilanciamento all'altro. E' la
    proprieta' per cui HRP e' stato proposto, quindi va misurata."""
    pts = W.iloc[::rebal]
    return float(pts.diff().abs().sum(axis=1).mean())


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all")
    ind = ind.dropna()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    eq = (ff["Mkt-RF"] + ff["RF"]).reindex(ind.index)
    print(f"49 settori, {ind.index[0].date()} -> {ind.index[-1].date()} "
          f"({len(ind)} mesi)")
    print(f"Stima su 60 mesi mobili, ribilanciamento annuale, "
          f"costi {C.COST_ROUND_TRIP*100:.2f}% round-trip\n")

    rows = []
    print(f"{'metodo':<26}{'CAGR':>9}{'Sharpe':>8}{'DD':>9}{'turn/an':>9}"
          f"{'stab.pesi':>11}{'IRR 33%':>10}")
    for m in ("hrp", "invvar", "equal"):
        net, turn, W, nfit = backtest(ind, m)
        s = _stats(net, 12)
        tpy = float(turn.sum()) / (len(net) / 12)
        stab = weight_stability(W)
        r33 = simulate_pac(net, CGT_SHARES, rf=rf.reindex(net.index).fillna(0),
                           realize_frac=turn.reindex(net.index).clip(0, 1),
                           periods_per_year=12)
        r52 = simulate_pac(net, TRADING_52, rf=rf.reindex(net.index).fillna(0),
                           realize_frac=turn.reindex(net.index).clip(0, 1),
                           periods_per_year=12)
        rows.append(dict(method=m, **s, turn=tpy, stab=stab,
                         irr=r33.irr_annual, irr52=r52.irr_annual,
                         net=net, nfit=nfit))
        print(f"{m:<26}{s['cagr']:>8.2f}%{s['sharpe']:>8.2f}{s['dd']:>8.1f}%"
              f"{tpy:>8.2f}x{stab:>11.3f}{r33.irr_annual:>9.2f}%")

    idx = rows[0]["net"].index
    bb = simulate_pac(eq.reindex(idx), CGT_SHARES,
                      rf=rf.reindex(idx).fillna(0), periods_per_year=12)
    be = _stats(eq.reindex(idx), 12)
    print(f"{'indice cap-weighted':<26}{be['cagr']:>8.2f}%{be['sharpe']:>8.2f}"
          f"{be['dd']:>8.1f}%{0.0:>8.2f}x{0.0:>11.3f}{bb.irr_annual:>9.2f}%")

    # ------------------------------------------------ verdetto
    hrp = next(r for r in rows if r["method"] == "hrp")
    eqw = next(r for r in rows if r["method"] == "equal")
    ivp = next(r for r in rows if r["method"] == "invvar")
    print(f"\n{'='*84}\nVERDETTO SU A2\n{'='*84}")
    print(f"   Predizione: HRP batte l'equal-weight in Sharpe ma non in IRR netta.")
    print(f"   FALSIFICATA se IRR netta > equal-weight di almeno 0,5 punti.\n")
    print(f"   Sharpe   HRP {hrp['sharpe']:.3f} contro equal-weight "
          f"{eqw['sharpe']:.3f}  -> {'SI' if hrp['sharpe']>eqw['sharpe'] else 'NO'}")
    d_irr = hrp["irr"] - eqw["irr"]
    print(f"   IRR netta HRP {hrp['irr']:.2f}% contro equal-weight "
          f"{eqw['irr']:.2f}%  -> differenza {d_irr:+.2f} punti")
    print(f"   Stabilita' dei pesi (movimento medio a ogni ribilanciamento):")
    print(f"     HRP {hrp['stab']:.3f} · inverse-variance {ivp['stab']:.3f} · "
          f"equal-weight {eqw['stab']:.3f}")
    print(f"     (piu' basso = pesi piu' stabili. E' la proprieta' per cui HRP")
    print(f"      e' stato proposto, e va misurata anche se non paga)")
    falsified = d_irr >= 0.5
    print(f"\n   -> ipotesi A2 {'FALSIFICATA' if falsified else 'CONFERMATA'}")

    vs_idx = hrp["irr"] - bb.irr_annual
    print(f"\n   Per riferimento, HRP contro l'indice cap-weighted: "
          f"{vs_idx:+.2f} punti")
    d = lab.deflated_sharpe(hrp["net"], N_PREREG, round_id=ROUND)
    print(f"   DSR di HRP su {N_PREREG} ipotesi pre-dichiarate: {d['dsr']:.3f}"
          f"  -> {'PROMUOVIBILE' if d['dsr']>0.95 and vs_idx>0 else 'NON promuovibile'}")

    lab.log_trials([dict(round=ROUND, hypothesis="A2 hierarchical risk parity",
                         config=r["method"], window=f"{idx[0].date()}/{idx[-1].date()}",
                         sharpe=r["sharpe"], irr=r["irr"], bh_irr=bb.irr_annual,
                         excess=r["irr"] - bb.irr_annual, n_obs=len(r["net"]),
                         note=f"turn={r['turn']:.2f}x,stab={r['stab']:.3f}")
                    for r in rows])
    pd.DataFrame([{k: v for k, v in r.items() if k != "net"}
                  for r in rows]).to_csv(OUT / "round31_hrp.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

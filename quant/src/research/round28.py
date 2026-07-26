"""Giro 28 — Ricostruzione di un modello "physics-based regime detection with
convex position optimization".

COSA RICOSTRUISCO. Dalla slide: due variabili di stato discretizzate in tre
livelli ciascuna (l'etichetta "E1_3 E2_3" suggerisce 3x3 = 9 regimi),
rilevamento di regime, e ottimizzazione convessa della posizione fra un
asset offensivo e uno difensivo ("Position: 30% DEF"). Risultato dichiarato:
+1717% contro +208,6% dell'S&P dal novembre 2006, drawdown 24% contro 55,9%.
Sono 16,5% annuo contro 6,2%.

Costruisco esattamente questo:

  E1 = stato di trend, l'analogo di una posizione in un potenziale: dove sta
       il prezzo rispetto alla sua media, in unita' di deviazione standard
  E2 = stato di turbolenza: volatilita' realizzata rispetto alla propria
       storia. E' l'analogo dell'energia cinetica.
  Entrambe in 3 livelli per terzili -> 9 regimi.

  Per ogni regime si stimano media e varianza condizionate dei due asset, e
  si risolve il problema convesso di Markowitz con vincoli di scatola
  (0 <= peso <= 1, somma = 1). E' l'"ottimizzazione convessa della posizione".

POI LO METTO ALLA PROVA IN DUE MODI, ED E' IL PUNTO DI QUESTO GIRO:

  (A) COME SI PRESENTA: parametri stimati su tutto il campione, nessun costo,
      nessuna imposta, curva unica dal 2006. E' cosi' che si producono i
      grafici che si vedono in giro.
  (B) COME VA VERIFICATO: parametri stimati solo sul passato (walk-forward
      annuale), costi di transazione, fiscalita' irlandese, e il conteggio
      dei tentativi nel registro.

La differenza fra (A) e (B) e' la misura di quanto vale la disciplina.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES, TRADING_52, first_of_month
from research import lab, multidata as M
from research.round25 import _stats

ROUND = 28
OUT = Path(__file__).resolve().parents[2] / "out"
START = "2006-11"


# ------------------------------------------------------------------ stati
def state_vars(px, ret):
    """E1 = trend normalizzato, E2 = turbolenza. Entrambi guardano indietro."""
    ma = px.rolling(200).mean()
    sd = ret.rolling(200).std() * np.sqrt(200)
    e1 = ((px - ma) / (ma * sd)).replace([np.inf, -np.inf], np.nan)
    e2 = ret.rolling(21).std() / ret.rolling(252).std()
    return e1.shift(1), e2.shift(1)          # noti solo il giorno dopo


def terziles(s, upto=None):
    """Terzili stimati su `upto` (solo passato) e applicati a tutta la serie."""
    ref = s.loc[:upto].dropna() if upto is not None else s.dropna()
    if len(ref) < 100:
        return pd.Series(np.nan, index=s.index)
    q = np.nanquantile(ref, [1 / 3, 2 / 3])
    return pd.Series(np.digitize(s.to_numpy(), q), index=s.index).where(s.notna())


def convex_weights(mu, cov, lam=3.0, wmax=1.0):
    """Markowitz con vincoli di scatola: max w'mu - lam/2 w'Sigma w,
    0 <= w <= wmax, somma <= 1. Due asset: si risolve per enumerazione fine,
    che su un simplesso bidimensionale e' esatto quanto un solver."""
    grid = np.linspace(0, wmax, 51)
    best, bw = -1e18, np.zeros(len(mu))
    for a in grid:
        b = 1.0 - a
        if b < 0 or b > wmax:
            continue
        w = np.array([a, b])
        v = float(w @ mu - lam / 2 * w @ cov @ w)
        if v > best:
            best, bw = v, w
    return bw


def build_weights(rets, e1t, e2t, train_idx, lam=3.0):
    """Pesi per data, dai momenti condizionati al regime stimati su train_idx."""
    tr = rets.loc[train_idx]
    k1, k2 = e1t.loc[train_idx], e2t.loc[train_idx]
    tab = {}
    for a in (0, 1, 2):
        for b in (0, 1, 2):
            m = (k1 == a) & (k2 == b)
            if m.sum() < 60:
                continue
            sub = tr[m.reindex(tr.index).fillna(False)]
            if len(sub) < 60:
                continue
            tab[(a, b)] = convex_weights(sub.mean().to_numpy() * 252,
                                         sub.cov().to_numpy() * 252, lam)
    dflt = convex_weights(tr.mean().to_numpy() * 252,
                          tr.cov().to_numpy() * 252, lam)
    W = np.tile(dflt, (len(rets), 1))
    for i, (a, b) in enumerate(zip(e1t.to_numpy(), e2t.to_numpy())):
        if np.isfinite(a) and np.isfinite(b):
            W[i] = tab.get((int(a), int(b)), dflt)
    return pd.DataFrame(W, index=rets.index, columns=rets.columns), len(tab)


def run(rets, W, cost=C.COST_ROUND_TRIP):
    turn = W.diff().abs().sum(axis=1).fillna(W.abs().sum(axis=1)) / 2.0
    return (W * rets).sum(axis=1) - turn * cost, turn


def main():
    ffd = dataio.ff_factors_daily()
    eq = (ffd["Mkt-RF"] + ffd["RF"]).dropna()
    px = 100 * (1 + eq).cumprod()
    bond_m = M.bond_total_return_monthly()
    # decennale a frequenza giornaliera: rendimento mensile ripartito
    bond = bond_m.reindex(eq.index, method="ffill") / 21.0
    rets = pd.DataFrame({"equity": eq, "bond": bond}).dropna().loc[START:]
    px = px.reindex(rets.index)
    print(f"Universo: azionario USA + decennale (il 'difensivo')")
    print(f"Finestra: {rets.index[0].date()} -> {rets.index[-1].date()} "
          f"({len(rets)} sedute)\n")

    e1, e2 = state_vars(px, rets["equity"])

    # ============================================ A. come si presenta
    print("=" * 84)
    print("A. COME SI PRESENTA — parametri su tutto il campione, zero costi,")
    print("   zero imposte, una curva sola")
    print("=" * 84)
    e1a, e2a = terziles(e1), terziles(e2)
    Wa, nreg = build_weights(rets, e1a, e2a, rets.index)
    net_a, _ = run(rets, Wa, cost=0.0)
    sa, sb = _stats(net_a.dropna(), 252), _stats(rets["equity"], 252)
    mult_a = float((1 + net_a.dropna()).prod())
    mult_b = float((1 + rets["equity"]).prod())
    print(f"   regimi popolati: {nreg}/9")
    print(f"   {'':<24}{'moltiplicatore':>16}{'CAGR':>9}{'DD':>9}{'Sharpe':>8}")
    print(f"   {'Strategia':<24}{mult_a:>15.1f}x{sa['cagr']:>8.2f}%"
          f"{sa['dd']:>8.1f}%{sa['sharpe']:>8.2f}")
    print(f"   {'S&P 500 buy&hold':<24}{mult_b:>15.1f}x{sb['cagr']:>8.2f}%"
          f"{sb['dd']:>8.1f}%{sb['sharpe']:>8.2f}")
    print(f"\n   Su 100 investiti: strategia {mult_a*100:,.0f}, "
          f"indice {mult_b*100:,.0f}")
    print(f"   (la slide dichiara 1.817 contro 308)")

    # ============================================ B. come va verificato
    print(f"\n{'='*84}")
    print("B. COME VA VERIFICATO — walk-forward, costi, imposte")
    print("=" * 84)
    years = sorted({t.year for t in rets.index})
    segs, turns, nev = [], [], 0
    for y in years:
        tr = rets.index[rets.index.year < y]
        if len(tr) < 500:
            continue
        upto = tr[-1]
        e1t, e2t = terziles(e1, upto), terziles(e2, upto)
        Wy, k = build_weights(rets, e1t, e2t, tr)
        nev += max(k, 1)
        n, t = run(rets, Wy)
        m = n.index.year == y
        segs.append(n[m]); turns.append(t[m])
    net_b = pd.concat(segs).sort_index()
    turn_b = pd.concat(turns).sort_index()
    idx = net_b.index
    bench = rets["equity"].reindex(idx)
    s2, b2 = _stats(net_b, 252), _stats(bench, 252)
    print(f"   fuori campione {idx[0].date()} -> {idx[-1].date()} "
          f"({len(idx)} sedute, {nev} regimi stimati)")
    print(f"   {'':<24}{'moltiplicatore':>16}{'CAGR':>9}{'DD':>9}{'Sharpe':>8}")
    print(f"   {'Strategia':<24}{float((1+net_b).prod()):>15.1f}x{s2['cagr']:>8.2f}%"
          f"{s2['dd']:>8.1f}%{s2['sharpe']:>8.2f}")
    print(f"   {'S&P 500 buy&hold':<24}{float((1+bench).prod()):>15.1f}x"
          f"{b2['cagr']:>8.2f}%{b2['dd']:>8.1f}%{b2['sharpe']:>8.2f}")

    rf = ffd["RF"].reindex(idx).fillna(0.0)
    con = first_of_month(idx)
    a33 = simulate_pac(net_b, CGT_SHARES, rf=rf, realize_frac=turn_b.clip(0, 1),
                       periods_per_year=252, contrib_on=con)
    a52 = simulate_pac(net_b, TRADING_52, rf=rf, realize_frac=turn_b.clip(0, 1),
                       periods_per_year=252, contrib_on=con)
    bb = simulate_pac(bench, CGT_SHARES, rf=rf, periods_per_year=252,
                      contrib_on=con)
    tpy = float(turn_b.sum()) / (len(idx) / 252)
    print(f"\n   turnover {tpy:.1f} volte l'anno")
    print(f"   {'PAC netto imposte':<24}{'IRR 33%':>12}{'IRR 52%':>10}{'vs B&H':>10}")
    print(f"   {'Strategia':<24}{a33.irr_annual:>11.2f}%{a52.irr_annual:>9.2f}%"
          f"{a33.irr_annual-bb.irr_annual:>+9.2f}%")
    print(f"   {'S&P 500 buy&hold':<24}{bb.irr_annual:>11.2f}%{'—':>10}"
          f"{0.0:>+9.2f}%")

    # ============================================ da dove viene il divario
    print(f"\n{'='*84}")
    print("C. DA DOVE VIENE IL DIVARIO FRA (A) E (B)")
    print("=" * 84)
    steps = []
    n0 = run(rets, Wa, cost=0.0)[0].dropna()
    steps.append(("come si presenta (in-sample, 0 costi, 0 imposte)",
                  _stats(n0, 252)["cagr"]))
    n1 = run(rets, Wa)[0].dropna()
    steps.append(("+ costi di transazione", _stats(n1, 252)["cagr"]))
    steps.append(("+ parametri stimati solo sul passato", s2["cagr"]))
    steps.append(("+ fiscalita' irlandese (IRR del PAC)", a33.irr_annual))
    prev = None
    for lbl, v in steps:
        delta = "" if prev is None else f"  ({v-prev:+.2f})"
        print(f"   {lbl:<52}{v:>8.2f}%{delta}")
        prev = v
    print(f"   {'buy&hold, stessa misura':<52}{bb.irr_annual:>8.2f}%")

    n_cum = lab.n_trials_so_far()
    d = lab.deflated_sharpe(net_b, n_cum + nev, rf=rf, round_id=ROUND)
    beats = a33.irr_annual > bb.irr_annual
    print(f"\n   DSR su {n_cum+nev} tentativi: {d['dsr']:.3f}  "
          f"(batte il B&H netto imposte: {'si' if beats else 'NO'})")
    print(f"   -> {'PROMUOVIBILE' if (d['dsr']>0.95 and beats) else 'NON promuovibile'}")

    lab.log_trials([dict(round=ROUND, hypothesis="H30 regime detection + convex sizing",
                         config="9 regimi, Markowitz vincolato", window=f"{idx[0].date()}/{idx[-1].date()}",
                         sharpe=s2["sharpe"], irr=a33.irr_annual,
                         bh_irr=bb.irr_annual, excess=a33.irr_annual - bb.irr_annual,
                         n_obs=len(idx), note=f"turn={tpy:.1f}x, regimi={nev}")])
    pd.DataFrame(dict(step=[s[0] for s in steps],
                      cagr=[s[1] for s in steps])).to_csv(
        OUT / "round28_waterfall.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

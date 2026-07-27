"""Giro 45 — A11: quanto dovrebbe rendere di piu' la sleeve obbligazionaria.

VOCE DELLA CODA, predizione e falsificazione scritte prima:

  Il giro 44 attribuisce l'84-92% della perdita delle allocazioni multi-classe
  alla COMPOSIZIONE, e la controprova mostra che anche con imposte zero restano
  1,8-3,3 punti sotto l'azionario. Ma il decennale usato e' una ricostruzione a
  duration costante da DGS10, che sottostima convessita' e rolldown: parte del
  divario potrebbe essere un difetto del proxy, non un fatto.
  PREDIZIONE: il pareggio richiede oltre 3 punti l'anno in piu' sulla sleeve
  obbligazionaria per ERC e inverse-vol, cioe' da 4 a 10 volte lo scarto
  plausibile del proxy. Il difetto di ricostruzione quindi NON spiega il divario.
  FALSIFICATA SE: il rendimento aggiuntivo richiesto sta sotto 1 punto l'anno per
  almeno una delle quattro allocazioni.

DUE MISURE INDIPENDENTI, e il confronto fra loro e' il test.

  (1) IL PAREGGIO. Per ogni allocazione, cerco per bisezione il rendimento
      annuo costante alpha da aggiungere alla sleeve obbligazionaria perche'
      l'IRR netta dell'allocazione eguagli quella dell'azionario 100%. Rieseguo
      tutta la pipeline con la serie maggiorata — pesi ristimati compresi —
      perche' cambiare il rendimento del decennale cambia anche la deriva dei
      pesi fra un ribilanciamento e l'altro.

  (2) LO SCARTO DEL PROXY. Invece di citare un intervallo di letteratura, lo
      MISURO: costruisco una seconda ricostruzione che aggiunge i due termini
      che la prima omette, e prendo la differenza di rendimento annuo fra le due.

        semplice   r = y/12 - D*dy                        (quella del giro 30)
        migliorata r = y/12 - D*dy + 0.5*C*dy^2 + roll    (questa)

      con C = convessita' di un decennale (circa 85 a rendimenti tipici) e
      `roll` = guadagno da rotolamento lungo la curva, approssimato dalla
      pendenza 10-2 anni scalata sulla parte di curva percorsa in un mese.
      La differenza fra le due e' la mia stima empirica di quanto la
      ricostruzione semplice sottostima un indice vero.

Se (1) e' molto piu' grande di (2), il difetto del proxy non spiega il divario e
la conclusione del giro 44 regge. Se (1) e' dell'ordine di (2), il giro 44 va
riletto.
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
from tax import simulate_pac, CGT_SHARES
from research import lab, bench as B, multidata as M
from research.round44 import weights_path

ROUND = 45
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 59
DUR = 8.5
CONV = 85.0        # convessita' di un decennale a rendimenti tipici


def bond_simple():
    y = M.fred("DGS10").resample("ME").last() / 100.0
    y.index = y.index.to_period("M").to_timestamp("M")
    return (y.shift(1) / 12.0 - DUR * y.diff()).dropna(), y


def bond_improved():
    """Aggiunge i due termini che la ricostruzione semplice omette."""
    y = M.fred("DGS10").resample("ME").last() / 100.0
    y2 = M.fred("DGS2").resample("ME").last() / 100.0
    for s in (y, y2):
        s.index = s.index.to_period("M").to_timestamp("M")
    dy = y.diff()
    # convessita': sempre positiva, e' il termine di secondo ordine
    convex = 0.5 * CONV * dy ** 2
    # rolldown: scendendo di un mese lungo la curva il titolo si rivaluta della
    # pendenza per mese, moltiplicata per la duration. Pendenza 10-2 spalmata
    # sugli 8 anni che separano i due punti.
    slope_per_month = (y - y2) / 8.0 / 12.0
    roll = DUR * slope_per_month
    return (y.shift(1) / 12.0 - DUR * dy + convex + roll).dropna()


def irr_alloc(df, method, rf, alpha=0.0, bond_col="decennale"):
    """IRR netta dell'allocazione con la sleeve obbligazionaria maggiorata di
    alpha annuo. Rieseguo tutto: i pesi dipendono dai rendimenti."""
    d = df.copy()
    if alpha:
        d[bond_col] = d[bond_col] + alpha / 12.0
    W, turn = weights_path(d, method)
    gross = (W.shift(1).fillna(0.0) * d).sum(axis=1) - turn * C.COST_ROUND_TRIP
    g = gross.dropna()
    r = simulate_pac(g, CGT_SHARES, rf=rf.reindex(g.index).fillna(0.0),
                     realize_frac=turn.reindex(g.index).clip(0, 1),
                     periods_per_year=12)
    return r.irr_annual


def breakeven(df, method, rf, target, lo=0.0, hi=0.20, tol=1e-4):
    """Bisezione su alpha. Restituisce None se non pareggia entro hi."""
    if irr_alloc(df, method, rf, hi) < target:
        return None
    a, b = lo, hi
    for _ in range(24):
        m = (a + b) / 2
        if irr_alloc(df, method, rf, m) < target:
            a = m
        else:
            b = m
        if b - a < tol:
            break
    return (a + b) / 2


def main():
    ffm = dataio.ff_factors_monthly()
    rf = ffm["RF"]
    eq = (ffm["Mkt-RF"] + ffm["RF"]).rename("azionario")
    simple, y = bond_simple()
    improved = bond_improved()

    df = pd.DataFrame({"azionario": eq, "decennale": simple}).dropna()
    rf0 = rf.reindex(df.index).fillna(0.0)

    print("A11 — di quanto dovrebbe rendere di piu' la sleeve obbligazionaria")
    print(f"Finestra {df.index[0].date()} -> {df.index[-1].date()} "
          f"({len(df)} mesi)\n")

    # ---------------------------------------------- (2) scarto del proxy
    print(f"{'='*88}\n(2) LO SCARTO DEL PROXY, misurato invece che citato\n{'='*88}")
    both = pd.DataFrame({"semplice": simple, "migliorata": improved}).dropna()
    ann = {k: (float((1 + both[k]).prod() ** (12 / len(both)) - 1) * 100)
           for k in both}
    gap = ann["migliorata"] - ann["semplice"]
    print(f"   ricostruzione semplice    (y/12 - D·dy)             "
          f"{ann['semplice']:>6.2f}% annuo")
    print(f"   ricostruzione migliorata  (+ convessita' + rolldown) "
          f"{ann['migliorata']:>6.2f}% annuo")
    print(f"   -> SCARTO DEL PROXY: {gap:+.2f} punti l'anno")
    cx = (0.5 * CONV * (y.diff() ** 2)).reindex(both.index).dropna()
    cx_ann = float(cx.mean()) * 1200
    print(f"      di cui convessita' da sola: {cx_ann:+.2f} punti,")
    print(f"      il resto e' rolldown ({gap - cx_ann:+.2f}).")
    print(f"   Volatilita' annua: semplice {float(both['semplice'].std()*np.sqrt(12))*100:.1f}%"
          f" · migliorata {float(both['migliorata'].std()*np.sqrt(12))*100:.1f}%")
    print(f"   Correlazione fra le due: {float(both.corr().iloc[0,1]):.4f}")

    # ---------------------------------------------- (1) pareggio
    print(f"\n{'='*88}\n(1) IL PAREGGIO: alpha necessario per eguagliare "
          f"l'azionario\n{'='*88}")
    bench = simulate_pac(df["azionario"], CGT_SHARES, rf=rf0,
                         periods_per_year=12).irr_annual
    print(f"   IRR azionario 100%: {bench:.2f}%\n")
    print(f"   {'allocazione':<14}{'IRR base':>11}{'divario':>10}"
          f"{'alpha di pareggio':>20}{'multiplo dello scarto':>24}")
    print("   " + "-" * 79)
    rows = []
    for m in ("erc", "invvol", "6040", "equal"):
        base = irr_alloc(df, m, rf0, 0.0)
        a = breakeven(df, m, rf0, bench)
        mult = (a * 100 / gap) if (a is not None and gap > 0) else float("nan")
        rows.append(dict(method=m, base=base, gap=bench - base,
                         alpha=(a * 100 if a is not None else float("nan")),
                         mult=mult))
        astr = f"{a*100:.2f}% annuo" if a is not None else "> 20% (nessuno)"
        mstr = f"{mult:.1f}x" if mult == mult else "n/d"
        print(f"   {m:<14}{base:>10.2f}%{bench-base:>9.2f}{astr:>20}{mstr:>24}")

    # ---------------------------------------------- controprova diretta
    print(f"\n   CONTROPROVA: e se uso direttamente la ricostruzione migliorata?")
    df2 = pd.DataFrame({"azionario": eq, "decennale": improved}).dropna()
    rf2 = rf.reindex(df2.index).fillna(0.0)
    b2 = simulate_pac(df2["azionario"], CGT_SHARES, rf=rf2,
                      periods_per_year=12).irr_annual
    for r in rows:
        v = irr_alloc(df2, r["method"], rf2, 0.0)
        r["improved"] = v
        print(f"     {r['method']:<10}{v:>7.2f}% contro {b2:.2f}% dell'azionario"
              f"  -> {v - b2:+.2f} punti "
              f"({'ancora sotto' if v < b2 else 'SOPRA'})")

    # ---------------------------------------------- verdetto
    print(f"\n{'='*88}\nVERDETTO SU A11\n{'='*88}")
    print("   Predizione: il pareggio richiede oltre 3 punti l'anno per ERC e")
    print("   inverse-vol, da 4 a 10 volte lo scarto del proxy.")
    print("   FALSIFICATA se l'alpha richiesto sta sotto 1 punto per almeno una")
    print("   delle quattro allocazioni.\n")
    alphas = {r["method"]: r["alpha"] for r in rows}
    for m in ("erc", "invvol"):
        a = alphas[m]
        print(f"   {m:<10} alpha di pareggio {a:.2f}% "
              f"-> {'sopra' if a > 3 else 'SOTTO'} i 3 punti previsti")
    amin = np.nanmin(list(alphas.values()))
    who = [k for k, v in alphas.items() if v == amin]
    print(f"   Alpha minimo fra le quattro: {amin:.2f}% ({who[0]})")
    fals = amin < 1.0
    print(f"   -> ipotesi A11 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    mults = [r["mult"] for r in rows if r["mult"] == r["mult"]]
    print(f"\n   Multiplo dello scarto misurato: da {min(mults):.1f}x a "
          f"{max(mults):.1f}x (previsto 4-10x)")

    lab.log_trials([dict(round=ROUND, hypothesis="A11 alpha di pareggio sleeve obbligazionaria",
                         config=r["method"],
                         window=f"{df.index[0].date()}/{df.index[-1].date()}",
                         sharpe="", irr=r["base"], bh_irr=bench,
                         excess=-r["gap"], n_obs=len(df),
                         note=f"alpha={r['alpha']:.2f}%,proxygap={gap:.2f}%,"
                              f"migliorata={r['improved']:.2f}%") for r in rows])
    pd.DataFrame(rows).assign(proxy_gap=gap, bench=bench).to_csv(
        OUT / "round45_a11.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

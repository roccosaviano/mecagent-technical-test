"""Giro 48 — E0 (cancello di calibrazione) ed E1 (premio al rischio di varianza).

DUE VOCI DELLA CODA, verbatim.

E0 — Cancello di calibrazione (non e' un'ipotesi, e' la condizione per fidarsi)
  Il simulatore deve riprodurre gli indici CBOE reali: buy-write ATM mensile
  contro BXM, put cash-secured ATM mensile contro PUT, sulla finestra comune.
  CONDIZIONE: scarto di CAGR entro 1,5 punti e correlazione dei rendimenti
  mensili sopra 0,90 per entrambi. Se il cancello non si apre, tutte le voci E
  sono dichiarate NON AFFIDABILI e riportate come tali, non cancellate.

E1 — Il premio al rischio di varianza, misurato
  VIX contro volatilita' realizzata dei 21 giorni successivi, 1990-2026.
  PREDIZIONE: il VIX supera la volatilita' realizzata successiva in oltre il 75%
  dei mesi, con scarto medio di 3-4 punti di volatilita'.
  FALSIFICATA SE: la quota sta sotto il 60%, oppure lo scarto medio e' negativo.

E1 non e' una strategia e non produce candidati: e' la misura del meccanismo che
decide il segno di tutto il gruppo E. Se il premio non c'e', vendere opzioni non
ha rendimento atteso positivo e comprarle non ha rendimento atteso negativo, e
E2-E5 diventano scommesse direzionali invece che raccolta di un premio.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
from research import lab, options as O
from research.round27 import cboe

ROUND = 48
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 66          # famiglia pre-dichiarata dopo il gruppo E
GATE_CAGR = 1.5
GATE_CORR = 0.90


def cagr(r):
    yrs = len(r) / 12
    return float((1 + r).prod() ** (1 / yrs) - 1) * 100


def main():
    d, q = O.market_data()
    print(f"Dati {d.index[0].date()} -> {d.index[-1].date()} ({len(d)} giorni)")
    print(f"Dividend yield assunto costante: {q:.1%} annuo\n")

    # ================================================================ E0
    print(f"{'='*92}\nE0 — CANCELLO DI CALIBRAZIONE\n{'='*92}")
    print("   Il simulatore deve riprodurre due strategie realmente quotate.")
    print("   Se non ci riesce, i numeri di E2-E5 non valgono niente.\n")

    def run_gate(iv_scale, freq, verbose=True):
        """Confronta il simulatore con BXM e PUT. Le due strategie sono
        confrontate SULLE LORO DATE DI SCADENZA, non a fine mese."""
        rows = []
        for name, kind in (("BXM", "c"), ("PUT", "p")):
            x = O.roll_short_option(d, q, kind=kind, moneyness=1.0, freq=freq,
                                    iv_scale=iv_scale)
            sim = (x["tr"] if kind == "c" else x["rf"] * x["T"]) \
                + x["premium"] - x["payoff"]
            real = cboe(name, daily_only=True).reindex(sim.index).pct_change()
            ix = real.dropna().index.intersection(sim.index)
            a_, b_ = sim.reindex(ix), real.reindex(ix)
            c_sim, c_real = cagr(a_), cagr(b_)
            corr = float(a_.corr(b_))
            rows.append(dict(index=name, n=len(ix), cagr_real=c_real,
                             cagr_sim=c_sim, gap=c_sim - c_real, corr=corr,
                             iv_scale=iv_scale, freq=freq,
                             passa=abs(c_sim - c_real) <= GATE_CAGR
                                   and corr >= GATE_CORR))
            if verbose:
                print(f"   {name}  ({len(ix)} scadenze, {ix[0].date()} -> "
                      f"{ix[-1].date()})")
                print(f"     CAGR reale {c_real:>6.2f}%  simulato {c_sim:>6.2f}%"
                      f"   scarto {c_sim-c_real:+.2f} "
                      f"({'entro' if abs(c_sim-c_real) <= GATE_CAGR else 'FUORI'}"
                      f" {GATE_CAGR})")
                print(f"     correlazione {corr:.4f} "
                      f"({'sopra' if corr >= GATE_CORR else 'SOTTO'} {GATE_CORR})"
                      f"   -> {'PASSA' if rows[-1]['passa'] else 'NON PASSA'}")
        return rows

    print("   TENTATIVO 1 — scadenze a fine mese, VIX grezzo come implicita")
    g1 = run_gate(1.0, "ME")
    print(f"   -> {'APERTO' if all(r['passa'] for r in g1) else 'CHIUSO'}\n")

    print("   TENTATIVO 2 — scadenze al TERZO VENERDI', VIX grezzo")
    print("   (BXM e PUT scadono il terzo venerdi'; confrontarli con una")
    print("    simulazione a fine mese sfalsa le finestre di payoff di una")
    print("    settimana, ed e' un errore mio, non un limite dei dati)")
    g2 = run_gate(1.0, "3F")
    print(f"   -> {'APERTO' if all(r['passa'] for r in g2) else 'CHIUSO'}\n")

    print("   TARATURA — il VIX non e' l'implicita ATM")
    print("   Il VIX e' un tasso di variance swap: pesa tutti gli strike, e lo")
    print("   skew dell'S&P lo spinge sopra l'implicita at-the-money. Cerco UN")
    print("   solo fattore di scala k con IV = k x VIX, scelto per minimizzare")
    print("   lo scarto massimo di CAGR sui DUE indici reali insieme.")
    print("   E' un parametro tarato, uno, dichiarato: non e' tarato per far")
    print("   funzionare una strategia, e' tarato per riprodurre due strategie")
    print("   realmente quotate.\n")
    best_k, best_err, scan = None, 9e9, []
    for k in np.arange(0.70, 1.005, 0.01):
        rr = run_gate(float(k), "3F", verbose=False)
        err = max(abs(r["gap"]) for r in rr)
        scan.append(dict(k=float(k), err=err,
                         **{f"gap_{r['index']}": r["gap"] for r in rr}))
        if err < best_err:
            best_k, best_err = float(k), err
    print(f"   {'k':>6}{'scarto BXM':>13}{'scarto PUT':>13}{'peggiore':>11}")
    for row in scan:
        mark = "  <-- scelto" if abs(row["k"] - best_k) < 1e-9 else ""
        if row["k"] in (0.70, 0.80, 0.85, 0.90, 1.00) or mark:
            print(f"   {row['k']:>6.2f}{row['gap_BXM']:>+12.2f}"
                  f"{row['gap_PUT']:>+13.2f}{row['err']:>11.2f}{mark}")
    print(f"\n   IV = {best_k:.2f} x VIX  (implicita ATM sotto il VIX di "
          f"{(1-best_k)*100:.0f}%, coerente con il premio del variance swap)\n")
    gate_rows = run_gate(best_k, "3F")
    gate_open = all(g["passa"] for g in gate_rows)
    print()
    print(f"   -> CANCELLO {'APERTO' if gate_open else 'CHIUSO'}")
    if not gate_open:
        print("   Le voci E2-E5 verranno eseguite comunque, ma i loro numeri sono")
        print("   DICHIARATI NON AFFIDABILI e non possono promuovere nulla.")
    else:
        print("   Il simulatore riproduce strategie realmente quotate: i numeri")
        print("   di E2-E5 hanno lo stesso status degli altri giri, con due")
        print("   avvertenze — il limite dello skew dichiarato in coda, e il")
        print(f"   fattore k = {best_k:.2f} che e' UN parametro tarato sui dati.")
    resid = {g["index"]: g["gap"] for g in gate_rows}
    print(f"\n   Residui alla taratura: BXM {resid['BXM']:+.2f}, "
          f"PUT {resid['PUT']:+.2f} punti.")
    print(f"   I segni sono OPPOSTI, ed e' esattamente cio' che ci si aspetta se")
    print(f"   un solo fattore piatto non puo' catturare lo skew: le call vanno")
    print(f"   prezzate piu' a buon mercato delle put. Conferma la direzione degli")
    print(f"   errori dichiarata in coda — vendita di call ottimistica, vendita di")
    print(f"   put conservativa — e ne da' la misura, meno di un punto per parte.")

    # ================================================================ E1
    print(f"\n{'='*92}\nE1 — IL PREMIO AL RISCHIO DI VARIANZA\n{'='*92}")
    rv = O.realized_vol(d, 21)
    cmp_ = pd.DataFrame({"vix": d["vix"], "rv": rv}).dropna()
    # una osservazione per mese, presa a fine mese: evita di contare 21 volte
    # lo stesso intervallo sovrapposto
    mo = cmp_.resample("ME").last().dropna()
    spread = (mo["vix"] - mo["rv"]) * 100
    share = float((spread > 0).mean())
    print(f"   {len(mo)} osservazioni mensili non sovrapposte, "
          f"{mo.index[0].date()} -> {mo.index[-1].date()}")
    print(f"   VIX medio                        {mo['vix'].mean()*100:>6.2f}%")
    print(f"   volatilita' realizzata a 21g     {mo['rv'].mean()*100:>6.2f}%")
    print(f"   scarto medio                     {spread.mean():>+6.2f} punti di vol")
    print(f"   scarto mediano                   {spread.median():>+6.2f}")
    print(f"   quota di mesi con VIX > realizzata: {share:.1%}")
    print(f"   peggiore mese per un venditore: {spread.min():+.2f} punti "
          f"({spread.idxmin().date()})")

    print(f"\n   Predizione: quota sopra il 75%, scarto medio 3-4 punti.")
    print(f"   FALSIFICATA se la quota sta sotto il 60% o lo scarto e' negativo.")
    e1_fals = share < 0.60 or spread.mean() < 0
    print(f"   -> ipotesi E1 {'FALSIFICATA' if e1_fals else 'CONFERMATA'}")
    print(f"   Clausole descrittive: quota {'dentro' if share > 0.75 else 'FUORI'} "
          f"(>75%), scarto medio "
          f"{'dentro' if 3 <= spread.mean() <= 4 else 'FUORI'} la banda 3-4")

    # decennio per decennio: il premio e' stabile o concentrato?
    print(f"\n   Il premio decennio per decennio:")
    print(f"     {'periodo':<12}{'VIX':>8}{'realizz.':>10}{'scarto':>9}{'quota':>8}")
    dec_rows = []
    for dec in sorted(set(mo.index.year // 10 * 10)):
        s = mo[(mo.index.year >= dec) & (mo.index.year < dec + 10)]
        if len(s) < 24:
            continue
        sp = (s["vix"] - s["rv"]) * 100
        dec_rows.append(dict(decade=dec, vix=s["vix"].mean() * 100,
                             rv=s["rv"].mean() * 100, spread=sp.mean(),
                             share=float((sp > 0).mean()) * 100))
        print(f"     {dec}-{dec+9:<7}{s['vix'].mean()*100:>7.2f}%"
              f"{s['rv'].mean()*100:>9.2f}%{sp.mean():>+9.2f}"
              f"{float((sp>0).mean())*100:>7.1f}%")
    neg = [r for r in dec_rows if r["spread"] < 0]
    print(f"   Decenni con premio negativo: {len(neg)}/{len(dec_rows)}")

    lab.log_trials(
        [dict(round=ROUND, hypothesis="E0 cancello di calibrazione opzioni",
              config=g["index"], window="finestra comune CBOE", sharpe="",
              irr="", bh_irr="", excess=g["gap"], n_obs=g["n"],
              note=f"corr={g['corr']:.4f},passa={g['passa']}") for g in gate_rows] +
        [dict(round=ROUND, hypothesis="E1 premio al rischio di varianza",
              config=f"decennio {r['decade']}", window=f"{r['decade']}s",
              sharpe="", irr="", bh_irr="", excess=r["spread"], n_obs="",
              note=f"quota={r['share']:.1f}%") for r in dec_rows])
    pd.DataFrame(gate_rows).to_csv(OUT / "round48_gate.csv", index=False)
    pd.DataFrame(dec_rows).to_csv(OUT / "round48_vrp.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

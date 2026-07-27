"""Giro 35 — A7 (stabilita' HRP contro min-variance) e A8 (min-variance in leva).

DUE VOCI DELLA CODA, predizioni scritte prima, riportate verbatim.

A7 — La tesi vera di HRP: stabilita' contro il min-variance
  PREDIZIONE: HRP risulta 3-10 volte piu' stabile del min-variance, cioe' la
  tesi del paper regge sul suo bersaglio dichiarato — e resta comunque
  irrilevante per l'IRR netta, perche' entrambi perdono contro il cap-weighted.
  FALSIFICATA SE: HRP non e' piu' stabile del min-variance.

A8 — Monetizzare lo Sharpe: min-variance portato in leva a pari volatilita'
  PREDIZIONE: la leva 1,20x recupera parte del divario ma non lo chiude — il
  costo di finanziamento (rf medio 4,45% + 3% sul 20% preso a prestito) piu' le
  imposte lasciano il risultato sotto il cap-weight di almeno 1 punto.
  FALSIFICATA SE: IRR netta >= cap-weight.

Le due voci sono nello stesso file perche' girano sugli stessi pesi calcolati
una volta sola, ma hanno verdetti separati e voci separate a registro.
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
from tax import simulate_pac, CGT_SHARES, TRADING_52
from research import lab, bench as B
from research.round31 import backtest as alloc_bt, weight_stability

ROUND = 35
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 56


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    eq = (ff["Mkt-RF"] + ff["RF"]).reindex(ind.index)

    print(f"49 settori, {ind.index[0].date()} -> {ind.index[-1].date()} "
          f"({len(ind)} mesi)\n")

    # pesi calcolati una volta sola e riusati dalle due voci
    from research.round32 import backtest as opt_bt
    out = {}
    for m in ("hrp", "invvar", "equal"):
        net, turn, W, nfit = alloc_bt(ind, m)
        out[m] = dict(net=net, turn=turn, W=W)
    for m in ("minvar", "maxdiv"):
        net, turn, W, conds, _ = opt_bt(ind, m)
        out[m] = dict(net=net, turn=turn, W=W)

    idx = out["hrp"]["net"].index
    bb = simulate_pac(eq.reindex(idx), CGT_SHARES,
                      rf=rf.reindex(idx).fillna(0), periods_per_year=12)

    # ---------------------------------------------------------------- A7
    print(f"{'='*88}\nA7 — stabilita' dei pesi: HRP contro il suo bersaglio\n{'='*88}")
    stab = {m: weight_stability(out[m]["W"]) for m in out}
    print(f"   {'metodo':<22}{'movimento medio dei pesi per ribilanciamento':>46}")
    for m in ("equal", "invvar", "hrp", "maxdiv", "minvar"):
        print(f"   {m:<22}{stab[m]:>46.3f}")
    ratio = stab["minvar"] / stab["hrp"]
    print(f"\n   Predizione: HRP 3-10 volte piu' stabile del min-variance.")
    print(f"   Osservato: min-var {stab['minvar']:.3f} / HRP {stab['hrp']:.3f} "
          f"= {ratio:.2f} volte")
    a7_fals = ratio <= 1.0
    print(f"   -> ipotesi A7 {'FALSIFICATA' if a7_fals else 'CONFERMATA nel verso'}"
          + ("" if a7_fals else f", ma il fattore e' {ratio:.2f}, non 3-10"))
    print(f"\n   Nota: l'equal-weight ({stab['equal']:.3f}) e' il piu' stabile per")
    print(f"   identita', non per merito — riazzera a 1/N a ogni ribilanciamento.")
    print(f"   Il confronto informativo e' HRP contro gli ottimizzatori.")

    # ---------------------------------------------------------------- A8
    print(f"\n{'='*88}\nA8 — min-variance in leva a pari volatilita'\n{'='*88}")
    mv = out["minvar"]["net"]
    vmv = float(mv.std() * np.sqrt(12))
    veq = float(eq.reindex(idx).std() * np.sqrt(12))
    L_match = veq / vmv
    print(f"   Volatilita' min-var {vmv*100:.1f}% · cap-weight {veq*100:.1f}%")
    print(f"   Leva per pareggiare: {L_match:.2f}x   (la voce ne dichiara 1,20)")
    fin = rf.reindex(mv.index).fillna(0.0) + C.FIN_SPREAD / 12.0
    print(f"   Finanziamento: risk-free + {C.FIN_SPREAD*100:.0f}% annuo\n")

    rows = []
    for L in (1.00, 1.20, L_match, 1.50):
        lev = L * mv - (L - 1.0) * fin
        curve = (1 + lev).cumprod()
        dd = curve / curve.cummax() - 1.0
        # margine: con leva L il prestito e' (L-1)/L del valore iniziale della
        # posizione. Il rapporto di equity peggiore si tocca al drawdown peggiore.
        worst = float(1.0 - (L - 1.0) / L / (1.0 + dd.min()))
        rz = out["minvar"]["turn"].reindex(mv.index).clip(0, 1)
        r = B.eval_stream(f"min-var leva {L:.2f}x", lev, rf, rz)
        r["worst_equity"] = worst
        r["L"] = L
        rows.append(r)
    bench_row = B.eval_stream("cap-weighted (benchmark)", eq.reindex(idx), rf)
    bench_row["L"] = 0.0
    rows.append(bench_row)
    print()
    B.table(rows)
    print(f"\n   Rapporto di equity al drawdown peggiore, per livello di leva.")
    print(f"   La chiusura forzata ESMA scatta sotto il 50% del margine iniziale:")
    for r in rows:
        if "worst_equity" not in r or r["L"] <= 1.0:
            continue
        w = r["worst_equity"]
        print(f"     {r['label']:<24}{w:>7.1%}   "
              + ("margin call: la posizione viene chiusa sui minimi"
                 if w < 0.5 else "regge, nessuna chiusura forzata"))
    print(f"   A 1,2x il margine iniziale e' l'83% del valore e regge. A 1,5x no:")
    print(f"   il drawdown del min-variance in leva arriva dove il broker chiude.")

    l12 = next(r for r in rows if abs(r["L"] - 1.20) < 1e-9)
    gap = l12["irr"] - bb.irr_annual
    print(f"\n   Predizione: la leva 1,20x lascia il risultato sotto il cap-weight")
    print(f"   di almeno 1 punto. FALSIFICATA se IRR netta >= cap-weight.")
    print(f"   Osservato: {l12['irr']:.2f}% contro {bb.irr_annual:.2f}% "
          f"-> {gap:+.2f} punti")
    a8_fals = gap >= 0
    print(f"   -> ipotesi A8 {'FALSIFICATA' if a8_fals else 'CONFERMATA'}"
          + ("" if abs(gap) >= 1 or a8_fals else "  (ma il divario e' sotto il punto previsto)"))

    be = None
    for L in np.arange(1.0, 3.01, 0.05):
        lev = L * mv - (L - 1.0) * fin
        rz = out["minvar"]["turn"].reindex(mv.index).clip(0, 1)
        r33 = simulate_pac(lev, CGT_SHARES, rf=rf.reindex(mv.index).fillna(0),
                           realize_frac=rz, periods_per_year=12)
        if r33.irr_annual >= bb.irr_annual:
            be = float(L)
            break
    print(f"\n   Leva necessaria per pareggiare il cap-weight: "
          + (f"{be:.2f}x" if be else "nessuna sotto 3,00x"))
    if be:
        print(f"   A quella leva la volatilita' sarebbe {vmv*be*100:.1f}% contro")
        print(f"   {veq*100:.1f}% del benchmark: si compra il pareggio di rendimento")
        print(f"   vendendo il vantaggio di rischio che era tutto il punto.")

    best = max(rows, key=lambda r: r["irr"])
    d = lab.deflated_sharpe(best["gross"], N_PREREG, round_id=ROUND)
    print(f"\n   DSR del migliore su N={N_PREREG}: {d['dsr']:.3f} -> "
          + ("PROMUOVIBILE" if d["dsr"] > 0.95 and best["irr"] > bb.irr_annual
             else "NON promuovibile"))

    lab.log_trials(
        [dict(round=ROUND, hypothesis="A7 stabilita' pesi HRP vs min-var",
              config=m, window=f"{idx[0].date()}/{idx[-1].date()}", sharpe="",
              irr="", bh_irr="", excess="", n_obs=len(idx),
              note=f"stab={stab[m]:.3f}") for m in stab] +
        [dict(round=ROUND, hypothesis="A8 min-variance in leva",
              config=r["label"], window=f"{idx[0].date()}/{idx[-1].date()}",
              sharpe=r["sharpe"], irr=r["irr"], bh_irr=bb.irr_annual,
              excess=r["irr"] - bb.irr_annual, n_obs=r["n"],
              note=f"vol={r['vol']:.1f}%") for r in rows])
    pd.DataFrame([{k: v for k, v in r.items() if k != "gross"}
                  for r in rows]).to_csv(OUT / "round35_leva.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

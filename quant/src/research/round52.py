"""Giro 52 — E6: stress sui LEAPS.

VOCE DELLA CODA, verbatim:
  PREDIZIONE: il vantaggio sparisce con un rincaro del premio sotto il 15% e con
  k sotto 1,00; sulle finestre mobili vince in meno della meta' dei casi.
  FALSIFICATA SE: sopravvive a un rincaro del 30% del premio E vince in piu'
  della meta' delle finestre mobili.

Tre stress sulla configurazione del giro 49: moneyness 80%, leve 1,0-1,5x.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import dataio
from research import lab, bench as B, options as O

ROUND = 52
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 72
WIN_Y = 20


def main():
    d, q = O.market_data()
    ff = dataio.ff_factors_monthly()
    rf_all = ff["RF"]

    bhs = O.roll_short_option(d, q, kind="c", moneyness=1.0, iv_scale=0.85)
    eq = O.monthly_index(bhs["tr"]).dropna()
    rf0 = rf_all.reindex(eq.index).ffill().fillna(0.0)
    bh = B.eval_stream("azionario buy&hold", eq, rf0)
    print(f"Finestra {eq.index[0].date()} -> {eq.index[-1].date()}")
    print(f"Benchmark PAC azionario: IRR netta {bh['irr']:.2f}%\n")

    def leaps(k, mult, L, sub=None):
        s, z = O.leaps_mtm(d, q, moneyness=0.80, iv_scale=k, leverage=L,
                           prem_mult=mult)
        if sub is not None:
            s, z = s.reindex(sub).dropna(), z.reindex(sub).dropna()
            if len(s) < WIN_Y * 12 - 6:
                return None
        return B.eval_stream(f"LEAPS k={k:.2f} m={mult:.2f} L={L:.1f}", s,
                             rf_all.reindex(s.index).ffill().fillna(0.0), z)

    rows = []
    # ---------------------------------------------- (i) implicita piu' alta
    print(f"{'='*88}\n(i) IMPLICITA PIU' ALTA — k = IV/VIX\n{'='*88}")
    print("   Le call deep ITM trattano sopra l'ATM per parita' dallo skew delle")
    print("   put. k = 0,85 e' il valore tarato su BXM e PUT, che sono ATM.\n")
    print(f"   {'k':>6}" + "".join(f"{f'leva {L:.1f}x':>14}" for L in (1.0, 1.2, 1.5)))
    print("   " + "-" * 48)
    for k in (0.85, 0.95, 1.05, 1.15):
        line = f"   {k:>6.2f}"
        for L in (1.0, 1.2, 1.5):
            r = leaps(k, 1.0, L)
            rows.append(dict(stress="k", k=k, mult=1.0, L=L, irr=r["irr_ref"],
                             vs=r["irr_ref"] - bh["irr"], dd=r["dd"]))
            line += f"{r['irr_ref']:>12.2f}%" + ("*" if r["irr_ref"] > bh["irr"] else " ")
        print(line)
    print(f"   (* batte il benchmark, {bh['irr']:.2f}%)")
    kfail = [r["k"] for r in rows if r["L"] == 1.5 and r["vs"] <= 0]
    print(f"\n   A leva 1,5x il vantaggio sparisce da k = "
          + (f"{min(kfail):.2f}" if kfail else "mai, entro 1,15"))

    # ---------------------------------------------- (ii) rincaro del premio
    print(f"\n{'='*88}\n(ii) RINCARO DEL PREMIO D'INGRESSO\n{'='*88}")
    print("   Spread denaro-lettera ed esecuzione su uno strumento poco liquido:")
    print("   si paga di piu' all'ingresso, il valore di mercato non cambia.\n")
    print(f"   {'rincaro':>9}" + "".join(f"{f'leva {L:.1f}x':>14}" for L in (1.0, 1.2, 1.5)))
    print("   " + "-" * 51)
    for m in (1.00, 1.05, 1.10, 1.15, 1.20, 1.30, 1.40):
        line = f"   {(m-1)*100:>8.0f}%"
        for L in (1.0, 1.2, 1.5):
            r = leaps(0.85, m, L)
            rows.append(dict(stress="mult", k=0.85, mult=m, L=L, irr=r["irr_ref"],
                             vs=r["irr_ref"] - bh["irr"], dd=r["dd"]))
            line += f"{r['irr_ref']:>12.2f}%" + ("*" if r["irr_ref"] > bh["irr"] else " ")
        print(line)
    mfail = [r["mult"] for r in rows if r["stress"] == "mult" and r["L"] == 1.5
             and r["vs"] <= 0]
    bp = (min(mfail) - 1) * 100 if mfail else None
    print(f"\n   A leva 1,5x il vantaggio sparisce con un rincaro del "
          + (f"{bp:.0f}%" if bp is not None else "oltre il 40%"))

    # ---------------------------------------------- (iii) finestre mobili
    print(f"\n{'='*88}\n(iii) FINESTRE MOBILI DI {WIN_Y} ANNI\n{'='*88}")
    y0, y1 = eq.index[0].year, eq.index[-1].year
    wins = {L: [] for L in (1.0, 1.2, 1.5)}
    for st in range(y0, y1 - WIN_Y + 2):
        sub = eq.index[(eq.index.year >= st) & (eq.index.year < st + WIN_Y)]
        if len(sub) < WIN_Y * 12 - 6:
            continue
        b = B.eval_stream("b", eq.reindex(sub), rf0.reindex(sub))
        for L in (1.0, 1.2, 1.5):
            r = leaps(0.85, 1.0, L, sub=sub)
            if r:
                wins[L].append((st, r["irr_ref"] - b["irr"]))
    print(f"   {'leva':>6}{'finestre':>10}{'vinte':>8}{'quota':>9}"
          f"{'media':>9}{'peggiore':>10}{'migliore':>10}")
    print("   " + "-" * 52)
    shares = {}
    for L in (1.0, 1.2, 1.5):
        v = np.array([x for _, x in wins[L]])
        if not len(v):
            continue
        shares[L] = float((v > 0).mean())
        print(f"   {L:>5.1f}x{len(v):>10}{int((v>0).sum()):>8}"
              f"{shares[L]*100:>8.1f}%{v.mean():>+8.2f}%{v.min():>+9.2f}%"
              f"{v.max():>+9.2f}%")

    # ---------------------------------------------- verdetto
    print(f"\n{'='*88}\nVERDETTO SU E6\n{'='*88}")
    print("   Predizione: sparisce con rincaro sotto il 15% e con k sotto 1,00;")
    print("   vince in meno della meta' delle finestre mobili.")
    print("   FALSIFICATA se sopravvive a un rincaro del 30% E vince in piu'")
    print("   della meta' delle finestre.\n")
    surv30 = [r for r in rows if r["stress"] == "mult" and abs(r["mult"] - 1.30) < 1e-9
              and r["vs"] > 0]
    maj = [L for L, s in shares.items() if s > 0.5]
    s30 = ("SI, a leva " + ", ".join("%.1fx" % r["L"] for r in surv30)) if surv30 else "NO"
    smaj = ("SI, a leva " + ", ".join("%.1fx" % L for L in maj)) if maj else "NO"
    print(f"   Sopravvive a un rincaro del 30%? {s30}")
    print(f"   Vince in piu' della meta' delle finestre? {smaj}")
    e6_fals = bool(surv30) and bool(maj) and bool(set(r["L"] for r in surv30) & set(maj))
    print(f"   -> ipotesi E6 {'FALSIFICATA' if e6_fals else 'CONFERMATA'}")
    if not e6_fals:
        print("\n   La voce si chiude: il +1,34 del giro 49 sta dentro l'incertezza")
        print("   del modello. I LEAPS NON sono un candidato.")

    lab.log_trials([dict(round=ROUND, hypothesis="E6 stress sui LEAPS",
                         config=f"{r['stress']} k={r['k']:.2f} m={r['mult']:.2f} L={r['L']:.1f}",
                         window="1990-2026", sharpe="", irr=r["irr"],
                         bh_irr=bh["irr"], excess=r["vs"], n_obs="",
                         note=f"dd={r['dd']:.1f}%") for r in rows])
    pd.DataFrame(rows).to_csv(OUT / "round52_leaps_stress.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

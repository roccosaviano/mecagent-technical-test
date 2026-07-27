"""Giro 58 — A14: rischio di sequenza sul LIVELLO, non sul divario.

VOCE DELLA CODA, verbatim:
  Il giro 47 ha falsificato A13 e ha mostrato dove sbagliavo: il peso del
  capitale in un PAC ventennale e' 9,5:1 fra ultimi e primi tre anni, ma il
  rapporto fra i coefficienti sul DIVARIO fra due allocazioni e' solo 1,2-2,7:1.
  PREDIZIONE: sul LIVELLO il rapporto sale sopra 6 e l'R2 dei soli ultimi tre
  anni supera 0,6, avvicinandosi al 9,5:1 aritmetico; entrambi i coefficienti
  sono POSITIVI, a differenza del divario dove hanno segni opposti.
  FALSIFICATA SE: il rapporto sul livello resta sotto 4 — nel qual caso la mia
  spiegazione del giro 47 e' sbagliata quanto quella del giro 46.
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")
import dataio
from research import lab
from research.round47 import rolling_windows, ols, capital_weight_profile, WIN_Y, EDGE_Y
from research.round45 import bond_simple

ROUND, N_PREREG = 58, 75
OUT = Path(__file__).resolve().parents[2] / "out"


def main():
    ffm = dataio.ff_factors_monthly()
    rf = ffm["RF"]
    eq = (ffm["Mkt-RF"] + ffm["RF"]).rename("azionario")
    simple, _ = bond_simple()
    full = pd.DataFrame({"azionario": eq, "decennale": simple}).dropna()
    df = rolling_windows(full, rf)

    w = capital_weight_profile()
    ratio_arit = w[-EDGE_Y:].sum() / w[:EDGE_Y].sum()
    print(f"A14 — rischio di sequenza sul LIVELLO dell'IRR")
    print(f"{len(df)} finestre di {WIN_Y} anni, {df['start'].min()}-{df['end'].max()}")
    print(f"Peso aritmetico del capitale, ultimi {EDGE_Y} anni contro primi "
          f"{EDGE_Y}: {ratio_arit:.2f}:1\n")

    targets = [("azionario 100%", "eq")] + [(f"{m}", f"{m}_irr")
                                            for m in ("erc", "invvol", "6040", "equal")]
    print(f"   {'PAC':<18}{'b(ultimi 3)':>14}{'b(primi 3)':>13}{'rapporto':>11}"
          f"{'R2 ultimi':>12}{'R2 entrambi':>13}")
    print("   " + "-" * 81)
    rows = []
    for lbl, col in targets:
        y = df[col].to_numpy()
        X = df[["last3", "first3"]].to_numpy()
        beta, r2b = ols(y, X)
        bl, bf = beta[1], beta[2]
        _, r2l = ols(y, df[["last3"]].to_numpy())
        rt = abs(bl) / abs(bf) if bf != 0 else float("inf")
        rows.append(dict(pac=lbl, b_last=bl, b_first=bf, ratio=rt,
                         r2_last=r2l, r2_both=r2b,
                         segni="entrambi positivi" if bl > 0 and bf > 0 else "segni misti"))
        print(f"   {lbl:<18}{bl:>14.3f}{bf:>13.3f}{rt:>11.2f}{r2l:>12.3f}{r2b:>13.3f}")

    # confronto diretto col giro 47 (divario)
    print(f"\n   Per confronto, il giro 47 sul DIVARIO fra allocazioni:")
    for m in ("erc", "invvol", "6040", "equal"):
        y = df[f"{m}_diff"].to_numpy()
        beta, _ = ols(y, df[["last3", "first3"]].to_numpy())
        rt = abs(beta[1]) / abs(beta[2]) if beta[2] != 0 else float("inf")
        print(f"     {m:<10} b(ult)={beta[1]:>7.3f}  b(pri)={beta[2]:>7.3f}  "
              f"rapporto {rt:>5.2f}")

    print(f"\n{'='*84}\nVERDETTO SU A14\n{'='*84}")
    print("   Predizione: sul livello il rapporto sale sopra 6, l'R2 dei soli")
    print("   ultimi tre supera 0,6, ed entrambi i coefficienti sono positivi.")
    print("   FALSIFICATA se il rapporto sul livello resta sotto 4.\n")
    rmin = min(r["ratio"] for r in rows)
    rmax = max(r["ratio"] for r in rows)
    print(f"   Rapporto sul livello: da {rmin:.2f} a {rmax:.2f}")
    print(f"   R2 dei soli ultimi 3: da {min(r['r2_last'] for r in rows):.3f} "
          f"a {max(r['r2_last'] for r in rows):.3f}")
    npos = sum(1 for r in rows if r["segni"] == "entrambi positivi")
    print(f"   Coefficienti entrambi positivi in {npos}/{len(rows)} PAC")
    fals = rmin < 4.0
    print(f"\n   -> ipotesi A14 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"\n   Clausole descrittive:")
    print(f"   (a) rapporto sopra 6: "
          f"{'SI' if rmin > 6 else 'NO'} (minimo {rmin:.2f})")
    print(f"   (b) R2 sopra 0,6: "
          f"{'SI' if min(r['r2_last'] for r in rows) > 0.6 else 'NO'}")
    print(f"   (c) rapporto vicino al 9,5:1 aritmetico: scarto "
          f"{abs(np.mean([r['ratio'] for r in rows]) - ratio_arit):.2f}")

    lab.log_trials([dict(round=ROUND, hypothesis="A14 sequenza sul livello",
                         config=r["pac"], window="finestre di 20 anni", sharpe="",
                         irr="", bh_irr="", excess="", n_obs=len(df),
                         note=f"b_last={r['b_last']:.3f},ratio={r['ratio']:.2f},"
                              f"r2={r['r2_last']:.3f}") for r in rows])
    pd.DataFrame(rows).to_csv(OUT / "round58_a14.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

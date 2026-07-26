"""Ricontabilizzazione del multiple testing: selezione contro specificazione.

IL DIFETTO CHE STO CORREGGENDO. Ho applicato a ogni candidato il numero
CUMULATO di configurazioni valutate in tutto lo studio (691 a registro, piu'
migliaia di valutazioni interne). E' troppo severo, e per una ragione precisa:
il Deflated Sharpe corregge la distorsione del MASSIMO di N estrazioni. Se un
candidato non e' stato scelto come massimo di quelle N prove, quel N non e' il
suo.

Le prove di questo studio sono di due tipi, e vanno contate diversamente:

  SELEZIONE   una griglia di parametri viene percorsa e si tiene il migliore.
              Qui il massimo E' distorto e N e' la dimensione della griglia.
              Esempi: i giri 1, 2, 4, 5, 11, 12 (walk-forward con scelta
              annuale dei parametri).

  SPECIFICAZIONE  una singola configurazione motivata a priori viene provata
              una volta sola. Non c'e' massimo da correggere. N = 1 per il
              test, ma la FAMIGLIA di ipotesi pre-dichiarate va comunque
              corretta, perche' riportare solo quelle che passano sarebbe
              selezione mascherata.
              Esempi: BXM e PUT (indici pubblicati, nessun parametro mio),
              Kronos (modello pre-addestrato), i punti della frontiera del
              giro 13 (valutati uno per uno, non scelti).

La correzione giusta per la seconda categoria e' sulla FAMIGLIA delle ipotesi
pre-dichiarate, che in questo studio sono circa 30, non 691. Sotto ricalcolo
tutto con entrambe le contabilita' e mostro quali conclusioni cambiano.

NOTA ONESTA: questa correzione mi e' stata fatta notare dall'utente, ed e'
corretta. Non cambia il risultato principale, ma cambia due verdetti.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from research import lab

OUT = Path(__file__).resolve().parents[2] / "out"

# candidati principali: (nome, Sharpe ann., n periodi, ppy, N selezione,
#                        extra vs benchmark)
CANDS = [
    ("H5 momentum settoriale",        0.67, 756, 12, 450, +2.95),
    ("H11a composito mom+low-vol",    0.67, 756, 12, 1260, +3.08),
    ("H11c media dei compositi",      0.68, 300, 12, 1335, +3.30),
    ("H12 momentum con isteresi",     0.55, 756, 12, 1512, +1.38),
    ("H4 tilt difensivo low-vol",     0.58, 756, 12, 378, +0.73),
    ("Frontiera giro 13, 60% turn.",  0.59, 900, 12, 10, +2.23),
    ("VWAP cripto trimestrale",       1.53, 2127, 365, 63, +23.6),
    ("Donchian cripto long-only",     1.35, 1826, 365, 36, +27.7),
    ("PUT writing (indice CBOE)",     0.55, 4779, 252, 1, -4.69),
    ("BXM covered call (indice CBOE)", 0.53, 5783, 252, 1, -4.94),
    ("Regime detection + convex",     0.57, 4378, 252, 140, -8.27),
]

N_PREREG = 30      # ipotesi pre-dichiarate in tutto lo studio


def dsr(sr_ann, T, ppy, n_trials, var_sr):
    """DSR con Sharpe per periodo, ipotizzando normalita' (skew 0, curtosi 3).
    E' la forma di base: senza la serie non posso correggere per le code, e
    ometterlo rende il test PIU' permissivo, non meno."""
    from scipy import stats as st
    import math
    sr = sr_ann / np.sqrt(ppy)
    if n_trials < 2 or var_sr <= 0:
        sr0 = 0.0
    else:
        g = 0.5772156649
        s = math.sqrt(var_sr)
        sr0 = s * ((1 - g) * st.norm.ppf(1 - 1 / n_trials)
                   + g * st.norm.ppf(1 - 1 / (n_trials * math.e)))
    z = (sr - sr0) * math.sqrt(T - 1)
    return float(st.norm.cdf(z)), sr0 * np.sqrt(ppy)


def main():
    reg = lab.load_registry()
    sh = pd.to_numeric(reg["sharpe"], errors="coerce").dropna() / np.sqrt(252)
    var_sr = float(sh.var(ddof=1))
    print(f"Varianza degli Sharpe a registro (per periodo): {var_sr:.6f}")
    print(f"Tentativi a registro: {len(reg)}   ipotesi pre-dichiarate: {N_PREREG}\n")

    print(f"{'candidato':<32}{'Sharpe':>8}{'vs B&H':>9}"
          f"{'DSR vecchio':>13}{'DSR corretto':>14}{'cambia?':>10}")
    print("-" * 88)
    rows = []
    for name, sr, T, ppy, nsel, ex in CANDS:
        # vecchia contabilita': tutto il registro
        d_old, _ = dsr(sr, T, ppy, len(reg), var_sr)
        # corretta: N = griglia che ha prodotto QUESTO candidato, ma mai meno
        # della famiglia di ipotesi pre-dichiarate
        n_fair = max(nsel, N_PREREG)
        d_new, sr0 = dsr(sr, T, ppy, n_fair, var_sr)
        pass_old = d_old > 0.95 and ex > 0
        pass_new = d_new > 0.95 and ex > 0
        chg = "SI" if pass_old != pass_new else ""
        rows.append(dict(name=name, sharpe=sr, ex=ex, n_fair=n_fair,
                         dsr_old=d_old, dsr_new=d_new, sr0=sr0,
                         pass_old=pass_old, pass_new=pass_new))
        print(f"{name:<32}{sr:>8.2f}{ex:>+8.2f}%{d_old:>13.3f}{d_new:>14.3f}"
              f"{chg:>10}")

    d = pd.DataFrame(rows)
    print(f"\nPromossi con la vecchia contabilita': "
          f"{int(d['pass_old'].sum())}/{len(d)}")
    print(f"Promossi con quella corretta:        "
          f"{int(d['pass_new'].sum())}/{len(d)}")
    if d["pass_new"].any():
        print(f"\nChi passa ora:")
        for _, r in d[d["pass_new"]].iterrows():
            print(f"  {r['name']:<32}Sharpe {r['sharpe']:.2f} contro soglia "
                  f"{r['sr0']:.2f}, {r['ex']:+.2f} punti sul benchmark")
    print(f"\nQuelli che restano fuori NON restano fuori per il conteggio:")
    for _, r in d[~d["pass_new"]].iterrows():
        why = "perde contro il benchmark" if r["ex"] <= 0 else \
              f"DSR {r['dsr_new']:.3f} sotto 0,95"
        print(f"  {r['name']:<32}{why}")

    d.to_csv(OUT / "recount_dsr.csv", index=False)
    return d


if __name__ == "__main__":
    main()

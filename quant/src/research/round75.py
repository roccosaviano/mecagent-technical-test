"""L3 — Il report finale.

VOCE DI CODA (verbatim, committata prima di eseguire):
  `quant/reports/REPORT.md` e' fermo al giro 29 e porta ancora il +1,72
  pre-correzione. Da produrre: un report che riporti la regola dell'holdout
  (giro 72), i sei-otto numeri che contano, i tre errori di misura trovati e
  corretti (base fiscale, lotti ETF, rotazione), e le raccomandazioni operative
  che il progetto PUO' sostenere.
  PREDIZIONE: i numeri che sopravvivono a una rilettura completa sono MENO DI
  DIECI, e NESSUNO di essi e' un margine di strategia: sono tutti costi, soglie
  o misure di fragilita'.
  FALSIFICATA SE: nella rilettura emerge un risultato di strategia mai
  contraddetto dai giri successivi e con margine sopra un punto.

Questo script NON e' il report: e' il CONTROLLO DI FALSIFICAZIONE, che il report
non puo' fare a mano su 1.365 righe. Scandaglia il registro cumulato e tira
fuori OGNI riga con excess >= +1,00 punti, la raggruppa per ipotesi, e per
ciascun gruppo stampa quante righe ha, il massimo e la finestra. Il giudizio
"contraddetta dai giri successivi o no" lo do io nel report, riga per riga, ma
la LISTA DEI CANDIDATI dev'essere esaustiva e prodotta dalla macchina, non
dalla mia memoria: se ne resta uno solo non contraddetto, L3 e' falsificata.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from research import lab

ROUND = 75
SOGLIA = 1.00


def main():
    reg = pd.read_csv(lab.REGISTRY)
    print(f"{'=' * 100}\nL3 — controllo di falsificazione sul registro cumulato\n{'=' * 100}")
    print(f"   righe a registro: {len(reg)}   giri: {reg['round'].min()}-{reg['round'].max()}")

    ex = pd.to_numeric(reg["excess"], errors="coerce")
    reg = reg.assign(excess=ex)
    vinc = reg[reg["excess"] >= SOGLIA].copy()
    print(f"   righe con excess >= +{SOGLIA:.2f} punti: **{len(vinc)}** "
          f"({len(vinc) / len(reg):.1%} del registro)\n")

    g = (vinc.groupby(["round", "hypothesis"])
             .agg(righe=("excess", "size"), max_ex=("excess", "max"),
                  med_ex=("excess", "median"), finestra=("window", "first"))
             .reset_index().sort_values("max_ex", ascending=False))

    print(f"   {'giro':>5}  {'ipotesi':<46}{'righe':>6}{'max':>8}{'mediana':>9}  finestra")
    print("   " + "-" * 96)
    for _, r in g.iterrows():
        print(f"   {r['round']:>5}  {str(r['hypothesis'])[:44]:<46}{r['righe']:>6}"
              f"{r['max_ex']:>+8.2f}{r['med_ex']:>+9.2f}  {str(r['finestra'])[:22]}")

    # quante ipotesi distinte, e quante hanno la MEDIANA sopra soglia
    print(f"\n   ipotesi distinte con almeno una riga sopra +{SOGLIA:.2f}: "
          f"**{len(g)}**")
    solide = g[g["med_ex"] >= SOGLIA]
    print(f"   di queste, con la MEDIANA del gruppo sopra +{SOGLIA:.2f}: "
          f"**{len(solide)}**")
    una_sola = g[g["righe"] == 1]
    print(f"   di queste, sostenute da UNA SOLA riga: **{len(una_sola)}**")

    # la distribuzione degli excess: dove sta il grosso
    print(f"\n   distribuzione di excess su tutto il registro")
    for lo, hi in [(-np.inf, -3), (-3, -1), (-1, 0), (0, 1), (1, 3), (3, np.inf)]:
        m = ((ex > lo) & (ex <= hi)).sum()
        eti = f"{lo:+.0f} .. {hi:+.0f}".replace("-inf", " -oo").replace("+inf", " +oo")
        print(f"      {eti:>16}  {m:>5}  {m / ex.notna().sum():>6.1%}")
    print(f"      {'mediana':>16}  {ex.median():>+5.2f}")
    print(f"      {'quota positiva':>16}  {(ex > 0).sum() / ex.notna().sum():>6.1%}")

    print(f"\n{'=' * 100}\n   ESITO DEL CONTROLLO\n{'=' * 100}")
    print(f"   La predizione dice: nessun numero superstite e' un margine di")
    print(f"   strategia. Il controllo automatico produce la lista esaustiva dei")
    print(f"   {len(g)} gruppi da esaminare a mano nel report. La falsificazione")
    print(f"   scatta solo se UNO di essi non e' contraddetto dai giri successivi.")

    lab.log_trials([dict(round=ROUND, hypothesis="L3 report finale",
                         config=f"scan excess>=+{SOGLIA}", window="registro",
                         sharpe="", irr="", bh_irr="", excess="",
                         n_obs=len(reg), note=f"{len(g)} gruppi da esaminare")])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

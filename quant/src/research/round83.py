"""Giro 83 — O5: il tasso di cambio fra alfa lordo e margine netto.

VOCE DELLA CODA, verbatim (committata al giro 80):

O5 — Il tasso di cambio fra alfa lordo e margine netto
  La scomposizione del giro 80 ha mostrato che nel train il candidato aveva 6,50
  punti di alfa lordo e ne consegnava 1,18, con una zavorra di 6,01 contro 0,69
  del benchmark. Ma quel differenziale di 5,32 punti NON e' un'aliquota: mescola
  la tassa sulla ROTAZIONE con la tassa sull'AVER GUADAGNATO DI PIU'. Separarle
  produce il numero piu' operativo che il progetto possa dare: quanti punti di
  alfa lordo servono per battere il benchmark di un punto netto, in funzione della
  rotazione.
  Da misurare, sul solo 1969-2009: una griglia di flussi SINTETICI costruiti sopra
  il benchmark equal-weight annuale, con alfa lordo costante imposto a 0/1/2/4/6/8
  punti l'anno e rotazione imposta a 0,2x/0,5x/0,9x/1,1x/2x/3,5x/6x (quattordici
  combinazioni x sei livelli di alfa = 42 celle, tutte pre-dichiarate, nessuna
  selezione). Per ogni cella, il margine netto di IRR. Da li' la CURVA DEL TASSO
  DI CAMBIO "alfa lordo richiesto per +1,00 netto" in funzione della rotazione, e
  il salto attraverso la soglia del 100%.
  PREDIZIONE: il tasso di cambio e' FORTEMENTE NON LINEARE nella rotazione e
  DISCONTINUO ALLA SOGLIA. Sotto 1,0x serve MENO DI 2 PUNTI di alfa lordo per
  farne uno netto; sopra 1,0x ne servono PIU' DI 3; e a 3,5x — la rotazione del
  candidato — ne servono FRA 4 E 6, coerente con i 6,50 -> 1,18 misurati al giro
  80. Il salto attraverso la soglia vale ALMENO 1,0 PUNTO di alfa richiesto, cioe'
  e' piu' grande di qualunque effetto di secondo ordine misurato nel progetto.
  FALSIFICATA SE: il tasso di cambio e' QUASI LINEARE nella rotazione, cioe' il
  rapporto fra la richiesta a 3,5x e quella a 0,5x sta SOTTO 2 — OPPURE se il
  salto alla soglia vale MENO DI 0,5 PUNTI.

============ DUE COSE DICHIARATE PRIMA DI ESEGUIRE ============

1. UN ERRORE ARITMETICO NELLA VOCE. Dice "quattordici combinazioni x sei livelli
   di alfa = 42 celle", ma le rotazioni elencate sono SETTE e 14 x 6 fa 84, non
   42. Il totale dichiarato (42) e' coerente con 7 x 6, non con 14 x 6. Uso la
   griglia che il totale implica — sette rotazioni x sei alfa — e non aggiungo
   rotazioni che la voce non elenca.

2. COME SI IMPONE L'ALFA. Il flusso sintetico e' il benchmark moltiplicato per un
   alfa geometrico costante: r_synth = (1 + r_bench)(1 + a_mensile) - 1 con
   a_mensile = (1 + a/100)^(1/12) - 1. Cosi' "alfa lordo = a punti l'anno" e' vero
   per costruzione e non dipende dal livello dei rendimenti. Sopra ci metto la
   rotazione imposta tau: costo di transazione tau/12 x COST_ROUND_TRIP al mese, e
   realize_frac = tau/12, che e' quello che il motore fiscale usa per decidere
   quanto si realizza e se scatta il 52%. L'alfa e' quindi LORDO di costi e
   imposte, che e' la lettura naturale di "alfa lordo".

   Il benchmark contro cui si misura il margine e' l'equal-weight annuale VERO,
   con la sua rotazione vera (0,07x) e la sua aliquota (33%). Non una versione
   sintetica: altrimenti il tasso di cambio misurerebbe se stesso.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from research import lab, bench as B
from research.round76 import simula

ROUND = 83
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
MESE_BENCH = 10
ALFA = (0.0, 1.0, 2.0, 4.0, 6.0, 8.0)
ROTAZ = (0.2, 0.5, 0.9, 1.1, 2.0, 3.5, 6.0)
BERSAGLIO = 1.00


def main():
    ind_g = dataio.ff_ind49_daily().dropna(axis=1, how="all").dropna()
    ind_g = ind_g[ind_g.index.year <= FINE]
    ind_m = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind_m = ind_m[ind_m.index.year <= FINE]
    ind_m.index = pd.DatetimeIndex(ind_m.index).to_period("M").to_timestamp("M")
    ind_m = ind_m[ind_g.columns]
    rf = dataio.ff_factors_monthly()["RF"]
    rf.index = pd.DatetimeIndex(rf.index).to_period("M").to_timestamp("M")

    print(f"{'=' * 104}\nO5 — quanti punti di alfa lordo servono per farne uno "
          f"netto\n{'=' * 104}")

    W = pd.DataFrame(0.0, index=ind_m.index, columns=ind_m.columns)
    W.loc[W.index.month == MESE_BENCH] = 1.0 / ind_m.shape[1]
    net_b, turn_b = simula(ind_g, W, 0)
    idx = net_b.dropna().index
    net_b, turn_b = net_b.reindex(idx), turn_b.reindex(idx)
    rfx = rf.reindex(idx).fillna(0.0)
    bench = B.eval_stream("x", net_b, rfx, turn_b)

    print(f"   Benchmark: equal-weight annuale, rotazione {bench['turn']:.3f}x, "
          f"aliquota {bench['rate_ref']}%, IRR {bench['irr_ref']:.2f}%.")
    print(f"   Griglia: {len(ROTAZ)} rotazioni × {len(ALFA)} alfa = "
          f"{len(ROTAZ) * len(ALFA)} celle, tutte pre-dichiarate.\n")

    def cella(a, tau):
        am = (1.0 + a / 100.0) ** (1.0 / 12.0) - 1.0
        lordo = (1.0 + net_b) * (1.0 + am) - 1.0
        tm = pd.Series(tau / 12.0, index=idx)
        netto = lordo - tm * C.COST_ROUND_TRIP
        r = B.eval_stream("x", netto, rfx, tm)
        return r["irr_ref"] - bench["irr_ref"], r["rate_ref"], r["turn"]

    print(f"   MARGINE NETTO (punti di IRR) per alfa lordo × rotazione")
    print(f"   {'rotaz.':<10}{'aliq.':>7}"
          + "".join(f"{'a=' + str(int(a)):>9}" for a in ALFA))
    print("   " + "-" * 72)
    tab = {}
    for tau in ROTAZ:
        riga = []
        aliq = None
        for a in ALFA:
            m, aliq, _ = cella(a, tau)
            riga.append(m)
        tab[tau] = riga
        print(f"   {str(tau) + 'x':<10}{aliq:>6}%"
              + "".join(f"{v:>+9.2f}" for v in riga))

    # ------------------------------------------- la curva del tasso di cambio
    def richiesto(riga):
        """alfa lordo che porta il margine a +1,00, per interpolazione lineare."""
        for i in range(len(ALFA) - 1):
            if riga[i] <= BERSAGLIO <= riga[i + 1]:
                d = riga[i + 1] - riga[i]
                if d <= 0:
                    continue
                return ALFA[i] + (BERSAGLIO - riga[i]) / d * (ALFA[i + 1] - ALFA[i])
        if riga[-1] < BERSAGLIO:      # estrapolo dall'ultimo segmento
            d = (riga[-1] - riga[-2]) / (ALFA[-1] - ALFA[-2])
            return ALFA[-1] + (BERSAGLIO - riga[-1]) / d if d > 0 else np.nan
        return np.nan

    print(f"\n{'=' * 104}\n   LA CURVA DEL TASSO DI CAMBIO\n{'=' * 104}")
    print(f"   {'rotazione':<12}{'aliquota':>10}"
          f"{'alfa lordo per +1,00 netto':>30}{'per +1 punto':>16}")
    print("   " + "-" * 70)
    req = {}
    for tau in ROTAZ:
        r = richiesto(tab[tau])
        req[tau] = r
        aliq = 52 if tau > 1.0 else 33
        stella = " (estrapolato)" if r > ALFA[-1] else ""
        print(f"   {str(tau) + 'x':<12}{aliq:>9}%{r:>26.2f}{stella:<14}"
              f"{r:>10.2f}×")

    salto = req[1.1] - req[0.9]
    rapp = req[3.5] / req[0.5] if req[0.5] > 0 else np.inf
    print(f"\n   **salto attraverso la soglia del 100%** (0,9× → 1,1×): "
          f"{salto:+.2f} punti di alfa richiesto")
    print(f"   rapporto fra la richiesta a 3,5× e quella a 0,5×: "
          f"**{rapp:.2f}×**")
    print(f"   controllo con il giro 80: il candidato aveva 6,50 di alfa lordo a "
          f"3,28× e ha reso +1,18;")
    print(f"   qui a 3,5× per +1,00 ne servono {req[3.5]:.2f}.")

    # ------------------------------------------------------------- verdetto
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: sotto 1,0× servono MENO DI 2 punti; sopra 1,0× PIU' DI "
          f"3; a 3,5× FRA 4 E 6;")
    print(f"   il salto alla soglia vale ALMENO 1,0 punto.")
    print(f"   FALSIFICATA se il rapporto 3,5×/0,5× sta SOTTO 2, oppure se il "
          f"salto vale MENO DI 0,5.\n")
    sotto = all(req[t] < 2.0 for t in (0.2, 0.5, 0.9))
    sopra = all(req[t] > 3.0 for t in (1.1, 2.0, 3.5, 6.0))
    c35 = 4.0 <= req[3.5] <= 6.0
    salto_ok = salto >= 1.0
    print(f"   sotto 1,0× serve meno di 2   : {'SI' if sotto else 'NO'}"
          f"   ({', '.join(f'{t}x {req[t]:.2f}' for t in (0.2, 0.5, 0.9))})")
    print(f"   sopra 1,0× servono più di 3  : {'SI' if sopra else 'NO'}"
          f"   ({', '.join(f'{t}x {req[t]:.2f}' for t in (1.1, 2.0, 3.5, 6.0))})")
    print(f"   a 3,5× fra 4 e 6             : {'SI' if c35 else 'NO'}"
          f"   ({req[3.5]:.2f})")
    print(f"   salto alla soglia ≥ 1,0      : {'SI' if salto_ok else 'NO'}"
          f"   ({salto:+.2f})")
    fals = (rapp < 2.0) or (salto < 0.5)
    print(f"\n   -> ipotesi O5 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    if not fals:
        manca = [x for x, ok in (("sotto 1,0×", sotto), ("sopra 1,0×", sopra),
                                 ("a 3,5×", c35), ("salto ≥ 1,0", salto_ok))
                 if not ok]
        if manca:
            print(f"      (confermata sul ramo che falsifica; clausole "
                  f"descrittive sbagliate: {', '.join(manca)})")

    pd.DataFrame({f"a={a}": [tab[t][i] for t in ROTAZ]
                  for i, a in enumerate(ALFA)},
                 index=[f"{t}x" for t in ROTAZ]).to_csv(OUT / "round83_o5.csv")
    lab.log_trials([dict(round=ROUND, hypothesis="O5 tasso di cambio",
                         config=f"alfa={a} rot={t}", window=f"1969-{FINE}",
                         sharpe="", irr="", bh_irr=bench["irr_ref"],
                         excess=tab[t][i], n_obs=len(idx),
                         note=f"aliq={52 if t > 1.0 else 33}")
                    for t in ROTAZ for i, a in enumerate(ALFA)])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

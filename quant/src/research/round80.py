"""Giro 80 — O2: da dove vengono i 2,13 punti fra train e holdout.

VOCE DELLA CODA, verbatim (committata al giro 78):

O2 — Da dove vengono i 2,13 punti fra train e holdout
  Il margine passa da +1,18 a -0,95. Tre cause candidate, mai separate: il PREMIO
  LORDO che si assottiglia (13,65% contro 13,34% nell'holdout: +0,31 — quanto era
  nel train?), la ROTAZIONE che sale da 3,284x a 3,804x dentro la stessa aliquota,
  e il BENCHMARK che migliora (l'equal-weight annuale rende 10,84% nell'holdout
  contro 10,09% nel train).
  Da misurare, sul solo train per la parte stimata e leggendo dall'holdout solo i
  numeri GIA' STAMPATI al giro 78 (nessuna nuova interrogazione del campione
  bruciato): la scomposizione del divario in (a) alfa lordo, (b) costo della
  rotazione aggiuntiva, (c) livello del benchmark.
  PREDIZIONE: la componente dominante e' (a) L'ALFA LORDO, che vale OLTRE LA META'
  dei 2,13 punti; la rotazione aggiuntiva vale MENO DI 0,3 punti, perche' il
  candidato era gia' al 52% in entrambi i periodi e mezza rotazione in piu' su una
  base gia' tassata al massimo costa poco; il benchmark migliore vale il resto.
  FALSIFICATA SE: la rotazione aggiuntiva spiega PIU' DI 0,5 PUNTI — nel qual caso
  il gradino fiscale ha un secondo ordine che il giro 66 non aveva visto — OPPURE
  se il benchmark spiega piu' dell'alfa, cioe' se il candidato non ha perso: e'
  stato superato.

============ UN DOPPIO CONTEGGIO NELLA VOCE, DICHIARATO PRIMA DI ESEGUIRE ============

La voce elenca tre cause, ma (a) e (c) SONO LA STESSA COSA GUARDATA DUE VOLTE.
L'alfa lordo e' per definizione CAGR_candidato - CAGR_benchmark: se il benchmark
migliora e il candidato no, l'alfa lordo si assottiglia. Non sono due contributi
che si sommano, sono il minuendo e il sottraendo della stessa differenza.

Non riscrivo la voce. La misuro cosi' com'e', e sciolgo il doppio conteggio nel
modo che la clausola di falsificazione rende obbligatorio — quella clausola chiede
di distinguere "il candidato ha perso" da "il candidato e' stato superato", e la
distinzione esiste eccome:

    Delta(alfa lordo) = [CAGR_cand_hold - CAGR_cand_train]      <- il candidato cade
                      - [CAGR_bench_hold - CAGR_bench_train]    <- il benchmark sale

Le due meta' di Delta(alfa) sono le due cause (a) e (c) della voce, e la clausola
di falsificazione chiede quale delle due e' piu' grande. Cosi' la domanda ha
risposta e il doppio conteggio sparisce.

==================== LA SCOMPOSIZIONE, DEFINITA PRIMA DI GUARDARE ====================

Il margine M = IRR_cand - IRR_bench si scrive in modo ESATTAMENTE additivo come

    M = (CAGR_cand - CAGR_bench)  -  (CAGR_cand - IRR_cand)  +  (CAGR_bench - IRR_bench)
      =        alfa lordo         -       zavorra_cand        +      zavorra_bench

dove la "zavorra" e' tutto cio' che sta fra il lordo time-weighted e il netto
money-weighted: imposte, costi, e la forma dei cashflow del PAC. Quindi

    Delta M = Delta(alfa) - Delta(zavorra_cand) + Delta(zavorra_bench)

e i tre pezzi sommano a -2,13 per costruzione, senza residui inventati. Dentro
Delta(zavorra_cand) sta la rotazione aggiuntiva, che isolo a parte con un
controfattuale MISURATO SUL SOLO TRAIN: quanto sarebbe costato al candidato, nel
train, ruotare 3,804x invece di 3,284x.

I numeri dell'holdout sono COSTANTI COPIATE dal giro 78 (`rounds/round78.txt`),
non ricalcolate. Il campione bruciato non viene interrogato di nuovo.
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
from research.round76 import simula, pesi_top

ROUND = 80
OUT = Path(__file__).resolve().parents[2] / "out"
FINE_TRAIN = 2009
K_CAND, TOP_CAND = 3, 5
MESE_BENCH = 1                     # gennaio: il calendario della tabella del giro 78

# ---- COSTANTI COPIATE DAL GIRO 78, non ricalcolate (rounds/round78.txt) ----
H_CAND_IRR = 9.89                  # IRR netta del candidato, aliquota 52%
H_BENCH_IRR = 10.83                # IRR netta del benchmark gennaio, aliquota 33%
H_CAND_CAGR = 13.65                # CAGR lordo del candidato
H_BENCH_CAGR = 13.34               # CAGR lordo del benchmark gennaio
H_CAND_ROT = 3.804
H_BENCH_ROT = 0.06
H_MARGINE_MEDIANO = -0.95          # mediana sui dodici calendari


def main():
    ind_g = dataio.ff_ind49_daily().dropna(axis=1, how="all").dropna()
    ind_g = ind_g[ind_g.index.year <= FINE_TRAIN]
    ind_m = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind_m = ind_m[ind_m.index.year <= FINE_TRAIN]
    ind_m.index = pd.DatetimeIndex(ind_m.index).to_period("M").to_timestamp("M")
    ind_m = ind_m[ind_g.columns]
    rf = dataio.ff_factors_monthly()["RF"]
    rf.index = pd.DatetimeIndex(rf.index).to_period("M").to_timestamp("M")

    print(f"{'=' * 104}\nO2 — da dove vengono i 2,13 punti fra train e holdout\n"
          f"{'=' * 104}")
    print(f"   Train {ind_g.index[0].year}-{FINE_TRAIN}, misurato qui. "
          f"Holdout 2010-2026, **solo numeri copiati dal giro 78**.\n")

    def irr(net, turn):
        i = net.dropna().index
        return B.eval_stream("x", net.reindex(i), rf.reindex(i).fillna(0.0),
                             turn.reindex(i))

    score = (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(K_CAND)
    net_c, turn_c = simula(ind_g, pesi_top(score, TOP_CAND), 0)
    cand = irr(net_c, turn_c)

    W = pd.DataFrame(0.0, index=ind_m.index, columns=ind_m.columns)
    W.loc[W.index.month == MESE_BENCH] = 1.0 / ind_m.shape[1]
    net_b, turn_b = simula(ind_g, W, 0)
    bench = irr(net_b, turn_b)

    # --------------------------------------------------- le due colonne, a specchio
    t_cand_irr, t_bench_irr = cand["irr_ref"], bench["irr_ref"]
    t_cand_cagr, t_bench_cagr = cand["cagr"], bench["cagr"]
    m_train = t_cand_irr - t_bench_irr
    m_hold = H_CAND_IRR - H_BENCH_IRR

    print(f"   {'':<30}{'train':>12}{'holdout':>12}{'variazione':>14}")
    print("   " + "-" * 68)
    for et, a, b in (("CAGR lordo candidato", t_cand_cagr, H_CAND_CAGR),
                     ("CAGR lordo benchmark", t_bench_cagr, H_BENCH_CAGR),
                     ("IRR netta candidato", t_cand_irr, H_CAND_IRR),
                     ("IRR netta benchmark", t_bench_irr, H_BENCH_IRR),
                     ("rotazione candidato", cand["turn"], H_CAND_ROT),
                     ("rotazione benchmark", bench["turn"], H_BENCH_ROT)):
        print(f"   {et:<30}{a:>12.2f}{b:>12.2f}{b - a:>+14.2f}")
    print(f"   {'MARGINE':<30}{m_train:>+12.2f}{m_hold:>+12.2f}"
          f"{m_hold - m_train:>+14.2f}")

    # ------------------------------------------------ la scomposizione additiva
    alfa_t = t_cand_cagr - t_bench_cagr
    alfa_h = H_CAND_CAGR - H_BENCH_CAGR
    zav_c_t = t_cand_cagr - t_cand_irr
    zav_c_h = H_CAND_CAGR - H_CAND_IRR
    zav_b_t = t_bench_cagr - t_bench_irr
    zav_b_h = H_BENCH_CAGR - H_BENCH_IRR
    d_alfa = alfa_h - alfa_t
    d_zc = zav_c_h - zav_c_t
    d_zb = zav_b_h - zav_b_t
    tot = d_alfa - d_zc + d_zb

    print(f"\n{'=' * 104}\n   LA SCOMPOSIZIONE\n{'=' * 104}")
    print(f"   {'componente':<34}{'train':>10}{'holdout':>10}"
          f"{'contributo al divario':>24}")
    print("   " + "-" * 80)
    print(f"   {'alfa lordo (cand − bench)':<34}{alfa_t:>+10.2f}{alfa_h:>+10.2f}"
          f"{d_alfa:>+24.2f}")
    print(f"   {'zavorra del candidato':<34}{zav_c_t:>10.2f}{zav_c_h:>10.2f}"
          f"{-d_zc:>+24.2f}")
    print(f"   {'zavorra del benchmark':<34}{zav_b_t:>10.2f}{zav_b_h:>10.2f}"
          f"{d_zb:>+24.2f}")
    print("   " + "-" * 80)
    print(f"   {'TOTALE':<34}{'':>10}{'':>10}{tot:>+24.2f}"
          f"   (divario vero {m_hold - m_train:+.2f})")

    # ------------------------------- le due meta' dell'alfa: chi cade, chi sale
    d_cand_g = H_CAND_CAGR - t_cand_cagr
    d_bench_g = H_BENCH_CAGR - t_bench_cagr
    print(f"\n   Le due meta' dell'alfa — la domanda della clausola di "
          f"falsificazione:")
    print(f"   {'il CANDIDATO cade':<34}{d_cand_g:>+10.2f}   punti di CAGR lordo")
    print(f"   {'il BENCHMARK sale':<34}{d_bench_g:>+10.2f}   punti di CAGR lordo")
    chi = ("il candidato ha PERSO" if abs(d_cand_g) > abs(d_bench_g)
           else "il candidato e' stato SUPERATO")
    print(f"   -> {chi}")

    # --------------------------- il controfattuale sulla rotazione, SOLO TRAIN
    f = H_CAND_ROT / cand["turn"]
    extra_cost = (f - 1.0) * turn_c * C.COST_ROUND_TRIP
    cand_rot = irr(net_c - extra_cost.reindex(net_c.index).fillna(0.0),
                   turn_c * f)
    costo_rot = cand_rot["irr_ref"] - t_cand_irr
    print(f"\n{'=' * 104}\n   IL CONTROFATTUALE SULLA ROTAZIONE (misurato sul solo "
          f"train)\n{'=' * 104}")
    print(f"   Domanda: quanto sarebbe costato al candidato, NEL TRAIN, ruotare "
          f"{H_CAND_ROT:.3f}x invece di {cand['turn']:.3f}x?")
    print(f"   {'rotazione':<34}{cand['turn']:>10.3f}x → "
          f"{cand_rot['turn']:>7.3f}x   (fattore {f:.4f})")
    print(f"   {'IRR netta':<34}{t_cand_irr:>10.2f}% → "
          f"{cand_rot['irr_ref']:>7.2f}%")
    print(f"   {'aliquota':<34}{cand['rate_ref']:>10}% → "
          f"{cand_rot['rate_ref']:>7}%   (nessun salto di scaglione)")
    print(f"   **costo della rotazione aggiuntiva: {costo_rot:+.2f} punti**"
          f"   (previsto sotto 0,30; falsifica sopra 0,50)")

    # -------------------------------------------------------------- verdetto
    quota_alfa = abs(d_alfa) / abs(m_hold - m_train)
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: (a) l'alfa lordo e' dominante e vale OLTRE LA META' dei "
          f"2,13 punti; la rotazione")
    print(f"   aggiuntiva vale MENO DI 0,30; il benchmark il resto.")
    print(f"   FALSIFICATA se la rotazione spiega PIU' DI 0,50, oppure se il "
          f"benchmark spiega piu' dell'alfa.\n")
    dom = abs(d_alfa) > abs(m_hold - m_train) / 2.0
    rot_ko = abs(costo_rot) > 0.50
    rot_ok = abs(costo_rot) < 0.30
    sup = abs(d_bench_g) > abs(d_cand_g)
    print(f"   alfa lordo oltre la meta'   : {'SI' if dom else 'NO'}"
          f"   ({d_alfa:+.2f} su {m_hold - m_train:+.2f}, "
          f"cioe' il {quota_alfa:.0%})")
    print(f"   rotazione sotto 0,30        : {'SI' if rot_ok else 'NO'}"
          f"   ({costo_rot:+.2f})")
    print(f"   rotazione sopra 0,50 → fals.: {'SI' if rot_ko else 'no'}")
    print(f"   benchmark spiega piu' dell'alfa → fals.: "
          f"{'SI' if sup else 'no'}   (cand {d_cand_g:+.2f} contro "
          f"bench {d_bench_g:+.2f})")
    fals = rot_ko or sup
    print(f"\n   -> ipotesi O2 {'FALSIFICATA' if fals else 'CONFERMATA'}")

    righe = [("alfa lordo", d_alfa), ("zavorra candidato", -d_zc),
             ("zavorra benchmark", d_zb), ("di cui rotazione", costo_rot)]
    pd.DataFrame(righe, columns=["componente", "punti"]).to_csv(
        OUT / "round80_o2.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="O2 scomposizione train-holdout",
                         config=n, window=f"1969-{FINE_TRAIN} vs 2010-2026",
                         sharpe="", irr="", bh_irr="", excess=v,
                         n_obs=len(ind_g), note="scomposizione additiva")
                    for n, v in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

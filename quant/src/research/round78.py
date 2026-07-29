"""Giro 78 — N1: L'APERTURA DELL'HOLDOUT. Una volta sola.

VOCE DELLA CODA, verbatim (committata al giro 77, prima di guardare qualunque
cosa del 2010-2026):

N1 — L'holdout 2010-2026, aperto una volta sola, sul momentum 12-3 top-5 mensile
  Il candidato ha passato tutti e quattro i cancelli della regola del giro 72 —
  G1 mediana +1,18 su dodici calendari, G2 DSR 0,9907, G3 quota 93,1% con mediana
  +2,23, G4 per costruzione. La regola dice che a questo punto l'holdout si apre
  su quello solo, una volta sola, e il risultato si registra qualunque sia.
  REGOLE DELL'APERTURA, fissate qui e non modificabili dopo:
   - un solo candidato: momentum 12-3 top-5 mensile, 49 settori, motore
     giornaliero del giro 73, nessun parametro ritoccato;
   - un solo benchmark: equal-weight annuale con la rotazione vera, e si riporta
     la MEDIANA sui dodici calendari, non un mese scelto;
   - una sola finestra: 2010-01-01 -> fine dei dati. Non si scelgono
     sottoperiodi, non si tolgono anni, non si "esclude il 2020";
   - NESSUNA RIOTTIMIZZAZIONE, nemmeno se il risultato e' brutto;
   - si riportano insieme margine, rotazione, aliquota applicata, drawdown e il
     profilo per finestre decennali dentro l'holdout.
  PREDIZIONE: il margine sull'holdout e' NEGATIVO, fra -3 e 0 punti. Tre ragioni:
  le uniche due finestre decennali negative del train sono le ultime due
  (1999-2008 a -1,23, 2000-2009 a -3,39); il giro 59 ha misurato che allungando
  l'orizzonte tutti i candidati peggiorano; il giro 76 ha mostrato che lo skip e'
  un parametro libero da 3,94-4,27 punti. Prevedo inoltre che la ROTAZIONE resti
  sopra 1,0x (aliquota 52%) e che il DRAWDOWN del candidato sia PEGGIORE di quello
  del benchmark.
  FALSIFICATA SE: il margine sull'holdout e' POSITIVO E SOPRA +1,00 punto come
  mediana sui dodici calendari. OPPURE se e' positivo ma sotto +1,00: in quel caso
  non c'e' ne' conferma ne' smentita netta, e va registrato come tale invece di
  essere arrotondato verso la tesi che preferisco.
  Dopo N1 l'holdout e' BRUCIATO: qualunque cosa dica, non si riapre.

===================== COME E' MISURATO, DICHIARATO PRIMA =====================

La simulazione gira sulla serie INTERA e poi si affetta al 2010-2026, che e'
esattamente il metodo con cui il giro 72 ha misurato le finestre decennali di G3
(`irr_finestra`). Non e' un modo di sbirciare: la simulazione e' deterministica
dato il segnale e non stima nessun parametro. Serve a due cose:
  1. il segnale ha bisogno di quattordici mesi di riscaldamento (rolling 11 +
     skip 3), e il progetto ha gia' pagato una volta l'errore di calcolare gli
     indicatori sulla finestra affettata invece che sulla serie intera;
  2. senza avviamento, il benchmark con calendario di ribilanciamento a dicembre
     starebbe in cassa per undici mesi del 2010 e quello di gennaio no — un
     artefatto asimmetrico fra i dodici calendari, cioe' esattamente cio' che la
     mediana sui calendari serve a evitare.

Il codice del motore e' importato dal giro 76 senza modifiche.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import dataio
from research import lab, bench as B
from research.round76 import simula, pesi_top

ROUND = 78
OUT = Path(__file__).resolve().parents[2] / "out"

INIZIO_HOLDOUT = 2010
FINE_TRAIN = 2009
K_CAND, TOP_CAND = 3, 5
LUNG = 10
MESI = ["gen", "feb", "mar", "apr", "mag", "giu",
        "lug", "ago", "set", "ott", "nov", "dic"]


def main():
    ind_g = dataio.ff_ind49_daily().dropna(axis=1, how="all").dropna()
    ind_m = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind_m.index = pd.DatetimeIndex(ind_m.index).to_period("M").to_timestamp("M")
    ind_m = ind_m[ind_g.columns]
    rf = dataio.ff_factors_monthly()["RF"]
    rf.index = pd.DatetimeIndex(rf.index).to_period("M").to_timestamp("M")

    print(f"{'=' * 104}")
    print(f"N1 — APERTURA DELL'HOLDOUT. Momentum 12-{K_CAND} top-{TOP_CAND} "
          f"mensile, 49 settori.")
    print(f"{'=' * 104}")
    print(f"   Serie completa {ind_g.index[0].date()} → {ind_g.index[-1].date()}."
          f"   Holdout: {INIZIO_HOLDOUT}-01-01 → fine dei dati.")
    print(f"   Una volta sola. Nessuna riottimizzazione. Il risultato si registra "
          f"qualunque sia.\n")

    # ------------------------------------------------ simulazioni, serie intera
    score = (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(K_CAND)
    net_c, turn_c = simula(ind_g, pesi_top(score, TOP_CAND), 0)

    n = ind_m.shape[1]
    bench_serie = {}
    for m in range(1, 13):
        W = pd.DataFrame(0.0, index=ind_m.index, columns=ind_m.columns)
        W.loc[W.index.month == m] = 1.0 / n
        bench_serie[m] = simula(ind_g, W, 0)

    def valuta(net, turn, a, b):
        i = net.index[(net.index.year >= a) & (net.index.year <= b)]
        s = net.reindex(i).dropna()
        if len(s) < 24:
            return None
        return B.eval_stream("x", s, rf.reindex(s.index).fillna(0.0),
                             turn.reindex(s.index))

    a_h, b_h = INIZIO_HOLDOUT, int(ind_g.index[-1].year)
    cand_h = valuta(net_c, turn_c, a_h, b_h)
    cand_t = valuta(net_c, turn_c, 1969, FINE_TRAIN)

    # ---------------------------------------------------------- il risultato
    print(f"   {'=' * 98}")
    print(f"   IL MARGINE SULL'HOLDOUT {a_h}-{b_h}, calendario per calendario")
    print(f"   {'=' * 98}")
    bh, marg = {}, {}
    for m in range(1, 13):
        bh[m] = valuta(*bench_serie[m], a_h, b_h)
        marg[m] = cand_h["irr_ref"] - bh[m]["irr_ref"]
    print("   " + "".join(f"{MESI[m - 1]:>7}" for m in range(1, 13)))
    print("   " + "".join(f"{bh[m]['irr_ref']:>7.2f}" for m in range(1, 13)))
    print("   " + "".join(f"{marg[m]:>+7.2f}" for m in range(1, 13)))
    med = float(np.median(list(marg.values())))
    pos = sum(1 for v in marg.values() if v > 0)
    print(f"\n   candidato IRR netta        : {cand_h['irr_ref']:>8.2f}%"
          f"   (aliquota {cand_h['rate_ref']}%)")
    print(f"   benchmark, mediana dei 12  : "
          f"{float(np.median([bh[m]['irr_ref'] for m in bh])):>8.2f}%")
    print(f"   **MARGINE, MEDIANA DEI 12**: {med:>+8.2f} punti"
          f"   (positivo in {pos}/12 calendari, "
          f"min {min(marg.values()):+.2f} max {max(marg.values()):+.2f})")

    # ------------------------------------------------- rotazione, aliquota, DD
    mm = min(marg, key=lambda m: abs(marg[m] - med))
    b_med = bh[mm]
    print(f"\n   {'':<26}{'candidato':>14}{'benchmark':>14}   (calendario "
          f"mediano: {MESI[mm - 1]})")
    print("   " + "-" * 58)
    for et, kc, kb in (("rotazione /anno", cand_h["turn"], b_med["turn"]),
                       ("aliquota applicata", cand_h["rate_ref"], b_med["rate_ref"]),
                       ("CAGR lordo", cand_h["cagr"], b_med["cagr"]),
                       ("volatilita'", cand_h["vol"], b_med["vol"]),
                       ("Sharpe", cand_h["sharpe"], b_med["sharpe"]),
                       ("max drawdown", cand_h["dd"], b_med["dd"]),
                       ("IRR netta 33%", cand_h["irr"], b_med["irr"]),
                       ("IRR netta 52%", cand_h["irr52"], b_med["irr52"])):
        print(f"   {et:<26}{kc:>14.2f}{kb:>14.2f}")

    # -------------------------------------- profilo decennale DENTRO l'holdout
    print(f"\n   FINESTRE DECENNALI DENTRO L'HOLDOUT")
    print("   " + "-" * 58)
    prof = []
    for y in range(a_h, b_h - LUNG + 2):
        x = valuta(net_c, turn_c, y, y + LUNG - 1)
        q = valuta(*bench_serie[mm], y, y + LUNG - 1)
        if x and q:
            prof.append((y, y + LUNG - 1, x["irr_ref"] - q["irr_ref"]))
    if prof:
        print("   " + "".join(f"{p[0]:>8}" for p in prof))
        print("   " + "".join(f"{p[2]:>+8.2f}" for p in prof))
        vv = np.array([p[2] for p in prof])
        print(f"   quota positiva {float((vv > 0).mean()):.1%}   "
              f"mediana {float(np.median(vv)):+.2f}   "
              f"(nel train: 93,1% e +2,23)")
    else:
        print("   (holdout troppo corto per una finestra decennale completa)")

    # sottoperiodi quinquennali, per vedere DOVE
    print(f"\n   FINESTRE QUINQUENNALI DENTRO L'HOLDOUT (diagnostica, non un "
          f"criterio)")
    print("   " + "-" * 58)
    q5 = []
    for y in range(a_h, b_h - 4 + 1):
        x = valuta(net_c, turn_c, y, y + 4)
        q = valuta(*bench_serie[mm], y, y + 4)
        if x and q:
            q5.append((y, x["irr_ref"] - q["irr_ref"]))
    print("   " + "".join(f"{p[0]:>8}" for p in q5))
    print("   " + "".join(f"{p[1]:>+8.2f}" for p in q5))

    # ------------------------------------------------------ train contro holdout
    print(f"\n   {'=' * 98}")
    print(f"   TRAIN CONTRO HOLDOUT")
    print(f"   {'=' * 98}")
    marg_t = {}
    for m in range(1, 13):
        bt = valuta(*bench_serie[m], 1969, FINE_TRAIN)
        marg_t[m] = cand_t["irr_ref"] - bt["irr_ref"]
    med_t = float(np.median(list(marg_t.values())))
    print(f"   {'':<28}{'train 1969-2009':>18}{'holdout ' + str(a_h) + '-' + str(b_h):>18}")
    print("   " + "-" * 64)
    print(f"   {'IRR del candidato':<28}{cand_t['irr_ref']:>17.2f}%"
          f"{cand_h['irr_ref']:>17.2f}%")
    print(f"   {'margine (mediana 12 cal.)':<28}{med_t:>+17.2f} {med:>+17.2f} ")
    print(f"   {'rotazione':<28}{cand_t['turn']:>17.3f}x{cand_h['turn']:>17.3f}x")
    print(f"   {'aliquota':<28}{cand_t['rate_ref']:>17}%{cand_h['rate_ref']:>17}%")
    print(f"   {'max drawdown':<28}{cand_t['dd']:>17.2f}%{cand_h['dd']:>17.2f}%")

    # ------------------------------------------------------------- verdetto
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: margine NEGATIVO fra -3 e 0; rotazione sopra 1,0x "
          f"(aliquota 52%); drawdown")
    print(f"   del candidato PEGGIORE del benchmark.")
    print(f"   FALSIFICATA se il margine e' POSITIVO E SOPRA +1,00, oppure "
          f"positivo ma sotto +1,00 (esito")
    print(f"   intermedio, da registrare come tale).\n")
    negativo = med < 0
    dentro = -3.0 <= med <= 0.0
    sopra1 = med > 1.0
    intermedio = 0.0 < med <= 1.0
    print(f"   margine mediano            : {med:>+7.2f}"
          f"   negativo: {'SI' if negativo else 'NO'}"
          f"   dentro [-3, 0]: {'SI' if dentro else 'NO'}")
    print(f"   rotazione sopra 1,0x       : "
          f"{'SI' if cand_h['turn'] > 1.0 else 'NO'} ({cand_h['turn']:.3f}x, "
          f"aliquota {cand_h['rate_ref']}%)")
    print(f"   drawdown peggiore del bench: "
          f"{'SI' if cand_h['dd'] < b_med['dd'] else 'NO'} "
          f"({cand_h['dd']:.2f}% contro {b_med['dd']:.2f}%)")
    if sopra1:
        esito = "FALSIFICATA — il candidato batte il benchmark fuori campione"
    elif intermedio:
        esito = "FALSIFICATA (ramo intermedio) — positivo ma sotto +1,00"
    else:
        esito = "CONFERMATA" if dentro else "CONFERMATA nel segno, sbagliata nella taglia"
    print(f"\n   -> ipotesi N1 {esito}")
    print(f"\n   L'HOLDOUT E' ORA BRUCIATO. Non si riapre.")

    df = pd.DataFrame([dict(mese=m, bench=bh[m]["irr_ref"], margine=marg[m])
                       for m in range(1, 13)])
    df.to_csv(OUT / "round78_n1.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="N1 apertura holdout",
                         config=f"12-{K_CAND} top-{TOP_CAND} bench {MESI[m - 1]}",
                         window=f"{a_h}-{b_h}", sharpe=cand_h["sharpe"],
                         irr=cand_h["irr_ref"], bh_irr=bh[m]["irr_ref"],
                         excess=marg[m], n_obs=cand_h["n"],
                         note=f"HOLDOUT,med={med:.2f},rot={cand_h['turn']:.3f}")
                    for m in range(1, 13)])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

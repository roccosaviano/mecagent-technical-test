"""Giro 77 — M1: il 12-3 top-5 mensile contro i quattro cancelli, misurati tutti.

VOCE DELLA CODA, predizione verbatim (committata prima di eseguire):

M1 — Il 12-3 top-5 mensile contro i quattro cancelli, misurati tutti
  Nata al giro 76. E' la prima cella in settantasei giri che passa TRE cancelli
  su quattro della regola del giro 72: G1 con +1,18 di margine, G2 con DSR 0,9870
  e G4 per costruzione, essendo mensile. G3 NON e' mai stato misurato, e G1 e'
  stato misurato contro un benchmark su UN SOLO calendario - gennaio.
  Da misurare, sul motore giornaliero del giro 73, finestra 1969-2009:
  (a) il margine contro l'equal-weight annuale su TUTTI E DODICI i calendari del
      benchmark, prendendone la MEDIANA - e' quella che deve superare +1,00;
  (b) G3: extra positivo in >= 2/3 delle finestre decennali mobili E mediana
      degli extra > 0;
  (c) il DSR con var_sr stimata su una famiglia che contenga ANCHE LO SKIP
      (5 skip x 4 taglie = 20 celle, non 10).
  PREDIZIONE: (a) TIENE - la mediana resta SOPRA +1,00 e si sposta di MENO DI 0,3
  punti da +1,18, perche' il giro 68 ha misurato che l'ampiezza del calendario per
  un EQUAL-WEIGHT e' appena 0,14%. (b) FALLISCE: la quota di finestre decennali
  positive resta SOTTO i 2/3, perche' il candidato piu' vicino mai registrato si
  fermo' a 66,0% contro 66,7% e perche' il giro 59 ha mostrato che allungando
  l'orizzonte tutti i candidati peggiorano. (c) SCENDE MA REGGE: il DSR resta
  sopra 0,95.
  Esito atteso: tre cancelli su quattro, l'holdout resta sigillato.
  FALSIFICATA SE: il candidato passa TUTTI E QUATTRO i cancelli - nel qual caso
  l'holdout va aperto su quello solo, una volta sola - OPPURE se (a) cade, cioe'
  la mediana sui dodici calendari scende sotto +1,00.

===================== QUELLO CHE QUESTO GIRO NON E' =====================

Non e' un walk-forward, e non lo nascondo dietro il fatto che non ottimizza
niente: lo skip k=3 e' stato SCELTO GUARDANDO IL CAMPIONE INTERO 1969-2009, come
massimo di dieci celle, al giro 76. E' esattamente la situazione contro cui i
quattro cancelli esistono - G2 conta la selezione nel DSR, G3 chiede che il
vantaggio non sia concentrato in un pezzo di storia, G1 e G4 che non sia un
artefatto di calendario. Il giro misura i cancelli, non rivendica un
out-of-sample che non c'e'.

L'holdout 2010-2026 NON viene toccato qui nemmeno se il candidato passa: la
regola del giro 72 dice che l'apertura e' un ATTO SEPARATO.
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
from research.round76 import simula, pesi_top, pesi_ew_annuale

ROUND = 77
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
LUNG = 10

SKIP_FAM = (1, 2, 3, 4, 6)
TAGLIE_FAM = (3, 5, 10, 25)
K_CAND, TOP_CAND = 3, 5

G1_MARGINE = 1.00
G2_DSR = 0.95
G3_QUOTA = 2.0 / 3.0
G4_CALENDARI = 10


def main():
    ind_g = dataio.ff_ind49_daily().dropna(axis=1, how="all").dropna()
    ind_g = ind_g[ind_g.index.year <= FINE]
    ind_m = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind_m = ind_m[ind_m.index.year <= FINE]
    ind_m.index = pd.DatetimeIndex(ind_m.index).to_period("M").to_timestamp("M")
    ind_m = ind_m[ind_g.columns]
    rf = dataio.ff_factors_monthly()["RF"]
    rf.index = pd.DatetimeIndex(rf.index).to_period("M").to_timestamp("M")
    y0, y1 = ind_g.index[0].year, ind_g.index[-1].year

    print(f"{'=' * 104}\nM1 — il momentum 12-3 top-5 mensile contro i quattro "
          f"cancelli\n{'=' * 104}")
    print(f"   49 settori giornalieri, {y0}-{y1} ({len(ind_g)} giorni di borsa). "
          f"**Holdout 2010-2026 non toccato.**")
    print(f"   Soglie del giro 72: G1 >= {G1_MARGINE:.2f} come MEDIANA sui dodici "
          f"calendari del benchmark,")
    print(f"   G2 DSR > {G2_DSR}, G3 >= {G3_QUOTA:.1%} finestre decennali E "
          f"mediana > 0, G4 >= {G4_CALENDARI}/12.\n")

    def irr(net, turn):
        i = net.dropna().index
        r = B.eval_stream("x", net.reindex(i), rf.reindex(i).fillna(0.0),
                          turn.reindex(i))
        r["rot"] = float(turn.reindex(i).sum()) / (len(i) / 12)
        r["net"] = net.reindex(i)
        r["turn"] = turn.reindex(i)
        return r

    def irr_finestra(net, turn, a, b):
        i = net.index[(net.index.year >= a) & (net.index.year <= b)]
        s = net.reindex(i).dropna()
        if len(s) < 100:
            return None
        return B.eval_stream("x", s, rf.reindex(s.index).fillna(0.0),
                             turn.reindex(s.index))["irr_ref"]

    mom = {k: (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(k)
           for k in SKIP_FAM}

    # -------------------------------------------- il candidato, una volta sola
    cand = irr(*simula(ind_g, pesi_top(mom[K_CAND], TOP_CAND), 0))
    print(f"   candidato: momentum 12-{K_CAND} top-{TOP_CAND} mensile   "
          f"IRR {cand['irr_ref']:.2f}%   rotazione {cand['rot']:.3f}x   "
          f"aliquota {cand['rate_ref']}%")

    # ------------------------------------ (a) G1 sui dodici calendari del bench
    print(f"\n   (a) G1 — il margine contro l'equal-weight annuale, calendario "
          f"per calendario")
    print("   " + "-" * 88)
    mesi_nome = ["gen", "feb", "mar", "apr", "mag", "giu",
                 "lug", "ago", "set", "ott", "nov", "dic"]
    bench, marg = {}, {}
    for m in range(1, 13):
        Wew = pesi_ew_annuale(ind_m)
        Wew.loc[:] = 0.0
        Wew.loc[Wew.index.month == m] = 1.0 / ind_m.shape[1]
        bench[m] = irr(*simula(ind_g, Wew, 0))
        marg[m] = cand["irr_ref"] - bench[m]["irr_ref"]
    print("   " + "".join(f"{mesi_nome[m - 1]:>7}" for m in range(1, 13)))
    print(f"   {'bench':<0}" + "".join(f"{bench[m]['irr_ref']:>7.2f}"
                                       for m in range(1, 13)))
    print("   " + "".join(f"{marg[m]:>+7.2f}" for m in range(1, 13)))
    med_marg = float(np.median(list(marg.values())))
    amp_bench = max(b["irr_ref"] for b in bench.values()) - \
        min(b["irr_ref"] for b in bench.values())
    pos_cal = sum(1 for v in marg.values() if v > 0)
    print(f"\n   mediana del margine sui dodici calendari : {med_marg:>+7.2f}"
          f"   (gennaio da solo: {marg[1]:+.2f})")
    print(f"   ampiezza del BENCHMARK sui dodici calendari: {amp_bench:>7.2f}"
          f"   (giro 68 su equal-weight: 0,14)")
    print(f"   calendari con margine positivo             : {pos_cal:>7}/12")

    # il calendario mediano, per G3
    mm = min(marg, key=lambda m: abs(marg[m] - med_marg))
    print(f"   calendario mediano usato per G3            : "
          f"{mesi_nome[mm - 1]:>7}")

    # ---------------------------------------------------------- (b) G3
    spans = [(y, y + LUNG - 1) for y in range(y0 + 3, y1 - LUNG + 2)]
    ex = []
    for a, b in spans:
        x = irr_finestra(cand["net"], cand["turn"], a, b)
        q = irr_finestra(bench[mm]["net"], bench[mm]["turn"], a, b)
        if x is not None and q is not None:
            ex.append((a, b, x - q))
    vals = np.array([e[2] for e in ex])
    quota = float((vals > 0).mean())
    med_ex = float(np.median(vals))
    print(f"\n   (b) G3 — {len(ex)} finestre decennali mobili "
          f"({ex[0][0]}-{ex[0][1]} … {ex[-1][0]}-{ex[-1][1]})")
    print("   " + "-" * 88)
    for i in range(0, len(ex), 9):
        blocco = ex[i:i + 9]
        print("   " + "".join(f"{e[0]:>8}" for e in blocco))
        print("   " + "".join(f"{e[2]:>+8.2f}" for e in blocco))
    print(f"\n   quota di finestre positive : {quota:>6.1%}   "
          f"(soglia {G3_QUOTA:.1%})")
    print(f"   mediana degli extra        : {med_ex:>+6.2f}   (soglia > 0)")
    print(f"   peggiore / migliore        : {vals.min():+.2f} / {vals.max():+.2f}")

    # ------------------------------------- (c) G2 con la famiglia allargata
    print(f"\n   (c) G2 — DSR con var_sr su una famiglia che contiene anche lo "
          f"skip ({len(SKIP_FAM)}x{len(TAGLIE_FAM)} = "
          f"{len(SKIP_FAM) * len(TAGLIE_FAM)} celle)")
    print("   " + "-" * 88)
    srs, tab = [], {}
    for top in TAGLIE_FAM:
        riga = []
        for k in SKIP_FAM:
            r = cand if (k == K_CAND and top == TOP_CAND) else \
                irr(*simula(ind_g, pesi_top(mom[k], top), 0))
            e = r["net"] - rf.reindex(r["net"].index).fillna(0.0)
            srs.append(float(e.mean() / e.std(ddof=1)))
            riga.append(r["irr_ref"] - bench[mm]["irr_ref"])
        tab[top] = riga
    print(f"   {'margine per skip':<20}" + "".join(f"{'k=' + str(k):>9}"
                                                   for k in SKIP_FAM))
    for top in TAGLIE_FAM:
        print(f"   {'top-' + str(top):<20}"
              + "".join(f"{v:>+9.2f}" for v in tab[top]))
    amp_fam = max(max(v) for v in tab.values()) - min(min(v) for v in tab.values())
    print(f"   ampiezza dell'intera famiglia: {amp_fam:.2f} punti   "
          f"(il massimo e' {max(max(v) for v in tab.values()):+.2f})")

    var_fam = float(np.var(srs, ddof=1))
    var_10 = 0.000400        # la famiglia del giro 76, per confronto
    n_cum = lab.n_trials_so_far()
    d_new = lab.deflated_sharpe(cand["net"], n_cum, var_sr=var_fam, rf=rf)
    d_old = lab.deflated_sharpe(cand["net"], n_cum, var_sr=var_10, rf=rf)
    d_reg = lab.deflated_sharpe(cand["net"], n_cum, rf=rf)
    dsr = float(d_new["dsr"]) if np.isfinite(d_new["dsr"]) else 0.0
    print(f"\n   {'var_sr stimata su':<40}{'SR0/periodo':>13}{'DSR':>9}")
    print(f"   {'famiglia di 20 celle (questo giro)':<40}"
          f"{float(d_new['sr0']):>13.4f}{dsr:>9.4f}")
    print(f"   {'famiglia di 10 celle (giro 76)':<40}"
          f"{float(d_old['sr0']):>13.4f}{float(d_old['dsr']):>9.4f}")
    print(f"   {'registro intero (non credibile)':<40}"
          f"{float(d_reg['sr0']):>13.4f}{float(d_reg['dsr']):>9.4f}")
    print(f"   N cumulato = {n_cum}   Sharpe annualizzato del candidato "
          f"{float(d_new['sr_ann']):.3f}")

    # ------------------------------------------------------------- verdetto
    g1 = med_marg >= G1_MARGINE
    g2 = dsr > G2_DSR
    g3 = (quota >= G3_QUOTA) and (med_ex > 0)
    g4 = True                     # mensile: nessun grado di liberta'
    print(f"\n{'=' * 104}\n   I QUATTRO CANCELLI\n{'=' * 104}")
    for nome, ok, det in (("G1 margine", g1, f"mediana {med_marg:+.2f} "
                           f"contro soglia +{G1_MARGINE:.2f}"),
                          ("G2 deflated Sharpe", g2, f"DSR {dsr:.4f} "
                           f"contro soglia {G2_DSR}"),
                          ("G3 stabilita'", g3, f"quota {quota:.1%} contro "
                           f"{G3_QUOTA:.1%}, mediana {med_ex:+.2f} contro 0"),
                          ("G4 calendario", g4, "mensile: passa per costruzione")):
        print(f"   {nome:<22}{'PASSA' if ok else 'FALLISCE':<10}{det}")

    tutti = g1 and g2 and g3 and g4
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: (a) tiene, mediana sopra +1,00 e a meno di 0,3 da "
          f"+1,18; (b) G3 FALLISCE con quota")
    print(f"   sotto i 2/3; (c) il DSR scende ma resta sopra 0,95. Esito atteso: "
          f"tre cancelli su quattro.")
    print(f"   FALSIFICATA se passa tutti e quattro, OPPURE se la mediana di G1 "
          f"scende sotto +1,00.\n")
    print(f"   (a) mediana {med_marg:+.2f}  sopra +1,00: "
          f"{'SI' if g1 else 'NO'}   scarto da +1,18: "
          f"{abs(med_marg - 1.18):.2f} (previsto sotto 0,30)")
    print(f"   (b) G3 {'PASSA' if g3 else 'FALLISCE'}  quota {quota:.1%} "
          f"(previsto sotto {G3_QUOTA:.1%})")
    print(f"   (c) DSR {dsr:.4f}  sopra 0,95: {'SI' if g2 else 'NO'}   "
          f"(era 0,9870 con 10 celle)")
    fals = tutti or (not g1)
    print(f"\n   -> ipotesi M1 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    if tutti:
        print(f"      RAMO 1: il candidato passa tutti e quattro i cancelli.")
        print(f"      L'holdout va aperto SU QUESTO SOLO, UNA VOLTA SOLA, come "
              f"ATTO SEPARATO. Non qui.")
    elif not g1:
        print(f"      RAMO 2: la mediana sui dodici calendari e' sotto +1,00. "
              f"Il +1,18 era il calendario.")
    else:
        print(f"      Cancelli passati: "
              f"{sum([g1, g2, g3, g4])}/4. Holdout SIGILLATO.")

    righe = [dict(round=ROUND, hypothesis="M1 quattro cancelli",
                  config=f"12-{K_CAND} top-{TOP_CAND} bench {mesi_nome[m - 1]}",
                  window=f"{y0}-{FINE}", sharpe="", irr=cand["irr_ref"],
                  bh_irr=bench[m]["irr_ref"], excess=marg[m], n_obs=len(ind_g),
                  note=f"g1med={med_marg:.2f},dsr={dsr:.4f},q3={quota:.3f}")
             for m in range(1, 13)]
    pd.DataFrame([dict(mese=m, bench=bench[m]["irr_ref"], margine=marg[m])
                  for m in range(1, 13)]).to_csv(OUT / "round77_m1.csv",
                                                 index=False)
    lab.log_trials(righe)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

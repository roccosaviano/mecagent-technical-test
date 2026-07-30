"""Giro 82 — O4: quanto vale la correlazione fra le celle, e quanto la N vera.

VOCE DELLA CODA, verbatim (committata al giro 79):

O4 — Quanto vale la correlazione fra le celle, e quanto la N vera
  Il cancello sul margine usa la formula del massimo atteso di N estrazioni
  INDIPENDENTI, e le celle di una famiglia non lo sono. I due errori vanno in
  direzioni opposte e nessuno dei due e' quantificato. VERSO IL BASSO: venti celle
  correlate hanno un massimo atteso piu' piccolo di venti indipendenti, quindi
  +2,19 e' conservativo. VERSO L'ALTO: la N vera della ricerca non e' venti ma
  l'intera griglia implicita — 5 skip x 12 calendari x 4 taglie — e passare da 20
  a 240 celle sposta la soglia da +2,19 a +3,25.
  Da misurare, sul solo 1969-2009: (a) la matrice di correlazione dei rendimenti
  mensili netti delle venti celle del giro 77, e da li' il NUMERO EFFETTIVO di
  estrazioni indipendenti N_eff (via autovalori della matrice, come si fa per i
  test multipli correlati); (b) la soglia ricalcolata con N_eff al posto di N;
  (c) la soglia con la griglia implicita completa.
  PREDIZIONE: N_eff e' FRA 3 E 8 su 20 celle nominali — le celle sono molto
  correlate perche' quattro taglie dello stesso segnale sono quasi lo stesso
  portafoglio — e la soglia corretta scende a +1,5/+1,9, quindi IL CANDIDATO RESTA
  RESPINTO (+1,18), ma con meno margine di quanto il giro 79 suggerisse. Con la
  griglia implicita completa e la stessa correzione, la soglia RISALE SOPRA +2,0:
  i due errori non si compensano, quello della N e' piu' grande.
  FALSIFICATA SE: la soglia corretta scende SOTTO +1,18, cioe' il candidato
  sarebbe passato anche col cancello giusto — OPPURE se N_eff supera 15, cioe' le
  celle sono quasi indipendenti e l'obiezione della correlazione non esisteva.

================= TRE SCELTE DICHIARATE PRIMA DI ESEGUIRE =================

1. QUALE SERIE CORRELARE. La voce dice "rendimenti mensili netti delle venti
   celle". Correlare i rendimenti GREZZI darebbe correlazioni sopra 0,9 per il
   solo fatto che sono tutti portafogli azionari, e schiaccerebbe N_eff a due o
   tre per una ragione che non c'entra col problema. La statistica selezionata e'
   il MARGINE, cioe' una quantita' relativa al benchmark, quindi la correlazione
   che conta e' quella delle serie di EXTRA (cella meno benchmark). Uso quelle, e
   riporto anche la versione sui rendimenti grezzi come sensibilita', perche' la
   voce diceva "netti" e la differenza va mostrata invece che nascosta.

2. QUALE STIMATORE DI N_eff. Tre in letteratura, tutti sugli autovalori della
   matrice di correlazione. Dichiaro PRIMARIO **Li & Ji (2005)**, che e' lo
   standard nei test multipli correlati:
       N_eff = somma_i [ I(|lam_i| >= 1) + (|lam_i| - floor(|lam_i|)) ]
   e riporto Nyholt (2004) e il rapporto di partecipazione M^2 / somma(lam^2)
   come controllo. Se i tre dessero risposte in classi diverse, lo direi.

3. UN SOVRACCONTEGGIO NELLA VOCE, DICHIARATO PRIMA. La voce scrive la griglia
   implicita come "5 skip x 12 calendari x 4 taglie = 240". E' sbagliata: le venti
   celle sono tutte MENSILI, e una strategia mensile NON HA il grado di liberta'
   del calendario — lo passa per costruzione, come dice G4 dal giro 72. I dodici
   calendari appartengono alle strategie annuali. Calcolo la (c) come scritta
   nella voce, perche' non si riscrive una predizione dopo averla vista, ma
   riporto accanto la griglia difendibile — 5 skip x 4 taglie x 3 frequenze = 60 —
   e dico quale delle due userei.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import dataio
from research import lab, bench as B
from research.round76 import simula, pesi_top

ROUND = 82
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
MESE_BENCH = 10
SKIP_FAM = (1, 2, 3, 4, 6)
TAGLIE_FAM = (3, 5, 10, 25)
MARG_CAND = 1.18
EULERO = 0.5772156649015329
N_VOCE = 240            # la griglia come scritta nella voce
N_DIFESA = 60           # 5 skip x 4 taglie x 3 frequenze


def soglia_max(n, sigma, mu=0.0):
    if n < 2 or sigma <= 0:
        return mu
    a = st.norm.ppf(1.0 - 1.0 / n)
    b = st.norm.ppf(1.0 - 1.0 / (n * np.e))
    return mu + sigma * ((1.0 - EULERO) * a + EULERO * b)


def n_eff_liji(lam):
    x = np.abs(lam)
    return float(np.sum((x >= 1.0).astype(float) + (x - np.floor(x))))


def n_eff_nyholt(lam):
    m = len(lam)
    return float(1.0 + (m - 1.0) * (1.0 - np.var(lam, ddof=1) / m))


def n_eff_part(lam):
    return float(np.sum(lam) ** 2 / np.sum(lam ** 2))


def main():
    ind_g = dataio.ff_ind49_daily().dropna(axis=1, how="all").dropna()
    ind_g = ind_g[ind_g.index.year <= FINE]
    ind_m = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind_m = ind_m[ind_m.index.year <= FINE]
    ind_m.index = pd.DatetimeIndex(ind_m.index).to_period("M").to_timestamp("M")
    ind_m = ind_m[ind_g.columns]
    rf = dataio.ff_factors_monthly()["RF"]
    rf.index = pd.DatetimeIndex(rf.index).to_period("M").to_timestamp("M")

    print(f"{'=' * 104}\nO4 — la correlazione fra le celle e la N vera della "
          f"ricerca\n{'=' * 104}")

    def irr(net, turn):
        i = net.dropna().index
        return B.eval_stream("x", net.reindex(i), rf.reindex(i).fillna(0.0),
                             turn.reindex(i))

    W = pd.DataFrame(0.0, index=ind_m.index, columns=ind_m.columns)
    W.loc[W.index.month == MESE_BENCH] = 1.0 / ind_m.shape[1]
    nb, tb = simula(ind_g, W, 0)
    bench = irr(nb, tb)

    mom = {k: (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(k)
           for k in SKIP_FAM}
    nomi, marg, serie = [], [], {}
    for top in TAGLIE_FAM:
        for k in SKIP_FAM:
            n_, t_ = simula(ind_g, pesi_top(mom[k], top), 0)
            r = irr(n_, t_)
            nomi.append(f"12-{k} top-{top}")
            marg.append(r["irr_ref"] - bench["irr_ref"])
            serie[nomi[-1]] = n_
    marg = np.array(marg)
    M = len(nomi)
    sd = float(np.std(marg, ddof=1))

    grezzi = pd.DataFrame(serie).dropna()
    extra = grezzi.sub(nb.reindex(grezzi.index), axis=0)

    print(f"   {M} celle, {len(grezzi)} mesi, benchmark equal-weight annuale "
          f"(calendario mediano).")
    print(f"   margini da {marg.min():+.2f} a {marg.max():+.2f}, "
          f"sigma {sd:.2f}, ampiezza {marg.max() - marg.min():.2f}\n")

    # ------------------------------------------------------------ (a) N_eff
    print(f"   {'=' * 98}\n   (a) IL NUMERO EFFETTIVO DI ESTRAZIONI "
          f"INDIPENDENTI\n   {'=' * 98}")
    ris = {}
    for et, df in (("serie di EXTRA (la scelta dichiarata)", extra),
                   ("rendimenti grezzi (sensibilita')", grezzi)):
        C = df.corr().to_numpy()
        lam = np.linalg.eigvalsh(C)[::-1]
        off = C[~np.eye(M, dtype=bool)]
        ris[et] = dict(liji=n_eff_liji(lam), nyholt=n_eff_nyholt(lam),
                       part=n_eff_part(lam), rho=float(off.mean()),
                       lam1=float(lam[0]), lam=lam)
        r = ris[et]
        print(f"\n   {et}")
        print(f"      correlazione media fuori diagonale : {r['rho']:>7.3f}"
              f"   (min {off.min():+.3f}, max {off.max():+.3f})")
        print(f"      primo autovalore                   : {r['lam1']:>7.2f}"
              f"   su {M} (spiega il {r['lam1'] / M:.0%})")
        print(f"      **N_eff Li & Ji (primario)**       : {r['liji']:>7.2f}")
        print(f"      N_eff Nyholt                       : {r['nyholt']:>7.2f}")
        print(f"      N_eff rapporto di partecipazione   : {r['part']:>7.2f}")

    ne = ris["serie di EXTRA (la scelta dichiarata)"]["liji"]

    # -------------------------------------------------- (b) soglia con N_eff
    print(f"\n   {'=' * 98}\n   (b) LA SOGLIA RICALCOLATA\n   {'=' * 98}")
    s_nom = soglia_max(M, sd)
    s_eff = soglia_max(ne, sd)
    print(f"   {'N usata':<44}{'N':>9}{'soglia':>10}{'candidato':>12}{'esito':>11}")
    print("   " + "-" * 88)
    for et, n_, s_ in (("nominale, come al giro 79", M, s_nom),
                       ("**effettiva (Li & Ji sugli extra)**", ne, s_eff),
                       ("effettiva (Nyholt)", ris["serie di EXTRA (la scelta dichiarata)"]["nyholt"],
                        soglia_max(ris["serie di EXTRA (la scelta dichiarata)"]["nyholt"], sd)),
                       ("effettiva (partecipazione)", ris["serie di EXTRA (la scelta dichiarata)"]["part"],
                        soglia_max(ris["serie di EXTRA (la scelta dichiarata)"]["part"], sd))):
        print(f"   {et:<44}{n_:>9.2f}{s_:>+10.2f}{MARG_CAND:>+12.2f}"
              f"{('PASSA' if MARG_CAND > s_ else 'RESPINTO'):>11}")

    # ------------------------------------------- (c) la griglia implicita
    print(f"\n   {'=' * 98}\n   (c) LA GRIGLIA IMPLICITA, con la stessa "
          f"correzione\n   {'=' * 98}")
    rid = ne / M
    print(f"   fattore di riduzione misurato: N_eff/N = {rid:.3f}\n")
    print(f"   {'griglia':<46}{'N nom.':>8}{'N eff.':>9}{'soglia':>10}{'esito':>11}")
    print("   " + "-" * 86)
    for et, n_ in (("come scritta nella voce (5 skip x 12 cal. x 4 taglie)", N_VOCE),
                   ("difendibile (5 skip x 4 taglie x 3 frequenze)", N_DIFESA),
                   ("la sola famiglia misurata", M)):
        nef = n_ * rid
        s_ = soglia_max(nef, sd)
        print(f"   {et:<46}{n_:>8}{nef:>9.1f}{s_:>+10.2f}"
              f"{('PASSA' if MARG_CAND > s_ else 'RESPINTO'):>11}")

    s_voce = soglia_max(N_VOCE * rid, sd)
    s_dif = soglia_max(N_DIFESA * rid, sd)

    # ------------------------------------------------------------- verdetto
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: N_eff fra 3 e 8; la soglia corretta scende a +1,5/+1,9 "
          f"e il candidato RESTA RESPINTO;")
    print(f"   con la griglia implicita la soglia RISALE SOPRA +2,0.")
    print(f"   FALSIFICATA se la soglia corretta scende SOTTO +1,18, oppure se "
          f"N_eff supera 15.\n")
    c1 = 3.0 <= ne <= 8.0
    c2 = 1.5 <= s_eff <= 1.9
    c3 = MARG_CAND <= s_eff
    c4 = s_voce > 2.0
    print(f"   N_eff fra 3 e 8              : {'SI' if c1 else 'NO'}"
          f"   ({ne:.2f})")
    print(f"   soglia corretta in [1,5; 1,9]: {'SI' if c2 else 'NO'}"
          f"   ({s_eff:+.2f})")
    print(f"   il candidato resta respinto  : {'SI' if c3 else 'NO'}"
          f"   ({MARG_CAND:+.2f} contro {s_eff:+.2f})")
    print(f"   griglia implicita sopra +2,0 : {'SI' if c4 else 'NO'}"
          f"   ({s_voce:+.2f} come da voce, {s_dif:+.2f} con la griglia "
          f"difendibile)")
    fals = (not c3) or (ne > 15.0)
    print(f"\n   -> ipotesi O4 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    if not fals and not (c1 and c2 and c4):
        print(f"      (confermata sul ramo che falsifica; clausole descrittive "
              f"sbagliate: "
              + ", ".join(x for x, ok in (("N_eff", c1), ("soglia", c2),
                                          ("griglia", c4)) if not ok) + ")")

    lab.log_trials([dict(round=ROUND, hypothesis="O4 N effettiva",
                         config=n, window=f"1969-{FINE}", sharpe="",
                         irr=v, bh_irr=s_eff, excess=v - s_eff,
                         n_obs=len(grezzi), note=f"N_eff={ne:.2f},sigma={sd:.3f}")
                    for n, v in zip(nomi, marg)])
    pd.DataFrame(extra.corr()).to_csv(OUT / "round82_corr.csv")
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

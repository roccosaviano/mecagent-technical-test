"""Giro 60 — D4: il benchmark giusto cambia il verdetto?

VOCE DELLA CODA, predizione verbatim:

D4 — Il benchmark giusto cambia il verdetto?
  Il giro 43 ha usato come benchmark l'equal-weight dei 49 settori, cioe' lo
  stesso universo su cui la strategia sceglie, e i tre candidati risultano
  negativi in 20 date di partenza su 20 — mentre contro il PAC cap-weighted H5
  risultava +2,95. Le due cose non sono in contraddizione, ma la scelta del
  benchmark vale piu' di qualunque parametro provato finora. Da misurare
  esplicitamente: gli stessi tre candidati contro tre benchmark diversi —
  cap-weighted, equal-weight dello stesso universo, e equal-weight ribilanciato
  annualmente — riportando quanto del margine e' selezione di titoli e quanto e'
  semplicemente il premio dell'equal-weighting.
  PREDIZIONE: contro il cap-weighted i candidati sembrano positivi, contro
  l'equal-weight dello stesso universo diventano negativi, e la differenza fra i
  due benchmark (~2-3 punti) spiega PIU' DELLA META' del margine apparente. Cioe'
  quasi tutto quel che sembrava alfa era il premio di equal-weighting.
  FALSIFICATA SE: la differenza fra i benchmark spiega meno di un terzo del
  margine.

Come leggo la predizione, fissato PRIMA di guardare i numeri.

  margine apparente = IRR(candidato) - IRR(cap-weight)
  premio di equal-weighting = IRR(equal-weight) - IRR(cap-weight)
  quota spiegata = premio / margine

Il test sta sulla quota spiegata: sopra 1/2 la predizione e' centrata, sotto 1/3
e' falsificata, in mezzo confermata ma con la clausola forte sbagliata. Se il
margine apparente e' negativo la quota non e' definita e lo dichiaro invece di
inventare una convenzione comoda.

IL CAP-WEIGHT E' DELLO STESSO UNIVERSO, non il mercato totale. I pesi sono
n_firms x avg_size delle 49 industrie, capitalizzazione CRSP reale. E' l'unico
modo di isolare lo SCHEMA DI PONDERAZIONE: se usassi il mercato intero cambierei
insieme universo e ponderazione e la decomposizione non direbbe niente. Riporto
comunque il mercato totale come riga di controllo, dichiarata.

I tre candidati sono quelli dei giri 43 e 59, ricostruiti dallo stesso codice.
Nessuna selezione: N resta la famiglia pre-dichiarata della coda.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import dataio
from research import lab, bench as B
from research.round43 import candidates

ROUND = 60
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 60


def ew_costed(rets, every_month):
    """Equal-weight con la rotazione VERA, non quella che vede W.diff().

    Il benchmark del giro 43 e' `ind.mean(axis=1)`, cioe' pesi costanti a 1/N.
    `wbacktest` calcola la rotazione come |W_t - W_{t-1}|, che su pesi costanti
    fa ZERO: il ribilanciamento mensile risulta gratuito e non tassato. Ma
    tenere 1/N ogni mese vuol dire vendere i vincitori e comprare i perdenti
    ogni mese, e quella rotazione esiste. Qui la misuro contro i pesi DERIVATI,
    che e' la definizione corretta.
    """
    n = rets.shape[1]
    w = np.ones(n) / n
    held, turns = [], []
    for i, t in enumerate(rets.index):
        reb = every_month or t.month == 1
        tgt = np.ones(n) / n if reb else w
        turns.append(float(np.abs(tgt - w).sum() / 2.0))
        w = tgt
        held.append(w.copy())
        g = w * (1 + rets.iloc[i].values)
        s = g.sum()
        w = g / s if s > 0 else np.ones(n) / n
    W = pd.DataFrame(held, index=rets.index, columns=rets.columns)
    turn = pd.Series(turns, index=rets.index)
    import config as C
    net = (W * rets).sum(axis=1) - turn * C.COST_ROUND_TRIP
    return net, turn


def ew_drift(rets, reset_month=1):
    """Equal-weight ribilanciato UNA VOLTA L'ANNO, con i pesi che driftano.

    Attenzione: tenere fermi i pesi target a 1/N non e' ribilanciamento annuale,
    e' ribilanciamento a ogni periodo — e' l'errore in cui sono cascato alla
    prima stesura, che produceva un benchmark identico a quello mensile. Il
    ribilanciamento annuale vero lascia che i vincitori pesino di piu' fino al
    gennaio successivo.
    """
    n = rets.shape[1]
    W = pd.DataFrame(0.0, index=rets.index, columns=rets.columns)
    w = np.ones(n) / n
    for i, t in enumerate(rets.index):
        if t.month == reset_month:
            w = np.ones(n) / n
        W.iloc[i] = w
        g = w * (1 + rets.iloc[i].values)
        s = g.sum()
        w = g / s if s > 0 else np.ones(n) / n
    return W


def main():
    vw, ew_ff, nf, sz = dataio.ff_ind49_monthly()
    ind = vw.dropna(axis=1, how="all").dropna()
    cap = (nf * sz).reindex(ind.index)[ind.columns]
    cap = cap.where(cap > 0).ffill()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    mkt = (ff["Mkt-RF"] + ff["RF"]).reindex(ind.index)

    y0, y1 = ind.index[0].year, ind.index[-1].year
    print(f"{'=' * 100}\nD4 — quanto del margine e' selezione e quanto e' "
          f"ponderazione\n{'=' * 100}")
    print(f"   Universo: 49 settori, {y0}-{y1}. Pesi di capitalizzazione = "
          f"n_firms x avg_size (CRSP).")

    # ------------------------------------------------------- i benchmark
    Wcap = cap.div(cap.sum(axis=1), axis=0).shift(1).fillna(0.0)
    Wew = pd.DataFrame(1.0 / ind.shape[1], index=ind.index, columns=ind.columns)
    Wewa = ew_drift(ind)

    benches = {}
    for nm, W in [("cap-weight (stesso universo)", Wcap),
                  ("equal-weight mensile", Wew),
                  ("equal-weight annuale", Wewa)]:
        net, turn = B.wbacktest(ind, W)
        net = net.dropna()
        benches[nm] = B.eval_stream(nm, net, rf.reindex(net.index).fillna(0.0),
                                    turn.reindex(net.index))
    # la stessa cosa con la rotazione misurata sui pesi derivati
    for nm, ev in [("equal-weight mensile (rotaz. vera)", True),
                   ("equal-weight annuale (rotaz. vera)", False)]:
        net, turn = ew_costed(ind, ev)
        net = net.dropna()
        benches[nm] = B.eval_stream(nm, net, rf.reindex(net.index).fillna(0.0),
                                    turn.reindex(net.index))
    # riga di controllo dichiarata: NON e' lo stesso universo
    benches["[controllo] mercato USA totale"] = B.eval_stream(
        "mkt", mkt.dropna(), rf.reindex(mkt.dropna().index).fillna(0.0))

    print(f"\n   {'benchmark':<34}{'CAGR':>9}{'vol':>8}{'Sharpe':>9}"
          f"{'rotaz.':>9}{'IRR':>9}{'aliq.':>7}")
    print("   " + "-" * 76)
    for nm, r in benches.items():
        print(f"   {nm:<34}{r['cagr']:>8.2f}%{r['vol']:>7.2f}%{r['sharpe']:>9.2f}"
              f"{r['turn']:>8.2f}x{r['irr_ref']:>8.2f}%{r['rate_ref']:>6}%")

    cw = benches["cap-weight (stesso universo)"]["irr_ref"]
    ewm = benches["equal-weight mensile"]["irr_ref"]
    ewa = benches["equal-weight annuale"]["irr_ref"]
    ewmt = benches["equal-weight mensile (rotaz. vera)"]["irr_ref"]
    ewat = benches["equal-weight annuale (rotaz. vera)"]["irr_ref"]
    print(f"\n   PREMIO DI EQUAL-WEIGHTING, netto imposte:")
    print(f"     equal-weight mensile  (come giro 43) - cap-weight : {ewm - cw:+.2f} punti")
    print(f"     equal-weight annuale  (pesi derivati) - cap-weight : {ewa - cw:+.2f} punti")
    print(f"     equal-weight mensile  (rotazione vera) - cap-weight : {ewmt - cw:+.2f} punti")
    print(f"     equal-weight annuale  (rotazione vera) - cap-weight : {ewat - cw:+.2f} punti")
    print(f"\n   Quanto costa il ribilanciamento che il giro 43 non addebitava: "
          f"{ewm - ewmt:.2f} punti")

    # ------------------------------------------------------- i candidati
    cands = candidates(ind)
    res = {}
    for nm, W in cands.items():
        net, turn = B.wbacktest(ind, W.shift(1).fillna(0.0))
        net = net.dropna()
        res[nm] = B.eval_stream(nm, net, rf.reindex(net.index).fillna(0.0),
                                turn.reindex(net.index))

    print(f"\n   {'candidato':<34}{'CAGR':>9}{'vol':>8}{'Sharpe':>9}"
          f"{'rotaz.':>9}{'IRR':>9}{'aliq.':>7}")
    print("   " + "-" * 76)
    for nm, r in res.items():
        print(f"   {nm:<34}{r['cagr']:>8.2f}%{r['vol']:>7.2f}%{r['sharpe']:>9.2f}"
              f"{r['turn']:>8.2f}x{r['irr_ref']:>8.2f}%{r['rate_ref']:>6}%")

    print(f"\n   {'candidato':<26}{'vs cap-w':>11}{'vs EW mens.':>13}"
          f"{'vs EW ann.':>12}{'premio EW':>11}{'quota spieg.':>14}")
    print("   " + "-" * 87)
    rows = []
    for nm, r in res.items():
        x = r["irr_ref"]
        m_cw, m_ewm, m_ewa = x - cw, x - ewm, x - ewa
        prem = ewm - cw
        if m_cw > 0:
            quota = f"{prem / m_cw * 100:.1f}%"
            q = prem / m_cw
        else:
            quota, q = "n.d. (marg.<0)", np.nan
        print(f"   {nm:<26}{m_cw:>10.2f}%{m_ewm:>12.2f}%{m_ewa:>11.2f}%"
              f"{prem:>10.2f}%{quota:>14}")
        rows.append(dict(candidato=nm, irr=x, vs_capw=m_cw, vs_ewm=m_ewm,
                         vs_ewa=m_ewa, premio_ew=prem, quota=q))

    # ------------------------------------------------------------ verdetto
    print(f"\n{'=' * 100}\n   VERDETTO\n{'=' * 100}")
    print(f"   Predizione: positivi contro il cap-weight, negativi contro "
          f"l'equal-weight, e il premio")
    print(f"   di equal-weighting (~2-3 punti) spiega PIU' DELLA META' del "
          f"margine apparente.")
    print(f"   FALSIFICATA se il premio spiega meno di UN TERZO del margine.\n")

    h5 = [r for r in rows if r["candidato"].startswith("H5")][0]
    h5m = h5["vs_capw"]
    pos_cw = sum(1 for r in rows if r["vs_capw"] > 0)
    neg_ew = sum(1 for r in rows if r["vs_ewm"] < 0)
    qs = [r["quota"] for r in rows if np.isfinite(r["quota"])]
    print(f"   positivi contro il cap-weight        : {pos_cw}/3")
    print(f"   negativi contro l'equal-weight mens. : {neg_ew}/3")
    print(f"   premio di equal-weighting misurato   : {ewm - cw:+.2f} punti"
          f"   (previsto 2-3)")
    if qs:
        print(f"   quota del margine spiegata           : da {min(qs) * 100:.1f}% "
              f"a {max(qs) * 100:.1f}%")
        fals = max(qs) < 1 / 3
        forte = min(qs) > 0.5
    else:
        print(f"   quota del margine spiegata           : non definita — "
              f"NESSUN candidato ha margine positivo contro il cap-weight")
        fals = False
        forte = False
    print(f"\n   -> ipotesi D4 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'spiega piu' della meta'': "
          f"{'centrata' if forte else 'SBAGLIATA'}")
    print(f"      clausola 'positivi contro il cap-weight': "
          f"{'centrata' if pos_cw == 3 else 'SBAGLIATA'}")
    print(f"      clausola 'negativi contro l'equal-weight': "
          f"{'centrata' if neg_ew == 3 else 'SBAGLIATA'}")

    # la stessa decomposizione con OGNI variante di equal-weight: il verdetto
    # non deve dipendere da quale delle tre uso, e se dipende va detto
    print(f"\n   Sensibilita' del verdetto alla variante di equal-weight "
          f"(margine H5 = {h5m:+.2f}):")
    for nm, v in [("mensile, come giro 43 (gratuito)", ewm),
                  ("mensile, rotazione vera", ewmt),
                  ("annuale, rotazione vera", ewat)]:
        q = (v - cw) / h5m if h5m > 0 else float("nan")
        stato = ("FALSIFICA" if q < 1 / 3 else
                 "conferma, clausola forte centrata" if q > 0.5 else
                 "conferma, clausola forte sbagliata")
        print(f"     {nm:<34} premio {v - cw:+5.2f}  quota {q * 100:6.1f}%  -> {stato}")

    print(f"\n   Riferimento del giro 05: H5 risultava +2,95 contro un PAC "
          f"cap-weighted.")

    print(f"   Qui H5 contro il cap-weight dello stesso universo: "
          f"{h5['vs_capw']:+.2f} punti.")

    pd.DataFrame(rows).to_csv(OUT / "round60_d4.csv", index=False)
    pd.DataFrame([dict(benchmark=nm, cagr=r["cagr"], vol=r["vol"],
                       sharpe=r["sharpe"], turn=r["turn"], irr=r["irr_ref"],
                       rate=r["rate_ref"]) for nm, r in benches.items()]
                 ).to_csv(OUT / "round60_bench.csv", index=False)
    lab.log_trials(
        [dict(round=ROUND, hypothesis="D4 scelta del benchmark", config=nm,
              window=f"{y0}-{y1}", sharpe=r["sharpe"], irr=r["irr_ref"],
              bh_irr=cw, excess=r["irr_ref"] - cw, n_obs=r["n"],
              note=f"rotaz={r['turn']:.2f},aliq={r['rate_ref']}")
         for nm, r in list(benches.items()) + list(res.items())])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

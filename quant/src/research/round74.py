"""Giro 74 — L2: il costo come lo paga un broker retail europeo.

VOCE DELLA CODA, predizione verbatim (committata prima di eseguire):

L2 — Il costo come lo paga un broker retail europeo
  Tutto il progetto usa 0,15% round-trip PROPORZIONALE. Un broker retail europeo
  non funziona cosi': commissione FISSA per ordine (1-3 EUR su Degiro/IBKR), piu'
  spread denaro-lettera, piu' eventualmente un minimo. Su un versamento da 750
  EUR una commissione fissa da 2 EUR e' lo 0,27% — quasi il doppio del modello — e
  su un ribilanciamento che tocca dieci posizioni sono dieci commissioni.
  Da misurare: rifare l'equal-weight annuale, il momentum top-5 e top-10 con un
  modello di costo FISSO + PROPORZIONALE (1,50 EUR per ordine + 0,05% di spread),
  contando UN ORDINE PER POSIZIONE TOCCATA, e confrontare con il modello
  proporzionale del progetto. Riportare anche la soglia di versamento sotto cui un
  PAC mensile diventa antieconomico.
  PREDIZIONE: il modello proporzionale SOTTOSTIMA il costo per le strategie
  concentrate e lo SOVRASTIMA per l'equal-weight, perche' 49 posizioni da 15 EUR
  l'una pagano 49 commissioni fisse. L'effetto netto ALLARGA il divario
  momentum-meno-equal-weight di 0,3-1,0 punti A SFAVORE DEL MOMENTUM, e la soglia
  di antieconomicita' per un PAC su 49 posizioni sta SOPRA i 500 EUR/mese.
  FALSIFICATA SE: il divario si RESTRINGE invece di allargarsi — nel qual caso la
  commissione fissa penalizza piu' il benchmark che il candidato e tutti i
  confronti del progetto sono conservativi nella direzione sbagliata.

UNA CONTRADDIZIONE NELLA VOCE, DICHIARATA PRIMA DI ESEGUIRE. La predizione dice
che il modello proporzionale "SOVRASTIMA il costo per l'equal-weight", ma la
ragione che porta subito dopo — "49 posizioni da 15 EUR l'una pagano 49
commissioni fisse" — dice l'OPPOSTO: con 49 ordini da 1,50 EUR su un versamento
da 750 EUR si pagano 73,50 EUR, cioe' il 9,8%, contro lo 0,075% del modello
proporzionale. Ho scritto una clausola che contraddice la sua stessa
motivazione. Non la riscrivo: la misuro cosi' com'e' e riporto quale delle due
meta' regge.

DUE VARIANTI, entrambe dichiarate qui.

  (i) LETTERALE, come la voce chiede: ogni posizione toccata e' un ordine,
      compreso il versamento mensile spalmato su tutte le posizioni target.
  (ii) SENSATA: il versamento mensile va in UN SOLO ordine, sulla posizione piu'
      sottopesata. E' quello che fa un investitore vero, e senza questa variante
      il confronto misura solo quanto e' assurdo comprare 49 titoli con 15 EUR.
La (i) decide il verdetto perche' e' quella pre-registrata. La (ii) sta accanto
perche' senza di lei il numero non serve a nessuno.

FINESTRA 1969-2009: L2 valuta candidati, l'holdout resta sigillato.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from research import lab
from tax import _xirr

ROUND = 74
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
FISSO = 1.50          # EUR per ordine
SPREAD = 0.0005       # 0,05% sul controvalore di ogni ordine
RATA = C.MONTHLY_CONTRIB


def pac(rets, Wt, modello, rata=RATA, un_ordine=False):
    """PAC con costi PROPORZIONALI ('prop') o FISSI+SPREAD ('retail').

    Restituisce IRR netta, montante, costi totali e numero di ordini.
    Fiscalita': CGT 33%, esenzione annua, riporto perdite, imposte pagate
    liquidando quote — le stesse convenzioni del resto del progetto.
    """
    idx = rets.index
    n = rets.shape[1]
    val = np.zeros(n)
    bas = np.zeros(n)
    year_gain = carry = 0.0
    anno = idx[0].year
    costi = 0.0
    ordini = 0
    cfs = []
    for i, t in enumerate(idx):
        if t.year != anno:
            tass = max(0.0, year_gain - carry)
            carry -= min(carry, max(0.0, year_gain))
            if year_gain < 0:
                carry += -year_gain
            dov = max(0.0, tass - C.CGT_EXEMPT_ANNUAL) * C.CGT_RATE
            tot = val.sum()
            if tot > 0 and dov > 0:
                f = min(1.0, dov / tot)
                val *= (1 - f)
                bas *= (1 - f)
            year_gain = 0.0
            anno = t.year

        tgt = Wt.iloc[i].to_numpy(dtype=float)
        attivo = tgt.sum() > 0
        cfs.append((t, -rata))

        # --- dove va il versamento
        if attivo:
            if un_ordine:
                # sulla posizione piu' sottopesata rispetto al target
                tot = val.sum() + rata
                gap = tgt * tot - val
                k = int(np.argmax(gap))
                quota = np.zeros(n)
                quota[k] = 1.0
            else:
                quota = tgt
        else:
            quota = np.zeros(n)
            quota[0] = 1.0

        n_ord_v = int((quota > 0).sum())
        if modello == "prop":
            fee = rata * (C.COST_ROUND_TRIP / 2.0)
        else:
            fee = n_ord_v * FISSO + rata * SPREAD
        fee = min(fee, rata)
        costi += fee
        ordini += n_ord_v
        inv = rata - fee
        val += quota * inv
        bas += quota * inv

        # --- ribilanciamento verso il target
        if attivo:
            tot = val.sum()
            obiettivo = tgt * tot
            vendi = np.maximum(val - obiettivo, 0.0)
            s_tot = float(vendi.sum())
            if s_tot > 1e-9:
                for k in np.nonzero(vendi > 1e-9)[0]:
                    f = vendi[k] / val[k]
                    year_gain += vendi[k] - bas[k] * f
                    bas[k] -= bas[k] * f
                val = val - vendi
                compra = np.maximum(obiettivo - val, 0.0)
                val = val + compra
                bas = bas + compra
                n_ord_r = int((vendi > 1e-9).sum() + (compra > 1e-9).sum())
                if modello == "prop":
                    fee = s_tot * C.COST_ROUND_TRIP
                else:
                    fee = n_ord_r * FISSO + (s_tot * 2) * SPREAD
                tot = val.sum()
                fee = min(fee, tot)
                costi += fee
                ordini += n_ord_r
                if tot > 0:
                    f = fee / tot
                    val *= (1 - f)

        val = val * (1.0 + rets.iloc[i].to_numpy(dtype=float))

    fin = float(val.sum())
    year_gain += fin - float(bas.sum())
    tass = max(0.0, max(0.0, year_gain - carry) - C.CGT_EXEMPT_ANNUAL)
    fin -= tass * C.CGT_RATE
    cfs.append((idx[-1], fin))
    return dict(irr=_xirr([d for d, _ in cfs], [a for _, a in cfs]) * 100,
                finale=fin, costi=costi, ordini=ordini,
                versato=rata * len(idx))


def pesi_annuali(ind, score=None, top=None, mese=1):
    n = ind.shape[1]
    w = np.ones(n) / n
    out = []
    for i, t in enumerate(ind.index):
        if t.month == mese:
            if score is None:
                w = np.ones(n) / n
            else:
                s = score.iloc[i]
                if s.notna().sum() >= top:
                    best = s.nlargest(top).index
                    w = np.zeros(n)
                    w[[ind.columns.get_loc(c) for c in best]] = 1.0 / top
        out.append(w.copy())
        g = w * (1 + ind.iloc[i].to_numpy(dtype=float))
        ssum = g.sum()
        w = g / ssum if ssum > 0 else w
    return pd.DataFrame(out, index=ind.index, columns=ind.columns)


def pesi_mensili(score, top):
    rk = score.rank(axis=1, ascending=False)
    W = (rk <= top).astype(float)
    return W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind = ind[ind.index.year <= FINE]
    ind.index = pd.DatetimeIndex(ind.index).to_period("M").to_timestamp("M")
    n = ind.shape[1]

    print(f"{'=' * 104}\nL2 — il costo come lo paga un broker retail europeo\n"
          f"{'=' * 104}")
    print(f"   49 settori, {ind.index[0].date()} → {ind.index[-1].date()}. "
          f"**Holdout non toccato.**")
    print(f"   Modello del progetto: {C.COST_ROUND_TRIP:.2%} round-trip "
          f"proporzionale.")
    print(f"   Modello retail: €{FISSO:.2f} per ordine + {SPREAD:.2%} di spread, "
          f"un ordine per posizione toccata.")
    print(f"   Rata €{RATA:.0f}/mese.\n")

    mom12 = (1 + ind).rolling(11).apply(np.prod, raw=True).shift(2)
    strategie = [
        ("equal-weight annuale (49 pos.)", pesi_annuali(ind), 49),
        ("momentum top-5 annuale", pesi_annuali(ind, mom12, 5), 5),
        ("momentum top-5 mensile", pesi_mensili(mom12, 5), 5),
        ("momentum top-10 mensile", pesi_mensili(mom12, 10), 10),
    ]

    for etichetta, un_ordine in (("(i) LETTERALE — un ordine per posizione toccata", False),
                                 ("(ii) SENSATA — il versamento in UN ordine solo", True)):
        print(f"\n   {etichetta}\n")
        print(f"   {'strategia':<32}{'IRR prop.':>11}{'IRR retail':>12}"
              f"{'delta':>9}{'ordini/anno':>13}{'costi retail':>14}")
        print("   " + "-" * 91)
        res = {}
        for nome, W, npos in strategie:
            a = pac(ind, W, "prop", un_ordine=un_ordine)
            b = pac(ind, W, "retail", un_ordine=un_ordine)
            res[nome] = (a["irr"], b["irr"])
            anni = len(ind) / 12
            print(f"   {nome:<32}{a['irr']:>10.2f}%{b['irr']:>11.2f}%"
                  f"{b['irr'] - a['irr']:>+8.2f}{b['ordini'] / anni:>12.0f}"
                  f"{b['costi'] / b['versato'] * 100:>12.1f}% ")
        ew = "equal-weight annuale (49 pos.)"
        print(f"\n   {'divario momentum-meno-equal-weight':<40}"
              f"{'proporzionale':>15}{'retail':>10}{'sposta':>9}")
        print("   " + "-" * 74)
        for nome, _, _ in strategie:
            if nome == ew:
                continue
            dp = res[nome][0] - res[ew][0]
            dr = res[nome][1] - res[ew][1]
            print(f"   {nome:<40}{dp:>+14.2f}{dr:>+10.2f}{dr - dp:>+9.2f}")
        if not un_ordine:
            divari = {nome: (res[nome][0] - res[ew][0], res[nome][1] - res[ew][1])
                      for nome, _, _ in strategie if nome != ew}

    # ---------------------------------------------- soglia di antieconomicita'
    print(f"\n   LA SOGLIA DI ANTIECONOMICITA'\n")
    print(f"   Un versamento spalmato su P posizioni paga P x €{FISSO:.2f}. "
          f"Perche' i costi")
    print(f"   del versamento stiano sotto l'1% della rata serve rata >= "
          f"P x €{FISSO:.2f} / 1%:\n")
    print(f"   {'posizioni':>10}{'commissioni':>14}{'su €750':>10}"
          f"{'rata per stare sotto 1%':>26}")
    print("   " + "-" * 60)
    for P in (1, 5, 10, 25, 49):
        c = P * FISSO
        print(f"   {P:>10}{c:>13.2f}€{c / RATA * 100:>9.1f}%"
              f"{c * 100:>24.0f}€")

    # ------------------------------------------------------------- verdetto
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: il divario momentum-meno-equal-weight si ALLARGA di "
          f"0,3-1,0 punti A SFAVORE")
    print(f"   del momentum, e la soglia di antieconomicita' su 49 posizioni "
          f"sta sopra i €500/mese.")
    print(f"   FALSIFICATA se il divario si RESTRINGE invece di allargarsi.\n")
    for nome, (dp, dr) in divari.items():
        verso = "si allarga" if dr < dp else "SI RESTRINGE"
        print(f"   {nome:<34}{dp:>+8.2f} → {dr:>+7.2f}   {verso} "
              f"({dr - dp:+.2f})")
    restringe = any(dr > dp for dp, dr in divari.values())
    soglia49 = 49 * FISSO * 100
    print(f"\n   soglia su 49 posizioni: €{soglia49:,.0f}/mese"
          f"   (previsto: sopra €500)")
    print(f"\n   -> ipotesi L2 {'FALSIFICATA' if restringe else 'CONFERMATA'}")
    print(f"      clausola 'si allarga a sfavore del momentum': "
          f"{'centrata' if not restringe else 'SBAGLIATA'}")
    print(f"      clausola 'soglia sopra €500': "
          f"{'centrata' if soglia49 > 500 else 'SBAGLIATA'}")

    lab.log_trials([dict(round=ROUND, hypothesis="L2 costo retail",
                         config=nome, window=f"{ind.index[0].year}-{FINE}",
                         sharpe="", irr=dr, bh_irr=dp, excess=dr - dp,
                         n_obs=len(ind), note="divario prop -> retail")
                    for nome, (dp, dr) in divari.items()])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

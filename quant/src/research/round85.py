"""Giro 85 — O7: il fattore 0,300 e' una proprieta' di quella famiglia o una costante?

VOCE DELLA CODA, verbatim (committata al giro 82):

O7 — Il fattore 0,300 e' una proprieta' di quella famiglia o una costante?
  Il cancello sul margine, corretto per la correlazione, dipende da un solo
  numero: N_eff/N, misurato 0,300 su UNA SOLA famiglia. Un cancello che poggia su
  una quantita' misurata una volta sola non e' un cancello.
  Da misurare, sul solo 1969-2009, il rapporto N_eff/N (Li & Ji sulle serie di
  extra, come al giro 82) su QUATTRO famiglie gia' esistenti, di eterogeneita'
  crescente: (1) le 20 celle skip x taglia del giro 77; (2) i 12 candidati del
  giro 72, che mescolano momentum, low-vol e punteggio misto su due frequenze;
  (3) la griglia F2 posizioni x frequenza del giro 50, 15 celle dello stesso
  segnale; (4) i 48 calendari x taglia del giro 68, che variano solo il mese di
  ribilanciamento.
  PREDIZIONE: il fattore NON E' COSTANTE e scala con l'eterogeneita' della
  famiglia. Il valore piu' basso e' quello dei CALENDARI (famiglia 4), sotto 0,15,
  perche' dodici calendari dello stesso portafoglio sono quasi lo stesso test; il
  piu' alto e' quello dei DODICI CANDIDATI (famiglia 2), sopra 0,45, perche'
  momentum e low-vol sono segnali diversi. L'intervallo fra il minimo e il massimo
  e' SUPERIORE A UN FATTORE 3, quindi N_eff/N NON e' utilizzabile come costante e
  va ristimato per famiglia.
  FALSIFICATA SE: tutti e quattro i fattori stanno ENTRO +-0,05 l'uno dall'altro —
  OPPURE se l'ordinamento e' invertito, cioe' la famiglia dei calendari risulta
  PIU' indipendente di quella dei dodici candidati.

================= TRE SCELTE DICHIARATE PRIMA DI ESEGUIRE =================

1. TUTTE E QUATTRO NEL MOTORE MENSILE. Il giro 82 aveva misurato la famiglia 1 nel
   motore giornaliero (0,300); le altre tre nascono in quello mensile. Confrontare
   quattro numeri misurati in due motori diversi introdurrebbe un confondimento
   dove serve proprio un confronto pulito. Ricalcolo tutto in mensile e uso il
   valore giornaliero del giro 82 come CONTROLLO INCROCIATO sulla famiglia 1: se i
   due motori danno lo stesso fattore, il numero e' una proprieta' della famiglia
   e non dello strumento.

2. UN BENCHMARK COMUNE PER TUTTE LE CELLE DI UNA FAMIGLIA. Sottrarre a ogni cella
   un benchmark DIVERSO (per esempio quello dello stesso mese, come faceva il giro
   68) aggiungerebbe agli extra una varianza che non viene dalla strategia, e
   gonfierebbe N_eff per la ragione sbagliata. Uso l'equal-weight annuale di
   GENNAIO per tutte, in tutte e quattro le famiglie: una scelta sola, uniforme,
   nessuna selezione.

3. LA ROTAZIONE VERA OVUNQUE. La famiglia 3 nasce dal giro 50, che usava
   `wbacktest` e quindi la convenzione di rotazione poi corretta al giro 60.
   Ricostruisco tutte e quattro le famiglie con `rot_vera`, altrimenti misurerei
   anche la differenza fra due convenzioni.
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
from research import lab
from research.round72 import pesi_annuali, pesi_mensili, rot_vera

ROUND = 85
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
MESE_BENCH = 1
F1_DAILY = 0.300          # il valore del giro 82, motore giornaliero


def n_eff_liji(lam):
    lam = np.abs(lam)
    return float(np.sum((lam >= 1.0).astype(float) + (lam - np.floor(lam))))


def n_eff_nyholt(lam):
    m = len(lam)
    return float(1.0 + (m - 1.0) * (1.0 - np.var(lam, ddof=1) / m))


def n_eff_part(lam):
    return float(np.sum(lam) ** 2 / np.sum(lam ** 2))


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind = ind[ind.index.year <= FINE]
    ind.index = pd.DatetimeIndex(ind.index).to_period("M").to_timestamp("M")
    rf = dataio.ff_factors_monthly()["RF"]
    rf.index = pd.DatetimeIndex(rf.index).to_period("M").to_timestamp("M")

    print(f"{'=' * 104}\nO7 — N_eff/N su quattro famiglie di eterogeneita' "
          f"crescente\n{'=' * 104}")
    print(f"   Motore mensile per tutte, benchmark comune (equal-weight annuale "
          f"di gennaio), rotazione vera.\n")

    def netto(W):
        tu = rot_vera(ind, W)
        return ((W * ind).sum(axis=1) - tu * C.COST_ROUND_TRIP).dropna()

    net_b = netto(pesi_annuali(ind, MESE_BENCH))

    mom = {k: (1 + ind).rolling(11).apply(np.prod, raw=True).shift(k)
           for k in (1, 2, 3, 4, 6)}
    mom6 = (1 + ind).rolling(5).apply(np.prod, raw=True).shift(2)
    vol36 = ind.rolling(36).std().shift(1)
    mix = mom[2].rank(axis=1, pct=True) + (-vol36).rank(axis=1, pct=True)

    def pesi_freq(score, top, step):
        """top-N ribilanciato ogni `step` mesi, pesi che derivano fra un
        ribilanciamento e l'altro."""
        n = ind.shape[1]
        w = np.ones(n) / n
        out = []
        for i, t in enumerate(ind.index):
            if i % step == 0:
                s = score.iloc[i]
                if s.notna().sum() >= top:
                    best = s.nlargest(top).index
                    w = np.zeros(n)
                    w[[ind.columns.get_loc(c) for c in best]] = 1.0 / top
            out.append(w.copy())
            g = w * (1 + ind.iloc[i].to_numpy(dtype=float))
            ss = g.sum()
            w = g / ss if ss > 0 else w
        return pd.DataFrame(out, index=ind.index, columns=ind.columns)

    fam = {}

    # (1) skip x taglia, 20 celle, tutte mensili — la famiglia del giro 77
    fam["1. skip × taglia (giro 77)"] = {
        f"12-{k} top-{t}": pesi_mensili(mom[k], t)
        for t in (3, 5, 10, 25) for k in (1, 2, 3, 4, 6)}

    # (2) i dodici candidati del giro 72
    f2 = {}
    for nome, ann, sc, top in [
            ("mom12-2 top-5 ann", True, mom[2], 5),
            ("mom12-2 top-10 ann", True, mom[2], 10),
            ("mom12-2 top-25 ann", True, mom[2], 25),
            ("mom6-2 top-10 ann", True, mom6, 10),
            ("lowvol top-10 ann", True, -vol36, 10),
            ("lowvol top-25 ann", True, -vol36, 25),
            ("misto top-10 ann", True, mix, 10),
            ("mom12-2 top-5 mens", False, mom[2], 5),
            ("H5 top-10 mens", False, mom[2], 10),
            ("mom12-2 top-25 mens", False, mom[2], 25),
            ("H4 lowvol top-10 mens", False, -vol36, 10),
            ("C1 misto top-10 mens", False, mix, 10)]:
        f2[nome] = (pesi_annuali(ind, MESE_BENCH, sc, top) if ann
                    else pesi_mensili(sc, top))
    fam["2. dodici candidati (giro 72)"] = f2

    # (3) F2 posizioni x frequenza, 15 celle
    fam["3. posizioni × frequenza (giro 50)"] = {
        f"top-{t} {nf}": pesi_freq(mom[2], t, st)
        for t in (1, 3, 5, 10, 25)
        for nf, st in (("mens", 1), ("trim", 3), ("ann", 12))}

    # (4) calendari x taglia, 48 celle
    f4 = {}
    for nome, sc, top in (("EW", None, None), ("top-5", mom[2], 5),
                          ("top-10", mom[2], 10), ("top-25", mom[2], 25)):
        for m in range(1, 13):
            f4[f"{nome} m{m:02d}"] = pesi_annuali(ind, m, sc, top)
    fam["4. calendari × taglia (giro 68)"] = f4

    print(f"   {'famiglia':<38}{'N':>5}{'corr media':>13}{'1° autov.':>12}"
          f"{'N_eff':>9}{'N_eff/N':>10}{'Nyholt':>9}{'ratio N':>9}")
    print("   " + "-" * 105)
    ris = []
    for nome, celle in fam.items():
        S = pd.DataFrame({k: netto(W) for k, W in celle.items()}).dropna()
        E = S.sub(net_b.reindex(S.index), axis=0)
        # una cella puo' COINCIDERE col benchmark (l'equal-weight di gennaio nella
        # famiglia 4): il suo extra e' identicamente zero e non entra in una
        # matrice di correlazione. La scarto e lo dico.
        degeneri = [c for c in E.columns if E[c].std(ddof=1) < 1e-12]
        if degeneri:
            print(f"   [scartate {len(degeneri)} celle con extra identicamente "
                  f"nullo: {', '.join(degeneri)} — coincidono col benchmark]")
            E = E.drop(columns=degeneri)
        Cm = E.corr().to_numpy()
        M = Cm.shape[0]
        lam = np.linalg.eigvalsh(Cm)[::-1]
        off = Cm[~np.eye(M, dtype=bool)]
        ne = n_eff_liji(lam)
        ny = n_eff_nyholt(lam)
        pa = n_eff_part(lam)
        ris.append((nome, M, float(off.mean()), float(lam[0]), ne, ne / M,
                    ny, ny / M, pa))
        print(f"   {nome:<38}{M:>5}{off.mean():>13.3f}{lam[0]:>11.2f}"
              f"{ne:>9.2f}{ne / M:>10.3f}{ny:>9.2f}{ny / M:>9.3f}")

    fatt = {r[0]: r[5] for r in ris}
    vmin, vmax = min(fatt.values()), max(fatt.values())
    nmin = min(fatt, key=fatt.get)
    nmax = max(fatt, key=fatt.get)

    print(f"\n   minimo  {vmin:.3f}  ({nmin})")
    print(f"   massimo {vmax:.3f}  ({nmax})")
    print(f"   **rapporto massimo/minimo: {vmax / vmin:.2f}×**   "
          f"(previsto sopra 3)")
    print(f"   ampiezza assoluta: {vmax - vmin:.3f}   "
          f"(falsifica se tutti entro ±0,05, cioe' ampiezza < 0,10)")

    f1_mens = fatt["1. skip × taglia (giro 77)"]
    print(f"\n   CONTROLLO INCROCIATO sulla famiglia 1: "
          f"motore mensile **{f1_mens:.3f}** contro giornaliero "
          f"**{F1_DAILY:.3f}** (giro 82)   → scarto {abs(f1_mens - F1_DAILY):.3f}")

    # ------------------------------------------------------------- verdetto
    f_cal = fatt["4. calendari × taglia (giro 68)"]
    f_can = fatt["2. dodici candidati (giro 72)"]
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: il fattore NON e' costante; il minimo e' la famiglia "
          f"dei CALENDARI sotto 0,15,")
    print(f"   il massimo i DODICI CANDIDATI sopra 0,45, e il rapporto "
          f"massimo/minimo e' sopra 3.")
    print(f"   FALSIFICATA se tutti entro ±0,05, oppure se i CALENDARI risultano "
          f"piu' indipendenti dei CANDIDATI.\n")
    c1 = f_cal < 0.15
    c2 = f_can > 0.45
    c3 = (vmax / vmin) > 3.0
    inv = f_cal > f_can
    piatta = (vmax - vmin) < 0.10
    print(f"   calendari sotto 0,15          : {'SI' if c1 else 'NO'}"
          f"   ({f_cal:.3f})")
    print(f"   dodici candidati sopra 0,45   : {'SI' if c2 else 'NO'}"
          f"   ({f_can:.3f})")
    print(f"   rapporto max/min sopra 3      : {'SI' if c3 else 'NO'}"
          f"   ({vmax / vmin:.2f}×)")
    print(f"   ordinamento invertito → fals. : {'SI' if inv else 'no'}"
          f"   (calendari {f_cal:.3f} contro candidati {f_can:.3f})")
    print(f"   tutti entro ±0,05 → fals.     : {'SI' if piatta else 'no'}"
          f"   (ampiezza {vmax - vmin:.3f})")
    fals = inv or piatta
    print(f"\n   -> ipotesi O7 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    if not fals:
        manca = [x for x, ok in (("calendari <0,15", c1),
                                 ("candidati >0,45", c2),
                                 ("rapporto >3", c3)) if not ok]
        if manca:
            print(f"      (confermata sul ramo che falsifica; clausole "
                  f"descrittive sbagliate: {', '.join(manca)})")

    pd.DataFrame(ris, columns=["famiglia", "N", "corr_media", "autov1",
                               "N_eff", "fattore", "nyholt", "fatt_nyholt",
                               "partecipazione"]).to_csv(
        OUT / "round85_o7.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="O7 fattore N_eff/N",
                         config=r[0], window=f"1969-{FINE}", sharpe=r[2],
                         irr=r[4], bh_irr=r[1], excess=r[5], n_obs=len(ind),
                         note=f"autov1={r[3]:.2f}") for r in ris])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

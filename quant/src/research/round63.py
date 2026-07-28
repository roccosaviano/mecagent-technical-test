"""Giro 63 — D6: quante valutazioni del progetto hanno la rotazione sottostimata.

VOCE DELLA CODA, predizione verbatim:

D6 — Quante valutazioni del progetto hanno la rotazione sottostimata
  Nata al giro 60. `bench.wbacktest` calcola la rotazione come |W_t - W_{t-1}|,
  cioe' la variazione dei pesi TARGET. Su pesi target costanti quella differenza
  e' ZERO, e il ribilanciamento risulta gratuito e non tassato. La rotazione vera
  si misura contro i pesi DERIVATI dai rendimenti: per l'equal-weight mensile dei
  49 settori e' 0,20x/anno, e addebitarla costa 1,35 punti di IRR (11,16% ->
  9,81%). L'errore e' sistematico e ha UN VERSO SOLO: favorisce i benchmark
  statici contro le strategie che ruotano, cioe' spinge tutti i verdetti del
  progetto nella stessa direzione.
  Da rifare: rieseguire con la rotazione derivata tutte le valutazioni con
  rotazione nominale sotto 0,5x/anno — i benchmark equal-weight dei giri 30-43 e
  50, l'inverse variance del giro 34, HRP e min-variance dei giri 31-32, il 60/40
  del giro 46.
  PREDIZIONE: almeno DUE TERZI di quelle valutazioni hanno rotazione vera
  superiore al TRIPLO di quella misurata, la correzione media vale OLTRE 0,5
  punti di IRR, e NESSUN VERDETTO SI RIBALTA — perche' i divari registrati sono
  quasi tutti sopra i 2 punti.
  FALSIFICATA SE: la correzione media sta SOTTO 0,2 punti di IRR, oppure ALMENO
  UN VERDETTO SI RIBALTA.

LE TRE CONVENZIONI, definite prima di misurare.

  W_tgt   pesi che la strategia VUOLE tenere nel periodo
  W_der   pesi che risultano dal periodo precedente per effetto dei rendimenti

  (a) "target"   |W_tgt,t - W_tgt,t-1| / 2      convenzione di bench.wbacktest
  (b) "detenuti" |W_der,t - W_der,t-1| / 2      convenzione di round31/round32
  (c) "vera"     |W_tgt,t - W_der,t|   / 2      quello che si compra e si vende

Solo (c) e' la rotazione: e' la distanza fra dove sei e dove vuoi essere. La (a)
va a zero su pesi costanti — e' il difetto del giro 60. La (b) invece conta come
scambio anche il DRIFT, che non e' uno scambio: nessuno compra niente quando un
settore sale e il suo peso cresce da solo.

QUESTO CAMBIA LA PREDIZIONE? No, ma va detto prima: la predizione dichiara che
l'errore ha "un verso solo". Se (a) sottostima e (b) sovrastima, il verso non e'
uno solo, e questa parte della predizione sarebbe sbagliata anche se il test
formale passasse. Lo dichiaro adesso, prima di vedere i numeri, e riportero'
entrambi i versi qualunque cosa venga fuori.

I VERDETTI DA CONTROLLARE, presi dai mini-report cosi' come sono registrati:
  A2  (giro 31) HRP 9,45% contro equal-weight 9,89%          -> gap -0,44
  A3  (giro 32) min-variance 8,22% contro cap-weight 10,88%  -> gap -2,66
  A3  (giro 32) max-diversification 9,34% contro cap-weight  -> gap -1,54
  A1/A5 inverse-variance contro equal-weight
Un verdetto "si ribalta" se il SEGNO del divario cambia dopo la correzione.

La griglia di F2 (giro 50) NON e' in questo giro: e' la voce D7, gia' registrata.
Qui misuro solo il suo benchmark.

Nessuna selezione: N resta la famiglia pre-dichiarata della coda.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from research import lab, bench as B
from research.round31 import hrp_weights, inv_var
from research.round32 import min_variance, max_diversification

ROUND = 63
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 63
LOOKBACK, REBAL = 60, 12


def pesi_ottimizzati(rets, metodo, lookback=LOOKBACK, rebal=REBAL):
    """Pesi TARGET: stimati sui soli `lookback` mesi precedenti, tenuti fermi
    fino al ribilanciamento successivo. Sono i pesi che la strategia vuole."""
    idx, n = rets.index, rets.shape[1]
    W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    w = np.ones(n) / n
    for i in range(len(idx)):
        if i >= lookback and i % rebal == 0:
            win = rets.iloc[i - lookback:i]
            cov = win.cov() * 12
            if metodo == "hrp":
                w = hrp_weights(cov, win.corr())
            elif metodo == "invvar":
                w = inv_var(cov)
            elif metodo == "minvar":
                w = min_variance(cov)
            elif metodo == "maxdiv":
                w = max_diversification(cov)
        W.iloc[i] = w
    return W


def tre_rotazioni(rets, Wt, cost=C.COST_ROUND_TRIP):
    """Le tre convenzioni, sulla stessa serie di pesi target."""
    n = rets.shape[1]
    w = np.zeros(n)
    der, vera = [], []
    W_der = []
    for i in range(len(rets)):
        tgt = Wt.iloc[i].to_numpy(dtype=float)
        if tgt.sum() <= 0:
            tgt = w
        vera.append(float(np.abs(tgt - w).sum() / 2.0))
        W_der.append(w.copy())
        w = tgt
        g = w * (1 + rets.iloc[i].to_numpy(dtype=float))
        s = g.sum()
        w = g / s if s > 0 else w
    W_der = pd.DataFrame(W_der, index=rets.index, columns=rets.columns)
    t_vera = pd.Series(vera, index=rets.index)
    t_tgt = Wt.diff().abs().sum(axis=1).fillna(Wt.abs().sum(axis=1)) / 2.0
    # convenzione round31/32: differenza fra i pesi DETENUTI, che include il drift
    t_det = W_der.diff().abs().sum(axis=1).fillna(W_der.abs().sum(axis=1)) / 2.0
    lordo = (Wt * rets).sum(axis=1)
    return lordo, dict(target=t_tgt, detenuti=t_det, vera=t_vera)


def main():
    vw, _, nf, sz = dataio.ff_ind49_monthly()
    ind = vw.dropna(axis=1, how="all").dropna()
    cap = (nf * sz).reindex(ind.index)[ind.columns]
    cap = cap.where(cap > 0).ffill()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    n = ind.shape[1]
    y0, y1 = ind.index[0].year, ind.index[-1].year

    print(f"{'=' * 108}\nD6 — la rotazione vera delle valutazioni a pesi lenti\n"
          f"{'=' * 108}")
    print(f"   Universo: 49 settori, {y0}-{y1}. Stima su {LOOKBACK} mesi, "
          f"ribilanciamento ogni {REBAL}.\n")

    ew = pd.DataFrame(1.0 / n, index=ind.index, columns=ind.columns)
    keep = pd.Series(ind.index.month == 1, index=ind.index)
    vol36 = ind.rolling(36).std().shift(1)
    mom12 = (1 + ind).rolling(11).apply(np.prod, raw=True).shift(2)

    def topw(score, top, asc=False):
        rk = score.rank(axis=1, ascending=asc)
        W = (rk <= top).astype(float)
        return W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)

    def annuale(W):
        return W.where(keep).ffill().fillna(0.0)

    def ew_drift():
        """Equal-weight ribilanciato SOLO a gennaio: fra un gennaio e l'altro il
        target e' 'quello che ho', perche' non si compra niente. Tenere invece
        fermo il target a 1/N e' ribilanciamento mensile travestito — e' la
        trappola del giro 60, e produrrebbe una riga identica a quella mensile."""
        w = np.ones(n) / n
        out = []
        for i, t in enumerate(ind.index):
            if t.month == 1:
                w = np.ones(n) / n
            out.append(w.copy())
            g = w * (1 + ind.iloc[i].to_numpy(dtype=float))
            ssum = g.sum()
            w = g / ssum if ssum > 0 else w
        return pd.DataFrame(out, index=ind.index, columns=ind.columns)

    # conv = la convenzione effettivamente usata nel giro originale
    porta = [
        ("cap-weight (49 settori)", cap.div(cap.sum(axis=1), axis=0).shift(1).fillna(0.0), "target", "giro 60"),
        ("equal-weight mensile", ew, "target", "giri 30-43, 50"),
        ("equal-weight annuale", ew_drift(), "target", "giri 31, 50"),
        ("inverse-variance annuale", pesi_ottimizzati(ind, "invvar"), "detenuti", "giri 31, 34"),
        ("HRP annuale", pesi_ottimizzati(ind, "hrp"), "detenuti", "giro 31"),
        ("min-variance annuale", pesi_ottimizzati(ind, "minvar"), "detenuti", "giro 32"),
        ("max-diversification annuale", pesi_ottimizzati(ind, "maxdiv"), "detenuti", "giro 32"),
        ("low-vol 36m top-25 annuale", annuale(topw(vol36, 25, asc=True)), "target", "giro 04"),
        ("momentum 12-2 top-25 annuale", annuale(topw(mom12, 25)), "target", "giro 50"),
    ]

    righe, irr = [], {}
    print(f"   {'portafoglio':<30}{'usata':>10}{'rot. usata':>12}"
          f"{'rot. vera':>11}{'x':>7}{'IRR usata':>11}{'IRR vera':>10}"
          f"{'delta':>9}")
    print("   " + "-" * 100)
    for nome, Wt, conv, dove in porta:
        lordo, t = tre_rotazioni(ind, Wt)
        anni = len(ind) / 12
        r_usata = float(t[conv].sum()) / anni
        r_vera = float(t["vera"].sum()) / anni
        net_u = lordo - t[conv] * C.COST_ROUND_TRIP
        net_v = lordo - t["vera"] * C.COST_ROUND_TRIP
        a = B.eval_stream(nome, net_u.dropna(), rf, t[conv])
        b = B.eval_stream(nome, net_v.dropna(), rf, t["vera"])
        mult = r_vera / r_usata if r_usata > 1e-9 else float("inf")
        d = b["irr_ref"] - a["irr_ref"]
        irr[nome] = (a["irr_ref"], b["irr_ref"])
        righe.append(dict(portafoglio=nome, giro=dove, convenzione=conv,
                          rot_usata=r_usata, rot_vera=r_vera, mult=mult,
                          irr_usata=a["irr_ref"], irr_vera=b["irr_ref"], delta=d,
                          rot_target=float(t["target"].sum()) / anni,
                          rot_detenuti=float(t["detenuti"].sum()) / anni))
        ms = "inf" if not np.isfinite(mult) else f"{mult:.1f}"
        print(f"   {nome:<30}{conv:>10}{r_usata:>11.3f}x{r_vera:>10.3f}x"
              f"{ms:>7}{a['irr_ref']:>10.2f}%{b['irr_ref']:>9.2f}%{d:>+8.2f}")

    # ------------------------------------------------ le tre convenzioni
    print(f"\n   Le tre convenzioni a confronto (rotazione annua):")
    print(f"   {'portafoglio':<30}{'(a) target':>12}{'(b) detenuti':>14}"
          f"{'(c) vera':>10}")
    print("   " + "-" * 66)
    for r in righe:
        print(f"   {r['portafoglio']:<30}{r['rot_target']:>11.3f}x"
              f"{r['rot_detenuti']:>13.3f}x{r['rot_vera']:>9.3f}x")

    # ------------------------------------------------ i verdetti
    print(f"\n   I VERDETTI, prima e dopo la correzione:")
    coppie = [("A2 giro 31", "HRP annuale", "equal-weight annuale"),
              ("A3 giro 32", "min-variance annuale", "cap-weight (49 settori)"),
              ("A3 giro 32", "max-diversification annuale", "cap-weight (49 settori)"),
              ("A1/A5", "inverse-variance annuale", "equal-weight annuale"),
              ("giro 04", "low-vol 36m top-25 annuale", "cap-weight (49 settori)")]
    print(f"   {'voce':<12}{'candidato':<30}{'benchmark':<28}"
          f"{'gap usato':>11}{'gap vero':>10}{'ribalta':>9}")
    print("   " + "-" * 100)
    ribalta = 0
    for voce, a, b in coppie:
        gu = irr[a][0] - irr[b][0]
        gv = irr[a][1] - irr[b][1]
        flip = (gu > 0) != (gv > 0)
        ribalta += int(flip)
        print(f"   {voce:<12}{a:<30}{b:<28}{gu:>10.2f}%{gv:>9.2f}%"
              f"{'SI' if flip else 'no':>9}")

    # ------------------------------------------------ verdetto
    K = len(righe)
    tripli = sum(1 for r in righe if r["mult"] > 3.0)
    corr_media = float(np.mean([abs(r["delta"]) for r in righe]))
    print(f"\n{'=' * 108}\n   VERDETTO\n{'=' * 108}")
    print(f"   Predizione: almeno 2/3 con rotazione vera oltre il TRIPLO di "
          f"quella usata, correzione")
    print(f"   media oltre 0,5 punti, e nessun verdetto ribaltato.")
    print(f"   FALSIFICATA se la correzione media sta sotto 0,2 punti, "
          f"OPPURE almeno un verdetto si ribalta.\n")
    print(f"   rotazione vera > 3x quella usata : {tripli}/{K} = "
          f"{tripli / K * 100:.1f}%   (previsto >=66,7%)")
    print(f"   correzione media                 : {corr_media:.2f} punti"
          f"   (previsto >0,5, falsifica sotto 0,2)")
    print(f"   verdetti ribaltati               : {ribalta}"
          f"   (previsto 0, falsifica se >=1)")
    fals = (corr_media < 0.2) or (ribalta >= 1)
    print(f"\n   -> ipotesi D6 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola '2/3 oltre il triplo': "
          f"{'centrata' if tripli / K >= 2 / 3 else 'SBAGLIATA'}")
    print(f"      clausola 'correzione media >0,5': "
          f"{'centrata' if corr_media > 0.5 else 'SBAGLIATA'}")
    print(f"      clausola 'nessun ribaltamento': "
          f"{'centrata' if ribalta == 0 else 'SBAGLIATA'}")

    sotto = sum(1 for r in righe if r["rot_usata"] < r["rot_vera"])
    sopra = sum(1 for r in righe if r["rot_usata"] > r["rot_vera"])
    print(f"\n   La clausola 'un verso solo', dichiarata prima di misurare:")
    print(f"     valutazioni che SOTTOSTIMANO la rotazione : {sotto}/{K}")
    print(f"     valutazioni che la SOVRASTIMANO           : {sopra}/{K}")
    print(f"     -> l'errore ha {'UN VERSO SOLO' if sopra == 0 or sotto == 0 else 'DUE VERSI'}")

    pd.DataFrame(righe).to_csv(OUT / "round63_d6.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="D6 rotazione sottostimata",
                         config=r["portafoglio"], window=f"{y0}-{y1}", sharpe="",
                         irr=r["irr_vera"], bh_irr=r["irr_usata"],
                         excess=r["delta"], n_obs=len(ind),
                         note=f"rot_usata={r['rot_usata']:.3f},rot_vera={r['rot_vera']:.3f}")
                    for r in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

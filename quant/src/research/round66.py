"""Giro 66 — D9: la fascia di rotazione fra 0,7x e 1,0x e' un precipizio.

VOCE DELLA CODA, predizione verbatim:

D9 — La fascia di rotazione fra 0,7x e 1,0x e' un precipizio, non un pendio
  Nata al giro 64. Il top-5 annuale passa da 0,83x a 1,022x di rotazione solo
  cambiando COME SI MISURA, e con quel passaggio l'aliquota salta dal 33% al 52%:
  diciannove punti d'imposta su una differenza di misura del 23%. Nessuna
  strategia dovrebbe avere il proprio risultato deciso da quale lato di una
  soglia cade una statistica misurata con un'incertezza di quell'ordine. La
  domanda non e' metodologica: ESISTE UN MODO DI STARE DELIBERATAMENTE SOTTO LA
  SOGLIA CHE PAGHI? Una strategia che rinuncia a parte della rotazione per
  restare al 33% puo' battere la stessa strategia lasciata libera di ruotare al
  52%.
  Da misurare: per ciascuna cella della griglia F2 con rotazione vera fra 0,7x e
  1,4x, costruire la variante VINCOLATA — stessa selezione, ma i ribilanciamenti
  si fermano quando la rotazione cumulata dell'anno raggiunge 0,95x — e
  confrontare IRR netta della libera (52%) contro la vincolata (33%). Riportare
  anche quanto segnale si perde, cioe' il calo di CAGR lordo.
  PREDIZIONE: la variante vincolata BATTE la libera in ALMENO DUE TERZI delle
  celle nella fascia, e il guadagno medio sta fra 1 e 3 punti di IRR — perche'
  rinunciare all'ultimo 10% di rotazione costa poco di lordo e vale diciannove
  punti di aliquota. Ma NESSUNA VINCOLATA BATTE l'equal-weight annuale, che resta
  a 10,65%.
  FALSIFICATA SE: la vincolata batte la libera in MENO DI META' delle celle — nel
  qual caso il segnale perso vale piu' dell'aliquota risparmiata, e la soglia del
  100% non e' sfruttabile — OPPURE una vincolata SUPERA l'equal-weight annuale,
  nel qual caso c'e' un candidato vero e va portato al DSR sul registro cumulato.

DUE SCELTE DICHIARATE PRIMA DI CALCOLARE.

1. COME SI "FERMA" UN RIBILANCIAMENTO. Le celle in fascia sono tutte annuali:
   ribilanciano una volta l'anno e quel singolo scambio costa ~1,0x. Fermarlo
   del tutto significherebbe non ribilanciare mai piu', cioe' distruggere la
   strategia invece di vincolarla. Eseguo quindi il ribilanciamento PARZIALE:
   ci si muove verso il target solo fino a consumare il budget residuo,

       w_nuovo = w_derivato + lambda * (target - w_derivato)

   con lambda scelto perche' la rotazione dell'anno arrivi esattamente a 0,95x e
   non oltre. E' l'unica lettura che lascia la strategia viva, e la dichiaro qui.

2. QUALE GRIGLIA. Uso `round50.rotate`, la stessa costruzione del giro 64, non
   il calendario di gennaio del giro 65. Il calendario e' un parametro libero
   scoperto al giro 65 e registrato come voce D10: sceglierlo qui in base a quale
   dei due conviene sarebbe selezione non contata. Il giro 64 e' la rivalutazione
   ufficiale di F2, quindi e' quella la griglia.

Nessuna selezione dichiarata oltre alla fascia: N resta la famiglia della coda.
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
from research import lab, bench as B
from research.round50 import rotate, FREQS

ROUND = 66
OUT = Path(__file__).resolve().parents[2] / "out"
BUDGET = 0.95


def esegui(rets, Wt, budget=None):
    """Rendimento netto e rotazione vera. Se `budget` e' dato, i ribilanciamenti
    sono eseguiti solo parzialmente una volta consumato il budget annuo."""
    n = rets.shape[1]
    w = np.zeros(n)
    held, turns = [], []
    anno, speso = None, 0.0
    for i, t in enumerate(rets.index):
        if t.year != anno:
            anno, speso = t.year, 0.0
        tgt = Wt.iloc[i].to_numpy(dtype=float)
        if tgt.sum() <= 0:
            tgt = w
        voluto = float(np.abs(tgt - w).sum() / 2.0)
        if budget is not None and voluto > 0:
            resto = max(0.0, budget - speso)
            lam = min(1.0, resto / voluto)
            tgt = w + lam * (tgt - w)
            voluto = voluto * lam
        speso += voluto
        turns.append(voluto)
        w = tgt
        held.append(w.copy())
        g = w * (1 + rets.iloc[i].to_numpy(dtype=float))
        s = g.sum()
        w = g / s if s > 0 else w
    W = pd.DataFrame(held, index=rets.index, columns=rets.columns)
    turn = pd.Series(turns, index=rets.index)
    lordo = (W * rets).sum(axis=1)
    return (lordo - turn * C.COST_ROUND_TRIP).dropna(), turn, lordo


def ew_annuale(rets):
    n = rets.shape[1]
    w = np.ones(n) / n
    out = []
    for i, t in enumerate(rets.index):
        if t.month == 1:
            w = np.ones(n) / n
        out.append(w.copy())
        g = w * (1 + rets.iloc[i].to_numpy(dtype=float))
        s = g.sum()
        w = g / s if s > 0 else w
    return pd.DataFrame(out, index=rets.index, columns=rets.columns)


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    y0, y1 = ind.index[0].year, ind.index[-1].year
    anni = len(ind) / 12

    print(f"{'=' * 104}\nD9 — restare deliberatamente sotto la soglia del 100% "
          f"di rotazione\n{'=' * 104}")
    print(f"   Universo: 49 settori, {y0}-{y1}. Griglia del giro 64, "
          f"budget annuo {BUDGET}x.\n")

    net_b, turn_b, _ = esegui(ind, ew_annuale(ind))
    ewa = B.eval_stream("EW annuale", net_b, rf, turn_b)
    print(f"   Benchmark: equal-weight annuale, rotazione "
          f"{float(turn_b.sum()) / anni:.3f}x, IRR {ewa['irr_ref']:.2f}%\n")

    # ------------------------------------------------- quali celle sono in fascia
    tutte = []
    for top in (1, 3, 5, 10, 25):
        for fname, step in FREQS.items():
            W = rotate(ind, top, step)
            net, turn, lordo = esegui(ind, W)
            r = B.eval_stream(f"top-{top} {fname}", net, rf, turn)
            r.update(top=top, freq=fname, rot=float(turn.sum()) / anni,
                     net=net, lordo=lordo)
            tutte.append(r)
    fascia = [c for c in tutte if 0.7 <= c["rot"] <= 1.4]
    print(f"   Celle con rotazione vera fra 0,7x e 1,4x: {len(fascia)} su "
          f"{len(tutte)}")
    print("   " + ", ".join(f"top-{c['top']} {c['freq']} ({c['rot']:.3f}x)"
                            for c in fascia) + "\n")

    def cagr(s):
        yrs = len(s) / 12
        tot = float((1 + s).prod())
        return (tot ** (1 / yrs) - 1) * 100 if tot > 0 else -100.0

    righe = []
    print(f"   {'cella':<20}{'rot. libera':>12}{'aliq.':>7}{'IRR libera':>12}"
          f"{'rot. vinc.':>12}{'aliq.':>7}{'IRR vinc.':>11}{'guadagno':>10}"
          f"{'CAGR lordo perso':>18}")
    print("   " + "-" * 109)
    for c in fascia:
        W = rotate(ind, c["top"], FREQS[c["freq"]])
        netv, turnv, lordov = esegui(ind, W, budget=BUDGET)
        v = B.eval_stream(f"top-{c['top']} {c['freq']} vinc.", netv, rf, turnv)
        rot_v = float(turnv.sum()) / anni
        g = v["irr_ref"] - c["irr_ref"]
        perso = cagr(c["lordo"]) - cagr(lordov)
        righe.append(dict(cella=f"top-{c['top']} {c['freq']}", rot_l=c["rot"],
                          aliq_l=c["rate_ref"], irr_l=c["irr_ref"], rot_v=rot_v,
                          aliq_v=v["rate_ref"], irr_v=v["irr_ref"], guadagno=g,
                          lordo_perso=perso, vs_ewa=v["irr_ref"] - ewa["irr_ref"],
                          net=netv))
        print(f"   {'top-' + str(c['top']) + ' ' + c['freq']:<20}"
              f"{c['rot']:>11.3f}x{c['rate_ref']:>6}%{c['irr_ref']:>11.2f}%"
              f"{rot_v:>11.3f}x{v['rate_ref']:>6}%{v['irr_ref']:>10.2f}%"
              f"{g:>+9.2f}{perso:>17.2f}")

    print(f"\n   {'cella':<20}{'IRR vincolata':>15}{'vs EW annuale':>16}")
    print("   " + "-" * 51)
    for r in righe:
        print(f"   {r['cella']:<20}{r['irr_v']:>14.2f}%{r['vs_ewa']:>+15.2f}")

    # ------------------------------------------------------------- verdetto
    K = len(righe)
    vince = sum(1 for r in righe if r["guadagno"] > 0)
    q = vince / K if K else float("nan")
    med = float(np.mean([r["guadagno"] for r in righe])) if K else float("nan")
    sopra = [r for r in righe if r["vs_ewa"] > 0]
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: la vincolata batte la libera in almeno DUE TERZI "
          f"delle celle, guadagno")
    print(f"   medio fra 1 e 3 punti, e NESSUNA vincolata batte l'equal-weight "
          f"annuale.")
    print(f"   FALSIFICATA se la vincolata vince in MENO DI META' delle celle, "
          f"OPPURE una supera l'EW annuale.\n")
    print(f"   celle nella fascia               : {K}")
    print(f"   la vincolata batte la libera in  : {vince}/{K}"
          + (f" = {q * 100:.1f}%" if K else "")
          + f"   (previsto >=66,7%, falsifica sotto 50%)")
    print(f"   guadagno medio                   : {med:+.2f} punti"
          f"   (previsto +1/+3)")
    print(f"   vincolate sopra l'EW annuale     : {len(sopra)}"
          f"   (previsto 0, falsifica se >=1)")

    fals = (K > 0 and q < 0.5) or len(sopra) >= 1
    print(f"\n   -> ipotesi D9 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'vince in >=2/3 delle celle': "
          f"{'centrata' if K and q >= 2 / 3 else 'SBAGLIATA'}")
    print(f"      clausola 'guadagno medio fra 1 e 3': "
          f"{'centrata' if 1.0 <= med <= 3.0 else 'SBAGLIATA'}")
    print(f"      clausola 'nessuna sopra l'EW annuale': "
          f"{'centrata' if not sopra else 'SBAGLIATA'}")

    if sopra:
        n_cum = lab.n_trials_so_far()
        srs = [float((r["net"] - rf.reindex(r["net"].index).fillna(0.0)).mean()
                     / (r["net"] - rf.reindex(r["net"].index).fillna(0.0)).std(ddof=1))
               for r in righe]
        var_fam = float(np.var(srs, ddof=1)) if len(srs) > 1 else None
        print(f"\n   DSR delle vincolate che superano l'EW annuale "
              f"(N = {n_cum}, var_sr sulla famiglia):")
        for r in sopra:
            d = lab.deflated_sharpe(r["net"], n_cum, var_sr=var_fam, rf=rf)
            print(f"     {r['cella']:<20}SR {d['sr_period']:.4f}  "
                  f"SR0 {d['sr0']:.4f}  DSR {d['dsr']:.4f}  -> "
                  f"{'PROMUOVIBILE' if d['dsr'] > 0.95 else 'sotto soglia'}")
    else:
        print(f"\n   Nessuna vincolata supera l'equal-weight annuale: "
              f"niente DSR da calcolare.")
    print(f"\n   Promozioni: ZERO se nessuna riga sopra dice PROMUOVIBILE. "
          f"Holdout ancora sigillato.")

    pd.DataFrame([{k: v for k, v in r.items() if k != "net"} for r in righe]
                 ).to_csv(OUT / "round66_d9.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="D9 vincolo di rotazione",
                         config=r["cella"], window=f"{y0}-{y1}", sharpe="",
                         irr=r["irr_v"], bh_irr=ewa["irr_ref"],
                         excess=r["vs_ewa"], n_obs=len(ind),
                         note=f"rot={r['rot_v']:.3f},guadagno={r['guadagno']:.2f}")
                    for r in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

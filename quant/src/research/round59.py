"""Giro 59 — D3: dispersione su finestre di lunghezza fissa.

VOCE DELLA CODA, predizione verbatim:

D3 — Dispersione su finestre di lunghezza fissa, non su date di partenza
  Nata perche' D1 e' stata falsificata per un difetto della sua stessa specifica.
  "Far partire il campione in 20 anni diversi" con la fine sempre al 2026 produce
  20 campioni che condividono 33-52 anni su 52: la dispersione misurata (0,17-0,56
  punti) e' piccola per costruzione, non perche' il risultato sia stabile. Il test
  che risponde davvero alla domanda usa finestre mobili di lunghezza fissa (10 e 20
  anni, passo 1 anno), che si sovrappongono molto meno e coprono regimi diversi.
  PREDIZIONE: su finestre di 10 anni la dispersione dell'extra-rendimento supera 4
  punti e il segno cambia in almeno un terzo delle finestre; su finestre di 20 anni
  la dispersione resta sopra 2 punti.
  FALSIFICATA SE: la dispersione su finestre di 10 anni resta sotto 2 punti.

Tre chiarimenti su come leggo la predizione, fissati PRIMA di guardare i numeri.

1. "Dispersione" = AMPIEZZA (massimo meno minimo), la stessa statistica su cui D1
   e' stata giudicata ("ampiezza 0,56 punti contro i 3 previsti"). Riporto anche
   la deviazione standard, ma il verdetto sta sull'ampiezza: cambiare metrica dopo
   aver visto i dati sarebbe esattamente quel che il protocollo vieta.

2. "Il segno cambia in almeno un terzo delle finestre" = la quota di finestre in
   cui l'extra-rendimento ha segno OPPOSTO a quello della media sta sopra 1/3.
   E' l'unica lettura che rende la clausola un test e non una tautologia.

3. I candidati e il benchmark sono gli stessi del giro 43, ricostruiti dallo
   stesso codice: H4 low-vol, H5 momentum 12-2, C1 punteggio misto, contro
   l'equal-weight dei 49 settori. Cambiare universo renderebbe D3 incomparabile
   con D1, che e' il confronto per cui la voce esiste.

Nessuna selezione: e' una misura di dispersione su strategie gia' fissate. N per
il Deflated Sharpe resta la famiglia pre-dichiarata della coda.
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

ROUND = 59
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 59


def excess_on(ind, W, bench, rf, i):
    """Extra-rendimento IRR sulla finestra i, gia' netto di costi e imposte."""
    net, turn = B.wbacktest(ind.loc[i], W.loc[i].shift(1).fillna(0.0))
    net = net.dropna()
    if len(net) < 100:
        return None
    rf0 = rf.reindex(net.index).fillna(0.0)
    r = B.eval_stream("x", net, rf0, turn.reindex(net.index))
    b = B.eval_stream("b", bench.reindex(net.index), rf0)
    return r["irr_ref"] - b["irr"]


def overlap_stats(spans, total_years):
    """Quota media di anni condivisi fra due campioni presi a caso.

    E' il numero che spiega perche' D1 non poteva vedere nulla: se due campioni
    condividono il 90% degli anni, la loro differenza e' quasi zero per
    costruzione, qualunque sia la strategia.
    """
    n = len(spans)
    sh = []
    for a in range(n):
        for b in range(a + 1, n):
            lo = max(spans[a][0], spans[b][0])
            hi = min(spans[a][1], spans[b][1])
            inter = max(0, hi - lo + 1)
            union = ((spans[a][1] - spans[a][0] + 1)
                     + (spans[b][1] - spans[b][0] + 1) - inter)
            sh.append(inter / union)
    return float(np.mean(sh)), float(np.max(sh))


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    bench = ind.mean(axis=1)
    cands = candidates(ind)

    y0, y1 = ind.index[0].year, ind.index[-1].year
    print(f"{'=' * 96}\nD3 — dispersione su finestre mobili di lunghezza fissa\n"
          f"{'=' * 96}")
    print(f"   Universo: 49 settori, {y0}-{y1} ({y1 - y0 + 1} anni). "
          f"Benchmark: equal-weight dello stesso universo.")

    # ---- il difetto di D1, quantificato prima di misurare qualunque cosa
    d1_spans = [(y, y1) for y in range(y0 + 5, y0 + 25)]
    m1, x1 = overlap_stats(d1_spans, y1 - y0 + 1)
    print(f"\n   Perche' D3 esiste — sovrapposizione media fra due campioni:")
    print(f"     D1 (20 partenze, fine fissa {y1}) : {m1 * 100:5.1f}%  "
          f"(massimo {x1 * 100:.1f}%)")

    results = {}
    for L in (10, 20):
        spans = [(y, y + L - 1) for y in range(y0 + 3, y1 - L + 2)]
        m, x = overlap_stats(spans, y1 - y0 + 1)
        print(f"     D3 finestre di {L:2d} anni, passo 1  : {m * 100:5.1f}%  "
              f"(massimo {x * 100:.1f}%)   {len(spans)} finestre")
        results[L] = (spans, m)

    for L in (10, 20):
        spans, _ = results[L]
        print(f"\n{'-' * 96}\n   FINESTRE DI {L} ANNI — {len(spans)} finestre da "
              f"{spans[0][0]}-{spans[0][1]} a {spans[-1][0]}-{spans[-1][1]}\n"
              f"{'-' * 96}")
        tab = {}
        for nm, W in cands.items():
            vals, keep = [], []
            for a, b in spans:
                i = ind.index[(ind.index.year >= a) & (ind.index.year <= b)]
                v = excess_on(ind, W, bench, rf, i)
                if v is not None and np.isfinite(v):
                    vals.append(v)
                    keep.append((a, b))
            tab[nm] = (np.array(vals), keep)
        print(f"   {'candidato':<26}{'media':>9}{'min':>9}{'max':>9}"
              f"{'ampiezza':>11}{'dev.std':>10}{'segno opp.':>12}")
        print("   " + "-" * 77)
        for nm, (v, _) in tab.items():
            opp = float((np.sign(v) != np.sign(v.mean())).mean())
            print(f"   {nm:<26}{v.mean():>8.2f}%{v.min():>8.2f}%{v.max():>8.2f}%"
                  f"{v.max() - v.min():>10.2f}%{v.std(ddof=1):>9.2f}%"
                  f"{opp * 100:>10.1f}% ")
        results[L] = (spans, tab)

    # ------------------------------------------------------------ verdetto
    v10 = {nm: t[0] for nm, t in results[10][1].items()}
    v20 = {nm: t[0] for nm, t in results[20][1].items()}
    amp10 = {nm: float(v.max() - v.min()) for nm, v in v10.items()}
    amp20 = {nm: float(v.max() - v.min()) for nm, v in v20.items()}
    opp10 = {nm: float((np.sign(v) != np.sign(v.mean())).mean())
             for nm, v in v10.items()}

    a10min, a10max = min(amp10.values()), max(amp10.values())
    a20min, a20max = min(amp20.values()), max(amp20.values())
    o10min, o10max = min(opp10.values()), max(opp10.values())

    print(f"\n{'=' * 96}\n   VERDETTO\n{'=' * 96}")
    print(f"   Predizione: ampiezza a 10 anni > 4 punti E segno opposto in "
          f"almeno 1/3 delle finestre;")
    print(f"               ampiezza a 20 anni > 2 punti.")
    print(f"   FALSIFICATA se l'ampiezza a 10 anni resta sotto 2 punti.\n")
    print(f"   ampiezza 10 anni   : da {a10min:.2f} a {a10max:.2f} punti"
          f"   (soglia predetta 4, soglia di falsificazione 2)")
    print(f"   ampiezza 20 anni   : da {a20min:.2f} a {a20max:.2f} punti"
          f"   (soglia predetta 2)")
    print(f"   segno opposto 10a  : da {o10min * 100:.1f}% a {o10max * 100:.1f}%"
          f"        (soglia predetta 33,3%)")

    fals = a10min < 2.0
    print(f"\n   -> ipotesi D3 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    if not fals:
        cl = []
        cl.append(("ampiezza 10a > 4", a10min > 4.0))
        cl.append(("segno opposto >= 1/3", o10min >= 1 / 3))
        cl.append(("ampiezza 20a > 2", a20min > 2.0))
        for nome, ok in cl:
            print(f"      clausola '{nome}': {'centrata' if ok else 'SBAGLIATA'}")

    # ---- il confronto che e' il senso della voce
    print(f"\n   Confronto diretto con D1 (stessi candidati, stesso benchmark):")
    print(f"      D1, 20 partenze con fine fissa : ampiezza max 0,56 punti")
    print(f"      D3, finestre di 10 anni        : ampiezza max {a10max:.2f} punti"
          f"   ({a10max / 0.56:.0f}x)")
    print(f"      D3, finestre di 20 anni        : ampiezza max {a20max:.2f} punti"
          f"   ({a20max / 0.56:.0f}x)")

    rows = []
    for L in (10, 20):
        spans, tab = results[L]
        for nm, (v, keep) in tab.items():
            for (a, b), x in zip(keep, v):
                rows.append(dict(lung=L, candidato=nm, da=a, a=b, extra=float(x)))
    pd.DataFrame(rows).to_csv(OUT / "round59_d3.csv", index=False)

    lab.log_trials([dict(round=ROUND, hypothesis="D3 dispersione finestre fisse",
                         config=f"{nm} L={L}a", window=f"{y0}-{y1}",
                         sharpe="", irr="", bh_irr="",
                         excess=float(results[L][1][nm][0].mean()),
                         n_obs=len(results[L][1][nm][0]),
                         note=(f"ampiezza={results[L][1][nm][0].max() - results[L][1][nm][0].min():.2f},"
                               f"sd={results[L][1][nm][0].std(ddof=1):.2f}"))
                    for L in (10, 20) for nm in results[L][1]])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

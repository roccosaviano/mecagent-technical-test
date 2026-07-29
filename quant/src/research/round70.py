"""Giro 70 — K2: il PAC che si interrompe.

VOCE DELLA CODA, predizione verbatim (committata prima di eseguire):

K2 — Il PAC che si interrompe
  Ogni simulazione assume 360 versamenti consecutivi. Nella realta' si salta, si
  riduce, si riscatta in anticipo. Il giro 61 ha dato lo strumento esatto per
  rispondere: il peso dIRR/dlog(1+R_k) e' monotono crescente, quindi saltare
  versamenti PRESTO e saltarli TARDI non costano uguale.
  Da misurare: PAC ventennale con un'interruzione di 24 mesi che comincia
  all'anno k = 1..18, e in parallelo un riscatto anticipato del 30% all'anno k.
  Riportare la perdita di IRR e di montante finale in funzione di k.
  PREDIZIONE: l'interruzione costa MENO DI 0,3 PUNTI di IRR ovunque — perche'
  l'IRR e' un tasso, e saltare versamenti riduce il montante ma non il
  rendimento — mentre il MONTANTE cala di 8-12% e il calo e' MONOTONO DECRESCENTE
  in k (saltare presto costa di piu' in montante). Il riscatto anticipato invece
  colpisce l'IRR, e di OLTRE 0,5 PUNTI se avviene nei primi dieci anni.
  FALSIFICATA SE: l'interruzione sposta l'IRR di oltre 0,5 punti in qualche k —
  nel qual caso l'IRR non e' la metrica giusta per un PAC irregolare e serve il
  montante — OPPURE il calo del montante non e' monotono in k.

DUE SCELTE DICHIARATE PRIMA DI CALCOLARE.

1. NON UN PERCORSO SOLO. Un PAC ventennale su un singolo percorso storico
   misurerebbe quel percorso, non il meccanismo. Uso TUTTE le finestre
   ventennali del mercato USA a passo annuale e riporto la MEDIANA, piu' minimo e
   massimo. Finestra 1926-2009: K2 non e' una voce metodologica sui verdetti gia'
   registrati, tocca il montante di un investitore, quindi tengo l'holdout
   sigillato.

2. "MONOTONO IN k" lo verifico sulla MEDIANA delle finestre, non su ogni singola
   finestra: su una finestra sola il rumore del percorso puo' rompere la
   monotonia senza che il meccanismo sia sbagliato. Lo dichiaro qui perche' e'
   una scelta che rende la clausola piu' facile da superare, e va detto.

IL MOTORE. Scritto qui e non riusato da tax.py perche' `simulate_pac` non
prevede USCITE di denaro: un riscatto e' un flusso positivo per l'investitore, e
va nel calcolo dell'IRR con la sua data. Convenzioni identiche al resto del
progetto: CGT 33%, esenzione 1.270 EUR l'anno, riporto perdite, imposte pagate
liquidando quote, costo di transazione 0,15% round-trip sui versamenti.
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

ROUND = 70
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
ANNI = 20
M = ANNI * 12
STOP_M = 24          # durata dell'interruzione
QUOTA = 0.30         # riscatto anticipato


def pac(rets, dates, salta=None, riscatta=None, contrib=C.MONTHLY_CONTRIB):
    """PAC ventennale con eventuale interruzione dei versamenti e/o riscatto.

    salta    (inizio, durata) in mesi: nessun versamento in quella finestra
    riscatta mese in cui si preleva QUOTA del portafoglio (flusso POSITIVO)
    """
    val = bas = 0.0
    year_gain = carry = 0.0
    anno = dates[0].year
    cfs = []
    for i, t in enumerate(dates):
        if t.year != anno:
            tass = max(0.0, year_gain - carry)
            carry -= min(carry, max(0.0, year_gain))
            if year_gain < 0:
                carry += -year_gain
            dovuta = max(0.0, tass - C.CGT_EXEMPT_ANNUAL) * C.CGT_RATE
            paga = min(val, max(0.0, dovuta))
            if val > 0:
                f = paga / val
                val -= paga
                bas -= bas * f
            year_gain = 0.0
            anno = t.year
        salto = salta is not None and salta[0] <= i < salta[0] + salta[1]
        if not salto:
            costo = contrib * (C.COST_ROUND_TRIP / 2.0)
            val += contrib - costo
            bas += contrib - costo
            cfs.append((t, -contrib))
        if riscatta is not None and i == riscatta and val > 0:
            preso = val * QUOTA
            year_gain += preso - bas * QUOTA
            bas -= bas * QUOTA
            val -= preso
            cfs.append((t, preso))
        val *= (1.0 + float(rets[i]))
    year_gain += val - bas
    tass = max(0.0, max(0.0, year_gain - carry) - C.CGT_EXEMPT_ANNUAL)
    fin = val - tass * C.CGT_RATE
    cfs.append((dates[-1], fin))
    return dict(finale=fin,
                irr=_xirr([d for d, _ in cfs], [a for _, a in cfs]) * 100,
                versato=sum(-a for _, a in cfs if a < 0))


def main():
    ffm = dataio.ff_factors_monthly()
    mkt = (ffm["Mkt-RF"] + ffm["RF"]).dropna()
    mkt = mkt[mkt.index.year <= FINE]
    idx = pd.DatetimeIndex(mkt.index).to_period("M").to_timestamp("M")
    r = mkt.to_numpy(dtype=float)

    starts = [i for i in range(0, len(r) - M + 1, 12)]
    print(f"{'=' * 100}\nK2 — il PAC che si interrompe, e quello che si "
          f"riscatta in anticipo\n{'=' * 100}")
    print(f"   {len(starts)} finestre ventennali del mercato USA, "
          f"{idx[0].year}-{FINE}. Holdout NON toccato.")
    print(f"   Interruzione di {STOP_M} mesi, riscatto del "
          f"{QUOTA * 100:.0f}%.\n")

    base = [pac(r[s:s + M], idx[s:s + M]) for s in starts]
    b_irr = np.array([x["irr"] for x in base])
    b_fin = np.array([x["finale"] for x in base])
    print(f"   PAC di riferimento: IRR mediana {np.median(b_irr):.2f}%, "
          f"montante mediano €{np.median(b_fin):,.0f} "
          f"su €{base[0]['versato']:,.0f} versati\n")

    righe = []
    print(f"   {'anno k':>7} | {'INTERRUZIONE 24 mesi':^38} | "
          f"{'RISCATTO 30%':^30}")
    print(f"   {'':>7} | {'d IRR (mediana)':>16}{'d montante':>13}"
          f"{'versato':>9} | {'d IRR (mediana)':>16}{'d montante':>14}")
    print("   " + "-" * 88)
    for k in range(1, 19):
        m0 = (k - 1) * 12
        di, dm, ri, rm = [], [], [], []
        for j, s in enumerate(starts):
            a = pac(r[s:s + M], idx[s:s + M], salta=(m0, STOP_M))
            di.append(a["irr"] - base[j]["irr"])
            dm.append(a["finale"] / base[j]["finale"] - 1)
            c = pac(r[s:s + M], idx[s:s + M], riscatta=m0)
            ri.append(c["irr"] - base[j]["irr"])
            rm.append(c["finale"] / base[j]["finale"] - 1)
        vers = pac(r[:M], idx[:M], salta=(m0, STOP_M))["versato"]
        righe.append(dict(k=k, d_irr=float(np.median(di)),
                          d_mont=float(np.median(dm)) * 100,
                          d_irr_max=float(np.max(np.abs(di))),
                          r_irr=float(np.median(ri)),
                          r_mont=float(np.median(rm)) * 100,
                          versato=vers))
        x = righe[-1]
        print(f"   {k:>7} | {x['d_irr']:>+15.3f}{x['d_mont']:>+12.2f}%"
              f"{vers / base[0]['versato'] * 100:>8.0f}% | "
              f"{x['r_irr']:>+15.3f}{x['r_mont']:>+13.2f}%")

    # ------------------------------------------------------------- verdetto
    di = np.array([x["d_irr"] for x in righe])
    dm = np.array([x["d_mont"] for x in righe])
    dimax = max(x["d_irr_max"] for x in righe)
    ri = np.array([x["r_irr"] for x in righe])
    mono = bool(np.all(np.diff(dm) > 0))     # calo che si attenua al crescere di k
    primi10 = ri[:10]

    print(f"\n{'=' * 100}\n   VERDETTO\n{'=' * 100}")
    print(f"   Predizione: l'interruzione costa MENO di 0,3 punti di IRR "
          f"ovunque, il montante cala del")
    print(f"   8-12% in modo MONOTONO in k, e il riscatto colpisce l'IRR di "
          f"OLTRE 0,5 punti nei primi dieci anni.")
    print(f"   FALSIFICATA se l'interruzione sposta l'IRR di oltre 0,5 punti "
          f"in qualche k, OPPURE il calo")
    print(f"   del montante non e' monotono in k.\n")
    print(f"   interruzione, |d IRR| mediano max : {np.max(np.abs(di)):.3f} "
          f"punti   (previsto <0,3)")
    print(f"   interruzione, |d IRR| su OGNI finestra: {dimax:.3f} punti"
          f"   (falsifica sopra 0,5)")
    print(f"   interruzione, calo del montante   : da {dm.min():.2f}% a "
          f"{dm.max():.2f}%   (previsto −8/−12%)")
    print(f"   calo monotono in k                : "
          f"{'SI' if mono else 'NO'}   (falsifica se NO)")
    print(f"   riscatto, d IRR nei primi 10 anni : da {primi10.min():.3f} a "
          f"{primi10.max():.3f}   (previsto oltre −0,5)")

    fals = (dimax > 0.5) or (not mono)
    print(f"\n   -> ipotesi K2 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'interruzione sotto 0,3 punti': "
          f"{'centrata' if np.max(np.abs(di)) < 0.3 else 'SBAGLIATA'}")
    print(f"      clausola 'montante −8/−12%': "
          f"{'centrata' if -12.0 <= dm.min() and dm.max() <= -8.0 else 'SBAGLIATA'}")
    print(f"      clausola 'riscatto oltre −0,5 nei primi 10 anni': "
          f"{'centrata' if primi10.max() < -0.5 else 'SBAGLIATA'}")

    print(f"\n   Il confronto che la voce cercava:")
    print(f"     saltare 24 versamenti (10% del capitale) costa "
          f"{np.median(dm):.2f}% di montante e {np.median(di):+.3f} di IRR")
    print(f"     riscattare il 30% costa {np.median([x['r_mont'] for x in righe]):.2f}% "
          f"di montante e {np.median(ri):+.3f} di IRR")

    pd.DataFrame(righe).to_csv(OUT / "round70_k2.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="K2 PAC interrotto",
                         config=f"anno k={x['k']}", window=f"{idx[0].year}-{FINE}",
                         sharpe="", irr=x["d_irr"], bh_irr="", excess=x["d_mont"],
                         n_obs=len(starts),
                         note=f"riscatto_irr={x['r_irr']:.3f}") for x in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

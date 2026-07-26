"""Giro 21 — Ensemble di catene di Markov multi-profondita' e multi-etichetta.

L'IDEA (proposta dall'utente). Si discretizzano i rendimenti in L etichette
(binarie 0/1, oppure 5 stati: forte ribasso, ribasso, neutro, rialzo, forte
rialzo). Per ogni profondita' k (quante barre indietro) e ogni orizzonte h
(quante barre avanti) si stima P(stato futuro | contesto di k stati passati).
A ogni istante t l'ensemble produce molte previsioni condizionate, e il
segnale e' quella con probabilita' massima. Concettualmente e' il
riconoscimento di motivi nel genoma.

DUE DOMANDE, IN QUEST'ORDINE.

  1. ESISTE STRUTTURA? Prima di costruire qualunque segnale: la distribuzione
     del futuro condizionata al contesto e' diversa da quella incondizionata?
     Si misura con un test chi-quadro di indipendenza e con l'informazione
     mutua, contro un nulla ottenuto permutando le etichette. Se non c'e'
     struttura, ogni segnale costruito sopra e' rumore e il backtest lo
     mascherera' soltanto.

  2. SE ESISTE, SI PUO' SFRUTTARE? Solo allora ha senso il backtest
     walk-forward, con le probabilita' stimate SOLO sul passato.

ATTENZIONE AL 'PRENDO LA P MAGGIORE'. Massimizzare su un ensemble di stime
rumorose e' esattamente la selezione che il Deflated Sharpe deve penalizzare:
il massimo di N stime e' distorto verso l'alto. Conto quindi ogni combinazione
(k, h, L) come un tentativo, e riporto anche il numero effettivo di celle
stimate, che e' il vero conteggio delle ipotesi implicite.
"""
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from research import lab
from research.round15 import load, evaluate
from research.round19 import load_crypto

ROUND = 21
OUT = Path(__file__).resolve().parents[2] / "out"

DEPTHS = (1, 2, 3)
HORIZONS = (1, 2, 3, 5)
NLABELS = (2, 3, 5)
MIN_COUNT = 30          # celle con meno osservazioni non si usano


def labelise(ret, n, edges=None):
    """Discretizza in n etichette per quantili. Gli estremi si stimano SOLO
    sui dati passati quando `edges` e' fornito dal chiamante."""
    if edges is None:
        qs = np.linspace(0, 1, n + 1)[1:-1]
        edges = np.quantile(ret.dropna(), qs)
    return np.digitize(ret.to_numpy(), edges), edges


def contexts(labels, k):
    """Codifica il contesto delle k etichette precedenti come intero."""
    n = int(np.nanmax(labels)) + 1
    ctx = np.zeros(len(labels), dtype=np.int64)
    ok = np.ones(len(labels), dtype=bool)
    for j in range(k):
        sh = np.roll(labels, j + 1).astype(np.int64)
        ctx = ctx * n + sh
        ok[:j + 1] = False
    return ctx, ok


def structure_test(ret, k, h, n, n_perm=100, seed=0):
    """C'e' dipendenza fra contesto passato e stato futuro?

    Chi-quadro sulla tabella di contingenza, piu' informazione mutua
    confrontata con la distribuzione nulla ottenuta permutando il futuro.
    La permutazione e' il nulla giusto: conserva le distribuzioni marginali
    e distrugge solo l'associazione.
    """
    lab_now, edges = labelise(ret, n)
    fwd = ret.rolling(h).sum().shift(-h)          # rendimento futuro su h
    lab_fwd, _ = labelise(fwd, n, edges * h)
    ctx, ok = contexts(lab_now, k)
    m = ok & np.isfinite(fwd.to_numpy())
    a, b = ctx[m], lab_fwd[m]
    if len(a) < 200:
        return None
    tab = pd.crosstab(a, b)
    tab = tab[tab.sum(axis=1) >= MIN_COUNT]
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return None
    chi = st.chi2_contingency(tab.to_numpy())
    mi = float(st.contingency.association(tab.to_numpy(), method="cramer"))
    # nullo per permutazione, con bincount invece di crosstab: stesso
    # risultato, due ordini di grandezza piu' veloce
    keep = set(tab.index.tolist())
    mk = np.array([x in keep for x in a])
    a2, b2 = a[mk], b[mk]
    ai = pd.factorize(a2)[0]
    bi = pd.factorize(b2)[0]
    na, nb = ai.max() + 1, bi.max() + 1
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    for z in range(n_perm):
        bp = rng.permutation(bi)
        t2 = np.bincount(ai * nb + bp, minlength=na * nb).reshape(na, nb)
        chi2 = st.chi2_contingency(t2 + 1e-9)[0]
        null[z] = np.sqrt(chi2 / (t2.sum() * (min(na, nb) - 1)))
    pperm = float((null >= mi).mean()) if len(null) else np.nan
    return dict(k=k, h=h, n=n, cells=int(tab.shape[0] * tab.shape[1]),
                obs=int(tab.to_numpy().sum()), chi2_p=float(chi.pvalue),
                cramer_v=mi, null_mean=float(null.mean()) if len(null) else np.nan,
                p_perm=pperm)


def run_market(name, ret, ppy):
    print(f"\n{'='*80}\n{name}   {len(ret)} osservazioni, "
          f"{ret.index[0].date()} -> {ret.index[-1].date()}")
    print("=" * 80)
    print("\n1. ESISTE STRUTTURA CONDIZIONALE?\n")
    print(f"{'k':>3}{'h':>3}{'L':>3}{'celle':>8}{'oss.':>8}{'Cramer V':>11}"
          f"{'V nullo':>10}{'p perm.':>10}{'chi2 p':>10}")
    res = []
    for k, h, n in product(DEPTHS, HORIZONS, NLABELS):
        r = structure_test(ret, k, h, n)
        if r is None:
            continue
        res.append(r)
        print(f"{k:>3}{h:>3}{n:>3}{r['cells']:>8}{r['obs']:>8}"
              f"{r['cramer_v']:>11.4f}{r['null_mean']:>10.4f}"
              f"{r['p_perm']:>10.3f}{r['chi2_p']:>10.3f}")
    d = pd.DataFrame(res)
    d["market"] = name
    n_test = len(d)
    sig = d[d["p_perm"] < 0.05]
    exp_false = 0.05 * n_test
    print(f"\n  Combinazioni testate: {n_test}")
    print(f"  Con p permutazionale < 0,05: {len(sig)}   "
          f"(falsi positivi attesi per solo caso: {exp_false:.1f})")
    if len(sig):
        print(f"  Le significative: "
              f"{', '.join(f'k{r.k}h{r.h}L{r.n}' for r in sig.itertuples())}")
    # Cramer V medio contro il nullo: e' la sintesi
    print(f"  Cramer V medio osservato {d['cramer_v'].mean():.4f} "
          f"contro nullo {d['null_mean'].mean():.4f} "
          f"(rapporto {d['cramer_v'].mean()/d['null_mean'].mean():.2f}x)")
    return d


def main():
    out = []
    ffd = dataio.ff_factors_daily()
    out.append(run_market("Indice CRSP giornaliero 1926-2026",
                          (ffd["Mkt-RF"] + ffd["RF"]).dropna(), 252))
    q = load("QQQ", "1day")
    out.append(run_market("QQQ giornaliero 2006-2026",
                          q.close.pct_change().dropna(), 252))
    try:
        btc = load_crypto("BTCUSDT")
        out.append(run_market("BTC giornaliero 2017-2026",
                              btc.close.pct_change().dropna(), 365))
    except FileNotFoundError:
        pass

    d = pd.concat(out, ignore_index=True)
    d.to_csv(OUT / "round21_markov_structure.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="H22 ensemble catene di Markov",
                         config=f"{r['market']}|k{r['k']}h{r['h']}L{r['n']}",
                         window="struttura", sharpe="", irr="", bh_irr="",
                         excess="", n_obs=r["obs"],
                         note=f"V={r['cramer_v']:.4f},p={r['p_perm']:.3f}")
                    for _, r in d.iterrows()])

    print(f"\n{'='*80}\nSINTESI SU TUTTI I MERCATI\n{'='*80}")
    print(f"{'mercato':<38}{'test':>7}{'p<0,05':>9}{'attesi':>9}{'V/V0':>8}")
    for mk, g in d.groupby("market"):
        print(f"{mk[:37]:<38}{len(g):>7}{int((g['p_perm']<0.05).sum()):>9}"
              f"{0.05*len(g):>9.1f}"
              f"{g['cramer_v'].mean()/g['null_mean'].mean():>8.2f}")
    tot_sig = int((d["p_perm"] < 0.05).sum())
    print(f"\nTotale: {tot_sig} significative su {len(d)} test, "
          f"{0.05*len(d):.1f} attese per solo caso.")
    print(f"Tentativi cumulati a registro: {lab.n_trials_so_far()}")
    return d


if __name__ == "__main__":
    main()

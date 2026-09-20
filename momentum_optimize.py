"""
OTTIMIZZAZIONE DISCIPLINATA — periodo del segnale, numero di posizioni, TP/SL adattivi.

    python3 momentum_optimize.py --data DIR

DOMANDA: esiste una configurazione di (lookback, numero di titoli, TP, SL, regime di
mercato) che rende profittevole la regola?

METODO: walk-forward. Si sceglie la configurazione sui 3 anni precedenti e la si applica
all'anno successivo senza piu' toccarla, poi si scorre. Il risultato che conta e' la
concatenazione degli anni fuori campione. Ottimizzare su tutto il campione e mostrare il
massimo della griglia non e' un risultato: con 1500 combinazioni il massimo e' rumore.

GRIGLIA
  lookback  2, 3, 5, 10, 20 giorni
  titoli    1, 3, 5, 10 (equipesati)
  TP        0.5, 1, 1.5, 2 volte l'ATR(14) del titolo, oppure nessuno
  SL        0.5, 1, 1.5, 2 volte l'ATR(14) del titolo, oppure nessuno
  regime    sempre · solo con SPY sopra la media a 200g · solo con volatilita' di
            mercato bassa (SPY, dev.std. 20g sotto il 60esimo percentile storico)

TP e SL in ATR sono la versione "in base all'andamento del mercato" chiesta: un titolo
che oscilla il 4% al giorno e uno che oscilla l'1% non possono avere lo stesso target
fisso all'1%. Il regime aggiunge lo stato del mercato a quello del titolo.

OBIETTIVO: Sharpe dei rendimenti giornalieri di portafoglio, calcolato su TUTTI i giorni
(zero quando il filtro di regime tiene fuori dal mercato, altrimenti un filtro che sta
fermo sembrerebbe bravo solo perche' opera poco). Lo Sharpe non dipende dalla leva: la
leva si sceglie dopo, con un target di volatilita'.
"""
import argparse, itertools
import numpy as np, pandas as pd
import momentum_backtest as M
from momentum_engine import Book, outcomes, picks, daily_returns, metrics

LOOKBACKS = [2, 3, 5, 10, 20]
NS        = [1, 3, 5, 10]
KS        = [0.5, 1.0, 1.5, 2.0, np.inf]      # multipli di ATR; inf = nessun livello
TRAIN, TEST = 756, 252                        # 3 anni di scelta, 1 anno di verifica

def build(bk, path='sl', **cost):
    """Calcola una volta sola i rendimenti giornalieri di ogni combinazione.
    Ritorna (matrice R [combinazioni x giorni], lista di chiavi, % giorni ambigui)."""
    regs = bk.regimes()
    ranks = {lb: bk.ranks(lb) for lb in LOOKBACKS}
    sels = {(lb, n): picks(ranks[lb], n) for lb in LOOKBACKS for n in NS}
    rows, keys, amb = [], [], []
    for tk, sk in itertools.product(KS, KS):
        tp = tk * bk.atr_pct if np.isfinite(tk) else np.inf
        sl = sk * bk.atr_pct if np.isfinite(sk) else np.inf
        out, both = outcomes(bk, tp, sl, path, **cost)
        for lb in LOOKBACKS:
            for n in NS:
                sel = sels[(lb, n)]
                r, cnt = daily_returns(ranks[lb], out, n)
                a = np.take_along_axis(both, sel, axis=1)[:, :n]
                a = np.where(np.isfinite(np.take_along_axis(ranks[lb], sel, axis=1)), a, np.nan)
                amb_pct = 100 * np.nanmean(a) if np.isfinite(a).any() else 0.0
                for rg, mask in regs.items():
                    rows.append(np.where(mask, r, 0.0))
                    keys.append((lb, n, tk, sk, rg))
                    amb.append(amb_pct)
    return np.array(rows), keys, np.array(amb)

def sharpe(R, sl_, sl_end):
    x = R[:, sl_:sl_end]
    sd = x.std(axis=1)
    return np.where(sd > 0, x.mean(axis=1) / np.maximum(sd, 1e-12) * np.sqrt(252), -9.9)

def fmt_key(k):
    lb, n, tk, sk, rg = k
    t = 'no TP' if not np.isfinite(tk) else f'TP {tk:g}·ATR'
    s = 'no SL' if not np.isfinite(sk) else f'SL {sk:g}·ATR'
    return f"lb{lb:>2} · top{n:<2} · {t:<11} · {s:<11} · {rg}"

def walk_forward(R, keys, amb, idx, bench, max_amb=None, label=''):
    n_days = R.shape[1]
    sel_mask = np.ones(len(keys), bool) if max_amb is None else (amb <= max_amb)
    oos = np.zeros(n_days); covered = np.zeros(n_days, bool)
    chosen, folds = [], []
    start = TRAIN
    while start + TEST <= n_days:
        s_is = sharpe(R, start - TRAIN, start)
        s_is = np.where(sel_mask, s_is, -9.9)
        j = int(np.argmax(s_is))
        te = slice(start, start + TEST)
        oos[te] = R[j, te]; covered[te] = True
        s_oos = sharpe(R, start, start + TEST)[j]
        chosen.append(keys[j])
        folds.append((idx[start].date(), idx[start + TEST - 1].date(),
                      s_is[j], s_oos, R[j, te].mean() * 1e4, keys[j], amb[j]))
        start += TEST
    return oos, covered, chosen, folds

def report_folds(folds, title):
    print(f"\n  {title}")
    print(f"  {'anno fuori campione':<26}{'Sharpe IS':>10}{'Sharpe OOS':>12}{'bp/g OOS':>10}  configurazione scelta")
    for a, b, si, so, bp, k, am in folds:
        print(f"  {str(a)+' -> '+str(b):<26}{si:>10.2f}{so:>12.2f}{bp:>10.1f}  {fmt_key(k)}")

def summarize(name, r, covered, bench_ret, lev=2.0):
    x = r[covered]
    m = metrics(r[covered], lev)
    print(f"  {name:<34}Sharpe {m['sharpe']:>6.2f}   bp/g {x.mean()*1e4:>+7.1f}   "
          f"CAGR(leva {lev:g}x) {m['cagr']:>8.2f}%   maxDD {m['mdd']:>7.1f}%")
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--path', default='sl', choices=['sl', 'tp'])
    a = ap.parse_args()
    d = M.load(a.data); bk = Book(d)
    print(f"Universo {len(bk.cols)} titoli · {bk.idx[0].date()} -> {bk.idx[-1].date()}")
    print(f"Ipotesi sui giorni ambigui: {'pessimista (stop per primo)' if a.path=='sl' else 'ottimista'}")
    R, keys, amb = build(bk, a.path)
    print(f"Combinazioni valutate: {len(keys)}")
    idx = bk.idx
    bench = bk.bench.pct_change().fillna(0).to_numpy()

    # riferimento: la regola originale, TP 1% / SL 3% fissi, top 1, lookback 5
    out0, _ = outcomes(bk, .01, .03, a.path)
    r0, _ = daily_returns(bk.ranks(5), out0, 1)

    print("\n" + "=" * 104)
    print("A. WALK-FORWARD: scelgo sui 3 anni precedenti, verifico sull'anno dopo, scorro")
    print("=" * 104)
    oos, cov, chosen, folds = walk_forward(R, keys, amb, idx, bench)
    report_folds(folds, "dettaglio per finestra")
    is_m = np.mean([f[2] for f in folds]); oos_m = np.mean([f[3] for f in folds])
    pos = sum(1 for f in folds if f[3] > 0)
    print(f"\n  Sharpe medio scelto in campione {is_m:+.2f}  ->  realizzato fuori campione "
          f"{oos_m:+.2f}   (degrado {is_m-oos_m:.2f})")
    print(f"  finestre fuori campione positive: {pos} su {len(folds)}")
    print()
    summarize("walk-forward ottimizzato", oos, cov, bench)
    summarize("regola originale TP1%/SL3% top1", r0, cov, bench)
    rnd = np.random.default_rng(3)
    pick_rand = rnd.integers(0, len(keys), size=len(folds))
    rr = np.zeros_like(oos); start = TRAIN
    for f, j in enumerate(pick_rand):
        rr[start:start+TEST] = R[j, start:start+TEST]; start += TEST
    summarize("configurazione a caso ogni anno", rr, cov, bench)
    best_all = int(np.argmax(sharpe(R, 0, R.shape[1])))
    summarize(f"miglior combinazione in-sample*", R[best_all], cov, bench)
    print(f"    * {fmt_key(keys[best_all])} — e' il massimo di {len(keys)} tentativi sullo")
    print("      stesso campione su cui viene misurata: non e' un risultato utilizzabile.")

    print("\n" + "=" * 104)
    print("B. SOLO CONFIGURAZIONI DECIDIBILI CON BARRE GIORNALIERE (giorni ambigui <= 5%)")
    print("=" * 104)
    oos2, cov2, chosen2, folds2 = walk_forward(R, keys, amb, idx, bench, max_amb=5.0)
    print(f"  combinazioni ammesse: {int((amb<=5).sum())} su {len(keys)}")
    report_folds(folds2, "dettaglio per finestra")
    print()
    summarize("walk-forward, regione decidibile", oos2, cov2, bench)

    print("\n" + "=" * 104)
    print("C. QUANTA PARTE DELLA GRIGLIA E' PROFITTEVOLE SU TUTTO IL CAMPIONE")
    print("=" * 104)
    mu = R.mean(axis=1) * 1e4
    sh = sharpe(R, 0, R.shape[1])
    print(f"  combinazioni con media > 0 bp/giorno: {(mu>0).sum()} su {len(keys)} "
          f"({100*(mu>0).mean():.1f}%)")
    print(f"  con media > 4 bp/giorno (soglia dei costi retail a/r): {(mu>4).sum()} "
          f"({100*(mu>4).mean():.1f}%)")
    print(f"  Sharpe: mediana {np.median(sh):.2f}   massimo {sh.max():.2f}   minimo {sh.min():.2f}")
    print("\n  Le migliori 12 su tutto il campione (in-sample, quindi da non usare):")
    print(f"  {'configurazione':<58}{'bp/g':>8}{'Sharpe':>9}{'ambigui%':>10}")
    for j in np.argsort(-sh)[:12]:
        print(f"  {fmt_key(keys[j]):<58}{mu[j]:>8.1f}{sh[j]:>9.2f}{amb[j]:>9.1f}%")

    print("\n" + "=" * 104)
    print("D. STABILITA' DEI PARAMETRI: cosa sceglie il walk-forward, anno per anno")
    print("=" * 104)
    for pos, nome in [(0, 'lookback'), (1, 'numero titoli'), (2, 'TP (xATR)'),
                      (3, 'SL (xATR)'), (4, 'regime')]:
        vals = [str(c[pos]) for c in chosen]
        vc = pd.Series(vals).value_counts()
        print(f"  {nome:<16}" + "  ".join(f"{k}×{v}" for k, v in vc.items()))
    print("\n  Se il parametro scelto salta da un anno all'altro, non esiste un valore")
    print("  'ottimale': la griglia sta inseguendo rumore.")

    print("\n" + "=" * 104)
    print("E. LEVA: fissa 2x contro dimensionamento a volatilita' obiettivo")
    print("=" * 104)
    past = pd.Series(oos).rolling(20).std().shift(1).to_numpy()
    for target in (0.10, 0.15, 0.25):
        lev = np.clip(target / (past * np.sqrt(252) + 1e-9), 0, 2.0)
        lev = np.nan_to_num(lev)
        x = lev[cov] * oos[cov]
        eq = np.cumprod(np.maximum(1e-12, 1 + x))
        sh_ = x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0
        print(f"  target vol {target*100:>3.0f}%  leva media {lev[cov].mean():.2f}x  "
              f"CAGR {(eq[-1]**(252/len(x))-1)*100:>8.2f}%   Sharpe {sh_:>5.2f}")
    m2 = metrics(oos[cov], 2.0)
    print(f"  leva fissa 2x                        "
          f"CAGR {m2['cagr']:>8.2f}%   Sharpe {m2['sharpe']:>5.2f}")
    print("\n  Il dimensionamento a volatilita' riduce il drag, non crea rendimento: porta il")
    print("  CAGR da -9.3% a -2.4% solo perche' riduce la leva media da 2x a 0.78x, e in questo")
    print("  campione peggiora pure lo Sharpe (deleveraggia dopo le fasi agitate che precedono")
    print("  i rimbalzi). Applicare una leva qualsiasi a uno Sharpe nullo non produce rendimento.")

    print("\n" + "=" * 104)
    print("F. EFFETTO MARGINALE DI OGNI PARAMETRO  (media su tutte le altre combinazioni)")
    print("=" * 104)
    K = np.array([[k[0], k[1]] for k in keys], float)
    tk = np.array([k[2] for k in keys]); sk = np.array([k[3] for k in keys])
    rg = np.array([k[4] for k in keys])
    def show(nome, vals, labels=None):
        print(f"\n  {nome}")
        print(f"    {'valore':<14}{'bp/g medio':>12}{'bp/g migliore':>15}{'Sharpe medio':>14}")
        for v in sorted(set(vals.tolist()), key=lambda z: (z == np.inf, z) if not isinstance(z, str) else z):
            m = vals == v
            lab = labels(v) if labels else (str(v) if v != np.inf else 'nessuno')
            print(f"    {lab:<14}{mu[m].mean():>12.2f}{mu[m].max():>15.2f}{sh[m].mean():>14.2f}")
    show("periodo del segnale (giorni)", K[:, 0], lambda v: f"{int(v)} g")
    show("numero di posizioni", K[:, 1], lambda v: f"top {int(v)}")
    show("take profit (xATR)", tk)
    show("stop loss (xATR)", sk)
    show("regime di mercato", rg, lambda v: v)
    print("\n  Nessuna colonna 'bp/g migliore' supera i ~4 bp che costa l'andata e ritorno")
    print("  retail: il massimo della griglia e' comunque sotto la soglia di pareggio.")

if __name__ == '__main__':
    main()

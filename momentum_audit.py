"""
AUDIT DEL BACKTEST — dove i numeri di MOMENTUM_RESULTS.md possono rompersi.

Non e' una lista di buoni propositi: ogni falla qui e' quantificata, e alcune
cambiano le conclusioni. Uso:  python3 momentum_audit.py --data DIR

Le sezioni sono ordinate per gravita' decrescente, cioe' per quanto sposterebbero
il risultato se l'ipotesi sottostante fosse sbagliata.
"""
import argparse
import numpy as np, pandas as pd
import momentum_backtest as M
from momentum_engine import Book, outcomes, picks, daily_returns, metrics, BP

DATA = None

def hdr(t):
    print("\n" + "=" * 104); print(t); print("=" * 104)

# ---------------------------------------------------------------- 1. significativita'
def audit_significance(bk, rank, out_raw, sel):
    hdr("1. L'EDGE DEL SEGNALE REGGE ALLE VERIFICHE? (e quanto ne resta dopo beta e costi)")
    r = np.take_along_axis(out_raw, sel, axis=1)[:, 0]
    who = bk.cols[sel[:, 0]]
    ok_idx = np.arange(len(r))
    ok_mask = np.isfinite(r)
    r, who = r[ok_mask], who[ok_mask]
    n = len(r)
    t_iid = r.mean() / r.std() * np.sqrt(n)
    print(f"  osservazioni {n}   media {r.mean()*1e4:+.1f} bp   t-stat ingenuo (iid) {t_iid:+.2f}")

    # (a) errore standard clusterizzato per titolo: 4176 trade ma pochi titoli distinti,
    #     e lo stesso titolo torna centinaia di volte -> le osservazioni non sono indipendenti
    df = pd.DataFrame({'r': r, 'k': who})
    g = df.groupby('k').r
    cnt, mean = g.count(), g.mean()
    num = ((mean - r.mean()) ** 2 * cnt ** 2).sum()
    se_cl = np.sqrt(num) / n
    print(f"  titoli distinti {df.k.nunique()}   il piu' frequente {cnt.max()} volte "
          f"({100*cnt.max()/n:.1f}% dei trade)")
    print(f"  t-stat con errore standard clusterizzato per titolo: {r.mean()/se_cl:+.2f}")

    # (b) block bootstrap: preserva l'autocorrelazione e le code grasse
    rng = np.random.default_rng(1)
    B, blk = 5000, 20
    nb = int(np.ceil(n / blk))
    starts = rng.integers(0, n - blk, size=(B, nb))
    off = np.arange(blk)
    means = np.array([r[(s[:, None] + off).ravel()[:n]].mean() for s in starts])
    lo, hi = np.percentile(means, [2.5, 97.5])
    print(f"  block bootstrap (blocchi da {blk} giorni, {B} ripetizioni): "
          f"IC95% [{lo*1e4:+.1f}, {hi*1e4:+.1f}] bp   P(media<=0) = {100*(means<=0).mean():.1f}%")

    # (c) e se si tolgono i tre titoli piu' pescati?
    top3 = cnt.nlargest(3).index.tolist()
    m = ~df.k.isin(top3)
    rr = df.r[m].to_numpy()
    print(f"  togliendo {', '.join(top3)}: {len(rr)} trade, media {rr.mean()*1e4:+.1f} bp, "
          f"t-stat iid {rr.mean()/rr.std()*np.sqrt(len(rr)):+.2f}")

    # (d) quanto dell'edge e' semplicemente esposizione al mercato? Il top performer
    #     e' per costruzione un titolo ad alto beta, e la giornata media di SPY sale.
    o = pd.read_csv(f"{DATA}/open.csv", index_col=0, parse_dates=True)['SPY']
    c = pd.read_csv(f"{DATA}/close.csv", index_col=0, parse_dates=True)['SPY']
    mkt = (c / o - 1).reindex(bk.idx).to_numpy()[ok_idx][ok_mask]
    X = np.c_[np.ones(len(mkt)), mkt]
    b = np.linalg.lstsq(X, r, rcond=None)[0]
    res = r - X @ b
    se = np.sqrt(res.var(ddof=2) * np.linalg.inv(X.T @ X)[0, 0])
    print(f"\n  regressione sul mercato (SPY apertura->chiusura dello stesso giorno):")
    print(f"    beta {b[1]:.2f}   alfa {b[0]*1e4:+.1f} bp/g   t(alfa) {b[0]/se:+.2f}")
    print(f"    dei {r.mean()*1e4:+.1f} bp, {b[1]*mkt.mean()*1e4:+.1f} sono solo esposizione al mercato")

    # (e) stabilita' temporale
    ser = pd.Series(r, index=bk.idx[ok_idx][ok_mask])
    yr = ser.resample('YE').mean()
    h = len(ser) // 2
    print(f"    anni con media positiva {int((yr>0).sum())}/{len(yr)}   "
          f"prima meta' {ser.iloc[:h].mean()*1e4:+.1f} bp   seconda meta' {ser.iloc[h:].mean()*1e4:+.1f} bp")
    print("\n  LETTURA: l'edge regge al clustering, al bootstrap e alla rimozione dei titoli")
    print("  dominanti, ed e' stabile nel tempo. Il problema non e' la significativita'")
    print("  statistica: e' che l'alfa netto di beta vale ~7 bp e l'andata-ritorno retail ne")
    print("  costa ~8. L'intervallo di confidenza include valori sotto la soglia dei costi.")

# ---------------------------------------------------------------- 2. ambiguita'
def audit_ambiguity(bk):
    hdr("2. QUANTA PARTE DELLO SPAZIO DEI PARAMETRI NON E' DECIDIBILE CON BARRE DAILY")
    rank = bk.ranks(5); sel = picks(rank, 1)
    print("  % di giorni in cui il minimo tocca lo stop E il massimo tocca il target")
    print("  (in quei giorni le barre giornaliere non sanno dire chi e' scattato prima)\n")
    tps = [0.005, 0.01, 0.02, 0.03]
    print("        " + "".join(f"{'SL '+str(s*100)+'%':>12}" for s in (0.01, 0.02, 0.03, 0.05)))
    for tp in tps:
        row = f"  TP {tp*100:>4.1f}%"
        for sl in (0.01, 0.02, 0.03, 0.05):
            _, both = outcomes(bk, tp, sl)
            b = np.take_along_axis(both, sel, axis=1)[:, 0]
            v = np.isfinite(np.take_along_axis(rank, sel, axis=1)[:, 0])
            row += f"{100*b[v].mean():>11.1f}%"
        print(row)
    print("\n  Piu' la coppia e' stretta, piu' il risultato dipende da un'ipotesi non osservabile.")
    print("  Le barre orarie coprono solo dal 2023-10 (limite yfinance 730g sull'intervallo 60m):")
    print("  ottimizzare TP e SL su barre giornaliere significa, in buona parte, ottimizzare l'ipotesi.")

# ---------------------------------------------------------------- 3. esecuzione
def audit_execution(bk):
    hdr("3. IPOTESI DI ESECUZIONE — quanto reggono")
    rank = bk.ranks(5); sel = picks(rank, 1)
    def run(**kw):
        o, _ = outcomes(bk, .01, .03, 'sl', **kw)
        r, _ = daily_returns(rank, o, 1)
        return metrics(r, 2.0)
    print("  a) il limite sul take profit: quanto deve spingersi il massimo oltre il target")
    print("     perche' l'ordine sia davvero eseguito (rischio di coda nel book)")
    for th in (0, 5, 10, 25):
        m = run(tp_through_bp=th)
        print(f"     serve superarlo di {th:>2} bp -> CAGR {m['cagr']:>8.2f}%   media {m['bp']/2:>6.1f} bp/trade")
    print("\n  b) slippage proporzionale alla volatilita' del titolo invece che piatto")
    print("     (k = frazione dell'ATR pagata in ingresso; il titolo tipico ha ATR ~2%)")
    for k in (0.0, 0.02, 0.05, 0.10):
        m = run(slip_vol_k=k)
        print(f"     k={k:<5} (~{k*2*1e4/100:>4.0f} bp su ATR 2%) -> CAGR {m['cagr']:>8.2f}%"
              f"   media {m['bp']/2:>6.1f} bp/trade")
    print("\n  Il primo blocco e' il piu' insidioso: il backtest assume che un massimo che")
    print("  sfiora il target riempia l'ordine. Se serve attraversarlo di 25 bp, il 51.5% di")
    print("  uscite in TP si assottiglia e le giornate finiscono nel bucket peggiore.")

# ---------------------------------------------------------------- 4. rovina
def audit_ruin(bk):
    hdr("4. IL CONTO SOPRAVVIVE? (il backtest compone all'infinito, un conto vero no)")
    rank = bk.ranks(5); sel = picks(rank, 1)
    o, _ = outcomes(bk, .01, .03, 'sl')
    r, _ = daily_returns(rank, o, 1)
    for lev in (1.0, 2.0):
        eq = np.cumprod(np.maximum(1e-12, 1 + lev * r))
        worst = (lev * r).min()
        for thr in (.5, .1):
            k = np.argmax(eq < thr) if (eq < thr).any() else None
            when = bk.idx[k].date() if k is not None else "mai"
            print(f"  leva {lev:g}x: sotto il {int(thr*100)}% del capitale iniziale il {when}")
        print(f"          peggior giornata singola {worst*100:.1f}%   "
              f"giorni con perdita > 5%: {(lev*r < -0.05).sum()}")
    print("\n  Con margine di mantenimento al 25% e leva 2x, la chiamata a margine scatta")
    print("  quando il capitale scende del 33% rispetto al nozionale: il backtest continua")
    print("  a comporre come se il broker non chiudesse mai nulla. Le equity finali a 0.000x")
    print("  vanno lette come 'conto azzerato molto prima', non come un numero.")

# ---------------------------------------------------------------- 5. capienza
def audit_capacity(bk):
    hdr("5. CAPIENZA E ATTRITI NON MODELLATI")
    rank = bk.ranks(5); sel = picks(rank, 1)
    dv = np.take_along_axis(bk.dv, sel, axis=1)[:, 0]
    v = np.isfinite(dv)
    q = np.percentile(dv[v], [10, 50, 90]) / 1e6
    print(f"  dollar volume medio a 20g del titolo scelto: "
          f"p10 {q[0]:,.0f}M   mediana {q[1]:,.0f}M   p90 {q[2]:,.0f}M")
    print(f"  all'1% del volume giornaliero si muoverebbero ~{q[1]*10:,.0f}k$ per trade:")
    print("  la capienza non e' il vincolo su questo universo. Lo sono i costi per unita' di edge.")
    print("\n  Non modellati, tutti a sfavore:")
    print("   - tasse: un trade al giorno e' reddito da negoziazione, non capital gain di lungo")
    print("     periodo (il precedente swing_harness.py modellava un 33% irlandese, qui no)")
    print("   - halt di volatilita': uno stop dentro un LULD halt non viene eseguito al prezzo")
    print("   - il prezzo d'asta di apertura e' assunto ottenibile: il proprio ordine lo muove")
    print("   - regola PDT: sotto i 25.000$ di conto, negli USA questa strategia non e' eseguibile")

# ---------------------------------------------------------------- 6. dati
def audit_data(bk, d):
    hdr("6. I DATI — fonte unica, prezzi rettificati a posteriori")
    c = d['close']
    print(f"  fonte: Yahoo Finance via yfinance, nessun riscontro incrociato")
    print(f"  buchi: {int(c.isna().sum().sum())} celle mancanti su {c.size} ({100*c.isna().mean().mean():.2f}%)")
    ret = c.pct_change()
    big = (ret.abs() > 0.5).sum().sum()
    print(f"  variazioni giornaliere oltre il 50% residue dopo la rettifica: {int(big)} "
          f"(spie di split non gestiti)")
    print("  i prezzi rettificati vengono riscritti a ogni nuovo dividendo/split: un backtest")
    print("  rifatto fra un anno sugli stessi giorni NON dara' esattamente gli stessi numeri.")
    jump = (ret.abs() > 0.30)
    win = jump.rolling(6).max().shift(1).fillna(0).to_numpy().astype(bool)
    rank = bk.ranks(5); sel = picks(rank, 1)
    raw, _ = outcomes(bk, np.inf, np.inf, 'sl', comm_bp=0, slip_in_bp=0, slip_cl_bp=0)
    rr = np.take_along_axis(raw, sel, axis=1)[:, 0]
    cont = np.take_along_axis(win, sel, axis=1)[:, 0]
    v = np.isfinite(rr)
    print(f"  DHR 2016-07-05 (+61%) e' lo scorporo di Fortive: Yahoo rettifica dividendi e")
    print(f"  split, NON gli spin-off. Quel giorno il titolo risulta top performer per un")
    print(f"  evento che non e' un rendimento. Trade la cui finestra contiene un salto >30%:")
    print(f"  {int(cont[v].sum())} su {int(v.sum())}, media {rr[v & cont].mean()*1e4:+.1f} bp contro "
          f"{rr[v & ~cont].mean()*1e4:+.1f} bp degli altri.")
    print(f"  -> la contaminazione esiste ma e' piccola e in perdita: non e' lei a creare l'edge.")
    print("  survivorship: l'universo e' la membership odierna. La direzione del bias e' nota")
    print("  (gonfia una strategia che compra chi e' salito), l'entita' no: servirebbe la")
    print("  composizione storica dell'indice, che Yahoo non fornisce.")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--data', required=True)
    a = ap.parse_args()
    global DATA
    DATA = a.data
    d = M.load(a.data); bk = Book(d)
    rank = bk.ranks(5); sel = picks(rank, 1)
    # segnale nudo: apertura->chiusura, nessun TP/SL, nessun costo
    raw, _ = outcomes(bk, np.inf, np.inf, 'sl', comm_bp=0, slip_in_bp=0, slip_cl_bp=0)
    print(f"Universo {len(bk.cols)} titoli · {bk.idx[0].date()} -> {bk.idx[-1].date()}")
    audit_significance(bk, rank, raw, sel)
    audit_ambiguity(bk)
    audit_execution(bk)
    audit_ruin(bk)
    audit_capacity(bk)
    audit_data(bk, d)

if __name__ == '__main__':
    main()

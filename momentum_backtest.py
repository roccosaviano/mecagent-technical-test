"""
BACKTEST: MOMENTUM CROSS-SECTIONALE A 5 GIORNI, LONG 2x CON TP 1% / SL 3%
=========================================================================
Regola testata (quella chiesta, senza aggiustamenti di comodo):

    A inizio giornata guardo i top performer della rolling window dei 5 giorni
    precedenti, apro un long a leva 2x, take-profit +1%, stop-loss -3%.

Uso:
    python3 momentum_backtest.py --data DIR            # caso base
    python3 momentum_backtest.py --data DIR --report   # tutte le tabelle

COME E' IMPLEMENTATA (i dettagli che decidono il risultato)
  - Universo: S&P 100. E' un universo a membership ODIERNA, quindi c'e'
    survivorship bias: i titoli usciti dall'indice non ci sono. Su una strategia
    che compra chi e' appena salito il bias gonfia i rendimenti, non li deprime.
  - Segnale: r5 = AdjClose[t-1]/AdjClose[t-6] - 1. Usa SOLO chiusure note prima
    dell'apertura di t. Nessun look-ahead.
  - OHLC rettificati moltiplicando O/H/L/C per (AdjClose/Close): senza questo uno
    split 4:1 sembra un -75% e uno split inverso un top performer.
  - Ingresso: apertura di t (prezzo pagato = Open * (1+slippage)).
  - TP e SL sono calcolati sul prezzo di RIEMPIMENTO, non sull'apertura teorica.
  - Barre giornaliere: se nello stesso giorno il minimo tocca lo stop E il massimo
    tocca il target, l'ordine degli eventi e' ignoto. Non si indovina: si riportano
    entrambi gli estremi (SL-first = pessimista, TP-first = ottimista) e si risolve
    l'ambiguita' con barre orarie (--intraday) sul periodo dove sono disponibili.
  - Uscita a fine giornata se non scatta nulla (e' una regola intraday: "a inizio
    giornata apro", nessun overnight). Con --hold N si tiene fino a N giorni,
    pagando il finanziamento della leva e subendo il gap risk sull'apertura.

COSTI (tutti parametrici, --report ne stressa cinque scenari)
  - commissione 1 bp per lato sul nozionale
  - slippage 3 bp in ingresso (ordine a mercato sull'apertura)
  - il TP e' un limite: riempie AL prezzo, zero slippage, ma serve che il massimo
    lo attraversi (rischio di coda in book)
  - lo stop e' un mercato: 8 bp avversi, di piu' se il gap lo salta
  - leva 2x => costi e slippage contano il DOPPIO sul capitale

RISULTATO (dettagli e tabelle in MOMENTUM_RESULTS.md)
  S&P 100, 2010-2026, 4176 trade: -63.8% annuo nell'ipotesi pessimista, -5.0% in quella
  ottimista, -35.3% col percorso vero ricostruito a barre orarie. Il buy&hold su SPY fa
  +14.6%. Il win rate e' 64%: non e' un errore, e' quello che produce un target piccolo
  con uno stop grande.

  Il segnale non e' il colpevole: comprare l'apertura del top performer e vendere la
  chiusura, senza TP/SL, rende +9.8 bp al giorno con t-stat 2.68. A ucciderlo sono, in
  ordine: (1) il TP a +1% sta dentro l'escursione intraday tipica (+1.71%/-1.59%) e
  tronca ogni vincita, mentre lo stop a -3% sta fuori e non tronca nulla; (2) la leva 2x
  su un titolo con vol 2.37% giornaliera produce 11 bp di volatility drag al giorno,
  piu' dell'edge lordo; (3) i costi retail si mangiano 8 dei 9.8 bp rimasti.
  Comprare un titolo a caso, con le stesse regole di uscita, perde MENO della strategia.
"""
import argparse, os, sys
import numpy as np, pandas as pd

# ------------------------------------------------------------------ parametri
class Cfg:
    lookback   = 5        # giorni della rolling window del segnale
    top_n      = 1        # quanti top performer comprare
    lev        = 2.0      # leva
    tp         = 0.01     # take profit sul prezzo
    sl         = 0.03     # stop loss sul prezzo
    hold       = 1        # giorni massimi di detenzione (1 = intraday)
    comm_bp    = 1.0      # commissione per lato, bp di nozionale
    slip_in_bp = 3.0      # slippage ingresso a mercato
    slip_st_bp = 8.0      # slippage aggiuntivo sull'uscita in stop
    slip_cl_bp = 3.0      # slippage uscita a mercato in chiusura
    fin_ann    = 0.060    # costo annuo del denaro preso a prestito con la leva
    min_dv     = 20e6     # filtro liquidita': dollar volume medio 20g
    path       = 'sl'     # 'sl' = pessimista, 'tp' = ottimista (giorni ambigui)

BP = 1e-4

# ------------------------------------------------------------------ dati
def load(dirpath):
    px = {f: pd.read_csv(f"{dirpath}/{f}.csv", index_col=0, parse_dates=True)
          for f in ('open', 'high', 'low', 'close', 'adj_close', 'volume')}
    adj = px['adj_close'] / px['close']          # fattore split+dividendi
    out = {k: px[k] * adj for k in ('open', 'high', 'low', 'close')}
    out['volume'] = px['volume']
    out['dollar_vol'] = px['close'] * px['volume']
    # scarto colonne completamente vuote (ticker non piu' quotati su Yahoo)
    keep = out['close'].notna().sum() > 250
    bench = out['close']['SPY'].copy()
    for k in out:
        out[k] = out[k].loc[:, keep].drop(columns=['SPY'], errors='ignore')
    out['bench'] = bench
    return out

# ------------------------------------------------------------------ segnale
def signal_rank(d, cfg):
    """Ritorna, per ogni giorno t, la lista dei ticker ordinati per r5 decrescente.
    r5 usa chiusure fino a t-1: e' noto prima dell'apertura di t."""
    c = d['close']
    r = c.shift(1) / c.shift(1 + cfg.lookback) - 1        # gia' laggato di 1
    liq = d['dollar_vol'].rolling(20).mean().shift(1)
    valid = (r.notna() & (liq > cfg.min_dv)
             & d['open'].notna() & d['high'].notna() & d['low'].notna() & d['close'].notna())
    return r.where(valid)

# ------------------------------------------------------------------ singolo trade
def simulate_trade(d, tkr, i, cfg, path=None):
    """Esegue un trade aperto all'apertura del giorno i.
    Ritorna (ret_prezzo, esito, giorni_tenuti). Il ret include lo slippage ma NON
    commissioni, leva e finanziamento, che si applicano a monte."""
    path = path or cfg.path
    o, h, l, c = d['open'][tkr], d['high'][tkr], d['low'][tkr], d['close'][tkr]
    fill = o.iloc[i] * (1 + cfg.slip_in_bp * BP)
    tp_px, sl_px = fill * (1 + cfg.tp), fill * (1 - cfg.sl)

    for k in range(i, min(i + cfg.hold, len(o))):
        hi, lo = h.iloc[k], l.iloc[k]
        if k > i:                                    # gap sull'apertura: lo stop non protegge
            op = o.iloc[k]
            if op <= sl_px:
                return op * (1 - cfg.slip_st_bp * BP) / fill - 1, 'gap_sl', k - i + 1
            if op >= tp_px:
                return op / fill - 1, 'gap_tp', k - i + 1
        hit_tp, hit_sl = hi >= tp_px, lo <= sl_px
        if hit_tp and hit_sl:                        # giorno ambiguo con barre daily
            if path == 'tp':
                return tp_px / fill - 1, 'tp_amb', k - i + 1
            return sl_px * (1 - cfg.slip_st_bp * BP) / fill - 1, 'sl_amb', k - i + 1
        if hit_tp:
            return tp_px / fill - 1, 'tp', k - i + 1
        if hit_sl:
            return sl_px * (1 - cfg.slip_st_bp * BP) / fill - 1, 'sl', k - i + 1
    k = min(i + cfg.hold, len(o)) - 1
    return c.iloc[k] * (1 - cfg.slip_cl_bp * BP) / fill - 1, 'close', k - i + 1

# ------------------------------------------------------------------ backtest
def backtest(d, cfg, start=None, end=None, pick='top', resolver=None):
    """pick: 'top' | 'bottom' | 'random'. resolver: funzione(tkr, data) -> 'tp'|'sl'
    per risolvere i giorni ambigui con dati intraday veri."""
    r = signal_rank(d, cfg)
    idx = d['close'].index
    lo_i = max(cfg.lookback + 21, idx.searchsorted(pd.Timestamp(start)) if start else 0)
    hi_i = idx.searchsorted(pd.Timestamp(end)) if end else len(idx) - cfg.hold
    rng = np.random.default_rng(7)

    eq, curve, log = 1.0, [], []
    for i in range(lo_i, min(hi_i, len(idx) - cfg.hold + 1)):
        row = r.iloc[i].dropna()
        if len(row) < 20:
            curve.append((idx[i], eq)); continue
        if pick == 'top':      names = row.nlargest(cfg.top_n).index
        elif pick == 'bottom': names = row.nsmallest(cfg.top_n).index
        else:                  names = rng.choice(row.index, size=min(cfg.top_n, len(row)), replace=False)

        rets = []
        for tkr in names:
            p = resolver(tkr, idx[i]) if resolver else None
            g, tag, days = simulate_trade(d, tkr, i, cfg, path=p)
            # il finanziamento si paga solo sulle notti effettivamente passate in posizione
            fin = cfg.fin_ann / 252 * (cfg.lev - 1) / cfg.lev * (days - 1)
            net = g - 2 * cfg.comm_bp * BP - fin
            rets.append(net)
            log.append(dict(date=idx[i], tkr=tkr, r5=row[tkr], gross=g, net=net, tag=tag))
        step = cfg.lev * float(np.mean(rets))
        eq *= max(1e-9, 1 + step)                    # 1+step<0 = conto azzerato
        curve.append((idx[i], eq))
    curve = pd.Series(dict(curve)).sort_index()
    return curve, pd.DataFrame(log)

# ------------------------------------------------------------------ metriche
def stats(curve, log, d=None):
    if len(curve) < 2: return {}
    ret = curve.pct_change().dropna()
    yrs = (curve.index[-1] - curve.index[0]).days / 365.25
    final = curve.iloc[-1]
    cagr = (final ** (1 / yrs) - 1) * 100 if final > 0 else -100.0
    dd = (curve / curve.cummax() - 1).min() * 100
    sh = ret.mean() / ret.std() * np.sqrt(252) if ret.std() > 0 else 0
    t = log.net if len(log) else pd.Series([0.0])
    w, ls = t[t > 0], t[t <= 0]
    return dict(final=final, cagr=cagr, mdd=dd, sharpe=sh, ntrade=len(t),
                win=100 * len(w) / max(1, len(t)), avg=t.mean() * 100,
                avg_w=w.mean() * 100 if len(w) else 0, avg_l=ls.mean() * 100 if len(ls) else 0,
                pf=w.sum() / abs(ls.sum()) if len(ls) and ls.sum() != 0 else np.inf,
                years=yrs)

def benchmark(d, curve):
    b = d['bench'].reindex(curve.index).ffill()
    b = b / b.iloc[0]
    yrs = (b.index[-1] - b.index[0]).days / 365.25
    return dict(final=b.iloc[-1], cagr=(b.iloc[-1] ** (1 / yrs) - 1) * 100,
                mdd=(b / b.cummax() - 1).min() * 100,
                sharpe=b.pct_change().mean() / b.pct_change().std() * np.sqrt(252))

def line(name, s):
    if not s: return f"{name:<34} (nessun trade)"
    return (f"{name:<34}{s['final']:>9.3f}x{s['cagr']:>9.2f}%{s['mdd']:>9.1f}%"
            f"{s['sharpe']:>8.2f}{s['win']:>8.1f}%{s['avg']*100:>10.1f}{s['pf']:>7.2f}{s['ntrade']:>8d}")

HDR = (f"{'':<34}{'equity':>10}{'CAGR':>10}{'maxDD':>10}{'Sharpe':>8}{'win%':>9}"
       f"{'avg bp':>10}{'PF':>7}{'trade':>8}")

# ------------------------------------------------------------------ risoluzione intraday
def load_60m(dirpath):
    """Barre orarie grezze (non rettificate): servono solo per l'ORDINE degli eventi
    dentro la seduta, e i rapporti infragiornalieri non risentono di split/dividendi."""
    import glob
    bars = {}
    for f in glob.glob(f"{dirpath}/*.csv"):
        t = os.path.basename(f)[:-4]
        df = pd.read_csv(f, index_col=0)
        ts = pd.to_datetime(df.index, utc=True).tz_convert('America/New_York')
        df.index = ts
        df['d'] = ts.date
        bars[t] = df
    return bars

def resolve_intraday(bars, tkr, day, cfg):
    """Ritorna 'tp' | 'sl' | None (nessun dato / ancora ambiguo dentro l'ora)."""
    df = bars.get(tkr)
    if df is None: return None
    s = df[df.d == day.date()]
    if len(s) < 2: return None
    fill = s.Open.iloc[0] * (1 + cfg.slip_in_bp * BP)
    tp_px, sl_px = fill * (1 + cfg.tp), fill * (1 - cfg.sl)
    for _, b in s.iterrows():
        hit_tp, hit_sl = b.High >= tp_px, b.Low <= sl_px
        if hit_tp and hit_sl: return None      # ambiguita' residua dentro l'ora
        if hit_tp: return 'tp'
        if hit_sl: return 'sl'
    return 'close'

def run_intraday(d, cfg, dirpath):
    bars = load_60m(dirpath)
    days = sorted({dd for df in bars.values() for dd in set(df.d)})
    start = pd.Timestamp(days[0]) + pd.Timedelta(days=1)
    print("\n" + "=" * 112)
    print(f"RISOLUZIONE DELL'AMBIGUITA' CON BARRE ORARIE VERE  ({start.date()} -> {days[-1]})")
    print("=" * 112)

    # 1) come si risolvono, di fatto, i giorni in cui daily tocca sia TP che SL
    cfg.path = 'sl'
    _, l = backtest(d, cfg, start=start)
    amb = l[l.tag.isin(['sl_amb', 'tp_amb'])]
    res = [resolve_intraday(bars, r.tkr, r.date, cfg) for r in amb.itertuples()]
    n = len(res); ok = [x for x in res if x]
    tp_first = sum(1 for x in ok if x == 'tp')
    print(f"giorni ambigui nel periodo: {n}   risolti con barre orarie: {len(ok)}"
          f"   ancora ambigui dentro l'ora: {n - len(ok)}")
    if ok:
        print(f"  -> TP per primo: {tp_first}/{len(ok)} ({100*tp_first/len(ok):.0f}%)   "
              f"SL per primo: {len(ok)-tp_first}/{len(ok)} ({100*(len(ok)-tp_first)/len(ok):.0f}%)")
    print("\nStesso periodo, stessa regola, tre ipotesi di percorso:")
    print(HDR)
    for tag, p in (('daily · SL-first (pessimista)', 'sl'), ('daily · TP-first (ottimista)', 'tp')):
        cfg.path = p
        c, l2 = backtest(d, cfg, start=start)
        print(line(tag, stats(c, l2)))
    cfg.path = 'sl'
    def resolver(tkr, day):
        r = resolve_intraday(bars, tkr, day, cfg)
        return r if r in ('tp', 'sl') else 'sl'   # irrisolti -> ipotesi prudente
    c, l3 = backtest(d, cfg, start=start, resolver=resolver)
    print(line('orario · percorso reale', stats(c, l3)))
    b = benchmark(d, c)
    print(f"{'SPY buy & hold (1x, no costi)':<34}{b['final']:>9.3f}x{b['cagr']:>9.2f}%"
          f"{b['mdd']:>9.1f}%{b['sharpe']:>8.2f}")
    return c, l3


def run_signal_edge(d, cfg):
    """Il segnale, nudo: compro l'apertura e vendo la chiusura. Nessun TP/SL, nessun costo,
    nessuna leva. Serve a sapere se il problema e' CHI si compra o COME si esce."""
    r = signal_rank(d, cfg)
    o, c, h, l = d['open'], d['close'], d['high'], d['low']
    oc = c / o - 1
    rows = []
    for i in range(cfg.lookback + 21, len(r)):
        row = r.iloc[i].dropna()
        if len(row) < 20: continue
        t, b = row.idxmax(), row.idxmin()
        rows.append((r.index[i], oc[t].iloc[i], oc[b].iloc[i], oc.iloc[i].mean(),
                     h[t].iloc[i] / o[t].iloc[i] - 1, l[t].iloc[i] / o[t].iloc[i] - 1))
    df = pd.DataFrame(rows, columns=['date', 'top', 'bottom', 'univ', 'hi', 'lo']).set_index('date')
    print("\n" + "=" * 112)
    print("IL SEGNALE NUDO  —  apertura->chiusura, senza TP/SL, senza costi, senza leva")
    print("=" * 112)
    print(f"{'':<34}{'bp/giorno':>12}{'t-stat':>9}{'annuo':>10}{'vol g.':>9}{'Sharpe':>9}")
    for k, nm in (('top', 'top performer 5g'), ('bottom', 'bottom performer 5g'),
                  ('univ', 'media dell universo')):
        s = df[k].dropna()
        t = s.mean() / s.std() * np.sqrt(len(s))
        sh = s.mean() / s.std() * np.sqrt(252)
        print(f"{nm:<34}{s.mean()*1e4:>+11.1f}{t:>9.2f}{s.mean()*252*100:>9.1f}%"
              f"{s.std()*100:>8.2f}%{sh:>9.2f}")
    print(f"\nescursione intraday media del titolo scelto: massimo {df.hi.mean()*100:+.2f}%  "
          f"minimo {df.lo.mean()*100:+.2f}%   -> il TP a +1% sta DENTRO l'escursione tipica,")
    print("lo stop a -3% sta fuori: il target tronca quasi ogni vincita, lo stop non tronca quasi nulla")
    print(f"\nmedia bp/giorno per anno:")
    y = (df.top.resample('YE').mean() * 1e4).rename(lambda x: x.year)
    print("  " + "  ".join(f"{i}:{v:+.0f}" for i, v in y.items()))
    return df

def run_exits(d, cfg):
    print("\n" + "=" * 112)
    print(f"STRUTTURA DI USCITA  —  stesso segnale, stessa leva {cfg.lev:g}x, stessi costi. "
          "Cambia solo dove metto TP e SL")
    print("=" * 112)
    print(f"{'':<32}{'CAGR pess.':>12}{'CAGR ott.':>12}{'equity pess.':>14}{'win%':>8}"
          f"{'avg bp pess.':>14}{'ambigui%':>10}")
    tp0, sl0 = cfg.tp, cfg.sl
    combos = [('nessun TP/SL (chiusura)', 9.9, 9.9), ('TP +1% / SL -3%  (la regola)', .01, .03),
              ('TP +1% / SL -1%', .01, .01), ('TP +2% / SL -2%', .02, .02),
              ('TP +3% / SL -1%  (invertita)', .03, .01), ('TP +3% / SL -3%', .03, .03),
              ('solo TP +1%', .01, 9.9), ('solo SL -3%', 9.9, .03),
              ('TP +1% / SL -10%', .01, .10)]
    for nm, tp, sl in combos:
        cfg.tp, cfg.sl = tp, sl
        res = {}
        for p in ('sl', 'tp'):
            cfg.path = p
            c, l = backtest(d, cfg)
            res[p] = (c, l, stats(c, l))
        s, so = res['sl'][2], res['tp'][2]
        amb = 100 * res['sl'][1].tag.isin(['sl_amb', 'tp_amb']).mean()
        print(f"{nm:<32}{s['cagr']:>11.2f}%{so['cagr']:>11.2f}%{s['final']:>13.3f}x"
              f"{s['win']:>7.1f}%{s['avg']*100:>14.1f}{amb:>10.1f}")
    cfg.tp, cfg.sl, cfg.path = tp0, sl0, 'sl'
    print("\n'pess.' = nei giorni in cui daily tocca sia TP che SL assumo che sia scattato lo stop;")
    print("'ott.' = assumo il target. Il vero valore sta in mezzo (vedi sezione barre orarie).")


def run_selftest(d, cfg):
    """Controllo anti-look-ahead. Se al segnale si concede di vedere la chiusura DI OGGI
    il backtest deve esplodere. Se non esplode, il motore sta sbagliando qualcosa."""
    import momentum_backtest as M
    c = Cfg(); c.tp = c.sl = 9.9; c.lev = 1.0
    orig = M.signal_rank
    def peek(d, cfg):
        cl = d['close']; r = cl / cl.shift(cfg.lookback) - 1
        liq = d['dollar_vol'].rolling(20).mean().shift(1)
        v = (r.notna() & (liq > cfg.min_dv) & d['open'].notna() & d['high'].notna()
             & d['low'].notna() & d['close'].notna())
        return r.where(v)
    s0 = stats(*backtest(d, c))
    M.signal_rank = peek
    s1 = stats(*backtest(d, c))
    M.signal_rank = orig
    print("\n" + "=" * 112)
    print("AUTOTEST ANTI-LOOK-AHEAD  (top 1, nessun TP/SL, 1x, costi retail)")
    print("=" * 112)
    print(f"  segnale corretto, chiusure fino a t-1 : {s0['avg']*100:+7.1f} bp/g   CAGR {s0['cagr']:+9.2f}%")
    print(f"  segnale che sbircia la chiusura di t  : {s1['avg']*100:+7.1f} bp/g   CAGR {s1['cagr']:+9.2f}%")
    ok = s1['avg'] > s0['avg'] * 10
    print(f"  esito: {'OK' if ok else 'SOSPETTO'} — il segnale che sbircia deve staccare di ordini di grandezza")
    return ok


# ------------------------------------------------------------------ report
def run_base(d, cfg):
    print("\n" + "=" * 112)
    print("CASO BASE  —  compro l'apertura del top performer a 5 giorni, long 2x, TP +1% / SL -3%")
    print("=" * 112)
    print(HDR)
    out = {}
    for tag, p in (('SL-first (pessimista)', 'sl'), ('TP-first (ottimista)', 'tp')):
        cfg.path = p
        c, l = backtest(d, cfg)
        out[p] = (c, l)
        print(line(f"strategia · {tag}", stats(c, l)))
    b = benchmark(d, out['sl'][0])
    print(f"{'SPY buy & hold (1x, no costi)':<34}{b['final']:>9.3f}x{b['cagr']:>9.2f}%"
          f"{b['mdd']:>9.1f}%{b['sharpe']:>8.2f}")
    cfg.path = 'sl'
    l = out['sl'][1]
    mix = l.tag.value_counts(normalize=True) * 100
    amb = mix.get('sl_amb', 0) + mix.get('tp_amb', 0)
    print(f"\nesiti: " + "  ".join(f"{k}={v:.1f}%" for k, v in mix.items()))
    print(f"giornate ambigue (toccati sia TP che SL con barre daily): {amb:.1f}% dei trade"
          f"  -> e' la forchetta fra le due righe sopra")
    return out

def run_sensitivity(d, cfg):
    print("\n" + "=" * 112)
    print("SENSIBILITA' AI COSTI  (path = SL-first; a leva 2x ogni bp di costo pesa doppio)")
    print("=" * 112); print(HDR)
    base = (cfg.comm_bp, cfg.slip_in_bp, cfg.slip_st_bp, cfg.slip_cl_bp)
    for name, (cm, si, ss, sc) in [
            ('costi zero (irrealistico)',      (0, 0, 0, 0)),
            ('istituzionale  (0.5/1/3 bp)',    (0.5, 1, 3, 1)),
            ('retail buono   (1/3/8 bp)',      (1, 3, 8, 3)),
            ('retail tipico  (2/8/20 bp)',     (2, 8, 20, 8)),
            ('mercato ostile (3/15/40 bp)',    (3, 15, 40, 15))]:
        cfg.comm_bp, cfg.slip_in_bp, cfg.slip_st_bp, cfg.slip_cl_bp = cm, si, ss, sc
        c, l = backtest(d, cfg)
        print(line(name, stats(c, l)))
    cfg.comm_bp, cfg.slip_in_bp, cfg.slip_st_bp, cfg.slip_cl_bp = base

def run_controls(d, cfg):
    print("\n" + "=" * 112)
    print("CONTROLLI  —  il segnale 'top performer' aggiunge qualcosa rispetto al caso?")
    print("=" * 112); print(HDR)
    for name, pick in (('top 5g (la strategia)', 'top'),
                       ('bottom 5g (i peggiori)', 'bottom'),
                       ('ticker a caso', 'random')):
        c, l = backtest(d, cfg, pick=pick)
        print(line(name, stats(c, l)))
    print("\nStesse regole di TP/SL/leva/costi: la sola differenza e' CHI si compra.")

def run_grid(d, cfg):
    print("\n" + "=" * 112)
    print("ROBUSTEZZA  —  finestra del segnale e numero di titoli")
    print("=" * 112); print(HDR)
    lb0, tn0 = cfg.lookback, cfg.top_n
    for lb in (3, 5, 10, 20):
        for tn in (1, 3, 5, 10):
            cfg.lookback, cfg.top_n = lb, tn
            c, l = backtest(d, cfg)
            print(line(f"lookback {lb}g · top {tn}", stats(c, l)))
    cfg.lookback, cfg.top_n = lb0, tn0

def run_hold(d, cfg):
    print("\n" + "=" * 112)
    print("VARIANTE  —  tenere la posizione finche' non scatta TP o SL (gap overnight inclusi)")
    print("=" * 112); print(HDR)
    h0 = cfg.hold
    for h in (1, 2, 3, 5, 10):
        cfg.hold = h
        c, l = backtest(d, cfg)
        print(line(f"hold max {h} giorn{'o' if h==1 else 'i'}", stats(c, l)))
    cfg.hold = h0

def run_periods(d, cfg):
    print("\n" + "=" * 112)
    print("PER PERIODO  (in-sample / out-of-sample: non c'e' nessun parametro ottimizzato,")
    print("              ma se il segno cambia fra i due mezzi campioni non e' un edge stabile)")
    print("=" * 112); print(HDR)
    for name, s, e in (('2010-2017', '2010-01-01', '2018-01-01'),
                       ('2018-2026', '2018-01-01', None),
                       ('2010-2015', '2010-01-01', '2016-01-01'),
                       ('2016-2020', '2016-01-01', '2021-01-01'),
                       ('2021-2026', '2021-01-01', None)):
        c, l = backtest(d, cfg, start=s, end=e)
        print(line(name, stats(c, l)))
    print("\nPer anno solare (rendimento equity, path SL-first):")
    c, l = backtest(d, cfg)
    yr = c.resample('YE').last() / c.resample('YE').last().shift(1) - 1
    yr.iloc[0] = c.resample('YE').last().iloc[0] - 1
    print("  " + "  ".join(f"{i.year}:{v*100:+6.1f}%" for i, v in yr.items()))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True)
    ap.add_argument('--report', action='store_true')
    ap.add_argument('--top-n', type=int, default=Cfg.top_n)
    ap.add_argument('--lookback', type=int, default=Cfg.lookback)
    ap.add_argument('--hold', type=int, default=Cfg.hold)
    ap.add_argument('--lev', type=float, default=Cfg.lev)
    ap.add_argument('--intraday')
    ap.add_argument('--selftest', action='store_true')
    ap.add_argument('--save-log')
    a = ap.parse_args()
    cfg = Cfg(); cfg.top_n, cfg.lookback, cfg.hold, cfg.lev = a.top_n, a.lookback, a.hold, a.lev
    d = load(a.data)
    print(f"Universo: {d['close'].shape[1]} titoli   "
          f"Periodo: {d['close'].index[0].date()} -> {d['close'].index[-1].date()}   "
          f"({len(d['close'])} sedute)")
    print(f"Regola: lookback {cfg.lookback}g · top {cfg.top_n} · leva {cfg.lev}x · "
          f"TP +{cfg.tp*100:g}% · SL -{cfg.sl*100:g}% · hold {cfg.hold}g")
    out = run_base(d, cfg)
    if a.save_log:
        out['sl'][1].to_csv(a.save_log, index=False)
        out['sl'][0].to_csv(a.save_log.replace('.csv', '_equity.csv'))
    if a.intraday:
        run_intraday(d, cfg, a.intraday)
    if a.selftest:
        run_selftest(d, cfg)
    if a.report:
        run_signal_edge(d, cfg); run_exits(d, cfg)
        run_sensitivity(d, cfg); run_controls(d, cfg)
        run_grid(d, cfg); run_hold(d, cfg); run_periods(d, cfg)

if __name__ == '__main__':
    main()

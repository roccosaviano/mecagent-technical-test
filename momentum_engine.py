"""
MOTORE VETTORIZZATO — stesso modello di momentum_backtest.py, ma su matrici numpy.

Serve perche' esplorare una griglia di 1500 configurazioni con il ciclo Python del
primo backtest richiederebbe ore. Qui l'esito di ogni coppia (giorno, titolo) si
calcola in una passata su matrici (giorni x titoli), e la selezione dei top N e'
un argpartition. Una configurazione costa millisecondi.

Vincolo: solo hold = 1 giorno (la regola chiesta). Il multi-giorno resta in
momentum_backtest.py, dove il ciclo esplicito gestisce i gap di apertura.

CONTROLLO: engine_selftest() verifica che questo motore riproduca i numeri del
backtest a ciclo. Se i due divergono, uno dei due ha un bug e non ci si fida.
"""
import warnings
import numpy as np, pandas as pd
warnings.filterwarnings('ignore', 'All-NaN slice encountered')
BP = 1e-4

class Book:
    """Tutto cio' che non dipende dai parametri, precalcolato una volta sola."""
    def __init__(self, d, min_dv=20e6):
        self.idx = d['close'].index
        self.cols = np.array(d['close'].columns)
        self.O = d['open'].to_numpy(float)
        self.H = d['high'].to_numpy(float)
        self.L = d['low'].to_numpy(float)
        self.C = d['close'].to_numpy(float)
        prev_c = np.vstack([np.full((1, self.C.shape[1]), np.nan), self.C[:-1]])
        with np.errstate(invalid='ignore'):
            tr = np.nanmax(np.dstack([self.H - self.L,
                                      np.abs(self.H - prev_c),
                                      np.abs(self.L - prev_c)]), axis=2)
        # ATR(14) in percentuale del prezzo, noto a t-1: e' la misura di "quanto si
        # muove di solito questo titolo in una giornata" usata per TP/SL adattivi
        atr = pd.DataFrame(tr, index=self.idx).rolling(14).mean().to_numpy()
        self.atr_pct = np.roll(atr / self.C, 1, axis=0)
        self.atr_pct[0] = np.nan
        liq = d['dollar_vol'].rolling(20).mean().shift(1).to_numpy(float)
        self.ok = (np.isfinite(self.O) & np.isfinite(self.H) & np.isfinite(self.L)
                   & np.isfinite(self.C) & np.isfinite(self.atr_pct) & (liq > min_dv))
        self.dv = d['dollar_vol'].rolling(20).mean().shift(1).to_numpy(float)
        self.bench = d['bench'].reindex(self.idx).ffill()

    def ranks(self, lookback):
        """r5 (o r-lookback) laggato di 1: usa solo chiusure fino a t-1."""
        c = pd.DataFrame(self.C, index=self.idx)
        r = np.array((c.shift(1) / c.shift(1 + lookback) - 1).to_numpy(), dtype=float)
        r[~self.ok] = np.nan
        return r

    def regimes(self):
        b = self.bench
        ma200 = b.rolling(200).mean().shift(1)
        vol20 = b.pct_change().rolling(20).std().shift(1)
        calm = vol20 < vol20.expanding(500).quantile(.6)     # soglia storica, non futura
        return {'sempre': np.ones(len(b), bool),
                'SPY>MA200': (b.shift(1) > ma200).to_numpy(),
                'vol bassa': calm.fillna(False).to_numpy()}

def outcomes(bk, tp, sl, path='sl', comm_bp=1.0, slip_in_bp=3.0, slip_st_bp=8.0,
             slip_cl_bp=3.0, slip_vol_k=0.0, tp_through_bp=0.0):
    """Rendimento netto di prezzo per ogni (giorno, titolo), come se si comprasse
    l'apertura di quel giorno. tp/sl sono frazioni (scalari o matrici); np.inf = assente.

    slip_vol_k  : slippage aggiuntivo proporzionale all'ATR% (0 = slippage piatto).
                  Con k=0.05 un titolo che oscilla il 3% al giorno paga 15 bp in piu'.
    tp_through_bp: quanti bp oltre il target deve spingersi il massimo perche' il
                  limite sia considerato eseguito (rischio di coda nel book).
    """
    extra = slip_vol_k * bk.atr_pct if slip_vol_k else 0.0
    s_in = slip_in_bp * BP + extra
    s_st = slip_st_bp * BP + 2 * extra                  # lo stop paga il doppio: e' a mercato
    s_cl = slip_cl_bp * BP + extra
    fill = bk.O * (1 + s_in)
    tp_px = fill * (1 + tp)
    sl_px = fill * (1 - sl)
    hit_tp = bk.H >= tp_px * (1 + tp_through_bp * BP)
    hit_sl = bk.L <= sl_px
    r_tp = np.broadcast_to(np.asarray(tp, float), fill.shape)
    r_sl = sl_px * (1 - s_st) / fill - 1
    r_cl = bk.C * (1 - s_cl) / fill - 1
    both = hit_tp & hit_sl
    r = np.where(hit_tp, r_tp, np.where(hit_sl, r_sl, r_cl))
    r = np.where(both, r_sl if path == 'sl' else r_tp, r)
    r = r - 2 * comm_bp * BP
    r[~bk.ok] = np.nan
    return r, both

def picks(rank, n, largest=True):
    """Indici dei primi n titoli per giorno. NaN -> in fondo."""
    r = np.where(np.isfinite(rank), rank, -np.inf if largest else np.inf)
    order = np.argsort(-r if largest else r, axis=1, kind='stable')
    return order[:, :n]

def daily_returns(rank, out, n, mask=None, largest=True):
    """Rendimento di prezzo del portafoglio equipesato sui primi n, giorno per giorno."""
    sel = picks(rank, n, largest)
    vals = np.take_along_axis(out, sel, axis=1)
    valid = np.isfinite(np.take_along_axis(rank, sel, axis=1)) & np.isfinite(vals)
    cnt = valid.sum(1)
    r = np.where(valid, np.nan_to_num(vals), 0.0).sum(1) / np.maximum(cnt, 1)
    r[cnt == 0] = 0.0
    if mask is not None:
        r = np.where(mask, r, 0.0)
        cnt = np.where(mask, cnt, 0)
    return r, cnt

def equity(r, lev):
    return np.cumprod(np.maximum(1e-12, 1 + lev * r))

def metrics(r, lev, active=None, freq=252):
    """r = rendimenti di prezzo giornalieri del portafoglio, lev = leva applicata."""
    x = lev * r
    eq = np.cumprod(np.maximum(1e-12, 1 + x))
    n = len(x)
    act = np.ones(n, bool) if active is None else active
    ra = x[act]
    sh = ra.mean() / ra.std() * np.sqrt(freq) if len(ra) > 2 and ra.std() > 0 else 0.0
    cagr = eq[-1] ** (freq / n) - 1 if eq[-1] > 0 else -1.0
    dd = (eq / np.maximum.accumulate(eq) - 1).min()
    return dict(cagr=cagr * 100, sharpe=sh, mdd=dd * 100, final=eq[-1],
                bp=ra.mean() * 1e4 if len(ra) else 0.0, ndays=int(act.sum()),
                vol=ra.std() * np.sqrt(freq) * 100 if len(ra) else 0.0)

def engine_selftest(data_dir='data'):
    """Confronta motore vettorizzato e motore a ciclo sulla regola base.
    Devono coincidere trade per trade, altrimenti uno dei due sbaglia."""
    import momentum_backtest as M
    d = M.load(data_dir)
    cfg = M.Cfg(); cfg.path = 'sl'
    curve, log = M.backtest(d, cfg)
    bk = Book(d, cfg.min_dv)
    rank = bk.ranks(cfg.lookback)
    out, _ = outcomes(bk, cfg.tp, cfg.sl, 'sl', cfg.comm_bp, cfg.slip_in_bp,
                      cfg.slip_st_bp, cfg.slip_cl_bp)
    sel = picks(rank, 1)
    ref = log.set_index('date')
    same_name = diff = 0; worst = 0.0
    for t, row in ref.iterrows():
        i = bk.idx.get_loc(t)
        j = sel[i, 0]
        if bk.cols[j] == row.tkr:
            same_name += 1
            worst = max(worst, abs(out[i, j] - row.net))
        else:
            diff += 1
    print(f"selftest motore: {same_name} trade con lo stesso titolo, {diff} diversi, "
          f"massimo scarto sul rendimento netto {worst:.2e}")
    ok = diff == 0 and worst < 1e-12
    print("  esito:", "OK" if ok else "DIVERGENZA — non fidarsi dei risultati vettorizzati")
    return ok

if __name__ == '__main__':
    import sys
    engine_selftest(sys.argv[1] if len(sys.argv) > 1 else 'data')

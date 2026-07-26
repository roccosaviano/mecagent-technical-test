"""
BANCO DI PROVA SWING TRADING
============================
Uso:  python3 swing_harness.py dati.csv

Il CSV deve avere colonne: Date,Open,High,Low,Close  (giornaliere, ordine crescente)
Dove prenderle: yfinance (`pip install yfinance`), Stooq, o l'export del tuo broker.

    import yfinance as yf
    yf.download("SPY", start="1993-01-01").to_csv("dati.csv")

COSA FA
  - implementa 4 strategie swing documentate in letteratura (non inventate)
  - applica costi realistici + fiscalita' irlandese (CGT 33% su ogni trade chiuso)
  - divide il campione: prima meta' per scegliere i parametri, seconda meta' SOLO per validare
  - riporta le metriche che contano, incluso il confronto col buy&hold

REGOLA D'ORO: guarda solo la colonna OUT-OF-SAMPLE. Il resto e' rumore che ti piacera'.
"""
import sys, numpy as np, pandas as pd

COST_RT   = 0.0015     # spread + commissioni per andata+ritorno (0.15%)
CGT       = 0.33       # capital gain irlandese; metti 0.52 se temi la riqualificazione
FIN_ANN   = 0.058      # costo finanziamento leva (benchmark + spread)
LEVA      = 1.0        # alza solo dopo che la strategia funziona a 1x

# ---------------------------------------------------------------- indicatori
def rsi(s, n):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    return 100 - 100/(1 + up/dn.replace(0, np.nan))

def atr(df, n=14):
    tr = pd.concat([df.High-df.Low,
                    (df.High-df.Close.shift()).abs(),
                    (df.Low-df.Close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

# ---------------------------------------------------------------- strategie
# Ognuna restituisce una Serie di posizione desiderata (0 o 1) PER IL GIORNO DOPO.
# Lo shift(1) finale e' cio' che impedisce il look-ahead: decidi con la chiusura di
# ieri ed esegui all'apertura di oggi. Non toglierlo mai.

def s_rsi2(df, p):
    """Connors: mean reversion su ipervenduto, solo in trend rialzista."""
    ma  = df.Close.rolling(p['trend']).mean()
    r   = rsi(df.Close, 2)
    exit_ma = df.Close.rolling(p['exit']).mean()
    pos, on = [], False
    for i in range(len(df)):
        if not on and df.Close.iloc[i] > ma.iloc[i] and r.iloc[i] < p['entry']: on = True
        elif on and df.Close.iloc[i] > exit_ma.iloc[i]: on = False
        pos.append(1 if on else 0)
    return pd.Series(pos, index=df.index).shift(1).fillna(0)

def s_streak(df, p):
    """N giorni consecutivi di ribasso sopra la media lunga -> compra, esci al primo rialzo."""
    ma = df.Close.rolling(p['trend']).mean()
    down = (df.Close.diff() < 0).astype(int)
    streak = down * (down.groupby((down != down.shift()).cumsum()).cumcount() + 1)
    pos, on = [], False
    for i in range(len(df)):
        if not on and df.Close.iloc[i] > ma.iloc[i] and streak.iloc[i] >= p['days']: on = True
        elif on and df.Close.iloc[i] > df.Close.iloc[i-1]: on = False
        pos.append(1 if on else 0)
    return pd.Series(pos, index=df.index).shift(1).fillna(0)

def s_donchian(df, p):
    """Breakout stile turtle: compra il massimo a N giorni, esci al minimo a M."""
    hi = df.Close.rolling(p['inn']).max()
    lo = df.Close.rolling(p['out']).min()
    pos, on = [], False
    for i in range(len(df)):
        if not on and df.Close.iloc[i] >= hi.iloc[i]: on = True
        elif on and df.Close.iloc[i] <= lo.iloc[i]: on = False
        pos.append(1 if on else 0)
    return pd.Series(pos, index=df.index).shift(1).fillna(0)

def s_atr_stop(df, p):
    """Trend con stop mobile a N ATR: entra sopra la media, esci sullo stop."""
    ma = df.Close.rolling(p['trend']).mean()
    a  = atr(df, 14)
    pos, on, peak = [], False, 0.0
    for i in range(len(df)):
        c = df.Close.iloc[i]
        if not on and c > ma.iloc[i]: on, peak = True, c
        elif on:
            peak = max(peak, c)
            if c < peak - p['mult']*a.iloc[i]: on = False
        pos.append(1 if on else 0)
    return pd.Series(pos, index=df.index).shift(1).fillna(0)

STRATS = {
 'RSI2 mean-reversion': (s_rsi2,     [{'trend':t,'entry':e,'exit':x}
                                      for t in (100,200) for e in (5,10,15) for x in (5,10)]),
 'Down-streak reversal':(s_streak,   [{'trend':t,'days':d} for t in (100,200) for d in (2,3,4)]),
 'Donchian breakout':   (s_donchian, [{'inn':i,'out':o} for i in (20,50,100) for o in (10,20,50)]),
 'Trend + ATR stop':    (s_atr_stop, [{'trend':t,'mult':m} for t in (50,100,200) for m in (2,3,4)]),
}

# ---------------------------------------------------------------- valutazione
def evaluate(df, pos):
    ret  = df.Close.pct_change().fillna(0)
    turn = pos.diff().abs().fillna(pos.abs())
    gross = pos*ret*LEVA - turn*COST_RT/2 - (LEVA-1)*FIN_ANN/252*pos

    # tassa: applicata al risultato di ogni trade chiuso in utile
    eq, entry_eq, taxes, trades = 1.0, None, 0.0, []
    equity = []
    for i in range(len(pos)):
        if pos.iloc[i] > 0 and entry_eq is None: entry_eq = eq
        eq *= (1 + gross.iloc[i])
        if pos.iloc[i] == 0 and entry_eq is not None:
            pnl = eq/entry_eq - 1
            trades.append(pnl)
            if pnl > 0:
                t_ = (eq-entry_eq)*CGT; taxes += t_; eq -= t_
            entry_eq = None
        equity.append(eq)
    if entry_eq is not None and eq > entry_eq:
        t_ = (eq-entry_eq)*CGT; taxes += t_; eq -= t_
        equity[-1] = eq

    yrs = len(df)/252
    # drawdown sull'equity NETTA: il prelievo fiscale e' cassa che esce davvero,
    # misurarlo sulla curva lorda sottostima il calo che vedi sul conto.
    # (lo Sharpe resta sui rendimenti lordi: la tassa e' un evento puntuale,
    #  inserirla nella serie giornaliera ne falserebbe la volatilita')
    curve = pd.Series(equity, index=pos.index)
    dd = (curve/curve.cummax() - 1).min()
    tr = np.array(trades) if trades else np.array([0.0])
    wins, losses = tr[tr>0], tr[tr<=0]
    return dict(
        cagr   = (eq**(1/yrs)-1)*100,
        mdd    = dd*100,
        sharpe = gross.mean()/gross.std()*np.sqrt(252) if gross.std()>0 else 0,
        ntrade = len(tr), trades_yr = len(tr)/yrs,
        win    = 100*len(wins)/len(tr),
        expect = tr.mean()*100,
        pf     = wins.sum()/abs(losses.sum()) if len(losses) and losses.sum()!=0 else np.inf,
        inmkt  = 100*(pos>0).mean(), taxes=taxes)

def buyhold(df):
    yrs = len(df)/252
    g = df.Close.iloc[-1]/df.Close.iloc[0]
    net = 1 + (g-1)*(1-CGT)
    curve = df.Close/df.Close.iloc[0]
    return dict(cagr=(net**(1/yrs)-1)*100, mdd=(curve/curve.cummax()-1).min()*100)

# ---------------------------------------------------------------- main
def main(path):
    df = pd.read_csv(path, parse_dates=[0], index_col=0).sort_index()
    df.columns = [c.split('.')[0].capitalize() for c in df.columns]
    df = df[['Open','High','Low','Close']].dropna()
    split = len(df)//2
    ins, oos = df.iloc[:split], df.iloc[split:]
    print(f"\nDati: {df.index[0].date()} -> {df.index[-1].date()}  ({len(df)} sedute)")
    print(f"IN-SAMPLE  {ins.index[0].date()} -> {ins.index[-1].date()}")
    print(f"OUT-SAMPLE {oos.index[0].date()} -> {oos.index[-1].date()}")
    b1, b2 = buyhold(ins), buyhold(oos)
    print(f"\nBuy&hold  in-sample {b1['cagr']:6.2f}%  |  out-of-sample {b2['cagr']:6.2f}%  (DD {b2['mdd']:.1f}%)")
    print("\n" + "="*104)
    print(f"{'Strategia':<24}{'parametri':<26}{'IS cagr':>9}{'OOS cagr':>10}{'OOS DD':>9}"
          f"{'win%':>7}{'exp%':>8}{'PF':>7}{'tr/an':>7}")
    print("="*104)
    for name,(fn,grid) in STRATS.items():
        best, bp, best_sig = None, None, None
        for p in grid:                                    # ottimizzo SOLO in-sample
            # i segnali si calcolano sulla serie INTERA e poi si affettano: gli indicatori
            # guardano solo indietro, quindi non e' look-ahead. Calcolarli sulla sola fetta
            # oos sprecherebbe il warm-up (fino a 200 sedute cieche a inizio out-of-sample).
            sig = fn(df, p)
            m = evaluate(ins, sig.loc[ins.index])
            if best is None or m['cagr'] > best['cagr']: best, bp, best_sig = m, p, sig
        o = evaluate(oos, best_sig.loc[oos.index])        # e valido SOLO out-of-sample
        flag = " <-- batte B&H" if o['cagr'] > b2['cagr'] else ""
        print(f"{name:<24}{str(bp):<26}{best['cagr']:>8.2f}%{o['cagr']:>9.2f}%{o['mdd']:>8.1f}%"
              f"{o['win']:>6.1f}%{o['expect']:>7.2f}%{o['pf']:>7.2f}{o['trades_yr']:>7.1f}{flag}")
    print("="*104)
    print("""
COME LEGGERLO
  - Confronta la colonna OOS con il buy&hold out-of-sample. Solo quella conta.
  - Se una strategia brilla in-sample e crolla out-of-sample, i parametri erano curve-fitted.
  - Profit factor < 1.2 out-of-sample: il margine e' troppo sottile per sopravvivere
    a slippage reale e a un cambio di regime.
  - Prima di alzare LEVA, la strategia deve funzionare a 1x. La leva moltiplica un edge,
    non lo crea: se l'edge e' zero, moltiplicare zero da' zero e i costi restano.
  - Fai girare anche su altri sottostanti e altri periodi. Un edge che esiste solo su SPY
    e solo dopo il 2010 non e' un edge, e' una coincidenza che ti e' costata tempo.""")

if __name__ == '__main__':
    if len(sys.argv) < 2: print(__doc__); sys.exit(0)
    main(sys.argv[1])

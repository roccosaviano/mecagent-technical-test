"""Gruppo A: strategie swing su serie giornaliere.

VINCOLO DATI. Non ho potuto scaricare OHLC di SPY/QQQ/IWM/EFA/EEM/GLD/TLT
(Yahoo risponde 429, Stooq blocca con verifica anti-bot). Uso quindi le serie
giornaliere di Ken French, che sono dati CRSP reali:
  - indice total return del mercato USA value-weighted, 1926-2026
  - 49 portafogli settoriali value-weighted, stessa finestra
Sono rendimenti, non prezzi: costruisco l'indice componendoli. Conseguenza
importante: NON esistono massimo e minimo di giornata, quindi l'ATR non e'
calcolabile. La strategia 4 usa uno stop a N deviazioni standard close-to-close
al posto di N ATR, ed e' etichettata come tale ovunque.

Tutti i segnali finiscono con shift(1): la decisione usa la chiusura di t-1 e
l'esecuzione avviene a t. La funzione falsify_lookahead() verifica che il
controllo funzioni davvero.
"""
import numpy as np
import pandas as pd


# ---------------------------------------------------------------- indicatori
def rsi(close, n):
    d = np.diff(close, prepend=close[0])
    up = np.zeros_like(d)
    dn = np.zeros_like(d)
    a = 1.0 / n
    u = v = 0.0
    for i in range(1, len(d)):
        u = a * max(d[i], 0.0) + (1 - a) * u
        v = a * max(-d[i], 0.0) + (1 - a) * v
        up[i], dn[i] = u, v
    out = np.full(len(d), np.nan)
    nz = dn > 0
    out[nz] = 100 - 100 / (1 + up[nz] / dn[nz])
    out[(dn == 0) & (up > 0)] = 100.0
    return out


def _sma(x, n):
    s = pd.Series(x).rolling(n).mean().to_numpy()
    return s


def _rollmax(x, n):
    return pd.Series(x).rolling(n).max().to_numpy()


def _rollmin(x, n):
    return pd.Series(x).rolling(n).min().to_numpy()


# ---------------------------------------------------------------- strategie
# Ognuna riceve il vettore dei prezzi (indice total return) e restituisce la
# posizione DESIDERATA per il giorno dopo, gia' 0/1. Lo shift lo applica run().

def s_rsi2(close, p):
    ma, ex = _sma(close, p["trend"]), _sma(close, p["exit"])
    r = rsi(close, 2)
    pos = np.zeros(len(close))
    on = False
    for i in range(len(close)):
        if not on:
            if close[i] > ma[i] and r[i] < p["entry"]:
                on = True
        elif close[i] > ex[i]:
            on = False
        pos[i] = 1.0 if on else 0.0
    return pos


def s_streak(close, p):
    ma = _sma(close, p["trend"])
    d = np.diff(close, prepend=close[0])
    streak = np.zeros(len(close))
    c = 0
    for i in range(1, len(close)):
        c = c + 1 if d[i] < 0 else 0
        streak[i] = c
    pos = np.zeros(len(close))
    on = False
    for i in range(len(close)):
        if not on:
            if close[i] > ma[i] and streak[i] >= p["days"]:
                on = True
        elif d[i] > 0:
            on = False
        pos[i] = 1.0 if on else 0.0
    return pos


def s_donchian(close, p):
    hi, lo = _rollmax(close, p["inn"]), _rollmin(close, p["out"])
    pos = np.zeros(len(close))
    on = False
    for i in range(len(close)):
        if not on:
            if close[i] >= hi[i]:
                on = True
        elif close[i] <= lo[i]:
            on = False
        pos[i] = 1.0 if on else 0.0
    return pos


def s_trend_stop(close, p):
    """Stop mobile a N sigma close-to-close. SOSTITUISCE l'ATR: senza High/Low
    l'ATR non e' calcolabile, quindi uso la volatilita' EWMA dei rendimenti
    giornalieri moltiplicata per il prezzo. Non e' la strategia originale."""
    ma = _sma(close, p["trend"])
    ret = np.diff(close, prepend=close[0]) / np.maximum(close, 1e-12)
    sig = pd.Series(ret).ewm(span=14, adjust=False).std().to_numpy()
    band = sig * close
    pos = np.zeros(len(close))
    on, peak = False, 0.0
    for i in range(len(close)):
        if not on:
            if close[i] > ma[i]:
                on, peak = True, close[i]
        else:
            peak = max(peak, close[i])
            if close[i] < peak - p["mult"] * band[i]:
                on = False
        pos[i] = 1.0 if on else 0.0
    return pos


GRIDS = {
    "RSI2 mean-reversion": (s_rsi2, [{"trend": t, "entry": e, "exit": x}
                                     for t in (100, 200) for e in (5, 10, 15)
                                     for x in (5, 10)]),
    "Down-streak reversal": (s_streak, [{"trend": t, "days": d}
                                        for t in (100, 200) for d in (2, 3, 4)]),
    "Donchian breakout": (s_donchian, [{"inn": i, "out": o}
                                       for i in (20, 50, 100) for o in (10, 20, 50)]),
    "Trend + stop sigma (sostituto ATR)": (s_trend_stop, [{"trend": t, "mult": m}
                                           for t in (50, 100, 200) for m in (2, 3, 4)]),
}
N_COMBOS = {k: len(v[1]) for k, v in GRIDS.items()}


# ---------------------------------------------------------------- esecuzione
def build_index(ret):
    """Indice total return a base 100 da una serie di rendimenti giornalieri."""
    return 100.0 * (1.0 + ret.fillna(0.0)).cumprod()


def positions(fn, close_series, p):
    """Posizione eseguibile: decisa su t-1, applicata a t. Lo shift(1) e' qui
    ed e' l'unico punto in cui il segnale tocca il tempo."""
    raw = fn(close_series.to_numpy(dtype=float), p)
    return pd.Series(raw, index=close_series.index).shift(1).fillna(0.0)


def gross_stats(ret, pos, cost_rt):
    """Metriche lorde di imposta ma nette di costi, per la selezione in-sample."""
    turn = pos.diff().abs().fillna(pos.abs())
    net = pos * ret - turn * cost_rt / 2.0
    yrs = len(ret) / 252.0
    curve = (1 + net).cumprod()
    return {
        "cagr": (curve.iloc[-1] ** (1 / yrs) - 1) * 100 if curve.iloc[-1] > 0 else -100.0,
        "sharpe": (net.mean() / net.std() * np.sqrt(252)) if net.std() > 0 else np.nan,
        "dd": float((curve / curve.cummax() - 1).min()) * 100,
        "trades_yr": float((pos.diff() > 0).sum()) / yrs,
        "inmkt": float((pos > 0).mean()) * 100,
    }


# ---------------------------------------------------------------- falsificazione
def falsify_lookahead(ret, cost_rt=0.0015):
    """Controllo del controllo.

    Costruisce un segnale che conosce il rendimento di domani. Se il motore e'
    corretto, questo segnale deve produrre un risultato palesemente assurdo.
    Se invece assomiglia ai risultati delle strategie vere, allora il motore
    ha una fuga di informazione e i risultati non valgono nulla.
    """
    # Convenzione di gross_stats: pos[i] moltiplica ret[i]. Quindi il segnale
    # "baro" e' il segno del rendimento DI OGGI usato oggi, senza shift.
    # Il segnale onesto e' lo stesso, ritardato di un giorno: e' quello che
    # produce positions(), e non deve avere nessun potere predittivo.
    cheat = (ret > 0).astype(float)
    honest = cheat.shift(1).fillna(0.0)
    return {
        "con look-ahead": gross_stats(ret, cheat, cost_rt),
        "stesso segnale ritardato di 1": gross_stats(ret, honest, cost_rt),
    }

"""Prezzatura di opzioni su indice con Black-Scholes e VIX come implicita.

Non ho catene di strike: nessuna fonte gratuita mi da' i prezzi delle opzioni
sull'S&P. Quello che ho e' il VIX (dal 1990), il percorso dell'indice (Ken French
daily, dal 1926) e il risk-free (DFF). Con questi tre posso PREZZARE le opzioni
invece di comprare indici gia' confezionati, e quindi scegliere scadenza,
moneyness e struttura.

IL LIMITE, che decide come vanno letti tutti i risultati: UN SOLO VIX PER OGNI
STRIKE. Il VIX e' un tasso di variance swap a 30 giorni; usarlo come implicita di
qualunque strike equivale a ipotizzare la superficie di volatilita' PIATTA,
mentre sull'S&P le put OTM trattano sopra il VIX e le call OTM sotto.

  vendere put OTM     premio incassato SOTTOSTIMATO   -> conservativo
  comprare put OTM    costo SOTTOSTIMATO              -> ottimistico
  vendere call OTM    premio SOVRASTIMATO             -> ottimistico
  comprare call ATM   costo circa giusto              -> neutro
  deep ITM (LEAPS)    costo SOTTOSTIMATO              -> ottimistico

Il VIX e' anche leggermente sopra l'implicita ATM vera, perche' la formula del
variance swap pesa gli strike lontani: anche l'ATM e' quindi un filo caro.

E' il motivo per cui il gruppo E ha un cancello di calibrazione (E0): il
simulatore deve riprodurre BXM e PUT del CBOE, che sono strategie realmente
quotate, prima che i suoi numeri valgano qualcosa.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import dataio
from research import multidata as M
from research.round27 import cboe

TRADING_DAYS = 252


def bs(S, K, T, r, sigma, q=0.0, kind="c"):
    """Black-Scholes-Merton. T in anni, sigma annualizzata, q dividend yield."""
    S = np.asarray(S, dtype=float)
    K = np.asarray(K, dtype=float)
    T = np.maximum(np.asarray(T, dtype=float), 1e-9)
    sigma = np.maximum(np.asarray(sigma, dtype=float), 1e-6)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if kind == "c":
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)


def market_data(start="1990-01-01"):
    """Percorso dell'indice, VIX, risk-free giornaliero, tutti allineati.

    L'indice e' il total return del mercato USA di Ken French. Le opzioni
    sull'S&P sono su un indice di PREZZO, quindi tratto il dividendo come
    rendimento continuo q e uso il percorso di prezzo: e' l'ipotesi corretta per
    prezzare, e la parte da dividendo rientra separatamente nel rendimento di
    chi detiene il sottostante.
    """
    ffd = dataio.ff_factors_daily()
    tr = (ffd["Mkt-RF"] + ffd["RF"]).loc[start:]
    vix = cboe("VIX", daily_only=True).reindex(tr.index).ffill() / 100.0
    rf = (M.fred("DFF") / 100.0).reindex(tr.index).ffill().fillna(0.0)
    idx = tr.index[vix.notna() & rf.notna()]
    tr = tr.reindex(idx)
    # dividend yield medio dell'S&P sul periodo: separa prezzo da total return
    q = 0.02
    px = (1 + tr - q / TRADING_DAYS).cumprod() * 100.0
    return pd.DataFrame({"tr": tr, "px": px, "vix": vix.reindex(idx),
                         "rf": rf.reindex(idx)}).dropna(), q


def third_fridays(idx):
    """Ultimo giorno di negoziazione fino al terzo venerdi' di ogni mese.

    E' la scadenza vera delle opzioni sull'S&P e degli indici BXM e PUT. Usare
    invece la fine del mese sembra un dettaglio e non lo e': al giro 48 la
    correlazione fra simulazione e indice reale passa da 0,85 a 0,975 solo
    cambiando questo. Le finestre di payoff sfalsate di una settimana bastano
    a rompere il confronto.
    """
    s = pd.Series(idx, index=idx)
    out = []
    for _, g in s.groupby([s.index.year, s.index.month]):
        fri = g[g.index.dayofweek == 4]
        if len(fri) >= 3:
            out.append(fri.index[2])
    return out


def expiries(idx, freq="ME"):
    """Date di scadenza. freq='3F' usa il terzo venerdi', il default vero."""
    if freq == "3F":
        return third_fridays(idx)
    s = pd.Series(idx, index=idx)
    return list(s.resample(freq).last().dropna())


def roll_short_option(d, q, kind="p", moneyness=1.0, freq="3F", iv_scale=1.0):
    """Vende un'opzione a ogni scadenza e la tiene fino alla successiva.

    Restituisce, per ogni periodo fra due scadenze:
      premio incassato (in frazione del nozionale)
      payoff pagato alla scadenza (frazione del nozionale, sempre >= 0)
      rendimento del sottostante nel periodo
    Il nozionale e' riscalato al livello dell'indice all'apertura, quindi tutto
    e' espresso in frazione: si compone come un rendimento.
    """
    exp = expiries(d.index, freq)
    rows = []
    for a, b in zip(exp[:-1], exp[1:]):
        S0 = float(d["px"].loc[a])
        S1 = float(d["px"].loc[b])
        T = (b - a).days / 365.25
        sig = float(d["vix"].loc[a]) * iv_scale
        r = float(d["rf"].loc[a])
        K = S0 * moneyness
        prem = float(bs(S0, K, T, r, sig, q, kind)) / S0
        pay = (max(S1 - K, 0.0) if kind == "c" else max(K - S1, 0.0)) / S0
        rows.append(dict(open=a, close=b, S0=S0, S1=S1, K=K / S0, T=T,
                         vix=sig, rf=r, premium=prem, payoff=pay,
                         under=S1 / S0 - 1.0,
                         tr=float((1 + d["tr"].loc[a:b].iloc[1:]).prod() - 1)))
    return pd.DataFrame(rows).set_index("close")


def realized_vol(d, days=21):
    """Volatilita' realizzata annualizzata sui `days` giorni SUCCESSIVI."""
    return (d["tr"].rolling(days).std().shift(-days) * np.sqrt(TRADING_DAYS))


def monthly_index(s):
    out = s.copy()
    out.index = pd.DatetimeIndex(out.index).to_period("M").to_timestamp("M")
    return out


def leaps_mtm(d, q, moneyness=0.80, iv_scale=1.0, leverage=1.0, tenor=12,
              prem_mult=1.0):
    """Call lunga a `tenor` mesi, rollata a scadenza, VALUTATA OGNI MESE.

    Serve perche' una posizione annuale osservata solo a scadenza produce una
    serie con 1 punto l'anno: darla in pasto a un motore che assume 12 periodi
    l'anno gonfia il CAGR di un fattore enorme. Qui la posizione e' marcata al
    mercato a fine di ogni mese con la maturita' residua corretta.

    Capitale 1. Nozionale L. Premio pagato prem0*L, il resto in liquidita' al
    risk-free. Restituisce la serie MENSILE dei rendimenti del portafoglio e la
    quota realizzata (1 al rollo, 0 altrove).
    """
    exp = third_fridays(d.index)
    opens = exp[::tenor]
    vals, rz = [], []
    for a, b in zip(opens[:-1], opens[1:]):
        S0 = float(d["px"].loc[a])
        K = S0 * moneyness
        r0 = float(d["rf"].loc[a])
        T0 = (b - a).days / 365.25
        prem0 = float(bs(S0, K, T0, r0, float(d["vix"].loc[a]) * iv_scale, q, "c")) / S0
        # prem_mult modella spread denaro-lettera ed esecuzione: si PAGA di piu'
        # all'ingresso senza che cambi il valore di mercato successivo
        cost = prem0 * prem_mult * leverage
        cash = 1.0 - cost
        days = d.loc[a:b]
        mensili = days.resample("ME").last().dropna()
        prev = 1.0
        for t, row in mensili.iterrows():
            if t <= a:
                continue
            Tr = max((b - t).days / 365.25, 1e-6)
            v = float(bs(float(row["px"]), K, Tr, float(row["rf"]),
                         float(row["vix"]) * iv_scale, q, "c")) / S0
            acc = cash * (1 + float(row["rf"]) * ((t - a).days / 365.25))
            V = acc + v * leverage
            vals.append((t, V / prev - 1.0))
            rz.append((t, 0.0))
            prev = V
        if vals:
            rz[-1] = (rz[-1][0], 1.0)      # il rollo realizza tutto
    s = pd.Series([v for _, v in vals],
                  index=pd.DatetimeIndex([t for t, _ in vals])
                  .to_period("M").to_timestamp("M"))
    z = pd.Series([v for _, v in rz],
                  index=pd.DatetimeIndex([t for t, _ in rz])
                  .to_period("M").to_timestamp("M"))
    # il mese del rollo compare due volte: chiude la posizione vecchia e apre
    # la nuova. I due spezzoni vanno COMPOSTI, non uno scelto e l'altro buttato,
    # e il flag di realizzo va tenuto con un max, non sovrascritto dallo zero.
    s = (1 + s).groupby(level=0).prod() - 1
    z = z.groupby(level=0).max()
    return s.sort_index(), z.reindex(s.index).fillna(0.0)

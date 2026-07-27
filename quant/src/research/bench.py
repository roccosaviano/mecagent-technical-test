"""Valutazione standard condivisa dai giri 34+.

Un solo posto dove si decide come si misura una strategia, cosi' i giri della
coda non reimplementano ognuno la propria convenzione. Due porte d'ingresso:

  eval_exposure   strategia LONG-ONLY con esposizione frazionaria 0-1. La parte
                  non investita e' liquidita' al risk-free netto DIRT.
  eval_stream     un flusso di rendimenti qualunque (anche long/short), tassato
                  sulla quota realizzata nel periodo.

Entrambe restituiscono lo stesso dizionario, cosi' le tabelle sono comparabili
fra giri diversi.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
from tax import simulate_pac, CGT_SHARES, TRADING_52


def stats(net, ppy=12):
    net = net.dropna()
    yrs = len(net) / ppy
    curve = (1 + net).cumprod()
    tot = float(curve.iloc[-1])
    sd = float(net.std())
    return dict(cagr=(tot ** (1 / yrs) - 1) * 100 if tot > 0 else -100.0,
                vol=sd * np.sqrt(ppy) * 100,
                sharpe=float(net.mean() / sd * np.sqrt(ppy)) if sd > 0 else np.nan,
                dd=float((curve / curve.cummax() - 1).min()) * 100,
                skew=float(net.skew()) if len(net) > 3 else np.nan)


def _finish(label, gross, rf, r33, r52, turn, ppy, extra):
    s = stats(gross, ppy)
    tpy = float(turn.sum()) / (len(gross) / ppy) if turn is not None else 0.0
    out = dict(label=label, **s, turn=tpy, irr=r33.irr_annual,
               irr52=r52.irr_annual, n=len(gross), gross=gross)
    # sopra il 100% di rotazione l'anno l'aliquota di riferimento e' il 52%
    out["irr_ref"] = out["irr52"] if tpy > 1.0 else out["irr"]
    out["rate_ref"] = 52 if tpy > 1.0 else 33
    out.update(extra or {})
    return out


def eval_exposure(label, ret, rf, e, ppy=12, extra=None):
    """Long-only con esposizione frazionaria. `e` in [0,1]."""
    idx = ret.index
    e = e.reindex(idx).fillna(0.0).clip(0.0, 1.0)
    rf0 = rf.reindex(idx).fillna(0.0)
    turn = e.diff().abs().fillna(e.abs())
    rz = (-e.diff()).clip(lower=0.0).fillna(0.0)
    gross = e * ret + (1 - e) * rf0 * (1 - C.DIRT_RATE)
    kw = dict(in_market=e, rf=rf0, turnover=turn, realize_frac=rz,
              periods_per_year=ppy)
    return _finish(label, gross, rf0, simulate_pac(ret, CGT_SHARES, **kw),
                   simulate_pac(ret, TRADING_52, **kw), turn, ppy, extra)


def eval_stream(label, net, rf, realize_frac=None, ppy=12, extra=None):
    """Un flusso di rendimenti gia' netto di costi. `realize_frac` e' la quota
    di portafoglio venduta nel periodo, che realizza plusvalenza."""
    idx = net.index
    rf0 = rf.reindex(idx).fillna(0.0)
    rz = (realize_frac.reindex(idx).fillna(0.0).clip(0, 1)
          if realize_frac is not None else None)
    kw = dict(rf=rf0, realize_frac=rz, periods_per_year=ppy)
    turn = rz if rz is not None else pd.Series(0.0, index=idx)
    return _finish(label, net, rf0, simulate_pac(net, CGT_SHARES, **kw),
                   simulate_pac(net, TRADING_52, **kw), turn, ppy, extra)


def table(rows, cols=("label", "cagr", "vol", "sharpe", "dd", "turn", "irr", "irr52")):
    w = {"label": 34}
    hdr = "".join(f"{c:<{w.get(c, 9)}}" if c == "label" else f"{c:>9}"
                  for c in cols)
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        line = ""
        for c in cols:
            v = r.get(c)
            if c == "label":
                line += f"{str(v)[:33]:<34}"
            elif isinstance(v, float):
                line += (f"{v:>8.2f}%" if c in ("cagr", "vol", "dd", "irr", "irr52")
                         else f"{v:>9.2f}")
            else:
                line += f"{str(v):>9}"
        print(line)


def erc_weights(cov, iters=300):
    n = cov.shape[0]
    w = np.ones(n) / n
    for _ in range(iters):
        rc = w * (cov @ w)
        w = w * (rc.mean() / np.maximum(rc, 1e-12)) ** 0.5
        w = np.maximum(w, 1e-6)
        w = w / w.sum()
    return w


def ma_filter(px, months=10):
    """Filtro di trend classico: investito se il prezzo chiude sopra la media
    mobile a N mesi, calcolata con i soli dati fino a ieri."""
    ma = px.rolling(months).mean()
    return (px > ma).shift(1).fillna(False).astype(float)


def xs_momentum(rets, lb=12, skip=1, top=10, hold=1):
    """Momentum cross-sectional long-only: lungo i `top` migliori su lb-skip.
    Il segnale usa solo il passato: rank su [t-lb, t-skip], applicato in t."""
    sig = (1 + rets).rolling(lb - skip).apply(np.prod, raw=True).shift(skip + 1)
    rk = sig.rank(axis=1, ascending=False)
    w = (rk <= top).astype(float)
    w = w.div(w.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    if hold > 1:
        w = w.rolling(hold).mean()
    return w


def wbacktest(rets, W, cost=C.COST_ROUND_TRIP):
    """Rendimento netto e turnover di un portafoglio a pesi dati.
    W.iloc[i] sono i pesi DETENUTI durante il periodo i (gia' ritardati)."""
    turn = W.diff().abs().sum(axis=1).fillna(W.abs().sum(axis=1)) / 2.0
    net = (W * rets).sum(axis=1) - turn * cost
    return net.dropna(), turn.reindex(net.index).fillna(0.0)

"""La cella decisiva: F2 top-5 annuale contro equal-weight statico.

E' l'unico punto dell'intero progetto in cui il divario (1,14 punti) e' dello
stesso ordine di grandezza della correzione da contabilita' per posizione.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd
import config as C
import dataio
from research.tax_poslevel import pac

ind = dataio.ff_ind49_daily().resample("ME").apply(lambda x: (1 + x).prod() - 1)
ind = ind.dropna(how="all").fillna(0.0)
ind = ind[ind.index >= "1990-01-01"]


def annual_top(rets, top):
    """Riseleziona una volta l'anno sui 12 mesi precedenti, poi tiene fermo."""
    sig = (1 + rets).rolling(12).apply(np.prod, raw=True).shift(1)
    rk = sig.rank(axis=1, ascending=False)
    W = (rk <= top).astype(float)
    W = W.div(W.sum(axis=1).replace(0, np.nan), axis=0)
    W = W.where(pd.Series(W.index.month == 1, index=W.index), other=np.nan)
    return W.ffill().fillna(0.0)


ew = pd.DataFrame(1.0 / ind.shape[1], index=ind.index, columns=ind.columns)

print(f"{'strategia':<24}{'IRR agg':>10}{'IRR pos':>10}{'delta':>9}")
print("-" * 53)
res = {}
for lbl, W, rate, ex in [
        ("top-5 annuale 33%", annual_top(ind, 5), C.CGT_RATE, C.CGT_EXEMPT_ANNUAL),
        ("top-5 annuale 52%", annual_top(ind, 5), C.TRADING_INCOME_RATE, 0.0),
        ("equal-weight 33%", ew, C.CGT_RATE, C.CGT_EXEMPT_ANNUAL)]:
    ok = W.sum(axis=1) > 0
    r, w = ind[ok], W[ok]
    a = pac(r, w, "agg", rate=rate, exempt=ex)
    p = pac(r, w, "pos", rate=rate, exempt=ex)
    res[lbl] = (a["irr"], p["irr"])
    print(f"{lbl:<24}{a['irr']:>9.2f}%{p['irr']:>9.2f}%{p['irr'] - a['irr']:>+8.2f}")

b = res["equal-weight 33%"]
for k in ("top-5 annuale 33%", "top-5 annuale 52%"):
    print(f"\n{k} vs equal-weight statico:"
          f"\n  contabilita' aggregata  {res[k][0] - b[0]:+.2f} punti"
          f"\n  contabilita' posizione  {res[k][1] - b[1]:+.2f} punti")

"""Esecutore di un giro di ricerca.

Contratto di ogni giro:
  - ottimizza SOLO su TRAIN
  - valuta su TEST, e OGNI configurazione valutata finisce nel registro
  - calcola il Deflated Sharpe sul numero cumulato di tentativi
  - non tocca mai HOLDOUT
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES
from research import lab
from research import multidata as M


# ------------------------------------------------------------------ universo
def build_assets():
    """Serie mensili di rendimento TOTALE di asset con driver diversi.

    Ogni riga e' un asset investibile long-only o un premio long-short; le
    seconde sono marcate perche' hanno vincoli di implementazione diversi.
    """
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    eq = (ff["Mkt-RF"] + ff["RF"]).rename("US equity")

    cen = M.century()
    out = {"US equity": eq}
    ls = {}
    for col in ("Equity indices Multi-style", "Fixed income Multi-style",
                "Currencies Multi-style", "Commodities Multi-style",
                "All Stock Selection Multi-style"):
        if col in cen.columns:
            ls[col] = cen[col].dropna()
    bonds = M.bond_total_return_monthly().rename("US 10y")
    out["US 10y"] = bonds
    return out, ls, rf


def corr_table(series_map, window):
    df = pd.DataFrame({k: v for k, v in series_map.items()})
    return lab.win(df, window).dropna().corr()


# ------------------------------------------------------------------ portafoglio
def blend(components, weights, rebal_months):
    """Combina componenti con pesi fissi e ribilanciamento periodico.
    Restituisce (rendimento, turnover) — il turnover serve alle imposte."""
    df = pd.DataFrame(components).dropna()
    w0 = np.array([weights[c] for c in df.columns], dtype=float)
    w0 = w0 / w0.sum()
    w = w0.copy()
    rets, turns = [], []
    for i in range(len(df)):
        if i % rebal_months == 0:
            turn = 0.5 * np.abs(w0 - w).sum()
            w = w0.copy()
        else:
            turn = 0.0
        r = df.iloc[i].to_numpy(dtype=float)
        rets.append(float(w @ r) - turn * C.COST_ROUND_TRIP)
        grown = w * (1.0 + r)
        w = grown / grown.sum()
        turns.append(turn)
    return pd.Series(rets, index=df.index), pd.Series(turns, index=df.index)


def lever(ret, rf, lev):
    """Leva con finanziamento a benchmark + spread."""
    if lev == 1.0:
        return ret
    return ret * lev - (lev - 1.0) * (rf.reindex(ret.index).fillna(0.0)
                                      + C.FIN_SPREAD / 12.0)


def pac(ret, rf, realize=None):
    return simulate_pac(ret, CGT_SHARES, rf=rf, realize_frac=realize)

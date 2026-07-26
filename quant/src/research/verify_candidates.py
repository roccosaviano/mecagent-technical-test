"""Verifiche sui due candidati promossi, prima di toccare l'holdout.

Tre prove che un candidato deve superare:
  1. scenario fiscale a 52% (riqualificazione come attivita' commerciale):
     H5 ruota il 262% l'anno, molto oltre la soglia di segnalazione
  2. ritardo aggiuntivo del segnale: se un mese in piu' di lag annulla il
     vantaggio, il margine dipendeva da un timing al limite
  3. costi doppi
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES, TRADING_52
from research import lab, walkforward as WF
from research import rounds_batch as B


def variants(name, build, grid, index, rf, bench, start_year, extra_lag=0,
             cost_mult=1.0):
    old = C.COST_ROUND_TRIP
    C.COST_ROUND_TRIP = old * cost_mult
    try:
        oos, rzs, picks, ne = WF.walk_forward(build, grid, index, rf,
                                              start_year=start_year)
    finally:
        C.COST_ROUND_TRIP = old
    idx = oos.index.intersection(bench.index)
    oos, rz = oos.reindex(idx), rzs.reindex(idx).fillna(0.0)
    b = bench.reindex(idx)
    rfw = rf.reindex(idx).fillna(0.0)
    out = {}
    for lbl, regime in (("CGT 33%", CGT_SHARES), ("riqualif. 52%", TRADING_52)):
        r = simulate_pac(oos, regime, rf=rfw, realize_frac=rz)
        bh = simulate_pac(b, regime, rf=rfw)
        out[lbl] = (r.irr_annual, r.irr_annual - bh.irr_annual)
    out["turnover"] = float(rz.mean() * 12 * 100)
    return out


def main():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    eq = (ff["Mkt-RF"] + ff["RF"]).rename("eq")
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all")

    # ricostruisco i due build con la possibilita' di aggiungere lag al segnale
    def make_h5(extra_lag):
        lg = np.log1p(ind)
        MOM = np.expm1(lg.rolling(12).sum()).shift(2 + extra_lag)

        def build(cfg, idx):
            n_sel, look, rb = cfg
            d = ind.reindex(idx).dropna(axis=1)
            if len(d) < 26 or d.shape[1] < n_sel:
                return None, None
            mom = MOM.reindex(d.index)[d.columns]
            rets, turns, w = [], [], None
            for i in range(len(d)):
                if i < 14 + extra_lag:
                    rets.append(np.nan); turns.append(0.0); continue
                if w is None or i % rb == 0:
                    m = mom.iloc[i].dropna()
                    if len(m) < n_sel:
                        rets.append(np.nan); turns.append(0.0); continue
                    sel = m.nlargest(n_sel).index
                    new = pd.Series(0.0, index=d.columns)
                    new[sel] = 1.0 / n_sel
                    turns.append(0.5 * float((new - (w if w is not None else 0)).abs().sum())
                                 if w is not None else 1.0)
                    w = new
                else:
                    turns.append(0.0)
                r = d.iloc[i]
                rets.append(float((w * r).sum()) - turns[-1] * C.COST_ROUND_TRIP)
                g = w * (1 + r); w = g / g.sum()
            s = pd.Series(rets, index=d.index).dropna()
            return s, pd.Series(turns, index=d.index).reindex(s.index)
        return build

    g5 = [(n, 12, rb) for n in (5, 10) for rb in (1, 3, 12)]
    g4 = [(n, rb) for n in (10, 15, 20) for rb in (12, 60)]

    print("=" * 78)
    print("VERIFICA DEI CANDIDATI PROMOSSI")
    print("=" * 78)

    print("\n1. Scenario fiscale e costi  (differenza di IRR contro il buy&hold)")
    print(f"{'':<34}{'CGT 33%':>12}{'riqualif. 52%':>16}{'turnover':>11}")
    for lbl, build, grid, sy in (("H5 momentum settoriale", make_h5(0), g5, 1935),
                                 ("H4 tilt low-vol", None, g4, 1935)):
        if build is None:
            # riuso il build originale di H4
            import types
            src = B.h4_defensive
            # estraggo il build ricostruendolo qui per non duplicare logica
            VOL = ind.rolling(60).std()

            def build(cfg, idx):
                n_sel, rb = cfg
                d = ind.reindex(idx).dropna(axis=1)
                if len(d) < 60 or d.shape[1] < n_sel:
                    return None, None
                vol = VOL.reindex(d.index)[d.columns]
                rets, turns, w = [], [], None
                for i in range(len(d)):
                    if i < 60:
                        rets.append(np.nan); turns.append(0.0); continue
                    if w is None or i % rb == 0:
                        v = vol.iloc[i - 1].dropna()
                        if len(v) < n_sel:
                            rets.append(np.nan); turns.append(0.0); continue
                        sel = v.nsmallest(n_sel).index
                        new = pd.Series(0.0, index=d.columns)
                        new[sel] = 1.0 / n_sel
                        turns.append(0.5 * float((new - (w if w is not None else 0)).abs().sum())
                                     if w is not None else 1.0)
                        w = new
                    else:
                        turns.append(0.0)
                    r = d.iloc[i]
                    rets.append(float((w * r).sum()) - turns[-1] * C.COST_ROUND_TRIP)
                    g = w * (1 + r); w = g / g.sum()
                s = pd.Series(rets, index=d.index).dropna()
                return s, pd.Series(turns, index=d.index).reindex(s.index)

        v = variants(lbl, build, grid, ind.index, rf, eq, sy)
        print(f"{lbl:<34}{v['CGT 33%'][1]:>+11.2f}%{v['riqualif. 52%'][1]:>+15.2f}%"
              f"{v['turnover']:>10.0f}%")

    print("\n2. H5 con un mese di ritardo in piu' sul segnale")
    print(f"{'':<34}{'CGT 33%':>12}{'riqualif. 52%':>16}")
    for lag in (0, 1, 2):
        v = variants("h5", make_h5(lag), g5, ind.index, rf, eq, 1935)
        print(f"{'  lag +' + str(lag) + ' mesi':<34}{v['CGT 33%'][1]:>+11.2f}%"
              f"{v['riqualif. 52%'][1]:>+15.2f}%")

    print("\n3. H5 con costi di transazione doppi (0,30% round-trip)")
    v = variants("h5", make_h5(0), g5, ind.index, rf, eq, 1935, cost_mult=2.0)
    print(f"{'  costi x2':<34}{v['CGT 33%'][1]:>+11.2f}%{v['riqualif. 52%'][1]:>+15.2f}%")


if __name__ == "__main__":
    main()

"""Gruppo A: ottimizzazione in-sample, validazione out-of-sample, robustezza."""
import json
import numpy as np
import pandas as pd

import dataio
import config as C
import strategies as S
from tax import simulate_pac, CGT_SHARES, TRADING_52

OUT = __import__("pathlib").Path(__file__).resolve().parents[1] / "out"


def market_daily():
    ff = dataio.ff_factors_daily()
    return (ff["Mkt-RF"] + ff["RF"]).rename("mkt")


def run_lookahead_check(ret):
    res = S.falsify_lookahead(ret, C.COST_ROUND_TRIP)
    cheat = res["con look-ahead"]["cagr"]
    honest = res["stesso segnale ritardato di 1"]["cagr"]
    print("\n--- Test di falsificazione del look-ahead -------------------------")
    print("  Segnale che conosce il rendimento di domani  : "
          f"CAGR {cheat:>10.1f}%  Sharpe {res['con look-ahead']['sharpe']:.2f}")
    print("  Stesso segnale ritardato di un giorno        : "
          f"CAGR {honest:>10.1f}%  Sharpe {res['stesso segnale ritardato di 1']['sharpe']:.2f}")
    ok = cheat > 100.0 and honest < 30.0
    print(f"  Esito: {'OK, il controllo distingue i due casi' if ok else 'ALLARME: il motore perde informazione'}")
    return ok, res


def optimise(close, ret, fn, grid, cost_rt):
    best, bp = None, None
    for p in grid:
        pos = S.positions(fn, close, p)
        m = S.gross_stats(ret, pos, cost_rt)
        if best is None or m["cagr"] > best["cagr"]:
            best, bp = m, p
    return best, bp


def main():
    mkt = market_daily()
    ok_la, la = run_lookahead_check(mkt)

    # finestra: tutto lo storico French disponibile
    close = S.build_index(mkt)
    n = len(mkt)
    split = n // 2
    ins_i, oos_i = slice(0, split), slice(split, n)
    ins_ret, oos_ret = mkt.iloc[ins_i], mkt.iloc[oos_i]

    tot_combos = sum(S.N_COMBOS.values())
    print(f"\n--- Gruppo A su indice total return mercato USA (Ken French) ------")
    print(f"  Campione   {mkt.index[0].date()} -> {mkt.index[-1].date()}  ({n} sedute)")
    print(f"  IN-SAMPLE  {ins_ret.index[0].date()} -> {ins_ret.index[-1].date()}")
    print(f"  OUT-SAMPLE {oos_ret.index[0].date()} -> {oos_ret.index[-1].date()}")
    print(f"  Combinazioni di parametri provate: {tot_combos} "
          f"({', '.join(f'{k}={v}' for k, v in S.N_COMBOS.items())})")

    bh_oos = S.gross_stats(oos_ret, pd.Series(1.0, index=oos_ret.index), C.COST_ROUND_TRIP)
    print(f"\n  Buy&hold OOS (lordo imposte): CAGR {bh_oos['cagr']:.2f}%  "
          f"Sharpe {bh_oos['sharpe']:.2f}  DD {bh_oos['dd']:.1f}%")

    rows = []
    print(f"\n{'Strategia':<36}{'parametri':<30}{'IS cagr':>9}{'OOS cagr':>10}"
          f"{'OOS Sh':>8}{'OOS DD':>9}{'op/anno':>9}{'%mkt':>7}")
    print("-" * 118)
    chosen = {}
    for name, (fn, grid) in S.GRIDS.items():
        # i segnali si calcolano sull'intera serie e si affettano: gli indicatori
        # guardano solo indietro, cosi' non si perde il warm-up a inizio OOS
        best, bp = None, None
        for p in grid:
            pos_full = S.positions(fn, close, p)
            m = S.gross_stats(ins_ret, pos_full.iloc[ins_i], C.COST_ROUND_TRIP)
            if best is None or m["cagr"] > best["cagr"]:
                best, bp, best_pos = m, p, pos_full
        o = S.gross_stats(oos_ret, best_pos.iloc[oos_i], C.COST_ROUND_TRIP)
        chosen[name] = (bp, best_pos)
        rows.append(dict(name=name, params=bp, is_cagr=best["cagr"], **{
            "oos_cagr": o["cagr"], "oos_sharpe": o["sharpe"], "oos_dd": o["dd"],
            "trades_yr": o["trades_yr"], "inmkt": o["inmkt"]}))
        print(f"{name:<36}{str(bp):<30}{best['cagr']:>8.2f}%{o['cagr']:>9.2f}%"
              f"{o['sharpe']:>8.2f}{o['dd']:>8.1f}%{o['trades_yr']:>9.1f}{o['inmkt']:>6.0f}%")

    # ------------------------------------------------ robustezza su 49 settori
    print(f"\n--- Robustezza: stessi parametri su 49 settori (finestra OOS) -----")
    ind = dataio.ff_ind49_daily()
    ind_oos = ind.loc[oos_ret.index[0]:oos_ret.index[-1]]
    rob = {}
    for name, (bp, _) in chosen.items():
        fn = S.GRIDS[name][0]
        beats, cagrs = 0, []
        for col in ind.columns:
            s = ind[col].dropna()
            if len(s) < 2000:
                continue
            cl = S.build_index(s)
            pos = S.positions(fn, cl, bp)
            sl = s.loc[oos_ret.index[0]:oos_ret.index[-1]]
            if len(sl) < 500:
                continue
            m = S.gross_stats(sl, pos.reindex(sl.index).fillna(0.0), C.COST_ROUND_TRIP)
            bh = S.gross_stats(sl, pd.Series(1.0, index=sl.index), C.COST_ROUND_TRIP)
            cagrs.append(m["cagr"] - bh["cagr"])
            beats += int(m["cagr"] > bh["cagr"])
        rob[name] = (beats, len(cagrs), float(np.median(cagrs)) if cagrs else np.nan)
        print(f"  {name:<36} batte il B&H in {beats:>2}/{len(cagrs)} settori   "
              f"mediana extra-CAGR {np.median(cagrs):+.2f}%")

    # ------------------------------------------------ sottoperiodi
    print(f"\n--- Robustezza: sottoperiodi di 20 anni sull'indice ---------------")
    print(f"  {'Strategia':<36}" + "".join(f"{d:>10}" for d in
          ("1930-49", "1950-69", "1970-89", "1990-09", "2010-26")))
    sub = [("1930", "1949"), ("1950", "1969"), ("1970", "1989"),
           ("1990", "2009"), ("2010", "2026")]
    subres = {}
    for name, (bp, pos_full) in chosen.items():
        cells, vals = [], []
        for a, b in sub:
            r = mkt.loc[a:b]
            if len(r) < 500:
                cells.append("  n/d"); continue
            m = S.gross_stats(r, pos_full.reindex(r.index).fillna(0.0), C.COST_ROUND_TRIP)
            bh = S.gross_stats(r, pd.Series(1.0, index=r.index), C.COST_ROUND_TRIP)
            d = m["cagr"] - bh["cagr"]
            vals.append(d)
            cells.append(f"{d:+9.2f}")
        subres[name] = vals
        print(f"  {name:<36}" + "".join(f"{c:>10}" for c in cells))
    print("  (valori = extra-CAGR annuo rispetto al buy&hold nello stesso periodo)")

    OUT.mkdir(exist_ok=True)
    with open(OUT / "group_a.json", "w") as f:
        json.dump({"lookahead_ok": bool(ok_la), "rows": rows,
                   "robust_sectors": {k: list(v) for k, v in rob.items()},
                   "subperiods": {k: v for k, v in subres.items()},
                   "n_combos": S.N_COMBOS}, f, indent=1, default=float)
    return chosen, rows


if __name__ == "__main__":
    main()

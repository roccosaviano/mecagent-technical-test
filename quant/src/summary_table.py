"""Tabella riassuntiva: CAGR lordo, IRR netta, Sharpe, drawdown.

Attenzione alle finestre. Le strategie non girano tutte sullo stesso periodo ne'
sullo stesso universo, e mescolarle in una colonna sola sarebbe fuorviante:
ogni riga porta la propria finestra e il confronto e' sempre col buy&hold DELLO
STESSO universo e DELLA STESSA finestra.

  CAGR lordo  rendimento annualizzato time-weighted, al lordo di imposte ma al
              netto dei costi di transazione. E' il numero confrontabile con
              "l'S&P fa circa il 10%".
  IRR netta   rendimento money-weighted del PAC da 500 EUR/mese, netto di tutto.
              E' sempre piu' bassa del CAGR: le imposte, e il fatto che i
              versamenti tardivi lavorano meno.
  Sharpe      su rendimenti in eccesso sul risk-free.
  Max DD      sul NAV di una quota, cioe' al netto delle imposte gia' pagate.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import config as C
import dataio
import run_c
import strategies as S
from tax import simulate_pac, CGT_SHARES, ETF_UCITS, TRADING_52, first_of_month

OUT = Path(__file__).resolve().parents[1] / "out"
W0, W1 = C.CALIB_START, C.CALIB_END
ROWS = []


def cagr(ret, periods=12):
    r = pd.Series(ret).dropna()
    if len(r) == 0:
        return np.nan
    yrs = len(r) / periods
    tot = float((1 + r).prod())
    return (tot ** (1 / yrs) - 1) * 100 if tot > 0 else -100.0


def sharpe(ret, rf, periods=12):
    r = pd.Series(ret).dropna()
    ex = r - pd.Series(rf).reindex(r.index).fillna(0.0)
    return float(ex.mean() / ex.std() * np.sqrt(periods)) if ex.std() > 0 else np.nan


def add(name, group, window, ret, rf, res, oos, bench_irr=None, periods=12):
    ROWS.append(dict(
        name=name, group=group, window=window,
        cagr=cagr(ret, periods), irr=res.irr_annual,
        vs=(res.irr_annual - bench_irr) if bench_irr is not None else np.nan,
        sharpe=sharpe(ret, rf, periods), dd=res.max_dd,
        trades=res.trades_per_year, oos=oos, taxes=res.taxes))


def main():
    # ---------------------------------------------------- studio principale
    c = run_c.build(W0, W1)
    idx, rf = c["index"], c["rf"]
    win = f"{W0}/{W1[:4]}"

    bench = simulate_pac(c["total_ret"], CGT_SHARES, rf=rf)
    b_irr = bench.irr_annual
    add("Buy&hold indice, CGT 33% all'uscita  [BENCHMARK]", "C", win,
        c["total_ret"], rf, bench, "in-sample", b_irr)
    add("Buy&hold azioni dirette, dividendi 52%/anno", "C", win,
        c["price_ret"] + c["div_m"], rf,
        simulate_pac(c["price_ret"], CGT_SHARES, div_yield=c["div_m"], rf=rf),
        "in-sample", b_irr)
    add("Buy&hold ETF UCITS, exit tax 38% + deemed disposal", "C", win,
        c["total_ret"], rf, simulate_pac(c["total_ret"], ETF_UCITS, rf=rf),
        "in-sample", b_irr)
    for lev in C.LEVERAGE_GRID:
        r = run_c.levered_return(c["total_ret"], c["trend_pos"], lev, rf)
        add(f"Trend following 10 mesi, leva {lev:g}x", "C", win, r, rf,
            simulate_pac(r, CGT_SHARES, in_market=c["trend_pos"], rf=rf),
            "regola pubblicata, non ottimizzata", b_irr)

    # ---------------------------------------------------- gruppo A (giornaliero)
    ffd = dataio.ff_factors_daily()
    mkt_d = (ffd["Mkt-RF"] + ffd["RF"])
    close_d = S.build_index(mkt_d)
    rf_d = ffd["RF"]
    wd = mkt_d.loc[W0:W1]
    rfd = rf_d.reindex(wd.index).fillna(0.0)
    com = first_of_month(wd.index)
    bh_a = simulate_pac(wd, CGT_SHARES, rf=rfd, periods_per_year=252, contrib_on=com)
    add("Buy&hold indice CRSP  [bench gruppo A]", "A", win, wd, rfd, bh_a,
        "in-sample", bh_a.irr_annual, periods=252)
    ga = json.load(open(OUT / "group_a.json"))
    for row in ga["rows"]:
        fn = S.GRIDS[row["name"]][0]
        pos = S.positions(fn, close_d, row["params"]).reindex(wd.index).fillna(0.0)
        turn = pos.diff().abs().fillna(pos.abs())
        gross = pos * wd - turn * C.COST_ROUND_TRIP / 2.0
        add(f"A. {row['name']}", "A", win, gross, rfd,
            simulate_pac(gross, CGT_SHARES, in_market=pos, rf=rfd,
                         periods_per_year=252, contrib_on=com),
            "OOS (meta' campione)", bh_a.irr_annual, periods=252)

    # ---------------------------------------------------- gruppo D
    import run_d
    vw, ew, mu = run_d.load_universe(W0)
    ml = mu.shift(1).dropna()
    va = vw.loc[ml.index]
    k = (ml.index >= idx[0]) & (ml.index <= idx[-1])
    ml, va = ml[k], va[k]
    cw = (ml * va).sum(axis=1)
    rfd2 = rf.reindex(cw.index).fillna(0.0)
    bh_d = simulate_pac(cw, CGT_SHARES, rf=rfd2)
    add("Cap-weight 49 settori  [bench gruppo D]", "D", win, cw, rfd2, bh_d,
        "in-sample", bh_d.irr_annual)
    for p in run_d.P_GRID:
        tgt = ml.apply(lambda r_: run_d.dw_weights(r_, p), axis=1)
        for lbl, rb in (("annuale", 12), ("mensile", 1)):
            r, tn = run_d.simulate_portfolio(va, tgt, rb)
            add(f"D. Diversity-weighted p={p:.2f}, ribil. {lbl}", "D", win, r,
                rfd2, simulate_pac(r, CGT_SHARES, rf=rfd2, realize_frac=tn),
                "teorema, non ottimizzato", bh_d.irr_annual)
    eqw = pd.DataFrame(1.0 / va.shape[1], index=ml.index, columns=ml.columns)
    r, tn = run_d.simulate_portfolio(va, eqw, 12)
    add("D. Equal-weight 49 settori, ribil. annuale", "D", win, r, rfd2,
        simulate_pac(r, CGT_SHARES, rf=rfd2, realize_frac=tn),
        "nessun parametro", bh_d.irr_annual)

    # ---------------------------------------------------- stampa
    def block(title, groups, sort=True):
        rows = [r for r in ROWS if r["group"] in groups]
        if sort:
            rows = sorted(rows, key=lambda r: -r["irr"])
        print(f"\n### {title}\n")
        print(f"| Strategia | Finestra | CAGR lordo | IRR netta PAC | vs B&H | "
              f"Sharpe | Max DD | Op/anno | Fuori campione |")
        print("|---|---|---:|---:|---:|---:|---:|---:|---|")
        for r in rows:
            print(f"| {r['name']} | {r['window']} | {r['cagr']:.2f}% | "
                  f"{r['irr']:.2f}% | {r['vs']:+.2f} | {r['sharpe']:.2f} | "
                  f"{r['dd']:.1f}% | {r['trades']:.1f} | {r['oos']} |")

    print("# Tabella riassuntiva\n")
    print("CAGR lordo = time-weighted, al lordo di imposte, netto di costi.")
    print("IRR netta = money-weighted del PAC 500 EUR/mese, netto di tutto.")
    block("Benchmark passivi e trend following (gruppo C)", ("C",))
    block("Swing trading giornaliero (gruppo A)", ("A",))
    block("Diversity-weighted / SPT (gruppo D)", ("D",))

    with open(OUT / "summary_table.json", "w") as f:
        json.dump(ROWS, f, indent=1, default=float)


if __name__ == "__main__":
    main()

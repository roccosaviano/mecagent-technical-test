"""Tabella unica: ogni strategia valutata come PAC da 500 EUR/mese,
stessa finestra, stessa fiscalita', stessi costi.

Finestra comune 1990-2023: e' l'unica coperta da tutte le fonti (Shiller
arriva a giugno 2024, OSAP a dicembre 2024) ed e' la finestra su cui l'utente
ha fornito i riferimenti di calibrazione.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

import dataio
import config as C
import strategies as S
import run_c
from tax import simulate_pac, CGT_SHARES, ETF_UCITS, TRADING_52, first_of_month

OUT = Path(__file__).resolve().parents[1] / "out"
W0, W1 = C.CALIB_START, C.CALIB_END


def row(name, group, res, note="", bench_key="shiller"):
    """bench_key indica CONTRO CHI va confrontata la riga.

    Non tutte le righe girano sullo stesso universo: il gruppo A usa l'indice
    giornaliero di Ken French, il gruppo D i 49 settori CRSP, il resto l'S&P
    composite di Shiller. Confrontarli tutti col solo benchmark Shiller
    attribuirebbe a una strategia la differenza fra due universi. Ogni riga
    ha quindi anche il confronto col buy&hold del PROPRIO universo.
    """
    return dict(name=name, group=group, irr=res.irr_annual, dd=res.max_dd,
                sharpe=res.sharpe, trades_yr=res.trades_per_year,
                taxes=res.taxes, final=res.final_net,
                contrib=res.contributions, costs=res.costs, note=note,
                bench_key=bench_key)


def main():
    rows = []
    c = run_c.build(W0, W1)
    idx, rf = c["index"], c["rf"]

    # ---------------------------------------------------------- gruppo C
    rows.append(row("Buy&hold indice, CGT 33% all'uscita  [BENCHMARK]", "C",
                    simulate_pac(c["total_ret"], CGT_SHARES, rf=rf)))
    rows.append(row("Buy&hold azioni dirette, dividendi tassati 52%/anno", "C",
                    simulate_pac(c["price_ret"], CGT_SHARES,
                                 div_yield=c["div_m"], rf=rf)))
    rows.append(row("Buy&hold ETF UCITS, exit tax 38% + deemed disposal", "C",
                    simulate_pac(c["total_ret"], ETF_UCITS, rf=rf)))

    for lev in C.LEVERAGE_GRID:
        r = run_c.levered_return(c["total_ret"], c["trend_pos"], lev, rf)
        res = simulate_pac(r, CGT_SHARES, in_market=c["trend_pos"], rf=rf)
        rows.append(row(f"Trend following 10 mesi, leva {lev:g}x", "C", res))

    # ---------------------------------------------------------- gruppo A
    ffd = dataio.ff_factors_daily()
    mkt_d = (ffd["Mkt-RF"] + ffd["RF"]).rename("mkt")
    close_d = S.build_index(mkt_d)
    rf_d = ffd["RF"]
    win_d = mkt_d.loc[W0:W1]
    try:
        ga = json.load(open(OUT / "group_a.json"))
        best_params = {r["name"]: r["params"] for r in ga["rows"]}
    except FileNotFoundError:
        raise SystemExit("esegui prima run_a.py")

    for name, p in best_params.items():
        fn = S.GRIDS[name][0]
        pos = S.positions(fn, close_d, p).reindex(win_d.index).fillna(0.0)
        turn = pos.diff().abs().fillna(pos.abs())
        gross = pos * win_d - turn * C.COST_ROUND_TRIP / 2.0
        res = simulate_pac(gross, CGT_SHARES, in_market=pos,
                           rf=rf_d.reindex(win_d.index).fillna(0.0),
                           periods_per_year=252,
                           contrib_on=first_of_month(win_d.index))
        note = ""
        if res.trades_per_year >= C.TRADE_COUNT_FLAG:
            alt = simulate_pac(gross, TRADING_52, in_market=pos,
                               rf=rf_d.reindex(win_d.index).fillna(0.0),
                               periods_per_year=252,
                               contrib_on=first_of_month(win_d.index))
            note = f"a 52% (riqualificazione): IRR {alt.irr_annual:.2f}%"
        rows.append(row(f"A. {name} {p}", "A", res, note, bench_key="ff_daily"))

    # buy&hold dello STESSO universo del gruppo A, per un confronto pulito
    rows.append(row("Buy&hold indice CRSP giornaliero [bench gruppo A]", "A",
                    simulate_pac(win_d, CGT_SHARES,
                                 rf=rf_d.reindex(win_d.index).fillna(0.0),
                                 periods_per_year=252,
                                 contrib_on=first_of_month(win_d.index)),
                    bench_key="ff_daily"))

    # ---------------------------------------------------------- gruppo B
    # Il fattore long-short e' un rendimento in eccesso: l'investitore ottiene
    # RF + premio netto dei costi di implementazione stimati in run_b.
    gb = json.load(open(OUT / "group_b.json"))
    impl = {d["name"]: d for d in gb["impl"]}
    ls = dataio.osap_ls_wide()
    bab = dataio.aqr_bab("USA")
    srcs = {"Bet Against Beta": bab, "Accruals": ls["Accruals"].dropna(),
            "Short interest": ls["ShortInterest"].dropna()}
    for nm, s in srcs.items():
        d = impl[nm]
        drag_m = (d["tc"] + d["borrow"] + d["fin"]) / 100.0 / 12.0
        r = (s.reindex(idx).fillna(0.0) + rf - drag_m)
        # ribilanciamento mensile: ogni mese realizza l'intero utile del periodo
        res = simulate_pac(r, CGT_SHARES, rf=rf,
                           realize_frac=pd.Series(1.0, index=idx))
        alt = simulate_pac(r, TRADING_52, rf=rf,
                           realize_frac=pd.Series(1.0, index=idx))
        rows.append(row(f"B. {nm} (RF + premio netto costi)", "B", res,
                        f"a 52%: IRR {alt.irr_annual:.2f}%"))

    # ---------------------------------------------------------- gruppo D
    import run_d
    vw, ew, mu = run_d.load_universe(W0)
    mu_lag = mu.shift(1).dropna()
    vw_a = vw.loc[mu_lag.index]
    keep = (mu_lag.index >= idx[0]) & (mu_lag.index <= idx[-1])
    mu_lag, vw_a = mu_lag[keep], vw_a[keep]
    cw_r = (mu_lag * vw_a).sum(axis=1)
    rf_d2 = rf.reindex(cw_r.index).fillna(0.0)
    rows.append(row("D. Cap-weight 49 settori [bench gruppo D]", "D",
                    simulate_pac(cw_r, CGT_SHARES, rf=rf_d2), bench_key="cw49"))
    for p in run_d.P_GRID:
        tgt = mu_lag.apply(lambda r_: run_d.dw_weights(r_, p), axis=1)
        for lbl, rb in (("annuale", 12), ("mensile", 1)):
            r, tn = run_d.simulate_portfolio(vw_a, tgt, rb)
            res = simulate_pac(r, CGT_SHARES, rf=rf_d2, realize_frac=tn)
            rows.append(row(f"D. Diversity-weighted p={p:.2f}, ribil. {lbl}", "D",
                            res, bench_key="cw49"))
    eqw = pd.DataFrame(1.0 / vw_a.shape[1], index=mu_lag.index, columns=mu_lag.columns)
    r, tn = run_d.simulate_portfolio(vw_a, eqw, 12)
    rows.append(row("D. Equal-weight 49 settori, ribil. annuale", "D",
                    simulate_pac(r, CGT_SHARES, rf=rf_d2, realize_frac=tn),
                    bench_key="cw49"))

    # ---------------------------------------------------------- output
    bench = next(r for r in rows if "BENCHMARK" in r["name"])
    own = {
        "shiller": bench["irr"],
        "ff_daily": next(r["irr"] for r in rows if "bench gruppo A" in r["name"]),
        "cw49": next(r["irr"] for r in rows if "bench gruppo D" in r["name"]),
    }
    for r in rows:
        r["vs_bench"] = r["irr"] - bench["irr"]
        r["vs_own"] = r["irr"] - own[r["bench_key"]]

    rows.sort(key=lambda r: -r["irr"])
    print(f"\nPAC {C.MONTHLY_CONTRIB:.0f} EUR/mese, {W0} -> {W1} "
          f"(versato {bench['contrib']:,.0f} EUR)\n")
    print(f"{'':<52}{'IRR':>8}{'vs bench':>10}{'vs proprio':>11}{'montante':>12}"
          f"{'max DD':>9}{'Sharpe':>8}{'op/an':>7}{'imposte':>11}")
    print("=" * 128)
    for r in rows:
        print(f"{r['name'][:51]:<52}{r['irr']:>7.2f}%{r['vs_bench']:>+9.2f}%"
              f"{r['vs_own']:>+10.2f}%{r['final']:>12,.0f}{r['dd']:>8.1f}%"
              f"{r['sharpe']:>8.2f}{r['trades_yr']:>7.1f}{r['taxes']:>11,.0f}")
    print("=" * 128)
    print("  'vs bench'  = contro il buy&hold Shiller (benchmark unico dichiarato)")
    print("  'vs proprio'= contro il buy&hold DELLO STESSO universo. E' la colonna")
    print("                onesta: neutralizza la differenza fra S&P composite,")
    print("                indice CRSP e paniere dei 49 settori.")

    beats = [r for r in rows if r["vs_own"] > 0.001 and "bench" not in r["name"]
             and "BENCHMARK" not in r["name"]]
    print(f"\nBattono il buy&hold del proprio universo: {len(beats)}")
    for r in beats:
        print(f"  {r['name'][:60]:<62}{r['vs_own']:+.2f} punti")
    # ---------------------------------------------------------- robustezza
    print("\n--- Robustezza di chi batte: costi doppi e sottoperiodi -----------")
    print(f"{'':<46}{'base':>9}{'costi x2':>10}{'1990-2006':>11}{'2007-2023':>11}")
    print("-" * 87)
    rob = []
    for r in beats:
        nm = r["name"]
        variants = {}
        if nm.startswith("Trend following"):
            lev = float(nm.split("leva ")[1].rstrip("x"))
            for lbl, (c0, c1, cost) in {
                    "costi x2": (W0, W1, C.COST_ROUND_TRIP * 2),
                    "1990-2006": ("1990-01", "2006-12", C.COST_ROUND_TRIP),
                    "2007-2023": ("2007-01", "2023-12", C.COST_ROUND_TRIP)}.items():
                cc = run_c.build(c0, c1)
                rr = run_c.levered_return(cc["total_ret"], cc["trend_pos"], lev,
                                          cc["rf"])
                a = simulate_pac(rr, CGT_SHARES, in_market=cc["trend_pos"],
                                 rf=cc["rf"], cost_rt=cost)
                b = simulate_pac(cc["total_ret"], CGT_SHARES, rf=cc["rf"],
                                 cost_rt=cost)
                variants[lbl] = a.irr_annual - b.irr_annual
        elif nm.startswith("D."):
            for lbl, (c0, c1, cost) in {
                    "costi x2": (W0, W1, C.COST_ROUND_TRIP * 2),
                    "1990-2006": ("1990-01", "2006-12", C.COST_ROUND_TRIP),
                    "2007-2023": ("2007-01", "2023-12", C.COST_ROUND_TRIP)}.items():
                sl = (mu_lag.index >= c0) & (mu_lag.index <= c1)
                ml, va = mu_lag[sl], vw_a[sl]
                cwr = (ml * va).sum(axis=1)
                rfx = rf.reindex(cwr.index).fillna(0.0)
                if "Equal-weight" in nm:
                    tg = pd.DataFrame(1.0 / va.shape[1], index=ml.index,
                                      columns=ml.columns)
                    rb = 12
                else:
                    pv = float(nm.split("p=")[1].split(",")[0])
                    tg = ml.apply(lambda r_: run_d.dw_weights(r_, pv), axis=1)
                    rb = 12 if "annuale" in nm else 1
                rr, tn = run_d.simulate_portfolio(va, tg, rb, cost_rt=cost)
                a = simulate_pac(rr, CGT_SHARES, rf=rfx, realize_frac=tn,
                                 cost_rt=cost)
                b = simulate_pac(cwr, CGT_SHARES, rf=rfx, cost_rt=cost)
                variants[lbl] = a.irr_annual - b.irr_annual
        rob.append(dict(name=nm, base=r["vs_own"], **variants))
        print(f"{nm[:45]:<46}{r['vs_own']:>+8.2f}%"
              + "".join(f"{variants.get(k, float('nan')):>+9.2f}%"
                        for k in ("costi x2", "1990-2006", "2007-2023")))
    print("  (valori = punti di IRR sopra il buy&hold del proprio universo)")

    # ---------------------------------------------------------- gate sulla leva
    print("\n--- Gate sulla leva: funziona a 1x? -------------------------------")
    base1x = next(r for r in rows if r["name"] == "Trend following 10 mesi, leva 1x")
    print(f"  Trend following a 1x: IRR {base1x['irr']:.2f}%, "
          f"{base1x['vs_bench']:+.2f} punti contro il benchmark")
    print(f"  Sharpe 1x {base1x['sharpe']:.2f} contro benchmark {bench['sharpe']:.2f}, "
          f"DD {base1x['dd']:.1f}% contro {bench['dd']:.1f}%")
    print("  A 1x rende MENO del buy&hold ma con Sharpe e drawdown migliori: la leva")
    print("  qui non moltiplica un extra-rendimento, ricompra beta che la strategia")
    print("  aveva tolto stando fuori dal mercato.")

    notes = [r for r in rows if r["note"]]
    if notes:
        print("\nScenario riqualificazione come attivita' commerciale (52%):")
        for r in notes:
            print(f"  {r['name'][:60]:<62}{r['note']}")

    with open(OUT / "final_table.json", "w") as f:
        json.dump(rows, f, indent=1, default=float)
    return rows


if __name__ == "__main__":
    main()

"""Giro 14 — NASDAQ come mercato di replica.

Fin qui tutto e' girato su universi CRSP/S&P. Il NASDAQ Composite (FRED
NASDAQCOM, dal 1971) e' un mercato diverso: piu' concentrato sul tecnologico,
volatilita' e drawdown molto piu' grandi, e una bolla nel 2000 che nessun'altra
serie qui dentro contiene con quella violenza.

E' il test che avevo dichiarato mancante fin dall'inizio: "un edge che esiste su
un solo ticker e un solo decennio non e' un edge". I parametri NON vengono
riottimizzati: prendo quelli scelti sull'indice CRSP e li applico qui. Se
reggono e' replica, se cadono era adattamento al campione.

LIMITE: NASDAQCOM e' un indice di PREZZO, non total return. Sottostima il
rendimento di circa il dividend yield (storicamente ~1%/anno sul Nasdaq, molto
meno dell'S&P). Il confronto strategia/buy&hold e' interno alla stessa serie,
quindi il difetto si cancella; il livello assoluto no, e lo dichiaro.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
import strategies as S
from tax import simulate_pac, CGT_SHARES, first_of_month
from research import lab, multidata as M

ROUND = 14
OUT = Path(__file__).resolve().parents[2] / "out"


def nasdaq_daily(series="NASDAQCOM"):
    px = M.fred(series).sort_index()
    px = px[px > 0]
    return px


def main():
    px = nasdaq_daily("NASDAQCOM")
    ret = px.pct_change().dropna()
    print(f"NASDAQ Composite (prezzo): {px.index[0].date()} -> {px.index[-1].date()}"
          f"  ({len(px)} sedute)")
    yrs = len(ret) / 252
    print(f"  CAGR prezzo {(( 1+ret).prod()**(1/yrs)-1)*100:.2f}%   "
          f"vol {ret.std()*np.sqrt(252)*100:.1f}%   "
          f"max DD {((1+ret).cumprod()/(1+ret).cumprod().cummax()-1).min()*100:.1f}%")

    ffd = dataio.ff_factors_daily()
    rf_d = ffd["RF"].reindex(ret.index).ffill().fillna(0.0)
    com = first_of_month(ret.index)

    bh = simulate_pac(ret, CGT_SHARES, rf=rf_d, periods_per_year=252, contrib_on=com)
    print(f"\nBuy&hold NASDAQ come PAC: IRR netta {bh.irr_annual:.2f}%  "
          f"DD {bh.max_dd:.1f}%  Sharpe {lab.summarise(ret, rf_d, 252)['sharpe']:.2f}")

    # --- parametri scelti sull'indice CRSP, applicati QUI senza riottimizzare
    ga = json.load(open(OUT / "group_a.json"))
    close = S.build_index(ret)
    print(f"\n--- Gruppo A: parametri scelti su CRSP, applicati al NASDAQ ---")
    print(f"{'strategia':<38}{'parametri':<28}{'IRR':>8}{'vs B&H':>9}"
          f"{'Sharpe':>8}{'DD':>9}{'op/an':>7}")
    rows = []
    for row in ga["rows"]:
        fn = S.GRIDS[row["name"]][0]
        pos = S.positions(fn, close, row["params"]).reindex(ret.index).fillna(0.0)
        turn = pos.diff().abs().fillna(pos.abs())
        gross = pos * ret - turn * C.COST_ROUND_TRIP / 2.0
        res = simulate_pac(gross, CGT_SHARES, in_market=pos, rf=rf_d,
                           periods_per_year=252, contrib_on=com)
        sh = lab.summarise(gross, rf_d, 252)["sharpe"]
        rows.append(dict(name=row["name"], irr=res.irr_annual,
                         vs=res.irr_annual - bh.irr_annual, sharpe=sh,
                         dd=res.max_dd, tr=res.trades_per_year))
        print(f"{row['name'][:37]:<38}{str(row['params'])[:27]:<28}"
              f"{res.irr_annual:>7.2f}%{res.irr_annual-bh.irr_annual:>+8.2f}%"
              f"{sh:>8.2f}{res.max_dd:>8.1f}%{res.trades_per_year:>7.1f}")
        lab.log_trials([dict(round=ROUND, hypothesis="H15 replica NASDAQ",
                             config=f"{row['name']}:{row['params']}",
                             window="NASDAQ", sharpe=sh, irr=res.irr_annual,
                             bh_irr=bh.irr_annual,
                             excess=res.irr_annual - bh.irr_annual,
                             n_obs=len(ret), note="parametri da CRSP")])

    # --- trend following mensile a 10 mesi, regola pubblicata
    pxm = px.resample("ME").last()
    rm = pxm.pct_change().dropna()
    ma = pxm.rolling(10).mean()
    sig = (pxm > ma).astype(float).shift(1).reindex(rm.index).fillna(0.0)
    ffm = dataio.ff_factors_monthly()["RF"].reindex(rm.index).ffill().fillna(0.0)
    bh_m = simulate_pac(rm, CGT_SHARES, rf=ffm)
    print(f"\n--- Trend following 10 mesi (regola Faber, nessuna ottimizzazione) ---")
    print(f"{'':<26}{'IRR':>8}{'vs B&H':>9}{'Sharpe':>8}{'DD':>9}")
    print(f"{'buy&hold NASDAQ':<26}{bh_m.irr_annual:>7.2f}%{0.0:>+8.2f}%"
          f"{lab.summarise(rm, ffm)['sharpe']:>8.2f}{bh_m.max_dd:>8.1f}%")
    for lev in (1.0, 1.5, 2.0):
        r = sig * rm * lev - max(lev - 1, 0) * (ffm + C.FIN_SPREAD / 12) * sig
        res = simulate_pac(r, CGT_SHARES, in_market=sig, rf=ffm)
        sh = lab.summarise(r, ffm)["sharpe"]
        print(f"{'trend 10m leva ' + f'{lev:g}x':<26}{res.irr_annual:>7.2f}%"
              f"{res.irr_annual-bh_m.irr_annual:>+8.2f}%{sh:>8.2f}{res.max_dd:>8.1f}%")
        lab.log_trials([dict(round=ROUND, hypothesis="H15 replica NASDAQ",
                             config=f"trend10m lev={lev}", window="NASDAQ-M",
                             sharpe=sh, irr=res.irr_annual, bh_irr=bh_m.irr_annual,
                             excess=res.irr_annual - bh_m.irr_annual,
                             n_obs=len(rm), note="regola pubblicata")])

    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")
    beat = [r for r in rows if r["vs"] > 0]
    print(f"Strategie del gruppo A che battono il buy&hold NASDAQ: {len(beat)}/{len(rows)}")
    return rows


if __name__ == "__main__":
    main()

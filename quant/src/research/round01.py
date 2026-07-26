"""Giro 01 — Ipotesi H1.

IPOTESI. Combinare azionario con asset a driver diverso (tassi, valute, materie
prime) abbassa la volatilita' piu' di quanto abbassi il rendimento atteso. Lo
Sharpe sale, e una leva moderata riporta il rendimento sopra quello azionario.
Sotto CGT irlandese la cosa e' fragile: ogni ribilanciamento realizza utili al
33%, quindi l'ipotesi vale solo se la rotazione resta bassa.

PREDIZIONE FALSIFICABILE. Il portafoglio misto a leva batte il PAC buy&hold
azionario su TEST di almeno 0,5 punti di IRR, con ribilanciamento non piu'
frequente dell'annuale.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from research import lab
from research import run_round as R

ROUND = 1
HYP = "H1 multi-asset a bassa rotazione, con e senza leva"


def main():
    assets, ls, rf = R.build_assets()
    eq, bonds = assets["US equity"], assets["US 10y"]

    # finestra comune: i tassi FRED partono dal 1962
    comp = pd.DataFrame({"eq": eq, "bond": bonds}).dropna()
    print(f"Universo: azionario USA + decennale USA, "
          f"{comp.index[0].date()} -> {comp.index[-1].date()} ({len(comp)} mesi)")

    tr = lab.win(comp, lab.TRAIN)
    te = lab.win(comp, lab.TEST)
    print(f"TRAIN {tr.index[0].date()}->{tr.index[-1].date()} ({len(tr)} mesi)   "
          f"TEST {te.index[0].date()}->{te.index[-1].date()} ({len(te)} mesi)")
    print(f"Correlazione azioni/obbligazioni  TRAIN {tr.corr().iloc[0,1]:+.2f}   "
          f"TEST {te.corr().iloc[0,1]:+.2f}")

    # -------------------------------------------------- griglia su TRAIN
    grid = []
    for w_eq in (0.4, 0.5, 0.6, 0.7, 0.8):
        for rebal in (12, 60):
            for lv in (1.0, 1.25, 1.5, 1.75, 2.0):
                grid.append((w_eq, rebal, lv))
    print(f"\nConfigurazioni in griglia: {len(grid)}")

    rf_tr = rf.reindex(tr.index).fillna(0.0)
    best, bcfg = None, None
    for w_eq, rebal, lv in grid:
        r, tn = R.blend({"eq": tr["eq"], "bond": tr["bond"]},
                        {"eq": w_eq, "bond": 1 - w_eq}, rebal)
        rl = R.lever(r, rf_tr, lv)
        res = R.pac(rl, rf_tr, realize=tn)
        if best is None or res.irr_annual > best.irr_annual:
            best, bcfg = res, (w_eq, rebal, lv)
    bh_tr = R.pac(tr["eq"], rf_tr)
    print(f"Migliore su TRAIN: azioni {bcfg[0]:.0%}, ribil. {bcfg[1]}m, leva {bcfg[2]}x"
          f"  -> IRR {best.irr_annual:.2f}% contro buy&hold {bh_tr.irr_annual:.2f}%")

    # -------------------------------------------------- valutazione su TEST
    # Valuto sia la configurazione scelta su TRAIN sia l'intera griglia: ogni
    # valutazione su TEST e' un tentativo e va nel registro, altrimenti il
    # Deflated Sharpe sottostima quanto ho cercato.
    rf_te = rf.reindex(te.index).fillna(0.0)
    bh_te = R.pac(te["eq"], rf_te)
    trials, rows = [], []
    for w_eq, rebal, lv in grid:
        r, tn = R.blend({"eq": te["eq"], "bond": te["bond"]},
                        {"eq": w_eq, "bond": 1 - w_eq}, rebal)
        rl = R.lever(r, rf_te, lv)
        res = R.pac(rl, rf_te, realize=tn)
        s = lab.summarise(rl, rf_te)
        rows.append(dict(cfg=(w_eq, rebal, lv), irr=res.irr_annual,
                         excess=res.irr_annual - bh_te.irr_annual,
                         sharpe=s["sharpe"], mdd=res.max_dd, ret=rl))
        trials.append(dict(round=ROUND, hypothesis=HYP,
                           config=f"eq={w_eq},rebal={rebal},lev={lv}",
                           window="TEST", sharpe=s["sharpe"], irr=res.irr_annual,
                           bh_irr=bh_te.irr_annual,
                           excess=res.irr_annual - bh_te.irr_annual,
                           n_obs=len(te), note=""))
    lab.log_trials(trials)
    n_cum = lab.n_trials_so_far()

    rows.sort(key=lambda d: -d["irr"])
    print(f"\nTEST — buy&hold azionario: IRR {bh_te.irr_annual:.2f}%, "
          f"Sharpe {lab.summarise(te['eq'], rf_te)['sharpe']:.2f}, "
          f"DD {bh_te.max_dd:.1f}%")
    print(f"\n{'config (eq, ribil, leva)':<28}{'IRR':>8}{'vs BH':>9}{'Sharpe':>8}{'DD':>9}")
    for d in rows[:6]:
        print(f"{str(d['cfg']):<28}{d['irr']:>7.2f}%{d['excess']:>+8.2f}%"
              f"{d['sharpe']:>8.2f}{d['mdd']:>8.1f}%")
    print("  ...")
    for d in rows[-2:]:
        print(f"{str(d['cfg']):<28}{d['irr']:>7.2f}%{d['excess']:>+8.2f}%"
              f"{d['sharpe']:>8.2f}{d['mdd']:>8.1f}%")

    # configurazione scelta su TRAIN, valutata su TEST: e' l'unico numero onesto
    chosen = next(d for d in rows if d["cfg"] == bcfg)
    print(f"\nConfigurazione scelta su TRAIN, misurata su TEST:")
    print(f"  {bcfg}  IRR {chosen['irr']:.2f}%  ({chosen['excess']:+.2f} vs buy&hold)"
          f"  Sharpe {chosen['sharpe']:.2f}  DD {chosen['mdd']:.1f}%")

    d = lab.deflated_sharpe(chosen["ret"], n_cum, rf=rf_te)
    print(f"\nDeflated Sharpe su {n_cum} tentativi cumulati:")
    print(f"  Sharpe annualizzato osservato : {d['sr_ann']:.3f}")
    print(f"  soglia attesa sotto H0 (SR0)  : {d['sr0']*np.sqrt(12):.3f} annualizzato")
    print(f"  DSR                           : {d['dsr']:.3f}"
          f"   {'PROMUOVIBILE' if d['dsr'] > 0.95 else 'NON promuovibile (serve > 0,95)'}")
    return chosen, d, bh_te, n_cum


if __name__ == "__main__":
    main()

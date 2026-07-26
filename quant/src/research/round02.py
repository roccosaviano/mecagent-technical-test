"""Giro 02 — Ipotesi H3 (H2 rinviata: TSMOM parte dal 1985, TRAIN troppo corto).

IPOTESI. Un overlay multi-stile su sei classi di asset (AQR Century of Factor
Premia: value, momentum, carry, defensive su azioni, indici, tassi, valute,
materie prime) ha correlazione bassa con l'azionario. Aggiunto a un core
azionario buy&hold dovrebbe alzare lo Sharpe abbastanza da giustificare leva.

PREDIZIONE FALSIFICABILE. Il core azionario + overlay batte il PAC buy&hold su
TEST di almeno 0,5 punti di IRR, con DSR > 0,95 sul cumulato dei tentativi.

ATTENZIONE ALL'IMPLEMENTABILITA'. Questi sono premi LONG-SHORT: richiedono
vendite allo scoperto e leva su sei mercati. Con 500 EUR/mese non sono
replicabili direttamente. L'unico accesso retail e' un fondo liquid-alt, che in
Irlanda e' quasi sempre UCITS: exit tax 38% + deemed disposal ogni 8 anni, cioe'
il regime peggiore. Modello entrambi i casi.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES, ETF_UCITS
from research import lab
from research import multidata as M
from research import run_round as R

ROUND = 2
HYP = "H3 core azionario + overlay multi-stile 6 classi di asset (AQR Century)"

# Drag di implementazione retail sull'overlay long-short, dichiarato:
#  - transazioni: ~300%/anno di turnover bilaterale x 0,15% = 0,45%
#  - prestito titoli sulla gamba short: 2,0% (meta' nozionale al 4%)
#  - finanziamento della leva implicita: 1,0%
# AQR pubblica i premi al lordo di tutto questo.
OVERLAY_DRAG_ANN = 0.045 + 0.020 + 0.010


def main():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    eq = (ff["Mkt-RF"] + ff["RF"]).rename("eq")
    cen = M.century()

    col = "All asset classes Multi-style"
    if col not in cen.columns:
        col = [c for c in cen.columns if "All asset classes" in c][0]
    ov = cen[col].dropna().rename("overlay")

    comp = pd.DataFrame({"eq": eq, "overlay": ov}).dropna()
    print(f"Universo: azionario USA + '{col}'")
    print(f"  {comp.index[0].date()} -> {comp.index[-1].date()} ({len(comp)} mesi)")

    tr, te = lab.win(comp, lab.TRAIN), lab.win(comp, lab.TEST)
    print(f"TRAIN {tr.index[0].date()}->{tr.index[-1].date()} ({len(tr)})   "
          f"TEST {te.index[0].date()}->{te.index[-1].date()} ({len(te)})")
    print(f"Correlazione overlay/azionario  TRAIN {tr.corr().iloc[0,1]:+.2f}   "
          f"TEST {te.corr().iloc[0,1]:+.2f}")
    print(f"Overlay lordo: TRAIN {tr['overlay'].mean()*1200:.2f}%/anno   "
          f"TEST {te['overlay'].mean()*1200:.2f}%/anno   "
          f"(drag retail applicato: {OVERLAY_DRAG_ANN*100:.1f}%/anno)")

    def combo(win_df, rf_w, w_ov, rebal, lv, regime=CGT_SHARES):
        """Core azionario + quota di overlay. L'overlay e' un rendimento in
        eccesso: chi lo detiene incassa anche RF sul collaterale."""
        ovr = win_df["overlay"] - OVERLAY_DRAG_ANN / 12.0
        parts = {"eq": win_df["eq"], "ov": rf_w + ovr}
        r, tn = R.blend(parts, {"eq": 1 - w_ov, "ov": w_ov}, rebal)
        rl = R.lever(r, rf_w, lv)
        # l'overlay ruota ogni mese al suo interno: realizza utili di continuo
        realize = (tn + w_ov).clip(0, 1)
        return rl, realize, simulate_pac(rl, regime, rf=rf_w, realize_frac=realize)

    grid = [(w, rb, lv) for w in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5)
            for rb in (12, 60) for lv in (1.0, 1.25, 1.5, 1.75, 2.0)]
    print(f"\nConfigurazioni in griglia: {len(grid)}")

    rf_tr = rf.reindex(tr.index).fillna(0.0)
    best, bcfg = None, None
    for w, rb, lv in grid:
        _, _, res = combo(tr, rf_tr, w, rb, lv)
        if best is None or res.irr_annual > best.irr_annual:
            best, bcfg = res, (w, rb, lv)
    bh_tr = simulate_pac(tr["eq"], CGT_SHARES, rf=rf_tr)
    print(f"Migliore su TRAIN: overlay {bcfg[0]:.0%}, ribil. {bcfg[1]}m, leva {bcfg[2]}x"
          f"  -> IRR {best.irr_annual:.2f}% contro buy&hold {bh_tr.irr_annual:.2f}%")

    rf_te = rf.reindex(te.index).fillna(0.0)
    bh_te = simulate_pac(te["eq"], CGT_SHARES, rf=rf_te)
    trials, rows = [], []
    for w, rb, lv in grid:
        rl, rz, res = combo(te, rf_te, w, rb, lv)
        s = lab.summarise(rl, rf_te)
        rows.append(dict(cfg=(w, rb, lv), irr=res.irr_annual, sharpe=s["sharpe"],
                         excess=res.irr_annual - bh_te.irr_annual,
                         mdd=res.max_dd, ret=rl))
        trials.append(dict(round=ROUND, hypothesis=HYP,
                           config=f"ov={w},rebal={rb},lev={lv}", window="TEST",
                           sharpe=s["sharpe"], irr=res.irr_annual,
                           bh_irr=bh_te.irr_annual,
                           excess=res.irr_annual - bh_te.irr_annual,
                           n_obs=len(te), note=""))
    lab.log_trials(trials)
    n_cum = lab.n_trials_so_far()

    rows.sort(key=lambda d: -d["irr"])
    print(f"\nTEST — buy&hold azionario: IRR {bh_te.irr_annual:.2f}%  "
          f"Sharpe {lab.summarise(te['eq'], rf_te)['sharpe']:.2f}  DD {bh_te.max_dd:.1f}%")
    print(f"\n{'config (overlay, ribil, leva)':<30}{'IRR':>8}{'vs BH':>9}{'Sharpe':>8}{'DD':>9}")
    for d in rows[:6]:
        print(f"{str(d['cfg']):<30}{d['irr']:>7.2f}%{d['excess']:>+8.2f}%"
              f"{d['sharpe']:>8.2f}{d['mdd']:>8.1f}%")

    chosen = next(d for d in rows if d["cfg"] == bcfg)
    print(f"\nConfigurazione scelta su TRAIN, misurata su TEST:")
    print(f"  {bcfg}  IRR {chosen['irr']:.2f}%  ({chosen['excess']:+.2f} vs buy&hold)"
          f"  Sharpe {chosen['sharpe']:.2f}  DD {chosen['mdd']:.1f}%")

    d = lab.deflated_sharpe(chosen["ret"], n_cum, rf=rf_te, round_id=ROUND)
    print(f"\nDeflated Sharpe su {n_cum} tentativi cumulati:")
    print(f"  Sharpe annualizzato : {d['sr_ann']:.3f}   soglia H0 SR0: "
          f"{d['sr0']*np.sqrt(12):.3f}")
    print(f"  DSR                 : {d['dsr']:.3f}   "
          f"{'PROMUOVIBILE' if d['dsr'] > 0.95 else 'NON promuovibile (serve > 0,95)'}")

    # implementabilita': stesso portafoglio via fondo UCITS
    rl, rz, _ = combo(te, rf_te, *bcfg)
    ucits = simulate_pac(rl, ETF_UCITS, rf=rf_te)
    print(f"\nSe l'overlay e' accessibile solo via fondo UCITS (caso realistico):")
    print(f"  IRR {ucits.irr_annual:.2f}%  contro {chosen['irr']:.2f}% in regime CGT"
          f"  ->  {ucits.irr_annual - chosen['irr']:+.2f} punti")
    print(f"  contro il buy&hold azionario: {ucits.irr_annual - bh_te.irr_annual:+.2f} punti")
    return chosen, d, bh_te, n_cum


if __name__ == "__main__":
    main()

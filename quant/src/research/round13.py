"""Giro 13 — La frontiera fra rotazione ed edge.

Il giro 12 ha mostrato che frenare la rotazione del momentum settoriale scambia
edge lordo contro efficienza fiscale: da 259% di turnover e +2,95 punti a 70% e
+1,38. Ma il confronto e' viziato, perche' a 259% l'aliquota realistica e' il 52%
(riqualificazione come attivita' commerciale) e a 70% e' il 33%.

Qui mappo la frontiera per intero e applico a ogni punto L'ALIQUOTA CHE GLI
COMPETE, invece di confrontare tutti al 33%. La domanda operativa e': esiste un
livello di rotazione che massimizza l'IRR NETTA, e quanto vale?

Regola usata per l'aliquota: sotto il 100% di turnover annuo assumo CGT 33%,
sopra assumo la riqualificazione al 52%. La soglia non e' di legge — Revenue
guarda frequenza, organizzazione e intento (badges of trade) — ma serve una
regola esplicita, e questa e' prudente in entrambe le direzioni.
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
from research.round12 import momentum_buffered

ROUND = 13
TURNOVER_FLAG = 1.0     # 100%/anno: sopra, assumo riqualificazione


def main():
    ff = dataio.ff_factors_monthly()
    rf, eq = ff["RF"], (ff["Mkt-RF"] + ff["RF"]).rename("eq")
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all")
    lg = np.log1p(ind)
    MOM = np.expm1(lg.rolling(12).sum()).shift(2)
    build = momentum_buffered(ind, MOM)

    # ogni configurazione e' un punto della frontiera: la valuto in walk-forward
    # senza ottimizzare, cosi' il confronto e' fra regimi di rotazione e non
    # fra esiti di una ricerca
    configs = [
        (5, 5, 0, 1), (5, 10, 0, 1), (5, 15, 0, 3), (5, 25, 0, 3),
        (5, 25, 6, 3), (5, 25, 12, 12), (10, 15, 0, 3), (10, 25, 0, 12),
        (10, 30, 12, 12), (10, 40, 24, 12),
    ]
    print(f"Frontiera rotazione/edge: {len(configs)} punti, ciascuno valutato in")
    print("walk-forward senza ottimizzazione (nessuna scelta = nessun tentativo)\n")

    rows = []
    for cfg in configs:
        oos, rzs, picks, ne, vsr = WF.walk_forward(build, [cfg], ind.index, rf,
                                              start_year=1935)
        if len(oos) == 0:
            continue
        idx = oos.index.intersection(eq.index)
        oos, rz = oos.reindex(idx), rzs.reindex(idx).fillna(0.0)
        b, rfw = eq.reindex(idx), rf.reindex(idx).fillna(0.0)
        turn = float(rz.mean() * 12)
        regime = TRADING_52 if turn > TURNOVER_FLAG else CGT_SHARES
        res = simulate_pac(oos, regime, rf=rfw, realize_frac=rz)
        bh = simulate_pac(b, CGT_SHARES, rf=rfw)
        # e per confronto, lo stesso punto valutato all'aliquota "sbagliata"
        alt = simulate_pac(oos, CGT_SHARES if regime == TRADING_52 else TRADING_52,
                           rf=rfw, realize_frac=rz)
        s = lab.summarise(oos, rfw)
        rows.append(dict(cfg=cfg, turn=turn * 100, regime="52%" if regime == TRADING_52
                         else "33%", irr=res.irr_annual, vs=res.irr_annual - bh.irr_annual,
                         alt=alt.irr_annual - bh.irr_annual, sharpe=s["sharpe"],
                         dd=res.max_dd, ret=oos, rz=rz, n_eval=ne))
        lab.log_trials([dict(round=ROUND, hypothesis="H13 frontiera rotazione",
                             config=str(cfg), window="WF-OOS", sharpe=s["sharpe"],
                             irr=res.irr_annual, bh_irr=bh.irr_annual,
                             excess=res.irr_annual - bh.irr_annual,
                             n_obs=len(idx), note=f"turn={turn*100:.0f}%")])

    rows.sort(key=lambda r: r["turn"])
    print(f"{'config (K,buffer,hold,ribil)':<30}{'turnover':>10}{'aliq.':>7}"
          f"{'IRR':>9}{'vs B&H':>9}{'altra aliq.':>13}{'Sharpe':>8}{'DD':>9}")
    print("-" * 95)
    for r in rows:
        print(f"{str(r['cfg']):<30}{r['turn']:>9.0f}%{r['regime']:>7}"
              f"{r['irr']:>8.2f}%{r['vs']:>+8.2f}%{r['alt']:>+12.2f}%"
              f"{r['sharpe']:>8.2f}{r['dd']:>8.1f}%")

    best = max(rows, key=lambda r: r["vs"])
    print(f"\nMassimo dell'IRR netta: {best['cfg']} con turnover "
          f"{best['turn']:.0f}%/anno, {best['vs']:+.2f} punti sul buy&hold")
    n_cum = lab.n_trials_so_far()
    # ogni punto e' valutato con una griglia da uno: la dispersione che conta
    # e' quella FRA i punti della frontiera, non dentro ciascuno
    import numpy as _np
    vsr = float((pd.Series([r["sharpe"] for r in rows]) / _np.sqrt(12)).var(ddof=1))
    d = lab.deflated_sharpe(best["ret"], n_cum,
                            rf=rf.reindex(best["ret"].index).fillna(0.0),
                            round_id=ROUND, var_sr=vsr)
    print(f"DSR su {n_cum} tentativi cumulati: {d['dsr']:.3f}"
          f"  (SR0 {d['sr0']*np.sqrt(12):.3f} ann.)")
    print(f"  -> {'PROMUOVIBILE' if d['dsr'] > 0.95 else 'NON promuovibile'}")

    print("\nLettura della colonna 'altra aliquota': e' lo stesso punto valutato")
    print("con l'aliquota opposta. Dove i due numeri divergono molto, il risultato")
    print("dipende dalla classificazione fiscale piu' che dalla strategia.")
    return rows


if __name__ == "__main__":
    main()

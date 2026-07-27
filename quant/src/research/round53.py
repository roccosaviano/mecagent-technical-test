"""Giro 53 — G1 (filtri di tendenza) e G2 (indice momentum come veicolo).

DUE VOCI DELLA CODA, verbatim in QUEUE.md.

G1 filtri su un PAC azionario: tutti riducono rischio e perdono IRR; il migliore
   perde meno di 2 punti, il peggiore piu' di 4.
   FALSIFICATA SE: un filtro batte il buy&hold netto imposte.
G2 momentum come VEICOLO: incartato in un fondo batte il cap-weighted a parita'
   di regime, ma il veicolo che lo rende possibile in Irlanda e' un ETF UCITS
   che costa 2,15 punti, quindi momentum-in-ETF perde contro cap-weight-diretto.
   FALSIFICATA SE: momentum in ETF UCITS batte il cap-weighted diretto in CGT.

LA DIFFERENZA CHE G2 ISOLA. Al giro 50 la rotazione era MIA: ogni ribilanciamento
realizzava e pagava. Dentro un fondo la stessa rotazione non e' un evento fiscale
per chi detiene le quote — si paga alla vendita. I costi di transazione restano e
li paga il fondo, quindi restano nel rendimento lordo.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES, ETF_UCITS
from research import lab, bench as B

ROUND = 53
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 74


def pac(ret, rf, regime, realize=None):
    return simulate_pac(ret, regime, rf=rf.reindex(ret.index).fillna(0.0),
                        realize_frac=(realize.reindex(ret.index).clip(0, 1)
                                      if realize is not None else None),
                        periods_per_year=12)


def main():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()

    # ================================================================ G1
    print(f"{'='*92}\nG1 — I FILTRI DI TENDENZA SU UN PAC AZIONARIO\n{'='*92}")
    idx = mkt.index
    rf0 = rf.reindex(idx).fillna(0.0)
    px = (1 + mkt).cumprod()
    rows1 = [B.eval_stream("buy&hold (nessun filtro)", mkt, rf0)]
    bh1 = rows1[0]
    filters = {}
    for n in (6, 10, 12):
        filters[f"media mobile {n} mesi"] = B.ma_filter(px, n)
    e9, e21, e50, e200 = (px.ewm(span=s, adjust=False).mean()
                          for s in (9, 21, 50, 200))
    filters["EMA200 + EMA21>EMA50"] = ((px > e200) & (e21 > e50)).shift(1) \
        .fillna(False).astype(float)
    ffd = dataio.ff_factors_daily()
    dpx = (1 + (ffd["Mkt-RF"] + ffd["RF"])).cumprod()
    ma200 = (dpx > dpx.rolling(200).mean()).resample("ME").last()
    ma200.index = ma200.index.to_period("M").to_timestamp("M")
    filters["media 200 giorni"] = ma200.shift(1).reindex(idx).fillna(False).astype(float)
    for nm, e in filters.items():
        rows1.append(B.eval_exposure(nm, mkt, rf0, e.reindex(idx).fillna(0.0)))
    B.table(rows1, cols=("label", "cagr", "vol", "sharpe", "dd", "turn", "irr", "irr52"))
    cand1 = rows1[1:]
    print(f"\n   {'filtro':<26}{'vs buy&hold':>13}{'DD evitato':>13}")
    for r in cand1:
        print(f"   {r['label']:<26}{r['irr_ref']-bh1['irr']:>+12.2f}"
              f"{r['dd']-bh1['dd']:>+12.1f}")
    g1_fals = any(r["irr_ref"] > bh1["irr"] for r in cand1)
    losses = sorted(bh1["irr"] - r["irr_ref"] for r in cand1)
    print(f"\n   Il migliore perde {losses[0]:.2f} punti, il peggiore {losses[-1]:.2f}")
    print(f"   -> ipotesi G1 {'FALSIFICATA' if g1_fals else 'CONFERMATA'}")

    # ================================================================ G2
    print(f"\n{'='*92}\nG2 — L'INDICE MOMENTUM COME VEICOLO\n{'='*92}")
    W = B.xs_momentum(ind, 12, 1, 10)
    net_m, turn_m = B.wbacktest(ind, W.shift(1).fillna(0.0))
    net_m = net_m.dropna()
    ix = net_m.index.intersection(mkt.index)
    net_m, turn_m = net_m.reindex(ix), turn_m.reindex(ix)
    cap = mkt.reindex(ix)
    ew = ind.mean(axis=1).reindex(ix)
    rfg = rf.reindex(ix).fillna(0.0)
    print(f"   Finestra {ix[0].date()} -> {ix[-1].date()} ({len(ix)} mesi)")
    print(f"   Momentum settoriale top-10 mensile, rotazione "
          f"{float(turn_m.sum())/(len(ix)/12):.2f}x l'anno")
    print(f"   I costi di transazione (0,15%) sono gia' dentro il rendimento lordo:")
    print(f"   li paga il fondo. Cambia solo CHI realizza la plusvalenza.\n")

    rows2 = []
    combos = [
        ("momentum, rotazione MIA (giro 50)", net_m, turn_m, CGT_SHARES),
        ("momentum DENTRO un fondo, CGT", net_m, None, CGT_SHARES),
        ("momentum DENTRO un fondo, ETF UCITS", net_m, None, ETF_UCITS),
        ("cap-weighted diretto, CGT", cap, None, CGT_SHARES),
        ("cap-weighted via ETF UCITS", cap, None, ETF_UCITS),
        ("equal-weight dentro un fondo, CGT", ew, None, CGT_SHARES),
    ]
    print(f"   {'configurazione':<40}{'CAGR':>9}{'IRR netta':>12}")
    print("   " + "-" * 61)
    res = {}
    for lbl, r_, rz, reg in combos:
        p = pac(r_, rfg, reg, rz)
        st = B.stats(r_)
        res[lbl] = p.irr_annual
        rows2.append(dict(label=lbl, cagr=st["cagr"], irr=p.irr_annual,
                          dd=st["dd"], sharpe=st["sharpe"]))
        print(f"   {lbl:<40}{st['cagr']:>8.2f}%{p.irr_annual:>11.2f}%")

    print(f"\n   (a) A PARITA' DI REGIME, il momentum in un fondo batte il cap-weight?")
    d_cgt = res["momentum DENTRO un fondo, CGT"] - res["cap-weighted diretto, CGT"]
    d_etf = res["momentum DENTRO un fondo, ETF UCITS"] - res["cap-weighted via ETF UCITS"]
    print(f"       in CGT diretto  {d_cgt:+.2f} punti")
    print(f"       in ETF UCITS    {d_etf:+.2f} punti")
    print(f"   (b) Quanto vale spostare la rotazione dentro il fondo?")
    d_wrap = res["momentum DENTRO un fondo, CGT"] - res["momentum, rotazione MIA (giro 50)"]
    print(f"       stesso identico rendimento lordo: {d_wrap:+.2f} punti di IRR")
    print(f"   (c) IL CONFRONTO CHE CONTA per un residente irlandese:")
    d_real = res["momentum DENTRO un fondo, ETF UCITS"] - res["cap-weighted diretto, CGT"]
    print(f"       momentum in ETF UCITS {res['momentum DENTRO un fondo, ETF UCITS']:.2f}% "
          f"contro cap-weight diretto in CGT {res['cap-weighted diretto, CGT']:.2f}%")
    print(f"       -> {d_real:+.2f} punti")
    g2_fals = d_real > 0
    print(f"\n   -> ipotesi G2 {'FALSIFICATA' if g2_fals else 'CONFERMATA'}")

    best = max(rows2, key=lambda r: r["irr"])
    print(f"\n   Migliore in assoluto: {best['label']} ({best['irr']:.2f}%)")

    lab.log_trials([dict(round=ROUND, hypothesis="G1 filtri di tendenza",
                         config=r["label"], window="1926-2026", sharpe=r["sharpe"],
                         irr=r["irr"], bh_irr=bh1["irr"],
                         excess=r["irr_ref"] - bh1["irr"], n_obs=r["n"],
                         note=f"turn={r['turn']:.2f}x") for r in rows1] +
                   [dict(round=ROUND, hypothesis="G2 momentum come veicolo",
                         config=r["label"], window=f"{ix[0].date()}/{ix[-1].date()}",
                         sharpe=r["sharpe"], irr=r["irr"],
                         bh_irr=res["cap-weighted diretto, CGT"],
                         excess=r["irr"] - res["cap-weighted diretto, CGT"],
                         n_obs=len(ix), note="") for r in rows2])
    pd.DataFrame(rows2).to_csv(OUT / "round53_veicolo.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

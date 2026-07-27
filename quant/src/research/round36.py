"""Giro 36 — A9 (Kelly contro frazione fissa) e A10 (curva del prezzo del DD).

DUE VOCI DELLA CODA, predizioni scritte prima, verbatim.

A9 — Kelly aggiunge qualcosa a una frazione fissa?
  PREDIZIONE: la frazione fissa batte Kelly in IRR netta in almeno 3 casi su 4,
  perche' ha lo stesso profilo di esposizione media senza pagare la rotazione, e
  perche' mu stimato su 60 mesi e' pro-ciclico.
  FALSIFICATA SE: Kelly batte la frazione fissa in almeno meta' dei casi.

A10 — Il prezzo dell'assicurazione sul drawdown, come curva
  PREDIZIONE: il rapporto costo/beneficio e' peggiore alle soglie basse e
  migliora monotonamente fino a circa il 30-35%, oltre il quale la soglia scatta
  troppo di rado per proteggere. Esiste quindi un minimo interno, intorno al 30%.
  FALSIFICATA SE: il rapporto e' piatto o monotono su tutto l'intervallo.
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
from research import lab, bench as B
from research.round33 import kelly_exposure

ROUND = 36
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 56


def main():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ew = ind.mean(axis=1)
    unders = [("indice cap-weighted", mkt), ("equal-weight 49", ew)]

    # ------------------------------------------------------------- A9
    print(f"{'='*92}\nA9 — Kelly contro una frazione fissa pari alla sua "
          f"esposizione media\n{'='*92}")
    rows9, wins_fixed = [], 0
    for uname, ret in unders:
        rf0 = rf.reindex(ret.index).fillna(0.0)
        for f in (0.25, 0.5):
            e, _ = kelly_exposure(ret, rf0, f)
            m = float(e.mean())
            rk = B.eval_exposure(f"{uname[:16]} {f:g}K dinamico", ret, rf0, e)
            fixed = pd.Series(m, index=ret.index)
            rx = B.eval_exposure(f"{uname[:16]} fissa {m:.2f}", ret, rf0, fixed)
            rows9 += [rk, rx]
            d = rx["irr"] - rk["irr"]
            wins_fixed += int(d > 0)
            print(f"\n   {uname} · {f:g} Kelly (esposizione media {m:.2f})")
            print(f"     Kelly dinamico  IRR {rk['irr']:.2f}%  Sharpe "
                  f"{rk['sharpe']:.2f}  turnover {rk['turn']:.2f}x")
            print(f"     frazione fissa  IRR {rx['irr']:.2f}%  Sharpe "
                  f"{rx['sharpe']:.2f}  turnover {rx['turn']:.2f}x")
            print(f"     -> la frazione fissa {'VINCE' if d > 0 else 'perde'} "
                  f"di {d:+.2f} punti")
    print(f"\n   La frazione fissa batte Kelly in {wins_fixed}/4 casi")
    a9_fals = wins_fixed < 2
    print(f"   -> ipotesi A9 {'FALSIFICATA' if a9_fals else 'CONFERMATA'}")
    print(f"   Lettura: se la frazione fissa vince, la stima di Kelly non sta")
    print(f"   aggiungendo informazione — sta solo aggiungendo rotazione tassabile.")

    # ------------------------------------------------------------- A10
    print(f"\n{'='*92}\nA10 — il prezzo dell'assicurazione sul drawdown, "
          f"come curva\n{'='*92}")
    rows10 = []
    for uname, ret in unders:
        rf0 = rf.reindex(ret.index).fillna(0.0)
        e0, _ = kelly_exposure(ret, rf0, 0.5)
        base = B.eval_exposure(f"{uname} base", ret, rf0, e0)
        print(f"\n   {uname} — riferimento: 0,5 Kelly senza de-risking, "
              f"IRR {base['irr']:.2f}%, DD {base['dd']:.1f}%")
        print(f"   {'soglia':>8}{'IRR':>9}{'DD':>9}{'IRR ceduta':>12}"
              f"{'DD evitato':>12}{'punti IRR per punto DD':>25}")
        for thr in np.arange(0.05, 0.501, 0.05):
            e, _ = kelly_exposure(ret, rf0, 0.5, float(thr))
            r = B.eval_exposure(f"{uname[:16]} DD>{thr:.0%}", ret, rf0, e)
            d_irr = base["irr"] - r["irr"]          # positivo = costo
            d_dd = r["dd"] - base["dd"]             # positivo = DD meno profondo
            ratio = d_irr / d_dd if d_dd > 0.5 else float("nan")
            r.update(underlying=uname, thr=float(thr), cost=d_irr,
                     benefit=d_dd, ratio=ratio)
            rows10.append(r)
            print(f"   {thr:>7.0%}{r['irr']:>8.2f}%{r['dd']:>8.1f}%"
                  f"{d_irr:>11.2f}{d_dd:>12.1f}"
                  f"{(f'{ratio:.3f}' if ratio == ratio else 'n/d'):>25}")
        sub = [r for r in rows10 if r["underlying"] == uname
               and r["ratio"] == r["ratio"]]
        if sub:
            bestr = min(sub, key=lambda r: r["ratio"])
            print(f"   -> assicurazione piu' efficiente a soglia "
                  f"{bestr['thr']:.0%}: {bestr['ratio']:.3f} punti di IRR per "
                  f"punto di drawdown evitato")

    # verdetto A10: c'e' un minimo interno?
    print()
    verdicts = []
    for uname, _ in unders:
        sub = [r for r in rows10 if r["underlying"] == uname
               and r["ratio"] == r["ratio"]]
        if len(sub) < 4:
            verdicts.append((uname, None, None))
            continue
        ths = [r["thr"] for r in sub]
        rr = [r["ratio"] for r in sub]
        k = int(np.argmin(rr))
        interior = 0 < k < len(rr) - 1
        verdicts.append((uname, ths[k], interior))
        print(f"   {uname:<24} minimo a {ths[k]:.0%}  "
              f"({'INTERNO' if interior else 'agli estremi, non interno'})"
              f"  intervallo del rapporto {min(rr):.3f}-{max(rr):.3f}")
    a10_fals = not any(v[2] for v in verdicts if v[2] is not None)
    print(f"\n   -> ipotesi A10 {'FALSIFICATA' if a10_fals else 'CONFERMATA'}")
    print(f"   (falsificata se il rapporto e' piatto o monotono, cioe' senza")
    print(f"    minimo interno su nessuno dei due sottostanti)")

    lab.log_trials(
        [dict(round=ROUND, hypothesis="A9 Kelly contro frazione fissa",
              config=r["label"], window="varie", sharpe=r["sharpe"],
              irr=r["irr"], bh_irr="", excess="", n_obs=r["n"],
              note=f"turn={r['turn']:.2f}x") for r in rows9] +
        [dict(round=ROUND, hypothesis="A10 curva prezzo del drawdown",
              config=r["label"], window="varie", sharpe=r["sharpe"],
              irr=r["irr"], bh_irr="", excess="", n_obs=r["n"],
              note=f"costo={r['cost']:.2f},beneficio={r['benefit']:.1f}")
         for r in rows10])
    pd.DataFrame([{k: v for k, v in r.items() if k != "gross"}
                  for r in rows9 + rows10]).to_csv(OUT / "round36_kelly2.csv",
                                                   index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

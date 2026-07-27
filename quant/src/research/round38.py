"""Giro 38 — B3 (credito) e B4 (curva dei tassi).

DUE VOCI DELLA CODA, predizioni verbatim.

B3 — Credito (spread high yield BAMLH0A0HYM2)
  Esci dall'azionario quando lo spread sale oltre N deviazioni.
  PREDIZIONE: segnale con potere in-sample, ma il ritardo di pubblicazione e la
  reazione gia' incorporata nei prezzi lo rendono inutile out-of-sample.
  FALSIFICATA SE: batte il buy&hold netto imposte fuori campione.

B4 — Curva dei tassi (T10Y2Y) come segnale di regime azionario
  Riduzione dell'esposizione azionaria quando la curva si inverte.
  PREDIZIONE: il segnale e' corretto ma troppo lento — l'anticipo mediano
  dell'inversione e' 12-18 mesi, e uscire con quell'anticipo costa piu' di
  quanto protegga.
  FALSIFICATA SE: IRR netta > buy&hold.

DISCIPLINA. Entrambi i segnali usano una soglia. Se scegliessi la soglia
guardando tutto il campione, misurerei la mia capacita' di scegliere soglie.
Quindi:
  - lo z-score e' calcolato su finestra mobile all'indietro, mai sull'intero
    campione (nemmeno media e deviazione standard);
  - il segnale e' ritardato di un mese oltre alla costruzione, per il ritardo
    di pubblicazione e per non usare il dato del giorno stesso;
  - la soglia viene scelta WALK-FORWARD: ogni anno si usa quella che ha reso
    di piu' fino all'anno prima. Riporto anche l'intera griglia in-sample, cosi'
    si vede la differenza fra quello che sembra e quello che si sarebbe preso.
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
from research import lab, bench as B, multidata as M

ROUND = 38
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 56
GRID_Z = (1.0, 1.5, 2.0)
GRID_W = (36, 60)


def monthly_last(s):
    m = s.resample("ME").last()
    m.index = m.index.to_period("M").to_timestamp("M")
    return m


def zsignal(x, win, z, lag=1):
    """Esposizione 0/1: fuori dal mercato quando lo z-score supera z.
    Media e deviazione standard su finestra mobile, mai sull'intero campione."""
    mu = x.rolling(win).mean()
    sd = x.rolling(win).std()
    zz = ((x - mu) / sd).shift(lag)
    return (zz <= z).astype(float), zz


def walk_forward_choice(ret, rf, x, win_grid, z_grid, lag=1):
    """Ogni anno Y si usa la configurazione migliore fino a Y-1 compreso."""
    idx = ret.index
    e = pd.Series(1.0, index=idx)
    cfgs = [(w, z) for w in win_grid for z in z_grid]
    cache = {c: zsignal(x, c[0], c[1], lag)[0].reindex(idx).fillna(1.0)
             for c in cfgs}
    years = sorted(set(idx.year))
    chosen = {}
    for y in years:
        past = idx[idx.year < y]
        if len(past) < 60:
            continue
        best, bs = None, -9e9
        for c in cfgs:
            ee = cache[c].loc[past]
            g = ee * ret.loc[past] + (1 - ee) * rf.loc[past] * (1 - C.DIRT_RATE)
            v = float(g.mean() / g.std()) if g.std() > 0 else -9e9
            if v > bs:
                best, bs = c, v
        chosen[y] = best
        m = idx.year == y
        e[m] = cache[best].loc[m]
    return e, chosen


def run_signal(name, x, ret, rf, rows, lag=1):
    print(f"\n   Griglia IN-SAMPLE (quello che SEMBRA, non quello che si prende):")
    for w in GRID_W:
        for z in GRID_Z:
            e, _ = zsignal(x, w, z, lag)
            e = e.reindex(ret.index).fillna(1.0)
            r = B.eval_exposure(f"{name} in-sample w{w} z{z}", ret, rf, e)
            rows.append(r)
            print(f"     finestra {w}m soglia {z}   IRR {r['irr']:>6.2f}%  "
                  f"esposizione media {float(e.mean()):.2f}  "
                  f"turnover {r['turn']:.2f}x")
    e, chosen = walk_forward_choice(ret, rf, x, GRID_W, GRID_Z, lag)
    r = B.eval_exposure(f"{name} WALK-FORWARD", ret, rf, e)
    rows.append(r)
    ch = pd.Series({k: f"w{v[0]}z{v[1]}" for k, v in chosen.items()})
    print(f"   Walk-forward: la configurazione scelta cambia "
          f"{int((ch != ch.shift()).sum())} volte in {len(ch)} anni")
    return r


def main():
    ff = dataio.ff_factors_monthly()
    rf_all = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()

    # =============================================================== B3
    print(f"{'='*92}\nB3 — credito: lo spread high yield come segnale "
          f"sull'azionario\n{'='*92}")
    hy = monthly_last(M.fred("BAMLH0A0HYM2"))
    if len(hy) < 200:
        print(f"   NON TESTABILE sulla serie dichiarata: BAMLH0A0HYM2 scarica")
        print(f"   solo {len(hy)} mesi. Le serie ICE BofA su FRED sono limitate")
        print(f"   agli ultimi 3 anni per licenza, e non esiste un endpoint")
        print(f"   alternativo che dia la storia dal 1996.")
        print(f"   B3 resta SENZA ESITO. Al suo posto eseguo B7, pre-registrata")
        print(f"   in coda PRIMA di girare, sullo spread Baa-Aaa di Moody's che")
        print(f"   ha storia dal 1919 ed e' il default spread della letteratura.")
        baa = monthly_last(M.fred("BAA"))
        aaa = monthly_last(M.fred("AAA"))
        hy = (baa - aaa).dropna()
        b3_label = "B7 spread Baa-Aaa"
    else:
        b3_label = "B3 spread HY"
    idx = mkt.index.intersection(hy.index)
    ret = mkt.reindex(idx)
    rf = rf_all.reindex(idx).fillna(0.0)
    hy = hy.reindex(idx)
    print(f"   Spread HY {idx[0].date()} -> {idx[-1].date()} ({len(idx)} mesi)")
    print(f"   Segnale ritardato di 1 mese oltre la costruzione.")
    rows3 = [B.eval_stream("azionario buy&hold", ret, rf)]
    bh3 = rows3[0]
    wf3 = run_signal(b3_label, hy, ret, rf, rows3)
    print()
    B.table([r for r in rows3 if "in-sample" not in r["label"]])
    best_is = max((r for r in rows3 if "in-sample" in r["label"]),
                  key=lambda r: r["irr"])
    print(f"\n   Migliore IN-SAMPLE: {best_is['label']} -> "
          f"{best_is['irr']:.2f}% ({best_is['irr']-bh3['irr']:+.2f} contro B&H)")
    print(f"   Preso WALK-FORWARD: {wf3['irr']:.2f}% "
          f"({wf3['irr']-bh3['irr']:+.2f} contro B&H)")
    print(f"   Il divario fra i due e' il costo di non conoscere il futuro: "
          f"{best_is['irr']-wf3['irr']:.2f} punti")
    b3_fals = wf3["irr_ref"] > bh3["irr"]
    nm = b3_label.split()[0]
    print(f"   -> ipotesi {nm} {'FALSIFICATA' if b3_fals else 'CONFERMATA'}")

    # =============================================================== B4
    print(f"\n{'='*92}\nB4 — curva dei tassi: l'inversione come segnale di "
          f"regime\n{'='*92}")
    t10y2y = monthly_last(M.fred("T10Y2Y"))
    idx = mkt.index.intersection(t10y2y.index)
    ret = mkt.reindex(idx)
    rf = rf_all.reindex(idx).fillna(0.0)
    cur = t10y2y.reindex(idx)
    print(f"   T10Y2Y {idx[0].date()} -> {idx[-1].date()} ({len(idx)} mesi)")

    # quanto anticipa davvero l'inversione? misura diretta, prima della strategia
    inv = (cur < 0).astype(int)
    starts = cur.index[(inv.diff() == 1).fillna(False)]
    curve = (1 + ret).cumprod()
    dd = curve / curve.cummax() - 1
    leads = []
    for s in starts:
        fut = dd.loc[s:].head(36)
        if len(fut) and fut.min() < -0.15:
            leads.append(int(np.argmax(fut.to_numpy() < -0.15)))
    print(f"   Inversioni nel campione: {len(starts)}. Di queste, "
          f"{len(leads)} seguite da un calo oltre il 15% entro 36 mesi.")
    if leads:
        print(f"   Anticipo mediano dell'inversione sul calo: "
              f"{int(np.median(leads))} mesi (previsto 12-18)")

    rows4 = [B.eval_stream("azionario buy&hold", ret, rf)]
    bh4 = rows4[0]
    # esposizione ridotta (non azzerata) quando la curva e' invertita
    for cut in (0.0, 0.5):
        for lag in (1, 3):
            e = pd.Series(1.0, index=idx)
            e[(cur < 0).shift(lag).fillna(False)] = cut
            r = B.eval_exposure(f"curva invertita -> {cut:.0%} (lag {lag}m)",
                                ret, rf, e)
            rows4.append(r)
    print()
    B.table(rows4)
    b4_fals = any(r["irr_ref"] > bh4["irr"] for r in rows4[1:])
    print(f"\n   Qualche variante batte il buy&hold netto imposte? "
          f"{'SI' if b4_fals else 'NO'}")
    print(f"   -> ipotesi B4 {'FALSIFICATA' if b4_fals else 'CONFERMATA'}")

    allr = rows3 + rows4
    for r in allr:
        d = None
    best = max(rows3[1:] + rows4[1:], key=lambda r: r["irr"])
    d = lab.deflated_sharpe(best["gross"], N_PREREG, round_id=ROUND)
    print(f"\n   DSR del migliore complessivo ({best['label']}) su N={N_PREREG}: "
          f"{d['dsr']:.3f}")

    lab.log_trials([dict(round=ROUND,
                         hypothesis=(b3_label if r in rows3
                                     else "B4 curva dei tassi"),
                         config=r["label"], window="varie", sharpe=r["sharpe"],
                         irr=r["irr"], bh_irr=(bh3 if r in rows3 else bh4)["irr"],
                         excess=r["irr_ref"] - (bh3 if r in rows3 else bh4)["irr"],
                         n_obs=r["n"], note=f"turn={r['turn']:.2f}x")
                    for r in allr])
    pd.DataFrame([{k: v for k, v in r.items() if k != "gross"}
                  for r in allr]).to_csv(OUT / "round38_b3b4.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

"""Giro 42 — C5 (copertura del premio di volatilita') e C6 (multi-strategia CTA).

DUE VOCI DELLA CODA, predizioni verbatim.

C5 — Overlay di copertura sul premio di volatilita'
  Vendere put e comprare put piu' lontane (put spread) per tagliare la coda che
  uccide BXM e PUT. Approssimato dai dati CBOE disponibili.
  PREDIZIONE: la copertura costa piu' della coda che evita, perche' il premio
  delle put lontane e' proporzionalmente piu' caro (volatility smile).
  FALSIFICATA SE: IRR netta superiore a PUT non coperto.

C6 — Multi-strategia su stream davvero non correlati
  Trend azionario, carry valutario, momentum materie prime, premio di
  volatilita'. Sono i quattro pilastri dei CTA.
  PREDIZIONE: correlazione media sotto 0,2, Sharpe combinato sopra ogni singolo,
  e IRR netta comunque sotto il buy&hold per la rotazione aggregata.
  FALSIFICATA SE: IRR netta > buy&hold azionario.

COME APPROSSIMO IL PUT SPREAD, dichiarato prima dei numeri. Non ho catene di
opzioni, quindi non posso costruire uno spread verticale su misura. Uso gli
indici CBOE pubblicati, che sono strategie realmente replicabili:

  PUT    vende put ATM sull'S&P, garantite in contanti — il premio NON coperto
  CNDR   CBOE Iron Condor: vende uno strangle e COMPRA le ali. E' un premio di
         volatilita' a rischio definito, cioe' esattamente la struttura che C5
         descrive, costruita dal CBOE invece che da me
  CLL    collar 95-110: azionario lungo, put protettiva, call venduta
  PPUT   solo la gamba di copertura (put protettiva al 5% OTM), per misurare
         quanto costa l'assicurazione da sola

Non e' lo spread verticale della voce, ed e' un'approssimazione che dichiaro. Ma
va nella stessa direzione: confronta un premio di volatilita' nudo con lo stesso
premio con le ali comprate.
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
from research.round27 import cboe

ROUND = 42
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 57


def monthly_ret(s):
    m = s.resample("ME").last()
    m.index = m.index.to_period("M").to_timestamp("M")
    return m.pct_change().dropna()


def main():
    ff = dataio.ff_factors_monthly()
    rf_all = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()

    # =============================================================== C5
    print(f"{'='*92}\nC5 — premio di volatilita' nudo contro premio coperto\n"
          f"{'='*92}")
    series = {}
    for nm in ("PUT", "BXM", "CNDR", "CLL", "PPUT"):
        try:
            series[nm] = monthly_ret(cboe(nm, daily_only=True))
        except Exception as e:
            print(f"   {nm}: non disponibile ({type(e).__name__})")
    D = pd.DataFrame(series).dropna()
    print(f"   Finestra comune {D.index[0].date()} -> {D.index[-1].date()} "
          f"({len(D)} mesi)")
    print(f"   Approssimazione dichiarata: CNDR (ali comprate) al posto dello")
    print(f"   spread verticale su misura, che richiederebbe catene di opzioni.\n")
    rf = rf_all.reindex(D.index).fillna(0.0)
    rows5 = []
    names = {"PUT": "PUT — premio NUDO", "CNDR": "CNDR — premio COPERTO",
             "BXM": "BXM — buy-write", "CLL": "CLL — collar 95/110",
             "PPUT": "PPUT — sola copertura"}
    for k in D.columns:
        rows5.append(B.eval_stream(names.get(k, k), D[k], rf))
    rows5.append(B.eval_stream("azionario (benchmark)", mkt.reindex(D.index), rf))
    B.table(rows5, cols=("label", "cagr", "vol", "sharpe", "skew", "dd", "irr"))

    nudo = next(r for r in rows5 if r["label"].startswith("PUT"))
    cop = next((r for r in rows5 if r["label"].startswith("CNDR")), None)
    print(f"\n   Condizione: FALSIFICATA se il premio COPERTO ha IRR netta")
    print(f"   superiore al PUT non coperto.")
    if cop:
        print(f"     PUT nudo    IRR {nudo['irr']:.2f}%  skew {nudo['skew']:+.2f}  "
              f"DD {nudo['dd']:.1f}%")
        print(f"     CNDR coperto IRR {cop['irr']:.2f}%  skew {cop['skew']:+.2f}  "
              f"DD {cop['dd']:.1f}%")
        c5_fals = cop["irr"] > nudo["irr"]
        print(f"     differenza {cop['irr']-nudo['irr']:+.2f} punti")
        print(f"   -> ipotesi C5 {'FALSIFICATA' if c5_fals else 'CONFERMATA'}")
        print(f"\n   La copertura ha tagliato la coda? skew da {nudo['skew']:+.2f} "
              f"a {cop['skew']:+.2f}, drawdown da {nudo['dd']:.1f}% a "
              f"{cop['dd']:.1f}%")
        pput = next((r for r in rows5 if r["label"].startswith("PPUT")), None)
        if pput:
            print(f"   Costo della sola assicurazione (PPUT contro azionario): "
                  f"{pput['cagr'] - rows5[-1]['cagr']:+.2f} punti di CAGR l'anno")
    else:
        c5_fals = False

    # =============================================================== C6
    print(f"\n{'='*92}\nC6 — i quattro pilastri dei CTA insieme\n{'='*92}")
    pil = {}
    # 1. trend azionario
    px = (1 + mkt).cumprod()
    e = B.ma_filter(px, 10)
    rf0 = rf_all.reindex(mkt.index).fillna(0.0)
    pil["trend azionario"] = (e * mkt + (1 - e) * rf0 * (1 - C.DIRT_RATE),
                              e.diff().abs().fillna(0.0))
    # 2. momentum materie prime (WTI)
    wti = M.fred("DCOILWTICO").resample("ME").last()
    wti.index = wti.index.to_period("M").to_timestamp("M")
    wr = wti.pct_change().dropna()
    ew = B.ma_filter(wti.reindex(wr.index), 12)
    pil["momentum materie prime"] = (ew * wr, ew.diff().abs().fillna(0.0))
    # 3. carry valutario EUR/JPY
    def ml(x):
        m = M.fred(x).resample("ME").last()
        m.index = m.index.to_period("M").to_timestamp("M")
        return m
    fxs = pd.DataFrame({"EUR": ml("DEXUSEU"), "JPY": 1.0 / ml("DEXJPUS")}).dropna()
    us = ml("TB3MS") / 100.0
    car = pd.DataFrame({"EUR": (ml("IR3TIB01EZM156N") / 100.0 - us),
                        "JPY": (ml("IR3TIB01JPM156N") / 100.0 - us)}) / 12.0
    tot = fxs.pct_change() + car.reindex(fxs.index).ffill()
    tot = tot.dropna()
    sg = car.reindex(tot.index).ffill().shift(1)
    w = pd.DataFrame(0.0, index=tot.index, columns=tot.columns)
    w[sg.rank(axis=1, ascending=False) == 1] = 1.0
    w[sg.rank(axis=1, ascending=False) == 2] = -1.0
    nc, tc = B.wbacktest(tot, w.shift(1).fillna(0.0))
    pil["carry valutario"] = (nc.dropna(), tc)
    # 4. premio di volatilita'
    pil["premio volatilita'"] = (D["PUT"], pd.Series(0.0, index=D.index))

    R = pd.DataFrame({k: v[0] for k, v in pil.items()}).dropna()
    RZ = pd.DataFrame({k: v[1] for k, v in pil.items()}).reindex(R.index).fillna(0.0)
    print(f"   Finestra comune {R.index[0].date()} -> {R.index[-1].date()} "
          f"({len(R)} mesi)")
    corr = R.corr()
    print(f"\n   Correlazioni:")
    print(corr.round(2).to_string())
    off = corr.to_numpy()[np.triu_indices(len(corr), 1)]
    print(f"\n   Correlazione media a coppie: {off.mean():.3f} "
          f"({'SOTTO' if off.mean() < 0.2 else 'sopra'} 0,2 come previsto)")

    rf1 = rf_all.reindex(R.index).fillna(0.0)
    rows6 = [B.eval_stream(f"solo {k}", R[k], rf1, RZ[k]) for k in R.columns]
    W = pd.DataFrame(0.25, index=R.index, columns=R.columns)
    net, turn = B.wbacktest(R, W)
    rz = (turn + (W * RZ).sum(axis=1)).clip(0, 1)
    rows6.append(B.eval_stream("4 pilastri equal-weight", net.dropna(), rf1,
                               rz.reindex(net.dropna().index)))
    Wi = pd.DataFrame(0.0, index=R.index, columns=R.columns)
    wv = np.ones(R.shape[1]) / R.shape[1]
    for i in range(len(R)):
        if i >= 36 and i % 12 == 0:
            v = R.iloc[i - 36:i].std().to_numpy()
            wv = (1 / np.maximum(v, 1e-9)) / (1 / np.maximum(v, 1e-9)).sum()
        Wi.iloc[i] = wv
    net2, turn2 = B.wbacktest(R, Wi.shift(1).fillna(0.25))
    rz2 = (turn2 + (Wi.shift(1).fillna(0.25) * RZ).sum(axis=1)).clip(0, 1)
    rows6.append(B.eval_stream("4 pilastri inverse-vol", net2.dropna(), rf1,
                               rz2.reindex(net2.dropna().index)))
    bh6 = B.eval_stream("azionario buy&hold (bench)", mkt.reindex(R.index), rf1)
    rows6.append(bh6)
    print()
    B.table(rows6)

    combos = [r for r in rows6 if r["label"].startswith("4 pilastri")]
    singles = [r for r in rows6 if r["label"].startswith("solo")]
    best_single = max(s["sharpe"] for s in singles)
    print(f"\n   Sharpe del combinato sopra ogni singolo? "
          f"{'SI' if max(c['sharpe'] for c in combos) > best_single else 'NO'}"
          f"  (combinato {max(c['sharpe'] for c in combos):.2f} contro il miglior "
          f"singolo {best_single:.2f})")
    c6_fals = any(c["irr_ref"] > bh6["irr"] for c in combos)
    print(f"   Qualche combinazione batte il buy&hold netto imposte? "
          f"{'SI' if c6_fals else 'NO'}")
    print(f"   -> ipotesi C6 {'FALSIFICATA' if c6_fals else 'CONFERMATA'}")

    allr = rows5 + rows6
    best = max(combos, key=lambda r: r["irr_ref"])
    d = lab.deflated_sharpe(best["gross"], N_PREREG, round_id=ROUND)
    print(f"   DSR del miglior combinato su N={N_PREREG}: {d['dsr']:.3f}")

    lab.log_trials([dict(round=ROUND,
                         hypothesis=("C5 premio volatilita' coperto" if r in rows5
                                     else "C6 multi-strategia 4 pilastri"),
                         config=r["label"], window="varie", sharpe=r["sharpe"],
                         irr=r["irr"], bh_irr=bh6["irr"],
                         excess=r["irr_ref"] - bh6["irr"], n_obs=r["n"],
                         note=f"skew={r['skew']:.2f},turn={r['turn']:.2f}x")
                    for r in allr])
    pd.DataFrame([{k: v for k, v in r.items() if k != "gross"}
                  for r in allr]).to_csv(OUT / "round42_c5c6.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

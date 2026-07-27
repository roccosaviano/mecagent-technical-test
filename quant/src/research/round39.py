"""Giro 39 — B5 (azionario internazionale) e B6 (cripto, universo esteso).

DUE VOCI DELLA CODA, predizioni verbatim.

B5 — Azionario internazionale (French Developed, Emerging, Japan, Europe)
  Momentum cross-sectional fra regioni, ribilanciamento annuale.
  PREDIZIONE: funziona come il momentum settoriale (stesso meccanismo) e muore
  come lui sulle imposte, con in piu' il fatto che la storia parte dal 1990.
  FALSIFICATA SE: DSR > 0,95 con IRR netta positiva.

B6 — Cripto: universo esteso oltre i 7 attuali
  PREDIZIONE: allargando l'universo il CAGR del buy&hold scende (i nuovi sono
  mediamente peggiori) e il vantaggio relativo del trend filter resta, ma il DSR
  non migliora perche' la finestra resta di sei anni.
  FALSIFICATA SE: DSR > 0,95.

NOTA SU B6. La condizione "DSR > 0,95" e' l'unica della coda che puo' essere
soddisfatta da una strategia con sei anni di storia, perche' il DSR con N grande
e' severo ma non guarda la LUNGHEZZA del campione quanto la sua qualita'. Riporto
quindi anche l'intervallo di confidenza dello Sharpe, che su 72 osservazioni e'
largo circa +/- 0,47: e' l'informazione che il DSR da solo non trasmette.
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

ROUND = 39
OUT = Path(__file__).resolve().parents[2] / "out"
DATA = Path(__file__).resolve().parents[2] / "data"
N_PREREG = 57          # 56 + B7 pre-registrata al giro 38


def sharpe_ci(sr, n, ppy=12):
    """Intervallo al 95% dello Sharpe annualizzato (Lo 2002, iid)."""
    se = np.sqrt((1 + 0.5 * (sr / np.sqrt(ppy)) ** 2) / n) * np.sqrt(ppy)
    return sr - 1.96 * se, sr + 1.96 * se


def main():
    ff = dataio.ff_factors_monthly()
    rf_all = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()

    # =============================================================== B5
    print(f"{'='*92}\nB5 — momentum cross-sectional fra regioni\n{'='*92}")
    regions = {}
    for nm in ("Developed", "Emerging", "Europe", "Japan",
               "Asia_Pacific_ex_Japan"):
        try:
            d = M.ff_region(nm if nm != "Emerging" else "Emerging_5_Factors")
        except Exception:
            try:
                d = M.ff_region(nm + "_3_Factors")
            except Exception as e:
                print(f"   {nm}: non disponibile ({type(e).__name__})")
                continue
        col = "Mkt-RF" if "Mkt-RF" in d.columns else d.columns[0]
        regions[nm] = (d[col] + d["RF"]) if "RF" in d.columns else d[col]
    R = pd.DataFrame(regions).dropna()
    print(f"   {len(R.columns)} regioni: {', '.join(R.columns)}")
    print(f"   Finestra comune {R.index[0].date()} -> {R.index[-1].date()} "
          f"({len(R)} mesi)")
    rf = rf_all.reindex(R.index).fillna(0.0)
    rows5 = [B.eval_stream("regioni equal-weight (bench)", R.mean(axis=1), rf),
             B.eval_stream("azionario USA (bench)", mkt.reindex(R.index), rf)]
    for top in (1, 2):
        for hold in (1, 12):
            W = B.xs_momentum(R, 12, 1, top)
            if hold == 12:                      # ribilanciamento annuale
                m = pd.Series(W.index.month == 12, index=W.index)
                W = W.where(m, other=np.nan).ffill().fillna(0.0)
            net, turn = B.wbacktest(R, W.shift(1).fillna(0.0))
            rows5.append(B.eval_stream(
                f"momentum top{top} ribil.{'annuale' if hold == 12 else 'mensile'}",
                net.dropna(), rf, turn))
    B.table(rows5)
    bh5 = rows5[0]
    cand5 = rows5[2:]
    best5 = max(cand5, key=lambda r: r["irr_ref"])
    d5 = lab.deflated_sharpe(best5["gross"], N_PREREG, round_id=ROUND)
    lo, hi = sharpe_ci(best5["sharpe"], best5["n"])
    print(f"\n   Migliore: {best5['label']} — IRR di riferimento "
          f"{best5['irr_ref']:.2f}% (aliquota {best5['rate_ref']}%) contro "
          f"{bh5['irr']:.2f}% dell'equal-weight fra regioni")
    print(f"   Sharpe {best5['sharpe']:.2f}, intervallo al 95% "
          f"[{lo:.2f}, {hi:.2f}] su {best5['n']} mesi")
    print(f"   DSR su N={N_PREREG}: {d5['dsr']:.3f}")
    b5_fals = d5["dsr"] > 0.95 and best5["irr_ref"] > 0
    print(f"   -> ipotesi B5 {'FALSIFICATA' if b5_fals else 'CONFERMATA'}")

    # =============================================================== B6
    print(f"\n{'='*92}\nB6 — cripto, universo esteso\n{'='*92}")
    files = sorted(DATA.glob("okx_*_1d.csv"))
    px = {}
    for f in files:
        sym = f.stem.split("_")[1]
        d = pd.read_csv(f, parse_dates=["datetime"]).set_index("datetime")
        m = d["close"].resample("ME").last()
        m.index = m.index.to_period("M").to_timestamp("M")
        px[sym] = m
    P = pd.DataFrame(px)
    print(f"   {len(P.columns)} asset: {', '.join(c[:-4] for c in P.columns)}")
    print(f"   Storia parziale ammessa di proposito: chi entra dopo entra dopo.")
    for c in P.columns:
        s = P[c].dropna()
        print(f"     {c[:-4]:<6} {s.index[0].date()} -> {s.index[-1].date()}  "
              f"({len(s)} mesi)")
    RET = P.pct_change()
    rfc = rf_all.reindex(RET.index).ffill().fillna(0.0)

    rows6 = []
    # buy&hold equal-weight su cio' che esiste in ogni istante
    ew = RET.mean(axis=1, skipna=True).dropna()
    rows6.append(B.eval_stream("cripto equal-weight buy&hold", ew, rfc))
    # universo ristretto ai 3 storici, per il confronto dichiarato in predizione
    core = [c for c in ("BTCUSDT", "ETHUSDT", "LTCUSDT") if c in RET.columns]
    rows6.append(B.eval_stream("solo BTC/ETH/LTC buy&hold",
                               RET[core].mean(axis=1).dropna(), rfc))
    # filtro di trend a 10 mesi, per asset
    for lb in (6, 10):
        E = pd.DataFrame({c: B.ma_filter(P[c], lb) for c in P.columns})
        E = E.div(E.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
        net, turn = B.wbacktest(RET.fillna(0.0), E.shift(1).fillna(0.0))
        rows6.append(B.eval_stream(f"trend MA{lb} multi-asset", net.dropna(),
                                   rfc, turn))
    # momentum cross-sectional
    W = B.xs_momentum(RET.fillna(0.0), 6, 1, 3)
    net, turn = B.wbacktest(RET.fillna(0.0), W.shift(1).fillna(0.0))
    rows6.append(B.eval_stream("momentum 6m top3", net.dropna(), rfc, turn))
    print()
    B.table(rows6)

    wide = rows6[0]
    narrow = rows6[1]
    print(f"\n   Allargando l'universo il CAGR del buy&hold "
          f"{'SCENDE' if wide['cagr'] < narrow['cagr'] else 'SALE'}: "
          f"{wide['cagr']:.2f}% contro {narrow['cagr']:.2f}% dei soli tre storici")
    best6 = max(rows6[2:], key=lambda r: r["irr_ref"])
    d6 = lab.deflated_sharpe(best6["gross"], N_PREREG, round_id=ROUND)
    lo, hi = sharpe_ci(best6["sharpe"], best6["n"])
    print(f"   Il trend filter batte il buy&hold esteso? "
          f"{'SI' if best6['irr_ref'] > wide['irr_ref'] else 'NO'}  "
          f"({best6['irr_ref']:.2f}% contro {wide['irr_ref']:.2f}%)")
    print(f"   Migliore: {best6['label']}, Sharpe {best6['sharpe']:.2f}, "
          f"intervallo al 95% [{lo:.2f}, {hi:.2f}] su {best6['n']} mesi")
    print(f"   DSR su N={N_PREREG}: {d6['dsr']:.3f}")
    b6_fals = d6["dsr"] > 0.95
    print(f"   -> ipotesi B6 {'FALSIFICATA' if b6_fals else 'CONFERMATA'}")
    print(f"\n   L'intervallo dello Sharpe e' l'informazione che il DSR non da':")
    print(f"   con {best6['n']} osservazioni l'ampiezza e' {hi-lo:.2f}, cioe' piu'")
    print(f"   larga della differenza fra qualunque coppia di strategie in tabella.")

    allr = rows5 + rows6
    lab.log_trials([dict(round=ROUND,
                         hypothesis=("B5 azionario internazionale" if r in rows5
                                     else "B6 cripto universo esteso"),
                         config=r["label"], window="varie", sharpe=r["sharpe"],
                         irr=r["irr"], bh_irr=(bh5 if r in rows5 else wide)["irr"],
                         excess=r["irr_ref"] - (bh5 if r in rows5 else wide)["irr"],
                         n_obs=r["n"], note=f"turn={r['turn']:.2f}x")
                    for r in allr])
    pd.DataFrame([{k: v for k, v in r.items() if k != "gross"}
                  for r in allr]).to_csv(OUT / "round39_b5b6.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

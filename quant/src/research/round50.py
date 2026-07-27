"""Giro 50 — F1 (rotazione top-1) e F2 (griglia posizioni x frequenza).

DUE VOCI DELLA CODA, verbatim.

F1 — Rotazione top-1 sul migliore del periodo precedente
  49 settori USA, 5 regioni, 8 cripto. Annuale, trimestrale, mensile.
  PREDIZIONE: il top-1 e' peggiore del top-10 gia' testato e peggiore
  dell'equal-weight del proprio universo; la versione annuale e' la meno peggio
  perche' e' la meno tassata.
  FALSIFICATA SE: una qualunque configurazione top-1 batte l'equal-weight del
  proprio universo netto di imposte.

F2 — La curva del numero di posizioni e della frequenza
  1, 3, 5, 10, 25 posizioni x mensile, trimestrale, annuale, sui 49 settori.
  PREDIZIONE: IRR netta monotona crescente nel numero di posizioni e decrescente
  nella frequenza; la cella migliore e' la piu' diversificata e meno frequente, e
  non batte l'equal-weight statico.
  FALSIFICATA SE: il massimo della griglia sta a meno di 5 posizioni, oppure
  batte l'equal-weight statico.

LA REGOLA, identica per tutti gli universi: alla fine di ogni periodo si
ordinano gli asset per rendimento del periodo APPENA CHIUSO e si tengono i primi
N per il periodo successivo. Nessun parametro scelto guardando il risultato: il
lookback e' il periodo di ribilanciamento stesso, come dice la domanda.
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

ROUND = 50
OUT = Path(__file__).resolve().parents[2] / "out"
DATA = Path(__file__).resolve().parents[2] / "data"
N_PREREG = 71          # famiglia pre-dichiarata dopo il gruppo F
FREQS = {"mensile": 1, "trimestrale": 3, "annuale": 12}


def rotate(rets, top, step):
    """Pesi detenuti: ogni `step` mesi si tengono i `top` migliori del periodo
    appena chiuso. Il segnale usa solo il passato."""
    idx = rets.index
    W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    cur = pd.Series(1.0 / rets.shape[1], index=rets.columns)
    for i in range(len(idx)):
        if i >= step and i % step == 0:
            perf = (1 + rets.iloc[i - step:i]).prod()
            best = perf.nlargest(top).index
            cur = pd.Series(0.0, index=rets.columns)
            cur[best] = 1.0 / len(best)
        W.iloc[i] = cur
    return W


def universes():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    out = {}
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    out["49 settori USA"] = ind
    regs = {}
    for nm in ("Developed", "Emerging_5_Factors", "Europe_3_Factors",
               "Japan_3_Factors", "Asia_Pacific_ex_Japan_3_Factors"):
        try:
            dfr = M.ff_region(nm)
            col = "Mkt-RF" if "Mkt-RF" in dfr.columns else dfr.columns[0]
            regs[nm.split("_")[0]] = dfr[col] + dfr.get("RF", 0.0)
        except Exception:
            pass
    if len(regs) >= 3:
        out["regioni"] = pd.DataFrame(regs).dropna()
    px = {}
    for f in sorted(DATA.glob("okx_*_1d.csv")):
        s = pd.read_csv(f, parse_dates=["datetime"]).set_index("datetime")["close"]
        m = s.resample("ME").last()
        m.index = m.index.to_period("M").to_timestamp("M")
        px[f.stem.split("_")[1][:-4]] = m
    cr = pd.DataFrame(px).pct_change()
    out["8 cripto"] = cr[cr.notna().sum(axis=1) >= 4].fillna(0.0)
    return out, rf


def main():
    unis, rf = universes()
    print("F1 — rotazione sul migliore del periodo precedente\n")

    rows1, verdict1 = [], []
    for uname, R in unis.items():
        rf0 = rf.reindex(R.index).ffill().fillna(0.0)
        ew = B.eval_stream(f"{uname}: equal-weight", R.mean(axis=1), rf0)
        rows1.append(ew)
        print(f"{'='*96}\n{uname}   {R.index[0].date()} -> {R.index[-1].date()}"
              f"   {R.shape[1]} asset, {len(R)} mesi\n{'='*96}")
        sub = [ew]
        for fname, step in FREQS.items():
            W = rotate(R, 1, step)
            net, turn = B.wbacktest(R, W.shift(1).fillna(0.0))
            sub.append(B.eval_stream(f"{uname}: top-1 {fname}", net.dropna(),
                                     rf0, turn))
        B.table(sub, cols=("label", "cagr", "vol", "sharpe", "dd", "turn",
                           "irr", "irr52"))
        rows1 += sub[1:]
        for r in sub[1:]:
            beats = r["irr_ref"] > ew["irr"]
            verdict1.append(beats)
            print(f"   {r['label']:<34} IRR di rif. {r['irr_ref']:>6.2f}% "
                  f"(aliquota {r['rate_ref']}%) contro {ew['irr']:.2f}% "
                  f"-> {r['irr_ref']-ew['irr']:+.2f}")
        best_f = max(sub[1:], key=lambda r: r["irr_ref"])
        print(f"   Migliore frequenza: {best_f['label'].split(': ')[1]}")
        print()

    print(f"{'='*96}\nVERDETTO SU F1\n{'='*96}")
    print("   Predizione: il top-1 e' peggiore dell'equal-weight del proprio")
    print("   universo; l'annuale e' la meno peggio.")
    print("   FALSIFICATA se una qualunque configurazione top-1 batte l'equal-weight.\n")
    f1_fals = any(verdict1)
    print(f"   Configurazioni top-1 che battono il proprio equal-weight: "
          f"{sum(verdict1)}/{len(verdict1)}")
    print(f"   -> ipotesi F1 {'FALSIFICATA' if f1_fals else 'CONFERMATA'}")

    # ================================================================ F2
    print(f"\n{'='*96}\nF2 — LA GRIGLIA: NUMERO DI POSIZIONI x FREQUENZA\n{'='*96}")
    R = unis["49 settori USA"]
    rf0 = rf.reindex(R.index).ffill().fillna(0.0)
    ew = B.eval_stream("equal-weight statico", R.mean(axis=1), rf0)
    print(f"   49 settori, {R.index[0].date()} -> {R.index[-1].date()}")
    print(f"   Riferimento: equal-weight statico, IRR netta {ew['irr']:.2f}%\n")
    grid, rows2 = [], []
    print(f"   IRR NETTA DI RIFERIMENTO (33% o 52% secondo la rotazione)")
    print(f"   {'posizioni':<12}" + "".join(f"{f:>14}" for f in FREQS))
    print("   " + "-" * 54)
    for top in (1, 3, 5, 10, 25):
        line = f"   {top:<12}"
        for fname, step in FREQS.items():
            W = rotate(R, top, step)
            net, turn = B.wbacktest(R, W.shift(1).fillna(0.0))
            r = B.eval_stream(f"top-{top} {fname}", net.dropna(), rf0, turn)
            grid.append(dict(top=top, freq=fname, irr=r["irr_ref"],
                             rate=r["rate_ref"], turn=r["turn"],
                             sharpe=r["sharpe"], cagr=r["cagr"], dd=r["dd"]))
            rows2.append(r)
            line += f"{r['irr_ref']:>12.2f}%*" if r["rate_ref"] == 52 else \
                    f"{r['irr_ref']:>13.2f}%"
        print(line)
    print(f"   (* = oltre 100% di rotazione l'anno, valutata al 52%)")

    g = pd.DataFrame(grid)
    best = g.loc[g["irr"].idxmax()]
    print(f"\n   Massimo della griglia: top-{int(best['top'])} {best['freq']} "
          f"-> {best['irr']:.2f}%  contro {ew['irr']:.2f}% dell'equal-weight statico")
    mono_pos = all(g[g.freq == f].sort_values("top")["irr"].is_monotonic_increasing
                   for f in FREQS)
    mono_freq = all(g[g.top == t].set_index("freq").loc[list(FREQS)]["irr"]
                    .is_monotonic_increasing for t in (1, 3, 5, 10, 25))
    print(f"   Monotona crescente nel numero di posizioni? "
          f"{'SI' if mono_pos else 'NO'}")
    print(f"   Monotona crescente allungando il ribilanciamento? "
          f"{'SI' if mono_freq else 'NO'}")
    f2_fals = best["top"] < 5 or best["irr"] > ew["irr"]
    print(f"\n   FALSIFICATA se il massimo sta sotto 5 posizioni o batte")
    print(f"   l'equal-weight statico.")
    print(f"   -> ipotesi F2 {'FALSIFICATA' if f2_fals else 'CONFERMATA'}")

    print(f"\n   Il costo della concentrazione, a parita' di frequenza annuale:")
    ann = g[g.freq == "annuale"].sort_values("top")
    for _, r in ann.iterrows():
        print(f"     top-{int(r['top']):<3} CAGR {r['cagr']:>6.2f}%  "
              f"Sharpe {r['sharpe']:>5.2f}  DD {r['dd']:>7.1f}%  "
              f"rotazione {r['turn']:>4.2f}x  IRR {r['irr']:>6.2f}%")

    allr = rows1 + rows2
    bestall = max(rows2, key=lambda r: r["irr_ref"])
    dd = lab.deflated_sharpe(bestall["gross"], N_PREREG, round_id=ROUND)
    print(f"\n   DSR del migliore su N={N_PREREG}: {dd['dsr']:.3f} -> "
          + ("PROMUOVIBILE" if dd["dsr"] > 0.95 and bestall["irr_ref"] > ew["irr"]
             else "NON promuovibile"))

    lab.log_trials([dict(round=ROUND,
                         hypothesis="F1 rotazione top-1" if r in rows1
                                    else "F2 griglia posizioni x frequenza",
                         config=r["label"], window="varie", sharpe=r["sharpe"],
                         irr=r["irr"], bh_irr=ew["irr"],
                         excess=r["irr_ref"] - ew["irr"], n_obs=r["n"],
                         note=f"turn={r['turn']:.2f}x,rate={r['rate_ref']}")
                    for r in allr])
    g.to_csv(OUT / "round50_griglia.csv", index=False)
    pd.DataFrame([{k: v for k, v in r.items() if k != "gross"}
                  for r in allr]).to_csv(OUT / "round50_rotazione.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

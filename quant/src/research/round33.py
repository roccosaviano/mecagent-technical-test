"""Giro 33 — A4: Kelly frazionario e de-risking sul drawdown.

VOCE DELLA CODA, predizione e falsificazione scritte prima:

  Esposizione = f x Kelly stimato sul passato, con f in {0,25 · 0,5}; variante
  che taglia l'esposizione quando il drawdown corrente supera una soglia.
  PREDIZIONE: il de-risking sul drawdown peggiora l'IRR (vende sui minimi) pur
  migliorando il DD massimo.
  FALSIFICATA SE: l'IRR netta migliora rispetto all'esposizione costante.

LE REGOLE, fissate prima di guardare i risultati.

  Kelly       f* = media(eccesso) / varianza(eccesso) sui 60 mesi PRECEDENTI.
              Esposizione grezza = f x f*, poi TAGLIATA A 1: senza leva.
              Il taglio e' una scelta dichiarata, non un dettaglio: Kelly su
              azionario da' f* intorno a 2,5-3, quindi mezzo Kelly chiederebbe
              leva 1,3x. La leva costa benchmark+3% ed e' gia' stata bocciata
              al giro 07; qui misuro il sizing, non il finanziamento. Riporto
              comunque quanto spesso il vincolo morde.
  Warmup      primi 60 mesi senza stima: esposizione 1,0.
  De-risking  finche' il drawdown corrente (calcolato sulla curva della
              STRATEGIA, con i soli dati fino a ieri) supera la soglia,
              l'esposizione viene dimezzata. Soglie {10% · 20% · 30%}.
  Liquidita'  la parte non investita rende il risk-free al netto della DIRT
              33%: e' gia' nel motore fiscale, e senza di essa una strategia
              che sta fuori dal mercato verrebbe penalizzata per un'ipotesi.
  Realizzo    ogni riduzione di esposizione e' una vendita, quindi realizza
              plusvalenza in proporzione. Passata come realize_frac.

GRIGLIA: 2 valori di f x 4 varianti di de-risking (nessuna + 3 soglie) = 8
configurazioni. C'e' selezione, quindi N per il DSR sarebbe 8; uso pero' 54,
la famiglia pre-dichiarata della coda, che e' piu' severa.

DUE SOTTOSTANTI, come richiede il protocollo di robustezza: indice
cap-weighted (1926-2026) e equal-weight dei 49 settori (1969-2026).
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
from tax import simulate_pac, CGT_SHARES, TRADING_52
from research import lab
from research.round25 import _stats

ROUND = 33
OUT = Path(__file__).resolve().parents[2] / "out"
N_GRID = 8
N_PREREG = 54          # 53 + A8 aggiunta al giro 32
LOOKBACK = 60


def kelly_exposure(ret, rf, f, dd_thr=None, lookback=LOOKBACK, cap=1.0):
    """Esposizione periodo per periodo, usando SOLO il passato.

    Restituisce (esposizione, quota di periodi in cui il cap ha morso).
    """
    r = ret.to_numpy(dtype=float)
    rfv = rf.reindex(ret.index).fillna(0.0).to_numpy(dtype=float)
    ex = r - rfv
    n = len(r)
    e = np.ones(n)
    capped = 0
    curve, peak = 1.0, 1.0
    dd = 0.0
    for i in range(n):
        if i >= lookback:
            w = ex[i - lookback:i]
            v = w.var(ddof=1)
            kel = w.mean() / v if v > 0 else 0.0
            raw = f * kel
            if raw > cap:
                capped += 1
            e[i] = min(max(raw, 0.0), cap)
        # de-risking sul drawdown corrente, noto solo fino a i-1
        if dd_thr is not None and dd < -dd_thr:
            e[i] *= 0.5
        # aggiorno la curva della strategia col rendimento del periodo i
        step = e[i] * r[i] + (1.0 - e[i]) * rfv[i] * (1 - C.DIRT_RATE)
        curve *= (1.0 + step)
        peak = max(peak, curve)
        dd = curve / peak - 1.0
    return pd.Series(e, index=ret.index), capped / max(n - lookback, 1)


def run(name, ret, rf, rows):
    print(f"\n{'='*92}\n{name}   {ret.index[0].date()} -> {ret.index[-1].date()} "
          f"({len(ret)} mesi)\n{'='*92}")
    rf0 = rf.reindex(ret.index).fillna(0.0)

    bh = simulate_pac(ret, CGT_SHARES, rf=rf0, periods_per_year=12)
    bs = _stats(ret, 12)
    hdr = (f"   {'configurazione':<26}{'espos.med':>10}{'CAGR':>9}{'Sharpe':>8}"
           f"{'DD':>9}{'turn/an':>9}{'IRR 33%':>10}{'vs B&H':>9}")
    print(hdr)
    print("   " + "-" * (len(hdr) - 3))

    for f in (0.25, 0.5):
        for thr in (None, 0.10, 0.20, 0.30):
            e, capfrac = kelly_exposure(ret, rf0, f, thr)
            turn = e.diff().abs().fillna(0.0)
            rz = (-e.diff()).clip(lower=0.0).fillna(0.0)
            gross = e * ret + (1 - e) * rf0 * (1 - C.DIRT_RATE)
            s = _stats(gross, 12)
            tpy = float(turn.sum()) / (len(ret) / 12)
            r33 = simulate_pac(ret, CGT_SHARES, in_market=e, rf=rf0,
                               turnover=turn, realize_frac=rz,
                               periods_per_year=12)
            r52 = simulate_pac(ret, TRADING_52, in_market=e, rf=rf0,
                               turnover=turn, realize_frac=rz,
                               periods_per_year=12)
            lbl = f"{f:g} Kelly" + (f" + DD>{thr:.0%}" if thr else " (costante)")
            rows.append(dict(underlying=name[:24], f=f,
                             thr=(thr if thr else 0.0), **s, espo=float(e.mean()),
                             capfrac=capfrac, turn=tpy, irr=r33.irr_annual,
                             irr52=r52.irr_annual, bh=bh.irr_annual,
                             vs=r33.irr_annual - bh.irr_annual, gross=gross))
            print(f"   {lbl:<26}{e.mean():>10.2f}{s['cagr']:>8.2f}%"
                  f"{s['sharpe']:>8.2f}{s['dd']:>8.1f}%{tpy:>8.2f}x"
                  f"{r33.irr_annual:>9.2f}%{r33.irr_annual-bh.irr_annual:>+8.2f}")
    print(f"   {'buy & hold (espos. 1,0)':<26}{1.0:>10.2f}{bs['cagr']:>8.2f}%"
          f"{bs['sharpe']:>8.2f}{bs['dd']:>8.1f}%{0.0:>8.2f}x"
          f"{bh.irr_annual:>9.2f}%{0.0:>+8.2f}")
    return bh.irr_annual


def main():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).rename("mkt").dropna()
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ew = ind.mean(axis=1).rename("ew49")

    print("A4 — Kelly frazionario e de-risking sul drawdown")
    print(f"Stima di Kelly su {LOOKBACK} mesi mobili PRECEDENTI, esposizione "
          f"tagliata a 1,0 (niente leva).")
    print("De-risking: esposizione dimezzata finche' il drawdown corrente "
          "supera la soglia.")
    print(f"Liquidita' non investita al risk-free netto DIRT "
          f"{C.DIRT_RATE:.0%}. Costi {C.COST_ROUND_TRIP*100:.2f}% round-trip.")

    rows = []
    bh_mkt = run("indice cap-weighted", mkt, rf, rows)
    bh_ew = run("equal-weight 49 settori", ew, rf, rows)

    # -------------------------------------------------- verdetto
    print(f"\n{'='*92}\nVERDETTO SU A4\n{'='*92}")
    print("   Predizione: il de-risking sul drawdown PEGGIORA l'IRR (vende sui")
    print("   minimi) pur migliorando il DD massimo.")
    print("   FALSIFICATA se l'IRR netta migliora rispetto all'esposizione costante.\n")

    ok_dd, ok_irr = [], []
    for u in ("indice cap-weighted", "equal-weight 49 settori"):
        for f in (0.25, 0.5):
            base = next(r for r in rows if r["underlying"] == u[:24]
                        and r["f"] == f and r["thr"] == 0.0)
            for thr in (0.10, 0.20, 0.30):
                v = next(r for r in rows if r["underlying"] == u[:24]
                         and r["f"] == f and r["thr"] == thr)
                d_irr = v["irr"] - base["irr"]
                d_dd = v["dd"] - base["dd"]         # positivo = DD meno profondo
                ok_dd.append(d_dd > 0)
                ok_irr.append(d_irr > 0)
                print(f"   {u[:22]:<24}{f:g}K DD>{thr:.0%}   "
                      f"IRR {d_irr:+.2f} · DD {d_dd:+.1f} punti")

    print(f"\n   Il de-risking migliora il DD in {sum(ok_dd)}/{len(ok_dd)} casi")
    print(f"   Il de-risking migliora l'IRR in {sum(ok_irr)}/{len(ok_irr)} casi")
    falsified = sum(ok_irr) > len(ok_irr) / 2
    print(f"   -> ipotesi A4 {'FALSIFICATA' if falsified else 'CONFERMATA'}")

    # la parte Kelly, separata dal de-risking
    print(f"\n   La componente KELLY, separata dal de-risking:")
    for u, bh in (("indice cap-weighted", bh_mkt),
                  ("equal-weight 49 settori", bh_ew)):
        for f in (0.25, 0.5):
            b = next(r for r in rows if r["underlying"] == u[:24]
                     and r["f"] == f and r["thr"] == 0.0)
            print(f"     {u[:22]:<24}{f:g} Kelly costante: esposizione media "
                  f"{b['espo']:.2f}, cap attivo il {b['capfrac']:.0%} del tempo,"
                  f" IRR {b['irr']:.2f}% contro B&H {bh:.2f}% ({b['vs']:+.2f})")

    best = max(rows, key=lambda r: r["vs"])
    d = lab.deflated_sharpe(best["gross"], N_PREREG, round_id=ROUND)
    print(f"\n   Migliore della griglia: {best['f']:g} Kelly "
          f"{'DD>%.0f%%' % (best['thr']*100) if best['thr'] else 'costante'} su "
          f"{best['underlying']}  ({best['vs']:+.2f} punti)")
    print(f"   DSR su N={N_PREREG} (famiglia pre-dichiarata; la sola griglia "
          f"sarebbe N={N_GRID}): {d['dsr']:.3f}")
    print(f"   -> {'PROMUOVIBILE' if d['dsr'] > 0.95 and best['vs'] > 0 else 'NON promuovibile'}")

    mx = max(r["turn"] for r in rows)
    print(f"\n   Turnover massimo della griglia: {mx:.2f} volte l'anno "
          f"({'sotto' if mx < 1 else 'SOPRA'} la soglia del 100%). Scenario 52% "
          f"comunque calcolato:")
    print(f"     migliore configurazione al 52%: {best['irr52']:.2f}%")

    lab.log_trials([dict(round=ROUND, hypothesis="A4 Kelly frazionario + de-risking",
                         config=f"{r['underlying'][:14]}|f={r['f']:g}|dd={r['thr']:.2f}",
                         window="varie", sharpe=r["sharpe"], irr=r["irr"],
                         bh_irr=r["bh"], excess=r["vs"], n_obs=len(r["gross"]),
                         note=f"espo={r['espo']:.2f},turn={r['turn']:.2f}x")
                    for r in rows])
    pd.DataFrame([{k: v for k, v in r.items() if k != "gross"}
                  for r in rows]).to_csv(OUT / "round33_kelly.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

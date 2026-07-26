"""Giro 23 — Sistema swing multi-strategia multi-asset su cripto, long e short.

Cosa c'e' di nuovo rispetto ai giri 19-20, che avevano gia' testato il VWAP
per singolo asset:

  CROSS-SECTIONAL. Invece di decidere asset per asset ("BTC sta sopra la sua
  media?"), si ordinano i 7 asset e si compra la testa della classifica e si
  vende la coda. E' l'approccio che rende un long/short sensato: la gamba
  corta non e' "il mercato scende" ma "questo asset e' peggio degli altri",
  che e' market-neutral e non richiede di prevedere la direzione del mercato.

  MULTI-STRATEGIA. Quattro famiglie con logiche diverse, poi la loro
  combinazione: trend temporale, momentum cross-sectional, breakout, e
  mean-reversion di breve. Se una funziona per caso, difficilmente funzionano
  tutte; se funziona la combinazione ma nessuna singola, e' rumore aggregato.

  WALK-FORWARD. I parametri si scelgono ogni anno su tutto cio' che precede.

IL PREGIUDIZIO DA CUI PARTO, dichiarato prima di guardare i risultati: al giro
19 lo short-only ha battuto il benchmark 1 volta su 21 e il long-short 10 su 21,
contro 19 su 21 del long-only. La gamba corta su cripto in un decennio rialzista
toglie valore. Mi aspetto che il long/short market-neutral faccia meglio dello
short direzionale ma peggio del long-only, e che nulla superi il DSR.

LIMITE PESANTE: la finestra comune ai 7 asset e' 2020-2026, sei anni, UN solo
ciclo. E il campione contiene solo le cripto vive nel 2026.
"""
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
from tax import simulate_pac, CGT_SHARES, TRADING_52
from research import lab
from research.round19 import load_crypto, SYMS, COST_CRYPTO

ROUND = 23
OUT = Path(__file__).resolve().parents[2] / "out"
PPY = 365


def panel():
    data = {}
    for s in SYMS:
        try:
            data[s] = load_crypto(s)
        except FileNotFoundError:
            pass
    px = pd.DataFrame({s: d.close for s, d in data.items()}).sort_index()
    hi = pd.DataFrame({s: d.high for s, d in data.items()}).reindex(px.index)
    lo = pd.DataFrame({s: d.low for s, d in data.items()}).reindex(px.index)
    return px, hi, lo


def rsi(px, n=2):
    d = px.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


# ------------------------------------------------------------------ segnali
# Ogni funzione restituisce una matrice di PESI (righe=date, colonne=asset),
# gia' ritardata di un giorno dal chiamante. Somma dei pesi = 1 in long-only,
# 0 in market-neutral.

def sig_trend(px, hi, lo, p, mode):
    n = p["n"]
    above = px > px.rolling(n).mean()
    if mode == "long":
        w = above.astype(float)
    else:
        w = above.astype(float) - (~above).astype(float)
    return w


def sig_xsmom(px, hi, lo, p, mode):
    k, top = p["k"], p["top"]
    mom = px.pct_change(k)
    r = mom.rank(axis=1, ascending=False)
    n_ok = mom.notna().sum(axis=1)
    longs = r.le(top).astype(float)
    if mode == "long":
        return longs
    shorts = r.gt(n_ok.values[:, None] - top).astype(float)
    return longs - shorts


def sig_donchian(px, hi, lo, p, mode):
    inn, out = p["inn"], p["out"]
    up = px >= px.rolling(inn).max()
    dn = px <= px.rolling(out).min()
    st = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
    st[up] = 1.0
    st[dn] = 0.0 if mode == "long" else -1.0
    return st.ffill().fillna(0.0)


def sig_meanrev(px, hi, lo, p, mode):
    thr, trend = p["thr"], p["trend"]
    r = rsi(px, 2)
    ok = px > px.rolling(trend).mean()
    lng = ((r < thr) & ok).astype(float)
    if mode == "long":
        return lng
    sht = ((r > 100 - thr) & ~ok).astype(float)
    return lng - sht


FAMILIES = {
    "trend temporale": (sig_trend, [{"n": n} for n in (20, 50, 100, 200)]),
    "momentum cross-sectional": (sig_xsmom, [{"k": k, "top": t}
                                             for k in (30, 60, 90) for t in (2, 3)]),
    "breakout Donchian": (sig_donchian, [{"inn": i, "out": o}
                                         for i in (20, 50) for o in (10, 20, 50)]),
    "mean reversion RSI2": (sig_meanrev, [{"thr": t, "trend": tr}
                                          for t in (5, 10, 20) for tr in (50, 200)]),
}


def backtest(px, w, cost=COST_CRYPTO):
    """Pesi normalizzati, rendimenti netti di costo, turnover per le imposte."""
    ret = px.pct_change().fillna(0.0)
    gross = w.abs().sum(axis=1).replace(0, np.nan)
    wn = w.div(gross, axis=0).fillna(0.0).shift(1).fillna(0.0)   # shift: niente look-ahead
    turn = wn.diff().abs().sum(axis=1).fillna(wn.abs().sum(axis=1)) / 2.0
    net = (wn * ret).sum(axis=1) - turn * cost
    return net, turn


def stats(net):
    net = net.dropna()
    yrs = len(net) / PPY
    curve = (1 + net).cumprod()
    tot = float(curve.iloc[-1])
    return dict(cagr=(tot ** (1 / yrs) - 1) * 100 if tot > 0 else -100.0,
                sharpe=float(net.mean() / net.std() * np.sqrt(PPY))
                if net.std() > 0 else np.nan,
                dd=float((curve / curve.cummax() - 1).min()) * 100)


def walk_forward(px, hi, lo, fn, grid, mode, start=2021):
    """Ogni anno sceglie i parametri sul passato e li applica nell'anno dopo."""
    years = sorted({t.year for t in px.index if t.year >= start})
    segs, turns, picks, nev = [], [], [], 0
    for y in years:
        tr = px.index[px.index.year < y]
        if len(tr) < 400:
            continue
        best, bp = None, None
        for p in grid:
            w = fn(px.loc[tr], hi.loc[tr], lo.loc[tr], p, mode)
            net, _ = backtest(px.loc[tr], w)
            s = stats(net)
            nev += 1
            v = s["sharpe"]
            if np.isfinite(v) and (best is None or v > best):
                best, bp = v, p
        if bp is None:
            continue
        upto = px.index[px.index.year <= y]
        w = fn(px.loc[upto], hi.loc[upto], lo.loc[upto], bp, mode)
        net, turn = backtest(px.loc[upto], w)
        m = net.index.year == y
        segs.append(net[m]); turns.append(turn[m]); picks.append((y, bp))
    if not segs:
        return None, None, picks, nev
    return pd.concat(segs), pd.concat(turns), picks, nev


def main():
    px, hi, lo = panel()
    print(f"{px.shape[1]} asset, {px.index[0].date()} -> {px.index[-1].date()}")
    common = px.dropna()
    print(f"Finestra con tutti e 7 gli asset: {common.index[0].date()} -> "
          f"{common.index[-1].date()} ({len(common)} giorni)\n")

    bh_net = px.pct_change().mean(axis=1)
    rows, streams = [], {}
    print(f"{'famiglia':<28}{'modo':<16}{'CAGR':>9}{'Sharpe':>8}{'DD':>9}"
          f"{'turn/an':>9}{'valut.':>8}")
    print("-" * 88)
    for fam, (fn, grid) in FAMILIES.items():
        for mode in ("long", "ls"):
            net, turn, picks, nev = walk_forward(px, hi, lo, fn, grid, mode)
            if net is None:
                continue
            s = stats(net)
            tpy = float(turn.sum()) / (len(net) / PPY)
            streams[(fam, mode)] = (net, turn)
            rows.append(dict(fam=fam, mode=mode, **s, turn=tpy, nev=nev))
            print(f"{fam:<28}{'long-only' if mode=='long' else 'long/short':<16}"
                  f"{s['cagr']:>8.1f}%{s['sharpe']:>8.2f}{s['dd']:>8.1f}%"
                  f"{tpy:>8.1f}x{nev:>8}")

    # benchmark sulla stessa finestra
    idx = next(iter(streams.values()))[0].index
    b = stats(bh_net.reindex(idx))
    print(f"{'buy&hold equipesato':<28}{'—':<16}{b['cagr']:>8.1f}%{b['sharpe']:>8.2f}"
          f"{b['dd']:>8.1f}%{0.0:>8.1f}x{0:>8}")

    # ---------------------------------------------------- combinazione
    print(f"\n--- Combinazione delle quattro famiglie (pesi uguali) ---")
    print(f"{'modo':<16}{'CAGR':>9}{'Sharpe':>8}{'DD':>9}{'turn/an':>9}")
    combos = {}
    for mode in ("long", "ls"):
        ns = [v[0] for k, v in streams.items() if k[1] == mode]
        ts = [v[1] for k, v in streams.items() if k[1] == mode]
        if not ns:
            continue
        cn = pd.concat(ns, axis=1).mean(axis=1).dropna()
        ct = pd.concat(ts, axis=1).mean(axis=1).reindex(cn.index).fillna(0.0)
        combos[mode] = (cn, ct)
        s = stats(cn)
        print(f"{'long-only' if mode=='long' else 'long/short':<16}{s['cagr']:>8.1f}%"
              f"{s['sharpe']:>8.2f}{s['dd']:>8.1f}%"
              f"{float(ct.sum())/(len(cn)/PPY):>8.1f}x")

    # ---------------------------------------------------- imposte
    print(f"\n--- Netto di imposte irlandesi (le cripto sono asset ai fini CGT) ---")
    print(f"{'strategia':<34}{'IRR 33%':>10}{'IRR 52%':>10}{'vs B&H 33%':>13}")
    rf0 = pd.Series(0.0, index=idx)
    bb = simulate_pac(bh_net.reindex(idx), CGT_SHARES, rf=rf0, periods_per_year=PPY)
    print(f"{'buy&hold equipesato':<34}{bb.irr_annual:>9.1f}%{'—':>10}{0.0:>12.1f}%")
    best_key = None
    for (fam, mode), (net, turn) in list(streams.items()) + \
            [(("COMBINAZIONE", m), v) for m, v in combos.items()]:
        r33 = simulate_pac(net, CGT_SHARES, rf=rf0, realize_frac=turn.clip(0, 1),
                           periods_per_year=PPY)
        r52 = simulate_pac(net, TRADING_52, rf=rf0, realize_frac=turn.clip(0, 1),
                           periods_per_year=PPY)
        lbl = f"{fam[:22]} {'L' if mode=='long' else 'L/S'}"
        d = r33.irr_annual - bb.irr_annual
        print(f"{lbl:<34}{r33.irr_annual:>9.1f}%{r52.irr_annual:>9.1f}%{d:>12.1f}%")
        if best_key is None or d > best_key[1]:
            best_key = ((fam, mode), d, net, turn)

    # ---------------------------------------------------- DSR
    n_cum = lab.n_trials_so_far()
    tot_ev = sum(r["nev"] for r in rows)
    sh = pd.Series([r["sharpe"] for r in rows]).dropna()
    vsr = float((sh / np.sqrt(PPY)).var(ddof=1)) if len(sh) > 2 else None
    d = lab.deflated_sharpe(best_key[2], n_cum + tot_ev, var_sr=vsr, round_id=ROUND)
    print(f"\n--- Deflated Sharpe del migliore ({best_key[0][0]}, "
          f"{'long' if best_key[0][1]=='long' else 'long/short'}) ---")
    print(f"  tentativi: {n_cum} a registro + {tot_ev} valutazioni interne = "
          f"{n_cum+tot_ev}")
    print(f"  Sharpe osservato {d['sr_period']*np.sqrt(PPY):.3f}  "
          f"soglia H0 {d['sr0']*np.sqrt(PPY):.3f}")
    print(f"  DSR {d['dsr']:.3f}  -> "
          f"{'PROMUOVIBILE' if d['dsr'] > 0.95 else 'NON promuovibile'}")

    lab.log_trials([dict(round=ROUND, hypothesis="H24 swing multi-strategia cripto L/S",
                         config=f"{r['fam']}|{r['mode']}", window="2021-2026",
                         sharpe=r["sharpe"], irr=r["cagr"], bh_irr=b["cagr"],
                         excess=r["cagr"] - b["cagr"], n_obs=len(idx),
                         note=f"turn={r['turn']:.1f}x") for r in rows])
    pd.DataFrame(rows).to_csv(OUT / "round23_crypto_swing.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

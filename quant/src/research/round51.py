"""Giro 51 — F3, F4, F5: il sistema EMA 9/21/50/200.

TRE VOCI DELLA CODA, verbatim in QUEUE.md, riassunte qui.

F3 sistema completo su base giornaliera (QQQ, AAPL, 8 cripto).
   PREDIZIONE: lordo positivo sugli asset in tendenza, ma 20-60 operazioni
   l'anno portano al 52% e netto finisce sotto il buy&hold su OGNI asset.
   FALSIFICATA SE: batte il buy&hold su almeno meta' degli asset.
F4 lo stesso su QQQ a 1 ora e 15 minuti.
   PREDIZIONE: risultato netto monotonicamente peggiore accorciando il timeframe.
   FALSIFICATA SE: un timeframe intraday batte il giornaliero.
F5 ablazione: cosa fa il lavoro.
   PREDIZIONE: il solo filtro di tendenza cattura almeno l'80% del vantaggio
   lordo del sistema completo.
   FALSIFICATA SE: l'aspettativa per operazione del sistema completo supera
   quella del solo filtro di tendenza di oltre il 50%.

LE REGOLE, dall'immagine, senza aggiunte:
  ingresso   prezzo sopra EMA200 E EMA21 sopra EMA50 (tendenza valida)
             ritracciamento: minimo della barra tocca o scende sotto la EMA21
             volume in calo durante il ritracciamento
             candela rialzista (chiusura sopra apertura) vicino alla EMA21
  uscita     stop iniziale sotto il minimo delle ultime 10 barre (NON e'
             specificato nell'immagine: lo fisso e lo dichiaro)
             meta' posizione chiusa a 1:2 rischio/rendimento
             stop a pareggio sul resto dopo il parziale
             trailing sulla EMA21
             uscita totale su chiusura sotto la EMA50

ORDINE DEGLI EVENTI DENTRO LA BARRA. Con solo OHLC non so se in una barra e'
venuto prima il minimo o il massimo. Assumo SEMPRE PRIMA IL PEGGIO: se una barra
tocca sia lo stop sia il target, conta lo stop. E' l'ipotesi conservativa, ed e'
l'unica difendibile senza dati intrabar.
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

ROUND = 51
OUT = Path(__file__).resolve().parents[2] / "out"
DATA = Path(__file__).resolve().parents[2] / "data"
N_PREREG = 71
STOP_LOOKBACK = 10


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def ema_system(df, use_volume=True, use_pullback=True, trend_only=False,
               cost=C.COST_ROUND_TRIP):
    """Restituisce (rendimenti per barra, numero di operazioni, lista trade).

    `trend_only` ignora ingressi e uscite tattiche: sta dentro finche' la
    tendenza e' valida, fuori altrimenti. E' il termine di paragone di F5.
    """
    o, h, l, c = df["open"], df["high"], df["low"], df["close"]
    v = df["volume"]
    e9, e21, e50, e200 = ema(c, 9), ema(c, 21), ema(c, 50), ema(c, 200)
    trend = (c > e200) & (e21 > e50)
    if trend_only:
        pos = trend.shift(1).fillna(False).astype(float)
        ret = c.pct_change().fillna(0.0) * pos
        turn = pos.diff().abs().fillna(0.0)
        return ret - turn * cost / 2.0, turn, float(turn.sum() / 2), []

    touch = (l <= e21) & (c > e21)                    # ritracciamento sulla EMA21
    volde = v < v.rolling(5).mean()                   # volume in calo
    bull = c > o                                      # candela rialzista
    sig = trend.shift(1).fillna(False)
    if use_pullback:
        sig &= touch.shift(1).fillna(False)
    if use_volume:
        sig &= volde.shift(1).fillna(False)
    sig &= bull.shift(1).fillna(False)

    n = len(df)
    ret = np.zeros(n)
    trades = []
    in_pos = False
    size = 0.0
    entry = stop = target = 0.0
    lo10 = l.rolling(STOP_LOOKBACK).min()
    for i in range(1, n):
        px_o, px_h, px_l, px_c = o.iloc[i], h.iloc[i], l.iloc[i], c.iloc[i]
        if in_pos:
            r = 0.0
            # PRIMA IL PEGGIO: se la barra tocca stop e target, vince lo stop
            if px_l <= stop:
                r = size * (stop / c.iloc[i - 1] - 1) - size * cost / 2
                trades.append((entry, stop, size, "stop"))
                in_pos, size = False, 0.0
            elif size == 1.0 and px_h >= target:
                r = 0.5 * (target / c.iloc[i - 1] - 1) - 0.5 * cost / 2
                r += 0.5 * (px_c / c.iloc[i - 1] - 1)
                trades.append((entry, target, 0.5, "target"))
                size, stop = 0.5, entry
            elif px_c < e50.iloc[i]:
                r = size * (px_c / c.iloc[i - 1] - 1) - size * cost / 2
                trades.append((entry, px_c, size, "sotto EMA50"))
                in_pos, size = False, 0.0
            else:
                r = size * (px_c / c.iloc[i - 1] - 1)
                stop = max(stop, e21.iloc[i])          # trailing sulla EMA21
            ret[i] = r
        elif sig.iloc[i] and not np.isnan(lo10.iloc[i - 1]):
            entry = px_o
            stop = lo10.iloc[i - 1]
            if stop >= entry:
                continue
            target = entry + 2.0 * (entry - stop)
            size, in_pos = 1.0, True
            ret[i] = (px_c / entry - 1) - cost / 2
    s = pd.Series(ret, index=df.index)
    turn = pd.Series(0.0, index=df.index)
    return s, turn, float(len(trades)), trades


def load_ohlc(path, tz=None):
    d = pd.read_csv(path, parse_dates=["datetime"]).sort_values("datetime")
    d = d.set_index("datetime")
    for c in ("open", "high", "low", "close", "volume"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()


def to_monthly_ret(s, bars_per_year):
    """Comprime i rendimenti per barra in rendimenti mensili."""
    m = (1 + s).resample("ME").prod() - 1
    m.index = m.index.to_period("M").to_timestamp("M")
    return m.dropna()


def assets():
    out = {}
    for nm, f in (("QQQ", "td_QQQ_1day.csv"), ("AAPL", "td_AAPL_1day.csv")):
        out[nm] = load_ohlc(DATA / f)
    for f in sorted(DATA.glob("okx_*_1d.csv")):
        out[f.stem.split("_")[1][:-4]] = load_ohlc(f)
    return out


def main():
    ff = dataio.ff_factors_monthly()
    rf_all = ff["RF"]
    A = assets()

    # ================================================================ F3
    print(f"{'='*100}\nF3 — IL SISTEMA COMPLETO SU BASE GIORNALIERA\n{'='*100}")
    print("   Ordine dentro la barra: SEMPRE PRIMA IL PEGGIO. Se una barra tocca")
    print("   sia lo stop sia il target, conta lo stop.\n")
    rows3, beats = [], []
    print(f"   {'asset':<8}{'anni':>6}{'oper.':>7}{'op/anno':>9}{'CAGR sist':>11}"
          f"{'CAGR B&H':>10}{'IRR sist':>10}{'IRR B&H':>9}{'delta':>8}")
    print("   " + "-" * 78)
    for nm, df in A.items():
        s, _, ntr, _ = ema_system(df)
        yrs = (df.index[-1] - df.index[0]).days / 365.25
        m = to_monthly_ret(s, 252)
        if len(m) < 24:
            continue
        rf0 = rf_all.reindex(m.index).ffill().fillna(0.0)
        bhm = to_monthly_ret(df["close"].pct_change().fillna(0.0), 252).reindex(m.index)
        rz = pd.Series(min(ntr / yrs / 12.0, 1.0), index=m.index)
        r = B.eval_stream(f"EMA {nm}", m, rf0, rz)
        bh = B.eval_stream(f"B&H {nm}", bhm, rf0)
        r["ntr"] = ntr
        r["per_year"] = ntr / yrs
        rows3.append((nm, r, bh))
        beats.append(r["irr_ref"] > bh["irr"])
        print(f"   {nm:<8}{yrs:>6.1f}{int(ntr):>7}{ntr/yrs:>9.1f}"
              f"{r['cagr']:>10.2f}%{bh['cagr']:>9.2f}%"
              f"{r['irr_ref']:>9.2f}%{bh['irr']:>8.2f}%"
              f"{r['irr_ref']-bh['irr']:>+8.2f}")
    f3_fals = sum(beats) >= len(beats) / 2
    print(f"\n   Batte il buy&hold su {sum(beats)}/{len(beats)} asset")
    print(f"   -> ipotesi F3 {'FALSIFICATA' if f3_fals else 'CONFERMATA'}")

    # ================================================================ F4
    print(f"\n{'='*100}\nF4 — LO STESSO SISTEMA SU TIMEFRAME INTRADAY (QQQ)\n{'='*100}")
    tfs = [("giornaliero", "td_QQQ_1day.csv", 252),
           ("1 ora", "td_QQQ_1h.csv", 252 * 7),
           ("15 minuti", "td_QQQ_15min.csv", 252 * 26)]
    rows4 = []
    print(f"   {'timeframe':<14}{'barre':>8}{'anni':>7}{'oper.':>7}{'op/anno':>9}"
          f"{'CAGR':>10}{'B&H':>9}{'IRR sist':>10}{'IRR B&H':>9}")
    print("   " + "-" * 83)
    for lbl, f, bpy in tfs:
        df = load_ohlc(DATA / f)
        s, _, ntr, _ = ema_system(df)
        yrs = (df.index[-1] - df.index[0]).days / 365.25
        m = to_monthly_ret(s, bpy)
        rf0 = rf_all.reindex(m.index).ffill().fillna(0.0)
        bhm = to_monthly_ret(df["close"].pct_change().fillna(0.0), bpy).reindex(m.index)
        rz = pd.Series(1.0, index=m.index)
        r = B.eval_stream(f"EMA QQQ {lbl}", m, rf0, rz)
        bh = B.eval_stream(f"B&H QQQ {lbl}", bhm, rf0)
        rows4.append((lbl, r, bh, ntr / yrs, len(df), yrs))
        print(f"   {lbl:<14}{len(df):>8}{yrs:>7.1f}{int(ntr):>7}{ntr/yrs:>9.1f}"
              f"{r['cagr']:>9.2f}%{bh['cagr']:>8.2f}%"
              f"{r['irr_ref']:>9.2f}%{bh['irr']:>8.2f}%")
    print("\n   ATTENZIONE alle finestre: 20 anni sul giornaliero, 2,9 sull'orario,")
    print("   0,8 sui 15 minuti. Twelve Data ne da' 5.000 barre e basta, quindi i")
    print("   tre timeframe NON coprono lo stesso periodo e il confronto di CAGR")
    print("   fra righe e' indicativo. Il numero di operazioni l'anno invece e'")
    print("   confrontabile, ed e' quello che decide.")
    daily_irr = rows4[0][1]["irr_ref"]
    f4_fals = any(r[1]["irr_ref"] > daily_irr for r in rows4[1:])
    print(f"\n   Un timeframe intraday batte il giornaliero? "
          f"{'SI' if f4_fals else 'NO'}")
    print(f"   -> ipotesi F4 {'FALSIFICATA' if f4_fals else 'CONFERMATA'}")

    # ================================================================ F5
    print(f"\n{'='*100}\nF5 — ABLAZIONE: QUALE PEZZO FA IL LAVORO\n{'='*100}")
    variants = [("sistema completo", dict()),
                ("senza filtro volume", dict(use_volume=False)),
                ("senza ritracciamento", dict(use_pullback=False)),
                ("solo filtro di tendenza", dict(trend_only=True))]
    rows5 = []
    print(f"   {'variante':<26}{'oper./anno':>12}{'CAGR medio':>12}"
          f"{'aspettativa/oper.':>19}{'IRR media':>11}")
    print("   " + "-" * 80)
    for lbl, kw in variants:
        cg, ir, npy, exp = [], [], [], []
        for nm, df in A.items():
            out = ema_system(df, **kw)
            s, _, ntr = out[0], out[1], out[2]
            yrs = (df.index[-1] - df.index[0]).days / 365.25
            m = to_monthly_ret(s, 252)
            if len(m) < 24:
                continue
            rf0 = rf_all.reindex(m.index).ffill().fillna(0.0)
            rz = pd.Series(min(max(ntr, 1) / yrs / 12.0, 1.0), index=m.index)
            r = B.eval_stream(f"{lbl} {nm}", m, rf0, rz)
            cg.append(r["cagr"])
            ir.append(r["irr_ref"])
            npy.append(ntr / yrs)
            gross = float((1 + s).prod() ** (1 / yrs) - 1)
            exp.append(gross / max(ntr / yrs, 1e-9) * 100)
        rows5.append(dict(variante=lbl, npy=np.mean(npy), cagr=np.mean(cg),
                          exp=np.mean(exp), irr=np.mean(ir)))
        print(f"   {lbl:<26}{np.mean(npy):>12.1f}{np.mean(cg):>11.2f}%"
              f"{np.mean(exp):>18.3f}%{np.mean(ir):>10.2f}%")
    full = rows5[0]
    trend = rows5[-1]
    ratio = full["exp"] / trend["exp"] if trend["exp"] != 0 else float("inf")
    cover = trend["cagr"] / full["cagr"] * 100 if full["cagr"] != 0 else float("nan")
    print(f"\n   Il solo filtro di tendenza cattura il {cover:.0f}% del CAGR lordo")
    print(f"   del sistema completo (previsto: almeno l'80%)")
    print(f"   Aspettativa per operazione: completo {full['exp']:.3f}% contro "
          f"tendenza {trend['exp']:.3f}%  -> rapporto {ratio:.2f}")
    f5_fals = ratio > 1.5
    print(f"   FALSIFICATA se il rapporto supera 1,50")
    print(f"   -> ipotesi F5 {'FALSIFICATA' if f5_fals else 'CONFERMATA'}")

    allr = [r for _, r, _ in rows3] + [r for _, r, _, _, _, _ in rows4]
    best = max(allr, key=lambda r: r["irr_ref"])
    dd = lab.deflated_sharpe(best["gross"], N_PREREG, round_id=ROUND)
    print(f"\n   DSR del migliore ({best['label']}) su N={N_PREREG}: {dd['dsr']:.3f}")

    lab.log_trials([dict(round=ROUND, hypothesis="F3/F4 sistema EMA",
                         config=r["label"], window="varie", sharpe=r["sharpe"],
                         irr=r["irr"], bh_irr=b["irr"],
                         excess=r["irr_ref"] - b["irr"], n_obs=r["n"],
                         note=f"turn={r['turn']:.2f}x")
                    for _, r, b in rows3] +
                   [dict(round=ROUND, hypothesis="F5 ablazione EMA",
                         config=r["variante"], window="tutti gli asset",
                         sharpe="", irr=r["irr"], bh_irr="", excess="",
                         n_obs="", note=f"op/anno={r['npy']:.1f},exp={r['exp']:.3f}%")
                    for r in rows5])
    pd.DataFrame(rows5).to_csv(OUT / "round51_ablazione.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

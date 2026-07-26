"""Giro 26 — Le due lacune: HMM sull'azionario, Kronos sulle cripto.

Fin qui i due modelli sono stati provati ciascuno su un mercato solo, e per
giunta su quello sbagliato:

  L'HMM a cambio di regime (giro 24) e' girato solo su cripto, dove i regimi
  durano poco e il campione e' di sei anni. Sull'azionario ci sono cento anni
  di storia e regimi (1929, 1937, 1973, 2000, 2008, 2020) che sono l'esempio
  da manuale di cio' che un modello a stati dovrebbe riconoscere.

  Kronos (giro 17) e' girato solo su QQQ. Ma e' addestrato su 12 miliardi di
  K-line da 45 borse, exchange cripto compresi, e la demo pubblicata dagli
  autori e' su BTC/USDT. Le cripto sono il suo terreno di casa: se non
  funziona li', non funziona.

Stesso protocollo dei giri originali, senza look-ahead: HMM ristimato ogni
anno con probabilita' filtrate (solo forward), Kronos con contesto che si
ferma alla barra precedente.
"""
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, "/tmp/claude-0/-home-user-mecagent-technical-test/"
                   "1282c159-1b67-5dda-8a70-400c3f3d0cf1/scratchpad/kronos_pkg")
warnings.filterwarnings("ignore")

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES, TRADING_52, first_of_month
from research import lab
from research.round15 import load, evaluate
from research.round19 import load_crypto, COST_CRYPTO
from research.round24 import hmm_filtered_states, forward_filter
from research.round25 import _stats

ROUND = 26
OUT = Path(__file__).resolve().parents[2] / "out"


# ============================================================ A. HMM azionario
def hmm_equity(name, ret, ppy, rf=None, cost=C.COST_ROUND_TRIP):
    print(f"\n{'='*82}\nHMM SU {name}   {len(ret)} osservazioni "
          f"{ret.index[0].date()} -> {ret.index[-1].date()}\n{'='*82}")
    pbear, means = hmm_filtered_states(ret, 2)
    valid = pbear.dropna()
    print(f"  copertura {len(valid)/len(ret)*100:.0f}%   "
          f"tempo in regime avverso {(valid>0.5).mean()*100:.0f}%")

    r = ret.reindex(valid.index)
    rf0 = (rf.reindex(valid.index).fillna(0.0) if rf is not None
           else pd.Series(0.0, index=valid.index))
    con = first_of_month(valid.index) if ppy > 12 else None
    bh = _stats(r, ppy)
    bb = simulate_pac(r, CGT_SHARES, rf=rf0, periods_per_year=ppy, contrib_on=con)

    rows = []
    print(f"\n  {'sistema':<34}{'CAGR':>9}{'Sharpe':>8}{'DD':>9}"
          f"{'op/an':>8}{'IRR 33%':>10}{'vs B&H':>9}")
    variants = {
        "long in favorevole, flat altrove": (pbear < 0.5).astype(float),
        "long in favorevole, short altrove": (pbear < 0.5).astype(float)
                                             - (pbear > 0.5).astype(float),
        "long solo se molto convinto": (pbear < 0.3).astype(float),
        "esposizione = 1 - P(avverso)": (1 - pbear).clip(0, 1),
    }
    for lbl, pos in variants.items():
        p = pos.reindex(valid.index).fillna(0.0).shift(1).fillna(0.0)
        turn = p.diff().abs().fillna(p.abs())
        net = (p * r - turn * cost / 2.0).dropna()
        s = _stats(net, ppy)
        res = simulate_pac(net, CGT_SHARES, in_market=(p.abs() > 0).astype(float),
                           rf=rf0, periods_per_year=ppy, contrib_on=con)
        res52 = simulate_pac(net, TRADING_52,
                             in_market=(p.abs() > 0).astype(float), rf=rf0,
                             periods_per_year=ppy, contrib_on=con)
        ops = float((p.diff().abs() > 0).sum()) / (len(p) / ppy)
        rows.append(dict(mkt=name, sys=lbl, **s, ops=ops, irr=res.irr_annual,
                         irr52=res52.irr_annual, vs=res.irr_annual - bb.irr_annual,
                         net=net))
        print(f"  {lbl:<34}{s['cagr']:>8.2f}%{s['sharpe']:>8.2f}{s['dd']:>8.1f}%"
              f"{ops:>8.1f}{res.irr_annual:>9.2f}%"
              f"{res.irr_annual-bb.irr_annual:>+8.2f}%")
    print(f"  {'buy&hold':<34}{bh['cagr']:>8.2f}%{bh['sharpe']:>8.2f}"
          f"{bh['dd']:>8.1f}%{0.0:>8.1f}{bb.irr_annual:>9.2f}%{0.0:>+8.2f}%")
    return rows


# ============================================================ B. Kronos cripto
def kronos_crypto(symbols=("BTCUSDT", "ETHUSDT"), lookback=256, horizon=5,
                  stride=5, n_pred=180):
    from model import Kronos, KronosTokenizer, KronosPredictor
    tok = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    mdl = Kronos.from_pretrained("NeoQuasar/Kronos-base")
    pred = KronosPredictor(mdl, tok, device="cpu", max_context=512)

    out = []
    for sym in symbols:
        d = load_crypto(sym).reset_index()
        d.columns = [c.lower() for c in d.columns]
        d["amount"] = d["close"] * d["volume"]
        starts = list(range(lookback, len(d) - horizon, stride))[-n_pred:]
        print(f"\n  {sym}: {len(starts)} previsioni, "
              f"{d['datetime'].iloc[starts[0]].date()} -> "
              f"{d['datetime'].iloc[starts[-1]].date()}")
        recs, t0 = [], time.time()
        for k, i in enumerate(starts):
            ctx = d.iloc[i - lookback:i]
            try:
                o = pred.predict(
                    df=ctx[["open", "high", "low", "close", "volume", "amount"]]
                        .reset_index(drop=True),
                    x_timestamp=ctx["datetime"].reset_index(drop=True),
                    y_timestamp=d.iloc[i:i + horizon]["datetime"].reset_index(drop=True),
                    pred_len=horizon, T=1.0, top_p=0.9, sample_count=1, verbose=False)
            except Exception:
                continue
            last = float(ctx["close"].iloc[-1])
            recs.append(dict(i=i, sym=sym, date=d["datetime"].iloc[i],
                             pred=float(o["close"].iloc[-1]) / last - 1.0,
                             actual=float(d["close"].iloc[i + horizon - 1]) / last - 1.0))
            if (k + 1) % 60 == 0:
                print(f"    {k+1}/{len(starts)} ({time.time()-t0:.0f}s)")
        out.append(pd.DataFrame(recs))
    return pd.concat(out, ignore_index=True)


def kronos_report(r):
    from scipy import stats as st
    print(f"\n{'='*82}\nKRONOS SUL SUO TERRENO DI CASA (cripto)\n{'='*82}")
    print(f"  {'simbolo':<10}{'n':>6}{'accur.':>9}{'indip.':>9}{'chi2 p':>9}"
          f"{'RankIC':>9}{'p':>8}{'prev.su':>9}{'real.su':>9}")
    rows = []
    for sym, g in list(r.groupby("sym")) + [("TUTTI", r)]:
        pu, au = (g["pred"] > 0).mean(), (g["actual"] > 0).mean()
        hit = float((np.sign(g["pred"]) == np.sign(g["actual"])).mean())
        base = pu * au + (1 - pu) * (1 - au)
        ct = pd.crosstab(g["pred"] > 0, g["actual"] > 0)
        try:
            chi = st.chi2_contingency(ct).pvalue
        except Exception:
            chi = np.nan
        rk = st.spearmanr(g["pred"], g["actual"])
        rows.append(dict(sym=sym, n=len(g), hit=hit, base=base, chi=chi,
                         rho=rk.statistic, p=rk.pvalue, pu=pu, au=au))
        print(f"  {sym:<10}{len(g):>6}{hit*100:>8.1f}%{base*100:>8.1f}%"
              f"{chi:>9.3f}{rk.statistic:>+9.3f}{rk.pvalue:>8.3f}"
              f"{pu*100:>8.0f}%{au*100:>8.0f}%")
    print("\n  'indip.' = accuratezza attesa se le previsioni fossero")
    print("  indipendenti dall'esito. Se coincide con quella osservata,")
    print("  il modello non porta informazione direzionale.")
    return pd.DataFrame(rows)


def kronos_backtest(r):
    print(f"\n  Backtest del segnale, per simbolo:")
    print(f"  {'simbolo':<10}{'CAGR':>9}{'B&H':>9}{'vs':>9}{'Sharpe':>8}{'DD':>9}")
    rows = []
    for sym, g in r.groupby("sym"):
        px = load_crypto(sym)
        ret = px.close.pct_change().fillna(0.0)
        pos = pd.Series(0.0, index=px.index)
        for _, row in g.iterrows():
            i = int(row["i"])
            pos.iloc[i:i + 5] = 1.0 if row["pred"] > 0 else 0.0
        sl = slice(int(g["i"].iloc[0]), int(g["i"].iloc[-1]) + 5)
        rr, pp = ret.iloc[sl], pos.iloc[sl]
        turn = pp.diff().abs().fillna(pp.abs())
        net = pp * rr - turn * COST_CRYPTO / 2
        s, b = _stats(net, 365), _stats(rr, 365)
        rows.append(dict(sym=sym, cagr=s["cagr"], bh=b["cagr"],
                         vs=s["cagr"] - b["cagr"], sharpe=s["sharpe"],
                         dd=s["dd"], net=net))
        print(f"  {sym:<10}{s['cagr']:>8.1f}%{b['cagr']:>8.1f}%"
              f"{s['cagr']-b['cagr']:>+8.1f}%{s['sharpe']:>8.2f}{s['dd']:>8.1f}%")
    return rows


def main():
    allrows = []

    # ---------------------------------------------------------- A
    ffd = dataio.ff_factors_daily()
    crsp = (ffd["Mkt-RF"] + ffd["RF"]).dropna()
    allrows += hmm_equity("indice CRSP giornaliero", crsp, 252,
                          ffd["RF"].reindex(crsp.index).fillna(0.0))
    ffm = dataio.ff_factors_monthly()
    crspm = (ffm["Mkt-RF"] + ffm["RF"]).dropna()
    allrows += hmm_equity("indice CRSP mensile", crspm, 12, ffm["RF"])
    qq = load("QQQ", "1day").close.pct_change().dropna()
    allrows += hmm_equity("QQQ giornaliero", qq, 252)

    # ---------------------------------------------------------- B
    r = kronos_crypto()
    r.to_csv(OUT / "round26_kronos_crypto.csv", index=False)
    diag = kronos_report(r)
    bt = kronos_backtest(r)

    # ---------------------------------------------------------- sintesi
    print(f"\n{'='*82}\nSINTESI\n{'='*82}")
    d = pd.DataFrame([{k: v for k, v in x.items() if k != "net"} for x in allrows])
    print(f"HMM sull'azionario: {int((d['vs']>0).sum())}/{len(d)} configurazioni "
          f"battono il buy&hold netto imposte")
    best = d.sort_values("vs", ascending=False).iloc[0]
    print(f"  migliore: {best['sys']} su {best['mkt']}  {best['vs']:+.2f} punti "
          f"(Sharpe {best['sharpe']:.2f})")
    tot = diag[diag["sym"] == "TUTTI"].iloc[0]
    print(f"\nKronos su cripto: accuratezza {tot['hit']*100:.1f}% contro "
          f"{tot['base']*100:.1f}% attesa sotto indipendenza, chi2 p={tot['chi']:.3f}")
    print(f"  battono il buy&hold: {sum(1 for x in bt if x['vs']>0)}/{len(bt)}")

    bn = allrows[int(np.argmax([x["vs"] for x in allrows]))]
    n_cum = lab.n_trials_so_far()
    nev = len(allrows) + len(bt)
    sh = pd.Series([x["sharpe"] for x in allrows]).dropna()
    vsr = float((sh / np.sqrt(252)).var(ddof=1)) if len(sh) > 2 else None
    dd = lab.deflated_sharpe(bn["net"], n_cum + nev, var_sr=vsr, round_id=ROUND)
    beats = bn["vs"] > 0
    print(f"\nDSR del migliore su {n_cum+nev} tentativi: {dd['dsr']:.3f}")
    print(f"  ATTENZIONE: il DSR verifica che lo Sharpe non sia un caso, cioe'")
    print(f"  lo confronta con ZERO, non con il benchmark. Qui il migliore ha")
    print(f"  Sharpe reale ma perde {abs(bn['vs']):.2f} punti contro il buy&hold:")
    print(f"  un DSR alto su una strategia che perde non e' una promozione.")
    print(f"  -> {'PROMUOVIBILE' if (dd['dsr']>0.95 and beats) else 'NON promuovibile'}")

    lab.log_trials(
        [dict(round=ROUND, hypothesis="H27 HMM azionario", config=f"{x['mkt']}|{x['sys']}",
              window="varie", sharpe=x["sharpe"], irr=x["irr"], bh_irr="",
              excess=x["vs"], n_obs=len(x["net"]), note=f"ops={x['ops']:.1f}")
         for x in allrows] +
        [dict(round=ROUND, hypothesis="H28 Kronos cripto", config=x["sym"],
              window="2020-2026", sharpe=x["sharpe"], irr=x["cagr"],
              bh_irr=x["bh"], excess=x["vs"], n_obs=len(x["net"]), note="")
         for x in bt])
    d.to_csv(OUT / "round26_hmm_equity.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

"""Giro 25 — Vol-targeting sulla struttura di ampiezza.

L'UNICA COSA PREVEDIBILE TROVATA IN 24 GIRI. Il giro 22 ha stabilito che la
dipendenza condizionale nei rendimenti sta quasi tutta nell'AMPIEZZA
(Cramer V 0,139, 12 test su 12 significativi) e quasi nulla nel SEGNO
(0,044, 4 su 12). Sapere che domani il mercato si muovera' molto non dice da
che parte — ma dice QUANTO ESPORSI.

IL SISTEMA. Si stima la volatilita' attesa e si scala l'esposizione per
mantenerla su un bersaglio costante: si alza quando il mercato e' calmo, si
abbassa quando e' agitato. Non c'e' nessuna previsione di direzione.

LA DOMANDA CHE DECIDE. Il vol-targeting funziona da decenni nella letteratura
(Moreira-Muir 2017 sui portafogli vol-managed, e tutta la famiglia risk
parity) e NON e' una mia idea. Le due domande vere sono:

  1. La catena di Markov sull'ampiezza aggiunge qualcosa rispetto a una
     banale volatilita' realizzata a 20 giorni? Se no, la "struttura" trovata
     al giro 21 e' solo autocorrelazione che qualunque stimatore cattura, e
     il formalismo non serve.

  2. Il miglioramento di Sharpe sopravvive a costi e imposte? Scalare
     l'esposizione significa ribilanciare di continuo, e ogni ribilanciamento
     e' un evento tassabile al 33% o al 52%. E' il muro contro cui sono
     finite quasi tutte le strategie di questo studio.

Se la risposta alla 1 e' no e alla 2 e' no, la conclusione e' che nemmeno la
sola cosa prevedibile che ho trovato e' monetizzabile nel regime fiscale
irlandese. Il che sarebbe il risultato piu' netto di tutto il lavoro.
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
from tax import simulate_pac, CGT_SHARES, TRADING_52, first_of_month
from research import lab
from research.round15 import load
from research.round19 import load_crypto, SYMS, COST_CRYPTO
from research.round21 import labelise, contexts

ROUND = 25
OUT = Path(__file__).resolve().parents[2] / "out"
MAX_LEV = 2.0            # tetto di leva: oltre non e' realistico per un retail


# ------------------------------------------------------------ previsori di vol
def vol_realised(ret, n=20):
    """Il riferimento banale: deviazione standard degli ultimi n giorni."""
    return ret.rolling(n).std().shift(1)


def vol_ewma(ret, lam=0.94):
    """RiskMetrics. Un filo piu' furbo, ancora banale."""
    return np.sqrt((ret ** 2).ewm(alpha=1 - lam).mean()).shift(1)


def vol_markov(ret, k=2, n=5, ppy=252, min_count=30):
    """Previsione di ampiezza dalla catena di Markov del giro 21.

    Il contesto sono le k etichette precedenti; la previsione e' il valore
    atteso di |rendimento| condizionato al contesto, stimato in modo
    ESPANSIVO: la tabella al tempo t usa solo osservazioni fino a t-1.
    """
    lab_now, edges = labelise(ret, n)
    ctx, ok = contexts(lab_now, k)
    absr = ret.abs().to_numpy()
    out = np.full(len(ret), np.nan)
    # accumulatori per contesto, aggiornati camminando in avanti
    ssum, scnt = {}, {}
    gsum, gcnt = 0.0, 0
    for i in range(len(ret)):
        c = int(ctx[i]) if ok[i] else None
        if c is not None and scnt.get(c, 0) >= min_count:
            out[i] = ssum[c] / scnt[c]
        elif gcnt > 0:
            out[i] = gsum / gcnt
        # aggiorno DOPO aver letto: la stima al tempo i non contiene i
        if ok[i] and np.isfinite(absr[i]):
            ssum[c] = ssum.get(c, 0.0) + absr[i]
            scnt[c] = scnt.get(c, 0) + 1
            gsum += absr[i]; gcnt += 1
    # |r| medio -> deviazione standard, sotto normalita': sd = |r| * sqrt(pi/2)
    return pd.Series(out * np.sqrt(np.pi / 2), index=ret.index)


PREDICTORS = {
    "vol realizzata 20g": lambda r: vol_realised(r, 20),
    "vol realizzata 60g": lambda r: vol_realised(r, 60),
    "EWMA RiskMetrics": lambda r: vol_ewma(r),
    "catena di Markov k=2": lambda r: vol_markov(r, 2, 5),
    "catena di Markov k=3": lambda r: vol_markov(r, 3, 5),
}


def forecast_quality(ret, ppy):
    """Quanto bene ciascun previsore anticipa la volatilita' realizzata dei
    20 giorni SUCCESSIVI. E' la domanda 1, e si risponde senza backtest."""
    fut = ret.rolling(20).std().shift(-20)
    rows = []
    for name, fn in PREDICTORS.items():
        p = fn(ret)
        m = p.notna() & fut.notna()
        if m.sum() < 200:
            continue
        from scipy import stats as st
        r2 = float(np.corrcoef(p[m], fut[m])[0, 1] ** 2)
        rho = float(st.spearmanr(p[m], fut[m]).statistic)
        mae = float((p[m] - fut[m]).abs().mean() * np.sqrt(ppy) * 100)
        rows.append(dict(name=name, r2=r2, rho=rho, mae=mae, n=int(m.sum())))
    return pd.DataFrame(rows)


def vol_target(ret, pred, target_ann, ppy, max_lev=MAX_LEV, cost=None,
               rf=None, band=0.10):
    """Esposizione = bersaglio / volatilita' prevista, con tetto e banda.

    La banda evita di ribilanciare per variazioni minime: si muove solo se
    l'esposizione desiderata devia oltre `band` da quella in essere.
    """
    tgt = (target_ann / np.sqrt(ppy)) / pred.replace(0, np.nan)
    tgt = tgt.clip(0, max_lev).fillna(0.0)
    cur, out = 0.0, []
    for v in tgt.to_numpy():
        if abs(v - cur) > band:
            cur = v
        out.append(cur)
    e = pd.Series(out, index=ret.index)
    turn = e.diff().abs().fillna(e.abs())
    c = cost if cost is not None else C.COST_ROUND_TRIP
    fin = 0.0
    if rf is not None:
        fin = (e - 1).clip(lower=0) * (rf.reindex(e.index).fillna(0.0)
                                       + C.FIN_SPREAD / ppy)
    return e * ret - turn * c - fin, turn, e


def run_market(name, ret, ppy, cost, rf=None, target=None):
    print(f"\n{'='*84}\n{name}   {len(ret)} osservazioni "
          f"{ret.index[0].date()} -> {ret.index[-1].date()}")
    print("=" * 84)

    q = forecast_quality(ret, ppy)
    print("\n1. QUALE PREVISORE DI VOLATILITA' E' MIGLIORE?")
    print(f"   {'previsore':<26}{'R2':>8}{'rho Spearman':>15}{'MAE ann.':>11}")
    for _, r in q.sort_values("r2", ascending=False).iterrows():
        print(f"   {r['name']:<26}{r['r2']:>8.3f}{r['rho']:>15.3f}{r['mae']:>10.1f}%")
    best_pred = q.sort_values("r2", ascending=False).iloc[0]["name"]
    mk = q[q["name"].str.contains("Markov")]["r2"].max()
    rv = q[~q["name"].str.contains("Markov")]["r2"].max()
    print(f"   Migliore fra i banali: {rv:.3f} · migliore Markov: {mk:.3f} · "
          f"guadagno {mk-rv:+.3f}")

    tgt_ann = target if target else float(ret.std() * np.sqrt(ppy))
    print(f"\n2. VOL-TARGETING (bersaglio {tgt_ann*100:.0f}% annuo, "
          f"leva max {MAX_LEV:g}x, banda 10%)")
    print(f"   {'previsore':<26}{'CAGR':>9}{'Sharpe':>8}{'DD':>9}"
          f"{'lev.med':>9}{'turn/an':>9}")
    bh = ret
    from research.round23 import stats
    b = stats(bh)
    rows = []
    for pname, fn in PREDICTORS.items():
        net, turn, e = vol_target(ret, fn(ret), tgt_ann, ppy, cost=cost, rf=rf)
        net = net.dropna()
        s = stats(net) if ppy == 365 else _stats(net, ppy)
        tpy = float(turn.sum()) / (len(net) / ppy)
        rows.append(dict(mkt=name, pred=pname, **s, lev=float(e.mean()),
                         turn=tpy, net=net, tn=turn))
        print(f"   {pname:<26}{s['cagr']:>8.1f}%{s['sharpe']:>8.2f}"
              f"{s['dd']:>8.1f}%{e.mean():>9.2f}{tpy:>8.1f}x")
    bs = stats(bh) if ppy == 365 else _stats(bh, ppy)
    print(f"   {'buy&hold':<26}{bs['cagr']:>8.1f}%{bs['sharpe']:>8.2f}"
          f"{bs['dd']:>8.1f}%{1.0:>9.2f}{0.0:>8.1f}x")

    print(f"\n3. NETTO DI IMPOSTE")
    print(f"   {'previsore':<26}{'IRR 33%':>10}{'IRR 52%':>10}{'vs B&H':>10}")
    rf0 = rf if rf is not None else pd.Series(0.0, index=ret.index)
    con = first_of_month(ret.index) if ppy > 12 else None
    bb = simulate_pac(bh, CGT_SHARES, rf=rf0, periods_per_year=ppy, contrib_on=con)
    print(f"   {'buy&hold':<26}{bb.irr_annual:>9.1f}%{'—':>10}{0.0:>9.1f}%")
    for r in rows:
        idx = r["net"].index
        r33 = simulate_pac(r["net"], CGT_SHARES, rf=rf0.reindex(idx).fillna(0),
                           realize_frac=r["tn"].reindex(idx).clip(0, 1),
                           periods_per_year=ppy,
                           contrib_on=first_of_month(idx) if ppy > 12 else None)
        r52 = simulate_pac(r["net"], TRADING_52, rf=rf0.reindex(idx).fillna(0),
                           realize_frac=r["tn"].reindex(idx).clip(0, 1),
                           periods_per_year=ppy,
                           contrib_on=first_of_month(idx) if ppy > 12 else None)
        r["irr33"], r["irr52"] = r33.irr_annual, r52.irr_annual
        r["vs"] = r33.irr_annual - bb.irr_annual
        print(f"   {r['pred']:<26}{r33.irr_annual:>9.1f}%{r52.irr_annual:>9.1f}%"
              f"{r['vs']:>9.1f}%")
    return rows, q


def _stats(net, ppy):
    net = net.dropna()
    yrs = len(net) / ppy
    curve = (1 + net).cumprod()
    tot = float(curve.iloc[-1])
    return dict(cagr=(tot ** (1 / yrs) - 1) * 100 if tot > 0 else -100.0,
                sharpe=float(net.mean() / net.std() * np.sqrt(ppy))
                if net.std() > 0 else np.nan,
                dd=float((curve / curve.cummax() - 1).min()) * 100)


def main():
    allrows, allq = [], []

    ffd = dataio.ff_factors_daily()
    crsp = (ffd["Mkt-RF"] + ffd["RF"]).dropna()
    r, q = run_market("Indice CRSP 1926-2026", crsp, 252, C.COST_ROUND_TRIP,
                      ffd["RF"].reindex(crsp.index).fillna(0.0))
    allrows += r; allq.append(q.assign(mkt="CRSP"))

    qq = load("QQQ", "1day").close.pct_change().dropna()
    r, q = run_market("QQQ 2006-2026", qq, 252, C.COST_ROUND_TRIP)
    allrows += r; allq.append(q.assign(mkt="QQQ"))

    px = pd.DataFrame({s: load_crypto(s).close for s in SYMS
                       if (Path(__file__).resolve().parents[2] / "data" /
                           f"okx_{s}_1d.csv").exists()}).dropna()
    cry = px.pct_change().mean(axis=1).dropna()
    r, q = run_market("7 cripto equipesate 2020-2026", cry, 365, COST_CRYPTO)
    allrows += r; allq.append(q.assign(mkt="cripto"))

    # -------------------------------------------------- sintesi
    print(f"\n{'='*84}\nSINTESI\n{'='*84}")
    qa = pd.concat(allq)
    print("\nLa catena di Markov batte i previsori banali?")
    for mkt, g in qa.groupby("mkt"):
        mk = g[g["name"].str.contains("Markov")]["r2"].max()
        rv = g[~g["name"].str.contains("Markov")]["r2"].max()
        print(f"  {mkt:<10} R2 Markov {mk:.3f} contro banale {rv:.3f}  "
              f"-> {'SI' if mk > rv else 'NO'} ({mk-rv:+.3f})")

    d = pd.DataFrame([{k: v for k, v in r.items() if k not in ("net", "tn")}
                      for r in allrows])
    print(f"\nVol-targeting: quante configurazioni battono il buy&hold "
          f"netto imposte? {int((d['vs'] > 0).sum())}/{len(d)}")
    best = d.sort_values("vs", ascending=False).iloc[0]
    print(f"Migliore: {best['pred']} su {best['mkt']}  "
          f"{best['vs']:+.2f} punti (Sharpe {best['sharpe']:.2f})")

    bn = next(r for r in allrows
              if r["pred"] == best["pred"] and r["mkt"] == best["mkt"])
    n_cum = lab.n_trials_so_far()
    nev = len(allrows)
    sh = pd.Series([r["sharpe"] for r in allrows]).dropna()
    ppy = 365 if best["mkt"].startswith("7 cripto") else 252
    vsr = float((sh / np.sqrt(ppy)).var(ddof=1)) if len(sh) > 2 else None
    dd = lab.deflated_sharpe(bn["net"], n_cum + nev, var_sr=vsr, round_id=ROUND)
    print(f"DSR su {n_cum+nev} tentativi: {dd['dsr']:.3f} "
          f"(Sharpe {dd['sr_period']*np.sqrt(ppy):.3f} contro soglia "
          f"{dd['sr0']*np.sqrt(ppy):.3f})")
    print(f"  -> {'PROMUOVIBILE' if dd['dsr'] > 0.95 else 'NON promuovibile'}")

    lab.log_trials([dict(round=ROUND, hypothesis="H26 vol-targeting su ampiezza",
                         config=f"{r['mkt']}|{r['pred']}", window="varie",
                         sharpe=r["sharpe"], irr=r["irr33"], bh_irr="",
                         excess=r["vs"], n_obs=len(r["net"]),
                         note=f"lev={r['lev']:.2f},turn={r['turn']:.1f}x")
                    for r in allrows])
    d.to_csv(OUT / "round25_voltarget.csv", index=False)
    qa.to_csv(OUT / "round25_volforecast.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

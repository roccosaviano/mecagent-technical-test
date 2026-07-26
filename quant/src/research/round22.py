"""Giro 22 — La struttura trovata al giro 21 e' direzionale o e' volatilita'?

Il giro 21 ha trovato dipendenza condizionale reale: 74 test significativi su
108, Cramer V fino a 3,54 volte il nullo. La domanda che decide tutto e' COSA
sia quella dipendenza, perche' due cose molto diverse la producono:

  VOLATILITA' (clustering)  giorni agitati seguono giorni agitati. E' il fatto
      piu' robusto della finanza empirica, non e' in discussione, e NON si
      traduce in un segnale direzionale: sapere che domani si muovera' molto
      non dice da che parte.

  DIREZIONE  il segno del rendimento futuro dipende dal contesto passato.
      Questa sarebbe sfruttabile.

Il segnale nella tabella del giro 21 c'e' gia': con L=2 (etichette di sola
direzione) la significativita' cade agli orizzonti lunghi, mentre con L=3 e
L=5 (etichette che codificano anche l'ampiezza) resta. Qui lo verifico
separando le due componenti in modo esplicito, e poi costruisco comunque il
segnale 'prendo la P maggiore' e lo porto fino all'IRR netta.
"""
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES, TRADING_52, first_of_month
from research import lab
from research.round15 import load, evaluate
from research.round21 import labelise, contexts, MIN_COUNT

ROUND = 22
OUT = Path(__file__).resolve().parents[2] / "out"


def cramer(a, b):
    tab = pd.crosstab(a, b)
    tab = tab[tab.sum(axis=1) >= MIN_COUNT]
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return np.nan, np.nan
    t = tab.to_numpy()
    chi = st.chi2_contingency(t)
    v = np.sqrt(chi.statistic / (t.sum() * (min(t.shape) - 1)))
    return float(v), float(chi.pvalue)


def decompose(ret, k=2, h=1, n=5):
    """Separa la dipendenza sul SEGNO da quella sull'AMPIEZZA."""
    lab_now, edges = labelise(ret, n)
    fwd = ret.rolling(h).sum().shift(-h)
    ctx, ok = contexts(lab_now, k)
    m = ok & np.isfinite(fwd.to_numpy())
    f = fwd.to_numpy()[m]
    c = ctx[m]
    sign = (f > 0).astype(int)
    mag = pd.qcut(np.abs(f), 4, labels=False, duplicates="drop")
    full, _ = labelise(pd.Series(f), n, edges * h)
    v_full, p_full = cramer(c, full)
    v_sign, p_sign = cramer(c, sign)
    v_mag, p_mag = cramer(c, mag)
    return dict(k=k, h=h, n=n, v_full=v_full, p_full=p_full,
                v_sign=v_sign, p_sign=p_sign, v_mag=v_mag, p_mag=p_mag,
                obs=len(f))


def ensemble_signal(ret, train_end, depths=(1, 2, 3), horizons=(1, 2, 3, 5),
                    nlabels=(2, 3, 5), min_count=MIN_COUNT):
    """Segnale 'prendo la P maggiore' su tutto l'ensemble.

    Le probabilita' sono stimate SOLO sui dati fino a train_end. A ogni t si
    guarda, per ogni (k, h, L), la probabilita' condizionata che il rendimento
    futuro sia positivo; si prende la mappa con la deviazione dal 50% piu'
    marcata e si va long se e' sopra, flat se e' sotto.
    """
    tr = ret.iloc[:train_end]
    models = []
    for k, h, n in product(depths, horizons, nlabels):
        lab_now, edges = labelise(tr, n)
        fwd_tr = tr.rolling(h).sum().shift(-h)
        ctx_tr, ok = contexts(lab_now, k)
        m = ok & np.isfinite(fwd_tr.to_numpy())
        up = (fwd_tr.to_numpy()[m] > 0).astype(int)
        dfm = pd.DataFrame({"ctx": ctx_tr[m], "up": up})
        g = dfm.groupby("ctx")["up"].agg(["mean", "count"])
        g = g[g["count"] >= min_count]
        if g.empty:
            continue
        models.append((k, h, n, edges, g["mean"].to_dict()))

    # applicazione su tutta la serie (le probabilita' restano quelle di train)
    full_ctx = {}
    for k, h, n, edges, table in models:
        lab_all = np.digitize(ret.to_numpy(), edges)
        ctx_all, ok = contexts(lab_all, k)
        full_ctx[(k, h, n)] = (ctx_all, ok, table)

    pos = np.zeros(len(ret))
    for i in range(len(ret)):
        best_dev, best_p = 0.0, 0.5
        for key, (ctx_all, ok, table) in full_ctx.items():
            if not ok[i]:
                continue
            p = table.get(int(ctx_all[i]))
            if p is None:
                continue
            dev = abs(p - 0.5)
            if dev > best_dev:
                best_dev, best_p = dev, p
        pos[i] = 1.0 if best_p > 0.5 else 0.0
    return pd.Series(pos, index=ret.index).shift(1).fillna(0.0), len(models)


def main():
    ffd = dataio.ff_factors_daily()
    ret = (ffd["Mkt-RF"] + ffd["RF"]).dropna()
    print(f"Indice CRSP giornaliero, {len(ret)} osservazioni "
          f"{ret.index[0].date()} -> {ret.index[-1].date()}")

    # ---------------------------------------------------- 1. decomposizione
    print(f"\n{'='*84}")
    print("1. LA DIPENDENZA E' SUL SEGNO O SULL'AMPIEZZA?")
    print("=" * 84)
    print(f"{'k':>3}{'h':>3}{'L':>3}{'V completo':>13}{'p':>8}"
          f"{'V solo segno':>15}{'p':>8}{'V ampiezza':>13}{'p':>8}")
    rows = []
    for k, h, n in product((1, 2, 3), (1, 2, 3, 5), (5,)):
        d = decompose(ret, k, h, n)
        rows.append(d)
        print(f"{k:>3}{h:>3}{n:>3}{d['v_full']:>13.4f}{d['p_full']:>8.3f}"
              f"{d['v_sign']:>15.4f}{d['p_sign']:>8.3f}"
              f"{d['v_mag']:>13.4f}{d['p_mag']:>8.3f}")
    dd = pd.DataFrame(rows)
    print(f"\n  V medio: completo {dd['v_full'].mean():.4f}, "
          f"solo segno {dd['v_sign'].mean():.4f}, "
          f"ampiezza {dd['v_mag'].mean():.4f}")
    print(f"  Test significativi al 5%: completo "
          f"{int((dd['p_full']<0.05).sum())}/{len(dd)}, "
          f"segno {int((dd['p_sign']<0.05).sum())}/{len(dd)}, "
          f"ampiezza {int((dd['p_mag']<0.05).sum())}/{len(dd)}")

    # ---------------------------------------------------- 2. il segnale
    print(f"\n{'='*84}")
    print("2. IL SEGNALE 'PRENDO LA P MAGGIORE', STIMATO SOLO SUL PASSATO")
    print("=" * 84)
    split = len(ret) // 2
    pos, nmod = ensemble_signal(ret, split)
    print(f"  Mappe nell'ensemble: {nmod}  "
          f"(probabilita' stimate su {split} osservazioni fino al "
          f"{ret.index[split].date()})")
    oos = ret.iloc[split:]
    p_oos = pos.iloc[split:]
    m = evaluate(oos, p_oos, 252)
    bh = evaluate(oos, pd.Series(1.0, index=oos.index), 252)
    print(f"\n  Fuori campione {oos.index[0].date()} -> {oos.index[-1].date()}")
    print(f"  {'':<22}{'CAGR':>9}{'Sharpe':>9}{'DD':>9}{'op/an':>8}{'%mkt':>7}")
    print(f"  {'ensemble max-P':<22}{m['cagr']:>8.2f}%{m['sharpe']:>9.2f}"
          f"{m['dd']:>8.1f}%{m['trades']:>8.1f}{m['inmkt']:>6.0f}%")
    print(f"  {'buy&hold':<22}{bh['cagr']:>8.2f}%{bh['sharpe']:>9.2f}"
          f"{bh['dd']:>8.1f}%{0.0:>8.1f}{100.0:>6.0f}%")
    print(f"  {'differenza':<22}{m['cagr']-bh['cagr']:>+8.2f}%"
          f"{m['sharpe']-bh['sharpe']:>+9.2f}")

    # accuratezza direzionale del segnale
    hit = float((p_oos.shift(-1).fillna(0) > 0).eq(oos > 0).mean())
    print(f"\n  Accuratezza direzionale del segnale: {hit*100:.2f}%")
    print(f"  Quota di giorni positivi nel campione: {(oos>0).mean()*100:.2f}%")

    # ---------------------------------------------------- 3. netto imposte
    rf = ffd["RF"].reindex(oos.index).fillna(0.0)
    com = first_of_month(oos.index)
    net = p_oos * oos - p_oos.diff().abs().fillna(p_oos.abs()) * C.COST_ROUND_TRIP / 2
    r33 = simulate_pac(net, CGT_SHARES, in_market=p_oos, rf=rf,
                       periods_per_year=252, contrib_on=com)
    r52 = simulate_pac(net, TRADING_52, in_market=p_oos, rf=rf,
                       periods_per_year=252, contrib_on=com)
    b = simulate_pac(oos, CGT_SHARES, rf=rf, periods_per_year=252, contrib_on=com)
    print(f"\n{'='*84}")
    print("3. PAC 500 EUR/MESE, NETTO DI IMPOSTE IRLANDESI")
    print("=" * 84)
    print(f"  {'ensemble, CGT 33%':<30}{r33.irr_annual:>8.2f}%  "
          f"({r33.irr_annual-b.irr_annual:+.2f} vs buy&hold)")
    print(f"  {'ensemble, riqualificato 52%':<30}{r52.irr_annual:>8.2f}%  "
          f"({r52.irr_annual-b.irr_annual:+.2f} vs buy&hold)")
    print(f"  {'buy&hold':<30}{b.irr_annual:>8.2f}%")

    n_cum = lab.n_trials_so_far()
    d = lab.deflated_sharpe(net, n_cum + nmod, rf=rf, round_id=ROUND)
    print(f"\n  DSR su {n_cum + nmod} tentativi (registro + {nmod} mappe): "
          f"{d['dsr']:.3f}")

    lab.log_trials([dict(round=ROUND, hypothesis="H23 ensemble Markov max-P",
                         config=f"{nmod} mappe, split meta campione",
                         window=f"{oos.index[0].date()}/{oos.index[-1].date()}",
                         sharpe=m["sharpe"], irr=r33.irr_annual,
                         bh_irr=b.irr_annual,
                         excess=r33.irr_annual - b.irr_annual, n_obs=len(oos),
                         note=f"hit={hit:.4f}")])
    dd.to_csv(OUT / "round22_decomposition.csv", index=False)
    print(f"\nTentativi cumulati: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

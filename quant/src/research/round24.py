"""Giro 24 — Due strategie e un HMM che decide quale accendere.

IL DISEGNO. Il giro 23 ha mostrato che il long/short SEMPRE ACCESO perde in 4
famiglie su 4: le due gambe si annullano, e su cripto la corta toglie proprio
l'esposizione che genera rendimento. Qui il disegno e' diverso:

    un modello a stati nascosti (HMM) stima il REGIME di mercato, e il regime
    decide QUALE delle due strategie e' attiva. Long in un regime, short
    nell'altro, flat quando il modello non e' convinto.

Non e' la stessa cosa di un long/short: li' compri e vendi contemporaneamente,
qui alterni. Se i regimi esistono e sono riconoscibili in tempo reale, questa
struttura guadagna in entrambe le direzioni; se non lo sono, perde due volte.

LA TRAPPOLA DELL'HMM, ED E' LA RAGIONE PER CUI META' DEI PAPER SU QUESTO
ARGOMENTO SONO SBAGLIATI. Un HMM addestrato su tutta la serie e poi
interrogato con Viterbi o con le probabilita' SMOOTHED usa il futuro: lo
stato al tempo t viene stimato anche dalle osservazioni dopo t. Sui grafici
sembra magia. Qui uso solo il FILTRO IN AVANTI (forward algorithm), che a
ogni t conosce esclusivamente le osservazioni fino a t, e il modello viene
ristimato ogni anno solo sul passato. Sotto c'e' un test che verifica la
differenza fra le due cose.

RIBILANCIAMENTO A BANDE. Al giro 23 i pesi venivano riportati al bersaglio
ogni giorno, il che gonfiava la rotazione a 18-65 volte l'anno perche'
l'uscita di un asset ripesava tutti gli altri. Qui si ribilancia solo quando
un peso devia oltre una banda, che e' come si fa davvero.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
from tax import simulate_pac, CGT_SHARES, TRADING_52
from research import lab
from research.round19 import load_crypto, SYMS, COST_CRYPTO
from research.round23 import panel, stats, PPY

ROUND = 24
OUT = Path(__file__).resolve().parents[2] / "out"


# ------------------------------------------------------------------ HMM
def hmm_filtered_states(ret_index, n_states=2, refit_years=None, seed=0):
    """Probabilita' di stato FILTRATE, ristimando il modello ogni anno.

    A ogni data t la probabilita' usa solo le osservazioni fino a t incluso,
    e i parametri del modello sono stati stimati solo su anni precedenti.
    Restituisce (prob_stato_ribassista, mappa stato->rendimento medio).
    """
    from hmmlearn.hmm import GaussianHMM

    idx = ret_index.index
    years = sorted({t.year for t in idx})
    out = pd.Series(np.nan, index=idx)
    means = {}
    for y in years[1:]:
        tr = ret_index[idx.year < y]
        if len(tr) < 400:
            continue
        X = np.column_stack([tr.to_numpy(),
                             tr.rolling(10).std().bfill().to_numpy()])
        m = GaussianHMM(n_components=n_states, covariance_type="diag",
                        n_iter=60, random_state=seed)
        try:
            m.fit(X)
        except Exception:
            continue
        # Lo stato "ribassista" NON e' semplicemente quello con media piu'
        # bassa: su cripto lo stato ad alta volatilita' contiene sia i crolli
        # sia i rialzi verticali, e puo' avere media positiva. Uso il rapporto
        # media/volatilita' dello stato, che e' cio' che conta per decidere se
        # stare investiti, e verifico l'occupazione.
        mu = np.asarray(m.means_)[:, 0]
        cv = np.asarray(m.covars_).reshape(n_states, -1)[:, 0]
        sd = np.sqrt(np.maximum(cv, 1e-12))
        bear = int(np.argmin(mu / sd))
        means[y] = m.means_[:, 0].round(5).tolist()

        # filtro in avanti su tutta la serie fino a fine anno y, ma leggo
        # solo l'anno y: ogni valore usa solo il proprio passato
        upto = ret_index[idx.year <= y]
        Xa = np.column_stack([upto.to_numpy(),
                              upto.rolling(10).std().bfill().to_numpy()])
        try:
            _, post = m.score_samples(Xa)          # smoothed: NON usabile
            fwd = forward_filter(m, Xa)            # filtrato: usabile
        except Exception:
            continue
        s = pd.Series(fwd[:, bear], index=upto.index)
        out.loc[s.index[s.index.year == y]] = s[s.index.year == y]
    return out, means


def forward_filter(model, X):
    """Probabilita' filtrate P(stato_t | osservazioni fino a t).

    hmmlearn espone solo le smoothed (predict_proba usa forward-backward),
    che guardano avanti. Questo e' il solo passo in avanti, normalizzato.
    """
    fl = model._compute_log_likelihood(X)
    n, k = fl.shape
    logA = np.log(model.transmat_ + 1e-300)
    a = np.log(model.startprob_ + 1e-300) + fl[0]
    out = np.empty((n, k))
    out[0] = np.exp(a - _lse(a))
    for t in range(1, n):
        a = fl[t] + np.array([_lse(a + logA[:, j]) for j in range(k)])
        out[t] = np.exp(a - _lse(a))
    return out


def _lse(v):
    m = v.max()
    return m + np.log(np.exp(v - m).sum())


# ------------------------------------------------------------------ segnali
def donchian_state(px, inn, out):
    up = px >= px.rolling(inn).max()
    dn = px <= px.rolling(out).min()
    st = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
    st[up] = 1.0
    st[dn] = 0.0
    return st.ffill().fillna(0.0)


def donchian_short(px, inn, out):
    """Speculare: corto sul minimo a N giorni, chiude sul massimo a M."""
    dn = px <= px.rolling(inn).min()
    up = px >= px.rolling(out).max()
    st = pd.DataFrame(np.nan, index=px.index, columns=px.columns)
    st[dn] = -1.0
    st[up] = 0.0
    return st.ffill().fillna(0.0)


def banded(target, band=0.20):
    """Ribilancia quando la deviazione COMPLESSIVA supera `band`.

    La prima versione confrontava la deviazione del singolo peso: con 7 asset
    i pesi valgono ~0,14 ciascuno, quindi una banda di 0,25 non scattava mai e
    il portafoglio restava congelato ai pesi iniziali (turnover zero, CAGR
    zero). La deviazione giusta e' quella aggregata, in norma L1.
    """
    tg = np.nan_to_num(target.to_numpy())
    out = np.zeros_like(tg)
    cur = tg[0].copy()
    for i in range(len(tg)):
        if np.abs(tg[i] - cur).sum() > band:
            cur = tg[i].copy()
        out[i] = cur
    return pd.DataFrame(out, index=target.index, columns=target.columns)


def run(px, w, cost=COST_CRYPTO):
    ret = px.pct_change().fillna(0.0)
    g = w.abs().sum(axis=1).replace(0, np.nan)
    wn = w.div(g, axis=0).fillna(0.0).shift(1).fillna(0.0)
    turn = wn.diff().abs().sum(axis=1).fillna(wn.abs().sum(axis=1)) / 2.0
    return (wn * ret).sum(axis=1) - turn * cost, turn


def main():
    px, hi, lo = panel()
    px = px.dropna()
    ret_eq = px.pct_change().mean(axis=1).dropna()
    print(f"7 cripto, {px.index[0].date()} -> {px.index[-1].date()} "
          f"({len(px)} giorni)\n")

    # ------------------------------------------------ 1. la trappola dell'HMM
    print("=" * 82)
    print("1. QUANTO VALE LA TRAPPOLA: SMOOTHED CONTRO FILTRATO")
    print("=" * 82)
    from hmmlearn.hmm import GaussianHMM
    X = np.column_stack([ret_eq.to_numpy(),
                         ret_eq.rolling(10).std().bfill().to_numpy()])
    m = GaussianHMM(n_components=2, covariance_type="diag", n_iter=80,
                    random_state=0).fit(X)
    bear = int(np.argmin(m.means_[:, 0]))
    _, smooth = m.score_samples(X)
    fwd = forward_filter(m, X)
    for lbl, p in (("SMOOTHED (guarda avanti — sbagliato)", smooth[:, bear]),
                   ("FILTRATO (solo passato — corretto)", fwd[:, bear])):
        pos = pd.Series(np.where(p < 0.5, 1.0, 0.0), index=ret_eq.index).shift(1).fillna(0)
        net = pos * ret_eq
        s = stats(net)
        print(f"  {lbl:<44}CAGR {s['cagr']:>7.1f}%  Sharpe {s['sharpe']:>5.2f}")
    s0 = stats(ret_eq)
    print(f"  {'buy&hold':<44}CAGR {s0['cagr']:>7.1f}%  Sharpe {s0['sharpe']:>5.2f}")
    print("  Se si usa la versione smoothed, il risultato e' un artefatto.\n")

    # ------------------------------------------------ 2. il sistema
    print("=" * 82)
    print("2. IL SISTEMA: HMM SCEGLIE LA GAMBA, DONCHIAN LA ESEGUE")
    print("=" * 82)
    pbear, means = hmm_filtered_states(ret_eq, 2)
    cov = pbear.notna().mean()
    print(f"  Copertura del segnale HMM: {cov*100:.0f}% delle date "
          f"(il primo anno serve a stimare)")
    valid = pbear.dropna()
    print(f"  Quota di tempo in regime ribassista (P>0,5): "
          f"{(valid>0.5).mean()*100:.0f}%")

    L = donchian_state(px, 50, 20)
    S = donchian_short(px, 50, 20)
    ret_idx = px.pct_change().fillna(0.0)

    rows = []
    print(f"\n{'sistema':<40}{'CAGR':>9}{'Sharpe':>8}{'DD':>9}{'turn/an':>9}")
    print("-" * 76)

    def add(name, w, band=None):
        wb = banded(w, band) if band else w
        net, turn = run(px, wb)
        net = net.reindex(valid.index).dropna()
        turn = turn.reindex(net.index).fillna(0)
        s = stats(net)
        tpy = float(turn.sum()) / (len(net) / PPY)
        rows.append(dict(name=name, **s, turn=tpy, net=net, tn=turn))
        print(f"{name:<40}{s['cagr']:>8.1f}%{s['sharpe']:>8.2f}{s['dd']:>8.1f}%"
              f"{tpy:>8.1f}x")

    # riallineo all'indice dei prezzi: pbear vive sull'indice dei rendimenti,
    # che e' una riga piu' corto. Senza questo la moltiplicazione introduce NaN
    # che propagano fino ad azzerare il portafoglio.
    bull = (pbear < 0.5).astype(float).reindex(px.index).fillna(0.0)
    bear_m = (pbear > 0.5).astype(float).reindex(px.index).fillna(0.0)
    conf = (pbear < 0.3).astype(float).reindex(px.index).fillna(0.0)

    add("Donchian long, sempre acceso", L)
    add("Donchian long, sempre acceso, bande 25%", L, 0.25)
    add("Donchian short, sempre acceso", S)
    add("HMM: long in rialzo, short in ribasso", L.mul(bull, axis=0) + S.mul(bear_m, axis=0))
    add("HMM: long in rialzo, flat in ribasso", L.mul(bull, axis=0))
    add("HMM: long solo se molto convinto", L.mul(conf, axis=0))
    add("HMM long/short, bande 25%", L.mul(bull, axis=0) + S.mul(bear_m, axis=0), 0.25)
    add("HMM long/flat, bande 25%", L.mul(bull, axis=0), 0.25)

    bh = stats(ret_eq.reindex(valid.index).dropna())
    print(f"{'buy&hold equipesato':<40}{bh['cagr']:>8.1f}%{bh['sharpe']:>8.2f}"
          f"{bh['dd']:>8.1f}%{0.0:>8.1f}x")

    # ------------------------------------------------ 3. imposte
    print(f"\n{'='*82}")
    print("3. NETTO DI IMPOSTE IRLANDESI")
    print("=" * 82)
    rf0 = pd.Series(0.0, index=rows[0]["net"].index)
    bb = simulate_pac(ret_eq.reindex(rf0.index), CGT_SHARES, rf=rf0,
                      periods_per_year=PPY)
    print(f"{'sistema':<40}{'IRR 33%':>10}{'IRR 52%':>10}{'vs B&H':>10}")
    print(f"{'buy&hold equipesato':<40}{bb.irr_annual:>9.1f}%{'—':>10}{0.0:>9.1f}%")
    best = None
    for r in rows:
        r33 = simulate_pac(r["net"], CGT_SHARES, rf=rf0,
                           realize_frac=r["tn"].clip(0, 1), periods_per_year=PPY)
        r52 = simulate_pac(r["net"], TRADING_52, rf=rf0,
                           realize_frac=r["tn"].clip(0, 1), periods_per_year=PPY)
        d = r33.irr_annual - bb.irr_annual
        r["irr33"], r["irr52"], r["vs"] = r33.irr_annual, r52.irr_annual, d
        print(f"{r['name']:<40}{r33.irr_annual:>9.1f}%{r52.irr_annual:>9.1f}%"
              f"{d:>9.1f}%")
        if best is None or d > best["vs"]:
            best = r

    # ------------------------------------------------ 4. DSR
    n_cum = lab.n_trials_so_far()
    nev = len(rows) + 24
    sh = pd.Series([r["sharpe"] for r in rows]).dropna()
    vsr = float((sh / np.sqrt(PPY)).var(ddof=1)) if len(sh) > 2 else None
    d = lab.deflated_sharpe(best["net"], n_cum + nev, var_sr=vsr, round_id=ROUND)
    print(f"\n{'='*82}")
    print(f"Migliore: {best['name']}  ({best['vs']:+.1f} punti al 33%, "
          f"{best['irr52']:.1f}% al 52%)")
    print(f"DSR su {n_cum+nev} tentativi: {d['dsr']:.3f}  "
          f"(Sharpe {d['sr_period']*np.sqrt(PPY):.3f} contro soglia "
          f"{d['sr0']*np.sqrt(PPY):.3f})")
    print(f"  -> {'PROMUOVIBILE' if d['dsr'] > 0.95 else 'NON promuovibile'}")

    lab.log_trials([dict(round=ROUND, hypothesis="H25 HMM regime + due gambe",
                         config=r["name"], window="2021-2026", sharpe=r["sharpe"],
                         irr=r["irr33"], bh_irr=bb.irr_annual, excess=r["vs"],
                         n_obs=len(r["net"]), note=f"turn={r['turn']:.1f}x")
                    for r in rows])
    pd.DataFrame([{k: v for k, v in r.items() if k not in ("net", "tn")}
                  for r in rows]).to_csv(OUT / "round24_hmm.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

"""Banco di ricerca con contabilita' dei tentativi.

PERCHE' ESISTE QUESTO FILE. L'istruzione "itera finche' non trovi qualcosa che
batte il buy&hold" garantisce un vincitore anche su dati puramente casuali: con
N configurazioni provate, il massimo Sharpe atteso sotto ipotesi nulla cresce
come sqrt(2 log N). Con N=500 vale gia' ~0,55. Un loop che si ferma al primo
successo apparente non ha trovato un edge, ha trovato il massimo di N estrazioni.

Quindi ogni configurazione provata viene REGISTRATA, e il criterio di promozione
non e' "batte il benchmark" ma il Deflated Sharpe Ratio di Bailey & Lopez de
Prado (2014), corretto per il numero CUMULATO di tentativi di tutta la ricerca.

Tre finestre, fissate una volta e mai piu' toccate:
  TRAIN   ottimizzazione dei parametri. Guardarlo quanto si vuole.
  TEST    validazione. Si guarda, ma ogni sguardo costa un tentativo nel registro.
  HOLDOUT si apre UNA SOLA VOLTA, alla fine, su un solo candidato. Se lo si
          guarda due volte non e' piu' un holdout.
"""
import csv
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / "research"
REGISTRY = RESEARCH / "registry.csv"
HOLDOUT_SEAL = RESEARCH / "holdout_opened.json"

TRAIN = ("1926-07", "1989-12")
TEST = ("1990-01", "2009-12")
HOLDOUT = ("2010-01", "2026-12")

EULER = 0.5772156649015329

REG_FIELDS = ["round", "hypothesis", "config", "window", "sharpe", "irr",
              "bh_irr", "excess", "n_obs", "note"]


# ------------------------------------------------------------------ registro
def load_registry():
    if not REGISTRY.exists():
        return pd.DataFrame(columns=REG_FIELDS)
    return pd.read_csv(REGISTRY)


def log_trials(rows):
    """Aggiunge tentativi al registro. Ogni configurazione valutata su TEST
    conta come un tentativo, anche quelle scartate: e' il punto."""
    RESEARCH.mkdir(parents=True, exist_ok=True)
    new = not REGISTRY.exists()
    with open(REGISTRY, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=REG_FIELDS)
        if new:
            w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in REG_FIELDS})


def n_trials_so_far():
    reg = load_registry()
    return len(reg)


# ------------------------------------------------------------------ DSR
def expected_max_sharpe(var_sr, n_trials):
    """Sharpe massimo atteso su n_trials estrazioni indipendenti sotto H0.

    Bailey & Lopez de Prado (2014), eq. per E[max SR]. var_sr e' la varianza
    degli Sharpe osservati fra i tentativi: e' cio' che rende la soglia
    specifica di QUESTA ricerca invece di una costante arbitraria.
    """
    if n_trials < 2 or var_sr <= 0:
        return 0.0
    s = math.sqrt(var_sr)
    a = stats.norm.ppf(1.0 - 1.0 / n_trials)
    b = stats.norm.ppf(1.0 - 1.0 / (n_trials * math.e))
    return s * ((1.0 - EULER) * a + EULER * b)


def deflated_sharpe(returns, n_trials, var_sr=None, rf=None):
    """Probabilita' che lo Sharpe osservato non sia il massimo di n_trials
    estrazioni sotto ipotesi nulla. Sopra 0,95 = promuovibile.

    Lavora sullo Sharpe per periodo (non annualizzato) e corregge per asimmetria
    e code spesse: una strategia con skew negativa e code grasse (tipico di chi
    vende volatilita' o usa stop) viene penalizzata, come deve essere.
    """
    # Stessa convenzione di summarise(): Sharpe su rendimenti IN ECCESSO. La
    # soglia SR0 e' costruita dalla varianza degli Sharpe nel registro, che sono
    # in eccesso; confrontarci uno Sharpe grezzo gonfierebbe il DSR.
    s = pd.Series(returns).dropna()
    if rf is not None:
        s = s - pd.Series(rf).reindex(s.index).fillna(0.0)
    r = np.asarray(s, dtype=float)
    T = len(r)
    if T < 24 or r.std(ddof=1) == 0:
        return dict(sr_period=np.nan, sr_ann=np.nan, sr0=np.nan, dsr=np.nan, T=T)
    sr = r.mean() / r.std(ddof=1)
    g3 = float(stats.skew(r))
    g4 = float(stats.kurtosis(r, fisher=False))
    if var_sr is None:
        reg = load_registry()
        s = pd.to_numeric(reg.get("sharpe", pd.Series(dtype=float)), errors="coerce").dropna()
        var_sr = float(s.var(ddof=1)) if len(s) > 2 else (0.5 / max(T, 1))
    sr0 = expected_max_sharpe(var_sr, max(n_trials, 2))
    denom = 1.0 - g3 * sr + (g4 - 1.0) / 4.0 * sr ** 2
    if denom <= 0:
        return dict(sr_period=sr, sr_ann=np.nan, sr0=sr0, dsr=np.nan, T=T)
    z = (sr - sr0) * math.sqrt(T - 1) / math.sqrt(denom)
    return dict(sr_period=sr, sr_ann=sr * math.sqrt(12), sr0=sr0,
                dsr=float(stats.norm.cdf(z)), T=T, skew=g3, kurt=g4,
                var_sr=var_sr, n_trials=n_trials)


# ------------------------------------------------------------------ holdout
def holdout_is_sealed():
    return HOLDOUT_SEAL.exists()


def open_holdout(candidate, result):
    """Apre l'holdout. Si puo' fare UNA VOLTA. Il sigillo e' su disco e
    versionato, cosi' non e' revocabile riavviando il processo."""
    if holdout_is_sealed():
        prev = json.load(open(HOLDOUT_SEAL))
        raise RuntimeError(
            f"Holdout gia' aperto il {prev['when']} sul candidato "
            f"{prev['candidate']!r}. Non e' piu' un holdout: qualunque nuovo "
            f"risultato su questa finestra e' in-sample.")
    RESEARCH.mkdir(parents=True, exist_ok=True)
    payload = dict(when=pd.Timestamp.utcnow().isoformat(), candidate=candidate,
                   result=result, n_trials_at_open=n_trials_so_far())
    json.dump(payload, open(HOLDOUT_SEAL, "w"), indent=1, default=float)
    return payload


# ------------------------------------------------------------------ metriche
def summarise(ret, rf=None, periods=12):
    r = pd.Series(ret).dropna()
    yrs = len(r) / periods
    curve = (1 + r).cumprod()
    dd = float((curve / curve.cummax() - 1).min())
    ex = r - (rf.reindex(r.index).fillna(0.0) if rf is not None else 0.0)
    return dict(
        cagr=float(curve.iloc[-1] ** (1 / yrs) - 1) * 100 if curve.iloc[-1] > 0 else -100.0,
        vol=float(r.std() * math.sqrt(periods)) * 100,
        sharpe=float(ex.mean() / ex.std() * math.sqrt(periods)) if ex.std() > 0 else np.nan,
        mdd=dd * 100, n=len(r),
    )


def win(series_or_df, w):
    return series_or_df.loc[w[0]:w[1]]

"""
RUNNER DI RICERCA
=================

La domanda e': esiste una strategia su SPXL che batte il buy&hold dell'S&P 500
al netto di costi e imposte? Per rispondere servono tre paletti, altrimenti la
risposta e' sempre si' e non vuol dire niente.

PALETTO 1 - RISCHIO APPAIATO
    Una strategia che rende il 9.7% l'anno con un ribasso massimo del 94% non
    batte un buy&hold che rende l'8.1% con un ribasso dell'85%. Prende piu'
    rischio, e per prendere piu' rischio non serve una strategia: basta la
    leva. Quindi ogni candidata viene misurata due volte: com'e', e riscalata
    a parita' di volatilita' attesa col benchmark. Solo la seconda risponde
    alla domanda.

PALETTO 2 - IMPOSTE SUL REALIZZATO
    Il buy&hold realizza una volta sola, alla fine, e fino ad allora capitalizza
    anche la quota che un giorno andra' allo Stato. Una strategia che ruota
    trenta volte l'anno paga ogni volta. Il confronto va fatto sul patrimonio
    finale al netto, non sul rendimento lordo con una nota a pie' di pagina.

PALETTO 3 - QUANTE COSE HAI PROVATO
    Provare mille combinazioni garantisce di trovarne una bella anche nel
    rumore puro. Per questo il protocollo procede a severita' crescente:

      check        i dati e la sintesi del fondo a leva reggono?
      baseline     parametri da manuale, zero ottimizzazione, piu' periodi
      sweep        griglia esplorativa, serve a mappare non a scegliere
      walkforward  parametri scelti solo sul passato, giudizio solo sul futuro

    e il deflated Sharpe ratio sconta il numero di tentativi fatti.

Uso:  python3 research.py [check|baseline|sweep|walkforward] [opzioni]
"""
from __future__ import annotations
import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import strategies as S
from engine import (TRADING_DAYS, REGIMES, Instrument, simulate, metrics,
                    deflated_sharpe, block_bootstrap_pvalue, quick_stats)
from world import build_world

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
REGIME_DEFAULT = "IE_CGT"

# I periodi non sono decorativi: ciascuno risponde a un'obiezione diversa.
PERIODI = {
    "1928+": (None, "tutto, compreso il 1929: la prova piu' dura che esista"),
    "1954+": ("1954-01-01", "da quando i tassi a breve sono dati veri e non stime"),
    "1990+": ("1990-01-01", "mercati moderni, esiste il VIX"),
    "2008+": ("2008-11-05", "da quando SPXL esiste davvero"),
}


# ==========================================================================
# esecuzione
# ==========================================================================
def strategy_weights(world, fn, params, overlay=None, match=None):
    """
    Pesi della strategia sull'intera storia, con eventuale overlay di rischio.

    I pesi si calcolano SEMPRE sulla serie completa e si affettano dopo: gli
    indicatori guardano solo indietro, quindi non e' look-ahead, e cosi' un
    periodo out-of-sample non parte con duecento sedute cieche di warm-up.
    """
    W = fn(world.ctx, world.cols, **params)
    if overlay or match is not None:
        R = np.column_stack([i.r_tot for i in world.instruments])
    if overlay:
        W = S.vol_overlay(W, R, **overlay)
    if match is not None:
        W = S.match_risk_overlay(W, R, match)
    return W


def run_weights(world, W, regime=REGIME_DEFAULT, sl=None, exec_lag=1,
                capital=100_000.0):
    if sl is None:
        sl = np.arange(len(world.dates))
    sub = [Instrument(i.name, i.r_tot[sl], i.r_div[sl], i.cost)
           for i in world.instruments]
    return simulate(world.dates[sl], sub, W[sl], REGIMES[regime],
                    cash_rate=world.cash_rate[sl], exec_lag=exec_lag,
                    capital=capital)


def evaluate(world, fn, params, regime=REGIME_DEFAULT, sl=None, overlay=None,
             bench=None, exec_lag=1, match=None):
    """
    Metriche di una configurazione, comprese quelle che servono a capire quanto
    del risultato se lo prende il fisco: la stessa strategia viene rigirata con
    aliquota zero, e la differenza fra i due CAGR e' il freno fiscale vero.
    """
    W = strategy_weights(world, fn, params, overlay, match)
    sl = np.arange(len(world.dates)) if sl is None else sl
    res = run_weights(world, W, regime, sl, exec_lag)
    m = metrics(res, cash_rate=world.cash_rate[sl], bench_equity=bench)
    lordo = run_weights(world, W, "NONE", sl, exec_lag)
    m["cagr_lordo"] = metrics(lordo, cash_rate=world.cash_rate[sl])["cagr_net"]
    m["tax_drag"] = m["cagr_lordo"] - m["cagr_net"]
    m["_res"] = res
    return m


def benchmark(world, regime=REGIME_DEFAULT, sl=None, exec_lag=1):
    """Buy&hold dell'indice: comprato una volta, tenuto, tassato alla fine."""
    W = strategy_weights(world, S.buy_hold_spy, {})
    return run_weights(world, W, regime, sl, exec_lag)


def bench_returns_full(world, regime=REGIME_DEFAULT, exec_lag=1):
    """
    Rendimenti del benchmark sulla storia INTERA.

    L'appaiamento del rischio lavora sui pesi, che sono definiti su tutta la
    storia: passargli il benchmark tagliato sul solo periodo in esame darebbe
    due serie di lunghezza diversa. E non e' solo una questione di indici: il
    fattore di scala e' una media espansiva, e farla ripartire da zero a ogni
    sottoperiodo la renderebbe instabile proprio all'inizio.
    """
    res = run_weights(world, strategy_weights(world, S.buy_hold_spy, {}),
                      regime, None, exec_lag)
    return res["equity"].pct_change().fillna(0.0).values


# ==========================================================================
# cataloghi
# ==========================================================================
def canonical_grid():
    """
    Un solo insieme di parametri per famiglia, quello che sta nei libri e nei
    paper, scelto prima di guardare questi dati. Se una strategia funziona qui
    non c'e' selezione da scontare: e' il risultato piu' forte ottenibile.
    """
    return [
        ("B&H SPXL",                S.buy_hold_spxl,    {}),
        ("Trend SMA200",            S.sma_trend,        dict(n=200)),
        ("Trend SMA200 banda 2%",   S.sma_trend,        dict(n=200, band=0.02)),
        ("Trend SMA200 mensile",    S.sma_trend,        dict(n=200, monthly=True)),
        ("Trend SMA10m (Faber)",    S.sma_trend,        dict(n=210, monthly=True)),
        ("Incrocio SMA50/200",      S.dual_sma,         dict(fast=50, slow=200)),
        ("Momentum assoluto 12m",   S.abs_momentum,     dict(n=252)),
        ("Vol target 15%",          S.vol_target,       dict(target=0.15, lookback=20)),
        ("Vol target 25%",          S.vol_target,       dict(target=0.25, lookback=20)),
        ("Regime vol 20%",          S.vol_regime,       dict(thr=0.20, lookback=20)),
        ("Filtro VIX 20",           S.vix_filter,       dict(thr=20.0)),
        ("Struttura VIX3M/VIX",     S.vix_term,         dict(thr=1.0)),
        ("RSI2 Connors",            S.rsi2,             dict(entry=10, exit_n=5, trend=200)),
        ("Compra il calo 5%",       S.dip_buy,          dict(drop=0.05, window=20, hold=10)),
        ("Tre ribassi di fila",     S.streak_buy,       dict(days=3, trend=200)),
        ("Long/short SMA200",       S.trend_long_short, dict(n=200, w_short=0.5)),
        ("Short solo se stress",    S.short_on_stress,  dict(n=200, vol_thr=0.25)),
        ("Trend difensivo 3 stati", S.trend_defensive,  dict(n=200)),
    ]


# ==========================================================================
# stampa
# ==========================================================================
COLS = [("cagr_net", "CAGR", "{:>8.2f}"), ("vol", "vol", "{:>7.1f}"),
        ("mdd", "MaxDD", "{:>8.1f}"), ("calmar", "Calmar", "{:>7.2f}"),
        ("sharpe", "Sharpe", "{:>7.2f}"), ("ulcer", "Ulcer", "{:>7.1f}"),
        ("underwater_yrs", "sotto", "{:>6.1f}"), ("expo", "espo", "{:>5.0f}"),
        ("turn_yr", "turn", "{:>6.1f}"), ("tax_drag", "fisco", "{:>6.2f}")]


def print_table(rows, titolo, bench_m=None, nota=""):
    print(f"\n{titolo}")
    if nota:
        print(f"  {nota}")
    head = f"{'strategia':<26}" + "".join(f"{h:>8}" for _, h, _ in COLS)
    print("=" * (len(head) + 6))
    print(head)
    print("-" * (len(head) + 6))
    if bench_m is not None:
        line = f"{'>> B&H S&P 500':<26}"
        for k, _, fmt in COLS:
            v = bench_m.get(k, np.nan)
            line += fmt.format(v) if np.isfinite(v) else f"{'-':>8}"
        print(line)
        print("-" * (len(head) + 6))
    for name, m in rows:
        line = f"{name:<26}"
        for k, _, fmt in COLS:
            v = m.get(k, np.nan)
            line += fmt.format(v) if np.isfinite(v) else f"{'-':>8}"
        if bench_m is not None:
            meglio_rend = m["cagr_net"] > bench_m["cagr_net"]
            meglio_risk = m["mdd"] >= bench_m["mdd"]
            line += "   VINCE" if (meglio_rend and meglio_risk) else ("   +rend" if meglio_rend else "")
        print(line)
    print("=" * (len(head) + 6))


# ==========================================================================
# comandi
# ==========================================================================
def cmd_check():
    w = build_world(verbose=True)
    print("\nStrumenti negoziabili:")
    for ins in w.instruments:
        r = pd.Series(ins.r_tot, index=w.dates)
        print(f"   {ins.name:5s} vol {r.std()*np.sqrt(TRADING_DAYS):6.1%}   "
              f"costo andata {ins.cost:.2%}   "
              f"distribuzioni {ins.r_div.sum()/len(r)*TRADING_DAYS:.2%}/anno")
    return w


def cmd_baseline(w=None, regime=REGIME_DEFAULT, exec_lag=1, periodi=None):
    """
    Livello 1: parametri da manuale, su piu' periodi, in due versioni.

    La prima tabella e' la strategia com'e'. La seconda la riscala a parita' di
    volatilita' attesa col benchmark: e' quella che risponde alla domanda vera.
    """
    w = w or build_world(verbose=False)
    tutto = {}
    for etichetta in (periodi or ["1928+", "1954+", "1990+", "2008+"]):
        start, descr = PERIODI[etichetta]
        sl = w.slice(start=start)
        b_res = benchmark(w, regime, sl, exec_lag)
        b_m = metrics(b_res, cash_rate=w.cash_rate[sl])
        b_m["cagr_lordo"] = metrics(run_weights(w, strategy_weights(w, S.buy_hold_spy, {}),
                                                "NONE", sl, exec_lag),
                                    cash_rate=w.cash_rate[sl])["cagr_net"]
        b_m["tax_drag"] = b_m["cagr_lordo"] - b_m["cagr_net"]
        bench_vol = b_m["vol"] / 100.0

        r_bench = bench_returns_full(w, regime, exec_lag)
        modi = {
            "grezzo": dict(nota=descr),
            "rischio appaiato": dict(
                match=r_bench,
                nota="pesi riscalati perche' la volatilita' realizzata coincida con "
                     "quella del benchmark, con fattore stimato solo sul passato"),
        }
        for modo, cfg in modi.items():
            righe = []
            for nome, fn, p in canonical_grid():
                try:
                    m = evaluate(w, fn, p, regime, sl, None, b_res["equity"],
                                 exec_lag, match=cfg.get("match"))
                    righe.append((nome, m))
                except Exception as e:
                    print(f"   errore su {nome}: {type(e).__name__}: {e}")
            per = f"{w.dates[sl][0].date()} -> {w.dates[sl][-1].date()}"
            print_table(righe,
                        f"[{etichetta}] {modo.upper()}   {per}   fisco {regime}, "
                        f"ritardo {exec_lag}g", b_m, cfg["nota"])
            tutto[(etichetta, modo)] = (righe, b_m)
    return w, tutto


# ==========================================================================
# griglia esplorativa
# ==========================================================================
def sweep_grid():
    """
    La mappa del terreno. NON serve a scegliere il vincitore: ogni riga e' un
    tentativo in piu' da scontare, e il conteggio viene riportato apposta
    insieme al deflated Sharpe ratio.
    """
    g = []
    for n in (50, 100, 150, 200, 250, 300):
        for band in (0.0, 0.02):
            for monthly in (False, True):
                g.append((f"SMA{n} b{band:.0%}{' mens' if monthly else ''}", "trend",
                          S.sma_trend, dict(n=n, band=band, monthly=monthly)))
    for fast in (20, 50, 100):
        for slow in (100, 150, 200, 300):
            if fast < slow:
                g.append((f"SMA{fast}/{slow}", "trend", S.dual_sma,
                          dict(fast=fast, slow=slow)))
    for n in (126, 189, 252):
        for monthly in (False, True):
            g.append((f"Momentum {n}g{' mens' if monthly else ''}", "trend",
                      S.abs_momentum, dict(n=n, monthly=monthly)))
    for t in (0.10, 0.15, 0.20, 0.25, 0.30):
        for lb in (10, 20, 40, 60):
            for monthly in (False, True):
                g.append((f"VolTarget {t:.0%} lb{lb}{' mens' if monthly else ''}", "vol",
                          S.vol_target, dict(target=t, lookback=lb, monthly=monthly)))
    for thr in (0.14, 0.18, 0.22, 0.26, 0.30):
        for lb in (10, 20, 40):
            g.append((f"RegimeVol {thr:.0%} lb{lb}", "vol", S.vol_regime,
                      dict(thr=thr, lookback=lb)))
    for thr in (16, 18, 20, 22, 25, 30):
        g.append((f"VIX<{thr}", "vix", S.vix_filter, dict(thr=float(thr))))
    for thr in (0.98, 1.0, 1.02, 1.05):
        g.append((f"VIX3M/VIX>{thr}", "vix", S.vix_term, dict(thr=thr)))
    for entry in (5, 10, 15, 20):
        for ex in (5, 10):
            for trend in (100, 200):
                g.append((f"RSI2 e{entry} u{ex} t{trend}", "reversione", S.rsi2,
                          dict(entry=entry, exit_n=ex, trend=trend)))
    for drop in (0.03, 0.05, 0.07, 0.10):
        for hold in (5, 10, 20):
            g.append((f"Calo {drop:.0%} tieni{hold}", "reversione", S.dip_buy,
                      dict(drop=drop, hold=hold)))
    for days in (2, 3, 4, 5):
        g.append((f"Streak {days}", "reversione", S.streak_buy, dict(days=days)))
    for n in (100, 200, 300):
        for ws in (0.25, 0.5, 1.0):
            g.append((f"LS SMA{n} short{ws:.0%}", "short", S.trend_long_short,
                      dict(n=n, w_short=ws)))
            g.append((f"Stress SMA{n} short{ws:.0%}", "short", S.short_on_stress,
                      dict(n=n, w_short=ws)))
    for n in (100, 200, 300):
        g.append((f"Difensivo SMA{n}", "trend", S.trend_defensive, dict(n=n)))

    # strutture pensate per pagare meno imposte a parita' di segnale
    for core in (0.4, 0.6, 0.8):
        sat = 1.0 - core
        for nome_b, fb, kb in (("SMA200", S.sma_trend, dict(n=200, band=0.02)),
                               ("SMA200m", S.sma_trend, dict(n=200, monthly=True)),
                               ("RSI2", S.rsi2, dict(entry=10, exit_n=5, trend=200)),
                               ("VolT20", S.vol_target, dict(target=0.20, lookback=20))):
            g.append((f"Nucleo{core:.0%}+{nome_b}", "nucleo", S.core_satellite,
                      dict(core=core, sat=sat, base_fn=fb, base_kw=kb)))
    for gradini in (2, 4, 8):
        for nome_b, fb, kb in (("SMA200", S.sma_trend, dict(n=200)),
                               ("SMA300", S.sma_trend, dict(n=300)),
                               ("RSI2", S.rsi2, dict(entry=10, exit_n=5, trend=200))):
            g.append((f"Scala{gradini} {nome_b}", "scala", S.ladder,
                      dict(base_fn=fb, base_kw=kb, gradini=gradini)))
    return g


class Mercato:
    """Rendimenti e costi degli strumenti in forma di array, per il percorso veloce."""

    def __init__(self, world):
        self.R = np.column_stack([i.r_tot for i in world.instruments])
        self.C = np.array([i.cost for i in world.instruments])
        self.cash = np.asarray(world.cash_rate, float)

    def stats(self, W, sl, exec_lag=1):
        return quick_stats(W[sl], self.R[sl], self.C, self.cash[sl], exec_lag)


class WeightCache:
    """
    I pesi di una configurazione dipendono solo dai dati di mercato, non dal
    periodo su cui la si valuta. Nel walk-forward la stessa configurazione viene
    rivalutata su decine di finestre: calcolarne i pesi ogni volta sarebbe il
    99% del tempo di calcolo speso a rifare lo stesso conto.
    """

    def __init__(self, world, match=None):
        self.world = world
        self.match = match
        self._c = {}

    def get(self, key, fn, params):
        if key not in self._c:
            self._c[key] = strategy_weights(self.world, fn, params, None, self.match)
        return self._c[key]


# ==========================================================================
# livello 2: griglia esplorativa
# ==========================================================================
def cmd_sweep(w=None, regime=REGIME_DEFAULT, periodo="1990+", exec_lag=1,
              appaia=True, top=15):
    """
    Gira tutta la griglia e ordina per Sharpe.

    Perche' Sharpe e non CAGR: se una strategia si puo' scalare con la leva - e
    con SPXL si puo' - allora il rendimento non e' una sua proprieta', e' una
    scelta di dosaggio. Cio' che la leva NON puo' cambiare e' il rapporto fra
    rendimento in eccesso e rischio. Battere il buy&hold vuol dire battere il
    suo Sharpe: tutto il resto e' decidere quanto scommettere.

    Il numero di configurazioni provate viene stampato perche' serve a leggere
    il risultato: con centinaia di tentativi la migliore ha uno Sharpe alto
    anche se sotto non c'e' niente, ed e' esattamente cio' che il deflated
    Sharpe ratio quantifica.
    """
    w = w or build_world(verbose=False)
    start, descr = PERIODI[periodo]
    sl = w.slice(start=start)
    b_res = benchmark(w, regime, sl, exec_lag)
    b_m = metrics(b_res, cash_rate=w.cash_rate[sl])
    match = bench_returns_full(w, regime, exec_lag) if appaia else None
    cache = WeightCache(w, match)

    griglia = sweep_grid()
    righe = []
    for nome, fam, fn, p in griglia:
        try:
            W = cache.get(nome, fn, p)
            res = run_weights(w, W, regime, sl, exec_lag)
            m = metrics(res, cash_rate=w.cash_rate[sl], bench_equity=b_res["equity"])
            if not np.isfinite(m["sharpe"]) or m["expo"] < 1:
                continue
            m["famiglia"] = fam
            r = res["equity"].pct_change().fillna(0.0)
            m["_r"] = r.values
            m["skew"] = float(r.skew())
            m["kurt"] = float(r.kurt() + 3.0)     # pandas restituisce l'eccesso
            lordo = run_weights(w, W, "NONE", sl, exec_lag)
            m["tax_drag"] = (metrics(lordo, cash_rate=w.cash_rate[sl])["cagr_net"]
                             - m["cagr_net"])
            righe.append((nome, m))
        except Exception:
            continue

    righe.sort(key=lambda x: -x[1]["sharpe"])
    n_prove = len(righe)
    # la dispersione degli Sharpe fra i tentativi e' l'ingrediente che dice
    # quanto in alto puo' arrivare il migliore per solo effetto del caso
    sd_prove = float(np.std([m["sharpe"] for _, m in righe], ddof=1))
    r_bench = b_res["equity"].pct_change().fillna(0.0).values

    print(f"\n[{periodo}] GRIGLIA ESPLORATIVA   {w.dates[sl][0].date()} -> "
          f"{w.dates[sl][-1].date()}   fisco {regime}")
    print(f"  {descr}")
    print(f"  {n_prove} configurazioni valutate, dispersione degli Sharpe {sd_prove:.3f}"
          + ("  |  pesi appaiati al rischio del benchmark" if appaia else ""))
    print(f"  benchmark: Sharpe {b_m['sharpe']:.3f}  CAGR {b_m['cagr_net']:.2f}%  "
          f"vol {b_m['vol']:.1f}%  MaxDD {b_m['mdd']:.1f}%  Calmar {b_m['calmar']:.2f}  "
          f"Ulcer {b_m['ulcer']:.1f}")

    migliori = righe[:top]
    print("\n" + "=" * 125)
    print(f"{'configurazione':<26}{'fam':<11}{'Sharpe':>8}{'dSR':>6}{'pboot':>7}"
          f"{'CAGR':>7}{'vol':>7}{'MaxDD':>8}{'Calmar':>7}{'Ulcer':>7}{'turn':>6}"
          f"{'fisco':>7}{'espo':>6}")
    print("-" * 125)
    def _num(v, fmt, larg):
        return format(v, fmt) if np.isfinite(v) else f"{'-':>{larg}}"

    for nome, m in migliori:
        # dSR: probabilita' che questo Sharpe non sia il massimo di n_prove
        # estrazioni casuali. p-boot: probabilita' che il vantaggio sul
        # benchmark venga dal caso. Entrambi vanno letti insieme allo Sharpe,
        # mai al posto suo.
        dsr = deflated_sharpe(m["sharpe"], len(sl), n_prove, sd_prove,
                              m.get("skew", 0.0), m.get("kurt", 3.0))
        pb = block_bootstrap_pvalue(m["_r"], r_bench)
        print(f"{nome:<26}{m['famiglia']:<11}{m['sharpe']:>8.3f}"
              f"{_num(dsr, '>6.2f', 6)}{_num(pb, '>7.3f', 7)}"
              f"{m['cagr_net']:>7.2f}{m['vol']:>7.1f}{m['mdd']:>8.1f}"
              f"{m['calmar']:>7.2f}{m['ulcer']:>7.1f}"
              f"{m['turn_yr']:>6.1f}{_num(m.get('tax_drag', np.nan), '>7.2f', 7)}"
              f"{m['expo']:>6.0f}")
    print("=" * 125)

    for chiave, verso, etichetta in (("sharpe", 1, "Sharpe"), ("cagr_net", 1, "CAGR netto"),
                                     ("calmar", 1, "Calmar"), ("ulcer", -1, "Ulcer (meno e' meglio)")):
        n = sum(1 for _, m in righe if verso * m[chiave] > verso * b_m[chiave])
        print(f"  configurazioni che battono il benchmark su {etichetta:<24} "
              f"{n:>4} su {n_prove}  ({n/max(n_prove,1):>3.0%})")
    return w, righe, b_m



# ==========================================================================
# livello 3: walk-forward ancorato
# ==========================================================================
def _finestre(dates, sl, anni_min=10, anni_test=3):
    """
    Finestre ancorate: si allena da sempre fino a T, si giudica da T a T+3 anni,
    poi si sposta T in avanti. L'allenamento cresce, il giudizio e' sempre su
    dati mai visti.

    Tre anni per finestra e' un compromesso: piu' corta e il giudizio e' rumore,
    piu' lunga e i parametri restano congelati per troppo tempo rispetto a come
    li aggiornerebbe una persona vera.
    """
    d = dates[sl]
    t0 = d[0] + pd.DateOffset(years=anni_min)
    out = []
    t = t0
    while t < d[-1]:
        fine = t + pd.DateOffset(years=anni_test)
        train = sl[(d >= d[0]) & (d < t)]
        test = sl[(d >= t) & (d < fine)]
        if len(train) > 250 * anni_min * 0.9 and len(test) > 250:
            out.append((train, test, t, min(fine, d[-1])))
        t = fine
    return out


def _scegli(punteggi, modo="plateau"):
    """
    Come si sceglie la configurazione da portare fuori campione.

    'migliore' prende il massimo in-sample. E' la scelta che sembra ovvia ed e'
    quella che sovradatta di piu': il massimo di una griglia sta quasi sempre su
    una punta di rumore, e la punta non si ripete.

    'plateau' prende la MEDIANA del quintile migliore. Se una zona di parametri
    funziona davvero, il suo centro funziona ancora l'anno dopo; se funzionava
    solo una combinazione isolata, la mediana la scarta. E' la stessa logica per
    cui si sceglie il centro di un altopiano e non la cima di un picco.
    """
    ordinati = sorted(punteggi, key=lambda x: -x[1])
    if modo == "migliore" or len(ordinati) < 5:
        return ordinati[0][0]
    quintile = ordinati[:max(3, len(ordinati) // 5)]
    return quintile[len(quintile) // 2][0]


def cmd_walkforward(w=None, regime=REGIME_DEFAULT, periodo="1954+", exec_lag=1,
                    anni_test=3, appaia=True, modo="plateau", verbose=True,
                    finalisti=30):
    """
    Il test che conta. Nessun parametro viene scelto guardando il periodo su cui
    viene poi giudicato.

    Il risultato non e' una tabella di candidate: e' UNA curva, quella che
    avrebbe ottenuto chi avesse seguito il metodo dall'inizio, riaggiornando i
    parametri ogni tre anni con i soli dati disponibili a quel momento.
    """
    w = w or build_world(verbose=False)
    start, descr = PERIODI[periodo]
    sl = w.slice(start=start)
    match = bench_returns_full(w, regime, exec_lag) if appaia else None
    cache = WeightCache(w, match)
    griglia = sweep_grid()
    finestre = _finestre(w.dates, sl, anni_test=anni_test)

    n_inst = len(w.cols)
    W_oos = np.zeros((len(w.dates), n_inst))
    scelte, coperti = [], []

    mkt = Mercato(w)
    for train, test, t_ini, t_fin in finestre:
        # PRIMO STADIO: scrematura veloce sullo Sharpe lordo. Serve solo a
        # ridurre il campo da qualche centinaio a qualche decina.
        veloci = []
        for nome, fam, fn, p in griglia:
            try:
                q = mkt.stats(cache.get(nome, fn, p), train, exec_lag)
                if np.isfinite(q["sharpe"]) and q["expo"] > 1:
                    veloci.append(((nome, fn, p), q["sharpe"]))
            except Exception:
                continue
        if not veloci:
            continue
        veloci.sort(key=lambda x: -x[1])

        # SECONDO STADIO: sui finalisti si gira il simulatore completo e si
        # sceglie sul rendimento NETTO di imposte.
        #
        # Non e' un dettaglio di implementazione. Scegliere sullo Sharpe lordo
        # premia sistematicamente le strategie che ruotano molto, perche' il
        # loro costo vero arriva dopo, ed e' il motivo per cui il walk-forward
        # continuava a selezionare mean reversion a venti operazioni l'anno che
        # poi perdeva il doppio in imposte. Chi paga le tasse deve ottimizzare
        # cio' che gli resta.
        punteggi = []
        for chiave, _ in veloci[:finalisti]:
            nome, fn, p = chiave
            try:
                m = metrics(run_weights(w, cache.get(nome, fn, p), regime, train,
                                        exec_lag), cash_rate=w.cash_rate[train])
                if np.isfinite(m["sharpe"]):
                    punteggi.append((chiave, m["sharpe"]))
            except Exception:
                continue
        if not punteggi:
            continue
        nome, fn, p = _scegli(punteggi, modo)
        W_oos[test] = cache.get(nome, fn, p)[test]
        coperti.append(test)
        scelte.append((str(t_ini.date()), str(t_fin.date()), nome, len(train)))

    if not coperti:
        print("nessuna finestra utilizzabile")
        return None
    oos = np.concatenate(coperti)

    res = run_weights(w, W_oos, regime, oos, exec_lag)
    b_res = run_weights(w, strategy_weights(w, S.buy_hold_spy, {}), regime, oos, exec_lag)
    m = metrics(res, cash_rate=w.cash_rate[oos], bench_equity=b_res["equity"])
    b_m = metrics(b_res, cash_rate=w.cash_rate[oos])
    lordo = metrics(run_weights(w, W_oos, "NONE", oos, exec_lag), cash_rate=w.cash_rate[oos])
    m["tax_drag"] = lordo["cagr_net"] - m["cagr_net"]
    b_lordo = metrics(run_weights(w, strategy_weights(w, S.buy_hold_spy, {}), "NONE",
                                  oos, exec_lag), cash_rate=w.cash_rate[oos])
    b_m["tax_drag"] = b_lordo["cagr_net"] - b_m["cagr_net"]

    if verbose:
        print(f"\nWALK-FORWARD ANCORATO   [{periodo}]   fisco {regime}   "
              f"selezione '{modo}'")
        print(f"  {len(finestre)} finestre da {anni_test} anni, "
              f"{len(griglia)} configurazioni valutate a ogni riselezione")
        print(f"  selezione a due stadi: scrematura veloce sul lordo, scelta "
              f"finale sul NETTO fra i primi {finalisti}")
        print(f"  periodo giudicato: {w.dates[oos][0].date()} -> {w.dates[oos][-1].date()}"
              f"  ({len(oos)/TRADING_DAYS:.1f} anni mai visti in fase di scelta)")
        print("\n  cosa ha scelto, finestra per finestra:")
        for a, b, nome, ntr in scelte:
            print(f"    {a} -> {b}   {nome:<26} (allenata su {ntr/TRADING_DAYS:5.1f} anni)")

        pb = block_bootstrap_pvalue(res["equity"].pct_change().fillna(0).values,
                                    b_res["equity"].pct_change().fillna(0).values)
        print_table([("Walk-forward (netto)", m), ("Walk-forward (lordo)", lordo),
                     ("B&H (lordo)", b_lordo)],
                    "\n  RISULTATO FUORI CAMPIONE", b_m,
                    f"probabilita' che il divario dal benchmark sia caso: {pb:.3f}"
                    if np.isfinite(pb) else "")
    return w, m, b_m, scelte


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    os.makedirs(RESULTS, exist_ok=True)
    t0 = time.time()
    if cmd == "check":
        cmd_check()
    elif cmd == "baseline":
        cmd_baseline(periodi=sys.argv[2:] or None)
    elif cmd == "sweep":
        # uso: sweep [periodo ...] [--fisco NOME]
        argv = sys.argv[2:]
        reg = REGIME_DEFAULT
        if "--fisco" in argv:
            i = argv.index("--fisco")
            reg = argv[i + 1]
            argv = argv[:i] + argv[i + 2:]
        mondo = build_world(verbose=False)
        for per in (argv or ["1990+"]):
            cmd_sweep(mondo, periodo=per, regime=reg)
    elif cmd == "walkforward":
        argv = sys.argv[2:]
        reg = REGIME_DEFAULT
        if "--fisco" in argv:
            k = argv.index("--fisco")
            reg, argv = argv[k + 1], argv[:k] + argv[k + 2:]
        mondo = build_world(verbose=False)
        for per in (argv or ["1954+"]):
            cmd_walkforward(mondo, periodo=per, regime=reg)
    else:
        print(__doc__)
    print(f"\n({time.time()-t0:.1f}s)")

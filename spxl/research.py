"""
RUNNER DI RICERCA
=================

Protocollo, in ordine di severita' crescente:

  1. PARAMETRI DA MANUALE, ZERO OTTIMIZZAZIONE
     Media a 200 giorni, vol target 15%, momentum a 12 mesi. Sono i numeri che
     stanno nei paper e nei libri da vent'anni, scelti prima di guardare questi
     dati. Se una strategia funziona qui, non c'e' selezione da correggere:
     e' il risultato piu' forte ottenibile e va guardato per primo.

  2. WALK-FORWARD ANCORATO
     I parametri si scelgono solo sul passato disponibile a quella data e si
     giudicano sul futuro mai visto. I segmenti out-of-sample si concatenano in
     un unico track record: e' l'approssimazione piu' onesta di "cosa avrei
     ottenuto avendola davvero seguita".

  3. CORREZIONE PER TENTATIVI MULTIPLI
     Provare mille combinazioni garantisce di trovarne una bella anche nel
     rumore. Il deflated Sharpe ratio stima quanto della bellezza e' dovuta al
     numero di tentativi, e il bootstrap a blocchi dice se il vantaggio sul
     benchmark sopravvive al caso.

Uso:
    python3 research.py check        verifica dati e sintesi
    python3 research.py baseline     confronto con parametri da manuale
    python3 research.py sweep        griglia completa (solo esplorativa)
    python3 research.py walkforward  il test che conta
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
from engine import (TRADING_DAYS, REGIMES, simulate, metrics,
                    deflated_sharpe, block_bootstrap_pvalue)
from world import build_world

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, "results")
REGIME_DEFAULT = "IE_CGT"


# ==========================================================================
# esecuzione di una singola configurazione
# ==========================================================================
def run(world, fn, params, regime=REGIME_DEFAULT, sl=None, exec_lag=1,
        capital=100_000.0):
    """Calcola i pesi sulla storia intera e simula sulla sola fetta richiesta."""
    W = fn(world.ctx, world.cols, **params)
    if sl is None:
        sl = np.arange(len(world.dates))
    dates = world.dates[sl]
    insts = world.instruments
    sub = []
    from engine import Instrument
    for ins in insts:
        sub.append(Instrument(ins.name, ins.r_tot[sl], ins.r_div[sl], ins.cost))
    res = simulate(dates, sub, W[sl], REGIMES[regime],
                   cash_rate=world.cash_rate[sl], exec_lag=exec_lag,
                   capital=capital)
    return res


def evaluate(world, fn, params, regime=REGIME_DEFAULT, sl=None, bench=None,
             exec_lag=1):
    res = run(world, fn, params, regime, sl, exec_lag)
    sl = np.arange(len(world.dates)) if sl is None else sl
    m = metrics(res, cash_rate=world.cash_rate[sl], bench_equity=bench)
    m["_res"] = res
    return m


def benchmark(world, regime=REGIME_DEFAULT, sl=None):
    """Buy&hold dell'indice: comprato una volta, tenuto, tassato alla fine."""
    return run(world, S.buy_hold_spy, {}, regime, sl)


# ==========================================================================
# griglia delle strategie
# ==========================================================================
def canonical_grid():
    """
    Un solo insieme di parametri per famiglia, quello canonico della
    letteratura. Nessuna ottimizzazione: e' il livello 1 del protocollo.
    """
    return [
        ("B&H SPY (benchmark)",     S.buy_hold_spy,   {}),
        ("B&H SPXL",                S.buy_hold_spxl,  {}),
        ("Trend SMA200",            S.sma_trend,      dict(n=200)),
        ("Trend SMA200 banda 2%",   S.sma_trend,      dict(n=200, band=0.02)),
        ("Trend SMA200 mensile",    S.sma_trend,      dict(n=200, monthly=True)),
        ("Trend SMA10m (Faber)",    S.sma_trend,      dict(n=210, monthly=True)),
        ("Incrocio SMA50/200",      S.dual_sma,       dict(fast=50, slow=200)),
        ("Momentum assoluto 12m",   S.abs_momentum,   dict(n=252)),
        ("Vol target 15%",          S.vol_target,     dict(target=0.15, lookback=20)),
        ("Vol target 15% mensile",  S.vol_target,     dict(target=0.15, lookback=20, monthly=True)),
        ("Regime vol 20%",          S.vol_regime,     dict(thr=0.20, lookback=20)),
        ("Filtro VIX 20",           S.vix_filter,     dict(thr=20.0)),
        ("Struttura VIX3M/VIX",     S.vix_term,       dict(thr=1.0)),
        ("RSI2 Connors",            S.rsi2,           dict(entry=10, exit_n=5, trend=200)),
        ("Compra il calo 5%",       S.dip_buy,        dict(drop=0.05, window=20, hold=10)),
        ("Tre ribassi di fila",     S.streak_buy,     dict(days=3, trend=200)),
        ("Long/short SMA200",       S.trend_long_short, dict(n=200, w_short=0.5)),
        ("Short solo se stress",    S.short_on_stress,  dict(n=200, vol_thr=0.25)),
        ("Trend difensivo 3 stati", S.trend_defensive,  dict(n=200)),
    ]


def sweep_grid():
    """
    La griglia esplorativa. Serve a mappare il terreno, non a scegliere il
    vincitore: ogni riga qui dentro e' un tentativo in piu' da scontare nel
    deflated Sharpe ratio, e il conteggio viene riportato apposta.
    """
    g = []
    for n in (50, 100, 150, 200, 250, 300):
        for band in (0.0, 0.01, 0.02, 0.03):
            for monthly in (False, True):
                g.append((f"SMA{n} b{band:.0%}{' m' if monthly else ''}",
                          S.sma_trend, dict(n=n, band=band, monthly=monthly)))
    for fast in (20, 50, 100):
        for slow in (100, 150, 200, 300):
            if fast < slow:
                g.append((f"SMA{fast}/{slow}", S.dual_sma, dict(fast=fast, slow=slow)))
    for n in (126, 189, 252):
        g.append((f"Momentum {n}g", S.abs_momentum, dict(n=n)))
    for t in (0.10, 0.12, 0.15, 0.18, 0.22, 0.26):
        for lb in (10, 20, 40, 60):
            for monthly in (False, True):
                g.append((f"VolTarget {t:.0%} lb{lb}{' m' if monthly else ''}",
                          S.vol_target, dict(target=t, lookback=lb, monthly=monthly)))
    for thr in (0.14, 0.18, 0.22, 0.26, 0.30):
        for lb in (10, 20, 40):
            g.append((f"RegimeVol {thr:.0%} lb{lb}", S.vol_regime, dict(thr=thr, lookback=lb)))
    for thr in (16, 18, 20, 22, 25, 30):
        g.append((f"VIX<{thr}", S.vix_filter, dict(thr=float(thr))))
    for thr in (0.98, 1.0, 1.02, 1.05):
        g.append((f"VIX3M/VIX>{thr}", S.vix_term, dict(thr=thr)))
    for entry in (5, 10, 15, 20):
        for ex in (5, 10):
            for trend in (100, 200):
                g.append((f"RSI2 e{entry} x{ex} t{trend}", S.rsi2,
                          dict(entry=entry, exit_n=ex, trend=trend)))
    for drop in (0.03, 0.05, 0.07, 0.10):
        for hold in (5, 10, 20):
            g.append((f"Calo {drop:.0%} hold{hold}", S.dip_buy, dict(drop=drop, hold=hold)))
    for days in (2, 3, 4, 5):
        g.append((f"Streak {days}", S.streak_buy, dict(days=days)))
    for n in (100, 200, 300):
        for ws in (0.25, 0.5, 1.0):
            g.append((f"LS SMA{n} short{ws:.0%}", S.trend_long_short, dict(n=n, w_short=ws)))
            g.append((f"Stress SMA{n} short{ws:.0%}", S.short_on_stress,
                      dict(n=n, w_short=ws)))
    for n in (100, 200, 300):
        g.append((f"Difensivo SMA{n}", S.trend_defensive, dict(n=n)))
    return g


# ==========================================================================
# stampa
# ==========================================================================
COLS = [("cagr_net", "CAGR", "{:>7.2f}"), ("vol", "vol", "{:>6.1f}"),
        ("mdd", "MaxDD", "{:>7.1f}"), ("calmar", "Calmar", "{:>7.2f}"),
        ("sharpe", "Sharpe", "{:>7.2f}"), ("ulcer", "Ulcer", "{:>6.1f}"),
        ("underwater_yrs", "sott.an", "{:>7.1f}"), ("expo", "espo%", "{:>6.0f}"),
        ("turn_yr", "turn/an", "{:>7.1f}"), ("tax_drag", "fisco", "{:>6.2f}")]


def print_table(rows, titolo, bench_row=None):
    print(f"\n{titolo}")
    head = f"{'strategia':<28}" + "".join(f"{h:>8}" for _, h, _ in COLS)
    print("=" * len(head))
    print(head)
    print("-" * len(head))
    for name, m in rows:
        line = f"{name:<28}"
        for k, _, fmt in COLS:
            v = m.get(k, np.nan)
            line += fmt.format(v) if np.isfinite(v) else f"{'-':>7}"
        if bench_row is not None and m is not bench_row:
            line += "  <<<" if m["cagr_net"] > bench_row["cagr_net"] else ""
        print(line)
    print("=" * len(head))


# ==========================================================================
# comandi
# ==========================================================================
def cmd_check():
    w = build_world(verbose=True)
    print("\nStrumenti:")
    for ins in w.instruments:
        r = pd.Series(ins.r_tot, index=w.dates)
        nz = r[r != 0]
        print(f"   {ins.name:5s} {len(nz):6d} sedute non nulle, "
              f"da {nz.index[0].date()}  vol {r.std()*np.sqrt(252):.1%}  costo {ins.cost:.2%}")
    return w


def cmd_baseline(w=None, regime=REGIME_DEFAULT, start=None, exec_lag=1):
    w = w or build_world(verbose=False)
    sl = w.slice(start=start)
    bench_res = benchmark(w, regime, sl)
    bench_m = metrics(bench_res, cash_rate=w.cash_rate[sl])
    rows = []
    for name, fn, p in canonical_grid():
        try:
            m = evaluate(w, fn, p, regime, sl, bench_res["equity"], exec_lag)
            rows.append((name, m))
        except Exception as e:
            print(f"   errore su {name}: {type(e).__name__}: {e}")
    per = f"{w.dates[sl][0].date()} -> {w.dates[sl][-1].date()}"
    print_table(rows, f"PARAMETRI DA MANUALE, NESSUNA OTTIMIZZAZIONE  [{per}]  "
                      f"fisco {regime}, ritardo {exec_lag}g", bench_m)
    return w, rows, bench_m


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    os.makedirs(RESULTS, exist_ok=True)
    t0 = time.time()
    if cmd == "check":
        cmd_check()
    elif cmd == "baseline":
        cmd_baseline()
    else:
        print(__doc__)
    print(f"\n({time.time()-t0:.1f}s)")

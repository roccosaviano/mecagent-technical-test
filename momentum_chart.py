"""Curve di equity del backtest momentum 5g (vedi momentum_backtest.py).
Uso: python3 momentum_chart.py --data DIR --intraday DIR60 --out grafico.png"""
import argparse, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from momentum_backtest import Cfg, load, backtest, load_60m, resolve_intraday
import pandas as pd

SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
BLUE, ORANGE, AQUA = '#2a78d6', '#eb6834', '#1baf7a'

def label(ax, x, y, text, color, dy=0):
    ax.annotate(text, (x, y), xytext=(6, dy), textcoords='offset points',
                color=color, fontsize=8.5, fontweight='600', va='center',
                annotation_clip=False)

def panel(ax, title, sub, curves, bench, ylim=None, floor_note=None):
    for s in ax.spines.values(): s.set_visible(False)
    ax.spines['bottom'].set_visible(True); ax.spines['bottom'].set_color(GRID)
    ax.set_facecolor(SURF)
    ax.grid(axis='y', color=GRID, lw=.8); ax.set_axisbelow(True)
    ax.set_yscale('log')
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f'{v:g}x'))
    ax.tick_params(colors=INK2, labelsize=8.5, length=0)

    if ylim: ax.set_ylim(*ylim)
    lo, hi = curves['pess'], curves['ott']
    floor = ylim[0] if ylim else lo.min()
    lo_c = lo.clip(lower=floor)
    ax.fill_between(lo_c.index, lo_c.values, hi.values, color=ORANGE, alpha=.16, lw=0)
    ax.plot(hi.index, hi.values, color=ORANGE, lw=1.6)
    ax.plot(lo_c.index, lo_c.values, color=ORANGE, lw=1.2, alpha=.6)
    ax.plot(bench.index, bench.values, color=BLUE, lw=2)
    label(ax, bench.index[-1], bench.iloc[-1], f"SPY  {bench.iloc[-1]:.2f}x", BLUE)
    label(ax, hi.index[-1], hi.iloc[-1], f"ottimista  {hi.iloc[-1]:.3f}x", ORANGE, 2)
    label(ax, lo_c.index[-1], lo_c.iloc[-1],
          floor_note or f"pessimista  {lo.iloc[-1]:.3f}x", ORANGE, -2)
    if 'real' in curves:
        r = curves['real']
        ax.plot(r.index, r.values, color=AQUA, lw=2)
        label(ax, r.index[-1], r.iloc[-1], f"percorso reale  {r.iloc[-1]:.3f}x", AQUA)
    ax.set_title(title, color=INK, fontsize=11.5, fontweight='700', loc='left', pad=14)
    ax.annotate(sub, (0, 1), xycoords='axes fraction', xytext=(0, 6),
                textcoords='offset points', color=INK2, fontsize=8.5)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True); ap.add_argument('--intraday', required=True)
    ap.add_argument('--out', default='momentum_equity.png')
    a = ap.parse_args()
    d = load(a.data); cfg = Cfg()
    cur = {}
    for k, p in (('pess', 'sl'), ('ott', 'tp')):
        cfg.path = p; cur[k], _ = backtest(d, cfg)
    bars = load_60m(a.intraday)
    days = sorted({dd for df in bars.values() for dd in set(df.d)})
    start = pd.Timestamp(days[0]) + pd.Timedelta(days=1)
    cfg.path = 'sl'
    res = lambda t, day: (resolve_intraday(bars, t, day, cfg) if
                          resolve_intraday(bars, t, day, cfg) in ('tp', 'sl') else 'sl')
    real, _ = backtest(d, cfg, start=start, resolver=res)
    sub = {}
    for k, p in (('pess', 'sl'), ('ott', 'tp')):
        cfg.path = p; sub[k], _ = backtest(d, cfg, start=start)
    sub['real'] = real

    b = d['bench'].reindex(cur['pess'].index).ffill(); b = b / b.iloc[0]
    b2 = d['bench'].reindex(real.index).ffill(); b2 = b2 / b2.iloc[0]
    for k in sub: sub[k] = sub[k] / sub[k].iloc[0]

    fig, axes = plt.subplots(2, 1, figsize=(11.5, 9.5), facecolor=SURF)
    fig.suptitle('Top performer a 5 giorni, long 2x, TP +1% / SL -3%  —  equity, scala logaritmica',
                 color=INK, fontsize=13.5, fontweight='700', x=.055, ha='left', y=.975)
    ruin = cur['pess'][cur['pess'] < 1e-3]
    panel(axes[0], 'Campione completo 2010-2026',
          'S&P 100 · 1 titolo al giorno · costi 1 bp commissione + 3/8 bp slippage', cur, b,
          ylim=(1e-3, 30),
          floor_note=f"pessimista: -99.9% entro il {ruin.index[0].date()}" if len(ruin) else None)
    panel(axes[1], f'{real.index[0].date()} - {real.index[-1].date()}: ambiguita\' risolta con barre orarie vere',
          'stesso periodo, stessa regola: la linea verde e\' l\'unica che non assume nulla sul percorso', sub, b2)
    fig.subplots_adjust(left=.055, right=.795, top=.9, bottom=.05, hspace=.28)
    fig.savefig(a.out, dpi=150, facecolor=SURF)
    print('scritto', a.out)

if __name__ == '__main__':
    main()

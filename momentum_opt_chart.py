"""Grafici dell'ottimizzazione (vedi momentum_optimize.py).
Uso: python3 momentum_opt_chart.py --data DIR --out ottimizzazione.png"""
import argparse, numpy as np, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.ticker import FuncFormatter
import momentum_backtest as M
from momentum_engine import Book, outcomes, daily_returns, metrics
from momentum_optimize import build, walk_forward, KS, TRAIN, TEST

SURF, INK, INK2, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#e4e3df'
BLUE, ORANGE, RED, MID = '#2a78d6', '#eb6834', '#e34948', '#f0efec'
CMAP = LinearSegmentedColormap.from_list('div', [RED, MID, BLUE])

def lab(k):
    return 'nessuno' if not np.isfinite(k) else f'{k:g}×ATR'

def heat(ax, mu, keys):
    grid = np.full((len(KS), len(KS)), np.nan)
    for i, k in enumerate(keys):
        if k[0] == 5 and k[1] == 1 and k[4] == 'vol bassa':
            grid[KS.index(k[2]), KS.index(k[3])] = mu[i]
    v = np.nanmax(np.abs(grid))
    ax.imshow(grid, cmap=CMAP, norm=TwoSlopeNorm(0, -v, v), aspect='auto')
    for r in range(len(KS)):
        for c in range(len(KS)):
            val = grid[r, c]
            col = '#ffffff' if abs(val) > v * .55 else INK
            ax.text(c, r, f'{val:+.1f}', ha='center', va='center',
                    color=col, fontsize=9.5, fontweight='700')
    ax.set_xticks(range(len(KS)), [lab(k) for k in KS], fontsize=8.5, color=INK2)
    ax.set_yticks(range(len(KS)), [lab(k) for k in KS], fontsize=8.5, color=INK2)
    ax.set_xlabel('stop loss', color=INK2, fontsize=9)
    ax.set_ylabel('take profit', color=INK2, fontsize=9)
    ax.tick_params(length=0)
    for s in ax.spines.values(): s.set_visible(False)
    ax.set_title('Rendimento medio per giornata, in bp — lookback 5g, 1 titolo, regime di volatilita\' bassa',
                 color=INK, fontsize=11, fontweight='700', loc='left', pad=48)
    ax.annotate('in campione, 2010-2026. Il massimo sta nell\'angolo senza TP e senza SL:\n'
                'ogni restringimento di uno dei due livelli toglie valore, in modo monotono.',
                (0, 1), xycoords='axes fraction', xytext=(0, 8), textcoords='offset points',
                color=INK2, fontsize=8.5, va='bottom')

def curves(ax, idx, series, bench):
    for s in ax.spines.values(): s.set_visible(False)
    ax.spines['bottom'].set_visible(True); ax.spines['bottom'].set_color(GRID)
    ax.set_facecolor(SURF); ax.grid(axis='y', color=GRID, lw=.8); ax.set_axisbelow(True)
    ax.set_yscale('log'); ax.set_ylim(1e-3, 30)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, p: f'{v:g}x'))
    ax.tick_params(colors=INK2, labelsize=8.5, length=0)
    ax.plot(idx, bench, color=BLUE, lw=2)
    ax.annotate(f'SPY  {bench[-1]:.2f}x', (idx[-1], bench[-1]), xytext=(6, 0),
                textcoords='offset points', color=BLUE, fontsize=8.5,
                fontweight='700', va='center', annotation_clip=False)
    for (nm, col, c) in series:
        cc = np.clip(c, 1e-3, None)
        ax.plot(idx, cc, color=col, lw=2)
        ax.annotate(f'{nm}  {c[-1]:.3f}x', (idx[-1], cc[-1]), xytext=(6, 0),
                    textcoords='offset points', color=col, fontsize=8.5,
                    fontweight='700', va='center', annotation_clip=False)
    ax.set_title('Walk-forward: parametri scelti sui 3 anni precedenti, applicati all\'anno dopo',
                 color=INK, fontsize=11, fontweight='700', loc='left', pad=48)
    ax.annotate('equity a leva 2x, scala logaritmica. L\'ottimizzazione recupera 51 punti di CAGR\n'
                'sulla regola originale e resta sotto zero.',
                (0, 1), xycoords='axes fraction', xytext=(0, 8), textcoords='offset points',
                color=INK2, fontsize=8.5, va='bottom')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', required=True); ap.add_argument('--out', default='momentum_opt.png')
    a = ap.parse_args()
    d = M.load(a.data); bk = Book(d)
    R, keys, amb = build(bk, 'sl')
    mu = R.mean(axis=1) * 1e4
    oos, cov, chosen, folds = walk_forward(R, keys, amb, bk.idx, None)
    out0, _ = outcomes(bk, .01, .03, 'sl')
    r0, _ = daily_returns(bk.ranks(5), out0, 1)
    idx = bk.idx[cov]
    eq = lambda r: np.cumprod(np.maximum(1e-12, 1 + 2.0 * r[cov]))
    b = bk.bench.to_numpy()[cov]; b = b / b[0]
    fig, axes = plt.subplots(2, 1, figsize=(11.5, 10.5), facecolor=SURF,
                             gridspec_kw={'height_ratios': [1, 1.15]})
    fig.suptitle('Ottimizzazione della regola momentum 5g — cosa si puo\' salvare, e quanto',
                 color=INK, fontsize=13.5, fontweight='700', x=.055, ha='left', y=.975)
    heat(axes[0], mu, keys)
    curves(axes[1], idx, [('walk-forward ottimizzato', ORANGE, eq(oos)),
                          ('regola originale TP1%/SL3%', RED, eq(r0))], b)
    fig.subplots_adjust(left=.095, right=.745, top=.865, bottom=.055, hspace=.5)
    fig.savefig(a.out, dpi=150, facecolor=SURF)
    print('scritto', a.out)

if __name__ == '__main__':
    main()

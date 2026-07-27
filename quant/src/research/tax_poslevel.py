"""Contabilita' fiscale PER POSIZIONE contro contabilita' AGGREGATA.

Il motore del progetto (tax.py) tiene UN SOLO costo fiscale per l'intero
portafoglio e, quando la strategia ruota, realizza una quota PROPORZIONALE
della plusvalenza aggregata non realizzata. Nella realta' si vendono posizioni
specifiche, e vendere un perdente cristallizza una MINUSVALENZA anche se il
portafoglio nel complesso e' in utile.

  A a +50%, B a -30%, pesi uguali. Aggregato +10%.
  La rotazione vende tutto B (turnover 50%).
    modello aggregato: 0,5 x (+10%) = +5%  -> plusvalenza tassabile
    realta':           -30% su meta' portafoglio = -15% -> MINUSVALENZA

Se lo scarto e' grande, tutte le conclusioni del progetto sulle strategie che
ruotano sono distorte CONTRO di esse.

Qui i due motori sono scritti nello stesso file e condividono TUTTO tranne il
libro dei costi fiscali: stessi flussi, stessi costi di transazione, stessa
regola di fine anno. L'unica differenza e' se la plusvalenza realizzata da una
vendita si calcola posizione per posizione o pro quota sull'aggregato.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from tax import _xirr
from research import bench as B


def pac(rets, W, mode, contrib=C.MONTHLY_CONTRIB, cost=C.COST_ROUND_TRIP,
        rate=C.CGT_RATE, exempt=C.CGT_EXEMPT_ANNUAL, rf=None):
    """PAC su un portafoglio a pesi dati. mode = 'pos' | 'agg'.

    W.iloc[i] sono i pesi DETENUTI durante il periodo i. All'inizio del periodo
    si versa la rata, si ribilancia ai pesi target, poi maturano i rendimenti.
    """
    idx = rets.index
    K = rets.shape[1]
    val = np.zeros(K)          # valore di mercato di ogni posizione
    bas = np.zeros(K)          # costo fiscale di ogni posizione (solo mode='pos')
    basis_agg = 0.0            # costo fiscale unico       (solo mode='agg')
    year_gain = 0.0
    carry = 0.0
    cur_year = idx[0].year
    taxes = costs = 0.0
    cfs = []
    vals = []

    def pay(amount):
        """Le imposte si pagano liquidando pro rata: non cambia il mix."""
        nonlocal basis_agg
        tot = val.sum()
        if amount <= 0 or tot <= 0:
            return 0.0
        take = min(tot, amount)
        f = take / tot
        # la liquidazione pro rata realizza a sua volta plusvalenza; la trascuro
        # in ENTRAMBI i motori per non introdurre una differenza che non c'entra
        val[:] = val * (1 - f)
        bas[:] = bas * (1 - f)
        basis_agg *= (1 - f)
        return take

    for i, t in enumerate(idx):
        if t.year != cur_year:
            taxable = max(0.0, year_gain - carry)
            carry -= min(carry, max(0.0, year_gain))
            if year_gain < 0:
                carry += -year_gain
            taxes += pay(max(0.0, taxable - exempt) * rate)
            year_gain = 0.0
            cur_year = t.year

        buy_cost = contrib * (cost / 2.0)
        costs += buy_cost
        inv = contrib - buy_cost
        cfs.append((t, -contrib))

        w = W.iloc[i].values.astype(float)
        tot = val.sum() + inv
        tgt = tot * w

        # --- vendite: e' qui che i due motori divergono
        sells = np.maximum(val - tgt, 0.0)
        s_tot = float(sells.sum())
        if s_tot > 0:
            if mode == "pos":
                for k in np.nonzero(sells > 0)[0]:
                    f = sells[k] / val[k]
                    g = sells[k] - bas[k] * f      # PUO' ESSERE NEGATIVO
                    year_gain += g
                    bas[k] -= bas[k] * f
            else:
                unreal = val.sum() - basis_agg
                frac = s_tot / val.sum() if val.sum() > 0 else 0.0
                g = unreal * frac                  # quota della plusvalenza aggregata
                year_gain += g
                basis_agg += g
            val = val - sells

        # --- acquisti
        buys = np.maximum(tgt - val, 0.0)
        b_tot = float(buys.sum())
        val = val + buys
        bas = bas + buys
        basis_agg += inv                          # solo i soldi nuovi alzano il costo
        # costo di transazione: meta' spread su ogni gamba, oltre alla rata gia'
        # addebitata sopra
        tc = (s_tot + max(0.0, b_tot - inv)) * (cost / 2.0)
        costs += tc
        if val.sum() > 0:
            f = tc / val.sum()
            val = val * (1 - f)

        val = val * (1.0 + rets.iloc[i].values.astype(float))
        vals.append(val.sum())

    # --- liquidazione finale
    fin = float(val.sum())
    if mode == "pos":
        year_gain += fin - float(bas.sum())
    else:
        year_gain += fin - basis_agg
    taxable = max(0.0, max(0.0, year_gain - carry) - exempt)
    due = taxable * rate
    taxes += due
    fin -= due
    cfs.append((idx[-1], fin))

    return dict(final=fin, taxes=taxes, costs=costs,
                contrib=contrib * len(idx),
                irr=_xirr([d for d, _ in cfs], [a for _, a in cfs]) * 100,
                value=pd.Series(vals, index=idx))


# ------------------------------------------------------------------ prova
ind = dataio.ff_ind49_daily().resample("ME").apply(lambda x: (1 + x).prod() - 1)
ind = ind.dropna(how="all").fillna(0.0)
ind = ind[ind.index >= "1990-01-01"]

print(f"49 settori, {ind.index[0].date()} -> {ind.index[-1].date()}, "
      f"{len(ind)} mesi\n")

rows = []
for top in (1, 3, 5, 10, 25):
    W = B.xs_momentum(ind, lb=12, skip=1, top=top)
    W = W.reindex(ind.index).fillna(0.0)
    ok = W.sum(axis=1) > 0
    r, w = ind[ok], W[ok]
    a = pac(r, w, "agg")
    p = pac(r, w, "pos")
    turn = w.diff().abs().sum(axis=1).fillna(0).mean() / 2 * 12
    rows.append((f"top-{top}", turn, a["irr"], p["irr"], p["irr"] - a["irr"],
                 a["taxes"], p["taxes"], a["final"], p["final"]))

# equal-weight statico, come controllo: senza rotazione i due DEVONO coincidere
W = pd.DataFrame(1.0 / ind.shape[1], index=ind.index, columns=ind.columns)
a = pac(ind, W, "agg"); p = pac(ind, W, "pos")
rows.append(("equal-weight", 0.0, a["irr"], p["irr"], p["irr"] - a["irr"],
             a["taxes"], p["taxes"], a["final"], p["final"]))

print(f"{'strategia':<14}{'rotaz.':>8}{'IRR agg':>10}{'IRR pos':>10}{'delta':>9}"
      f"{'tax agg':>11}{'tax pos':>11}{'fin agg':>11}{'fin pos':>11}")
print("-" * 95)
for r in rows:
    print(f"{r[0]:<14}{r[1]:>7.2f}x{r[2]:>9.2f}%{r[3]:>9.2f}%{r[4]:>+8.2f} "
          f"{r[5]:>10,.0f}{r[6]:>11,.0f}{r[7]:>11,.0f}{r[8]:>11,.0f}")

# --- controllo vero: un solo asset, nessuna rotazione possibile. I due motori
#     devono coincidere alla cifra, altrimenti c'e' un bug e non un effetto.
one = ind[["Agric"]]
W1 = pd.DataFrame(1.0, index=one.index, columns=one.columns)
a = pac(one, W1, "agg"); p = pac(one, W1, "pos")
print(f"\ncontrollo 1 asset: IRR agg {a['irr']:.4f}%  IRR pos {p['irr']:.4f}%  "
      f"delta {p['irr'] - a['irr']:+.6f}")

# --- stesso confronto ad aliquota 52%: sopra il 100% di rotazione l'anno e'
#     quella di riferimento nel progetto, ed e' li' che lo scarto conta
print(f"\naliquota 52% (nessuna esenzione)")
print(f"{'strategia':<14}{'IRR agg':>10}{'IRR pos':>10}{'delta':>9}")
print("-" * 43)
for top in (1, 3, 5, 10, 25):
    W = B.xs_momentum(ind, lb=12, skip=1, top=top).reindex(ind.index).fillna(0.0)
    ok = W.sum(axis=1) > 0
    r, w = ind[ok], W[ok]
    a = pac(r, w, "agg", rate=C.TRADING_INCOME_RATE, exempt=0.0)
    p = pac(r, w, "pos", rate=C.TRADING_INCOME_RATE, exempt=0.0)
    print(f"top-{top:<10}{a['irr']:>9.2f}%{p['irr']:>9.2f}%{p['irr'] - a['irr']:>+8.2f}")

# --- il caso peggiore possibile: una strategia che vende SISTEMATICAMENTE i
#     perdenti. Reversal a 1 mese preso al contrario: tiene i migliori del mese
#     appena chiuso, quindi ogni mese liquida chi e' appena sceso.
sig = ind.shift(1)
rk = sig.rank(axis=1, ascending=False)
Wl = (rk <= 10).astype(float)
Wl = Wl.div(Wl.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
ok = Wl.sum(axis=1) > 0
a = pac(ind[ok], Wl[ok], "agg"); p = pac(ind[ok], Wl[ok], "pos")
print(f"\nvende i perdenti (top-10 su 1 mese): IRR agg {a['irr']:.2f}%  "
      f"pos {p['irr']:.2f}%  delta {p['irr'] - a['irr']:+.2f}")

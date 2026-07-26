"""Giro 29 — Due ipotesi pre-dichiarate.

Protocollo nuovo, concordato con l'utente: l'ipotesi e la predizione si
dichiarano PRIMA di guardare i risultati, si prova una configurazione sola, e
l'esito si riporta qualunque sia. Cosi' N e' la famiglia delle ipotesi
pre-dichiarate (~32), non una griglia.

--------------------------------------------------------------------------
H31  COMBINAZIONE DEI TRE CANDIDATI PROMOSSI (multi-strategia)

Dopo la ricontabilizzazione passano tre candidati: H5 momentum settoriale,
H11a punteggio misto momentum+low-vol, e il punto a 60% di turnover della
frontiera. Sono tutti e tre costruiti sui 49 settori con segnali di momentum.

PREDIZIONE: sono varianti dello stesso segnale, quindi la correlazione media
fra i loro rendimenti sara' sopra 0,7 e combinarli non alzera' lo Sharpe
oltre il migliore singolo. FALSIFICATA se corr media < 0,5 E Sharpe combinato
> Sharpe del migliore singolo.

--------------------------------------------------------------------------
H32  EFFETTO TURN-OF-MONTH (mono-strategia, mercati tradizionali e cripto)

Ariel (1987) e Lakonishok-Smidt (1988): i rendimenti si concentrano a cavallo
del cambio di mese. La strategia sta long solo dal giorno -1 al +3 rispetto
alla fine del mese, quindi e' investita ~5 giorni su 21 e ruota 24 volte
l'anno. E' il profilo di rotazione piu' basso fra tutte le strategie attive
provate finora, ed e' l'unica cosa che ha contato in questo studio.

PREDIZIONE: l'effetto esiste nel campione pre-pubblicazione (fino al 1988) e
si e' ridotto di circa meta' dopo, coerentemente con i 50,4% di decadimento
medio misurati al giro 10 su 201 anomalie. FALSIFICATA se il premio
post-1988 e' uguale o superiore a quello pre-1988.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES, TRADING_52, first_of_month
from research import lab, walkforward as WF
from research.round15 import load
from research.round19 import load_crypto, SYMS, COST_CRYPTO
from research.round23 import panel
from research.round25 import _stats

ROUND = 29
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 32


# ==================================================================== H31
def h31():
    print("=" * 84)
    print("H31 — I TRE CANDIDATI PROMOSSI SONO LA STESSA COSA?")
    print("=" * 84)
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all")
    ff = dataio.ff_factors_monthly()
    rf, eq = ff["RF"], (ff["Mkt-RF"] + ff["RF"]).rename("eq")
    lg = np.log1p(ind)
    MOM = np.expm1(lg.rolling(12).sum()).shift(2)
    VOL = ind.rolling(60).std().shift(1)

    from research.round11 import make_composite
    from research.round12 import momentum_buffered

    def mom_plain(cfg, idx):
        n_sel, look, rb = cfg
        d = ind.reindex(idx).dropna(axis=1)
        if len(d) < 26 or d.shape[1] < n_sel:
            return None, None
        m = MOM.reindex(d.index)[d.columns]
        rets, turns, w = [], [], None
        for i in range(len(d)):
            if i < 14:
                rets.append(np.nan); turns.append(0.0); continue
            if w is None or i % rb == 0:
                s = m.iloc[i].dropna()
                if len(s) < n_sel:
                    rets.append(np.nan); turns.append(0.0); continue
                new = pd.Series(0.0, index=d.columns)
                new[s.nlargest(n_sel).index] = 1.0 / n_sel
                turns.append(0.5 * float((new - (w if w is not None else 0)).abs().sum())
                             if w is not None else 1.0)
                w = new
            else:
                turns.append(0.0)
            r = d.iloc[i]
            rets.append(float((w * r).sum()) - turns[-1] * C.COST_ROUND_TRIP)
            g = w * (1 + r); w = g / g.sum()
        s_ = pd.Series(rets, index=d.index).dropna()
        return s_, pd.Series(turns, index=d.index).reindex(s_.index)

    specs = {
        "H5 momentum settoriale": (mom_plain, (5, 12, 1)),
        "H11a composito mom+low-vol": (make_composite(ind, MOM, VOL), (5, 3, 1.0)),
        "Frontiera 60% turnover": (momentum_buffered(ind, MOM), (5, 25, 0, 3)),
    }
    streams = {}
    for nm, (fn, cfg) in specs.items():
        oos, rzs, picks, ne, vsr = WF.walk_forward(fn, [cfg], ind.index, rf,
                                                   start_year=1935)
        if oos is not None and len(oos):
            streams[nm] = (oos, rzs)
    idx = None
    for o, _ in streams.values():
        idx = o.index if idx is None else idx.intersection(o.index)
    M = pd.DataFrame({k: v[0].reindex(idx) for k, v in streams.items()}).dropna()
    cm = M.corr()
    print(f"\n  Finestra comune {M.index[0].date()} -> {M.index[-1].date()} "
          f"({len(M)} mesi)")
    print("\n  Correlazione fra i rendimenti mensili:")
    print("  " + cm.round(3).to_string().replace("\n", "\n  "))
    avg = float(cm.to_numpy()[np.triu_indices(len(cm), 1)].mean())
    print(f"\n  Correlazione media a coppie: {avg:.3f}")

    rfw = rf.reindex(M.index).fillna(0.0)
    print(f"\n  {'':<32}{'CAGR':>9}{'Sharpe':>8}{'DD':>9}")
    best_sh = -9
    for c in M.columns:
        s = _stats(M[c], 12)
        best_sh = max(best_sh, s["sharpe"])
        print(f"  {c:<32}{s['cagr']:>8.2f}%{s['sharpe']:>8.2f}{s['dd']:>8.1f}%")
    comb = M.mean(axis=1)
    sc = _stats(comb, 12)
    print(f"  {'COMBINAZIONE (pesi uguali)':<32}{sc['cagr']:>8.2f}%"
          f"{sc['sharpe']:>8.2f}{sc['dd']:>8.1f}%")
    bh = _stats(eq.reindex(M.index), 12)
    print(f"  {'buy&hold':<32}{bh['cagr']:>8.2f}%{bh['sharpe']:>8.2f}{bh['dd']:>8.1f}%")

    falsified = (avg < 0.5) and (sc["sharpe"] > best_sh)
    print(f"\n  PREDIZIONE: corr > 0,7 e combinazione non migliora.")
    print(f"  Osservato: corr {avg:.3f}, Sharpe combinato {sc['sharpe']:.2f} "
          f"contro {best_sh:.2f} del migliore singolo.")
    print(f"  -> ipotesi {'FALSIFICATA' if falsified else 'CONFERMATA'}")
    return dict(corr=avg, sharpe_comb=sc["sharpe"], sharpe_best=best_sh,
                falsified=falsified, comb=comb)


# ==================================================================== H32
def tom_position(idx, lo=-1, hi=3):
    """Long dal giorno -1 (ultimo del mese) al +3 del mese successivo."""
    s = pd.Series(idx, index=idx)
    mon = s.dt.to_period("M")
    pos = pd.Series(0.0, index=idx)
    for _, g in s.groupby(mon):
        d = g.index
        if lo < 0:
            pos.loc[d[max(0, len(d) + lo):]] = 1.0
        pos.loc[d[:hi]] = 1.0
    return pos.shift(1).fillna(0.0)


def h32():
    print(f"\n{'='*84}")
    print("H32 — TURN-OF-MONTH: DECADE DOPO LA PUBBLICAZIONE?")
    print("=" * 84)
    ffd = dataio.ff_factors_daily()
    mkt = (ffd["Mkt-RF"] + ffd["RF"]).dropna()
    rf = ffd["RF"]
    out = []

    markets = [("Indice CRSP", mkt, 252, C.COST_ROUND_TRIP, rf)]
    try:
        markets.append(("QQQ", load("QQQ", "1day").close.pct_change().dropna(),
                        252, C.COST_ROUND_TRIP, None))
        px, _, _ = panel()
        markets.append(("7 cripto equipesate", px.dropna().pct_change()
                        .mean(axis=1).dropna(), 365, COST_CRYPTO, None))
    except Exception as e:
        print(f"  (mercato saltato: {e})")

    for nm, r, ppy, cost, rfx in markets:
        pos = tom_position(r.index)
        inm = float((pos > 0).mean())
        turn = pos.diff().abs().fillna(pos.abs())
        net = (pos * r - turn * cost / 2.0).dropna()
        s, b = _stats(net, ppy), _stats(r, ppy)
        ops = float((pos.diff() > 0).sum()) / (len(r) / ppy)
        # premio giornaliero dentro e fuori finestra
        inn = r[pos.shift(-1).fillna(0) > 0]
        outw = r[pos.shift(-1).fillna(0) == 0]
        t = st.ttest_ind(inn, outw, equal_var=False)
        print(f"\n  {nm}  {r.index[0].date()} -> {r.index[-1].date()}")
        print(f"    tempo in mercato {inm*100:.0f}%   operazioni/anno {ops:.0f}")
        print(f"    rendimento medio dentro finestra {inn.mean()*10000:.2f} bp, "
              f"fuori {outw.mean()*10000:.2f} bp  (t={t.statistic:+.2f}, "
              f"p={t.pvalue:.3f})")
        print(f"    {'':<20}{'CAGR':>9}{'Sharpe':>8}{'DD':>9}")
        print(f"    {'turn-of-month':<20}{s['cagr']:>8.2f}%{s['sharpe']:>8.2f}"
              f"{s['dd']:>8.1f}%")
        print(f"    {'buy&hold':<20}{b['cagr']:>8.2f}%{b['sharpe']:>8.2f}"
              f"{b['dd']:>8.1f}%")
        rf0 = (rfx.reindex(net.index).fillna(0.0) if rfx is not None
               else pd.Series(0.0, index=net.index))
        con = first_of_month(net.index)
        a33 = simulate_pac(net, CGT_SHARES, in_market=pos.reindex(net.index),
                           rf=rf0, periods_per_year=ppy, contrib_on=con)
        bb = simulate_pac(r.reindex(net.index), CGT_SHARES, rf=rf0,
                          periods_per_year=ppy, contrib_on=con)
        print(f"    IRR netta 33%: {a33.irr_annual:.2f}% contro "
              f"{bb.irr_annual:.2f}%  ({a33.irr_annual-bb.irr_annual:+.2f})")
        out.append(dict(mkt=nm, cagr=s["cagr"], sharpe=s["sharpe"], dd=s["dd"],
                        ops=ops, irr=a33.irr_annual, bh=bb.irr_annual,
                        vs=a33.irr_annual - bb.irr_annual, net=net,
                        t=float(t.statistic), p=float(t.pvalue)))

    # decadimento post-pubblicazione, sul solo CRSP che ha storia lunga
    print(f"\n  Decadimento post-pubblicazione (Lakonishok-Smidt 1988), CRSP:")
    pos = tom_position(mkt.index)
    inw = pos.shift(-1).fillna(0) > 0
    for a, b, lbl in [("1926", "1987", "PRE  1926-1987"),
                      ("1988", "2026", "POST 1988-2026")]:
        rr = mkt.loc[a:b]
        ii = inw.reindex(rr.index).fillna(False)
        prem = (rr[ii].mean() - rr[~ii].mean()) * 10000
        tt = st.ttest_ind(rr[ii], rr[~ii], equal_var=False)
        print(f"    {lbl}: premio {prem:+.2f} bp/giorno  "
              f"(t={tt.statistic:+.2f}, p={tt.pvalue:.4f})")
        out.append(dict(mkt=f"CRSP {lbl}", prem=float(prem),
                        t=float(tt.statistic), p=float(tt.pvalue)))
    pre = next(x for x in out if "PRE" in str(x.get("mkt", "")))
    post = next(x for x in out if "POST" in str(x.get("mkt", "")))
    decay = (1 - post["prem"] / pre["prem"]) * 100 if pre["prem"] else np.nan
    print(f"    decadimento: {decay:.0f}%  (atteso ~50% dal giro 10)")
    print(f"\n  PREDIZIONE: effetto pre-1988 positivo, post-1988 ridotto ~meta'.")
    print(f"  -> ipotesi {'CONFERMATA' if 20 < decay < 90 else 'NON confermata'}")
    return out, decay


def main():
    a = h31()
    b, decay = h32()

    print(f"\n{'='*84}\nESITO DEL GIRO\n{'='*84}")
    n_cum = N_PREREG
    dd = lab.deflated_sharpe(a["comb"], n_cum, round_id=ROUND)
    print(f"  H31 combinazione: DSR {dd['dsr']:.3f} su {n_cum} ipotesi "
          f"pre-dichiarate")
    best = max((x for x in b if "vs" in x), key=lambda x: x["vs"], default=None)
    if best:
        print(f"  H32 migliore: {best['mkt']}  {best['vs']:+.2f} punti "
              f"({best['ops']:.0f} operazioni/anno)")
        d2 = lab.deflated_sharpe(best["net"], n_cum, round_id=ROUND)
        print(f"       DSR {d2['dsr']:.3f}  -> "
              f"{'PROMUOVIBILE' if d2['dsr']>0.95 and best['vs']>0 else 'NON promuovibile'}")

    lab.log_trials(
        [dict(round=ROUND, hypothesis="H31 combinazione dei promossi",
              config="pesi uguali su 3", window="walk-forward",
              sharpe=a["sharpe_comb"], irr="", bh_irr="", excess="",
              n_obs=len(a["comb"]), note=f"corr={a['corr']:.3f}")] +
        [dict(round=ROUND, hypothesis="H32 turn-of-month", config=x["mkt"],
              window="varie", sharpe=x.get("sharpe", ""), irr=x.get("irr", ""),
              bh_irr=x.get("bh", ""), excess=x.get("vs", ""),
              n_obs=len(x["net"]) if "net" in x else 0,
              note=f"t={x.get('t', float('nan')):.2f}") for x in b if "net" in x])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

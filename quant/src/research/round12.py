"""Giro 12 — Tre ipotesi mirate al vincolo che domina: la fiscalita' sul turnover.

H12  Momentum settoriale CON CONTROLLO DELLA ROTAZIONE. E' la domanda piu'
     importante rimasta aperta: H5 funziona ma ruota il 259% l'anno, il che
     porta l'aliquota da 33% a 52%. Se l'edge sopravvive con una banda di
     isteresi (vendo solo quando un settore esce dalla top-K allargata) e
     periodi minimi di detenzione, cambia tutto. Se non sopravvive, allora
     l'edge ERA la rotazione e non c'e' niente da salvare.

H13  Raccolta sistematica delle minusvalenze. Strutturale, non statistica:
     il fisco irlandese consente di compensare le minusvalenze realizzate e
     di riportarle senza limite. Vendere in perdita le posizioni sott'acqua
     e ricomprare esposizione equivalente crea un credito d'imposta senza
     cambiare il portafoglio. Richiede il tracciamento per singola posizione,
     che simulate_pac non fa: sotto c'e' un motore a lotti dedicato.

H14  Sfruttamento dell'esenzione annua da 1.270 EUR. Ogni anno realizzo
     esattamente 1.270 EUR di plusvalenza (esente) e ricompro, alzando il
     costo fiscale. E' gratis e certo: nessuna previsione, solo aritmetica.

Regola dei 4 settimane: in Irlanda riacquistare lo STESSO titolo entro 4
settimane annulla la minusvalenza. Nel modello si vende un settore e si
compra un settore diverso ma correlato, quindi la regola non scatta. E'
un'assunzione favorevole e la dichiaro.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from research import lab, walkforward as WF

ROUND = 12


# ------------------------------------------------------------------ H12
def momentum_buffered(ind, MOM):
    """Momentum con isteresi: entro nella top-K, esco solo sotto la top-B (B>K),
    e rispetto un periodo minimo di detenzione."""
    def build(cfg, idx):
        k, buf, minhold, rb = cfg
        d = ind.reindex(idx).dropna(axis=1)
        if len(d) < 30 or d.shape[1] < buf:
            return None, None
        m = MOM.reindex(d.index)[d.columns]
        rets, turns = [], []
        held = {}          # settore -> mesi di detenzione
        w = None
        for i in range(len(d)):
            if i < 26:
                rets.append(np.nan); turns.append(0.0); continue
            if w is None or i % rb == 0:
                sc = m.iloc[i].dropna()
                if len(sc) < buf:
                    rets.append(np.nan); turns.append(0.0); continue
                rank = sc.rank(ascending=False)
                keep = [c for c in held
                        if c in rank.index and (rank[c] <= buf
                                                or held[c] < minhold)]
                room = k - len(keep)
                if room > 0:
                    cand = [c for c in rank.nsmallest(buf).index if c not in keep]
                    keep += cand[:room]
                keep = keep[:k]
                new = pd.Series(0.0, index=d.columns)
                if keep:
                    new[keep] = 1.0 / len(keep)
                turns.append(0.5 * float((new - (w if w is not None else 0)).abs().sum())
                             if w is not None else 1.0)
                held = {c: held.get(c, 0) + 1 for c in keep}
                w = new
            else:
                turns.append(0.0)
                held = {c: v + 1 for c, v in held.items()}
            r = d.iloc[i]
            rets.append(float((w * r).sum()) - turns[-1] * C.COST_ROUND_TRIP)
            g = w * (1 + r)
            w = g / g.sum() if g.sum() > 0 else w
        s = pd.Series(rets, index=d.index).dropna()
        return s, pd.Series(turns, index=d.index).reindex(s.index)
    return build


# ------------------------------------------------------------------ motore a lotti
def sim_lots(ret_df, weights, rf, contrib=C.MONTHLY_CONTRIB,
             harvest_losses=False, harvest_exempt=False,
             cost_rt=C.COST_ROUND_TRIP, rate=C.CGT_RATE,
             exempt=C.CGT_EXEMPT_ANNUAL):
    """PAC su un paniere di N posizioni con tracciamento per posizione.

    Ogni mese il versamento e' ripartito secondo `weights`. A dicembre, se
    richiesto, si realizzano le minusvalenze delle posizioni sott'acqua
    (creando credito d'imposta) e/o esattamente `exempt` di plusvalenza
    esente, ricomprando subito: il portafoglio non cambia, cambia la base.
    """
    cols = list(ret_df.columns)
    val = {c: 0.0 for c in cols}     # valore di mercato
    bas = {c: 0.0 for c in cols}     # costo fiscale
    carry = 0.0
    year_gain = 0.0
    taxes = costs = 0.0
    cur_year = ret_df.index[0].year
    cash_flows, navs = [], []
    nav = 100.0

    for t, row in ret_df.iterrows():
        if t.year != cur_year:
            taxable = max(0.0, year_gain - carry)
            used = min(carry, max(0.0, year_gain))
            carry -= used
            if year_gain < 0:
                carry += -year_gain
            taxable = max(0.0, taxable - exempt)
            due = taxable * rate
            if due > 0:
                tot = sum(val.values())
                if tot > 0:
                    for c in cols:
                        val[c] -= due * val[c] / tot
                taxes += due
            year_gain = 0.0
            cur_year = t.year

        # versamento
        fee = contrib * cost_rt / 2.0
        costs += fee
        inv = contrib - fee
        for c in cols:
            val[c] += inv * weights[c]
            bas[c] += inv * weights[c]
        cash_flows.append((t, -contrib))

        # rendimento
        prev = sum(val.values())
        for c in cols:
            val[c] *= (1.0 + float(row[c]))
        cur = sum(val.values())
        nav *= (cur / prev) if prev > 0 else 1.0

        # raccolta a dicembre
        if t.month == 12:
            if harvest_losses:
                for c in cols:
                    if val[c] < bas[c]:
                        loss = val[c] - bas[c]        # negativo
                        year_gain += loss
                        fee = abs(loss) * cost_rt
                        costs += fee
                        val[c] -= fee
                        bas[c] = val[c]               # riacquisto: nuova base
            if harvest_exempt:
                need = exempt
                for c in cols:
                    if need <= 0:
                        break
                    g = val[c] - bas[c]
                    if g > 0:
                        take = min(g, need)
                        year_gain += take
                        bas[c] += take
                        need -= take
        navs.append(nav)

    # liquidazione
    final = sum(val.values())
    total_basis = sum(bas.values())
    year_gain += final - total_basis
    taxable = max(0.0, year_gain - carry)
    taxable = max(0.0, taxable - exempt)
    due = taxable * rate
    taxes += due
    final -= due

    from tax import _xirr
    dates = [d for d, _ in cash_flows] + [ret_df.index[-1]]
    amts = [a for _, a in cash_flows] + [final]
    nav_s = pd.Series(navs, index=ret_df.index)
    dd = float((nav_s / nav_s.cummax() - 1).min()) * 100
    return dict(irr=_xirr(dates, amts) * 100, final=final, taxes=taxes,
                costs=costs, dd=dd, nav=nav_s)


def main():
    ff = dataio.ff_factors_monthly()
    rf, eq = ff["RF"], (ff["Mkt-RF"] + ff["RF"]).rename("eq")
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all")
    lg = np.log1p(ind)
    MOM = np.expm1(lg.rolling(12).sum()).shift(2)
    out = []

    # -------------------------------------------------- H12
    grid = [(k, buf, mh, rb) for k in (5, 10) for buf in (15, 25)
            for mh in (0, 6, 12) for rb in (3, 12)]
    oos, rzs, picks, ne, vsr = WF.walk_forward(momentum_buffered(ind, MOM), grid,
                                          ind.index, rf, start_year=1935)
    cfgs = [c for _, c in picks]
    r = WF.report("H12 momentum settoriale con isteresi e hold minimo", "H12",
                  oos, rzs, eq, rf, ne, ROUND,
                  extra=f"config scelta piu' spesso: {max(set(cfgs), key=cfgs.count)}",
                  var_sr=vsr)
    if r:
        out.append(r)

    # -------------------------------------------------- H13/H14
    print(f"\n{'='*74}\nH13/H14 — raccolta minusvalenze ed esenzione annua")
    print("  Paniere: 49 settori equipesati, buy&hold, nessuna selezione.")
    print("  L'unica differenza fra le righe e' la gestione fiscale.")
    win = ind.loc[C.CALIB_START:C.CALIB_END].dropna(axis=1)
    w = {c: 1.0 / win.shape[1] for c in win.columns}
    base = sim_lots(win, w, rf)
    variants = [
        ("buy&hold, nessuna gestione fiscale", dict()),
        ("+ raccolta minusvalenze (H13)", dict(harvest_losses=True)),
        ("+ sfruttamento esenzione 1.270 (H14)", dict(harvest_exempt=True)),
        ("+ entrambe", dict(harvest_losses=True, harvest_exempt=True)),
    ]
    print(f"\n  {'variante':<40}{'IRR':>9}{'vs base':>10}{'imposte':>12}{'costi':>10}")
    for lbl, kw in variants:
        res = sim_lots(win, w, rf, **kw)
        print(f"  {lbl:<40}{res['irr']:>8.2f}%{res['irr']-base['irr']:>+9.2f}%"
              f"{res['taxes']:>12,.0f}{res['costs']:>10,.0f}")
        lab.log_trials([dict(round=ROUND, hypothesis="H13/H14", config=lbl,
                             window="CALIB", sharpe="", irr=res["irr"],
                             bh_irr=base["irr"], excess=res["irr"] - base["irr"],
                             n_obs=len(win), note="motore a lotti")])
    print("\n  La raccolta minusvalenze conta solo se ci SONO minusvalenze da")
    print("  raccogliere: su un paniere che sale per 34 anni le posizioni")
    print("  sott'acqua a fine anno sono poche, e il credito si usa una volta sola.")

    print(f"\n{'='*74}\nTentativi cumulati a registro: {lab.n_trials_so_far()}")
    return out


if __name__ == "__main__":
    main()

"""Gruppo D: portafogli diversity-weighted (Stochastic Portfolio Theory).

Riferimento: Fernholz, Karatzas & Kardaras, "Diversity and relative arbitrage in
equity markets", Finance and Stochastics 9(1):1-27, 2005.

UNIVERSO. Non avendo i prezzi dei singoli titoli dell'S&P 500 (Yahoo/Stooq
bloccati), uso i 49 portafogli settoriali di Ken French come "titoli". Le
capitalizzazioni sono reali, non ricostruite: French pubblica per ogni mese il
numero di societa' e la dimensione media di ciascun portafoglio, e il prodotto
dei due e' la capitalizzazione aggregata del settore. Il costo di questa scelta
e' che la diversita' misurata e' quella FRA settori, non fra singoli titoli:
sottostima la concentrazione vera, perche' dentro "Tecnologia" la quota di una
singola societa' non si vede. Lo dico nel report, non lo nascondo in una nota.

Identita' usata per la scomposizione (Fernholz):

    log( V_pi(T) / V_mu(T) ) = log( D_p(mu(T)) / D_p(mu(0)) ) + (1-p) * Int_0^T gamma*_pi dt

dove D_p(mu) = (Sum_i mu_i^p)^(1/p) e' la misura di diversita' e
gamma*_pi = 1/2 * ( Sum_i pi_i sigma_ii - sigma_pipi ) il tasso di crescita in eccesso.
Il primo termine e' la deriva dei pesi di mercato, il secondo il guadagno da
ribilanciamento. La sovraperformance non e' un errore di prezzo: e' un'identita'.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd

import dataio
import config as C
from tax import simulate_pac, CGT_SHARES

OUT = Path(__file__).resolve().parents[1] / "out"
REBAL = {"mensile": 1, "trimestrale": 3, "annuale": 12}
P_GRID = (0.25, 0.50, 0.75)


def load_universe(start="1990-01"):
    """Rendimenti mensili e pesi di capitalizzazione reali dei 49 settori."""
    vw, ew, nf, sz = dataio.ff_ind49_monthly()
    cap = (nf * sz)
    common = vw.index.intersection(cap.index)
    vw, ew, cap = vw.loc[common], ew.loc[common], cap.loc[common]
    ok = vw.notna().all(axis=1) & cap.notna().all(axis=1) & (cap > 0).all(axis=1)
    vw, ew, cap = vw[ok], ew[ok], cap[ok]
    vw, ew, cap = vw.loc[start:], ew.loc[start:], cap.loc[start:]
    mu = cap.div(cap.sum(axis=1), axis=0)
    return vw, ew, mu


def dw_weights(mu_row, p):
    w = mu_row ** p
    return w / w.sum()


def simulate_portfolio(ret, target_w, rebal_months, cost_rt=C.COST_ROUND_TRIP):
    """Portafoglio con pesi obiettivo, ribilanciato ogni N mesi.

    I pesi obiettivo di t sono calcolati sui dati di t-1: target_w e' gia'
    ritardato dal chiamante. Fra un ribilanciamento e l'altro i pesi derivano
    con i rendimenti, che e' esattamente cio' che rende il ribilanciamento
    un'operazione non banale.
    Restituisce (rendimenti netti di costo, turnover per periodo).
    """
    idx = ret.index
    w = target_w.iloc[0].to_numpy(dtype=float)
    rets, turns = [], []
    for i, t in enumerate(idx):
        if i % rebal_months == 0:
            tgt = target_w.iloc[i].to_numpy(dtype=float)
            turn = 0.5 * np.abs(tgt - w).sum()
            w = tgt
        else:
            turn = 0.0
        r = ret.iloc[i].to_numpy(dtype=float)
        port_r = float(w @ r) - turn * cost_rt
        # deriva dei pesi con i rendimenti del periodo
        grown = w * (1.0 + r)
        w = grown / grown.sum()
        rets.append(port_r)
        turns.append(turn)
    return pd.Series(rets, index=idx), pd.Series(turns, index=idx)


def excess_growth(ret_window, w):
    """gamma*_pi = 1/2 ( Sum_i pi_i sigma_ii - sigma_pipi ), annualizzato."""
    cov = ret_window.cov().to_numpy() * 12.0
    var_i = np.diag(cov)
    return 0.5 * (float(w @ var_i) - float(w @ cov @ w))


def diversity(mu_row, p):
    return float((mu_row ** p).sum() ** (1.0 / p))


def main():
    vw, ew, mu = load_universe("1990-01")
    n = vw.shape[1]
    print(f"--- Gruppo D: {n} settori, {vw.index[0].date()} -> {vw.index[-1].date()} "
          f"({len(vw)} mesi)")

    # pesi obiettivo ritardati di un mese: si usa la capitalizzazione nota a t-1
    mu_lag = mu.shift(1).dropna()
    vw_a = vw.loc[mu_lag.index]

    # ---------------------------------------------- 12: equal vs cap weight
    # Il portafoglio di mercato NON si ribilancia: i pesi seguono da soli i
    # prezzi, quindi il suo rendimento e' Sum_i mu_i(t-1) r_i(t) e il turnover
    # e' zero. E' il punto centrale del confronto: il cap-weight non paga ne'
    # costi di transazione ne' imposte finche' non vendi. Trattarlo come un
    # portafoglio da ribilanciare gli addebiterebbe costi che non sostiene.
    cw_r = (mu_lag * vw_a).sum(axis=1)
    cw_t = pd.Series(0.0, index=cw_r.index)
    n_assets = vw_a.shape[1]
    eqw = pd.DataFrame(1.0 / n_assets, index=mu_lag.index, columns=mu_lag.columns)
    print("\n--- 12. Equal-weight contro cap-weight (proxy dei 49 settori) -----")
    print(f"{'portafoglio':<26}{'CAGR lordo':>12}{'vol':>8}{'turnover/anno':>15}")
    ew_rows = {}
    for lbl, tgt, rb in (("cap-weight (nessun ribil.)", None, 0),
                         ("equal-weight, mensile", eqw, 1),
                         ("equal-weight, annuale", eqw, 12)):
        r, tn = (cw_r, cw_t) if tgt is None else simulate_portfolio(vw_a, tgt, rb)
        cagr = ((1 + r).prod() ** (12 / len(r)) - 1) * 100
        ew_rows[lbl] = dict(cagr=cagr, vol=r.std() * np.sqrt(12) * 100,
                            turn=tn.sum() / (len(r) / 12) * 100)
        print(f"{lbl:<26}{cagr:>11.2f}%{r.std()*np.sqrt(12)*100:>7.1f}%"
              f"{tn.sum()/(len(r)/12)*100:>14.0f}%")

    # ---------------------------------------------- 11: diversity-weighted
    print("\n--- 11. Diversity-weighted: p x frequenza di ribilanciamento ------")
    print(f"{'p':>6}{'ribilanc.':>13}{'CAGR lordo':>12}{'vs cap-w':>10}"
          f"{'turnover/anno':>15}{'vol':>8}")
    dw_rows = []
    dw_series = {}
    for p in P_GRID:
        tgt = mu_lag.apply(lambda row: dw_weights(row, p), axis=1)
        for lbl, rb in REBAL.items():
            r, tn = simulate_portfolio(vw_a, tgt, rb)
            cagr = ((1 + r).prod() ** (12 / len(r)) - 1) * 100
            base = ((1 + cw_r).prod() ** (12 / len(cw_r)) - 1) * 100
            turn_yr = tn.sum() / (len(r) / 12)
            dw_rows.append(dict(p=p, rebal=lbl, cagr=cagr, excess=cagr - base,
                                turn=turn_yr * 100, vol=r.std() * np.sqrt(12) * 100))
            dw_series[(p, lbl)] = (r, tn)
            print(f"{p:>6.2f}{lbl:>13}{cagr:>11.2f}%{cagr-base:>+9.2f}%"
                  f"{turn_yr*100:>14.0f}%{r.std()*np.sqrt(12)*100:>7.1f}%")

    # ---------------------------------------------- 13: scomposizione
    print("\n--- 13. Scomposizione dell'extra-rendimento (identita' di Fernholz) ")
    print(f"{'p':>6}{'log(V_pi/V_mu)':>17}{'deriva diversita':>19}"
          f"{'(1-p)*Int gamma*':>19}{'residuo':>10}")
    decomp = []
    for p in P_GRID:
        r, _ = dw_series[(p, "mensile")]
        lhs = float(np.log((1 + r).prod()) - np.log((1 + cw_r).prod()))
        d0, dT = diversity(mu_lag.iloc[0], p), diversity(mu_lag.iloc[-1], p)
        drift = float(np.log(dT / d0))
        # integrale di gamma* su finestre mobili di 60 mesi, pesi DW
        gam = []
        for i in range(len(mu_lag)):
            lo = max(0, i - 60)
            if i - lo < 24:
                gam.append(np.nan); continue
            w = dw_weights(mu_lag.iloc[i], p).to_numpy(dtype=float)
            gam.append(excess_growth(vw_a.iloc[lo:i], w))
        gam = pd.Series(gam, index=mu_lag.index)
        integral = float(gam.mean(skipna=True) * len(gam) / 12.0)
        rhs = drift + (1 - p) * integral
        decomp.append(dict(p=p, lhs=lhs, drift=drift, gamma_int=integral,
                           rhs=rhs, resid=lhs - rhs,
                           gamma_ann=float(gam.mean(skipna=True)) * 100))
        print(f"{p:>6.2f}{lhs:>+16.4f}{drift:>+18.4f}{(1-p)*integral:>+18.4f}"
              f"{lhs-rhs:>+10.4f}")
    print("  gamma* medio annuo (p=0,50): "
          f"{[d['gamma_ann'] for d in decomp if d['p']==0.5][0]:.2f}%/anno")
    print("  Il residuo non e' zero perche' l'identita' vale in tempo continuo,")
    print("  mentre qui i dati sono mensili e i costi di transazione sono dentro V_pi.")

    # ---------------------------------------------- diversita' nel tempo
    print("\n--- Diversita' del mercato nel tempo ------------------------------")
    top1 = mu.max(axis=1) * 100
    top10 = mu.apply(lambda r: r.nlargest(10).sum(), axis=1) * 100
    hhi = (mu ** 2).sum(axis=1) * 10000
    div50 = mu.apply(lambda r: diversity(r, 0.5), axis=1)
    print(f"{'periodo':<12}{'top-1 %':>10}{'top-10 %':>11}{'HHI':>9}{'D(0,5)':>10}")
    for a, b in (("1990", "1999"), ("2000", "2009"), ("2010", "2014"),
                 ("2015", "2019"), ("2020", "2026")):
        s = slice(a, b)
        print(f"{a+'-'+b:<12}{top1[s].mean():>9.1f}{top10[s].mean():>10.1f}"
              f"{hhi[s].mean():>9.0f}{div50[s].mean():>10.3f}")

    # correlazione fra variazione di diversita' e sovraperformance DW
    print("\n--- Ipotesi da falsificare ----------------------------------------")
    r50, _ = dw_series[(0.50, "mensile")]
    rel = (r50 - cw_r)
    d_div = div50.reindex(rel.index).diff()
    ok = d_div.notna() & rel.notna()
    corr = float(np.corrcoef(d_div[ok], rel[ok])[0, 1])
    print(f"  Correlazione fra variazione mensile di diversita' e sovraperformance")
    print(f"  del diversity-weighted (p=0,50): {corr:+.3f}")
    print(f"  Sotto-periodi, extra-rendimento annuo del DW p=0,50 vs cap-weight:")
    worst = None
    for a, b in (("1990", "1999"), ("2000", "2009"), ("2010", "2014"),
                 ("2015", "2025")):
        x, y = r50.loc[a:b], cw_r.loc[a:b]
        if len(x) < 24:
            continue
        e = (((1 + x).prod() ** (12 / len(x))) - ((1 + y).prod() ** (12 / len(y)))) * 100
        dd = div50.loc[a:b]
        trend = "in calo" if dd.iloc[-1] < dd.iloc[0] else "in salita"
        print(f"    {a}-{b}: {e:+6.2f}%/anno   diversita' {trend}")
        if worst is None or e < worst[1]:
            worst = (f"{a}-{b}", e)
    print(f"  Peggior sotto-periodo: {worst[0]} con {worst[1]:+.2f}%/anno")

    # ---------------------------------------------- orizzonte del teorema
    print("\n--- Orizzonte garantito dal teorema T > 2 log(n)/(eps*delta*p) ----")
    cov_ann = vw_a.cov().to_numpy() * 12.0
    eig = np.linalg.eigvalsh(cov_ann)
    delta = float(eig.min())
    eps = float(1.0 - top1.max() / 100.0)
    print(f"  n = {n}   log(n) = {np.log(n):.3f}")
    print(f"  delta = autovalore minimo della covarianza annualizzata = {delta:.5f}")
    print(f"  eps   = 1 - max quota osservata = 1 - {top1.max()/100:.4f} = {eps:.4f}")
    horiz = {}
    for p in P_GRID:
        T = 2 * np.log(n) / (eps * delta * p)
        horiz[p] = T
        print(f"  p = {p:.2f}  ->  T > {T:>12,.0f} anni")
    print("  Il teorema e' vero. L'orizzonte su cui garantisce l'arbitraggio relativo")
    print("  non ha alcun rapporto con un orizzonte di investimento umano.")

    # ---------------------------------------------- break-even fiscale
    print("\n--- Break-even fiscale del ribilanciamento ------------------------")
    print(f"{'p':>6}{'ribilanc.':>13}{'extra lordo':>13}{'costo transaz.':>16}"
          f"{'costo fiscale':>15}{'extra netto':>13}")
    be_rows = []
    for p in P_GRID:
        for lbl, rb in REBAL.items():
            r, tn = dw_series[(p, lbl)]
            base_cagr = ((1 + cw_r).prod() ** (12 / len(cw_r)) - 1) * 100
            cagr = ((1 + r).prod() ** (12 / len(r)) - 1) * 100
            gross_extra = cagr - base_cagr
            tc = tn.sum() / (len(r) / 12) * C.COST_ROUND_TRIP * 100
            # il ribilanciamento realizza plusvalenze: la parte venduta paga 33%
            pac_dw = simulate_pac(r, CGT_SHARES, realize_frac=tn, periods_per_year=12)
            pac_cw = simulate_pac(cw_r, CGT_SHARES, realize_frac=cw_t, periods_per_year=12)
            tax_drag = pac_cw.irr_annual - pac_dw.irr_annual
            be_rows.append(dict(p=p, rebal=lbl, gross_extra=gross_extra, tc=tc,
                                irr_dw=pac_dw.irr_annual, irr_cw=pac_cw.irr_annual,
                                net_extra=pac_dw.irr_annual - pac_cw.irr_annual,
                                taxes=pac_dw.taxes))
            print(f"{p:>6.2f}{lbl:>13}{gross_extra:>+12.2f}%{tc:>15.2f}%"
                  f"{tax_drag:>+14.2f}%{pac_dw.irr_annual - pac_cw.irr_annual:>+12.2f}%")
    print("  'extra netto' = IRR del PAC diversity-weighted meno IRR del PAC")
    print("  cap-weighted, entrambi con CGT 33% sulle plusvalenze realizzate.")

    OUT.mkdir(exist_ok=True)
    with open(OUT / "group_d.json", "w") as f:
        json.dump({"ew_vs_cw": ew_rows, "dw": dw_rows, "decomp": decomp,
                   "horizon": {str(k): v for k, v in horiz.items()},
                   "delta": delta, "eps": eps, "corr_div": corr,
                   "worst_period": list(worst), "breakeven": be_rows,
                   "diversity": {"top1_last": float(top1.iloc[-1]),
                                 "top1_1990s": float(top1["1990":"1999"].mean()),
                                 "hhi_last": float(hhi.iloc[-1]),
                                 "hhi_1990s": float(hhi["1990":"1999"].mean())}},
                  f, indent=1, default=float)


if __name__ == "__main__":
    main()

"""Giro 11 — Strategie composte.

Tre composizioni, tutte in walk-forward:

  C1  punteggio settoriale misto: invece di mettere insieme due serie di
      rendimenti, fondo i due segnali PRIMA della selezione. I settori sono
      ordinati su una combinazione di momentum a 12 mesi (H5) e bassa
      volatilita' (H4), con peso alpha sul primo. E' una strategia sola, non
      una media di due.
  C2  Gross Profitability LONG-ONLY (Novy-Marx 2013), unico sopravvissuto
      eseguibile del giro 10. Prendo il decile lungo dai portafogli OSAP:
      niente vendite allo scoperto, niente prestito titoli, e il segnale e'
      contabile quindi ruota poco. E' il profilo piu' compatibile con la
      fiscalita' irlandese fra tutti quelli visti.
  C3  media dei flussi di C1 e C2, ribilanciata annualmente.

Ipotesi: la composizione alza lo Sharpe piu' di quanto la rotazione aggiuntiva
costi in imposte. Se il vantaggio dei compositi non supera il migliore dei
singoli, la composizione non serve.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from research import lab, walkforward as WF

ROUND = 11


def sector_panel():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all")
    lg = np.log1p(ind)
    MOM = np.expm1(lg.rolling(12).sum()).shift(2)   # 12-2, niente look-ahead
    VOL = ind.rolling(60).std().shift(1)
    return ind, MOM, VOL


def make_composite(ind, MOM, VOL):
    """C1: selezione su punteggio misto momentum + bassa volatilita'."""
    def build(cfg, idx):
        n_sel, rb, alpha = cfg
        d = ind.reindex(idx).dropna(axis=1)
        if len(d) < 66 or d.shape[1] < n_sel:
            return None, None
        m = MOM.reindex(d.index)[d.columns]
        v = VOL.reindex(d.index)[d.columns]
        rets, turns, w = [], [], None
        for i in range(len(d)):
            if i < 64:
                rets.append(np.nan); turns.append(0.0); continue
            if w is None or i % rb == 0:
                mi, vi = m.iloc[i].dropna(), v.iloc[i].dropna()
                common = mi.index.intersection(vi.index)
                if len(common) < n_sel:
                    rets.append(np.nan); turns.append(0.0); continue
                # rank percentile: momentum alto buono, volatilita' bassa buona
                rm = mi[common].rank(pct=True)
                rv = (-vi[common]).rank(pct=True)
                score = alpha * rm + (1 - alpha) * rv
                sel = score.nlargest(n_sel).index
                new = pd.Series(0.0, index=d.columns)
                new[sel] = 1.0 / n_sel
                turns.append(0.5 * float((new - (w if w is not None else 0)).abs().sum())
                             if w is not None else 1.0)
                w = new
            else:
                turns.append(0.0)
            r = d.iloc[i]
            rets.append(float((w * r).sum()) - turns[-1] * C.COST_ROUND_TRIP)
            g = w * (1 + r); w = g / g.sum()
        s = pd.Series(rets, index=d.index).dropna()
        return s, pd.Series(turns, index=d.index).reindex(s.index)
    return build


def gp_long_only():
    """C2: decile lungo di Gross Profitability dai portafogli OSAP."""
    doc = dataio.osap_signaldoc()
    sign = float(doc.loc["GP", "Sign"]) if "GP" in doc.index else 1.0
    ports = dataio.osap_ports(["GP"])
    ports["port"] = ports["port"].astype(str).str.strip()
    # OSAP non usa sempre i decili: GP e' a quintili (01..05). Prendo l'estremo
    # dalla numerazione effettiva invece di dare per scontato il decile 10.
    buckets = sorted(b for b in ports["port"].unique() if b.isdigit())
    long_port = buckets[-1] if sign > 0 else buckets[0]
    print(f"  bucket disponibili: {buckets}")
    p = ports[ports["port"] == long_port].set_index("date")["ret"].sort_index() / 100.0
    p = p[~p.index.duplicated()]
    print(f"  GP: segno {sign:+.0f}, gamba lunga = decile {long_port}, "
          f"{p.index[0].date()} -> {p.index[-1].date()} ({len(p)} mesi)")
    return p.rename("gp")


def main():
    ff = dataio.ff_factors_monthly()
    rf, eq = ff["RF"], (ff["Mkt-RF"] + ff["RF"]).rename("eq")
    ind, MOM, VOL = sector_panel()
    out = []

    # ---------------------------------------------------------------- C1
    grid1 = [(n, rb, a) for n in (5, 10) for rb in (3, 12)
             for a in (0.0, 0.25, 0.5, 0.75, 1.0)]
    oos, rzs, picks, ne, vsr = WF.walk_forward(make_composite(ind, MOM, VOL), grid1,
                                          ind.index, rf, start_year=1935)
    alphas = [c[2] for _, c in picks]
    r = WF.report("C1 punteggio settoriale misto momentum+low-vol", "H11a",
                  oos, rzs, eq, rf, ne, ROUND,
                  extra=f"alpha scelto piu' spesso: {max(set(alphas), key=alphas.count)}")
    if r:
        out.append(r)

    # ---------------------------------------------------------------- C2
    print("\ncaricamento portafogli OSAP per Gross Profitability...")
    gp = gp_long_only()
    gp_df = pd.DataFrame({"gp": gp}).dropna()

    def build_gp(cfg, idx):
        (rb,) = cfg
        d = gp_df.reindex(idx).dropna()
        if len(d) < 60:
            return None, None
        # il decile e' gia' un portafoglio ribilanciato: il turnover che pago
        # e' quello del portafoglio, non una mia scelta. rb qui controlla solo
        # con che frequenza rientro sul segnale aggiornato.
        s = d["gp"]
        turn = pd.Series(1.0 / rb, index=d.index)   # quota realizzata per periodo
        return s - turn * C.COST_ROUND_TRIP, turn

    oos2, rz2, picks2, ne2, vsr2 = WF.walk_forward(build_gp, [(1,), (3,), (12,)],
                                             gp_df.index, rf, start_year=1985,
                                             min_train_months=180)
    r2 = WF.report("C2 Gross Profitability long-only (decile lungo)", "H11b",
                   oos2, rz2, eq, rf, ne2, ROUND,
                   extra="Novy-Marx 2013, unico sopravvissuto VW del giro 10", var_sr=vsr2)
    if r2:
        out.append(r2)

    # ---------------------------------------------------------------- C3
    if r and r2:
        common = r["ret"].index.intersection(r2["ret"].index)
        if len(common) >= 60:
            mix = 0.5 * r["ret"].reindex(common) + 0.5 * r2["ret"].reindex(common)
            rzm = pd.Series(0.5, index=common)   # entrambe ruotano
            r3 = WF.report("C3 media di C1 e C2", "H11c", mix, rzm, eq, rf,
                           ne + ne2, ROUND,
                           extra=f"finestra comune {common[0].date()}->{common[-1].date()}", var_sr=vsr)
            if r3:
                out.append(r3)
        else:
            print("\nH11c — finestra comune troppo corta, non valutabile")

    print(f"\n{'='*74}\nRIEPILOGO GIRO 11")
    print(f"{'ip.':<7}{'strategia':<46}{'vs B&H':>9}{'DSR':>8}{'esito':>14}")
    for x in sorted(out, key=lambda d: -d["excess"]):
        print(f"{x['hyp']:<7}{x['name'][:45]:<46}{x['excess']:>+8.2f}%"
              f"{x['dsr']:>8.3f}{x['verdict']:>14}")
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")
    return out


if __name__ == "__main__":
    main()

"""Giro 27 — Opzioni e stock picking.

DUE DOMANDE MOLTO DIVERSE PER TESTABILITA'.

STOCK PICKING. In larga parte l'ho gia' testato senza chiamarlo cosi': il
giro 10 ha passato al setaccio 201 anomalie pubblicate (valore, qualita',
momentum, accruals, short interest...), che SONO segnali di selezione titoli.
Ne sopravvivono 2 a tutti i filtri, e il filtro che decide e' la
costruzione: solo 22 su 201 sono value-weighted, il resto e' guidato da
microcap non eseguibili. Quello che resta fuori e' la selezione
discrezionale, che non e' backtestabile per costruzione: non esiste una
serie storica delle idee che avresti avuto.

OPZIONI. Qui invece ci sono dati veri e la domanda e' netta. Il premio al
rischio di volatilita' (la volatilita' implicita eccede sistematicamente
quella realizzata) e' uno dei fatti empirici piu' solidi della finanza, e
si incassa VENDENDO opzioni. CBOE pubblica gli indici delle due strategie
canoniche, con metodologia documentata e storia lunga:

    BXM  BuyWrite: comprare l'S&P 500 e vendere call coperte, dal 2002
    PUT  PutWrite: vendere put cash-secured sull'S&P 500, dal 1991

Non sono simulazioni mie: sono gli indici ufficiali. Il test e' se quel
premio, reale e documentato, sopravvive alla fiscalita' irlandese.

Le opzioni hanno pero' una caratteristica che il solo Sharpe non cattura:
vendere volatilita' produce molti guadagni piccoli e poche perdite enormi.
Misuro quindi anche asimmetria, curtosi e peggior mese.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES, TRADING_52, first_of_month
from research import lab
from research.round25 import _stats

ROUND = 27
DATA = Path(__file__).resolve().parents[2] / "data"
OUT = Path(__file__).resolve().parents[2] / "out"


def cboe(name, col=None, daily_only=False):
    """Serie CBOE. `daily_only` taglia il periodo iniziale in cui il file NON
    e' giornaliero: la storia di PUT contiene osservazioni sparse fra il 1991
    e il 2006 (1994, 1997, 2001, 2004...), e calcolarci sopra un pct_change
    produce 'rendimenti giornalieri' del +72% che falsano CAGR, asimmetria e
    curtosi. Tengo solo gli anni con almeno 200 osservazioni."""
    d = pd.read_csv(DATA / f"cboe_{name}.csv")
    d.columns = [c.strip().upper() for c in d.columns]
    d["DATE"] = pd.to_datetime(d["DATE"], format="%m/%d/%Y", errors="coerce")
    d = d.dropna(subset=["DATE"]).set_index("DATE").sort_index()
    c = col or ("CLOSE" if "CLOSE" in d.columns else d.columns[0])
    out = pd.to_numeric(d[c], errors="coerce").dropna()
    if daily_only:
        cnt = out.groupby(out.index.year).size()
        good = cnt[cnt >= 200].index
        if len(good):
            out = out[(out.index.year >= good.min()) & (out.index.year <= good.max())]
    return out


def main():
    vix = cboe("VIX", "CLOSE")
    bxm = cboe("BXM", daily_only=True)
    put = cboe("PUT", daily_only=True)
    ffd = dataio.ff_factors_daily()
    mkt = (ffd["Mkt-RF"] + ffd["RF"]).dropna()
    rf = ffd["RF"]

    # ============================================ 1. il premio esiste?
    print("=" * 84)
    print("1. IL PREMIO AL RISCHIO DI VOLATILITA' ESISTE DAVVERO?")
    print("=" * 84)
    print("   Confronto il VIX (volatilita' implicita a 30 giorni) con la")
    print("   volatilita' REALIZZATA nei 21 giorni successivi.\n")
    rv = (mkt.rolling(21).std() * np.sqrt(252) * 100).shift(-21)
    j = pd.concat([vix.rename("implicita"), rv.rename("realizzata")],
                  axis=1).dropna()
    j["premio"] = j["implicita"] - j["realizzata"]
    t = st.ttest_1samp(j["premio"], 0)
    print(f"   osservazioni                 {len(j):>10,}")
    print(f"   implicita media              {j['implicita'].mean():>9.2f}%")
    print(f"   realizzata media             {j['realizzata'].mean():>9.2f}%")
    print(f"   premio medio                 {j['premio'].mean():>9.2f} punti "
          f"(t = {t.statistic:.1f})")
    print(f"   quota di giorni con premio>0 {(j['premio']>0).mean()*100:>9.1f}%")
    for a, b in [("1990", "1999"), ("2000", "2009"), ("2010", "2019"),
                 ("2020", "2026")]:
        s = j.loc[a:b, "premio"]
        if len(s) > 200:
            print(f"     {a}-{b}: {s.mean():+6.2f} punti, "
                  f"positivo il {(s>0).mean()*100:.0f}% dei giorni")
    print("\n   Il premio c'e', e' grande e non decade. E' il fatto piu' solido")
    print("   incontrato in tutto lo studio. Ora: si puo' incassare?")

    # ============================================ 2. le strategie CBOE
    print(f"\n{'='*84}")
    print("2. LE DUE STRATEGIE CANONICHE, INDICI UFFICIALI CBOE")
    print("=" * 84)
    rows = []
    for name, ser, desc in (("PUT", put, "vendita put cash-secured"),
                            ("BXM", bxm, "covered call (long indice + call venduta)")):
        r = ser.pct_change().dropna()
        idx = r.index.intersection(mkt.index)
        r, m = r.reindex(idx), mkt.reindex(idx)
        s, b = _stats(r, 252), _stats(m, 252)
        sk, ku = float(st.skew(r)), float(st.kurtosis(r, fisher=False))
        worst = float(r.resample("ME").apply(lambda x: (1 + x).prod() - 1).min())
        print(f"\n   {name} — {desc}")
        print(f"   finestra {idx[0].date()} -> {idx[-1].date()} ({len(idx)} sedute)")
        print(f"   {'':<22}{'CAGR':>9}{'Sharpe':>8}{'DD':>9}{'skew':>8}"
              f"{'curtosi':>9}{'peggior mese':>14}")
        print(f"   {name:<22}{s['cagr']:>8.2f}%{s['sharpe']:>8.2f}{s['dd']:>8.1f}%"
              f"{sk:>8.2f}{ku:>9.1f}{worst*100:>13.1f}%")
        bsk = float(st.skew(m)); bku = float(st.kurtosis(m, fisher=False))
        bworst = float(m.resample("ME").apply(lambda x: (1 + x).prod() - 1).min())
        print(f"   {'indice (confronto)':<22}{b['cagr']:>8.2f}%{b['sharpe']:>8.2f}"
              f"{b['dd']:>8.1f}%{bsk:>8.2f}{bku:>9.1f}{bworst*100:>13.1f}%")
        rows.append(dict(name=name, ret=r, mkt=m, **s, skew=sk, kurt=ku,
                         worst=worst * 100, bench_sharpe=b["sharpe"],
                         bench_cagr=b["cagr"]))

    # ============================================ 3. netto imposte
    print(f"\n{'='*84}")
    print("3. NETTO DI FISCALITA' IRLANDESE")
    print("=" * 84)
    print("   Le strategie in opzioni ruotano per costruzione: BXM e PUT")
    print("   scrivono una nuova opzione OGNI MESE alla scadenza. Sono dodici")
    print("   realizzi l'anno, il che porta dritti allo scenario 52%.\n")
    print(f"   {'strategia':<30}{'IRR 33%':>10}{'IRR 52%':>10}{'vs B&H':>10}")
    for r in rows:
        idx = r["ret"].index
        rf0 = rf.reindex(idx).fillna(0.0)
        con = first_of_month(idx)
        # realizzo mensile: alla scadenza l'opzione si chiude
        rz = pd.Series(0.0, index=idx)
        rz[con.to_numpy()] = 1.0
        a33 = simulate_pac(r["ret"], CGT_SHARES, rf=rf0, realize_frac=rz,
                           periods_per_year=252, contrib_on=con)
        a52 = simulate_pac(r["ret"], TRADING_52, rf=rf0, realize_frac=rz,
                           periods_per_year=252, contrib_on=con)
        bb = simulate_pac(r["mkt"], CGT_SHARES, rf=rf0, periods_per_year=252,
                          contrib_on=con)
        r["irr33"], r["irr52"] = a33.irr_annual, a52.irr_annual
        r["vs"] = a33.irr_annual - bb.irr_annual
        r["bench_irr"] = bb.irr_annual
        print(f"   {r['name'] + ' (' + str(idx[0].year) + '-' + str(idx[-1].year) + ')':<30}"
              f"{a33.irr_annual:>9.2f}%{a52.irr_annual:>9.2f}%{r['vs']:>+9.2f}%")
        print(f"   {'  buy&hold stessa finestra':<30}{bb.irr_annual:>9.2f}%"
              f"{'—':>10}{0.0:>+9.2f}%")

    # ============================================ 4. la coda
    print(f"\n{'='*84}")
    print("4. LA FORMA DEL RISCHIO, CHE LO SHARPE NON MOSTRA")
    print("=" * 84)
    for r in rows:
        x = r["ret"]
        q01 = float(np.percentile(x, 1)) * 100
        n5 = int((x < -0.05).sum())
        print(f"   {r['name']}: skew {r['skew']:+.2f} contro {float(st.skew(r['mkt'])):+.2f} "
              f"dell'indice · 1° percentile {q01:.2f}% · "
              f"{n5} giorni sotto -5%")
    print("\n   Vendere volatilita' produce molti guadagni piccoli e poche")
    print("   perdite grandi. Su un PAC ventennale non e' un dettaglio: e' la")
    print("   differenza fra tenere la posizione e chiuderla nel momento peggiore.")

    # ============================================ 5. stock picking
    print(f"\n{'='*84}")
    print("5. STOCK PICKING: COSA E' GIA' STATO TESTATO")
    print("=" * 84)
    try:
        surv = pd.read_csv(Path(__file__).resolve().parents[2] /
                           "research" / "osap_survivors.csv")
        print(f"   Anomalie di selezione titoli passate al setaccio al giro 10: 201")
        print(f"   Sopravvissute a t>2, value-weighted, quantile>=10%, "
              f"netto costi: {len(surv)}")
        for _, s in surv.iterrows():
            print(f"     {s['acr']:<18}{s['authors'][:26]:<28}{s['year']}  "
                  f"netto {s['net']:.2f}%/anno, t={s['t']:.2f}")
    except FileNotFoundError:
        print("   (esegui prima round10)")
    print(f"\n   Il filtro che decide non e' la significativita' ma la")
    print(f"   COSTRUZIONE: 22 anomalie su 201 sono value-weighted. Le altre")
    print(f"   pesano allo stesso modo una societa' da 20 milioni e Apple, e")
    print(f"   con 500 EUR/mese non sono eseguibili su nessuna delle due gambe.")

    n_cum = lab.n_trials_so_far()
    best = max(rows, key=lambda r: r["vs"])
    d = lab.deflated_sharpe(best["ret"], n_cum + len(rows), round_id=ROUND)
    print(f"\n   DSR di {best['name']} su {n_cum+len(rows)} tentativi: "
          f"{d['dsr']:.3f}  (batte il B&H: {'si' if best['vs']>0 else 'NO'})")

    lab.log_trials([dict(round=ROUND, hypothesis="H29 opzioni CBOE",
                         config=r["name"], window="1991-2026" if r["name"] == "PUT"
                         else "2002-2026", sharpe=r["sharpe"], irr=r["irr33"],
                         bh_irr=r["bench_irr"], excess=r["vs"],
                         n_obs=len(r["ret"]),
                         note=f"skew={r['skew']:.2f},worst={r['worst']:.1f}%")
                    for r in rows])
    pd.DataFrame([{k: v for k, v in r.items() if k not in ("ret", "mkt")}
                  for r in rows]).to_csv(OUT / "round27_options.csv", index=False)
    j.to_csv(OUT / "round27_vrp.csv")
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

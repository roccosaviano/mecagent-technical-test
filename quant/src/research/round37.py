"""Giro 37 — B1 (materie prime) e B2 (valute).

DUE VOCI DELLA CODA, predizioni verbatim.

B1 — Materie prime (petrolio WTI, FRED DCOILWTICO dal 1986)
  Trend following e carry sul future proxy.
  PREDIZIONE: il trend following su materie prime funziona lordo (e' il caso
  canonico dei CTA) e muore sui costi piu' le imposte, come sull'azionario.
  FALSIFICATA SE: IRR netta > buy&hold azionario.

B2 — Valute (DEXUSEU, DEXJPUS, DEXCHUS) — carry e momentum
  PREDIZIONE: il carry ha premio positivo ma skew fortemente negativa, e le tre
  valute non bastano a diversificare il rischio di crash.
  FALSIFICATA SE: Sharpe > 0,5 con skew > -0,5 dopo costi.

DUE AVVERTENZE SUI DATI, dichiarate prima dei numeri.

  Il WTI di FRED e' un PREZZO SPOT, non un investimento. Chi compra petrolio
  paga il roll dei futures, storicamente la componente dominante e spesso
  negativa (contango). Tutti i numeri di B1 sono quindi un LIMITE SUPERIORE:
  la strategia vera renderebbe meno. Se perde anche cosi', il verdetto e' solido;
  se vincesse, non potrei concluderne niente.

  Il carry valutario richiede i tassi esteri. EUR e JPY li ho (FRED IR3TIB01*),
  lo yuan NO: non c'e' una serie di tasso interbancario cinese confrontabile, ed
  e' una valuta amministrata, dove il carry non e' un premio di rischio ma una
  scelta di politica. CNY resta quindi nel momentum e fuori dal carry, dichiarato.
  Aggiungo GBP come controllo di robustezza DICHIARATO, non come sostituzione.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from research import lab, bench as B, multidata as M

ROUND = 37
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 56


def monthly_last(s):
    m = s.resample("ME").last()
    m.index = m.index.to_period("M").to_timestamp("M")
    return m


def main():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()

    # =============================================================== B1
    print(f"{'='*92}\nB1 — materie prime: trend following sul WTI\n{'='*92}")
    wti = monthly_last(M.fred("DCOILWTICO"))
    r = wti.pct_change().dropna()
    print(f"   WTI spot {r.index[0].date()} -> {r.index[-1].date()} "
          f"({len(r)} mesi)")
    print(f"   ATTENZIONE: prezzo spot, senza roll. I numeri sono un limite")
    print(f"   SUPERIORE del rendimento davvero ottenibile.\n")
    rf0 = rf.reindex(r.index).fillna(0.0)
    rows1 = [B.eval_stream("WTI buy&hold", r, rf0),
             B.eval_stream("azionario (benchmark)", mkt.reindex(r.index).dropna(),
                           rf0)]
    px = wti.reindex(r.index)
    for lb in (6, 10, 12):
        e = B.ma_filter(px, lb)
        rows1.append(B.eval_exposure(f"WTI trend MA{lb}", r, rf0, e))
    for lb in (6, 12):
        sig = (px / px.shift(lb) - 1).shift(1)
        e = (sig > 0).astype(float)
        rows1.append(B.eval_exposure(f"WTI momentum {lb}m", r, rf0, e))
    B.table(rows1)
    bh_eq = next(x for x in rows1 if x["label"].startswith("azionario"))
    trend = [x for x in rows1 if "trend" in x["label"] or "momentum" in x["label"]]
    print(f"\n   Il trend following funziona LORDO sul WTI? "
          f"{'SI' if max(t['cagr'] for t in trend) > rows1[0]['cagr'] else 'NO'}"
          f"  (miglior CAGR trend {max(t['cagr'] for t in trend):.2f}% contro "
          f"{rows1[0]['cagr']:.2f}% del buy&hold)")
    b1_fals = any(t["irr_ref"] > bh_eq["irr"] for t in trend)
    print(f"   Qualche configurazione batte l'azionario netto imposte? "
          f"{'SI' if b1_fals else 'NO'}")
    print(f"   -> ipotesi B1 {'FALSIFICATA' if b1_fals else 'CONFERMATA'}")
    print(f"   Carry sul future: NON TESTABILE, non ho la curva dei futures.")

    # =============================================================== B2
    print(f"\n{'='*92}\nB2 — valute: carry e momentum\n{'='*92}")
    # rendimento di detenere la valuta estera contro USD
    fx = {}
    fx["EUR"] = monthly_last(M.fred("DEXUSEU"))               # USD per EUR
    fx["JPY"] = 1.0 / monthly_last(M.fred("DEXJPUS"))         # JPY per USD -> USD per JPY
    fx["CNY"] = 1.0 / monthly_last(M.fred("DEXCHUS"))
    fx["GBP"] = monthly_last(M.fred("DEXUSUK"))
    us = monthly_last(M.fred("TB3MS")) / 100.0
    fr = {"EUR": monthly_last(M.fred("IR3TIB01EZM156N")) / 100.0,
          "JPY": monthly_last(M.fred("IR3TIB01JPM156N")) / 100.0,
          "GBP": monthly_last(M.fred("IR3TIB01GBM156N")) / 100.0}

    spot = pd.DataFrame(fx).dropna(how="all")
    sret = spot.pct_change()
    # rendimento totale = variazione del cambio + tasso estero - tasso USA
    carry = pd.DataFrame({k: (fr[k] - us).reindex(spot.index).ffill() / 12.0
                          for k in fr})
    # NIENTE fill_value: sommare il carry dove il cambio non esiste ancora
    # fabbricherebbe un asset senza rischio di cambio. Il carry mancante (CNY)
    # vale zero, il CAMBIO mancante deve restare NaN.
    tot = sret + carry.reindex(sret.index).reindex(columns=sret.columns).fillna(0.0)

    decl = ["EUR", "JPY", "CNY"]
    sub = tot[decl].dropna()
    print(f"   Le tre valute dichiarate: {', '.join(decl)}")
    print(f"   Finestra comune {sub.index[0].date()} -> {sub.index[-1].date()} "
          f"({len(sub)} mesi)")
    print(f"   CNY: senza tasso interbancario confrontabile, entra solo nel")
    print(f"   momentum. E' anche una valuta amministrata, dove il carry non e'")
    print(f"   un premio di rischio ma una scelta di politica monetaria.\n")

    rf1 = rf.reindex(sub.index).fillna(0.0)
    rows2 = []
    # carry: lunga la valuta col differenziale piu' alto, corta la piu' bassa
    cav = carry[["EUR", "JPY"]].reindex(sub.index).ffill()
    sig = cav.shift(1)
    wc = pd.DataFrame(0.0, index=sub.index, columns=["EUR", "JPY"])
    wc[sig.rank(axis=1, ascending=False) == 1] = 1.0
    wc[sig.rank(axis=1, ascending=False) == 2] = -1.0
    net_c, turn_c = B.wbacktest(tot[["EUR", "JPY"]].reindex(sub.index).fillna(0.0),
                                wc.shift(1).fillna(0.0))
    rows2.append(B.eval_stream("carry EUR/JPY long-short", net_c.dropna(), rf1,
                               turn_c))
    # momentum a 12 mesi, long-short fra le tre dichiarate
    mom = (1 + sub).rolling(12).apply(np.prod, raw=True).shift(1)
    wm = pd.DataFrame(0.0, index=sub.index, columns=decl)
    wm[mom.rank(axis=1, ascending=False) == 1] = 1.0
    wm[mom.rank(axis=1, ascending=False) == 3] = -1.0
    net_m, turn_m = B.wbacktest(sub, wm.shift(1).fillna(0.0))
    rows2.append(B.eval_stream("momentum 12m long-short", net_m.dropna(), rf1,
                               turn_m))
    # long-only sulle tre, equal weight
    rows2.append(B.eval_stream("3 valute equal-weight long", sub.mean(axis=1),
                               rf1))
    # robustezza dichiarata: aggiungendo GBP al carry
    cav4 = carry[["EUR", "JPY", "GBP"]].dropna()
    s4 = tot[["EUR", "JPY", "GBP"]].reindex(cav4.index).dropna()
    if len(s4) > 60:
        sg = cav4.reindex(s4.index).shift(1)
        w4 = pd.DataFrame(0.0, index=s4.index, columns=s4.columns)
        w4[sg.rank(axis=1, ascending=False) == 1] = 1.0
        w4[sg.rank(axis=1, ascending=False) == 3] = -1.0
        n4, t4 = B.wbacktest(s4, w4.shift(1).fillna(0.0))
        rows2.append(B.eval_stream("carry +GBP (robustezza)", n4.dropna(),
                                   rf.reindex(n4.index).fillna(0.0), t4))
    print()
    B.table(rows2, cols=("label", "cagr", "vol", "sharpe", "skew", "dd", "turn",
                         "irr"))

    print(f"\n   Condizione di falsificazione: Sharpe > 0,5 CON skew > -0,5.")
    for r_ in rows2:
        ok = r_["sharpe"] > 0.5 and r_["skew"] > -0.5
        print(f"     {r_['label']:<28} Sharpe {r_['sharpe']:>5.2f} · skew "
              f"{r_['skew']:>6.2f}  -> {'PASSA' if ok else 'no'}")
    b2_fals = any(r_["sharpe"] > 0.5 and r_["skew"] > -0.5 for r_ in rows2)
    print(f"   -> ipotesi B2 {'FALSIFICATA' if b2_fals else 'CONFERMATA'}")

    # ---------------------------------------------------------------
    # VERIFICA DELLA FALSIFICAZIONE. E' la prima della coda, e una
    # falsificazione merita piu' scrutinio di una conferma. Il sospetto
    # specifico: lo yuan e' stato AGGANCIATO al dollaro fino al luglio 2005.
    # Una valuta a rendimento quasi nullo dentro un long/short a tre finisce
    # sistematicamente in una posizione di rango, e puo' generare un segnale
    # che non e' un premio ma un artefatto del regime di cambio.
    if b2_fals:
        print(f"\n   {'-'*84}")
        print(f"   VERIFICA — la falsificazione regge?")
        print(f"   {'-'*84}")
        checks = []
        def mom_ls(cols, name, src=None):
            src = src if src is not None else tot
            d = src[cols].dropna()
            if len(d) < 60:
                return None
            m = (1 + d).rolling(12).apply(np.prod, raw=True).shift(1)
            w = pd.DataFrame(0.0, index=d.index, columns=cols)
            w[m.rank(axis=1, ascending=False) == 1] = 1.0
            w[m.rank(axis=1, ascending=False) == len(cols)] = -1.0
            n, t = B.wbacktest(d, w.shift(1).fillna(0.0))
            return B.eval_stream(name, n.dropna(),
                                 rf.reindex(n.index).fillna(0.0), t)
        for cols, nm in ((["EUR", "JPY", "CNY"], "dichiarato EUR/JPY/CNY"),
                         (["EUR", "JPY", "GBP"], "senza CNY: EUR/JPY/GBP"),
                         (["EUR", "JPY", "GBP", "CNY"], "quattro valute")):
            c = mom_ls(cols, nm)
            if c:
                checks.append(c)
        # sottoperiodi: prima e dopo lo sgancio dello yuan (luglio 2005)
        d = tot[decl].dropna()
        for lo, hi, nm in ((None, "2005-07", "EUR/JPY/CNY fino al 2005-07"),
                           ("2005-08", None, "EUR/JPY/CNY dal 2005-08")):
            seg = d.loc[lo:hi]
            if len(seg) > 60:
                c = mom_ls(decl, nm, src=seg)
                if c:
                    checks.append(c)
        B.table(checks, cols=("label", "cagr", "vol", "sharpe", "skew", "dd",
                              "turn", "irr"))
        passes = [c for c in checks if c["sharpe"] > 0.5 and c["skew"] > -0.5]
        print(f"\n   Passano la condizione in {len(passes)}/{len(checks)} varianti")
        base = checks[0]
        dd = lab.deflated_sharpe(base["gross"], N_PREREG, round_id=ROUND)
        print(f"   DSR del caso dichiarato su N={N_PREREG}: {dd['dsr']:.3f}")
        print(f"   Turnover {base['turn']:.2f}x l'anno -> oltre il 100%, "
              f"l'aliquota di riferimento e' il 52%: IRR {base['irr52']:.2f}%")
        print(f"   contro {bh_eq['irr']:.2f}% dell'azionario "
              f"({base['irr52']-bh_eq['irr']:+.2f} punti).")
        print(f"\n   LETTURA: la condizione di falsificazione di B2 e' scritta su")
        print(f"   Sharpe e skew, non sul montante. Puo' quindi essere superata da")
        print(f"   una strategia che resta comunque inutile per un PAC. Le due cose")
        print(f"   vanno tenute separate e riportate entrambe.")
        rows2.extend(checks)

    allr = rows1 + rows2
    lab.log_trials([dict(round=ROUND,
                         hypothesis=("B1 materie prime" if r_ in rows1
                                     else "B2 valute carry e momentum"),
                         config=r_["label"], window="varie", sharpe=r_["sharpe"],
                         irr=r_["irr"], bh_irr=bh_eq["irr"],
                         excess=r_["irr_ref"] - bh_eq["irr"], n_obs=r_["n"],
                         note=f"skew={r_['skew']:.2f},turn={r_['turn']:.2f}x")
                    for r_ in allr])
    pd.DataFrame([{k: v for k, v in r_.items() if k != "gross"}
                  for r_ in allr]).to_csv(OUT / "round37_b1b2.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

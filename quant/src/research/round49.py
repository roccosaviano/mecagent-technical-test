"""Giro 49 — E2, E3, E4, E5: comprare e vendere opzioni.

QUATTRO VOCI DELLA CODA, predizioni verbatim (abbreviate qui, integrali in
QUEUE.md), tutte scritte e committate PRIMA di eseguire.

E2 comprare opzioni: ogni configurazione long ha IRR netta negativa; le put
   perdono piu' delle call. FALSIFICATA SE una qualunque long ha IRR positiva.
E3 vendere put cash-secured: Sharpe lordo sopra il buy&hold, IRR netta sotto,
   perche' 12 realizzi l'anno contro il differimento trentennale del buy&hold.
   FALSIFICATA SE IRR netta > buy&hold.
E4 covered call: piu' OTM, piu' piccoli sia il taglio di volatilita' sia il
   costo; nessuna batte il buy&hold; l'ATM perde di piu'.
   FALSIFICATA SE una qualunque configurazione batte il buy&hold.
E5 LEAPS come leva: il finanziamento incorporato costa meno di rf+3%, ma il
   rollo annuale realizza ogni anno e il drag fiscale supera il risparmio.
   FALSIFICATA SE IRR netta >= buy&hold.

IL SIMULATORE. Tarato al giro 48: scadenze al terzo venerdi', IV = 0,85 x VIX.
Il cancello E0 e' aperto — BXM +0,55 e PUT -0,72 punti di CAGR contro gli indici
reali, correlazione 0,975 e 0,978. Il fattore 0,85 e' UN parametro tarato, sui
due indici CBOE e non su nessuna delle strategie qui sotto.

FISCALITA'. Ogni scadenza chiude la posizione, quindi realizza. Le conseguenze
non sono uguali per tutte le voci e sono il cuore di E3 e E5:
  E2, E3   posizione interamente chiusa ogni mese -> 12 realizzi l'anno
  E4       la parte azionaria resta, si realizza solo il flusso dell'opzione
  E5       rollo annuale -> 1 realizzo l'anno
Sopra il 100% di rotazione l'aliquota di riferimento e' il 52%, come per tutto
il resto del progetto.
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
from research import lab, bench as B, options as O

ROUND = 49
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 66
IV_K = 0.85            # tarato al giro 48 su BXM e PUT


def to_monthly(s):
    """Serie indicizzata sulle scadenze -> indice mensile, per il motore PAC."""
    out = s.copy()
    out.index = pd.DatetimeIndex(out.index).to_period("M").to_timestamp("M")
    return out[~out.index.duplicated(keep="last")]


def main():
    d, q = O.market_data()
    ff = dataio.ff_factors_monthly()
    rf_m = ff["RF"]

    # sottostante di riferimento sulla stessa finestra e stesse scadenze
    base = O.roll_short_option(d, q, kind="c", moneyness=1.0, iv_scale=IV_K)
    idx = base.index
    eq = to_monthly(base["tr"])
    rf0 = rf_m.reindex(eq.index).fillna(0.0)
    bh = B.eval_stream("azionario buy&hold (bench)", eq, rf0)
    print(f"Finestra {idx[0].date()} -> {idx[-1].date()} ({len(idx)} scadenze)")
    print(f"IV = {IV_K:.2f} x VIX, scadenze al terzo venerdi' (tarato al giro 48)")
    print(f"Benchmark: PAC azionario, IRR netta {bh['irr']:.2f}%\n")

    def leg(kind, mny, freq="3F"):
        return O.roll_short_option(d, q, kind=kind, moneyness=mny, freq=freq,
                                   iv_scale=IV_K)

    rows_all = {}

    # ================================================================ E2
    print(f"{'='*96}\nE2 — COMPRARE OPZIONI\n{'='*96}")
    print("   Liquidita' al risk-free piu' l'opzione comprata, nozionale pari al")
    print("   portafoglio. E' la versione interamente finanziata: nessuna leva.\n")
    r2 = []
    for kind, nm in (("c", "call"), ("p", "put")):
        for mny, lbl in ((1.00, "ATM"), (1.05 if kind == "c" else 0.95, "5% OTM")):
            x = leg(kind, mny)
            net = x["rf"] * x["T"] - x["premium"] + x["payoff"]
            s = to_monthly(net)
            rz = pd.Series(1.0, index=s.index)     # chiusa ogni scadenza
            r = B.eval_stream(f"long {nm} {lbl}", s, rf0.reindex(s.index), rz)
            r["premio_annuo"] = float(x["premium"].sum()) / (len(x) / 12)
            r2.append(r)
    B.table(r2, cols=("label", "cagr", "vol", "sharpe", "skew", "dd", "turn", "irr", "irr52"))
    print(f"\n   Premio pagato in un anno, in frazione del nozionale:")
    for r in r2:
        print(f"     {r['label']:<20}{r['premio_annuo']:>7.1%}")
    e2_fals = any(r["irr_ref"] > 0 for r in r2)
    print(f"\n   Qualche configurazione long ha IRR netta positiva? "
          f"{'SI' if e2_fals else 'NO'}")
    print(f"   -> ipotesi E2 {'FALSIFICATA' if e2_fals else 'CONFERMATA'}")
    put_loss = min(r["irr"] for r in r2 if "put" in r["label"])
    call_loss = min(r["irr"] for r in r2 if "call" in r["label"])
    print(f"   Le put perdono piu' delle call? "
          f"{'SI' if put_loss < call_loss else 'NO'} "
          f"(peggior put {put_loss:.2f}% contro peggior call {call_loss:.2f}%)")
    rows_all["E2"] = r2

    # ================================================================ E3
    print(f"\n{'='*96}\nE3 — VENDERE PUT CASH-SECURED\n{'='*96}")
    print("   Interamente collateralizzate: la liquidita' copre lo strike, nessuna")
    print("   leva e nessun margine. E' il profilo dell'indice PUT del CBOE.\n")
    r3 = [bh]
    for mny, lbl in ((1.00, "ATM"), (0.95, "5% OTM"), (0.90, "10% OTM")):
        x = leg("p", mny)
        net = x["rf"] * x["T"] + x["premium"] - x["payoff"]
        s = to_monthly(net)
        rz = pd.Series(1.0, index=s.index)
        r3.append(B.eval_stream(f"short put {lbl}", s, rf0.reindex(s.index), rz))
    B.table(r3, cols=("label", "cagr", "vol", "sharpe", "skew", "dd", "turn", "irr", "irr52"))
    cand3 = r3[1:]
    print(f"\n   Sharpe lordo sopra il buy&hold? "
          f"{'SI' if max(r['sharpe'] for r in cand3) > bh['sharpe'] else 'NO'} "
          f"(migliore {max(r['sharpe'] for r in cand3):.2f} contro {bh['sharpe']:.2f})")
    for r in cand3:
        print(f"     {r['label']:<18} IRR di riferimento {r['irr_ref']:>6.2f}% "
              f"(aliquota {r['rate_ref']}%, {r['turn']:.1f} realizzi/anno) contro "
              f"{bh['irr']:.2f}%  -> {r['irr_ref']-bh['irr']:+.2f}")
    e3_fals = any(r["irr_ref"] > bh["irr"] for r in cand3)
    print(f"   -> ipotesi E3 {'FALSIFICATA' if e3_fals else 'CONFERMATA'}")
    rows_all["E3"] = cand3

    # ================================================================ E4
    print(f"\n{'='*96}\nE4 — COVERED CALL SU UN PAC AZIONARIO\n{'='*96}")
    print("   ATTENZIONE. Vendere call OTM e' l'unico caso in cui la volatilita'")
    print("   piatta e' OTTIMISTICA, ed era dichiarato in coda. La misura dello")
    print("   scostamento contro i tre indici CBOE reali:")
    print("     BXM  (ATM)     simulato +0,55 punti sopra il reale")
    print("     BXY  (2% OTM)  simulato +1,51 punti sopra il reale")
    print("     BXMD (5% OTM)  simulato +2,56 punti sopra il reale")
    print("   L'errore CRESCE con la moneyness, come impone lo skew. Quindi qui")
    print("   NON uso il simulatore: uso i tre indici REALI, che non hanno")
    print("   parametri tarati e sono strategie realmente quotate.")
    print("   Trattamento fiscale piu' generoso possibile per la covered call:")
    print("   la tratto come un buy&hold con un solo realizzo finale. Se perde")
    print("   anche cosi', il verdetto e' solido a maggior ragione.\n")
    from research.round27 import cboe as _cboe
    r4 = []
    real_series = {}
    for nm, lbl in (("BXM", "BXM  covered call ATM"),
                    ("BXY", "BXY  covered call +2%"),
                    ("BXMD", "BXMD covered call ~5%")):
        try:
            rr = _cboe(nm, daily_only=True).resample("ME").last().pct_change().dropna()
        except Exception:
            print(f"   {nm} non disponibile")
            continue
        rr.index = rr.index.to_period("M").to_timestamp("M")
        real_series[nm] = rr
    ix4 = None
    for rr in real_series.values():
        ix4 = rr.index if ix4 is None else ix4.intersection(rr.index)
    ix4 = ix4.intersection(eq.index)
    bh4 = B.eval_stream("azionario buy&hold (bench)", eq.reindex(ix4),
                        rf0.reindex(ix4))
    r4.append(bh4)
    for nm, lbl in (("BXM", "BXM  covered call ATM"),
                    ("BXY", "BXY  covered call +2%"),
                    ("BXMD", "BXMD covered call ~5%")):
        if nm in real_series:
            r4.append(B.eval_stream(lbl, real_series[nm].reindex(ix4),
                                    rf0.reindex(ix4)))
    print(f"   Finestra comune ai tre indici: {ix4[0].date()} -> {ix4[-1].date()} "
          f"({len(ix4)} mesi)\n")
    B.table(r4, cols=("label", "cagr", "vol", "sharpe", "skew", "dd", "turn", "irr", "irr52"))
    cand4 = r4[1:]
    print(f"\n   Piu' OTM = meno taglio di volatilita' E meno costo?")
    for r in cand4:
        print(f"     {r['label']:<24} vol {r['vol']:>5.1f}% (contro {bh4['vol']:.1f}%)"
              f"   IRR {r['irr_ref']:>6.2f}%  ({r['irr_ref']-bh4['irr']:+.2f})")
    mono = (len(cand4) == 3 and cand4[0]["vol"] < cand4[1]["vol"] < cand4[2]["vol"]
            and cand4[0]["irr_ref"] < cand4[2]["irr_ref"])
    print(f"   Monotono come previsto? {'SI' if mono else 'NO'}")
    e4_fals = any(r["irr_ref"] > bh4["irr"] for r in cand4)
    print(f"   -> ipotesi E4 {'FALSIFICATA' if e4_fals else 'CONFERMATA'}")
    rows_all["E4"] = cand4

    # ================================================================ E5
    print(f"\n{'='*96}\nE5 — LEAPS COME LEVA A BUON MERCATO\n{'='*96}")
    print("   Call deep ITM a 12 mesi, rollate una volta l'anno. Perdita massima")
    print("   pari al premio: nessun margin call, che al giro 35 chiudeva la")
    print("   posizione sui minimi a leva 1,5x.\n")
    r5 = [bh]
    fin_rows = []
    print("   La posizione e' MARCATA AL MERCATO ogni mese con la maturita'")
    print("   residua corretta. Una posizione annuale osservata solo a scadenza")
    print("   da' 1 punto l'anno, e darla a un motore che assume 12 periodi")
    print("   l'anno gonfia il CAGR di un fattore enorme: nella prima stesura di")
    print("   questo giro usciva 264-434%% annuo, che e' il sintomo di quel bug.\n")
    for mny, lbl in ((0.80, "80%"), (0.90, "90%")):
        xa = O.roll_short_option(d, q, kind="c", moneyness=mny, freq="YE",
                                 iv_scale=IV_K)
        # Finanziamento incorporato. Comprando una call invece dell'azione si
        # prende a prestito lo strike E si rinuncia ai dividendi: entrambi i
        # termini vanno contati. Ometterne uno sottostima il costo di q.
        intr = np.maximum(1.0 - xa["K"], 0.0)
        emb = ((xa["premium"] - intr) / xa["K"] / xa["T"]) + q
        fin_rows.append(dict(moneyness=lbl, emb=float(emb.mean()) * 100,
                             prem=float(xa["premium"].mean()) * 100))
        for L in (1.0, 1.2, 1.5):
            sm, zm = O.leaps_mtm(d, q, moneyness=mny, iv_scale=IV_K, leverage=L)
            r5.append(B.eval_stream(f"LEAPS {lbl} leva {L:.1f}x", sm,
                                    rf0.reindex(sm.index), zm))
    B.table(r5, cols=("label", "cagr", "vol", "sharpe", "dd", "turn", "irr", "irr52"))
    print(f"\n   Finanziamento incorporato nella call deep ITM (annualizzato):")
    for f in fin_rows:
        print(f"     moneyness {f['moneyness']:<5} premio {f['prem']:>5.1f}% del "
              f"nozionale · finanziamento implicito {f['emb']:>5.2f}% annuo")
    rfa = float(d["rf"].mean()) * 100
    print(f"   Risk-free medio del periodo: {rfa:.2f}%  ·  CFD del giro 35: "
          f"{rfa + C.FIN_SPREAD*100:.2f}%")
    cheaper = all(f["emb"] < rfa + C.FIN_SPREAD * 100 for f in fin_rows)
    print(f"   Il LEAPS finanzia a meno del CFD? {'SI' if cheaper else 'NO'}")
    cand5 = r5[1:]
    e5_fals = any(r["irr_ref"] >= bh["irr"] for r in cand5)
    print(f"   Migliore: {max(cand5, key=lambda r: r['irr_ref'])['label']} "
          f"{max(r['irr_ref'] for r in cand5):.2f}% contro {bh['irr']:.2f}%")
    print(f"   -> ipotesi E5 {'FALSIFICATA' if e5_fals else 'CONFERMATA'}")
    rows_all["E5"] = cand5

    # ================================================================ DSR
    print(f"\n{'='*96}\nCONTABILITA'\n{'='*96}")
    allc = [r for k in ("E2", "E3", "E4", "E5") for r in rows_all[k]]
    best = max(allc, key=lambda r: r["irr_ref"])
    dd = lab.deflated_sharpe(best["gross"], N_PREREG, round_id=ROUND)
    print(f"   Migliore in assoluto del gruppo E: {best['label']} "
          f"{best['irr_ref']:.2f}% contro {bh['irr']:.2f}% del benchmark "
          f"({best['irr_ref']-bh['irr']:+.2f})")
    print(f"   DSR su N={N_PREREG}: {dd['dsr']:.3f} -> "
          + ("PROMUOVIBILE" if dd["dsr"] > 0.95 and best["irr_ref"] > bh["irr"]
             else "NON promuovibile"))
    print(f"   Nessuna configurazione con oltre 1 rotazione l'anno e' valutata")
    print(f"   al 33%: la colonna irr52 e' quella che conta per E2, E3 e E5.")

    lab.log_trials([dict(round=ROUND, hypothesis=f"{k} opzioni",
                         config=r["label"], window=f"{idx[0].date()}/{idx[-1].date()}",
                         sharpe=r["sharpe"], irr=r["irr"], bh_irr=bh["irr"],
                         excess=r["irr_ref"] - bh["irr"], n_obs=r["n"],
                         note=f"turn={r['turn']:.1f}x,rate={r['rate_ref']}")
                    for k in ("E2", "E3", "E4", "E5") for r in rows_all[k]])
    pd.DataFrame([{kk: vv for kk, vv in r.items() if kk != "gross"}
                  for r in allc + [bh]]).to_csv(OUT / "round49_opzioni.csv",
                                                index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

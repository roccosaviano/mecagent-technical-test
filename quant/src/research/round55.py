"""Giro 55 — PAC su dati REALI: S&P 500 Momentum contro S&P 500.

Il giro 54 usava un proxy di Ken French perche' i dati dell'indice erano
licenziati. Yahoo ha risposto: ora ho SPMO, l'ETF di Invesco che replica
ESATTAMENTE l'S&P 500 Momentum (SP500MUP), e SPY per l'S&P 500. Prezzi
aggiustati, quindi dividendi reinvestiti: e' total return per entrambi.

DUE AVVERTENZE CHE VENGONO PRIMA DEI NUMERI.

1. Nello screenshot il confronto e' SBILANCIATO. `.INX` e' l'S&P 500 PRICE
   index, senza dividendi. SP500MUT e SP500MUN sono TOTAL RETURN. Confrontare
   +69,80% con +159,16% mette a paragone un indice senza dividendi con due che
   li hanno: parte del divario e' reale, parte e' la mancanza dei dividendi.
   Qui uso total return da entrambe le parti.

2. Cinque anni sono UNA finestra. Il giro 54 ha misurato 90 finestre decennali:
   il momentum vince nell'82% con +2,23 punti di media, ma le finestre che
   partono dopo il 2007 sono le peggiori della serie. Un quinquennio non
   distingue "funziona" da "e' andata bene".
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import dataio
from tax import simulate_pac, CGT_SHARES, ETF_UCITS
from research import bench as B

DATA = Path(__file__).resolve().parents[2] / "data"
OUT = Path(__file__).resolve().parents[2] / "out"
CONTRIB = 750.0


def load(sym):
    s = pd.read_csv(DATA / f"yh_{sym}.csv", index_col=0, parse_dates=True).iloc[:, 0]
    s.index = s.index.to_period("M").to_timestamp("M")
    return s[~s.index.duplicated(keep="last")].sort_index()


def main():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    px = {s: load(s) for s in ("SPMO", "SPY", "MTUM", "BRK-B")}
    names = {"SPMO": "S&P 500 Momentum (SPMO)", "SPY": "S&P 500 (SPY)",
             "MTUM": "MSCI USA Momentum (MTUM)", "BRK-B": "Berkshire (BRK.B)"}

    # ---------------------------------------------- controllo sullo screenshot
    print(f"{'='*94}\nCONTROLLO: i numeri dello screenshot su 5 anni\n{'='*94}")
    end = min(s.index[-1] for s in px.values())
    st5 = end - pd.DateOffset(years=5)
    print(f"   {'strumento':<30}{'5 anni':>10}   nota")
    for s in ("BRK-B", "SPY", "SPMO"):
        v = px[s]
        w = v[(v.index >= st5) & (v.index <= end)]
        print(f"   {names[s]:<30}{(w.iloc[-1]/w.iloc[0]-1)*100:>9.1f}%")
    print(f"\n   Nello screenshot: BRK.B +78,2% · .INX +69,8% · SP500MUN +154,1%")
    print(f"   Il mio SPY e' TOTAL RETURN, .INX no: la differenza fra i due e'")
    print(f"   quanto valgono i dividendi dell'S&P in cinque anni.")

    # ---------------------------------------------- il PAC
    for yrs in (5, 10):
        start = end - pd.DateOffset(years=yrs)
        avail = [s for s in ("SPY", "SPMO", "MTUM", "BRK-B")
                 if px[s].index[0] <= start]
        print(f"\n{'='*94}\nPAC DI EUR {CONTRIB:.0f}/MESE PER {yrs} ANNI  "
              f"({start.date()} -> {end.date()})\n{'='*94}")
        rows = []
        for s in avail:
            v = px[s]
            w = v[(v.index >= start) & (v.index <= end)]
            r = w.pct_change().dropna()
            rf0 = rf.reindex(r.index).ffill().fillna(0.0)
            stt = B.stats(r)
            e = simulate_pac(r, ETF_UCITS, rf=rf0, contrib=CONTRIB,
                             periods_per_year=12)
            c = simulate_pac(r, CGT_SHARES, rf=rf0, contrib=CONTRIB,
                             periods_per_year=12)
            rows.append(dict(sym=s, nome=names[s], cagr=stt["cagr"],
                             vol=stt["vol"], dd=stt["dd"], sharpe=stt["sharpe"],
                             irr_etf=e.irr_annual, fin_etf=e.final_net,
                             irr_cgt=c.irr_annual, fin_cgt=c.final_net,
                             versato=e.contributions, tax_etf=e.taxes))
        print(f"   {'strumento':<28}{'CAGR':>8}{'vol':>7}{'DD':>9}{'Sharpe':>8}"
              f"{'IRR ETF':>9}{'montante':>12}{'imposte':>10}")
        print("   " + "-" * 91)
        for r in rows:
            print(f"   {r['nome']:<28}{r['cagr']:>7.2f}%{r['vol']:>6.1f}%"
                  f"{r['dd']:>8.1f}%{r['sharpe']:>8.2f}{r['irr_etf']:>8.2f}%"
                  f"{r['fin_etf']:>11,.0f}{r['tax_etf']:>10,.0f}")
        base = next(r for r in rows if r["sym"] == "SPY")
        print(f"\n   Versato: EUR {base['versato']:,.0f}")
        for r in rows:
            if r["sym"] == "SPY":
                continue
            print(f"   {r['nome']:<28} contro S&P 500: "
                  f"{r['irr_etf']-base['irr_etf']:+6.2f} punti, "
                  f"EUR {r['fin_etf']-base['fin_etf']:+,.0f}")
        pd.DataFrame(rows).to_csv(OUT / f"round55_pac{yrs}a.csv", index=False)

    # ---------------------------------------------- tutte le finestre di SPMO
    print(f"\n{'='*94}\nOGNI FINESTRA DI 5 ANNI DA QUANDO SPMO ESISTE\n{'='*94}")
    a, b = px["SPMO"], px["SPY"]
    ix = a.index.intersection(b.index)
    diffs = []
    for i in range(len(ix)):
        s0 = ix[i]
        s1 = s0 + pd.DateOffset(years=5)
        if s1 > ix[-1]:
            break
        w = ix[(ix >= s0) & (ix <= s1)]
        ra, rb = a.reindex(w).pct_change().dropna(), b.reindex(w).pct_change().dropna()
        rf0 = rf.reindex(ra.index).ffill().fillna(0.0)
        ea = simulate_pac(ra, ETF_UCITS, rf=rf0, contrib=CONTRIB, periods_per_year=12)
        eb = simulate_pac(rb, ETF_UCITS, rf=rf0, contrib=CONTRIB, periods_per_year=12)
        diffs.append((s0, ea.irr_annual - eb.irr_annual))
    d = np.array([x[1] for x in diffs])
    print(f"   {len(d)} finestre mensili sovrapposte, dal {diffs[0][0].date()} "
          f"al {diffs[-1][0].date()}")
    print(f"   Il momentum vince in {int((d>0).sum())}/{len(d)} ({(d>0).mean()*100:.0f}%)")
    print(f"   Differenza media {d.mean():+.2f} punti · mediana {np.median(d):+.2f}")
    print(f"   Peggiore {d.min():+.2f} (dal {diffs[int(np.argmin(d))][0].date()}) · "
          f"migliore {d.max():+.2f} (dal {diffs[int(np.argmax(d))][0].date()})")
    print(f"\n   Le finestre si sovrappongono di 59 mesi su 60: sono circa DUE")
    print(f"   osservazioni indipendenti, non {len(d)}. Descrittive, non un test.")
    pd.DataFrame(diffs, columns=["inizio", "diff"]).to_csv(
        OUT / "round55_finestre5a.csv", index=False)


if __name__ == "__main__":
    main()

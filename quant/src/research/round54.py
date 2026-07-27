"""Giro 54 — S&P 500 contro S&P 500 Momentum, PAC 750 EUR/mese per 10 anni.

RICHIESTA DIRETTA, non una voce di coda: nessuna predizione pre-registrata,
nessun candidato promuovibile. E' una misura, e va letta come tale.

IL PROXY, dichiarato prima dei numeri. Non ho i dati dell'indice S&P 500
Momentum (SP500MUP): sono licenziati, e Stooq e Twelve Data non me li danno.
Uso i portafogli di Ken French 6_Portfolios_ME_Prior_12_2, colonna
BIG HiPRIOR: grandi capitalizzazioni, terzile alto di momentum 12-2,
value-weighted, ribilanciati mensilmente.

  cosa fa l'indice vero   ~100 titoli su 500, selezionati per momentum
                          RISK-ADJUSTED, pesati per punteggio x float cap,
                          ribilanciamento SEMESTRALE
  cosa fa il proxy        terzile alto di momentum fra le grandi, pesato per
                          capitalizzazione, ribilanciamento MENSILE

Le differenze contano e vanno nella stessa direzione: il proxy ruota di piu' e
non normalizza per la volatilita', quindi e' piu' aggressivo dell'indice vero.
E siccome la rotazione avviene DENTRO l'indice, per chi compra l'ETF non e' un
evento fiscale: il costo della rotazione sta nel rendimento lordo, non nelle
imposte del detentore.
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
from tax import simulate_pac, CGT_SHARES, ETF_UCITS
from research import bench as B

ROUND = 54
OUT = Path(__file__).resolve().parents[2] / "out"
DATA = Path(__file__).resolve().parents[2] / "data"
CONTRIB = 750.0
YEARS = 10
TER_MOM, TER_SP = 0.0035, 0.0007      # TER tipici: momentum ~0,35%, S&P ~0,07%


def load_mom():
    p = DATA / "6_Portfolios_ME_Prior_12_2/6_Portfolios_ME_Prior_12_2.csv"
    s = dataio._ff_sections(p)
    key = next(k for k in s if "Average Value Weighted Returns -- Monthly" in (k or ""))
    df = dataio._to_period_index(s[key]) / 100.0
    df.columns = [c.strip() for c in df.columns]
    return df["BIG HiPRIOR"]


def run(label, ret, rf, regime, contrib, ter=0.0):
    r = ret - ter / 12.0
    p = simulate_pac(r, regime, rf=rf.reindex(r.index).fillna(0.0),
                     contrib=contrib, periods_per_year=12)
    st = B.stats(r)
    return dict(label=label, cagr=st["cagr"], vol=st["vol"], sharpe=st["sharpe"],
                dd=st["dd"], irr=p.irr_annual, final=p.final_net,
                versato=p.contributions, imposte=p.taxes)


def main():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    sp = (ff["Mkt-RF"] + ff["RF"]).dropna()
    mom = load_mom().dropna()
    ix = sp.index.intersection(mom.index)
    end = ix[-1]
    start = end - pd.DateOffset(years=YEARS) + pd.DateOffset(days=1)
    w = ix[(ix >= start) & (ix <= end)]

    print(f"PAC di EUR {CONTRIB:.0f}/mese per {YEARS} anni")
    print(f"Finestra {w[0].date()} -> {w[-1].date()} ({len(w)} mesi, "
          f"EUR {CONTRIB*len(w):,.0f} versati)")
    print(f"Proxy dell'S&P 500 Momentum: Ken French BIG HiPRIOR "
          f"(grandi cap, terzile alto momentum 12-2, value-weighted)")
    print(f"TER applicati: momentum {TER_MOM*100:.2f}%, S&P {TER_SP*100:.2f}%\n")

    rows = []
    for lbl, r_, ter in (("S&P 500", sp.reindex(w), TER_SP),
                         ("S&P 500 Momentum (proxy)", mom.reindex(w), TER_MOM)):
        for reg, rn in ((ETF_UCITS, "ETF UCITS"), (CGT_SHARES, "diretto CGT")):
            rows.append(run(f"{lbl} — {rn}", r_, rf, reg, CONTRIB, ter))

    print(f"   {'configurazione':<38}{'CAGR':>8}{'vol':>8}{'DD':>9}"
          f"{'IRR netta':>11}{'montante':>13}{'imposte':>11}")
    print("   " + "-" * 88)
    for r in rows:
        print(f"   {r['label']:<38}{r['cagr']:>7.2f}%{r['vol']:>7.1f}%"
              f"{r['dd']:>8.1f}%{r['irr']:>10.2f}%{r['final']:>12,.0f}"
              f"{r['imposte']:>11,.0f}")

    etf_sp = rows[0]
    etf_mom = rows[2]
    print(f"\n   IL CONFRONTO CHE FARESTI DAVVERO (entrambi ETF UCITS):")
    print(f"     S&P 500          IRR {etf_sp['irr']:.2f}%   montante EUR {etf_sp['final']:,.0f}")
    print(f"     S&P 500 Momentum IRR {etf_mom['irr']:.2f}%   montante EUR {etf_mom['final']:,.0f}")
    print(f"     -> {etf_mom['irr']-etf_sp['irr']:+.2f} punti, "
          f"EUR {etf_mom['final']-etf_sp['final']:+,.0f} sul montante")

    # ---- quanto e' fragile una finestra di 10 anni?
    print(f"\n{'='*92}\nQUANTO VALE UNA FINESTRA DI 10 ANNI\n{'='*92}")
    print("   Il giro 46 ha mostrato che per un PAC conta soprattutto quando")
    print("   finisce. Rifaccio lo stesso confronto su TUTTE le finestre di 10")
    print("   anni disponibili, a passo annuale, per vedere se il risultato sopra")
    print("   e' una proprieta' o un pezzo di storia.\n")
    diffs = []
    for y0 in range(ix[0].year, ix[-1].year - YEARS + 2):
        sub = ix[(ix.year >= y0) & (ix.year < y0 + YEARS)]
        if len(sub) < YEARS * 12 - 6:
            continue
        a = run("sp", sp.reindex(sub), rf, ETF_UCITS, CONTRIB, TER_SP)
        b = run("mom", mom.reindex(sub), rf, ETF_UCITS, CONTRIB, TER_MOM)
        diffs.append((y0, b["irr"] - a["irr"], a["irr"], b["irr"]))
    d = np.array([x[1] for x in diffs])
    print(f"   {len(d)} finestre di {YEARS} anni, dal {diffs[0][0]} al {diffs[-1][0]}")
    print(f"   Il momentum vince in {int((d>0).sum())}/{len(d)} finestre "
          f"({(d>0).mean()*100:.0f}%)")
    print(f"   Differenza media {d.mean():+.2f} punti · mediana {np.median(d):+.2f}")
    print(f"   Peggiore {d.min():+.2f} (dal {diffs[int(np.argmin(d))][0]}) · "
          f"migliore {d.max():+.2f} (dal {diffs[int(np.argmax(d))][0]})")
    print(f"   Deviazione standard fra finestre: {d.std(ddof=1):.2f} punti")
    print(f"\n   Ultime 10 finestre:")
    print(f"     {'inizio':>8}{'S&P':>9}{'Momentum':>11}{'differenza':>13}")
    for y0, dd_, a_, b_ in diffs[-10:]:
        print(f"     {y0:>8}{a_:>8.2f}%{b_:>10.2f}%{dd_:>+12.2f}")

    pd.DataFrame(rows).to_csv(OUT / "round54_sp_vs_momentum.csv", index=False)
    pd.DataFrame(diffs, columns=["inizio", "diff", "irr_sp", "irr_mom"]).to_csv(
        OUT / "round54_finestre10.csv", index=False)


if __name__ == "__main__":
    main()

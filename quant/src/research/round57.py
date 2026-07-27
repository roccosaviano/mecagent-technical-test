"""Giro 57 — H1: azionario globale contro solo USA.

VOCE DELLA CODA, verbatim:
  PREDIZIONE: l'S&P batte il globale di 1,5-3 punti sulle finestre disponibili,
  ma la differenza e' interamente attribuibile alla sovraperformance USA del
  periodo, e su finestre mobili la quota di vittorie dell'S&P sta SOTTO il 90%.
  FALSIFICATA SE: il globale batte l'S&P sulla finestra principale, oppure l'S&P
  vince in TUTTE le finestre mobili.
"""
import sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")
import dataio
from tax import simulate_pac, ETF_UCITS
from research import lab, bench as B, multidata as M

ROUND, CONTRIB = 57, 750.0
DATA = Path(__file__).resolve().parents[2] / "data"
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 75


def yh(sym):
    x = pd.read_csv(DATA / f"yh_{sym}.csv", index_col=0, parse_dates=True).iloc[:, 0]
    x.index = x.index.to_period("M").to_timestamp("M")
    return x[~x.index.duplicated(keep="last")].sort_index().pct_change().dropna()


def pac(r, rf):
    return simulate_pac(r, ETF_UCITS, rf=rf.reindex(r.index).ffill().fillna(0.0),
                        contrib=CONTRIB, periods_per_year=12)


def main():
    ff = dataio.ff_factors_monthly(); rf = ff["RF"]
    us_long = (ff["Mkt-RF"] + ff["RF"]).dropna()
    series = {s: yh(s) for s in ("SPY", "VT", "ACWI", "URTH")}
    nm = {"SPY": "S&P 500 (SPY)", "VT": "All-World (VT)",
          "ACWI": "MSCI ACWI (ACWI)", "URTH": "MSCI World (URTH)"}

    # ---------------------------------------------- dati reali
    ix = series["SPY"].index
    for s in ("VT", "ACWI"):
        ix = ix.intersection(series[s].index)
    print(f"DATI REALI · PAC EUR {CONTRIB:.0f}/mese · regime ETF UCITS")
    print(f"Finestra comune {ix[0].date()} -> {ix[-1].date()} ({len(ix)} mesi, "
          f"EUR {CONTRIB*len(ix):,.0f} versati)\n")
    rows = []
    print(f"   {'strumento':<22}{'CAGR':>8}{'vol':>7}{'DD':>9}{'IRR':>9}"
          f"{'montante':>12}{'vs S&P':>11}")
    print("   " + "-" * 78)
    base = None
    for s in ("SPY", "VT", "ACWI", "URTH"):
        r = series[s].reindex(ix).dropna()
        if len(r) < 60:
            continue
        st = B.stats(r); p = pac(r, rf)
        if base is None:
            base = p.final_net; birr = p.irr_annual
        rows.append(dict(s=s, cagr=st["cagr"], vol=st["vol"], dd=st["dd"],
                         irr=p.irr_annual, fin=p.final_net))
        print(f"   {nm[s]:<22}{st['cagr']:>7.2f}%{st['vol']:>6.1f}%{st['dd']:>8.1f}%"
              f"{p.irr_annual:>8.2f}%{p.final_net:>12,.0f}"
              f"{p.final_net-base:>+11,.0f}")
    glob = min(r["irr"] for r in rows if r["s"] != "SPY")
    gap = birr - max(r["irr"] for r in rows if r["s"] != "SPY")
    print(f"\n   Divario S&P contro il MIGLIORE dei globali: {gap:+.2f} punti")

    # ---------------------------------------------- proxy lungo
    print(f"\n{'='*84}\nPROXY LUNGO: French Developed contro USA, dal 1990\n{'='*84}")
    dev = M.ff_region("Developed_3_Factors")
    col = "Mkt-RF" if "Mkt-RF" in dev.columns else dev.columns[0]
    g = (dev[col] + dev.get("RF", 0.0)).dropna()
    jx = g.index.intersection(us_long.index)
    a, b = us_long.reindex(jx), g.reindex(jx)
    pa, pb = pac(a, rf), pac(b, rf)
    print(f"   {len(jx)} mesi, {jx[0].date()} -> {jx[-1].date()}")
    print(f"   USA      CAGR {B.stats(a)['cagr']:5.2f}%  IRR {pa.irr_annual:5.2f}%"
          f"  montante {pa.final_net:>10,.0f}")
    print(f"   Developed CAGR {B.stats(b)['cagr']:5.2f}%  IRR {pb.irr_annual:5.2f}%"
          f"  montante {pb.final_net:>10,.0f}")
    print(f"   -> USA {pa.irr_annual-pb.irr_annual:+.2f} punti, "
          f"EUR {pa.final_net-pb.final_net:+,.0f}")

    # ---------------------------------------------- finestre mobili di 10 anni
    print(f"\n{'='*84}\nFINESTRE MOBILI DI 10 ANNI (proxy lungo)\n{'='*84}")
    wins = []
    for y0 in range(jx[0].year, jx[-1].year - 9):
        w = jx[(jx.year >= y0) & (jx.year < y0 + 10)]
        if len(w) < 118:
            continue
        d = pac(a.reindex(w), rf).irr_annual - pac(b.reindex(w), rf).irr_annual
        wins.append((y0, d))
    d = np.array([x[1] for x in wins])
    share = float((d > 0).mean())
    print(f"   {len(d)} finestre, dal {wins[0][0]} al {wins[-1][0]}")
    print(f"   L'USA vince in {int((d>0).sum())}/{len(d)} ({share*100:.0f}%)")
    print(f"   Differenza media {d.mean():+.2f} · peggiore {d.min():+.2f} "
          f"({wins[int(np.argmin(d))][0]}) · migliore {d.max():+.2f} "
          f"({wins[int(np.argmax(d))][0]})")
    neg = [y for y, v in wins if v < 0]
    if neg:
        print(f"   Finestre in cui il GLOBALE vince: partenze "
              f"{', '.join(str(y) for y in neg)}")

    # ---------------------------------------------- verdetto
    print(f"\n{'='*84}\nVERDETTO SU H1\n{'='*84}")
    print("   Predizione: S&P batte il globale di 1,5-3 punti, e la quota di")
    print("   vittorie dell'S&P su finestre mobili sta SOTTO il 90%.")
    print("   FALSIFICATA se il globale batte l'S&P sulla finestra principale,")
    print("   oppure se l'S&P vince in TUTTE le finestre mobili.\n")
    print(f"   (a) divario sulla finestra reale: {gap:+.2f} punti "
          f"({'dentro' if 1.5 <= gap <= 3 else 'FUORI'} la banda 1,5-3)")
    print(f"   (b) quota di vittorie USA su finestre mobili: {share*100:.0f}% "
          f"({'sotto' if share < 0.90 else 'SOPRA'} il 90%)")
    fals = gap < 0 or share == 1.0
    print(f"\n   -> ipotesi H1 {'FALSIFICATA' if fals else 'CONFERMATA'}")

    lab.log_trials([dict(round=ROUND, hypothesis="H1 globale contro USA",
                         config=nm[r["s"]], window=f"{ix[0].date()}/{ix[-1].date()}",
                         sharpe="", irr=r["irr"], bh_irr=birr,
                         excess=r["irr"] - birr, n_obs=len(ix), note="")
                    for r in rows])
    pd.DataFrame(rows).to_csv(OUT / "round57_globale.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

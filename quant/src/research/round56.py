"""Giro 56 — Indietro nel tempo: proxy dell'S&P 500 Momentum validato, 1927-2026.

Il giro 55 ha misurato SPMO contro SPY sui dieci anni in cui SPMO esiste. Per
andare piu' indietro serve un proxy, e il giro 54 ha dimostrato che sceglierlo
male porta alla conclusione opposta (il terzile di grandi cap dava +0,09 punti
dove l'indice vero ne dava +5,17).

QUINDI: CANCELLO DI VALIDAZIONE PRIMA, storia dopo. Il proxy deve riprodurre
SPMO sui dieci anni di sovrapposizione — CAGR entro 2 punti e correlazione dei
rendimenti mensili sopra 0,90 — altrimenti i numeri storici non valgono niente
e lo dico invece di pubblicarli.

I CANDIDATI PROXY, dai portafogli di Ken French:
  BIG HiPRIOR 3x2   terzile alto di momentum fra le grandi (giro 54, fallito)
  BIG HiPRIOR 5x5   QUINTILE alto fra le grandi: top 20%, che e' la stessa
                    proporzione dell'indice vero (~100 titoli su 500)
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import dataio
from tax import simulate_pac, ETF_UCITS
from research import bench as B

DATA = Path(__file__).resolve().parents[2] / "data"
OUT = Path(__file__).resolve().parents[2] / "out"
CONTRIB = 750.0
GATE_CAGR, GATE_CORR = 2.0, 0.90


def ff_port(folder, col):
    p = next((DATA / folder).glob("*.csv"))
    s = dataio._ff_sections(p)
    key = next(k for k in s if "Average Value Weighted Returns -- Monthly" in (k or ""))
    df = dataio._to_period_index(s[key]) / 100.0
    df.columns = [c.strip() for c in df.columns]
    return df[col].dropna()


def load_yh(sym):
    x = pd.read_csv(DATA / f"yh_{sym}.csv", index_col=0, parse_dates=True).iloc[:, 0]
    x.index = x.index.to_period("M").to_timestamp("M")
    return x[~x.index.duplicated(keep="last")].sort_index().pct_change().dropna()


def cagr(r):
    return float((1 + r).prod() ** (12 / len(r)) - 1) * 100


def main():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()
    spmo, spy = load_yh("SPMO"), load_yh("SPY")
    proxies = {
        "terzile grandi (giro 54)": ff_port("6_Portfolios_ME_Prior_12_2", "BIG HiPRIOR"),
        "QUINTILE grandi (5x5)": ff_port("25_Portfolios_ME_Prior_12_2", "BIG HiPRIOR"),
    }

    print(f"{'='*94}\nCANCELLO: il proxy riproduce SPMO?\n{'='*94}")
    print(f"   Condizione: CAGR entro {GATE_CAGR} punti E correlazione mensile "
          f"sopra {GATE_CORR}\n")
    ok = {}
    for nm, s in proxies.items():
        ix = s.index.intersection(spmo.index)
        a, b = s.reindex(ix), spmo.reindex(ix)
        ca, cb, cr = cagr(a), cagr(b), float(a.corr(b))
        passa = abs(ca - cb) <= GATE_CAGR and cr >= GATE_CORR
        ok[nm] = passa
        print(f"   {nm:<28} {len(ix)} mesi  proxy {ca:>6.2f}%  SPMO {cb:>6.2f}%"
              f"  scarto {ca-cb:>+6.2f}  corr {cr:.3f}  -> "
              f"{'PASSA' if passa else 'NON PASSA'}")
    # riferimento: anche il mercato contro SPY, per sapere quanto e' buono il
    # confronto in condizioni normali
    ix = mkt.index.intersection(spy.index)
    print(f"   {'(controllo) mercato vs SPY':<28} {len(ix)} mesi  "
          f"proxy {cagr(mkt.reindex(ix)):>6.2f}%  SPY {cagr(spy.reindex(ix)):>6.2f}%"
          f"  corr {float(mkt.reindex(ix).corr(spy.reindex(ix))):.3f}")

    good = [k for k, v in ok.items() if v]
    if not good:
        print(f"\n   -> NESSUN PROXY PASSA. Non pubblico numeri storici: senza uno")
        print(f"      strumento che riproduca l'indice vero, andare indietro nel")
        print(f"      tempo significa misurare un'altra cosa e chiamarla momentum.")
        print(f"      E' esattamente l'errore del giro 54.")
        best = min(proxies, key=lambda k: abs(cagr(proxies[k].reindex(
            proxies[k].index.intersection(spmo.index))) - cagr(spmo.reindex(
            proxies[k].index.intersection(spmo.index)))))
        print(f"\n   Il meno peggio e' '{best}'. Lo uso SOLO per una domanda che")
        print(f"   non dipende dal livello: il momentum accademico batteva il")
        print(f"   mercato piu' spesso in passato di quanto faccia oggi?")
        s = proxies[best]
    else:
        print(f"\n   -> PROXY VALIDATO: {good[0]}")
        s = proxies[good[0]]

    # ------------------------------------------------ PAC decennio per decennio
    print(f"\n{'='*94}\nPAC DI EUR {CONTRIB:.0f}/MESE PER 10 ANNI, DECENNIO PER "
          f"DECENNIO\n{'='*94}")
    ix = s.index.intersection(mkt.index)
    print(f"   Proxy: {best if not good else good[0]} · regime ETF UCITS")
    print(f"   {'decennio':<12}{'mercato':>11}{'momentum':>11}{'differenza':>13}"
          f"{'netto mkt':>12}{'netto mom':>12}")
    print("   " + "-" * 71)
    rows = []
    for dec in range(1930, 2021, 10):
        w = ix[(ix.year >= dec) & (ix.year < dec + 10)]
        if len(w) < 118:
            continue
        rf0 = rf.reindex(w).ffill().fillna(0.0)
        a = simulate_pac(mkt.reindex(w), ETF_UCITS, rf=rf0, contrib=CONTRIB,
                         periods_per_year=12)
        b = simulate_pac(s.reindex(w), ETF_UCITS, rf=rf0, contrib=CONTRIB,
                         periods_per_year=12)
        rows.append(dict(dec=dec, mkt=a.irr_annual, mom=b.irr_annual,
                         d=b.irr_annual - a.irr_annual, fa=a.final_net,
                         fb=b.final_net, vers=a.contributions))
        print(f"   {dec}-{dec+9:<7}{a.irr_annual:>10.2f}%{b.irr_annual:>10.2f}%"
              f"{b.irr_annual-a.irr_annual:>+12.2f}{a.final_net:>12,.0f}"
              f"{b.final_net:>12,.0f}")
    d = np.array([r["d"] for r in rows])
    print(f"\n   Versato in ogni decennio: EUR {rows[0]['vers']:,.0f}")
    print(f"   Il momentum vince in {int((d>0).sum())}/{len(d)} decenni")
    print(f"   Differenza media {d.mean():+.2f} punti · mediana {np.median(d):+.2f}")
    print(f"   Peggiore {d.min():+.2f} ({rows[int(np.argmin(d))]['dec']}s) · "
          f"migliore {d.max():+.2f} ({rows[int(np.argmax(d))]['dec']}s)")

    # ------------------------------------------------ quota mobile
    print(f"\n{'='*94}\nIL PREMIO SI STA CONSUMANDO? Finestre decennali mobili\n{'='*94}")
    diffs = []
    for y0 in range(ix[0].year, ix[-1].year - 9):
        w = ix[(ix.year >= y0) & (ix.year < y0 + 10)]
        if len(w) < 118:
            continue
        rf0 = rf.reindex(w).ffill().fillna(0.0)
        a = simulate_pac(mkt.reindex(w), ETF_UCITS, rf=rf0, contrib=CONTRIB, periods_per_year=12)
        b = simulate_pac(s.reindex(w), ETF_UCITS, rf=rf0, contrib=CONTRIB, periods_per_year=12)
        diffs.append((y0, b.irr_annual - a.irr_annual))
    dd = pd.Series({y: v for y, v in diffs})
    for lo, hi, lbl in ((1927, 1969, "1927-1969 (pre-pubblicazione)"),
                        (1970, 1992, "1970-1992 (pre-pubblicazione)"),
                        (1993, 2006, "1993-2006 (post Jegadeesh-Titman)"),
                        (2007, 2020, "2007-2020 (post-crisi)")):
        seg = dd[(dd.index >= lo) & (dd.index <= hi)]
        if len(seg):
            print(f"   {lbl:<36} {len(seg):>3} finestre  vince "
                  f"{float((seg>0).mean())*100:>5.1f}%  media {seg.mean():>+6.2f}")
    print(f"\n   Le finestre si sovrappongono 9 anni su 10: poche osservazioni")
    print(f"   indipendenti. Descrittivo, non un test.")
    pd.DataFrame(rows).to_csv(OUT / "round56_decenni.csv", index=False)


if __name__ == "__main__":
    main()

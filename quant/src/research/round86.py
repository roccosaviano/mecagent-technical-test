"""Giro 86 — O8: quanto costa che l'alfa sia volatile invece che costante.

VOCE DELLA CODA, verbatim (committata al giro 83):

O8 — Quanto costa che l'alfa sia volatile invece che costante
  La curva del tasso di cambio e' costruita su un alfa COSTANTE ogni mese, e il
  controllo col giro 80 mostra che e' OTTIMISTA DI CIRCA 0,8 PUNTI di margine
  netto: il candidato reale, con 6,50 di alfa lordo a 3,28x di rotazione, ha
  consegnato +1,18, mentre il sintetico a 3,5x con lo stesso alfa ne darebbe circa
  +1,9. Il sospetto e' la VOLATILITA' DELL'ALFA. Finche' non e' misurato, tutta la
  curva del giro 83 e' un limite inferiore di taglia ignota.
  Da misurare, sul solo 1969-2009: rifare la griglia del giro 83 alla sola
  rotazione 3,5x e al solo alfa lordo 6,0, ma con l'alfa mensile RUMOROSO invece
  che costante — media imposta a 6 punti l'anno e volatilita' dell'alfa imposta a
  0 / 2 / 5 / 10 / 15 / 20 punti annualizzati (sei celle, tutte pre-dichiarate),
  con 200 estrazioni per cella e seme fissato. Riportare la mediana e i percentili
  5-95 del margine netto, e da li' DI QUANTO SALE L'ALFA RICHIESTO per +1,00 a
  ciascun livello di volatilita'.
  PREDIZIONE: il margine netto SCENDE IN MODO MONOTONO al crescere della
  volatilita' dell'alfa, e alla volatilita' che il candidato aveva davvero — circa
  14 punti di tracking error annualizzato, cioe' fra la cella 10 e la cella 15 —
  la perdita e' FRA 0,5 E 1,2 PUNTI, coerente con lo 0,8 misurato indirettamente
  al giro 83. Il meccanismo e' fiscale e non statistico: la dispersione NON
  dovrebbe far scendere la mediana se il motore fosse lineare, quindi la caduta
  misura la CONVESSITA' DEL PRELIEVO.
  FALSIFICATA SE: la mediana del margine NON SCENDE al crescere della volatilita'
  dell'alfa, o scende di MENO DI 0,2 PUNTI anche a 20 di volatilita' — OPPURE se
  la caduta supera 2,5 PUNTI.

================= DUE SCELTE DICHIARATE PRIMA DI ESEGUIRE =================

1. COME SI IMPONE UNA MEDIA CHE NON DIPENDE DALLA VOLATILITA'. Se sommassi rumore
   a un alfa aritmetico, alzare la volatilita' abbasserebbe da sola la media
   GEOMETRICA, e misurerei quel drag invece della convessita' fiscale. Estraggo
   quindi il LOGARITMO dell'alfa mensile da una normale:
       log(1 + alfa_m) ~ N( log(1,06)/12 , (sigma/sqrt(12))^2 )
   cosi' l'alfa geometrico annuo resta 6 punti a OGNI livello di volatilita', per
   costruzione. Se la mediana del margine scende, non e' perche' e' sceso l'alfa.

2. LA VOLATILITA' VERA DEL CANDIDATO LA MISURO, NON LA ASSUMO. La voce dice
   "circa 14 punti" senza averlo verificato. Calcolo il tracking error vero del
   12-3 top-5 contro il benchmark sul train e uso QUELLO per scegliere la cella di
   confronto — anche se cade fuori dall'intervallo che avevo scritto.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from research import lab, bench as B
from research.round76 import simula, pesi_top

ROUND = 86
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
MESE_BENCH = 10
ROT = 3.5
ALFA = 6.0
VOLS = (0.0, 2.0, 5.0, 10.0, 15.0, 20.0)
NDRAW = 200
SEME = 20260731
BERSAGLIO = 1.00


def main():
    ind_g = dataio.ff_ind49_daily().dropna(axis=1, how="all").dropna()
    ind_g = ind_g[ind_g.index.year <= FINE]
    ind_m = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind_m = ind_m[ind_m.index.year <= FINE]
    ind_m.index = pd.DatetimeIndex(ind_m.index).to_period("M").to_timestamp("M")
    ind_m = ind_m[ind_g.columns]
    rf = dataio.ff_factors_monthly()["RF"]
    rf.index = pd.DatetimeIndex(rf.index).to_period("M").to_timestamp("M")

    print(f"{'=' * 104}\nO8 — quanto costa che l'alfa sia volatile invece che "
          f"costante\n{'=' * 104}")

    W = pd.DataFrame(0.0, index=ind_m.index, columns=ind_m.columns)
    W.loc[W.index.month == MESE_BENCH] = 1.0 / ind_m.shape[1]
    net_b, turn_b = simula(ind_g, W, 0)
    idx = net_b.dropna().index
    net_b, turn_b = net_b.reindex(idx), turn_b.reindex(idx)
    rfx = rf.reindex(idx).fillna(0.0)
    bench = B.eval_stream("x", net_b, rfx, turn_b)

    # ---------------------- la volatilita' vera del candidato, misurata non assunta
    score = (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(3)
    net_c, _ = simula(ind_g, pesi_top(score, 5), 0)
    d = (net_c.reindex(idx) - net_b).dropna()
    te = float(d.std(ddof=1) * np.sqrt(12) * 100)
    print(f"   Benchmark: equal-weight annuale, IRR {bench['irr_ref']:.2f}%, "
          f"aliquota {bench['rate_ref']}%.")
    print(f"   **Tracking error vero del 12-3 top-5 contro il benchmark: "
          f"{te:.2f} punti annualizzati** (la voce diceva «circa 14»).")
    print(f"   Griglia: rotazione {ROT}x, alfa lordo {ALFA:.0f} punti, "
          f"volatilita' dell'alfa {VOLS}, {NDRAW} estrazioni per cella.\n")

    tm = pd.Series(ROT / 12.0, index=idx)
    mu = np.log(1.0 + ALFA / 100.0) / 12.0
    n = len(idx)

    def margine(alfa_m):
        lordo = (1.0 + net_b) * (1.0 + alfa_m) - 1.0
        netto = lordo - tm * C.COST_ROUND_TRIP
        r = B.eval_stream("x", netto, rfx, tm)
        return r["irr_ref"] - bench["irr_ref"]

    rng = np.random.default_rng(SEME)
    print(f"   {'vol alfa':>10}{'mediana':>11}{'media':>10}{'p5':>10}{'p95':>10}"
          f"{'perdita':>11}{'alfa richiesto':>17}")
    print("   " + "-" * 79)
    ris, base = [], None
    for v in VOLS:
        sm = (v / 100.0) / np.sqrt(12.0)
        if v == 0.0:
            vals = np.array([margine(pd.Series(np.exp(mu) - 1.0, index=idx))])
        else:
            vals = np.array([
                margine(pd.Series(np.exp(mu + sm * rng.standard_normal(n)) - 1.0,
                                  index=idx))
                for _ in range(NDRAW)])
        med = float(np.median(vals))
        if base is None:
            base = med
        ris.append((v, med, float(vals.mean()),
                    float(np.percentile(vals, 5)),
                    float(np.percentile(vals, 95)), med - base))
        print(f"   {v:>9.0f} {med:>+10.2f}{vals.mean():>+10.2f}"
              f"{np.percentile(vals, 5):>+10.2f}{np.percentile(vals, 95):>+10.2f}"
              f"{med - base:>+11.2f}", end="")
        print("" if v == 0 else "")

    # ---- pendenza locale del margine rispetto all'alfa, per convertire in "alfa richiesto"
    m6 = base
    a8 = np.log(1.0 + 8.0 / 100.0) / 12.0
    m8 = margine(pd.Series(np.exp(a8) - 1.0, index=idx))
    pend = (m8 - m6) / 2.0
    print(f"\n   pendenza del margine rispetto all'alfa a {ROT}x: "
          f"**{pend:.3f} punti di margine per punto di alfa** "
          f"(da {m6:+.2f} a 6 e {m8:+.2f} a 8)")
    print(f"\n   {'vol alfa':>10}{'perdita di margine':>22}"
          f"{'alfa in piu richiesto':>25}{'tasso di cambio':>18}")
    print("   " + "-" * 76)
    for v, med, _, _, _, perd in ris:
        extra = -perd / pend if pend > 0 else np.nan
        print(f"   {v:>9.0f}{perd:>+22.2f}{extra:>+25.2f}"
              f"{5.27 + extra:>18.2f}")

    # ------------------------------------------- la cella che corrisponde al vero
    vv = np.array([r[0] for r in ris])
    mm = np.array([r[1] for r in ris])
    med_te = float(np.interp(te, vv, mm))
    perd_te = med_te - base
    print(f"\n   **Alla volatilita' vera del candidato ({te:.2f} punti) la perdita "
          f"interpolata e' {perd_te:+.2f} punti.**")
    print(f"   (il giro 83 aveva stimato indirettamente ~0,8; la voce prevedeva "
          f"fra 0,5 e 1,2)")

    # ------------------------------------------------------------- verdetto
    perd_max = ris[-1][5]
    monot = all(ris[i][1] >= ris[i + 1][1] - 1e-9 for i in range(len(ris) - 1))
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: la mediana SCENDE in modo monotono; alla volatilita' "
          f"vera la perdita sta FRA 0,5 E 1,2.")
    print(f"   FALSIFICATA se la mediana NON SCENDE, o scende di MENO DI 0,2 "
          f"anche a 20, OPPURE se supera 2,5.\n")
    c_mon = monot
    c_int = 0.5 <= abs(perd_te) <= 1.2
    scende = perd_max < 0
    print(f"   mediana monotona decrescente : {'SI' if c_mon else 'NO'}")
    print(f"   scende a vol 20              : {'SI' if scende else 'NO'}"
          f"   ({perd_max:+.2f})")
    print(f"   perdita alla vol vera in [0,5; 1,2]: "
          f"{'SI' if c_int else 'NO'}   ({abs(perd_te):.2f})")
    fals = (not scende) or (abs(perd_max) < 0.2) or (abs(perd_max) > 2.5)
    print(f"\n   -> ipotesi O8 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    if fals:
        if not scende or abs(perd_max) < 0.2:
            print(f"      ramo 1: la volatilita' dell'alfa non spiega lo scarto "
                  f"del giro 83. La causa e' altrove.")
        else:
            print(f"      ramo 2: la volatilita' conta piu' della rotazione.")

    pd.DataFrame(ris, columns=["vol_alfa", "mediana", "media", "p5", "p95",
                               "perdita"]).to_csv(OUT / "round86_o8.csv",
                                                  index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="O8 volatilita dell'alfa",
                         config=f"vol={r[0]:.0f} rot={ROT} alfa={ALFA:.0f}",
                         window=f"1969-{FINE}", sharpe="", irr="",
                         bh_irr=bench["irr_ref"], excess=r[1], n_obs=len(idx),
                         note=f"p5={r[3]:.2f},p95={r[4]:.2f}") for r in ris])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

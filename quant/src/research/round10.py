"""Giro 10 — Scansione sistematica della letteratura (Chen & Zimmermann).

Invece di leggere paper uno per uno, uso il database di 212 anomalie gia'
replicate, con anno di pubblicazione, giornale e dettagli di costruzione.
La domanda non e' "quali anomalie esistono" ma "quali sopravvivono a TUTTI
e quattro i filtri che contano per me":

  1. premio POST-pubblicazione positivo e statisticamente distinguibile da zero
     (il pre-pubblicazione non serve a niente: e' il campione dell'autore)
  2. costruzione value-weighted, non equal-weighted: un portafoglio EW mette
     una società da 20 milioni accanto ad Apple e non e' eseguibile con
     500 EUR al mese
  3. quantile largo (decili o quintili, non l'1% estremo): capacita' e liquidita'
  4. il premio deve superare i costi di implementazione retail stimati

Chi passa tutti e quattro entra nel giro 11 come ingrediente per portafogli
compositi. Ogni segnale valutato conta come un tentativo nel registro.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from research import lab

ROUND = 10
HYP = "H10 scansione sistematica delle anomalie pubblicate (OSAP)"

# costi retail per un long-short mensile, stessa base dei giri precedenti
BORROW_SHORT = 0.05          # prestito titoli sulla gamba short
TURNOVER_ANN = 3.0           # 300%/anno bilaterale, prudente per un decile L/S


def implementation_drag():
    return TURNOVER_ANN * C.COST_ROUND_TRIP + BORROW_SHORT * 0.5


def main():
    ls = dataio.osap_ls_wide()
    doc = dataio.osap_signaldoc()
    drag = implementation_drag()

    print(f"Anomalie con serie di rendimenti: {ls.shape[1]}")
    print(f"Drag di implementazione retail applicato: {drag*100:.2f}%/anno\n")

    rows = []
    for acr in ls.columns:
        if acr not in doc.index:
            continue
        d = doc.loc[acr]
        if str(d.get("Cat.Signal", "")).strip() != "Predictor":
            continue
        try:
            yr = int(d["Year"])
        except (ValueError, TypeError):
            continue
        s = ls[acr].dropna()
        post = s[s.index.year >= yr]
        if len(post) < 120:                     # almeno 10 anni post-pubblicazione
            continue
        t, _ = stats.ttest_1samp(post, 0.0)
        gross = post.mean() * 1200
        net = gross - drag * 100
        sw = str(d.get("Stock Weight", "")).strip().upper()
        try:
            q = float(d.get("LS Quantile", np.nan))
        except (ValueError, TypeError):
            q = np.nan
        rows.append(dict(
            acr=acr, year=yr, authors=str(d.get("Authors", ""))[:28],
            journal=str(d.get("Journal", ""))[:6], n_post=len(post),
            gross=gross, net=net, t=float(t),
            sharpe=float(post.mean() / post.std() * np.sqrt(12)),
            vw=(sw == "VW"), quantile=q,
            mean_median=float(post.mean() / post.median()) if post.median() else np.inf,
        ))

    df = pd.DataFrame(rows)
    print(f"Anomalie con >=10 anni di storia post-pubblicazione: {len(df)}")

    f1 = df["t"] > 2.0
    f2 = df["vw"]
    f3 = df["quantile"] >= 0.1
    f4 = df["net"] > 0
    print(f"\n{'filtro':<52}{'passano':>9}")
    print(f"{'1. t-stat post-pubblicazione > 2':<52}{int(f1.sum()):>9}")
    print(f"{'2. value-weighted (eseguibile)':<52}{int(f2.sum()):>9}")
    print(f"{'3. quantile >= 10% (capacita)':<52}{int(f3.sum()):>9}")
    print(f"{'4. premio netto dei costi retail > 0':<52}{int(f4.sum()):>9}")
    print(f"{'   tutti e quattro insieme':<52}{int((f1&f2&f3&f4).sum()):>9}")

    surv = df[f1 & f2 & f3 & f4].sort_values("net", ascending=False)
    print(f"\n--- Sopravvissuti a tutti i filtri ---")
    if len(surv) == 0:
        print("  NESSUNO.")
    else:
        print(f"{'segnale':<24}{'autori':<30}{'anno':>6}{'lordo':>9}{'netto':>9}"
              f"{'t':>6}{'Sharpe':>8}")
        for _, r in surv.iterrows():
            print(f"{r['acr']:<24}{r['authors']:<30}{r['year']:>6}"
                  f"{r['gross']:>8.2f}%{r['net']:>8.2f}%{r['t']:>6.2f}{r['sharpe']:>8.2f}")

    # per confronto: i migliori senza il filtro di eseguibilita'
    print(f"\n--- Per confronto: i 8 migliori ignorando VW e quantile ---")
    top = df[f1 & f4].sort_values("net", ascending=False).head(8)
    print(f"{'segnale':<24}{'netto':>9}{'t':>6}{'peso':>6}{'quant.':>8}"
          f"{'media/mediana':>15}")
    for _, r in top.iterrows():
        print(f"{r['acr']:<24}{r['net']:>8.2f}%{r['t']:>6.2f}"
              f"{'VW' if r['vw'] else 'EW':>6}{r['quantile']:>8.2f}"
              f"{r['mean_median']:>15.1f}")
    print("  Un rapporto media/mediana molto sopra 1 = il premio sta in pochi mesi")
    print("  estremi. Colonna 'peso' EW = non eseguibile con 500 EUR/mese.")

    # registro: ogni anomalia valutata e' un tentativo
    lab.log_trials([dict(round=ROUND, hypothesis=HYP, config=r["acr"],
                         window="POST-PUB", sharpe=r["sharpe"], irr=r["net"],
                         bh_irr=0.0, excess=r["net"], n_obs=r["n_post"],
                         note=f"t={r['t']:.2f},vw={r['vw']}")
                    for _, r in df.iterrows()])
    print(f"\nTentativi registrati in questo giro: {len(df)}   "
          f"cumulati: {lab.n_trials_so_far()}")
    surv.to_csv(lab.RESEARCH / "osap_survivors.csv", index=False)
    return surv


if __name__ == "__main__":
    main()

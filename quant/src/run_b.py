"""Gruppo B: anomalie cross-sectional, split alla data di PUBBLICAZIONE.

Lo split non e' a meta' campione: serve a misurare se il premio sopravvive
dopo che il mercato ha letto il paper. McLean & Pontiff (2016) trovano un
decadimento medio del ~50% post-pubblicazione; qui lo verifico sia sulle tre
anomalie richieste sia sull'intero universo replicato da Chen-Zimmermann.
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

import dataio
import config as C

OUT = Path(__file__).resolve().parents[1] / "out"

# anomalia -> (serie, anno di pubblicazione, riferimento, note di implementabilita')
NAMED = {
    "Bet Against Beta": dict(
        src="aqr", key="USA", year=2014,
        ref="Frazzini & Pedersen, JFE 111:1-25, 2014",
        impl="richiede leva sulla gamba a beta basso: il rendimento AQR non "
             "addebita alcun costo di finanziamento retail"),
    "Accruals": dict(
        src="osap", key="Accruals", year=1996,
        ref="Sloan, The Accounting Review, 1996",
        impl="richiede bilanci trimestrali e lo short su small cap illiquide"),
    "Short interest": dict(
        src="osap", key="ShortInterest", year=2001,
        ref="Dechow et al., JFE, 2001",
        impl="la gamba short e' proprio sui titoli piu' cari da prendere a "
             "prestito: il costo del prestito titoli mangia il premio"),
    "Short interest / IO": dict(
        src="osap", key="IO_ShortInterest", year=2005,
        ref="Asquith, Pathak & Ritter, JFE, 2005",
        impl="stessa criticita' del precedente, su un sottoinsieme ancora piu' "
             "stretto e meno liquido"),
}


def ann(x):
    return (1 + x).prod() ** (12 / len(x)) - 1 if len(x) else np.nan


def split_stats(s, year):
    pre = s[s.index.year < year]
    post = s[s.index.year >= year]
    out = {}
    for lbl, x in (("pre", pre), ("post", post)):
        if len(x) < 24:
            out[lbl] = dict(n=len(x), mean_ann=np.nan, t=np.nan, sharpe=np.nan)
            continue
        t, _ = stats.ttest_1samp(x, 0.0)
        out[lbl] = dict(n=len(x), mean_ann=x.mean() * 12 * 100,
                        t=float(t), sharpe=float(x.mean() / x.std() * np.sqrt(12)))
    a, b = out["pre"]["mean_ann"], out["post"]["mean_ann"]
    out["decay_pct"] = (1 - b / a) * 100 if (a and np.isfinite(a) and a != 0) else np.nan
    return out


def main():
    ls = dataio.osap_ls_wide()
    doc = dataio.osap_signaldoc()
    bab = dataio.aqr_bab("USA")

    print("--- Gruppo B: premio lordo prima e dopo la pubblicazione ----------")
    print(f"{'Anomalia':<22}{'pubbl.':>7}{'pre %/anno':>12}{'t':>7}"
          f"{'post %/anno':>13}{'t':>7}{'decadim.':>10}{'mesi post':>11}")
    print("-" * 92)
    rows = []
    for name, meta in NAMED.items():
        s = bab if meta["src"] == "aqr" else ls[meta["key"]].dropna()
        r = split_stats(s, meta["year"])
        rows.append(dict(name=name, year=meta["year"], ref=meta["ref"],
                         impl=meta["impl"], **{
                             "pre_ann": r["pre"]["mean_ann"], "pre_t": r["pre"]["t"],
                             "post_ann": r["post"]["mean_ann"], "post_t": r["post"]["t"],
                             "post_sharpe": r["post"]["sharpe"],
                             "decay": r["decay_pct"], "n_post": r["post"]["n"]}))
        print(f"{name:<22}{meta['year']:>7}{r['pre']['mean_ann']:>11.2f}%"
              f"{r['pre']['t']:>7.2f}{r['post']['mean_ann']:>12.2f}%"
              f"{r['post']['t']:>7.2f}{r['decay_pct']:>9.0f}%{r['post']['n']:>11}")

    # ------------------------------------------------ McLean-Pontiff su tutto OSAP
    print("\n--- Verifica McLean-Pontiff su tutte le anomalie replicate --------")
    decays, pres, posts = [], [], []
    for acr in ls.columns:
        if acr not in doc.index:
            continue
        row = doc.loc[acr]
        if str(row.get("Cat.Signal", "")).strip() != "Predictor":
            continue
        try:
            yr = int(row["Year"])
        except (ValueError, TypeError):
            continue
        s = ls[acr].dropna()
        if len(s) < 120:
            continue
        pre = s[s.index.year < yr]
        post = s[s.index.year >= yr]
        if len(pre) < 60 or len(post) < 60:
            continue
        a, b = pre.mean() * 12 * 100, post.mean() * 12 * 100
        if a <= 0:
            continue                      # il premio in-sample deve esistere
        pres.append(a); posts.append(b); decays.append((1 - b / a) * 100)
    decays = np.array(decays)
    print(f"  Anomalie con premio pre-pubblicazione positivo e storia sufficiente: {len(decays)}")
    print(f"  Premio medio  PRE  : {np.mean(pres):6.2f}%/anno")
    print(f"  Premio medio  POST : {np.mean(posts):6.2f}%/anno")
    print(f"  Decadimento medio  : {np.mean(decays):6.1f}%   mediano: {np.median(decays):.1f}%")
    print(f"  Atteso McLean-Pontiff (2016): ~50%")
    print(f"  Quota di anomalie con premio post-pubblicazione negativo: "
          f"{100*np.mean(np.array(posts) < 0):.0f}%")

    # ------------------------------------------------ qualita' della serie
    print("\n--- Prima dei costi: la serie e' investibile? ---------------------")
    print(f"{'Anomalia':<22}{'vol/anno':>10}{'Sharpe':>8}{'peggior m.':>12}"
          f"{'miglior m.':>12}{'media/mediana':>15}")
    print("-" * 79)
    quality = {}
    for name, meta in NAMED.items():
        s = bab if meta["src"] == "aqr" else ls[meta["key"]].dropna()
        post = s[s.index.year >= meta["year"]]
        ratio = post.mean() / post.median() if post.median() != 0 else np.inf
        quality[name] = dict(vol=post.std() * np.sqrt(12) * 100,
                             sharpe=post.mean() / post.std() * np.sqrt(12),
                             worst=post.min() * 100, best=post.max() * 100,
                             mean_median=float(ratio))
        q = quality[name]
        print(f"{name:<22}{q['vol']:>9.1f}%{q['sharpe']:>8.2f}{q['worst']:>11.1f}%"
              f"{q['best']:>11.1f}%{q['mean_median']:>15.1f}")
    print("  Un rapporto media/mediana molto sopra 1 vuol dire che il premio sta")
    print("  in pochi mesi estremi su titoli minuscoli, non in un edge ripetibile.")

    # ------------------------------------------------ implementabilita'
    # Ipotesi dichiarate, tutte sfavorevoli quanto la letteratura suggerisce:
    #  - i portafogli OSAP sono EQUAL-WEIGHTED: la gamba short pesa quanto la long
    #    su titoli minuscoli. Con 500 EUR/mese la gamba short non e' eseguibile.
    #  - prestito titoli: 5%/anno sul nozionale short e' prudente per il decile
    #    piu' shortato; sui titoli hard-to-borrow si va ben oltre.
    #  - BAB: la gamba a beta basso va levereggiata ~1,4x per arrivare a beta 1.
    #    Un retail paga benchmark+3% sulla parte a prestito, AQR no.
    BORROW_SHORT = 0.05
    print("\n--- Implementabilita': cosa resta dopo i costi reali --------------")
    print(f"{'Anomalia':<22}{'post lordo':>12}{'transaz.':>10}{'prestito':>10}"
          f"{'finanz.':>9}{'netto':>9}")
    print("-" * 72)
    impl_rows = []
    for r in rows:
        turnover = 6.0 if "Short" in r["name"] else 2.0   # mensile vs annuale
        tc = turnover * C.COST_ROUND_TRIP * 100
        borrow = BORROW_SHORT * 0.5 * 100                 # short = meta' nozionale
        fin = (C.FIN_SPREAD * 0.43 * 100) if r["name"] == "Bet Against Beta" else 0.0
        net = r["post_ann"] - tc - borrow - fin
        impl_rows.append(dict(name=r["name"], turnover=turnover, tc=tc,
                              borrow=borrow, fin=fin, net=net))
        print(f"{r['name']:<22}{r['post_ann']:>11.2f}%{tc:>9.2f}%{borrow:>9.2f}%"
              f"{fin:>8.2f}%{net:>8.2f}%")

    OUT.mkdir(exist_ok=True)
    with open(OUT / "group_b.json", "w") as f:
        json.dump({"named": rows, "impl": impl_rows, "quality": quality,
                   "mp_n": len(decays), "mp_mean_decay": float(np.mean(decays)),
                   "mp_median_decay": float(np.median(decays)),
                   "mp_pre": float(np.mean(pres)), "mp_post": float(np.mean(posts)),
                   "mp_share_negative": float(np.mean(np.array(posts) < 0))},
                  f, indent=1, default=float)
    return rows


if __name__ == "__main__":
    main()

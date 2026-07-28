"""Giro 62 — D5: la quota di vittorie per finestra e' un indicatore ingannevole.

VOCE DELLA CODA, predizione verbatim:

D5 — La quota di vittorie per finestra e' un indicatore ingannevole
  Nata al giro 59. H5 vince 31 finestre decennali su 46 (67,4%) e ha
  extra-rendimento medio +0,16%, cioe' praticamente zero: mediana +0,54%, media
  +0,16%, e la differenza sta tutta in quattro finestre che contengono il 2008
  (-5,78%, -5,69%, -3,61%, -3,24%). Se il disaccordo fra "vince spesso" e "rende
  in media" e' sistematico, allora ogni tabella di questo progetto che riporta
  una quota di vittorie sta sovrastimando le strategie che ruotano, e vanno
  rilette tutte — F1 (regioni top-1, +0,30), E6 (17/17 finestre), H1 (73% dei
  decenni). Da misurare su TUTTI i candidati mai valutati nel progetto: quota di
  vittorie su finestre decennali, media, mediana, e lo scarto mediana - media.
  PREDIZIONE: lo scarto mediana - media e' positivo per almeno l'80% dei
  candidati (cioe' la coda sinistra domina ovunque, non solo per H5), e almeno
  un terzo dei candidati che vincono oltre meta' delle finestre ha media <= 0.
  Il meccanismo e' che una strategia tassata sul realizzato incassa il premio in
  tanti piccoli pezzi e restituisce il capitale in un colpo solo, senza
  recuperare l'imposta gia' pagata.
  FALSIFICATA SE: lo scarto mediana - media e' positivo per meno del 60% dei
  candidati, oppure nessun candidato con quota di vittorie sopra il 50% ha media
  negativa.

DUE SCELTE DICHIARATE PRIMA DI GUARDARE I NUMERI.

1. "Tutti i candidati mai valutati nel progetto" non e' letteralmente eseguibile:
   molti vivono su universi diversi (cripto, valute, opzioni) con storie di 6-30
   anni, e mescolarli renderebbe la statistica un miscuglio di periodi. Prendo
   invece l'insieme piu' ampio che condivide ESATTAMENTE universo e finestra: 21
   candidati sui 49 settori, 1969-2026, che coprono tutte le famiglie provate nel
   progetto (momentum a piu' orizzonti e concentrazioni, low-vol, punteggi misti,
   reversione, inverse-vol, filtri di tendenza, ribilanciamenti). E' una scelta
   restrittiva e la dichiaro: se il fenomeno c'e', deve vedersi qui.

2. La rotazione e' misurata sui pesi DERIVATI, non su |W_t - W_{t-1}|. E' il
   difetto trovato al giro 60 e registrato come voce D6. Non lo sto eseguendo:
   sto solo evitando di ripeterlo in un giro nuovo, dove sarebbe un errore noto.

Benchmark: cap-weight dello stesso universo, la scelta stabilita al giro 60.
Nessuna selezione: N resta la famiglia pre-dichiarata della coda.
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
from research import lab, bench as B

ROUND = 62
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 62
LUNG = 10


def esegui(rets, Wt, cost=C.COST_ROUND_TRIP):
    """Rendimento netto e rotazione VERA di un portafoglio a pesi target.

    I pesi derivano coi rendimenti fra un ribilanciamento e l'altro; la
    rotazione e' la distanza fra il target e i pesi derivati, non fra due
    target consecutivi.
    """
    n = rets.shape[1]
    w = np.zeros(n)
    held, turns = [], []
    for i in range(len(rets)):
        tgt = Wt.iloc[i].to_numpy(dtype=float)
        if tgt.sum() <= 0:
            tgt = w
        turns.append(float(np.abs(tgt - w).sum() / 2.0))
        w = tgt
        held.append(w.copy())
        g = w * (1 + rets.iloc[i].to_numpy(dtype=float))
        s = g.sum()
        w = g / s if s > 0 else w
    W = pd.DataFrame(held, index=rets.index, columns=rets.columns)
    turn = pd.Series(turns, index=rets.index)
    return (W * rets).sum(axis=1) - turn * cost, turn


def topw(score, top, asc=False):
    rk = score.rank(axis=1, ascending=asc)
    W = (rk <= top).astype(float)
    return W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def tieni_annuale(W):
    keep = pd.Series(W.index.month == 1, index=W.index)
    return W.where(keep).ffill().fillna(0.0)


def candidati(ind, cap):
    """Ventuno candidati, una per famiglia provata nel progetto."""
    out = {}
    n = ind.shape[1]
    mom12 = (1 + ind).rolling(11).apply(np.prod, raw=True).shift(2)
    mom6 = (1 + ind).rolling(5).apply(np.prod, raw=True).shift(2)
    mom3 = (1 + ind).rolling(2).apply(np.prod, raw=True).shift(2)
    rev1 = ind.shift(1)
    vol36 = ind.rolling(36).std().shift(1)
    vol12 = ind.rolling(12).std().shift(1)

    for k in (1, 3, 5, 10, 25):
        out[f"momentum 12-2 top-{k}"] = topw(mom12, k)
    out["momentum 12-2 top-10 annuale"] = tieni_annuale(topw(mom12, 10))
    out["momentum 12-2 top-5 annuale"] = tieni_annuale(topw(mom12, 5))
    out["momentum 6-2 top-10"] = topw(mom6, 10)
    out["momentum 3-2 top-10"] = topw(mom3, 10)
    out["reversione 1 mese top-10"] = topw(rev1, 10, asc=True)
    out["momentum 1 mese top-10"] = topw(rev1, 10)
    for k in (5, 10, 25):
        out[f"low-vol 36m top-{k}"] = topw(vol36, k, asc=True)
    out["low-vol 12m top-10"] = topw(vol12, 10, asc=True)
    out["high-vol 36m top-10"] = topw(vol36, 10)
    mix = mom12.rank(axis=1, pct=True) + (-vol36).rank(axis=1, pct=True)
    out["punteggio misto mom+lowvol"] = topw(mix, 10)
    iv = (1.0 / vol36.replace(0, np.nan))
    out["inverse-volatility (tutti)"] = iv.div(iv.sum(axis=1), axis=0).fillna(0.0)
    out["equal-weight mensile"] = pd.DataFrame(1.0 / n, index=ind.index,
                                               columns=ind.columns)
    out["equal-weight annuale"] = tieni_annuale(out["equal-weight mensile"].copy())
    # filtro di tendenza sull'equal-weight: dentro o fuori, non selezione
    px = (1 + ind.mean(axis=1)).cumprod()
    dentro = B.ma_filter(px, 10)
    out["filtro di tendenza 10m su EW"] = (
        pd.DataFrame(1.0 / n, index=ind.index, columns=ind.columns)
        .mul(dentro, axis=0).fillna(0.0))
    return out


def main():
    vw, _, nf, sz = dataio.ff_ind49_monthly()
    ind = vw.dropna(axis=1, how="all").dropna()
    cap = (nf * sz).reindex(ind.index)[ind.columns]
    cap = cap.where(cap > 0).ffill()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    y0, y1 = ind.index[0].year, ind.index[-1].year

    print(f"{'=' * 104}\nD5 — quota di vittorie contro rendimento medio, "
          f"su finestre decennali\n{'=' * 104}")
    print(f"   Universo: 49 settori, {y0}-{y1}. Benchmark: cap-weight dello "
          f"stesso universo (giro 60).")

    Wcap = cap.div(cap.sum(axis=1), axis=0).shift(1).fillna(0.0)
    bnet, bturn = esegui(ind, Wcap)
    cands = candidati(ind, cap)
    streams = {nm: esegui(ind, W) for nm, W in cands.items()}
    print(f"   {len(cands)} candidati, tutti sulla stessa finestra e sullo "
          f"stesso universo.\n")

    spans = [(y, y + LUNG - 1) for y in range(y0 + 3, y1 - LUNG + 2)]
    print(f"   {len(spans)} finestre decennali, da {spans[0][0]}-{spans[0][1]} "
          f"a {spans[-1][0]}-{spans[-1][1]}\n")

    def irr_win(net, turn, i):
        s = net.reindex(i).dropna()
        if len(s) < 100:
            return None
        r = B.eval_stream("x", s, rf.reindex(s.index).fillna(0.0),
                          turn.reindex(s.index))
        return r["irr_ref"]

    bench_irr = {}
    for a, b in spans:
        i = ind.index[(ind.index.year >= a) & (ind.index.year <= b)]
        bench_irr[(a, b)] = irr_win(bnet, bturn, i)

    righe = []
    for nm, (net, turn) in streams.items():
        vals = []
        for a, b in spans:
            i = ind.index[(ind.index.year >= a) & (ind.index.year <= b)]
            x = irr_win(net, turn, i)
            bq = bench_irr[(a, b)]
            if x is not None and bq is not None and np.isfinite(x) and np.isfinite(bq):
                vals.append(x - bq)
        v = np.array(vals)
        righe.append(dict(candidato=nm, n=len(v), quota=float((v > 0).mean()),
                          media=float(v.mean()), mediana=float(np.median(v)),
                          scarto=float(np.median(v) - v.mean()),
                          minimo=float(v.min()), massimo=float(v.max())))

    righe.sort(key=lambda r: -r["quota"])
    print(f"   {'candidato':<32}{'vince':>8}{'media':>9}{'mediana':>10}"
          f"{'mediana-media':>15}{'min':>9}{'max':>9}")
    print("   " + "-" * 92)
    for r in righe:
        flag = " <<<" if r["quota"] > 0.5 and r["media"] <= 0 else ""
        print(f"   {r['candidato']:<32}{r['quota'] * 100:>7.1f}%"
              f"{r['media']:>8.2f}%{r['mediana']:>9.2f}%{r['scarto']:>14.2f}%"
              f"{r['minimo']:>8.2f}%{r['massimo']:>8.2f}%{flag}")

    # ------------------------------------------------------------ verdetto
    K = len(righe)
    pos = sum(1 for r in righe if r["scarto"] > 0)
    quota_pos = pos / K
    vincenti = [r for r in righe if r["quota"] > 0.5]
    ingann = [r for r in vincenti if r["media"] <= 0]
    q_ing = len(ingann) / len(vincenti) if vincenti else float("nan")

    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: scarto mediana-media positivo per almeno l'80% dei "
          f"candidati, E almeno")
    print(f"   un terzo di quelli che vincono oltre meta' delle finestre ha "
          f"media <= 0.")
    print(f"   FALSIFICATA se lo scarto e' positivo per meno del 60%, OPPURE "
          f"nessun candidato")
    print(f"   con quota sopra il 50% ha media negativa.\n")
    print(f"   scarto mediana-media positivo : {pos}/{K} = {quota_pos * 100:.1f}%"
          f"   (previsto >=80%, falsifica sotto 60%)")
    print(f"   candidati che vincono >50%    : {len(vincenti)}/{K}")
    print(f"   di questi, con media <= 0     : {len(ingann)}"
          f"   ({q_ing * 100:.1f}%)   (previsto >=33,3%, falsifica se 0)")
    if ingann:
        print(f"   i casi ingannevoli:")
        for r in ingann:
            print(f"     {r['candidato']:<32} vince {r['quota'] * 100:.1f}% "
                  f"e rende {r['media']:+.2f}% in media")

    fals = (quota_pos < 0.60) or (len(ingann) == 0)
    print(f"\n   -> ipotesi D5 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'scarto positivo per >=80%': "
          f"{'centrata' if quota_pos >= 0.80 else 'SBAGLIATA'}")
    print(f"      clausola 'almeno 1/3 degli ingannevoli': "
          f"{'centrata' if q_ing >= 1 / 3 else 'SBAGLIATA'}")

    # il meccanismo dichiarato nella predizione: e' la rotazione?
    print(f"\n   Il meccanismo previsto era la tassazione sul realizzato. "
          f"Correlazione fra")
    print(f"   rotazione e scarto mediana-media, sui {K} candidati:")
    tp = np.array([float(streams[r["candidato"]][1].sum())
                   / (len(ind) / 12) for r in righe])
    sc = np.array([r["scarto"] for r in righe])
    md = np.array([r["media"] for r in righe])
    print(f"     corr(rotazione, scarto) = {np.corrcoef(tp, sc)[0, 1]:+.3f}")
    print(f"     corr(rotazione, media)  = {np.corrcoef(tp, md)[0, 1]:+.3f}")

    # ---- controllo: il fenomeno dipende dal benchmark?
    # Al giro 59 il confronto era contro l'EQUAL-WEIGHT e lo scarto di H5 era
    # POSITIVO (+0,38). Qui contro il cap-weight e' negativo. Se il segno dipende
    # dal benchmark, allora "mediana meno media" non e' una proprieta' della
    # strategia e la voce D5 e' mal posta a monte.
    ewnet, ewturn = esegui(ind, cands["equal-weight mensile"])
    ew_irr = {}
    for a, b in spans:
        i = ind.index[(ind.index.year >= a) & (ind.index.year <= b)]
        ew_irr[(a, b)] = irr_win(ewnet, ewturn, i)
    r2 = []
    for nm, (net, turn) in streams.items():
        vals = []
        for a, b in spans:
            i = ind.index[(ind.index.year >= a) & (ind.index.year <= b)]
            x = irr_win(net, turn, i)
            bq = ew_irr[(a, b)]
            if x is not None and bq is not None and np.isfinite(x) and np.isfinite(bq):
                vals.append(x - bq)
        v = np.array(vals)
        if len(v) == 0 or v.std() == 0:
            continue
        r2.append(dict(candidato=nm, quota=float((v > 0).mean()),
                       media=float(v.mean()), scarto=float(np.median(v) - v.mean())))
    pos2 = sum(1 for r in r2 if r["scarto"] > 0)
    vinc2 = [r for r in r2 if r["quota"] > 0.5]
    ing2 = [r for r in vinc2 if r["media"] <= 0]
    print(f"\n   CONTROLLO — stessa misura contro l'EQUAL-WEIGHT (benchmark del giro 59):")
    print(f"     scarto positivo : {pos2}/{len(r2)} = {pos2 / len(r2) * 100:.1f}%"
          f"   (contro cap-weight era {quota_pos * 100:.1f}%)")
    print(f"     ingannevoli     : {len(ing2)}/{len(vinc2)} che vincono >50%")
    fals2 = (pos2 / len(r2) < 0.60) or (len(ing2) == 0)
    print(f"     con questo benchmark D5 sarebbe "
          f"{'FALSIFICATA' if fals2 else 'CONFERMATA'}")
    print(f"     -> il segno dello scarto "
          f"{'DIPENDE' if fals2 != fals else 'NON dipende'} dal benchmark")

    pd.DataFrame(r2).to_csv(OUT / "round62_vs_ew.csv", index=False)
    r2d = {r["candidato"]: r for r in r2}
    print(f"\n   I cinque che vincono piu' della meta' delle finestre, "
          f"contro i due benchmark:")
    print(f"     {'candidato':<32}{'vs cap-w':>10}{'vs EW':>9}")
    for r in righe[:5]:
        e = r2d.get(r["candidato"])
        ev = f"{e['media']:>8.2f}%" if e else "     n.d."
        print(f"     {r['candidato']:<32}{r['media']:>9.2f}%{ev}")

    df = pd.DataFrame(righe)
    df["rotazione"] = tp
    df.to_csv(OUT / "round62_d5.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="D5 quota di vittorie contro media",
                         config=r["candidato"], window=f"{y0}-{y1}", sharpe="",
                         irr="", bh_irr="", excess=r["media"], n_obs=r["n"],
                         note=f"quota={r['quota']:.3f},scarto={r['scarto']:.3f}")
                    for r in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

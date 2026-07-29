"""Giro 76 — L4: il ritardo di venti giorni e' davvero uno skip piu' lungo?

VOCE DELLA CODA, predizione verbatim (committata prima di eseguire):

L4 — Il ritardo di venti giorni e' davvero uno skip piu' lungo?
  Nata al giro 73. Il momentum 12-2 top-5 ritardato di venti giorni di borsa
  passa da -0,87 a +0,86 contro l'equal-weight annuale. L'ipotesi meccanica e'
  che ritardare l'esecuzione di un mese equivalga a saltare un mese in piu',
  cioe' a usare un momentum 12-3 invece del 12-2: se e' cosi', l'effetto deve
  vedersi misurando il 12-3 DIRETTAMENTE, senza passare dal ritardo. Se non si
  vede li', il +0,86 era rumore e va chiuso.
  Da misurare: momentum 12-k top-5 e top-10 mensile per k = 1, 2, 3, 4, 6 (skip
  crescente) sui 49 settori, contro l'equal-weight annuale con la rotazione
  vera, finestra 1969-2009. Confrontare il 12-3 senza ritardo col 12-2 ritardato
  di venti giorni: se il meccanismo e' quello, devono coincidere entro 0,3 punti.
  PREDIZIONE: il 12-3 senza ritardo NON riproduce il +0,86 e resta SOTTO LO ZERO,
  entro 0,5 punti dal 12-2 senza ritardo, perche' lo skip non e' la variabile che
  conta a questa scala. Il profilo del margine in funzione di k e' PIATTO entro
  +-0,6 punti su tutti e cinque i valori: nessuno skip e' sistematicamente
  migliore. Il +0,86 del giro 73 era il massimo di dieci celle.
  FALSIFICATA SE: il 12-3 senza ritardo produce un margine POSITIVO e ENTRO 0,3
  PUNTI dal +0,86 misurato col ritardo — nel qual caso il meccanismo e' reale, lo
  skip conta, e va rifatto il gruppo A con lo skip come parametro dichiarato
  invece che fissato a 1 — OPPURE il profilo in k ha un'ampiezza sopra 1,5 punti,
  nel qual caso lo skip e' un grado di liberta' mai contato, come il calendario
  al giro 68.

===================== DUE SCELTE DICHIARATE PRIMA DI ESEGUIRE =====================

1. IL MOTORE E' QUELLO GIORNALIERO DEL GIRO 73, NON QUELLO MENSILE.
   La voce non lo specifica, ma la sua condizione di falsificazione confronta un
   numero con il +0,86, e quel numero e' nato nel motore giornaliero. Nel motore
   mensile lo stesso 12-2 top-5 vale +0,56 (giro 72) invece di -0,87: 1,43 punti
   di differenza fra i due motori, che e' piu' grande dell'effetto da misurare.
   Misurare il profilo in k con un motore e confrontarlo col +0,86 dell'altro
   sarebbe barare senza accorgersene. Uso il motore del giro 73 per tutto,
   ricalcolando anche il 12-2 a venti giorni dentro questo stesso giro invece di
   citarlo: se non riproduce +0,86, e' un problema mio e va detto.

2. "12-k" = FINESTRA DI 11 MESI, SKIP VARIABILE.
   Il progetto implementa il 12-2 come rolling(11).prod().shift(2), cioe' undici
   mesi di rendimenti che finiscono k mesi prima di quello da investire. Tengo la
   LUNGHEZZA fissa a 11 e muovo solo lo SKIP, perche' la voce chiede "skip
   crescente" e perche' cosi' k=2 riproduce esattamente il segnale del giro 73.
   L'altra lettura possibile ("12-k = 12 mesi meno k") cambierebbe due cose
   insieme e non risponderebbe alla domanda.

   k=1 non e' look-ahead: il segnale a t usa i rendimenti fino a t-1, che a fine
   mese t-1 sono noti, e i pesi entrano in vigore all'inizio di t.
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

ROUND = 76
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
SKIP = (1, 2, 3, 4, 6)
RITARDO_GIRO73 = 20
BERSAGLIO_73 = 0.86          # il numero da riprodurre o da chiudere
TOLL_COINCIDENZA = 0.30      # "devono coincidere entro 0,3 punti"
AMPIEZZA_FALS = 1.50         # "ampiezza sopra 1,5 punti" falsifica


def date_ribilancio(idx_g, ritardo):
    """Per ogni mese, il giorno di borsa in cui i pesi nuovi entrano in vigore."""
    s = pd.Series(range(len(idx_g)), index=idx_g)
    fine_mese = s.groupby([idx_g.year, idx_g.month]).max()
    out = {}
    for pos in fine_mese.values:
        j = pos + ritardo
        if j < len(idx_g):
            out[idx_g[j]] = idx_g[pos]
    return out


def simula(rets_g, target_mensile, ritardo, cost=C.COST_ROUND_TRIP):
    """Portafoglio giornaliero, rotazione vera |W_target - W_detenuti| / 2."""
    idx_g = rets_g.index
    n = rets_g.shape[1]
    quando = date_ribilancio(idx_g, ritardo)
    w = np.zeros(n)
    ret_g, turn_g = [], []
    for t, riga in zip(idx_g, rets_g.to_numpy(dtype=float)):
        tv = 0.0
        if t in quando:
            mese = quando[t].to_period("M").to_timestamp("M")
            if mese in target_mensile.index:
                tgt = target_mensile.loc[mese].to_numpy(dtype=float)
                if tgt.sum() > 0:
                    tv = float(np.abs(tgt - w).sum() / 2.0)
                    w = tgt
        ret_g.append(float(w @ riga) - tv * cost)
        turn_g.append(tv)
        g = w * (1 + riga)
        s = g.sum()
        w = g / s if s > 0 else w
    r = pd.Series(ret_g, index=idx_g)
    tu = pd.Series(turn_g, index=idx_g)
    key = idx_g.to_period("M").to_timestamp("M")
    return ((1 + r).groupby(key).prod() - 1), tu.groupby(key).sum()


def pesi_top(score, top):
    rk = score.rank(axis=1, ascending=False)
    W = (rk <= top).astype(float)
    return W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def pesi_ew_annuale(ind_m):
    """1/N ogni gennaio: fuori da gennaio il target e' vuoto (non si tocca)."""
    n = ind_m.shape[1]
    W = pd.DataFrame(0.0, index=ind_m.index, columns=ind_m.columns)
    W.loc[W.index.month == 1] = 1.0 / n
    return W


def main():
    ind_g = dataio.ff_ind49_daily().dropna(axis=1, how="all").dropna()
    ind_g = ind_g[ind_g.index.year <= FINE]
    ind_m = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind_m = ind_m[ind_m.index.year <= FINE]
    ind_m.index = pd.DatetimeIndex(ind_m.index).to_period("M").to_timestamp("M")
    ind_m = ind_m[ind_g.columns]
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    rf.index = pd.DatetimeIndex(rf.index).to_period("M").to_timestamp("M")

    print(f"{'=' * 100}\nL4 — lo skip contro il ritardo: il 12-3 riproduce il "
          f"+0,86 del giro 73?\n{'=' * 100}")
    print(f"   49 settori giornalieri, {ind_g.index[0].date()} → "
          f"{ind_g.index[-1].date()} ({len(ind_g)} giorni di borsa).")
    print(f"   **Holdout 2010-2026 non toccato.** Motore giornaliero del giro 73,"
          f" skip k = {', '.join(map(str, SKIP))}.\n")

    def irr(net, turn):
        i = net.dropna().index
        r = B.eval_stream("x", net.reindex(i), rf.reindex(i).fillna(0.0),
                          turn.reindex(i))
        r["rot"] = float(turn.reindex(i).sum()) / (len(i) / 12)
        r["net"] = net.reindex(i)
        return r

    # ---------------------------------------------------- benchmark, ritardo 0
    Wew = pesi_ew_annuale(ind_m)
    nb, tb = simula(ind_g, Wew, 0)
    bench = irr(nb, tb)
    print(f"   benchmark equal-weight annuale (ritardo 0): "
          f"IRR {bench['irr_ref']:.2f}%   rotazione {bench['rot']:.3f}x")

    # ---------------------------------------------------- il profilo in k
    momk = {k: (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(k)
            for k in SKIP}
    righe = []
    for top in (5, 10):
        print(f"\n   momentum 12-k **top-{top}** mensile, nessun ritardo")
        print("   " + "-" * 78)
        print(f"   {'skip k':<26}" + "".join(f"{k:>10}" for k in SKIP))
        irrs, marg, rots = [], [], []
        for k in SKIP:
            net, turn = simula(ind_g, pesi_top(momk[k], top), 0)
            r = irr(net, turn)
            irrs.append(r["irr_ref"])
            marg.append(r["irr_ref"] - bench["irr_ref"])
            rots.append(r["rot"])
            righe.append(dict(top=top, k=k, ritardo=0, irr=r["irr_ref"],
                              margine=r["irr_ref"] - bench["irr_ref"],
                              rot=r["rot"], aliq=r["rate_ref"], net=r["net"]))
        print(f"   {'IRR netta':<26}" + "".join(f"{v:>9.2f}%" for v in irrs))
        print(f"   {'margine vs EW annuale':<26}"
              + "".join(f"{v:>+9.2f} " for v in marg))
        print(f"   {'rotazione':<26}" + "".join(f"{v:>9.3f}x" for v in rots))
        amp = max(marg) - min(marg)
        dev = max(abs(v - float(np.mean(marg))) for v in marg)
        print(f"   {'ampiezza del profilo':<26}{amp:>9.2f} punti"
              f"   (scarto max dalla media {dev:+.2f})")

    # --------------------------------------- il confronto diretto col giro 73
    print(f"\n   IL CONFRONTO CHE DECIDE: 12-3 senza ritardo contro 12-2 "
          f"ritardato di {RITARDO_GIRO73} giorni")
    print("   " + "-" * 92)
    nb20, tb20 = simula(ind_g, Wew, RITARDO_GIRO73)
    bench20 = irr(nb20, tb20)
    confronto = []
    for top in (5, 10):
        net, turn = simula(ind_g, pesi_top(momk[2], top), RITARDO_GIRO73)
        r20 = irr(net, turn)
        m20 = r20["irr_ref"] - bench20["irr_ref"]
        m03 = [x["margine"] for x in righe if x["top"] == top and x["k"] == 3][0]
        m02 = [x["margine"] for x in righe if x["top"] == top and x["k"] == 2][0]
        confronto.append(dict(top=top, m20=m20, m03=m03, m02=m02))
        print(f"   top-{top:<3} 12-2 a 0g {m02:>+7.2f}   "
              f"12-2 a {RITARDO_GIRO73}g {m20:>+7.2f}   "
              f"12-3 a 0g {m03:>+7.2f}   |12-3 − 12-2@{RITARDO_GIRO73}g| "
              f"= {abs(m03 - m20):>5.2f}")
        righe.append(dict(top=top, k=2, ritardo=RITARDO_GIRO73,
                          irr=r20["irr_ref"], margine=m20, rot=r20["rot"],
                          aliq=r20["rate_ref"], net=r20["net"]))

    # -------------------------------------------------------------- DSR
    fam = [r for r in righe if r["ritardo"] == 0]
    srs = []
    for r in fam:
        e = r["net"] - rf.reindex(r["net"].index).fillna(0.0)
        srs.append(float(e.mean() / e.std(ddof=1)))
    var_fam = float(np.var(srs, ddof=1))
    n_cum = lab.n_trials_so_far()
    migl = max(fam, key=lambda r: r["margine"])
    d = lab.deflated_sharpe(migl["net"], n_cum, var_sr=var_fam, rf=rf)
    dsr = float(d["dsr"]) if np.isfinite(d["dsr"]) else 0.0
    print(f"\n   cella migliore del profilo: top-{migl['top']} k={migl['k']} "
          f"a {migl['margine']:+.2f}   DSR {dsr:.4f} su N={n_cum} "
          f"(var_sr {var_fam:.6f} sulla famiglia del giro)")

    # ---------------------------------------------------------- verdetto
    print(f"\n{'=' * 100}\n   VERDETTO\n{'=' * 100}")
    print(f"   Predizione: il 12-3 senza ritardo NON riproduce il +{BERSAGLIO_73:.2f},"
          f" resta SOTTO ZERO, entro 0,5 dal 12-2,")
    print(f"   e il profilo in k e' piatto entro +-0,6 punti.")
    print(f"   FALSIFICATA se il 12-3 e' POSITIVO e entro {TOLL_COINCIDENZA:.2f} "
          f"dal +{BERSAGLIO_73:.2f}, OPPURE se l'ampiezza in k supera "
          f"{AMPIEZZA_FALS:.2f}.\n")

    fals_a = fals_b = False
    for c in confronto:
        vicino = abs(c["m03"] - BERSAGLIO_73) <= TOLL_COINCIDENZA
        pos = c["m03"] > 0
        if pos and vicino:
            fals_a = True
        print(f"   top-{c['top']:<3} 12-3 = {c['m03']:+.2f}   positivo: "
              f"{'SI' if pos else 'no':<3}   entro {TOLL_COINCIDENZA:.2f} dal "
              f"+{BERSAGLIO_73:.2f}: {'SI' if vicino else 'no':<3}   "
              f"→ ramo (a) {'SCATTA' if pos and vicino else 'non scatta'}")
        print(f"          scarto dal 12-2 senza ritardo: "
              f"{abs(c['m03'] - c['m02']):.2f}  (previsto entro 0,50)")

    for top in (5, 10):
        m = [x["margine"] for x in righe if x["top"] == top and x["ritardo"] == 0]
        amp = max(m) - min(m)
        dev = max(abs(v - float(np.mean(m))) for v in m)
        if amp > AMPIEZZA_FALS:
            fals_b = True
        print(f"   top-{top:<3} ampiezza in k = {amp:.2f}  "
              f"(soglia {AMPIEZZA_FALS:.2f} → ramo (b) "
              f"{'SCATTA' if amp > AMPIEZZA_FALS else 'non scatta'})"
              f"   scarto max dalla media {dev:.2f} (previsto entro 0,60)")

    fals = fals_a or fals_b
    print(f"\n   -> ipotesi L4 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      ramo (a) il meccanismo dello skip e' reale : "
          f"{'SCATTATO' if fals_a else 'non scattato'}")
    print(f"      ramo (b) lo skip e' un grado di liberta'   : "
          f"{'SCATTATO' if fals_b else 'non scattato'}")

    df = pd.DataFrame([{k: v for k, v in r.items() if k != "net"} for r in righe])
    df.to_csv(OUT / "round76_l4.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="L4 skip contro ritardo",
                         config=f"top-{r['top']} 12-{r['k']} +{r['ritardo']}g",
                         window=f"{ind_g.index[0].year}-{FINE}", sharpe="",
                         irr=r["irr"], bh_irr=r["irr"] - r["margine"],
                         excess=r["margine"], n_obs=len(ind_g),
                         note=f"rot={r['rot']:.3f},aliq={r['aliq']}")
                    for r in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

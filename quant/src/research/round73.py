"""Giro 73 — L1: il costo di essere in ritardo, misurato in giorni.

VOCE DELLA CODA, predizione verbatim (committata prima di eseguire):

L1 — Il costo di essere in ritardo, misurato in giorni
  Ogni segnale del progetto e' applicato il mese successivo, come se il
  ribilanciamento avvenisse a mezzanotte del 31. Il giro 05 aveva misurato il
  degrado con ritardi di UNO e DUE MESI (+2,93 -> +2,35 -> +2,16), ma mai sui
  GIORNI, che e' la scala a cui il ritardo esiste davvero.
  PREDIZIONE: il margine DECADE IN MODO MONOTONO col ritardo, di 0,2-0,8 punti
  ogni 20 giorni — cioe' in linea con i -0,58 al mese del giro 05. A UN SOLO
  GIORNO la perdita sta SOTTO 0,1 PUNTI, quindi il risultato del progetto non
  dipende dal ribilanciamento a mezzanotte. E NESSUN RITARDO RENDE IL MARGINE
  POSITIVO: il momentum non diventa buono aspettando.
  FALSIFICATA SE: il margine NON E' MONOTONO decrescente nel ritardo, OPPURE un
  ritardo di 5 giorni o piu' MIGLIORA il margine — nel qual caso il segnale sta
  catturando reversione di brevissimo periodo e non momentum, e va riletto il
  gruppo A per intero.

COME SI IMPLEMENTA UN RITARDO IN GIORNI, dichiarato prima di calcolare.

Il segnale resta quello mensile: momentum 12-2 calcolato sui rendimenti mensili
fino al mese t-1. Cambia SOLO quando lo si esegue. Con ritardo k, i pesi nuovi
entrano in vigore al k-esimo giorno di borsa DOPO la fine del mese; fino a quel
giorno si resta con i pesi vecchi, che nel frattempo derivano coi prezzi.

  k = 0   ribilanciamento a mezzanotte del 31, la convenzione di tutto il progetto
  k = 1   si ordina il primo giorno utile
  k = 20  circa un mese, il ritardo che il giro 05 aveva gia' misurato

La rotazione e' quella VERA (giri 63-68): |peso target - peso derivato| / 2, e va
calcolata sui pesi GIORNALIERI, altrimenti il ritardo non si vede nei costi.

Il portafoglio si valuta su base giornaliera e i rendimenti si aggregano al mese
per il motore fiscale, che lavora a 12 periodi l'anno come nel resto del
progetto. La rotazione mensile e' la somma di quella giornaliera.

BENCHMARK: equal-weight annuale con la rotazione vera, il piu' severo fra quelli
implementabili (giri 60-64, cancello G1 della regola del giro 72). Lo stesso
ritardo si applica anche a lui: un investitore in ritardo lo e' su tutto.

FINESTRA 1969-2009. L1 valuta candidati: l'holdout resta sigillato.

Nessuna selezione fra i ritardi: sono una griglia dichiarata, non una scelta.
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

ROUND = 73
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
RITARDI = (0, 1, 5, 10, 20)


def date_ribilancio(idx_g, ritardo):
    """Per ogni mese, il giorno di borsa in cui i pesi nuovi entrano in vigore."""
    s = pd.Series(range(len(idx_g)), index=idx_g)
    fine_mese = s.groupby([idx_g.year, idx_g.month]).max()
    out = {}
    for pos in fine_mese.values:
        j = pos + ritardo
        if j < len(idx_g):
            out[idx_g[j]] = idx_g[pos]      # giorno di esecuzione -> mese del segnale
    return out


def simula(rets_g, target_mensile, ritardo, cost=C.COST_ROUND_TRIP):
    """Portafoglio giornaliero con i pesi che entrano in vigore in ritardo."""
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

    print(f"{'=' * 100}\nL1 — quanto costa ordinare qualche giorno dopo\n"
          f"{'=' * 100}")
    print(f"   49 settori giornalieri, {ind_g.index[0].date()} → "
          f"{ind_g.index[-1].date()} ({len(ind_g)} giorni di borsa).")
    print(f"   **Holdout 2010-2026 non toccato.** Ritardi: "
          f"{', '.join(str(k) for k in RITARDI)} giorni di borsa.\n")

    mom12 = (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(2)
    strategie = [("momentum 12-2 top-5 mensile", pesi_top(mom12, 5)),
                 ("momentum 12-2 top-10 mensile", pesi_top(mom12, 10))]
    Wew = pesi_ew_annuale(ind_m)

    def irr(net, turn):
        i = net.dropna().index
        r = B.eval_stream("x", net.reindex(i), rf.reindex(i).fillna(0.0),
                          turn.reindex(i))
        r["rot"] = float(turn.reindex(i).sum()) / (len(i) / 12)
        return r

    bench = {}
    for k in RITARDI:
        nb, tb = simula(ind_g, Wew, k)
        bench[k] = irr(nb, tb)

    print(f"   {'benchmark equal-weight annuale':<34}"
          + "".join(f"{k:>10}g" for k in RITARDI))
    print("   " + "-" * 89)
    print(f"   {'IRR netta':<34}"
          + "".join(f"{bench[k]['irr_ref']:>10.2f}%" for k in RITARDI))
    print(f"   {'rotazione':<34}"
          + "".join(f"{bench[k]['rot']:>10.3f}x" for k in RITARDI))

    righe = []
    for nome, W in strategie:
        print(f"\n   {nome:<34}" + "".join(f"{k:>10}g" for k in RITARDI))
        print("   " + "-" * 89)
        irrs, margini, rots = [], [], []
        for k in RITARDI:
            net, turn = simula(ind_g, W, k)
            r = irr(net, turn)
            irrs.append(r["irr_ref"])
            margini.append(r["irr_ref"] - bench[k]["irr_ref"])
            rots.append(r["rot"])
            righe.append(dict(strategia=nome, ritardo=k, irr=r["irr_ref"],
                              margine=r["irr_ref"] - bench[k]["irr_ref"],
                              rot=r["rot"], aliq=r["rate_ref"]))
        print(f"   {'IRR netta':<34}" + "".join(f"{v:>10.2f}%" for v in irrs))
        print(f"   {'margine vs EW annuale':<34}"
              + "".join(f"{v:>+10.2f} " for v in margini))
        print(f"   {'rotazione':<34}" + "".join(f"{v:>10.3f}x" for v in rots))

    # ------------------------------------------------------------- verdetto
    print(f"\n{'=' * 100}\n   VERDETTO\n{'=' * 100}")
    print(f"   Predizione: margine monotono decrescente, −0,2/−0,8 ogni 20 "
          f"giorni, perdita a 1 giorno sotto 0,1,")
    print(f"   e nessun ritardo rende il margine positivo.")
    print(f"   FALSIFICATA se il margine non e' monotono, OPPURE un ritardo "
          f">= 5 giorni MIGLIORA il margine.\n")
    fals = False
    for nome, _ in strategie:
        m = [r["margine"] for r in righe if r["strategia"] == nome]
        mono = all(m[i] >= m[i + 1] for i in range(len(m) - 1))
        d20 = m[0] - m[-1]
        d1 = m[0] - m[1]
        migliora5 = any(m[i] > m[0] for i, k in enumerate(RITARDI) if k >= 5)
        positivo = any(v > 0 for v in m)
        fals = fals or (not mono) or migliora5
        print(f"   {nome}")
        print(f"     margine da {m[0]:+.2f} (0g) a {m[-1]:+.2f} (20g)"
              f"   → decadimento {d20:+.2f} punti in 20 giorni")
        print(f"     perdita a 1 giorno solo   : {d1:+.3f} punti"
              f"   (previsto sotto 0,1)")
        print(f"     monotono decrescente      : {'SI' if mono else 'NO'}")
        print(f"     un ritardo >=5g migliora  : {'SI' if migliora5 else 'no'}")
        print(f"     qualche ritardo lo rende positivo: "
              f"{'SI' if positivo else 'no'}")

    print(f"\n   -> ipotesi L1 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    tutti = {}
    for nome, _ in strategie:
        m = [r["margine"] for r in righe if r["strategia"] == nome]
        tutti[nome] = (m[0] - m[-1], m[0] - m[1], all(v <= 0 for v in m))
    print(f"      clausola 'decadimento 0,2-0,8 su 20 giorni': "
          + ", ".join(f"{n.split()[-2]} {'centrata' if 0.2 <= v[0] <= 0.8 else 'SBAGLIATA'}"
                      for n, v in tutti.items()))
    print(f"      clausola 'a 1 giorno sotto 0,1': "
          + ", ".join(f"{n.split()[-2]} {'centrata' if abs(v[1]) < 0.1 else 'SBAGLIATA'}"
                      for n, v in tutti.items()))
    print(f"      clausola 'nessun ritardo lo rende positivo': "
          + ", ".join(f"{n.split()[-2]} {'centrata' if v[2] else 'SBAGLIATA'}"
                      for n, v in tutti.items()))

    print(f"\n   Confronto con il giro 05, che misurava il ritardo in MESI:")
    print(f"     +2,93 → +2,35 (1 mese) → +2,16 (2 mesi), cioe' −0,58 il primo mese")
    for nome, _ in strategie:
        m = [r["margine"] for r in righe if r["strategia"] == nome]
        print(f"     {nome}: −{m[0] - m[-1]:.2f} su 20 giorni di borsa")

    pd.DataFrame(righe).to_csv(OUT / "round73_l1.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="L1 ritardo in giorni",
                         config=f"{r['strategia']} +{r['ritardo']}g",
                         window=f"{ind_g.index[0].year}-{FINE}", sharpe="",
                         irr=r["irr"], bh_irr=r["irr"] - r["margine"],
                         excess=r["margine"], n_obs=len(ind_g),
                         note=f"rot={r['rot']:.3f}") for r in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

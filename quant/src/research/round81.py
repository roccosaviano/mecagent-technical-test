"""Giro 81 — O3: le finestre sovrapposte non sono prove indipendenti.

VOCE DELLA CODA, verbatim (committata al giro 78):

O3 — Le finestre sovrapposte non sono prove indipendenti
  G3 chiede l'extra positivo in >= 2/3 delle finestre decennali MOBILI. Nel train
  il candidato fa 93,1% (27 su 29), nell'holdout 37,5%. Ma le ventinove finestre
  del train condividono in media l'85,5% dei dati (misurato al giro 43 su D1, e mai
  applicato ai cancelli): "ventisette successi su ventinove" e' lo stesso pezzo di
  storia contato ventisette volte.
  Da misurare: rifare G3 sui dodici candidati del giro 72 e sul 12-3 top-5 con
  finestre decennali DISGIUNTE (1970-79, 1980-89, 1990-99, 2000-09: quattro prove
  indipendenti) e con un BOOTSTRAP A BLOCCHI che tenga conto della sovrapposizione,
  confrontando la quota di vittorie e il suo intervallo di confidenza con quelli
  delle finestre mobili.
  PREDIZIONE: con finestre disgiunte la quota del 12-3 top-5 SCENDE SOTTO I 2/3,
  cioe' G3 SAREBBE FALLITO IN CAMPIONE se fosse stato misurato su prove
  indipendenti; e l'intervallo di confidenza della quota su finestre mobili e'
  ALMENO TRE VOLTE PIU' LARGO di quanto la numerosita' apparente (29) suggerisca.
  FALSIFICATA SE: la quota su finestre disgiunte resta SOPRA i 2/3 — nel qual caso
  la sovrapposizione non era il problema e il crollo dell'holdout va attribuito a
  un cambio di regime, non a un cancello mal costruito.

===================== DUE SCELTE DICHIARATE PRIMA DI ESEGUIRE =====================

1. OGNI CANDIDATO NEL MOTORE IN CUI G3 LO AVEVA MISURATO. I dodici del giro 72
   furono misurati col motore MENSILE, il 12-3 top-5 col motore GIORNALIERO al
   giro 77 (ed e' da li' che viene il 93,1%). Li riproduco ciascuno nel proprio
   motore: la voce confronta due SCHEMI DI FINESTRE, non due motori, e cambiare
   motore introdurrebbe 1,43 punti di differenza che non c'entrano nulla (giro 76).

2. IL BOOTSTRAP. Ricampiono a blocchi di 120 mesi — la lunghezza della finestra
   decennale, che e' la scala della dipendenza che voglio conservare — la COPPIA
   (rendimento netto del candidato, rendimento netto del benchmark) insieme alla
   rotazione, cosi' l'accoppiamento fra le due gambe resta intatto. Su ogni
   percorso sintetico ricalcolo la quota di vittorie con le finestre mobili, e da
   li' l'intervallo di confidenza. Lo confronto con l'intervallo di Wilson
   costruito sulla numerosita' APPARENTE n=29, che e' quello che uno userebbe se
   credesse che le ventinove finestre siano ventinove prove.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import dataio
from research import lab, bench as B
from research.round72 import valuta, pesi_annuali, pesi_mensili
from research.round76 import simula, pesi_top

ROUND = 81
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
LUNG = 10
G3_QUOTA = 2.0 / 3.0
DISGIUNTE = [(1970, 1979), (1980, 1989), (1990, 1999), (2000, 2009)]
NBOOT = 400
BLOCCO = 120
SEME = 20260730


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


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
    rf_m = rf.reindex(ind_m.index).fillna(0.0)
    y0, y1 = int(ind_m.index[0].year), FINE

    print(f"{'=' * 104}\nO3 — le finestre sovrapposte non sono prove indipendenti"
          f"\n{'=' * 104}")
    print(f"   Train {y0}-{y1}. Finestre disgiunte: "
          f"{', '.join(f'{a}-{b}' for a, b in DISGIUNTE)}.\n")

    def irr_fin(net, turn, a, b):
        i = net.index[(net.index.year >= a) & (net.index.year <= b)]
        s = net.reindex(i).dropna()
        if len(s) < 24:
            return None
        return B.eval_stream("x", s, rf.reindex(s.index).fillna(0.0),
                             turn.reindex(s.index))["irr_ref"]

    def quote(net_c, turn_c, net_b, turn_b):
        """(quota mobile, n mobile, quota disgiunta, n disgiunta, extra mobili)."""
        mob = []
        for y in range(y0 + 3, y1 - LUNG + 2):
            x = irr_fin(net_c, turn_c, y, y + LUNG - 1)
            q = irr_fin(net_b, turn_b, y, y + LUNG - 1)
            if x is not None and q is not None:
                mob.append(x - q)
        dis = []
        for a, b in DISGIUNTE:
            x = irr_fin(net_c, turn_c, a, b)
            q = irr_fin(net_b, turn_b, a, b)
            if x is not None and q is not None:
                dis.append(x - q)
        return (float(np.mean(np.array(mob) > 0)), len(mob),
                float(np.mean(np.array(dis) > 0)), len(dis),
                np.array(mob), np.array(dis))

    # ================================================ A1: il 12-3 top-5 (daily)
    print(f"   {'=' * 98}\n   A1 — il candidato che ha passato i cancelli "
          f"(motore giornaliero)\n   {'=' * 98}")
    score = (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(3)
    net_c, turn_c = simula(ind_g, pesi_top(score, 5), 0)
    Wew = pd.DataFrame(0.0, index=ind_m.index, columns=ind_m.columns)
    Wew.loc[Wew.index.month == 10] = 1.0 / ind_m.shape[1]     # calendario mediano
    net_b, turn_b = simula(ind_g, Wew, 0)
    qm, nm, qd, nd, ex_m, ex_d = quote(net_c, turn_c, net_b, turn_b)
    print(f"   {'schema':<24}{'n':>5}{'quota':>10}{'soglia 2/3':>13}{'esito':>12}")
    print("   " + "-" * 66)
    print(f"   {'finestre MOBILI':<24}{nm:>5}{qm:>9.1%}{G3_QUOTA:>12.1%}"
          f"{('PASSA' if qm >= G3_QUOTA else 'FALLISCE'):>12}")
    print(f"   {'finestre DISGIUNTE':<24}{nd:>5}{qd:>9.1%}{G3_QUOTA:>12.1%}"
          f"{('PASSA' if qd >= G3_QUOTA else 'FALLISCE'):>12}")
    print(f"\n   i quattro decenni disgiunti: "
          + "   ".join(f"{a}-{str(b)[2:]} {v:+.2f}"
                       for (a, b), v in zip(DISGIUNTE, ex_d)))

    # ================================================ A2: i dodici del giro 72
    print(f"\n   {'=' * 98}\n   A2 — i dodici candidati del giro 72 "
          f"(motore mensile, come allora)\n   {'=' * 98}")
    mom12 = (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(2)
    mom6 = (1 + ind_m).rolling(5).apply(np.prod, raw=True).shift(2)
    vol36 = ind_m.rolling(36).std().shift(1)
    mix = mom12.rank(axis=1, pct=True) + (-vol36).rank(axis=1, pct=True)
    cands = [("momentum 12-2 top-5 annuale", True, mom12, 5),
             ("momentum 12-2 top-10 annuale", True, mom12, 10),
             ("momentum 12-2 top-25 annuale", True, mom12, 25),
             ("momentum 6-2 top-10 annuale", True, mom6, 10),
             ("low-vol 36m top-10 annuale", True, -vol36, 10),
             ("low-vol 36m top-25 annuale", True, -vol36, 25),
             ("punteggio misto top-10 annuale", True, mix, 10),
             ("momentum 12-2 top-5 mensile", False, mom12, 5),
             ("H5 momentum top-10 mensile", False, mom12, 10),
             ("momentum 12-2 top-25 mensile", False, mom12, 25),
             ("H4 low-vol 36m top-10 mensile", False, -vol36, 10),
             ("C1 punteggio misto top-10 mensile", False, mix, 10)]
    bench_m = {m: valuta(ind_m, pesi_annuali(ind_m, m), rf_m) for m in range(1, 13)}
    from research.round72 import rot_vera
    turn_bm = {m: rot_vera(ind_m, pesi_annuali(ind_m, m)) for m in range(1, 13)}

    print(f"   {'candidato':<36}{'mobili':>10}{'disgiunte':>12}"
          f"{'mobili':>9}{'disg.':>8}")
    print("   " + "-" * 78)
    ribalta = 0
    righe = []
    for nome, ann, sc, top in cands:
        if ann:
            mesi = {m: valuta(ind_m, pesi_annuali(ind_m, m, sc, top), rf_m)
                    for m in range(1, 13)}
            marg = {m: mesi[m]["irr_ref"] - bench_m[m]["irr_ref"] for m in mesi}
            med = float(np.median(list(marg.values())))
            mm = min(marg, key=lambda m: abs(marg[m] - med))
            W = pesi_annuali(ind_m, mm, sc, top)
        else:
            mm = 1
            W = pesi_mensili(sc, top)
        tu = rot_vera(ind_m, W)
        ne = ((W * ind_m).sum(axis=1) - tu * 0.0015).dropna()
        nb = bench_m[mm]["net"]
        a, na, b, nb_, exm, exd = quote(ne, tu, nb, turn_bm[mm])
        pa, pb = a >= G3_QUOTA, b >= G3_QUOTA
        if pa != pb:
            ribalta += 1
        righe.append((nome, a, b, pa, pb))
        print(f"   {nome:<36}{a:>9.1%}{b:>12.1%}"
              f"{('PASSA' if pa else 'no'):>9}{('PASSA' if pb else 'no'):>8}")
    print(f"\n   candidati il cui verdetto G3 CAMBIA passando a finestre "
          f"disgiunte: **{ribalta}/12**")
    print(f"   passano G3 con le mobili: {sum(1 for r in righe if r[3])}/12   "
          f"con le disgiunte: {sum(1 for r in righe if r[4])}/12")

    # ================================================ B: bootstrap a blocchi
    print(f"\n   {'=' * 98}\n   B — l'intervallo di confidenza della quota "
          f"({NBOOT} ricampionamenti a blocchi di {BLOCCO} mesi)\n   {'=' * 98}")
    key = net_c.index
    nc = net_c.reindex(key).fillna(0.0).to_numpy()
    tc = turn_c.reindex(key).fillna(0.0).to_numpy()
    nbv = net_b.reindex(key).fillna(0.0).to_numpy()
    tbv = turn_b.reindex(key).fillna(0.0).to_numpy()
    rfv = rf.reindex(key).fillna(0.0).to_numpy()
    T = len(key)
    nblocchi = T // BLOCCO
    rng = np.random.default_rng(SEME)

    def quota_su(nc_, tc_, nb_, tb_, rf_, idx):
        anni = len(idx) // 12
        v = []
        for s in range(0, anni - LUNG + 1):
            sl = slice(s * 12, s * 12 + LUNG * 12)
            if sl.stop > len(idx):
                break
            i = idx[sl]
            x = B.eval_stream("x", pd.Series(nc_[sl], index=i),
                              pd.Series(rf_[sl], index=i),
                              pd.Series(tc_[sl], index=i))["irr_ref"]
            q = B.eval_stream("x", pd.Series(nb_[sl], index=i),
                              pd.Series(rf_[sl], index=i),
                              pd.Series(tb_[sl], index=i))["irr_ref"]
            v.append(x - q)
        return float(np.mean(np.array(v) > 0)), len(v)

    quote_boot = []
    for _ in range(NBOOT):
        pos = rng.integers(0, T - BLOCCO + 1, size=nblocchi)
        sel = np.concatenate([np.arange(p, p + BLOCCO) for p in pos])
        idx = key[:len(sel)]
        q, _ = quota_su(nc[sel], tc[sel], nbv[sel], tbv[sel], rfv[sel], idx)
        quote_boot.append(q)
    quote_boot = np.array(quote_boot)
    lo_b, hi_b = np.percentile(quote_boot, [2.5, 97.5])
    lo_w, hi_w = wilson(round(qm * nm), nm)
    larg_b, larg_w = hi_b - lo_b, hi_w - lo_w
    print(f"   {'intervallo':<40}{'basso':>10}{'alto':>10}{'larghezza':>12}")
    print("   " + "-" * 72)
    print(f"   {'Wilson 95% sulla numerosita apparente n=' + str(nm):<40}"
          f"{lo_w:>10.1%}{hi_w:>10.1%}{larg_w:>12.1%}")
    print(f"   {'bootstrap a blocchi 95%':<40}"
          f"{lo_b:>10.1%}{hi_b:>10.1%}{larg_b:>12.1%}")
    rapp = larg_b / larg_w if larg_w > 0 else np.inf
    print(f"\n   **rapporto fra le larghezze: {rapp:.2f}×**   "
          f"(previsto almeno 3)")
    print(f"   mediana della quota nei ricampionamenti: "
          f"{float(np.median(quote_boot)):.1%}   "
          f"(osservata {qm:.1%})")

    # ================================================ C: il tasso di falsi positivi
    print(f"\n   {'=' * 98}\n   C — quanto e' selettivo G3, sotto ipotesi nulla"
          f"\n   {'=' * 98}")
    k_mob = int(np.ceil(G3_QUOTA * nm))
    fp_mob = 1.0 - st.binom.cdf(k_mob - 1, nm, 0.5)
    k_dis = int(np.ceil(G3_QUOTA * len(DISGIUNTE)))
    fp_dis = 1.0 - st.binom.cdf(k_dis - 1, len(DISGIUNTE), 0.5)
    n_eff = float(np.median(quote_boot))
    print(f"   Una strategia che vince il 50% delle volte per puro caso, "
          f"quante probabilita' ha di passare G3?")
    print(f"   {'con ' + str(nm) + ' finestre MOBILI trattate come indipendenti':<56}"
          f"servono {k_mob:>2}/{nm:<3}  →  {fp_mob:>7.2%}")
    print(f"   {'con ' + str(len(DISGIUNTE)) + ' finestre DISGIUNTE (le prove vere)':<56}"
          f"servono {k_dis:>2}/{len(DISGIUNTE):<3}  →  {fp_dis:>7.2%}")
    print(f"   rapporto fra i due tassi di falsi positivi: "
          f"**{fp_dis / fp_mob:.0f}×**")

    # ------------------------------------------------------------- verdetto
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: con finestre disgiunte la quota del 12-3 top-5 SCENDE "
          f"SOTTO i 2/3 (G3 sarebbe")
    print(f"   fallito in campione), e l'intervallo di confidenza e' ALMENO TRE "
          f"VOLTE piu' largo del Wilson.")
    print(f"   FALSIFICATA se la quota disgiunta resta SOPRA i 2/3.\n")
    sotto = qd < G3_QUOTA
    tre = rapp >= 3.0
    print(f"   quota disgiunta sotto i 2/3 : {'SI' if sotto else 'NO'}"
          f"   ({qd:.1%} contro {G3_QUOTA:.1%}, {int(round(qd * nd))}/{nd})")
    print(f"   intervallo almeno 3× piu' largo: {'SI' if tre else 'NO'}"
          f"   ({rapp:.2f}×)")
    fals = not sotto
    print(f"\n   -> ipotesi O3 {'FALSIFICATA' if fals else 'CONFERMATA'}")

    lab.log_trials([dict(round=ROUND, hypothesis="O3 finestre disgiunte",
                         config=r[0], window=f"{y0}-{FINE}", sharpe="",
                         irr=r[1], bh_irr=r[2], excess=r[2] - r[1],
                         n_obs=len(ind_m),
                         note=f"mob={r[3]},dis={r[4]}") for r in righe]
                   + [dict(round=ROUND, hypothesis="O3 finestre disgiunte",
                           config="12-3 top-5 mensile (daily)",
                           window=f"{y0}-{FINE}", sharpe="", irr=qm, bh_irr=qd,
                           excess=qd - qm, n_obs=len(ind_g),
                           note=f"CI boot {larg_b:.3f} vs Wilson {larg_w:.3f}")])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

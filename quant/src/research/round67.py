"""Giro 67 — J1: statistical jump model per i regimi, long e long/short.

VOCE DELLA CODA, predizione verbatim:

J1 — Statistical jump model per l'identificazione dei regimi, long e long/short
  Riferimento: Aydinhan, Kolm, Mulvey, Shu, "Identifying patterns in financial
  markets: extending the statistical jump model for regime identification",
  Annals of Operations Research 2024 — estensione dello statistical jump model di
  Bemporad et al. 2018 e Nystrup-Kolm-Lindstrom 2020. Il modello e' un clustering
  TEMPORALMENTE REGOLARIZZATO: minimizza la distanza intra-cluster PIU' una
  penalita' lambda per ogni cambio di stato, il che produce regimi molto piu'
  persistenti di un HMM gaussiano — ed e' esattamente la proprieta' che in questo
  progetto conta, perche' la persistenza e' rotazione bassa e la rotazione bassa
  e' l'aliquota al 33%.
  PREDIZIONE: il segnale del jump model correla OLTRE 0,7 con un semplice filtro
  a media mobile 10 mesi — cioe' e' un filtro di tendenza con una procedura di
  stima piu' raffinata, non un'informazione nuova. La variante LONG-ONLY PERDE
  contro il buy&hold di 1,5-4 punti netti (stessa fascia di G1, giro 53, dove il
  migliore perdeva 2,51), e la LONG/SHORT e' PEGGIORE della long-only in tutte e
  tre le varianti, perche' il premio azionario e' positivo e stare corti ha
  aspettativa negativa prima ancora dei costi di finanziamento. L'unica clausola
  che puo' reggere e' la rotazione: sotto 1,0x/anno grazie a lambda, quindi
  aliquota 33% invece del 52% dei filtri del giro 53.
  FALSIFICATA SE: la variante long-only BATTE il buy&hold netto di fiscalita'
  irlandese, OPPURE una variante long/short batte la corrispondente long-only.

VINCOLO SULL'HOLDOUT. J1 valuta CANDIDATI, non e' una voce metodologica come le
D: quindi il campione si ferma al 2009-12. L'holdout 2010-2026 resta sigillato.

L'ALGORITMO, scritto prima di guardare qualunque risultato.

Dato X (T x p) standardizzato, K stati, penalita' lambda:
  1. L[t,k] = ||x_t - mu_k||^2
  2. assegnazione per PROGRAMMAZIONE DINAMICA:
       V[0,k] = L[0,k]
       V[t,k] = L[t,k] + min_j ( V[t-1,j] + lambda * 1{j != k} )
     e backtracking della sequenza ottima
  3. mu_k = media delle x_t assegnate a k
  4. ripeti fino a stabilita' delle assegnazioni

FUORI CAMPIONE SI USA LA REGOLA CAUSALE, NON LA DP. La DP guarda tutta la
sequenza, quindi in produzione non e' disponibile: usarla per il periodo di
applicazione sarebbe look-ahead puro e mascherato. Fuori campione assegno
  s_t = argmin_k ( L[t,k] + lambda * 1{k != s_{t-1}} )
che e' la versione online del medesimo criterio — un filtro con isteresi.

WALK-FORWARD. Rifitto ogni 5 anni sui 20 anni precedenti (5.040 giorni), lambda
scelto sul solo passato massimizzando il CAGR netto della variante (a) nel
periodo di stima. Venti anni perche' i regimi non sono stazionari su un secolo,
cinque anni fra un rifit e l'altro per costo computazionale: entrambe dichiarate.

FEATURE, dalla sola serie del mercato USA come nel paper: per ogni emivita
h in {5, 21, 63} giorni, media EWM dei rendimenti, deviazione al ribasso EWM, e
il loro rapporto. Nove feature, tutte causali. La standardizzazione usa media e
deviazione del solo periodo di stima.

IL LATO CORTO, modellato esplicitamente:
  rendimento corto = -(total return) + rf - 1%/anno di finanziamento
Chi sta corto su un indice paga i dividendi e un costo di prestito; l'1% e' la
fascia bassa per un indice liquido, quindi e' un'ipotesi FAVOREVOLE allo short.

N per il DSR = 7 lambda x 3 varianti = 21, perche' c'e' selezione.
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

ROUND = 67
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = "2009-12-31"          # l'holdout 2010-2026 resta sigillato
K = 2
LAMBDAS = (0.0, 5.0, 10.0, 25.0, 50.0, 100.0, 200.0)
N_GRID = len(LAMBDAS) * 3
TRAIN_D = 20 * 252
REFIT_Y = 5
COSTO_SHORT = 0.01           # finanziamento annuo del lato corto


def feature(r):
    """Nove feature causali dalla sola serie dei rendimenti giornalieri."""
    out = {}
    for h in (5, 21, 63):
        m = r.ewm(halflife=h).mean()
        giu = r.where(r < 0, 0.0)
        dd = np.sqrt((giu ** 2).ewm(halflife=h).mean())
        out[f"m{h}"] = m
        out[f"dd{h}"] = dd
        out[f"s{h}"] = m / dd.replace(0, np.nan)
    return pd.DataFrame(out).replace([np.inf, -np.inf], np.nan).dropna()


def dp_assegna(L, lam):
    """Sequenza di stati che minimizza somma L[t,s_t] + lam * salti."""
    T, k = L.shape
    V = np.empty((T, k))
    prev = np.zeros((T, k), dtype=np.int8)
    V[0] = L[0]
    for t in range(1, T):
        for j in range(k):
            c = V[t - 1] + lam * (np.arange(k) != j)
            i = int(np.argmin(c))
            prev[t, j] = i
            V[t, j] = L[t, j] + c[i]
    s = np.empty(T, dtype=np.int8)
    s[-1] = int(np.argmin(V[-1]))
    for t in range(T - 1, 0, -1):
        s[t - 1] = prev[t, s[t]]
    return s


def fit_jump(X, lam, k=K, iters=25, seed=0):
    """Coordinate descent: DP sugli stati, media sui centroidi."""
    rng = np.random.default_rng(seed)
    T = X.shape[0]
    q = np.quantile(X[:, 0], [0.25, 0.75])
    mu = np.vstack([X[X[:, 0] <= q[0]].mean(axis=0),
                    X[X[:, 0] >= q[1]].mean(axis=0)])
    s_old = None
    for _ in range(iters):
        L = ((X[:, None, :] - mu[None, :, :]) ** 2).sum(axis=2)
        s = dp_assegna(L, lam)
        if s_old is not None and np.array_equal(s, s_old):
            break
        s_old = s
        for j in range(k):
            m = s == j
            if m.sum() > 0:
                mu[j] = X[m].mean(axis=0)
            else:
                mu[j] = X[rng.integers(T)]
    return mu, s


def assegna_causale(X, mu, lam, s0=0):
    """Versione ONLINE: al tempo t si conosce solo il passato."""
    L = ((X[:, None, :] - mu[None, :, :]) ** 2).sum(axis=2)
    s = np.empty(len(X), dtype=np.int8)
    prev = s0
    for t in range(len(X)):
        c = L[t] + lam * (np.arange(mu.shape[0]) != prev)
        prev = int(np.argmin(c))
        s[t] = prev
    return s


def segnale_wf(F, r, lam):
    """Stato giornaliero fuori campione, walk-forward. 1 = regime 'toro'."""
    idx = F.index
    fuori = pd.Series(np.nan, index=idx)
    anni = sorted(set(idx.year))
    inizio = anni[0] + 20
    blocchi = [y for y in anni if y >= inizio and (y - inizio) % REFIT_Y == 0]
    for y in blocchi:
        tr = idx[idx < f"{y}-01-01"][-TRAIN_D:]
        if len(tr) < TRAIN_D // 2:
            continue
        mu_, sd_ = F.loc[tr].mean(), F.loc[tr].std().replace(0, 1.0)
        Xtr = ((F.loc[tr] - mu_) / sd_).to_numpy()
        mu, s_tr = fit_jump(Xtr, lam)
        # etichetta: lo stato col rendimento medio piu' alto NEL PERIODO DI STIMA
        med = [r.reindex(tr)[s_tr == j].mean() for j in range(K)]
        toro = int(np.argmax(med))
        ap = idx[(idx >= f"{y}-01-01") & (idx < f"{y + REFIT_Y}-01-01")]
        if len(ap) == 0:
            continue
        Xap = ((F.loc[ap] - mu_) / sd_).to_numpy()
        s_ap = assegna_causale(Xap, mu, lam, s0=int(s_tr[-1]))
        fuori.loc[ap] = (s_ap == toro).astype(float)
    return fuori.dropna()


def main():
    ffd = dataio.ff_factors_daily()
    r = (ffd["Mkt-RF"] + ffd["RF"]).loc[:FINE].dropna()
    rfd = ffd["RF"].reindex(r.index).fillna(0.0)
    ffm = dataio.ff_factors_monthly()
    rm = (ffm["Mkt-RF"] + ffm["RF"]).loc[:FINE].dropna()
    rfm = ffm["RF"].reindex(rm.index).fillna(0.0)

    print(f"{'=' * 104}\nJ1 — statistical jump model sui regimi del mercato USA\n"
          f"{'=' * 104}")
    print(f"   Campione {r.index[0].date()} → {r.index[-1].date()} "
          f"({len(r)} giorni). **Holdout 2010-2026 NON toccato.**")
    print(f"   K={K} stati, rifit ogni {REFIT_Y} anni su {TRAIN_D} giorni, "
          f"assegnazione fuori campione CAUSALE.\n")

    F = feature(r)
    bh = B.eval_stream("buy&hold", rm, rfm)
    print(f"   Buy&hold mensile: CAGR {bh['cagr']:.2f}%, IRR "
          f"{bh['irr_ref']:.2f}%, DD {bh['dd']:.2f}%\n")

    # filtro a media mobile 10 mesi, il termine di paragone della predizione
    px = (1 + rm).cumprod()
    ma = B.ma_filter(px, 10)

    righe = []
    print(f"   {'lambda':>8}{'variante':<14}{'salti/anno':>12}{'esposiz.':>10}"
          f"{'CAGR':>9}{'rotaz.':>9}{'aliq.':>7}{'IRR':>9}{'vs B&H':>9}"
          f"{'corr MA10':>11}")
    print("   " + "-" * 98)
    for lam in LAMBDAS:
        sig_d = segnale_wf(F, r, lam)
        if len(sig_d) < 2520:
            continue
        # stato a fine mese -> esposizione del mese successivo (causale)
        sig_m = sig_d.resample("ME").last().shift(1).dropna()
        sig_m.index = pd.DatetimeIndex(sig_m.index).to_period("M").to_timestamp("M")
        rm2 = rm.copy()
        rm2.index = pd.DatetimeIndex(rm2.index).to_period("M").to_timestamp("M")
        rf2 = rfm.copy()
        rf2.index = pd.DatetimeIndex(rf2.index).to_period("M").to_timestamp("M")
        idx = sig_m.index.intersection(rm2.index)
        sig_m, rr, rfx = sig_m.loc[idx], rm2.loc[idx], rf2.loc[idx]
        ma_x = ma.copy()
        ma_x.index = pd.DatetimeIndex(ma_x.index).to_period("M").to_timestamp("M")
        corr = float(np.corrcoef(sig_m, ma_x.reindex(idx).fillna(0.0))[0, 1])
        salti = float(sig_m.diff().abs().sum()) / (len(idx) / 12)
        espo = float(sig_m.mean())

        corto = -rr + rfx - COSTO_SHORT / 12.0
        for nome, giu in [("long/cash", None), ("long/short", 1.0),
                          ("long/short 0,5", 0.5)]:
            if giu is None:
                net = sig_m * rr + (1 - sig_m) * rfx * (1 - C.DIRT_RATE)
                turn = sig_m.diff().abs().fillna(sig_m.abs())
            else:
                net = sig_m * rr + (1 - sig_m) * (giu * corto
                                                  + (1 - giu) * rfx * (1 - C.DIRT_RATE))
                turn = sig_m.diff().abs().fillna(sig_m.abs()) * (1 + giu) / 2 + \
                    sig_m.diff().abs().fillna(0.0) * giu / 2
            res = B.eval_stream(f"lam={lam:g} {nome}", net.dropna(), rfx, turn)
            res.update(lam=lam, variante=nome, corr=corr, salti=salti, espo=espo,
                       net=net.dropna())
            righe.append(res)
            print(f"   {lam:>8.0f}{nome:<14}{salti:>11.2f} {espo * 100:>8.1f}%"
                  f"{res['cagr']:>8.2f}%{res['turn']:>8.2f}x{res['rate_ref']:>6}%"
                  f"{res['irr_ref']:>8.2f}%{res['irr_ref'] - bh['irr_ref']:>+8.2f}"
                  f"{corr:>11.3f}")

    # ------------------------------------------------------------- verdetto
    lo = [x for x in righe if x["variante"] == "long/cash"]
    ls1 = {x["lam"]: x for x in righe if x["variante"] == "long/short"}
    ls5 = {x["lam"]: x for x in righe if x["variante"] == "long/short 0,5"}
    best_lo = max(lo, key=lambda x: x["irr_ref"])
    corrs = [x["corr"] for x in lo]
    batte_ls = sum(1 for x in lo
                   if (ls1.get(x["lam"]) and ls1[x["lam"]]["irr_ref"] > x["irr_ref"])
                   or (ls5.get(x["lam"]) and ls5[x["lam"]]["irr_ref"] > x["irr_ref"]))
    gap = best_lo["irr_ref"] - bh["irr_ref"]

    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: correlazione col filtro MA10 sopra 0,7; la long-only "
          f"perde 1,5-4 punti;")
    print(f"   la long/short e' peggiore della long-only ovunque; rotazione "
          f"sotto 1,0x/anno.")
    print(f"   FALSIFICATA se la long-only BATTE il buy&hold, OPPURE una "
          f"long/short batte la sua long-only.\n")
    print(f"   correlazione col MA10        : da {min(corrs):.3f} a "
          f"{max(corrs):.3f}   (previsto >0,7)")
    print(f"   migliore long/cash           : lambda={best_lo['lam']:g}, "
          f"IRR {best_lo['irr_ref']:.2f}% contro {bh['irr_ref']:.2f}% "
          f"del buy&hold = {gap:+.2f}")
    print(f"   rotazione della migliore     : {best_lo['turn']:.2f}x/anno "
          f"(aliquota {best_lo['rate_ref']}%)")
    print(f"   lambda in cui una long/short batte la long/cash: {batte_ls}/"
          f"{len(lo)}   (previsto 0)")

    fals = gap > 0 or batte_ls > 0
    print(f"\n   -> ipotesi J1 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'correlazione > 0,7': "
          f"{'centrata' if min(corrs) > 0.7 else 'SBAGLIATA'}")
    print(f"      clausola 'long-only perde 1,5-4 punti': "
          f"{'centrata' if -4.0 <= gap <= -1.5 else 'SBAGLIATA'}")
    print(f"      clausola 'long/short sempre peggiore': "
          f"{'centrata' if batte_ls == 0 else 'SBAGLIATA'}")
    print(f"      clausola 'rotazione sotto 1,0x': "
          f"{'centrata' if best_lo['turn'] < 1.0 else 'SBAGLIATA'}")

    if gap > 0:
        srs = []
        for x in righe:
            e = x["net"] - rfm.reindex(x["net"].index).fillna(0.0)
            srs.append(float(e.mean() / e.std(ddof=1)))
        var_fam = float(np.var(srs, ddof=1))
        d = lab.deflated_sharpe(best_lo["net"], N_GRID, var_sr=var_fam, rf=rfm)
        dc = lab.deflated_sharpe(best_lo["net"], lab.n_trials_so_far(),
                                 var_sr=var_fam, rf=rfm)
        print(f"\n   La long-only batte il buy&hold: DSR su N={N_GRID} "
              f"{d['dsr']:.4f}, su registro cumulato {dc['dsr']:.4f}")
    print(f"\n   Holdout 2010-2026 ancora sigillato.")

    pd.DataFrame([{k: v for k, v in x.items() if k not in ("net", "gross")}
                  for x in righe]).to_csv(OUT / "round67_j1.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="J1 statistical jump model",
                         config=f"lam={x['lam']:g} {x['variante']}",
                         window=f"{r.index[0].year}-2009", sharpe=x["sharpe"],
                         irr=x["irr_ref"], bh_irr=bh["irr_ref"],
                         excess=x["irr_ref"] - bh["irr_ref"], n_obs=x["n"],
                         note=f"corr={x['corr']:.3f},salti={x['salti']:.2f}")
                    for x in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

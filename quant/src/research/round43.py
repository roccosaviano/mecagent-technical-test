"""Giro 43 — D1 (dispersione per data di partenza) e D2 (bootstrap a blocchi).

DUE VOCI DELLA CODA, predizioni verbatim.

D1 — Quanto vale la finestra di partenza
  Rieseguire i tre candidati promossi facendo partire il campione in 20 anni
  diversi, per misurare la dispersione dovuta alla sola data di inizio.
  PREDIZIONE: la dispersione dell'extra-rendimento supera 3 punti, cioe' e' piu'
  grande dell'extra-rendimento stesso.
  FALSIFICATA SE: dispersione sotto 1 punto.

D2 — Bootstrap a blocchi dei candidati
  Rendimenti risimulati a blocchi per costruire la distribuzione nulla
  dell'extra-rendimento, invece di affidarsi al solo DSR.
  PREDIZIONE: il candidato migliore cade dentro il 95esimo percentile della
  distribuzione nulla.
  FALSIFICATA SE: sta oltre il 99esimo.

I TRE CANDIDATI, ricostruiti come nei giri 04, 05 e 11:
  H4  tilt low-volatility settoriale, lungo i 10 settori meno volatili a 36 mesi
  H5  momentum settoriale 12-2, lungo i 10 migliori
  C1  punteggio misto momentum + low-vol, meta' e meta'

Nessuno dei tre e' mai stato promosso davvero: il DSR li ha respinti tutti. D1 e
D2 misurano QUANTO era fragile quel che sembrava un margine, ed e' il motivo per
cui stanno in coda come voci metodologiche e non come strategie.

SUL BOOTSTRAP A BLOCCHI. Uso il bootstrap stazionario di Politis-Romano: la
lunghezza dei blocchi e' geometrica di media L, cosi' la serie risimulata resta
stazionaria invece di avere giunzioni fisse. Blocchi di 12 mesi, perche' e'
l'orizzonte del segnale di momentum: blocchi piu' corti distruggerebbero proprio
l'autocorrelazione che si vuole preservare sotto ipotesi nulla.
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

ROUND = 43
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 57
N_BOOT = 5000
BLOCK = 12
SEED = 20260727


def candidates(ind):
    """I tre candidati, ognuno restituisce (pesi detenuti nel periodo)."""
    out = {}
    mom = (1 + ind).rolling(11).apply(np.prod, raw=True).shift(2)
    vol = ind.rolling(36).std().shift(1)

    def topw(score, top=10, asc=False):
        rk = score.rank(axis=1, ascending=asc)
        W = (rk <= top).astype(float)
        return W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)

    out["H5 momentum settoriale"] = topw(mom)
    out["H4 tilt low-vol"] = topw(vol, asc=True)
    mix = mom.rank(axis=1, pct=True) + (-vol).rank(axis=1, pct=True)
    out["C1 punteggio misto"] = topw(mix)
    return out


def excess_irr(ind, W, bench, rf, start=None):
    i = ind.index if start is None else ind.index[ind.index.year >= start]
    if len(i) < 120:
        return None
    net, turn = B.wbacktest(ind.loc[i], W.loc[i].shift(1).fillna(0.0))
    net = net.dropna()
    r = B.eval_stream("x", net, rf.reindex(net.index).fillna(0.0),
                      turn.reindex(net.index))
    b = B.eval_stream("b", bench.reindex(net.index), rf.reindex(net.index).fillna(0.0))
    return r["irr_ref"] - b["irr"], r, b


def stationary_bootstrap(x, n_boot, mean_block, rng):
    """Politis-Romano: blocchi di lunghezza geometrica, serie circolare."""
    n = len(x)
    p = 1.0 / mean_block
    out = np.empty(n_boot)
    for b in range(n_boot):
        idx = np.empty(n, dtype=np.int64)
        i = rng.integers(n)
        for t in range(n):
            idx[t] = i
            if rng.random() < p:
                i = rng.integers(n)
            else:
                i = (i + 1) % n
        out[b] = x[idx].mean()
    return out


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    bench = ind.mean(axis=1)          # equal-weight dei 49, stesso universo
    cands = candidates(ind)

    # =============================================================== D1
    print(f"{'='*92}\nD1 — dispersione dovuta alla sola data di partenza\n{'='*92}")
    first = ind.index[0].year + 5
    starts = list(range(first, first + 20))
    print(f"   Benchmark: equal-weight dei 49 settori (stesso universo)")
    print(f"   {len(starts)} date di partenza, da {starts[0]} a {starts[-1]}, "
          f"fine sempre {ind.index[-1].year}\n")
    tab = {}
    for nm, W in cands.items():
        vals = []
        for y in starts:
            r = excess_irr(ind, W, bench, rf, y)
            if r:
                vals.append(r[0])
        tab[nm] = np.array(vals)
    print(f"   {'candidato':<26}{'media':>9}{'min':>9}{'max':>9}"
          f"{'ampiezza':>11}{'dev.std':>10}{'volte>0':>9}")
    print("   " + "-" * 73)
    for nm, v in tab.items():
        print(f"   {nm:<26}{v.mean():>8.2f}%{v.min():>8.2f}%{v.max():>8.2f}%"
              f"{v.max()-v.min():>10.2f}%{v.std(ddof=1):>9.2f}%"
              f"{int((v > 0).sum()):>6}/{len(v)}")
    disp = max(v.max() - v.min() for v in tab.values())
    sd = max(v.std(ddof=1) for v in tab.values())
    mean_ex = max(abs(v.mean()) for v in tab.values())
    print(f"\n   Predizione: la dispersione supera 3 punti ed e' piu' grande")
    print(f"   dell'extra-rendimento stesso. FALSIFICATA se sotto 1 punto.")
    print(f"   Ampiezza massima {disp:.2f} punti · deviazione standard massima "
          f"{sd:.2f} punti")
    print(f"   Extra-rendimento medio piu' grande in valore assoluto: "
          f"{mean_ex:.2f} punti")
    d1_fals = disp < 1.0
    verso = "PIU' GRANDE" if disp > mean_ex else "piu' piccola"
    print(f"   La dispersione e' {verso} dell'extra-rendimento")
    print(f"   -> ipotesi D1 {'FALSIFICATA' if d1_fals else 'CONFERMATA'}")

    # =============================================================== D2
    print(f"\n{'='*92}\nD2 — bootstrap a blocchi contro la distribuzione nulla\n"
          f"{'='*92}")
    rng = np.random.default_rng(SEED)
    best_nm = max(tab, key=lambda k: tab[k].mean())
    print(f"   Candidato migliore per extra-rendimento medio: {best_nm}")
    print(f"   Bootstrap stazionario di Politis-Romano, blocchi di media "
          f"{BLOCK} mesi, {N_BOOT} risimulazioni\n")
    rows = []
    for nm, W in cands.items():
        net, turn = B.wbacktest(ind, W.shift(1).fillna(0.0))
        net = net.dropna()
        d = (net - bench.reindex(net.index)).to_numpy()
        obs = float(d.mean())
        # sotto H0 il differenziale ha media zero: centro e risimulo
        null = stationary_bootstrap(d - d.mean(), N_BOOT, BLOCK, rng)
        pct = float((null < obs).mean() * 100)
        rows.append((nm, obs * 1200, pct,
                     float(np.percentile(null, 95)) * 1200,
                     float(np.percentile(null, 99)) * 1200))
    print(f"   {'candidato':<26}{'extra ann.':>12}{'percentile':>12}"
          f"{'95° nullo':>12}{'99° nullo':>12}")
    print("   " + "-" * 74)
    for nm, obs, pct, p95, p99 in rows:
        print(f"   {nm:<26}{obs:>11.2f}%{pct:>11.1f}%{p95:>11.2f}%{p99:>11.2f}%")
    bestrow = max(rows, key=lambda r: r[1])
    print(f"\n   Predizione: il candidato migliore cade DENTRO il 95esimo")
    print(f"   percentile. FALSIFICATA se sta oltre il 99esimo.")
    print(f"   {bestrow[0]}: percentile {bestrow[2]:.1f}")
    d2_fals = bestrow[2] > 99.0
    inside95 = bestrow[2] <= 95.0
    print(f"   -> ipotesi D2 {'FALSIFICATA' if d2_fals else 'CONFERMATA'}"
          + ("" if inside95 else
             f"  (dentro il 99esimo ma FUORI dal 95esimo: la predizione"
             f" sbaglia il livello)"))
    print(f"\n   Il bootstrap misura una cosa che il DSR non misura: quanto")
    print(f"   dell'extra-rendimento sopravvive quando si preserva")
    print(f"   l'autocorrelazione della serie ma si distrugge il legame fra")
    print(f"   segnale e rendimento futuro.")

    lab.log_trials([dict(round=ROUND, hypothesis="D1 dispersione data di partenza",
                         config=nm, window=f"{starts[0]}-{starts[-1]}",
                         sharpe="", irr="", bh_irr="", excess=float(v.mean()),
                         n_obs=len(v),
                         note=f"ampiezza={v.max()-v.min():.2f},sd={v.std(ddof=1):.2f}")
                    for nm, v in tab.items()] +
                   [dict(round=ROUND, hypothesis="D2 bootstrap a blocchi",
                         config=nm, window="intera", sharpe="", irr="",
                         bh_irr="", excess=obs, n_obs=N_BOOT,
                         note=f"percentile={pct:.1f}")
                    for nm, obs, pct, _, _ in rows])
    pd.DataFrame([dict(candidato=nm, media=float(v.mean()),
                       minimo=float(v.min()), massimo=float(v.max()),
                       ampiezza=float(v.max() - v.min()),
                       devstd=float(v.std(ddof=1))) for nm, v in tab.items()]
                 ).to_csv(OUT / "round43_d1.csv", index=False)
    pd.DataFrame(rows, columns=["candidato", "extra_annuo", "percentile",
                                "p95_nullo", "p99_nullo"]
                 ).to_csv(OUT / "round43_d2.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

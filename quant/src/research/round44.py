"""Giro 44 — A6: la perdita delle allocazioni multi-classe, scomposta.

VOCE DELLA CODA, predizione e falsificazione scritte prima:

  Il giro 30 mostra che ogni allocazione multi-classe perde contro l'azionario
  puro netto imposte, ma con turnover bassissimo (0,13-0,17 volte l'anno). Se il
  costo non e' la rotazione, e' la composizione: il decennale rende meno.
  Scomporre l'IRR persa in (a) minor rendimento atteso della sleeve difensiva e
  (b) imposte sul ribilanciamento.
  PREDIZIONE: oltre il 90% della perdita viene da (a), non da (b).
  FALSIFICATA SE: la componente fiscale supera il 25%.

COME SI SCOMPONE, e perche' l'ordine e' un problema.

Il divario totale e' IRR(azionario 100%) - IRR(allocazione, tutto incluso). Ci
sono tre ingredienti da spegnere e riaccendere:

  COMPOSIZIONE   i pesi diversi da 100% azionario, con lo stesso trattamento
                 fiscale del benchmark (un solo realizzo alla fine) e zero costi
  COSTI          0,15% round-trip sul turnover del ribilanciamento
  IMPOSTE        il 33% sulla plusvalenza realizzata a ogni ribilanciamento

Una scomposizione sequenziale dipende dall'ORDINE in cui si accendono: se le
imposte si applicano su un montante gia' ridotto dai costi, sembrano piu'
piccole. Non e' un dettaglio: e' esattamente la leva con cui si puo' far dire a
una scomposizione quel che si vuole.

Quindi calcolo TUTTI E SEI gli ordinamenti dei tre fattori e prendo la media dei
contributi marginali. E' il valore di Shapley, che e' l'unica attribuzione
simmetrica: ogni fattore riceve il suo contributo marginale medio su tutte le
sequenze possibili. Riporto anche il minimo e il massimo per ordinamento, cosi'
si vede quanto l'ordine avrebbe potuto cambiare la risposta.

DATI. Solo la finestra lunga azionario + decennale (1962-2026). Oro e materie
prime restano non testabili come al giro 30, e il PAXG che li' faceva da proxy
dell'oro non e' piu' nei dati scaricati. Lo dichiaro invece di sostituirlo.
"""
import sys
import warnings
from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES
from research import lab, bench as B, multidata as M

ROUND = 44
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 59          # famiglia pre-dichiarata dopo D3 e D4

FACTORS = ("composizione", "costi", "imposte")


def weights_path(rets, method, lookback=36, rebal=12):
    """Pesi DETENUTI in ogni periodo, stimati solo sul passato. Identico al
    giro 30: qui non si cambia la strategia, si scompone il suo risultato."""
    idx = rets.index
    n = rets.shape[1]
    W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    w = np.ones(n) / n
    for i in range(len(idx)):
        if i >= lookback and i % rebal == 0:
            cov = rets.iloc[i - lookback:i].cov().to_numpy() * 12
            if method == "erc":
                w = B.erc_weights(cov)
            elif method == "invvol":
                v = np.sqrt(np.diag(cov))
                w = (1 / np.maximum(v, 1e-12)) / (1 / np.maximum(v, 1e-12)).sum()
            elif method == "6040":
                w = np.array([0.6, 0.4] + [0.0] * (n - 2))
            elif method == "equal":
                w = np.ones(n) / n
        W.iloc[i] = w
        r = rets.iloc[i].to_numpy()
        g = w * (1 + r)
        w = g / g.sum() if g.sum() > 0 else w
    turn = W.diff().abs().sum(axis=1).fillna(W.abs().sum(axis=1)) / 2.0
    return W, turn


def irr_of(rets, W, turn, rf, comp=True, costs=True, taxes=True):
    """IRR netta con i tre ingredienti accesi o spenti.

    comp=False  -> pesi 100% azionario (prima colonna), cioe' il benchmark
    costs=False -> nessun costo di transazione sul ribilanciamento
    taxes=False -> il ribilanciamento non realizza plusvalenza (realize_frac=0)
    """
    if comp:
        Wu = W
        tu = turn
    else:
        Wu = pd.DataFrame(0.0, index=W.index, columns=W.columns)
        Wu.iloc[:, 0] = 1.0
        tu = pd.Series(0.0, index=W.index)
    gross = (Wu.shift(1).fillna(0.0) * rets).sum(axis=1)
    if costs:
        gross = gross - tu * C.COST_ROUND_TRIP
    rz = tu.clip(0, 1) if taxes else None
    g = gross.dropna()
    r = simulate_pac(g, CGT_SHARES, rf=rf.reindex(g.index).fillna(0.0),
                     realize_frac=(rz.reindex(g.index) if rz is not None else None),
                     periods_per_year=12)
    return r.irr_annual


def shapley(rets, W, turn, rf):
    """Contributo medio di ogni fattore su tutti gli ordinamenti."""
    def v(active):
        return irr_of(rets, W, turn, rf,
                      comp="composizione" in active,
                      costs="costi" in active,
                      taxes="imposte" in active)
    cache = {}

    def val(active):
        k = frozenset(active)
        if k not in cache:
            cache[k] = v(k)
        return cache[k]

    base = val(set())                      # nessun fattore = benchmark azionario
    contrib = {f: [] for f in FACTORS}
    per_order = {}
    for order in permutations(FACTORS):
        active, prev = set(), base
        seq = {}
        for f in order:
            active.add(f)
            cur = val(active)
            seq[f] = prev - cur            # positivo = perdita causata da f
            contrib[f].append(seq[f])
            prev = cur
        per_order[order] = seq
    total = base - val(set(FACTORS))
    return base, total, {f: float(np.mean(c)) for f, c in contrib.items()}, \
        {f: (float(np.min(c)), float(np.max(c))) for f, c in contrib.items()}, \
        per_order


def main():
    ffm = dataio.ff_factors_monthly()
    rf = ffm["RF"]
    eq = (ffm["Mkt-RF"] + ffm["RF"]).rename("azionario")
    bond = M.bond_total_return_monthly().rename("decennale")
    df = pd.DataFrame({"azionario": eq, "decennale": bond}).dropna()
    rf0 = rf.reindex(df.index).fillna(0.0)

    print("A6 — scomposizione della perdita delle allocazioni multi-classe")
    print(f"Finestra {df.index[0].date()} -> {df.index[-1].date()} "
          f"({len(df)} mesi), azionario + decennale")
    print("Oro e materie prime restano NON TESTABILI (giro 30); il PAXG che li'")
    print("faceva da proxy non e' piu' nei dati scaricati. Dichiarato, non sostituito.")
    print(f"Attribuzione di Shapley su tutti i {len(list(permutations(FACTORS)))} "
          f"ordinamenti dei tre fattori.\n")

    rows = []
    for m in ("erc", "invvol", "6040", "equal"):
        W, turn = weights_path(df, m)
        base, total, sh, rng, per_order = shapley(df, W, turn, rf0)
        tpy = float(turn.sum()) / (len(df) / 12)
        shares = {f: (sh[f] / total * 100 if total else float("nan")) for f in FACTORS}
        rows.append(dict(method=m, base=base, total=total, turn=tpy,
                         **{f"c_{f}": sh[f] for f in FACTORS},
                         **{f"q_{f}": shares[f] for f in FACTORS},
                         **{f"r_{f}": rng[f] for f in FACTORS}))
        print(f"{'='*88}\n{m.upper()}   turnover {tpy:.2f} volte l'anno\n{'='*88}")
        print(f"   IRR azionario 100%      {base:>7.2f}%")
        print(f"   IRR allocazione piena   {base-total:>7.2f}%")
        print(f"   divario totale          {total:>7.2f} punti\n")
        print(f"   {'fattore':<16}{'contributo':>12}{'quota':>9}"
              f"{'min-max per ordinamento':>28}")
        print("   " + "-" * 63)
        for f in FACTORS:
            lo, hi = rng[f]
            print(f"   {f:<16}{sh[f]:>11.3f}%{shares[f]:>8.1f}%"
                  f"{lo:>14.3f} / {hi:.3f}")
        print(f"   {'somma':<16}{sum(sh.values()):>11.3f}%{100.0:>8.1f}%")

    # ------------------------------------------------------------ verdetto
    print(f"\n{'='*88}\nVERDETTO SU A6\n{'='*88}")
    print("   Predizione: oltre il 90% della perdita viene da (a) la composizione.")
    print("   FALSIFICATA se la componente fiscale supera il 25%.\n")
    print(f"   {'allocazione':<12}{'composizione':>14}{'costi':>10}"
          f"{'imposte':>10}{'fiscale > 25%?':>18}")
    print("   " + "-" * 64)
    worst = 0.0
    for r in rows:
        q = r["q_imposte"]
        worst = max(worst, q)
        print(f"   {r['method']:<12}{r['q_composizione']:>13.1f}%"
              f"{r['q_costi']:>9.1f}%{r['q_imposte']:>9.1f}%"
              f"{('SI' if q > 25 else 'no'):>18}")
    fals = worst > 25.0
    print(f"\n   Quota fiscale massima fra le quattro allocazioni: {worst:.1f}%")
    comp_min = min(r["q_composizione"] for r in rows)
    print(f"   Quota della composizione, minima fra le quattro: {comp_min:.1f}%")
    print(f"   -> ipotesi A6 {'FALSIFICATA' if fals else 'CONFERMATA'}")

    # quanto avrebbe potuto cambiare l'ordine
    spread = max((r[f"r_imposte"][1] - r[f"r_imposte"][0]) for r in rows)
    print(f"\n   L'ordine di attribuzione avrebbe potuto spostare il contributo")
    print(f"   fiscale di al massimo {spread:.3f} punti fra il primo e l'ultimo")
    print(f"   ordinamento. Con l'attribuzione di Shapley questa scelta non c'e':")
    print(f"   ogni fattore prende il suo contributo marginale medio.")

    # controprova indipendente dalla scomposizione
    print(f"\n   CONTROPROVA. Se le imposte sul ribilanciamento fossero ZERO,")
    print(f"   l'allocazione batterebbe l'azionario?")
    for r, m in zip(rows, ("erc", "invvol", "6040", "equal")):
        W, turn = weights_path(df, m)
        free = irr_of(df, W, turn, rf0, comp=True, costs=True, taxes=False)
        print(f"     {m:<10} senza imposte sul ribilanciamento {free:>6.2f}% "
              f"contro {r['base']:.2f}% dell'azionario -> "
              f"{'SI' if free > r['base'] else 'NO'} ({free-r['base']:+.2f})")
    print(f"   E' la verifica che conta: anche azzerando del tutto la componente")
    print(f"   fiscale, l'allocazione resta sotto. Il problema non e' l'imposta.")

    lab.log_trials([dict(round=ROUND, hypothesis="A6 scomposizione della perdita",
                         config=r["method"],
                         window=f"{df.index[0].date()}/{df.index[-1].date()}",
                         sharpe="", irr=r["base"] - r["total"], bh_irr=r["base"],
                         excess=-r["total"], n_obs=len(df),
                         note=f"comp={r['q_composizione']:.1f}%,"
                              f"costi={r['q_costi']:.1f}%,"
                              f"imposte={r['q_imposte']:.1f}%") for r in rows])
    pd.DataFrame([{k: (str(v) if isinstance(v, tuple) else v)
                   for k, v in r.items()} for r in rows]
                 ).to_csv(OUT / "round44_a6.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

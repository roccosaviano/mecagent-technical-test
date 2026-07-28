"""Giro 69 — K1: il conto in valuta.

VOCE DELLA CODA, predizione verbatim (committata prima di eseguire, 3f0e1d2):

K1 — Il conto in valuta
  Tutti i sessantotto giri misurano in dollari. Un residente irlandese versa
  euro, incassa euro e paga imposte in euro su plusvalenze in euro.
  PREDIZIONE: il LIVELLO dell'IRR si sposta di 0,5-1,5 punti, la volatilita' in
  euro e' 2-5 punti piu' alta che in dollari, ma il MARGINE strategia-meno-
  benchmark si sposta di MENO DI 0,5 PUNTI, perche' il cambio e' un fattore
  comune ai due lati e in differenza si cancella quasi tutto. Quasi, non del
  tutto: le imposte si pagano su plusvalenze in euro, quindi chi realizza piu'
  spesso cristallizza piu' spesso anche il cambio, e il residuo e' proporzionale
  alla rotazione.
  FALSIFICATA SE: il margine di almeno una coppia si sposta di OLTRE 0,5 PUNTI —
  nel qual caso il cambio non e' un fattore comune e ogni verdetto del progetto
  va rimisurato in euro — OPPURE la volatilita' in euro risulta PIU' BASSA che in
  dollari, nel qual caso il cambio copre il rischio azionario invece di
  sommarvisi.

LA SERIE DEL CAMBIO. DEXUSEU (dollari per euro) e' giornaliera dal 1999. Prima
non esisteva l'euro: uso il marco, EXGEUS (marchi per dollaro, mensile dal 1971),
e lo converto al tasso irrevocabile 1,95583 DEM/EUR. E' l'euro sintetico
standard. Il raccordo cade a dicembre 1998 ed e' verificato sotto: le due serie
devono combaciare al raccordo, altrimenti c'e' un errore di verso.

LA CONVERSIONE. Un investitore in euro che detiene un'attivita' in dollari:
  valore in EUR = valore in USD / fx      (fx = dollari per euro)
  r_eur = (1 + r_usd) * fx_{t-1}/fx_t - 1
Se l'euro si rafforza (fx sale) l'attivita' in dollari vale meno in euro. Il
verso e' quello, e sotto c'e' un controllo numerico che lo conferma.

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
from research import multidata as M

ROUND = 69
OUT = Path(__file__).resolve().parents[2] / "out"
DEM_EUR = 1.95583


def cambio_mensile(raccorda=False):
    """Dollari per euro, mensile. Euro sintetico dal marco prima del 1999.

    EXGEUS e' una MEDIA mensile, DEXUSEU ricampionato e' un FINE MESE: al
    raccordo le due convenzioni non combaciano. Con raccorda=True il tratto
    sintetico viene riscalato perche' combaci esattamente al primo mese comune.
    """
    d = M.fred("DEXUSEU").resample("ME").last().dropna()
    g = M.fred("EXGEUS").dropna()          # marchi per dollaro, mensile
    g.index = pd.DatetimeIndex(g.index).to_period("M").to_timestamp("M")
    sint = DEM_EUR / g                     # dollari per euro
    d.index = pd.DatetimeIndex(d.index).to_period("M").to_timestamp("M")
    prima = sint[sint.index < d.index[0]]
    if raccorda:
        ov = sint.index.intersection(d.index)
        if len(ov):
            k = float(d.reindex(ov).iloc[0]) / float(sint.reindex(ov).iloc[0])
            prima = prima * k
    return pd.concat([prima, d]).sort_index(), sint, d


def in_euro(r_usd, fx):
    """Rendimento in euro di un'attivita' in dollari."""
    f = fx.reindex(r_usd.index).ffill()
    return ((1 + r_usd) * f.shift(1) / f - 1).dropna()


def rot_vera(rets, Wt):
    n = rets.shape[1]
    w = np.zeros(n)
    turns = []
    for i in range(len(rets)):
        tgt = Wt.iloc[i].to_numpy(dtype=float)
        turns.append(float(np.abs(tgt - w).sum() / 2.0))
        w = tgt
        g = w * (1 + rets.iloc[i].to_numpy(dtype=float))
        s = g.sum()
        w = g / s if s > 0 else w
    return pd.Series(turns, index=rets.index)


def annuale(ind, mese, score=None, top=None):
    n = ind.shape[1]
    w = np.ones(n) / n
    out = []
    for i, t in enumerate(ind.index):
        if t.month == mese:
            if score is None:
                w = np.ones(n) / n
            else:
                s = score.iloc[i]
                if s.notna().sum() >= top:
                    best = s.nlargest(top).index
                    w = np.zeros(n)
                    w[[ind.columns.get_loc(c) for c in best]] = 1.0 / top
        out.append(w.copy())
        g = w * (1 + ind.iloc[i].to_numpy(dtype=float))
        ssum = g.sum()
        w = g / ssum if ssum > 0 else w
    return pd.DataFrame(out, index=ind.index, columns=ind.columns)


def mensile_top(score, top):
    rk = score.rank(axis=1, ascending=False)
    W = (rk <= top).astype(float)
    return W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def main():
    fx, sint, dex = cambio_mensile()
    print(f"{'=' * 104}\nK1 — il conto in valuta: lo stesso PAC misurato in "
          f"dollari e in euro\n{'=' * 104}")

    # ---- controllo del raccordo e del verso, prima di qualunque risultato
    ov = sint.index.intersection(dex.index)
    print(f"\n   Cambio: euro sintetico dal marco {sint.index[0].date()} → "
          f"{sint.index[-1].date()}, poi DEXUSEU.")
    if len(ov) > 0:
        a, b = float(sint.reindex(ov).iloc[0]), float(dex.reindex(ov).iloc[0])
        print(f"   Raccordo: sintetico {a:.4f} contro DEXUSEU {b:.4f} "
              f"({(a / b - 1) * 100:+.2f}%)")
    else:
        print(f"   Raccordo: dic-1998 sintetico "
              f"{float(sint.iloc[-1]):.4f}, gen-1999 DEXUSEU "
              f"{float(dex.iloc[0]):.4f}")
    print(f"   Controllo del verso: se l'euro si rafforza, un'attivita' in "
          f"dollari deve rendere MENO in euro.")
    prova = pd.Series([0.0, 0.0], index=fx.index[-2:])
    f2 = fx.iloc[-2:]
    seg = "+" if f2.iloc[-1] > f2.iloc[-2] else "-"
    print(f"     fx da {float(f2.iloc[-2]):.4f} a {float(f2.iloc[-1]):.4f} "
          f"({seg}), rendimento USD 0% → in euro "
          f"{float(in_euro(prova, fx).iloc[-1]) * 100:+.2f}%")

    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ffm = dataio.ff_factors_monthly()
    mkt = (ffm["Mkt-RF"] + ffm["RF"])
    rf = ffm["RF"]
    for s in (ind, mkt, rf):
        s.index = pd.DatetimeIndex(s.index).to_period("M").to_timestamp("M")
    idx = ind.index.intersection(fx.index)
    ind, mkt, rf = ind.loc[idx], mkt.loc[idx], rf.loc[idx]
    fx = fx.reindex(idx).ffill()
    print(f"\n   Finestra comune: {idx[0].date()} → {idx[-1].date()} "
          f"({len(idx)} mesi)\n")

    mom12 = (1 + ind).rolling(11).apply(np.prod, raw=True).shift(2)
    strategie = [
        ("buy&hold azionario USA", None, None),
        ("equal-weight annuale (gen)", annuale(ind, 1), None),
        ("momentum top-10 mensile", mensile_top(mom12, 10), None),
        ("momentum top-5 annuale (gen)", annuale(ind, 1, mom12, 5), None),
    ]

    righe = []
    print(f"   {'strategia':<30}{'valuta':>8}{'CAGR':>9}{'vol':>8}{'rotaz.':>9}"
          f"{'aliq.':>7}{'IRR':>9}")
    print("   " + "-" * 80)
    for nome, W, _ in strategie:
        for val in ("USD", "EUR"):
            if W is None:
                r = mkt if val == "USD" else in_euro(mkt, fx)
                turn = pd.Series(0.0, index=r.index)
            else:
                base = ind if val == "USD" else ind.apply(lambda c: in_euro(c, fx))
                base = base.dropna()
                Wx = W.reindex(base.index).fillna(0.0)
                turn = rot_vera(base, Wx)
                r = ((Wx * base).sum(axis=1) - turn * C.COST_ROUND_TRIP).dropna()
            rfx = rf.reindex(r.index).fillna(0.0)
            res = B.eval_stream(f"{nome} {val}", r.dropna(), rfx,
                                turn.reindex(r.index))
            res.update(strategia=nome, valuta=val,
                       rot=float(turn.sum()) / (len(r) / 12))
            righe.append(res)
            print(f"   {nome if val == 'USD' else '':<30}{val:>8}"
                  f"{res['cagr']:>8.2f}%{res['vol']:>7.2f}%{res['rot']:>8.2f}x"
                  f"{res['rate_ref']:>6}%{res['irr_ref']:>8.2f}%")

    # ------------------------------------------------------- livelli e margini
    D = {(r["strategia"], r["valuta"]): r for r in righe}
    nomi = [n for n, _, _ in strategie]
    print(f"\n   SPOSTAMENTO DEL LIVELLO (EUR meno USD):\n")
    print(f"   {'strategia':<30}{'IRR USD':>10}{'IRR EUR':>10}{'delta':>9}"
          f"{'vol USD':>10}{'vol EUR':>10}{'delta vol':>11}")
    print("   " + "-" * 90)
    liv, dvol = [], []
    for n in nomi:
        a, b = D[(n, "USD")], D[(n, "EUR")]
        liv.append(b["irr_ref"] - a["irr_ref"])
        dvol.append(b["vol"] - a["vol"])
        print(f"   {n:<30}{a['irr_ref']:>9.2f}%{b['irr_ref']:>9.2f}%"
              f"{liv[-1]:>+8.2f}{a['vol']:>9.2f}%{b['vol']:>9.2f}%"
              f"{dvol[-1]:>+10.2f}")

    print(f"\n   SPOSTAMENTO DEL MARGINE contro l'equal-weight annuale:\n")
    print(f"   {'coppia':<34}{'margine USD':>13}{'margine EUR':>13}"
          f"{'spostamento':>13}{'rotaz.':>9}")
    print("   " + "-" * 82)
    marg = []
    for n in nomi:
        if n == "equal-weight annuale (gen)":
            continue
        mu = D[(n, "USD")]["irr_ref"] - D[("equal-weight annuale (gen)", "USD")]["irr_ref"]
        me = D[(n, "EUR")]["irr_ref"] - D[("equal-weight annuale (gen)", "EUR")]["irr_ref"]
        marg.append((n, mu, me, me - mu, D[(n, "USD")]["rot"]))
        print(f"   {n:<34}{mu:>+12.2f}%{me:>+12.2f}%{me - mu:>+12.2f}"
              f"{D[(n, 'USD')]['rot']:>8.2f}x")

    # ------------------------------------------------------------- verdetto
    liv_min, liv_max = min(abs(x) for x in liv), max(abs(x) for x in liv)
    vol_neg = sum(1 for x in dvol if x < 0)
    sp_max = max(abs(m[3]) for m in marg)
    peggiore = max(marg, key=lambda m: abs(m[3]))

    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: il livello si sposta di 0,5-1,5 punti, la volatilita' "
          f"in euro e' 2-5 punti")
    print(f"   piu' alta, e il margine si sposta di MENO di 0,5 punti.")
    print(f"   FALSIFICATA se un margine si sposta di OLTRE 0,5 punti, OPPURE "
          f"la volatilita' in euro e' piu' bassa.\n")
    print(f"   spostamento del livello       : da {liv_min:.2f} a {liv_max:.2f} "
          f"punti   (previsto 0,5-1,5)")
    print(f"   volatilita' EUR meno USD      : da {min(dvol):+.2f} a "
          f"{max(dvol):+.2f} punti   (previsto +2/+5; falsifica se negativa)")
    print(f"   spostamento massimo del margine: {sp_max:.2f} punti "
          f"({peggiore[0]}, rotazione {peggiore[4]:.2f}x)   (falsifica sopra 0,5)")

    fals = sp_max > 0.5 or vol_neg > 0
    print(f"\n   -> ipotesi K1 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'livello 0,5-1,5 punti': "
          f"{'centrata' if 0.5 <= liv_min and liv_max <= 1.5 else 'SBAGLIATA'}")
    print(f"      clausola 'volatilita' +2/+5 punti': "
          f"{'centrata' if 2.0 <= min(dvol) and max(dvol) <= 5.0 else 'SBAGLIATA'}")
    print(f"      clausola 'margine sotto 0,5': "
          f"{'centrata' if sp_max <= 0.5 else 'SBAGLIATA'}")

    # il meccanismo previsto: il residuo cresce con la rotazione?
    rr = np.array([m[4] for m in marg])
    ss = np.array([abs(m[3]) for m in marg])
    if len(rr) > 2 and rr.std() > 0:
        print(f"\n   Meccanismo previsto (il residuo cresce con la rotazione):")
        print(f"     corr(rotazione, |spostamento del margine|) = "
              f"{np.corrcoef(rr, ss)[0, 1]:+.3f}")

    # ---- controllo: quanto conta il salto al raccordo delle due serie
    fx2, _, _ = cambio_mensile(raccorda=True)
    fx2 = fx2.reindex(idx).ffill()
    print(f"\n   CONTROLLO — raccordo delle due serie del cambio riscalato "
          f"perche' combaci:\n")
    print(f"   {'strategia':<32}{'IRR EUR':>10}{'IRR EUR raccordato':>21}"
          f"{'differenza':>13}")
    print("   " + "-" * 76)
    for nome, W, _ in strategie:
        if W is None:
            r2 = in_euro(mkt, fx2)
            t2 = pd.Series(0.0, index=r2.index)
        else:
            b2 = ind.apply(lambda c: in_euro(c, fx2)).dropna()
            W2 = W.reindex(b2.index).fillna(0.0)
            t2 = rot_vera(b2, W2)
            r2 = ((W2 * b2).sum(axis=1) - t2 * C.COST_ROUND_TRIP).dropna()
        e2 = B.eval_stream("x", r2.dropna(), rf.reindex(r2.index).fillna(0.0),
                           t2.reindex(r2.index))
        v1 = D[(nome, "EUR")]["irr_ref"]
        print(f"   {nome:<32}{v1:>9.2f}%{e2['irr_ref']:>20.2f}%"
              f"{e2['irr_ref'] - v1:>+12.2f}")

    pd.DataFrame([{k: v for k, v in r.items() if k not in ("net", "gross")}
                  for r in righe]).to_csv(OUT / "round69_k1.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="K1 conto in valuta",
                         config=f"{r['strategia']} {r['valuta']}",
                         window=f"{idx[0].year}-{idx[-1].year}",
                         sharpe=r["sharpe"], irr=r["irr_ref"], bh_irr="",
                         excess="", n_obs=r["n"],
                         note=f"vol={r['vol']:.2f},rot={r['rot']:.2f}")
                    for r in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

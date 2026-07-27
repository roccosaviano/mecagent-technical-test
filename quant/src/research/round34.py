"""Giro 34 — A5: equal risk contribution fra i 4 stream meno correlati.

VOCE DELLA CODA, predizione e falsificazione scritte prima:

  Selezionati per correlazione, non per rendimento, cosi' la scelta non guarda
  il risultato.
  PREDIZIONE: correlazione media sotto 0,3 raggiungibile, ma l'IRR netta resta
  sotto il buy&hold perche' i componenti a rendimento alto sono anche quelli ad
  alta rotazione.
  FALSIFICATA SE: IRR netta > buy&hold.

LA REGOLA DI SELEZIONE, fissata prima di calcolare i rendimenti. Costruisco la
libreria di flussi disponibili, calcolo la matrice di correlazione, e scelgo il
sottoinsieme di 4 che MINIMIZZA la correlazione media a coppie. Il rendimento
non entra nella scelta: e' l'unico modo di evitare che questa voce diventi
"scegli i quattro che hanno funzionato".

Le cripto sono escluse dalla selezione: entrerebbero certamente (correlazione
quasi nulla con tutto) ma taglierebbero la finestra comune a sei anni, e la
finestra corta e' gia' il problema di B6. Lo dichiaro invece di nasconderlo.
"""
import sys
import warnings
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from research import lab, bench as B, multidata as M

ROUND = 34
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 56          # famiglia pre-dichiarata dopo A9 e A10


def build_streams():
    """Libreria di flussi. Ognuno restituisce (rendimento netto, realize_frac)."""
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    out = {}

    # 1. azionario puro
    out["azionario"] = (mkt, pd.Series(0.0, index=mkt.index))

    # 2. decennale ricostruito
    bond = M.bond_total_return_monthly()
    out["decennale"] = (bond, pd.Series(0.0, index=bond.index))

    # 3. momentum settoriale 12-2, lungo i 10 migliori
    W = B.xs_momentum(ind, 12, 1, 10)
    net, turn = B.wbacktest(ind, W.shift(1).fillna(0.0))
    out["momentum settoriale"] = (net, turn)

    # 4. tilt low-volatility settoriale: i 10 settori meno volatili a 36 mesi
    vol = ind.rolling(36).std().shift(1)
    rk = vol.rank(axis=1)
    Wl = (rk <= 10).astype(float)
    Wl = Wl.div(Wl.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
    nl, tl = B.wbacktest(ind, Wl.shift(1).fillna(0.0))
    out["low-vol settoriale"] = (nl, tl)

    # 5. filtro di trend sull'indice (10 mesi)
    px = (1 + mkt).cumprod()
    e = B.ma_filter(px, 10)
    rf0 = rf.reindex(mkt.index).fillna(0.0)
    tr = e * mkt + (1 - e) * rf0 * (1 - C.DIRT_RATE)
    out["trend sull'indice"] = (tr, e.diff().abs().clip(lower=0).fillna(0.0))

    # 6. premio di volatilita': BXM (buy-write CBOE)
    try:
        from research.round27 import cboe
        bxm = cboe("BXM")
        b = bxm.resample("ME").last().pct_change().dropna()
        b.index = b.index.to_period("M").to_timestamp("M")
        out["premio volatilita' BXM"] = (b, pd.Series(0.0, index=b.index))
    except Exception as ex:
        print(f"   (BXM non disponibile: {type(ex).__name__})")

    # 7. gross profitability long-only dai portafogli OSAP
    try:
        sd = dataio.osap_signaldoc()
        pt = dataio.osap_ports(["GP"])
        gp = pt[pt["signalname"] == "GP"] if "signalname" in pt else None
        if gp is not None and len(gp):
            b = sorted(gp["port"].unique())
            hi = gp[gp["port"] == b[-1]].set_index("date")["ret"] / 100.0
            hi.index = pd.to_datetime(hi.index).to_period("M").to_timestamp("M")
            out["gross profitability"] = (hi.dropna(),
                                          pd.Series(0.0, index=hi.dropna().index))
    except Exception as ex:
        print(f"   (GP non disponibile: {type(ex).__name__})")

    return out, rf, mkt


def main():
    print("A5 — equal risk contribution fra i 4 stream meno correlati")
    print("Selezione per CORRELAZIONE, mai per rendimento.\n")
    streams, rf, mkt = build_streams()
    names = list(streams)
    print(f"Libreria: {len(names)} flussi — {', '.join(names)}")

    R = pd.DataFrame({k: v[0] for k, v in streams.items()})
    RZ = pd.DataFrame({k: v[1] for k, v in streams.items()})
    R = R.dropna()
    RZ = RZ.reindex(R.index).fillna(0.0)
    print(f"Finestra comune: {R.index[0].date()} -> {R.index[-1].date()} "
          f"({len(R)} mesi)\n")

    corr = R.corr()
    print("Matrice di correlazione:")
    print(corr.round(2).to_string())

    best, bestc = None, 9e9
    for combo in combinations(names, 4):
        sub = corr.loc[list(combo), list(combo)].to_numpy()
        m = (sub.sum() - 4) / (4 * 3)
        if m < bestc:
            best, bestc = combo, m
    print(f"\nQuartetto meno correlato: {', '.join(best)}")
    print(f"Correlazione media a coppie: {bestc:.3f}  -> "
          f"{'SOTTO' if bestc < 0.3 else 'SOPRA'} 0,30 come previsto")

    sub = R[list(best)]
    subz = RZ[list(best)]
    rows = []

    # benchmark: azionario puro sulla stessa finestra
    bh = B.eval_stream("azionario puro (benchmark)", R["azionario"], rf)
    rows.append(bh)

    for meth in ("erc", "equal", "invvol"):
        W = pd.DataFrame(0.0, index=sub.index, columns=sub.columns)
        w = np.ones(4) / 4
        for i in range(len(sub)):
            if i >= 36 and i % 12 == 0:
                cov = sub.iloc[i - 36:i].cov().to_numpy() * 12
                if meth == "erc":
                    w = B.erc_weights(cov)
                elif meth == "invvol":
                    v = np.sqrt(np.diag(cov))
                    w = (1 / v) / (1 / v).sum()
                else:
                    w = np.ones(4) / 4
            W.iloc[i] = w
        net, turn = B.wbacktest(sub, W.shift(1).fillna(0.0))
        # realizzo = ribilanciamento + realizzi interni dei componenti
        rz = (turn + (W.shift(1).fillna(0.0) * subz).sum(axis=1)).clip(0, 1)
        rows.append(B.eval_stream(f"4 stream — {meth}", net.dropna(), rf,
                                  rz.reindex(net.dropna().index)))

    print()
    B.table(rows)

    print(f"\n{'='*88}\nVERDETTO SU A5\n{'='*88}")
    print("   Predizione: correlazione media sotto 0,3 raggiungibile, ma IRR")
    print("   netta sotto il buy&hold. FALSIFICATA se IRR netta > buy&hold.\n")
    print(f"   (a) correlazione media {bestc:.3f} -> "
          f"{'raggiunta' if bestc < 0.3 else 'NON raggiunta'}")
    cand = [r for r in rows if r["label"].startswith("4 stream")]
    for r in cand:
        print(f"   (b) {r['label']:<24} IRR di riferimento {r['irr_ref']:.2f}% "
              f"(aliquota {r['rate_ref']}%) contro benchmark {bh['irr']:.2f}% "
              f"-> {r['irr_ref']-bh['irr']:+.2f}")
    falsified = any(r["irr_ref"] > bh["irr"] for r in cand)
    print(f"\n   -> ipotesi A5 {'FALSIFICATA' if falsified else 'CONFERMATA'}")

    bestr = max(cand, key=lambda r: r["irr_ref"])
    d = lab.deflated_sharpe(bestr["gross"], N_PREREG, round_id=ROUND)
    print(f"   DSR del migliore su N={N_PREREG}: {d['dsr']:.3f} -> "
          f"{'PROMUOVIBILE' if d['dsr']>0.95 and bestr['irr_ref']>bh['irr'] else 'NON promuovibile'}")
    print("\n   ESCLUSE dalla selezione: le cripto. Entrerebbero di certo per")
    print("   correlazione quasi nulla, ma taglierebbero la finestra comune a")
    print("   sei anni. La finestra corta e' gia' il problema di B6.")

    lab.log_trials([dict(round=ROUND, hypothesis="A5 ERC fra 4 stream scorrelati",
                         config=r["label"], window=f"{R.index[0].date()}/{R.index[-1].date()}",
                         sharpe=r["sharpe"], irr=r["irr"], bh_irr=bh["irr"],
                         excess=r["irr_ref"] - bh["irr"], n_obs=r["n"],
                         note=f"turn={r['turn']:.2f}x") for r in rows])
    pd.DataFrame([{k: v for k, v in r.items() if k != "gross"}
                  for r in rows]).to_csv(OUT / "round34_erc4.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

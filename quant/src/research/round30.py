"""Giro 30 — A1: risk parity fra classi di asset.

VOCE DELLA CODA, predizione e falsificazione gia' scritte prima:

  Pesi inversi al contributo di rischio su azionario, decennale, oro-proxy,
  materie prime. Ribilanciamento annuale.
  PREDIZIONE: Sharpe superiore al 60/40 ma IRR netta inferiore all'azionario
  puro, perche' il decennale rende meno e il ribilanciamento e' tassato.
  FALSIFICATA SE: IRR netta > buy&hold azionario.

COSA HO POTUTO COSTRUIRE, E COSA NO.

  azionario     indice CRSP total return, dati reali dal 1926
  decennale     ricostruito da DGS10 a duration costante. NON e' un indice
                obbligazionario: sottostima convessita' e rolldown, e lo
                dichiaro. Dal 1962.
  oro           PAXG, oro tokenizzato su OKX. E' l'unico proxy dell'oro
                COMPRABILE che sono riuscito a ottenere: su FRED ci sono solo
                indici di prezzo alla produzione, che non sono investibili, e
                le serie LBMA sono state ritirate. Storia dal 2020 e rischio
                di controparte dell'emittente.
  materie prime NON TESTABILE. Servirebbe un indice total return (GSCI,
                Bloomberg Commodity) che replichi il rolling dei futures. Il
                petrolio spot di FRED e' un prezzo, non un investimento: chi
                compra petrolio paga il roll, che storicamente e' la
                componente dominante del rendimento. Usarlo darebbe un numero
                sbagliato in modo non conservativo.

Eseguo quindi su DUE finestre, dichiarando entrambe:
  (1) lunga 1962-2026, azionario + decennale — le due classi che ho davvero
  (2) corta 2020-2026, azionario + decennale + oro + cripto — quattro classi,
      ma sei anni e con il bias di sopravvivenza delle cripto

Il risk parity vero e' un metodo di allocazione, non un asset: se funziona su
due classi funziona anche su quattro, e se non funziona su due non lo salva
aggiungerne altre.
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
from tax import simulate_pac, CGT_SHARES, TRADING_52, first_of_month
from research import lab, multidata as M
from research.round25 import _stats

ROUND = 30
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 52          # famiglia delle ipotesi pre-dichiarate dopo QUEUE.md


def erc_weights(cov, iters=200):
    """Equal risk contribution: ogni asset contribuisce ugualmente al rischio.
    Algoritmo iterativo di Spinu, semplice e stabile su pochi asset."""
    n = cov.shape[0]
    w = np.ones(n) / n
    for _ in range(iters):
        mrc = cov @ w
        rc = w * mrc
        w = w * (rc.mean() / np.maximum(rc, 1e-12)) ** 0.5
        w = np.maximum(w, 1e-6)
        w = w / w.sum()
    return w


def inv_vol(cov):
    v = np.sqrt(np.diag(cov))
    w = 1.0 / np.maximum(v, 1e-12)
    return w / w.sum()


def alloc_backtest(rets, method, lookback=36, rebal=12,
                   cost=C.COST_ROUND_TRIP):
    """Ribilanciamento periodico su pesi stimati SOLO sul passato."""
    idx = rets.index
    W = pd.DataFrame(0.0, index=idx, columns=rets.columns)
    w = np.ones(rets.shape[1]) / rets.shape[1]
    for i in range(len(idx)):
        if i >= lookback and i % rebal == 0:
            cov = rets.iloc[i - lookback:i].cov().to_numpy() * 12
            if method == "erc":
                w = erc_weights(cov)
            elif method == "invvol":
                w = inv_vol(cov)
            elif method == "6040":
                w = np.array([0.6, 0.4] + [0.0] * (rets.shape[1] - 2))
                w = w / w.sum()
            elif method == "equal":
                w = np.ones(rets.shape[1]) / rets.shape[1]
        W.iloc[i] = w
        r = rets.iloc[i].to_numpy()
        g = w * (1 + r)
        w = g / g.sum() if g.sum() > 0 else w
    turn = W.diff().abs().sum(axis=1).fillna(W.abs().sum(axis=1)) / 2.0
    net = (W.shift(1).fillna(0.0) * rets).sum(axis=1) - turn * cost
    return net.dropna(), turn.reindex(net.index).fillna(0.0), W


def report(name, rets, rf, methods=("erc", "invvol", "6040", "equal")):
    print(f"\n{'='*84}\n{name}   {rets.index[0].date()} -> {rets.index[-1].date()} "
          f"({len(rets)} mesi, {rets.shape[1]} classi)\n{'='*84}")
    print(f"   classi: {', '.join(rets.columns)}")
    eq = rets.iloc[:, 0]
    rf0 = rf.reindex(rets.index).fillna(0.0)
    con = None
    bb = simulate_pac(eq, CGT_SHARES, rf=rf0, periods_per_year=12)
    be = _stats(eq, 12)
    out = []
    print(f"\n   {'metodo':<22}{'CAGR':>9}{'Sharpe':>8}{'DD':>9}{'turn/an':>9}"
          f"{'IRR 33%':>10}{'vs azion.':>11}")
    for m in methods:
        net, turn, W = alloc_backtest(rets, m)
        s = _stats(net, 12)
        tpy = float(turn.sum()) / (len(net) / 12)
        r33 = simulate_pac(net, CGT_SHARES, rf=rf0.reindex(net.index).fillna(0),
                           realize_frac=turn.clip(0, 1), periods_per_year=12)
        r52 = simulate_pac(net, TRADING_52, rf=rf0.reindex(net.index).fillna(0),
                           realize_frac=turn.clip(0, 1), periods_per_year=12)
        out.append(dict(name=name, method=m, **s, turn=tpy, irr=r33.irr_annual,
                        irr52=r52.irr_annual, vs=r33.irr_annual - bb.irr_annual,
                        net=net))
        print(f"   {m:<22}{s['cagr']:>8.2f}%{s['sharpe']:>8.2f}{s['dd']:>8.1f}%"
              f"{tpy:>8.2f}x{r33.irr_annual:>9.2f}%"
              f"{r33.irr_annual-bb.irr_annual:>+10.2f}%")
    print(f"   {'azionario 100%':<22}{be['cagr']:>8.2f}%{be['sharpe']:>8.2f}"
          f"{be['dd']:>8.1f}%{0.0:>8.2f}x{bb.irr_annual:>9.2f}%{0.0:>+10.2f}%")
    return out, bb.irr_annual, be["sharpe"]


def main():
    ffm = dataio.ff_factors_monthly()
    rf = ffm["RF"]
    eq = (ffm["Mkt-RF"] + ffm["RF"]).rename("azionario")
    bond = M.bond_total_return_monthly().rename("decennale")

    # ---------------------------------------------- finestra lunga
    long_df = pd.DataFrame({"azionario": eq, "decennale": bond}).dropna()
    o1, bh1, bsh1 = report("FINESTRA LUNGA — azionario + decennale",
                           long_df, rf)

    # ---------------------------------------------- finestra corta
    short_parts = {"azionario": eq, "decennale": bond}
    try:
        from research.round19 import load_crypto
        g = load_crypto("PAXGUSDT").close.resample("ME").last().pct_change()
        short_parts["oro"] = g.rename("oro")
        b = load_crypto("BTCUSDT").close.resample("ME").last().pct_change()
        short_parts["cripto"] = b.rename("cripto")
    except FileNotFoundError:
        print("\n   (oro/cripto non disponibili, salto la finestra corta)")
    o2 = []
    if len(short_parts) > 2:
        short_df = pd.DataFrame(short_parts).dropna()
        if len(short_df) > 40:
            o2, bh2, bsh2 = report(
                "FINESTRA CORTA — azionario + decennale + oro + cripto",
                short_df, rf)

    # ---------------------------------------------- verdetto
    print(f"\n{'='*84}\nVERDETTO SU A1\n{'='*84}")
    allr = o1 + o2
    erc_long = next(x for x in o1 if x["method"] == "erc")
    s6040 = next(x for x in o1 if x["method"] == "6040")
    print(f"   Predizione: Sharpe risk parity > 60/40, ma IRR netta < azionario.")
    print(f"   Osservato (finestra lunga):")
    print(f"     Sharpe ERC {erc_long['sharpe']:.2f} contro 60/40 "
          f"{s6040['sharpe']:.2f}  -> {'SI' if erc_long['sharpe']>s6040['sharpe'] else 'NO'}")
    print(f"     IRR netta ERC {erc_long['irr']:.2f}% contro azionario "
          f"{bh1:.2f}%  -> {'INFERIORE' if erc_long['irr']<bh1 else 'SUPERIORE'}")
    falsified = any(x["vs"] > 0 for x in allr)
    print(f"\n   Qualche configurazione batte l'azionario netto imposte? "
          f"{'SI' if falsified else 'NO'}")
    print(f"   -> ipotesi A1 {'FALSIFICATA' if falsified else 'CONFERMATA'}")

    best = max(allr, key=lambda x: x["vs"])
    d = lab.deflated_sharpe(best["net"], N_PREREG, round_id=ROUND)
    print(f"\n   Migliore: {best['method']} su {best['name'][:28]}  "
          f"{best['vs']:+.2f} punti")
    print(f"   DSR su {N_PREREG} ipotesi pre-dichiarate: {d['dsr']:.3f}  -> "
          f"{'PROMUOVIBILE' if d['dsr']>0.95 and best['vs']>0 else 'NON promuovibile'}")

    print(f"\n   NON TESTATO: materie prime. Serve un indice total return che")
    print(f"   replichi il rolling dei futures; il petrolio spot di FRED e' un")
    print(f"   prezzo, e usarlo sovrastimerebbe il rendimento della classe.")

    lab.log_trials([dict(round=ROUND, hypothesis="A1 risk parity fra classi",
                         config=f"{x['name'][:20]}|{x['method']}",
                         window="varie", sharpe=x["sharpe"], irr=x["irr"],
                         bh_irr="", excess=x["vs"], n_obs=len(x["net"]),
                         note=f"turn={x['turn']:.2f}x") for x in allr])
    pd.DataFrame([{k: v for k, v in x.items() if k != "net"}
                  for x in allr]).to_csv(OUT / "round30_riskparity.csv",
                                         index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

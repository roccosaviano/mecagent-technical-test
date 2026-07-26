"""Giro 20 — I tre controlli che il risultato crypto del giro 19 deve superare.

Il giro 19 ha dato il primo risultato positivo forte di tutto lo studio: VWAP
long-only trimestrale su 7 crypto, 90,3% di CAGR contro 63,8% del buy&hold,
Sharpe 1,53 contro 1,03, drawdown -41,8% contro -81,0%.

Prima di crederci, tre domande che possono demolirlo:

  1. E' VWAP o e' solo un FILTRO DI TREND? "Long quando il prezzo sta sopra
     il VWAP trimestrale" e' quasi indistinguibile da "long quando il prezzo
     sta sopra la sua media a N giorni". Se una media mobile semplice da' gli
     stessi numeri, il VWAP non c'entra niente: sto ritestando il trend
     following, che ho gia' bocciato sull'azionario.

  2. Cosa resta DOPO LE IMPOSTE? 34-115 operazioni l'anno su cripto: in
     Irlanda sono un asset ai fini CGT, e a quella frequenza la
     riqualificazione al 52% e' lo scenario da assumere, non il caso limite.

  3. Quanto pesa la SOPRAVVIVENZA? BTC, ETH, SOL, XRP, DOGE, LTC, ADA sono i
     superstiti di oggi. Le cripto morte fra il 2017 e oggi non sono nel
     campione, ne' per la strategia ne' per il benchmark.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
from tax import simulate_pac, CGT_SHARES, TRADING_52
from research import lab
from research.round16 import anchored_vwap
from research.round19 import load_crypto, evaluate_ls, SYMS, COST_CRYPTO

ROUND = 20
OUT = Path(__file__).resolve().parents[2] / "out"


def main():
    data = {}
    for s in SYMS:
        try:
            data[s] = load_crypto(s)
        except FileNotFoundError:
            pass
    common = None
    for df in data.values():
        common = df.index if common is None else common.intersection(df.index)
    print(f"{len(data)} asset, finestra comune {common[0].date()} -> "
          f"{common[-1].date()} ({len(common)} giorni)\n")

    # ============================================ 1. VWAP o solo trend?
    print("=" * 78)
    print("1. IL SEGNALE E' IL VWAP O E' SOLO UN FILTRO DI TREND?")
    print("=" * 78)
    print("   Confronto il VWAP trimestrale con medie mobili semplici di")
    print("   lunghezza confrontabile, sullo stesso portafoglio equipesato.\n")

    def port_net(posfun):
        nets = []
        for s, df in data.items():
            ret = df.close.pct_change().fillna(0.0)
            nets.append(evaluate_ls(ret, posfun(df))["net"].reindex(common))
        return pd.concat(nets, axis=1).mean(axis=1).dropna()

    def stats(net):
        yrs = len(net) / 365
        curve = (1 + net).cumprod()
        tot = float(curve.iloc[-1])
        return dict(cagr=(tot ** (1 / yrs) - 1) * 100 if tot > 0 else -100.0,
                    sharpe=float(net.mean() / net.std() * np.sqrt(365)),
                    dd=float((curve / curve.cummax() - 1).min()) * 100)

    variants = {
        "buy&hold": lambda df: pd.Series(1.0, index=df.index),
        "VWAP trimestrale": lambda df: (df.close > anchored_vwap(df, "QE"))
                                       .astype(float).shift(1).fillna(0.0),
        "VWAP mensile": lambda df: (df.close > anchored_vwap(df, "ME"))
                                   .astype(float).shift(1).fillna(0.0),
    }
    for n in (20, 50, 100, 200):
        variants[f"media mobile {n}g"] = (
            lambda df, n=n: (df.close > df.close.rolling(n).mean())
            .astype(float).shift(1).fillna(0.0))

    print(f"{'segnale':<24}{'CAGR':>10}{'Sharpe':>9}{'DD':>9}")
    nets = {}
    for name, fn in variants.items():
        net = port_net(fn)
        nets[name] = net
        st = stats(net)
        print(f"{name:<24}{st['cagr']:>9.1f}%{st['sharpe']:>9.2f}{st['dd']:>8.1f}%")

    print(f"\n   Correlazione fra i rendimenti giornalieri dei segnali:")
    keys = ["VWAP trimestrale", "media mobile 50g", "media mobile 100g"]
    cm = pd.concat([nets[k].rename(k) for k in keys], axis=1).corr()
    print(cm.round(3).to_string())

    # ============================================ 2. dopo le imposte
    print(f"\n{'='*78}")
    print("2. COSA RESTA DOPO LE IMPOSTE IRLANDESI")
    print("=" * 78)
    rf = pd.Series(0.0, index=common)
    print(f"{'segnale':<24}{'op/anno':>9}{'IRR 33%':>10}{'IRR 52%':>10}"
          f"{'vs B&H 33%':>12}{'vs B&H 52%':>12}")
    base33 = base52 = None
    for name in ("buy&hold", "VWAP trimestrale", "VWAP mensile",
                 "media mobile 100g"):
        net = nets[name]
        # turnover del portafoglio: media dei turnover dei singoli asset
        turns = []
        for s, df in data.items():
            pos = variants[name](df)
            turns.append(pos.diff().abs().fillna(pos.abs()).reindex(common))
        tn = pd.concat(turns, axis=1).mean(axis=1).fillna(0.0)
        ops = float((tn > 0).sum()) / (len(common) / 365)
        r33 = simulate_pac(net, CGT_SHARES, rf=rf, realize_frac=tn,
                           periods_per_year=365)
        r52 = simulate_pac(net, TRADING_52, rf=rf, realize_frac=tn,
                           periods_per_year=365)
        if name == "buy&hold":
            base33, base52 = r33.irr_annual, r52.irr_annual
        print(f"{name:<24}{ops:>9.0f}{r33.irr_annual:>9.1f}%{r52.irr_annual:>9.1f}%"
              f"{r33.irr_annual-base33:>+11.1f}%{r52.irr_annual-base52:>+11.1f}%")

    # ============================================ 3. sopravvivenza
    print(f"\n{'='*78}")
    print("3. QUANTO PESA LA SOPRAVVIVENZA")
    print("=" * 78)
    print("   Il campione contiene solo cripto vive nel 2026. Non posso")
    print("   ricostruire le morte, ma posso misurare quanto il risultato")
    print("   dipende dai vincitori: rimuovo un asset per volta.\n")
    print(f"{'escluso':<12}{'B&H CAGR':>11}{'VWAP-Q CAGR':>13}{'differenza':>12}")
    full_bh = stats(port_net(variants["buy&hold"]))["cagr"]
    full_v = stats(port_net(variants["VWAP trimestrale"]))["cagr"]
    print(f"{'nessuno':<12}{full_bh:>10.1f}%{full_v:>12.1f}%"
          f"{full_v-full_bh:>+11.1f}%")
    for drop in list(data):
        sub = {k: v for k, v in data.items() if k != drop}
        saved = dict(data)
        data.clear(); data.update(sub)
        b = stats(port_net(variants["buy&hold"]))["cagr"]
        v = stats(port_net(variants["VWAP trimestrale"]))["cagr"]
        data.clear(); data.update(saved)
        print(f"{drop:<12}{b:>10.1f}%{v:>12.1f}%{v-b:>+11.1f}%")

    # ============================================ DSR
    print(f"\n{'='*78}")
    n_cum = lab.n_trials_so_far()
    reg = lab.load_registry()
    sh = pd.to_numeric(reg[reg["round"] == 19]["sharpe"], errors="coerce").dropna()
    vsr = float((sh / np.sqrt(365)).var(ddof=1)) if len(sh) > 2 else None
    d = lab.deflated_sharpe(nets["VWAP trimestrale"], n_cum, var_sr=vsr,
                            round_id=19)
    print(f"Deflated Sharpe del VWAP trimestrale su {n_cum} tentativi cumulati:")
    print(f"  Sharpe osservato {d['sr_period']*np.sqrt(365):.3f} annualizzato")
    print(f"  soglia H0        {d['sr0']*np.sqrt(365):.3f}")
    print(f"  DSR              {d['dsr']:.3f}  -> "
          f"{'PROMUOVIBILE' if d['dsr'] > 0.95 else 'NON promuovibile'}")

    lab.log_trials([dict(round=ROUND, hypothesis="H21 controlli sul risultato crypto",
                         config=name, window="2020-2026",
                         sharpe=stats(nets[name])["sharpe"],
                         irr=stats(nets[name])["cagr"], bh_irr=full_bh,
                         excess=stats(nets[name])["cagr"] - full_bh,
                         n_obs=len(common), note="portafoglio equipesato")
                    for name in nets])
    print(f"\nTentativi cumulati: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

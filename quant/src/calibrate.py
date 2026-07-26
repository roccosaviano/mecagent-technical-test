"""Gate di correttezza. Riproduce i due numeri di riferimento dichiarati
dall'utente sul buy&hold Shiller 1990-2023 prima di passare al resto."""
import sys
import pandas as pd

import dataio
import config as C
from tax import simulate_pac, CGT_SHARES, ETF_UCITS


def window(df, start=C.CALIB_START, end=C.CALIB_END):
    return df.loc[start:end]


def run():
    sh = window(dataio.shiller_monthly())
    price_ret = sh["price"].pct_change().fillna(0.0)
    div_m = sh["div_yield_m"].fillna(0.0)
    total_ret = sh["tr"].fillna(0.0)
    ff = dataio.ff_factors_monthly()
    rf = window(ff)["RF"]

    print(f"Finestra Shiller: {sh.index[0].date()} -> {sh.index[-1].date()}  ({len(sh)} mesi)")
    ann_tr = (1 + total_ret).prod() ** (12 / len(total_ret)) - 1
    ann_pr = (1 + price_ret).prod() ** (12 / len(price_ret)) - 1
    print(f"Rendimento totale lordo annuo : {ann_tr*100:6.2f}%")
    print(f"Solo prezzo, lordo annuo      : {ann_pr*100:6.2f}%")
    print(f"Dividend yield medio annuo    : {(ann_tr-ann_pr)*100:6.2f}%\n")

    # Il benchmark e' definito dall'utente come "CGT 33% solo all'uscita": il
    # rendimento e' quello TOTALE e i dividendi non subiscono prelievo annuo.
    # La variante con dividendi al 52% e' cio' che accade davvero detenendo
    # azioni USA da residente irlandese, e la riporto separatamente.
    bench = simulate_pac(total_ret, CGT_SHARES, rf=rf)
    real_eq = simulate_pac(price_ret, CGT_SHARES, div_yield=div_m, rf=rf)
    etf = simulate_pac(total_ret, ETF_UCITS, rf=rf)

    rows = [
        ("BENCHMARK indice buy&hold, CGT 33% solo all'uscita",
         bench, C.REF_BH_EQUITY_IRR),
        ("ETF UCITS buy&hold, exit tax + deemed disposal 8 anni",
         etf, C.REF_BH_ETF_IRR),
    ]
    print(f"{'':<62}{'IRR netta':>11}{'atteso':>9}{'delta':>8}{'max DD':>9}{'montante':>12}")
    ok = True
    for name, r, ref in rows:
        d = r.irr_annual - ref
        flag = "OK" if abs(d) <= C.REF_TOLERANCE else "FUORI TOLLERANZA"
        ok &= abs(d) <= C.REF_TOLERANCE
        print(f"{name:<62}{r.irr_annual:>10.2f}%{ref:>8.2f}%{d:>+8.2f}"
              f"{r.max_dd:>8.1f}%{r.final_net:>12,.0f}  {flag}")
    print(f"\nDD atteso azioni: {C.REF_BH_EQUITY_DD:.0f}%   "
          f"versato totale: {bench.contributions:,.0f} EUR")
    print(f"Imposte pagate  benchmark {bench.taxes:>11,.0f}   ETF {etf.taxes:>11,.0f}")
    print(f"\nVariante realistica azioni diritte (dividendi esteri tassati "
          f"{C.__dict__.get('DIV_RATE_FOREIGN', 0.52)*100:.0f}% ogni anno):")
    print(f"  IRR netta {real_eq.irr_annual:.2f}%  -> il prelievo annuo sui dividendi "
          f"costa {bench.irr_annual - real_eq.irr_annual:.2f} punti l'anno")
    return ok


if __name__ == "__main__":
    sys.exit(0 if run() else 1)

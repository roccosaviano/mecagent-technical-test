"""Gruppo C: benchmark passivi e trend following mensile."""
import numpy as np
import pandas as pd

import dataio
import config as C


def trend_signal(price, months=10):
    """Prezzo sopra la media a 10 mesi. shift(1): la decisione usa la chiusura
    del mese precedente e l'esecuzione avviene nel mese corrente."""
    ma = price.rolling(months).mean()
    return (price > ma).astype(float).shift(1).fillna(0.0)


def levered_return(total_ret, pos, lev, rf):
    """Rendimento con leva. La parte a prestito costa benchmark + spread.
    Il costo si paga solo quando si e' investiti."""
    fin_rate = (rf + C.FIN_SPREAD / 12.0)
    borrowed = max(lev - 1.0, 0.0)
    return pos * total_ret * lev - borrowed * fin_rate * pos


def build(window_start=C.CALIB_START, window_end=C.CALIB_END):
    """Restituisce i mattoni del gruppo C sulla finestra richiesta."""
    sh = dataio.shiller_monthly().loc[window_start:window_end]
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(sh.index).ffill().fillna(0.0)

    # il segnale va calcolato sulla serie intera e poi affettato, altrimenti si
    # perdono i primi 10 mesi della finestra
    full = dataio.shiller_monthly()
    sig_full = trend_signal(full["price"], 10)
    sig = sig_full.reindex(sh.index).fillna(0.0)

    return dict(
        index=sh.index,
        price_ret=sh["price"].pct_change().fillna(0.0),
        div_m=sh["div_yield_m"].fillna(0.0),
        total_ret=sh["tr"].fillna(0.0),
        rf=rf,
        trend_pos=sig,
    )

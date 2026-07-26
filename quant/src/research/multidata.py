"""Fonti multi-asset per la ricerca. Solo dati reali, nessuna simulazione."""
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[2] / "data"


def _aqr(fname, sheet):
    raw = pd.read_excel(DATA / fname, sheet_name=sheet, header=None, nrows=40)
    # l'header e' la riga sopra la prima riga di dati. Non cerco la parola
    # "DATE": in TSMOM la cella dell'indice e' vuota.
    first_data = next(i for i in raw.index
                      if pd.notna(pd.to_datetime(raw.iloc[i, 0], errors="coerce")))
    hdr = first_data - 1
    df = pd.read_excel(DATA / fname, sheet_name=sheet, skiprows=hdr)
    df.columns = [str(c).strip() for c in df.columns]
    first = df.columns[0]
    df[first] = pd.to_datetime(df[first], errors="coerce")
    df = df.dropna(subset=[first]).set_index(first)
    df.index = df.index.to_period("M").to_timestamp("M")
    return df.apply(pd.to_numeric, errors="coerce")


def century():
    """AQR Century of Factor Premia: 6 classi di asset x 4-5 stili, 1926-2026.
    Sono rendimenti long-short in eccesso, gia' al netto di costi stimati da AQR
    ma NON dei costi retail e NON delle imposte."""
    return _aqr("aqr_century.xlsx", "Century of Factor Premia")


def vme():
    """Value and Momentum Everywhere (Asness-Moskowitz-Pedersen), 1972-2026."""
    return _aqr("aqr_vme.xlsx", "VME Factors")


def tsmom():
    """Time Series Momentum (Moskowitz-Ooi-Pedersen): trend following su futures."""
    return _aqr("aqr_tsmom.xlsx", "TSMOM Factors")


def ff_region(name):
    """Fattori regionali di Ken French (Developed, Emerging, Europe, Japan, ...)."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import dataio
    p = DATA / name / f"{name}.csv"
    if not p.exists():
        cands = list((DATA / name).glob("*.csv"))
        if not cands:
            raise FileNotFoundError(f"{name} non scaricato")
        p = cands[0]
    s = dataio._ff_sections(p)
    for df in s.values():
        if len(df.index[0]) == 6:
            out = dataio._to_period_index(df) / 100.0
            out.columns = [c.strip() for c in out.columns]
            return out
    raise RuntimeError(f"sezione mensile non trovata in {name}")


def fred(series_id):
    """Serie FRED. Non richiede API key sull'endpoint fredgraph."""
    p = DATA / f"fred_{series_id}.csv"
    if not p.exists():
        raise FileNotFoundError(f"manca {p}; scaricala con fetch_data.sh")
    d = pd.read_csv(p)
    d.columns = [c.strip() for c in d.columns]
    dc, vc = d.columns[0], d.columns[1]
    d[dc] = pd.to_datetime(d[dc], errors="coerce")
    d[vc] = pd.to_numeric(d[vc], errors="coerce")
    return d.dropna().set_index(dc)[vc]


def bond_total_return_monthly():
    """Rendimento totale mensile approssimato di un decennale, da DGS10.

    Approssimazione a duration costante: r = y/12 + D*(y_prev - y) con D~8,5.
    NON e' un indice obbligazionario vero: e' una ricostruzione da rendimenti a
    scadenza, e sottostima convessita' e rolldown. La uso solo come asset
    decorrelato, non come strumento investibile per se'.
    """
    y = fred("DGS10").resample("ME").last() / 100.0
    dur = 8.5
    return (y.shift(1) / 12.0 - dur * y.diff()).dropna()

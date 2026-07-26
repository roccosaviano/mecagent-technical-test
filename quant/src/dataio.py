"""Caricamento delle fonti dati. Ogni loader restituisce dati grezzi verificati,
senza riempimenti e senza sostituzioni: se una fonte manca, il chiamante lo sa."""
from pathlib import Path
import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"
MISSING = (-99.99, -999)


# ------------------------------------------------------------------ Ken French
def _ff_sections(path):
    """Spezza un CSV di Ken French nelle sue sezioni.

    Il formato e': righe di intestazione libera, poi blocchi separati da riga vuota.
    Ogni blocco inizia con un titolo (riga senza virgole) oppure direttamente con
    l'header delle colonne. Restituisce {titolo: DataFrame}.
    """
    raw = path.read_text(errors="replace").replace("\r\n", "\n").splitlines()
    blocks, cur, title = [], [], None
    for line in raw:
        line = line.rstrip("\r")
        # alcuni file French "riempiono" le righe vuote con virgole: ',,' e' vuota
        if not line.strip().strip(","):
            if cur:
                blocks.append((title, cur))
                cur, title = [], None
            continue
        # una riga di solo testo senza virgole e' un titolo di sezione
        if "," not in line:
            if cur:
                blocks.append((title, cur))
                cur = []
            title = line.strip()
            continue
        cur.append(line)
    if cur:
        blocks.append((title, cur))

    out, unnamed = {}, 0
    for t, lines in blocks:
        # scarto i blocchi di prosa (copyright, note) che non hanno un header di colonne
        head = lines[0]
        if not head.startswith(","):
            continue
        body = [l for l in lines[1:] if l.split(",")[0].strip().isdigit()]
        if not body:
            continue
        cols = [c.strip() for c in head.split(",")][1:]
        keep = [i for i, c in enumerate(cols) if c != ""]   # scarta colonne fantasma
        cols = [cols[i] for i in keep]
        idx, vals = [], []
        for l in body:
            parts = l.split(",")[1:]
            idx.append(l.split(",")[0].strip())
            vals.append([float(parts[i]) if i < len(parts) and parts[i].strip() not in ("", "nan")
                         else np.nan for i in keep])
        df = pd.DataFrame(vals, index=idx, columns=cols)
        if t is None:
            unnamed += 1
            t = f"section_{unnamed}"
        out[t] = df
    return out


def _to_period_index(df):
    """Converte l'indice testuale di French in DatetimeIndex di fine periodo."""
    n = len(df.index[0])
    if n == 8:      # AAAAMMGG
        idx = pd.to_datetime(df.index, format="%Y%m%d")
    elif n == 6:    # AAAAMM -> fine mese
        idx = pd.PeriodIndex(df.index, freq="M").to_timestamp("M")
    elif n == 4:    # AAAA -> fine anno
        idx = pd.PeriodIndex(df.index, freq="Y").to_timestamp("Y")
    else:
        raise ValueError(f"indice French non riconosciuto: {df.index[0]!r}")
    out = df.copy()
    out.index = idx
    return out.replace(list(MISSING), np.nan)


def ff_factors_daily():
    p = DATA / "F-F_Research_Data_Factors_daily_CSV/F-F_Research_Data_Factors_daily.csv"
    s = _ff_sections(p)
    df = _to_period_index(list(s.values())[0]) / 100.0
    df.columns = [c.strip() for c in df.columns]
    return df


def ff_factors_monthly():
    p = DATA / "F-F_Research_Data_Factors_CSV/F-F_Research_Data_Factors.csv"
    s = _ff_sections(p)
    # la prima sezione e' mensile, la seconda annuale: prendo quella con indice a 6 cifre
    for df in s.values():
        if len(df.index[0]) == 6:
            out = _to_period_index(df) / 100.0
            out.columns = [c.strip() for c in out.columns]
            return out
    raise RuntimeError("sezione mensile non trovata nei fattori FF")


def ff_mom_daily():
    p = DATA / "F-F_Momentum_Factor_daily_CSV/F-F_Momentum_Factor_daily.csv"
    df = _to_period_index(list(_ff_sections(p).values())[0]) / 100.0
    df.columns = [c.strip() for c in df.columns]
    return df


def ff_ind49_daily():
    """Rendimenti giornalieri value-weighted delle 49 industrie."""
    p = DATA / "49_Industry_Portfolios_daily_CSV/49_Industry_Portfolios_Daily.csv"
    s = _ff_sections(p)
    key = next(k for k in s if "Value Weighted" in (k or ""))
    df = _to_period_index(s[key]) / 100.0
    df.columns = [c.strip() for c in df.columns]
    return df


def ff_ind49_monthly():
    """Restituisce (ret_vw, ret_ew, n_firms, avg_size) mensili per le 49 industrie.

    n_firms * avg_size da' la capitalizzazione totale di ogni industria: e' la
    fonte dei pesi di mercato mu_i usati nel gruppo D. Sono dati CRSP reali,
    non una ricostruzione.
    """
    p = DATA / "49_Industry_Portfolios_CSV/49_Industry_Portfolios.csv"
    s = _ff_sections(p)

    def pick(pattern, monthly=True):
        for k, df in s.items():
            if k and pattern in k and (len(df.index[0]) == 6) == monthly:
                return _to_period_index(df)
        raise KeyError(pattern)

    vw = pick("Average Value Weighted Returns") / 100.0
    ew = pick("Average Equal Weighted Returns") / 100.0
    nf = pick("Number of Firms")
    sz = pick("Average Firm Size")
    for d in (vw, ew, nf, sz):
        d.columns = [c.strip() for c in d.columns]
    return vw, ew, nf, sz


def ff_size_deciles_monthly():
    p = DATA / "Portfolios_Formed_on_ME_CSV/Portfolios_Formed_on_ME.csv"
    s = _ff_sections(p)
    key = next(k for k in s if k and "Value Weight" in k and len(s[k].index[0]) == 6)
    df = _to_period_index(s[key]) / 100.0
    df.columns = [c.strip() for c in df.columns]
    return df


# ------------------------------------------------------------------ Shiller
def shiller_monthly():
    """S&P Composite mensile da Robert Shiller.

    Colonne restituite: price (P), div_annual (D, dividendo annualizzato),
    cpi, gs10, tr (rendimento totale nominale mensile),
    div_yield_m (quota di rendimento da dividendo nel mese).
    Il rendimento totale e' (P_t + D_t/12)/P_(t-1) - 1: e' la convenzione di
    Shiller, il dividendo D e' annualizzato e va diviso per 12.
    """
    d = pd.read_excel(DATA / "ie_data.xls", sheet_name="Data", header=None, skiprows=8)
    d = d.iloc[:, :8]
    d.columns = ["date", "P", "D", "E", "CPI", "frac", "GS10", "RealP"]
    d = d[pd.to_numeric(d["date"], errors="coerce").notna()].copy()
    d["date"] = d["date"].astype(float)
    # 1871.01 -> anno 1871 mese 1. Attenzione: 1871.10 e' ottobre, non gennaio.
    yr = np.floor(d["date"] + 1e-9).astype(int)
    mo = np.round((d["date"] - yr) * 100).astype(int)
    ok = (mo >= 1) & (mo <= 12)
    d, yr, mo = d[ok], yr[ok], mo[ok]
    stamp = [f"{y:04d}-{m:02d}" for y, m in zip(yr, mo)]
    d.index = pd.PeriodIndex(stamp, freq="M").to_timestamp("M")
    d = d[["P", "D", "E", "CPI", "GS10"]].apply(pd.to_numeric, errors="coerce").dropna(subset=["P"])

    p, dv = d["P"], d["D"]
    tr = (p + dv / 12.0) / p.shift(1) - 1.0
    div_part = (dv / 12.0) / p.shift(1)
    out = pd.DataFrame({
        "price": p, "div_annual": dv, "cpi": d["CPI"], "gs10": d["GS10"] / 100.0,
        "tr": tr, "div_yield_m": div_part,
    }).dropna(subset=["tr"])
    return out


# ------------------------------------------------------------------ AQR
def aqr_bab(country="USA"):
    """Serie mensile del fattore Betting Against Beta di AQR."""
    xl = pd.ExcelFile(DATA / "bab.xlsx")
    sheet = "BAB Factors"
    raw = pd.read_excel(xl, sheet_name=sheet, header=None)
    # l'header vero e' la riga che contiene 'DATE' in prima colonna (righe sopra: prosa)
    hrow = raw.index[raw.iloc[:, 0].astype(str).str.strip().str.upper() == "DATE"][0]
    df = pd.read_excel(xl, sheet_name=sheet, skiprows=hrow)
    df.columns = [str(c).strip() for c in df.columns]
    first = df.columns[0]
    df[first] = pd.to_datetime(df[first], errors="coerce")
    df = df.dropna(subset=[first]).set_index(first)
    df.index = df.index.to_period("M").to_timestamp("M")
    if country not in df.columns:
        raise KeyError(f"{country} non presente. Disponibili: {list(df.columns)[:12]}")
    return pd.to_numeric(df[country], errors="coerce").dropna()


# ------------------------------------------------------------------ OSAP
def osap_signaldoc():
    """Metadati Chen-Zimmermann: autori, anno di pubblicazione, giornale, campione."""
    df = pd.read_csv(DATA / "osap_signaldoc.csv")
    df.columns = [c.strip() for c in df.columns]
    return df.set_index("Acronym")


def osap_ls_wide():
    """Rendimenti mensili long-short (in %) di ogni anomalia replicata."""
    df = pd.read_csv(DATA / "osap_ls_wide.csv", parse_dates=["date"])
    df = df.set_index("date")
    df.index = df.index.to_period("M").to_timestamp("M")
    return df / 100.0


def osap_ports(signals):
    """Rendimenti dei portafogli decile per i segnali richiesti (file da 78 MB)."""
    keep = set(signals)
    chunks = []
    for ch in pd.read_csv(DATA / "osap_ports.csv", chunksize=500_000):
        chunks.append(ch[ch["signalname"].isin(keep)])
    df = pd.concat(chunks)
    df["date"] = pd.to_datetime(df["date"]).dt.to_period("M").dt.to_timestamp("M")
    return df


# ------------------------------------------------------------------ diagnostica
def inventory():
    """Verifica che ogni fonte carichi e stampa copertura ed estremi."""
    rows = []
    checks = {
        "FF factors daily": ff_factors_daily,
        "FF factors monthly": ff_factors_monthly,
        "FF momentum daily": ff_mom_daily,
        "FF 49 industry daily": ff_ind49_daily,
        "FF size deciles monthly": ff_size_deciles_monthly,
        "Shiller monthly": shiller_monthly,
        "AQR BAB USA": lambda: aqr_bab("USA").to_frame("BAB"),
        "OSAP long-short": osap_ls_wide,
        "OSAP signaldoc": osap_signaldoc,
    }
    for name, fn in checks.items():
        try:
            df = fn()
            span = (f"{df.index[0]} -> {df.index[-1]}"
                    if isinstance(df.index, pd.DatetimeIndex) else f"{len(df)} righe")
            rows.append((name, "ok", df.shape, span))
        except Exception as e:
            rows.append((name, f"FALLITO: {type(e).__name__}: {e}", None, ""))
    try:
        vw, ew, nf, sz = ff_ind49_monthly()
        rows.append(("FF 49 industry monthly (vw/ew/n/size)", "ok", vw.shape,
                     f"{vw.index[0].date()} -> {vw.index[-1].date()}"))
    except Exception as e:
        rows.append(("FF 49 industry monthly", f"FALLITO: {e}", None, ""))
    return rows


if __name__ == "__main__":
    for name, status, shape, span in inventory():
        print(f"{name:<40} {str(status):<28} {str(shape):<14} {span}")

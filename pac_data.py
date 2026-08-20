"""
SCARICO E CACHE DEI DATI PER LO STUDIO PAC
==========================================
Uso:  python3 pac_data.py          (riscarica tutto in data/)

COSA SCARICA E PERCHE'

1) Fattori giornalieri Fama-French + momentum (Ken French Data Library, dal 1926)
   - Mkt-RF : rendimento TOTALE (dividendi inclusi) del mercato azionario USA
              in eccesso rispetto al T-bill
   - RF     : T-bill a 1 mese, giornaliero -> serve sia come tasso privo di rischio
              sia come costo di finanziamento della leva
   - MOM    : fattore momentum long/short
   Sono la spina dorsale dello studio: cento anni di dati totali (non solo prezzo)
   gia' puliti, gratuiti e citabili. Senza questi, per SPXL avremmo solo il
   2008-oggi, cioe' il miglior mercato toro della storia: campione inutile.

2) Prezzi giornalieri reali di SPY, SPMO, SPXL (API Nasdaq, ultimi 10 anni)
   Servono a CALIBRARE e a VALIDARE le serie ricostruite, non a fare lo studio.

NOTA SUI DIVIDENDI: l'API Nasdaq da' prezzi non aggiustati. I dividendi vengono
riaggiunti come rateo costante (vedi YIELD in pac_lab.py) usando il rendimento da
distribuzione dichiarato dai tre ETF. E' un'approssimazione: sposta il livello dei
rendimenti di ~1%/anno, non la struttura. Conta solo per la calibrazione.
"""
import io
import os
import zipfile

import pandas as pd
import requests

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
      "Accept": "application/json, text/plain, */*"}
FF_BASE = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"


def _ff_zip(name):
    r = requests.get(FF_BASE + name, headers={"User-Agent": UA["User-Agent"]}, timeout=120)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    return z.read(z.namelist()[0]).decode("latin-1").splitlines()


def fetch_factors():
    """Mkt-RF, SMB, HML, RF, MOM giornalieri in forma decimale (0.01 = +1%)."""
    txt = _ff_zip("F-F_Research_Data_Factors_daily_CSV.zip")
    rows = [l for l in txt if l[:8].strip().isdigit() and l.count(",") == 4]
    ff = pd.read_csv(io.StringIO("\n".join(rows)), header=None,
                     names=["date", "MktRF", "SMB", "HML", "RF"])

    txt = _ff_zip("F-F_Momentum_Factor_daily_CSV.zip")
    rows = [l for l in txt if l[:8].strip().isdigit() and l.count(",") == 1]
    mom = pd.read_csv(io.StringIO("\n".join(rows)), header=None, names=["date", "MOM"])

    df = ff.merge(mom, on="date", how="inner")
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    df = df.set_index("date").sort_index()
    return df / 100.0


def fetch_prices(tickers=("SPY", "SPMO", "SPXL")):
    """Chiusure giornaliere non aggiustate (l'API copre ~10 anni)."""
    out = {}
    for t in tickers:
        r = requests.get(f"https://api.nasdaq.com/api/quote/{t}/historical",
                         params={"assetclass": "etf", "fromdate": "1990-01-01",
                                 "limit": "99999", "todate": pd.Timestamp.today().strftime("%Y-%m-%d")},
                         headers=UA, timeout=120)
        r.raise_for_status()
        rows = r.json()["data"]["tradesTable"]["rows"]
        num = lambda s: float(str(s).replace("$", "").replace(",", ""))
        s = pd.Series({pd.Timestamp(x["date"]): num(x["close"]) for x in rows}).sort_index()
        out[t] = s
    return pd.DataFrame(out)


def fetch_cpi():
    """Indice prezzi al consumo USA, mensile, dal 1913 (FRED, serie CPIAUCNS).

    Serve a leggere i montanti in potere d'acquisto: 100 anni di rendimenti
    nominali contengono ~3%/anno di inflazione media, ignorarla gonfia tutto.
    """
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                     params={"id": "CPIAUCNS"}, headers={"User-Agent": UA["User-Agent"]}, timeout=120)
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))
    d.columns = ["date", "CPI"]
    d["date"] = pd.to_datetime(d["date"])
    d["CPI"] = pd.to_numeric(d["CPI"], errors="coerce")
    return d.set_index("date").dropna()


def fetch_eurusd():
    """Dollari per euro, giornaliero, dal 1999 (FRED, serie DEXUSEU)."""
    r = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                     params={"id": "DEXUSEU"}, headers={"User-Agent": UA["User-Agent"]}, timeout=120)
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))
    d.columns = ["date", "USD_per_EUR"]
    d["date"] = pd.to_datetime(d["date"])
    d["USD_per_EUR"] = pd.to_numeric(d["USD_per_EUR"], errors="coerce")
    return d.set_index("date").dropna()


def main():
    os.makedirs(DATA, exist_ok=True)
    ff = fetch_factors()
    ff.round(6).to_csv(os.path.join(DATA, "ff_daily.csv.gz"))
    print(f"fattori   {len(ff):6d} giorni  {ff.index[0].date()} -> {ff.index[-1].date()}")

    px = fetch_prices()
    px.round(4).to_csv(os.path.join(DATA, "etf_daily.csv.gz"))
    for c in px:
        s = px[c].dropna()
        print(f"{c:9s} {len(s):6d} giorni  {s.index[0].date()} -> {s.index[-1].date()}")

    cpi = fetch_cpi()
    cpi.round(4).to_csv(os.path.join(DATA, "cpi_monthly.csv.gz"))
    print(f"CPI       {len(cpi):6d} mesi    {cpi.index[0].date()} -> {cpi.index[-1].date()}")

    fx = fetch_eurusd()
    fx.round(6).to_csv(os.path.join(DATA, "eurusd_daily.csv.gz"))
    print(f"EURUSD    {len(fx):6d} giorni  {fx.index[0].date()} -> {fx.index[-1].date()}")


if __name__ == "__main__":
    main()

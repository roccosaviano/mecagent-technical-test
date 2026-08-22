"""
RACCOLTA DATI
=============

Ogni serie ha una cascata di provider e si prende il primo che risponde.
Non e' pignoleria: in questa sessione Yahoo limita per indirizzo IP condiviso e
puo' restare chiuso per ore, mentre FRED e i file grezzi su GitHub passano
sempre. Senza cascata la ricerca si fermerebbe per un motivo che non ha niente
a che fare con la finanza.

Chi serve cosa:

  indice S&P 500 giornaliero dal 1927
      Il file SP500.csv del repo fja05680/dow-sp500-100-years e' un export di
      Yahoo che arriva al 2019; la serie SP500 di FRED copre gli ultimi dieci
      anni. Si sovrappongono dal 2016 al 2019, quindi la giunta si puo'
      VERIFICARE invece di sperare che vada bene, e la verifica viene stampata.

  dividendi storici
      Il dataset Shiller (mensile dal 1871) da' il dividendo dell'indice: serve
      a costruire il rendimento TOTALE prima del 1988, quando l'indice total
      return ufficiale non esiste. Senza, il buy&hold verrebbe sottostimato di
      tre o quattro punti l'anno e il confronto sarebbe falsato a favore delle
      strategie attive.

  VIX e VIX a 3 mesi
      FRED li pubblica entrambi: VIXCLS dal 1990, VXVCLS dal 2007.

  ETF a leva
      Yahoo quando risponde, altrimenti Nasdaq: ultimi dieci anni e senza
      aggiustamento per i dividendi, sufficiente a calibrare il costo della
      leva ma non a farci sopra un backtest lungo.

  tassi a breve
      FRED: DFF dal 1954, DTB3 dal 1954, DGS10 dal 1962.

Lo script e' RIPARTIBILE: salta cio' che ha gia' in data/. Con --force riscarica.
"""
import io
import json
import os
import subprocess
import sys
import time
import urllib.parse

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
PAUSA_YAHOO = 90
COLS = ["Date", "Open", "High", "Low", "Close", "Volume", "AdjClose"]

GITHUB_SP500 = ("https://raw.githubusercontent.com/fja05680/dow-sp500-100-years/"
                "master/SP500.csv")
GITHUB_SHILLER = ("https://raw.githubusercontent.com/datasets/s-and-p-500/"
                  "main/data/data.csv")


# ==========================================================================
# trasporto
# ==========================================================================
def _curl(url, tries=2, pausa=20, ua=True):
    """
    Si scarica con curl e non con urllib perche' dietro il proxy di questa
    sessione urllib resta appeso su alcuni host.

    Il parametro ua non e' un dettaglio: Yahoo risponde 429 a chi non manda uno
    User-Agent da browser, FRED chiude la connessione a chi ne manda uno.
    """
    for k in range(tries):
        cmd = ["curl", "-sS", "--max-time", "180", "-w", "\\n%{http_code}"]
        if ua:
            cmd += ["-H", f"User-Agent: {UA}"]
        p = subprocess.run(cmd + [url], capture_output=True)
        body, _, code = p.stdout.rpartition(b"\n")
        code = code.decode().strip()
        if code == "200" and body:
            return body
        if k == tries - 1:
            raise RuntimeError(f"HTTP {code or 'errore'}: {p.stderr.decode()[:60]}")
        time.sleep(pausa)


# ==========================================================================
# provider
# ==========================================================================
def p_fred(series, tries=3):
    """Serie giornaliera di FRED. I giorni di chiusura sono marcati '.'."""
    raw = _curl(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}",
                tries=tries, pausa=10, ua=False)
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = ["Date", "value"]
    df["Date"] = pd.to_datetime(df["Date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna()


def p_yahoo(ticker):
    """
    Storico completo da Yahoo. period1 deve essere un epoch NEGATIVO: con 0 si
    partirebbe dal 1970 e si perderebbero quarant'anni di indice.
    """
    url = ("https://query2.finance.yahoo.com/v8/finance/chart/"
           f"{urllib.parse.quote(ticker)}?period1=-2208988800&period2=9999999999"
           "&interval=1d")
    res = json.loads(_curl(url, tries=2, pausa=PAUSA_YAHOO))["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    ts = pd.to_datetime(res["timestamp"], unit="s", utc=True)
    df = pd.DataFrame({
        "Date":  ts.tz_convert("America/New_York").normalize().tz_localize(None),
        "Open":  q["open"], "High": q["high"], "Low": q["low"],
        "Close": q["close"], "Volume": q.get("volume"),
    })
    adj = res["indicators"].get("adjclose")
    # AdjClose incorpora dividendi e frazionamenti: e' la serie del rendimento
    # totale. Sugli indici coincide con Close.
    df["AdjClose"] = adj[0]["adjclose"] if adj else q["close"]
    return df.dropna(subset=["Close"]).drop_duplicates("Date").sort_values("Date")[COLS]


def p_nasdaq(ticker, kind="etf"):
    """
    Ripiego per gli ETF. Copre solo gli ultimi dieci anni e NON corregge per i
    dividendi: basta a calibrare il costo della leva, non a fare backtest lunghi.
    """
    url = (f"https://api.nasdaq.com/api/quote/{ticker}/historical"
           f"?assetclass={kind}&fromdate=1990-01-01&todate=2030-01-01&limit=99999")
    rows = json.loads(_curl(url, tries=3, pausa=15))["data"]["tradesTable"]["rows"]
    df = pd.DataFrame(rows)
    for src, dst in (("open", "Open"), ("high", "High"), ("low", "Low"), ("close", "Close")):
        df[dst] = pd.to_numeric(df[src].astype(str).str.replace("$", "", regex=False),
                                errors="coerce")
    df["Date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
    df["Volume"] = pd.to_numeric(df["volume"].astype(str).str.replace(",", "", regex=False),
                                 errors="coerce")
    df["AdjClose"] = df["Close"]      # nessun aggiustamento disponibile qui
    return df.dropna(subset=["Close"]).drop_duplicates("Date").sort_values("Date")[COLS]


def p_github(url):
    return pd.read_csv(io.BytesIO(_curl(url, tries=3, pausa=10, ua=False)))


# ==========================================================================
# serie composte
# ==========================================================================
def build_gspc():
    """
    Indice S&P 500 giornaliero, il piu' lungo che si riesca a mettere insieme.

    Prima si prova Yahoo, che darebbe tutto in un colpo solo e con OHLC.
    Se non risponde si incolla l'export storico su GitHub (1927-2019) con la
    serie FRED (2016-2026), CONTROLLANDO la sovrapposizione: se i due pezzi non
    coincidono nel periodo comune la giunta e' sbagliata e ci si ferma, invece
    di costruire in silenzio una serie che non esiste.
    """
    try:
        df = p_yahoo("^GSPC")
        if len(df) > 20000:
            print("      indice preso da Yahoo (storia completa)", flush=True)
            return df
        print(f"      Yahoo ha dato solo {len(df)} sedute, passo alla giunta", flush=True)
    except Exception as e:
        print(f"      Yahoo non risponde ({str(e)[:50]}), passo alla giunta", flush=True)

    old = p_github(GITHUB_SP500)
    old["Date"] = pd.to_datetime(old["Date"])
    old = old.rename(columns={"Adj Close": "AdjClose"})[COLS].sort_values("Date")

    new = p_fred("SP500").rename(columns={"value": "Close"})
    for c in ("Open", "High", "Low", "AdjClose"):
        new[c] = new["Close"]
    new["Volume"] = 0.0
    new = new[COLS]

    a = old.set_index("Date")["Close"]
    b = new.set_index("Date")["Close"]
    comune = a.index.intersection(b.index)
    if len(comune) < 100:
        raise RuntimeError(f"sovrapposizione troppo corta ({len(comune)} sedute)")
    err = (a.loc[comune] / b.loc[comune] - 1).abs()
    print(f"      giunta verificata su {len(comune)} sedute comuni: "
          f"scarto medio {err.mean():.2e}, massimo {err.max():.2e}", flush=True)
    if err.max() > 0.01:
        raise RuntimeError("le due fonti dell'indice non coincidono, giunta rifiutata")

    taglio = a.index.max()
    df = pd.concat([old[old.Date <= taglio], new[new.Date > taglio]], ignore_index=True)
    print(f"      GitHub fino al {taglio.date()}, poi FRED", flush=True)
    return df.drop_duplicates("Date").sort_values("Date")


def build_dividends():
    """
    Dividendo dell'indice dal dataset Shiller (mensile dal 1871), convertito in
    rendimento da dividendi. Serve a ricostruire il total return prima del 1988.
    """
    df = p_github(GITHUB_SHILLER)
    df["Date"] = pd.to_datetime(df["Date"].astype(str), format="mixed")
    df = df[["Date", "SP500", "Dividend"]].dropna()
    df["yield"] = df["Dividend"] / df["SP500"]     # il dividendo Shiller e' gia' annuo
    # Nel file gli ultimi mesi hanno dividendo zero: non e' che le societa'
    # abbiano smesso di distribuire, e' che il dato non e' ancora pubblicato.
    # Uno zero preso alla lettera azzererebbe il total return del buy&hold
    # sull'ultimo tratto, cioe' proprio dove il confronto conta di piu'.
    df = df[df["yield"] > 0]
    return df[["Date", "yield"]]


def _fred_px(series):
    """Serie FRED presentata nel formato prezzi, per usarla come le altre."""
    df = p_fred(series).rename(columns={"value": "Close"})
    for c in ("Open", "High", "Low", "AdjClose"):
        df[c] = df["Close"]
    df["Volume"] = 0.0
    return df[COLS]


def _fred_col(series):
    df = p_fred(series)
    df.columns = ["Date", series]
    return df


def _etf(ticker):
    try:
        return p_yahoo(ticker)
    except Exception as e:
        print(f"      Yahoo ko su {ticker} ({str(e)[:40]}), provo Nasdaq", flush=True)
        return p_nasdaq(ticker)


def plan():
    return [
        ("gspc",     build_gspc,                  "indice S&P 500 giornaliero"),
        ("divyield", build_dividends,             "dividend yield storico (Shiller)"),
        ("vix",      lambda: _fred_px("VIXCLS"),  "VIX"),
        ("vix3m",    lambda: _fred_px("VXVCLS"),  "VIX a 3 mesi"),
        ("dff",      lambda: _fred_col("DFF"),    "fed funds effettivo"),
        ("dtb3",     lambda: _fred_col("DTB3"),   "T-bill 3 mesi"),
        ("dgs10",    lambda: _fred_col("DGS10"),  "Treasury 10 anni"),
        ("spxl",     lambda: _etf("SPXL"),        "Direxion Daily S&P500 Bull 3X"),
        ("spxs",     lambda: _etf("SPXS"),        "Direxion Daily S&P500 Bear 3X"),
        ("spy",      lambda: _etf("SPY"),         "ETF S&P 500"),
        ("upro",     lambda: _etf("UPRO"),        "ProShares UltraPro S&P500 3X"),
        ("sp500tr",  lambda: p_yahoo("^SP500TR"), "S&P 500 total return ufficiale"),
    ]


def main(force=False):
    os.makedirs(DATA, exist_ok=True)
    mancanti = []
    for nome, fn, descr in plan():
        path = os.path.join(DATA, f"{nome}.csv")
        if os.path.exists(path) and not force:
            print(f"  cache {nome}", flush=True)
            continue
        print(f"  ...   {nome}: {descr}", flush=True)
        try:
            df = fn()
            df.to_csv(path, index=False)
            print(f"  ok    {nome:9s} {len(df):6d} righe  "
                  f"{df.Date.iloc[0].date()} -> {df.Date.iloc[-1].date()}", flush=True)
        except Exception as e:
            mancanti.append(nome)
            print(f"  KO    {nome:9s} {type(e).__name__}: {str(e)[:90]}", flush=True)
    print(f"\nmancanti: {mancanti if mancanti else 'nessuno'}", flush=True)
    return len(mancanti)


if __name__ == "__main__":
    sys.exit(1 if main(force="--force" in sys.argv) else 0)

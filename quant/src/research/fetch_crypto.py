"""Scarica OHLCV giornaliero multi-asset crypto da OKX, con paginazione.

OKX espone /market/history-candles senza chiave, 100 candele per richiesta.
Si pagina all'indietro passando `after` = timestamp piu' vecchio ricevuto.
Nessuna registrazione, nessun limite di simboli come la demo di Twelve Data.
"""
import json
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request

import pandas as pd

DATA = Path(__file__).resolve().parents[2] / "data"
SYMBOLS = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT", "DOGE-USDT",
           "LTC-USDT", "ADA-USDT", "LINK-USDT",
           # oro tokenizzato: l'unico proxy investibile dell'oro che riesco a
           # ottenere. Storia corta e rischio di controparte dell'emittente,
           # ma e' un asset comprabile, a differenza degli indici FRED.
           "PAXG-USDT"]
BASE = "https://www.okx.com/api/v5/market/history-candles"


def fetch(inst, bar="1D", max_pages=60):
    rows, after = [], None
    for _ in range(max_pages):
        url = f"{BASE}?instId={inst}&bar={bar}&limit=100"
        if after:
            url += f"&after={after}"
        try:
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            d = json.loads(urlopen(req, timeout=30).read())
        except Exception as e:
            print(f"  {inst}: richiesta fallita ({type(e).__name__}), mi fermo")
            break
        if d.get("code") != "0" or not d.get("data"):
            break
        batch = d["data"]
        rows.extend(batch)
        after = batch[-1][0]          # il piu' vecchio del blocco
        time.sleep(0.25)              # cortesia verso l'endpoint pubblico
        if len(batch) < 100:
            break
    if not rows:
        return None
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close",
                                     "volume", "volCcy", "volCcyQuote",
                                     "confirm"][:len(rows[0])])
    df["datetime"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms")
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = (df[["datetime", "open", "high", "low", "close", "volume"]]
          .drop_duplicates("datetime").sort_values("datetime")
          .reset_index(drop=True))
    return df


def main():
    ok = []
    for s in SYMBOLS:
        df = fetch(s)
        if df is None or len(df) < 300:
            print(f"{s:<12} scartato ({0 if df is None else len(df)} candele)")
            continue
        p = DATA / f"okx_{s.replace('-', '')}_1d.csv"
        df.to_csv(p, index=False)
        ok.append(s)
        print(f"{s:<12} {len(df):>5} candele  {df['datetime'].iloc[0].date()}"
              f" -> {df['datetime'].iloc[-1].date()}")
    print(f"\nScaricati {len(ok)}/{len(SYMBOLS)} simboli")
    return ok


if __name__ == "__main__":
    main()

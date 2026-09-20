"""Scarica i dati per momentum_backtest.py.

    python3 momentum_fetch.py daily    DATA_DIR  2010-01-01 2026-09-20
    python3 momentum_fetch.py intraday DATA60_DIR                  # barre 60m, ultimi 730g

Le barre giornaliere servono al backtest, quelle orarie a risolvere i giorni in cui,
con sole barre daily, non si sa se sia scattato prima il target o prima lo stop.
yfinance non va piu' indietro di 730 giorni sull'intervallo 60m: e' il motivo per cui
la verifica del percorso copre solo la coda del campione.
"""
import os, sys
import yfinance as yf

# S&P 100, membership odierna. ATTENZIONE: e' survivorship bias e gonfia i risultati
# di una strategia che compra chi e' appena salito. Dichiarato in MOMENTUM_RESULTS.md.
TICKERS = """AAPL ABBV ABT ACN ADBE AIG AMD AMGN AMT AMZN AVGO AXP BA BAC BK BKNG BLK BMY BRK-B C
CAT CHTR CL CMCSA COF COP COST CRM CSCO CVS CVX DE DHR DIS DOW DUK EMR EXC F FDX GD GE GILD GM
GOOG GOOGL GS HD HON IBM INTC INTU JNJ JPM KHC KO LIN LLY LMT LOW MA MCD MDLZ MDT MET META MMM
MO MRK MS MSFT NEE NFLX NKE NVDA ORCL PEP PFE PG PM PYPL QCOM RTX SBUX SCHW SO SPG T TGT TMO
TMUS TSLA TXN UNH UNP UPS USB V VZ WBA WFC WMT XOM""".split()

def daily(out, start, end):
    os.makedirs(out, exist_ok=True)
    df = yf.download(TICKERS + ["SPY"], start=start, end=end, progress=False,
                     auto_adjust=False, group_by="column", threads=True)
    for f in ["Open", "High", "Low", "Close", "Adj Close", "Volume"]:
        df[f].to_csv(f"{out}/{f.replace(' ', '_').lower()}.csv")
        print(f, df[f].shape)
    print("range:", df.index[0].date(), "->", df.index[-1].date())

def intraday(out, tickers):
    os.makedirs(out, exist_ok=True)
    for i in range(0, len(tickers), 12):
        b = tickers[i:i+12]
        df = yf.download(b, period="730d", interval="60m", progress=False,
                         auto_adjust=False, group_by="ticker", threads=True, prepost=False)
        for t in b:
            try: sub = df[t].dropna(how="all")
            except KeyError: continue
            if len(sub): sub.to_csv(f"{out}/{t}.csv")
        print("scaricati", i + len(b), "/", len(tickers))

if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    if mode == "daily":  daily(out, sys.argv[3], sys.argv[4])
    else:                intraday(out, sys.argv[3:] or TICKERS)

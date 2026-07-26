# Tutti i metodi provati

La colonna che conta e' **vs B&H**: ogni riga e' confrontata col
buy&hold dello stesso mercato e della stessa finestra. I CAGR assoluti
di mercati e periodi diversi non sono confrontabili fra loro.


## Benchmark passivi

| Metodo | Mercato | Finestra | CAGR | IRR netta | vs B&H | Sharpe | Max DD | Op/anno | DSR | Esito |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Trend following 10 mesi, leva 2x | S&P/CRSP | 1990-01/2023 | 14.82% | 12.78% | 4.38% | 0.74 | -38.33% | 0.6 | — |  |
| Trend following 10 mesi, leva 1.5x | S&P/CRSP | 1990-01/2023 | 12.44% | 10.50% | 2.10% | 0.77 | -28.61% | 0.6 | — |  |
| Buy&hold indice, CGT 33% all'uscita  [BENCHMARK] | S&P/CRSP | 1990-01/2023 | 10.14% | 8.40% | 0.00% | 0.64 | -49.04% | 0.0 | — |  |
| Trend following 10 mesi, leva 1x | S&P/CRSP | 1990-01/2023 | 9.87% | 8.11% | -0.30% | 0.82 | -18.98% | 0.6 | — |  |
| Buy&hold azioni dirette, dividendi 52%/anno | S&P/CRSP | 1990-01/2023 | 10.22% | 7.55% | -0.85% | 0.65 | -50.82% | 0.0 | — |  |
| Buy&hold ETF UCITS, exit tax 38% + deemed disposal | S&P/CRSP | 1990-01/2023 | 10.14% | 6.39% | -2.01% | 0.64 | -49.04% | 0.0 | — |  |

## Swing trading giornaliero

| Metodo | Mercato | Finestra | CAGR | IRR netta | vs B&H | Sharpe | Max DD | Op/anno | DSR | Esito |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Buy&hold indice CRSP  [bench gruppo A] | S&P/CRSP | 1990-01/2023 | 10.29% | 8.60% | 0.00% | 0.49 | -54.57% | 0.0 | — |  |
| A. Donchian breakout | S&P/CRSP | 1990-01/2023 | 4.78% | 3.77% | -4.84% | 0.25 | -32.41% | 4.2 | — |  |
| A. Trend + stop sigma (sostituto ATR) | S&P/CRSP | 1990-01/2023 | 4.37% | 3.20% | -5.40% | 0.21 | -44.40% | 8.4 | — |  |
| A. RSI2 mean-reversion | S&P/CRSP | 1990-01/2023 | 1.47% | 1.86% | -6.74% | -0.28 | -10.06% | 3.4 | — |  |
| A. Down-streak reversal | S&P/CRSP | 1990-01/2023 | 0.50% | 0.99% | -7.61% | -0.66 | -9.14% | 3.5 | — |  |

## Diversity-weighted (SPT)

| Metodo | Mercato | Finestra | CAGR | IRR netta | vs B&H | Sharpe | Max DD | Op/anno | DSR | Esito |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| D. Equal-weight 49 settori, ribil. annuale | S&P/CRSP | 1990-01/2023 | 11.23% | 9.10% | 0.36% | 0.59 | -52.35% | 1.0 | — |  |
| D. Diversity-weighted p=0.25, ribil. annuale | S&P/CRSP | 1990-01/2023 | 11.11% | 8.96% | 0.22% | 0.59 | -51.41% | 1.0 | — |  |
| D. Diversity-weighted p=0.50, ribil. annuale | S&P/CRSP | 1990-01/2023 | 10.98% | 8.84% | 0.11% | 0.59 | -50.76% | 1.0 | — |  |
| Cap-weight 49 settori  [bench gruppo D] | S&P/CRSP | 1990-01/2023 | 10.68% | 8.74% | 0.00% | 0.58 | -50.21% | 0.0 | — |  |
| D. Diversity-weighted p=0.75, ribil. annuale | S&P/CRSP | 1990-01/2023 | 10.84% | 8.74% | -0.00% | 0.59 | -50.30% | 1.0 | — |  |
| D. Diversity-weighted p=0.25, ribil. mensile | S&P/CRSP | 1990-01/2023 | 10.97% | 8.54% | -0.20% | 0.58 | -51.78% | 12.0 | — |  |
| D. Diversity-weighted p=0.50, ribil. mensile | S&P/CRSP | 1990-01/2023 | 10.87% | 8.43% | -0.31% | 0.58 | -51.12% | 12.0 | — |  |
| D. Diversity-weighted p=0.75, ribil. mensile | S&P/CRSP | 1990-01/2023 | 10.76% | 8.33% | -0.41% | 0.58 | -50.62% | 12.0 | — |  |

## Ricerca iterativa (walk-forward)

| Metodo | Mercato | Finestra | CAGR | IRR netta | vs B&H | Sharpe | Max DD | Op/anno | DSR | Esito |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| H11c media dei due compositi | misto | 1985-2009 | — | 9.84% | 3.30% | 0.68 | -47.30% | — | 0.990 | candidato |
| H11a composito momentum+low-vol | 49 settori | 1947-2009 | — | 12.77% | 3.08% | 0.67 | -60.20% | — | 0.997 | candidato |
| H5 momentum settoriale | 49 settori | 1947-2009 | — | 12.64% | 2.95% | 0.67 | -60.80% | — | 0.998 | candidato |
| H11b Gross Profitability long-only | OSAP quintili | 1985-2009 | — | 8.94% | 2.40% | 0.59 | -40.60% | — | 0.788 | respinta |
| H12 momentum con isteresi | 49 settori | 1947-2009 | — | 11.07% | 1.38% | 0.55 | -53.10% | — | 0.996 | candidato |
| H4 tilt difensivo low-vol | 49 settori | 1947-2009 | — | 10.42% | 0.73% | 0.58 | -46.20% | — | 0.989 | candidato |
| H8 diversificazione geografica | Dev/EM/JP/EU | 1996-2009 | — | 2.14% | -0.16% | 0.25 | -56.60% | — | 0.163 | respinta |
| H2 trend following multi-asset | AQR Century | 1960-2009 | — | 8.45% | -0.40% | 0.27 | -68.10% | — | 0.351 | respinta |
| H6 stop loss / take profit mensili | CRSP | 1960-2009 | — | 8.31% | -0.55% | 0.29 | -50.30% | — | 0.442 | respinta |
| H7 leva con margin call ESMA | CRSP | 1960-2009 | — | 4.68% | -4.18% | 0.14 | -95.10% | — | 0.141 | respinta |
| H9 combinazione inverse-vol | multi-asset | 1995-2009 | — | -3.97% | -6.85% | -2.48 | -39.20% | — | 0.000 | respinta |

## Replica su NASDAQ

| Metodo | Mercato | Finestra | CAGR | IRR netta | vs B&H | Sharpe | Max DD | Op/anno | DSR | Esito |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| Trend 10 mesi leva 2x | NASDAQ Comp. | 1971-2026 | — | 9.63% | -0.83% | 0.35 | -74.50% | — | — | respinta |
| Donchian breakout (parametri da CRSP) | NASDAQ Comp. | 1971-2026 | — | 9.40% | -1.03% | 0.60 | -28.20% | 3.8 | — | respinta |
| Trend + stop sigma (parametri da CRSP) | NASDAQ Comp. | 1971-2026 | — | 8.07% | -2.37% | 0.51 | -49.80% | 8.1 | — | respinta |
| Trend 10 mesi leva 1x | NASDAQ Comp. | 1971-2026 | — | 7.92% | -2.54% | 0.37 | -44.70% | — | — | respinta |
| RSI2 (parametri da CRSP) | NASDAQ Comp. | 1971-2026 | — | 2.60% | -7.83% | -0.82 | -19.90% | 3.7 | — | respinta |
| Down-streak (parametri da CRSP) | NASDAQ Comp. | 1971-2026 | — | 1.88% | -8.55% | -1.41 | -9.80% | 3.5 | — | respinta |

## ATR vero (OHLCV)

| Metodo | Mercato | Finestra | CAGR | IRR netta | vs B&H | Sharpe | Max DD | Op/anno | DSR | Esito |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| MA200 + stop 4xATR | QQQ | 2006-2026 | 10.88% | — | -4.73% | 0.71 | -26.73% | 2.7 | — | respinta |
| MA50 + stop 4xATR | QQQ | 2006-2026 | 10.80% | — | -4.81% | 0.73 | -28.31% | 2.7 | — | respinta |
| MA50 + stop 3xATR | QQQ | 2006-2026 | 9.93% | — | -5.68% | 0.70 | -29.52% | 4.5 | — | respinta |
| MA200 + stop 3xATR | QQQ | 2006-2026 | 9.72% | — | -5.88% | 0.67 | -29.84% | 4.8 | — | respinta |
| MA100 + stop 4xATR | QQQ | 2006-2026 | 8.77% | — | -6.83% | 0.60 | -34.48% | 2.8 | — | respinta |
| MA100 + stop 4xATR | AAPL | 2006-2026 | 20.64% | — | -7.06% | 0.88 | -51.21% | 3.2 | — | respinta |
| MA100 + stop 3xATR | QQQ | 2006-2026 | 7.94% | — | -7.66% | 0.57 | -34.90% | 4.8 | — | respinta |
| MA50 + stop 4xATR | AAPL | 2006-2026 | 19.79% | — | -7.91% | 0.89 | -45.72% | 3.4 | — | respinta |
| MA50 + stop 3xATR | AAPL | 2006-2026 | 19.75% | — | -7.95% | 0.91 | -44.68% | 5.1 | — | respinta |
| MA100 + stop 3xATR | AAPL | 2006-2026 | 19.62% | — | -8.08% | 0.87 | -38.93% | 5.2 | — | respinta |
| MA200 + stop 2xATR | AAPL | 2006-2026 | 19.45% | — | -8.25% | 0.88 | -36.87% | 9.1 | — | respinta |
| MA200 + stop 3xATR | AAPL | 2006-2026 | 19.24% | — | -8.46% | 0.86 | -42.91% | 4.9 | — | respinta |
| MA200 + stop 2xATR | QQQ | 2006-2026 | 7.03% | — | -8.58% | 0.52 | -28.61% | 10.0 | — | respinta |
| MA50 + stop 2xATR | QQQ | 2006-2026 | 6.59% | — | -9.02% | 0.51 | -23.12% | 9.2 | — | respinta |
| MA200 + stop 4xATR | AAPL | 2006-2026 | 18.32% | — | -9.39% | 0.82 | -43.44% | 3.2 | — | respinta |
| MA100 + stop 2xATR | QQQ | 2006-2026 | 6.16% | — | -9.45% | 0.48 | -28.31% | 9.6 | — | respinta |
| MA100 + stop 2xATR | AAPL | 2006-2026 | 17.67% | — | -10.04% | 0.82 | -38.57% | 9.1 | — | respinta |
| MA50 + stop 2xATR | AAPL | 2006-2026 | 17.46% | — | -10.24% | 0.85 | -38.84% | 8.7 | — | respinta |

## VWAP intraday (OHLCV)

| Metodo | Mercato | Finestra | CAGR | IRR netta | vs B&H | Sharpe | Max DD | Op/anno | DSR | Esito |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| rientro -1 dev.std | ora | 2023-09-14/2026-07-24 | -10.62% | — | -34.21% | -1.16 | -33.00% | 118.5 | — | respinta |
| breakout +1 dev.std | ora | 2023-09-14/2026-07-24 | -14.96% | — | -38.55% | -1.98 | -39.39% | 138.7 | — | respinta |
| rientro -1 dev.std | minuti | 2025-10-15/2026-07-24 | -25.24% | — | -43.33% | -2.92 | -21.30% | 297.5 | — | respinta |
| long sotto VWAP (mean rev.) | ora | 2023-09-14/2026-07-24 | -19.94% | — | -43.53% | -1.56 | -47.46% | 237.4 | — | respinta |
| long sopra VWAP | ora | 2023-09-14/2026-07-24 | -24.22% | — | -47.81% | -1.86 | -54.49% | 237.1 | — | respinta |
| breakout +1 dev.std | minuti | 2025-10-15/2026-07-24 | -41.82% | — | -59.92% | -6.36 | -34.10% | 382.6 | — | respinta |
| long sotto VWAP (mean rev.) | minuti | 2025-10-15/2026-07-24 | -42.27% | — | -60.37% | -3.54 | -34.69% | 495.3 | — | respinta |
| long sopra VWAP | minuti | 2025-10-15/2026-07-24 | -53.64% | — | -71.74% | -5.48 | -45.97% | 495.3 | — | respinta |

## Non testabile

| Metodo | Perche' |
|---|---|
| Kronos (foundation model K-line) | pesi scaricabili, ma serve OHLCV su universo ampio: la demo Twelve Data copre 2 simboli |
| Bet Against Beta implementato davvero | richiede leva e prestito titoli su 23 mercati |
| Diversita' a livello di singolo titolo S&P 500 | richiede CRSP/Compustat firm-level |
| SPY/IWM/EFA/EEM/GLD/TLT | Yahoo 429 e Stooq anti-bot per tutta la sessione |

---

**62 metodi valutati.** Battono il buy&hold del proprio mercato: **11**.
Tentativi a registro per il controllo multiple-testing: **383**, piu' ~4.000 valutazioni interne al walk-forward.

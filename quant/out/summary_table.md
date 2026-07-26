# Tabella riassuntiva

CAGR lordo = time-weighted, al lordo di imposte, netto di costi.
IRR netta = money-weighted del PAC 500 EUR/mese, netto di tutto.

### Benchmark passivi e trend following (gruppo C)

| Strategia | Finestra | CAGR lordo | IRR netta PAC | vs B&H | Sharpe | Max DD | Op/anno | Fuori campione |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Trend following 10 mesi, leva 2x | 1990-01/2023 | 14.82% | 12.78% | +4.38 | 0.74 | -38.3% | 0.6 | regola pubblicata, non ottimizzata |
| Trend following 10 mesi, leva 1.5x | 1990-01/2023 | 12.44% | 10.50% | +2.10 | 0.77 | -28.6% | 0.6 | regola pubblicata, non ottimizzata |
| Buy&hold indice, CGT 33% all'uscita  [BENCHMARK] | 1990-01/2023 | 10.14% | 8.40% | +0.00 | 0.64 | -49.0% | 0.0 | in-sample |
| Trend following 10 mesi, leva 1x | 1990-01/2023 | 9.87% | 8.11% | -0.30 | 0.82 | -19.0% | 0.6 | regola pubblicata, non ottimizzata |
| Buy&hold azioni dirette, dividendi 52%/anno | 1990-01/2023 | 10.22% | 7.55% | -0.85 | 0.65 | -50.8% | 0.0 | in-sample |
| Buy&hold ETF UCITS, exit tax 38% + deemed disposal | 1990-01/2023 | 10.14% | 6.39% | -2.01 | 0.64 | -49.0% | 0.0 | in-sample |

### Swing trading giornaliero (gruppo A)

| Strategia | Finestra | CAGR lordo | IRR netta PAC | vs B&H | Sharpe | Max DD | Op/anno | Fuori campione |
|---|---|---:|---:|---:|---:|---:|---:|---|
| Buy&hold indice CRSP  [bench gruppo A] | 1990-01/2023 | 10.29% | 8.60% | +0.00 | 0.49 | -54.6% | 0.0 | in-sample |
| A. Donchian breakout | 1990-01/2023 | 4.78% | 3.77% | -4.84 | 0.25 | -32.4% | 4.2 | OOS (meta' campione) |
| A. Trend + stop sigma (sostituto ATR) | 1990-01/2023 | 4.37% | 3.20% | -5.40 | 0.21 | -44.4% | 8.4 | OOS (meta' campione) |
| A. RSI2 mean-reversion | 1990-01/2023 | 1.47% | 1.86% | -6.74 | -0.28 | -10.1% | 3.4 | OOS (meta' campione) |
| A. Down-streak reversal | 1990-01/2023 | 0.50% | 0.99% | -7.61 | -0.66 | -9.1% | 3.5 | OOS (meta' campione) |

### Diversity-weighted / SPT (gruppo D)

| Strategia | Finestra | CAGR lordo | IRR netta PAC | vs B&H | Sharpe | Max DD | Op/anno | Fuori campione |
|---|---|---:|---:|---:|---:|---:|---:|---|
| D. Equal-weight 49 settori, ribil. annuale | 1990-01/2023 | 11.23% | 9.10% | +0.36 | 0.59 | -52.4% | 1.0 | nessun parametro |
| D. Diversity-weighted p=0.25, ribil. annuale | 1990-01/2023 | 11.11% | 8.96% | +0.22 | 0.59 | -51.4% | 1.0 | teorema, non ottimizzato |
| D. Diversity-weighted p=0.50, ribil. annuale | 1990-01/2023 | 10.98% | 8.84% | +0.11 | 0.59 | -50.8% | 1.0 | teorema, non ottimizzato |
| Cap-weight 49 settori  [bench gruppo D] | 1990-01/2023 | 10.68% | 8.74% | +0.00 | 0.58 | -50.2% | 0.0 | in-sample |
| D. Diversity-weighted p=0.75, ribil. annuale | 1990-01/2023 | 10.84% | 8.74% | -0.00 | 0.59 | -50.3% | 1.0 | teorema, non ottimizzato |
| D. Diversity-weighted p=0.25, ribil. mensile | 1990-01/2023 | 10.97% | 8.54% | -0.20 | 0.58 | -51.8% | 12.0 | teorema, non ottimizzato |
| D. Diversity-weighted p=0.50, ribil. mensile | 1990-01/2023 | 10.87% | 8.43% | -0.31 | 0.58 | -51.1% | 12.0 | teorema, non ottimizzato |
| D. Diversity-weighted p=0.75, ribil. mensile | 1990-01/2023 | 10.76% | 8.33% | -0.41 | 0.58 | -50.6% | 12.0 | teorema, non ottimizzato |

### Ipotesi di ricerca, valutate in walk-forward (giri 03-09)

Ogni anno i parametri sono scelti su tutto cio' che precede e applicati l'anno
dopo: la serie e' interamente fuori campione. Finestre diverse fra loro, il
confronto e' sempre col buy&hold della stessa finestra.

| Ipotesi | Finestra OOS | IRR netta | B&H stessa finestra | vs B&H | Sharpe | B&H Sharpe | Max DD | DSR | Esito |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| H5 Momentum settoriale cross-sectional | 1947-2009 | 12.64% | 9.69% | **+2.95** | 0.67 | 0.47 | -60.8% | **0.998** | candidato |
| H4 Tilt difensivo settoriale low-vol | 1947-2009 | 10.42% | 9.69% | **+0.73** | 0.58 | 0.47 | -46.2% | **0.989** | candidato |
| H8 Diversificazione geografica | 1996-2009 | 2.14% | 2.30% | -0.16 | 0.25 | 0.26 | -56.6% | 0.163 | respinta |
| H2 Trend following multi-asset | 1960-2009 | 8.45% | 8.85% | -0.40 | 0.27 | 0.33 | -68.1% | 0.351 | respinta |
| H6 Stop loss / take profit mensili | 1960-2009 | 8.31% | 8.85% | -0.55 | 0.29 | 0.33 | -50.3% | 0.442 | respinta |
| H7 Leva con margin call ESMA | 1960-2009 | 4.68% | 8.85% | -4.18 | 0.14 | 0.33 | **-95.1%** | 0.141 | respinta |
| H9 Combinazione inverse-vol | 1995-2009 | -3.97% | 2.87% | -6.85 | -2.48 | 0.36 | -39.2% | 0.000 | respinta |

DSR = Deflated Sharpe Ratio corretto per il numero cumulato di configurazioni
provate. Soglia di promozione 0,95.

### Prove di robustezza sui due candidati

| Prova | H5 (CGT 33%) | H5 (riqualif. 52%) |
|---|---:|---:|
| caso base | +2.95 | **+1.88** |
| segnale ritardato di 1 mese | +2.29 | +1.24 |
| segnale ritardato di 2 mesi | +2.11 | +1.08 |
| costi di transazione doppi | +2.60 | +1.59 |

H5 ruota il 259%/anno: l'aliquota da assumere e' il 52%, non il 33%.
H4 ruota il 7%/anno: +0.73 a CGT 33%, +0.41 a 52%.

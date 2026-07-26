# quant — confronto attivo/passivo netto di fiscalità irlandese

Valuta strategie attive e passive come PAC da €500/mese, netto di costi e
imposte irlandesi (CGT 33%, exit tax 38% con deemed disposal a 8 anni, DIRT 33%,
dividendi esteri ~52%, scenario riqualificazione al 52%).

**Il report è in [`reports/REPORT.md`](reports/REPORT.md).**

## Uso

```bash
./fetch_data.sh                 # scarica le fonti (~110 MB, nessuna registrazione)
pip install pandas numpy scipy statsmodels xlrd openpyxl

cd src
python dataio.py                # verifica che tutte le fonti carichino
python calibrate.py             # gate: riproduce i riferimenti buy&hold Shiller
python run_a.py                 # gruppo A: swing trading
python run_b.py                 # gruppo B: anomalie cross-sectional
python run_d.py                 # gruppo D: diversity-weighted (SPT)
python run_all.py               # tabella unica di confronto
```

`calibrate.py` esce con codice 1 se il buy&hold si scosta dai riferimenti oltre
la tolleranza in `config.py`: è un gate, non un test informativo.

## Struttura

| File | Contenuto |
|---|---|
| `src/config.py` | tutti i parametri fiscali e di costo, un solo posto da toccare |
| `src/tax.py` | motore fiscale a lotti + simulatore PAC con XIRR datato |
| `src/dataio.py` | loader per Ken French, Shiller, AQR, OSAP |
| `src/strategies.py` | segnali gruppo A + test di falsificazione del look-ahead |
| `src/run_a/b/c/d.py` | i quattro gruppi |
| `src/run_all.py` | tabella unica, robustezza, gate sulla leva |
| `out/` | output testuali e JSON dell'ultima esecuzione |

## Fonti

- **Ken French Data Library** — fattori giornalieri/mensili, 49 portafogli
  settoriali (con numero società e dimensione media, da cui le capitalizzazioni),
  decili di size. 1926-2026.
- **Robert Shiller**, `ie_data.xls` — S&P Composite mensile 1871-2024.
- **AQR**, *Betting Against Beta: Equity Factors, Monthly* — BAB 1930-2026.
- **Open Source Asset Pricing** (Chen & Zimmermann) — 212 anomalie replicate con
  date di pubblicazione.

Non scaricabili da questo ambiente: Yahoo Finance (429), Stooq (anti-bot),
AlphaVantage (API key). Le conseguenze sui test sono elencate in apertura del
report.

# Stato della ricerca

**Obiettivo.** Trovare una strategia che batta il PAC buy&hold azionario da
€500/mese, netto di costi (0,15% round-trip) e fiscalità irlandese (CGT 33% sul
realizzato, esenzione €1.270, riporto perdite; DIRT 33% sulla liquidità).

**Criterio di promozione — non negoziabile.** Battere il benchmark su TEST *non
basta*. Serve **Deflated Sharpe Ratio > 0,95**, calcolato sul numero **cumulato**
di configurazioni provate in tutta la ricerca (registro in `registry.csv`).
Motivo: con N tentativi il massimo Sharpe atteso sotto ipotesi nulla cresce come
√(2 log N); fermarsi al primo successo apparente significa promuovere il massimo
di N estrazioni casuali, non un edge.

## Finestre — fissate, mai modificate

| | Periodo | Uso |
|---|---|---|
| TRAIN | 1926-07 → 1989-12 | ottimizzazione parametri, guardabile liberamente |
| TEST | 1990-01 → 2009-12 | validazione; **ogni sguardo costa un tentativo nel registro** |
| HOLDOUT | 2010-01 → 2026-12 | **si apre una volta sola**, su un solo candidato, alla fine |

Lo stato dell'holdout è sigillato in `holdout_opened.json`. Se il file esiste,
l'holdout è bruciato e qualunque risultato su quella finestra è in-sample.

## Contatori

| | |
|---|---|
| Giri completati | 1 |
| Configurazioni provate (cumulate) | **50** |
| Soglia SR0 attesa sotto H0 | 0,538 annualizzato |
| Candidati promossi | **0** |
| Holdout | **sigillato, mai aperto** |

## Dati disponibili

Azionario USA giornaliero e mensile (Ken French, 1926-2026) · 49 settori ·
Shiller 1871-2024 · **AQR Century of Factor Premia** (6 classi di asset × 4-5
stili, 1926-2026) · **AQR Value & Momentum Everywhere** (1972-2026) · **AQR
TSMOM** (trend following su futures, 1985-2026) · AQR BAB · OSAP 212 anomalie ·
French regionali (Developed, Emerging, Europe, Japan, Asia-Pac) · **FRED**
(senza API key: DGS10 e qualunque altra serie).

Non disponibili: Yahoo, Stooq, AlphaVantage → niente OHLC di ETF, niente
High/Low, quindi **niente stop loss/take profit intraday**. Gli SL/TP sono
testabili solo su chiusure mensili o giornaliere, ed è una limitazione reale da
dichiarare quando li proverò.

## Esito dei giri

| Giro | Ipotesi | Scelto su TRAIN → TEST | DSR | Esito |
|---|---|---|---|---|
| 01 | H1 multi-asset azioni+obbligazioni, bassa rotazione, leva | +0,87 punti IRR | **0,328** | **RESPINTA** |

## Coda delle ipotesi

- [ ] **H2** Trend following multi-asset (TSMOM AQR) come overlay sul core azionario. Turnover alto → verificare se la fiscalità lo uccide.
- [ ] **H3** Composito multi-stile su 6 classi di asset (Century) a rotazione minima, con leva calibrata sulla vol azionaria.
- [ ] **H4** Core azionario + tilt difensivo/qualità a rotazione bassissima (il tilt più tax-efficient possibile).
- [ ] **H5** Momentum a 12 mesi cross-asset su N mercati (tactical asset allocation).
- [ ] **H6** Stop loss e take profit su chiusure mensili applicati al miglior candidato dei giri precedenti, con e senza.
- [ ] **H7** Ottimizzazione della leva sul candidato migliore, con vincolo di margine ESMA (5:1 azioni singole, 20:1 indici) e verifica di margin call.
- [ ] **H8** Diversificazione geografica pura (Developed/Emerging/Japan/Europe) buy&hold, zero rotazione — il candidato strutturalmente più tax-efficient.
- [ ] **H9** Combinazione dei migliori stream non correlati fra loro, pesati inverse-vol, ribilanciamento annuale.

## Note metodologiche accumulate

- **La finestra TEST 1990-2009 è ostile all'azionario**: il buy&hold rende solo
  3,10% IRR (due mercati orso pesanti). Qualunque cosa diversifichi sembra
  brillante lì. È un rischio di selezione legato alla finestra, non un edge:
  serve verificare la stabilità del risultato prima di credere a un margine.
- La fiscalità è il vincolo dominante: ogni punto di turnover annuo costa
  ~0,33 × (utile realizzato). Le strategie a bassa rotazione partono avvantaggiate.
- Convenzione Sharpe: **sempre su rendimenti in eccesso**, sia in `summarise`
  sia nel DSR. Mischiare le due convenzioni gonfiava il DSR (0,796 → 0,328).

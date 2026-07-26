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
| Giri completati | 9 (tutte le ipotesi in coda eseguite) |
| Configurazioni provate (cumulate) | **117 a registro + ~2.580 valutazioni interne al walk-forward** |
| Soglia SR0 (giro 02) | 0,962 annualizzato |
| Candidati promossi | **2** (H5, H4) — verifiche superate, holdout ANCORA SIGILLATO |
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
| 02 | H3 core azionario + overlay multi-stile 6 classi (AQR Century) | −2,65 punti IRR | **0,001** | **RESPINTA** |
| 03 | H2 trend following multi-asset (Century momentum) | −0,41 | 0,351 | RESPINTA |
| 04 | H4 tilt difensivo settoriale low-vol, long-only | **+0,73** | **0,989** | **candidato** |
| 05 | H5 momentum settoriale cross-sectional | **+2,93** | **0,998** | **candidato** |
| 06 | H6 stop loss / take profit su chiusure mensili | −0,56 | 0,442 | RESPINTA |
| 07 | H7 leva con margin call ESMA modellata | −4,40 | 0,141 | RESPINTA |
| 08 | H8 diversificazione geografica, rotazione minima | −0,24 | 0,163 | RESPINTA |
| 09 | H9 combinazione inverse-vol multi-asset | −8,62 | 0,000 | RESPINTA |

Dal giro 03 in poi la valutazione e' **walk-forward a finestre espandenti**: ogni
anno Y i parametri sono scelti su tutto cio' che precede Y e applicati durante Y.
Sostituisce lo split unico, che aveva il disallineamento di regime descritto sotto.

## Verifiche sui candidati (in corso)

| | CGT 33% | riqualif. 52% | turnover |
|---|---:|---:|---:|
| H5 momentum settoriale | +2,93% | **+1,89%** | **262%/anno** |
| H4 tilt low-vol | +0,73% | +0,42% | 7%/anno |

**Verifiche chiuse, tutte superate da H5:**

| Prova | vs B&H (CGT 33%) | vs B&H (52%) |
|---|---:|---:|
| caso base | +2,93% | +1,89% |
| segnale ritardato di 1 mese | +2,35% | +1,31% |
| segnale ritardato di 2 mesi | +2,16% | +1,14% |
| costi di transazione doppi (0,30%) | +2,61% | +1,62% |

Il degrado con il ritardo e' graduale, non un crollo: il margine non dipende da
un timing al limite. E' anche il profilo atteso del momentum, che decade con il
lag ma non svanisce. Con 262% di turnover annuo l'aliquota da assumere e' il 52%,
non il 33%: il numero di riferimento per H5 e' **+1,89 punti**, non +2,93.

**Holdout ancora sigillato.** Va aperto su UN SOLO candidato, dopo le verifiche.

## Coda delle ipotesi (tutte eseguite)

- [x] **H2** Trend following multi-asset (TSMOM AQR). **Bloccata dai dati**: TSMOM parte dal 1985, il TRAIN si ridurrebbe a 60 mesi. Va rifatta con uno split dedicato o con un proxy a storia lunga (Century "All asset classes Momentum", dal 1926).
- [x] **H4** Core azionario + tilt difensivo/qualità a rotazione bassissima (il tilt più tax-efficient possibile).
- [x] **H5** Momentum a 12 mesi cross-asset su N mercati (tactical asset allocation).
- [x] **H6** Stop loss e take profit su chiusure mensili applicati al miglior candidato dei giri precedenti, con e senza.
- [x] **H7** Ottimizzazione della leva sul candidato migliore, con vincolo di margine ESMA (5:1 azioni singole, 20:1 indici) e verifica di margin call.
- [x] **H8** Diversificazione geografica pura (Developed/Emerging/Japan/Europe) buy&hold, zero rotazione — il candidato strutturalmente più tax-efficient.
- [x] **H9** Combinazione dei migliori stream non correlati fra loro, pesati inverse-vol, ribilanciamento annuale.

## Note metodologiche accumulate

- **La finestra TEST 1990-2009 è ostile all'azionario**: il buy&hold rende solo
  3,10% IRR (due mercati orso pesanti). Qualunque cosa diversifichi sembra
  brillante lì. È un rischio di selezione legato alla finestra, non un edge:
  serve verificare la stabilità del risultato prima di credere a un margine.
- La fiscalità è il vincolo dominante: ogni punto di turnover annuo costa
  ~0,33 × (utile realizzato). Le strategie a bassa rotazione partono avvantaggiate.
- Convenzione Sharpe: **sempre su rendimenti in eccesso**, sia in `summarise`
  sia nel DSR. Mischiare le due convenzioni gonfiava il DSR (0,796 → 0,328).
- `var_sr` del DSR va calcolata **entro la famiglia di strategie del giro**, non
  sul registro intero: famiglie con profili di rischio diversi (1× contro 2× di
  leva) hanno Sharpe centrati diversamente e la varianza aggregata (0,0210 contro
  0,0047 e 0,0117 entro giro) gonfia SR0 per il motivo sbagliato. N resta cumulato.
- **Lo split TRAIN/TEST ha un disallineamento di regime.** TRAIN 1926-1989 premia
  la leva (lunghi mercati toro), TEST 1990-2009 la punisce (due crolli del 50%).
  Nel giro 02 l'ottimizzatore ha scelto leva 2× su TRAIN e ha prodotto −84% di
  drawdown su TEST. Non è un difetto della strategia, è il mio disegno: da
  affrontare con walk-forward a finestre mobili invece di uno split unico.
- **Bug trovato nel walk-forward: `realize_frac` non veniva propagato**, quindi
  le strategie erano tassate come un buy&hold e il turnover risultava gratuito.
  Corretto: H5 e' scesa da +6,08 a +2,93 punti, H4 da +1,73 a +0,73. Era il
  vincolo dominante dell'intero studio, e mancava.
- **Bug nel `build_fn` applicato ai soli 12 mesi dell'anno Y**: le strategie
  hanno bisogno di storia per scaldare gli indicatori e restituivano `None`.
  Ora la configurazione scelta gira sull'intera storia fino a fine Y e si
  ritaglia il solo anno Y; i parametri non vedono comunque il proprio anno.
- **Bug in H6**: lo stop rientrava nello stesso mese in cui usciva, quindi non
  era uno stop. Aggiunta la regola di rientro sopra la media a 10 mesi.
- **I premi AQR non sopravvivono ai costi retail.** L'overlay multi-stile rende
  3,3-3,4%/anno lordo contro un drag di implementazione stimato al 7,5%/anno.
  È negativo prima ancora di iniziare.

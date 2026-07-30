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
| Giri completati | 11 |
| Configurazioni provate (cumulate) | **322 a registro + ~4.000 valutazioni interne al walk-forward** |
| Soglia SR0 (giro 02) | 0,962 annualizzato |
| Candidati promossi | **2** (H5, H4) — verifiche superate, holdout ANCORA SIGILLATO |
| Holdout | **APERTO AL GIRO 78 e BRUCIATO.** Una volta sola, sul momentum 12-3 top-5 mensile: margine **−0,95**, negativo in 12 calendari su 12. Non si riapre |

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
| 05 | H5 momentum settoriale cross-sectional | **+2,95** | **0,998** | **candidato** |
| 06 | H6 stop loss / take profit su chiusure mensili | −0,55 | 0,442 | RESPINTA |
| 07 | H7 leva con margin call ESMA modellata | −4,18 | 0,141 | RESPINTA |
| 08 | H8 diversificazione geografica, rotazione minima | −0,16 | 0,163 | RESPINTA |
| 09 | H9 combinazione inverse-vol multi-asset | −6,85 | 0,000 | RESPINTA |
| 10 | H10 scansione sistematica di 201 anomalie pubblicate | — | — | 2 sopravvissuti |
| 11a | C1 punteggio settoriale misto momentum + low-vol | **+3,08** | **0,997** | **candidato** |
| 11b | C2 Gross Profitability long-only (Novy-Marx 2013) | +2,40 | 0,709 | RESPINTA |
| 11c | C3 media di C1 e C2 | +3,30 | 0,816 | RESPINTA |

Dal giro 03 in poi la valutazione e' **walk-forward a finestre espandenti**: ogni
anno Y i parametri sono scelti su tutto cio' che precede Y e applicati durante Y.
Sostituisce lo split unico, che aveva il disallineamento di regime descritto sotto.

## Verifiche sui candidati (in corso)

| | CGT 33% | riqualif. 52% | turnover |
|---|---:|---:|---:|
| H5 momentum settoriale | +2,95% | da rimisurare | **262%/anno** |
| H4 tilt low-vol | +0,73% | da rimisurare | 7%/anno |

> **I numeri sotto sono stati rigenerati dopo la correzione della base fiscale**
> (vedi note metodologiche): il motore tassava i versamenti come plusvalenza.
> Le verifiche di robustezza sono in corso di riesecuzione.

**Verifiche (valori pre-correzione, in aggiornamento):**

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

## Giro 10 — cosa sopravvive alla letteratura

201 anomalie pubblicate con almeno 10 anni di storia post-pubblicazione,
filtrate su quattro criteri:

| Filtro | Passano |
|---|---:|
| t-stat post-pubblicazione > 2 | 61 |
| costruzione value-weighted (eseguibile) | **22** |
| quantile ≥ 10% (capacita') | 122 |
| premio netto dei costi retail > 0 | 98 |
| **tutti e quattro insieme** | **2** |

I due sopravvissuti: **Gross Profitability** (Novy-Marx 2013, netto 9,03%,
t 2,80) e **CPVolSpread** (Bali-Hovakimian 2009, netto 2,39%, t 3,08).

Il filtro che decide e' la costruzione: **solo 22 anomalie su 201 sono
value-weighted**. La letteratura e' quasi tutta equal-weighted, cioe' guidata da
microcap che con 500 EUR/mese non sono eseguibili ne' sul lato lungo ne' su
quello corto.

## Coda delle ipotesi

**La coda vive in [`QUEUE.md`](QUEUE.md)**: 20 voci pre-dichiarate su allocazione
e sizing, mercati non toccati (materie prime, valute, credito, curva dei tassi,
azionario internazionale, cripto estese), sistemi nuovi (cointegrazione, breadth,
momentum multi-orizzonte, term structure del VIX, copertura del premio di
volatilita', multi-strategia su stream davvero scorrelati) e due voci
metodologiche (dispersione per data di inizio, bootstrap a blocchi).

Ogni voce ha predizione e condizione di falsificazione scritte PRIMA. Il Routine
notturno ne esegue una per giro e aggiorna la tabella degli esiti.

**Esiti della coda finora** (dettaglio in `QUEUE.md`, mini-report in `rounds/`):

| Giro | Voce | Esito | Numero chiave |
|---|---|---|---|
| 29 | H31 combinazione dei promossi | confermata | corr 0,944 |
| 29 | H32 turn-of-month | confermata | t=7,04, strategia −7,26 |
| 30 | A1 risk parity fra classi | confermata | ERC 7,08% contro 10,48% |
| 31 | A2 hierarchical risk parity | confermata | HRP 9,45% contro 9,89% equal-weight |
| 32 | A3 min-variance / max-diversification | confermata | min-var 8,22%, max-div 9,34%, cap-weight 10,88% |
| 33 | A4 Kelly frazionario + de-risking | confermata | DD migliora 12/12, IRR migliora 0/12 |
| 34 | A5 ERC fra 4 stream scorrelati | confermata | Sharpe 1,19 contro 0,69, IRR 5,64% contro 9,88% |
| 35 | A7 stabilità HRP contro min-variance | confermata nel verso | fattore 1,67, non 3-10 |
| 35 | A8 min-variance in leva 1,20× | confermata | 8,64% contro 10,88%, Sharpe 0,78→0,69 |
| 36 | A9 Kelly contro frazione fissa | confermata | la frazione fissa vince 4/4 |
| 36 | A10 curva del prezzo del drawdown | confermata | minimo interno, ma a 40% e 20%, non 30-35% |
| 37 | B1 materie prime | confermata | trend 3,75% netto contro 9,90% |
| 37 | B2 valute | confermata dopo bug | Sharpe 0,25, skew −0,12 |
| 38 | B3 credito HY | **senza esito** | serie ICE limitata a 35 mesi |
| 38 | B7 credito Baa−Aaa (sostituta) | confermata | 8,48% contro 10,56% |
| 38 | B4 curva dei tassi | confermata | 12 inversioni su 13, e perde 1,2-2,6 punti |
| 39 | B5 azionario internazionale | confermata | DSR 0,864 |
| 39 | B6 cripto esteso | confermata | DSR 0,904, Sharpe [0,22 – 1,56] |

| 40 | C1 cointegrazione | confermata | 5,4% persiste fuori campione, p = 0,476 |
| 40 | C2 breadth | confermata | correlazione 0,830 col filtro di trend |
| 41 | C3 momentum multi-orizzonte | confermata | ogni composito peggio su entrambi i criteri |
| 41 | C4 term structure VIX | confermata | direzione p = 0,535, volatilità ρ = +0,42 |
| 42 | C5 premio coperto | confermata | −5,91 punti, coda non accorciata |
| 42 | C6 quattro pilastri | confermata | Sharpe 0,76 contro 0,95 del miglior singolo |
| 43 | **D1 data di partenza** | **falsificata** | ampiezza 0,56 punti, per difetto della specifica |
| 43 | **D2 bootstrap a blocchi** | **falsificata** | H5 al 100° percentile, +3,82% lordo / −1,20% netto |
| 44 | A6 scomposizione della perdita | confermata | quota fiscale 15,3%, composizione 84-92% |
| 45 | A11 alpha di pareggio della sleeve | confermata | servirebbero 6,5-7,0 punti l'anno in più |
| 46 | A12 finestre mobili di 20 anni | confermata | ERC vince 48,4% delle finestre, divario medio −0,37 |
| 47 | **A13 rischio di sequenza** | **falsificata** | rapporto 1,2-2,7 invece di ≥4; 0/14 finestre recuperate |
| 48 | E0 cancello opzioni | **aperto** | terzo venerdì + IV = 0,85 × VIX, residui ±0,7 |
| 48 | E1 premio di varianza | confermata | 83,0% dei mesi, +3,91 punti, 0/4 decenni negativi |
| 49 | **E2 comprare opzioni** | **falsificata** | condizione mal posta: testava un portafoglio, non l'opzione |
| 49 | E3 vendere put cash-secured | confermata | Sharpe 0,77 > 0,71, IRR −4,98, skew fino a −12,57 |
| 49 | E4 covered call | confermata | col simulatore +0,98, con gli indici reali −2,92 |
| 49 | **E5 LEAPS come leva** | **falsificata** | +1,34 ma DSR 0,000 e drawdown −62,5% |
| 52 | E6 stress sui LEAPS | confermata | muore a +10% di rincaro, ma 17/17 finestre e k fino a 1,15 |
| 53 | G1 filtri di tendenza | confermata | il migliore perde 2,51 punti, il peggiore 4,50 |
| 53 | **G2 momentum come veicolo** | **falsificata** | +0,77 in ETF UCITS, ma +2,77 solo dallo spostare la rotazione nel fondo |
| 57 | H1 globale contro USA | confermata | S&P +1,89 sui dati reali, ma vince solo il 73% delle finestre decennali |
| 58 | **A14 sequenza sul livello** | **falsificata** | rapporto 0,55-48,51, R² max 0,210 |
| 50 | **F1 rotazione top-1** | **falsificata** | 1 cella su 9, +0,30 su un benchmark debole |
| 50 | F2 griglia posizioni × frequenza | confermata | max top-5 annuale 10,02% contro 11,16% statico |
| 51 | F3 sistema EMA giornaliero | confermata | batte il B&H su 1/10 asset, muore sul lordo |
| 51 | **F4 sistema EMA intraday** | **falsificata** | ma finestre 20 / 2,9 / 0,8 anni, non confrontabili |
| 51 | F5 ablazione del sistema EMA | confermata | il solo trend filter vale **24 volte** il sistema completo |
| 59 | **D3 finestre di lunghezza fissa** | confermata | ampiezza **10,19** punti contro i **0,56** di D1: **18×** |
| 60 | **D4 scelta del benchmark** | confermata | il premio di equal-weighting spiega **263-398%** del margine di H5 |
| 61 | **A15 peso analitico di ciascun anno** | confermata | rapporto **5,91** mediano, non 9,5; monotono in 80/80 |
| 62 | **D5 quota di vittorie ingannevole** | **falsificata** | scarto positivo per il **28,6%**, e di segno opposto |
| 63 | **D6 rotazione sottostimata** | **falsificata** | un verdetto si ribalta (+0,16 → −0,07); l'errore ha **due versi** |
| 64 | **D7 F2 con benchmark corretto** | **falsificata** | il divario si **allarga** a −1,92; DSR 0,9743 su N=15 ma **0,7691** sul cumulato |
| 65 | **D8 verdetti dentro la correzione** | **falsificata** | cambia segno il **57,1%**; il calendario del ribilanciamento vale **3,43 punti** |
| 66 | **D9 vincolo di rotazione** | confermata | **3 celle su 4**, guadagno **+0,64**; nessuna sopra l'EW annuale |
| 67 | **J1 statistical jump model** | confermata | migliore **−1,63**, long/short perde **21 su 21**; corr MA10 da 0,610 a **0,006** |
| 68 | **D10 calendario del ribilanciamento** | confermata | ampiezza **3,65%** sul top-5 contro **0,14%** sull'equal-weight |
| 69 | **K1 conto in valuta** | confermata | margine max **0,25**, livello **−0,46/−0,77** punti in euro |
| 70 | **K2 PAC interrotto** | **falsificata** | l'IRR e' cieca: −22,51% di montante = **−0,016** di IRR |
| 71 | **K3 vantaggio del veicolo** | **falsificata** | +3,43 sopra la soglia, ma la rotazione vale **+0,00**: sono i dividendi |
| 72 | **K4 regola per l'holdout** | confermata | **0 candidati su 12** passano; il cancello che elimina di piu' e' il **margine** |
| 73 | **L1 ritardo in giorni** | **falsificata** | non monotono; il costo di 1 giorno e' **0,08** punti |
| 74 | **L2 costo retail** | **falsificata** | il divario si allarga **a favore** del momentum (+0,53): la commissione fissa colpisce il benchmark a 49 posizioni |
| 75 | **L3 report finale** | confermata | **0 su 30** gruppi sopra +1,00 sopravvive alla rilettura; ma i numeri superstiti sono **dodici**, non «meno di dieci» |
| 76 | **L4 skip contro ritardo** | **falsificata** | ampiezza in k **3,94** punti: lo skip è un grado di libertà mai contato. E il 12-3 top-5 mensile passa **3 cancelli su 4** |
| 77 | **M1 quattro cancelli** | **falsificata (ramo 1)** | **il candidato passa 4 su 4**: G1 +1,18 su 12 calendari, G2 0,9907, G3 **93,1%**, G4 per costruzione |
| 78 | **N1 APERTURA DELL'HOLDOUT** | confermata, **3 clausole su 3** | **il candidato perde −0,95 fuori campione, in 12 calendari su 12.** Holdout **bruciato** |
| 79 | **O1 cancello sul margine** | confermata, **3 su 3** | soglia **+2,19** contro il +1,18 del candidato: **0 passanti su 32**. Il fallimento dell'holdout **è spiegato dalla selezione** |
| 80 | **O2 scomposizione train-holdout** | confermata | **alfa lordo da +6,50 a +0,31**: −6,19, cioè il **291%** del divario. Rotazione aggiuntiva **−0,11** |
| 81 | **O3 finestre disgiunte** | **falsificata**, 2 clausole su 2 | quota disgiunta **75,0%**: G3 passa anche su prove indipendenti. E il rimedio è **10× peggiore** (falsi positivi 3,07% → 31,25%) |

**La coda dichiarata è esaurita**, più i gruppi E (opzioni, giri 48-49 e 52) e F
(rotazione concentrata e sistema EMA, giri 50-51). 58 voci eseguite nei giri 30-81:
**39 confermate, 18 falsificate, 1 senza esito per dati (B3)**.
**Il progetto ha avuto una promozione e l'ha vista fallire fuori campione**: il
momentum 12-3 top-5 mensile ha passato tutti e quattro i cancelli al giro 77 e ha
perso **−0,95** sull'holdout al giro 78.
In coda: **O4, O5, O6** — l'autopsia dei cancelli e del motore fiscale. Non ci
sono piu' voci su strategie nuove, perche' non c'e' piu' un campione per
validarle.

Registro a **1.439 tentativi** cumulati.
Il report finale è **[`../reports/REPORT.md`](../reports/REPORT.md)**, riscritto
al giro 75 (era fermo al giro 29).

## Coda vecchia (tutte eseguite)

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
- **Bug nella base fiscale alla liquidazione (il piu' grave trovato finora).**
  La plusvalenza era calcolata contro il valore del portafoglio al PRIMO
  versamento (~500 EUR) invece che contro i versamenti cumulati (204.000 EUR):
  il motore tassava il montante quasi per intero. Segnalato dall'utente, che ha
  notato che i numeri non tornavano con un CAGR dell'S&P intorno al 10%.
  Corretto: benchmark 8,11% -> 8,40%, vantaggio del veicolo fiscale contro ETF
  UCITS da 1,72 a 2,01 punti. Il regime ETF non era interessato (base per lotti).
- **L'IRR ha uno scarto di convenzione di ~0,05 punti**: XIRR usa act/365 mentre
  il compounding e' mensile, e i mesi non sono 1/12 di anno esatto. Su un caso
  analitico all'8% esatto restituisce 8,049%. Si applica identicamente a ogni
  strategia, quindi i confronti non ne risentono.
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
- **La composizione non ha aggiunto nulla.** Nel giro 11 il punteggio misto
  momentum+low-vol sceglie alpha = 1,0, cioe' momentum puro: l'ottimizzatore
  scarta da solo la componente low-vol. E la media dei due flussi (C3) ha
  differenza maggiore (+3,30) ma DSR piu' basso (0,816 contro 0,997), perche'
  raddoppia il turnover a 600%/anno. Combinare due segnali non e' gratis quando
  ogni rotazione e' un evento tassabile.
- **Il metodo di allocazione non salva niente a composizione fissa.** Il giro 30
  aveva mostrato che con turnover quasi nullo la perdita viene dalla composizione
  (il decennale rende meno dell'azionario). Il giro 31 tiene la composizione fissa
  — quattro portafogli di soli 49 settori USA — e perde comunque 1,43 punti di IRR
  netta contro il cap-weighted, con 0,31 rotazioni l'anno. HRP guadagna 0,28 punti
  di CAGR lordo e ne restituisce 1,4 netti: il conto fiscale del ribilanciamento
  supera il guadagno di un metodo che non prova nemmeno a prevedere i rendimenti.
- **Il vantaggio del veicolo era sovrastimato una seconda volta: i DIVIDENDI.**
  Nei confronti CGT contro ETF ho sempre passato al motore la serie **total
  return** senza `div_yield`, il che equivale a far accumulare i dividendi
  esentasse **anche a chi detiene le azioni direttamente**. È vero per un fondo ad
  accumulazione, è falso per un detentore diretto, che in Irlanda paga ~52% sui
  dividendi **ogni anno**. Rimisurato con un dividend yield realistico:

  | dividend yield | vantaggio 1990-2023 | vantaggio 1990-2026 |
  |---:|---:|---:|
  | 0,0% (quello che avevo usato) | +1,23 | +1,49 |
  | 1,5% | +0,56 | +0,79 |
  | **2,0%** | **+0,34** | **+0,56** |
  | 2,5% | +0,13 | +0,33 |

  Con il rendimento da dividendo storico dell'S&P (~2%), il vantaggio reale delle
  azioni diritte sull'ETF UCITS è **fra +0,3 e +0,6 punti**, non 2,15 come avevo
  riportato all'inizio né 1,23 dopo la prima correzione. È ancora positivo, ma è
  un ordine di grandezza diverso: non è più la voce dominante del progetto.
- **BUG GRAVE nel regime ETF, trovato al giro 53.** `pay_from_portfolio` riduceva
  le `units` globali ma **non i lotti ETF**: la somma dei lotti restava gonfia e
  ogni deemed disposal successivo tassava quote inesistenti. Su 57 anni azzerava il
  portafoglio (3,48 M di imposte su 344.500 versati). C'era già una pezza al solo
  realizzo finale — avevo notato la deriva e corretto il punto sbagliato. Corretto
  riducendo i lotti pro rata. **Il vantaggio del veicolo scende da +2,15 a +1,23
  punti** su 1990-2023, e cresce con l'orizzonte (+2,12 su 1969-2026).
- **Chi realizza la plusvalenza vale più della strategia.** A parità ESATTA di
  rendimento lordo, spostare la rotazione del momentum settoriale **dentro un
  fondo** invece di farla in conto proprio vale **+2,77 punti di IRR** (giro 53).
  È il numero più grande prodotto da una singola scelta in tutto il progetto, e non
  richiede di prevedere niente: richiede solo di non essere tu a premere i bottoni.
- **Una voce è morta per una ragione nuova, e vale la pena distinguerla.** I LEAPS
  (giri 49 e 52) hanno un vantaggio di +1,34 punti che **non** è fragile al periodo
  (17 finestre di 20 anni su 17, peggior caso +0,42%) né al livello di volatilità
  implicita (regge fino a IV = 1,15 × VIX). Muore a un **rincaro del 10% del premio
  d'ingresso**, cioè 2 punti di nozionale: lo spread normale di un'opzione lunga
  deep ITM poco scambiata. Tutte le altre 51 voci sono morte perché il vantaggio non
  c'era, o era selezione, o lo mangiavano le imposte. Questa muore dentro il **costo
  di transazione dello strumento**, e la soglia è misurata: 2 punti di nozionale.
- **Concentrare sul migliore è la scelta peggiore della griglia.** Il giro 50
  misura 15 celle (1, 3, 5, 10, 25 posizioni × mensile, trimestrale, annuale) sui
  49 settori: il massimo è **top-5 annuale a 10,02%**, contro **11,16%**
  dell'equal-weight statico, e **nessuna cella batte lo statico**. Passare da 1 a 5
  posizioni vale **+5,5 punti di IRR e +27 punti di drawdown**. Il top-1 perde in
  ogni universo e a ogni frequenza; sulle cripto arriva a −96,3% di drawdown.
- **In un sistema di trading a regole, il pezzo banale fa tutto il lavoro.** Il
  giro 51 smonta il sistema EMA 9/21/50/200 pezzo per pezzo: il **solo filtro di
  tendenza** (sopra EMA200 e EMA21>EMA50) ha aspettativa per operazione del
  **13,321%**, il sistema completo con ritracciamento, filtro sul volume, stop,
  parziale a 1:2 e trailing ne ha **0,564%** — un ventiquattresimo. Ogni
  raffinamento tolto migliora il risultato in modo monotono. Il "piano di uscita
  professionale" fa entrare tardi e uscire presto dentro tendenze che il filtro
  semplice avrebbe cavalcato intere.
- **Il premio al rischio di varianza è il fenomeno più solido di tutto il progetto,
  e non è incassabile.** Il VIX supera la volatilità realizzata successiva nell'**83%
  dei mesi** dal 1990, con scarto medio di 3,91 punti e **zero decenni negativi su
  quattro**. È molto più robusto di qualunque anomalia azionaria trovata. E per
  raccoglierlo servono **12 realizzi l'anno**, cioè esattamente il vincolo che ha
  ucciso tutto il resto: vendere put cash-secured ha Sharpe 0,77 contro 0,71 del
  buy&hold e IRR netta **4,98 punti sotto**.
- **Un simulatore va tarato su strumenti reali prima di credergli, e a volte va
  buttato.** Al giro 49 la covered call OTM simulata batteva il benchmark di +0,98
  con DSR 0,997 — la prima promozione apparente in 49 giri. Il confronto con BXM,
  BXY e BXMD reali ha mostrato che l'inflazione da volatilità piatta è
  **+0,55 / +1,51 / +2,56**, crescente con la moneyness: il margine stava dentro
  l'errore. Rifatto con gli indici reali: **−2,92**. La direzione dell'errore era
  pre-dichiarata in coda, ed è stata la ragione per cui l'ho cercata.
- **Tre tentativi falliti di spiegare quali finestre favoriscono cosa, e ho
  smesso.** Giro 46: "sono centrate sui mercati orso", sbagliata. Giro 47: "e'
  rischio di sequenza, sul divario", falsificata. Giro 58: "e' rischio di sequenza,
  sul livello", falsificata con un rapporto che oscilla fra 0,55 e 48,51 e R2
  massimo 0,210. **La regressione su due rendimenti di bordo non e' lo strumento**,
  e una quarta specifica sarebbe cercare quella che funziona invece della
  spiegazione vera. Sostituita da A15, che calcola analiticamente il peso di
  ciascun anno invece di stimarlo. L'unica cosa solida che resta: sul PAC azionario
  b(ultimi 3) = +0,137 e b(primi 3) = **−0,034**, cioe' un piano di accumulo
  preferisce **partenza brutta e finale buono**.
- **Il rischio di sequenza spiega il MONTANTE, non quale allocazione vince.** Il
  giro 47 separa due cose che avevo confuso. Il peso del capitale in un PAC
  ventennale è **9,5:1** fra ultimi e primi tre anni — aritmetica pura, nessun dato
  di mercato. Ma il rapporto fra i coefficienti sul **divario** fra due allocazioni
  è solo **1,2-2,7:1**, con R² 0,28-0,33. Il divario è la differenza fra due
  montanti che percorrono lo **stesso** sentiero di prezzi: il peso del capitale
  agisce su entrambi e si cancella. E b(primi 3) è **positivo**, non trascurabile —
  i due estremi del piano contano in versi opposti.
- **Su 45 finestre di 20 anni il multi-classe perde quasi sempre.** Estendendo al
  1962 (giro 47) l'ERC vince 14 volte su 45 e le altre tre allocazioni 6 su 45: il
  quadro è più duro di quanto sembrasse al giro 46, che vedeva solo il 1976-2026.
  Le 14 finestre recuperate perdono **tutte e quattordici**.
- **Ho nominato due volte di fila un periodo che il disegno non può produrre.** Al
  giro 46 "finestre centrate sul 1969-1982" quando nessuna finestra poteva averci
  il punto medio; al giro 47 "finestre che finiscono nel 1974-1982" quando con
  finestre di 20 anni dal 1962 la fine più vecchia è il 1981. **Prima di scrivere
  una condizione, verificare che il disegno del test possa generarla.**
- **Su vent'anni il divario quasi sparisce, e per un PAC conta la FINE.** Il giro
  46 rifà il confronto su 32 finestre mobili di 20 anni, ognuna un PAC completo:
  l'ERC vince nel **48,4%** dei casi e il divario medio scende da 3,63 punti
  (sull'intera storia) a **0,37**. E le finestre vinte sono tutte e sole quelle che
  **finiscono** fra il 2002 e il 2016, non quelle centrate sui mercati orso. È
  rischio di sequenza: dopo vent'anni di versamenti il capitale è al massimo,
  quindi gli ultimi anni pesano su una somma enorme e i primi su quasi niente.
  Chiudere nel 2009 significa valutare subito dopo un −50%; chiudere nel 2025
  significa valutare dopo quindici anni di rialzo. Aggiunta A13 per misurarlo.
- **Le predizioni sbagliano quasi sempre sui NUMERI, quasi mai sul verso.** Su 22
  voci eseguite, il test di falsificazione è passato 20 volte, ma le clausole
  descrittive (soglie, quote, ampiezze) si sono rivelate sbagliate in almeno sei
  giri — A3, A10, B6, C6, A6, A12. La direzione era giusta, la calibrazione no.
  È l'argomento più forte per scrivere condizioni di falsificazione binarie invece
  che a soglia numerica: le prime hanno retto, le seconde no.
- **E non è colpa del proxy obbligazionario.** Il giro 45 misura lo scarto invece
  di citarlo: una ricostruzione con convessità e rolldown rende **1,58 punti** più
  di quella semplice (avevo assunto 0,3-0,8 — stima sbagliata, per difetto). Ma per
  pareggiare servirebbero **6,5-7,0 punti**, cioè un decennale al 12,5-13% annuo
  per 64 anni. Usando direttamente la ricostruzione migliorata — che a 7,58% annuo
  è probabilmente già troppo generosa — l'allocazione resta 2,4-3,4 punti sotto.
- **Le allocazioni multi-classe perdono per la composizione, non per il fisco.**
  Il giro 44 scompone il divario con l'attribuzione di Shapley su tutti e sei gli
  ordinamenti dei tre fattori — l'ordine sequenziale avrebbe potuto spostare il
  contributo fiscale fra lo 0% e il 31%, cioè decidere l'esito. Risultato:
  composizione 84-92%, imposte 8-15%, **costi di transazione 0,3%**. E la
  controprova che non dipende da nessuna convenzione: con imposte ZERO sul
  ribilanciamento l'allocazione resta 1,8-3,3 punti sotto l'azionario.
- **La frase che riassume tutto il progetto** viene dal giro 43. Il bootstrap a
  blocchi mette il momentum settoriale al **100° percentile** della distribuzione
  nulla: +3,82% annuo lordo, oltre il 99° percentile, il premio è statisticamente
  reale. La stessa strategia sullo stesso benchmark fa **−1,20% di IRR netta**.
  262% di rotazione l'anno al 52% costa più di cinque punti. **Il premio esiste e
  l'investitore perde comunque.**
- **La scelta del benchmark vale più di qualunque parametro.** Contro il PAC
  cap-weighted H5 valeva +2,95 punti; contro l'equal-weight dello **stesso
  universo** su cui sceglie, è negativo in 60 casi su 60 (20 date di partenza × 3
  candidati). Aggiunta D4 per misurare quanto del margine apparente era solo il
  premio dell'equal-weighting.
- **Una condizione di falsificazione può falsificarsi da sola.** D1 chiedeva la
  dispersione su 20 date di partenza con fine fissa: quei 20 campioni condividono
  33-52 anni su 52, quindi la dispersione è piccola per costruzione (0,56 punti).
  La falsificazione è vera sulla lettera e vuota nella sostanza. Aggiunta D3 con
  finestre di lunghezza fissa. **Scrivere la predizione prima non basta: bisogna
  anche che il test possa davvero fallire.**
- **Un bug da fill_value che ha prodotto una falsificazione falsa.** Al giro 37
  `sret.add(carry, fill_value=0.0)` sommava il carry anche dove il CAMBIO non
  esisteva ancora, fabbricando un euro senza rischio di cambio dal 1994 al 1999.
  B2 risultava falsificata con Sharpe 0,58 e skew +1,81; corretta, Sharpe 0,25 e
  skew −0,12. Trovato inseguendo un problema diverso, non perché il numero
  sembrasse strano. Regola che ne esce: **`fill_value` su un allineamento fra
  serie di lunghezza diversa va sempre giustificato per colonna**, perché riempie
  anche dove il dato non manca ma NON ESISTE.
- **Un segnale può avere ragione e costare comunque.** La curva dei tassi (giro
  38) azzecca 12 inversioni su 13 con anticipo mediano di 13 mesi, e perde 1,2-2,6
  punti l'anno: avere ragione con un anno di anticipo significa stare fuori per un
  anno di rialzi. Il drawdown massimo non migliora di un decimo di punto.
- **Tre giri di fila, tre metodi diversi, lo stesso muro.** HRP (31), min-variance
  (32) e Kelly con de-risking (33) migliorano tutti lo Sharpe del PAC azionario —
  il migliore in assoluto è 0,73 contro 0,63 del buy&hold — e perdono tutti fra
  0,4 e 5,5 punti di IRR netta. Non è un caso ripetuto tre volte: è la stessa
  identità vista da tre direzioni. Migliorare il rischio senza leva a buon mercato
  significa ridurre l'esposizione, e ridurre l'esposizione a un asset con premio
  positivo costa montante.
- **Il de-risking sul drawdown è ordinato, non rumoroso.** 12 casi su 12 migliorano
  il drawdown, 0 su 12 migliorano l'IRR, e il costo è monotono nella soglia: al 10%
  costa 1,0-1,7 punti, al 30% ne costa 0,3-0,5 per 12-14 punti di drawdown in meno.
  Sull'indice dal 1926 il buy&hold ha un drawdown massimo del −83,7%: portarlo a
  −57% per 0,40 punti l'anno è una decisione di preferenza, non di ottimizzazione,
  e va presentata come tale a chi deve versare per trent'anni senza smettere.
- **La stima di Kelly su 60 mesi è pro-ciclica.** μ misurato all'indietro è basso
  proprio dopo i crolli, cioè quando i rendimenti attesi sono più alti: il sizing
  taglia l'esposizione nel momento sbagliato. Costa più del de-risking (3,1-5,5
  punti contro 0,3-1,7).
- **Lo Sharpe non è la funzione obiettivo di chi versa €500 al mese.** Il giro 32
  è il caso più pulito: il minimum variance fa esattamente quello che l'anomalia
  low-volatility promette — Sharpe 0,78 contro 0,74, volatilità 13,2% contro
  15,8% — e resta 2,65 punti sotto di IRR netta. Un PAC non può monetizzare uno
  Sharpe migliore senza leva, e la leva costa benchmark+3% (giro 07: −4,18 punti
  con il margine ESMA). La funzione obiettivo è il montante netto, che segue il
  rendimento composto, non il rendimento per unità di rischio. Aggiunta A8 per
  misurare esplicitamente la leva 1,20× invece di lasciarlo a un conto a mente.
- **Il drawdown non è un fenomeno di volatilità, è un fenomeno di correlazione.**
  Avevo previsto che il min-variance tagliasse oltre 10 punti di drawdown: ne ha
  tagliati 4,2, a fronte di 2,6 punti di volatilità in meno. Un ottimizzatore che
  minimizza la varianza su 60 mesi di storia normale non ha informazione sulle
  code, e nel 2008 i settori difensivi sono scesi con tutto il resto.
- **"Minimum variance su 49 settori" è in realtà una scommessa su 7 settori.**
  L'84% del portafoglio sta in cinque posizioni, 7,5 posizioni effettive su 49,
  con numero condizionale mediano della covarianza a 18.569. Lo shrinkage di
  Ledoit-Wolf recupera solo +0,14 punti: la sconfitta **non** è errore di stima,
  è il metodo. È una diagnostica che vale la pena rifare su ogni ottimizzatore.
- **HRP è meno stabile di inverse-variance**, non più (0,283 contro 0,109 di
  movimento medio dei pesi per ribilanciamento). Il clustering a legame singolo
  riorganizza l'albero in modo discreto quando le correlazioni si muovono di poco.
  La tesi del paper è però contro il **min-variance**, non contro il metodo
  diagonale: confronto rimandato ad A7, dopo A3.
- **I premi AQR non sopravvivono ai costi retail.** L'overlay multi-stile rende
  3,3-3,4%/anno lordo contro un drag di implementazione stimato al 7,5%/anno.
  È negativo prima ancora di iniziare.
- **La stabilità misurata al giro 43 non esisteva: era il disegno del test.**
  D1 faceva partire il campione in 20 anni diversi con la fine sempre al 2026, e
  due suoi campioni condividono in media **l'85,5% degli anni** (massimo 98,1%).
  Su finestre mobili di lunghezza fissa la sovrapposizione scende al **13,9%**, e
  l'ampiezza dell'extra-rendimento passa da **0,56 a 10,19 punti — diciotto
  volte**. Regola generale che ne esce: *quando si misura la dispersione di una
  statistica su sottocampioni, la prima cosa da calcolare è la sovrapposizione fra
  i sottocampioni*, prima di qualunque risultato. Una dispersione bassa fra
  campioni che si sovrappongono al 90% non dice nulla.
- **Allungare l'orizzonte peggiora i candidati invece di migliorarli.** Da finestre
  di 10 anni a finestre di 20, la quota di vittorie di H5 scende da 67,4% a 38,9%,
  quella di H4 da 43,5% a 30,6%, e C1 passa da 30,4% a **0 su 36**. È l'opposto di
  quel che fa un premio vero, che con l'orizzonte emerge dal rumore. Il motivo è
  che il costo fiscale si accumula deterministicamente ogni anno mentre il
  vantaggio lordo non si accumula affatto: il tempo lavora per l'erario.
- **H5 vince due finestre decennali su tre e rende zero.** 31/46 vittorie, mediana
  +0,54%, media **+0,16%**. Tutta la differenza sta in quattro finestre, e sono le
  quattro che contengono il **2008** (−5,78%, −5,69%, −3,61%, −3,24%). È la firma
  di una posizione short-volatility, non di un premio. Da qui la voce D5: se il
  disaccordo fra "vince spesso" e "rende in media" è generale, ogni quota di
  vittorie riportata in questo progetto va riletta.
- **Limite del motore fiscale, misurato e delimitato (non un bug).** `tax.py` tiene
  **un solo costo fiscale aggregato** per il portafoglio e, quando la strategia
  ruota, realizza una quota *proporzionale* della plusvalenza aggregata. Nella
  realtà si vendono posizioni specifiche, e vendere un perdente cristallizza una
  **minusvalenza** anche mentre il portafoglio nel complesso è in utile. Ho scritto
  un motore per posizione (`val[]`/`bas[]` separati, vendite riconosciute
  singolarmente) identico in tutto il resto — stessi flussi, stessi costi, stessa
  regola di fine anno — e ho confrontato:

  | strategia (49 settori, 1990-2026) | IRR aggregata | IRR per posizione | delta |
  |---|---:|---:|---:|
  | momentum top-1 mensile | 9,31% | 9,31% | +0,00 |
  | momentum top-3 mensile | 12,66% | 12,81% | +0,15 |
  | momentum top-10 mensile | 9,99% | 10,16% | +0,17 |
  | momentum top-25 mensile | 9,16% | 9,40% | +0,24 |
  | top-5 mensile, aliquota 52% | 8,23% | 8,52% | **+0,29** |
  | top-25 mensile, aliquota 52% | 6,73% | 7,14% | **+0,41** |
  | equal-weight ribilanciato | 8,83% | 8,78% | **−0,05** |

  Controlli: con **un solo asset** i due motori coincidono a sei decimali, e col
  **top-1** coincidono esattamente (una posizione alla volta *è* il portafoglio) —
  quindi il delta misura l'effetto, non un bug. Il verso è quello atteso: la
  contabilità aggregata **penalizza** chi ruota (fino a +0,41 punti) e **favorisce**
  chi ribilancia verso pesi fissi (−0,05), perché quest'ultimo vende i vincitori.
  **Nessun verdetto del progetto cambia**: il divario più stretto mai registrato è
  1,14 punti (F2, top-5 annuale contro equal-weight statico), e la correzione lì
  vale +0,10 al 33% e +0,15 al 52%. Resta come limite dichiarato, non corretto:
  riscrivere `tax.py` per posizione cambierebbe di ±0,4 punti conclusioni che
  stanno tutte oltre 1 punto dal confine.
- **Il rischio di sequenza in un PAC vale 6-7, non 9,5 — e i giri 47 e 58
  cercavano un bersaglio che il meccanismo non produce.** La sensibilità
  dell'IRR al rendimento dell'anno k si scrive invece di stimarla:
  `∂y/∂log(1+ρ_m) = A_m / (∂Φ/∂y)`, con `A_m` il montante a scadenza dei soli
  versamenti fino a m. Il profilo è **monotono crescente in 80 finestre storiche
  su 80**, ma il rapporto ultimi/primi triennio **dipende dal livello dei
  rendimenti**: 10,27× al 2%, 6,91× all'8%, 5,61× al 12%, mediana storica 5,91×.
  Il punto: erano **tre quantità diverse** trattate come una sola —

  | quantità | valore |
  |---|---:|
  | peso aritmetico puro dei versamenti, (18+19+20)/(1+2+3) | **9,50×** |
  | capitale esposto, capitalizzato all'8% | **24,72×** |
  | sensibilità dell'IRR, ∂IRR/∂log(1+R_k), all'8% | **6,91×** |

  Due effetti opposti, nessuno dei due presente nel 9,5: il capitale accumulato
  **cresce** con k (spinge sopra), il tempo di capitalizzazione residuo **scende**
  con k (riporta sotto). Un rendimento del ventesimo anno colpisce molto capitale
  ma non ha più tempo di comporsi. **Regola generale**: prima di regredire per
  stimare una sensibilità, verificare se si può derivare — e se il valore atteso
  che si sta cercando è davvero la quantità che il modello produce.
- **Il controllo a differenze finite ha pagato, di nuovo.** Al giro 61 la prima
  stesura aggregava i mesi con una somma invece che con una media, e il rapporto
  analitico/numerico è uscito **0,0833 = 1/12 su tutti e venti gli anni**. Un
  errore di scala ha questa firma: costante su ogni elemento. Il rumore no.
  Nessun risultato del giro sarebbe cambiato di segno, ma i pesi non sarebbero
  stati quello che dicevo. **Ogni derivata analitica del progetto va verificata
  contro una differenza finita prima di essere letta.**
- **La rotazione si misura fra dove sei e dove vuoi essere, non fra due target
  né fra due posizioni.** Il progetto ha usato due convenzioni, entrambe
  sbagliate e in direzioni opposte:

  | | definizione | dove | errore |
  |---|---|---|---|
  | (a) target | \|W_tgt,t − W_tgt,t−1\|/2 | `bench.wbacktest` | va a **zero** su pesi costanti |
  | (b) detenuti | \|W_der,t − W_der,t−1\|/2 | `round31/32.backtest` | conta il **drift** come scambio |
  | **(c) vera** | \|W_tgt,t − W_der,t\|/2 | — | corretta |

  Il caso che le smaschera entrambe è l'equal-weight **annuale**: rotazione vera
  **0,071×/anno** contro 0,239× della (a) e 0,251× della (b). Chi ribilancia una
  volta l'anno compra e vende **solo a gennaio**; negli altri undici mesi non
  tocca niente, e le due convenzioni sbagliate registrano movimento ogni mese.
  L'errore vale **0,32 punti di IRR in media**, con un massimo di **1,35 punti**
  sull'equal-weight mensile — il benchmark più usato del progetto, che per
  trentatré giri ha ribilanciato gratis.
- **L'errore non aveva un verso solo, e questo era il punto della voce D6.**
  Avevo registrato la tesi che favorisse i benchmark statici contro le strategie
  che ruotano. Misurato: 4 valutazioni su 9 sottostimano, **5 su 9 sovrastimano**.
  I giri 31 e 32 *penalizzavano* HRP e min-variance addebitando come costo il
  puro drift dei pesi. Regola: **quando si registra un difetto, la direzione del
  suo effetto è un'ipotesi da testare, non un corollario ovvio.**
- **Stesso errore, terza forma, terzo giro di fila.** Al 60 avevo costruito un
  "equal-weight annuale" tenendo fermi i pesi target a 1/N — che è
  ribilanciamento mensile travestito — e produceva un benchmark identico a
  quello mensile. Al 63 ci sono ricascato nella prima stesura, con lo stesso
  sintomo (11,16% contro 11,16%). Il commento sta ora dentro `round63.ew_drift`.
  Un test che dà **esattamente** lo stesso numero di un altro test è quasi sempre
  lo stesso test.
- **Correggere la rotazione può spostare una strategia di REGIME FISCALE, e
  quello non è un aggiustamento, è un gradino.** Il top-5 annuale sui 49 settori
  aveva rotazione misurata **0,83×/anno** e pagava il 33%; con la rotazione vera
  ha **1,022×**, scavalca la soglia del 100%/anno e paga il **52%**. Il divario
  contro il suo benchmark non si chiude — si **allarga da −1,14 a −1,92**. Lo
  stesso succede al top-3 annuale (1,053×). **Ogni strategia con rotazione
  nominale fra 0,7× e 1,0× va rimisurata prima di attribuirle un'aliquota**: è la
  fascia in cui un errore di misura del 20% cambia l'imposta di diciannove punti.
- **Il "massimo di concentrazione" della griglia F2 era il costo di rotazione non
  addebitato.** Al giro 50 la griglia annuale aveva un massimo interno a 5
  posizioni (relazione "a campana"); con la rotazione vera è **monotona
  crescente**: 4,84 → 7,74 → 8,73 → 8,91 → **9,65** da 1 a 25 posizioni. Non c'è
  optimum di concentrazione. Più si diversifica, meglio va — e comunque sotto
  l'equal-weight annuale (10,65%).
- **Il DSR va letto sul registro cumulato, e la differenza è enorme.** Il top-5
  annuale ha DSR **0,9743 su N=15** (la griglia) e **0,7691 su N=1.175** (il
  registro). Il primo numero dice "dentro questa griglia non è il massimo di
  quindici estrazioni casuali", il secondo dice "dentro questo progetto sì".
  La regola di promozione di STATE.md usa il secondo — e va ricordato quando una
  voce della coda lega la propria condizione di falsificazione a "DSR > 0,95"
  senza specificare N: **un DSR alto su una strategia che perde contro il proprio
  benchmark non è un candidato**, è la conferma che lo Sharpe non è la funzione
  obiettivo di un PAC.
- **Il calendario del ribilanciamento è un parametro libero che il progetto ha
  usato per sessantacinque giri senza contarlo.** La stessa strategia — momentum
  12-2, top-5, ribilanciamento annuale, 49 settori, 1969-2026 — vale **+1,51 o
  −1,92** contro lo stesso benchmark a seconda che si ribilanci a **gennaio
  civile** o **ogni 12 mesi a partire dall'inizio del campione**:

  | strategia | calendario | rotaz. | aliquota | IRR | vs EW annuale |
  |---|---|---:|---:|---:|---:|
  | top-5 | gennaio | 0,962× | 33% | 12,16% | **+1,51** |
  | top-5 | ogni 12 mesi | 1,022× | 52% | 8,73% | **−1,92** |
  | top-10 | gennaio | 0,901× | 33% | 10,98% | +0,33 |
  | top-10 | ogni 12 mesi | 0,951× | 33% | 8,91% | −1,74 |

  Per il top-5 il salto attraversa anche la soglia fiscale, ma non è solo quello:
  il top-10 e il top-25 restano al 33% e si spostano comunque di 2,07 e 0,53
  punti. **Ogni backtest con ribilanciamento periodico ha dodici implementazioni,
  e sceglierne una dopo aver visto i risultati è selezione non contata.**
- **La cosa più vicina a un candidato in 65 giri**: momentum 12-2 top-10 annuale
  a calendario gennaio, **+0,33 punti** contro l'equal-weight annuale
  correttamente addebitato, DSR **0,9424**. Sotto soglia, non pre-registrato, e
  il margine sta dentro il rumore misurato al giro 59 (±5-10 punti su finestre
  decennali). **Non promosso**, ma registrato perché è il massimo che il progetto
  ha prodotto.
- **`lab.deflated_sharpe` con `var_sr` di default dà SR0 implausibili.** Stimando
  la dispersione degli Sharpe sul registro **intero** — che mescola famiglie con
  profili di rischio diversi — esce SR0 = **1,78 per periodo**, cioè oltre 6
  annualizzato, e il DSR collassa a 0,0000 per qualunque candidato. Con `var_sr`
  stimata sulla famiglia del giro, SR0 = 0,0921 e il DSR diventa leggibile.
  **Quando una voce della coda scrive "DSR > 0,95" deve anche dire come si stima
  `var_sr`**, altrimenti la condizione è ambigua per un fattore venti.
- **La soglia del 100% di rotazione è sfruttabile, e vale meno di un punto.**
  Vincolando il ribilanciamento a un budget di 0,95×/anno (esecuzione parziale
  verso il target) le celle di F2 che stavano appena sopra la soglia rientrano al
  33% e guadagnano: top-3 **+0,79**, top-5 **+1,02**. Ma il controllo è quello che
  conta: il **top-10, già al 33%, perde −0,09**. Vincolare *di per sé* non giova —
  giova solo riattraversare la soglia. Costo del vincolo: **0,11-0,59 punti di
  CAGR lordo** contro **19 punti di aliquota** risparmiati. Resta ingegneria
  fiscale, non una strategia: la migliore cella vincolata è ancora **−0,90**
  dall'equal-weight annuale.
- **Lo statistical jump model non identifica regimi utili: identifica quanto
  spesso gli si dà retta.** Al crescere della penalità di salto λ la correlazione
  col filtro a media mobile 10 mesi **crolla da 0,610 a 0,006**, l'esposizione
  sale dal 59% all'**84,4%**, i salti scendono a **0,06 l'anno** (uno ogni
  diciassette) e il divario contro il buy&hold si chiude da **−4,77 a −1,63**.
  Il segnale ha valore marginale **negativo a ogni λ**: l'unica cosa che migliora
  il risultato è avvicinarsi al buy&hold. Non esiste un λ in cui identificare il
  regime paghi.
- **λ è però un modo diretto di comprare l'aliquota.** Fra λ=10 e λ=25 la
  rotazione passa da 2,74× a 0,88×/anno e il regime fiscale dal **52% al 33%** —
  la stessa soglia del giro 66. È un controllo molto più maneggevole di un
  parametro di lisciatura, e vale la pena ricordarselo se un giorno servisse
  ridurre la rotazione di un candidato vero.
- **Il lato corto sull'azionario è un puro sottrarre, misurato.** Su 21
  configurazioni la long/short perde contro la long-only in **21 su 21**; a λ=25 e
  λ=50 la strategia **perde denaro in valore assoluto** (IRR −0,45% e −2,37%) su
  ottant'anni. Il costo del solo lato corto arriva a **−7,20 punti**. La variante
  a leva 0,5 sul corto sta sempre esattamente in mezzo fra long-only e
  long/short: **dimezzare lo short dimezza il danno**, che è la controprova più
  pulita che il lato corto non contenga informazione — solo il segno sbagliato
  del premio azionario, moltiplicato per il tempo passato fuori dal mercato.
- **Il grado di libertà del calendario esiste solo per chi seleziona, ed è
  proporzionale a quanto concentra.** Ampiezza dell'IRR fra il mese di
  ribilanciamento migliore e il peggiore, 49 settori 1969-2026:

  | strategia | posizioni | ampiezza |
  |---|---:|---:|
  | equal-weight annuale | 49 | **0,14%** |
  | momentum top-25 | 25 | 0,90% |
  | momentum top-10 | 10 | 2,21% |
  | momentum top-5 | 5 | **3,65%** |

  Un portafoglio passivo rende lo stesso in tutti e dodici i mesi. Cinque
  posizioni comprano **3,65 punti di arbitrarietà**. Quello che al giro 65
  sembrava il vantaggio del top-5 era in buona parte il suo grado di libertà.
  **Regola operativa**: una strategia annuale va riportata con la **mediana dei
  dodici mesi**, e tutte e dodici vanno a registro. Il giro 68 lo ha fatto: il
  registro è cresciuto di 48 tentativi, non di 4.
- **L'anomalia di fine anno ricompare dal lato del ribilanciamento.** Gennaio e
  dicembre sono i due mesi migliori per tutte e tre le varianti momentum, e la
  differenza fra dicembre e luglio vale **~2,3 punti** di IRR sul top-5. È lo
  stesso effetto che il giro 29 aveva misurato con **t = 7,04** e che la
  strategia costruita apposta non riusciva a monetizzare (−7,26 punti). Chi
  sceglie il mese di ribilanciamento guardando i risultati lo sta incassando come
  se fosse alfa.
- **Il conto va fatto in euro, e costa 0,6-0,8 punti l'anno.** Tutti i giri
  1-68 misurano in dollari; un residente irlandese versa e incassa euro. Sul
  1971-2026 l'euro (e prima il marco) si è rafforzato, e l'IRR in euro
  dell'azionario USA è **0,77 punti sotto** quella in dollari — 0,72 per
  l'equal-weight, 0,46 per il momentum mensile. **Il livello di ogni numero del
  progetto va abbassato di circa mezzo punto.**
- **Ma nessun verdetto relativo cambia**: il cambio è un fattore quasi comune, e
  in differenza resta al massimo **0,25 punti**. Il residuo non è zero e cresce
  con la rotazione — 0,00× → −0,06, 0,79× → +0,14, 2,81× → +0,25 — perché le
  imposte si pagano su plusvalenze in euro e chi realizza più spesso cristallizza
  più spesso anche il cambio. La correlazione è +0,985 **su tre punti soli**:
  l'ordinamento è quello previsto, la taglia no.
- **Il cambio non copre: somma.** La volatilità in euro è più alta in tutte e
  quattro le strategie (+0,46 / +1,10 punti). Meno di quanto avessi previsto
  (+2/+5), ma il segno esclude che il rischio di cambio compensi quello azionario.
- **Attenzione ai raccordi fra serie con convenzioni diverse.** EXGEUS è una
  *media* mensile, DEXUSEU ricampionato è un *fine mese*: al raccordo del 1999 le
  due differiscono dell'**1,93%**. Riscalando, le IRR si spostano di 0,03-0,04
  punti in modo uniforme — trascurabile qui, ma è il tipo di discontinuità che va
  cercata e quantificata ogni volta che si incollano due fonti.
- **L'IRR è quasi cieca a un PAC irregolare: serve il montante.** Su 64 finestre
  ventennali, saltare **24 versamenti** (il 10% del capitale) costa **−8,66% di
  montante** e **+0,021 di IRR**; riscattare il **30%** del portafoglio costa
  **−22,51% di montante** e **−0,016 di IRR**. Un evento che porta via un quinto
  del risultato finale sposta il tasso di sedici millesimi di punto. Il motivo è
  che l'IRR misura quanto rende ogni euro versato, non quanti euro si versa.
  **Regola**: quando due PAC hanno flussi diversi, riportare il montante. Fra le
  voci già eseguite nessuna è colpita — confrontano tutte PAC a flussi identici.
- **Il costo di interrompere dipende da quando, per un fattore cinque.** Il calo
  del montante va da **−21,13%** (interruzione al primo anno) a **−4,05%**
  (al diciottesimo), monotono. Avevo previsto 8-12%: quello è il *valore medio*,
  non l'intervallo. Gli euro saltati presto si sarebbero composti per vent'anni.
- **L'effetto sull'IRR cambia segno al sesto anno**, ed è il profilo del giro 61
  visto dal lato dei versamenti. L'IRR è una media dei rendimenti per euro
  pesata per il tempo che ogni euro resta investito: togliere i versamenti
  **tardivi alza la media**, perché elimina gli euro che si compongono meno.
  Quindi sospendere tardi fa *salire* l'IRR mentre il montante cala comunque —
  è l'IRR che mente, non il montante. **Simmetricamente**: interrompere costa di
  più **presto**, riscattare costa di più **tardi**, perché tardi il 30% è il 30%
  di un portafoglio molto più grande.
- **La correzione della rotazione conta per i portafogli lenti e non per quelli
  veloci.** Sul momentum top-10 mensile la rotazione vera passa da **2,676× a
  2,828×** l'anno e l'effetto sull'IRR è **−0,005 punti**: praticamente zero.
  Chi realizza il 22% del portafoglio ogni mese ha la base imponibile **già
  azzerata in continuo**, quindi spostarla al 24% non cambia niente. È il
  complemento esatto del giro 63, dove la stessa correzione valeva **1,35 punti**
  sull'equal-weight a 0,20×/anno. **La correzione è grande dove la rotazione è
  piccola.** La predizione di K3 diceva il contrario ed era sbagliata.
- **Il wrapper aiuta solo se ruoti**, ed è il risultato operativo più netto del
  progetto:

  | chi sei | veicolo migliore | margine |
  |---|---|---:|
  | ruoti spesso (momentum top-10, 2,8×/anno) | **fondo / ETF UCITS** | **+0,64** |
  | stai fermo (cap-weight buy&hold) | **azioni dirette** | **+1,09** |

  Due segni opposti che dicono una cosa sola: **l'ETF UCITS compra il diritto di
  non realizzare e lo paga col deemed disposal**. Chi non realizzerebbe comunque
  sta comprando un diritto che non usa. Il vantaggio del diretto **cresce con
  l'orizzonte** (+0,34 su 1990-2023, +0,56 su 1990-2026, **+1,09 su 1969-2026**),
  perché sono sette cicli di prelievo forzoso al 41/38% contro un solo 33% finale.
- **Il costo di realizzare, misurato in isolamento, è +3,43 punti** — a parità
  esatta di rendimento lordo, fra chi ruota in conto proprio e chi lascia ruotare
  il fondo. Non è un vantaggio disponibile: nessuno lo incassa scegliendo un
  veicolo, si può solo evitare di perderlo. Di quei 3,43, **+2,77 erano già noti
  al giro 53**, **+0,66 sono i dividendi** tassati al detentore diretto (giro 56)
  e **+0,00 è la rotazione**.

## La regola per aprire l'holdout — IN VIGORE dal giro 72

Scritta al giro 72, quando non esisteva nessun candidato che potesse passarla.
Un candidato merita l'holdout **solo se passa tutti e quattro i cancelli**.

| | cancello | soglia |
|---|---|---|
| **G1** | margine | IRR ≥ benchmark **+1,00 punto**, come **mediana sui dodici calendari** di ribilanciamento |
| **G2** | Deflated Sharpe | **> 0,95** su N = registro **cumulato**, `var_sr` stimata sulla famiglia del giro |
| **G3** | stabilità | extra positivo in **≥ 2/3** delle finestre decennali mobili **E** mediana degli extra **> 0** |
| **G4** | calendario | margine positivo in **≥ 10 dei 12** mesi di ribilanciamento (le strategie mensili lo passano per costruzione) |

Benchmark: **equal-weight annuale** dello stesso universo, con la rotazione vera.
Se un candidato passa, l'holdout si apre **una volta sola, su quello solo**, e il
risultato si registra qualunque sia. L'apertura è un **atto separato**, non un
sottoprodotto di un giro.

**Applicata ai dodici candidati riproducibili sui 49 settori (1969-2009): zero
passano.**

> **ESITO FINALE, GIRO 78 — la regola è stata passata, l'holdout è stato aperto,
> il candidato ha perso.** Margine **−0,95** su 2010-2026, **negativo in 12
> calendari su 12** (banda −1,04 … −0,82). Rotazione 3,804× (52%), drawdown
> −31,38% contro −25,50%. Il premio **lordo** è sopravvissuto (CAGR 13,65% contro
> 13,34%), l'investitore no. E il controfattuale: **anche al 33% il candidato
> avrebbe fatto +0,90, sotto il suo stesso cancello di +1,00**. **L'holdout è ora
> bruciato e non si riapre.**
>
> **Il cancello che è crollato è G3**, cioè quello che in campione era il più
> forte: **93,1% di finestre decennali positive nel train contro 37,5%
> nell'holdout**, mediana da +2,23 a −0,16. Un cancello che passa al 93% dentro e
> al 37% fuori non misurava la stabilità: misurava il campione. Le 29 finestre del
> train si sovrappongono in media all'85,5% (misurato al giro 43 su D1 e mai
> applicato ai cancelli), quindi «27 successi su 29» è lo stesso pezzo di storia
> contato 27 volte. È la voce **O3**.
>
> Lo scarto train→holdout è **2,13 punti**, dello stesso ordine dei gradi di
> libertà già misurati uno per uno: **3,94** lo skip (giro 76), **3,65** il
> calendario su un top-5 (giro 68), **5,81-10,19** la finestra temporale (giro
> 59). **Il candidato non è stato smentito da un evento raro: è rientrato nella
> dispersione che il progetto aveva già misurato tre volte.**
>
> **E il giro 79 ha mostrato che era prevedibile senza l'holdout.** Deflatando sul
> **margine** invece che sullo Sharpe — stessa formula di G2, applicata alla
> grandezza su cui la selezione è davvero avvenuta — la soglia per una famiglia di
> venti celle con σ 1,15 è **+2,19**, e il candidato ne aveva **+1,18**. Sarebbe
> stato fermato prima di arrivare all'holdout, e con lui **tutti e 32** i
> candidati mai registrati.

> **AGGIORNAMENTO DEL GIRO 77 — la regola è stata passata.** Un tredicesimo
> candidato, che al giro 72 non esisteva perché lo **skip** non era ancora un
> parametro dichiarato, passa tutti e quattro i cancelli: **momentum 12-3 top-5
> mensile**, G1 **+1,18** (mediana su 12 calendari), G2 **0,9907**, G3 **93,1%**
> con mediana +2,23, G4 per costruzione. L'apertura dell'holdout è un **atto
> separato** ed è pre-registrata come voce **N1**, con la predizione — margine
> **negativo, fra −3 e 0** — scritta prima di guardare. **Dopo N1 l'holdout è
> bruciato**: qualunque cosa dica, non si riapre.

- **G1 elimina 12/12.** Nessuno arriva a un punto di margine sull'equal-weight
  annuale. Il migliore è **momentum top-5 mensile a +0,56**, e per arrivarci
  serve una rotazione di 2,8×/anno, cioè l'aliquota al 52%.
- G2 elimina 10/12, G3 elimina 10/12, **G4 elimina 7/12**.
- **La predizione che il calendario fosse il cancello più selettivo è sbagliata**,
  e la ragione è che cinque candidati su dodici sono mensili e lo passano per
  costruzione. Ristretto ai **sette annuali**, G4 ne elimina **sei su sette**.
  Entrambe le letture vanno tenute: quella richiesta dalla predizione è falsa,
  quella condizionata è vera, e la seconda non salva la prima.
- **Il più vicino al bersaglio in 72 giri**: momentum 12-2 top-5 mensile passa
  G2 (DSR **0,971**) e G4, e fallisce G3 per **sette decimi di punto percentuale**
  (66% contro 66,7%). Resta comunque a mezzo punto dal margine richiesto.
- **Il ribilanciamento a mezzanotte non nasconde niente: ordinare il giorno dopo
  costa 0,08 punti** sul momentum top-10 e 0,22 sul top-5. È la convenzione usata
  in settantatré giri, ed è la prima volta che viene misurata sui **giorni**
  invece che sui mesi. Entrambi i valori stanno dentro il rumore e molto sotto i
  divari con cui il progetto ha respinto le strategie.
- **Ma il margine a un dato ritardo non è un numero preciso.** Sul top-5 il
  margine oscilla fra −1,13 e +0,86 al variare del ritardo, **±0,5 punti senza
  tendenza**. È la stessa cosa che il giro 59 aveva misurato dal lato delle
  finestre temporali e il giro 68 dal lato del calendario: **la dispersione di
  questi margini è dello stesso ordine dei margini stessi**, da qualunque lato la
  si guardi.
- **Un massimo su dieci celle non è un risultato, ed è ora una regola.** Il top-5
  ritardato di 20 giorni fa +0,86 contro il −0,87 senza ritardo. Non l'ho
  registrato come candidato: è il massimo di dieci celle, la **mediana dei cinque
  ritardi è −0,65**, e non passa il cancello G1 della regola del giro 72, che
  chiede +1,00 **come mediana**. L'ipotesi meccanica che ne segue — ritardare di
  venti giorni un segnale 12-2 equivale a usare un 12-3 — va testata
  **direttamente sul 12-3**, ed è la voce L4.
- **Il modello di costo del progetto (0,15% round-trip) è conservativo nella
  direzione giusta, non in quella sbagliata.** Con costi da broker retail vero
  (€1,50/ordine + 0,05% di spread) il divario momentum-meno-equal-weight si
  **allarga a favore del momentum** di +0,47/+0,66 punti. Due gambe, che spingono
  nello stesso verso: la commissione fissa è un costo **per posizione** e il
  benchmark ne ha 49 (636 ordini/anno contro gli 89 del top-5 annuale), mentre lo
  spread retail (0,05%) è **un terzo** del round-trip proporzionale, quindi su un
  patrimonio grande il retail costa **meno** del modello del progetto — il top-5
  mensile ha IRR retail *superiore* alla proporzionale.
- **Ma il modello di costo e la scelta del veicolo non sono separabili.** Quel
  +1,30 non è un vantaggio del momentum: è l'artefatto di far pagare al benchmark
  un modo di implementarlo che nessuno userebbe. Un equal-weight su 49 settori a
  €500 al mese in azioni singole brucia il **14,7%** del versamento in
  commissioni; si compra come **fondo**, dove la commissione fissa è una sola.
  Confrontare due strategie con lo stesso modello di costo ha senso solo se
  entrambe si implementano allo stesso modo. Si aggancia al giro 71: chi sta fermo
  su tante posizioni vuole il fondo **per le commissioni**, non per le imposte.
- **La soglia di antieconomicità di un PAC frammentato è `P × €1,50 / 1%`**: con
  P = 49 posizioni serve una rata di **€7.350/mese** perché i costi del versamento
  restino sotto l'1%. A €750 se ne va il 14,7%; a 5 posizioni la soglia è €750, a
  10 è €1.500.
- **Versare in un ordine solo non serve a chi è diversificato.** L'equal-weight
  passa da 636 a 600 ordini/anno e l'IRR retail resta identica (9,42%): gli ordini
  si spostano dal versamento al ribilanciamento, che ri-tocca comunque tutte e 49
  le posizioni. Concentrare il versamento aiuta solo se il portafoglio è già
  concentrato (top-5 mensile: 133 → 86 ordini/anno).
- **Nessun risultato di strategia sopra un punto sopravvive alla rilettura del
  registro**, e la verifica è automatica, non a memoria (giro 75). Delle 1.365
  righe registrate, **213 (15,6%) hanno extra ≥ +1,00**, in **30 ipotesi
  distinte**: cripto (sopravvivenza selezionata: allargare l'universo **alza** il
  buy&hold da 22,6% a 55,3%; DSR 0,443 e 0,880), anomalie pubblicate (premi
  lordi, 2 su 201 passano i filtri), candidati storici (negativi in **60/60**
  contro l'equal-weight dello stesso universo, **12/12** eliminati da G1), opzioni
  (il premio esiste, incassarlo perde −4,98/−2,92), e nove gruppi che **non sono
  margini di strategia**. Mediana dell'extra su tutto il registro: **−1,32**;
  quota positiva **30,3%**; sotto −1,00 sta il **55,9%**.
- **I numeri del progetto che reggono sono dodici**, non meno di dieci come avevo
  previsto: sette costi o soglie (rotazione vera 1,35 · soglia del 100% come
  gradino · calendario 3,65 contro 0,14 · veicolo +1,09/+0,64 · costo di
  realizzare +3,43 · soglia retail €7.350 · quota fiscale massima 15,3%) e cinque
  misure di fragilità o metodo (ampiezza decennale 5,81-10,19 · il benchmark
  spiega il 263-398% · l'IRR cieca a −22,51% di montante · 2 anomalie su 201 · il
  peso analitico 5,91×). **Nessuno di essi è un margine di strategia**, e questa
  metà della predizione è centrata.
- **La stessa forma di artefatto è comparsa tre volte, e tre volte è stata
  riconosciuta solo perché la regola era scritta prima**: il +13,11 di Kronos
  (giro 26, DSR 0,999, ma è ETH e su BTC fa −22,7, χ² p = 0,671), il +1,51 di
  gennaio (giro 65, mediana dei dodici mesi −0,46), il +0,86 del ritardo a venti
  giorni (giro 73, massimo di dieci celle, mediana −0,65). **Un massimo su N celle
  non è un risultato.**
- **Due raccomandazioni del giro 29 sono ritirate, non aggiornate** (giro 75). Il
  **+1,72 del veicolo** è oggi **+0,34** sulla stessa finestra 1990-2023 — catena
  +1,72 → +2,01 (base fiscale) → +2,15 → +1,23 (lotti ETF) → +0,34 (dividendi),
  un fattore cinque in quattro misurazioni successive dello stesso oggetto. E il
  **trend following levereggiato** cade due volte: con il margin call ESMA
  modellato dà **−4,18** (giro 07), e testato sistematicamente al giro 53
  **nessun filtro di tendenza batte il buy&hold** (il migliore perde 2,51 punti,
  e vince fra i filtri solo perché ruota 0,19×/anno).
- **Lo skip del momentum è un parametro libero mai dichiarato, e vale 3,94 punti**
  (giro 76). Il profilo del margine del top-5 mensile al variare dello skip k è
  **+0,65 / −0,87 / +1,18 / −0,39 / −2,75** per k = 1, 2, 3, 4, 6: cambia segno
  tre volte con salti di due punti. È **lo stesso ordine di grandezza del
  calendario** (3,65 al giro 68), e il gruppo A del giro 05 lo aveva fissato a 1
  senza contarlo. Moltiplicati fra loro, skip e calendario rendono lo spazio di
  ricerca vero del momentum settoriale **un ordine di grandezza più grande** di
  quello che il registro ha contato.
- **Ritardare l'esecuzione di venti giorni è quasi un'identità con lo skip di un
  mese in più**, non una scoperta: 12-2 ritardato di 20 giorni e 12-3 senza
  ritardo distano **0,33** (top-5) e **0,28** (top-10). Il +0,86 del giro 73 non
  era rumore da chiudere — **era lo skip**. Ma il profilo dello skip è a sua volta
  rumore, e le due cose non si annullano.
- **Un buco nella regola del giro 72, trovato applicandola** (giro 76). G1 chiede
  la mediana del margine sui **dodici calendari di ribilanciamento**, ma una
  strategia **mensile** non ha quel grado di libertà: ce l'ha il suo **benchmark
  annuale**. Sia il giro 72 sia il giro 76 hanno usato il **solo gennaio**. La
  mediana va presa sui dodici calendari del benchmark, ed è la voce M1.
- **Per la prima volta in settantasei giri esiste una cella che passa tre cancelli
  su quattro**: momentum **12-3 top-5 mensile**, margine **+1,18** (G1 come
  misurato), **DSR 0,9870** (G2, con la `var_sr` che la regola prescrive), G4 per
  costruzione. **G3 non è mai stato misurato.** Non è una promozione e non apre
  l'holdout — la regola dice che l'apertura è un **atto separato** — ed è il
  massimo di dieci celle, la quarta volta che il progetto incontra questa forma
  (Kronos +13,11 su 2 simboli, gennaio +1,51 su 12 calendari, il ritardo +0,86 su
  10 celle). Le tre letture del DSR: **0,9870** con la `var_sr` della regola,
  0,9984 con N=10, **0,0000** col registro intero (SR0 1,7631 per periodo, oltre 6
  annualizzato: non credibile, come al giro 65).
- **La regola del giro 72 è stata passata** (giro 77). Il momentum **12-3 top-5
  mensile** passa **tutti e quattro** i cancelli: G1 mediana **+1,18** sui dodici
  calendari del benchmark (positivo in **12/12**, minimo +1,04), G2 **DSR 0,9907**,
  G3 quota **93,1%** su 29 finestre decennali con mediana **+2,23**, G4 per
  costruzione. IRR 11,27% contro 10,09% del benchmark, rotazione 3,284×, aliquota
  **52%**: paga il regime peggiore e vince lo stesso. La regola era stata scritta
  quando nessun candidato poteva passarla, proprio per non poterla adattare dopo.
- **Il buco di G1 trovato al giro 76 era reale ma non cambiava il verdetto.** La
  mediana sui dodici calendari del benchmark è +1,18, identica a gennaio, e
  l'ampiezza del benchmark è **0,19** punti — coerente con lo 0,14% che il giro 68
  aveva misurato per un equal-weight. Il grado di libertà del calendario appartiene
  a chi seleziona, non al benchmark.
- **DIFETTO DI G2, scoperto applicandolo** (giro 77). Nella famiglia di venti celle
  (5 skip × 4 taglie) i margini vanno da **−2,76 a +1,51**, cioè **4,27 punti di
  ampiezza**, e il candidato **non è nemmeno il massimo** (top-3 con k=1 fa +1,51).
  Ma la `var_sr` del Deflated Sharpe è stimata sulla dispersione degli **Sharpe**,
  che è minuscola (SR0 0,0608), mentre la selezione è avvenuta sui **margini di IRR
  netta**. **Il DSR sta proteggendo dalla selezione sbagliata**: fra Sharpe e IRR
  di un PAC ci sono in mezzo il motore fiscale, la soglia del 100% e la forma dei
  cashflow. Non riscrivo G2 adesso — sarebbe il peccato che il progetto ha evitato
  per settantasette giri — ma il difetto vale indipendentemente da come andrà
  l'holdout.
- **Il difetto di G2 è stato misurato, e spiega il fallimento dell'holdout**
  (giro 79). La versione **margine** della statistica di Bailey-López de Prado —
  stessa formula, applicata alla dispersione dei margini di IRR netta invece che
  degli Sharpe — dà **+2,19** di soglia sulla famiglia di 20 celle (σ 1,15) contro
  il **+1,18** del candidato: **respinto**, e con lui **0 passanti su 32** fra le
  due famiglie. Il verdetto non dipende dalla centratura (anche +1,33 lo respinge)
  e il cancello **discrimina ancora**: l'equal-weight contro il cap-weight (+1,50,
  non selezionato, N=1) passa. Non serve invocare un cambio di regime per spiegare
  il −0,95 fuori campione: **è la selezione**.
- **La sovrapposizione delle finestre NON era il difetto di G3, e la correzione
  ovvia è dieci volte peggiore del difetto** (giro 81). Con finestre decennali
  **disgiunte** il candidato fa **75,0%** (3 decenni su 4) e **G3 passa lo
  stesso**. Il bootstrap a blocchi dice che la sovrapposizione costa un fattore
  **1,45×** sull'intervallo di confidenza, cioè **n_eff ≈ 14** su 29 finestre
  nominali — metà dell'informazione apparente, non un ventisettesimo. E il rimedio
  distrugge il test: con 4 finestre e soglia 2/3 servono 3/4, che il **caso passa
  il 31,25% delle volte** contro il 3,07% delle mobili. Empiricamente si vede:
  sui dodici candidati del giro 72 passano **2/12 con le mobili e 4/12 con le
  disgiunte**.
- **Il limite di G3 è di campione, non di schema.** Quarant'anni contengono
  **quattro decenni indipendenti**, e nessuna scelta di finestre ne produce di
  più. Un cancello di stabilità su finestre decennali dentro un campione
  quarantennale è sottodimensionato in partenza: contarle come 29 le sopravvaluta
  di un fattore 2, contarle come 4 azzera il potere del test.
- **Il colpevole del fallimento dell'holdout è uno solo, ed è la selezione.** Il
  giro 79 mostra che G1/G2 con la soglia giusta (+2,19 contro +1,18) avrebbero
  respinto il candidato; il giro 81 assolve G3, che non lo avrebbe fermato in
  nessuna versione. Le due cose insieme chiudono l'autopsia: **il candidato era il
  massimo di una griglia troppo grande per il suo margine**, punto.
- **Lo schema delle finestre è un grado di libertà mai dichiarato**, della stessa
  famiglia del calendario (giro 68) e dello skip (giro 76): cambiarlo ribalta **4
  verdetti G3 su 12**. La differenza è che questo non gonfia il margine — gonfia
  il **verdetto di un cancello**.
- **Nel train il candidato aveva 6,50 punti di alfa lordo e ne consegnava 1,18**
  (giro 80). Zavorra — tutto ciò che sta fra il CAGR lordo time-weighted e l'IRR
  netta money-weighted — **6,01 punti** contro **0,69** del benchmark:
  differenziale **5,32**. Il segnale funzionava, e molto; la macchina fiscale ne
  prendeva cinque sesti. Fuori campione l'alfa lordo è passato a **+0,31**: non
  c'era più niente da tassare.
- **La macchina fiscale è un ammortizzatore simmetrico, e questo falsa la lettura
  di ogni decadimento.** Fra train e holdout l'alfa lordo crolla di **6,19** punti
  e il margine netto solo di **2,12**: i due terzi mancanti sono la zavorra che si
  riduce insieme all'alfa, perché su un vantaggio più piccolo si paga meno imposta.
  **Chi guarda solo l'IRR vede una strategia indebolita; chi guarda il lordo vede
  un segnale morto.** Vale per ogni confronto netto del progetto.
- **Sopra la soglia del 100% la rotazione aggiuntiva è quasi gratis** (giro 80).
  Portare il candidato da 3,284× a 3,804× nel train costa **0,11 punti** e non
  cambia scaglione. È il giro 66 visto dal lato opposto — lì il top-10, già al 33%,
  non guadagnava niente a farsi vincolare. **Il gradino è tutto; ciò che succede
  sopra e sotto è quasi piatto.**
- **La zavorra non è un'aliquota**: scala col livello del rendimento lordo, perché
  una strategia che rende il 17,28% ha in valore assoluto più plusvalenze da
  realizzare di una che rende il 10,78%. Il differenziale di 5,32 punti mescola la
  tassa sulla **rotazione** con la tassa sull'**aver guadagnato di più**, e la
  scomposizione additiva del giro 80 è un'identità contabile, non un'attribuzione
  causale. Separarle è la voce **O5**.
- **G1 era tarato sulla cosa sbagliata, e G1 e G2 provavano a fare la stessa
  cosa.** La soglia di +1,00 fu fissata al giro 72 sul **rumore di misura** (0,32
  medio, 1,35 massimo, giro 63). Il riferimento giusto è la **dispersione che la
  ricerca genera**, che cresce con quante celle si guardano: **+1,91** a 12 celle,
  **+2,19** a 20, **+2,70** a 60, **+3,25** a 240 — e 240 è la griglia implicita
  che il progetto ha davvero esplorato (5 skip × 12 calendari × 4 taglie). Il
  cancello sul margine unifica G1 e G2 in uno solo, con la soglia funzione di *N*
  invece che costante.
- **Il candidato peggiora esattamente dove comincia l'holdout.** Le uniche due
  finestre decennali negative su ventinove sono **le ultime due**: 1999-2008 a
  **−1,23** e 2000-2009 a **−3,39**, dopo cinque finestre consecutive sopra +3.
  L'holdout comincia nel 2010. È lo stesso profilo che il giro 59 aveva trovato su
  H5 (le quattro peggiori finestre contenevano tutte il 2008).

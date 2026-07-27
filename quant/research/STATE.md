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

Nessuna promozione dalla coda. Registro a **722 tentativi** cumulati.

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

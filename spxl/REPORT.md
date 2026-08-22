# Strategie su SPXL contro il buy&hold dell'S&P 500

Domanda di partenza: esiste una strategia su SPXL — lunga, corta o entrambe —
che batta il semplice comprare e tenere l'S&P 500, al netto di costi reali e
imposte?

Risposta breve: **no, non in modo che regga a una verifica onesta.** Una
struttura arriva vicino e la si trova più sotto, ma il suo vantaggio è più
piccolo dell'incertezza con cui è misurato. Il resto di questo documento serve a
mostrare perché, e soprattutto *dove* si rompe: non è la qualità del segnale, e
non sono solo le imposte.

---

## 1. Come è stato misurato

### I dati

| serie | copertura | fonte |
|---|---|---|
| S&P 500 giornaliero | 1927-12-30 → 2026-08-21 | export storico Yahoo su GitHub fino al 2019, poi FRED |
| dividendi dell'indice | 1871 → 2023 (mensili) | dataset Shiller |
| VIX / VIX 3 mesi | 1990 / 2007 → oggi | FRED (VIXCLS, VXVCLS) |
| tassi a breve | 1954 → oggi | FRED (DTB3, DFF) |
| SPXL, SPXS, SPY, UPRO | 2016 → oggi | Nasdaq |

L'indice giornaliero è ottenuto incollando due fonti che si sovrappongono dal
2016 al 2019: sulle 841 sedute comuni lo scarto relativo medio è 4.7e-07 e il
massimo 3.6e-04. La giunta è verificata, non sperata; se lo scarto superasse
l'1% il codice si ferma invece di produrre una serie che non esiste.

I dividendi servono a non sottostimare il buy&hold. Prima del 1988 non c'è un
indice total return giornaliero: senza i dividendi Shiller il benchmark
perderebbe tre o quattro punti l'anno nei decenni vecchi e ogni confronto
sarebbe truccato a favore delle strategie.

### La serie di SPXL prima del 2016

SPXL esiste dal novembre 2008 e i dati raggiungibili in questa sessione partono
dal 2016. Novant'anni su cento la serie usata **non è un dato, è un modello**:

```
r_fondo = 3 · r_indice + α + β · r_breve/252
```

α e β non sono presi dal prospetto, sono stimati per regressione sul fondo vero:

| | stimato | teorico |
|---|---|---|
| β (unità di cassa finanziate) | **−2.17** | −2.00 |
| α (expense ratio + spread swap) | **+1.51%/anno** | — |
| correlazione con il fondo reale | 0.9985 | |
| tracking error | 3.06%/anno | |

β vicino a −2 conferma che la meccanica è quella dichiarata. L'α positivo non è
un errore: la fonte disponibile per SPXL non corregge per le distribuzioni,
quindi il modello replica il *prezzo* e assorbe i dividendi dell'indice
moltiplicati per tre.

**Il numero che conta di più in tutto il documento** è la verifica fuori
campione: stimando il modello sulla prima metà dello storico reale e
verificandolo sulla seconda, lo scostamento è **+2.59% l'anno**. Cioè il modello
può essere generoso con SPXL di due punti e mezzo l'anno. Tenere a mente questa
cifra: alla fine si scoprirà che è più grande del vantaggio che stiamo cercando.

### Costi e imposte

Costo di un lato: 5 punti base su SPXL, 8 su SPXS, 2 su SPY. Sono valori
prudenti: lo spread reale su SPXL è di 1-3 punti base.

Il fisco è modellato sul **realizzato**, anno per anno, con compensazione delle
minusvalenze e prelievo di cassa a fine anno che entra nel ribasso massimo.
Regime predefinito: Irlanda, CGT 33% sulle plusvalenze e 41% sui dividendi,
franchigia 1.270 euro. Sono disponibili e testati anche IT 26%, IT IRPEF 43%,
exit tax irlandese 41% e USA breve termine 40.8%.

Questo è il punto che decide quasi tutto. Il buy&hold realizza **una volta
sola**, alla fine, e fino ad allora capitalizza anche la quota che un giorno
andrà allo Stato. Una strategia che ruota venti volte l'anno paga venti volte.

### Le tre regole del confronto

1. **Rischio appaiato.** Una strategia che rende il 9.7% con un ribasso massimo
   del 94% non batte un buy&hold che rende l'8.1% con un ribasso dell'85%: sta
   solo prendendo più rischio, e per prendere più rischio non serve una
   strategia, basta la leva. Ogni candidata viene quindi anche riscalata perché
   la sua volatilità realizzata coincida con quella del benchmark, con fattore
   stimato **solo sul passato**.

   Quanto pesa questa regola si vede togliendola: lo stesso walk-forward, con i
   pesi grezzi, chiude a **+0.36 punti** sopra il benchmark — ma con un ribasso
   massimo del 71.1% contro il 56.4%. È tutto qui il modo in cui un backtest
   sembra vincere senza vincere.
2. **Niente look-ahead.** Il segnale del giorno *t* usa solo dati chiusi al
   giorno *t*; la posizione parte il giorno dopo. Il ritardo è imposto dal
   simulatore, non dalle strategie, così nessuna può dimenticarselo.

   La prova del nove è ritardare ancora l'esecuzione: una strategia che vive di
   look-ahead crolla appena le si toglie il giorno che stava rubando. Qui il
   walk-forward completo, rifatto con uno, due e tre giorni di ritardo, dà un
   divario dal benchmark di −1.81, −2.19 e −1.93 punti. Nessun gradino: perde in
   modo stabile perché perde davvero, non per un artefatto.
3. **Conteggio dei tentativi.** Provare centinaia di combinazioni garantisce di
   trovarne una bella anche nel rumore. Ogni tabella riporta quante ne sono
   state provate, e il deflated Sharpe ratio sconta quel numero.

---

## 2. Le cose da sapere prima di cercare una strategia

### Usare SPXL per avere esposizione 1x costa circa 3.8 punti l'anno

Tenere il 33% in SPXL e il resto liquido dà la stessa esposizione all'indice di
tenere il 100% in SPY. Non dà lo stesso rendimento (1954-2026, al netto):

| | esposizione | CAGR netto | MaxDD |
|---|---|---|---|
| 100% SPY | 1.00x | **9.41%** | −56.4% |
| 33% SPXL + 67% liquidità | 1.00x | **5.58%** | −59.2% |

Il costo di finanziamento si annulla quasi esattamente con l'interesse sulla
liquidità. Ciò che resta è il *volatility drag*: la leva è giornaliera, e
comporre ogni giorno tre volte il rendimento erode circa `3σ²` l'anno. Con σ ≈
16% fanno circa 7.7 punti l'anno sulla quota a leva, cioè 2.6 sul portafoglio,
più mezzo punto di spese.

Questo è il pedaggio d'ingresso. Qualunque segnale deve prima ripagare questo.

### La quota costante ottimale di SPXL non è 100%, e sul periodo lungo non è nemmeno positiva

| peso SPXL | esposizione | CAGR 1954+ | MaxDD |
|---|---|---|---|
| 0% (solo SPY) | 1.00x | **9.41%** | −56.4% |
| 33% | 1.00x | 5.58% | −59.2% |
| 50% | 1.50x | 6.54% | −79.4% |
| 67% | 2.00x | 7.14% | −90.7% |
| 100% | 3.00x | 7.92% | −98.5% |

Sui periodi recenti (1990+, 2008+) il massimo si sposta al 100% di SPXL, ma con
ribassi massimi del 98.5% e del 76.7%. Sono numeri che nessuno attraversa
restando investito.

### Ribilanciare meno spesso vale da mezzo punto a un punto e mezzo l'anno

Con pesi obiettivo costanti, la frequenza con cui si riportano le quote
all'obiettivo cambia il risultato per due ragioni opposte: ogni ribilanciamento
vende la parte salita (quindi realizza plusvalenze e anticipa l'imposta) e taglia
la quota a leva proprio mentre sta correndo.

| miscela | ogni giorno | ogni anno | differenza |
|---|---|---|---|
| 33% SPXL | 5.58% | **6.30%** | +0.72 |
| 50% SPXL | 6.54% | **7.61%** | +1.07 |
| 67% SPXL | 7.14% | **8.47%** | +1.33 |

Il ribasso massimo migliora anche lui (da −59.2% a −49.9% sul 33%).

### Il lato short toglie valore, sempre

Stessa identica regola di trend, quota short crescente (1954-2026, al netto):

| | CAGR | Sharpe | MaxDD |
|---|---|---|---|
| solo lungo, fuori sotto SMA200 | **7.60%** | **0.28** | −37.1% |
| short 25% sotto SMA200 | 7.23% | 0.25 | −41.0% |
| short 50% sotto SMA200 | 6.38% | 0.21 | −42.1% |
| short 100% sotto SMA200 | 4.81% | 0.12 | −41.9% |
| short 50% solo se volatilità > 25% | 6.53% | 0.22 | −44.6% |

Monotòno: ogni punto di esposizione corta toglie rendimento *e* Sharpe *e*
peggiora il ribasso. Due ragioni, entrambe indipendenti dal segnale:

- il drag da varianza colpisce anche l'inverso a leva, e i mercati sotto la
  media a 200 giorni sono i più volatili che esistano: è lo scenario peggiore in
  cui tenere un −3x;
- l'indice ha una deriva positiva, e stare corti significa remare contro quella
  deriva ogni giorno, anche quando si ha ragione sulla direzione.

**Il lato short della domanda ha una risposta netta: non conviene.**

---

## 3. Le strategie

### Parametri da manuale, zero ottimizzazione

Diciotto famiglie documentate (trend su media mobile, incroci, momentum
assoluto, volatility targeting, regimi di volatilità, filtro VIX, struttura a
termine del VIX, RSI2 di Connors, acquisto dei cali, long/short), coi parametri
che stanno nei libri, su quattro periodi, a rischio appaiato.

Nessuna batte il buy&hold sul CAGR netto né sullo Sharpe. Diverse lo battono su
Calmar e ribasso massimo: è il profilo tipico del trend following, che rinuncia a
rendimento in cambio di code più corte.

### Griglia esplorativa: l'edge esiste al lordo e muore col fisco

176 configurazioni su 1990-2026, a rischio appaiato:

| | al lordo di imposte | al netto (CGT 33%) |
|---|---|---|
| battono lo Sharpe del benchmark | **16 su 155 (10%)** | **1 su 176 (1%)** |
| battono il CAGR | 25 (16%) | 3 (2%) |
| battono il Calmar | 71 (46%) | 49 (28%) |

Le migliori al lordo sono tutte mean reversion a breve (RSI2 di Connors, Sharpe
0.71 contro 0.51 del benchmark, deflated Sharpe 0.99 anche scontando 155
tentativi). Ruotano però **19 volte l'anno**, e con imposta sul realizzato quel
ritmo costa **4.8 punti l'anno**, contro i 1.9 del buy&hold. Il vantaggio c'era e
se lo mangia il fisco.

Va detto subito, però, che nemmeno al lordo il vantaggio è statisticamente
distinguibile: il bootstrap a blocchi dà p ≈ 0.17 sul divario dal benchmark, su
36 anni.

### Il freno fiscale, in cifre

| | rotazione annua | freno fiscale |
|---|---|---|
| buy&hold S&P 500 | 0 | 1.9 – 2.8 %/anno |
| trend following mensile | 1.5 | 3.0 – 3.3 %/anno |
| mean reversion RSI2 | 15 – 21 | 4.3 – 5.3 %/anno |

Il freno del buy&hold è quasi tutto imposta sui **dividendi** (41% su un
rendimento medio del 3.5%), non sulle plusvalenze: quelle le paga una volta
sola, alla fine.

### Walk-forward ancorato: il test che conta

Nessun parametro scelto guardando il periodo su cui viene giudicato. Si allena da
sempre fino a *T*, si giudica da *T* a *T*+3 anni, si sposta *T*. 21 finestre,
180 configurazioni rivalutate a ogni riselezione, selezione a due stadi
(scrematura veloce sul lordo, scelta finale sul **netto**). 62.6 anni mai visti in
fase di scelta.

| 1964 – 2026 | CAGR netto | vol | MaxDD | Calmar | Sharpe |
|---|---|---|---|---|---|
| **B&H S&P 500** | **8.75%** | 16.6 | −56.4% | 0.16 | **0.35** |
| walk-forward | 6.73% | 17.6 | **−47.7%** | 0.14 | 0.21 |
| *le stesse, al lordo:* | | | | | |
| B&H S&P 500 | 10.69% | 16.5 | −55.3% | 0.19 | **0.43** |
| walk-forward | 9.82% | 17.2 | **−45.5%** | **0.22** | 0.37 |

Perde di due punti l'anno al netto. E **perde anche al lordo**, di quasi un
punto: quando i parametri si scelgono onestamente, il vantaggio che si vedeva
nella griglia non si presenta. Era selezione, non segnale.

Il metodo, va detto, ha imparato qualcosa: sceglie in modo molto stabile le
strutture a nucleo con filtro di trend mensile, e il ribasso massimo che ottiene
è dieci punti migliore del benchmark, in entrambe le versioni.

### Una seconda iterazione, e la trappola che ha rivelato

L'analisi fiscale dice che il vincolo è il numero di realizzi. Quindi vale la
pena aggiungere alla griglia due famiglie a rotazione quasi nulla: le
combinazioni di segnali poco correlati, che si muovono a gradini e realizzano a
fette, e l'**effetto stagionale** (esposizione piena da novembre ad aprile,
ridotta da maggio a ottobre: due operazioni l'anno).

Con quelle dentro, il walk-forward cambia faccia. Sceglie la stagionalità in
quindici finestre su ventuno, e:

| 1964 – 2026, al lordo | CAGR | vol | MaxDD | Calmar | Sharpe |
|---|---|---|---|---|---|
| B&H S&P 500 | 10.69% | 16.5 | −55.3% | 0.19 | 0.43 |
| walk-forward con stagionalità | **12.00%** | 16.7 | **−44.4%** | **0.27** | **0.49** |

Batte il buy&hold su tutto, al lordo, in walk-forward onesto, su 62 anni mai
visti in fase di scelta. Al netto arriva a 8.22% contro 8.75%, cioè quasi in
pareggio invece dei due punti di distacco di prima.

**Ed è qui che bisogna fermarsi invece di esultare.** La disciplina del
walk-forward protegge dalla scelta dei *parametri*, non dalla scelta delle
*famiglie*: quella l'ho fatta io, dopo aver guardato tutto il campione. E
l'effetto Halloween è l'anomalia di calendario più cercata e più contestata
della letteratura.

C'è però una verifica possibile. Bouman e Jacobsen la pubblicano nel 2002 usando
dati fino al 1998: tutto ciò che viene dopo è fuori campione rispetto alla
*scoperta*, non solo rispetto ai parametri.

| | 1954 – 1998 (scoperta) | | 1999 – 2026 (verifica) | |
|---|---|---|---|---|
| | CAGR | MaxDD | CAGR | MaxDD |
| B&H S&P 500 | 10.43% | −45.9% | **6.82%** | −56.2% |
| stagionale 50% + SMA200 | **10.63%** | **−26.6%** | 6.57% | −48.2% |
| stagionale 0% + SMA200 | **11.50%** | −33.2% | 5.73% | −53.3% |
| stagionale nuda, senza trend | 7.40% | −50.0% | 5.42% | −59.8% |

Funzionava prima di essere pubblicata e ha smesso dopo. Il Calmar resta un
filo migliore (0.14 contro 0.12) ma lo Sharpe peggiora (0.33 contro 0.39) e il
rendimento passa sotto.

Il vantaggio lordo del walk-forward veniva da lì. Non è un risultato, è la
firma di chi ha cercato.

### La conferma per un'altra strada

C'è un modo di verificarlo che non passa dalle date di pubblicazione: rifare il
walk-forward spostando in avanti l'inizio, così che il periodo *giudicato* cada
sempre più fuori dai decenni in cui la stagionalità funzionava.

| walk-forward avviato nel | periodo giudicato | strategia lorda | B&H lordo | divario |
|---|---|---|---|---|
| 1954 | 1964 – 2026 (62.6 anni) | **12.00%** | 10.69% | **+1.31** |
| 1990 | 2000 – 2026 (26.6 anni) | 5.42% | 8.57% | −3.15 |
| 1999 | 2009 – 2026 (17.6 anni) | 11.56% | 14.85% | −3.29 |

L'unico che vince è quello il cui giudizio comincia nel 1964. I due il cui
giudizio sta interamente dopo il 2000 perdono di tre punti l'anno, al lordo e
al netto. Il metodo non ha imparato a battere il mercato: ha imparato a
riconoscere un'anomalia che nel frattempo era sparita.

---

## 4. La strategia costruita dalle misure

Invece di cercare in una griglia, si mette insieme quello che le misure hanno
indicato, una cosa per volta:

1. **Solo lungo** — la quota short peggiora tutto, in modo monotòno.
2. **Un nucleo che non si vende mai** — è il vantaggio strutturale del buy&hold
   (differimento dell'imposta per decenni); conviene tenerselo invece di
   rinunciarci.
3. **Satellite con filtro di trend** — dentro sopra la media a 200 giorni, fuori
   sotto, con banda di isteresi al 2% perché i falsi segnali si pagano due volte.
4. **Decisione mensile** — segnale quasi identico, rotazione un ordine di
   grandezza più bassa.
5. **Ribilanciamento annuale** — vale mezzo punto o più, e migliora il ribasso.

Nessun parametro è stato cercato: 200 giorni, banda 2%, mensile, annuale sono
tutti valori canonici. L'unica scelta è quanto mettere nel nucleo, e sotto c'è
tutta la curva.

**Nucleo 80% SPY (mai venduto) + 20% SPXL con filtro di trend:**

| periodo | CAGR strategia | CAGR B&H | MaxDD strategia | MaxDD B&H | Sharpe |
|---|---|---|---|---|---|
| 1954 – 2026 | **9.60%** | 9.41% | **−50.8%** | −56.4% | 0.38 vs 0.41 |
| 1990 – 2026 | **9.76%** | 9.00% | **−50.7%** | −56.3% | 0.46 vs 0.47 |
| 2008 – 2026 | **13.39%** | 12.11% | **−31.6%** | −33.8% | 0.70 vs 0.73 |

Batte il benchmark su rendimento *e* su ribasso massimo in tutti e tre i
periodi. È il risultato migliore di tutto il lavoro.

E adesso le tre ragioni per cui non basta.

**Primo: lo Sharpe è più basso in tutti e tre i periodi.** La strategia prende
circa il 15% di volatilità in più (18.4% contro 16.0%). Guadagna di più perché
rischia di più; solo che rischia in un modo che allunga la coda destra e accorcia
la sinistra, il che è desiderabile ma non è "battere il benchmark".

**Secondo: non è statisticamente significativo.** Il bootstrap a blocchi sul
divario dà p tra 0.09 e 0.24 a seconda della variante e del periodo. Su
settantadue anni. Un vantaggio di due decimi di punto l'anno non si distingue dal
caso nemmeno con tutta la storia disponibile.

**Terzo, e decisivo: il vantaggio è più piccolo dell'errore del modello.**
Applicando una penalità crescente ai fondi a leva — cioè chiedendo "e se il mio
modello di SPXL fosse stato generoso di tanto?" — il divario di CAGR si annulla
qui:

| penalità annua sui fondi a leva | 1954+ | 1990+ | 2008+ |
|---|---|---|---|
| 0.0% | +0.19 | +0.76 | +1.28 |
| 1.0% | +0.06 | +0.62 | +1.13 |
| **1.5%** | **−0.00** | +0.55 | +1.05 |
| 2.5% | −0.13 | +0.41 | +0.90 |
| 4.0% | −0.32 | +0.20 | +0.67 |

Sul periodo lungo il vantaggio sparisce con una penalità dell'**1.5% l'anno**. La
verifica fuori campione del modello di SPXL, riportata al paragrafo 1, dice che
l'errore può essere di **2.59% l'anno**. Il vantaggio è dentro la barra d'errore
del proprio strumento di misura.

Sui periodi recenti il vantaggio regge fino a penalità del 4%, ma 1990-2026 e
2008-2026 sono esattamente i tratti in cui l'azionario americano ha fatto meglio
di sempre: sono i più favorevoli a qualunque cosa contenga leva.

---

## 5. Risposta

**Al lordo di tutto**, un vantaggio esiste ma è piccolo e non significativo: la
mean reversion a breve sull'indice ha uno Sharpe superiore al buy&hold, ma il
divario non si distingue dal caso su 36 anni.

**Al netto di costi e imposte** quel vantaggio sparisce: ruota troppo, e
l'imposta sul realizzato costa più di quanto il segnale renda.

**In walk-forward onesto** non resta niente, nemmeno al lordo: scegliendo i
parametri solo sul passato, il metodo perde contro il buy&hold di quasi un punto
l'anno prima delle imposte e di due dopo.

**L'unica struttura che regge** — nucleo permanente più satellite a leva con
filtro di trend — batte il benchmark su rendimento e ribasso in tre periodi
indipendenti, ma con Sharpe più basso, p tra 0.09 e 0.24, e un margine più
sottile dell'incertezza del modello con cui è misurato.

**Sul lato short la risposta è netta e negativa.**

Il vincolo che decide non è la qualità del segnale. Sono due fatti strutturali:

- SPXL costa circa **3.8 punti l'anno** per ogni unità di esposizione 1x, prima
  di qualunque strategia;
- l'imposta sul realizzato costa alle strategie attive **1-2.5 punti l'anno** più
  che al buy&hold, e il buy&hold quel vantaggio non lo perde mai.

---

## 6. Cosa cambierebbe la risposta

Le condizioni sotto cui varrebbe la pena riaprire il discorso, in ordine di
quanto sposterebbero il risultato:

- **Un conto esente da imposta sul realizzato** (previdenziale o simile).
  Elimina 1-2.5 punti l'anno di svantaggio. Attenzione però: non basta. Il
  walk-forward è stato rifatto per intero a ogni aliquota, e continua a perdere
  anche a zero:

  | aliquota sulle plusvalenze | 0% | 20% | 26% | 33% | 41% | 50% |
  |---|---|---|---|---|---|---|
  | divario di CAGR dal benchmark | −1.09 | −1.17 | −1.47 | −2.03 | −1.92 | −2.47 |

  L'imposta peggiora le cose in modo regolare, ma il buco iniziale non lo apre
  lei. Stesso esito muovendo l'aliquota sui dividendi, che colpisce soprattutto
  il *benchmark*: portandola a zero il buy&hold sale a 10.10% e il divario si
  allarga a −2.33.

  Sui regimi reali, il divario di CAGR dal benchmark è:

  | regime | divario | perché |
  |---|---|---|
  | nessuna imposta | −0.99 | il buco è già lì senza fisco |
  | Irlanda, CGT 33% | −1.81 | minusvalenze compensabili e riportabili |
  | Italia, 26% | **−3.11** | i proventi da ETF sono redditi di capitale e le minus da ETF non li abbattono: si paga sulle plusvalenze lorde |
  | Irlanda, exit tax 41% | −3.45 | aliquota alta e nessuna compensazione |

  Il caso italiano è peggiore di quello irlandese pur avendo un'aliquota più
  bassa di sette punti, e la ragione non è l'aliquota: è l'asimmetria. Dove le
  perdite non abbattono i guadagni, una strategia che alterna operazioni in
  utile e in perdita paga su tutte quelle in utile e non recupera niente sulle
  altre. È il singolo dettaglio fiscale che pesa di più su una strategia attiva,
  e non compare quasi mai nei backtest.

  Nota sulla praticabilità in Italia: SPXL è un ETF statunitense senza KID
  conforme alla normativa PRIIPs, quindi i broker europei generalmente non lo
  rendono acquistabile alla clientela retail. Il regime IRPEF per gli ETF non
  armonizzati (fino al 43%) è modellato nel codice ma il vincolo che viene prima
  è l'accesso allo strumento.
- **Dati reali di SPXL dal 2008, corretti per le distribuzioni.** Ridurrebbero
  l'incertezza del modello da 2.6 punti a qualche decimo e renderebbero
  decidibile il risultato del paragrafo 4. In questa sessione Yahoo ha limitato
  per indirizzo IP e non è stato possibile ottenerli; lo script
  `refresh_yahoo.py` li recupera appena la fonte torna disponibile, e tutte le
  tabelle si rigenerano senza modifiche al codice.
- **Un secondo attivo decorrelato.** Tutta questa analisi è vincolata a un solo
  indice, come chiedeva la domanda. Il modo in cui la leva viene usata con
  qualche successo in letteratura prevede di affiancarle un attivo che sale
  quando l'azionario scende; il 2022, quando sono scesi insieme, mostra il limite
  anche di quello.
- **Costi di transazione molto più bassi del previsto.** Poco probabile: sono già
  modellati a 5 punti base contro 1-3 reali, e comunque i costi non sono la voce
  che decide.

---

## 7. Riprodurre

```
python3 spxl/fetch_data.py          # scarica e mette in cache i dati
python3 spxl/research.py check      # verifica dati e modello del fondo a leva
python3 spxl/research.py leva       # quanta leva conviene, senza segnali
python3 spxl/research.py ribilancio # frequenza di ribilanciamento
python3 spxl/research.py short      # il lato short
python3 spxl/research.py baseline   # parametri da manuale, quattro periodi
python3 spxl/research.py sweep      # griglia esplorativa
python3 spxl/research.py walkforward # il test che conta
python3 spxl/research.py sintesi    # la strategia costruita dalle misure
python3 spxl/research.py rottura    # a quale penalita' il vantaggio sparisce
python3 spxl/research.py sensitivity # walk-forward a ipotesi variabili
```

I tabulati completi sono in `spxl/results/`. I dati scaricati non sono nel
repository (si rigenerano con `fetch_data.py`, che è ripartibile).

Aggiungere una strategia significa scrivere una funzione in `strategies.py` che
restituisce una matrice di pesi e inserirla in `sweep_grid()` dentro
`research.py`. Il ritardo di esecuzione, i costi e il fisco li applica il
simulatore: non c'è modo di dimenticarseli.

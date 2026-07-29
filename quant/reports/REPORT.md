# Attivo contro passivo, netto di fiscalità irlandese

**Report finale — settantotto giri, 1.402 tentativi a registro, holdout aperto una
volta sola al giro 78 e ora bruciato.**

Domanda: *esiste una strategia attiva che, per un residente fiscale irlandese che
versa €500 al mese per vent'anni o più, batta un PAC buy&hold netto di costi e
imposte?*

Risposta: **no**, e dal giro 78 la risposta ha un **test fuori campione** a
sostenerla: l'unico candidato che abbia mai passato tutti e quattro i cancelli ha
perso **−0,95 punti** su 2010-2026, in dodici calendari su dodici. Questo report
dice con quanta forza, con quali limiti, e cosa resta di utilizzabile — che non è
una strategia.

> Questo documento sostituisce la versione del giro 29, che portava in prima
> pagina un **+1,72** poi rivelatosi sbagliato per due correzioni successive (vedi
> *[Tre errori di misura](#tre-errori-di-misura-trovati-e-corretti)*). Il dettaglio
> giro per giro sta in [`../research/rounds/`](../research/rounds/), le ipotesi
> pre-registrate in [`../research/QUEUE.md`](../research/QUEUE.md), lo stato del
> metodo in [`../research/STATE.md`](../research/STATE.md), e ogni singola
> configurazione valutata in `../research/registry.csv`.

---

## Come è stato condotto

Cinque regole, mai cambiate dopo aver visto un risultato.

1. **Pre-registrazione.** Ogni ipotesi ha una *predizione* e una *condizione di
   falsificazione* scritte e committate **prima** dell'esecuzione. Nessuna è stata
   riscritta dopo i dati: quando una voce si è rivelata mal posta o
   autocontraddittoria (E2 al giro 49, L2 al giro 74) l'ho dichiarato prima di
   eseguire e ho misurato la voce così com'era.
2. **Walk-forward.** Dal giro 03 in poi i parametri di ogni anno *Y* si scelgono
   solo su ciò che precede *Y*. Nessuna ottimizzazione sull'intero campione.
3. **Fiscalità irlandese sempre applicata**: CGT 33% al realizzo con esenzione
   €1.270 e riporto delle minusvalenze; ETF UCITS a exit tax 41/38% con deemed
   disposal ogni 8 anni e **senza** compensazione delle perdite; DIRT 33% sulla
   liquidità; dividendi esteri ~52%; e **riqualificazione a 52% sopra ~100% di
   rotazione annua**.
4. **Deflated Sharpe** con *N* = dimensione della griglia se c'è selezione,
   altrimenti la famiglia pre-dichiarata; `var_sr` stimata entro la famiglia del
   giro. Il registro cumulato è la soglia del progetto.
5. **Holdout 2010-2026 sigillato** per settantasette giri, **aperto al giro 78**
   una volta sola, su un candidato solo, con la predizione committata prima —
   e ora **bruciato**.

Ogni esito è registrato, comprese le ipotesi fallite: **37 confermate, 17
falsificate, 1 senza esito per dati** fra le voci di coda dei giri 30-78, più i
ventinove giri esplorativi iniziali.

---

## La risposta, in un paragrafo

Sulle **1.402 configurazioni** registrate, la **mediana dell'extra-rendimento
contro il proprio benchmark è −1,32 punti** e solo il **30,3%** è positivo.

**Un solo candidato**, in settantotto giri, ha superato la regola di apertura
dell'holdout scritta al giro 72 — il momentum **12-3 top-5 mensile**, con +1,18
punti in campione. L'holdout è stato aperto su di lui, una volta sola, al giro 78:
**ha perso −0,95 punti**, in dodici calendari su dodici. Il secondo miglior
candidato mai registrato, il momentum 12-2 top-5 mensile, si ferma a **+0,56** in
campione e non arriva nemmeno al cancello.

Quel test è la differenza fra questo report e un backtest: la conclusione non è
«non ho trovato niente», è **«ho trovato una cosa, l'ho messa alla prova su un
campione mai guardato, e non ha tenuto»**.

Quello che resta di utilizzabile riguarda **il veicolo, il calendario e la
rotazione**: dove metti i titoli, quanto spesso li tocchi, e chi preme il bottone
del realizzo. Non quale segnale segui.

---

## La regola per aprire l'holdout — in vigore dal giro 72

Scritta **quando non esisteva nessun candidato che potesse passarla**, per non
poterla adattare a un candidato. Un candidato merita l'holdout solo se passa
**tutti e quattro** i cancelli.

| | cancello | soglia |
|---|---|---|
| **G1** | margine | IRR ≥ benchmark **+1,00 punto**, come **mediana sui dodici calendari** di ribilanciamento |
| **G2** | Deflated Sharpe | **> 0,95** su *N* = registro cumulato |
| **G3** | stabilità | extra positivo in **≥ 2/3** delle finestre decennali mobili **E** mediana degli extra **> 0** |
| **G4** | calendario | margine positivo in **≥ 10 dei 12** mesi di ribilanciamento |

Benchmark: **equal-weight annuale dello stesso universo, con la rotazione vera**.
Se un candidato passa, l'holdout si apre **una volta sola, su quello solo**, e il
risultato si registra qualunque sia.

**Applicata ai dodici candidati riproducibili: zero passano.**

- **G1 elimina 12 su 12.** Nessuno arriva a un punto di margine.
- G2 ne elimina 10, G3 ne elimina 10, G4 ne elimina 7 (ma **6 su 7** fra i soli
  candidati annuali: i mensili lo passano per costruzione).
- Il più vicino al bersaglio: **momentum 12-2 top-5 mensile**, che passa G2 (DSR
  0,971) e G4 e fallisce G3 per **sette decimi di punto percentuale** (66,0%
  contro 66,7%) — restando comunque a mezzo punto dal margine richiesto.

L'holdout resta sigillato. Non è prudenza: è che **non c'è niente da testarci**.

*(Le righe qui sopra sono il testo del giro 75. Quello che segue le ha superate, e
lo lascio in coda invece di riscriverle: **il verso in cui una conclusione si
muove è informazione**, e cancellare il punto di partenza la distruggerebbe.)*

### Addendum del giro 76 — la prima cella che arriva ai cancelli

*Scritto un giro dopo il resto del report, e messo qui invece che riscrivere le
righe sopra, perché il verso in cui una conclusione si muove è informazione.*

Misurando lo **skip** del momentum come parametro esplicito (giro 76), il
**momentum 12-3 top-5 mensile** dà **+1,18 punti** contro l'equal-weight annuale,
con **DSR 0,9870**. Passa **G1 come misurato, G2 e G4**. **G3 non è mai stato
misurato**, e G1 è misurato contro un benchmark su **un solo calendario**.

La verifica completa è stata pre-registrata come voce **M1**, con predizione
scritta prima: *G1 tiene, G3 fallisce*.

### Addendum del giro 77 — la regola è stata passata

**G3 non è fallito. Il candidato passa tutti e quattro i cancelli.**

| | cancello | soglia | misurato |
|---|---|---|---|
| **G1** | margine | ≥ +1,00, mediana su 12 calendari | **+1,18** (positivo in 12/12, minimo +1,04) |
| **G2** | Deflated Sharpe | > 0,95 | **0,9907** |
| **G3** | stabilità | ≥ 66,7% finestre **e** mediana > 0 | **93,1%** (27 finestre su 29), mediana **+2,23** |
| **G4** | calendario | ≥ 10/12 | mensile, per costruzione |

Momentum **12-3 top-5 mensile**: IRR **11,27%** contro **10,09%** del benchmark,
rotazione 3,284×/anno, quindi **aliquota 52%** — paga il regime peggiore e vince
lo stesso. La predizione di M1 diceva *tre cancelli su quattro* e sbagliava
proprio sul cancello di cui ero più sicuro.

**L'holdout non è ancora aperto**: la regola dice che l'apertura è un **atto
separato**, ed è pre-registrata come voce **N1** con la predizione — margine
**negativo, fra −3 e 0 punti** — scritta prima di guardare. Tre dubbi messi a
verbale *prima* del risultato, perché dopo non varrebbero niente:

1. **Difetto di G2.** Nella famiglia di venti celle i margini vanno da −2,76 a
   **+1,51** (4,27 punti di ampiezza) e il candidato **non è il massimo**. Ma la
   `var_sr` del DSR è stimata sulla dispersione degli **Sharpe**, minuscola, mentre
   la selezione è avvenuta sui **margini di IRR netta**: il DSR sta proteggendo
   dalla selezione sbagliata. La regola non si riscrive adesso — il difetto si
   registra.
2. **Il candidato peggiora dove comincia l'holdout.** Le uniche due finestre
   decennali negative su ventinove sono **le ultime due** (1999-2008 a −1,23,
   2000-2009 a **−3,39**), dopo cinque consecutive sopra +3.
3. **Lo skip k=3 è stato scelto in-sample**, come massimo di dieci celle.

### Addendum del giro 78 — l'holdout è stato aperto, e il candidato ha perso

**Margine −0,95 su 2010-2026, negativo in 12 calendari su 12** (banda −1,04 …
−0,82). Le tre clausole della predizione di N1, scritte prima di guardare, sono
centrate tutte e tre.

| | candidato | benchmark |
|---|---:|---:|
| IRR netta (aliquota applicabile) | **9,89%** (52%) | **10,84%** (33%) |
| CAGR **lordo** | **13,65%** | 13,34% |
| Sharpe | 0,72 | **0,86** |
| max drawdown | −31,38% | **−25,50%** |
| rotazione | 3,804× | 0,06× |

**Il premio lordo è sopravvissuto; l'investitore no.** Il segnale batte ancora il
benchmark di **+0,31 punti** di CAGR lordo fuori campione. Netto di imposte perde
di quasi un punto.

E il controfattuale, che è la frase più affilata di tutto il lavoro:

> **Anche pagando il 33% invece del 52%, il candidato avrebbe fatto +0,90 — sotto
> il suo stesso cancello.** Nemmeno in un mondo dove ruotare 3,8 volte l'anno non
> facesse scattare la riqualificazione a reddito d'impresa, questa strategia
> sarebbe passata.

**Il cancello che è crollato è G3, cioè quello che in campione era il più forte**:
93,1% di finestre decennali positive nel train, **37,5%** nell'holdout; mediana da
+2,23 a −0,16. Un cancello che passa al 93% dentro e al 37% fuori non stava
misurando la stabilità — stava misurando il campione, perché le 29 finestre del
train si sovrappongono in media all'85,5% e «27 successi su 29» è lo stesso pezzo
di storia contato 27 volte.

Lo scarto train→holdout è **2,13 punti**, dello stesso ordine dei gradi di libertà
che il progetto aveva già misurato uno per uno — skip 3,94, calendario 3,65,
finestra temporale 5,81-10,19. **Il candidato non è stato smentito da un evento
raro: è rientrato nella dispersione nota.**

**La conclusione del report non cambia, e adesso ha un test fuori campione a
sostenerla.** L'holdout 2010-2026 è **bruciato** e non si riapre.

---

## I numeri che contano

Criterio, dichiarato prima di contare: un numero entra qui se **(a)** non è stato
contraddetto da nessun giro successivo e **(b)** regge una conclusione o una
raccomandazione. Sono **dodici**. La predizione della voce L3 diceva «meno di
dieci»: **sbagliata**, e sbagliata per difetto.

### Costi e soglie — cosa ti costa muoverti

| # | numero | cosa dice | giro |
|---|---:|---|---:|
| 1 | **1,35 punti** | il costo della rotazione vera di un equal-weight annuale (11,16% → 9,81%). Un portafoglio "che non fa niente" deriva coi prezzi e va ricomprato | 60, 63 |
| 2 | **100%/anno** | la soglia di riqualificazione fiscale è un **gradino**, non un aggiustamento: attraversarla vale ~19 punti di aliquota. Rinunciare all'ultimo 10% di rotazione per restare sotto costa 0,11-0,59 punti di CAGR lordo e ne rende fino a +1,02 netti | 64, 66 |
| 3 | **3,65% / 0,14%** | l'ampiezza del margine al variare del **mese di ribilanciamento**, su un top-5 e su un equal-weight. Il grado di libertà del calendario esiste solo per chi seleziona, e scala con la concentrazione | 68 |
| 4 | **+1,09 / +0,64** | il vantaggio del veicolo, **di segno opposto** a seconda di cosa fai: +1,09 alle azioni dirette se stai fermo, +0,64 all'ETF UCITS se ruoti | 71 |
| 5 | **+3,43 punti** | il costo di realizzare, misurato in isolamento a parità esatta di lordo. Scomposto: **+0,00 la rotazione**, +0,66 i dividendi, il resto il differimento. Non è incassabile: si può solo evitare di perderlo | 53, 71 |
| 6 | **€7.350/mese** | la rata sotto cui un PAC su 49 posizioni comprate una per una è antieconomico (soglia = *P* × €1,50 / 1%). A €750 il 14,7% del versamento se ne va in commissioni | 74 |
| 7 | **max 15,3%** | la quota **fiscale** della perdita di un'allocazione multi-asset contro l'azionario puro. L'84-92% è composizione: il decennale rende meno delle azioni, e nessun metodo di allocazione lo ripara | 44, 45 |

### Fragilità — quanto vale un margine misurato

| # | numero | cosa dice | giro |
|---|---:|---|---:|
| 8 | **5,81-10,19 punti** | l'ampiezza dei margini su finestre decennali di lunghezza fissa, contro gli 0,56 punti che si vedono spostando solo la data di partenza: **18×**. La dispersione di questi margini è dello stesso ordine dei margini stessi — confermato dal lato del calendario (3,65) e da quello dei giorni di ritardo (±0,5) | 59, 68, 73 |
| 9 | **263-398%** | quanto del margine del miglior candidato è spiegato dalla **scelta del benchmark**. Il contributo della selezione è **−0,61**: il momentum settoriale sceglie *peggio del caso* dentro lo stesso universo | 60 |
| 10 | **−22,51% = −0,016** | l'IRR è quasi cieca ai cashflow: riscattare il 30% a metà percorso costa **22,51% di montante** e sposta l'IRR di **sedici millesimi di punto**. Se ti interessa quanto avrai, guarda il montante, non l'IRR | 70 |
| 11 | **2 su 201** | le anomalie pubblicate che sopravvivono a t>2 post-pubblicazione, costruzione value-weighted, capacità e costi retail. Il filtro che decide non è la significatività: **solo 22 su 201 sono value-weighted**, le altre sono guidate da microcap non eseguibili con €500 al mese | 10 |
| 12 | **5,91×** | quanto pesa l'ultimo triennio di un PAC ventennale rispetto al primo, calcolato analiticamente (∂IRR/∂r) e non stimato. Tre quantità diverse che tre giri avevano confuso: aritmetica pura 9,50, capitale esposto 24,72, **sensibilità dell'IRR 6,91** | 61 |

**Nessuno dei dodici è un margine di strategia.** Sono sette costi o soglie, cinque
misure di fragilità o di metodo. Questa metà della predizione L3 è centrata.

---

## Il controllo di falsificazione, fatto dalla macchina

La voce L3 sarebbe stata falsificata se nella rilettura fosse emerso **un
risultato di strategia mai contraddetto dai giri successivi e con margine sopra un
punto**. Non l'ho cercato a memoria: ho scandagliato il registro cumulato.

Su 1.365 righe, **213 (15,6%) hanno un extra ≥ +1,00 punto**, raggruppate in
**30 ipotesi distinte**. Ognuna esaminata:

| famiglia | gruppi | perché non sopravvive |
|---|---:|---|
| **cripto** (H20, H21, H24, H28, B6, F1) | 6 | finestre 2017-2026 con sopravvivenza selezionata — allargare l'universo ai simboli **oggi quotati** fa **salire** il buy&hold da 22,6% a 55,3% (giro 39). E il DSR li respinge dove è stato calcolato: 0,443 sul VWAP trimestrale, 0,880 sul Donchian. Il solo con DSR 0,999 (Kronos, giro 26) batte il buy&hold su **1 simbolo su 2** e ha accuratezza direzionale 50,8% contro 49,5% attesa, **χ² p = 0,671** |
| **anomalie pubblicate** (H10) | 1 | 78 righe sopra un punto, mediana +4,23 — ma sono premi lordi post-pubblicazione. Passano i quattro filtri **2 su 201**, e l'unica testata come strategia (Gross Profitability, giro 11) dà DSR 0,709 |
| **candidati storici** (H5, H11a/b/c, H12, H13) | 6 | i margini del 2024: +2,95, +3,08, +3,30, +1,38, +2,23. Contraddetti tre volte: contro l'equal-weight **dello stesso universo** sono negativi in **60 casi su 60** (giro 43); il benchmark spiega il 263-398% del margine (giro 60); e tutti e dodici cadono su G1 (giro 72). Il +2,23 di H13 crolla a **+0,75** già solo passando all'aliquota giusta per la sua rotazione, che era misurata con la convenzione difettosa |
| **opzioni** (E0, E1, E5, E6) | 4 | E1 è un premio reale (VIX sopra la realizzata nell'83,0% dei mesi, +3,91 punti) ma **incassarlo perde**: −4,98 vendendo put, −2,92 con gli indici CBOE reali. E5/E6: il +1,34 dei LEAPS è **stabile nel tempo** (17 finestre su 17) e muore per un'altra ragione — un rincaro del 10% del premio d'ingresso, cioè lo spread normale di un'opzione lunga poco liquida |
| **veicolo e metodo** (G2, D2, D4, D5, D8, D10, K4, A15, E0) | 9 | non sono margini di strategia: sono il premio di equal-weighting (+0,99 come portafoglio), il costo di realizzare, la sensibilità analitica dell'IRR, l'ampiezza del calendario. Dove *sembrano* margini, sono contraddetti nello stesso giro: il +3,82 del bootstrap è **lordo** e vale −1,20 netto; i +1,85/+1,99 del calendario sono i mesi migliori di dodici, la cui **mediana è −0,46**; il +2,35 del giro 65 è contro l'equal-weight **mensile** e torna negativo contro quello annuale |
| **multi-asset e regimi** (H1, H25, H26, F3/F4, B5) | 4 | respinti dal DSR nel proprio giro: 0,328 / 0,097 / 0,670 / —. Il +10,09 del sistema EMA è **LTC, il cui buy&hold fa −17%** |

**Nessun gruppo sopravvive. L3 non è falsificata.**

Un dettaglio che vale la pena isolare, perché è il modo tipico in cui questi
numeri nascono: il **+13,11 di Kronos** (giro 26) fu registrato come
«PROMUOVIBILE» con DSR 0,999. È ETH; su BTC la stessa strategia fa **−22,7
punti**. Un massimo su due celle, con un χ² che dice che il segnale non c'è. La
stessa forma del +0,86 del giro 73 (massimo di dieci celle, mediana −0,65) e del
+1,51 del giro 65 (gennaio, secondo mese migliore su dodici, mediana −0,46).

---

## Tre errori di misura trovati e corretti

Tutti e tre spingevano nella stessa direzione — **far sembrare l'attivo migliore
di quello che è** — e tutti e tre sono stati trovati dal progetto stesso, non
dall'esterno.

### 1. La base imponibile alla liquidazione *(il più grave)*

La plusvalenza finale era calcolata contro il valore del portafoglio al **primo
versamento** (~€500) invece che contro i **versamenti cumulati** (€204.000): il
motore tassava quasi l'intero montante. Segnalato dall'utente, che aveva notato
che i numeri non tornavano con un CAGR dell'S&P intorno al 10%.
**Effetto**: benchmark 8,11% → 8,40%. Il regime ETF non ne era toccato, perché
tiene la base per lotti.

### 2. I lotti dell'ETF non venivano ridotti *(giro 53)*

Liquidando quote per pagare l'imposta, il motore riduceva le `units` globali ma
**non i lotti**: la somma dei lotti restava gonfia e ogni deemed disposal
successivo tassava quote inesistenti. Su 57 anni e sette cicli il portafoglio si
azzerava — €3,48 M di imposte su €344.500 versati. C'era già una pezza al solo
realizzo finale: avevo notato la deriva e corretto il punto sbagliato.
**Effetto**: vantaggio del veicolo da +2,15 a **+1,23** su 1990-2023.

### 3. La rotazione era misurata con la convenzione sbagliata *(giri 60 e 63)*

`wbacktest` calcolava la rotazione come |W*ₜ* − W*ₜ*₋₁| sui **pesi target**, che
su pesi costanti fa **zero**: l'equal-weight ribilanciava ogni mese *gratis e non
tassato*. Ma l'errore ha **due versi**, e questa è la parte che non mi aspettavo:
altre routine usavano |W_detenuti,*ₜ* − W_detenuti,*ₜ*₋₁|, che **sovrastima**
contando la deriva dei prezzi come scambio.

La rotazione vera è **|W_target,*ₜ* − W_detenuti,*ₜ*| / 2**: quello che
effettivamente si compra e si vende. Per un equal-weight annuale vale **0,071×**,
contro lo 0,239× e lo 0,251× delle due convenzioni sbagliate.
**Effetto**: 1,35 punti sul benchmark principale, e **il 57,1% dei verdetti
riesaminati cambia segno** (giro 65) — senza però produrre una sola promozione,
perché contro il benchmark corretto tornano negativi.

### E una quarta correzione, di natura diversa

**I dividendi non erano tassati al detentore diretto** (giro 56). Nei confronti
CGT-contro-ETF passavo la serie total return senza `div_yield`, il che equivale a
far accumulare i dividendi esentasse anche a chi tiene le azioni in proprio — vero
per un fondo ad accumulazione, falso per un residente irlandese che paga ~52%
ogni anno.

| dividend yield | vantaggio 1990-2023 | vantaggio 1990-2026 |
|---:|---:|---:|
| 0,0% (quello che avevo usato) | +1,23 | +1,49 |
| **2,0% (storico S&P)** | **+0,34** | **+0,56** |

**È qui che muore il +1,72 del report del giro 29.** La catena completa:
+1,72 → +2,01 (base fiscale) → +2,15 → **+1,23** (lotti ETF) → **+0,34**
(dividendi), sulla stessa finestra 1990-2023. Il numero è ancora positivo e
**cresce con l'orizzonte** (+0,56 su 1990-2026, **+1,09** su 1969-2026), ma non è
più la voce dominante del progetto: è un ordine di grandezza diverso da quello che
avevo scritto in prima pagina.

---

## Cosa è stato provato, e come è morto

Settantaquattro giri, per famiglia. Il dettaglio sta nei mini-report.

| famiglia | provato | esito | il numero |
|---|---|---|---|
| **Swing / trading tecnico** | RSI2, down-streak, Donchian, trend+stop, sistemi EMA 9/21/50/200 su 10 asset e 3 timeframe | nessun edge, spesso **negativo già in-sample** | il **solo filtro di tendenza** rende 24 volte il sistema completo: 13,321% contro 0,564% di aspettativa per operazione |
| **Momentum / rotazione settoriale** | 12-2 e 6-2, top-1/3/5/10/25, mensile/trimestrale/annuale, isteresi, hold minimo, budget di rotazione, ritardo di esecuzione 0-20 giorni | il miglior candidato del progetto, e **non basta** | +0,56 contro l'equal-weight annuale; da 1 a 5 posizioni valgono +5,5 punti di IRR e **+27 di drawdown** |
| **Allocazione e sizing** | risk parity, HRP, min-variance, max-diversification, Kelly frazionario, de-risking, leva con margin call ESMA | il de-risking migliora il drawdown in **12 casi su 12** e l'IRR in **0 su 12** | lo Sharpe più alto della ricerca (**1,19** contro 0,69) rende **4,24 punti di IRR in meno**. E la leva **distrugge** lo Sharpe che doveva monetizzare (0,78 → 0,69) |
| **Anomalie pubblicate** | 201 anomalie con ≥10 anni post-pubblicazione (Chen-Zimmermann) | decadimento del 50,4% confermato; **2 sopravvivono ai quattro filtri** | 22 su 201 sono value-weighted |
| **Mercati nuovi** | materie prime, valute, credito, curva dei tassi, azionario internazionale, cripto | il trend following sulle commodity **funziona lordo e muore netto**: 5,31% contro 3,76% del buy&hold, ma 3,75% contro 9,90% dell'azionario | la curva dei tassi ha ragione **12 volte su 13** con 13 mesi di anticipo — e la strategia perde comunque 1,2-2,6 punti |
| **Opzioni** | premio di varianza, put cash-secured, covered call, LEAPS come leva | il premio è reale, **incassarlo perde** | vendere put: Sharpe lordo 0,77 > 0,71, IRR netta **−4,98**, skew da −4,15 a **−12,57** |
| **Regimi** | HMM, catena di Markov, breadth, VIX term structure, **statistical jump model** (Aydınhan-Kolm-Mulvey-Shu 2024) | il jump model perde in **21 configurazioni su 21** sia long sia long/short | **migliora quanto meno lo si ascolta**: a λ=200 cambia stato una volta ogni 17 anni, sta investito l'84,4% del tempo, e il divario si chiude da −4,77 a −1,63. Ciò che si compra con la persistenza è il diritto di stare fermi, e stare fermi al 100% si chiama buy&hold |
| **Portfolio theory stocastica** | diversity-weighting, identità di Fernholz su 437 mesi | **il teorema è vero e il trade è in perdita**: γ* = 1,12%/anno esiste, la deriva della diversità lo annulla *prima* delle imposte | l'orizzonte su cui il teorema **garantisce** l'arbitraggio relativo è **6.484 anni** per p=0,50 |
| **Metodo** | dispersione per finestra, bootstrap a blocchi, benchmark, rotazione, calendario, valuta, PAC interrotto, costi retail | quasi ogni giro metodologico ha trovato **un difetto di misura o un grado di libertà mai contato**, non un edge | vedi *[I numeri che contano](#i-numeri-che-contano)* |

---

## Cosa cambia rispetto al report del giro 29

Chi ha letto la versione precedente trova qui tre cose diverse. Le elenco perché
due di esse erano **raccomandazioni**, e sono state ritirate.

| il giro 29 diceva | oggi | perché |
|---|---|---|
| **«Il veicolo vale +1,72 punti l'anno, è il risultato più grande e affidabile del lavoro»** | **+0,34** sulla stessa finestra, +1,09 su 1969-2026 | due correzioni: i lotti ETF (giro 53) e i dividendi non tassati al detentore diretto (giro 56). La raccomandazione **regge nel verso**, non nella taglia — e vale solo per chi sta fermo |
| **«Il trend following mensile a 10 mesi è l'unica strategia attiva che regge tutti gli stress; a 2× rende +3,70»** | **ritirata** | la leva col margin call ESMA modellato dà **−4,18** (giro 07), e a 1,50× su min-variance il margin call scatta con equity al 2,3% (giro 35). Testati sistematicamente al giro 53, **nessun filtro di tendenza batte il buy&hold**: il migliore perde **2,51** punti — e vince fra i filtri solo perché ruota 0,19×/anno contro 1,3-2,2 degli altri. In cambio di 18-40 punti di drawdown |
| «Il gruppo D è un teorema vero e un trade in perdita» | **invariata** | γ* = 1,12%/anno esiste, l'identità di Fernholz torna, la deriva della diversità la annulla, le imposte portano il residuo sotto zero |

Il giro 29 aveva anche scritto che il trend following andava «trattato con
sospetto per tre ragioni che il backtest non cattura». Erano le ragioni giuste, e
il sospetto era troppo blando: quando i tre punti sono stati misurati invece che
sospettati, la strategia è caduta.

---

## Quello che il progetto non può dire

Da leggere prima delle raccomandazioni.

- **Un solo mercato, in sostanza.** Il grosso gira sull'universo di Ken French
  (indice CRSP e 49 portafogli settoriali, 1926-2026). Lungo e pulito, ma è
  l'azionario USA. Il confronto globale-contro-USA (giro 57) dà +1,89 punti
  all'S&P sui dati reali 2011-2026 — e l'USA vince solo il **73%** delle finestre
  decennali, con le sette perse che partono **tutte fra il 1995 e il 2001**.
- **Il livello dei rendimenti è in dollari.** Convertito in euro (giro 69,
  DEM sintetico a 1,95583 prima del 1999), l'azionario USA ha reso **0,46-0,77
  punti l'anno in meno** di quanto scritto ovunque nel progetto. **Nessun verdetto
  cambia** — il margine si sposta al massimo di 0,25 punti — ma il livello sì.
- **Niente dati a livello di singolo titolo.** La diversità è misurata **fra 49
  settori**, il che sottostima la concentrazione vera: dentro "Tecnologia" il peso
  di una singola società non si vede. Serve CRSP/Compustat firm-level.
- **Serie bloccate**: OHLC di SPY/QQQ/IWM/EFA/EEM/GLD/TLT non scaricabili (Yahoo
  429, Stooq anti-bot), quindi nessuno stop in ATR; l'high yield ICE
  (`BAMLH0A0HYM2`) si scarica solo per 35 mesi contro i 30 anni necessari, e la
  voce B3 è chiusa **senza esito**.
- **Il motore fiscale aggrega.** Tiene un solo costo medio e realizza pro quota,
  mentre nella realtà si vendono posizioni specifiche e vendere un perdente
  cristallizza una minusvalenza. Misurato con un motore per posizione scritto
  apposta: **da +0,10 a +0,41 punti a favore delle strategie che ruotano**. Il
  divario più stretto mai registrato è 1,14 punti, quindi nessun verdetto cambia —
  ma il numero va sottratto mentalmente da ogni margine di una strategia veloce.
- **L'holdout 2010-2026 non è mai stato guardato.** Tutto ciò che sta qui è
  1969-2009 (o la finestra dichiarata voce per voce).

---

## Raccomandazioni operative

Poche, e nessuna riguarda quale segnale seguire.

### 1. Il veicolo, ma nel verso giusto — e non è quello che avevo scritto

| chi sei | veicolo migliore | margine |
|---|---|---:|
| **stai fermo** (buy&hold, cap-weight) | **azioni / indice in regime CGT** | **+1,09** |
| **ruoti spesso** (2,8×/anno) | **fondo o ETF UCITS** | **+0,64** |

Due segni opposti che dicono una cosa sola: **l'ETF UCITS compra il diritto di non
realizzare, e lo paga col deemed disposal ogni otto anni**. Chi non realizzerebbe
comunque sta comprando un diritto che non usa. Il vantaggio del diretto **cresce
con l'orizzonte** (+0,34 su 1990-2023, +1,09 su 1969-2026): sono sette prelievi
forzosi al 41/38% contro un solo 33% finale.

Il corollario è scomodo ma è il risultato più solido del progetto: **se proprio
vuoi una strategia che ruota, la cosa che conta di più non è la strategia — è non
essere tu a premere il bottone del realizzo.** A parità esatta di rendimento
lordo, spostare la rotazione dentro un fondo vale **+3,43 punti**. Non è un
vantaggio disponibile — nessuno lo incassa scegliendo un prodotto — ma è la misura
di quanto costa realizzare in conto proprio.

### 2. Non superare il 100% di rotazione annua. Mai.

Non è una linea morbida: è un **gradino** da 33% a 52%. Un budget di rotazione
esplicito (ribilanciamento parziale, ~0,95×/anno) fa guadagnare **+0,79 e +1,02
punti** alle configurazioni che grazie a esso **riattraversano la soglia** — e
**−0,09** a quella che era già sotto. Vincolare di per sé non giova: giova
scavalcare la soglia nel verso giusto. Rinunciare all'ultimo 10% di rotazione
costa 0,11-0,59 punti di CAGR **lordo** e ne rende molti di più netti.

### 3. Se selezioni, il mese in cui ribilanci è una scelta, non un dettaglio

Vale **3,65 punti di ampiezza** su un top-5 e **0,14** su un equal-weight. Il
grado di libertà esiste solo per chi seleziona, e **scala con la concentrazione**.
Chi sceglie il mese guardando il passato si sta regalando un parametro libero mai
contato: al giro 65 il +1,51 di gennaio era il secondo mese migliore su dodici, e
la mediana dei dodici era **−0,46**.

### 4. Un PAC frammentato in azioni singole non è un prodotto retail

Soglia: *P* × €1,50 / 1%. Su 49 posizioni servono **€7.350 al mese** perché le
commissioni del versamento restino sotto l'1%; a €750 se ne va il **14,7%**. E
concentrare il versamento in un ordine solo **non serve** se poi ribilanci: gli
ordini si spostano, non spariscono (636 → 600 all'anno, IRR identica). Un
equal-weight diversificato si compra **come fondo** — per le commissioni, prima
ancora che per le imposte.

### 5. Guarda il montante, non l'IRR

L'IRR è quasi cieca alle irregolarità dei versamenti: saltare 24 rate costa
**−8,66% di montante** e sposta l'IRR di **+0,021**; riscattare il 30% costa
**−22,51% di montante** e **−0,016** di IRR. Se la domanda è «quanto avrò», l'IRR
non è lo strumento — e l'effetto **cambia segno intorno al sesto anno**, il che è
lo stesso profilo che si vede dal lato analitico (l'ultimo triennio pesa 5,91
volte il primo).

### 6. E su tutto il resto: non fare niente

Il ribilanciamento è un evento tassabile e, in questo regime, quasi sempre in
perdita. Vale per il diversity-weighting, per l'equal-weighting e per qualunque
schema a pesi fissi. Con CGT al 33% e nessun conto fiscalmente protetto, **la
strategia migliore è quella che non vende** — e il suo avversario, un cap-weight
che non si ribilancia mai perché i pesi seguono da soli i prezzi, è imbattibile
per costruzione fiscale.

---

## Appendice A — il gate di calibrazione

Prima di qualunque risultato, i due numeri di riferimento riprodotti.

| | misurato | riferimento | delta |
|---|---:|---:|---:|
| Buy&hold indice, CGT 33% all'uscita | 8,11% | 8,21% | −0,10 |
| ETF UCITS, exit tax + deemed disposal | 6,39% | 6,76% | −0,37 |
| Max drawdown | −49,0% | −47% | −2,0 |

*(Valori del giro 29, prima della correzione della base fiscale, che porta il
benchmark a 8,40%.)*

Una **incompatibilità nella specifica**, risolta e dichiarata: il benchmark è
definito come «CGT 33% solo all'uscita», ma la tabella fiscale impone anche
«dividendi esteri ~52%». Sono incompatibili — con i dividendi tassati ogni anno
l'IRR scende a 7,02%. Ho adottato la definizione letterale del benchmark e riporto
la variante realistica separatamente. **Il prelievo annuo sui dividendi esteri
costa 1,09 punti l'anno**, ed è lo stesso meccanismo che al giro 56 ha dimezzato
il vantaggio del veicolo.

Per le opzioni c'è un cancello separato (giro 48), aperto solo dopo due
correzioni: scadenze al **terzo venerdì** (la correlazione con gli indici CBOE
reali passa da 0,850 a 0,975) e **IV = 0,85 × VIX**. Residui BXM +0,55 e PUT
−0,72, di **segno opposto**, che è la firma dello skew — ed è esattamente
l'errore che al giro 49 faceva sembrare la covered call **+0,98 con DSR 0,997**,
la prima promozione apparente del progetto. Coi dati reali: **−2,92**.

## Appendice B — fonti

Ken French Data Library (indice CRSP giornaliero 1926-2026, 26.253 sedute; 49
portafogli settoriali giornalieri e mensili con capitalizzazioni reali), Robert
Shiller (`ie_data.xls`), AQR (*Betting Against Beta*), Open Source Asset Pricing
(Chen & Zimmermann, 212 anomalie replicate), CBOE (BXM, PUT), FRED (`EXGEUS`,
`BAMLH0A0HYM2`), Twelve Data (intraday), Binance (cripto).
Tutte riscaricabili con `quant/fetch_data.sh`.

## Appendice C — dove sta il resto

| cosa | dove |
|---|---|
| ipotesi pre-registrate e tabella degli esiti | [`../research/QUEUE.md`](../research/QUEUE.md) |
| stato del metodo, note accumulate, regola dell'holdout | [`../research/STATE.md`](../research/STATE.md) |
| mini-report giro per giro | [`../research/rounds/`](../research/rounds/) |
| ogni configurazione valutata (1.366 righe) | `../research/registry.csv` |
| codice di ogni giro | `../src/research/` |

---

*Holdout 2010-2026: **aperto una volta sola al giro 78**, sul momentum 12-3 top-5
mensile — l'unico candidato che in settantotto giri abbia passato tutti e quattro
i cancelli. Margine **−0,95**, negativo in dodici calendari su dodici. Ora
**bruciato**: non si riapre.*

# Giro 75 — L3: il report finale

**Predizione** (verbatim, committata prima di eseguire): *i numeri che
sopravvivono a una rilettura completa sono **meno di dieci**, e **nessuno** di
essi è un margine di strategia: sono tutti costi, soglie o misure di fragilità.*
**Falsificata se**: nella rilettura emerge un risultato di strategia **mai
contraddetto** dai giri successivi e con **margine sopra un punto**.

**Esito: CONFERMATA sulla clausola che falsifica. Sbagliata sul conteggio, e
sbagliata per difetto — sono dodici, non meno di dieci.**

Prodotto: [`quant/reports/REPORT.md`](../../reports/REPORT.md), riscritto da capo.
Era fermo al giro 29 e portava in prima pagina il **+1,72**.

## Il controllo di falsificazione l'ho fatto fare alla macchina

Non a memoria: su 1.365 righe la memoria è esattamente lo strumento che questo
progetto ha passato quaranta giri a non fidarsi. `round75.py` scandaglia il
registro cumulato e tira fuori **ogni** riga con extra ≥ +1,00 punto.

| | |
|---|---:|
| righe a registro (giri 1-74) | 1.365 |
| righe con extra ≥ +1,00 | **213** (15,6%) |
| ipotesi distinte che le contengono | **30** |
| di queste, con la **mediana** del gruppo sopra +1,00 | 30 |
| di queste, sostenute da **una sola riga** | 13 |
| mediana dell'extra su tutto il registro | **−1,32** |
| quota di righe positive | **30,3%** |

La distribuzione dice già quasi tutto: il **55,9%** del registro sta sotto −1,00
punto, il 9,8% sopra +3,00 — e quel 9,8% è quasi interamente cripto e premi
lordi pre-imposte.

## I trenta gruppi, esaminati uno per uno

| famiglia | gruppi | come muore |
|---|---:|---|
| cripto | 6 | sopravvivenza selezionata (allargare l'universo **alza** il buy&hold da 22,6% a 55,3%) e DSR: 0,443 / 0,880. L'unico con DSR 0,999 batte il B&H su **1 simbolo su 2** con χ² p = 0,671 |
| anomalie pubblicate | 1 | 78 righe sopra un punto, ma sono premi lordi: **2 su 201** passano i quattro filtri, e l'unica testata come strategia dà DSR 0,709 |
| candidati storici (H5, H11a/b/c, H12, H13) | 6 | negativi in **60 casi su 60** contro l'equal-weight dello stesso universo (giro 43); il benchmark spiega il **263-398%** del margine (giro 60); **12/12 cadono su G1** (giro 72). Il +2,23 di H13 crolla a **+0,75** già solo con l'aliquota giusta per la sua rotazione vera |
| opzioni | 4 | il premio esiste (83,0% dei mesi, +3,91 punti) e **incassarlo perde**: −4,98 / −2,92. I LEAPS muoiono per un rincaro del 10% del premio d'ingresso |
| veicolo e metodo | 9 | **non sono margini di strategia**: premio di equal-weighting, costo di realizzare, sensibilità analitica dell'IRR, ampiezza del calendario |
| multi-asset e regimi | 4 | DSR nel proprio giro: 0,328 / 0,097 / 0,670. Il +10,09 è **LTC, il cui buy&hold fa −17%** |

**Nessuno sopravvive.** La condizione di falsificazione non scatta.

Il caso più istruttivo è il **+13,11 di Kronos** (giro 26), che all'epoca
registrai come «PROMUOVIBILE» con DSR 0,999: è ETH, e su BTC la stessa strategia
fa **−22,7 punti**. Un massimo su due celle, con un χ² che dice che il segnale non
c'è. È la stessa forma del +0,86 del giro 73 (massimo di dieci celle, mediana
−0,65) e del +1,51 del giro 65 (gennaio, mediana dei dodici mesi −0,46). Il
progetto ha prodotto lo stesso artefatto tre volte in settantacinque giri, e l'ha
riconosciuto tre volte solo perché la regola era scritta prima.

## Dove la predizione sbaglia

Criterio dichiarato prima di contare: un numero sopravvive se **(a)** nessun giro
successivo lo ha contraddetto e **(b)** regge una conclusione o una
raccomandazione. Applicandolo, sono **dodici**: sette costi o soglie (rotazione
vera 1,35; soglia del 100% come gradino; calendario 3,65 contro 0,14; veicolo
+1,09/+0,64; costo di realizzare +3,43; soglia retail €7.350; quota fiscale
massima 15,3%) e cinque misure di fragilità o metodo (ampiezza decennale
5,81-10,19; il benchmark spiega il 263-398%; l'IRR cieca a −22,51% di montante;
2 anomalie su 201; il peso analitico 5,91×).

«Meno di dieci» è **sbagliata**. Non di poco e non nel verso comodo: ce ne sono
**più** di quanti ne avevo previsti, e il motivo è che i giri 59-74 — quelli
metodologici — hanno prodotto numeri nuovi invece di limitarsi a demolire i
vecchi. Se li avessi contati per **famiglia** invece che uno per uno sarebbero
cinque, ma la predizione diceva «numeri», non «famiglie», e non la riscrivo
adesso.

L'altra metà — **nessuno di essi è un margine di strategia** — è centrata, ed è
quella su cui la voce si giocava la falsificazione.

## Cosa contiene il report nuovo

Le quattro cose che la voce chiedeva, più una che non chiedeva.

1. **La regola dell'holdout del giro 72**, con il conteggio dei cancelli: G1
   elimina 12/12, e il più vicino al bersaglio fallisce G3 per **sette decimi di
   punto percentuale**.
2. **I numeri che contano**, dodici, con il giro di provenienza.
3. **I tre errori di misura** trovati e corretti — base fiscale, lotti ETF,
   rotazione — più il quarto, i dividendi non tassati al detentore diretto, che è
   quello che uccide il +1,72.
4. **Le raccomandazioni operative**, sei, nessuna delle quali riguarda quale
   segnale seguire.
5. **Una sezione che non era richiesta**: *cosa cambia rispetto al report del giro
   29*. Due delle raccomandazioni di allora vanno **ritirate**, non aggiornate —
   il +1,72 sul veicolo e il trend following levereggiato — e un report finale che
   le lasciasse cadere in silenzio sarebbe disonesto verso chi ha letto la
   versione precedente.

La catena completa del numero ritirato, che è il singolo pezzo di storia più utile
del progetto: **+1,72 → +2,01** (base fiscale) **→ +2,15 → +1,23** (lotti ETF,
giro 53) **→ +0,34** (dividendi al 2%, giro 56), sulla stessa finestra 1990-2023.
Quattro misurazioni dello stesso oggetto, ognuna più corretta della precedente,
per un fattore cinque complessivo. È ancora positivo e **cresce con l'orizzonte**
(+1,09 su 1969-2026), ma non è più la voce dominante di niente.

## Nessuna idea nuova in coda

La rilettura non ne ha prodotte: ogni domanda aperta che ho incontrato era già
una voce (L4 sullo skip) o già chiusa. Resta **L4**, ed è l'ultima.

Nessuna promozione. Nessuna selezione: la soglia del +1,00 per lo scan è quella
del cancello G1, fissata al giro 72.

**Tentativi cumulati a registro: 1.366.** Holdout 2010-2026 **ancora sigillato**.

# Giro 70 — K2: il PAC che si interrompe

**Predizione** (verbatim, committata prima di eseguire): *l'interruzione costa
**meno di 0,3 punti** di IRR ovunque, mentre il **montante cala di 8-12%** e il
calo è **monotono decrescente in k**. Il riscatto anticipato invece colpisce
l'IRR, e di **oltre 0,5 punti** se avviene nei primi dieci anni.*
**Falsificata se**: l'interruzione sposta l'IRR di **oltre 0,5 punti** in qualche
k, **oppure** il calo del montante non è monotono in k.

**Esito: FALSIFICATA** — ma su una lettura ambigua che devo dichiarare, e che
risolvo **contro di me**.

## L'ambiguità, e come la risolvo

Nel codice avevo dichiarato di verificare la **monotonia** sulla mediana delle
finestre, non su ogni singola finestra. Non avevo dichiarato la stessa cosa per
la clausola sull'IRR, e "in qualche k" si può leggere in due modi:

| lettura | misura | esito |
|---|---:|---|
| mediana sulle 64 finestre | max **0,126** punti | non falsifica |
| **ogni coppia (k, finestra)** | max **1,019** punti | **falsifica** |

Prendo la seconda, che è la più severa per me: **K2 è falsificata**. Il massimo è
a **k=1 sulla finestra che parte nel 1928**, e le coppie sopra 0,5 punti sono
**50 su 1.152, il 4,3%** — cioè una coda, non il caso tipico. Ma la condizione
non diceva "tipicamente".

## I numeri, 64 finestre ventennali 1926-2009

PAC di riferimento: IRR mediana **9,73%**, montante mediano su €120.000 versati.

| anno k | **interruzione 24 mesi** | | | **riscatto 30%** | |
|---:|---:|---:|---:|---:|---:|
| | Δ IRR | Δ montante | versato | Δ IRR | Δ montante |
| 1 | **−0,096** | **−21,13%** | 90% | −0,000 | −0,27% |
| 2 | −0,126 | −19,09% | 90% | −0,004 | −3,38% |
| 3 | −0,086 | −16,90% | 90% | −0,006 | −6,57% |
| 5 | −0,022 | −13,93% | 90% | −0,027 | −11,86% |
| **6** | **+0,012** | −12,42% | 90% | −0,052 | −14,29% |
| 9 | +0,044 | −9,01% | 90% | −0,038 | −21,56% |
| 12 | +0,032 | −6,69% | 90% | −0,062 | −26,89% |
| 15 | +0,029 | −5,07% | 90% | +0,028 | −31,09% |
| 18 | +0,009 | **−4,05%** | 90% | +0,087 | **−34,21%** |

| clausola | previsto | misurato | |
|---|---:|---:|---|
| interruzione, ΔIRR mediano | < 0,3 | **max 0,126** | **centrata** |
| montante, calo | −8 / −12% | **da −21,13% a −4,05%** | **sbagliata** |
| calo monotono in k | sì | **sì** | centrata |
| riscatto, ΔIRR primi 10 anni | oltre −0,5 | **da −0,072 a −0,000** | **sbagliata** |

## Il risultato: l'IRR è quasi cieca a entrambi gli eventi

| evento | costo in **montante** | costo in **IRR** |
|---|---:|---:|
| saltare 24 versamenti (10% del capitale) | **−8,66%** | **+0,021** |
| riscattare il 30% del portafoglio | **−22,51%** | **−0,016** |

Un riscatto che porta via **un quinto del montante finale** sposta l'IRR di
**sedici millesimi di punto**. È il risultato che la voce cercava, e conferma
esattamente la conseguenza che la condizione di falsificazione le attaccava:
**l'IRR non è la metrica giusta per un PAC irregolare, serve il montante.**

Il motivo è che l'IRR è un *tasso*: misura quanto rende ogni euro versato, non
quanti euro si è versato. Togliere versamenti toglie montante ma lascia il tasso
dov'era; prelevare denaro riduce il montante ma quel denaro il suo rendimento
l'aveva già fatto.

## Il segno cambia al sesto anno, e non è rumore

L'effetto dell'interruzione sull'IRR è **negativo fino all'anno 5 e positivo dal
6 in poi** (da +0,009 a +0,044). Non è un artefatto: è il profilo del giro 61
visto dal lato dei versamenti.

L'IRR è una media dei rendimenti per euro versato, pesata per quanto a lungo ogni
euro resta investito. Un euro versato al primo anno si compone per venti anni e
rende molto; uno versato al diciottesimo si compone per due e rende poco.
**Togliere i versamenti tardivi alza la media**, perché elimina gli euro che
rendono meno. Togliere quelli iniziali la abbassa.

Il che ha una conseguenza pratica poco intuitiva: **se si è costretti a
sospendere, sospendere tardi costa meno in montante *e* fa perfino salire l'IRR**
— ma è l'IRR che sta mentendo, non il montante. Il montante cala comunque del
4-5%.

## Perché avevo sbagliato le due clausole

**Sul montante**: avevo ragionato che 24 versamenti su 240 sono il 10% del
capitale, quindi ~10% di montante. Sbagliato: gli euro saltati al primo anno si
sarebbero composti per vent'anni, quelli saltati al diciottesimo per due. Il calo
va da **−21,13% a −4,05%** — un fattore **cinque** fra i due estremi. Il 10% è la
media, non l'intervallo.

**Sul riscatto**: avevo previsto oltre −0,5 punti di IRR nei primi dieci anni, e
il massimo misurato è **−0,072**. L'errore è lo stesso di prima al contrario:
avevo pensato al riscatto come a un danno al *rendimento*, mentre è un danno al
*capitale investito*. Il denaro prelevato smette di comporsi, ma quello che aveva
già guadagnato resta nel conto dell'IRR.

## Cosa resta

**Per l'investitore**: interrompere due anni di versamenti costa fra il 4% e il
21% del montante a seconda di quando, ed è **presto** che costa. Riscattare il
30% costa fra il 3% e il 34%, ed è **tardi** che costa — perché tardi il 30% è
30% di un portafoglio molto più grande.

**Per il progetto**: da qui in avanti, ogni volta che si confrontano PAC con
flussi diversi va riportato il **montante**, non solo l'IRR. Fra le voci già
eseguite non ce ne sono — tutte confrontano PAC coi flussi identici, dove l'IRR
è legittima — ma la regola va scritta.

Nessuna promozione. Nessuna selezione: N resta la famiglia pre-dichiarata.

**Tentativi cumulati a registro: 1.330.** Holdout 2010-2026 **ancora sigillato**.

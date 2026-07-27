# Giri 50-51 — gruppo F: rotazione concentrata e sistema EMA 9/21/50/200

Cinque voci pre-registrate e committate prima di eseguire (`388ee8d`).
**F2, F3, F5 confermate; F1 e F4 falsificate**, entrambe con una lettura precisa.

---

## Giro 50 — F1: rotazione sul migliore del periodo precedente → **FALSIFICATA**

Tre universi × tre frequenze. La regola è quella della domanda: alla fine di ogni
periodo si tiene **il primo** del periodo appena chiuso.

| universo | configurazione | CAGR | Sharpe | max DD | rotaz. | IRR di rif. | vs equal-weight |
|---|---|---:|---:|---:|---:|---:|---:|
| 49 settori | equal-weight | 11,15% | 0,70 | −52,6% | 0,00× | **11,16%** | — |
| 49 settori | top-1 mensile | 5,15% | 0,32 | −74,1% | 11,2× | 4,64% | **−6,52** |
| 49 settori | top-1 trimestrale | 4,17% | 0,29 | −91,2% | 3,7× | 4,39% | −6,77 |
| 49 settori | top-1 annuale | 6,02% | 0,35 | −83,9% | 0,94× | 4,53% | −6,63 |
| regioni | equal-weight | 7,49% | 0,52 | −56,0% | 0,00× | 6,45% | — |
| regioni | **top-1 mensile** | 9,21% | 0,60 | −42,3% | 8,9× | **6,75%** | **+0,30** |
| 8 cripto | equal-weight | 46,62% | 0,75 | −76,7% | 0,00× | **47,17%** | — |
| 8 cripto | top-1 mensile | 19,26% | 0,60 | −90,1% | 10,2× | 9,22% | −37,96 |
| 8 cripto | top-1 annuale | 0,10% | 0,41 | −96,3% | 0,99× | −33,82% | −80,99 |

**Falsificata da una sola cella su nove**: regioni top-1 mensile, **+0,30 punti**.

Quella cella non è un risultato: è l'universo più debole (4 regioni, 431 mesi), con
**894% di rotazione l'anno**, e il suo 6,75% perde **3 punti** contro il semplice
buy&hold azionario USA sulla stessa finestra (9,68%, giro 39). Ha battuto un
benchmark che era già la cosa peggiore in tabella.

**Le altre otto celle perdono da 1,4 a 81 punti.** Sui 49 settori il top-1 perde
6,5-6,8 punti a **qualunque** frequenza; sulle cripto il top-1 annuale arriva a
**−96,3% di drawdown** e IRR **−33,82%**.

## Giro 50 — F2: la griglia completa → **CONFERMATA**

IRR netta di riferimento sui 49 settori (33% o 52% secondo la rotazione):

| posizioni | mensile | trimestrale | annuale |
|---:|---:|---:|---:|
| **1** | 4,64%* | 4,39%* | 4,53% |
| 3 | 5,88%* | 5,65%* | 9,12% |
| 5 | 6,59%* | 7,26%* | **10,02%** |
| 10 | 7,06%* | 8,06%* | 8,91% |
| 25 | 7,43%* | 8,09%* | 9,47% |

\* oltre 100% di rotazione l'anno → valutata al 52%.
**Equal-weight statico: 11,16%.** Nessuna delle quindici celle lo batte.

Il costo della concentrazione, a frequenza annuale:

| | CAGR | Sharpe | max DD | rotazione | IRR |
|---|---:|---:|---:|---:|---:|
| top-1 | 6,02% | 0,35 | **−83,9%** | 0,94× | 4,53% |
| top-3 | 12,15% | 0,61 | −64,1% | 0,86× | 9,12% |
| top-5 | **12,72%** | 0,67 | −56,7% | 0,83× | **10,02%** |
| top-10 | 11,27% | 0,66 | −59,9% | 0,76× | 8,91% |
| top-25 | 11,49% | 0,72 | −50,9% | 0,48× | 9,47% |

**Le due clausole di monotonia sono entrambe sbagliate**: la relazione col numero
di posizioni è a campana (massimo a 5, poi cala a 10, poi risale a 25), e con la
frequenza non è monotona per il top-1. Ma il test — *il massimo sta sotto 5
posizioni, oppure batte l'equal-weight statico* — è superato in entrambi i rami:
il massimo è a 5 posizioni e resta 1,14 punti sotto lo statico.

**Il numero che risponde alla domanda**: passare da 1 a 5 posizioni vale **+5,5
punti di IRR e +27 punti di drawdown**. Concentrare sul migliore è la scelta
peggiore dell'intera griglia, in ogni universo e a ogni frequenza.

---

## Giro 51 — F3: il sistema EMA 9/21/50/200 → **CONFERMATA**

Regole implementate esattamente come nell'immagine. Lo stop iniziale non è
specificato lì: l'ho fissato al minimo delle ultime 10 barre e l'ho dichiarato in
coda. **Ordine dentro la barra: sempre prima il peggio** — se una barra tocca sia
stop sia target, conta lo stop. È l'unica ipotesi difendibile senza dati intrabar.

| asset | anni | oper. | op/anno | CAGR sistema | CAGR B&H | IRR sistema | IRR B&H | delta |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| QQQ | 19,9 | 141 | 7,1 | 0,75% | 15,55% | 0,26% | 14,80% | **−14,55** |
| AAPL | 19,9 | 117 | 5,9 | 3,41% | 27,59% | 1,57% | 23,19% | −21,62 |
| BTC | 8,8 | 65 | 7,4 | 13,92% | 34,04% | 4,61% | 25,71% | −21,10 |
| ETH | 8,8 | 84 | 9,6 | 3,37% | 23,55% | 2,24% | 22,58% | −20,34 |
| DOGE | 7,0 | 40 | 5,7 | 9,34% | 58,13% | 3,84% | 45,70% | −41,86 |
| SOL | 5,8 | 30 | 5,2 | −4,59% | 74,07% | −1,53% | 41,20% | −42,74 |
| LINK | 8,5 | 63 | 7,4 | 9,29% | 26,12% | −2,90% | 28,91% | −31,81 |
| XRP | 8,5 | 46 | 5,4 | 2,59% | −7,80% | 0,28% | 14,38% | −14,10 |
| ADA | 8,0 | 39 | 4,9 | −0,11% | −0,29% | −4,55% | 1,95% | −6,49 |
| **LTC** | 8,5 | 59 | 6,9 | 1,61% | −17,05% | −0,75% | −10,85% | **+10,09** |

**Batte il buy&hold su 1 asset su 10** — e quell'uno è LTC, l'unico il cui
buy&hold è profondamente negativo (−17%). Il sistema non ci ha guadagnato: ha
perso meno.

Da notare che **la predizione sbagliava anche il verso sul lordo**: avevo scritto
"lordo positivo sugli asset in tendenza". Il CAGR lordo del sistema è 0,75% su QQQ
contro 15,55% del buy&hold, e negativo su SOL e ADA. Non è che muore sulle imposte:
**muore prima**, sul lordo.

## Giro 51 — F4: gli stessi timeframe intraday → **FALSIFICATA**

| timeframe | barre | anni | oper. | op/anno | CAGR sistema | CAGR B&H | IRR sistema |
|---|---:|---:|---:|---:|---:|---:|---:|
| giornaliero | 5.000 | 19,9 | 141 | **7,1** | 0,75% | 15,55% | 0,30% |
| 1 ora | 5.000 | 2,9 | 96 | **33,6** | 0,62% | 22,89% | **1,12%** |
| 15 minuti | 5.000 | 0,8 | 103 | **133,4** | −16,67% | 16,55% | **−18,65%** |

**Falsificata**: l'orario (1,12%) supera il giornaliero (0,30%).

Ma la falsificazione è un artefatto della finestra, e va detto: Twelve Data dà
**5.000 barre e basta**, quindi i tre timeframe coprono **20 anni, 2,9 anni e 0,8
anni** — periodi completamente diversi. La finestra oraria (2023-2026) è un mercato
toro per il QQQ, con buy&hold al 22,89%. Confrontare CAGR fra quelle righe non
misura il timeframe, misura il periodo.

Il meccanismo previsto invece si vede benissimo, ed è confrontabile: **7,1 → 33,6 →
133,4 operazioni l'anno**. E a 15 minuti il sistema perde **18,65%** contro un
buy&hold a **+20,30%**: un divario di **39 punti** in dieci mesi. La monotonia
fallisce sul punto centrale per la finestra, e regge in modo devastante all'estremo.

## Giro 51 — F5: quale pezzo fa il lavoro → **CONFERMATA**

Ablazione su tutti e dieci gli asset, media semplice:

| variante | oper./anno | CAGR medio | **aspettativa per operazione** | IRR media |
|---|---:|---:|---:|---:|
| sistema completo | 6,5 | 3,96% | **0,564%** | 0,31% |
| senza filtro volume | 11,6 | 14,11% | 1,098% | 3,66% |
| senza ritracciamento | 17,5 | 23,42% | 1,377% | 10,90% |
| **solo filtro di tendenza** | **3,5** | **45,13%** | **13,321%** | **27,16%** |

Il rapporto fra le aspettative per operazione è **0,04**: il sistema completo
cattura **un ventiquattresimo** di quello che cattura il solo filtro di tendenza.
Confermata con un margine enorme — avevo previsto che il filtro di tendenza da solo
valesse almeno l'80%, e ne vale il **1.140%**.

**È il risultato più utile del gruppo F.** La parte del sistema che tutti
considerano banale — *stai dentro se il prezzo è sopra la EMA200 e la EMA21 è sopra
la EMA50, altrimenti stai fuori* — fa tutto il lavoro. Ogni raffinamento aggiunto
sopra peggiora il risultato monotonicamente:

- togliere il **ritracciamento**: da 0,564% a 1,377% di aspettativa
- togliere anche il **volume**: fino a 13,321% col solo trend

Il meccanismo è visibile nei numeri: le regole di ingresso tattico e il "piano di
uscita professionale" (stop sotto il minimo, parziale a 1:2, trailing sulla EMA21,
uscita sotto la EMA50) fanno entrare **tardi** e uscire **presto** dentro una
tendenza che il filtro semplice avrebbe cavalcato intera. Lo stop viene colpito, si
rientra più in alto, e si ripete: 6,5 operazioni l'anno invece di 3,5, ciascuna con
un ventiquattresimo dell'aspettativa.

**Nessuna promozione.** Il DSR del migliore è 0,593 su N=71, e la variante
"solo tendenza" non era pre-registrata come candidato — è il termine di paragone
dell'ablazione. Sul suo merito resta il verdetto già dato al giro 39: il trend
following multi-asset su cripto ha DSR 0,904 e un intervallo di confidenza dello
Sharpe di ampiezza 1,34.

---

## Bilancio del gruppo F

| voce | esito | numero chiave |
|---|---|---|
| F1 rotazione top-1 | **falsificata** | 1 cella su 9, +0,30 su un benchmark che perde 3 punti contro l'S&P |
| F2 griglia posizioni × frequenza | confermata | massimo a top-5 annuale, 10,02% contro 11,16% statico |
| F3 sistema EMA giornaliero | confermata | batte il B&H su 1/10 asset; muore sul **lordo**, non sulle imposte |
| F4 sistema EMA intraday | **falsificata** | ma per finestre non confrontabili; 7,1 → 33,6 → 133,4 op/anno |
| F5 ablazione | confermata | il solo filtro di tendenza vale **24 volte** il sistema completo |

**Tentativi cumulati a registro: 969.** Holdout 2010-2026 **ancora sigillato**.

# Giro 63 — D6: quante valutazioni hanno la rotazione sbagliata

**Predizione** (verbatim): *almeno **due terzi** di quelle valutazioni hanno
rotazione vera superiore al **triplo** di quella misurata, la correzione media
vale **oltre 0,5 punti** di IRR, e **nessun verdetto si ribalta**.*
**Falsificata se**: la correzione media sta **sotto 0,2 punti**, oppure **almeno
un verdetto si ribalta**.

**Esito: FALSIFICATA** — un verdetto si ribalta. E tutte e tre le clausole
descrittive sono sbagliate, compresa quella su cui la voce era stata scritta.

## Le tre convenzioni

| | definizione | dove è usata |
|---|---|---|
| **(a) target** | \|W_tgt,t − W_tgt,t−1\| / 2 | `bench.wbacktest` |
| **(b) detenuti** | \|W_der,t − W_der,t−1\| / 2 | `round31.backtest`, `round32.backtest` |
| **(c) vera** | \|W_tgt,t − W_der,t\| / 2 | quello che si compra e si vende |

Solo (c) è la rotazione: la distanza fra dove sei e dove vuoi essere. La (a) va a
zero su pesi costanti — è il difetto trovato al giro 60. **La (b) conta come
scambio anche il drift**, che non è uno scambio: nessuno compra niente quando un
settore sale e il suo peso cresce da solo.

| portafoglio | (a) target | (b) detenuti | **(c) vera** |
|---|---:|---:|---:|
| cap-weight | 0,199× | 0,309× | **0,260×** |
| equal-weight mensile | **0,000×** | 0,280× | **0,205×** |
| equal-weight annuale | 0,239× | 0,251× | **0,071×** |
| inverse-variance annuale | 0,050× | 0,289× | **0,225×** |
| HRP annuale | 0,138× | 0,384× | **0,318×** |
| min-variance annuale | 0,232× | 0,435× | **0,379×** |
| max-diversification annuale | 0,257× | 0,590× | **0,496×** |
| low-vol 36m top-25 annuale | 0,126× | 0,325× | **0,269×** |
| momentum 12-2 top-25 annuale | 0,445× | 0,686× | **0,620×** |

## L'effetto sull'IRR

| portafoglio | convenzione usata | IRR usata | **IRR vera** | delta |
|---|---|---:|---:|---:|
| cap-weight | target | 9,66% | 9,54% | −0,12 |
| **equal-weight mensile** | target | **11,16%** | **9,81%** | **−1,35** |
| **equal-weight annuale** | target | 9,92% | **10,65%** | **+0,73** |
| inverse-variance annuale | detenuti | 9,43% | 9,55% | +0,11 |
| HRP annuale | detenuti | 9,27% | 9,33% | +0,07 |
| min-variance annuale | detenuti | 8,13% | 8,17% | +0,05 |
| max-diversification annuale | detenuti | 9,24% | 9,29% | +0,05 |
| low-vol 36m top-25 annuale | target | 9,82% | 9,47% | −0,34 |
| momentum 12-2 top-25 annuale | target | 10,27% | 10,18% | −0,09 |

## Il verdetto

| | previsto | misurato | |
|---|---:|---:|---|
| rotazione vera > 3× quella usata | ≥ 66,7% | **11,1%** (1/9) | sbagliata |
| correzione media | > 0,5 punti | **0,32 punti** | sbagliata (ma sopra 0,2: non falsifica) |
| verdetti ribaltati | 0 | **1** | **falsifica** |

| voce | candidato | benchmark | gap usato | **gap vero** | |
|---|---|---|---:|---:|---|
| A2 giro 31 | HRP annuale | equal-weight annuale | −0,66% | −1,32% | no |
| A3 giro 32 | min-variance | cap-weight | −1,54% | −1,37% | no |
| A3 giro 32 | max-diversification | cap-weight | −0,42% | −0,25% | no |
| A1/A5 | inverse-variance | equal-weight annuale | −0,49% | −1,11% | no |
| **giro 04** | **low-vol top-25 annuale** | **cap-weight** | **+0,16%** | **−0,07%** | **SÌ** |

Il ribaltamento è quello del **tilt low-vol**: da marginalmente positivo a
marginalmente negativo. **La correzione peggiora il candidato, non lo salva.**
La condizione di falsificazione era scritta senza distinguere il verso del
ribaltamento — è scattata, e la registro come scattata.

## Quello che avevo sbagliato di più

La voce D6 era nata su una tesi precisa: *"l'errore è sistematico e ha **un verso
solo**: favorisce i benchmark statici contro le strategie che ruotano"*. Avevo
dichiarato prima di misurare che se (a) sottostima e (b) sovrastima quella tesi
cade. È esattamente quello che è successo:

| | |
|---|---:|
| valutazioni che **sottostimano** la rotazione | 4/9 |
| valutazioni che la **sovrastimano** | 5/9 |

**L'errore ha due versi, non uno.** I giri 31 e 32 non favorivano affatto i loro
metodi: li **penalizzavano**, addebitando come costo di transazione il puro
drift dei pesi. Correggendo, HRP guadagna +0,07 e min-variance +0,05 — e restano
comunque sotto i rispettivi benchmark, perché anche i benchmark si correggono.

Il caso più istruttivo è l'**equal-weight annuale**: la convenzione (a) gli
attribuiva **0,239×** di rotazione, la (b) 0,251×, ma la rotazione vera è
**0,071×** — un terzo. Perché un portafoglio ribilanciato una volta l'anno
compra e vende **solo a gennaio**; negli altri undici mesi non tocca niente,
mentre entrambe le convenzioni sbagliate registrano movimento ogni mese.

Nel costruire questo giro ci sono cascato di nuovo io: la prima stesura
dell'"equal-weight annuale" teneva i pesi target fermi a 1/N, che è
ribilanciamento mensile travestito, e produceva una riga **identica** a quella
mensile (11,16% contro 11,16%). È il terzo giro di fila in cui lo stesso errore
si ripresenta in una forma nuova — l'ho scritto nel codice come commento perché
non ricapiti una quarta volta.

## Cosa resta in piedi

**Nessuna delle conclusioni sostanziali del progetto cambia.** I quattro gap
principali restano tutti negativi, e due su quattro peggiorano dopo la
correzione. L'unico ribaltamento riguarda un candidato il cui margine era +0,16
punti — cioè dentro il rumore misurato al giro 59 (dispersione 5-10 punti su
finestre decennali).

Ma il numero da tenere è quello dell'equal-weight mensile: **1,35 punti**. È il
benchmark più usato nel progetto e per trentatré giri ha ribilanciato ogni mese
senza pagare nulla. Le voci che lo usavano come metro vanno lette sapendolo, e
la griglia di F2 è già in coda come **D7**.

Nessuna promozione. Nessuna selezione: N resta la famiglia pre-dichiarata.

**Tentativi cumulati a registro: 1.175.** Holdout 2010-2026 **ancora sigillato**.

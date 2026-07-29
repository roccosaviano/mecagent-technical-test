# Giro 76 — L4: lo skip contro il ritardo

**Predizione** (verbatim, committata prima di eseguire): *il 12-3 senza ritardo
**non riproduce** il +0,86 e resta **sotto lo zero**, entro **0,5 punti** dal 12-2
senza ritardo. Il profilo del margine in funzione di k è **piatto entro ±0,6
punti** su tutti e cinque i valori.*
**Falsificata se**: il 12-3 senza ritardo produce un margine **positivo** e
**entro 0,3 punti** dal +0,86 — **oppure** il profilo in k ha un'ampiezza sopra
**1,5 punti**.

**Esito: FALSIFICATA sul ramo (b). Lo skip è un grado di libertà mai contato, e
vale fino a 3,94 punti.**

## Due scelte dichiarate prima di eseguire

**Il motore è quello giornaliero del giro 73.** La voce non lo specifica, ma la
sua condizione di falsificazione confronta un numero col +0,86, che è nato lì.
Nel motore mensile lo stesso 12-2 top-5 vale **+0,56** (giro 72) invece di −0,87:
**1,43 punti di differenza fra i due motori**, cioè più dell'effetto da misurare.
Misurare il profilo con un motore e confrontarlo col numero dell'altro sarebbe
barare senza accorgersene. Ho anche **ricalcolato il 12-2 a venti giorni dentro
questo giro** invece di citarlo: riproduce **+0,86** esatto.

**«12-k» = finestra di 11 mesi, skip variabile**, cioè `rolling(11).shift(k)`.
Tengo la lunghezza fissa e muovo solo lo skip, perché la voce chiede «skip
crescente» e perché così k=2 riproduce esattamente il segnale del giro 73.

## Il profilo in k, 49 settori giornalieri, 1969-2009

Benchmark: equal-weight annuale, rotazione vera 0,071×, **IRR 10,09%**.

| momentum 12-k **top-5** mensile | k=1 | k=2 | k=3 | k=4 | k=6 |
|---|---:|---:|---:|---:|---:|
| IRR netta | 10,74% | 9,22% | **11,27%** | 9,70% | 7,34% |
| **margine vs EW annuale** | +0,65 | **−0,87** | **+1,18** | −0,39 | **−2,75** |
| rotazione | 3,302× | 3,300× | 3,284× | 3,274× | 3,251× |

| momentum 12-k **top-10** mensile | k=1 | k=2 | k=3 | k=4 | k=6 |
|---|---:|---:|---:|---:|---:|
| IRR netta | 9,86% | 9,24% | 9,16% | 9,04% | 8,07% |
| **margine vs EW annuale** | −0,22 | −0,84 | −0,92 | −1,05 | −2,02 |
| rotazione | 2,759× | 2,758× | 2,754× | 2,746× | 2,737× |

**Ampiezza: 3,94 punti sul top-5, 1,79 sul top-10.** Entrambe sopra la soglia di
1,50. Il ramo (b) scatta su tutte e due le strategie.

La rotazione è **piatta** su tutti gli skip e resta sopra 1,0×: nessuna cella
cambia regime fiscale, quindi le differenze non sono l'effetto-soglia del giro 66.

## Il confronto che decideva il ramo (a)

| | 12-2 a 0g | 12-2 a **20g** | 12-3 a 0g | scarto |
|---|---:|---:|---:|---:|
| top-5 | −0,87 | **+0,86** | **+1,18** | **0,33** |
| top-10 | −0,84 | −1,21 | −0,92 | **0,28** |

Il ramo (a) **non scatta**, ma va detto come non scatta: chiedeva un 12-3
positivo **e** entro 0,30 dal +0,86, e il top-5 fa +1,18, cioè **0,32** di
distanza. **Manca per due centesimi di punto.** Sul top-10 la distanza è 0,28 —
dentro la tolleranza — ma il margine è negativo, quindi l'AND non si chiude.

**Il meccanismo che la voce ipotizzava è reale**, e la clausola diagnostica che la
voce stessa aveva scritto («se il meccanismo è quello, devono coincidere entro 0,3
punti») è centrata a 0,33 e 0,28. Non è una scoperta: ritardare l'esecuzione di
venti giorni di borsa **è** far entrare in vigore un segnale calcolato un mese
prima. Le due misure descrivono lo stesso oggetto, ed è giusto che coincidano.

## Perché questo non promuove niente — e perché ne serve un altro giro

Il profilo del top-5 è **+0,65 / −0,87 / +1,18 / −0,39 / −2,75**. Cambia segno
tre volte su cinque valori adiacenti, con salti di due punti. **Non è la forma di
un meccanismo: è la forma del rumore.** Se lo skip contasse davvero, il margine
sarebbe monotono o almeno regolare in k. Non lo è — e questo dice, dal lato dello
skip, la stessa cosa che il giro 59 diceva dal lato delle finestre e il giro 68
dal lato del calendario: **la dispersione di questi margini è dello stesso ordine
dei margini stessi**.

Segue la conseguenza scomoda, che è il vero risultato del giro:

> **Lo skip è un parametro libero mai dichiarato, e vale 3,94 punti** — lo stesso
> ordine del calendario di ribilanciamento (3,65 al giro 68). Il gruppo A del giro
> 05 lo aveva fissato a 1 e non l'aveva mai contato come grado di libertà.
> Moltiplicato per i dodici calendari, lo spazio di ricerca vero del momentum
> settoriale è **un ordine di grandezza più grande** di quello che il registro ha
> contato.

## E però: il 12-3 top-5 mensile passa tre cancelli su quattro

Va scritto, perché è la prima volta in settantasei giri.

| cancello | soglia | il 12-3 top-5 mensile |
|---|---|---|
| **G1** margine | ≥ +1,00, mediana sui dodici calendari | **+1,18** — ma misurato su **un solo calendario del benchmark** |
| **G2** DSR | > 0,95 | **0,9870** con la `var_sr` della regola |
| **G3** stabilità | ≥ 2/3 finestre decennali **e** mediana > 0 | **mai misurato** |
| **G4** calendario | ≥ 10/12 | **passa per costruzione** (è mensile) |

Tre letture del DSR, come al giro 65, e prendo la più severa contro di me:

| `var_sr` stimata su | SR0/periodo | DSR |
|---|---:|---:|
| famiglia del giro, 10 celle (**la regola**) | 0,0669 | **0,9870** |
| N = 10, la sola griglia degli skip | 0,0315 | 0,9984 |
| registro intero | **1,7631** (>6 annualizzato: non credibile) | 0,0000 |

**Non apro l'holdout, e non promuovo.** Tre ragioni, tutte scritte prima del
giro 76:

1. **La regola del giro 72 dice che l'apertura è un atto separato**, non un
   sottoprodotto di un giro. Un cancello non misurato (G3) non è un cancello
   passato.
2. **Il +1,18 è il massimo di dieci celle**, e questo progetto ha documentato lo
   stesso artefatto tre volte: Kronos +13,11 su due simboli (giro 26), gennaio
   +1,51 su dodici calendari (giro 65), il ritardo +0,86 su dieci celle (giro 73).
3. **C'è un buco nella regola**, e l'ho trovato applicandola: G1 chiede la mediana
   sui dodici calendari, ma una strategia **mensile** non ha quel grado di
   libertà — ce l'ha il suo **benchmark annuale**, e sia il giro 72 sia questo
   giro hanno usato il solo gennaio. La mediana va presa sui dodici calendari
   **del benchmark**.

Quindi la voce nuova, pre-registrata in coda come **M1** e **non eseguita qui**:
misurare G1 sui dodici calendari del benchmark, misurare G3, e rifare il DSR con
una `var_sr` stimata su una famiglia che **contenga anche lo skip**. Se passa
tutti e quattro, l'holdout si apre su quello, una volta sola.

## Il verdetto

| clausola | top-5 | top-10 |
|---|---|---|
| il 12-3 resta sotto zero | **sbagliata** (+1,18) | centrata (−0,92) |
| entro 0,5 dal 12-2 senza ritardo | **sbagliata** (2,05) | centrata (0,08) |
| profilo piatto entro ±0,6 | **sbagliata** (2,32) | **sbagliata** (1,01) |
| ampiezza sotto 1,5 → **falsificazione (b)** | **SCATTA** (3,94) | **SCATTA** (1,79) |
| 12-3 positivo e entro 0,3 dal +0,86 → **(a)** | non scatta **per 0,02** | non scatta |

Il +0,86 del giro 73 **non era rumore da chiudere**: era lo skip. E lo skip, a sua
volta, è un parametro libero il cui profilo è rumore. Le due cose stanno insieme e
non si annullano.

Nessuna promozione. La griglia (5 skip × 2 taglie) era fissata in anticipo; la
cella migliore è dichiarata come massimo di dieci, non come risultato.

**Tentativi cumulati a registro: 1.378.** Holdout 2010-2026 **ancora sigillato**.

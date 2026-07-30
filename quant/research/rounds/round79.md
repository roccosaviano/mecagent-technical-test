# Giro 79 — O1: deflatare sul margine, non sullo Sharpe

**Predizione** (verbatim, committata al giro 78): *il cancello sul margine
**avrebbe respinto** il 12-3 top-5 mensile. E respinge anche **tutti** gli altri
candidati mai registrati, quindi non è un cancello costruito su misura per il caso
che ha fallito. Il rapporto fra la soglia sul margine e quella sullo Sharpe è
**superiore a 3**.*
**Falsificata se**: il cancello **lascia passare** il candidato — **oppure** se
respinge anche l'equal-weight contro il cap-weight, cioè se non discrimina più
niente.

**Esito: CONFERMATA, tutte e tre le clausole.**

## Cosa ho costruito

La versione **margine** della statistica di Bailey-López de Prado. Sotto l'ipotesi
nulla «nessuna strategia batte il benchmark» il margine atteso è zero, e il
massimo di *N* estrazioni vale

```
E[max] = σ · [ (1−γ)·Φ⁻¹(1 − 1/N) + γ·Φ⁻¹(1 − 1/(N·e)) ]      γ = 0,5772
```

con **σ = deviazione standard dei margini dentro la famiglia** da cui il massimo è
stato preso, invece della deviazione standard degli *Sharpe*. È la stessa
matematica di G2; cambia solo la statistica su cui si applica.

Tre letture dichiarate **prima** di eseguire, perché ognuna poteva cambiare il
verdetto: la centratura (H0 = 0, e in alternativa sulla media della famiglia); il
significato del «rapporto fra le due soglie», che ho definito senza unità come
`(soglia/osservato)_margine ÷ (soglia/osservato)_Sharpe`; e la *N* del controllo,
per cui applico **la N della selezione realmente avvenuta**.

## Le soglie

| famiglia | N | media | σ | ampiezza | soglia H0 | soglia su media |
|---|---:|---:|---:|---:|---:|---:|
| A — 12 candidati (giro 72) | 12 | −0,59 | 0,71 | 2,31 | **+1,18** | +0,59 |
| B — 20 celle (giro 77) | 20 | −0,86 | **1,15** | **4,27** | **+2,19** | +1,33 |

## Il candidato contro i due cancelli

| cancello | osservato | soglia | soglia/oss. | esito |
|---|---:|---:|---:|---|
| **G2 come scritto** (Sharpe) | 0,1755 | 0,0608 | 0,35 | **PASSA** |
| G2 sul margine, H0 = 0 | **+1,18** | **+2,19** | 1,86 | **RESPINTO** |
| G2 sul margine, centrata su media | +1,18 | +1,33 | 1,13 | **RESPINTO** |

**Rapporto fra le due esigenze: 5,36×** contro il «sopra 3» previsto.

Il verdetto non dipende dalla centratura: entrambe le letture respingono. E il
candidato che ha perso −0,95 sull'holdout sarebbe stato fermato **prima** di
arrivarci.

## Non è un cancello costruito sul caso che ha fallito

| famiglia | soglia | passano |
|---|---:|---|
| A — 12 candidati (giro 72) | +1,18 | **0 / 12** — il migliore è il 12-2 top-5 mensile a +0,56 |
| B — 20 celle (giro 77) | +2,19 | **0 / 20** — il migliore è il **12-1 top-3 a +1,51** |

**Zero su trentadue.** Notare la seconda riga: il massimo vero della famiglia B non
è il candidato (+1,18) ma il **12-1 top-3 a +1,51**, e viene respinto anche quello.
Il cancello non è tarato sul numero che sapevo dover respingere.

*(Curiosità aritmetica, non un risultato: la soglia della famiglia A viene
+1,18, cioè identica al margine del candidato — famiglie diverse, coincidenza.
Vale la pena dirlo perché a prima vista sembra un errore di copiatura.)*

## Il controllo: discrimina ancora?

Oggetto: **equal-weight annuale contro cap-weight, +1,50 punti** (giro 60). È
l'effetto strutturale più pulito del progetto, e **non è stato selezionato**: è un
confronto singolo, pre-specificato.

| lettura | N | soglia | esito |
|---|---:|---:|---|
| **N della selezione avvenuta** (dichiarata prima) | 1 | +0,00 | **PASSA** |
| sotto stress: stessa N e σ del momentum | 20 | +2,19 | RESPINTO |

Il cancello **discrimina**: lascia passare un effetto reale non selezionato e
ferma il massimo di una griglia. Sotto la lettura di stress respinge anche il
+1,50, e lo riporto perché chi non è d'accordo con la mia lettura deve avere il
numero — ma penalizzare una selezione che non c'è stata non è severità, è un
errore di applicazione: *N* nella formula **è** il numero di estrazioni da cui il
massimo è stato preso.

## Il risultato che non stavo cercando: G1 era tarato sulla cosa sbagliata

La soglia di **+1,00** di G1 fu fissata al giro 72 «perché è sopra il rumore
misurato al giro 63 sulla correzione della rotazione (0,32 medio, 1,35 massimo)».
Era il riferimento sbagliato. Il rumore rilevante non è l'errore di misura di una
singola valutazione: è **la dispersione di ciò che la ricerca genera**, e quella
dipende da quante celle si guardano.

| N celle guardate | soglia (σ = 1,15) |
|---:|---:|
| 12 | +1,91 |
| 20 | **+2,19** |
| 60 | +2,70 |
| 240 (5 skip × 12 calendari × 4 taglie) | **+3,25** |

Con la griglia completa che il progetto ha di fatto esplorato, la soglia onesta è
**+3,2 punti**, più del triplo di quella scritta al giro 72. **G1 e G2 stavano
provando a fare la stessa cosa e nessuno dei due la faceva**: G1 con una soglia
fissa che ignora quante celle guardi, G2 con la statistica giusta applicata alla
grandezza sbagliata. Il cancello sul margine li unifica in uno solo, e la soglia
diventa una funzione di *N* invece che una costante.

## Due limiti, entrambi da dire

**La formula assume estrazioni indipendenti, e le venti celle non lo sono.**
Condividono universo, finestra e segnale: il massimo atteso di venti celle
correlate è **più basso** di quello di venti indipendenti, quindi +2,19 è una
soglia **conservativa** — cioè taglia contro la mia conclusione, non a favore.

**Ma la N vera della ricerca è molto più grande di venti.** Lo skip (giro 76) e il
calendario (giro 68) sono stati scoperti come gradi di libertà *dopo* aver girato
per settanta giri senza contarli, e la tabella qui sopra dice che passare da 20 a
240 celle sposta la soglia di un punto intero. I due effetti spingono in direzioni
opposte e non li ho quantificati: quantificare la correlazione fra le celle è la
cosa che manca, e la aggiungo in coda come **O4**.

## Il verdetto

| clausola | previsto | misurato | |
|---|---|---|---|
| respinge il 12-3 top-5 | sì | +1,18 contro +2,19 | **centrata** |
| respinge anche tutti gli altri | sì | **0/32** | **centrata** |
| rapporto fra le soglie sopra 3 | sì | **5,36×** | **centrata** |
| discrimina ancora (controllo) | sì | passa il +1,50 non selezionato | **centrata** |

**Il fallimento dell'holdout è spiegato dalla selezione.** Non serve invocare un
cambio di regime: un candidato preso come massimo di una famiglia con 4,27 punti
di ampiezza aveva bisogno di **+2,19** per essere credibile e ne aveva **+1,18**.
Ha poi fatto **−0,95** fuori campione, che è dentro un σ dalla media della sua
stessa famiglia (−0,86).

**Tentativi cumulati a registro: 1.422.** Holdout 2010-2026: **bruciato al giro
78**, non si riapre.

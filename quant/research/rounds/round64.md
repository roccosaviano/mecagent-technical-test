# Giro 64 — D7: F2 contro un equal-weight che paga il ribilanciamento

**Predizione** (verbatim): *il top-5 annuale supera l'equal-weight annuale
correttamente addebitato di **0,5-2 punti**, ma il **DSR resta sotto 0,95**.*
**Falsificata se**: il top-5 annuale resta **sotto** l'equal-weight annuale,
**oppure** il DSR supera 0,95.

**Esito: FALSIFICATA su entrambi i rami** — e nella direzione opposta a quella
per cui avevo aperto la voce.

## I benchmark

| benchmark | rotaz. vera | CAGR | IRR 33% | IRR 52% | **IRR rif.** |
|---|---:|---:|---:|---:|---:|
| equal-weight mensile | 0,205× | 11,12% | 9,81% | 8,64% | **9,81%** |
| equal-weight annuale | 0,071× | 11,44% | 10,65% | 9,60% | **10,65%** |
| *equal-weight GRATUITO (quello di F2)* | *0,000×* | *11,15%* | *11,16%* | *10,40%* | *11,16%* |

## La griglia, IRR netta di riferimento

| posizioni | mensile | trimestrale | annuale |
|---:|---:|---:|---:|
| 1 | 5,33%\* | 6,56%\* | 4,84% |
| 3 | 8,66%\* | 7,90%\* | **7,74%\*** |
| 5 | 8,82%\* | 8,51%\* | **8,73%\*** |
| 10 | 8,79%\* | 8,74%\* | 8,91% |
| **25** | 8,31%\* | 8,44%\* | **9,65%** |

\* oltre il 100% di rotazione l'anno → valutata al **52%**

## Il meccanismo: la correzione ha spostato due celle di regime fiscale

| posizioni | mensile | trimestrale | annuale |
|---:|---:|---:|---:|
| 1 | 11,218× | 3,716× | 0,943× |
| 3 | 10,649× | 3,646× | **1,053×** |
| 5 | 10,187× | 3,512× | **1,022×** |
| 10 | 9,115× | 3,158× | 0,951× |
| 25 | 5,701× | 2,075× | 0,656× |

Al giro 50 il top-5 annuale aveva rotazione **0,83×** e pagava il **33%**. Con la
rotazione misurata correttamente ha **1,022×** e **scavalca la soglia del 100%**:
paga il **52%**. Lo stesso vale per il top-3 annuale (1,053×).

**È l'opposto di quello che avevo previsto.** Avevo aperto D7 perché la
correzione peggiorava il *benchmark* di 1,35 punti; ma peggiora anche il
*candidato*, e per il candidato il salto non è graduale — è un gradino, perché
attraversa il confine fra due aliquote.

## I confronti

| confronto | divario |
|---|---:|
| top-5 annuale vs EW annuale (rotazione vera) | **−1,92** |
| top-5 annuale vs EW mensile (rotazione vera) | −1,08 |
| top-5 annuale vs EW GRATUITO (come F2) | −2,43 |
| **massimo della griglia** (top-25 annuale) vs EW annuale | **−1,00** |

Per riferimento, F2 al giro 50 registrava **top-5 annuale 10,02% contro 11,16% =
−1,14**. Il divario non si è chiuso: si è **allargato** a −1,92.

## Il DSR

| | SR periodo | SR0 | **DSR** |
|---|---:|---:|---:|
| top-5 annuale, **N=15** (la griglia) | 0,1329 | 0,0556 | **0,9743** |
| top-5 annuale, **N=1.175** (registro cumulato) | 0,1329 | 0,1037 | **0,7691** |
| massimo della griglia, N=15 | 0,1355 | 0,0556 | 0,9769 |

## Il verdetto, e cosa non ne segue

| clausola | previsto | misurato | |
|---|---:|---:|---|
| divario vs EW annuale | +0,5 / +2 | **−1,92** | **falsifica** |
| DSR sotto 0,95 | sì | **0,9743** su N=15 | **falsifica** |

Entrambi i rami della condizione sono scattati. **D7 è falsificata**, e la
registro come tale.

**Ma la promozione non ne segue, e va detto con precisione.** La condizione di
falsificazione legava il ramo DSR a una conseguenza — *"nel qual caso c'è per la
prima volta un candidato da portare all'holdout"* — e quella conseguenza è
falsa, per due ragioni indipendenti:

1. **Il candidato perde contro il proprio benchmark di 1,92 punti.** Un DSR alto
   su una strategia che rende meno del suo metro non è un candidato: è la
   conferma che lo Sharpe non è la funzione obiettivo di un PAC, cosa già
   registrata al giro 32.
2. **La soglia del progetto è il DSR sul registro cumulato**, non sulla singola
   griglia — è scritto in STATE.md dal giro 01. Su N=1.175 il DSR è **0,7691**.

Il DSR a 0,9743 su N=15 misura una cosa vera e diversa: dentro *questa* griglia
il top-5 annuale non è il massimo di quindici estrazioni casuali. Ma la griglia
non è l'universo dei tentativi fatti in questo progetto — sono 1.175.

**Promozioni: zero. Holdout ancora sigillato.**

## Cosa cambia di F2, e cosa no

| | giro 50 | giro 64 |
|---|---|---|
| massimo della griglia | **top-5 annuale** | **top-25 annuale** |
| valore del massimo | 10,02% | 9,65% |
| benchmark | 11,16% (gratuito) | 10,65% (annuale vero) |
| divario | −1,14 | **−1,00** |
| **conclusione** | nessuna cella batte l'equal-weight | **identica** |

La conclusione di F2 **regge per intero**. Cambia dove sta il massimo — non più a
5 posizioni ma a 25 — e quindi la clausola descrittiva "la relazione col numero
di posizioni è a campana" del giro 50 era un artefatto della misura sbagliata:
con la rotazione vera è **monotona crescente** nelle posizioni a frequenza
annuale (4,84 → 7,74 → 8,73 → 8,91 → 9,65). Più si diversifica, meglio va, senza
massimo interno.

Il che è coerente con tutto il resto del progetto: **quello che sembrava un
optimum di concentrazione era il costo di rotazione non addebitato.**

**Tentativi cumulati a registro: 1.190.** Holdout 2010-2026 **ancora sigillato**.

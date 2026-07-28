# Giro 66 — D9: restare deliberatamente sotto la soglia del 100%

**Predizione** (verbatim): *la variante vincolata **batte** la libera in **almeno
due terzi** delle celle nella fascia, e il guadagno medio sta fra **1 e 3 punti**
di IRR. Ma **nessuna vincolata batte l'equal-weight annuale**.*
**Falsificata se**: la vincolata batte la libera in **meno di metà** delle celle,
**oppure** una vincolata **supera l'equal-weight annuale**.

**Esito: CONFERMATA** su entrambi i rami. Sbagliata solo la taglia del guadagno.

## Come ho vincolato

Le celle in fascia sono tutte annuali: ribilanciano una volta l'anno e quel
singolo scambio costa ~1,0×. Fermarlo del tutto significherebbe non ribilanciare
mai più, cioè distruggere la strategia invece di vincolarla. Ho quindi eseguito
il ribilanciamento **parziale**: ci si muove verso il target solo fino a
consumare il budget annuo,

```
w_nuovo = w_derivato + λ · (target − w_derivato)
```

con λ scelto perché la rotazione dell'anno arrivi esattamente a **0,95×** e non
oltre. È l'unica lettura che lascia la strategia viva, ed è dichiarata nel codice
prima dei numeri.

Griglia: quella del **giro 64** (`round50.rotate`), non il calendario di gennaio
del giro 65. Sceglierlo qui in base a quale dei due conviene sarebbe selezione
non contata — il calendario è la voce D10, non ancora eseguita.

## Le quattro celle in fascia

Su 15 celle, **4 hanno rotazione vera fra 0,7× e 1,4×**, e sono tutte annuali.

| cella | rot. libera | aliq. | IRR libera | rot. vinc. | aliq. | IRR vinc. | **guadagno** | CAGR lordo perso |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| top-1 annuale | 0,943× | 33% | 4,84% | 0,937× | 33% | 5,66% | **+0,82** | **−0,37** |
| **top-3 annuale** | **1,053×** | **52%** | 7,74% | 0,956× | **33%** | 8,53% | **+0,79** | 0,59 |
| **top-5 annuale** | **1,022×** | **52%** | 8,73% | 0,942× | **33%** | 9,75% | **+1,02** | 0,46 |
| top-10 annuale | 0,951× | 33% | 8,91% | 0,908× | 33% | 8,82% | **−0,09** | 0,11 |

## Il verdetto

| | previsto | misurato | |
|---|---:|---:|---|
| la vincolata batte la libera | ≥ 66,7% | **75,0%** (3/4) | centrata |
| guadagno medio | +1 / +3 punti | **+0,64** | **sbagliata** |
| vincolate sopra l'EW annuale | 0 | **0** | centrata |

Nessuna delle quattro si avvicina all'equal-weight annuale (10,65%): la migliore,
il top-5 vincolato, resta a **−0,90**.

## Il meccanismo è confermato con precisione chirurgica

Guardando quali celle guadagnano si vede che **il vantaggio viene solo dal
riattraversare la soglia**:

| cella | attraversa la soglia? | guadagno |
|---|---|---:|
| top-3 annuale | **sì, 52% → 33%** | +0,79 |
| top-5 annuale | **sì, 52% → 33%** | +1,02 |
| top-1 annuale | no, era già 33% | +0,82 |
| top-10 annuale | no, era già 33% | **−0,09** |

Per il **top-10**, che pagava già il 33%, vincolare la rotazione è puro costo:
**−0,09**. È il controllo che serviva — se il vincolo giovasse *di per sé*,
gioverebbe anche a chi non ha nulla da guadagnare in aliquota. Non lo fa.

Il **top-1** è l'eccezione, e per una ragione diversa: vincolando **guadagna
anche di lordo** (CAGR perso **−0,37**, cioè negativo). Un portafoglio a una sola
posizione che ogni gennaio salta interamente sul vincitore dell'anno prima sta
comprando il massimo della reversione; muoversi solo parzialmente lo attenua. È
coerente con F1 e F2, che avevano già stabilito che concentrare sul migliore è la
scelta peggiore dell'intera griglia.

**Rinunciare all'ultimo 10% di rotazione costa poco di lordo** — da 0,11 a 0,59
punti di CAGR — **e vale diciannove punti di aliquota**. Il meccanismo previsto
c'è tutto. Solo che la taglia è la metà di quella prevista: **+0,64 invece di
+1/+3**, perché nella fascia solo due celle su quattro avevano davvero l'aliquota
da risparmiare.

## Cosa resta

La soglia del 100% **è sfruttabile**, ma vale meno di un punto e non basta a
colmare i due punti che separano la migliore cella dall'equal-weight annuale.
Resta un risultato di ingegneria fiscale, non una strategia: se un giorno un
candidato arrivasse a mezzo punto dal benchmark con rotazione appena sopra 1,0×,
**questo è il modo di recuperare quel mezzo punto**.

Nessuna promozione. Nessuna selezione oltre alla fascia dichiarata: N resta la
famiglia pre-dichiarata della coda.

**Tentativi cumulati a registro: 1.227.** Holdout 2010-2026 **ancora sigillato**.

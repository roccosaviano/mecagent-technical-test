# Giri 34-36 — chiusura del gruppo A (A5, A7, A8, A9, A10)

Cinque voci, tutte **confermate**. Sotto, per ognuna, la predizione verbatim e il
numero che la decide.

---

## Giro 34 — A5: equal risk contribution fra i 4 stream meno correlati

**Predizione**: *correlazione media sotto 0,3 raggiungibile, ma l'IRR netta resta
sotto il buy&hold.* **Falsificata se**: IRR netta > buy&hold. → **CONFERMATA**

Libreria di 7 flussi, finestra comune 2002-04 → 2024-12 (273 mesi). La selezione
guarda **solo la correlazione**, mai il rendimento: è l'unico modo perché la voce
non diventi "scegli i quattro che hanno funzionato". Quartetto vincente:
**decennale · trend sull'indice · premio di volatilità BXM · gross profitability**,
correlazione media a coppie **0,024**.

| | CAGR | vol | Sharpe | max DD | turn | IRR netta |
|---|---:|---:|---:|---:|---:|---:|
| azionario puro (benchmark) | 9,86% | 15,5% | 0,69 | −50,3% | 0,00× | **9,88%** |
| 4 stream — ERC | 6,37% | 6,1% | 1,04 | −14,3% | 0,68× | 5,39% |
| 4 stream — equal | 6,58% | 5,5% | **1,19** | **−11,7%** | 0,35× | 5,64% |
| 4 stream — inverse-vol | 5,65% | 5,3% | 1,07 | −13,1% | 0,37× | 4,63% |

**Lo Sharpe più alto di tutta la ricerca — 1,19 contro 0,69 — e perde 4,24 punti di
IRR netta.** Il drawdown scende da −50% a −12%. La diversificazione funziona
esattamente come promette la teoria: riduce il rischio. E riduce il montante,
perché per ridurre il rischio bisogna spostare capitale fuori dall'unico asset con
un premio grande, e senza leva a buon mercato non c'è modo di riportarcelo.

Cripto **escluse dalla selezione**, dichiarato: entrerebbero di certo per
correlazione quasi nulla, ma taglierebbero la finestra comune a sei anni.

---

## Giro 35 — A7: la tesi vera di HRP, contro il min-variance

**Predizione**: *HRP risulta 3-10 volte più stabile del min-variance.*
**Falsificata se**: HRP non è più stabile del min-variance. → **CONFERMATA nel
verso, sbagliata nella misura**

| metodo | movimento medio dei pesi per ribilanciamento |
|---|---:|
| equal-weight | 0,017 |
| inverse-variance | 0,109 |
| **HRP** | **0,283** |
| minimum variance | 0,473 |
| max diversification | 0,523 |

HRP è più stabile del min-variance di un fattore **1,67**, non 3-10. La tesi di
López de Prado regge sul suo bersaglio dichiarato, ma il margine è molto più
sottile di quanto il paper lasci intendere — e HRP resta comunque **meno** stabile
dell'inverse-variance, che è il metodo diagonale banale (giro 31).

---

## Giro 35 — A8: monetizzare lo Sharpe con la leva

**Predizione**: *la leva 1,20× recupera parte del divario ma non lo chiude; il
risultato resta sotto il cap-weight di almeno 1 punto.* **Falsificata se**: IRR
netta ≥ cap-weight. → **CONFERMATA**

Volatilità min-var 13,2% contro 15,8% del cap-weight: la leva di pareggio è
esattamente **1,20×**. Finanziamento a risk-free + 3%.

| | CAGR | vol | Sharpe | max DD | IRR netta |
|---|---:|---:|---:|---:|---:|
| min-var 1,00× | 9,90% | 13,2% | **0,78** | −46,2% | 8,22% |
| min-var 1,20× | 10,13% | 15,9% | 0,69 | −54,9% | 8,64% |
| min-var 1,50× | 10,32% | 19,9% | 0,60 | −65,9% | 9,15% |
| cap-weighted | 10,98% | 15,8% | 0,74 | −50,3% | **10,88%** |

**La leva distrugge proprio la cosa che doveva monetizzare.** A 1,20× lo Sharpe
scende da 0,78 a 0,69 — sotto quello del benchmark — perché il costo di
finanziamento è una sottrazione certa dal numeratore. Si compra +0,42 punti di IRR
e si vendono 0,09 di Sharpe, restando −2,24 punti sotto il cap-weight.

**Nessuna leva sotto 3,00× chiude il divario.** E il margine: a 1,20× il rapporto
di equity al drawdown peggiore è 63%, sopra la soglia di chiusura forzata ESMA del
50%, quindi regge. A 1,50× scende al **2,3%**: la posizione viene chiusa dal broker
sui minimi, e il 9,15% in tabella è un numero che nella realtà non si incassa.

Il vantaggio di Sharpe del min-variance (0,04) è troppo piccolo per sopravvivere a
uno spread di finanziamento del 3%. Questo chiude formalmente la domanda aperta dal
giro 32.

---

## Giro 36 — A9: Kelly aggiunge qualcosa a una frazione fissa?

**Predizione**: *la frazione fissa batte Kelly in IRR netta in almeno 3 casi su 4.*
**Falsificata se**: Kelly batte la frazione fissa in almeno metà dei casi.
→ **CONFERMATA, 4 casi su 4**

Confronto diretto: esposizione **costante** pari alla media realizzata di ogni
configurazione Kelly, contro la configurazione Kelly stessa. Stesso sottostante,
stessa finestra, stessa esposizione media — cambia solo se la si fa variare.

La frazione fissa vince **in tutti e quattro i casi**. Detto altrimenti: la stima
di Kelly su 60 mesi **non aggiunge informazione**, aggiunge solo rotazione
tassabile. Muovere l'esposizione secondo μ stimato all'indietro è peggio che non
muoverla affatto, perché μ è pro-ciclico — basso proprio dopo i crolli, cioè quando
i rendimenti attesi sono alti.

---

## Giro 36 — A10: il prezzo dell'assicurazione sul drawdown

**Predizione**: *il rapporto costo/beneficio migliora monotonamente fino a circa il
30-35%, oltre il quale la soglia scatta troppo di rado. Esiste un minimo interno,
intorno al 30%.* **Falsificata se**: il rapporto è piatto o monotono.
→ **CONFERMATA sull'esistenza del minimo, sbagliata sulla sua posizione**

Punti di IRR ceduti per punto di drawdown evitato, soglie dal 5% al 50%:

| soglia | cap-weighted | equal-weight 49 |
|---:|---:|---:|
| 5% | 0,061 | 0,221 |
| 10% | 0,050 | 0,170 |
| 20% | 0,040 | **0,102** |
| 30% | 0,029 | 0,586 |
| **40%** | **0,014** | — |
| 50% | 0,018 | — |

Il minimo interno **esiste su entrambi i sottostanti**, quindi A10 è confermata. Ma
sta a **40%** sul cap-weighted e a **20%** sull'equal-weight, non al 30-35% che
avevo previsto, e i due livelli di costo differiscono di un ordine di grandezza
(0,014 contro 0,102). **La soglia efficiente dipende dal sottostante**, quindi non
è un parametro trasferibile: è una funzione della profondità tipica dei drawdown di
quello specifico portafoglio. Sul cap-weighted, che ha drawdown molto più profondi
(−71% contro −39%), conviene una soglia larga; sull'equal-weight una stretta.

Il numero da portarsi via: sul cap-weighted, **27 punti di drawdown in meno costano
1,65 punti di IRR** alla soglia del 5%, ma **14 punti costano 0,19** alla soglia del
40%. L'assicurazione contro i crolli catastrofici è quasi gratis; quella contro le
correzioni ordinarie è cara.

---

**Gruppo A chiuso: 10 voci su 10 confermate, nessuna promozione.**
Registro a **733 tentativi** (deduplicato dopo due riesecuzioni). Holdout
2010-2026 **sigillato**.

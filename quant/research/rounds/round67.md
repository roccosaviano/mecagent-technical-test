# Giro 67 — J1: statistical jump model sui regimi, long e long/short

**Predizione** (verbatim): *il segnale correla **oltre 0,7** con un filtro a media
mobile 10 mesi; la **long-only perde 1,5-4 punti**; la **long/short è peggiore
della long-only** in tutte e tre le varianti; la **rotazione sta sotto 1,0×/anno**
grazie a λ.*
**Falsificata se**: la long-only **batte il buy&hold**, **oppure** una long/short
batte la corrispondente long-only.

**Esito: CONFERMATA.** Nessuno dei due rami scatta. Tre clausole descrittive su
quattro centrate; quella sulla correlazione è sbagliata, e in modo istruttivo.

**L'holdout 2010-2026 non è stato toccato**: J1 valuta candidati, non è una voce
metodologica come le D, quindi il campione si ferma al **1926-2009**.

## Come l'ho implementato

Coordinate descent alla Bemporad-Nystrup-Kolm: assegnazione degli stati per
**programmazione dinamica** con penalità λ per ogni salto, aggiornamento dei
centroidi come media, iterato fino a stabilità. Nove feature causali dalla sola
serie del mercato USA — per h ∈ {5, 21, 63} giorni: media EWM, deviazione al
ribasso EWM, e il loro rapporto.

**Fuori campione uso la regola causale, non la DP.** La programmazione dinamica
guarda tutta la sequenza: applicarla al periodo di test sarebbe look-ahead puro e
mascherato. Fuori campione assegno
`s_t = argmin_k ( L[t,k] + λ·1{k ≠ s_{t−1}} )`, la versione online dello stesso
criterio — un filtro con isteresi.

Rifit ogni 5 anni sui 20 anni precedenti. Lato corto modellato come
`−(total return) + rf − 1%/anno`, che è la fascia **bassa** del costo di prestito:
un'ipotesi favorevole allo short.

## I risultati

Buy&hold: CAGR 9,61%, **IRR 9,72%**, drawdown −83,65%.

| λ | salti/anno | esposiz. | long/cash IRR | **vs B&H** | long/short IRR | long/short 0,5 | rotaz. | aliq. | corr MA10 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 3,72 | 59,2% | 4,96% | −4,77 | 1,13% | 3,21% | 3,74× | 52% | **0,610** |
| 5 | 3,41 | 57,2% | 4,82% | −4,90 | 0,93% | 2,94% | 3,43× | 52% | 0,606 |
| 10 | 2,72 | 58,1% | 4,94% | −4,78 | 1,24% | 3,16% | 2,74× | 52% | 0,601 |
| 25 | 0,86 | 57,5% | 5,34% | −4,38 | **−0,45%** | 2,79% | 0,88× | **33%** | 0,508 |
| 50 | 0,17 | 48,9% | 4,83% | −4,89 | **−2,37%** | 1,73% | 0,19× | 33% | 0,104 |
| 100 | 0,08 | 77,4% | 7,12% | −2,61 | 3,63% | 5,63% | 0,09× | 33% | 0,067 |
| **200** | **0,06** | **84,4%** | **8,10%** | **−1,63** | 6,01% | 7,15% | **0,08×** | 33% | **0,006** |

## Il verdetto

| clausola | esito |
|---|---|
| correlazione col MA10 > 0,7 | **sbagliata** — va da 0,610 a **0,006** |
| la long-only perde 1,5-4 punti | **centrata** — la migliore fa **−1,63** |
| la long/short sempre peggiore della long-only | **centrata** — **21 configurazioni su 21** |
| rotazione sotto 1,0×/anno | **centrata** — 0,08× alla migliore |

## Il risultato vero: la strategia migliora quanto meno la si ascolta

La correlazione col filtro di tendenza **crolla** al crescere di λ, e questo
falsifica la mia lettura ma dice qualcosa di più forte. Guardando la colonna
insieme all'esposizione:

| λ | corr MA10 | esposizione | vs B&H |
|---:|---:|---:|---:|
| 0 | 0,610 | 59,2% | −4,77 |
| 25 | 0,508 | 57,5% | −4,38 |
| 100 | 0,067 | 77,4% | −2,61 |
| **200** | **0,006** | **84,4%** | **−1,63** |

Ad alto λ il modello **non è più un filtro di tendenza**: è un modello che
cambia stato **una volta ogni diciassette anni** e sta investito l'84% del tempo.
E man mano che si avvicina al buy&hold, il divario si chiude — da −4,77 a −1,63.

**Il segnale ha valore marginale negativo a ogni λ.** L'unica cosa che migliora il
risultato è ridurre il numero di volte in cui gli si dà retta. Estrapolando: a
λ→∞ il modello è il buy&hold, esposizione 100%, divario zero. Non esiste un λ in
cui identificare il regime paghi.

## Sul lato corto, la risposta è netta

**La long/short perde in 21 configurazioni su 21**, e non di poco:

| λ | long/cash | long/short | costo del lato corto |
|---:|---:|---:|---:|
| 25 | 5,34% | **−0,45%** | **−5,79 punti** |
| 50 | 4,83% | **−2,37%** | **−7,20 punti** |
| 200 | 8,10% | 6,01% | −2,09 punti |

A λ=25 e λ=50 la strategia long/short **perde denaro in valore assoluto** su
ottant'anni. Il meccanismo è quello previsto e non ha niente di sottile: il premio
azionario è positivo, quindi il valore atteso del lato corto è negativo **prima**
del costo di finanziamento, e il modello sta fuori dal mercato il 42% del tempo —
cioè sta corto per quarant'anni su un mercato che sale.

La variante a leva 0,5 sul corto è sempre in mezzo alle altre due, esattamente
come deve essere se il lato corto è un puro sottrarre: **dimezzare lo short
dimezza il danno**. È la controprova più pulita che si potesse chiedere.

## Cosa vale la pena tenere

Una cosa il jump model la fa, ed è quella per cui la voce era stata scritta:
**λ controlla la rotazione, e la rotazione controlla l'aliquota.** Da λ=10 a λ=25
la rotazione passa da 2,74× a 0,88× e l'aliquota dal **52% al 33%** — la stessa
soglia misurata al giro 66. La penalità di salto è un modo *diretto* di comprare
persistenza, molto più controllabile di un parametro di lisciatura.

Solo che serve a niente, perché ciò che si compra con la persistenza è il diritto
di stare fermi — e stare fermi al 100% si chiama buy&hold e non costa nulla.

**Nessuna promozione.** Nessuna variante si avvicina al benchmark, quindi non c'è
DSR da calcolare.

**Tentativi cumulati a registro: 1.248.** Holdout 2010-2026 **ancora sigillato**.

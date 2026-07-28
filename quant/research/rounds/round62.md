# Giro 62 — D5: la quota di vittorie è un indicatore ingannevole?

**Predizione** (verbatim): *lo scarto mediana − media è positivo per almeno
l'80% dei candidati, e almeno un terzo dei candidati che vincono oltre metà
delle finestre ha media ≤ 0.*
**Falsificata se**: lo scarto è positivo per **meno del 60%** dei candidati,
oppure **nessun** candidato con quota sopra il 50% ha media negativa.

**Esito: FALSIFICATA.** Positivo solo per il **28,6%**, e il segno è **opposto**
a quello previsto.

## L'insieme misurato

21 candidati sui 49 settori, 1969-2026, tutti sulla stessa finestra e sullo
stesso universo: momentum a cinque concentrazioni e tre orizzonti, versioni
annuali, reversione, low-vol a tre concentrazioni e due finestre, high-vol,
punteggio misto, inverse-volatility, equal-weight mensile e annuale, filtro di
tendenza. Benchmark: cap-weight dello stesso universo (la scelta stabilita al
giro 60). 46 finestre decennali.

La rotazione è misurata sui **pesi derivati**, non su |W_t − W_{t−1}|: è il
difetto trovato al giro 60. Non sto eseguendo D6 — sto evitando di ripetere in
un giro nuovo un errore già noto.

## Il tabellone

| candidato | vince | media | mediana | **mediana−media** | min | max |
|---|---:|---:|---:|---:|---:|---:|
| momentum 12-2 top-5 annuale | 71,7% | **+2,14%** | +1,72% | −0,42% | −3,54% | +11,61% |
| momentum 12-2 top-10 annuale | 69,6% | +1,52% | +1,37% | −0,16% | −2,42% | +7,16% |
| low-vol 36m top-25 | 67,4% | +0,26% | +0,66% | +0,40% | −4,61% | +2,48% |
| **low-vol 36m top-10** | **60,9%** | **−0,59%** | +0,44% | **+1,03%** | −8,21% | +3,40% |
| inverse-volatility | 56,5% | +0,29% | +0,23% | −0,07% | −4,95% | +2,93% |
| momentum 12-2 top-3 | 45,7% | +1,80% | −0,20% | **−2,00%** | −4,27% | +14,63% |
| momentum 12-2 top-5 | 45,7% | +1,15% | −0,19% | −1,33% | −2,73% | +11,22% |
| equal-weight mensile | 45,7% | +0,30% | −0,11% | −0,41% | −4,93% | +3,42% |
| filtro di tendenza 10m | 45,7% | +0,22% | −0,19% | −0,40% | −5,00% | +3,31% |
| momentum 12-2 top-10 | 41,3% | +0,26% | −0,60% | −0,86% | −3,13% | +7,49% |
| low-vol 36m top-5 | 34,8% | −1,73% | −0,49% | +1,24% | −10,37% | +4,34% |
| momentum 12-2 top-1 | 30,4% | −0,95% | −2,57% | −1,63% | −12,79% | +13,66% |
| momentum 3-2 top-10 | 23,9% | −2,04% | −1,68% | +0,36% | −5,89% | +2,35% |
| reversione 1 mese top-10 | 6,5% | −5,91% | −6,33% | −0,42% | −10,70% | +0,42% |

*(mostrate 14 delle 21 righe; il file completo è `out/round62_d5.csv`)*

## Il verdetto

| | previsto | misurato | |
|---|---:|---:|---|
| scarto positivo | ≥ 80% | **28,6%** (6/21) | falsifica (soglia 60%) |
| di chi vince >50%, con media ≤ 0 | ≥ 33,3% | 20,0% (1/5) | sbagliata, ma non falsifica |

**Controllo sul benchmark.** Al giro 59 il confronto era contro l'equal-weight e
lo scarto di H5 era *positivo* (+0,38). Rifacendo tutto contro l'equal-weight:
scarto positivo per **42,1%** invece di 28,6%, 1 caso ingannevole su 4.
**D5 resta falsificata con entrambi i benchmark** — il segno non è un artefatto
della scelta del riferimento.

## Cosa ho sbagliato, e cosa vuol dire

Avevo previsto una **coda sinistra sistematica**: piccole vittorie frequenti,
grandi perdite rare. È il contrario. Nella maggioranza dei casi la media supera
la mediana, cioè domina la coda **destra**: molte finestre mediocri e poche
molto buone. I due estremi lo dicono chiaro:

- **momentum top-3**: vince solo il 45,7% delle finestre e ha media **+1,80%**,
  perché il massimo è **+14,63%**. Perde spesso di poco, vince raramente di
  molto — l'opposto di quello che avevo scritto.
- **low-vol top-10**: vince il 60,9% e rende **−0,59%**. È l'unico caso
  davvero ingannevole del tabellone, e non è un momentum.

**H5 al giro 59 era un caso isolato, non una regola.** La conseguenza operativa
è quella che avevo temuto, ma al contrario: **non serve rileggere le quote di
vittorie di F1, E6 e H1**. Il disaccordo fra "vince spesso" e "rende in media"
esiste in 1 candidato su 21, non in tutti.

## Il meccanismo previsto era sbagliato sul bersaglio, giusto sull'effetto

Avevo attribuito lo scarto alla tassazione sul realizzato. Le correlazioni sui
21 candidati:

| | |
|---|---:|
| corr(rotazione, **scarto** mediana−media) | **−0,265** |
| corr(rotazione, **media**) | **−0,600** |

La rotazione spiega poco della **forma** della distribuzione e molto del suo
**livello**. Il fisco non produce una coda sinistra: sposta l'intera
distribuzione verso il basso, in proporzione a quanto si ruota. È lo stesso
risultato di sempre in questo progetto, misurato qui su ventuno strategie in una
volta sola.

## Una cosa che va guardata, e che non guardo in questo giro

`momentum 12-2 top-5 annuale` è positivo contro **entrambi** i benchmark:

| | vs cap-weight | vs equal-weight |
|---|---:|---:|
| momentum 12-2 top-5 annuale | **+2,14%** | **+1,84%** |
| momentum 12-2 top-10 annuale | +1,52% | +1,23% |

Al giro 50 (F2) la stessa configurazione risultava **1,14 punti sotto**
l'equal-weight statico — ma quel benchmark era l'equal-weight *gratuito*, quello
che il giro 60 ha mostrato ribilanciare ogni mese senza costi né imposte. Con la
rotazione addebitata correttamente il confronto potrebbe girare.

Non lo eseguo qui: sarebbe scegliere un vincitore fra 21 dopo aver visto i
numeri, e non era pre-registrato. **Lo registro come voce D7.**

Nessuna promozione. Nessuna selezione dichiarata: N resta la famiglia
pre-dichiarata della coda.

*Nota sul registro*: 63 righe per il giro 62 su **21 configurazioni distinte** —
tre esecuzioni durante la costruzione del controllo sul benchmark. Tengo il
conteggio gonfiato, sbaglia in direzione conservativa.

**Tentativi cumulati a registro: 1.157.** Holdout 2010-2026 **ancora sigillato**.

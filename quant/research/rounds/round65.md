# Giro 65 — D8: i verdetti col margine dentro la correzione

**Predizione** (verbatim): *i verdetti col margine sotto 1,35 punti sono **fra 4
e 10**, e ne cambia segno **meno di un terzo**. Nessuno dei ribaltati supera
comunque il DSR, quindi il numero di promozioni resta zero.*
**Falsificata se**: cambia segno **più di metà**, **oppure** un candidato
ribaltato supera il DSR 0,95 sul registro cumulato.

**Esito: FALSIFICATA — cambia segno il 57,1%.**

## Il censimento

11 coppie (candidato, equal-weight) prese dai giri 04, 05, 11, 31, 34, 43 e 50 e
riproducibili sui 49 settori. Margine misurato **con la convenzione originale**
di quei giri, poi rimisurato con la rotazione vera su **entrambi i lati**.

| candidato | benchmark | giro | margine orig. | margine vero | censito | cambia segno |
|---|---|---|---:|---:|:---:|:---:|
| HRP annuale | EW annuale | 31 (A2) | −0,30% | −1,32% | sì | no |
| **inverse-variance annuale** | EW annuale | 31/34 | **+0,27%** | **−1,11%** | sì | **SÌ** |
| **H5 momentum top-10 mensile** | EW mensile | 05/43 | **−0,86%** | **+0,46%** | sì | **SÌ** |
| C1 punteggio misto top-10 | EW mensile | 11/43 | −2,67% | −1,33% | no | — |
| H4 low-vol 36m top-10 | EW mensile | 04/43 | −2,67% | −1,36% | no | — |
| low-vol 36m top-25 annuale | EW annuale | 04 | −0,11% | −1,18% | sì | no |
| momentum top-5 annuale | EW mensile | 50 (F2) | +1,08% | +2,35% | sì | no |
| **momentum top-10 annuale** | EW mensile | 50 (F2) | **−0,11%** | **+1,17%** | sì | **SÌ** |
| **momentum top-25 annuale** | EW mensile | 50 (F2) | **−0,89%** | **+0,37%** | sì | **SÌ** |
| momentum top-25 mensile | EW mensile | 50 (F2) | −1,86% | −0,54% | no | — |
| filtro di tendenza 10m | EW mensile | G1 | −5,33% | −3,62% | no | — |

**7 verdetti nel censimento** (la clausola "fra 4 e 10" era centrata), **4
cambiano segno = 57,1%**, sopra la soglia di falsificazione del 50%.

Avevo previsto che i due effetti si compensassero — *"correggere alza anche la
rotazione dei candidati, non solo quella del benchmark"*. Non si compensano:
nessuno dei sette salta di aliquota, quindi la correzione è tutta di livello, e il
benchmark si muove più dei candidati esattamente come temevo al giro 63. Avevo
misurato bene il meccanismo e sbagliato la conclusione.

## Le tre promozioni apparenti, e perché non lo sono

| candidato | vs EW mensile | vs EW annuale | DSR | promuovibile |
|---|---:|---:|---:|:---:|
| H5 momentum top-10 mensile | **+0,46%** | −0,38% | 0,9889 | **no** |
| momentum top-10 annuale | +1,17% | **+0,33%** | 0,9424 | **no** |
| momentum top-25 annuale | +0,37% | −0,47% | 0,9278 | **no** |

I tre diventano positivi **contro l'equal-weight mensile**, che è il *peggiore*
dei due benchmark (9,81% contro 10,65%). Contro l'equal-weight annuale — quello
implementabile, stabilito al giro 63 — due dei tre tornano negativi, e il terzo
resta sotto il DSR.

**Il DSR va dichiarato ambiguo, non risolto in mio favore.** La condizione parlava
di "DSR 0,95 sul registro cumulato" senza specificare come stimare `var_sr`:

| stima di var_sr | SR0 per periodo | DSR di H5 |
|---|---:|---:|
| registro intero (default di `lab`) | **1,7785** | 0,0000 |
| gli 11 candidati di questo giro | 0,0921 | **0,9889** |

Un SR0 di 1,78 **per periodo** — cioè oltre 6 annualizzato — non è credibile: nasce
dal mescolare nel registro famiglie con profili di rischio diversi. Riporto
entrambi e prendo il più severo per me, cioè 0,9889. **Il ramo DSR della
condizione è scattato.** La conseguenza che gli era attaccata — *"c'è per la prima
volta qualcosa da portare all'holdout"* — **non segue**, perché la regola di
promozione di STATE.md ha due condizioni e la prima non è soddisfatta.

**Promozioni: zero. Holdout ancora sigillato.**

Detto questo: **momentum top-10 annuale a +0,33 contro l'equal-weight annuale con
DSR 0,9424 è la cosa più vicina a un candidato che questo progetto abbia
prodotto in 65 giri.** Non lo promuovo — non era pre-registrato, il DSR è sotto
soglia, e il margine è dentro il rumore misurato al giro 59. Ma va scritto.

## Il risultato che conta più del verdetto

Il top-5 annuale al giro 64 valeva **8,73%**; qui vale **12,16%**. Stessa
strategia, stesso universo, stesso periodo. **Cambia solo il calendario del
ribilanciamento.**

| strategia | calendario | rotaz. | aliquota | IRR | vs EW annuale |
|---|---|---:|---:|---:|---:|
| momentum top-5 | **gennaio civile** | 0,962× | **33%** | **12,16%** | **+1,51** |
| momentum top-5 | ogni 12 mesi dall'inizio | 1,022× | **52%** | 8,73% | **−1,92** |
| momentum top-10 | gennaio civile | 0,901× | 33% | 10,98% | +0,33 |
| momentum top-10 | ogni 12 mesi dall'inizio | 0,951× | 33% | 8,91% | −1,74 |
| momentum top-25 | gennaio civile | 0,620× | 33% | 10,18% | −0,47 |
| momentum top-25 | ogni 12 mesi dall'inizio | 0,656× | 33% | 9,65% | −1,00 |

**Il top-5 annuale è +1,51 o −1,92 a seconda del mese in cui si ribilancia**: 3,43
punti di divario da un parametro che nessun giro ha mai dichiarato. Per il top-5
il salto attraversa anche la soglia fiscale (0,962× contro 1,022×), ma non è solo
quello — il top-10 e il top-25 restano al 33% e si spostano comunque di 2,07 e
0,53 punti.

Questa non è una discrepanza fra due giri da nascondere: **è un parametro libero
che il progetto ha usato per sessantacinque giri senza contarlo nel registro dei
tentativi.** Lo registro come voce **D10**.

Nessuna promozione. Nessuna selezione dichiarata: N resta la famiglia
pre-dichiarata della coda.

**Tentativi cumulati a registro: 1.223.** Holdout 2010-2026 **ancora sigillato**.

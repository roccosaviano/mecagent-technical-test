# Giro 32 — A3: minimum variance e maximum diversification

**Predizione scritta prima** (voce A3, verbatim): *minimum variance riduce il
drawdown di oltre 10 punti e perde 2-4 punti di CAGR; nessuno dei due batte l'IRR
netta del cap-weight.* **Falsificata se**: uno dei due supera il cap-weight netto
imposte.

**Esito: CONFERMATA sul test di falsificazione — ma le due clausole descrittive
della predizione sono entrambe SBAGLIATE.** Lo scrivo per esteso sotto, perché è
la parte informativa del giro.

## Cosa ho eseguito

Due portafogli long-only sui 49 settori Ken French, 1969-07 → 2026-05 (683 mesi):

- **minimum variance**: `min w'Σw`, `w ≥ 0`, `Σw = 1`
- **maximum diversification** (Choueifaty-Coignard 2008): `max (w'σ)/√(w'Σw)`,
  stessi vincoli — massimizza il rapporto fra volatilità media pesata e
  volatilità del portafoglio

Entrambi con SLSQP su covarianza stimata sui **soli 60 mesi precedenti**,
ribilanciamento annuale, costi 0,15% round-trip. **Nessun parametro selezionato**:
non c'è griglia, quindi N per il DSR resta la famiglia pre-dichiarata (53 voci,
52 + A7 aggiunta al giro 31).

## Risultati

| metodo | CAGR | vol | Sharpe | max DD | turn/anno | top-5 | N eff. | IRR netta 33% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| minimum variance | 9,90% | 13,2% | **0,78** | −46,2% | 0,37× | 84,3% | 7,5 | 8,22% |
| max diversification | 11,30% | 16,2% | 0,75 | −47,8% | 0,50× | 74,9% | 9,7 | 9,34% |
| equal-weight | 11,57% | 16,9% | 0,74 | −51,5% | 0,23× | 10,7% | 48,6 | 9,89% |
| min-var + shrinkage *(diagn.)* | 10,07% | 13,2% | 0,80 | −46,3% | 0,37× | 80,5% | 8,2 | 8,36% |
| **cap-weighted** | 10,98% | 15,8% | 0,74 | −50,3% | 0,00× | — | — | **10,88%** |

**Test di falsificazione (c)**: min-var **−2,65** punti, max-div **−1,53** punti
contro il cap-weight netto imposte. Nessuno dei due lo supera → **A3 confermata**.

## Dove la mia predizione ha sbagliato

Il test pass/fail regge, ma il meccanismo che avevo descritto no, in entrambe le
clausole e nella stessa direzione — **avevo sovrastimato quanto il min-variance
cambia le cose**:

| clausola | prevista | osservata |
|---|---|---|
| taglio del drawdown | > 10 punti | **+4,2 punti** (−46,2% contro −50,3%) |
| CAGR ceduto | 2-4 punti | **1,08 punti** (9,90% contro 10,98%) |

La volatilità scende da 15,8% a 13,2%, cioè di 2,6 punti, e il drawdown scende
proporzionalmente meno perché **i crolli azionari sono eventi di correlazione, non
di volatilità**: nel 2008 i settori difensivi che il min-variance sovrappesa sono
scesi insieme a tutto il resto. Un ottimizzatore che minimizza la varianza su 60
mesi di storia normale non ha nessuna informazione sul comportamento delle code, e
il drawdown è un fenomeno di coda. Se avessi tenuto conto di questo prima, avrei
scritto una clausola diversa.

## La concentrazione: "minimum variance su 49 settori" non è quello che sembra

| | top-5 | posizioni effettive (1/HHI) |
|---|---:|---:|
| minimum variance | **84,3%** | **7,5** su 49 |
| max diversification | 74,9% | 9,7 |
| equal-weight | 10,7% | 48,6 |

Il min-variance mette l'84% del portafoglio in cinque settori. Non è un portafoglio
diversificato a bassa varianza: è **una scommessa concentrata su 7-8 settori
difensivi**, con tutto il rischio idiosincratico e di regolamentazione che comporta
(utility, beni di consumo di base, farmaceutico). Il numero condizionale mediano
della covarianza campionaria è **18.569**: con 49 asset e 60 osservazioni la
matrice è tecnicamente invertibile e sostanzialmente rumore lungo le direzioni a
bassa varianza, che sono esattamente quelle su cui l'ottimizzatore si butta.

## La diagnostica che chiude una possibile scusa

Il min-variance con **shrinkage di Ledoit-Wolf** verso la diagonale rende 8,36%
contro 8,22%: **+0,14 punti**. Fuori specifica pre-dichiarata, e la dichiaro come
tale, ma serve a separare due spiegazioni diverse di una sconfitta:

- *"la covarianza campionaria è rumore"* → lo shrinkage avrebbe recuperato molto
- *"il metodo non paga"* → lo shrinkage non cambia niente

**È la seconda.** Il regolarizzatore non salva il min-variance, quindi la perdita
di 2,65 punti non è un artefatto di stima: è il metodo. (L'intensità di shrinkage
stimata è solo 0,11, e ha senso — i settori sono correlati 0,6-0,7 fra loro, quindi
la parte fuori diagonale della covarianza è segnale vero e grande rispetto al suo
errore di stima. Lo shrinkage non ha molto da togliere.)

## Il punto che conta, ed è il più duro del giro

**Il minimum variance fa esattamente quello che l'anomalia low-volatility promette,
e resta inutile.** Sharpe 0,78 contro 0,74 del cap-weight: il rischio migliora
davvero. E l'IRR netta è 2,65 punti sotto.

Il motivo è che **un PAC non può monetizzare uno Sharpe più alto senza leva**. Per
portare il min-variance alla stessa volatilità del cap-weight servirebbe una leva
di 15,8/13,2 = **1,20×**, e la leva su questo progetto è già stata testata al giro
07: −4,18 punti con il margine ESMA modellato, e il finanziamento a benchmark+3%
mangia il differenziale prima ancora del margin call. Con un tasso privo di rischio
medio del 4,45% sul periodo, prendere in prestito il 20% del portafoglio al 7,45%
per comprare un asset che rende il 9,90% lascia un margine che i costi di
ribilanciamento e il 33% di CGT chiudono per intero.

È lo stesso muro di sempre visto da un'altra angolazione: **lo Sharpe non è la
funzione obiettivo di chi versa €500 al mese**. La funzione obiettivo è il montante
netto, e per un investitore che non può prendere leva a buon mercato il montante
netto segue il rendimento composto, non il rendimento per unità di rischio.

Il max-diversification si comporta come una versione attenuata: meno concentrato
(9,7 posizioni effettive), CAGR quasi pari al cap-weight (11,30% contro 10,98%), ma
0,50 rotazioni l'anno lo portano comunque a −1,53 punti netti. Guadagna 0,32 punti
lordi e ne restituisce 1,85 fra costi e imposte.

## Aliquota e scenario 52%

Il turnover più alto è 0,50 volte l'anno, ben sotto la soglia del 100% che farebbe
scattare la riqualificazione a reddito da negoziazione. Lo scenario al 52% è
comunque calcolato: min-var **7,18%**, max-div **8,10%**.

## Misurato per A7, verdetto rimandato

Movimento medio dei pesi per ribilanciamento: **min-variance 0,473**,
**max-diversification 0,523**, contro HRP 0,283 e inverse-variance 0,109 del giro
31. Il numero c'è perché i pesi si calcolano qui, ma **il verdetto su A7 lo do nel
giro dedicato**: si esegue una voce per volta.

DSR del migliore (max-div) su 53 ipotesi pre-dichiarate: 1,000, **non promuovibile**
— il benchmark vince.

**Tentativi cumulati a registro: 706.** Holdout 2010-2026 **ancora sigillato**.

# Giro 55 — PAC su dati REALI: S&P 500 Momentum contro S&P 500

**Correzione del giro 54.** Lì avevo usato un proxy di Ken French perché i dati
dell'indice erano licenziati, e avevo concluso "+0,09 punti, sono lo stesso
investimento". Yahoo ha risposto: con **SPMO**, l'ETF di Invesco che replica
*esattamente* SP500MUP, il risultato è **+5,17 punti su dieci anni**. Il proxy era
sbagliato, e avevo anche sbagliato la direzione dell'errore: avevo scritto che
sarebbe stato *più aggressivo* dell'indice vero, ed era molto più diluito.

## Prima: lo screenshot confronta cose diverse

`.INX` è l'S&P 500 **price index**, senza dividendi. SP500MUT e SP500MUN sono
**total return**. Sui miei dati, stessi 5 anni, tutto total return:

| | screenshot | mio dato (total return) |
|---|---:|---:|
| BRK.B | +78,2% | 78,1% |
| S&P 500 | +69,8% (.INX, **senza dividendi**) | **81,4%** (SPY) |
| S&P 500 Momentum | +154,1% | 155,5% (SPMO) |

I 12 punti di differenza sull'S&P sono i dividendi di cinque anni. Il divario resta
enorme, ma è 155 contro 81, non 154 contro 70.

## Il PAC, €750/mese, dati reali, regime ETF UCITS

**5 anni** (2021-07 → 2026-07, €45.000 versati):

| | CAGR | vol | max DD | Sharpe | IRR netta | montante | imposte |
|---|---:|---:|---:|---:|---:|---:|---:|
| S&P 500 (SPY) | 12,65% | 15,9% | −23,9% | 0,83 | 12,04% | €60.324 | €9.422 |
| **S&P 500 Momentum (SPMO)** | 20,63% | 20,6% | −21,3% | **1,02** | **20,85%** | **€74.408** | €18.099 |
| MSCI USA Momentum (MTUM) | 13,09% | 20,6% | −30,2% | 0,70 | 15,66% | €65.788 | €12.825 |
| Berkshire (BRK.B) | 12,24% | 18,9% | −24,3% | 0,71 | 7,47% | €54.013 | €5.681 |

SPMO contro S&P: **+8,81 punti, +€14.084**.

**10 anni** (2016-07 → 2026-07, €90.000 versati):

| | CAGR | vol | max DD | Sharpe | IRR netta | montante |
|---|---:|---:|---:|---:|---:|---:|
| S&P 500 (SPY) | 14,93% | 15,3% | −23,9% | 0,99 | 11,37% | €161.100 |
| **S&P 500 Momentum (SPMO)** | 19,74% | 17,8% | −21,3% | **1,10** | **16,54%** | **€211.637** |
| MSCI USA Momentum (MTUM) | 15,92% | 18,0% | −30,2% | 0,91 | 12,12% | €167.522 |
| Berkshire (BRK.B) | 13,14% | 18,1% | −24,3% | 0,78 | 9,13% | €143.296 |

SPMO contro S&P: **+5,17 punti, +€50.537**. E con **drawdown minore** (−21,3%
contro −23,9%) e **Sharpe più alto** (1,10 contro 0,99).

## Le quattro ragioni per non prendere questo numero per buono

**1. Due ETF momentum, stesso decennio, risultati opposti.** SPMO +5,17 punti,
MTUM **+0,74**. Il divario fra i due "momentum" (4,4 punti) è **sei volte** il
divario fra MTUM e l'S&P. Se il momentum fosse un premio robusto, due indici che
lo cercano lo troverebbero entrambi. Qui la costruzione specifica conta più del
fattore, che è un altro modo di dire che il risultato **non è robusto alla
specifica**.

**2. Dieci anni, un ciclo solo.** SPMO esiste da novembre 2015. La finestra copre
un unico regime dominato dalle mega-cap tecnologiche, e un indice che pesa per
momentum × float cap ci finisce dentro per costruzione. Non è momentum che
funziona: è momentum che negli ultimi dieci anni **era** il megacap tech trade.

**3. Il vantaggio si concentra alla fine.** +8,81 punti sui 5 anni contro +5,17 sui
10: gran parte è arrivata di recente. Su tutte le 69 finestre quinquennali
disponibili il momentum vince nel 68%, media +2,41, ma **peggiore −3,12** (dal
2018-07) e **migliore +12,12** (dal 2021-06). E 69 finestre che si sovrappongono
per 59 mesi su 60 sono circa **due osservazioni indipendenti**.

**4. Il giro 54, con un secolo di dati, dice il contrario per le finestre
recenti.** Su 90 finestre decennali dal 1927 il momentum vince l'82% con +2,23
punti di media — ma le finestre che partono dopo il 2007 sono le peggiori della
serie, otto su dieci negative. I due risultati non sono contraddittori: il proxy
diluito cattura il premio momentum accademico (decaduto), SPMO cattura una
concentrazione su mega-cap che nel decennio ha funzionato.

## Cosa resta

Il numero è reale e grande: **+€50.537 su €90.000 in dieci anni**. Non è un
artefatto di modello — è il prezzo di due ETF realmente quotati, dividendi
inclusi, con la fiscalità irlandese applicata.

Ed è anche, punto per punto, il profilo che questo progetto ha imparato a
diffidare in 55 giri: una finestra, uno strumento, guardato dopo aver visto il
risultato, con un gemello (MTUM) che non lo conferma.

**Le due cose sono vere insieme.** Chi l'ha comprato nel 2016 ha 50.000 euro in
più; non ne segue che chi lo compra oggi li avrà.

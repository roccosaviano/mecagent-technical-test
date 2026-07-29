# Giro 77 — M1: il candidato passa tutti e quattro i cancelli

**Predizione** (verbatim, committata prima di eseguire): *(a) **tiene** — la
mediana resta **sopra +1,00** e si sposta di **meno di 0,3 punti** da +1,18.
(b) **fallisce**: la quota di finestre decennali positive resta **sotto i 2/3**.
(c) **scende ma regge**: il DSR resta **sopra 0,95**. Esito atteso: **tre cancelli
su quattro, l'holdout resta sigillato**.*
**Falsificata se**: il candidato **passa tutti e quattro** i cancelli — nel qual
caso l'holdout va aperto su quello solo, una volta sola — **oppure** se (a) cade.

**Esito: FALSIFICATA sul ramo 1. Il candidato passa 4 cancelli su 4.**

È la prima volta in settantasette giri. E la clausola che sbaglia è **proprio
quella su cui ero sicuro**.

## Il candidato

**Momentum 12-3 top-5 mensile** sui 49 settori, motore giornaliero del giro 73,
1969-2009. IRR netta **11,27%**, rotazione **3,284×/anno**, quindi aliquota
**52%** — paga il regime peggiore e vince lo stesso.

## (a) G1 — la mediana sui dodici calendari del benchmark

| | gen | feb | mar | apr | mag | giu | lug | ago | set | ott | nov | dic |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| benchmark | 10,09 | 10,23 | 10,23 | 10,16 | 10,11 | 10,23 | 10,08 | 10,06 | 10,08 | 10,09 | 10,04 | 10,10 |
| **margine** | +1,18 | +1,04 | +1,04 | +1,11 | +1,17 | +1,04 | +1,19 | +1,21 | +1,19 | +1,18 | **+1,23** | +1,17 |

**Mediana +1,18**, identica a gennaio. Positivo in **12 calendari su 12**, minimo
**+1,04**: sopra soglia ovunque, non solo in mediana. L'ampiezza del benchmark sui
dodici calendari è **0,19 punti**, coerente con lo 0,14% che il giro 68 aveva
misurato per un equal-weight.

**Clausola (a): centrata, con scarto 0,00.** Il buco della regola trovato al giro
76 era reale come buco, ma **non cambiava il verdetto**: il +1,18 di gennaio non
era il calendario.

## (b) G3 — la stabilità, che doveva essere il cancello che uccide

29 finestre decennali mobili, 1972-1981 … 2000-2009.

| | | | | | | | | |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1972 | 1973 | 1974 | 1975 | 1976 | 1977 | 1978 | 1979 | 1980 |
| +3,98 | +2,87 | +0,92 | +0,88 | +1,20 | +1,28 | +2,23 | +0,41 | +0,22 |
| 1981 | 1982 | 1983 | 1984 | 1985 | 1986 | 1987 | 1988 | 1989 |
| +1,66 | +1,39 | +2,57 | +3,30 | +2,05 | +2,24 | +1,53 | +0,74 | +1,34 |
| 1990 | 1991 | 1992 | 1993 | 1994 | 1995 | 1996 | 1997 | 1998 |
| +4,42 | +2,29 | +3,91 | **+6,53** | +3,72 | +3,14 | +4,20 | +3,11 | +3,51 |
| 1999 | 2000 | | | | | | | |
| **−1,23** | **−3,39** | | | | | | | |

**Quota positiva 93,1%** contro la soglia del 66,7%. **Mediana +2,23** contro 0.

**Clausola (b): SBAGLIATA, e non di poco.** Avevo previsto una quota *sotto* i due
terzi, sulla base del fatto che il candidato più vicino mai registrato (12-2 top-5
mensile, giro 72) si era fermato a 66,0%. Il 12-3 fa **93,1%**. Ventisette
finestre su ventinove.

## (c) G2 — il DSR con la famiglia allargata

| margine per skip | k=1 | k=2 | k=3 | k=4 | k=6 |
|---|---:|---:|---:|---:|---:|
| top-3 | **+1,51** | −1,50 | −0,06 | +0,33 | −2,28 |
| top-5 | +0,65 | −0,87 | **+1,18** | −0,39 | −2,76 |
| top-10 | −0,23 | −0,85 | −0,93 | −1,05 | −2,02 |
| top-25 | −1,22 | −1,19 | −1,70 | −1,88 | −1,92 |

| `var_sr` stimata su | SR0/periodo | DSR |
|---|---:|---:|
| **famiglia di 20 celle (questo giro)** | 0,0608 | **0,9907** |
| famiglia di 10 celle (giro 76) | 0,0669 | 0,9870 |
| registro intero (SR0 oltre 6 annualizzato: non credibile) | 1,7631 | 0,0000 |

**Clausola (c): centrata sul verso sbagliato.** Avevo previsto che il DSR
«scendesse ma reggesse»: **sale**, da 0,9870 a 0,9907. Allargare la famiglia da 10
a 20 celle **abbassa** `var_sr` invece di alzarla, perché le dodici celle nuove
(top-3 e top-25) hanno Sharpe più *concentrati*, non più dispersi.

## I quattro cancelli

| | cancello | soglia | misurato | |
|---|---|---|---|---|
| **G1** | margine | ≥ +1,00 mediana su 12 calendari | **+1,18** | **PASSA** |
| **G2** | Deflated Sharpe | > 0,95 | **0,9907** | **PASSA** |
| **G3** | stabilità | ≥ 66,7% finestre **e** mediana > 0 | **93,1%**, +2,23 | **PASSA** |
| **G4** | calendario | ≥ 10/12 | mensile, per costruzione | **PASSA** |

**La regola del giro 72 è passata.** Va detto senza attenuazioni: è stata scritta
quando non esisteva nessun candidato che potesse passarla, proprio per non poterla
adattare, e ora un candidato la passa.

## Quello che NON faccio, e perché

**Non apro l'holdout in questo giro.** Due ragioni, entrambe scritte prima:

1. La regola del giro 72 dice che l'apertura è un **atto separato**, non il
   sottoprodotto del giro che scopre il candidato.
2. Il protocollo del progetto lo vieta esplicitamente a ogni giro di ricerca.

L'ho pre-registrato come voce **N1**, con la predizione scritta **adesso**, prima
di guardare qualunque cosa del 2010-2026.

## Tre dubbi, messi a verbale PRIMA del risultato

Se il candidato fallirà sull'holdout, questi non diventano «l'avevo detto». Se
avrà successo, restano validi lo stesso. Per questo li scrivo ora.

**1. Il difetto di G2, scoperto applicandolo.** Nella famiglia di venti celle i
margini vanno da **−2,76 a +1,51**, cioè **4,27 punti di ampiezza** — e il
candidato **non è nemmeno il massimo**: il top-3 con k=1 fa **+1,51**. Ma la
`var_sr` del DSR è stimata sulla dispersione degli **Sharpe**, che è minuscola
(SR0 0,0608), mentre la selezione che ho fatto davvero è avvenuta sui **margini di
IRR netta**, che variano di 4,27 punti. **Il DSR sta proteggendo dalla selezione
sbagliata.** Fra Sharpe e IRR netta di un PAC ci sono in mezzo il motore fiscale,
la soglia del 100% e la forma dei cashflow, e il giro 70 aveva già misurato che
l'IRR e le altre metriche non si muovono insieme. Non riscrivo G2 adesso — sarebbe
esattamente il peccato che questo progetto ha passato settantasette giri a
evitare — ma lo registro come **difetto della regola**, valido indipendentemente
da come andrà l'holdout.

**2. Il candidato peggiora esattamente dove comincia l'holdout.** Le due sole
finestre negative su ventinove sono **le ultime due**: 1999-2008 a −1,23 e
2000-2009 a **−3,39**, dopo cinque finestre consecutive sopra +3. L'holdout
comincia nel **2010**. Il giro 59 aveva già trovato che le quattro peggiori
finestre di H5 contenevano tutte il 2008, e che allungando l'orizzonte tutti i
candidati peggiorano. Il profilo temporale di questo candidato dice la stessa
cosa, e la dice **puntando dritto verso il campione mai guardato**.

**3. Lo skip k=3 è stato scelto in-sample.** Al giro 76, come massimo di dieci
celle, sul campione intero 1969-2009. I cancelli esistono per questo, e li ha
passati — ma il fatto resta, e l'holdout è l'unica cosa che può dirimerlo.

## Il verdetto

| clausola | previsto | misurato | |
|---|---|---|---|
| (a) mediana sopra +1,00, entro 0,3 da +1,18 | sì | **+1,18**, scarto 0,00 | **centrata** |
| (b) G3 fallisce, quota sotto 66,7% | sì | **93,1%** | **SBAGLIATA** |
| (c) DSR scende ma resta sopra 0,95 | sì | **sale** a 0,9907 | centrata sul verso sbagliato |
| esito atteso: 3 cancelli su 4 | sì | **4 su 4** | **SBAGLIATA** |

Ero sicuro che G3 avrebbe ucciso il candidato, e G3 è il cancello che ha passato
con il margine più largo di tutti.

Nessuna promozione dichiarata: la promozione **è** l'apertura dell'holdout, ed è
la voce N1.

**Tentativi cumulati a registro: 1.390.** Holdout 2010-2026 **ancora sigillato**.

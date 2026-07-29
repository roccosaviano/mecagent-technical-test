# Giro 73 — L1: il costo di essere in ritardo, in giorni

**Predizione** (verbatim, committata prima di eseguire): *il margine **decade in
modo monotono** col ritardo, di **0,2-0,8 punti ogni 20 giorni**. A **un solo
giorno** la perdita sta **sotto 0,1 punti**. E **nessun ritardo rende il margine
positivo**.*
**Falsificata se**: il margine **non è monotono**, **oppure** un ritardo di 5
giorni o più **migliora** il margine.

**Esito: FALSIFICATA su entrambi i rami.**

## Come ho implementato il ritardo

Il segnale resta mensile (momentum 12-2 sui rendimenti fino al mese t−1). Cambia
solo **quando lo si esegue**: con ritardo k i pesi nuovi entrano in vigore al
k-esimo giorno di borsa **dopo** la fine del mese, e fino a quel giorno si resta
coi pesi vecchi, che nel frattempo derivano coi prezzi. Portafoglio valutato ogni
giorno su 10.223 giorni di borsa, rotazione vera calcolata sui pesi giornalieri,
rendimenti aggregati al mese per il motore fiscale.

**Lo stesso ritardo si applica al benchmark**: un investitore in ritardo lo è su
tutto. L'equal-weight annuale passa da 10,09% (0g) a 10,23% (20g) — il ritardo
per lui è irrilevante, come dev'essere per chi tocca il portafoglio una volta
l'anno.

## I risultati, 1969-2009

| momentum 12-2 **top-5** mensile | 0g | 1g | 5g | 10g | 20g |
|---|---:|---:|---:|---:|---:|
| IRR netta | 9,22% | 9,44% | 8,99% | 9,76% | **11,09%** |
| **margine vs EW annuale** | **−0,87** | −0,65 | −1,13 | −0,37 | **+0,86** |
| rotazione | 3,300× | 3,283× | 3,282× | 3,283× | 3,284× |

| momentum 12-2 **top-10** mensile | 0g | 1g | 5g | 10g | 20g |
|---|---:|---:|---:|---:|---:|
| IRR netta | 9,24% | 9,33% | 9,15% | 8,94% | 9,02% |
| **margine vs EW annuale** | **−0,84** | −0,76 | −0,97 | −1,19 | **−1,21** |
| rotazione | 2,758× | 2,752× | 2,754× | 2,753× | 2,754× |

La rotazione è **piatta** su tutti i ritardi e resta sopra 1,0×: nessuna cella
cambia regime fiscale, quindi le differenze non sono l'effetto-soglia del giro 66.

## Il verdetto

| clausola | top-5 | top-10 |
|---|---|---|
| monotono decrescente | **NO** | **NO** |
| decadimento 0,2-0,8 su 20 giorni | **sbagliata** (−1,72, cioè *migliora*) | centrata (+0,36) |
| perdita a 1 giorno sotto 0,1 | **sbagliata** (0,215) | centrata (0,081) |
| nessun ritardo lo rende positivo | **sbagliata** (+0,86 a 20g) | centrata |

**Il top-5 ritardato di venti giorni passa da −0,87 a +0,86**: uno scarto di
**1,73 punti** nella direzione opposta a quella prevista. È questo che falsifica
la voce.

## Cosa NON concludo da quel +0,86

Il +0,86 è **una cella su dieci** (cinque ritardi × due strategie) ed è il
massimo di quelle dieci. Il progetto ha passato quaranta giri a documentare
esattamente questo tipo di artefatto: al giro 68 il +1,51 di gennaio era il
massimo di dodici calendari, al giro 64 il DSR a 0,9743 era su N=15.

E comunque **non passa il cancello G1** della regola del giro 72, che chiede
**+1,00** come mediana, non come massimo. Con la stessa regola applicata ai
dieci ritardi, il +0,86 è sotto soglia e la mediana dei cinque ritardi del top-5
è **−0,65**.

Non lo registro come candidato. Lo registro come **domanda**, e la domanda è
precisa: ritardare l'esecuzione di venti giorni su un segnale 12-2 equivale, di
fatto, a **saltare un mese in più** — cioè a usare un momentum 12-3. Se
l'effetto è reale, deve vedersi **misurando direttamente il 12-3**, senza passare
dal ritardo. Se non si vede lì, era rumore. L'ho aggiunta in coda come **L4**.

## Quello che invece si può concludere

**Il risultato del progetto non dipende dal ribilanciamento a mezzanotte.** Il
costo di ordinare il giorno dopo è **0,08 punti** sul top-10 e **0,22** sul
top-5: entrambi dentro il rumore, ed entrambi molto sotto i divari con cui il
progetto ha respinto le strategie. La convenzione usata in settantatré giri non
sta nascondendo nulla.

**Ma il margine a un dato ritardo non è un numero preciso.** L'oscillazione fra
un ritardo e l'altro è di ±0,5 punti sul top-5 senza nessuna tendenza, il che
conferma dal lato dei giorni quello che il giro 59 aveva misurato dal lato delle
finestre: **la dispersione di questi margini è dello stesso ordine dei margini
stessi.**

**Sul confronto col giro 05**: quello misurava +2,93 → +2,35 con un mese di
ritardo, cioè −0,58. Qui il top-10 fa −0,36 su venti giorni — coerente in ordine
di grandezza. Il top-5 fa il contrario, e il giro 05 non aveva mai guardato il
top-5.

Nessuna promozione. Nessuna selezione dichiarata: la griglia dei ritardi era
fissata in anticipo.

**Tentativi cumulati a registro: 1.362.** Holdout 2010-2026 **ancora sigillato**.

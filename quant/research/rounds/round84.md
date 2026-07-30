# Giro 84 — O6: nessuna statistica in campione lo distingueva

**Predizione** (verbatim, committata al giro 81): *la **pendenza (1) segnala il
candidato**, ed è **l'unica** delle cinque a farlo con specificità — segnala il
12-3 top-5 e **non più di tre** degli altri dodici. Le statistiche (3) e (5) sono
troppo rumorose, e la (4) non segnala.*
**Falsificata se**: **nessuna** delle cinque segnala il candidato — **oppure** se
**più di tre** lo segnalano.

**Esito: CONFERMATA sul ramo che falsifica (una su cinque). E la predizione
principale è sbagliata in pieno: la pendenza non segnala niente.**

## Le soglie d'allarme, dichiarate nel codice prima di eseguire

La voce non le definiva, quindi le ho fissate su basi interpretabili: pendenza
implicita sull'arco degli anni sotto **−1,00**; differenza ultimo-meno-primo terzo
sotto **−1,00**; quota positiva sulle ultime dieci finestre sotto **2/3** (la
soglia di G3 applicata al solo tratto recente); t-stat dell'ultimo terzo **≤ 0**;
rapporto mesi positivi ultimi-cinque su primi-cinque sotto **0,90**. E, poiché
ogni soglia è contestabile, riporto anche il **rango** del candidato fra i tredici,
che non dipende da nessuna soglia.

## La tabella

| candidato | (1) pend | (2) terzi | (3) quota | (4) t-stat | (5) mesi | allarmi |
|---|---:|---:|---:|---:|---:|---:|
| **12-3 top-5 mensile (il candidato)** | **+0,40** | **−4,10** ✱ | 80% | +1,35 | 0,91 | **1** |
| momentum 12-2 top-5 annuale | −3,59 ✱ | −7,36 ✱ | 40% ✱ | +0,28 | 1,00 | 3 |
| momentum 12-2 top-10 annuale | −0,25 | −1,30 ✱ | 40% ✱ | +0,57 | 1,07 | 2 |
| momentum 12-2 top-25 annuale | +0,53 | −0,91 | 80% | +0,62 | 1,19 | 0 |
| momentum 6-2 top-10 annuale | +2,55 | +0,18 | 100% | +0,79 | 1,00 | 0 |
| low-vol 36m top-10 annuale | −4,45 ✱ | −0,41 | 0% ✱ | −1,58 ✱ | 0,82 ✱ | 4 |
| low-vol 36m top-25 annuale | −1,34 ✱ | −0,09 | 20% ✱ | −1,17 ✱ | 0,79 ✱ | 4 |
| punteggio misto top-10 annuale | −1,83 ✱ | −0,62 | 10% ✱ | −0,85 ✱ | 1,11 | 3 |
| momentum 12-2 top-5 mensile | +2,81 | −5,09 ✱ | 80% | +1,45 | 1,00 | 1 |
| H5 momentum top-10 mensile | +2,32 | −3,92 ✱ | 80% | +1,23 | 0,92 | 1 |
| momentum 12-2 top-25 mensile | +1,23 | −1,09 ✱ | 50% ✱ | +1,20 | 0,68 ✱ | 3 |
| H4 low-vol 36m top-10 mensile | −4,51 ✱ | −1,63 ✱ | 0% ✱ | −1,17 ✱ | 0,79 ✱ | **5** |
| C1 punteggio misto top-10 mensile | +0,56 | +0,59 | 30% ✱ | +0,29 | 0,88 ✱ | 2 |

## La pendenza non segnala, e il rango dice perché

| statistica | segnala il candidato | segnala altri | rango del candidato |
|---|---|---:|---:|
| (1) pendenza | **no** | 5 | **7 su 13** |
| (2) terzi | **SÌ** | 6 | 3 su 13 |
| (3) quota recente | no | 8 | 9 su 13 |
| (4) t-stat | no | 4 | **12 su 13** |
| (5) mesi positivi | no | 5 | 6 su 13 |

**La pendenza del candidato è +0,40** — cioè il profilo decennale *sale*, non
scende — e il candidato sta **a metà classifica**, settimo su tredici. Sul t-stat
dell'ultimo terzo è **dodicesimo su tredici**, cioè quasi il migliore del gruppo.

## L'errore che questo giro trova, ed è mio

Al giro 77, **prima** di conoscere l'esito dell'holdout, avevo messo a verbale:

> «Le uniche due finestre decennali negative su ventinove sono **le ultime due**
> (1999-2008 a −1,23, 2000-2009 a −3,39), dopo cinque consecutive sopra +3. Il
> degrado punta dritto verso l'holdout.»

Sembrava un'osservazione forte, e l'esito dell'holdout sembrava confermarla.
**Trasformata in una statistica, non discrimina.** Il profilo era +3,98 all'inizio,
saliva fino a **+6,53** nel 1993, e poi cadeva: è una **gobba**, non una discesa, e
una retta ci passa sopra con pendenza **positiva**.

Avevo letto un trend nella coda di una serie rumorosa. È lo **stesso errore che il
progetto ha documentato quattro volte** — Kronos +13,11 su due simboli, gennaio
+1,51 su dodici calendari, il ritardo +0,86 su dieci celle — solo **in immagine
speculare**: invece di prendere il massimo di N celle per un risultato, ho preso il
**minimo** di N celle per un presagio. E il fatto che l'holdout mi abbia poi dato
ragione **non rende l'osservazione corretta**: era giusta per caso.

Questo è il motivo per cui la voce O6 esisteva, ed è la ragione per cui vale la
pena scrivere i dubbi *prima* e poi **testarli** invece di incassarli.

## La risposta alla domanda della voce

**No.** Non c'era una statistica in campione che distinguesse il candidato. L'unica
che alza la mano è la (2), la differenza fra i terzi — e ne segnala **altri sei su
dodici**, quindi non distingue niente: segnala metà del campo.

La batteria non è inutile in assoluto: sui candidati **low-vol** funziona benissimo
(H4 fa cinque allarmi su cinque, i due low-vol annuali quattro), e quelli erano
davvero deteriorati. Ma sul candidato che poi ha fallito, **quattro indicatori su
cinque lo davano nella media o meglio**.

**Conseguenza per il progetto, e chiusura dell'autopsia**: si può giudicare un
candidato solo guardando **la griglia da cui viene**, non il candidato. Il cancello
sul margine del giro 79 — soglia +2,19 contro un osservato di +1,18 — resta
**l'unica difesa che avrebbe funzionato**, e adesso si sa che non è una fra tante:
è l'unica.

## Il verdetto

| clausola | previsto | misurato | |
|---|---|---|---|
| la pendenza segnala il candidato | sì | **+0,40**, rango 7/13 | **SBAGLIATA** |
| la pendenza è specifica (≤3 altri) | sì | 5 altri | **SBAGLIATA** |
| la (4) non segnala | sì | t-stat +1,35 | **centrata** |
| nessuna segnala → falsifica | — | 1 su 5 | non scatta |
| più di tre segnalano → falsifica | — | 1 su 5 | non scatta |

Nuova voce in coda: **O9**, perché guardando la tabella viene il sospetto che la
batteria non misuri il deterioramento ma **il margine stesso** — i candidati con
molti allarmi sono quelli che perdevano già.

**Tentativi cumulati a registro: 1.514.** Holdout **bruciato al giro 78**, non
interrogato in questo giro.

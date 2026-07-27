# Giro 59 — D3: dispersione su finestre di lunghezza fissa

**Predizione** (verbatim): *su finestre di 10 anni la dispersione
dell'extra-rendimento supera 4 punti e il segno cambia in almeno un terzo delle
finestre; su finestre di 20 anni la dispersione resta sopra 2 punti.*
**Falsificata se**: la dispersione su finestre di 10 anni resta **sotto 2 punti**.

**Esito: CONFERMATA.** Due clausole su tre centrate. E D1 aveva torto, esattamente
come sospettavo quando ho scritto D3.

## Prima di misurare: il difetto di D1, quantificato

Sovrapposizione media fra due campioni presi a caso dentro lo stesso disegno:

| disegno | sovrapposizione media | massima | campioni |
|---|---:|---:|---:|
| **D1** — 20 partenze, fine fissa 2026 | **85,5%** | 98,1% | 20 |
| D3 — finestre di 10 anni, passo 1 | **13,9%** | 81,8% | 46 |
| D3 — finestre di 20 anni, passo 1 | 34,1% | 90,5% | 36 |

Due campioni di D1 condividono in media **l'85,5% degli anni**. La loro differenza
è quasi zero per costruzione, qualunque cosa faccia la strategia. D1 non ha
misurato la stabilità del risultato: ha misurato la sovrapposizione del proprio
disegno sperimentale.

## Finestre di 10 anni — 46 finestre, 1972-1981 → 2017-2026

| candidato | media | min | max | **ampiezza** | dev.std | vince | mediana |
|---|---:|---:|---:|---:|---:|---:|---:|
| H5 momentum settoriale | +0,16% | −5,78% | +4,41% | **10,19%** | 2,04% | 31/46 = 67,4% | +0,54% |
| H4 tilt low-vol | −0,30% | −4,56% | +3,65% | **8,22%** | 2,21% | 20/46 = 43,5% | −0,61% |
| C1 punteggio misto | −0,96% | −3,80% | +2,01% | **5,81%** | 1,30% | 14/46 = 30,4% | −1,06% |

## Finestre di 20 anni — 36 finestre, 1972-1991 → 2007-2026

| candidato | media | min | max | **ampiezza** | dev.std | vince |
|---|---:|---:|---:|---:|---:|---:|
| H5 momentum settoriale | −0,28% | −1,78% | +2,38% | 4,16% | 1,01% | 14/36 = 38,9% |
| H4 tilt low-vol | −0,82% | −2,89% | +0,53% | 3,42% | 0,96% | 11/36 = 30,6% |
| C1 punteggio misto | −1,25% | −2,30% | −0,04% | 2,26% | 0,54% | **0/36 = 0,0%** |

## Il verdetto clausola per clausola

| clausola | soglia | misurato | |
|---|---:|---|---|
| ampiezza a 10 anni > 4 punti | 4,00 | da **5,81 a 10,19** | centrata |
| segno opposto in ≥ 1/3 delle finestre | 33,3% | da **30,4% a 43,5%** | **sbagliata** |
| ampiezza a 20 anni > 2 punti | 2,00 | da **2,26 a 4,16** | centrata |

La clausola sul segno fallisce di poco e su un solo candidato: C1 cambia segno nel
30,4% delle finestre invece del 33,3% richiesto. Gli altri due la superano.

**Il confronto per cui la voce esisteva:**

| | ampiezza massima |
|---|---:|
| D1, 20 partenze con fine fissa | 0,56 punti |
| D3, finestre di 10 anni | **10,19 punti — 18×** |
| D3, finestre di 20 anni | 4,16 punti — 7× |

Quello che D1 non aveva visto c'era, ed era **diciotto volte** più grande di quel
che aveva misurato. La stabilità apparente dei giri 04-05 era un artefatto del
disegno.

## Cosa dicono davvero i numeri, oltre alla predizione

**1. La dispersione è da 6 a 64 volte la media.** H5 ha extra-rendimento medio
+0,16% e ampiezza 10,19 punti: il rapporto è **64:1**. Non esiste un modo onesto
di chiamare "margine" una quantità la cui incertezza da scelta della finestra è
sessantaquattro volte il suo valore centrale. Vale per tutti e tre.

**2. H5 vince due finestre decennali su tre e perde comunque in media.** 31/46 =
67,4% di vittorie, mediana **+0,54%**, media **+0,16%**. La differenza fra mediana
e media è tutta in quattro finestre:

| finestra | extra |
|---|---:|
| 2000-2009 | **−5,78%** |
| 1999-2008 | **−5,69%** |
| 2001-2010 | −3,61% |
| 2002-2011 | −3,24% |

Sono le quattro finestre che contengono il **2008**. Il momentum settoriale vince
piano e con regolarità, poi restituisce tutto in un colpo. È la firma di una
strategia short-volatility, non di un premio.

**3. Allungare l'orizzonte peggiora tutti e tre.** Da 10 a 20 anni:

| candidato | vittorie 10a | vittorie 20a | media 10a | media 20a |
|---|---:|---:|---:|---:|
| H5 | 67,4% | **38,9%** | +0,16% | **−0,28%** |
| H4 | 43,5% | 30,6% | −0,30% | −0,82% |
| C1 | 30,4% | **0,0%** | −0,96% | −1,25% |

Non è quel che ci si aspetta da un premio vero, che con l'orizzonte dovrebbe
emergere dal rumore. Qui succede il contrario: **più lunga la finestra, peggio
vanno**. C1 su 20 anni perde in **36 finestre su 36**. La ragione è il costo
fiscale, che si accumula deterministicamente ogni anno mentre il vantaggio lordo
non si accumula affatto.

## Conseguenza sul registro

D1 resta falsificata — la sua conclusione era sbagliata, ma il verdetto registrato
lo era per la sua stessa specifica, ed è la cosa che D3 doveva accertare. Da ora
**la dispersione di riferimento per i tre candidati è quella di D3**: ±5-10 punti
su finestre decennali, non ±0,56.

Nessuna promozione: la voce misura la fragilità di candidati già respinti dal DSR,
non ne propone di nuovi. Nessuna selezione, quindi N resta la famiglia
pre-dichiarata della coda.

**Tentativi cumulati a registro: 1.041.** Holdout 2010-2026 **ancora sigillato**.

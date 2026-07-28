# Giro 68 — D10: dodici calendari per la stessa strategia

**Predizione** (verbatim): *l'ampiezza fra il mese migliore e il peggiore supera
**2 punti** di IRR per ogni strategia, la **mediana dei dodici è negativa** contro
il benchmark per tutte, e **meno di un terzo** delle 48 configurazioni batte il
proprio benchmark.*
**Falsificata se**: l'ampiezza resta **sotto 1 punto per la maggioranza** delle
strategie, **oppure** la mediana dei dodici è **positiva per almeno una**.

**Esito: CONFERMATA.** Nessuno dei due rami scatta. Sbagliata la clausola
sull'ampiezza, e il modo in cui è sbagliata è il risultato del giro.

## I dodici calendari, 1969-2026

| strategia | gen | feb | mar | apr | mag | giu | lug | ago | set | ott | nov | dic |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **equal-weight annuale** (IRR) | 10,65 | 10,59 | 10,66 | 10,68 | 10,62 | 10,58 | 10,63 | 10,57 | 10,61 | 10,58 | 10,62 | 10,54 |
| **momentum top-5** (IRR) | 12,51 | 11,57 | 11,86 | 10,60 | 9,03 | 9,42 | 8,88 | 9,75 | 9,55 | 9,30 | 10,97 | 12,53 |
| *vs EW stesso mese* | **+1,85** | +0,98 | +1,20 | −0,09 | −1,59 | −1,16 | **−1,75** | −0,83 | −1,05 | −1,29 | +0,34 | **+1,99** |
| **momentum top-10** (IRR) | 11,27 | 11,05 | 11,66 | 10,35 | 10,08 | 9,45 | 10,10 | 9,69 | 9,76 | 10,50 | 10,77 | 11,28 |
| *vs EW stesso mese* | +0,61 | +0,46 | +1,00 | −0,33 | −0,54 | −1,13 | −0,52 | −0,88 | −0,85 | −0,09 | +0,15 | +0,74 |
| **momentum top-25** (IRR) | 10,37 | 10,52 | 10,58 | 10,37 | 10,03 | 9,68 | 9,74 | 9,79 | 10,04 | 10,09 | 10,47 | 10,19 |
| *vs EW stesso mese* | −0,28 | −0,07 | −0,08 | −0,32 | −0,58 | −0,90 | −0,89 | −0,78 | −0,57 | −0,49 | −0,15 | −0,35 |

| strategia | ampiezza IRR | mediana IRR | **mediana extra** | vince | migliore | peggiore |
|---|---:|---:|---:|---:|---|---|
| equal-weight annuale | **0,14%** | 10,61% | +0,00% | 0/12 | — | — |
| momentum top-5 annuale | **3,65%** | 10,17% | **−0,46%** | 5/12 | dic | lug |
| momentum top-10 annuale | 2,21% | 10,42% | −0,21% | 5/12 | mar | giu |
| momentum top-25 annuale | 0,90% | 10,14% | −0,42% | 0/12 | feb | giu |

## Il verdetto

| | previsto | misurato | |
|---|---:|---:|---|
| ampiezza > 2 punti per ogni strategia | 4/4 | **2/4** | **sbagliata** |
| mediana degli extra negativa per tutte | sì | **0 positive** | centrata |
| meno di un terzo delle 48 vince | < 33,3% | **20,8%** (10/48) | centrata |

## Perché la clausola sbagliata è la cosa interessante

L'ampiezza non è uguale per tutte: **scala con la concentrazione**, in modo
monotono.

| strategia | posizioni | ampiezza |
|---|---:|---:|
| equal-weight annuale | 49 | **0,14%** |
| momentum top-25 | 25 | 0,90% |
| momentum top-10 | 10 | 2,21% |
| momentum top-5 | 5 | **3,65%** |

**Un portafoglio passivo non ha il problema**: l'equal-weight annuale rende lo
stesso in tutti e dodici i mesi, ampiezza 0,14 punti — cioè zero. Il grado di
libertà del calendario non esiste per chi non seleziona. **Esiste solo per chi
seleziona, ed è proporzionale a quanto concentra.** Cinque posizioni comprano
3,65 punti di arbitrarietà; quarantanove ne comprano 0,14.

Il che ha una lettura diretta: **quello che al giro 65 sembrava il vantaggio del
top-5 era in buona parte il suo grado di libertà**, non il suo segnale.

## Il conflitto fra i giri 64 e 65, risolto

| | |
|---|---:|
| top-5 annuale a **gennaio** (giro 65) | **+1,85** |
| top-5 annuale, **mediana dei dodici mesi** | **−0,46** |
| ampiezza fra il migliore (dic) e il peggiore (lug) | **3,74 punti** |

Gennaio è il **secondo mese migliore su dodici**. Il +1,51 registrato al giro 65
non era un risultato: era il **massimo di dodici estrazioni** — e nel registro
contava per uno.

**Il registro è cresciuto di 48 tentativi, non di 4**, esattamente come la
predizione diceva che dovesse. Da 1.248 a **1.296**.

## Il controllo senza l'holdout

L'ampiezza non è un fenomeno recente:

| strategia | 1969-2026 | 1969-2009 |
|---|---:|---:|
| equal-weight annuale | 0,14% | 0,21% |
| momentum top-5 | 3,65% | **3,31%** |
| momentum top-10 | 2,21% | 1,59% |
| momentum top-25 | 0,90% | 0,62% |

Stessa struttura, stessa monotonia nella concentrazione.

## Un filo che si riannoda

**Gennaio e dicembre sono i due mesi migliori per tutte e tre le varianti
momentum.** Non è casuale: è dove sta l'anomalia di fine anno che il giro 29
(H32, turn-of-month) aveva già misurato con **t = 7,04** — un effetto di
calendario statisticamente enorme che la strategia costruita apposta non riusciva
a monetizzare, perdendo 7,26 punti.

Qui ricompare dal lato opposto: non come strategia, ma come **il mese in cui
conviene ribilanciare**. L'effetto è reale e la sua taglia, misurata così, è di
circa **2,3 punti** di IRR fra dicembre e luglio per il top-5. Chi sceglie il mese
guardando i risultati lo sta incassando come se fosse alfa.

## Cosa resta

Nessuna promozione. Nessuna configurazione ha mediana positiva, quindi non c'è
niente da portare al DSR.

**La regola che ne esce, e che vale per tutto il resto del progetto**: ogni
backtest con ribilanciamento periodico ha **tante implementazioni quanti sono i
periodi**, e sceglierne una senza dichiararlo è selezione non contata. D'ora in
poi una strategia annuale va riportata con la **mediana dei dodici mesi**, non con
un mese solo — e le dodici vanno tutte a registro.

**Tentativi cumulati a registro: 1.296.** Holdout 2010-2026 **ancora sigillato**.

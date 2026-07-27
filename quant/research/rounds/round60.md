# Giro 60 — D4: il benchmark giusto cambia il verdetto?

**Predizione** (verbatim): *contro il cap-weighted i candidati sembrano positivi,
contro l'equal-weight dello stesso universo diventano negativi, e la differenza
fra i due benchmark (~2-3 punti) spiega **più della metà** del margine apparente.*
**Falsificata se**: la differenza fra i benchmark spiega **meno di un terzo** del
margine.

**Esito: CONFERMATA**, e il numero è molto più estremo del previsto: il premio di
equal-weighting non spiega metà del margine, ne spiega **quasi quattro volte**.

## I benchmark, stesso universo, netto costi e imposte

| benchmark | CAGR | vol | Sharpe | rotaz. | **IRR** |
|---|---:|---:|---:|---:|---:|
| cap-weight (49 settori, pesi CRSP) | 11,12% | 15,73% | 0,75 | 0,20× | **9,66%** |
| equal-weight mensile — *come al giro 43* | 11,15% | 17,20% | 0,70 | 0,00× | **11,16%** |
| equal-weight mensile — rotazione vera | 11,12% | 17,20% | 0,70 | 0,20× | **9,81%** |
| equal-weight annuale — rotazione vera | 11,45% | 17,05% | 0,72 | 0,06× | **10,65%** |
| *[controllo] mercato USA totale* | 10,98% | 15,83% | 0,74 | 0,00× | *10,88%* |

Il cap-weight è dello **stesso universo** (n_firms × avg_size, capitalizzazione
CRSP reale), non il mercato intero: usare il mercato cambierebbe insieme universo
e ponderazione e la decomposizione non direbbe niente.

## Il problema trovato costruendo i benchmark

Il benchmark del giro 43 è `ind.mean(axis=1)`, cioè pesi costanti a 1/N.
`wbacktest` calcola la rotazione come |W_t − W_{t−1}|, che su pesi **costanti fa
zero**: il ribilanciamento mensile risulta gratuito e non tassato. Ma tenere 1/N
ogni mese vuol dire vendere i vincitori e comprare i perdenti ogni mese, e quella
rotazione esiste — misurata contro i pesi **derivati** è **0,20×/anno**.

> **Il ribilanciamento che il giro 43 non addebitava vale 1,35 punti di IRR**
> (11,16% → 9,81%).

È lo stesso errore in cui sono cascato io alla prima stesura di questo giro:
avevo costruito l'"equal-weight annuale" tenendo fermi i pesi target a 1/N, che
non è ribilanciamento annuale — è ribilanciamento a ogni periodo. Produceva un
benchmark **identico** a quello mensile (11,16% contro 11,16%). Corretto con i
pesi che driftano e si azzerano ogni gennaio.

**Il miglior equal-weight veramente implementabile è quello annuale: 10,65%.**
Il mensile a 11,16% non esiste — è un indice, non un portafoglio.

## I candidati e la decomposizione

| candidato | CAGR | Sharpe | rotaz. | IRR | aliquota |
|---|---:|---:|---:|---:|---:|
| H5 momentum settoriale | 15,16% | 0,86 | 2,68× | **10,04%** | 52% |
| H4 tilt low-vol | 10,13% | 0,79 | 0,76× | 8,39% | 33% |
| C1 punteggio misto | 11,70% | 0,84 | 2,34× | 8,36% | 52% |

| candidato | vs cap-weight | vs EW mensile | vs EW annuale |
|---|---:|---:|---:|
| H5 momentum settoriale | **+0,38** | −1,12 | +0,12 |
| H4 tilt low-vol | −1,27 | −2,77 | −1,53 |
| C1 punteggio misto | −1,30 | −2,80 | −1,56 |

**Solo uno dei tre è positivo contro il cap-weight**, e di 0,38 punti. La clausola
"contro il cap-weighted i candidati sembrano positivi" era sbagliata per due terzi.

## Il verdetto, e la sua robustezza

Quota del margine di H5 (+0,38) spiegata dal premio di equal-weighting:

| variante di equal-weight | premio | quota spiegata | esito |
|---|---:|---:|---|
| mensile, come giro 43 (gratuito) | +1,50 | **398,3%** | conferma, clausola forte centrata |
| mensile, rotazione vera | +0,15 | **40,1%** | conferma, clausola forte sbagliata |
| annuale, rotazione vera | +0,99 | **262,8%** | conferma, clausola forte centrata |

**La soglia di falsificazione (un terzo) non è raggiunta in nessuna delle tre
varianti**, minimo 40,1%. Il verdetto non dipende da quale equal-weight si sceglie,
il che è il modo più forte in cui poteva risultare confermata.

| clausola | esito |
|---|---|
| il premio spiega più della metà del margine | **centrata** (398%, e 263% sulla variante implementabile) |
| i candidati sono positivi contro il cap-weight | **sbagliata** — 1 su 3 |
| i candidati sono negativi contro l'equal-weight | centrata — 3 su 3 |
| il premio vale 2-3 punti | **sbagliata** — vale 1,50 come indice, **0,99** come portafoglio |

## Cosa resta, e cosa cade

Il giro 05 registrava H5 a **+2,95** contro un PAC cap-weighted. Qui, contro il
cap-weight dello stesso universo e col motore fiscale corretto, H5 fa **+0,38**.
Contro il mercato USA totale (10,88%) fa **−0,84**: è negativo.

Il margine apparente di H5 era la somma di tre cose, e nessuna delle tre è
selezione di settori:

| componente | valore |
|---|---:|
| premio di equal-weighting (variante implementabile) | +0,99 |
| residuo attribuibile alla selezione | **−0,61** |
| **margine osservato contro il cap-weight** | **+0,38** |

**Il contributo della selezione è negativo.** Il momentum settoriale sceglie
peggio del pescare a caso dentro lo stesso universo: tutto il suo margine, e più
del suo margine, viene dal fatto di essere equalmente pesato invece che pesato per
capitalizzazione. Con 2,68 rotazioni l'anno e l'aliquota al 52%, quel che il
peso uguale dà, il fisco lo riprende.

**Nessuna promozione.** Nessuna selezione in questo giro: N resta la famiglia
pre-dichiarata della coda.

*Nota sul registro*: il giro 60 vi lascia 32 righe ma solo **9 configurazioni
distinte** — ho rieseguito lo script quattro volte mentre correggevo la costruzione
dei benchmark. Tengo il conteggio gonfiato invece di ripulirlo perché sbaglia nella
direzione conservativa: alza la soglia del Deflated Sharpe per tutti.

**Tentativi cumulati a registro: 1.073.** Holdout 2010-2026 **ancora sigillato**.

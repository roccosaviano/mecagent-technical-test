# Giro 69 — K1: il conto in valuta

**Predizione** (verbatim, committata prima di eseguire): *il **livello** dell'IRR
si sposta di **0,5-1,5 punti**, la volatilità in euro è **2-5 punti più alta**,
ma il **margine strategia-meno-benchmark si sposta di meno di 0,5 punti**, perché
il cambio è un fattore comune. Quasi, non del tutto: il residuo è proporzionale
alla rotazione.*
**Falsificata se**: un margine si sposta di **oltre 0,5 punti**, **oppure** la
volatilità in euro risulta **più bassa**.

**Esito: CONFERMATA.** Nessuno dei due rami scatta. Ma **due clausole su tre sono
sbagliate**, entrambe perché avevo sovrastimato la taglia dell'effetto.

## La serie del cambio, e i suoi controlli

DEXUSEU (dollari per euro) dal 1999; prima l'euro sintetico dal marco (EXGEUS,
1971+, a 1,95583 DEM/EUR).

**Controllo del verso**, fatto prima di qualunque risultato: con fx da 1,1417 a
1,1440 (euro che si rafforza) e rendimento USD 0%, il rendimento in euro esce
**−0,20%**. Corretto.

**Il raccordo ha un salto dell'1,93%**: EXGEUS è una *media* mensile, DEXUSEU
ricampionato è un *fine mese*. Riscalando il tratto sintetico perché combaci, le
IRR in euro si spostano di **−0,03/−0,04 punti**, uniformemente su tutte e quattro
le strategie — quindi i margini non ne risentono affatto.

## I risultati, 1971-2026 (665 mesi)

| strategia | valuta | CAGR | vol | rotaz. | aliq. | **IRR** |
|---|---|---:|---:|---:|---:|---:|
| buy&hold azionario USA | USD | 11,37% | 15,71% | 0,00× | 33% | **10,93%** |
| | EUR | 9,74% | 16,82% | 0,00× | 33% | **10,16%** |
| equal-weight annuale (gen) | USD | 11,96% | 16,85% | 0,07× | 33% | 10,71% |
| | EUR | 10,27% | 17,60% | 0,07× | 33% | 10,00% |
| momentum top-10 mensile | USD | 15,25% | 18,31% | 2,81× | 52% | 10,26% |
| | EUR | 13,89% | 19,02% | 2,82× | 52% | 9,79% |
| momentum top-5 annuale (gen) | USD | 15,26% | 20,86% | 0,79× | 33% | 12,67% |
| | EUR | 13,52% | 21,32% | 0,79× | 33% | 12,09% |

**Lo spostamento del livello:**

| strategia | IRR USD | IRR EUR | delta | vol USD | vol EUR | delta vol |
|---|---:|---:|---:|---:|---:|---:|
| buy&hold | 10,93% | 10,16% | **−0,77** | 15,71% | 16,82% | +1,10 |
| equal-weight annuale | 10,71% | 10,00% | −0,72 | 16,85% | 17,60% | +0,75 |
| momentum top-10 mensile | 10,26% | 9,79% | −0,46 | 18,31% | 19,02% | +0,70 |
| momentum top-5 annuale | 12,67% | 12,09% | −0,57 | 20,86% | 21,32% | +0,46 |

**Lo spostamento del margine** (contro l'equal-weight annuale):

| coppia | margine USD | margine EUR | **spostamento** | rotazione |
|---|---:|---:|---:|---:|
| buy&hold | +0,22% | +0,17% | **−0,06** | 0,00× |
| momentum top-5 annuale | +1,95% | +2,10% | **+0,14** | 0,79× |
| momentum top-10 mensile | −0,46% | −0,20% | **+0,25** | 2,81× |

## Il verdetto

| clausola | previsto | misurato | |
|---|---:|---:|---|
| spostamento del livello | 0,5-1,5 punti | **0,46-0,77** | **sbagliata** (per 4 centesimi) |
| volatilità EUR meno USD | +2 / +5 punti | **+0,46 / +1,10** | **sbagliata** |
| spostamento del margine | < 0,5 punti | **max 0,25** | **centrata** |

## Il meccanismo previsto è centrato in pieno

Avevo scritto che il residuo sarebbe stato **proporzionale alla rotazione**,
perché le imposte si pagano su plusvalenze in euro e chi realizza più spesso
cristallizza più spesso anche il cambio. Misurato:

| rotazione | spostamento del margine |
|---:|---:|
| 0,00× | −0,06 |
| 0,79× | +0,14 |
| 2,81× | +0,25 |

**corr(rotazione, |spostamento|) = +0,985.**

Va detto subito che **sono tre punti**: una correlazione di 0,985 su n=3 non è una
misura, è una coincidenza compatibile con il meccanismo. Quello che si può dire
onestamente è che l'ordinamento è quello previsto e la monotonia è netta — il
buy&hold, che non realizza mai, è l'unico col segno opposto.

## Cosa vuol dire in pratica

**Per un investitore in euro, l'azionario americano è reso circa 0,6-0,8 punti
l'anno in meno** di quanto tutti i sessantotto giri precedenti abbiano scritto —
perché l'euro (e prima il marco) si è rafforzato contro il dollaro su
cinquantacinque anni. Su un PAC trentennale da €750/mese quello **è denaro vero**,
e nessun giro prima di questo lo aveva contato.

**Ma nessun verdetto relativo cambia**, ed è la cosa che conta per questo
progetto: il cambio colpisce strategia e benchmark quasi allo stesso modo, e in
differenza resta al massimo **0,25 punti**. Le cinquantacinque conclusioni dei
giri 30-68 reggono tutte, in euro come in dollari.

Il cambio, inoltre, **non copre nulla**: la volatilità in euro è più alta di
0,46-1,10 punti in tutte e quattro le strategie. Meno di quanto avessi previsto,
ma il segno è quello — il rischio di cambio si somma al rischio azionario, non lo
compensa.

**Una nota di prudenza sul +1,95 del momentum top-5 annuale**: è calcolato sul
calendario di **gennaio**, che il giro 68 ha mostrato essere il **secondo mese
migliore su dodici**, con mediana dei dodici a **−0,46**. Quel numero non va letto
come un vantaggio, e non è per misurarlo che il giro esiste.

Nessuna promozione. Nessuna selezione: N resta la famiglia pre-dichiarata.

**Tentativi cumulati a registro: 1.312.** Holdout 2010-2026 **ancora sigillato**.

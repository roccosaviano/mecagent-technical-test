# Giri 48-49 — gruppo E: opzioni, comprare e vendere

Cinque voci più un cancello di calibrazione, tutte pre-registrate e **committate
prima** di eseguire (commit `3dff7b2`). Esito: **E1, E3, E4 confermate; E2 ed E5
falsificate**, con una lettura in entrambi i casi.

---

## Giro 48 — E0: il cancello di calibrazione

Il simulatore doveva riprodurre BXM e PUT del CBOE, che sono strategie realmente
quotate, entro 1,5 punti di CAGR e con correlazione mensile sopra 0,90.

| tentativo | BXM scarto | BXM corr | PUT scarto | PUT corr | esito |
|---|---:|---:|---:|---:|---|
| scadenze a fine mese, VIX grezzo | +7,04 | 0,850 | +5,65 | 0,862 | **chiuso** |
| scadenze al **terzo venerdì**, VIX grezzo | +4,76 | **0,974** | +3,65 | **0,978** | chiuso |
| terzo venerdì, **IV = 0,85 × VIX** | **+0,55** | 0,975 | **−0,72** | 0,978 | **APERTO** |

Due correzioni, entrambe istruttive:

**Le scadenze.** BXM e PUT scadono il terzo venerdì. Confrontarli con una
simulazione a fine mese sfalsa le finestre di payoff di una settimana, e la
correlazione crolla da 0,975 a 0,850. Sembra un dettaglio contabile e vale un
quarto della correlazione: era un mio errore, non un limite dei dati.

**Il livello.** Il VIX **non è** l'implicita at-the-money: è un tasso di variance
swap, pesa tutti gli strike, e lo skew dell'S&P lo spinge sopra l'ATM. Un solo
fattore di scala, scelto per minimizzare lo scarto massimo sui **due** indici
insieme, dà **IV = 0,85 × VIX** — cioè un'implicita ATM il 15% sotto il VIX.

**Un parametro tarato, dichiarato.** k = 0,85 è fittato, ma su due indici esterni
reali e non su nessuna delle strategie testate dopo. È lo stesso ruolo del cancello
Shiller all'inizio del progetto.

I residui hanno **segni opposti** — BXM +0,55, PUT −0,72 — che è esattamente quel
che ci si aspetta se un fattore piatto non può catturare lo skew: le call vanno
prezzate più a buon mercato delle put. Conferma la direzione degli errori
dichiarata in coda, e ne dà la misura: meno di un punto per parte.

## Giro 48 — E1: il premio al rischio di varianza → **CONFERMATA**

436 osservazioni mensili non sovrapposte, 1990-2026:

| | |
|---|---:|
| VIX medio | 19,45% |
| volatilità realizzata a 21 giorni | 15,54% |
| **scarto medio** | **+3,91 punti** |
| **quota di mesi con VIX > realizzata** | **83,0%** |
| peggior mese per un venditore | −54,98 punti (febbraio 2020) |

| decennio | VIX | realizzata | scarto | quota |
|---|---:|---:|---:|---:|
| 1990-99 | 18,55% | 12,32% | +6,23 | 93,3% |
| 2000-09 | 21,90% | 19,29% | +2,61 | 75,0% |
| 2010-19 | 17,09% | 13,63% | +3,45 | 81,7% |
| 2020-29 | 20,76% | 17,74% | +3,02 | 81,6% |

**Zero decenni con premio negativo.** Entrambe le clausole descrittive centrate
(quota >75%, scarto nella banda 3-4) — è l'unica volta in tutta la coda.

---

## Giro 49 — E2: comprare opzioni → **FALSIFICATA**, ma la condizione era mal posta

| | CAGR | vol | Sharpe | skew | IRR (52%) |
|---|---:|---:|---:|---:|---:|
| long call ATM | 6,30% | 9,2% | 0,71 | +1,46 | **+4,42%** |
| long call 5% OTM | 1,61% | 4,5% | 0,38 | +4,81 | +0,81% |
| long put 5% OTM | 2,51% | 6,9% | 0,39 | +8,27 | +1,42% |
| long put ATM | −3,19% | 10,9% | −0,25 | +3,99 | −4,15% |

Tre configurazioni su quattro hanno IRR positiva → **falsificata sulla lettera**.

**Ma ho testato la cosa sbagliata.** La condizione diceva "IRR netta negativa", e
io l'ho implementata come *liquidità al risk-free più l'opzione comprata*. Quello
non è una scommessa sul premio di varianza: per parità put-call, **cassa + call ≈
azione + put**, cioè una posizione azionaria protetta. Eredita il risk-free e il
premio azionario, e in un periodo in cui l'azionario ha reso l'11% all'anno la
componente direzionale vince su quella di volatilità.

Comprare una call è **soprattutto una scommessa direzionale con leva**, non un
acquisto di volatilità. Il test pulito del premio di varianza sarebbe uno straddle
delta-hedgiato, che non ho pre-registrato e non eseguo qui.

Le due clausole descrittive tengono: le put perdono più delle call (−4,06% contro
+1,04% nel caso peggiore), e nessuna delle quattro si avvicina al benchmark
(9,64%). Comprare opzioni **non** è un modo per battere il PAC — semplicemente non
è vero che perde soldi in assoluto.

## Giro 49 — E3: vendere put cash-secured → **CONFERMATA**

| | CAGR | vol | Sharpe | skew | max DD | realizzi/anno | IRR di rif. |
|---|---:|---:|---:|---:|---:|---:|---:|
| azionario buy&hold | 11,13% | 17,0% | 0,71 | −1,12 | −47,2% | 0 | **9,64%** |
| short put ATM | 8,04% | 10,9% | **0,77** | **−4,15** | −34,4% | 12 | 4,66% |
| short put 5% OTM | 2,79% | 7,0% | 0,44 | **−8,49** | −30,8% | 12 | 1,12% |
| short put 10% OTM | 2,01% | 4,8% | 0,44 | **−12,57** | −28,5% | 12 | 0,62% |

Lo Sharpe lordo supera il buy&hold (0,77 contro 0,71) **esattamente come previsto**,
e l'IRR netta è **4,98 punti sotto**. Il meccanismo è quello dichiarato: 12
realizzi l'anno contro un unico realizzo differito di 36 anni, e sopra il 100% di
rotazione l'aliquota è il 52%.

E la skew: **−4,15 ATM, −8,49 a 5% OTM, −12,57 a 10% OTM**. Più il premio sembra
sicuro, più la coda è mostruosa. Il febbraio 2020 da solo vale −55 punti di
volatilità sul venditore. Questa colonna è il motivo per cui "vendere put è come
incassare un affitto" è una descrizione sbagliata.

*Direzione dell'errore: conservativa* — con lo skew vero il premio incassato sarebbe
maggiore. Ma il divario da colmare è di 5 punti, e la taratura mostra che lo skew
vale meno di un punto.

## Giro 49 — E4: covered call → **CONFERMATA**, dopo aver buttato il simulatore

Alla prima esecuzione la covered call +5% simulata batteva il benchmark di **+0,98
punti** con DSR 0,997 — la prima promozione apparente in 49 giri.

Non lo era. Vendere call OTM è **l'unico caso in cui la volatilità piatta è
ottimistica**, ed era dichiarato in coda. Ho misurato lo scostamento contro i tre
indici CBOE reali:

| | reale | simulato | scarto |
|---|---:|---:|---:|
| BXM (ATM) | 6,26% | 6,81% | +0,55 |
| BXY (2% OTM) | 9,60% | 11,10% | **+1,51** |
| BXMD (~5% OTM) | 10,06% | 12,62% | **+2,56** |

**L'errore cresce con la moneyness**, come impone lo skew. Il +0,98 stava
interamente dentro un'inflazione di +2,56.

Rifatto con gli **indici reali**, senza nessun parametro tarato, e con il
trattamento fiscale **più generoso possibile** per la covered call (buy&hold, un
solo realizzo finale), 2003-2025:

| | CAGR | vol | Sharpe | skew | IRR netta | vs B&H |
|---|---:|---:|---:|---:|---:|---:|
| azionario buy&hold | 11,64% | 17,7% | 0,72 | −1,49 | **10,43%** | — |
| BXM covered call ATM | 6,62% | 10,4% | 0,67 | −1,37 | 5,23% | −5,20 |
| BXY covered call +2% | 8,95% | 12,1% | 0,78 | −1,00 | 7,19% | −3,24 |
| BXMD covered call ~5% | 9,35% | 12,3% | 0,79 | −0,92 | 7,51% | −2,92 |

Monotono come previsto, e **nessuna batte il buy&hold**. Confermata.

## Giro 49 — E5: LEAPS come leva → **FALSIFICATA**

Prima, un bug: la stesura iniziale valutava la posizione annuale **solo a
scadenza**, producendo 36 osservazioni date in pasto a un motore che assume 12
periodi l'anno. Uscivano CAGR del **264-434%**. Corretto con la marcatura al
mercato mensile (maturità residua corretta a ogni fine mese).

| | CAGR | vol | Sharpe | max DD | realizzi/anno | IRR netta |
|---|---:|---:|---:|---:|---:|---:|
| azionario buy&hold | 11,13% | 17,0% | 0,71 | −47,2% | 0 | 9,64% |
| LEAPS 90% leva 1,0× | 9,94% | 10,7% | **0,94** | **−36,6%** | 1 | 7,79% |
| LEAPS 80% leva 1,0× | 10,61% | 12,5% | 0,87 | −44,8% | 1 | 8,37% |
| LEAPS 80% leva 1,2× | 11,90% | 15,0% | 0,83 | −52,5% | 1 | 9,47% |
| **LEAPS 80% leva 1,5×** | **13,67%** | 18,7% | 0,78 | −62,5% | 1 | **10,98%** |

Il finanziamento incorporato, contando **sia** lo strike preso a prestito **sia** i
dividendi a cui si rinuncia: **2,95% annuo** a moneyness 80%, contro un risk-free
medio del 2,90% e il **5,90%** del CFD del giro 35. Il LEAPS finanzia a tre punti
meno del CFD, non ha margin call, e la perdita massima è il premio.

**Falsificata**: 10,98% contro 9,64%, **+1,34 punti**.

### Perché non è un candidato

1. **DSR 0,000** su N=66. Non passa il criterio di promozione del progetto.
2. **La direzione dell'errore è ottimistica, ed era dichiarata.** Le call deep ITM
   in realtà trattano sopra l'implicita ATM (via parità dallo skew delle put):
   il premio vero è più alto e il finanziamento incorporato più caro di 2,95%.
   Non ho un indice reale per misurare di quanto — a differenza di E4, dove BXY e
   BXMD mi hanno permesso di quantificare l'inflazione e buttare il simulatore.
3. **Il drawdown peggiora**: −62,5% contro −47,2%. Il +1,34 di IRR si compra con 15
   punti di drawdown in più, ed è la stessa leva del giro 35 con un'etichetta
   diversa.
4. **Una sola finestra**, 1990-2026, che è il periodo in cui la leva azionaria ha
   funzionato meglio nella storia.

La parte della predizione sbagliata è precisa: avevo scritto che *il drag fiscale
del rollo annuale supera il risparmio di finanziamento*. Non è vero — un realizzo
l'anno resta sotto la soglia del 100% e paga il 33%, e tre punti di finanziamento
risparmiati sono più del costo di anticipare la tassa. **Avevo sopravvalutato il
drag fiscale e sottovalutato quanto sia caro il finanziamento CFD.**

---

## Bilancio del gruppo E

| voce | esito | numero chiave |
|---|---|---|
| E0 cancello | **aperto** dopo due correzioni | terzo venerdì + IV = 0,85 × VIX |
| E1 premio di varianza | **confermata** | 83,0% dei mesi, +3,91 punti, 0 decenni negativi |
| E2 comprare opzioni | **falsificata** | ma la condizione misurava un portafoglio, non l'opzione |
| E3 vendere put | **confermata** | Sharpe 0,77 > 0,71 e IRR −4,98; skew fino a −12,57 |
| E4 covered call | **confermata** | col simulatore sembrava +0,98, con gli indici reali −2,92 |
| E5 LEAPS | **falsificata** | +1,34 punti, DSR 0,000, drawdown −62,5% |

**Nessuna promozione.** Il premio al rischio di varianza è il fenomeno più solido
misurato in tutto il progetto — 83% dei mesi, quattro decenni su quattro — e
**non è incassabile** da un PAC irlandese: raccoglierlo richiede 12 realizzi
l'anno, che è la definizione del vincolo che ha ucciso tutto il resto.

**Tentativi cumulati a registro: 912.** Holdout 2010-2026 **ancora sigillato**.

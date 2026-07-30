# Giro 85 — O7: il fattore non è una costante, ma non per la ragione che avevo dato

**Predizione** (verbatim, committata al giro 82): *il fattore **non è costante** e
**scala con l'eterogeneità** della famiglia. Il valore più basso è quello dei
**calendari** (famiglia 4), **sotto 0,15**; il più alto è quello dei **dodici
candidati** (famiglia 2), **sopra 0,45**. L'intervallo fra minimo e massimo è
**superiore a un fattore 3**.*
**Falsificata se**: tutti e quattro i fattori stanno **entro ±0,05** l'uno
dall'altro — **oppure** se i calendari risultano **più** indipendenti dei dodici
candidati.

**Esito: CONFERMATA sul ramo che falsifica. Due clausole descrittive su tre sono
sbagliate, e una lo è perché avevo classificato male una famiglia.**

## Un bug trovato eseguendo, e cosa ha rivelato

Il primo lancio è morto su `Eigenvalues did not converge`. Motivo: nella famiglia
4 la cella **«equal-weight annuale di gennaio» è il benchmark stesso**, quindi il
suo extra è **identicamente zero** e la matrice di correlazione degenera.

Non è solo un bug: **una delle 48 configurazioni del giro 68 era il benchmark**.
L'ho scartata e la famiglia 4 conta **47 celle**, non 48.

## I quattro fattori

| famiglia | N | corr. media | 1° autov. | `N_eff` | **`N_eff/N`** | Nyholt | ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1. skip × taglia (giro 77) | 20 | **0,761** | 15,50 | 6,00 | **0,300** | 8,79 | 0,439 |
| 2. dodici candidati (giro 72) | 12 | **0,412** | 5,83 | 6,00 | **0,500** | 9,04 | 0,753 |
| 3. posizioni × frequenza (giro 50) | 15 | 0,654 | 10,29 | 6,00 | **0,400** | 8,65 | 0,576 |
| 4. calendari × taglia (giro 68) | 47 | 0,466 | 25,73 | 16,00 | **0,340** | 32,47 | 0,691 |

**Controllo incrociato**: la famiglia 1 dà **0,300 nel motore mensile** e
**0,300** in quello giornaliero (giro 82). Scarto **zero**. Il fattore è una
proprietà della famiglia, non dello strumento — ed è la conferma che serviva per
poter confrontare le quattro righe.

## Dove sbaglio, e perché è istruttivo

**«I calendari sotto 0,15»: misurato 0,340.** L'errore non è di taglia, è di
**classificazione**. Avevo scritto che la famiglia 4 «varia solo il mese di
ribilanciamento» e che «dodici calendari dello stesso portafoglio sono quasi lo
stesso test». Ma la famiglia 4 non è dodici calendari di *un* portafoglio: è
**quattro strategie diverse × dodici calendari** — equal-weight, top-5, top-10,
top-25 — e la dimensione della strategia porta eterogeneità vera. La sua
correlazione media è **0,466**, cioè la **seconda più bassa** delle quattro.

Avevo classificato come la più omogenea quella che è la seconda più eterogenea.
Il numero era sbagliato perché era sbagliata la descrizione.

**«Rapporto sopra 3»: misurato 1,67×.** Conseguenza del punto precedente: senza un
estremo basso a 0,15, l'intervallo si stringe.

## La struttura che non avevo previsto

Guardando la colonna `N_eff` invece del rapporto:

> **6,00 / 6,00 / 6,00 / 16,00.** Tre famiglie di dimensione 12, 15 e 20 e di
> correlazione media 0,41 / 0,65 / 0,76 danno **lo stesso numero di test
> indipendenti**. Nyholt lo conferma: 9,04 / 8,65 / 8,79, cioè **entro il 4%**.

Il mio meccanismo — «il fattore scala con l'eterogeneità» — è quasi **assente**:
fra la famiglia più eterogenea e la più omogenea, `N_eff` si muove del 4% con
Nyholt e **di zero** con Li & Ji. Il rapporto varia (0,300 … 0,500) quasi solo
perché varia il **denominatore**.

Detto altrimenti: **allargare una griglia da 12 a 20 celle non aggiunge test
indipendenti.** Se ne aggiunge quando si passa a 47, ma sublinearmente (da 6 a
16). C'è un tetto a quante scommesse davvero diverse si costruiscono su 49
settori, e le griglie del progetto ci sbattevano contro senza saperlo.

**Nota sull'estimatore**: Li & Ji restituisce **valori interi** (6, 6, 6, 16) per
la ragione aritmetica vista al giro 82, quindi non risolve differenze sotto
l'unità. Le tre famiglie «tutte a 6,00» potrebbero essere 5,6 / 6,0 / 6,4. Nyholt,
che è continuo, dice 8,79 / 9,04 / 8,65 e conferma comunque la sostanza: sono lo
stesso numero.

## Cosa cambia per il cancello

Il fattore **non è una costante** — 0,300 a 0,500 è un fattore 1,67 — quindi va
ristimato per famiglia, che era la conclusione operativa della voce e regge.

Ma per il caso che conta, **l'incertezza non morde**: sulla famiglia del candidato
la soglia va da **+1,50** (col fattore misurato, 0,300) a circa **+1,9** (col
fattore più alto osservato, 0,500). Il candidato aveva **+1,18** ed è respinto
sotto tutta la banda. **La conclusione dei giri 79 e 82 è robusta all'incertezza
misurata qui.**

Da notare anche il verso: **un fattore più basso rende il cancello più
permissivo**, non più severo. Lo 0,300 usato finora è quindi la scelta **meno
prudente** fra quelle osservate, e regge lo stesso.

## Il verdetto

| clausola | previsto | misurato | |
|---|---|---|---|
| il fattore non è costante | sì | 0,300 … 0,500 | **centrata** |
| calendari sotto 0,15 | sì | **0,340** | **SBAGLIATA** |
| dodici candidati sopra 0,45 | sì | **0,500** | **centrata** |
| rapporto max/min sopra 3 | sì | **1,67×** | **SBAGLIATA** |
| ordinamento invertito → falsifica | no | 0,340 contro 0,500 | non scatta |
| tutti entro ±0,05 → falsifica | no | ampiezza 0,200 | non scatta |

Nuova voce in coda: **O10**, perché il «6,00 tre volte» è la cosa più interessante
di questo giro e non era nella domanda.

**Tentativi cumulati a registro: 1.518.** Holdout **bruciato al giro 78**, non
interrogato in questo giro.

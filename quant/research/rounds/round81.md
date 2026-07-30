# Giro 81 — O3: le finestre sovrapposte non erano il problema

**Predizione** (verbatim, committata al giro 78): *con finestre disgiunte la quota
del 12-3 top-5 **scende sotto i 2/3**, cioè **G3 sarebbe fallito in campione** se
fosse stato misurato su prove indipendenti; e l'intervallo di confidenza della
quota su finestre mobili è **almeno tre volte più largo** di quanto la numerosità
apparente (29) suggerisca.*
**Falsificata se**: la quota su finestre disgiunte resta **sopra i 2/3**.

**Esito: FALSIFICATA, su entrambe le clausole. E il rimedio che proponevo era
peggiore del difetto.**

## A1 — il candidato, con le due griglie di finestre

| schema | n | quota | soglia | esito |
|---|---:|---:|---:|---|
| finestre **mobili** | 29 | 93,1% | 66,7% | **PASSA** |
| finestre **disgiunte** | 4 | **75,0%** | 66,7% | **PASSA** |

| decennio | 1970-79 | 1980-89 | 1990-99 | 2000-09 |
|---|---:|---:|---:|---:|
| extra | **+4,81** | +0,22 | **+4,42** | **−3,39** |

Tre decenni su quattro positivi. **G3 passa anche su prove indipendenti**, e la
condizione di falsificazione scatta.

Il 1970-79 non compariva nel profilo del giro 78 (che partiva dal 1972) ed è il
decennio migliore dei quattro: **+4,81**.

## A2 — e sui dodici candidati del giro 72 le disgiunte sono MENO severe

| candidato | mobili | disgiunte | | |
|---|---:|---:|---|---|
| momentum 12-2 top-5 annuale | 65,5% | **75,0%** | no | **PASSA** |
| momentum 12-2 top-10 annuale | 62,1% | **75,0%** | no | **PASSA** |
| momentum 12-2 top-25 annuale | 69,0% | 50,0% | **PASSA** | no |
| momentum 6-2 top-10 annuale | 86,2% | 100,0% | **PASSA** | **PASSA** |
| low-vol 36m top-10 annuale | 48,3% | 25,0% | no | no |
| low-vol 36m top-25 annuale | 62,1% | 50,0% | no | no |
| punteggio misto top-10 annuale | 51,7% | **75,0%** | no | **PASSA** |
| momentum 12-2 top-5 mensile | 65,5% | 50,0% | no | no |
| H5 momentum top-10 mensile | 58,6% | 50,0% | no | no |
| momentum 12-2 top-25 mensile | 24,1% | 50,0% | no | no |
| H4 low-vol 36m top-10 mensile | 37,9% | 25,0% | no | no |
| C1 punteggio misto top-10 mensile | 17,2% | 25,0% | no | no |

**Passano 2/12 con le mobili e 4/12 con le disgiunte**, e **quattro verdetti su
dodici si ribaltano**. Le finestre disgiunte non stringono il cancello: lo
allargano.

## B — quanto costa davvero la sovrapposizione

| intervallo di confidenza al 95% | basso | alto | larghezza |
|---|---:|---:|---:|
| Wilson sulla numerosità apparente n=29 | 78,0% | 98,1% | **20,1%** |
| bootstrap a blocchi (400 ricampionamenti, blocchi da 120 mesi) | 71,0% | 100,0% | **29,0%** |

**Rapporto 1,45×**, contro il «almeno 3» previsto. **Sbagliata.**

La larghezza di un intervallo su una proporzione va all'incirca come 1/√n, quindi
un fattore 1,45 corrisponde a **n_eff ≈ 14** su 29 finestre nominali — non 4, e
non 29. Le finestre mobili portano **circa metà** dell'informazione che il loro
numero suggerisce. È uno sconto reale, e molto lontano dalla caricatura che avevo
scritto in coda: *«ventisette successi su ventinove sono lo stesso pezzo di storia
contato ventisette volte»* era falso.

## C — il rimedio che proponevo era peggiore del difetto

Una strategia che vince il 50% delle volte per puro caso, quante probabilità ha di
passare G3?

| schema | serve | falsi positivi sotto H0 |
|---|---|---:|
| 29 finestre mobili, trattate come indipendenti | 20/29 | **3,07%** |
| **4 finestre disgiunte** (le «prove vere») | 3/4 | **31,25%** |

**Dieci volte peggio.** Con quattro decenni e una soglia dei due terzi bisogna
vincerne tre, e il caso ne vince tre quasi un terzo delle volte. La correzione che
avevo pre-registrato come «la cosa giusta da fare» avrebbe reso G3 **un cancello
che non ferma niente**.

Questo spiega anche A2: le disgiunte fanno passare il doppio dei candidati non
perché siano più permissive per caso, ma perché **con n=4 la statistica non ha
potere**.

## Cosa concludo, e cosa non concludo

**Non concludo che G3 andasse bene.** Concludo che **il difetto non era quello che
avevo diagnosticato**, e che la diagnosi sbagliata portava a una cura dannosa.

Il vero limite è di **campione, non di schema**: quarant'anni contengono **quattro
decenni indipendenti**. Nessuna scelta di finestre può produrre più prove di
quante ce ne siano. Un cancello di stabilità basato su finestre decennali dentro
un campione quarantennale è sottodimensionato in partenza, e lo è sia contando le
finestre come 29 (che le sopravvaluta di un fattore 2) sia contandole come 4 (che
distrugge il potere del test).

**E il colpevole era già stato trovato, un giro prima.** Il giro 79 ha mostrato
che il candidato andava respinto da G1/G2 — soglia sul margine **+2,19** contro un
osservato di **+1,18** — cioè dalla **selezione**, non dalla stabilità. O3
assolve il secondo sospettato che avevo messo in fila. I due risultati stanno
insieme e si rinforzano: il fallimento dell'holdout è spiegato per intero dal
fatto che il candidato era il massimo di una griglia troppo grande per il suo
margine, e **G3 non c'entrava**.

## Un difetto diverso, che però resta

Quattro verdetti su dodici cambiano cambiando solo lo schema di finestre. Non è
sovrapposizione: è **un altro grado di libertà mai dichiarato**, della stessa
famiglia del calendario (giro 68) e dello skip (giro 76). Chi sceglie lo schema
delle finestre dopo aver visto i risultati ha un terzo parametro libero. La
differenza rispetto agli altri due è che qui il parametro non gonfia il margine —
gonfia il **verdetto di un cancello**.

## Il verdetto

| clausola | previsto | misurato | |
|---|---|---|---|
| quota disgiunta sotto i 2/3 | sì | **75,0%** (3/4) | **SBAGLIATA** — falsifica |
| intervallo almeno 3× più largo | sì | **1,45×** | **SBAGLIATA** |
| *(non previsto)* rimedio peggiore del difetto | — | falsi positivi 3,07% → **31,25%** | — |

Due clausole su due sbagliate, e la voce cade sulla prima. È la seconda volta in
tre giri che una mia diagnosi metodologica si rivela sbagliata dopo essere
sembrata ovvia — la prima fu G3 stesso al giro 77, che ero sicuro avrebbe ucciso
il candidato e fu il cancello che passò meglio.

Nuova voce in coda: **O6**, l'unica domanda che resta aperta — esiste *qualche*
statistica in campione che avrebbe segnalato il candidato?

**Tentativi cumulati a registro: 1.439.** Holdout **bruciato al giro 78**, non
interrogato in questo giro.

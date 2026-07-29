# Giro 72 — K4: la regola per aprire l'holdout

**Predizione** (verbatim, committata prima di eseguire): *nessuno dei candidati
mai registrati passa la regola, e la voce si chiude con l'holdout ancora
sigillato. La soglia che eliminerà **più candidati** non sarà il DSR ma la
**stabilità sul calendario**.*
**Falsificata se**: almeno un candidato già registrato passa tutte le soglie.

**Esito: CONFERMATA** sul test. **Sbagliata sulla seconda clausola**, e in un modo
che vale la pena guardare.

## La regola, fissata sopra il codice che la applica

Quattro cancelli. Un candidato merita l'holdout solo se li passa **tutti e
quattro**.

| | cancello | soglia | perché quella |
|---|---|---|---|
| **G1** | margine | IRR ≥ benchmark **+1,00 punto**, **mediana sui dodici calendari** | sopra il rumore misurato al giro 63 (0,32 medio, 1,35 massimo sulla sola convenzione di rotazione). Sotto, non si distingue una strategia da un errore di misura |
| **G2** | Deflated Sharpe | **> 0,95** su N = registro **cumulato**, var_sr sulla famiglia | giro 65: sul registro intero SR0 esce 1,78 per periodo, non credibile |
| **G3** | stabilità | extra positivo in **≥ 2/3** delle finestre decennali **E** mediana > 0 | giro 62 ha trovato candidati che vincono spesso e rendono zero; giro 59, dispersione decennale di 5-10 punti |
| **G4** | calendario | margine positivo in **≥ 10 dei 12** mesi di ribilanciamento | giro 68: il top-5 annuale vinceva in 5 mesi su 12 e il suo +1,51 di gennaio era il massimo di dodici estrazioni |

Benchmark: **equal-weight annuale** dello stesso universo con la rotazione vera —
il più severo fra quelli implementabili, stabilito ai giri 60-64.

Una strategia a ribilanciamento **mensile** non ha il grado di libertà del
calendario e passa G4 per costruzione. L'ho dichiarato nel codice invece di
nasconderlo, e sotto si vede quanto conta.

**Finestra 1969-2009**: è la voce che decide se aprire l'holdout, quindi non può
guardarlo.

## Il tabellone

| candidato | G1 margine | G2 DSR | G3 quota | G3 mediana | G4 cal. | passa |
|---|---:|---:|---:|---:|---:|:---:|
| momentum 12-2 top-5 annuale | −0,20 | 0,823 | 66% | +0,67 | 5/12 | — |
| momentum 12-2 top-10 annuale | −0,07 | 0,818 | 62% | +1,19 | 5/12 | — |
| momentum 12-2 top-25 annuale | −0,35 | 0,799 | **69%** | +0,90 | 1/12 | — |
| momentum 6-2 top-10 annuale | +0,13 | 0,836 | **86%** | +1,25 | 9/12 | — |
| low-vol 36m top-10 annuale | −1,12 | 0,701 | 48% | −0,15 | 0/12 | — |
| low-vol 36m top-25 annuale | −0,61 | 0,737 | 62% | +0,36 | 0/12 | — |
| punteggio misto top-10 annuale | −0,55 | 0,837 | 52% | +0,58 | 3/12 | — |
| **momentum 12-2 top-5 mensile** | **+0,56** | **0,971** | 66% | +1,43 | **12/12** | — |
| H5 momentum top-10 mensile | −0,24 | **0,968** | 59% | +0,94 | 12/12 | — |
| momentum 12-2 top-25 mensile | −1,29 | 0,936 | 24% | −0,85 | 12/12 | — |
| H4 low-vol 36m top-10 mensile | −1,56 | 0,753 | 38% | −1,61 | 12/12 | — |
| C1 punteggio misto top-10 mensile | −1,75 | 0,879 | 17% | −1,08 | 12/12 | — |

**Nessuno passa. Zero su dodici.**

## Quale cancello elimina di più

| cancello | elimina |
|---|---:|
| **G1 margine** | **12/12** |
| G2 DSR | 10/12 |
| G3 stabilità | 10/12 |
| G4 calendario | **7/12** |

**La clausola sulla seconda parte della predizione è sbagliata**: il calendario è
il cancello **meno** selettivo, non il più selettivo. Ma va letta bene, e la
lettura giusta non è quella che mi conviene:

- G4 è meno selettivo **perché cinque candidati su dodici lo passano per
  costruzione** — sono mensili e non hanno un calendario da scegliere.
- Fra i **sette annuali**, quelli che il calendario riguarda davvero, **G4 ne
  elimina sei su sette**. Restringendo all'insieme rilevante sarebbe il cancello
  più duro dopo G1.

Dichiaro tutte e due le letture: quella che la predizione richiedeva è sbagliata,
quella condizionata è vera, e la seconda non salva la prima.

**Il vero risultato è G1: nessun candidato arriva a un punto di margine.** Il
migliore è il momentum top-5 mensile a **+0,56** — e per arrivarci ha bisogno di
2,8 rotazioni l'anno, cioè dell'aliquota al 52%.

## Il candidato che ci è andato più vicino

**momentum 12-2 top-5 mensile** passa **due cancelli su quattro** (G2 e G4):

| | |
|---|---:|
| margine | +0,56 (serve 1,00) |
| DSR | **0,971** ✓ |
| quota di finestre vinte | **66%** — serve 66,7% |
| mediana degli extra | +1,43 ✓ |
| calendari | 12/12 ✓ (per costruzione) |

Fallisce G3 per **sette decimi di punto percentuale**: 66% contro 66,7%. È il
punto più vicino al bersaglio che il progetto abbia prodotto, e resta a mezzo
punto di margine dalla soglia.

## L'esito

**Nessun candidato merita l'holdout. Resta sigillato.**

La regola è ora **in vigore**: qualunque candidato futuro deve passare tutti e
quattro i cancelli prima che l'holdout si apra, e l'apertura sarà un atto
separato, registrato come tale, una volta sola.

**Tentativi cumulati a registro: 1.352.** Holdout 2010-2026 **ancora sigillato,
mai aperto in 72 giri**.

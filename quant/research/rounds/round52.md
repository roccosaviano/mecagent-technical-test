# Giro 52 — E6: stress sui LEAPS

**Predizione** (verbatim): *il vantaggio sparisce con un rincaro del premio sotto
il 15% e con k sotto 1,00; sulle finestre mobili vince in meno della metà dei casi.*
**Falsificata se**: sopravvive a un rincaro del **30%** del premio **E** vince in
più della metà delle finestre.

**Esito: CONFERMATA — ma per un solo stress su tre, e non quello che avevo previsto.**

## (i) Implicita più alta — non è qui che si rompe

| k = IV/VIX | leva 1,0× | leva 1,2× | leva 1,5× |
|---:|---:|---:|---:|
| **0,85** (tarato) | 8,37% | 9,47% | **10,98%** |
| 0,95 | 8,14% | 9,19% | **10,63%** |
| 1,05 | 7,88% | 8,87% | **10,22%** |
| 1,15 | 7,59% | 8,52% | **9,77%** |

Benchmark 9,64%. A leva 1,5× il vantaggio **sopravvive a tutte** le implicite
testate, fino a IV = 1,15 × VIX. **La mia predizione qui era sbagliata**: avevo
scritto che sarebbe sparito sotto k = 1,00, e invece regge anche 35 punti
percentuali di implicita sopra il valore tarato.

## (ii) Rincaro del premio d'ingresso — è qui che si rompe

| rincaro | leva 1,0× | leva 1,2× | leva 1,5× |
|---:|---:|---:|---:|
| 0% | 8,37% | 9,47% | **10,98%** |
| 5% | 7,61% | 8,55% | **9,81%** |
| **10%** | 6,85% | 7,61% | 8,64% |
| 15% | 6,07% | 6,69% | 7,49% |
| 30% | 3,79% | 4,01% | 4,26% |

**Il vantaggio sparisce con un rincaro del 10%.** Non sopravvive al 30% richiesto
dalla condizione di falsificazione, e nemmeno al 15% che avevo previsto — è ancora
più fragile.

Cosa vuol dire un rincaro del 10% in pratica: il premio di una call 80% a 12 mesi è
il **20,7% del nozionale**, quindi il 10% è **2 punti di nozionale**. Su un'opzione
lunga, deep ITM e poco scambiata, due punti di spread denaro-lettera più esecuzione
non sono uno scenario avverso: sono la normalità.

## (iii) Finestre mobili — e qui invece regge benissimo

| leva | finestre | vinte | quota | media | peggiore | migliore |
|---:|---:|---:|---:|---:|---:|---:|
| 1,0× | 17 | 7 | 41,2% | −0,09% | −0,92% | +0,49% |
| 1,2× | 17 | **17** | **100,0%** | +0,84% | +0,42% | +1,38% |
| 1,5× | 17 | **17** | **100,0%** | +2,10% | +0,61% | +3,31% |

**Diciassette finestre di vent'anni su diciassette**, a entrambe le leve, con il
caso peggiore ancora positivo. Anche questa clausola della predizione era sbagliata:
avevo scritto "meno della metà".

## Il verdetto, e perché è confermata lo stesso

La condizione di falsificazione era una **congiunzione**: sopravvivere al 30% di
rincaro **e** vincere in più della metà delle finestre. Il secondo ramo passa in
modo schiacciante, il primo fallisce di netto. **E6 confermata: i LEAPS non sono un
candidato.**

Ma la forma del risultato è precisa e vale la pena separarla, perché è diversa da
tutto il resto del progetto:

| dimensione | fragilità |
|---|---|
| **periodo storico** | nessuna — 17/17 finestre, peggior caso +0,42% |
| **livello di volatilità implicita** | nessuna — regge fino a k = 1,15 |
| **prezzo pagato all'ingresso** | **fatale — muore a +10%** |

Tutte le altre 51 voci del progetto sono morte perché il vantaggio non c'era, o
perché era selezione, o perché lo mangiavano le imposte. **Questa muore per una
ragione diversa: il vantaggio c'è, è stabile nel tempo, e sta tutto dentro il costo
di transazione dello strumento con cui lo si prenderebbe.**

È lo stesso vincolo che ha ucciso il resto — i costi — ma stavolta non sotto forma
di rotazione tassata: sotto forma di spread su uno strumento illiquido. Un LEAPS
deep ITM sull'S&P non è QQQ: si negozia poco, e quel poco costa.

## Cosa resta

Il numero da ricordare non è il +1,34: è **la soglia di 2 punti di nozionale**. Chi
avesse accesso a esecuzione istituzionale su opzioni lunghe — spread sotto i 2 punti
sul premio — starebbe guardando un vantaggio reale e stabile su diciassette finestre
di vent'anni. Con l'esecuzione retail, no.

Non è una raccomandazione: è la misura di quanto il risultato dipenda da chi lo
esegue, e nel progetto non ho dati di spread reali su opzioni lunghe per stabilire
da che parte cada un investitore retail irlandese. **Lo dichiaro come limite, e la
voce resta chiusa.**

**Tentativi cumulati a registro: 1.002.** Holdout 2010-2026 **ancora sigillato**.

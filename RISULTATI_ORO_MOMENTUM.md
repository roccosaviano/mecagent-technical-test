# Battere l'S&P 500 ruotando sull'oro col momentum?

Idea testata: stare sull'S&P finché sale, passare all'oro quando si rompe. L'oro è poco
correlato all'azionario (correlazione dei rendimenti mensili 1971-2026: **−0.01**), quindi
in teoria si cavalcano i rialzi e si evita di incassare i crolli.

Riproducibile con `python3 rotation.py`; output integrale in `results/rotation_output.txt`.

## Risposta in tre righe

1. **La rotazione col momentum non funziona.** La strategia esatta della domanda ("S&P se
   il momentum a 12 mesi è positivo, sennò oro") fa **8.47% netto** annuo dal 1971 contro
   **10.28%** del buy&hold, con drawdown quasi uguale (−38.8% vs −49.1%). Nessuna delle 11
   varianti di momentum testate batte il buy&hold in modo stabile su entrambi i campioni.
2. **La diversificazione statica invece funziona, ma sul rischio, non sul rendimento.**
   Un 70/30 S&P/oro ribilanciato con banda 5%: Sharpe **0.99 vs 0.91**, drawdown **−34.8%
   vs −49.1%**, CAGR netto 9.15% vs 10.28%. Rende un po' meno perché rischia molto meno.
   Zero previsioni, turnover 0.10 volte l'anno.
3. **L'unico modo per battere davvero l'S&P è diversificare e poi rialzare il rischio con
   la leva** — e sul campione lungo non basta: 70/30 a 1.5x fa 10.04% contro 10.28%, con
   drawdown −53%. Funziona solo nei periodi in cui l'oro ha fatto bene (dal 1998: 9.88% vs
   7.82%). È una scommessa sul regime, non un edge.

## Cosa è stato confrontato

11 famiglie di strategie, tutte con decisione mensile e pesi applicati **dopo** il segnale:

| # | strategia | logica |
|---|---|---|
| 1 | buy&hold S&P | il benchmark |
| 2 | mix statico 90/10 … 60/40 | ribilanciato con banda 5%, nessuna previsione |
| 3 | momentum relativo 3/6/12m | tutto su quello dei due andato meglio |
| 4 | **S&P se sale, sennò oro** (mom 6m, 12m, MA10 mesi) | la strategia della domanda |
| 5 | dual momentum 6/12m (Antonacci) | il migliore dei due, ma solo se batte il T-bill |
| 6 | risk parity | pesi inversi alla volatilità a 12 mesi |
| 7 | mix 70/30 con leva 1.2/1.3/1.5x | diversificare e rialzare il rischio |

Costi applicati a tutte: 0.075% per lato, CGT 33% su ogni plusvalenza realizzata (con
compensazione delle minus), spese di gestione annue (0.09% azionario, 0.40% oro) nel
campione lungo, liquidità e debito al T-bill (+1.5% di spread se si prende a prestito).

**Due campioni**, perché uno solo mente:
- **1971-2026 mensile** — oro LBMA + S&P total return ricostruito da Shiller. Include il
  1980-2000, ventennio in cui l'oro è stato un disastro. È la parte che conta.
- **2004-2026 giornaliero** — SPY e GLD veri, ETF comprabili, drawdown su dati giornalieri.

## 1971-2026: la tabella che risponde

| strategia | par | CAGR ante | CAGR netto | MDD | Sharpe | turn/an |
|---|---|---|---|---|---|---|
| **buy&hold S&P** | — | 11.08% | **10.28%** | −49.1% | 0.91 | 0.02 |
| mix statico | 90/10 | 10.97% | 10.20% | −44.1% | **0.97** | 0.05 |
| mix statico | 80/20 | 10.33% | 9.64% | −39.6% | **0.98** | 0.08 |
| mix statico | 70/30 | 9.82% | 9.15% | −34.8% | **0.99** | 0.10 |
| mix statico | 60/40 | 9.43% | 8.78% | −29.8% | 0.95 | 0.12 |
| momentum relativo | 12m | 11.39% | 11.19% | −48.4% | 0.70 | 1.71 |
| momentum relativo | 6m | 8.92% | 8.92% | −36.3% | 0.61 | 3.29 |
| **S&P se sale, sennò oro** | mom 12m | 8.76% | 8.47% | −38.8% | 0.70 | 1.18 |
| S&P se sale, sennò oro | MA10m | 7.23% | 7.12% | −41.6% | 0.60 | 1.97 |
| dual momentum | 12m | 10.60% | 10.41% | −46.4% | 0.68 | 1.98 |
| risk parity | — | 6.95% | 6.71% | −29.1% | 0.73 | 0.46 |
| mix 70/30 con leva | 1.5x | 10.79% | 10.04% | −53.1% | 0.74 | 0.25 |

Il momentum relativo a 12 mesi sembra vincere (11.19% vs 10.28%). Guarda la colonna
Sharpe: 0.70 contro 0.91. Prende più rendimento prendendo molto più rischio, e il
drawdown resta a −48%. Non è un miglioramento, è un portafoglio diverso e più scomodo.

## Il test che smonta tutto: decennio per decennio

CAGR netto per decade:

| strategia | 1970s | 1980s | 1990s | 2000s | 2010s | 2020s |
|---|---|---|---|---|---|---|
| buy&hold S&P | 4.1% | **13.4%** | **14.6%** | −0.8% | **10.1%** | 11.2% |
| mix 70/30 | 10.2% | 7.8% | 8.8% | 2.8% | 7.7% | **11.6%** |
| momentum relativo 12m | **26.3%** | 5.4% | 11.3% | **8.7%** | 6.2% | 5.9% |
| S&P se sale, sennò oro (12m) | 7.7% | 8.1% | 11.5% | 5.5% | 8.4% | 9.6% |
| dual momentum 12m | 25.2% | 4.2% | 11.1% | 7.6% | 6.2% | 5.5% |

Tutto il vantaggio storico delle strategie con l'oro viene **da un decennio solo**, gli
anni '70: momentum relativo +26% l'anno mentre l'S&P faceva +4%. Togli quel decennio e la
classifica si ribalta: negli anni '80 e '90 il momentum sull'oro fa 5% mentre l'S&P fa 13-14%.

Questo è il rischio vero della strategia, e non è "un drawdown del 30%": è **restare venti
anni indietro al mercato** perché il tuo asset di rifugio è entrato in un mercato orso
lungo come una generazione. Chi ha comprato oro nel 1980 ha dovuto attendere il 2007 per
tornare in pari in dollari nominali, e non è ancora in pari in termini reali.

Nota positiva per l'idea: nei **due decenni brutti per l'azionario** (anni '70 e 2000s) le
strategie con l'oro hanno fatto molto meglio (+8.7% vs −0.8% nei 2000s). L'oro come
diversificatore paga quando serve. Semplicemente non paga quando non serve, e non sai in
anticipo in quale dei due mondi ti trovi.

## 2004-2026 con gli ETF veri (SPY, GLD)

| strategia | par | CAGR netto | MDD | Sharpe |
|---|---|---|---|---|
| buy&hold S&P | — | 9.34% | −55.2% | 0.65 |
| mix statico | 80/20 | 9.41% | −45.6% | 0.74 |
| mix statico | 60/40 | 9.25% | −36.7% | **0.79** |
| momentum relativo | 12m | 8.23% | −35.7% | 0.52 |
| S&P se sale, sennò oro | mom 12m | 8.21% | −35.3% | 0.58 |
| dual momentum | 12m | 6.92% | −36.8% | 0.48 |
| risk parity | — | 8.56% | −33.2% | 0.75 |
| mix 70/30 con leva | 1.5x | **11.77%** | −56.5% | 0.68 |

Stessa storia sui dati giornalieri e sugli strumenti veri: **nessuna rotazione col momentum
batte il buy&hold**, i mix statici pareggiano il rendimento con 10-19 punti di drawdown in
meno, e il solo modo per superare l'S&P in valore assoluto è il mix con leva — pagando un
drawdown identico o peggiore (−56.5%).

## Perché il momentum fallisce qui, in concreto

- **Con due soli asset i segnali sono pochi e grossi.** Una decisione sbagliata resta
  addosso per mesi. Il momentum funziona meglio su universi ampi, dove gli errori si
  compensano fra molte posizioni.
- **Il momentum a 12 mesi arriva tardi ai punti di svolta.** Verificato sui segnali del
  2020: la regola "S&P se sale, sennò oro" è passata all'oro il **31 marzo**, cioè otto
  giorni dopo il minimo del 23 marzo, ed è rientrata in azioni il **30 aprile**, dopo che
  il rimbalzo era già avvenuto. Ha venduto il fondo e ricomprato più caro. Il momentum
  relativo a 12 mesi ha fatto lo stesso il 28 febbraio.
- **La CGT al 33% per realizzo è brutale su chi ruota.** Il buy&hold differisce l'imposta
  per decenni e compone sul lordo; una strategia che ruota 1-2 volte l'anno paga e ricompone
  sul netto. Nel campione lungo la differenza fra ante e netto è 0.2-0.9 punti l'anno.
- **L'oro costa lo 0.40% l'anno di gestione e non paga cedole né dividendi.** Su 55 anni
  quello 0.40% si mangia il **20% del capitale finale** della quota in oro: non un'inezia.
  L'azionario nel frattempo incassa dividendi, che sono un terzo del suo rendimento totale.

## Cosa farei, se voglio l'oro nel portafoglio

**Tenerne una quota fissa e ribilanciare, senza previsioni.** È la sola cosa che nei dati
migliora il rapporto rendimento/rischio in modo stabile: 20-30% di oro, banda di
ribilanciamento del 5%, e il ribilanciamento fa da solo il lavoro che il momentum cerca di
fare a mano — vende quello che è salito, compra quello che è scivolato.

Il momentum lo lascerei fuori da questo problema. Non perché "non funzioni mai", ma perché
tra due soli asset non ha abbastanza informazione da estrarre, e paga tasse e commissioni
per ottenere un risultato che un mix fisso ottiene gratis.

Se l'obiettivo è **battere l'S&P in valore assoluto** e non "avere lo stesso rendimento con
metà del dolore", nei dati esiste una sola strada e va detta per quello che è: mix
diversificato più leva moderata. Batte l'S&P dal 1998 in poi (9.88% vs 7.82% a 1.5x) ma non
sul campione da 55 anni, aumenta il drawdown oltre il 50%, richiede margine e la disciplina
di non liquidare nel momento peggiore. Nella mia lettura non è un affare: stai scambiando
un rischio che conosci con uno che si manifesta tutto insieme.

## Limiti dichiarati

- **Serie mensili storiche = medie del mese, non chiusure** (verificato: la serie oro LBMA
  ha vol mensile 3.9% contro 5.0% del GLD reale, correlazione 0.62). Quindi nel campione
  lungo volatilità e drawdown sono sottostimati e gli Sharpe sovrastimati **per tutte le
  strategie**. Per questo i segnali usano due mesi di stacco invece di uno: con le medie,
  un mese solo farebbe incassare mezzo mese di movimento già avvenuto. I numeri di rischio
  affidabili sono quelli del campione giornaliero 2004-2026.
- **11 famiglie × più parametri = molti tentativi.** Che qualcuna batta il benchmark in un
  sottocampione è atteso: per questo la tabella per decenni e la divisione IS/OOS contano
  più della riga migliore.
- **Fiscalità:** CGT 33% con compensazione delle minus. Non è modellata l'exit tax 41% con
  deemed disposal a 8 anni degli ETF UCITS ad accumulazione, che per un residente irlandese
  cambia i livelli assoluti (non l'ordine fra le strategie).
- **Un solo asset di diversificazione.** Con Treasury lunghi, TIPS o managed futures i
  numeri sarebbero diversi; questo studio risponde alla domanda posta, cioè oro.

## Riprodurre

```bash
pip install pandas numpy requests
python3 rotation.py          # ~1 minuto, usa la cache in data_cache/
```

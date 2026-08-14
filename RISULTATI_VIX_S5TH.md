# VIX e S5TH sono predittivi del mercato?

Risposta misurata su dati reali, non a sensazione. Tutto riproducibile con
`python3 predictive_test.py` (output integrale in `results/predictive_test_output.txt`).

## Risposta in tre righe

1. **Sul rischio futuro: sì, il VIX molto.** Correlazione di rango 0.74 con la volatilità
   dei 21 giorni successivi (t di Newey-West 14.2), 0.57 a un anno. È il risultato più
   solido di tutto lo studio, e regge qualunque correzione per test multipli.
2. **Sui rendimenti futuri: poco, e nella direzione contraria all'intuito.** VIX alto →
   rendimenti *più alti* (IC +0.09 a +0.18). Il segno è quello del premio al rischio, non
   dell'allarme. Nessuno di questi IC sopravvive alla soglia di Bonferroni (55 test → serve
   p < 0.0009, il migliore ha p = 0.002).
3. **S5TH: quasi tutta la sua informazione è già nel VIX.** Messi nella stessa regressione,
   sulla volatilità a 21 giorni il VIX ha t = 4.3 e S5TH −2.9; a 63 giorni S5TH scende a
   −0.7. Sui rendimenti non tiene nulla dove il campione è abbastanza lungo da contare.

E la conseguenza operativa, che è la cosa che serve davvero: **entrambi funzionano per
dosare il rischio, nessuno dei due per fare timing di entrata/uscita.** Dopo costi e CGT
33%, nessuna regola long/flat basata su VIX o S5TH batte il buy&hold; il vol targeting
migliora lo Sharpe, ma di quel miglioramento la quasi totalità si ottiene anche stando
staticamente al 60% di esposizione, senza previsioni.

## Dati

| serie | fonte | periodo |
|---|---|---|
| SPY, chiusure aggiustate (total return) | stockanalysis.com | 1993-02-01 → 2026-08-13, 8441 sedute |
| VIX | FRED `VIXCLS` | dal 1990 (usato dal 1993) |
| VIX 3 mesi | FRED `VXVCLS` | dal 2007 |
| T-bill 3 mesi (rendimento della liquidità) | FRED `DGS3MO` | tutto il campione |
| **S5TH ricostruito** | composizione point-in-time S&P 500 + prezzi titolo per titolo | 1996 → 2026, usato dal **2015-03-23** |

S5TH (% di membri S&P 500 sopra la propria MA200) è un indice proprietario Bloomberg:
non esiste una fonte storica gratuita, quindi `market_data.py` lo ricostruisce dal basso
con la composizione storica dell'indice giorno per giorno (nessun look-ahead sulla
membership) e i prezzi dei singoli titoli.

**Il limite serio da tenere presente:** i titoli usciti dall'indice e delistati non hanno
più storia prezzi gratuita. La copertura dei membri passa dal 42% (1995-99) al 94-99%
(2020-2026). Sotto copertura piena la breadth ricostruita legge *troppo alto*, perché i
nomi mancanti sono i caduti. Per questo lo studio usa la replica solo dove la copertura
supera il 75%, cioè **dal 2015: 11 anni e mezzo, quasi tutti di mercato rialzista**. È
poco, e va detto prima di dare peso ai numeri su S5TH.

Se hai un export del S5TH vero (Bloomberg o TradingView), mettilo in `data/s5th.csv`
(prima colonna data, ultima colonna il valore): lo studio lo usa al posto della replica e
stampa la correlazione fra i due, che è il modo più rapido per sapere quanto vale la
ricostruzione.

## 1. Rendimenti futuri: informazione debole

IC = correlazione di rango fra segnale e rendimento successivo. `p rot` = p-value da
bootstrap di rotazione circolare (rompe la relazione conservando l'autocorrelazione di
entrambe le serie: è il null giusto per finestre sovrapposte).

| segnale | orizz. | IC | p rot |
|---|---|---|---|
| VIX percentile 3 anni | 5 g | **+0.090** | 0.002 |
| VIX percentile 3 anni | 21 g | **+0.133** | 0.004 |
| VIX percentile 3 anni | 63 g | **+0.156** | 0.019 |
| VIX percentile 3 anni | 252 g | +0.184 | 0.140 |
| VIX3M/VIX (term structure) | 21 g | −0.134 | 0.010 |
| S5TH livello | 5 g | −0.096 | 0.016 |
| S5TH livello | 21 g | −0.155 | 0.033 |
| S5TH livello | 63 g | −0.146 | 0.360 |
| prezzo/MA200 (baseline) | 21 g | −0.033 | 0.475 |

Tre cose da leggere qui:

- **Il segno del VIX è positivo.** Paura alta oggi = rendimento medio più alto dopo, non
  più basso. Chi usa il VIX come segnale di uscita sta usando il segno sbagliato.
- **Il segno di S5TH è negativo:** breadth alta = rendimenti successivi più bassi. Cioè
  S5TH funziona come indicatore di esaurimento, non di conferma del trend. Attenzione però:
  vale sul campione 2015-2026 e sparisce quando allungo la storia (IC −0.081, p 0.16).
- **IC di 0.15 vuol dire il 2% della varianza spiegata.** È informazione vera ma piccola:
  serve a modulare quanto rischio prendere, non a decidere se stare dentro o fuori.

Con 55 combinazioni segnale × orizzonte testate, la soglia di Bonferroni al 5% è
p < 0.0009. **Nessuna riga della tabella dei rendimenti la passa.** Le tengo perché il
pattern è coerente fra segnali correlati e con la letteratura sul premio al rischio di
varianza, ma trattarle come scoperte sarebbe sbagliato.

## 2. Rischio futuro: qui l'informazione è forte

| segnale | target | orizz. | IC | p rot | t NW |
|---|---|---|---|---|---|
| VIX livello | volatilità realizzata | 21 g | **+0.735** | <0.001 | 14.20 |
| VIX livello | volatilità realizzata | 63 g | **+0.689** | 0.003 | 11.65 |
| VIX livello | volatilità realizzata | 252 g | **+0.568** | 0.010 | 4.98 |
| VIX percentile 3 anni | volatilità realizzata | 252 g | +0.421 | <0.001 | 3.39 |
| VIX livello | peggior drawdown | 21 g | −0.492 | 0.005 | −9.11 |
| VIX livello | peggior drawdown | 63 g | −0.451 | 0.010 | −5.71 |
| VIX3M/VIX | volatilità realizzata | 21 g | −0.529 | <0.001 | −6.17 |
| S5TH livello | volatilità realizzata | 21 g | −0.425 | 0.006 | −5.12 |
| S5TH livello | peggior drawdown | 21 g | +0.262 | 0.037 | +3.94 |
| prezzo/MA200 | volatilità realizzata | 21 g | −0.336 | 0.005 | −7.99 |

Questa è la risposta vera alla domanda "sono predittivi": **predicono il rischio, non il
rendimento.** Il VIX a un mese spiega il 54% della varianza di rango della volatilità
futura, e mantiene IC 0.57 perfino a un anno.

Sul dato a 21 giorni nessuna delle 3000 rotazioni nulle si avvicina all'IC osservato
(p < 0.001 con soglia di Bonferroni 0.0015 su 33 test): passa. A 63 e 252 giorni la
rotazione dà p = 0.003 e 0.010, sopra la soglia corretta — con finestre lunghe e
sovrapposte il null di rotazione è largo, ed è giusto che lo sia. Le t di Newey-West sulle
stesse regressioni restano 11.7 e 5.0, quindi la conclusione non cambia: la relazione
VIX → volatilità futura è la cosa più robusta in tutto il dataset.

## 3. S5TH aggiunge qualcosa al VIX?

Le stesse variabili nella stessa regressione, standardizzate, t di Newey-West
(campione 2015-2026, dove la replica è affidabile):

| target | orizz. | n eff | VIX perc. | S5TH livello | prezzo/MA200 | R² |
|---|---|---|---|---|---|---|
| volatilità futura | 21 g | 135 | **4.33** | −2.92 | −0.55 | 24.5% |
| volatilità futura | 63 g | 44 | 2.59 | −0.70 | −0.13 | 12.2% |
| drawdown futuro | 21 g | 135 | −2.96 | +2.44 | −0.90 | 10.0% |
| rendimento futuro | 21 g | 135 | 0.35 | −0.49 | −0.90 | 3.4% |
| rendimento futuro | 63 g | 44 | 0.89 | −1.09 | +0.25 | 5.0% |
| rendimento futuro | 252 g | **10** | −0.18 | −4.21 | +2.27 | 20.1% |

Il t = −4.21 di S5TH sui rendimenti a un anno è la riga più tentatrice della tabella ed è
anche quella da buttare: `n eff = 10` finestre non sovrapposte. Dieci osservazioni
indipendenti in un solo regime di mercato non sono un'evidenza, sono un aneddoto con una t
davanti.

Dove il campione permette di misurare (21-63 giorni), **il VIX regge e S5TH si sgonfia**:
un secondo termometro nella stessa stanza.

## 4. Le tabelle condizionali, per farsi un'idea delle grandezze

Rendimento annualizzato nei 63 giorni successivi, quintili point-in-time del segnale:

| quintile | VIX percentile (1993-2026) | S5TH livello (2015-2026) |
|---|---|---|
| Q1 (più basso) | 7.2% | 22.2% |
| Q2 | 13.1% | 20.2% |
| Q3 | 10.7% | 9.2% |
| Q4 | 12.2% | 17.6% |
| Q5 (più alto) | **16.9%** | **10.8%** |
| intero campione | 11.8% | 15.5% |

Interazione, rendimento annualizzato a 63 giorni (2015-2026):

| | S5TH basso | S5TH medio | S5TH alto |
|---|---|---|---|
| **VIX alto** | **30.8%** (n=491) | 18.4% (n=257) | 18.3% (n=114) |
| VIX medio | 1.1% (n=161) | 2.6% (n=282) | 8.8% (n=346) |
| VIX basso | 15.2% (n=98) | 13.5% (n=345) | 16.6% (n=455) |

La cella "VIX alto + breadth a terra" rende 30.8% annualizzato: è il momento in cui tutti
vendono. Con un campione che contiene un solo vero panico (marzo 2020) più i minori del
2022 e 2025, però, quella cella è tre episodi, non una legge.

## 5. E dopo costi e tasse? Nessun timing sopravvive

Overlay long/flat o dosati, costi 0.15% round-trip, CGT 33% pagata a ogni realizzo,
liquidità remunerata al T-bill netto, parametri scelti in-sample e validati out-of-sample.
Estratto della tabella 6a (campione pieno, OOS 2009-10-30 → 2026-08-13):

| regola | par | OOS ante imposte | OOS netto | OOS DD | Sharpe | esposiz. |
|---|---|---|---|---|---|---|
| **buy&hold** | — | **14.82%** | **12.43%** | −33.7% | 0.90 | 100% |
| VIX alto → investito | p>0.8 | 7.06% | 4.07% | −28.3% | 0.65 | 16% |
| VIX basso → investito | p<0.9 | 10.59% | 5.46% | −32.1% | 0.79 | 92% |
| prezzo>MA200 (baseline) | — | 9.88% | 5.59% | −22.4% | 0.86 | 83% |
| vol target da VIX | 20% | 12.48% | 7.85% | −24.0% | 0.93 | 94% |
| vol target da vol realizzata | 15% | 12.42% | 8.33% | −19.5% | **0.97** | 90% |
| statico 60% | — | 9.43% | 6.74% | −21.3% | 0.93 | 60% |

Cosa dice questa tabella:

- **Nessuna regola di timing batte il buy&hold sul rendimento**, né netta né ante imposte.
  Parte del divario è differimento fiscale (il buy&hold paga la CGT una volta sola alla
  fine): per questo la colonna ante imposte c'è, e anche lì il timing perde.
- **Il vol targeting migliora lo Sharpe** (0.97 vs 0.90) e taglia il drawdown da −34% a
  −20%. Ma: (a) il vol targeting dalla volatilità *realizzata* batte quello dal VIX
  (0.97 vs 0.93), quindi il contributo specifico del VIX è negativo, non positivo;
  (b) uno statico al 60% prende Sharpe 0.93 senza prevedere niente. Quasi tutto il
  guadagno di Sharpe è "meno esposizione", non "esposizione al momento giusto".
- Nel sottocampione 2015-2026 (tabella 6b) la combinazione `S5TH>50% o VIX estremo` arriva
  a Sharpe OOS 1.15 contro 0.97 del buy&hold. Con ~30 regole provate su 5 anni e mezzo di
  out-of-sample, il massimo che supera il benchmark è quello che ti aspetti dal caso: non
  ci costruirei sopra.

## 6. Cosa ne farei operativamente

- **Usare il VIX per dimensionare, non per decidere.** Ha senso: esposizione più bassa
  quando la volatilità attesa è alta, e la volatilità attesa è la cosa che il VIX sa
  davvero. Ma va confrontato con il vol targeting sulla volatilità realizzata, che qui fa
  meglio ed è gratis.
- **Non usare il VIX come allarme per uscire.** Il segno storico è il contrario: dopo VIX
  alto i rendimenti medi sono superiori, non inferiori.
- **S5TH: tenerlo come cruscotto, non come segnale.** Nella parte in cui aggiunge qualcosa
  (rischio a breve) è quasi interamente sovrapposto al VIX, che ha 30 anni di storia
  pulita invece di 11 ricostruiti.
- **Prima di dare peso a qualunque risultato su S5TH, procurarsi la serie vera.** Con
  `data/s5th.csv` lo studio si riesegue sul dato Bloomberg e dice subito quanto la replica
  gli assomiglia.

## 7. Limiti, in chiaro

- La replica di S5TH ha copertura piena solo dal 2020; usata dal 2015 con copertura ≥75%.
  Il campione utile è corto e in gran parte rialzista: qualsiasi conclusione su S5TH è
  provvisoria per costruzione.
- I test multipli sono contati (55 sui rendimenti) e la soglia di Bonferroni è dichiarata.
  I risultati sul rischio la passano; quelli sui rendimenti no.
- I costi (0.15% round-trip) e la fiscalità (CGT 33% per realizzo, T-bill netto sulla
  liquidità) sono quelli di `swing_harness.py`, cioè un investitore individuale irlandese.
  Con conti fiscalmente differiti la penalizzazione del timing si riduce, ma il confronto
  ante imposte in tabella mostra che non si ribalta.
- SPY come sottostante: un solo mercato, un solo strumento. Un edge che esiste solo qui non
  è un edge.

## Riprodurre

```bash
pip install pandas numpy requests
python3 market_data.py        # ricostruisce data/market_dataset.csv (~25 min: 1206 ticker)
python3 predictive_test.py    # lo studio completo (~2 min)
python3 predictive_test.py --quick   # meno rotazioni bootstrap, ~30 s
```

`data/market_dataset.csv` è già nel repo, quindi `predictive_test.py` gira senza
riscaricare niente. La cache dei download sta in `data_cache/` (ignorata da git).

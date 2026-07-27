# Giri 40-43 — gruppi C e D: la coda è finita

Otto voci: C1-C6 tutte **confermate**, D1 e D2 **falsificate** — le prime due
falsificazioni vere della coda, e nessuna delle due promuove niente.

---

## Giro 40 — C1: cointegrazione fra i 49 settori

**Predizione**: *molte coppie risultano cointegrate in-sample per puro caso, e la
cointegrazione non persiste fuori campione.* **Falsificata se**: la quota che resta
cointegrata fuori campione supera significativamente il 5%. → **CONFERMATA**

1.176 coppie, Engle-Granger al 5%, stima 1969-1997 / verifica 1997-2026:

| | |
|---|---:|
| cointegrate **in-sample** | 130 / 1.176 (**11,1%**) |
| attese per solo caso al 5% | 58 |
| di quelle 130, ancora cointegrate **fuori campione** | **7 / 130 (5,4%)** |
| test binomiale contro H₀ = 5% | **p = 0,476** |

Il doppio dei falsi positivi attesi in-sample (11,1% contro 5%) — quindi *un po'* di
cointegrazione vera c'è. Ma di quelle che passano il test, la quota che regge nel
periodo successivo è **5,4%, indistinguibile dal caso**. Lo spread trading sulle 60
coppie selezionate rende **−0,65%** netto contro 9,53% dell'azionario.

---

## Giro 40 — C2: breadth

**Predizione**: *correlato al trend dell'indice oltre 0,8, quindi non aggiunge
informazione.* **Falsificata se**: correlazione sotto 0,6 **e** migliora l'IRR.
→ **CONFERMATA**

| | CAGR | Sharpe | max DD | turn | IRR netta |
|---|---:|---:|---:|---:|---:|
| azionario buy&hold | 10,38% | 0,63 | −83,7% | 0,00× | **10,56%** |
| breadth > 40% | 8,57% | 0,71 | −46,9% | 1,51× | 6,78% |
| breadth > 60% | 8,68% | **0,83** | **−29,3%** | 1,95× | 6,54% |
| filtro di trend MA10 | 9,44% | 0,79 | −43,9% | 1,47× | 7,42% |

Correlazione col filtro di trend **0,830**, sopra 0,8 come previsto. Il breadth a
60% porta il drawdown da −83,7% a −29,3% — la riduzione di rischio più grande di
tutta la ricerca — e costa 4 punti di IRR.

---

## Giro 41 — C3: momentum a orizzonti multipli

**Predizione**: *il 12-2 domina; aggiungere orizzonti brevi introduce reversione e
alza il turnover senza alzare lo Sharpe.* **Falsificata se**: Sharpe > del solo
12-2 con turnover non superiore. → **CONFERMATA**

| | CAGR | Sharpe | turn | IRR (52%) |
|---|---:|---:|---:|---:|
| **solo 12-2 (riferimento)** | 15,16% | **0,862** | 2,68× | 10,04% |
| composito 6+12 | 14,04% | 0,821 | 3,45× | 9,34% |
| 12-2 con reversione a 1m | 14,16% | 0,825 | 7,49× | 9,36% |
| composito 1+3+6+12 | 12,75% | 0,776 | 5,71× | 8,49% |
| solo 1m | 9,76% | 0,610 | **9,08×** | 6,95% |
| 49 settori equal-weight (bench) | 11,15% | 0,700 | 0,00× | **10,40%** |

Nessun composito passa: **tutti** hanno Sharpe più basso **e** turnover più alto.
La predizione è esatta in entrambe le clausole. Il solo 1 mese ha 9 rotazioni
l'anno — reversione pura, il caso peggiore per la fiscalità irlandese.

---

## Giro 41 — C4: term structure del VIX

**Predizione**: *il segnale funziona per cronometrare la volatilità, non la
direzione.* **Falsificata se**: produce un segnale direzionale con accuratezza sopra
la frequenza di base in modo significativo. → **CONFERMATA**

Finestra 2010-2026, **dichiarata dentro l'holdout**: non lo brucia (C4 non promuove
candidati, la sua condizione è sull'accuratezza di un segnale) ma nessun candidato
può uscire da qui.

| | |
|---|---:|
| frequenza di base dei giorni positivi | 54,76% |
| in **contango** (VIX < VIX3M, 92% del campione) | 54,70% |
| in **backwardation** (VIX ≥ VIX3M, 8%) | 55,45% |
| test binomiale contro la frequenza di base | **p = 0,535** |
| Spearman fra VIX/VIX3M e volatilità realizzata dei 21 giorni **successivi** | **+0,421** (p ≈ 10⁻¹⁷²) |

Il contrasto è netto: **zero potere direzionale, potere enorme sulla volatilità**.
È il risultato più pulito su cosa il VIX dice e cosa non dice.

> Nota di correzione: la prima esecuzione aveva le etichette invertite — chiamavo
> "backwardation" il rapporto sotto 1, che è il contango. Il test misurava
> l'opposto di quel che dichiarava e l'esposizione della strategia era capovolta
> (2,22% invece di 12,57%). Corretto prima di riportare.

---

## Giro 42 — C5: premio di volatilità nudo contro coperto

**Predizione**: *la copertura costa più della coda che evita.* **Falsificata se**:
IRR netta superiore a PUT non coperto. → **CONFERMATA**

Approssimazione dichiarata: non ho catene di opzioni, quindi al posto dello spread
verticale su misura uso gli indici CBOE pubblicati. **CNDR** (iron condor) vende uno
strangle e **compra le ali**: è un premio di volatilità a rischio definito.

| | CAGR | vol | Sharpe | skew | max DD | IRR netta |
|---|---:|---:|---:|---:|---:|---:|
| PUT — premio **nudo** | 9,40% | 10,0% | 0,95 | −1,02 | −20,7% | **6,44%** |
| CNDR — premio **coperto** | 0,57% | 6,6% | 0,12 | **−1,50** | −19,0% | 0,53% |
| BXM — buy-write | 8,43% | 10,2% | 0,84 | −0,97 | −22,2% | 5,77% |
| CLL — collar 95/110 | 8,34% | 12,0% | 0,73 | −1,39 | −22,1% | 7,69% |
| PPUT — sola copertura | 11,28% | 11,8% | 0,97 | −0,37 | −20,8% | 8,88% |
| azionario | 15,52% | 15,3% | 1,03 | −0,37 | −24,8% | 11,76% |

Il coperto perde **5,91 punti** contro il nudo. E la parte che non mi aspettavo:
**comprare le ali non ha tagliato la coda** — la skew peggiora da −1,02 a −1,50 e
il drawdown migliora di appena 1,7 punti. Va detto che il confronto è confuso dal
fatto che CNDR vende anche call, quindi non è solo un put spread: è
un'approssimazione, e questo ne è il limite.

Il numero pulito è l'ultima riga contro l'azionario: **la sola assicurazione (PPUT)
costa 4,24 punti di CAGR l'anno**.

---

## Giro 42 — C6: i quattro pilastri dei CTA

**Predizione**: *correlazione media sotto 0,2, Sharpe combinato sopra ogni singolo,
IRR netta comunque sotto il buy&hold.* **Falsificata se**: IRR netta > buy&hold.
→ **CONFERMATA sul test, sbagliata sulla seconda clausola**

Correlazione media a coppie **0,189**, sotto 0,2 come previsto.

| | CAGR | vol | Sharpe | max DD | turn | IRR netta |
|---|---:|---:|---:|---:|---:|---:|
| solo trend azionario | 10,45% | 11,2% | 0,94 | −17,8% | 1,60× | 8,04% |
| solo premio volatilità | 9,40% | 10,0% | **0,95** | −20,7% | 0,00× | 6,44% |
| solo momentum materie prime | 0,44% | 18,8% | 0,12 | −50,6% | 2,36× | 0,43% |
| solo carry valutario | −0,75% | 10,6% | −0,02 | −49,6% | 0,24× | 1,37% |
| 4 pilastri equal-weight | 5,34% | 8,0% | 0,69 | −15,2% | 1,11× | 4,77% |
| 4 pilastri inverse-vol | 5,63% | 7,6% | 0,76 | **−14,7%** | 0,99× | 4,90% |
| azionario buy&hold | 15,52% | 15,3% | 1,03 | −24,8% | 0,00× | **11,76%** |

Il Sharpe combinato è **0,76 contro 0,95** del miglior singolo: la mia seconda
clausola era sbagliata. Il motivo è aritmetico — diversificare fra quattro stream
di cui due hanno Sharpe ≈ 0 non può battere il migliore dei quattro; la
diversificazione riduce la varianza ma trascina il numeratore verso la media.
**Combinare cose che non funzionano con cose che funzionano peggiora il risultato**,
e questo è vero anche quando le correlazioni sono basse.

---

## Giro 43 — D1: dispersione per data di partenza → **FALSIFICATA**

**Predizione**: *la dispersione dell'extra-rendimento supera 3 punti, cioè è più
grande dell'extra-rendimento stesso.* **Falsificata se**: dispersione sotto 1 punto.

20 date di partenza (1974-1993), fine sempre 2026, benchmark **equal-weight dei 49
settori** (stesso universo su cui la strategia sceglie):

| candidato | media | min | max | ampiezza | dev. std | volte > 0 |
|---|---:|---:|---:|---:|---:|---:|
| H5 momentum settoriale | −1,20% | −1,41% | −1,04% | **0,36%** | 0,14% | **0/20** |
| H4 tilt low-vol | −2,85% | −2,91% | −2,74% | 0,17% | 0,05% | **0/20** |
| C1 punteggio misto | −2,54% | −2,88% | −2,32% | 0,56% | 0,17% | **0/20** |

**Falsificata**: ampiezza massima 0,56 punti, ben sotto 1.

**Ma la falsificazione è colpa della specifica, non un risultato di stabilità.**
Venti date di partenza fra il 1974 e il 1993 con la fine sempre al 2026 producono
venti campioni che condividono **33-52 anni su 52**. Sono quasi lo stesso campione:
la dispersione è piccola per costruzione. Ho scritto una condizione che si
falsifica quasi da sola, e va detto invece di presentare 0,56 come "il risultato è
robusto". Ho aggiunto **D3** in coda per il test che risponde davvero alla domanda:
finestre mobili di **lunghezza fissa**, che si sovrappongono molto meno.

**La cosa importante di questa tabella è un'altra**, e non riguarda D1: contro
l'equal-weight dello **stesso universo**, tutti e tre i candidati sono negativi in
**60 casi su 60**. Contro il PAC cap-weighted H5 risultava +2,95 punti. Le due cose
non si contraddicono — equal-weight e cap-weight rendono diverso — ma dicono che
**la scelta del benchmark vale più di qualunque parametro provato in 43 giri**. Ho
aggiunto **D4** per misurarlo esplicitamente.

---

## Giro 43 — D2: bootstrap a blocchi → **FALSIFICATA**

**Predizione**: *il candidato migliore cade dentro il 95° percentile della
distribuzione nulla.* **Falsificata se**: sta oltre il 99°.

Bootstrap stazionario di Politis-Romano, blocchi di media 12 mesi, 5.000
risimulazioni del differenziale strategia − benchmark, centrato a zero:

| candidato | extra annuo (lordo di imposte) | percentile | 95° nullo | 99° nullo |
|---|---:|---:|---:|---:|
| **H5 momentum settoriale** | **+3,82%** | **100,0** | 1,81% | 2,49% |
| C1 punteggio misto | +0,05% | 51,3 | 1,54% | 2,13% |
| H4 tilt low-vol | −1,53% | 7,7 | 1,67% | 2,38% |

**Falsificata**: H5 sta oltre il 99° percentile.

Cosa vuol dire davvero, perché è facile leggerlo male:

- Il nullo qui è *"il differenziale mensile ha media zero, con la stessa
  autocorrelazione"*. È in sostanza un t-test corretto per autocorrelazione.
  **Non tiene conto della selezione** — quello lo fa il DSR, che H5 non passa.
- Il +3,82% è **lordo di imposte** e al netto dei soli costi di transazione.
- Nella stessa tabella di D1, la stessa strategia sullo stesso benchmark fa
  **−1,20 punti di IRR netta**.

Messe insieme, le due righe sono la sintesi di tutto il progetto:

> **Il premio momentum è reale — statisticamente distinguibile da zero oltre il
> 99° percentile — e l'investitore perde comunque.** 3,82 punti lordi diventano
> −1,20 netti, perché 262% di rotazione l'anno a un'aliquota del 52% costa più di
> cinque punti.

D2 è falsificata e non promuove niente: una falsificazione statistica su un premio
lordo non è un candidato.

---

## Bilancio dei gruppi C e D

| voce | esito | numero chiave |
|---|---|---|
| C1 cointegrazione | confermata | 5,4% persiste fuori campione, p = 0,476 |
| C2 breadth | confermata | correlazione 0,830 col filtro di trend |
| C3 momentum multi-orizzonte | confermata | ogni composito: Sharpe più basso E turnover più alto |
| C4 term structure VIX | confermata | direzione p = 0,535 · volatilità ρ = +0,42 |
| C5 premio coperto | confermata | −5,91 punti, e la coda non si accorcia |
| C6 quattro pilastri | confermata | Sharpe 0,76 contro 0,95 del miglior singolo |
| **D1 data di partenza** | **falsificata** | ampiezza 0,56 punti — ma per difetto della specifica |
| **D2 bootstrap a blocchi** | **falsificata** | H5 al 100° percentile, +3,82% lordo / −1,20% netto |

**Registro a 854 tentativi. Holdout 2010-2026 ancora sigillato. La coda è esaurita**
salvo le tre voci nate durante l'esecuzione: **D3**, **D4** (pre-registrate qui) e
**A6** (rimasta dal giro 30).

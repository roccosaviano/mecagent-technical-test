# Attivo contro passivo, netto di fiscalità irlandese

PAC da €500/mese, finestra 1990-01 → 2023-12 (408 versamenti, €204.000 versati).
Tutto netto di costi (0,15% round-trip) e imposte irlandesi.

---

## La risposta

**Nessuna strategia attiva basata su un pattern di mercato batte il buy&hold netto
di tasse.** Le uniche due cose che aggiungono valore non sono strategie: sono la
scelta del veicolo fiscale (+1,72 punti l'anno) e una riduzione di rischio che va
poi rilevereggiata (trend following mensile).

Il margine totale disponibile, tolto tutto ciò che non sopravvive alla verifica,
è di circa **1,7 punti l'anno**, e sta interamente nel *non* comprare un ETF UCITS.
Su €204.000 versati in 34 anni sono €314.000 di montante finale in più — più di
quanto produca qualunque strategia testata qui.

---

## Quello che non ho potuto testare

Da dichiarare prima dei risultati, perché limita le conclusioni.

| Cosa | Stato | Perché |
|---|---|---|
| OHLC di SPY, QQQ, IWM, EFA, EEM, GLD, TLT | **non scaricabile** | Yahoo Finance risponde `429 Too Many Requests` in modo persistente; Stooq e stooq.pl rispondono con un muro anti-bot JavaScript; AlphaVantage richiede API key |
| RSP (equal-weight ETF) per il test 12 | **non scaricabile** | stessa ragione |
| Strategia 4 con stop a N **ATR** | **non testabile come specificata** | senza High/Low giornalieri l'ATR non è calcolabile. Ho usato uno stop a N deviazioni standard close-to-close, che **non è la stessa strategia** ed è etichettato come sostituto ovunque |
| Diversità a livello di **singolo titolo** S&P 500 | **non testabile** | serve CRSP/Compustat a livello firm. Ho misurato la diversità fra 49 settori, che **sottostima** la concentrazione vera: dentro "Tecnologia" il peso di una singola società non si vede |

**Sostituzioni fatte, tutte con dati reali e nessuna simulazione:**

- Gruppo A gira sull'indice total return CRSP giornaliero di Ken French
  (1926-2026, 26.253 sedute) e sui 49 portafogli settoriali giornalieri. È un
  campione **più lungo e più pulito** dei 7 ETF richiesti, ma è un solo mercato.
- Gruppo D usa i 49 settori con capitalizzazioni reali (numero di società ×
  dimensione media, pubblicati da French mese per mese).
- Gruppo C usa Shiller `ie_data.xls`, la stessa fonte dei tuoi riferimenti.

Fonti effettivamente usate: Ken French Data Library, Robert Shiller, AQR
(*Betting Against Beta: Equity Factors, Monthly*), Open Source Asset Pricing
(Chen & Zimmermann, 212 anomalie replicate). Tutte verificate e riscaricabili
con `quant/fetch_data.sh`.

---

## Gate di calibrazione

Prima di qualunque risultato, ho riprodotto i tuoi due numeri di riferimento.

| | mio | tuo | delta |
|---|---|---|---|
| Buy&hold indice, CGT 33% all'uscita | 8,11% | 8,21% | −0,10 |
| ETF UCITS, exit tax + deemed disposal | 6,39% | 6,76% | −0,37 |
| Max drawdown | −49,0% | −47% | −2,0 |

Per arrivarci ho dovuto risolvere un'ambiguità nella tua specifica: il benchmark
è definito come *"CGT 33% solo all'uscita"*, ma la tabella fiscale impone anche
*"dividendi esteri ~52%"*. Sono incompatibili. Con i dividendi tassati ogni anno
l'IRR scende a **7,02%**, lontano dal tuo 8,21%; senza, dà 8,12%. Ho quindi
adottato la tua definizione letterale del benchmark (dividendi non tassati) e
riporto separatamente la variante realistica.

**Il prelievo annuo sui dividendi esteri costa 1,09 punti l'anno.** Se detieni
azioni USA direttamente da residente irlandese, quello è il tuo numero vero,
non 8,11%.

Sull'ETF ho usato **38% su tutto il percorso**, non lo scalino storico 41%→38%:
il tuo orizzonte sta interamente oltre il 2026. Con il 41% storico l'IRR sarebbe
5,99%.

---

## Tabella unica

`vs proprio` è la colonna che conta: confronta ogni riga col buy&hold **dello
stesso universo**. La colonna `vs bench` confronta col benchmark Shiller e per i
gruppi A e D contiene anche la differenza fra universi diversi, che non è merito
della strategia.

| Strategia | IRR | vs bench | vs proprio | Montante | Max DD | Sharpe | Op/anno | Imposte |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Trend following 10 mesi, leva 2x | 11,82% | +3,70 | +3,70 | 2.334.978 | −38,3% | 0,77 | 0,6 | 945.229 |
| Trend following 10 mesi, leva 1,5x | 9,53% | +1,42 | +1,42 | 1.386.289 | −28,6% | 0,81 | 0,6 | 538.570 |
| D. Equal-weight 49 settori, annuale | 8,85% | +0,74 | +0,39 | 1.183.350 | −52,4% | 0,59 | 1,0 | 507.187 |
| D. Diversity-weighted p=0,25, annuale | 8,70% | +0,59 | +0,24 | 1.144.638 | −51,4% | 0,59 | 1,0 | 500.479 |
| D. Diversity-weighted p=0,50, annuale | 8,58% | +0,47 | +0,11 | 1.114.132 | −50,8% | 0,59 | 1,0 | 495.113 |
| *D. Cap-weight 49 settori* `[bench D]` | 8,47% | +0,36 | 0,00 | 1.086.393 | −50,2% | 0,58 | 0,0 | 534.218 |
| D. Diversity-weighted p=0,75, annuale | 8,47% | +0,35 | −0,00 | 1.085.981 | −50,3% | 0,59 | 1,0 | 487.805 |
| *Buy&hold indice CRSP* `[bench A]` | 8,33% | +0,22 | 0,00 | 1.067.513 | −54,6% | 0,49 | 0,0 | 524.918 |
| D. Diversity-weighted p=0,25, mensile | 8,25% | +0,14 | −0,21 | 1.036.491 | −51,8% | 0,58 | 12,0 | 397.846 |
| D. Diversity-weighted p=0,50, mensile | 8,14% | +0,02 | −0,33 | 1.010.258 | −51,1% | 0,58 | 12,0 | 387.802 |
| **Buy&hold indice, CGT 33% all'uscita** `[BENCHMARK]` | **8,11%** | 0,00 | 0,00 | **1.011.938** | −49,0% | 0,65 | 0,0 | 497.546 |
| D. Diversity-weighted p=0,75, mensile | 8,03% | −0,08 | −0,44 | 987.113 | −50,6% | 0,58 | 12,0 | 378.434 |
| Trend following 10 mesi, leva 1x | 7,12% | −1,00 | −1,00 | 814.956 | **−19,0%** | **0,88** | 0,6 | 296.781 |
| Buy&hold azioni dirette, dividendi 52%/anno | 7,02% | −1,09 | −1,09 | 798.257 | −50,8% | 0,48 | 0,0 | 491.927 |
| Buy&hold **ETF UCITS**, exit tax 38% + DD | 6,39% | −1,72 | −1,72 | 697.784 | −49,0% | 0,65 | 0,0 | 404.329 |
| B. Short interest (RF + premio netto) | 5,88% | −2,23 | −2,23 | 626.983 | −28,7% | 0,53 | 12,0 | 211.499 |
| A. Donchian breakout {20, 20} | 2,93% | −5,18 | −5,40 | 347.364 | −32,4% | 0,27 | 4,2 | 86.546 |
| B. Bet Against Beta (RF + premio netto) | 2,77% | −5,34 | −5,34 | 336.051 | −54,2% | 0,34 | 12,0 | 120.432 |
| A. Trend + stop σ {50, 3} *(sostituto ATR)* | 2,16% | −5,96 | −6,17 | 299.906 | −44,4% | 0,19 | 8,4 | 83.184 |
| A. RSI2 mean-reversion {100, 5, 5} | 1,93% | −6,18 | −6,40 | 287.576 | −10,1% | 0,10 | 3,4 | 17.890 |
| A. Down-streak reversal {200, 4} | 1,14% | −6,97 | −7,19 | 249.054 | −9,1% | −0,20 | 3,4 | 3.523 |
| B. Accruals (RF + premio netto) | −2,16% | −10,27 | −10,27 | 144.158 | −41,1% | −0,12 | 12,0 | 56.046 |

### Ranking per Sharpe

1. **Trend following 1x — 0,88** (unico chiaramente sopra il benchmark)
2. Trend following 1,5x — 0,81
3. Trend following 2x — 0,77
4. Benchmark buy&hold / ETF — 0,65
5. Diversity-weighted e cap-weight 49 settori — 0,58-0,59
6. Tutto il gruppo A — 0,10-0,27
7. Accruals, Down-streak — negativi

Il ranking per Sharpe e quello per IRR dicono cose diverse solo per il trend
following. Per tutto il resto concordano.

---

## Chi batte il benchmark, e quanto regge

| Strategia | base | costi ×2 | 1990-2006 | 2007-2023 |
|---|---:|---:|---:|---:|
| Trend following 2x | +3,70 | +3,63 | +4,25 | +3,86 |
| Trend following 1,5x | +1,42 | +1,34 | +2,29 | +1,04 |
| D. Equal-weight annuale | +0,39 | +0,35 | +1,89 | **−0,26** |
| D. Diversity-weighted p=0,25 annuale | +0,24 | +0,22 | +1,47 | **−0,26** |
| D. Diversity-weighted p=0,50 annuale | +0,11 | +0,11 | +1,02 | **−0,12** |

**Il gruppo D non sopravvive al cambio di sottoperiodo.** Tutto il suo vantaggio
viene dal 1990-2006; nel 2007-2023 il segno si inverte. Un margine di 0,1-0,4
punti che cambia segno a metà campione è rumore, non edge.

**Il trend following regge tutti e tre gli stress.** Ma va giudicato con la tua
stessa regola.

### Il gate sulla leva, applicato alla lettera

Hai scritto: *"Applica leva solo a ciò che funziona già a 1x."*

A 1x il trend following rende **7,12%, cioè 1,00 punto in MENO del buy&hold.**
Per la tua regola, il risultato a 2x va scartato.

Però la regola merita una precisazione, perché qui il caso è ambiguo. A 1x la
strategia ha **Sharpe 0,88 contro 0,65** e **drawdown −19,0% contro −49,0%**.
Non è che non funzioni: converte rendimento in stabilità. Sta fuori dal mercato
circa un quarto del tempo, quindi perde rialzi, ma evita i crolli. La leva non
sta moltiplicando un extra-rendimento inesistente — sta ricomprando il beta che
la strategia aveva rimosso, su una serie a rischio più basso.

Se accetti quella lettura, il trend following levereggiato è l'unica strategia
attiva testata che regge. Se applichi la tua regola letteralmente, non ne resta
nessuna. **Io la tratterei con sospetto per tre ragioni che il backtest non
cattura:**

1. Il drawdown modellato a 2x è −38,3%. Su CFD a leva 2 su indice, un −38% è una
   sequenza di margin call, non una riga in un foglio di calcolo. Il modello
   assume che tu regga la posizione; la meccanica del broker no.
2. Il costo di finanziamento è ipotizzato a benchmark + 3%. È l'ipotesi che ti
   sei dato tu, ed è ragionevole, ma il risultato è direttamente proporzionale:
   +1 punto di spread toglie circa 1 punto di IRR a 2x.
3. Non c'è split in-sample/out-of-sample. La regola dei 10 mesi è pubblicata
   (Faber 2007) e non l'ho ottimizzata io, il che è una difesa parziale — ma non
   equivale a una validazione fuori campione.

---

## Gruppo A — swing trading: fallimento su tutta la linea

36 combinazioni di parametri provate (RSI2: 12, down-streak: 6, Donchian: 9,
trend+stop: 9), ottimizzate **solo** sulla prima metà (1926-1974), validate
**solo** sulla seconda (1974-2026).

| Strategia | IS CAGR | OOS CAGR | OOS Sharpe | vs B&H OOS |
|---|---:|---:|---:|---:|
| Buy&hold | — | **12,03%** | 0,75 | — |
| Donchian breakout {20,20} | 9,24% | 7,32% | 0,71 | −4,71 |
| Trend + stop σ {50,3} | 9,94% | 7,40% | 0,69 | −4,63 |
| RSI2 {100,5,5} | −0,90% | 0,93% | 0,27 | −11,10 |
| Down-streak {200,4} | −0,34% | −0,17% | −0,04 | −12,20 |

Due delle quattro perdono già **in-sample**, cioè sul campione su cui le ho
ottimizzate scegliendo il massimo di 12 e 6 combinazioni. Questo non è
overfitting: è assenza di segnale.

**Robustezza su 49 settori** (stessi parametri, finestra OOS):

| Strategia | settori in cui batte il B&H | mediana extra-CAGR |
|---|---:|---:|
| RSI2 | **0 / 49** | −11,51% |
| Down-streak | **0 / 49** | −12,16% |
| Donchian | 8 / 49 | −3,26% |
| Trend + stop σ | 8 / 49 | −2,47% |

**Sottoperiodi ventennali** (extra-CAGR vs buy&hold): l'unico periodo in cui
qualcosa funziona è il 1930-1949 (Donchian +4,48, trend+stop +3,66). Dal 1950
in poi tutto negativo, con un peggioramento monotono fino al 2010-2026
(−6,67 e −7,85).

### Contro la tua soglia di expectancy

Hai calcolato che con 100 operazioni l'anno serve un'expectancy lorda dello
0,273% per operazione. Queste strategie operano 3-8 volte l'anno, quindi la
soglia per loro è molto più alta — ogni operazione deve pesare di più:

| Strategia | Op/anno | Expectancy realizzata | Soglia di pareggio |
|---|---:|---:|---:|
| RSI2 | 3,6 | 0,262% | **3,181%** |
| Down-streak | 3,8 | −0,033% | **3,050%** |
| Donchian | 4,1 | 1,902% | **2,831%** |
| Trend + stop σ | 8,4 | 0,813% | **1,370%** |

Nessuna arriva neanche vicino. Donchian, la migliore, realizza il 67% di quanto
le servirebbe. Il divario non è colmabile con costi più bassi: è mancanza di edge.

### Verifica del look-ahead

Il controllo richiesto ha trovato un bug — nel controllo stesso, alla prima
stesura. Corretto, il risultato è:

- segnale che conosce il rendimento di oggi: **CAGR 131,1%, Sharpe 7,92**
- stesso segnale ritardato di un giorno: **CAGR 5,8%, Sharpe 0,55**

Il motore distingue i due casi, quindi lo `shift(1)` sta facendo il suo lavoro e
i risultati sopra non contengono informazione dal futuro.

---

## Gruppo B — anomalie: il decadimento è reale e quantificato

Split alla data di pubblicazione, non a metà campione.

| Anomalia | Pubbl. | Pre %/anno | t | Post %/anno | t | Decadimento |
|---|---:|---:|---:|---:|---:|---:|
| Bet Against Beta | 2014 | 8,25% | 6,57 | 5,03% | 2,02 | **39%** |
| Accruals (Sloan) | 1996 | 6,87% | 7,04 | 1,17% | 1,00 | **83%** |
| Short interest (Dechow) | 2001 | 8,63% | 5,26 | 11,86% | 4,10 | −37% |
| Short interest / IO | 2005 | 24,78% | 2,99 | 69,78% | 3,31 | −182% |

### Verifica di McLean & Pontiff su tutto l'universo

Su **205 anomalie** replicate con premio pre-pubblicazione positivo e storia
sufficiente:

- premio medio **pre**-pubblicazione: **7,36%/anno**
- premio medio **post**-pubblicazione: **4,05%/anno**
- **decadimento medio: 50,4%** (mediano 58,2%)
- quota con premio post-pubblicazione negativo: 16%

McLean & Pontiff (2016) riportano ~50%. **Replicato quasi esattamente.** È il
risultato più solido di tutto questo lavoro, e vale come validazione della
pipeline oltre che come risultato in sé.

### I due "short interest" che sembrano migliorare non sono investibili

`IO_ShortInterest` ha volatilità **94,2%/anno**, un mese a **+321,3%** e uno a
−67,8%. Il premio sta in pochi mesi estremi su titoli minuscoli. Non è un edge,
è un artefatto di costruzione: i portafogli OSAP sono **equal-weighted**, quindi
una società da 20 milioni pesa quanto Apple. Con €500/mese la gamba short non è
eseguibile in nessuna delle due.

### Implementabilità: cosa resta dopo i costi veri

| Anomalia | Post lordo | Transaz. | Prestito titoli | Finanz. leva | **Netto** |
|---|---:|---:|---:|---:|---:|
| Bet Against Beta | 5,03% | 0,30% | 2,50% | 1,29% | **0,94%** |
| Accruals | 1,17% | 0,30% | 2,50% | — | **−1,63%** |
| Short interest | 11,86% | 0,90% | 2,50% | — | **8,46%** |

Ipotesi dichiarate: prestito titoli 5%/anno sul nozionale short (metà del
portafoglio), che è **prudente** per il decile più shortato — sui titoli
hard-to-borrow si va ben oltre; BAB levereggiata ~1,4× con spread di
finanziamento retail del 3%.

Messe nel PAC con CGT 33% sul realizzo mensile, nessuna arriva al benchmark:
short interest 5,88%, BAB 2,77%, accruals −2,16%. **Nello scenario di
riqualificazione al 52%** scendono a 4,38%, 1,31% e −4,07%.

Per short interest il break-even sul costo del prestito titoli è intorno al
**22%/anno** sulla gamba short. Sui titoli più shortati del mercato quel livello
si raggiunge e si supera regolarmente: il premio esiste sulla carta e viene
incassato da chi presta i titoli, non da chi li shorta.

---

## Gruppo D — il teorema è vero, il trade è in perdita

### La matematica funziona

Ho verificato numericamente l'identità di Fernholz

```
log( V_π(T) / V_μ(T) ) = log( D_p(μ(T)) / D_p(μ(0)) ) + (1−p) ∫ γ*_π dt
```

su 437 mesi e 49 settori:

| p | log(V_π/V_μ) | deriva diversità | (1−p)·∫γ* | residuo |
|---|---:|---:|---:|---:|
| 0,25 | −0,0031 | −0,3038 | +0,3352 | −0,0345 |
| 0,50 | −0,0110 | −0,2029 | +0,2032 | −0,0113 |
| 0,75 | −0,0141 | −0,1002 | +0,0949 | −0,0088 |

L'identità torna. **γ\* = 1,12%/anno per p=0,50**, esattamente nella banda
0,5-1,5% che avevi previsto.

### Ma la deriva della diversità se lo mangia tutto

Il tasso di crescita in eccesso genera +0,2032 di log-rendimento in 36 anni. La
perdita di diversità del mercato ne toglie −0,2029. **Il netto è −0,0110: zero,
con il segno sbagliato.**

Diversità del mercato nel tempo (fra 49 settori):

| Periodo | Top-1 % | Top-10 % | HHI | D(0,5) |
|---|---:|---:|---:|---:|
| 1990-1999 | 9,3 | 60,3 | 467 | 35,48 |
| 2000-2009 | 11,7 | 65,3 | 546 | 33,34 |
| 2010-2014 | 9,1 | 62,7 | 492 | 34,74 |
| 2015-2019 | 11,8 | 65,2 | 554 | 33,37 |
| 2020-2026 | **17,9** | **68,5** | **764** | **30,75** |

Ricordo che questa è concentrazione **fra settori**: quella fra singoli titoli è
più alta e non l'ho potuta misurare.

### La tua ipotesi: metà confermata, metà falsificata

> *"Nei periodi di diversità calante il diversity-weighted sottoperforma, e il
> decennio 2015-2025 dovrebbe essere il caso peggiore del campione."*

**Prima parte: confermata.** Correlazione fra variazione mensile di diversità e
sovraperformance del DW: **+0,114**. Debole ma del segno giusto, e i sottoperiodi
sono coerenti:

| Periodo | Extra-rendimento DW p=0,50 | Diversità |
|---|---:|---|
| 1990-1999 | **−1,51%/anno** | in calo |
| 2000-2009 | +2,42%/anno | in salita |
| 2010-2014 | +0,08%/anno | in calo |
| 2015-2025 | −1,22%/anno | in calo |

**Seconda parte: falsificata.** Il peggior sottoperiodo non è il 2015-2025
(−1,22%) ma il **1990-1999 (−1,51%)**. La concentrazione è cresciuta molto più
nell'ultimo decennio, ma il DW ha sofferto di più negli anni '90. La relazione
diversità→performance esiste come direzione, non come classifica.

### L'orizzonte del teorema

Con i parametri stimati sui dati reali:

- n = 49, log(n) = 3,892
- δ = autovalore minimo della covarianza annualizzata = **0,00305**
- ε = 1 − max quota osservata = 1 − 0,2130 = **0,7870**

| p | T garantito |
|---|---:|
| 0,25 | **12.968 anni** |
| 0,50 | **6.484 anni** |
| 0,75 | **4.323 anni** |

Il teorema è vero e la dimostrazione è corretta. L'orizzonte su cui garantisce
l'arbitraggio relativo supera il tuo di due o tre ordini di grandezza. **Per una
decisione di investimento è inutilizzabile.**

### Break-even fiscale del ribilanciamento

La domanda che avevi posto: a quale frequenza γ* supera il costo fiscale?

| p | Ribilanciamento | Extra lordo | Costo transaz. | Costo fiscale | **Extra netto** |
|---|---|---:|---:|---:|---:|
| 0,25 | mensile | −0,01% | 0,03% | +0,79% | **−0,79%** |
| 0,25 | trimestrale | +0,01% | 0,02% | +0,57% | **−0,57%** |
| 0,25 | annuale | +0,14% | 0,01% | +0,24% | **−0,24%** |
| 0,50 | mensile | −0,03% | 0,03% | +0,82% | **−0,82%** |
| 0,50 | trimestrale | −0,03% | 0,01% | +0,58% | **−0,58%** |
| 0,50 | annuale | +0,08% | 0,01% | +0,25% | **−0,25%** |
| 0,75 | annuale | +0,06% | 0,01% | +0,21% | **−0,21%** |

**Non esiste una frequenza di ribilanciamento che pareggia.** Nemmeno quella
annuale, la più economica. Il motivo è quello che avevi anticipato: γ* vale
1,12%/anno, ma non arriva mai all'investitore perché la deriva della diversità lo
neutralizza *prima* delle tasse. Quello che resta da tassare è un extra lordo di
+0,06/+0,14 punti contro un costo fiscale di 0,21/0,25.

Il confronto è contro un cap-weight che **non si ribilancia mai**: i pesi seguono
da soli i prezzi, quindi non paga né costi né imposte finché non vendi. È quello
il vero avversario, ed è imbattibile per costruzione fiscale.

Nella tabella principale il DW annuale appare a +0,11/+0,24 sul suo benchmark:
la differenza rispetto a questi numeri è che lì il cap-weight paga CGT alla
liquidazione finale del PAC. Il segno cambia col dettaglio della modellazione,
il che è di per sé la prova che il margine è dentro il rumore.

---

## Edge statistici contro edge strutturali

Hai chiesto di separarli. La separazione è netta e sbilanciata.

### Edge statistici (gruppi A e B): contributo **zero**

Non sopravvive nulla.

- Gruppo A: −5,40 / −7,19 punti contro il proprio benchmark, 0-8 settori su 49,
  negativo in 4 sottoperiodi su 5, expectancy per operazione tra un terzo e due
  terzi di quella necessaria.
- Gruppo B: decadimento post-pubblicazione del 50,4% confermato su 205 anomalie.
  Ciò che resta viene consumato da prestito titoli e finanziamento. La migliore
  arriva a −2,23 punti dal benchmark.

### Edge strutturali: contributo **+1,72 punti l'anno**, tutto dal veicolo fiscale

| Fonte | Valore | Natura |
|---|---:|---|
| **Azioni/indice diretto invece di ETF UCITS** | **+1,72 punti/anno** | regola fiscale, non decade |
| Evitare il prelievo annuo sui dividendi esteri | +1,09 punti/anno | regola fiscale |
| Diversity-weighted (gruppo D) | **0,00** | teorema vero, annullato da ipotesi venute meno + tasse |
| Trend following levereggiato | +1,42/+3,70 | riduzione di rischio rilevereggiata, **non** un'identità matematica |

**Il gruppo D è l'esempio più pulito di edge strutturale che non paga.** Il
teorema non è stato falsificato: γ* esiste, vale 1,12%/anno, e l'identità di
Fernholz torna nei dati. Sono venute meno le *ipotesi*: il mercato ha perso
diversità in modo monotono, e la deriva dei pesi ha assorbito esattamente il
guadagno da ribilanciamento. Poi il 33% sul realizzo ha portato il residuo sotto
zero. Vero, dimostrato, e in perdita.

Il trend following **non appartiene a questa categoria**, anche se sopravvive ai
test. Non deriva da un'identità né da una regola fiscale: dipende dal fatto che i
mercati abbiano continuato a produrre trend persistenti. È un edge statistico che
finora non è decaduto, non una legge.

---

## Fallimenti ed errori trovati

Per trasparenza sul processo, non solo sui risultati.

**Dati:** quattro fonti di prezzi bloccate (Yahoo, Stooq ×2, AlphaVantage). Il
Gruppo A è stato eseguito su un universo sostitutivo, l'ATR non è stato testato,
la diversità a livello di titolo non è stata misurata.

**Bug trovati e corretti durante il lavoro:**

1. **Il test di look-ahead era sbagliato.** Il segnale "baro" leggeva `ret[t+1]`
   ma veniva moltiplicato per `ret[t]`, quindi era disallineato: il segnale
   "onesto" risultava quello con la preveggenza. Il test ha fatto esattamente il
   lavoro per cui esisteva, trovando un errore nella propria costruzione.
2. **Il cap-weight veniva ribilanciato ogni mese**, addebitandogli 26%/anno di
   turnover e imposte che non sostiene. Un portafoglio di mercato non richiede
   trading: i pesi seguono i prezzi. Correggendolo, il Gruppo D è passato da
   apparentemente positivo a negativo su tutte le frequenze.
3. **La liquidità non investita non rendeva nulla**, penalizzando le strategie
   poco esposte. Ora frutta il risk-free al netto della DIRT 33%. Il Gruppo A ne
   ha guadagnato circa 1 punto — restando comunque a −5/−7.
4. **L'IRR non convergeva** (bisezione senza bracketing valido, produceva valori
   dell'ordine di 10¹⁴). Riscritta in spazio logaritmico con XIRR datato.
5. **Warm-up degli indicatori perso** all'inizio della finestra out-of-sample:
   i segnali vanno calcolati sulla serie intera e poi affettati.

**Ambiguità nella specifica:** benchmark "CGT solo all'uscita" contro tabella
"dividendi 52%" — incompatibili, risolta a favore della definizione letterale
del benchmark, con la variante riportata separatamente.

**Cosa non ho fatto:** nessuno split in-sample/out-of-sample sul trend following
mensile del Gruppo C (era specificato come benchmark, non come strategia da
ottimizzare). Nessuna modellazione di margin call, gap overnight o
ricomposizione dell'indice. Nessun test su mercati non-USA.

---

## Conclusione operativa

Su €500/mese e 20-30 anni:

1. **Il veicolo conta più di qualunque strategia.** Indice o azioni in regime CGT
   invece di ETF UCITS vale +1,72 punti l'anno, non decade, non richiede di
   azzeccare nulla. È il risultato più grande e più affidabile del lavoro.
   Verifica con un consulente fiscale come accedervi in pratica: molti broker
   retail offrono principalmente UCITS proprio perché è il prodotto standard UE.
2. **Il ribilanciamento è un evento tassabile e, nel tuo regime, quasi sempre in
   perdita.** Vale per il diversity-weighting, per l'equal-weighting e per
   qualunque schema a pesi fissi. Con CGT al 33% e nessun conto fiscalmente
   protetto, la strategia migliore è quella che non vende.
3. **Lo swing trading su questo campione non ha edge.** Non è una questione di
   parametri o di costi: l'expectancy per operazione è un terzo di quella
   necessaria, e due strategie su quattro perdono già in-sample.
4. **Se vuoi comunque una componente attiva**, l'unica che ha superato tutti gli
   stress è il trend following mensile a 10 mesi — ma a 1x rende meno del
   buy&hold, e per la tua stessa regola questo lo squalifica. Se decidi di usarlo
   levereggiato, sappi che stai scommettendo sulla persistenza dei trend e sulla
   tua capacità di reggere un −38% a leva 2 senza essere liquidato.

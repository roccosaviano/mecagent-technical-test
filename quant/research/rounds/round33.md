# Giro 33 — A4: Kelly frazionario e de-risking sul drawdown

**Predizione scritta prima** (voce A4, verbatim): *il de-risking sul drawdown
peggiora l'IRR (vende sui minimi) pur migliorando il DD massimo.* **Falsificata
se**: l'IRR netta migliora rispetto all'esposizione costante.

**Esito: CONFERMATA, e in modo insolitamente netto — 12 casi su 12 in entrambe le
direzioni.**

## Le regole, fissate prima

- **Kelly**: `f* = media(eccesso) / varianza(eccesso)` sui **60 mesi precedenti**,
  esposizione grezza `f × f*`, **tagliata a 1,0**. Il taglio è una scelta
  dichiarata: Kelly sull'azionario dà `f*` intorno a 2,5-3, quindi mezzo Kelly
  chiederebbe leva 1,3×, e la leva costa benchmark+3% (bocciata al giro 07). Qui
  misuro il sizing, non il finanziamento — riporto però quanto spesso il cap morde.
- **De-risking**: finché il drawdown corrente della **curva della strategia**
  (calcolato sui soli dati fino a ieri) supera la soglia, l'esposizione è
  dimezzata. Soglie 10% · 20% · 30%.
- **Liquidità**: la parte non investita rende il risk-free al netto della DIRT 33%.
  Senza questo una strategia che sta fuori dal mercato verrebbe penalizzata per
  un'ipotesi invece che per i suoi meriti.
- **Realizzo**: ogni riduzione di esposizione è una vendita, e realizza plusvalenza
  in proporzione (passata come `realize_frac` al motore fiscale).

Griglia 2 × 4 = **8 configurazioni**, su **due sottostanti** come richiede il
protocollo di robustezza.

## Risultati — indice cap-weighted, 1926-2026 (1.199 mesi)

| configurazione | espos. media | CAGR | Sharpe | max DD | turn/anno | IRR netta | vs B&H |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0,25 Kelly costante | 0,66 | 7,45% | 0,66 | −65,0% | 0,40× | 6,62% | −3,94 |
| 0,25 Kelly + DD>10% | 0,55 | 6,80% | 0,71 | −45,8% | 0,46× | 5,60% | −4,96 |
| 0,25 Kelly + DD>20% | 0,59 | 7,30% | 0,72 | −45,8% | 0,44× | 6,14% | −4,42 |
| 0,25 Kelly + DD>30% | 0,60 | 7,13% | 0,68 | −53,1% | 0,41× | 6,18% | −4,38 |
| 0,5 Kelly costante | 0,76 | 8,15% | 0,64 | −71,1% | 0,35× | 7,44% | −3,12 |
| 0,5 Kelly + DD>10% | 0,62 | 7,60% | **0,73** | −50,2% | 0,44× | 6,39% | −4,17 |
| 0,5 Kelly + DD>20% | 0,66 | 7,77% | 0,71 | −50,2% | 0,46× | 6,61% | −3,95 |
| 0,5 Kelly + DD>30% | 0,68 | 7,89% | 0,69 | −56,9% | 0,36× | 7,04% | −3,52 |
| **buy & hold** | 1,00 | 10,38% | 0,63 | **−83,7%** | 0,00× | **10,56%** | +0,00 |

## Risultati — equal-weight 49 settori, 1969-2026 (683 mesi)

| configurazione | espos. media | CAGR | Sharpe | max DD | turn/anno | IRR netta | vs B&H |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0,25 Kelly costante | 0,70 | 6,43% | 0,55 | −38,8% | 0,54× | 5,68% | −5,48 |
| 0,25 Kelly + DD>10% | 0,58 | 5,67% | 0,58 | −28,1% | 0,71× | 4,67% | −6,50 |
| 0,25 Kelly + DD>20% | 0,64 | 5,91% | 0,54 | −32,9% | 0,69× | 5,15% | −6,01 |
| 0,25 Kelly + DD>30% | 0,67 | 5,96% | 0,53 | −38,6% | 0,63× | 5,15% | −6,01 |
| 0,5 Kelly costante | 0,84 | 8,37% | 0,62 | −39,4% | 0,38× | 7,49% | −3,67 |
| 0,5 Kelly + DD>10% | 0,70 | 7,03% | 0,63 | −29,1% | 0,78× | 5,75% | −5,41 |
| 0,5 Kelly + DD>20% | 0,79 | 7,76% | 0,61 | −32,9% | 0,46× | 6,83% | −4,33 |
| 0,5 Kelly + DD>30% | 0,82 | 8,07% | 0,61 | −38,8% | 0,38× | 7,17% | −3,99 |
| **buy & hold** | 1,00 | 11,15% | 0,70 | −52,6% | 0,00× | **11,16%** | +0,00 |

## Il verdetto

| | de-risking migliora |
|---|---|
| il **drawdown massimo** | **12 casi su 12** |
| l'**IRR netta** | **0 casi su 12** |

Non c'è nemmeno un'eccezione, su due sottostanti, due valori di `f` e tre soglie.
**A4 confermata.** Il costo del de-risking va da −0,32 a −1,74 punti di IRR, e il
guadagno in drawdown da +0,2 a +20,9 punti.

## Il meccanismo, che è più interessante del verdetto

Il de-risking dimezza l'esposizione **dopo** che il drawdown ha superato la soglia,
cioè vende in basso, e la ripristina quando il recupero è già avvenuto, cioè
ricompra in alto. È esattamente la struttura di un ordine di vendita a mercato in
un momento di ribasso, ripetuto sistematicamente. Aggiunge anche rotazione
tassabile: sul equal-weight la soglia al 10% porta il turnover da 0,38× a 0,78×
l'anno, cioè lo raddoppia, e ogni riduzione realizza plusvalenza al 33%.

**Il gradiente è monotono nella soglia**: più bassa la soglia, più spesso scatta,
più costa. A 10% costa 1,0-1,7 punti; a 30% costa 0,3-0,5. La soglia bassa
protegge di più e costa di più, in modo ordinato — non è rumore, è il prezzo
dell'assicurazione.

## La parte da non liquidare: 20 punti di drawdown per 0,4 punti di IRR

Sull'indice cap-weighted, `0,5 Kelly + DD>30%` costa **0,40 punti** di IRR contro
l'esposizione costante e taglia **14,2 punti** di drawdown. E il buy&hold puro ha
un drawdown massimo del **−83,7%** (1929-1932): il de-risking lo porta a −50/−57%.

Il test di falsificazione riguarda il rendimento, e lì la risposta è no. Ma sarebbe
disonesto fermarsi lì: **per chi versa €500 al mese per trent'anni, la variabile
che determina il risultato non è solo il rendimento, è se smette di versare durante
un −80%.** Un drawdown dimezzato a 0,4 punti l'anno di costo è un prezzo che molti
pagherebbero razionalmente, e questa è una decisione di preferenza, non di
ottimizzazione. Quello che i numeri dicono è **quanto costa**, non se convenga.

## La componente Kelly, separata dal de-risking

| sottostante | f | espos. media | cap attivo | IRR netta | vs B&H |
|---|---:|---:|---:|---:|---:|
| cap-weighted | 0,25 | 0,66 | 46% del tempo | 6,62% | −3,94 |
| cap-weighted | 0,50 | 0,76 | 64% | 7,44% | −3,12 |
| equal-weight 49 | 0,25 | 0,70 | 37% | 5,68% | −5,48 |
| equal-weight 49 | 0,50 | 0,84 | 68% | 7,49% | −3,67 |

**Il sizing di Kelly costa più del de-risking**: 3,1-5,5 punti contro 0,3-1,7. E il
motivo non è che Kelly sbaglia — è che Kelly frazionario con `f` sotto 1 è per
costruzione un modo di **stare meno investiti**, e su un asset con premio al
rischio positivo stare meno investiti costa. L'esposizione media va da 0,66 a 0,84:
il resto è liquidità al risk-free tassato DIRT 33%.

Da notare: **il cap a 1,0 morde il 37-68% del tempo**. Per più di metà della storia
mezzo Kelly chiederebbe di stare in leva, e non può. Questo rende il test una cosa
sola: *"vale la pena ridurre l'esposizione quando la stima di Kelly è bassa?"*, e la
risposta è no — quei periodi a bassa esposizione sono quelli che seguono i crolli,
cioè quelli con i rendimenti attesi più alti. La stima di Kelly su 60 mesi è
**pro-ciclica**: μ misurato all'indietro è basso proprio quando i prezzi sono bassi.

## Ancora lo stesso schema del giro 32

Lo Sharpe migliore della griglia è **0,73** (`0,5 Kelly + DD>10%`) contro **0,63**
del buy&hold: +0,10, il miglioramento di rischio più grande visto in tutta la
ricerca. E la stessa configurazione perde **4,17 punti** di IRR netta. Tre giri di
fila — HRP, min-variance, Kelly — arrivano allo stesso posto da tre direzioni
diverse: **si può migliorare lo Sharpe di un PAC azionario, e non serve a niente
senza leva a buon mercato.**

## Contabilità

Turnover massimo della griglia 0,78 volte l'anno, sotto la soglia del 100% che
farebbe scattare la riqualificazione; lo scenario 52% è calcolato comunque (miglior
configurazione: 6,68%). DSR del migliore 1,000 su N=54 (la sola griglia sarebbe
N=8; uso la famiglia pre-dichiarata, più severa) — **non promuovibile**, perché
nessuna configurazione batte il benchmark.

**Tentativi cumulati a registro: 722.** Holdout 2010-2026 **ancora sigillato**.

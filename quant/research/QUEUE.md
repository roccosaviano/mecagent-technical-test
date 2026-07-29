# Coda delle ipotesi pre-dichiarate

Ogni voce ha **predizione** e **condizione di falsificazione** scritte prima
dell'esecuzione. Il Routine ne prende **una** per giro, in ordine, e riporta
l'esito qualunque sia. Nessuna voce viene riscritta dopo aver visto i dati: se
un'ipotesi va rivista, si aggiunge una voce nuova che dichiara perché.

Contabilità dei tentativi: `N` = dimensione della griglia se c'è selezione,
altrimenti la famiglia delle ipotesi pre-dichiarate (attualmente 59 — ogni voce
aggiunta alza la soglia per tutte).

**STATO: la coda dichiarata è esaurita.** A1-A5, B1-B6, C1-C6, D1-D2 sono tutte
eseguite (giri 30-43). Restano solo le voci nate durante l'esecuzione e non ancora
eseguite: **L2, L3, L4** (gruppo L, aggiunto al giro 73). Il gruppo E (opzioni) è stato
aggiunto ed eseguito ai giri 48-49.

**Vincolo che ha ucciso quasi tutto finora**: ogni realizzo paga 33%, e sopra
~100 operazioni l'anno diventa 52%. Le ipotesi sotto sono ordinate mettendo
per prime quelle a **bassa rotazione**, che è dove resta spazio.

---

## A. Allocazione e sizing (bassa rotazione, priorità alta)

**A1 — Risk parity fra classi di asset** ✔ eseguita (giro 30)
Pesi inversi al contributo di rischio su azionario, decennale, oro-proxy,
materie prime. Ribilanciamento annuale.
*Predizione*: Sharpe superiore al 60/40 ma IRR netta inferiore all'azionario
puro, perché il decennale rende meno e il ribilanciamento è tassato.
*Falsificata se*: IRR netta > buy&hold azionario.

**A2 — Hierarchical Risk Parity (López de Prado 2016)** ✔ eseguita (giro 31)
Clustering gerarchico della matrice di correlazione, allocazione ricorsiva.
Sui 49 settori, ribilanciamento annuale.
*Predizione*: batte l'equal-weight in Sharpe ma non l'IRR netta; il vantaggio
documentato di HRP è sulla stabilità dei pesi, non sul rendimento.
*Falsificata se*: IRR netta > equal-weight annuale di almeno 0,5 punti.

**A3 — Minimum variance e maximum diversification** ✔ eseguita (giro 32)
Due portafogli ottimizzati sui 49 settori, vincolo long-only, annuale.
*Predizione*: minimum variance riduce il drawdown di oltre 10 punti e perde
2-4 punti di CAGR; nessuno dei due batte l'IRR netta del cap-weight.
*Falsificata se*: uno dei due supera il cap-weight netto imposte.

**A4 — Kelly frazionario e de-risking sul drawdown** ✔ eseguita (giro 33)
Esposizione = f × Kelly stimato sul passato, con f in {0,25 · 0,5}; variante
che taglia l'esposizione quando il drawdown corrente supera una soglia.
*Predizione*: il de-risking sul drawdown peggiora l'IRR (vende sui minimi) pur
migliorando il DD massimo.
*Falsificata se*: l'IRR netta migliora rispetto all'esposizione costante.

**A5 — Equal risk contribution fra i 4 stream non correlati migliori** ✔ eseguita (giro 34)
Selezionati per correlazione, non per rendimento, così la scelta non guarda
il risultato.
*Predizione*: correlazione media sotto 0,3 raggiungibile, ma l'IRR netta resta
sotto il buy&hold perché i componenti a rendimento alto sono anche quelli ad
alta rotazione.
*Falsificata se*: IRR netta > buy&hold.

---

## B. Mercati non ancora toccati

**B1 — Materie prime (petrolio WTI, FRED DCOILWTICO dal 1986)** ✔ eseguita (giro 37)
Trend following e carry sul future proxy.
*Predizione*: il trend following su materie prime funziona lordo (è il caso
canonico dei CTA) e muore sui costi più le imposte, come sull'azionario.
*Falsificata se*: IRR netta > buy&hold azionario.

**B2 — Valute (DEXUSEU, DEXJPUS, DEXCHUS) — carry e momentum** ✔ eseguita (giro 37)
Carry = differenziale tassi (DGS2 contro tasso estero implicito), momentum a
12 mesi. Long/short fra tre cambi.
*Predizione*: il carry ha premio positivo ma skew fortemente negativa, e le
tre valute non bastano a diversificare il rischio di crash.
*Falsificata se*: Sharpe > 0,5 con skew > -0,5 dopo costi.

**B3 — Credito (spread high yield BAMLH0A0HYM2)** ✖ NON TESTABILE (giro 38)
Segnale macro: allargamento dello spread come indicatore di rischio per
l'azionario. Esci dall'azionario quando lo spread sale oltre N deviazioni.
*Predizione*: segnale con potere in-sample, ma il ritardo di pubblicazione e
la reazione già incorporata nei prezzi lo rendono inutile out-of-sample.
*Falsificata se*: batte il buy&hold netto imposte fuori campione.

**B4 — Curva dei tassi (T10Y2Y) come segnale di regime azionario** ✔ eseguita (giro 38)
L'inversione della curva precede le recessioni. Riduzione dell'esposizione
azionaria quando la curva si inverte.
*Predizione*: il segnale è corretto ma troppo lento — l'anticipo mediano
dell'inversione è 12-18 mesi, e uscire con quell'anticipo costa più di quanto
protegga.
*Falsificata se*: IRR netta > buy&hold.

**B5 — Azionario internazionale (French Developed, Emerging, Japan, Europe)** ✔ eseguita (giro 39)
Momentum cross-sectional fra regioni, ribilanciamento annuale.
*Predizione*: funziona come il momentum settoriale (stesso meccanismo) e
muore come lui sulle imposte, con in più il fatto che la storia parte dal 1990.
*Falsificata se*: DSR > 0,95 con IRR netta positiva.

**B6 — Cripto: universo esteso oltre i 7 attuali** ✔ eseguita (giro 39)
Aggiungere le maggiori per capitalizzazione disponibili su OKX, e includere
esplicitamente asset con storia parziale per attenuare la sopravvivenza.
*Predizione*: allargando l'universo il CAGR del buy&hold scende (i nuovi sono
mediamente peggiori) e il vantaggio relativo del trend filter resta, ma il DSR
non migliora perché la finestra resta di sei anni.
*Falsificata se*: DSR > 0,95.

---

## C. Sistemi non ancora provati

**C1 — Pairs trading / cointegrazione sui 49 settori** ✔ eseguita (giro 40)
Test di Engle-Granger su tutte le coppie, trading dello spread sulle coppie
cointegrate nel periodo di stima.
*Predizione*: molte coppie risultano cointegrate in-sample per puro caso
(1.176 coppie testate al 5% danno ~59 falsi positivi), e la cointegrazione non
persiste fuori campione.
*Falsificata se*: la quota di coppie che restano cointegrate fuori campione
supera significativamente il 5%.

**C2 — Breadth / partecipazione come segnale di mercato** ✔ eseguita (giro 40)
Quota di settori sopra la propria media a 200 giorni come indicatore di
salute del mercato.
*Predizione*: correlato al trend dell'indice stesso oltre 0,8, quindi non
aggiunge informazione a un semplice filtro di trend.
*Falsificata se*: correlazione col filtro di trend sotto 0,6 E migliora l'IRR.

**C3 — Momentum a orizzonti multipli combinato (1, 3, 6, 12 mesi)** ✔ eseguita (giro 41)
Punteggio composito invece del solo 12-2.
*Predizione*: il 12-2 domina; aggiungere orizzonti brevi introduce reversione
e alza il turnover senza alzare lo Sharpe.
*Falsificata se*: Sharpe > del solo 12-2 con turnover non superiore.

**C4 — Volatilità come asset: term structure del VIX** ✔ eseguita (giro 41)
VIX contro VIX a 3 mesi (contango/backwardation) come segnale di rischio.
*Predizione*: il segnale funziona per cronometrare la volatilità, non la
direzione — stesso esito del giro 22.
*Falsificata se*: produce un segnale direzionale con accuratezza sopra la
frequenza di base in modo significativo.

**C5 — Overlay di copertura sul premio di volatilità** ✔ eseguita (giro 42)
Vendere put e comprare put più lontane (put spread) per tagliare la coda che
uccide BXM e PUT. Approssimato dai dati CBOE disponibili.
*Predizione*: la copertura costa più della coda che evita, perché il premio
delle put lontane è proporzionalmente più caro (volatility smile).
*Falsificata se*: IRR netta superiore a PUT non coperto.

**C6 — Multi-strategia su stream davvero non correlati** ✔ eseguita (giro 42)
Combinare: trend azionario, carry valutario, momentum materie prime, premio
di volatilità. Sono i quattro pilastri dei CTA.
*Predizione*: correlazione media sotto 0,2, Sharpe combinato sopra ogni
singolo, e IRR netta comunque sotto il buy&hold per la rotazione aggregata.
*Falsificata se*: IRR netta > buy&hold azionario.

---

## D. Metodologiche

**D1 — Quanto vale la finestra di partenza** ✔ eseguita (giro 43)
Rieseguire i tre candidati promossi facendo partire il campione in 20 anni
diversi, per misurare la dispersione del risultato dovuta alla sola data di
inizio.
*Predizione*: la dispersione dell'extra-rendimento supera 3 punti, cioè è più
grande dell'extra-rendimento stesso.
*Falsificata se*: dispersione sotto 1 punto.

**D2 — Bootstrap a blocchi dei candidati** ✔ eseguita (giro 43)
Rendimenti risimulati a blocchi per costruire la distribuzione nulla
dell'extra-rendimento, invece di affidarsi al solo DSR.
*Predizione*: il candidato migliore cade dentro il 95° percentile della
distribuzione nulla.
*Falsificata se*: sta oltre il 99°.

---

## Esiti registrati

| Voce | Giro | Esito |
|---|---|---|
| H31 combinazione dei promossi | 29 | **confermata** — corr 0,944, la combinazione non aggiunge |
| H32 turn-of-month | 29 | **confermata** — effetto reale (t=7,04), decaduto del 60%, strategia a −7,26 |
| A1 risk parity fra classi | 30 | **confermata** — ERC Sharpe 0,92 contro 0,87 del 60/40, ma IRR netta 7,08% contro 10,48% dell'azionario. Nessuna delle 4 allocazioni batte. Oro e materie prime **non testabili** |
| A2 hierarchical risk parity | 31 | **confermata** — Sharpe 0,78 contro 0,74 dell'equal-weight, ma IRR netta 9,45% contro 9,89% (−0,44) e −1,43 contro il cap-weighted. In più HRP risulta **meno stabile** di inverse-variance (0,283 contro 0,109): la tesi del paper è contro il min-variance, che è A3 |
| A3 min-variance / max-diversification | 32 | **confermata** sul test — min-var 8,22% e max-div 9,34% contro 10,88% del cap-weight. Ma **entrambe le clausole descrittive della predizione erano sbagliate**: il DD scende di 4,2 punti (non >10) e il CAGR ceduto è 1,08 (non 2-4). Il min-var tiene l'84% in 5 settori, 7,5 posizioni effettive |
| A4 Kelly frazionario + de-risking | 33 | **confermata** — il de-risking migliora il DD in **12 casi su 12** e l'IRR in **0 su 12**. Costa 0,3-1,7 punti e taglia 0,2-20,9 punti di drawdown, monotono nella soglia. Il sizing di Kelly costa più del de-risking (3,1-5,5 punti): μ su 60 mesi è pro-ciclico |
| A5 ERC fra 4 stream scorrelati | 34 | **confermata** — correlazione media 0,024 raggiunta, Sharpe **1,19** contro 0,69 e DD −11,7% contro −50,3%, ma IRR netta 5,64% contro 9,88%. Lo Sharpe più alto della ricerca, −4,24 punti |
| A7 stabilità HRP contro min-variance | 35 | **confermata nel verso, sbagliata nella misura** — HRP 0,283 contro min-var 0,473, fattore **1,67** e non 3-10. HRP resta meno stabile di inverse-variance |
| A8 min-variance in leva 1,20× | 35 | **confermata** — 8,64% contro 10,88% (−2,24). La leva **distrugge lo Sharpe** che doveva monetizzare: 0,78 → 0,69. Nessuna leva sotto 3,00× pareggia; a 1,50× scatta il margin call (equity 2,3%) |
| A9 Kelly contro frazione fissa | 36 | **confermata, 4 casi su 4** — la frazione fissa vince sempre. Kelly non aggiunge informazione, aggiunge rotazione tassabile |
| A10 curva del prezzo del drawdown | 36 | **confermata** sull'esistenza del minimo interno, **sbagliata sulla posizione**: 40% sul cap-weighted, 20% sull'equal-weight, non 30-35%. La soglia efficiente dipende dal sottostante |
| B1 materie prime | 37 | **confermata** — trend following funziona lordo (5,31% contro 3,76% del buy&hold WTI) e muore netto: 3,75% contro 9,90% dell'azionario. Numeri comunque un **limite superiore**, il WTI spot ignora il roll |
| B2 valute carry e momentum | 37 | **confermata dopo la correzione di un bug** — alla prima esecuzione risultava falsificata (Sharpe 0,58, skew +1,81), ma `fill_value=0` fabbricava un EUR senza rischio di cambio prima del 1999. Corretto: Sharpe 0,25, skew −0,12, nessuna variante passa |
| B3 credito HY | 38 | **senza esito — non testabile**. `BAMLH0A0HYM2` si scarica solo per 3 anni (licenza ICE): 35 mesi contro i 30 anni necessari |
| B4 curva dei tassi | 38 | **confermata** — **12 inversioni su 13** seguite da un calo oltre il 15%, anticipo mediano 13 mesi, e la strategia perde 1,2-2,6 punti. Un segnale che ha ragione quasi sempre e costa comunque |
| B5 azionario internazionale | 39 | **confermata** — nessuna variante batte nemmeno l'equal-weight fra regioni (5,05% contro 6,74%), DSR 0,864 |
| B6 cripto universo esteso | 39 | **confermata** sul test (DSR 0,904), **sbagliata sulla prima clausola**: il CAGR del buy&hold sale invece di scendere (55,3% contro 22,6%), perché allargare ai simboli oggi quotati **aumenta** la sopravvivenza. Intervallo dello Sharpe [0,22 – 1,56] |
| B7 credito Baa−Aaa (sostituta di B3) | 38 | **confermata** — 8,48% walk-forward contro 10,56% del buy&hold, e perde in **ogni** configurazione della griglia. Divario in-sample/walk-forward 0,39 punti, non ≥1 come previsto |
| C1 cointegrazione | 40 | **confermata** — 130/1176 cointegrate in-sample (11,1% contro 5% atteso) ma solo **5,4% persiste** fuori campione, p = 0,476. Spread trading a −0,65% |
| C2 breadth | 40 | **confermata** — correlazione **0,830** col filtro di trend. Porta il DD da −83,7% a −29,3% e costa 4 punti |
| C3 momentum multi-orizzonte | 41 | **confermata** — **ogni** composito ha Sharpe più basso E turnover più alto del solo 12-2. Il solo 1m ha 9,08 rotazioni l'anno |
| C4 term structure VIX | 41 | **confermata** — direzione p = 0,535 (nessun potere), volatilità ρ = **+0,421** (p ≈ 10⁻¹⁷²). Finestra dentro l'holdout, dichiarata, nessun candidato ne esce |
| C5 premio di volatilità coperto | 42 | **confermata** — il coperto perde **5,91 punti** e **non accorcia la coda** (skew da −1,02 a −1,50). La sola assicurazione costa 4,24 punti di CAGR |
| C6 quattro pilastri CTA | 42 | **confermata** sul test, **sbagliata sulla seconda clausola**: correlazione media 0,189 come previsto, ma lo Sharpe combinato è **0,76 contro 0,95** del miglior singolo |
| **D1 data di partenza** | 43 | **FALSIFICATA** — ampiezza 0,56 punti contro i 3 previsti. Ma per **difetto della specifica**: 20 date di partenza con fine fissa condividono 33-52 anni su 52. Vedi D3. Risultato collaterale importante: contro l'equal-weight dello stesso universo i 3 candidati sono negativi in **60 casi su 60** |
| **D2 bootstrap a blocchi** | 43 | **FALSIFICATA** — H5 al **100° percentile** del nullo (+3,82% lordo contro 99° a 2,49%). Ma il nullo non tiene conto della selezione, e la stessa strategia fa **−1,20% netto**. Il premio è reale, l'investitore perde comunque |
| A6 scomposizione della perdita | 44 | **confermata** — quota fiscale massima **15,3%**, sotto il 25% che falsificava. Ma la clausola "oltre il 90%" regge solo per l'inverse-vol (91,9%): le altre stanno all'84-88%. I costi di transazione valgono lo **0,3%** del divario. Controprova: con imposte ZERO sul ribilanciamento l'allocazione resta sotto di 1,8-3,3 punti |
| A11 alpha di pareggio della sleeve | 45 | **confermata** — il decennale dovrebbe rendere **6,5-7,0 punti l'anno in più** (cioè 12,5-13% annuo per 64 anni) perché l'allocazione pareggi. Lo scarto del proxy **misurato** è 1,58 punti, non 0,3-0,8 come avevo assunto: il multiplo è 4,1-4,4×, sul bordo inferiore della banda prevista. Controprova: con la ricostruzione migliorata l'allocazione resta **−2,4/−3,4 punti** |
| A12 finestre mobili di 20 anni | 46 | **confermata** sul test (quote 35,5-48,4%, nessuna oltre metà né a zero) e **tutte e tre le clausole descrittive sbagliate**: l'ERC vince **48,4%** delle volte, non 15-35%; le vittorie non sono centrate sui mercati orso; l'ampiezza scende a 5,50 per il 60/40. Divario medio ERC **−0,37 punti**, non 3,63. Il criterio vero è **quando la finestra finisce**, non dove è centrata |
| **A13 rischio di sequenza** | 47 | **FALSIFICATA** — il segno è giusto (b(ultimi 3) negativo in 8 casi su 8) ma il rapporto è **1,21-2,71**, non ≥4, e cinque su otto stanno sotto 2. R² 0,28-0,33 invece di >0,5. Sulla finestra estesa la quota di vittorie **scende** a 13,3-31,1% invece di salire sopra il 50%: le 14 finestre recuperate perdono **0 su 14**. Il peso aritmetico del capitale è 9,5:1, ma sul **divario** fra allocazioni si cancella in buona parte |
| E0 cancello di calibrazione | 48 | **aperto** dopo due correzioni: scadenze al **terzo venerdì** (la correlazione passa da 0,850 a 0,975) e **IV = 0,85 × VIX**. Residui BXM +0,55 / PUT −0,72, **segni opposti**, che è la firma dello skew |
| E1 premio al rischio di varianza | 48 | **confermata** — VIX sopra la realizzata nell'**83,0%** dei mesi, scarto medio **+3,91** punti, **0 decenni su 4** con premio negativo. Entrambe le clausole descrittive centrate, unica volta in tutta la coda |
| **E2 comprare opzioni** | 49 | **FALSIFICATA** — 3 configurazioni su 4 hanno IRR positiva. Ma la condizione era **mal posta**: ho testato *cassa + opzione*, che per parità put-call è una posizione azionaria protetta, non una scommessa sulla volatilità. Nessuna si avvicina al benchmark |
| E3 vendere put cash-secured | 49 | **confermata** — Sharpe lordo 0,77 contro 0,71 come previsto, IRR netta **−4,98** punti (12 realizzi/anno → 52%). Skew da **−4,15 a −12,57**: più il premio sembra sicuro, più la coda è mostruosa |
| E4 covered call | 49 | **confermata**, ma solo dopo aver buttato il simulatore: col modello la +5% sembrava **+0,98 con DSR 0,997**, la prima promozione apparente in 49 giri. Contro gli indici CBOE reali l'inflazione da skew è **+0,55/+1,51/+2,56** crescente con la moneyness. Coi dati reali: **−2,92** |
| **E5 LEAPS come leva** | 49 | **FALSIFICATA** — 10,98% contro 9,64%, **+1,34**. Il finanziamento incorporato è **2,95%** contro il 5,90% del CFD. Ma DSR **0,000**, drawdown **−62,5%** contro −47,2%, direzione dell'errore ottimistica e non quantificabile senza un indice reale. Avevo sopravvalutato il drag fiscale del rollo annuale |
| E6 stress sui LEAPS | 52 | **confermata** — muore a un **rincaro del 10%** del premio d'ingresso (2 punti di nozionale, cioè lo spread normale di un'opzione lunga poco liquida). Ma regge a tutto il resto: implicita fino a **k = 1,15** e **17 finestre su 17** di 20 anni con il caso peggiore ancora positivo. Due clausole della predizione su tre erano sbagliate. Il vantaggio esiste ed è stabile nel tempo: sta dentro il costo di transazione dello strumento |
| H1 globale contro USA | 57 | **confermata** — S&P **+1,89** punti sui dati reali (SPY contro VT/ACWI/URTH, 2011-2026) e **+1,61** sul proxy lungo 1990-2026, cioè **+€567.187** su un PAC trentennale. Ma su 26 finestre decennali l'USA vince solo il **73%**, e le 7 finestre perse partono **tutte fra il 1995 e il 2001**. Il globale non riduce nemmeno il rischio: stessa volatilità, drawdown peggiore |
| **A14 sequenza sul livello** | 58 | **FALSIFICATA** — rapporto da **0,55 a 48,51**, minimo ben sotto 4, e R² fra 0,002 e 0,210 contro lo 0,6 previsto. Vero solo il verso sul PAC azionario: b(ultimi 3) **+0,137** e b(primi 3) **−0,034**, cioè un PAC preferisce partenza brutta e finale buono. **Terzo tentativo fallito di spiegare quali finestre favoriscono cosa** (46, 47, 58): linea chiusa, sostituita da A15 che calcola invece di stimare |
| G1 filtri di tendenza | 53 | **confermata** — nessuno batte il buy&hold. Il migliore perde **2,51** punti (EMA200+EMA21>EMA50, e vince perché ruota 0,19×/anno contro 1,3-2,2 degli altri), il peggiore 4,50. In cambio 18-40 punti di drawdown |
| **G2 momentum come veicolo** | 53 | **FALSIFICATA** — momentum in ETF UCITS **11,64%** contro cap-weight diretto in CGT **10,88%**: **+0,77**. Il risultato model-free è però un altro: a parità esatta di lordo, spostare la rotazione **dentro il fondo** vale **+2,77 punti**. Non promosso: il lordo (4,18 punti di premio) è più generoso degli indici momentum reali, manca il TER, e i parametri furono scelti al giro 05 |
| **BUG nel motore fiscale** | 53 | i lotti ETF non venivano ridotti quando si liquidavano quote per pagare le imposte: su 57 anni e 7 cicli di deemed disposal il portafoglio si azzerava. Corretto pro rata. **Il vantaggio del veicolo scende da +2,15 a +1,23** su 1990-2023 (+2,12 su 1969-2026: cresce con l'orizzonte) |
| **F1 rotazione top-1** | 50 | **FALSIFICATA da 1 cella su 9** — regioni top-1 mensile +0,30, ma su 4 asset con 894% di rotazione, e perde 3 punti contro il buy&hold USA. Le altre 8 celle perdono da 1,4 a 81 punti; sui 49 settori −6,5/−6,8 a ogni frequenza; cripto top-1 annuale **−96,3% di drawdown** |
| F2 griglia posizioni × frequenza | 50 | **confermata** — massimo a **top-5 annuale, 10,02%** contro 11,16% dell'equal-weight statico. Nessuna delle 15 celle lo batte. Da 1 a 5 posizioni valgono **+5,5 punti di IRR e +27 di drawdown**. Le clausole di monotonia erano sbagliate: la relazione è a campana |
| F3 sistema EMA giornaliero | 51 | **confermata** — batte il buy&hold su **1 asset su 10**, e quell'uno è LTC il cui B&H è −17%. Predizione sbagliata sul verso del lordo: il sistema **muore sul lordo** (0,75% contro 15,55% su QQQ), non sulle imposte |
| **F4 sistema EMA intraday** | 51 | **FALSIFICATA** — l'orario (1,12%) supera il giornaliero (0,30%). Ma le finestre sono **20 / 2,9 / 0,8 anni**: Twelve Data dà 5.000 barre e basta, quindi il confronto di CAGR fra righe misura il periodo, non il timeframe. Il meccanismo previsto si vede: **7,1 → 33,6 → 133,4** operazioni/anno, e a 15 minuti −18,65% contro +20,30% |
| F5 ablazione del sistema EMA | 51 | **confermata con margine enorme** — il **solo filtro di tendenza** ha aspettativa per operazione **13,321%** contro **0,564%** del sistema completo: rapporto **0,04**, cioè il sistema completo cattura un ventiquattresimo. Ingressi tattici e piano di uscita fanno entrare tardi e uscire presto |
| **D3 finestre di lunghezza fissa** | 59 | **confermata** — ampiezza **5,81-10,19 punti** su finestre decennali contro i **0,56** di D1: **18×**. La sovrapposizione media fra campioni passa da **85,5%** (D1) a **13,9%**. Sbagliata solo la clausola sul segno (30,4% invece di ≥33,3% per C1). Risultato collaterale decisivo: **allungando l'orizzonte tutti e tre peggiorano** — H5 da 67,4% a 38,9% di vittorie, C1 da 30,4% a **0/36**. Le 4 peggiori finestre di H5 contengono tutte il 2008 |
| **L1 ritardo in giorni** | 73 | **FALSIFICATA su entrambi i rami**: il margine **non e' monotono** e il top-5 ritardato di **20 giorni passa da −0,87 a +0,86**, uno scarto di 1,73 nella direzione opposta. Ma quel +0,86 e' **una cella su dieci** e **non passa il cancello G1** (serve +1,00 come mediana; la mediana dei cinque ritardi e' −0,65): registrato come domanda (voce L4), non come candidato. Quello che regge: **il costo di ordinare il giorno dopo e' 0,08 punti** sul top-10 e 0,22 sul top-5 — il ribilanciamento a mezzanotte non nasconde niente. E l'oscillazione fra un ritardo e l'altro (±0,5) conferma dal lato dei giorni la dispersione che il giro 59 aveva visto dal lato delle finestre |
| **K4 regola per l'holdout** | 72 | **confermata** — **zero candidati su dodici** passano i quattro cancelli, e l'holdout resta sigillato. Sbagliata la seconda clausola: il cancello piu' selettivo e' **G1 margine (12/12 eliminati)**, non il calendario (7/12) — ma G4 e' poco selettivo solo perche' **cinque candidati mensili lo passano per costruzione**; fra i **sette annuali ne elimina sei**. Nessuno arriva a un punto di margine: il migliore e' **momentum top-5 mensile a +0,56**, che passa G2 (DSR 0,971) e G4 e fallisce G3 per **sette decimi di punto** (66% contro 66,7%). **La regola e' ora in vigore** |
| **K3 vantaggio del veicolo** | 71 | **FALSIFICATA** — (a) spostare la rotazione dentro il fondo vale **+3,43**, sopra la soglia di 2,77. Ma **non per la rotazione**: scomposto, la correzione della rotazione vale **+0,00** (2,676× → 2,828×, effetto −0,005 punti) e i **+0,66** vengono dai dividendi, che il giro 53 non tassava al detentore diretto. Motivo preciso: chi realizza il 22% al mese ha la base imponibile **gia' azzerata in continuo** — la correzione conta per i portafogli lenti (1,35 punti sull'equal-weight al giro 63) e non per quelli veloci. (b) il vantaggio delle **azioni dirette sull'ETF** e' **+1,09**, dentro i limiti e coerente con la serie registrata (+0,34 su 1990-2023, +0,56 su 1990-2026): cresce con l'orizzonte. **Il wrapper aiuta solo se ruoti**: +0,64 all'ETF sul momentum, +1,09 al diretto sul cap-weight |
| **K2 PAC interrotto** | 70 | **FALSIFICATA**, su una lettura che ho risolto contro di me: sulla **mediana** delle 64 finestre lo scarto di IRR resta a **0,126** punti, ma su **ogni coppia (k, finestra)** arriva a **1,019** (50 coppie su 1.152 sopra 0,5). Il risultato vero: **l'IRR e' quasi cieca**. Saltare 24 versamenti costa **−8,66% di montante e +0,021 di IRR**; riscattare il 30% costa **−22,51% di montante e −0,016 di IRR**. Sbagliate due clausole: il calo del montante va da **−21,13% a −4,05%** (previsto −8/−12: era la media, non l'intervallo) e il riscatto tocca l'IRR di **−0,072** al massimo, non −0,5. L'effetto sull'IRR **cambia segno al sesto anno**, che e' il profilo del giro 61 visto dal lato dei versamenti |
| **K1 conto in valuta** | 69 | **confermata** — il margine si sposta al massimo di **0,25 punti** e la volatilita' in euro e' piu' alta ovunque: **nessun verdetto dei giri 30-68 cambia**. Ma il **livello** si': per un investitore in euro l'azionario USA ha reso **0,46-0,77 punti l'anno in meno** di quanto tutto il progetto avesse scritto. Sbagliate due clausole su tre, entrambe per aver sovrastimato la taglia (volatilita' **+0,46/+1,10** invece di +2/+5). Il meccanismo previsto e' centrato: lo spostamento del margine cresce con la rotazione (0,00× → −0,06; 0,79× → +0,14; 2,81× → +0,25), corr **+0,985** ma su soli **3 punti** |
| **D10 calendario del ribilanciamento** | 68 | **confermata** — mediana degli extra **negativa per tutte** e solo **10/48** configurazioni battono il benchmark. Sbagliata la clausola sull'ampiezza (2/4 sopra 2 punti), e il modo in cui e' sbagliata e' il risultato: **l'ampiezza scala con la concentrazione** — equal-weight **0,14%**, top-25 0,90%, top-10 2,21%, top-5 **3,65%**. Un portafoglio passivo non ha il problema; il grado di liberta' del calendario esiste solo per chi seleziona. **Il +1,51 del giro 65 era gennaio, il secondo mese migliore su dodici: la mediana e' −0,46.** Registro cresciuto di **48** tentativi, non di 4 |
| **J1 statistical jump model** | 67 | **confermata** — nessuna delle 21 configurazioni batte il buy&hold (migliore **−1,63** a λ=200) e la **long/short perde in 21 su 21**, fino a IRR **−0,45%** e **−2,37%** in valore assoluto. Sbagliata la clausola sulla correlazione: col MA10 **crolla da 0,610 a 0,006** al crescere di λ. Il risultato vero: **la strategia migliora quanto meno la si ascolta** — a λ=200 cambia stato una volta ogni 17 anni, sta investita l'84,4% del tempo e il divario si chiude da −4,77 a −1,63. λ **controlla davvero l'aliquota** (da 2,74× a 0,88× fra λ=10 e λ=25, 52%→33%), ma cio' che si compra con la persistenza e' il diritto di stare fermi, e stare fermi al 100% si chiama buy&hold |
| **D9 vincolo di rotazione sotto la soglia** | 66 | **confermata** — la vincolata (budget 0,95×/anno, ribilanciamento parziale) batte la libera in **3 celle su 4**, e **nessuna** supera l'equal-weight annuale. Sbagliata la taglia: guadagno medio **+0,64** invece di +1/+3. Il meccanismo e' isolato con precisione: guadagnano le due celle che **riattraversano la soglia** (top-3 e top-5, 52%→33%: +0,79 e +1,02), mentre il **top-10, gia' al 33%, PERDE −0,09** — vincolare di per se' non giova. Rinunciare all'ultimo 10% di rotazione costa **0,11-0,59 punti di CAGR lordo** e vale **19 punti di aliquota** |
| **D8 verdetti dentro la correzione** | 65 | **FALSIFICATA** — cambia segno il **57,1%** (4 su 7), sopra la soglia del 50%. Centrata la clausola "fra 4 e 10 verdetti" (7). I due effetti **non si compensano**: nessuno dei sette salta di aliquota, quindi il benchmark si muove piu' dei candidati. Tre diventano positivi contro l'EW **mensile**, ma contro l'EW **annuale** due tornano negativi e il terzo (momentum top-10 annuale, **+0,33**) ha DSR **0,9424**, sotto soglia: **promozioni zero**. Il ramo DSR e' scattato ma la sua conseguenza no — la regola di STATE.md ha due condizioni. Trovato un parametro libero mai contato: **il calendario del ribilanciamento vale 3,43 punti** (top-5 annuale: +1,51 a gennaio, −1,92 ogni 12 mesi dall'inizio) → voce D10 |
| **D7 F2 con benchmark corretto** | 64 | **FALSIFICATA su entrambi i rami**, e nel verso opposto: il top-5 annuale non sale sopra l'equal-weight, **scende a −1,92** (era −1,14). Motivo: con la rotazione vera passa da **0,83× a 1,022×** e **scavalca la soglia del 100%**, pagando il **52%** invece del 33% — un gradino, non un aggiustamento. DSR **0,9743** su N=15 (secondo ramo scattato) ma **0,7691** sul registro cumulato, che e' la soglia del progetto, e il candidato perde comunque contro il suo benchmark: **promozioni zero**. La conclusione di F2 regge; cade la clausola "a campana": con la rotazione vera la griglia annuale e' **monotona crescente** (4,84 → 9,65), il massimo e' a **top-25** |
| **D6 rotazione sottostimata** | 63 | **FALSIFICATA** — **un verdetto si ribalta** (tilt low-vol top-25 contro cap-weight: da **+0,16 a −0,07**, cioe' la correzione lo peggiora). Tutte e tre le clausole sbagliate: solo **1/9** ha rotazione vera oltre il triplo, correzione media **0,32** punti invece di >0,5. E la tesi su cui la voce era nata cade: l'errore ha **DUE versi** — `wbacktest` sottostima (4/9), `round31/32` **sovrastimano** contando il drift come scambio (5/9). Equal-weight annuale: rotazione vera **0,071×** contro 0,239× e 0,251× delle due convenzioni sbagliate |
| **D5 quota di vittorie ingannevole** | 62 | **FALSIFICATA** — scarto mediana-media positivo solo per il **28,6%** dei 21 candidati (soglia di falsificazione 60%), e **il segno e' opposto** a quello previsto: domina la coda DESTRA, non la sinistra. Il momentum top-3 vince il 45,7% delle finestre e rende **+1,80%** perche' il massimo e' +14,63%. Un solo caso ingannevole su 21 (low-vol top-10: vince 60,9%, rende −0,59%): **H5 al giro 59 era isolato, le quote di vittorie di F1/E6/H1 NON vanno rilette**. Il fisco non crea code: sposta il livello — corr(rotazione, media) **−0,600**, corr(rotazione, scarto) −0,265 |
| **A15 peso analitico di ciascun anno** | 61 | **confermata** sul test (monotono in **80/80** finestre storiche, rapporto minimo 5,61 contro la soglia di 4) e **sbagliata sul livello**: il rapporto ultimi/primi triennio va da **10,27 al 2%** a **5,61 al 12%**, mediana storica **5,91** — non il 9,5:1 previsto. Il risultato vero e' che erano **tre quantita' diverse**: aritmetica pura **9,50**, capitale esposto **24,72**, sensibilita' dell'IRR **6,91**. I giri 47 e 58 cercavano un bersaglio che il meccanismo non produce. Errore vs differenze finite **3,5e-05** |
| **D4 scelta del benchmark** | 60 | **confermata**, e piu' estrema del previsto: il premio di equal-weighting spiega **398%** del margine di H5 (**263%** sulla variante implementabile, **40%** sulla piu' avversa) — la soglia di falsificazione di 1/3 non e' raggiunta in **nessuna** delle tre varianti. Sbagliate due clausole: solo **1 candidato su 3** e' positivo contro il cap-weight, e il premio vale **0,99** punti come portafoglio, non 2-3. **Il contributo della selezione e' −0,61**: il momentum settoriale sceglie peggio del caso dentro lo stesso universo |
| **DIFETTO in `wbacktest`** | 60 | la rotazione e' calcolata come \|W_t − W_{t−1}\|, che su **pesi costanti fa zero**: l'equal-weight del giro 43 ribilanciava ogni mese **gratis e non tassato**. La rotazione vera e' 0,20×/anno e vale **1,35 punti di IRR** (11,16% → 9,81%). Colpisce ogni valutazione a pesi statici o lenti. Nuova voce D6 per rimisurarle |
| **LIMITE del motore fiscale, misurato** | 59 | il motore tiene **un solo costo fiscale aggregato** e realizza pro quota, mentre nella realtà si vendono posizioni specifiche e vendere un perdente cristallizza una minusvalenza. Effetto misurato su un motore per posizione scritto apposta: **da +0,10 a +0,41 punti di IRR a favore delle strategie che ruotano** (+0,29 al 52% sul top-5). Controllo a 1 asset: identico a 6 decimali. **Nessun verdetto del progetto cambia**: il divario più stretto mai registrato è 1,14 punti |


---

## Note sui dati emerse durante l'esecuzione

- **Oro: nessuna serie investibile ottenibile.** FRED ha ritirato le serie LBMA
  (`GOLDAMGBD228NLBM` e `GOLDPMGBD228NLBM` danno 404) e offre solo indici di
  prezzo alla produzione, che non sono comprabili. L'oro tokenizzato PAXG su
  OKX ha 286 candele, troppo poche. Le voci che assumono una sleeve d'oro
  vanno eseguite senza, dichiarandolo.
- **Materie prime: idem.** Serve un indice total return che replichi il
  rolling dei futures (GSCI, Bloomberg Commodity). Il petrolio spot di FRED e'
  un prezzo: chi compra petrolio paga il roll, storicamente la componente
  dominante del rendimento. Usarlo sovrastimerebbe la classe.
- **Cripto: ora 8 asset** (aggiunto LINK, dal 2018). Rilevante per B6.
- **L'ambiente Python non sopravvive al riavvio del container**, i dati in
  `quant/data/` sì (sono versionati). Al giro 31 numpy/pandas/scipy erano spariti.
  Rimedio: `pip install numpy pandas scipy xlrd openpyxl statsmodels` prima di
  eseguire, senza riscaricare niente.

---

## Voci aggiunte durante l'esecuzione

**A6 — Il ribilanciamento e' l'unico costo, o serve anche il premio?** ✔ eseguita (giro 44)
Il giro 30 mostra che ogni allocazione multi-classe perde contro l'azionario
puro netto imposte, ma con turnover bassissimo (0,13-0,17 volte l'anno). Se il
costo non e' la rotazione, e' la composizione: il decennale rende meno.
Scomporre l'IRR persa in (a) minor rendimento atteso della sleeve difensiva e
(b) imposte sul ribilanciamento.
*Predizione*: oltre il 90% della perdita viene da (a), non da (b).
*Falsificata se*: la componente fiscale supera il 25%.

**A7 — La tesi vera di HRP: stabilità contro il min-variance** ✔ eseguita (giro 35)
Il giro 31 ha misurato che HRP è **meno** stabile dell'inverse-variance (0,283
contro 0,109 di movimento medio dei pesi). Ma la rivendicazione del paper è contro
il **min-variance di Markowitz**, che inverte la covarianza ed è instabile per
costruzione con 49 asset e 60 mesi di storia. Quel confronto non l'ho eseguito
perché il min-variance è A3. Da fare **dopo** A3, riusando i pesi già calcolati lì.
*Predizione*: HRP risulta 3-10 volte più stabile del min-variance, cioè la tesi del
paper regge sul suo bersaglio dichiarato — e resta comunque irrilevante per l'IRR
netta, perché entrambi perdono contro il cap-weighted.
*Falsificata se*: HRP non è più stabile del min-variance.

**A8 — Monetizzare lo Sharpe: min-variance portato in leva a pari volatilità** ✔ eseguita (giro 35)
Il giro 32 ha trovato il caso più pulito finora di uno Sharpe migliore che non
serve a niente: min-variance 0,78 contro 0,74 del cap-weight, e IRR netta 2,65
punti sotto. Il ponte fra le due cose è la leva — servirebbe 15,8/13,2 = **1,20×**
per pareggiare la volatilità. Da testare esplicitamente con il finanziamento a
benchmark+3% e il margine ESMA già modellati al giro 07, invece di lasciarlo a un
conto a mente.
*Predizione*: la leva 1,20× recupera parte del divario ma non lo chiude — il costo
di finanziamento (rf medio 4,45% + 3% = 7,45% sul 20% preso a prestito) più le
imposte sul ribilanciamento più frequente lasciano il risultato sotto il
cap-weight di almeno 1 punto. Il vantaggio di Sharpe del min-variance è troppo
piccolo (0,04) per sopravvivere a uno spread di finanziamento del 3%.
*Falsificata se*: IRR netta ≥ cap-weight.
*Nota di soglia*: perché la leva paghi serve che il rendimento in eccesso del
min-variance per unità di leva superi lo spread. Con 9,90% di CAGR e 7,45% di
costo marginale il margine lordo sul 20% preso a prestito è ~0,49 punti l'anno,
e il turnover del ribilanciamento in leva ne consuma una parte. È un test stretto,
ed è il motivo per cui va misurato invece che assunto.

**A9 — Kelly aggiunge qualcosa a una frazione fissa?** ✔ eseguita (giro 36)
Il giro 33 mostra che il cap a 1,0 morde il 37-68% del tempo e che l'esposizione
media di quarto-Kelly è 0,66-0,70. Quindi quarto-Kelly potrebbe essere, in
pratica, "stai investito al 67% e basta", con in più il rumore della stima e la
rotazione tassabile che ne deriva. Confronto diretto: esposizione **costante** pari
alla media realizzata di ogni configurazione Kelly, contro la configurazione Kelly
stessa, stesso sottostante e stessa finestra.
*Predizione*: la frazione fissa batte Kelly in IRR netta in almeno 3 casi su 4,
perché ha lo stesso profilo di esposizione media senza pagare la rotazione, e
perché μ stimato su 60 mesi è pro-ciclico (basso proprio dopo i crolli, cioè quando
i rendimenti attesi sono alti).
*Falsificata se*: Kelly batte la frazione fissa in almeno metà dei casi.

**A10 — Il prezzo dell'assicurazione sul drawdown, come curva** ✔ eseguita (giro 36)
Il giro 33 dà tre punti isolati (soglie 10/20/30%) e mostra un gradiente monotono:
a 30% si pagano 0,4 punti di IRR per 14 di drawdown, a 10% se ne pagano 1,0-1,7
per 20. Da tracciare come curva completa, soglie dal 5% al 50% a passi di 5, su
entrambi i sottostanti, misurando **punti di IRR ceduti per punto di drawdown
evitato**. Non è un tentativo di battere il benchmark: è la quantificazione di un
trade-off che l'investitore deve poter decidere.
*Predizione*: il rapporto costo/beneficio è peggiore alle soglie basse e migliora
monotonamente fino a circa il 30-35%, oltre il quale la soglia scatta troppo di
rado per proteggere. Esiste quindi un minimo interno, intorno al 30%.
*Falsificata se*: il rapporto è piatto (nessun minimo interno distinguibile) o
monotono su tutto l'intervallo.

**B7 — Credito con una serie a storia lunga: spread Baa−Aaa di Moody's (1919→)** ✔ eseguita (giro 38)
Nata perché B3 è risultata **non testabile sulla serie dichiarata**: le serie ICE
BofA (`BAMLH0A0HYM2`) sono scaricabili solo per gli ultimi 3 anni, licenza ICE.
Lo spread Baa−Aaa è il *default spread* classico della letteratura (Fama-French
1989) e ha 107 anni di storia. Stessa meccanica di B3: si esce dall'azionario
quando lo z-score dello spread supera una soglia, z-score su finestra mobile,
segnale ritardato di un mese, soglia scelta walk-forward.
*Predizione*: lo spread di default ha potere predittivo documentato sui rendimenti
azionari futuri, ma è un segnale **di lungo periodo e a bassa frequenza** — dice
che i rendimenti attesi sono alti quando lo spread è largo, cioè dopo i crolli.
Usarlo come segnale di uscita fa quindi l'opposto di quel che dovrebbe: vende dopo
il calo. La versione walk-forward resterà sotto il buy&hold netto imposte, e il
divario fra il miglior parametro in-sample e quello preso walk-forward sarà di
almeno 1 punto.
*Falsificata se*: la versione walk-forward batte il buy&hold netto imposte.

**D3 — Dispersione su finestre di lunghezza fissa, non su date di partenza**
Nata perché **D1 è stata falsificata per un difetto della sua stessa specifica**.
"Far partire il campione in 20 anni diversi" con la fine sempre al 2026 produce 20
campioni che condividono 33-52 anni su 52: la dispersione misurata (0,17-0,56
punti) è piccola per costruzione, non perché il risultato sia stabile. Il test che
risponde davvero alla domanda usa **finestre mobili di lunghezza fissa** (10 e 20
anni, passo 1 anno), che si sovrappongono molto meno e coprono regimi diversi.
*Predizione*: su finestre di 10 anni la dispersione dell'extra-rendimento supera 4
punti e il segno cambia in almeno un terzo delle finestre; su finestre di 20 anni
la dispersione resta sopra 2 punti. Cioè: quello che D1 non ha visto c'era, ed era
nascosto dalla sovrapposizione dei campioni.
*Falsificata se*: la dispersione su finestre di 10 anni resta sotto 2 punti.

**D4 — Il benchmark giusto cambia il verdetto?**
Il giro 43 ha usato come benchmark l'**equal-weight dei 49 settori**, cioè lo stesso
universo su cui la strategia sceglie, e i tre candidati risultano negativi in 20
date di partenza su 20 — mentre contro il PAC cap-weighted H5 risultava +2,95.
Le due cose non sono in contraddizione (equal-weight e cap-weight rendono diverso),
ma la scelta del benchmark vale più di qualunque parametro provato finora.
Da misurare esplicitamente: gli stessi tre candidati contro tre benchmark diversi
— cap-weighted, equal-weight dello stesso universo, e equal-weight ribilanciato
annualmente — riportando quanto del margine è selezione di titoli e quanto è
semplicemente il premio dell'equal-weighting.
*Predizione*: contro il cap-weighted i candidati sembrano positivi, contro
l'equal-weight dello stesso universo diventano negativi, e la differenza fra i due
benchmark (~2-3 punti) spiega **più della metà** del margine apparente. Cioè quasi
tutto quel che sembrava alfa era il premio di equal-weighting.
*Falsificata se*: la differenza fra i benchmark spiega meno di un terzo del margine.

**A11 — Di quanto dovrebbe rendere di più la sleeve difensiva per pareggiare?** ✔ eseguita (giro 45)
Il giro 44 attribuisce l'84-92% della perdita delle allocazioni multi-classe alla
**composizione**, e la controprova mostra che anche con imposte zero sul
ribilanciamento restano 1,8-3,3 punti sotto l'azionario. Ma il decennale usato è
una **ricostruzione a duration costante da DGS10**, che sottostima convessità e
rolldown: parte del divario potrebbe essere un difetto del proxy, non un fatto.
Da calcolare al contrario: quanti punti di rendimento annuo in più dovrebbe avere
la sleeve obbligazionaria perché ogni allocazione pareggi l'azionario netto
imposte, e confrontare quel numero con lo scarto plausibile fra un indice
obbligazionario vero e questa ricostruzione (in letteratura 0,3-0,8 punti l'anno).
*Predizione*: il pareggio richiede oltre 3 punti l'anno in più sulla sleeve
obbligazionaria per ERC e inverse-vol, cioè da 4 a 10 volte lo scarto plausibile
del proxy. Il difetto di ricostruzione quindi **non** spiega il divario, e la
conclusione del giro 44 regge anche con un indice obbligazionario vero.
*Falsificata se*: il rendimento aggiuntivo richiesto sta sotto 1 punto l'anno per
almeno una delle quattro allocazioni, cioè dentro l'incertezza del proxy.

**A12 — In quante finestre di 20 anni l'allocazione multi-classe avrebbe vinto?** ✔ eseguita (giro 46)
I giri 44 e 45 concludono che il multi-classe perde 2,4-3,9 punti contro l'azionario
puro, ma su **una sola finestra**: 1962-2026, che contiene il più lungo mercato toro
obbligazionario della storia *e* un premio azionario altissimo. Una media su 64 anni
non dice a un investitore cosa rischia in trent'anni. Da misurare su **finestre
mobili di 20 anni, passo 1 anno**, con la ricostruzione migliorata del giro 45: in
quale frazione delle finestre ERC, inverse-vol, 60/40 ed equal-weight battono
l'azionario netto imposte, e quanto valgono il migliore e il peggiore caso.
*Predizione*: il multi-classe vince in una minoranza di finestre — fra il 15% e il
35% — e sono tutte e sole quelle centrate sui due mercati orso lunghi (1969-1982 e
2000-2012). L'ampiezza fra la finestra migliore e la peggiore supera **6 punti**,
cioè è più grande del divario medio, e quindi la conclusione "l'azionario puro
vince" è vera in media e falsa in una finestra su quattro.
*Falsificata se*: il multi-classe vince in più della metà delle finestre, oppure in
nessuna.

**A13 — Per un PAC conta la fine, non il centro: il rischio di sequenza** ✔ eseguita (giro 47)
Il giro 46 ha trovato che le finestre in cui il multi-classe batte l'azionario sono
**tutte e sole quelle che finiscono fra il 2002 e il 2016**, non quelle centrate sui
mercati orso come avevo previsto. Il meccanismo proposto è il **rischio di sequenza**:
dopo vent'anni di versamenti il capitale è al massimo, quindi i rendimenti degli
ultimi anni pesano su una somma enorme e quelli dei primi su quasi niente. Da
misurare direttamente invece di dedurlo: (i) regressione del divario di ogni
finestra sul rendimento azionario degli **ultimi 3 anni** della finestra contro
quello dei **primi 3**; (ii) la stessa cosa con la ricostruzione obbligazionaria
**semplice**, che copre 1962-2026 e recupera le 12 finestre perse per la mancanza
del DGS2, incluse quelle centrate sul mercato orso 1969-1982 che il giro 46 non ha
potuto testare.
*Predizione*: il coefficiente sugli ultimi 3 anni è negativo, di modulo almeno
**4 volte** quello sui primi 3, e da solo spiega oltre metà della varianza del
divario fra finestre. Sulla finestra estesa 1962-2026 la quota di vittorie del
multi-classe sale sopra il 50%, perché si aggiungono le finestre che finiscono nel
1974-1982.
*Falsificata se*: i due coefficienti hanno modulo comparabile (rapporto sotto 2), o
se il segno di quello sugli ultimi 3 anni è positivo.

**A14 — Rischio di sequenza sul LIVELLO, non sul divario** ✔ eseguita (giro 58)
Il giro 47 ha falsificato A13 e ha mostrato dove sbagliavo: il peso del capitale in
un PAC ventennale è **9,5:1** fra ultimi e primi tre anni (aritmetica pura), ma il
rapporto fra i coefficienti sul **divario** fra due allocazioni è solo 1,2-2,7:1.
Le due affermazioni sono diverse e le avevo confuse: il divario è la differenza fra
due montanti che percorrono lo stesso sentiero di prezzi, quindi il peso del
capitale si cancella in buona parte. Da rifare la stessa regressione sul **livello**
dell'IRR di ciascun PAC (azionario puro e ogni allocazione, separatamente), invece
che sulla differenza.
*Predizione*: sul livello il rapporto |b(ultimi 3)| / |b(primi 3)| sale sopra **6**
e l'R² dei soli ultimi tre anni supera **0,6**, avvicinandosi al 9,5:1 aritmetico;
entrambi i coefficienti sono **positivi** (buoni rendimenti a qualunque punto del
piano aiutano il montante), a differenza del divario dove hanno segni opposti.
*Falsificata se*: il rapporto sul livello resta sotto 4, cioè non è
significativamente più grande di quello sul divario — nel qual caso la mia
spiegazione del giro 47 è sbagliata quanto quella del giro 46 e il meccanismo va
cercato altrove.

---

## E. Opzioni — comprare e vendere

Finora le opzioni sono entrate solo come **indici CBOE già confezionati** (BXM, PUT,
CNDR, CLL, PPUT ai giri 27 e 42). Non ho mai prezzato un'opzione: non ho catene di
strike, quindi non ho mai potuto scegliere scadenza, moneyness o struttura.

**Cosa posso costruire.** Black-Scholes con il **VIX come volatilità implicita**,
sul percorso dell'indice azionario (Ken French daily, 1926→) e con il risk-free da
DFF. Il VIX parte dal 1990: **36 anni, ~430 scadenze mensili**.

**Il limite, dichiarato prima di qualunque numero: non ho lo skew.** Il VIX è un
tasso di variance swap a 30 giorni, uno solo; usarlo per ogni strike equivale a
ipotizzare volatilità piatta, mentre sull'S&P le put OTM trattano *sopra* il VIX e
le call OTM *sotto*. Le direzioni dell'errore sono note e opposte:

| struttura | effetto della vol piatta |
|---|---|
| vendere put OTM | premio incassato **sottostimato** → risultato **conservativo** |
| comprare put OTM | costo **sottostimato** → risultato **ottimistico** |
| vendere call OTM | premio **sovrastimato** → risultato **ottimistico** |
| deep ITM (LEAPS) | costo **sottostimato** → risultato **ottimistico** |

Ogni voce sotto va letta con la sua direzione di errore accanto.

**E0 — Cancello di calibrazione (non è un'ipotesi, è la condizione per fidarsi)** ✔ eseguita (giro 48)
Prima di qualunque test, il simulatore deve **riprodurre gli indici CBOE reali**:
un buy-write ATM mensile simulato contro **BXM**, e una put cash-secured ATM
mensile simulata contro **PUT**, sulla finestra comune.
*Condizione*: scarto di CAGR entro **1,5 punti** e correlazione dei rendimenti
mensili sopra **0,90** per entrambi. Se il cancello non si apre, tutte le voci E
sono dichiarate **non affidabili** e riportate come tali, non cancellate.

**E1 — Il premio al rischio di varianza, misurato** ✔ eseguita (giro 48)
VIX contro volatilità realizzata dei 21 giorni successivi, 1990-2026. Non è una
strategia: è il meccanismo che decide il segno di tutto il resto del gruppo E.
*Predizione*: il VIX supera la volatilità realizzata successiva in oltre il **75%**
dei mesi, con scarto medio di **3-4 punti di volatilità**. È il motivo per cui
vendere opzioni ha rendimento atteso lordo positivo e comprarle negativo.
*Falsificata se*: la quota sta sotto il 60%, oppure lo scarto medio è negativo.

**E2 — Comprare opzioni sistematicamente** ✔ eseguita (giro 49)
Long call e long put a 30 giorni, ATM e 5% OTM, rollate ogni mese.
*Predizione*: **ogni** configurazione ha IRR netta negativa; le put perdono più
delle call, perché al premio di varianza si somma la deriva positiva del
sottostante. La perdita annua è dell'ordine del premio di varianza moltiplicato
per l'esposizione vega.
*Falsificata se*: una qualunque configurazione long ha IRR netta positiva.
*Direzione dell'errore*: ottimistica sulle put OTM (costo sottostimato).

**E3 — Vendere put cash-secured contro il buy&hold azionario** ✔ eseguita (giro 49)
Put ATM e 5% OTM mensili, interamente collateralizzate in liquidità (nessuna leva).
*Predizione*: Sharpe **lordo superiore** al buy&hold azionario, come mostra
l'indice PUT del CBOE, ma **IRR netta inferiore**: ogni scadenza è un realizzo,
quindi 12 eventi fiscali l'anno contro un unico realizzo differito di 34 anni del
buy&hold. Il differimento vale più del premio.
*Falsificata se*: IRR netta > buy&hold azionario.
*Direzione dell'errore*: conservativa (premio sottostimato sulle put OTM).

**E4 — Covered call su un PAC azionario** ✔ eseguita (giro 49)
Call vendute mensilmente a moneyness 0%, +2%, +5% sul portafoglio azionario.
*Predizione*: più la call è OTM, più piccoli sono **sia** la riduzione di
volatilità **sia** il costo in IRR; nessuna configurazione batte il buy&hold; la
versione ATM perde di più, perché tronca il rialzo proprio nei mesi che fanno il
rendimento di lungo periodo.
*Falsificata se*: una qualunque configurazione batte il buy&hold netto imposte.
*Direzione dell'errore*: ottimistica (premio delle call OTM sovrastimato).

**E5 — LEAPS come leva a buon mercato** ✔ eseguita (giro 49)
Il giro 35 (A8) ha mostrato che la leva via CFD a benchmark+3% distrugge il
vantaggio di Sharpe che doveva monetizzare, e che a 1,5× scatta la chiusura
forzata. Una call deep ITM a 12 mesi incorpora un finanziamento vicino al
risk-free, **non ha margin call** e ha perdita massima pari al premio. Da testare a
moneyness 80% e 90%, rollata annualmente.
*Predizione*: il finanziamento incorporato è effettivamente più a buon mercato di
rf+3%, ma il rollo annuale realizza la plusvalenza **ogni anno** al 33%, contro il
differimento trentennale del buy&hold, e questo drag fiscale supera il risparmio di
finanziamento. IRR netta sotto il buy&hold.
*Falsificata se*: IRR netta ≥ buy&hold azionario.
*Direzione dell'errore*: ottimistica (costo del deep ITM sottostimato).

---

## F. Rotazione concentrata e il sistema EMA 9/21/50/200

Due richieste distinte. La prima: **prendere il migliore** invece di un paniere —
rotazione settoriale top-1 sulla base del periodo precedente, su mercati e
frequenze diverse. La seconda: il sistema a quattro EMA di uso comune fra i
trader, con le sue regole di ingresso e di uscita, applicato a mercati e
**timeframe** diversi.

**Il sistema EMA, come lo implemento** (dalle regole dell'immagine, verbatim):
ingresso solo se prezzo sopra EMA200 **e** EMA21 sopra EMA50; il prezzo deve
ritracciare verso la EMA21; il volume deve **calare** durante il ritracciamento;
si compra su candela rialzista vicino alla EMA21. Uscita: stop iniziale sotto il
minimo del ritracciamento, presa di profitto parziale (metà) a 1:2 rischio/rendimento,
stop a pareggio sul resto, trailing sulla EMA21, uscita totale su chiusura sotto
la EMA50. Le regole non specificano lo stop iniziale: lo fisso al minimo delle
ultime 10 barre e lo dichiaro.

**F1 — Rotazione top-1 sul migliore del periodo precedente** ✔ eseguita (giro 50)
49 settori USA, 5 regioni, 8 cripto. Ribilanciamento annuale, trimestrale e
mensile, con lookback pari al periodo precedente.
*Predizione*: il top-1 è **peggiore** del top-10 già testato (H5) e peggiore
dell'equal-weight del proprio universo, perché concentrare aggiunge varianza senza
aggiungere rendimento atteso — il segnale non è abbastanza forte da giustificare
una posizione sola. La versione annuale è la meno peggio perché è la meno tassata.
*Falsificata se*: una qualunque configurazione top-1 batte l'equal-weight del
proprio universo netto di imposte.

**F2 — La curva del numero di posizioni e della frequenza** ✔ eseguita (giro 50)
Griglia completa: 1, 3, 5, 10, 25 posizioni × ribilanciamento mensile,
trimestrale, annuale, sui 49 settori. Misura il compromesso fra concentrazione e
rotazione invece di provarne due punti.
*Predizione*: l'IRR netta è **monotona crescente** nel numero di posizioni e
**decrescente** nella frequenza di ribilanciamento; la cella migliore è quella più
diversificata e meno frequente, cioè quella più vicina al buy&hold. Il massimo
della griglia non batte l'equal-weight statico.
*Falsificata se*: il massimo della griglia sta a meno di 5 posizioni, oppure batte
l'equal-weight statico.

**F3 — Il sistema EMA 9/21/50/200 su base giornaliera** ✔ eseguita (giro 51)
QQQ e AAPL (Twelve Data, OHLCV) e le 8 cripto OKX. Serve OHLCV vero: volume per il
filtro sul ritracciamento, massimi e minimi per stop e target.
*Predizione*: lordo positivo sugli asset in tendenza (cripto, QQQ), perché è un
sistema di trend following e quello è il periodo giusto; ma 20-60 operazioni
l'anno portano l'aliquota al 52%, e netto di costi e imposte finisce **sotto il
buy&hold su ogni asset**.
*Falsificata se*: l'IRR netta batte il buy&hold su almeno metà degli asset.

**F4 — Lo stesso sistema su timeframe intraday** ✔ eseguita (giro 51)
QQQ a 1 ora e a 15 minuti, contro la versione giornaliera.
*Predizione*: accorciando il timeframe il vantaggio lordo per operazione si
restringe verso il costo mentre il numero di operazioni esplode; il risultato netto
è **monotonicamente peggiore** passando da giornaliero a orario a 15 minuti.
*Falsificata se*: un timeframe intraday batte la versione giornaliera netto di
costi e imposte.

**F5 — Quale pezzo del sistema fa il lavoro?** ✔ eseguita (giro 51)
Ablazione: (a) sistema completo, (b) senza il filtro sul volume, (c) senza il
requisito di ritracciamento, (d) solo il filtro di tendenza (prezzo sopra EMA200 e
EMA21 sopra EMA50, dentro o fuori), (e) buy&hold.
*Predizione*: il **solo filtro di tendenza** cattura almeno l'80% del vantaggio
lordo del sistema completo; ritracciamento e volume riducono il numero di
operazioni senza migliorare l'aspettativa per operazione. Cioè: la parte che
funziona è quella che tutti considerano banale.
*Falsificata se*: l'aspettativa per operazione del sistema completo supera quella
del solo filtro di tendenza di oltre il 50%.

**E6 — Stress sui LEAPS: quanto regge il +1,34?** ✔ eseguita (giro 52)
Il giro 49 ha falsificato E5: una call deep ITM a 12 mesi finanzia al 2,95% annuo
contro il 5,90% del CFD, non ha margin call, un solo rollo l'anno la tiene al 33%,
e batte il buy&hold di **+1,34 punti**. Non l'ho promossa per quattro motivi, e il
più serio è che **la direzione dell'errore del prezzatore è ottimistica e non l'ho
potuta quantificare**: per la covered call avevo BXY e BXMD reali, per il deep ITM
non esiste un indice di riferimento. Prima di dire che c'è qualcosa, va misurato
quanto margine di errore regge.
Tre stress, tutti sulla configurazione migliore (moneyness 80%, leve 1,0-1,5×):
(i) **implicita più alta**: k da 0,85 (tarato) a 0,95, 1,05, 1,15 — le call deep
ITM in realtà trattano sopra l'ATM per parità dallo skew delle put;
(ii) **rincaro secco del premio d'ingresso** dallo 0% al 40%, che modella spread
denaro-lettera ed esecuzione su uno strumento poco liquido;
(iii) **finestre mobili di 20 anni**, per vedere se il vantaggio è una proprietà o
un pezzo di storia.
*Predizione*: il vantaggio sparisce con un rincaro del premio **sotto il 15%** e
con k sotto **1,00**; sulle finestre mobili vince in **meno della metà** dei casi.
Cioè: +1,34 punti è dentro l'incertezza del modello, e la voce va chiusa.
*Falsificata se*: il vantaggio sopravvive a un rincaro del **30%** del premio **E**
vince in più della metà delle finestre mobili. In quel caso, e solo in quel caso,
i LEAPS diventano il primo candidato vero del progetto e vanno portati alle
verifiche di robustezza complete.

---

## G. Filtri e indice momentum come VEICOLO

**G1 — I filtri di tendenza su un PAC azionario, misurati insieme** ✔ eseguita (giro 53)
Filtro a media mobile 10 mesi, 200 giorni, e il solo filtro di tendenza del giro 51
(sopra EMA200 e EMA21>EMA50), sull'indice cap-weighted. Non su cripto e non su
asset scelti: sul benchmark che l'investitore userebbe davvero.
*Predizione*: tutti riducono volatilità e drawdown e tutti perdono IRR netta,
perché ogni uscita è un realizzo e il rientro avviene più in alto. Il migliore
perde meno di 2 punti, il peggiore più di 4.
*Falsificata se*: un filtro batte il buy&hold netto imposte.

**G2 — L'indice momentum come VEICOLO, non come strategia** ✔ eseguita (giro 53)
La domanda vera: al giro 50 il momentum settoriale perdeva perché **io** ruotavo e
**io** pagavo il 33-52% a ogni rotazione. Ma se la stessa rotazione avviene
**dentro un fondo**, per chi detiene le quote non è un evento fiscale: si paga solo
alla vendita. È la differenza fra fare la strategia e comprare l'indice che la fa.
Confronto 2×2: momentum settoriale top-10 mensile contro cap-weighted, ciascuno in
regime **CGT diretto** e in regime **ETF UCITS** (exit tax 38% + deemed disposal).
I costi di transazione restano, li paga il fondo.
*Predizione*: incartato in un fondo il momentum **batte** il cap-weighted a parità
di regime, perché il vincolo che lo uccideva era il realizzo del detentore e non il
segnale. Ma il veicolo che lo rende possibile in Irlanda è un ETF UCITS, che costa
**2,15 punti** (giro sul veicolo): il confronto che conta è momentum-in-ETF contro
cap-weighted-diretto, e lì il momentum **perde**.
*Falsificata se*: momentum in ETF UCITS batte il cap-weighted detenuto direttamente
in regime CGT.

---

## H. Il buco dichiarato: azionario globale contro solo USA

**H1 — All-world contro S&P 500** ✔ eseguita (giro 57)
Tutto il progetto usa l'azionario USA. Al giro 39 gli USA hanno battuto ogni forma
di diversificazione geografica di 3 punti nel 1990-2026 — ma è lo stesso senno di
poi di cui diffido per tutto il resto, e per un investitore europeo il default
onesto è globale. Confronto su dati reali (VT, ACWI, URTH contro SPY) e sul proxy
lungo di Ken French (Developed contro USA), regime ETF UCITS, PAC €750/mese.
*Predizione*: sulle finestre disponibili l'S&P batte il globale di **1,5-3 punti**,
perché il globale è ~60% USA più il resto che ha reso meno; ma la differenza è
**interamente attribuibile alla sovraperformance USA del periodo**, non a un
vantaggio strutturale, e su finestre mobili la quota di vittorie dell'S&P sta
**sotto il 90%** — cioè esistono finestre in cui il globale vince.
*Falsificata se*: il globale batte l'S&P sulla finestra principale, oppure l'S&P
vince in **tutte** le finestre mobili (nel qual caso la sovraperformance USA non è
un caso di periodo ma qualcosa di più sistematico).

**A15 — Il peso di ciascun anno, calcolato invece che stimato**
Tre tentativi di spiegare con una regressione quali finestre favoriscono cosa
(giri 46, 47, 58) sono tutti falliti. Provarne un quarto significherebbe cercare la
specifica che funziona invece della spiegazione vera. Quindi: **niente regressione**.
Il montante di un PAC è la somma esatta dei versamenti capitalizzati, quindi la
sensibilità dell'IRR al rendimento di ciascun anno **si scrive**, non si stima.
Da calcolare analiticamente il vettore dei pesi ∂IRR/∂r_k per k = 1..20, e
confrontarlo con i coefficienti di regressione dei giri 47 e 58.
*Predizione*: il peso analitico è monotono crescente in k e il rapporto fra
l'ultimo e il primo triennio si avvicina al 9,5:1 aritmetico entro il 20%. La
regressione lo mancava perché due variabili di bordo comprimono venti gradi di
libertà in due, non perché il meccanismo sia sbagliato.
*Falsificata se*: il peso analitico non è monotono, oppure il suo rapporto
ultimi/primi tre anni sta sotto 4 — nel qual caso il rischio di sequenza non
spiega il livello dell'IRR di un PAC e va cercato un altro meccanismo.

**D5 — La quota di vittorie per finestra è un indicatore ingannevole**
Nata al giro 59. H5 vince **31 finestre decennali su 46 (67,4%)** e ha
extra-rendimento medio **+0,16%**, cioè praticamente zero: mediana +0,54%, media
+0,16%, e la differenza sta tutta in quattro finestre che contengono il 2008
(−5,78%, −5,69%, −3,61%, −3,24%). Se il disaccordo fra "vince spesso" e "rende in
media" è sistematico, allora **ogni tabella di questo progetto che riporta una
quota di vittorie sta sovrastimando le strategie che ruotano**, e vanno rilette
tutte — F1 (regioni top-1, +0,30), E6 (17/17 finestre), H1 (73% dei decenni).
Da misurare su TUTTI i candidati mai valutati nel progetto: quota di vittorie su
finestre decennali, media, mediana, e lo scarto mediana − media.
*Predizione*: lo scarto mediana − media è **positivo per almeno l'80%** dei
candidati (cioè la coda sinistra domina ovunque, non solo per H5), e **almeno un
terzo** dei candidati che vincono oltre metà delle finestre ha media ≤ 0. Il
meccanismo è che una strategia tassata sul realizzato incassa il premio in tanti
piccoli pezzi e restituisce il capitale in un colpo solo, senza recuperare
l'imposta già pagata.
*Falsificata se*: lo scarto mediana − media è positivo per meno del **60%** dei
candidati, oppure nessun candidato con quota di vittorie sopra il 50% ha media
negativa — nel qual caso H5 è un caso isolato e le quote di vittorie restano
leggibili così come sono.

**D6 — Quante valutazioni del progetto hanno la rotazione sottostimata**
Nata al giro 60. `bench.wbacktest` calcola la rotazione come |W_t − W_{t−1}|, cioè
la variazione dei pesi **target**. Su pesi target costanti — equal-weight, inverse
variance a finestra lunga, qualunque allocazione statica — quella differenza è
**zero**, e il ribilanciamento risulta gratuito e non tassato. La rotazione vera si
misura contro i pesi **derivati** dai rendimenti: per l'equal-weight mensile dei 49
settori è **0,20×/anno**, e addebitarla costa **1,35 punti di IRR** (11,16% →
9,81%). L'errore è sistematico e ha un verso solo: **favorisce i benchmark statici
contro le strategie che ruotano**, cioè spinge tutti i verdetti del progetto nella
stessa direzione.
Da rifare: rieseguire con la rotazione derivata tutte le valutazioni con rotazione
nominale sotto 0,5×/anno — i benchmark equal-weight dei giri 30-43 e 50, l'inverse
variance del giro 34, HRP e min-variance dei giri 31-32, il 60/40 del giro 46.
*Predizione*: almeno **due terzi** di quelle valutazioni hanno rotazione vera
superiore al triplo di quella misurata, la correzione media vale **oltre 0,5 punti**
di IRR, e **nessun verdetto si ribalta** — perché i divari registrati sono quasi
tutti sopra i 2 punti. Cioè: l'errore è reale e grande, ma spinge le conclusioni
nella direzione in cui erano già.
*Falsificata se*: la correzione media sta **sotto 0,2 punti** di IRR, oppure
**almeno un verdetto si ribalta** — nel qual caso non è una nota metodologica ma
una revisione, e le voci colpite vanno rieseguite una per una.

**D7 — F2 rivalutata contro un equal-weight che paga il suo ribilanciamento**
Nata al giro 62. Il giro 50 (F2) ha concluso che nessuna delle 15 celle
posizioni × frequenza batte l'equal-weight statico, col massimo a **top-5 annuale
10,02% contro 11,16%**: −1,14 punti. Ma quel benchmark è l'equal-weight
**gratuito** — il giro 60 ha mostrato che `wbacktest` non gli addebita la
rotazione di 0,20×/anno, che vale **1,35 punti**. Con quella addebitata,
l'equal-weight mensile vale 9,81% e l'annuale 10,65%, e il divario di F2 si
chiuderebbe o si invertirebbe. Al giro 62 lo stesso candidato risulta **+2,14
contro il cap-weight e +1,84 contro l'equal-weight** in media su 46 finestre
decennali.
Da rifare: l'intera griglia di F2 (5 concentrazioni × 3 frequenze) contro
l'equal-weight mensile e annuale **con la rotazione derivata**, riportando IRR
netta a 33% e 52% e il DSR su N = 15, che è la dimensione della griglia.
*Predizione*: il top-5 annuale supera l'equal-weight annuale correttamente
addebitato di **0,5-2 punti**, ma il **DSR resta sotto 0,95** su N=15 e cresce a
N=1.157 nel registro cumulato, quindi il verdetto di F2 regge come *non
promosso* pur avendo il segno rovesciato. Cioè: il benchmark era sbagliato, la
conclusione no.
*Falsificata se*: il top-5 annuale resta **sotto** l'equal-weight annuale
correttamente addebitato — nel qual caso il difetto di `wbacktest` non spostava
nulla e F2 era giusta per intero — **oppure** il DSR supera 0,95, nel qual caso
c'è per la prima volta un candidato da portare all'holdout.

**D8 — Quali verdetti "perde contro l'equal-weight" sopravvivono alla correzione**
Nata al giro 63. La correzione della rotazione vale **0,32 punti in media sui
candidati**, ma **1,35 punti sul solo equal-weight mensile**, che è il benchmark
usato dai giri 30-43. L'asimmetria è il punto: correggere sposta il *metro* molto
più dei *misurati*. Ne segue meccanicamente che **ogni verdetto in cui un
candidato perdeva contro l'equal-weight mensile per meno di ~1,35 punti è
sospetto**, e al giro 63 ne ho controllati solo cinque. Il giro 63 ha già mostrato
che uno dei cinque si ribalta.
Da rifare: censire in QUEUE.md e nei mini-report **tutti** i verdetti la cui
formula è "il candidato X perde contro l'equal-weight di meno di 1,35 punti",
rieseguirli con la rotazione vera su entrambi i lati, e riportare quanti
cambiano segno.
*Predizione*: i verdetti col margine sotto 1,35 punti sono **fra 4 e 10**, e ne
cambia segno **meno di un terzo** — perché correggere alza anche la rotazione dei
candidati, non solo quella del benchmark, e i due effetti si compensano in buona
parte. Nessuno dei ribaltati supera comunque il DSR, quindi **il numero di
promozioni resta zero**.
*Falsificata se*: cambia segno **più di metà** dei verdetti col margine sotto
1,35 punti — nel qual caso la correzione non è una nota metodologica ma una
revisione dei giri 30-43, e vanno rieseguiti tutti — **oppure** un candidato
ribaltato supera il DSR 0,95 sul registro cumulato, nel qual caso c'è per la
prima volta qualcosa da portare all'holdout.

**D9 — La fascia di rotazione fra 0,7× e 1,0× è un precipizio, non un pendio**
Nata al giro 64. Il top-5 annuale passa da 0,83× a 1,022× di rotazione solo
cambiando *come si misura*, e con quel passaggio l'aliquota salta dal **33% al
52%**: diciannove punti d'imposta su una differenza di misura del 23%. Nessuna
strategia dovrebbe avere il proprio risultato deciso da quale lato di una soglia
cade una statistica misurata con un'incertezza di quell'ordine. La domanda non è
metodologica: **esiste un modo di stare deliberatamente sotto la soglia che
paghi?** Una strategia che rinuncia a parte della rotazione per restare al 33%
può battere la stessa strategia lasciata libera di ruotare al 52%.
Da misurare: per ciascuna cella della griglia F2 con rotazione vera fra 0,7× e
1,4×, costruire la variante **vincolata** — stessa selezione, ma i ribilanciamenti
si fermano quando la rotazione cumulata dell'anno raggiunge 0,95× — e confrontare
IRR netta della libera (52%) contro la vincolata (33%). Riportare anche quanto
segnale si perde, cioè il calo di CAGR lordo.
*Predizione*: la variante vincolata **batte** la libera in **almeno due terzi**
delle celle nella fascia, e il guadagno medio sta fra **1 e 3 punti** di IRR —
perché rinunciare all'ultimo 10% di rotazione costa poco di lordo e vale
diciannove punti di aliquota. Ma **nessuna vincolata batte l'equal-weight
annuale**, che resta a 10,65%.
*Falsificata se*: la vincolata batte la libera in **meno di metà** delle celle —
nel qual caso il segnale perso vale più dell'aliquota risparmiata, e la soglia
del 100% non è sfruttabile — **oppure** una vincolata **supera l'equal-weight
annuale**, nel qual caso c'è un candidato vero e va portato al DSR sul registro
cumulato.

**D10 — Il calendario del ribilanciamento è un parametro libero mai contato**
Nata al giro 65. La stessa strategia — momentum 12-2, top-5, ribilanciamento
annuale, 49 settori, 1969-2026 — vale **+1,51 o −1,92** contro lo stesso
benchmark a seconda che ribilanci a **gennaio civile** o **ogni 12 mesi a partire
dall'inizio del campione**. Sono **3,43 punti** da una scelta che nessuno dei
sessantacinque giri ha mai dichiarato né contato nel registro dei tentativi. Per
il top-5 il salto attraversa anche la soglia fiscale (0,962× contro 1,022×), ma
non è solo quello: il top-10 e il top-25 restano al 33% e si spostano comunque di
2,07 e 0,53 punti. **Un backtest con ribilanciamento annuale ha dodici
implementazioni, e finora ne è stata usata una alla volta senza dirlo.**
Da misurare: per momentum top-5, top-10, top-25 annuale e per l'equal-weight
annuale, tutte e **dodici** le date di ribilanciamento (gennaio…dicembre), contro
l'equal-weight annuale ribilanciato nello stesso mese. Riportare ampiezza,
mediana e quante configurazioni battono il benchmark.
*Predizione*: l'ampiezza fra il mese migliore e il peggiore supera **2 punti** di
IRR per ogni strategia, la **mediana dei dodici è negativa** contro il benchmark
per tutte, e **meno di un terzo** delle 48 configurazioni batte il proprio
benchmark. Cioè: il +1,51 di gennaio è il massimo di dodici estrazioni, non un
risultato — e il registro va aumentato di 48 tentativi, non di 4.
*Falsificata se*: l'ampiezza resta **sotto 1 punto** per la maggioranza delle
strategie — nel qual caso il calendario non è un parametro libero e il conflitto
fra i giri 64 e 65 ha un'altra causa da cercare — **oppure** la mediana dei dodici
mesi è positiva per almeno una strategia, nel qual caso il vantaggio non dipende
dalla scelta del mese e va portato al DSR.

**J1 — Statistical jump model per l'identificazione dei regimi, long e long/short**
Proposta dall'utente al giro 66. Riferimento: Aydınhan, Kolm, Mulvey, Shu,
*"Identifying patterns in financial markets: extending the statistical jump model
for regime identification"*, Annals of Operations Research 2024 — estensione
(assegnazioni continue + selezione sparsa delle feature) dello statistical jump
model di Bemporad et al. 2018 e Nystrup-Kolm-Lindström 2020. Il modello è un
clustering **temporalmente regolarizzato**: minimizza la distanza intra-cluster
**più una penalità λ per ogni cambio di stato**, il che produce regimi molto più
persistenti di un HMM gaussiano — ed è esattamente la proprietà che in questo
progetto conta, perché la persistenza è rotazione bassa e la rotazione bassa è
l'aliquota al 33%.
Da implementare a mano (nessuna libreria disponibile): assegnazione degli stati
per programmazione dinamica con penalità di salto, aggiornamento dei centroidi,
iterato fino a convergenza. Feature dal solo mercato USA giornaliero di Ken
French (1926-2026), come nel paper: rendimenti EWM a più emivite, deviazione al
ribasso, rapporti tipo Sortino. **K = 2 stati, λ scelto walk-forward solo sul
passato.** Tre varianti: (a) long nel regime 1, liquidità nel regime 2; (b) long
/ short; (c) long / short con la leva a 0,5 sul lato corto.
*Predizione*: il segnale del jump model correla **oltre 0,7** con un semplice
filtro a media mobile 10 mesi — cioè è un filtro di tendenza con una procedura di
stima più raffinata, non un'informazione nuova. La variante **long-only perde
contro il buy&hold di 1,5-4 punti** netti (stessa fascia di G1, giro 53, dove il
migliore perdeva 2,51), e la **long/short è peggiore della long-only in tutte e
tre le varianti**, perché il premio azionario è positivo e stare corti ha
aspettativa negativa prima ancora dei costi di finanziamento. L'unica clausola
che può reggere è la rotazione: sotto **1,0×/anno** grazie a λ, quindi aliquota
33% invece del 52% dei filtri del giro 53.
*Falsificata se*: la variante long-only **batte il buy&hold** netto di fiscalità
irlandese, **oppure** una variante long/short batte la corrispondente long-only —
nel qual caso il lato corto aggiunge valore e va capito perché, dato che il segno
del premio azionario dice il contrario.

---

## K. Quello che il progetto non ha mai misurato

Aggiunte al giro 69, dopo l'esaurimento della coda. Committate **prima** di
eseguire qualunque cosa: la pre-registrazione vale solo se la predizione è nel
repository prima dei dati.

**K1 — Il conto in valuta**
Tutti i sessantotto giri misurano in dollari. Un residente irlandese versa euro,
incassa euro e paga imposte in euro su plusvalenze in euro. Il cambio EUR/USD ha
una deriva e una volatilità che non sono mai entrate in un'IRR di questo
progetto. Serie: DEXUSEU dal 1999, e prima l'euro sintetico dal marco (EXGEUS,
1971+, convertito a 1,95583 DEM/EUR).
Da misurare: buy&hold azionario USA, equal-weight annuale dei 49 settori,
momentum top-10 mensile e momentum top-5 annuale, ciascuno in USD e in EUR, con
versamenti e imposte in euro.
*Predizione*: il **livello** dell'IRR si sposta di **0,5-1,5 punti**, la
volatilità in euro è **2-5 punti più alta** che in dollari, ma il **margine
strategia-meno-benchmark si sposta di meno di 0,5 punti**, perché il cambio è un
fattore comune ai due lati e in differenza si cancella quasi tutto. Quasi, non
del tutto: le imposte si pagano su plusvalenze in euro, quindi chi realizza più
spesso cristallizza più spesso anche il cambio, e il residuo è proporzionale alla
rotazione.
*Falsificata se*: il margine di almeno una coppia si sposta di **oltre 0,5
punti** — nel qual caso il cambio non è un fattore comune e ogni verdetto del
progetto va rimisurato in euro — **oppure** la volatilità in euro risulta **più
bassa** che in dollari, nel qual caso il cambio copre il rischio azionario invece
di sommarvisi, e va capito perché.

**K2 — Il PAC che si interrompe**
Ogni simulazione assume 360 versamenti consecutivi. Nella realtà si salta, si
riduce, si riscatta in anticipo. Il giro 61 ha dato lo strumento esatto per
rispondere: il peso ∂IRR/∂log(1+R_k) è monotono crescente, quindi saltare
versamenti **presto** e saltarli **tardi** non costano uguale.
Da misurare: PAC ventennale con un'interruzione di 24 mesi che comincia all'anno
k = 1..18, e in parallelo un riscatto anticipato del 30% all'anno k. Riportare la
perdita di IRR e di montante finale in funzione di k.
*Predizione*: l'interruzione costa **meno di 0,3 punti di IRR** ovunque — perché
l'IRR è un tasso, e saltare versamenti riduce il montante ma non il rendimento —
mentre il **montante** cala di **8-12%** e il calo è **monotono decrescente in k**
(saltare presto costa di più in montante). Il riscatto anticipato invece colpisce
l'IRR, e di **oltre 0,5 punti** se avviene nei primi dieci anni.
*Falsificata se*: l'interruzione sposta l'IRR di oltre 0,5 punti in qualche k —
nel qual caso l'IRR non è la metrica giusta per un PAC irregolare e serve il
montante — **oppure** il calo del montante non è monotono in k.

**K3 — Il vantaggio del veicolo, rimisurato con la rotazione vera**
Il giro 53 aveva trovato **+2,77 punti** dallo spostare la rotazione dentro un
fondo UCITS invece di farla in conto proprio, poi corretti a **+1,23** dopo il bug
dei lotti ETF e a **+0,34** dopo aver tassato i dividendi. Non è mai stato
rimisurato dopo i giri 63-68, che hanno cambiato come si misura la rotazione — e
questo numero dipende dalla rotazione più di qualunque altro nel progetto, perché
è *fatto* di rotazione. È anche l'unico risultato del progetto che non è una
strategia ma una scelta di veicolo, cioè l'unica cosa che potrebbe diventare una
raccomandazione operativa.
*Predizione*: con la rotazione vera il vantaggio del veicolo **cresce** rispetto
al +0,34, e finisce fra **+0,5 e +2,0 punti**, perché la correzione colpisce chi
ruota in conto proprio e non chi ruota dentro il fondo. Ma resta **sotto i 2,77**
del giro 53, e **sotto il divario che separa il momentum dall'equal-weight**,
quindi non salva nessuna strategia: sposta solo dove conviene tenerla.
*Falsificata se*: il vantaggio risulta **negativo**, oppure **sopra 2,77** — nel
primo caso il veicolo non conta e il giro 53 era un artefatto, nel secondo la
correzione della rotazione vale più del bug dei lotti e va rifatta l'intera
contabilità del gruppo G.

**K4 — La regola per aprire l'holdout, scritta prima di guardare**
L'holdout 2010-2026 non è mai stato aperto in 68 giri, e il criterio per aprirlo è
sempre stato descritto a parole ("un solo candidato, alla fine"). Scriverlo dopo
aver visto un candidato promettente non varrebbe niente. Va scritto **ora**, che
non c'è nessun candidato: il migliore mai registrato è **+0,33** contro il proprio
benchmark con DSR **0,9424** (giro 65).
Da produrre: una regola eseguibile — soglie numeriche su margine, DSR, stabilità
su finestre mobili e sensibilità al calendario — che decida da sola se un
candidato merita l'holdout, più il conto di quanti dei 1.296 tentativi registrati
la passerebbero (previsione: zero).
*Predizione*: nessuno dei candidati mai registrati passa la regola, e la voce si
chiude con l'holdout ancora sigillato. La soglia che eliminerà più candidati non
sarà il DSR ma la **stabilità sul calendario**, il grado di libertà scoperto al
giro 68.
*Falsificata se*: almeno un candidato già registrato passa tutte le soglie — nel
qual caso l'holdout va aperto su quello, una volta sola, e il progetto finisce lì.

---

## L. Il divario fra il modello e chi versa davvero

Aggiunte al giro 73, dopo il secondo esaurimento della coda. Committate **prima**
di eseguire qualunque cosa.

**L1 — Il costo di essere in ritardo, misurato in giorni**
Ogni segnale del progetto è applicato il mese successivo, come se il
ribilanciamento avvenisse a mezzanotte del 31. Un investitore reale vede i dati
con giorni di ritardo, ordina a mercato aperto e ottiene un prezzo diverso. Il
giro 05 aveva misurato il degrado con ritardi di **uno e due mesi** (+2,93 →
+2,35 → +2,16), ma mai sui **giorni**, che è la scala a cui il ritardo esiste
davvero.
Da misurare: momentum 12-2 top-5 e top-10 mensile sui 49 settori con dati
**giornalieri**, ribilanciando a fine mese **+ 0, 1, 5, 10, 20 giorni di
borsa**, contro l'equal-weight annuale con la rotazione vera. Finestra
1969-2009: l'holdout resta sigillato.
*Predizione*: il margine **decade in modo monotono** col ritardo, di **0,2-0,8
punti ogni 20 giorni** — cioè in linea con i −0,58 al mese del giro 05. A **un
solo giorno** la perdita sta **sotto 0,1 punti**, quindi il risultato del progetto
non dipende dal ribilanciamento a mezzanotte. E **nessun ritardo rende il margine
positivo**: il momentum non diventa buono aspettando.
*Falsificata se*: il margine **non è monotono** decrescente nel ritardo, **oppure**
un ritardo di 5 giorni o più **migliora** il margine — nel qual caso il segnale
sta catturando reversione di brevissimo periodo e non momentum, e va riletto il
gruppo A per intero.

**L2 — Il costo come lo paga un broker retail europeo**
Tutto il progetto usa **0,15% round-trip proporzionale**. Un broker retail europeo
non funziona così: commissione **fissa** per ordine (€1-3 su Degiro/IBKR), più
spread denaro-lettera sull'ETF, più eventualmente un minimo. Su un versamento da
€750 una commissione fissa da €2 è lo **0,27%** — quasi il doppio del modello — e
su un ribilanciamento che tocca dieci posizioni sono dieci commissioni.
Da misurare: rifare l'equal-weight annuale, il momentum top-5 e top-10 con un
modello di costo **fisso + proporzionale** (€1,50 per ordine + 0,05% di spread),
contando **un ordine per posizione toccata**, e confrontare con il modello
proporzionale del progetto. Riportare anche la soglia di versamento sotto cui un
PAC mensile diventa antieconomico.
*Predizione*: il modello proporzionale **sottostima** il costo per le strategie
concentrate e lo **sovrastima** per l'equal-weight, perché 49 posizioni da €15
l'una pagano 49 commissioni fisse. L'effetto netto **allarga** il divario
momentum-meno-equal-weight di **0,3-1,0 punti** a sfavore del momentum, e la
soglia di antieconomicità per un PAC su 49 posizioni sta **sopra i €500/mese**.
*Falsificata se*: il divario si **restringe** invece di allargarsi — nel qual caso
la commissione fissa penalizza più il benchmark che il candidato e tutti i
confronti del progetto sono conservativi nella direzione sbagliata.

**L3 — Il report finale**
`quant/reports/REPORT.md` è fermo al giro 29 e porta ancora il **+1,72**
pre-correzione. Quarantatré giri di risultati non esistono in forma consultabile,
e la conclusione del progetto — *nessuna strategia attiva batte il PAC buy&hold
netto di fiscalità irlandese* — non è scritta da nessuna parte in modo leggibile
da chi non ha seguito i giri.
Da produrre: un report che riporti la regola dell'holdout (giro 72), i sei-otto
numeri che contano, i tre errori di misura trovati e corretti (base fiscale, lotti
ETF, rotazione), e le raccomandazioni operative che il progetto **può**
sostenere — che sono poche e riguardano il veicolo, non la strategia.
*Predizione*: i numeri che sopravvivono a una rilettura completa sono **meno di
dieci**, e **nessuno** di essi è un margine di strategia: sono tutti costi,
soglie o misure di fragilità.
*Falsificata se*: nella rilettura emerge un risultato di strategia mai
contraddetto dai giri successivi e con margine sopra un punto — nel qual caso il
progetto ha un candidato che non aveva registrato come tale.

**L4 — Il ritardo di venti giorni è davvero uno skip più lungo?**
Nata al giro 73. Il momentum 12-2 top-5 ritardato di venti giorni di borsa passa
da **−0,87 a +0,86** contro l'equal-weight annuale. L'ipotesi meccanica è che
ritardare l'esecuzione di un mese equivalga a **saltare un mese in più**, cioè a
usare un momentum **12-3** invece del 12-2: se è così, l'effetto deve vedersi
misurando il 12-3 **direttamente**, senza passare dal ritardo. Se non si vede lì,
il +0,86 era rumore e va chiuso.
Da misurare: momentum 12-k top-5 e top-10 mensile per **k = 1, 2, 3, 4, 6**
(skip crescente) sui 49 settori, contro l'equal-weight annuale con la rotazione
vera, finestra 1969-2009. Confrontare il 12-3 senza ritardo col 12-2 ritardato di
venti giorni: se il meccanismo è quello, devono coincidere entro **0,3 punti**.
*Predizione*: il 12-3 senza ritardo **non riproduce** il +0,86 e resta **sotto lo
zero**, entro **0,5 punti** dal 12-2 senza ritardo, perché lo skip non è la
variabile che conta a questa scala. Il profilo del margine in funzione di k è
**piatto entro ±0,6 punti** su tutti e cinque i valori: nessuno skip è
sistematicamente migliore. Il +0,86 del giro 73 era il massimo di dieci celle.
*Falsificata se*: il 12-3 senza ritardo produce un margine **positivo** e **entro
0,3 punti** dal +0,86 misurato col ritardo — nel qual caso il meccanismo è reale,
lo skip conta, e va rifatto il gruppo A con lo skip come parametro dichiarato
invece che fissato a 1 — **oppure** il profilo in k ha un'ampiezza sopra 1,5
punti, nel qual caso lo skip è un grado di libertà mai contato, come il calendario
al giro 68.

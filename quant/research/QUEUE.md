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
eseguite: **A13, D3, D4**.

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

**A13 — Per un PAC conta la fine, non il centro: il rischio di sequenza**
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

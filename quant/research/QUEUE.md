# Coda delle ipotesi pre-dichiarate

Ogni voce ha **predizione** e **condizione di falsificazione** scritte prima
dell'esecuzione. Il Routine ne prende **una** per giro, in ordine, e riporta
l'esito qualunque sia. Nessuna voce viene riscritta dopo aver visto i dati: se
un'ipotesi va rivista, si aggiunge una voce nuova che dichiara perché.

Contabilità dei tentativi: `N` = dimensione della griglia se c'è selezione,
altrimenti la famiglia delle ipotesi pre-dichiarate (attualmente ~32 e in
crescita con questa coda — ogni voce aggiunta alza la soglia per tutte).

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

**C1 — Pairs trading / cointegrazione sui 49 settori**
Test di Engle-Granger su tutte le coppie, trading dello spread sulle coppie
cointegrate nel periodo di stima.
*Predizione*: molte coppie risultano cointegrate in-sample per puro caso
(1.176 coppie testate al 5% danno ~59 falsi positivi), e la cointegrazione non
persiste fuori campione.
*Falsificata se*: la quota di coppie che restano cointegrate fuori campione
supera significativamente il 5%.

**C2 — Breadth / partecipazione come segnale di mercato**
Quota di settori sopra la propria media a 200 giorni come indicatore di
salute del mercato.
*Predizione*: correlato al trend dell'indice stesso oltre 0,8, quindi non
aggiunge informazione a un semplice filtro di trend.
*Falsificata se*: correlazione col filtro di trend sotto 0,6 E migliora l'IRR.

**C3 — Momentum a orizzonti multipli combinato (1, 3, 6, 12 mesi)**
Punteggio composito invece del solo 12-2.
*Predizione*: il 12-2 domina; aggiungere orizzonti brevi introduce reversione
e alza il turnover senza alzare lo Sharpe.
*Falsificata se*: Sharpe > del solo 12-2 con turnover non superiore.

**C4 — Volatilità come asset: term structure del VIX**
VIX contro VIX a 3 mesi (contango/backwardation) come segnale di rischio.
*Predizione*: il segnale funziona per cronometrare la volatilità, non la
direzione — stesso esito del giro 22.
*Falsificata se*: produce un segnale direzionale con accuratezza sopra la
frequenza di base in modo significativo.

**C5 — Overlay di copertura sul premio di volatilità**
Vendere put e comprare put più lontane (put spread) per tagliare la coda che
uccide BXM e PUT. Approssimato dai dati CBOE disponibili.
*Predizione*: la copertura costa più della coda che evita, perché il premio
delle put lontane è proporzionalmente più caro (volatility smile).
*Falsificata se*: IRR netta superiore a PUT non coperto.

**C6 — Multi-strategia su stream davvero non correlati**
Combinare: trend azionario, carry valutario, momentum materie prime, premio
di volatilità. Sono i quattro pilastri dei CTA.
*Predizione*: correlazione media sotto 0,2, Sharpe combinato sopra ogni
singolo, e IRR netta comunque sotto il buy&hold per la rotazione aggregata.
*Falsificata se*: IRR netta > buy&hold azionario.

---

## D. Metodologiche

**D1 — Quanto vale la finestra di partenza**
Rieseguire i tre candidati promossi facendo partire il campione in 20 anni
diversi, per misurare la dispersione del risultato dovuta alla sola data di
inizio.
*Predizione*: la dispersione dell'extra-rendimento supera 3 punti, cioè è più
grande dell'extra-rendimento stesso.
*Falsificata se*: dispersione sotto 1 punto.

**D2 — Bootstrap a blocchi dei candidati**
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

**A6 — Il ribilanciamento e' l'unico costo, o serve anche il premio?**
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

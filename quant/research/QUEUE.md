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

**A2 — Hierarchical Risk Parity (López de Prado 2016)**
Clustering gerarchico della matrice di correlazione, allocazione ricorsiva.
Sui 49 settori, ribilanciamento annuale.
*Predizione*: batte l'equal-weight in Sharpe ma non l'IRR netta; il vantaggio
documentato di HRP è sulla stabilità dei pesi, non sul rendimento.
*Falsificata se*: IRR netta > equal-weight annuale di almeno 0,5 punti.

**A3 — Minimum variance e maximum diversification**
Due portafogli ottimizzati sui 49 settori, vincolo long-only, annuale.
*Predizione*: minimum variance riduce il drawdown di oltre 10 punti e perde
2-4 punti di CAGR; nessuno dei due batte l'IRR netta del cap-weight.
*Falsificata se*: uno dei due supera il cap-weight netto imposte.

**A4 — Kelly frazionario e de-risking sul drawdown**
Esposizione = f × Kelly stimato sul passato, con f in {0,25 · 0,5}; variante
che taglia l'esposizione quando il drawdown corrente supera una soglia.
*Predizione*: il de-risking sul drawdown peggiora l'IRR (vende sui minimi) pur
migliorando il DD massimo.
*Falsificata se*: l'IRR netta migliora rispetto all'esposizione costante.

**A5 — Equal risk contribution fra i 4 stream non correlati migliori**
Selezionati per correlazione, non per rendimento, così la scelta non guarda
il risultato.
*Predizione*: correlazione media sotto 0,3 raggiungibile, ma l'IRR netta resta
sotto il buy&hold perché i componenti a rendimento alto sono anche quelli ad
alta rotazione.
*Falsificata se*: IRR netta > buy&hold.

---

## B. Mercati non ancora toccati

**B1 — Materie prime (petrolio WTI, FRED DCOILWTICO dal 1986)**
Trend following e carry sul future proxy.
*Predizione*: il trend following su materie prime funziona lordo (è il caso
canonico dei CTA) e muore sui costi più le imposte, come sull'azionario.
*Falsificata se*: IRR netta > buy&hold azionario.

**B2 — Valute (DEXUSEU, DEXJPUS, DEXCHUS) — carry e momentum**
Carry = differenziale tassi (DGS2 contro tasso estero implicito), momentum a
12 mesi. Long/short fra tre cambi.
*Predizione*: il carry ha premio positivo ma skew fortemente negativa, e le
tre valute non bastano a diversificare il rischio di crash.
*Falsificata se*: Sharpe > 0,5 con skew > -0,5 dopo costi.

**B3 — Credito (spread high yield BAMLH0A0HYM2)**
Segnale macro: allargamento dello spread come indicatore di rischio per
l'azionario. Esci dall'azionario quando lo spread sale oltre N deviazioni.
*Predizione*: segnale con potere in-sample, ma il ritardo di pubblicazione e
la reazione già incorporata nei prezzi lo rendono inutile out-of-sample.
*Falsificata se*: batte il buy&hold netto imposte fuori campione.

**B4 — Curva dei tassi (T10Y2Y) come segnale di regime azionario**
L'inversione della curva precede le recessioni. Riduzione dell'esposizione
azionaria quando la curva si inverte.
*Predizione*: il segnale è corretto ma troppo lento — l'anticipo mediano
dell'inversione è 12-18 mesi, e uscire con quell'anticipo costa più di quanto
protegga.
*Falsificata se*: IRR netta > buy&hold.

**B5 — Azionario internazionale (French Developed, Emerging, Japan, Europe)**
Momentum cross-sectional fra regioni, ribilanciamento annuale.
*Predizione*: funziona come il momentum settoriale (stesso meccanismo) e
muore come lui sulle imposte, con in più il fatto che la storia parte dal 1990.
*Falsificata se*: DSR > 0,95 con IRR netta positiva.

**B6 — Cripto: universo esteso oltre i 7 attuali**
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

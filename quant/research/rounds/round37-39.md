# Giri 37-39 — gruppo B: mercati non ancora toccati

Sei voci dichiarate (B1-B6), più **B7** pre-registrata durante l'esecuzione perché
B3 è risultata non testabile. Esito: **cinque confermate, una senza esito per dati,
una sostituta confermata.** E **un bug vero trovato per strada**, che aveva prodotto
una falsificazione falsa.

---

## Giro 37 — B1: materie prime (WTI)

**Predizione**: *il trend following su materie prime funziona lordo e muore sui
costi più le imposte.* **Falsificata se**: IRR netta > buy&hold azionario.
→ **CONFERMATA**

Avvertenza dichiarata prima dei numeri: il WTI di FRED è un **prezzo spot**, non un
investimento. Chi compra petrolio paga il roll dei futures, storicamente dominante
e spesso negativo. Tutti i numeri sotto sono quindi un **limite superiore**.

| | CAGR | vol | Sharpe | max DD | turn | IRR netta |
|---|---:|---:|---:|---:|---:|---:|
| WTI buy&hold | 3,76% | 37,9% | 0,28 | −86,3% | 0,00× | 3,34% |
| WTI trend MA12 | **5,31%** | 24,3% | 0,33 | −50,4% | 1,73× | 3,75% |
| WTI trend MA6 | 4,79% | 24,8% | 0,31 | −49,2% | 2,72× | 2,59% |
| WTI momentum 12m | 3,77% | 23,5% | 0,28 | −54,5% | 1,65× | 2,05% |
| **azionario (benchmark)** | 11,52% | 15,6% | 0,78 | −50,3% | 0,00× | **9,90%** |

Il trend following **funziona lordo**, come previsto: 5,31% contro 3,76% del
buy&hold, e taglia il drawdown da −86% a −50%. Poi paga 1,7-2,7 rotazioni l'anno e
arriva a 3,75% netto, contro 9,90% dell'azionario. La prima metà della predizione è
esatta, la seconda anche.

Carry sui futures: **non testabile**, non ho la curva forward.

---

## Giro 37 — B2: valute, carry e momentum

**Predizione**: *il carry ha premio positivo ma skew fortemente negativa, e le tre
valute non bastano a diversificare il rischio di crash.* **Falsificata se**: Sharpe
> 0,5 con skew > −0,5 dopo costi. → **CONFERMATA** — dopo la correzione di un bug

### Il bug, perché è la cosa più importante di questo giro

Alla prima esecuzione B2 risultava **falsificata**: il momentum long/short a 12 mesi
dava Sharpe 0,58 con skew +1,81, superando la condizione. Sarebbe stata la prima
falsificazione di tutta la coda.

Non lo era. Il rendimento totale di ogni valuta era costruito così:

```python
tot = sret.add(carry.reindex(sret.index).fillna(0.0), fill_value=0.0)
```

`fill_value=0.0` fa sì che dove **il cambio non esiste ancora** ma il tasso sì, il
risultato sia il solo carry. L'euro esiste dal 1999; i tassi euro dal 1994. Per
cinque anni la serie EUR conteneva un asset che pagava il differenziale di tasso
**senza rischio di cambio** — un titolo inesistente con Sharpe altissimo. La
finestra comune risultava 1981-2026 invece della vera, 1999-2026.

Corretto (il carry mancante vale zero, il **cambio** mancante deve restare NaN):

| | Sharpe prima | Sharpe dopo |
|---|---:|---:|
| momentum 12m long/short | 0,58 | **0,25** |
| skew | +1,81 | −0,12 |

**Nessuna variante passa più la condizione. B2 è confermata.**

L'ho trovato inseguendo un problema diverso — i dati del credito per B3 — non
perché il risultato sembrasse strano. Avevo anzi già scritto una verifica della
falsificazione che puntava sulla causa sbagliata (lo yuan agganciato al dollaro
fino al 2005): era un sospetto ragionevole e sarebbe stato un vero problema, ma non
era **il** problema.

Risultati corretti, 1999-02 → 2026-07 (330 mesi):

| | CAGR | vol | Sharpe | skew | turn | IRR netta |
|---|---:|---:|---:|---:|---:|---:|
| carry EUR/JPY long-short | −0,47% | 10,6% | 0,01 | −0,66 | 0,18× | 0,37% |
| momentum 12m long-short | 2,02% | 9,7% | 0,25 | −0,12 | 3,27× | 2,13% |
| 3 valute equal-weight long | −0,54% | 5,5% | −0,07 | +0,01 | 0,00× | −1,49% |
| carry +GBP (robustezza) | 1,17% | 10,2% | 0,17 | **−1,02** | 0,45× | 1,67% |

La skew negativa del carry è confermata (−0,66, e −1,02 aggiungendo la sterlina):
è il profilo classico del carry, che raccoglie premi piccoli e regolari e restituisce
tutto nei crolli. Il premio, in questa finestra, non è nemmeno positivo.

---

## Giro 38 — B3: non testabile, e B7 al suo posto

**B3 resta SENZA ESITO.** La serie dichiarata `BAMLH0A0HYM2` (ICE BofA high yield)
si scarica da FRED **solo per gli ultimi 3 anni** — 35 mesi di sovrapposizione con
l'azionario, contro i 30 anni che servirebbero. È una restrizione di licenza ICE:
né `fredgraph.csv?cosd=1900-01-01` né l'endpoint `/data/*.txt` restituiscono la
storia dal 1996.

Prima di eseguire qualunque cosa ho **pre-registrato B7 in coda**, con predizione e
condizione di falsificazione scritte prima di girare: stessa meccanica, ma sullo
**spread Baa−Aaa di Moody's**, il *default spread* di Fama-French 1989, con storia
dal 1919.

**B7 — Predizione**: *lo spread di default dice che i rendimenti attesi sono alti
quando è largo, cioè dopo i crolli; usarlo come segnale di uscita fa l'opposto di
quel che dovrebbe. La versione walk-forward resterà sotto il buy&hold, e il divario
fra il miglior parametro in-sample e quello preso walk-forward sarà di almeno 1
punto.* **Falsificata se**: la versione walk-forward batte il buy&hold netto
imposte. → **CONFERMATA sul test, sbagliata sul divario**

1931-2026, 95 anni. Soglia scelta **walk-forward**, z-score su finestra mobile,
segnale ritardato di un mese:

| | IRR netta | vs B&H |
|---|---:|---:|
| azionario buy&hold | **10,56%** | — |
| miglior parametro in-sample (w60, z2,0) | 8,87% | −1,69 |
| preso **walk-forward** | 8,48% | −2,08 |

Il segnale perde **in ogni singola configurazione della griglia**, in-sample
compresa: non c'è nemmeno il parametro fortunato da cui diffidare. E il divario fra
il miglior in-sample e il walk-forward è **0,39 punti**, non "almeno 1" come avevo
previsto — perché quando tutte le configurazioni perdono, scegliere male costa
poco. Avevo previsto il costo dell'ottimizzazione in un caso in cui non c'è niente
da ottimizzare.

---

## Giro 38 — B4: la curva dei tassi

**Predizione**: *il segnale è corretto ma troppo lento — l'anticipo mediano
dell'inversione è 12-18 mesi, e uscire con quell'anticipo costa più di quanto
protegga.* **Falsificata se**: IRR netta > buy&hold. → **CONFERMATA, e in modo
istruttivo**

Prima la misura del segnale, separata dalla strategia: **13 inversioni** nel
campione 1976-2026, di cui **12 seguite da un calo oltre il 15% entro 36 mesi**.
L'anticipo mediano è **13 mesi**, dentro la banda 12-18 prevista.

| | CAGR | Sharpe | max DD | turn | IRR netta |
|---|---:|---:|---:|---:|---:|
| azionario buy&hold | 12,18% | 0,83 | −50,3% | 0,00× | **10,94%** |
| curva invertita → 0% (lag 1m) | 11,88% | **0,87** | −50,3% | 0,54× | 9,26% |
| curva invertita → 50% (lag 1m) | 12,08% | 0,86 | −50,3% | 0,28× | 9,71% |
| curva invertita → 0% (lag 3m) | 10,70% | 0,79 | −50,3% | 0,54× | 8,35% |

**Un segnale che ha ragione 12 volte su 13 perde 1,2-2,6 punti l'anno.** È il
risultato più chiaro contro l'intuizione "basta avere ragione": avere ragione con
13 mesi di anticipo significa stare fuori dal mercato per un anno di rialzi prima
di ogni calo, e il drawdown massimo non migliora nemmeno di un decimo di punto
(−50,3% in tutte le varianti) perché il crollo del 2008 è arrivato quando la curva
si era già normalizzata.

---

## Giro 39 — B5: azionario internazionale

**Predizione**: *funziona come il momentum settoriale e muore come lui sulle
imposte.* **Falsificata se**: DSR > 0,95 con IRR netta positiva. → **CONFERMATA**

5 regioni, 1990-07 → 2026-05 (431 mesi):

| | CAGR | Sharpe | turn | IRR netta |
|---|---:|---:|---:|---:|
| regioni equal-weight (bench) | 7,74% | 0,55 | 0,00× | **6,74%** |
| azionario USA (bench) | 11,16% | 0,78 | 0,00× | 9,68% |
| momentum top2 ribil. mensile | 7,50% | 0,52 | 1,66× | 5,81% |
| momentum top2 ribil. annuale | 6,72% | 0,47 | 0,56× | 5,05% |
| momentum top1 ribil. mensile | 5,14% | 0,37 | 3,10× | 4,60% |

Nessuna variante batte nemmeno l'equal-weight fra regioni, prima ancora
dell'azionario USA. DSR 0,864. Da notare la cosa più semplice della tabella:
**tenere solo gli Stati Uniti ha battuto ogni forma di diversificazione geografica
di 3 punti l'anno**, il che è un fatto sul campione 1990-2026 e non una
raccomandazione — è esattamente il tipo di risultato che il senno di poi rende
ovvio.

---

## Giro 39 — B6: cripto, universo esteso

**Predizione**: *allargando l'universo il CAGR del buy&hold scende, il vantaggio
relativo del trend filter resta, ma il DSR non migliora.* **Falsificata se**: DSR >
0,95. → **CONFERMATA sul test, sbagliata sulla prima clausola**

8 asset, storie parziali dichiarate (SOL entra nel 2020, DOGE nel 2019):

| | CAGR | vol | Sharpe | max DD | turn | IRR (52%) |
|---|---:|---:|---:|---:|---:|---:|
| cripto equal-weight buy&hold | 55,33% | 111,5% | 0,83 | −76,7% | 0,00× | 47,74% |
| solo BTC/ETH/LTC buy&hold | 22,58% | 76,6% | 0,63 | −80,7% | 0,00× | 15,86% |
| **trend MA10 multi-asset** | 70,69% | 110,5% | **0,89** | −79,4% | 2,38× | 52,44% |
| momentum 6m top3 | 39,35% | 110,0% | 0,69 | −76,8% | 3,08× | 30,45% |

Il CAGR del buy&hold **sale** invece di scendere: 55,33% contro 22,58% dei tre
storici. La mia predizione era sbagliata, e il motivo è che **allargare l'universo
ai simboli oggi quotati su OKX non attenua la sopravvivenza, la aumenta**: ADA, SOL
e DOGE sono lì perché sono sopravvissuti. La voce diceva "includere asset con storia
parziale per attenuare la sopravvivenza", ma la storia parziale che serve è quella
dei **delistati**, che su un exchange non c'è.

DSR **0,904**, sotto la soglia: confermata. E il numero che il DSR non dice —
l'intervallo di confidenza al 95% dello Sharpe su 106 mesi è **[0,22, 1,56]**,
ampiezza 1,34, più larga della differenza fra qualunque coppia di righe in tabella.
Con questa quantità di dati non si può distinguere il trend filter dal buy&hold.

---

## Bilancio del gruppo B

| voce | esito | numero chiave |
|---|---|---|
| B1 materie prime | confermata | trend 3,75% netto contro 9,90% azionario |
| B2 valute | confermata **dopo correzione di un bug** | Sharpe 0,25, skew −0,12 |
| B3 credito HY | **senza esito** | serie ICE limitata a 35 mesi |
| B4 curva dei tassi | confermata | 12 inversioni su 13 azzeccate, −1,2/−2,6 punti |
| B5 azionario internazionale | confermata | DSR 0,864, nessuna variante batte |
| B6 cripto esteso | confermata | DSR 0,904, Sharpe [0,22 – 1,56] |
| B7 credito Baa−Aaa (sostituta) | confermata | 8,48% walk-forward contro 10,56% |

**Nessuna promozione.** Registro a **808 tentativi**. Holdout 2010-2026 sigillato.

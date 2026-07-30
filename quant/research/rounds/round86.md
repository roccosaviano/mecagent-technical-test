# Giro 86 — O8: la volatilità dell'alfa non spiega niente, e lo scarto da spiegare era più piccolo di quanto avevo scritto

**Predizione** (verbatim, committata al giro 83): *il margine netto **scende in
modo monotono** al crescere della volatilità dell'alfa, e alla volatilità che il
candidato aveva davvero — circa **14 punti** — la perdita è **fra 0,5 e 1,2
punti**, coerente con lo 0,8 misurato indirettamente al giro 83.*
**Falsificata se**: la mediana **non scende**, o scende di **meno di 0,2 punti**
anche a 20 di volatilità — **oppure** se la caduta supera **2,5 punti**.

**Esito: FALSIFICATA sul ramo 1. E il giro trova un errore mio nel giro 83, che è
la vera spiegazione.**

## La griglia

Rotazione fissa 3,5×, alfa lordo **geometrico** fisso a 6 punti l'anno — imposto
sul logaritmo, così la media non dipende dalla volatilità per costruzione — e 200
estrazioni per cella con seme fissato.

| vol. alfa | mediana | media | p5 | p95 | perdita |
|---:|---:|---:|---:|---:|---:|
| 0 | **+1,55** | +1,55 | +1,55 | +1,55 | — |
| 2 | +1,56 | +1,56 | +1,12 | +1,99 | +0,01 |
| 5 | +1,56 | +1,54 | +0,58 | +2,47 | +0,00 |
| 10 | +1,49 | +1,54 | −0,57 | +3,68 | −0,07 |
| 15 | **+1,22** | +1,38 | −1,75 | +4,25 | **−0,33** |
| 20 | +1,37 | +1,40 | −2,87 | +5,76 | **−0,18** |

La cella a volatilità zero dà **+1,55**, esattamente il valore del giro 83 a 3,5×
con alfa 6: la costruzione sintetica è la stessa e il controllo torna.

**Il tracking error vero del candidato è 12,64 punti**, non «circa 14» come la
voce assumeva. L'ho misurato invece di assumerlo, come dichiarato.

## Perché la voce cade

**La mediana non scende in modo monotono** — a 15 fa −0,33 e a 20 risale a −0,18 —
e **a 20 la caduta è 0,18, sotto la soglia di 0,2** che falsificava.

E la non-monotonia non è un fenomeno: è **rumore Monte Carlo**. Con 200 estrazioni
e l'intervallo p5-p95 osservato, l'errore standard della mediana è **±0,16 a
vol 15** e **±0,23 a vol 20**. I due valori distano meno di un errore standard
l'uno dall'altro. **L'effetto misurato (≤0,33) è dello stesso ordine del suo
stesso rumore.**

Alla volatilità vera del candidato la perdita interpolata è **−0,21 punti**, non
gli 0,5-1,2 previsti né gli 0,8 da spiegare.

## L'errore che il giro trova, ed è nel giro 83

Se la volatilità dell'alfa vale 0,2 punti, che cosa spiegava gli 0,8 di scarto che
al giro 83 avevo attribuito proprio a lei? **Niente, perché quegli 0,8 non
esistevano.**

Al giro 80 ho misurato l'alfa lordo del candidato come **differenza di CAGR**:
17,28% − 10,78% = **6,50 punti**. Al giro 83 ho poi confrontato quel 6,50 con il
parametro `a` del sintetico — che però è un **alfa geometrico**, un moltiplicatore,
non una differenza. Le due cose coincidono solo se i livelli sono piccoli, e qui
non lo sono:

| | |
|---|---:|
| alfa **aritmetico** (differenza di CAGR) | **6,50** |
| alfa **geometrico** (1,1728 / 1,1078 − 1) | **5,87** |

Il candidato corrisponde quindi a `a = 5,87`, non a 6,50. Il sintetico a 5,87 con
rotazione 3,5× dà **+1,45**, non «circa +1,9».

| | |
|---|---:|
| sintetico all'alfa **giusto** (5,87) | **+1,45** |
| candidato reale | **+1,18** |
| **scarto residuo** | **0,27** |

**Lo scarto da spiegare non era 0,8: era 0,27.** E la volatilità dell'alfa ne
spiega **0,21**. Insieme, i due effetti lo chiudono quasi per intero — restano
**sei centesimi di punto**, e il candidato ruotava per giunta a 3,28× invece di
3,5×, il che va nella direzione giusta.

## Correzione a un numero registrato

Al giro 83 avevo scritto, e messo in `STATE.md` e in coda, che *«la curva del tasso
di cambio è un limite inferiore: il tasso vero a 3,5× è più vicino a 6,0-6,5 che a
5,27»*. **È sbagliato.** Con la conversione corretta e la penalità da volatilità
misurata qui, il tasso vero a 3,5× è

> **5,27 + 0,27 ≈ 5,5**, non 6,0-6,5.

La curva del giro 83 era **quasi giusta**, e l'ho screditata sulla base di un
confronto mal fatto. Correggo il numero in `STATE.md` e in `QUEUE.md`.

Questo non cambia nessuna conclusione del progetto — a 3,5× servono comunque
cinque volte e mezzo l'alfa lordo per un punto netto, e il candidato ne aveva
5,87 — ma cambia un numero che avevo pubblicato, e va corretto dove è scritto.

## Cosa resta vero della cautela del giro 83

Che il sintetico sia un **limite inferiore** resta vero: la volatilità dell'alfa
costa qualcosa (0,2 punti alla volatilità del candidato) e la curva non la
include. Ma la taglia è **un quarto** di quella che avevo dichiarato.

E c'è una cosa che il sintetico non cattura affatto e che questa griglia rende
visibile: **la dispersione degli esiti**. A volatilità 15 il margine mediano è
+1,22, ma il quinto percentile è **−1,75** e il novantacinquesimo **+4,25**. Chi
compra una strategia con quel profilo compra una mediana appena positiva e una
coda sinistra che perde quasi due punti l'anno per vent'anni. **La mediana non è
l'esperienza**, ed è la stessa lezione del giro 70 vista dal lato della
dispersione invece che da quello dei cashflow.

## Il verdetto

| clausola | previsto | misurato | |
|---|---|---|---|
| mediana monotona decrescente | sì | **no** (−0,33 a 15, −0,18 a 20) | **SBAGLIATA** |
| perdita alla vol vera in [0,5; 1,2] | sì | **0,21** | **SBAGLIATA** |
| scende di meno di 0,2 a vol 20 → falsifica | no | **0,18** | **SCATTA** |
| caduta sopra 2,5 → falsifica | no | 0,33 | non scatta |

Nuova voce in coda: **O11**, per validare la curva del giro 83 su tutti e tredici
i candidati invece che su uno solo — che è il controllo che avrebbe evitato
l'errore di conversione fin dall'inizio.

**Tentativi cumulati a registro: 1.524.** Holdout **bruciato al giro 78**, non
interrogato in questo giro.

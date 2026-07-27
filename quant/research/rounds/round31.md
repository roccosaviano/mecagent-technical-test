# Giro 31 — A2: Hierarchical Risk Parity (López de Prado 2016)

**Predizione scritta prima** (voce A2 della coda, verbatim): *batte l'equal-weight
in Sharpe ma non l'IRR netta; il vantaggio documentato di HRP è sulla stabilità dei
pesi, non sul rendimento.* **Falsificata se**: IRR netta > equal-weight di almeno
0,5 punti.

**Esito: CONFERMATA.**

## Cosa ho eseguito

L'algoritmo nella forma originale in tre passi, sui 49 settori Ken French,
1969-07 → 2026-05 (683 mesi):

1. distanza fra asset `d_ij = sqrt(0,5·(1−ρ_ij))`, poi distanza euclidea fra le
   colonne della matrice di distanza;
2. clustering gerarchico a legame singolo e riordino quasi-diagonale;
3. bisezione ricorsiva, con il budget di rischio diviso fra i due sotto-alberi in
   modo inversamente proporzionale alla loro varianza di cluster.

Covarianza e correlazione stimate su **60 mesi mobili precedenti**, ribilanciamento
annuale, costi 0,15% round-trip. Fra un ribilanciamento e l'altro i pesi derivano
coi prezzi, come farebbe un portafoglio vero. Confronto contro inverse-variance ed
equal-weight sullo stesso universo e la stessa finestra, più l'indice cap-weighted
come riferimento esterno.

## Risultati

| metodo | CAGR | Sharpe | max DD | turnover/anno | mov. pesi | IRR netta 33% |
|---|---:|---:|---:|---:|---:|---:|
| HRP | 11,26% | **0,78** | −46,6% | 0,31× | 0,283 | 9,45% |
| inverse-variance | 11,26% | 0,76 | −49,2% | 0,23× | 0,109 | 9,65% |
| equal-weight | 11,57% | 0,74 | −51,5% | 0,23× | 0,017 | **9,89%** |
| indice cap-weighted | 10,98% | 0,74 | −50,3% | 0,00× | 0,000 | **10,88%** |

- **Sharpe**: HRP 0,780 contro equal-weight 0,737. La prima metà della predizione
  regge — HRP migliora il rischio, e lo fa dove è progettato per farlo (il
  drawdown massimo scende di 4,9 punti).
- **IRR netta**: HRP 9,45% contro equal-weight 9,89%, **−0,44 punti**. Seconda metà
  della predizione confermata: il miglioramento di rischio non si traduce in
  rendimento netto.
- **Contro l'indice cap-weighted: −1,43 punti.** Tutti e tre i metodi di
  allocazione perdono contro il portafoglio che non fa niente.
- DSR 1,000 su 52 ipotesi pre-dichiarate, ma **non promuovibile**: il DSR misura
  lo Sharpe contro zero, non contro il benchmark, e qui il benchmark vince.

## La parte che smentisce il motivo per cui HRP esiste

HRP è stato proposto **per la stabilità dei pesi**. Ho misurato il movimento medio
dei pesi a ogni ribilanciamento, ed è la riga che non torna:

```
HRP 0,283  ·  inverse-variance 0,109  ·  equal-weight 0,017
```

HRP è **il meno stabile dei tre**, di un fattore 2,6 contro inverse-variance.

Due precisazioni, perché il confronto va letto per quello che è:

- **Contro equal-weight il confronto non è informativo.** L'equal-weight riazzera
  a 1/N a ogni ribilanciamento: il suo 0,017 misura solo la deriva dei prezzi in
  dodici mesi, non una scelta di allocazione. Che sia il più stabile è
  un'identità, non un risultato.
- **Contro inverse-variance il confronto è informativo, ed è il verso sbagliato.**
  La tesi del paper è che HRP sia più stabile del **min-variance di Markowitz**,
  che inverte la matrice di covarianza ed è instabile per costruzione con 49 asset
  e 60 mesi. Inverse-variance non inverte niente: usa solo la diagonale. HRP è più
  stabile del bersaglio del paper, ma non del metodo diagonale banale, perché il
  clustering a legame singolo può riorganizzare l'albero in modo discreto quando
  le correlazioni si muovono di poco.

Il confronto che il paper rivendica davvero — HRP contro min-variance — **non l'ho
eseguito qui**, perché il min-variance è la voce A3 della coda con la sua
predizione già scritta. Lo si vedrà lì, e sarà il test onesto della tesi.

## Cosa aggiunge questo giro

Il giro 30 aveva mostrato che con turnover quasi nullo la perdita contro
l'azionario viene dalla **composizione**, non dalle imposte. Qui la composizione è
controllata — tutti e quattro i portafogli sono azionario USA sullo stesso
universo — e il risultato non cambia: **9,45% contro 10,88%**. Con la composizione
fissa e il turnover basso (0,31×/anno, cioè un terzo del portafoglio all'anno), il
metodo di allocazione sposta 1,4 punti di IRR netta nella direzione sbagliata.

Il costo si scompone così: HRP guadagna 0,28 punti di CAGR lordo sul cap-weighted
(11,26% contro 10,98%) e ne perde 1,43 di IRR netta. La differenza è quasi
interamente il conto fiscale di 0,31 rotazioni l'anno più i costi di transazione —
lo stesso vincolo che ha ucciso tutto il resto della ricerca, applicato stavolta a
una strategia che *non prova nemmeno* a prevedere i rendimenti.

**Tentativi cumulati a registro: 702.**

Holdout 2010-2026 **ancora sigillato**.

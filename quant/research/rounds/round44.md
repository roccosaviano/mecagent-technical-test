# Giro 44 — A6: la perdita delle allocazioni multi-classe, scomposta

**Predizione scritta prima** (voce A6, verbatim): *oltre il 90% della perdita viene
da (a) il minor rendimento atteso della sleeve difensiva, non da (b) le imposte sul
ribilanciamento.* **Falsificata se**: la componente fiscale supera il 25%.

**Esito: CONFERMATA sul test — ma la soglia del 90% regge solo in 1 caso su 4.**

## Il problema di metodo, risolto prima di guardare i numeri

Il divario da scomporre è `IRR(azionario 100%) − IRR(allocazione, tutto incluso)`,
e ci sono tre ingredienti da spegnere e riaccendere: **composizione** (i pesi
diversi da 100% azionario), **costi** (0,15% round-trip sul turnover), **imposte**
(33% sulla plusvalenza realizzata a ogni ribilanciamento).

Una scomposizione sequenziale **dipende dall'ordine**: se le imposte si applicano
su un montante già ridotto dai costi sembrano più piccole. Non è un dettaglio, è
esattamente la leva con cui si può far dire a una scomposizione quello che si
vuole — e qui la conclusione da difendere ("è la composizione, non il fisco") è
proprio quella che l'ordine potrebbe fabbricare.

Quindi calcolo **tutti e sei gli ordinamenti** e prendo il contributo marginale
medio di ciascun fattore: è il valore di Shapley, l'unica attribuzione simmetrica.
Riporto anche il minimo e il massimo per ordinamento, così si vede quanto la scelta
avrebbe potuto cambiare la risposta.

## Risultati — 1962-2026, azionario + decennale (772 mesi)

IRR dell'azionario 100%: **10,48%**.

| allocazione | IRR piena | divario | composizione | costi | imposte | turnover |
|---|---:|---:|---:|---:|---:|---:|
| ERC | 6,85% | 3,63 | **3,258%** (89,9%) | 0,012% (0,3%) | 0,356% (9,8%) | 0,16× |
| inverse-vol | 6,52% | 3,96 | **3,640%** (91,9%) | 0,010% (0,3%) | 0,312% (7,9%) | 0,14× |
| 60/40 | 7,84% | 2,64 | **2,229%** (84,3%) | 0,010% (0,4%) | 0,405% (**15,3%**) | 0,13× |
| equal-weight | 7,36% | 3,12 | **2,735%** (87,6%) | 0,010% (0,3%) | 0,378% (12,1%) | 0,13× |

**Quota fiscale massima: 15,3%**, ben sotto il 25% che avrebbe falsificato la voce.
**A6 confermata.**

## Dove la predizione sbaglia

Avevo scritto *"oltre il 90%"*. La quota della composizione è **84,3% – 91,9%**:
supera il 90% solo per l'inverse-vol. Le altre tre stanno fra l'84% e il 90%.

La direzione è giusta e il test passa, ma il numero preciso no, e il verso
dell'errore è sempre lo stesso che ho fatto in tutta questa coda: **avevo
sottostimato il peso della componente fiscale**. Su un turnover di 0,13-0,16 volte
l'anno — praticamente nulla — il fisco si prende comunque un ottavo del divario.

I costi di transazione, invece, sono **irrilevanti: 0,3-0,4%** del divario, cioè un
centesimo di punto l'anno. A questa rotazione lo 0,15% round-trip non è un vincolo.

## Quanto avrebbe potuto cambiare l'ordine

Il contributo attribuito alle imposte varia fra **0,000 e 0,812 punti** a seconda
dell'ordinamento — cioè fra lo 0% e il 31% del divario di un'allocazione. Con
l'ordinamento "sbagliato" (imposte per ultime, su un montante già eroso) la voce
sarebbe apparsa confermata con margine enorme; con quello opposto (imposte per
prime, sul montante pieno) il 60/40 avrebbe sfiorato la soglia del 25% di
falsificazione. **La scelta dell'ordine avrebbe potuto decidere l'esito**, ed è il
motivo per cui la scomposizione di Shapley non era un vezzo.

## La controprova, che vale più della scomposizione

Una scomposizione è pur sempre un'attribuzione. La verifica che non dipende da
nessuna convenzione è: **azzerando del tutto le imposte sul ribilanciamento,
l'allocazione batterebbe l'azionario?**

| | senza imposte sul ribilanciamento | azionario | differenza |
|---|---:|---:|---:|
| ERC | 7,56% | 10,48% | **−2,92** |
| inverse-vol | 7,14% | 10,48% | −3,34 |
| 60/40 | 8,64% | 10,48% | −1,83 |
| equal-weight | 8,11% | 10,48% | −2,37 |

**No, e non ci va nemmeno vicino.** In un mondo con fiscalità irlandese zero sui
ribilanciamenti, l'allocazione multi-classe perderebbe ancora 1,8-3,3 punti l'anno
contro l'azionario puro.

## Cosa chiude questo giro

Il giro 30 aveva lasciato aperta la domanda se le allocazioni multi-classe
perdessero *a causa della fiscalità irlandese* o *a causa del decennale*. La
risposta è netta: **a causa del decennale**. In questa finestra il decennale
ricostruito rende molto meno dell'azionario, e qualunque peso gli si dia è capitale
tolto all'unico asset con un premio grande.

È una conclusione che vale per il campione 1962-2026 e per **questa** ricostruzione
del decennale, che sottostima convessità e rolldown (dichiarato al giro 30 e ancora
vero). Non è un argomento contro il possedere obbligazioni: è la misura di quanto
sia costato possederle, dentro un PAC azionario a trent'anni, in un periodo che
contiene il più lungo mercato toro obbligazionario della storia **e** un premio
azionario altissimo.

**Tentativi cumulati a registro: 858.** Holdout 2010-2026 **ancora sigillato**.

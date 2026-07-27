# Giro 53 — G1 (filtri) e G2 (indice momentum come veicolo)

**G1 confermata. G2 FALSIFICATA** — e nel farlo ha trovato la cosa più interessante
degli ultimi dieci giri. In più il giro ha scoperto **un bug nel motore fiscale**
che cambia un numero già riportato.

## Il bug, prima di tutto

Il regime ETF UCITS restituiva `nan` sulla finestra 1969-2026. Causa: quando si
pagano le imposte liquidando quote, `pay_from_portfolio` riduceva le `units`
globali **ma non i lotti ETF**. La somma dei lotti restava gonfia, e ogni deemed
disposal successivo calcolava la plusvalenza su quote che non esistevano più.

Su 34 anni (4 cicli) l'errore era tollerabile; su 57 anni (7 cicli) azzerava il
portafoglio — €3,48 milioni di imposte su €344.500 versati. C'era già una pezza al
solo **realizzo finale** (`scale = units / tot_units`): avevo notato la deriva e
corretto il punto sbagliato.

Corretto riducendo i lotti **pro rata** a ogni prelievo. **Il vantaggio del veicolo
cambia**, ed era un numero che avevo riportato:

| finestra | prima | **dopo** |
|---|---:|---:|
| 1990-2023 | +2,15 | **+1,23** |
| 1990-2026 | — | +1,49 |
| 1969-2026 | — | +2,12 |

Il vantaggio **cresce con l'orizzonte**, il che è coerente: più anni, più cicli di
deemed disposal. La cifra da usare per un PAC trentennale è **~1,2-1,5 punti**, non
2,15.

## G1 — I filtri di tendenza → **CONFERMATA**

| filtro | CAGR | vol | Sharpe | max DD | rotaz. | IRR | vs B&H | DD evitato |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| buy&hold | 10,38% | 18,4% | 0,63 | −83,7% | 0,00× | **10,56%** | — | — |
| media mobile 12 mesi | 9,58% | 12,6% | **0,80** | −46,3% | 1,31× | 7,62% | −3,92 | +37,4 |
| media mobile 10 mesi | 9,44% | 12,5% | 0,79 | −43,9% | 1,47× | 7,42% | −4,10 | +39,8 |
| media 200 giorni | 9,32% | 12,4% | 0,78 | −52,8% | 1,47× | 7,43% | −4,08 | +30,8 |
| media mobile 6 mesi | 9,10% | 12,8% | 0,75 | −46,6% | 2,17× | 6,98% | −4,50 | +37,1 |
| **EMA200 + EMA21>EMA50** | 8,53% | 14,8% | 0,63 | −65,1% | **0,19×** | **8,05%** | **−2,51** | +18,6 |

Nessuno batte il buy&hold. Il migliore perde 2,51 punti, il peggiore 4,50 — dentro
la banda prevista. Da notare **perché** il filtro del giro 51 è il meno caro:
0,19 rotazioni l'anno contro 1,3-2,2 degli altri. Non è più bravo a prevedere, è
più pigro.

## G2 — L'indice momentum come veicolo → **FALSIFICATA**

La domanda che il giro 50 non aveva isolato: lì il momentum perdeva perché **io**
ruotavo e **io** pagavo. Dentro un fondo la stessa rotazione non è un evento
fiscale per chi detiene le quote.

| configurazione | CAGR | IRR netta |
|---|---:|---:|
| momentum, rotazione **mia** (giro 50) | 15,16% | 11,67% |
| **momentum dentro un fondo, CGT** | 15,16% | **14,44%** |
| momentum dentro un fondo, ETF UCITS | 15,16% | 11,64% |
| cap-weighted diretto, CGT | 10,98% | 10,88% |
| cap-weighted via ETF UCITS | 10,98% | 8,74% |
| equal-weight dentro un fondo, CGT | 11,15% | 11,16% |

**Il risultato indipendente dal modello**: a parità **esatta** di rendimento lordo,
spostare la rotazione dentro il fondo vale **+2,77 punti di IRR**. Non cambia
niente nella strategia — cambia solo chi realizza la plusvalenza.

**Il confronto che conta per un residente irlandese**: momentum in ETF UCITS
**11,64%** contro cap-weight diretto in CGT **10,88%** → **+0,77 punti**.
Falsificata.

### Perché non la chiamo un candidato

1. **Il lordo è troppo generoso.** 15,16% contro 10,98% sono **4,18 punti** di
   premio momentum lordo su 57 anni. Gli indici momentum reali (MSCI USA Momentum)
   hanno storicamente battuto l'S&P di 1-2 punti, non 4. Il mio è costruito su 49
   portafogli settoriali value-weighted, che non è un prodotto acquistabile.
2. **Manca il TER.** Un ETF momentum costa 0,15-0,35% l'anno, che non ho dedotto.
   Al 0,30% il +0,77 scende a **~+0,45**.
3. **I parametri (12-1, top-10) furono scelti al giro 05**, su questa stessa
   storia. Il premio lordo è in-sample rispetto a quella scelta.

Sommando le tre cose, il margine plausibile è fra **zero e mezzo punto**, contro un
buy&hold che non richiede di scegliere niente. Non è abbastanza per promuovere, ma
è la prima volta che una falsificazione indica un meccanismo reale invece di un
artefatto.

**Tentativi cumulati: 1.026.** Holdout **sigillato**.

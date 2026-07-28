# Giro 61 — A15: il peso di ciascun anno, calcolato invece che stimato

**Predizione** (verbatim): *il peso analitico è monotono crescente in k e il
rapporto fra l'ultimo e il primo triennio si avvicina al 9,5:1 aritmetico entro
il 20%.*
**Falsificata se**: il peso analitico **non è monotono**, oppure il suo rapporto
ultimi/primi tre anni sta **sotto 4**.

**Esito: CONFERMATA** sul test, **sbagliata sulla clausola del livello**. E dopo
tre giri di regressione fallita, questa volta il numero è esatto per costruzione.

## La derivazione

Un PAC versa `c` all'inizio di ogni mese `i = 1..N`. Il montante è
`V = Σ_i c · Π_{j≥i}(1+ρ_j)`, e l'IRR mensile `y` risolve `Σ_i c(1+y)^(N-i+1) = V`.

Derivando rispetto a `log(1+ρ_m)` — perché il rendimento annuale è il *prodotto*
dei dodici mensili, e in log-spazio le sensibilità si sommano esattamente:

```
∂V/∂log(1+ρ_m) = Σ_{i≤m} c·Π_{j≥i}(1+ρ_j) = A_m     montante dei versamenti fino a m
∂Φ/∂y          = Σ_i c(N-i+1)(1+y)^(N-i)
∂y/∂log(1+ρ_m) = A_m / (∂Φ/∂y)                       teorema della funzione implicita
w_k            = (1/12)·Σ_{m∈k} ∂y/∂log(1+ρ_m)
```

**Il controllo a differenze finite ha trovato un errore alla prima stesura.**
Avevo aggregato i mesi con una *somma* invece che con una media, e il rapporto
analitico/numerico è uscito **0,0833 = 1/12 su tutti e venti gli anni** — la
firma di un errore di scala, non di rumore. Il vincolo che mi era sfuggito è
`log(1+R_k) = Σ_{m∈k} log(1+ρ_m)`: per alzare di uno il log-rendimento
dell'anno bisogna alzare di 1/12 quello di ogni mese. Corretto, l'errore
residuo è **3,5·10⁻⁵**, cioè troncamento della differenza finita.

## Il profilo, percorso piatto

| rendimento annuo | monotono | ultimi3/primi3 | errore vs diff. finite |
|---:|:---:|---:|---:|
| 2% | sì | **10,27×** | 3,9·10⁻⁵ |
| 4% | sì | 8,88× | 3,8·10⁻⁵ |
| 6% | sì | 7,79× | 3,7·10⁻⁵ |
| **8%** | sì | **6,91×** | 3,7·10⁻⁵ |
| 10% | sì | 6,20× | 3,6·10⁻⁵ |
| 12% | sì | 5,61× | 3,5·10⁻⁵ |

**Il rapporto non è una costante: dipende dal livello dei rendimenti**, e scende
da 10,27 al 2% a 5,61 al 12%. Più il mercato rende, meno conta la sequenza — il
capitale accumulato presto cresce abbastanza da contare comunque.

Profilo al 8%, normalizzato a w₂₀ = 1:

| anno | 1 | 2 | 3 | 5 | 10 | 15 | 18 | 20 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| peso | 0,052 | 0,144 | 0,228 | 0,379 | 0,669 | 0,866 | 0,952 | 1,000 |

Il primo anno pesa **il 5,2%** dell'ultimo. Ma la curva è **concava**: già al
decimo anno si è a due terzi del peso finale. Non è una rampa lineare.

## Percorsi storici reali

80 finestre ventennali del mercato USA, 1926-2025:

| | |
|---|---|
| monotono | **80 su 80** |
| rapporto mediano | **5,91×** |
| minimo | 4,34× |
| massimo | 16,11× |

Il minimo storico, **4,34**, sta appena sopra la soglia di falsificazione di 4.

## Il verdetto

| clausola | esito |
|---|---|
| peso monotono crescente | **centrata** — in tutti gli scenari e in 80/80 finestre storiche |
| rapporto entro il 20% del 9,5:1 (cioè 7,6-11,4) | **sbagliata** — va da 5,61 a 10,27, e la mediana storica è 5,91 |
| *falsificazione: rapporto sotto 4* | **non raggiunta** — minimo 5,61 sugli scenari, 4,34 sul peggior percorso storico |

## Il vero risultato: erano tre quantità diverse, non una

I giri 47 e 58 hanno cercato il **9,5:1** nei coefficienti di regressione. Quel
numero non era mai stato la sensibilità dell'IRR:

| quantità | valore |
|---|---:|
| peso **aritmetico puro** dei versamenti, (18+19+20)/(1+2+3) | **9,50×** |
| **capitale esposto**, capitalizzato all'8% | **24,72×** |
| **peso dell'IRR**, ∂IRR/∂log(1+R_k), all'8% | **6,91×** |

Il 9,5:1 non è né l'uno né l'altro: sta in mezzo, ed è la statistica di un PAC
**senza crescita**. Due effetti tirano in direzioni opposte e nessuno dei due
compare in quel conto:

- il capitale accumulato **cresce** con k → spinge il rapporto *sopra* 9,5 (24,72)
- il tempo di capitalizzazione residuo **scende** con k → lo riporta *sotto* (6,91)

Un rendimento del ventesimo anno colpisce molto capitale ma non ha più tempo di
comporsi; uno del primo anno colpisce poco capitale e si compone per vent'anni.
Il netto, a rendimenti azionari realistici, è **6-7 volte**, non 9,5.

## Perché le regressioni non potevano trovarlo

| giro | metodo | rapporto | R² |
|---|---|---|---:|
| 47 (A13) | regressione, 2 variabili di bordo | 1,21-2,71 | 0,28-0,33 |
| 58 (A14) | regressione sul livello | 0,55-48,51 | 0,002-0,210 |
| **61 (A15)** | **calcolo diretto** | **5,61-10,27** | esatto per costruzione |

La predizione diceva che la regressione mancava il bersaglio perché *"due
variabili di bordo comprimono venti gradi di libertà in due"*. È vero, ma non
basta a spiegare tutto: anche una regressione perfetta avrebbe dovuto trovare
**5,9**, non 9,5, perché **9,5 era il bersaglio sbagliato**. I giri 47 e 58 non
hanno fallito solo per la specifica — cercavano un numero che il meccanismo non
produce.

**La linea si chiude qui, e stavolta con una risposta.** Il rischio di sequenza
in un PAC è reale, monotono, e vale un fattore **6-7 fra l'ultimo e il primo
triennio** a rendimenti azionari — non 9,5, e non 1,2-2,7.

Nessuna promozione: è una voce esplicativa, non una strategia. Nessuna selezione,
N resta la famiglia pre-dichiarata della coda.

**Tentativi cumulati a registro: 1.087.** Holdout 2010-2026 **ancora sigillato**.

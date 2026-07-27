# Giro 58 — A14: rischio di sequenza sul livello → **FALSIFICATA**

**Predizione** (verbatim): *sul livello il rapporto |b(ultimi 3)|/|b(primi 3)| sale
sopra 6 e l'R² dei soli ultimi tre supera 0,6, avvicinandosi al 9,5:1 aritmetico;
entrambi i coefficienti positivi.* **Falsificata se**: il rapporto resta sotto 4.

Peso aritmetico del capitale, ultimi 3 anni contro primi 3: **9,50:1**.

| PAC | b(ultimi 3) | b(primi 3) | rapporto | R² ultimi | R² entrambi |
|---|---:|---:|---:|---:|---:|
| azionario 100% | +0,137 | **−0,034** | 4,05 | **0,210** | 0,223 |
| 60/40 | +0,069 | −0,009 | 7,78 | 0,088 | 0,090 |
| equal-weight | +0,060 | −0,001 | 48,51 | 0,065 | 0,065 |
| inverse-vol | +0,035 | +0,020 | 1,76 | 0,014 | 0,020 |
| ERC | +0,020 | +0,037 | **0,55** | 0,002 | 0,027 |

**Falsificata**: il minimo è **0,55**, ben sotto 4. E le altre due clausole
falliscono: R² fra 0,002 e 0,210, mai vicino a 0,6; coefficienti entrambi positivi
solo in 2 PAC su 5.

Il 48,51 dell'equal-weight non è un risultato: è il rapporto fra +0,060 e −0,001,
cioè una divisione per un numero che è rumore. L'intervallo 0,55-48,51 dice che
**la statistica stessa non è stabile**.

## Cosa è vero, in mezzo alla falsificazione

Sul PAC azionario il **verso** è quello giusto e ha senso economico:
**b(ultimi 3) = +0,137, b(primi 3) = −0,034.** Un piano di accumulo **preferisce
una partenza brutta e un finale buono** — rendimenti forti all'inizio significano
comprare meno quote a prezzi più alti per tutti i versamenti successivi.

Ma R² = 0,210: **il 79% della variazione fra finestre sta altrove.**

## La cosa che devo dire e che vale più del verdetto

Ho provato **tre volte** a spiegare quali finestre favoriscono cosa:

| giro | spiegazione tentata | esito |
|---|---|---|
| 46 | "le finestre vinte sono centrate sui mercati orso" | sbagliata |
| 47 | "è rischio di sequenza, sul divario" | falsificata, rapporto 1,2-2,7 invece di ≥4 |
| 58 | "è rischio di sequenza, sul livello" | **falsificata**, rapporto 0,55-48,51 |

Tre specifiche, tre fallimenti. **La regressione su due rendimenti di bordo non è
lo strumento giusto**, e a questo punto provarne una quarta significherebbe cercare
la specifica che funziona invece della spiegazione che è vera — cioè esattamente
ciò che 58 giri di lavoro esistono per non fare.

**Chiudo questa linea di indagine.** Ho aggiunto in coda **A15**, che non è un
quarto tentativo di regressione: è il calcolo **esatto**. Il montante di un PAC è
la somma dei versamenti capitalizzati, quindi la derivata dell'IRR rispetto al
rendimento di ciascun anno si può scrivere analiticamente invece di stimarla. Se
nemmeno il calcolo esatto riproduce quello che si osserva, allora l'effetto non è
il rischio di sequenza e va cercato altrove.

**Tentativi cumulati: 1.035.** Holdout **sigillato**.

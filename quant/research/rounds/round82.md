# Giro 82 — O4: la correlazione fra le celle e la N vera

**Predizione** (verbatim, committata al giro 79): *`N_eff` è **fra 3 e 8** su 20
celle nominali, e la soglia corretta scende a **+1,5/+1,9**, quindi **il candidato
resta respinto** (+1,18). Con la griglia implicita completa e la stessa
correzione, la soglia **risale sopra +2,0**: i due errori non si compensano.*
**Falsificata se**: la soglia corretta scende **sotto +1,18** — **oppure** se
`N_eff` supera 15.

**Esito: CONFERMATA sul ramo che falsifica. Una clausola descrittiva manca il
bordo per cinque millesimi, e la registro come sbagliata.**

## (a) Quante estrazioni indipendenti ci sono davvero

Ho correlato le **serie di extra** (cella meno benchmark), non i rendimenti
grezzi: la statistica selezionata è il *margine*, che è già relativa al benchmark,
e correlare i grezzi misurerebbe il fatto che sono tutti portafogli azionari. La
scelta era dichiarata prima; riporto entrambe.

| | serie di **extra** | rendimenti grezzi |
|---|---:|---:|
| correlazione media fuori diagonale | **0,750** (0,479 … 0,944) | 0,908 (0,790 … 0,995) |
| primo autovalore | 15,28 su 20 (**76%**) | 18,26 su 20 (91%) |
| **N_eff Li & Ji** (primario) | **6,00** | 3,00 |
| N_eff Nyholt | 9,10 | 4,30 |
| N_eff rapporto di partecipazione | 1,68 | 1,20 |

**`N_eff` = 6,00 esatto**, e non è una coincidenza: su una matrice di correlazione
la traccia vale *M*, quindi la somma delle parti frazionarie degli autovalori è
`M − Σ⌊λ⌋`, cioè un intero. La formula di Li & Ji restituisce **sempre** un intero
in questo contesto — tre autovalori sopra 1, più 20 − 17 = 3.

## (b) La soglia ricalcolata

| N usata | N | soglia | candidato | esito |
|---|---:|---:|---:|---|
| nominale, come al giro 79 | 20,00 | **+2,19** | +1,18 | **RESPINTO** |
| **effettiva (Li & Ji sugli extra)** | 6,00 | **+1,495** | +1,18 | **RESPINTO** |
| effettiva (Nyholt) | 9,10 | +1,76 | +1,18 | **RESPINTO** |
| effettiva (rapporto di partecipazione) | 1,68 | +0,00 | +1,18 | **PASSA** |

### I tre stimatori non concordano, e uno di essi lo farebbe passare

Avevo dichiarato prima di eseguire che se i tre avessero dato risposte in classi
diverse l'avrei detto. **Lo dicono.** Li & Ji e Nyholt respingono, il rapporto di
partecipazione (1,68) porta la soglia a zero e lo lascia passare.

Non prendo il rapporto di partecipazione, e la ragione è che misura un'altra cosa:
`M²/Σλ²` è dominato dal primo autovalore ed è una misura del **numero effettivo di
fattori**, non del numero effettivo di *test*. Con un primo autovalore che spiega
il 76% della varianza risponde «c'è un fattore e mezzo», che è vero e irrilevante:
la domanda non è quante direzioni indipendenti ci sono nei rendimenti, è quante
estrazioni indipendenti ha fatto la ricerca. Li & Ji esiste esattamente per questo
ed è lo standard nei test multipli correlati.

Ma resta che **la scelta dello stimatore è un grado di libertà**, il quarto che il
progetto incontra dopo il calendario (giro 68), lo skip (giro 76) e lo schema
delle finestre (giro 81). Qui la scelta è difendibile su basi teoriche e non sul
risultato — l'ho dichiarata prima — però va contata.

## (c) La griglia implicita

Fattore di riduzione misurato: **`N_eff/N` = 0,300**.

| griglia | N nominale | N effettiva | soglia | esito |
|---|---:|---:|---:|---|
| come scritta nella voce (5 skip × 12 cal. × 4 taglie) | 240 | 72,0 | **+2,78** | RESPINTO |
| difendibile (5 skip × 4 taglie × 3 frequenze) | 60 | 18,0 | **+2,14** | RESPINTO |
| la sola famiglia misurata | 20 | 6,0 | +1,50 | RESPINTO |

**Un sovraconteggio nella voce, dichiarato prima di eseguire**: il «5 skip × 12
calendari × 4 taglie» è sbagliato, perché le venti celle sono tutte **mensili** e
una strategia mensile non ha il grado di libertà del calendario — lo passa per
costruzione, come G4 dice dal giro 72. Ho calcolato la griglia come scritta,
perché non si riscrive una predizione dopo averla vista, e accanto quella
difendibile. **Entrambe stanno sopra +2,0**, quindi la clausola regge in ogni
caso.

## I due errori non si compensano, ma quasi

Il giro 79 aveva dichiarato due difetti di segno opposto e non li aveva
quantificati. Adesso:

| | effetto sulla soglia |
|---|---:|
| soglia nominale del giro 79 (N=20, indipendenti) | **+2,19** |
| correggendo **solo** la correlazione | +1,50 (−0,69) |
| correggendo **solo** la griglia (60 celle indipendenti) | +2,70 (+0,51) |
| correggendo **entrambe** | **+2,14** (−0,05) |

**Il +2,19 del giro 79 era accidentalmente quasi giusto**: i due errori si
elidono a cinque centesimi di punto. Non perché fossero della stessa taglia per
qualche ragione profonda — è una compensazione fortuita — ma il numero
pubblicato al giro 79 non va corretto in pratica, e questo va detto invece di
lasciar credere che servisse un giro per aggiustarlo.

## Il verdetto

| clausola | previsto | misurato | |
|---|---|---|---|
| `N_eff` fra 3 e 8 | sì | **6,00** | **centrata** |
| soglia corretta in [+1,5; +1,9] | sì | **+1,495** | **sbagliata per 0,005** |
| il candidato resta respinto | sì | +1,18 contro +1,495 | **centrata** |
| griglia implicita sopra +2,0 | sì | **+2,78** (voce) / **+2,14** (difendibile) | **centrata** |
| `N_eff` sopra 15 → falsifica | no | 6,00 | non scatta |

La seconda clausola manca il bordo inferiore della banda per **cinque millesimi di
punto**. È dentro qualunque precisione sensata, ed è comunque **fuori dalla banda
che avevo scritto**: la registro come sbagliata invece di arrotondarla a +1,50, che
sarebbe stato comodo e disonesto.

## Cosa resta in piedi dell'autopsia

Dopo quattro giri: il candidato è respinto **sotto ogni lettura difendibile** —
soglia nominale +2,19, corretta per correlazione +1,50, corretta per griglia
+2,14, tutte sopra il suo +1,18. **La conclusione del giro 79 non cambia**, e ora
ha un intervallo invece di un punto.

Nuova voce in coda: **O7**, perché il fattore 0,300 è stato misurato su **una
sola** famiglia e un cancello che dipende da un numero misurato una volta sola non
è un cancello.

**Tentativi cumulati a registro: 1.459.** Holdout **bruciato al giro 78**, non
interrogato in questo giro.

# Giro 80 — O2: da dove vengono i 2,13 punti fra train e holdout

**Predizione** (verbatim, committata al giro 78): *la componente dominante è
**l'alfa lordo**, che vale **oltre la metà** dei 2,13 punti; la rotazione
aggiuntiva vale **meno di 0,3** punti; il benchmark migliore vale il resto.*
**Falsificata se**: la rotazione spiega **più di 0,5 punti** — **oppure** se il
benchmark spiega più dell'alfa, cioè se il candidato non ha perso ma è stato
superato.

**Esito: CONFERMATA. E la taglia dell'alfa lordo è tre volte quella del divario
che deve spiegare.**

## Un doppio conteggio nella voce, dichiarato prima di eseguire

La voce elencava **tre** cause, ma (a) *alfa lordo* e (c) *livello del benchmark*
sono la stessa cosa guardata due volte: l'alfa lordo **è** CAGR del candidato meno
CAGR del benchmark, quindi «il benchmark migliora» e «l'alfa si assottiglia» non
si sommano, sono il minuendo e il sottraendo della stessa differenza.

Non ho riscritto la voce. L'ho misurata così com'è, sciogliendo il doppio
conteggio nel modo che la clausola di falsificazione rende obbligatorio — quella
clausola chiede di distinguere «il candidato ha perso» da «il candidato è stato
superato», e la distinzione esiste: sono **le due metà** di Δ(alfa).

## Le due colonne

| | train | holdout | variazione |
|---|---:|---:|---:|
| CAGR **lordo** candidato | **17,28** | 13,65 | **−3,63** |
| CAGR **lordo** benchmark | 10,78 | 13,34 | **+2,56** |
| IRR netta candidato | 11,27 | 9,89 | −1,38 |
| IRR netta benchmark | 10,09 | 10,83 | +0,74 |
| rotazione candidato | 3,28× | 3,80× | +0,52 |
| **margine** | **+1,18** | **−0,94** | **−2,12** |

*(I numeri dell'holdout sono costanti copiate dal giro 78, non ricalcolate: il
campione bruciato non è stato interrogato di nuovo.)*

## La scomposizione, additiva per costruzione

Il margine si scrive esattamente come
`alfa lordo − zavorra_candidato + zavorra_benchmark`, dove la zavorra è tutto ciò
che sta fra il lordo time-weighted e il netto money-weighted: imposte, costi, e la
forma dei cashflow del PAC.

| componente | train | holdout | contributo al divario |
|---|---:|---:|---:|
| alfa lordo (cand − bench) | **+6,50** | **+0,31** | **−6,19** |
| zavorra del candidato | 6,01 | 3,76 | +2,25 |
| zavorra del benchmark | 0,69 | 2,51 | +1,82 |
| **totale** | | | **−2,12** ✓ |

## Il numero che non mi aspettavo

**Nel train il candidato aveva 6,50 punti di alfa lordo, e ne consegnava 1,18.**

La zavorra del candidato era **6,01 punti** contro **0,69** del benchmark: un
differenziale di **5,32 punti** fra chi ruota 3,3 volte l'anno e chi ruota 0,07.
Il segnale funzionava — funzionava molto — e la macchina fiscale ne ha preso
cinque sesti.

E poi, fuori campione, l'alfa lordo è passato a **+0,31**: non c'era più niente da
tassare.

## La macchina fiscale è un ammortizzatore, in entrambi i versi

Questo è il risultato collaterale del giro, e non era nella voce.

**L'alfa lordo è crollato di 6,19 punti e il margine netto solo di 2,12.** I due
terzi mancanti sono stati assorbiti dalla zavorra, che si è ridotta insieme
all'alfa: quando il vantaggio lordo si assottiglia, si assottiglia anche l'imposta
che ci paghi sopra.

Il 52% funziona come un ammortizzatore simmetrico. Prende cinque sesti di un alfa
grande e restituisce due terzi di una sua caduta. Per un investitore questo è
freddo conforto — resta il fatto che di 6,50 punti lordi ne incassava 1,18 — ma
spiega perché **il crollo di un segnale, misurato al netto, sembra sempre più
piccolo di quello che è**. Chi guarda solo l'IRR vede −2,12 e pensa a una
strategia che si è indebolita un po'. Chi guarda il lordo vede **−6,19** e capisce
che il segnale è morto.

## Le due metà dell'alfa, che è la domanda della clausola

| | punti di CAGR lordo |
|---|---:|
| il **candidato cade** | **−3,63** |
| il **benchmark sale** | +2,56 |

**Il candidato ha perso**, per 59% contro 41%. Ma non è una valanga: il
benchmark che sale spiega quasi la metà del crollo dell'alfa, e l'holdout è stato
un periodo in cui l'equal-weight dei 49 settori ha reso il **13,34% lordo** contro
il 10,78% del train. Parte di quello che sembra decadimento del segnale è **un
benchmark diventato più difficile da battere**.

## Il controfattuale sulla rotazione, misurato sul solo train

Domanda: quanto sarebbe costato al candidato, **nel train**, ruotare 3,804× invece
di 3,284×?

| | |
|---|---:|
| IRR netta | 11,27% → **11,16%** |
| aliquota | 52% → 52% (nessun salto di scaglione) |
| **costo della rotazione aggiuntiva** | **−0,11 punti** |

**Centrata**: previsto sotto 0,30, misurato 0,11, e molto sotto lo 0,50 che
falsificava. Il motivo è quello scritto nella voce e regge: mezza rotazione in più
su una base **già tassata al massimo** costa poco. Il gradino del 100% è tutto —
quello che succede sopra è quasi piatto, come il giro 66 aveva mostrato dal lato
opposto (il top-10, già al 33%, non guadagnava niente a farsi vincolare).

## Una cautela sulla scomposizione

I tre termini sommano a −2,12 **per costruzione**: è un'identità contabile, non
un'attribuzione causale. In particolare **la zavorra non è un'aliquota**: scala col
livello del rendimento lordo, perché una strategia che rende il 17,28% ha in
valore assoluto più plusvalenze da realizzare di una che rende il 10,78%. Parte
del differenziale di 5,32 punti è «tassa sulla rotazione» e parte è
«tassa sull'aver guadagnato di più», e questa scomposizione non le separa.
Separarle è la voce **O5**, che aggiungo in coda.

## Il verdetto

| clausola | previsto | misurato | |
|---|---|---|---|
| alfa lordo dominante, oltre metà del divario | sì | **−6,19 su −2,12, il 291%** | **centrata** |
| rotazione sotto 0,30 | sì | **−0,11** | **centrata** |
| rotazione sopra 0,50 → falsifica | no | 0,11 | non scatta |
| il benchmark spiega più dell'alfa → falsifica | no | cand −3,63 contro bench +2,56 | non scatta |

Il 291% ha la stessa forma del 398% del giro 60 (il premio di equal-weighting
spiegava quattro volte il margine di H5): un contributo può superare il 100% del
totale quando gli altri lo compensano. Qui l'alfa crolla di 6,19 e la zavorra ne
restituisce 4,07.

**Tentativi cumulati a registro: 1.426.** Holdout **bruciato al giro 78**, non
interrogato in questo giro.

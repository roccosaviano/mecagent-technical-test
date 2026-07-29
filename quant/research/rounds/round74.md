# Giro 74 — L2: il costo come lo paga un broker retail europeo

**Predizione** (verbatim, committata prima di eseguire): *il modello proporzionale
**sottostima** il costo per le strategie concentrate e lo **sovrastima** per
l'equal-weight, perché 49 posizioni da €15 l'una pagano 49 commissioni fisse.
L'effetto netto **allarga** il divario momentum-meno-equal-weight di **0,3-1,0
punti** a sfavore del momentum, e la soglia di antieconomicità per un PAC su 49
posizioni sta **sopra i €500/mese**.*
**Falsificata se**: il divario si **restringe** invece di allargarsi.

**Esito: FALSIFICATA sulla clausola principale. La soglia era centrata.**

## Una contraddizione dentro la voce, dichiarata prima di eseguire

L'ho scritta nel docstring dello script prima di far girare qualsiasi cosa. La
predizione dice che il modello proporzionale **sovrastima** il costo
dell'equal-weight, ma la ragione che porta subito dopo — *«49 posizioni da €15
l'una pagano 49 commissioni fisse»* — dice l'**opposto**: 49 ordini da €1,50 su
un versamento da €750 fanno €73,50, cioè il **9,8%**, contro lo 0,075% del
modello proporzionale. La clausola contraddice la propria motivazione.

Non l'ho riscritta. L'ho misurata così com'è, e il risultato è che **la metà
motivazione regge e la metà conclusione cade**.

## I numeri, 49 settori, 1969-2009, rata €500/mese

Modello del progetto: 0,15% round-trip proporzionale.
Modello retail: **€1,50 per ordine + 0,05% di spread**, un ordine per posizione
toccata.

### (i) letterale — il versamento spalmato su tutte le posizioni target

| strategia | IRR prop. | IRR retail | delta | ordini/anno |
|---|---:|---:|---:|---:|
| equal-weight annuale (49 pos.) | 10,02% | 9,42% | **−0,60** | 636 |
| momentum top-5 annuale | 10,79% | 10,72% | −0,07 | 89 |
| momentum top-5 mensile | 11,82% | 11,88% | **+0,06** | 133 |
| momentum top-10 mensile | 11,05% | 10,99% | −0,06 | 260 |

| divario momentum-meno-EW | proporzionale | retail | sposta |
|---|---:|---:|---:|
| top-5 annuale | +0,77 | +1,30 | **+0,53** |
| top-5 mensile | +1,79 | +2,46 | **+0,66** |
| top-10 mensile | +1,03 | +1,57 | **+0,54** |

### (ii) sensata — il versamento in un ordine solo

| strategia | IRR prop. | IRR retail | delta | ordini/anno |
|---|---:|---:|---:|---:|
| equal-weight annuale (49 pos.) | 9,95% | 9,42% | −0,54 | 600 |
| momentum top-5 annuale | 10,79% | 10,72% | −0,07 | 96 |
| momentum top-5 mensile | 11,82% | 11,92% | +0,10 | 86 |
| momentum top-10 mensile | 11,05% | 11,08% | +0,03 | 155 |

| divario momentum-meno-EW | proporzionale | retail | sposta |
|---|---:|---:|---:|
| top-5 annuale | +0,83 | +1,30 | +0,47 |
| top-5 mensile | +1,87 | +2,50 | +0,63 |
| top-10 mensile | +1,10 | +1,66 | +0,56 |

Le due varianti danno **lo stesso verso e la stessa taglia**: +0,47/+0,66. Il
verdetto non dipende da quale delle due si prende.

## Perché la clausola cade

Il divario momentum-meno-equal-weight **cresce** di mezzo punto passando al
modello retail. Cioè: la commissione fissa **penalizza il benchmark, non il
candidato**. Esattamente il ramo di falsificazione scritto in coda.

Il meccanismo è quello che la motivazione della predizione già diceva, e ha due
gambe:

1. **Il benchmark è quello con 49 posizioni.** Ogni mese l'equal-weight tocca
   tutte e 49 le posizioni e paga 636 ordini l'anno; il momentum top-5 annuale ne
   paga 89. La commissione fissa è un costo **per posizione**, e il portafoglio
   diversificato ne ha dieci volte tante.
2. **Lo spread retail è metà del costo proporzionale.** 0,05% contro 0,15%
   round-trip: sulle operazioni grandi — quelle di un portafoglio da centinaia di
   migliaia di euro dopo trent'anni di PAC — il retail costa **meno** del modello
   del progetto. Per questo il top-5 mensile ha IRR retail *superiore* alla
   proporzionale (+0,06 e +0,10): con 3,3× di rotazione su un patrimonio grande,
   dimezzare il costo variabile vale più di quanto pesino 133 commissioni da
   €1,50.

Le due gambe spingono nella stessa direzione perché il progetto ha scelto come
benchmark la strategia **più frammentata** e come candidati le strategie **più
concentrate**.

## La cosa che non mi aspettavo: l'ordine unico non serve

Sotto (ii) l'equal-weight passa da 636 a 600 ordini l'anno — praticamente niente.
Motivo: si versa in un ordine solo, ma **subito dopo si ribilancia verso il
target**, e il ribilanciamento tocca di nuovo tutte e 49 le posizioni. Gli ordini
si spostano dalla fase di versamento a quella di ribilanciamento, non
spariscono. L'IRR retail dell'equal-weight è **identica nelle due varianti**
(9,42% e 9,42%).

Il trucco funziona solo per chi ha poche posizioni: il top-5 mensile scende da
133 a 86 ordini/anno. **Concentrare il versamento aiuta solo se il portafoglio è
già concentrato.**

## La soglia di antieconomicità — clausola centrata

Perché i costi del versamento stiano sotto l'1% della rata serve
`rata ≥ P × €1,50 / 1%`:

| posizioni | commissioni | su €750 | rata minima |
|---:|---:|---:|---:|
| 1 | €1,50 | 0,3% | €150 |
| 5 | €7,50 | 1,5% | €750 |
| 10 | €15,00 | 3,0% | €1.500 |
| 25 | €37,50 | 7,5% | €3.750 |
| 49 | €73,50 | 14,7% | **€7.350** |

**€7.350/mese** contro i «sopra €500» previsti: centrata, e con quattordici volte
il margine. Un PAC equal-weight su 49 posizioni comprate una per una **non è un
prodotto retail**: a rata normale il 15% del versamento se ne va in commissioni.

## Cosa cambia per il progetto

**Niente sul verdetto, e questo è il punto.** I confronti del progetto sono
**conservativi nella direzione giusta**: il modello proporzionale usato in
settantatré giri dà al momentum mezzo punto **in meno** di quanto gli darebbe un
broker retail vero. Il momentum perde comunque, e con costi realistici perde di
meno ma perde ancora — nessuna delle celle qui sopra arriva al **+1,00 di mediana**
che il cancello G1 della regola del giro 72 richiede su dodici calendari, e
queste sono tre celle su un calendario solo.

**Ma la lettura ingenua di questo giro sarebbe sbagliata.** «Il momentum guadagna
mezzo punto coi costi veri» non significa che il momentum vada meglio: significa
che **il benchmark scelto è impraticabile**. Un equal-weight su 49 settori non si
compra in azioni singole a €500 al mese, si compra come **fondo**, dove la
commissione fissa è una sola. Il divario di +1,30 non è un vantaggio del
momentum: è l'artefatto di aver fatto pagare al benchmark un modo di
implementarlo che nessuno userebbe.

Lo registro come nota metodologica, non come risultato: **il modello di costo e la
scelta del veicolo non sono separabili**. Ha senso confrontare due strategie con
lo stesso modello di costo solo se entrambe si implementano nello stesso modo, e
qui non è vero. Questo si aggancia direttamente al risultato del giro 71 (il
wrapper aiuta solo se ruoti) e chiude il cerchio: chi sta fermo su 49 posizioni
vuole il fondo per **le commissioni**, non per le imposte.

Nessuna idea nuova da mettere in coda: la domanda che questo giro solleva —
*quanto vale il benchmark implementato come fondo invece che come 49 azioni* — è
già dentro il gruppo K/G sul veicolo, misurata al giro 71.

Nessuna promozione. Nessuna selezione: la griglia (4 strategie × 2 modelli ×
2 varianti) era fissata in anticipo.

**Tentativi cumulati a registro: 1.365.** Holdout 2010-2026 **ancora sigillato**.

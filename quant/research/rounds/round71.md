# Giro 71 — K3: il vantaggio del veicolo con la rotazione vera

**Predizione** (verbatim, committata prima di eseguire): *con la rotazione vera
il vantaggio **cresce** rispetto al +0,34 e finisce fra **+0,5 e +2,0 punti**. Ma
resta **sotto i 2,77** del giro 53, e **sotto il divario momentum-equal-weight**.*
**Falsificata se**: risulta **negativo**, oppure **sopra 2,77**.

**Esito: FALSIFICATA** — una delle due quantità supera 2,77. Ma la ragione per cui
la supera non c'entra con la rotazione, ed è quello il risultato del giro.

## Un errore mio nella voce, dichiarato prima di eseguire

Scrivendo K3 al giro 69 avevo incollato in una sola catena **due quantità
diverse**:

| | definizione | registrato |
|---|---|---:|
| **(a)** spostare la rotazione dentro il fondo | stesso lordo, stesso regime CGT: cambia solo *chi* realizza | **+2,77** |
| **(b)** vantaggio del veicolo | azioni **dirette** contro ETF UCITS | +2,15 → +1,23 → **+0,34** |

La voce dice "*il vantaggio del veicolo cresce rispetto al +0,34… resta sotto i
2,77*": mescola (b) con (a). Non ho riscritto la predizione — l'ho misurate
entrambe, applicata la condizione a entrambe, e dichiarata l'ambiguità **nel
codice prima di guardare i numeri**.

## I risultati, 1969-2026 (683 mesi, la finestra del giro 53)

| configurazione | CAGR | **IRR netta** |
|---|---:|---:|
| momentum, rotazione **mia** (CGT + dividendi) | 12,87% | **10,98%** |
| momentum **dentro un fondo**, CGT | 15,13% | **14,42%** |
| momentum dentro un fondo, ETF UCITS | 15,13% | 11,62% |
| cap-weight **diretto** (CGT + dividendi) | 8,80% | **9,83%** |
| cap-weight via ETF UCITS | 10,98% | 8,74% |

| | valore | esito |
|---|---:|---|
| **(a)** rotazione dentro il fondo | **+3,43** | **falsifica** (sopra 2,77) |
| **(b)** vantaggio delle azioni dirette sull'ETF | **+1,09** | dentro i limiti |

## La correzione della rotazione non serve a niente qui, e ha una ragione

Scomponendo il +3,43:

| | |
|---|---:|
| come il giro 53 (nessuna correzione) | +2,77 |
| **+ rotazione vera** | **+0,00** |
| + dividendi tassati al detentore diretto | **+0,66** |

La rotazione del momentum top-10 passa da **2,676× a 2,828×** l'anno (+5,7%), e
l'effetto sull'IRR è **−0,005 punti**. Praticamente zero.

**Il motivo è preciso, ed è il complemento del giro 63.** Una strategia che
realizza il 22% del portafoglio ogni mese ha il costo fiscale **già azzerato in
continuo**: la base imponibile viene resettata di continuo, quindi spostarla dal
22% al 24% non cambia nulla. La correzione della rotazione conta per i
portafogli **lenti** — al giro 63 valeva 1,35 punti sull'equal-weight a 0,20×/anno
— e **non conta per quelli veloci**. È l'opposto dell'intuizione che avevo scritto
nella predizione ("la correzione colpisce chi ruota in conto proprio").

Quello che porta (a) sopra 2,77 sono i **dividendi**, che il giro 53 non tassava
al detentore diretto: **+0,66**. Una correzione fatta al giro 56 e mai riportata
in questo confronto.

## (b) è confermata su ogni clausola, e cresce con l'orizzonte

| finestra | vantaggio delle azioni dirette sull'ETF |
|---|---:|
| 1990-2023 (registrato) | +0,34 |
| 1990-2026 (registrato) | +0,56 |
| **1969-2026 (qui)** | **+1,09** |

Cresce con l'orizzonte, come STATE.md già annotava. Il meccanismo è il deemed
disposal: **sette cicli** di prelievo forzoso al 41/38% su cinquantasette anni
contro un solo 33% alla fine.

*Nota su un verso che avevo sbagliato nello script*: alla prima stesura avevo
definito (b) come ETF **meno** diretto e ottenuto −1,09, che sembrava
contraddire il +0,34 registrato. Non c'era nessuna contraddizione: STATE.md
definisce il vantaggio come quello **delle azioni dirette sull'ETF**. Corretto il
verso, il numero combacia con la serie registrata e ne è la naturale
prosecuzione.

## Il risultato che resta

**Il wrapper aiuta solo se ruoti.**

| chi sei | conviene |
|---|---|
| ruoti spesso (momentum top-10) | **dentro un fondo**: 11,62% contro 10,98% = **+0,64** |
| stai fermo (cap-weight) | **azioni dirette**: 9,83% contro 8,74% = **+1,09** |

Sono due risultati con segno opposto, e insieme dicono una cosa sola: **l'ETF
UCITS compra il diritto di non realizzare, e lo paga col deemed disposal.** Se
non realizzi comunque, stai comprando un diritto che non usi e paghi il prezzo.

E il termine di paragone che la predizione chiedeva: il divario
momentum-meno-equal-weight è **+1,25 punti**, mentre (a) vale +3,43. La clausola
"resta sotto il divario" è sbagliata — ma va letta bene: (a) **non è un
vantaggio disponibile**, è la misura di quanto costa realizzare. Nessuno può
incassare +3,43 scegliendo un veicolo; può solo evitare di perderli.

Nessuna promozione. Nessuna selezione: N resta la famiglia pre-dichiarata.

**Tentativi cumulati a registro: 1.340.** Holdout 2010-2026 **ancora sigillato**.

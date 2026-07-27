# Giro 46 — A12: il multi-classe su finestre mobili di 20 anni

**Predizione scritta prima** (voce A12, verbatim): *il multi-classe vince in una
minoranza di finestre — fra il 15% e il 35% — e sono tutte e sole quelle centrate
sui due mercati orso lunghi (1969-1982 e 2000-2012). L'ampiezza fra la finestra
migliore e la peggiore supera 6 punti.* **Falsificata se**: vince in più della metà
delle finestre, oppure in nessuna.

**Esito: CONFERMATA sul test di falsificazione — e tutte e tre le clausole
descrittive sono sbagliate.**

## Un vincolo di dati, dichiarato prima dei numeri

La voce chiede la ricostruzione migliorata del giro 45, che per il termine di
rolldown usa la pendenza 10-2 anni e quindi richiede **DGS2, disponibile solo dal
1976**. Il campione scende da 1962-2026 a **1976-2026**: **32 finestre invece delle
44** che avrei avuto con la ricostruzione semplice.

La conseguenza è che **la prima metà della clausola (b) non era testabile**: la
finestra più vecchia è 1976-1995, con punto medio 1985,5. **Nessuna finestra ha il
punto medio dentro il 1969-1982.** Ho scritto una predizione che nominava un
periodo che i dati richiesti dalla predizione stessa non contengono.

## Risultati — 32 finestre di 20 anni, passo 1 anno

Ogni finestra è un **PAC completo e indipendente**: chi comincia a versare €500 al
mese nel gennaio dell'anno Y e smette venti anni dopo. I pesi si ristimano dentro
la finestra, quindi i primi 36 mesi girano a pesi uguali — esattamente come
capiterebbe a quell'investitore, che il giorno in cui apre il conto non ha una
covarianza stimata.

| allocazione | finestre | vinte | quota | divario medio | peggiore | migliore | ampiezza |
|---|---:|---:|---:|---:|---:|---:|---:|
| ERC | 31 | 15 | **48,4%** | −0,37% | −5,62% | +4,39% | **10,01** |
| 60/40 | 31 | 13 | 41,9% | −0,48% | −3,18% | +2,32% | 5,50 |
| inverse-vol | 31 | 12 | 38,7% | −1,00% | −5,95% | +3,24% | 9,19 |
| equal-weight | 31 | 11 | 35,5% | −0,69% | −4,14% | +2,63% | 6,77 |

Nessuna allocazione vince in più della metà delle finestre, nessuna vince in
nessuna. **A12 confermata.**

## Le tre clausole, una per una

| clausola | prevista | osservata |
|---|---|---|
| (a) quota di vittorie | 15-35% | **35,5% – 48,4%** |
| (b) tutte e sole centrate sui mercati orso | sì | **no**, 6-7 su 11-15 |
| (c) ampiezza oltre 6 punti | sì | **5,50 – 10,01**, sotto 6 per il 60/40 |

**L'ERC vince quasi una volta su due.** Avevo previsto una minoranza netta e ho
trovato qualcosa che assomiglia a un lancio di moneta. Il divario medio è −0,37
punti: su vent'anni, la differenza fra ERC e azionario puro è, in media, **poco più
di un terzo di punto l'anno** — non i 3,63 punti del giro 44 sulla finestra intera.

Questo non contraddice i giri 44 e 45: sono la stessa cosa vista su due orizzonti
diversi. Su 64 anni consecutivi la capitalizzazione composta amplifica un divario
piccolo e persistente; su vent'anni quel divario è dentro il rumore delle
condizioni iniziali.

L'ampiezza (5,50-10,01 punti) è comunque **molto più grande del divario medio**
(0,37-1,00): la clausola che contava è vera, anche se il numero di soglia era
sbagliato per una delle quattro allocazioni.

## Il risultato vero, che non avevo previsto

Guardando **quali** finestre vince, il criterio non è dove sono centrate. È **quando
finiscono**.

L'ERC vince in 15 finestre, e sono **tutte e sole quelle che iniziano fra il 1983 e
il 1997** — cioè quelle che **finiscono fra il 2002 e il 2016**. Le finestre che
finiscono dopo il 2019 perdono tutte, e pesantemente:

```
1976  1995   -1.10%   ---
1980  1999   -3.50%   ----------
1983  2002   +1.75%   +++++
1990  2009   +4.39%   +++++++++++++   (la migliore)
1997  2016   +0.44%   +
2001  2020   -2.63%   -------
2005  2024   -5.16%   ---------------
2006  2025   -5.62%   ----------------  (la peggiore)
```

**Per un PAC conta la fine, non il centro.** È una conseguenza diretta della
struttura di un piano di accumulo: dopo vent'anni di versamenti il capitale è al
massimo, quindi i rendimenti degli ultimi anni pesano su una somma enorme e quelli
dei primi su quasi niente. Una finestra che si chiude nel 2009 valuta il
portafoglio subito dopo un crollo del 50%, e lì la sleeve obbligazionaria ha
appena fatto il suo lavoro sulla parte di capitale che conta. Una finestra che si
chiude nel 2025 valuta dopo quindici anni di rialzo azionario quasi ininterrotto.

Avevo scritto "centrate sui mercati orso" pensando al periodo *attraversato*. Il
meccanismo giusto è il **rischio di sequenza dei rendimenti**, e riguarda solo la
coda del piano. Ho aggiunto **A13** in coda per misurarlo direttamente invece di
dedurlo da questa tabella.

## Cosa vuol dire, per chi versa €500 al mese

La conclusione dei giri 44-45 — "l'azionario puro vince" — resta vera **in media**,
ed è quella su cui scommettere se non si hanno informazioni sul futuro. Ma su un
orizzonte di vent'anni è vera **poco più di una volta su due**, e il caso peggiore
per chi sceglie l'azionario puro è di 4,4 punti l'anno peggiore dell'ERC.

Il che è un modo diverso di dire una cosa già trovata al giro 33: la differenza
fra le allocazioni è piccola rispetto alla dispersione di quello che il mercato
fa, e **la variabile che l'investitore controlla davvero non è quale portafoglio
scegliere, è quanto versa e per quanto tempo**.

## Contabilità

Le 32 finestre si sovrappongono fino a 19 anni su 20: **le osservazioni non sono
indipendenti**, il numero effettivo è vicino a 3. La quota di vittorie è
descrittiva, non un test, e non ci calcolo p-value sopra — D1 è stata falsificata
proprio per non aver visto un problema di questo tipo, e non lo ripeto.

**Nessun candidato esce da qui.** Scegliere la finestra migliore fra 32
sovrapposte è esattamente la selezione che il DSR esiste per punire.

Turnover 0,13-0,16 volte l'anno, sotto la soglia del 100%: aliquota di riferimento
33%, scenario 52% comunque calcolato e salvato in `out/round46_a12.csv`.

**Tentativi cumulati a registro: 866.** Holdout 2010-2026 **ancora sigillato**.

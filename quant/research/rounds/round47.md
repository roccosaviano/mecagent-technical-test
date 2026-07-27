# Giro 47 — A13: il rischio di sequenza, misurato invece che dedotto

**Predizione scritta prima** (voce A13, verbatim): *il coefficiente sugli ultimi 3
anni è negativo, di modulo almeno 4 volte quello sui primi 3, e da solo spiega
oltre metà della varianza del divario fra finestre. Sulla finestra estesa
1962-2026 la quota di vittorie del multi-classe sale sopra il 50%.*
**Falsificata se**: i due coefficienti hanno modulo comparabile (rapporto sotto 2),
o se il segno di quello sugli ultimi 3 anni è positivo.

**Esito: FALSIFICATA.** La terza falsificazione della coda, e la più informativa.

## Il meccanismo, verificato senza regressione

Prima dei dati di mercato, l'aritmetica del piano di accumulo. Con versamenti
costanti per 20 anni, la quota di capitale-anni esposta al mercato in ciascun anno:

| | quota |
|---|---:|
| primi 3 anni | **2,9%** |
| ultimi 3 anni | **27,1%** |
| **rapporto** | **9,50×** |

Il meccanismo che avevo proposto è reale e non dipende da nessun dato: gli ultimi
tre anni di un PAC ventennale pesano **nove volte e mezzo** i primi tre. Se il
divario fra allocazioni fosse governato da quel peso, il rapporto fra i
coefficienti dovrebbe avvicinarsi a 9,5.

## Cosa dicono i dati

**Finestra estesa 1962-2026, ricostruzione semplice — 45 finestre:**

| alloc | vinte | quota | b(ultimi 3) | b(primi 3) | rapporto | R² solo ultimi | R² entrambi |
|---|---:|---:|---:|---:|---:|---:|---:|
| ERC | 14/45 | 31,1% | **−0,116** | +0,071 | **1,65** | 0,299 | 0,390 |
| inverse-vol | 6/45 | 13,3% | −0,102 | +0,054 | 1,89 | 0,305 | 0,377 |
| 60/40 | 6/45 | 13,3% | −0,067 | +0,025 | 2,71 | 0,325 | 0,365 |
| equal-weight | 6/45 | 13,3% | −0,077 | +0,033 | 2,36 | 0,302 | 0,350 |

**Finestra del giro 46, 1976-2026, ricostruzione migliorata — 31 finestre:**
rapporti **1,21 · 1,26 · 1,78 · 1,53**, tutti sotto 2.

**Falsificata**: cinque rapporti su otto stanno sotto 2. Il segno è quello giusto —
b(ultimi 3) è negativo in tutti e otto i casi — ma la magnitudine no.

## L'errore che ho fatto, ed è concettuale

Ho confuso due affermazioni diverse:

1. **Il rischio di sequenza determina il risultato di un PAC.** Vero, e il rapporto
   è 9,5:1 — pura aritmetica dei versamenti.
2. **Il rischio di sequenza determina quale allocazione vince.** Molto più debole:
   il rapporto misurato è **1,2-2,7:1**.

La differenza fra le due è che il *divario* fra due allocazioni non è un montante:
è la differenza fra due montanti che percorrono **lo stesso identico sentiero di
prezzi**. Il peso del capitale agisce su entrambi allo stesso modo e in buona parte
si cancella. Quel che resta è la differenza di **esposizione**, che dipende da quando
le due allocazioni divergono, non da quando il capitale è grande.

E infatti **b(primi 3) è positivo**, non trascurabile: un rendimento azionario forte
nei primi tre anni migliora l'allocazione *rispetto* all'azionario puro. I due
estremi del piano contano in versi opposti, non uno solo.

L'R² dei soli ultimi tre anni è **0,28-0,33**: due terzi della varianza del divario
fra finestre è qualcos'altro. Avevo previsto oltre la metà.

## Le 14 finestre recuperate, e un errore ripetuto

La voce prometteva che estendere il campione al 1962 avrebbe aggiunto "le finestre
che finiscono nel 1974-1982" e portato la quota di vittorie sopra il 50%. Le
finestre recuperate sono queste:

| inizio | fine | ERC | azionario | divario |
|---:|---:|---:|---:|---:|
| 1962 | 1981 | 3,15% | 6,09% | −2,94% |
| 1966 | 1985 | 7,36% | 9,25% | −1,89% |
| 1970 | 1989 | 8,97% | 11,57% | −2,60% |
| 1975 | 1994 | 9,02% | 11,34% | −2,32% |

**Vinte dal multi-classe: 0 su 14.** La quota di vittorie **scende** — da 35,5-48,4%
del giro 46 a **13,3-31,1%** — invece di salire sopra il 50%. Direzione opposta a
quella prevista.

E il motivo è lo stesso errore del giro 46, fatto due volte di fila: **con finestre
di 20 anni che partono dal 1962, la fine più vecchia possibile è il 1981.** Le
"finestre che finiscono nel 1974-1982" che avevo promesso non esistono nella
geometria che avevo specificato — ne esiste una sola, 1962-1981. Ho nominato un
periodo che il disegno del test non può produrre, esattamente come al giro 46 avevo
nominato finestre "centrate sul 1969-1982" quando nessuna finestra poteva averci il
punto medio.

**È il difetto ricorrente delle mie predizioni in questa coda**: non sbaglio il
verso, sbaglio i numeri e ogni tanto specifico condizioni che il disegno rende
impossibili. Registrato in STATE.md.

## Cosa resta in piedi

Il fatto che le finestre 1962-1975 perdano tutte rafforza, non indebolisce, la
conclusione dei giri 44-45: su **45 finestre di 20 anni**, l'ERC batte l'azionario
in 14 e le altre tre allocazioni in 6 su 45. Il quadro complessivo è più duro per
il multi-classe di quanto sembrasse al giro 46, che guardava solo il 1976-2026.

Ma la spiegazione del *perché* certe finestre vincono resta aperta: non è (solo) il
rischio di sequenza. Ho aggiunto **A14** in coda per separare le due affermazioni
che ho confuso — la stessa regressione applicata al **livello** dell'IRR invece che
al divario, dove il rapporto 9,5:1 dovrebbe comparire.

## Contabilità

Le finestre si sovrappongono fino a 19 anni su 20: **nessun p-value, nessun errore
standard**. I coefficienti descrivono la forma dei dati, non provano una relazione.
Nessun candidato esce da qui. Turnover 0,13-0,16 volte l'anno, sotto la soglia del
100%; scenario 52% calcolato e salvato in `out/round47_finestre_estese.csv`.

**Tentativi cumulati a registro: 874.** Holdout 2010-2026 **ancora sigillato**.

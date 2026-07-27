# Giro 45 — A11: di quanto dovrebbe rendere di più la sleeve obbligazionaria

**Predizione scritta prima** (voce A11, verbatim): *il pareggio richiede oltre 3
punti l'anno in più sulla sleeve obbligazionaria per ERC e inverse-vol, cioè da 4 a
10 volte lo scarto plausibile del proxy. Il difetto di ricostruzione quindi non
spiega il divario.* **Falsificata se**: il rendimento aggiuntivo richiesto sta sotto
1 punto l'anno per almeno una delle quattro allocazioni.

**Esito: CONFERMATA.**

## Perché questo giro esiste

Il giro 44 ha attribuito l'84-92% della perdita delle allocazioni multi-classe alla
**composizione**, cioè al fatto che il decennale rende meno dell'azionario. Ma il
decennale che uso è una **ricostruzione a duration costante da DGS10**, che omette
convessità e rolldown. Se quell'omissione fosse grande, il giro 44 starebbe
misurando un difetto del mio proxy invece di un fatto sui mercati.

Il test è il confronto fra due misure indipendenti: **quanto servirebbe** contro
**quanto manca**.

## (2) Lo scarto del proxy, misurato invece che citato

Nella voce di coda avevo scritto "in letteratura 0,3-0,8 punti l'anno". Invece di
fidarmi di quel numero l'ho misurato, costruendo una seconda ricostruzione con i due
termini mancanti:

```
semplice     r = y/12 − D·dy
migliorata   r = y/12 − D·dy + ½·C·dy²  +  D·(y₁₀ − y₂)/8/12
                              convessità        rolldown
```

| | rendimento annuo |
|---|---:|
| ricostruzione semplice | 6,00% |
| ricostruzione migliorata | 7,58% |
| **scarto del proxy** | **+1,58 punti** (convessità +0,59 · rolldown +0,98) |

Volatilità 10,1% contro 10,2%, correlazione **0,9990**: i due termini aggiungono
rendimento senza cambiare il profilo di rischio, che è esattamente quello che ci si
aspetta.

**Il numero che avevo citato in coda era troppo stretto**: 1,58 punti è il doppio
del limite superiore di quel "0,3-0,8". Non cambia il verdetto, ma è una stima che
avevo tirato a indovinare invece di misurare, e va detto.

Anzi, va detto di più: **7,58% annuo per un decennale fra il 1962 e il 2026 è
probabilmente troppo alto** (le serie storiche di riferimento stanno intorno al
6,0-6,5%). Il mio termine di rolldown applica l'intera duration alla pendenza 10-2
mensilizzata, e per un titolo tenuto un mese è generoso. **L'errore va nella
direzione conservativa per la tesi che sto testando**: sto regalando rendimento
alla sleeve obbligazionaria, e la conclusione tiene lo stesso.

## (1) Il pareggio: quanto servirebbe

Per ogni allocazione, bisezione su α = rendimento annuo costante aggiunto alla
sleeve obbligazionaria, rieseguendo **tutta** la pipeline (pesi ristimati compresi,
perché cambiare il rendimento del decennale cambia anche la deriva dei pesi fra un
ribilanciamento e l'altro). IRR azionario 100%: **10,48%**.

| allocazione | IRR base | divario | **α di pareggio** | multiplo dello scarto |
|---|---:|---:|---:|---:|
| ERC | 6,85% | 3,63 | **6,52% annuo** | 4,1× |
| inverse-vol | 6,52% | 3,96 | **6,69% annuo** | 4,3× |
| 60/40 | 7,84% | 2,64 | **6,96% annuo** | 4,4× |
| equal-weight | 7,36% | 3,12 | **6,62% annuo** | 4,2× |

Il decennale dovrebbe rendere **6,5-7,0 punti l'anno in più** di quanto ha reso.
Con 6,00% di base, significherebbe un decennale al **12,5-13% annuo per 64 anni**.

Il multiplo dello scarto misurato è **4,1× – 4,4×**, dentro la banda 4-10× prevista
ma sul suo bordo inferiore — perché lo scarto vero (1,58) è più grande di quello
che avevo assunto (0,3-0,8). Se avessi usato il numero citato, il multiplo sarebbe
stato 8-22×.

## La controprova diretta

Invece di ragionare per multipli: **uso la ricostruzione migliorata al posto della
semplice** e rieseguo tutto.

| | IRR con decennale migliorato | azionario | differenza |
|---|---:|---:|---:|
| ERC | 8,11% | 10,94% | **−2,83** |
| inverse-vol | 7,50% | 10,94% | −3,44 |
| 60/40 | 8,55% | 10,94% | −2,39 |
| equal-weight | 8,15% | 10,94% | −2,79 |

Regalando alla sleeve obbligazionaria 1,58 punti l'anno di convessità e rolldown —
probabilmente più di quanto le spetti — **l'allocazione multi-classe resta 2,4-3,4
punti sotto l'azionario puro**. Il recupero è di circa 1,2 punti su un divario di
3-4: chiude un terzo del buco e ne lascia due terzi.

## Cosa chiude, e cosa no

**Chiude**: la conclusione del giro 44 non è un artefatto del proxy obbligazionario.
Con una ricostruzione migliore, e anche con una ricostruzione generosa, le
allocazioni multi-classe restano sotto.

**Non chiude**: tutto questo vale per il campione **1962-2026**, che contiene sia il
più lungo mercato toro obbligazionario della storia sia un premio azionario
altissimo. Il fatto che l'azionario abbia vinto in questa finestra non è
un'affermazione su quale sia l'allocazione giusta per i prossimi trent'anni — è la
misura di cosa sarebbe successo in quella passata. Ho aggiunto **A12** in coda per
misurare in quante finestre mobili di 20 anni l'allocazione multi-classe avrebbe
invece vinto: è la domanda che resta aperta, ed è più onesta di una media su 64 anni.

**Tentativi cumulati a registro: 862.** Holdout 2010-2026 **ancora sigillato**.

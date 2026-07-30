# Giro 83 — O5: quanti punti di alfa lordo servono per farne uno netto

**Predizione** (verbatim, committata al giro 80): *sotto 1,0× serve **meno di 2
punti** di alfa lordo per farne uno netto; sopra 1,0× ne servono **più di 3**; e a
3,5× ne servono **fra 4 e 6**. Il salto attraverso la soglia vale **almeno 1,0
punto**.*
**Falsificata se**: il rapporto fra la richiesta a 3,5× e quella a 0,5× sta
**sotto 2** — **oppure** se il salto alla soglia vale **meno di 0,5 punti**.

**Esito: CONFERMATA sul ramo che falsifica. Una clausola descrittiva è sbagliata,
e sbagliarla è istruttivo.**

## Un errore aritmetico nella voce, dichiarato prima di eseguire

La voce dice «quattordici combinazioni × sei livelli di alfa = **42 celle**», ma
le rotazioni elencate sono **sette**, e 14 × 6 fa 84. Il totale dichiarato è
coerente con 7 × 6. Ho usato la griglia che il totale implica, senza aggiungere
rotazioni che la voce non elenca.

## La griglia: margine netto per alfa lordo × rotazione

Benchmark: equal-weight annuale vero, rotazione 0,074×, aliquota 33%, IRR 10,09%.
Il flusso sintetico è il benchmark moltiplicato per un alfa geometrico costante,
con rotazione imposta e il motore fiscale che decide da solo lo scaglione.

| rotaz. | aliq. | a=0 | a=1 | a=2 | a=4 | a=6 | a=8 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0,2× | 33% | −0,51 | +0,45 | +1,42 | +3,35 | +5,30 | +7,27 |
| 0,5× | 33% | −0,89 | +0,05 | +0,96 | +2,77 | +4,58 | +6,42 |
| 0,9× | 33% | −1,16 | −0,25 | +0,66 | +2,47 | +4,25 | +6,01 |
| **1,1×** | **52%** | **−2,55** | −1,73 | −0,92 | +0,69 | +2,29 | +3,87 |
| 2,0× | 52% | −2,81 | −2,01 | −1,23 | +0,34 | +1,90 | +3,44 |
| 3,5× | 52% | −3,07 | −2,29 | −1,51 | +0,03 | +1,55 | +3,06 |
| 6,0× | 52% | −3,40 | −2,63 | −1,86 | −0,34 | +1,16 | +2,65 |

## Il numero operativo: il tasso di cambio

| rotazione | aliquota | **alfa lordo per +1,00 netto** |
|---|---:|---:|
| 0,2× | 33% | **1,57** |
| 0,5× | 33% | **2,04** |
| 0,9× | 33% | **2,38** |
| **1,1×** | **52%** | **4,39** |
| 2,0× | 52% | **4,85** |
| 3,5× | 52% | **5,27** |
| 6,0× | 52% | **5,78** |

**Il salto attraverso la soglia del 100% vale +2,01 punti di alfa richiesto.**
Passare da 0,9× a 1,1× — un aumento di rotazione del 22% — costa **più che
quadruplicare la rotazione da 0,2× a 0,9×**, che ne costa 0,81.

Detto in una riga: **attraversare il 100% di rotazione quasi raddoppia l'alfa
lordo che serve per battere il benchmark di un punto.**

## La clausola sbagliata, e perché sbagliarla è istruttivo

Avevo previsto che **sotto** la soglia servisse *meno di 2 punti*. Misurato: 1,57
a 0,2×, ma **2,04** a 0,5× e **2,38** a 0,9×. Solo la rotazione più bassa sta
sotto 2.

Il che significa: **anche muovendosi pochissimo, il conto è già di due a uno.**
Un portafoglio che ruota mezza volta l'anno — cioè che tocca metà delle posizioni
in dodici mesi, un ribilanciamento lento e ragionevole — deve produrre **due punti
di alfa lordo** per consegnarne uno. Non è il 52% a rendere il gioco duro: il
gioco è duro **anche al 33%**, e la soglia lo rende soltanto proibitivo.

Nota anche la colonna a=0: una strategia che ruota **senza nessun alfa** perde da
**−0,51** (a 0,2×) a **−3,40** (a 6,0×) contro un benchmark che sta fermo. Quello
è il prezzo del movimento in sé.

## Il controllo con il giro 80, e una cautela che ne esce

Il candidato reale aveva **6,50 punti di alfa lordo a 3,28× di rotazione** e ha
consegnato **+1,18**. La curva sintetica a 3,5× dice che con 6 punti si ottengono
**+1,55**, e con 6,50 circa **+1,9**.

**Il sintetico è ottimista di circa 0,8 punti.** La ragione è che impone un alfa
**costante ogni mese**, mentre l'alfa vero è grumoso e volatile: il candidato ha
il 21,07% di volatilità contro il 16,07% del benchmark, e un vantaggio irregolare
realizzato con rotazione alta paga imposte nei momenti sbagliati.

Quindi la curva qui sopra è un **limite inferiore**: il tasso di cambio vero per
una strategia reale a 3,5× non è 5,27 ma qualcosa come **6,0-6,5**. Lo registro
come cautela e come voce nuova (**O8**), perché la differenza fra alfa costante e
alfa volatile è misurabile e non l'ho misurata.

## Cosa dice questo di tutto il progetto

Ottantatré giri riassunti in un numero: **per battere un PAC buy&hold di un punto
l'anno netto, ruotando come ruota una strategia momentum concentrata, serve un
alfa lordo di sei punti l'anno.** Prima di costi, prima di imposte, ogni anno, per
vent'anni.

Il miglior candidato che il progetto abbia mai prodotto ne aveva 6,50 in campione
— quindi era **esattamente al limite** — e fuori campione ne aveva **0,31**.

## Il verdetto

| clausola | previsto | misurato | |
|---|---|---|---|
| sotto 1,0× serve meno di 2 | sì | 1,57 / **2,04** / **2,38** | **SBAGLIATA** |
| sopra 1,0× servono più di 3 | sì | 4,39 / 4,85 / 5,27 / 5,78 | **centrata** |
| a 3,5× fra 4 e 6 | sì | **5,27** | **centrata** |
| salto alla soglia ≥ 1,0 | sì | **+2,01** | **centrata** |
| rapporto 3,5×/0,5× sotto 2 → falsifica | no | **2,58×** | non scatta |

**Tentativi cumulati a registro: 1.501.** Holdout **bruciato al giro 78**, non
interrogato in questo giro.

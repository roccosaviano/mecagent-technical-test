# Giro 78 — N1: l'holdout, aperto una volta sola

**Predizione** (verbatim, committata al giro 77 prima di guardare qualunque cosa
del 2010-2026): *il margine sull'holdout è **negativo, fra −3 e 0 punti**. Prevedo
inoltre che la **rotazione resti sopra 1,0×** (aliquota 52%) e che il **drawdown**
del candidato sia **peggiore** di quello del benchmark.*
**Falsificata se**: il margine è **positivo e sopra +1,00** — oppure positivo ma
sotto +1,00, esito intermedio da registrare come tale.

**Esito: CONFERMATA. Margine −0,95, dentro la banda prevista, negativo in 12
calendari su 12.**

Dopo settantotto giri e 1.402 tentativi registrati, l'holdout è stato aperto una
volta sola, su un candidato solo, e **il candidato ha perso**.

## Il risultato

| | gen | feb | mar | apr | mag | giu | lug | ago | set | ott | nov | dic |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| benchmark | 10,83 | 10,71 | 10,90 | 10,93 | 10,92 | 10,85 | 10,76 | 10,79 | 10,82 | 10,91 | 10,82 | 10,85 |
| **margine** | −0,94 | −0,82 | −1,01 | −1,04 | −1,03 | −0,96 | −0,86 | −0,90 | −0,93 | −1,02 | −0,92 | −0,96 |

**Mediana −0,95.** Negativo in **12 calendari su 12**, in una banda strettissima
(−1,04 … −0,82): non è un artefatto di calendario, e non c'è un mese fortunato da
scegliere. Il verso è lo stesso ovunque.

| | candidato | benchmark |
|---|---:|---:|
| IRR netta (aliquota applicabile) | **9,89%** (52%) | **10,84%** (33%) |
| rotazione | 3,804× | 0,06× |
| CAGR lordo | **13,65%** | 13,34% |
| volatilità | 21,07% | 16,07% |
| Sharpe | 0,72 | **0,86** |
| max drawdown | **−31,38%** | −25,50% |

## Le tre clausole

| clausola | previsto | misurato | |
|---|---|---|---|
| margine negativo, fra −3 e 0 | sì | **−0,95** | **centrata** |
| rotazione sopra 1,0× (aliquota 52%) | sì | **3,804×**, 52% | **centrata** |
| drawdown peggiore del benchmark | sì | −31,38% contro −25,50% | **centrata** |

Tre su tre. È la seconda volta in tutto il progetto che tutte le clausole di una
voce sono centrate (la prima fu E1, il premio al rischio di varianza).

## Il numero che chiude il progetto

**Il premio lordo è sopravvissuto. L'investitore no.**

Sul CAGR lordo il candidato batte ancora il benchmark: **13,65% contro 13,34%**,
cioè **+0,31 punti**. Il segnale non è morto fuori campione — si è solo
assottigliato.

E poi c'è il controfattuale, che è la frase più affilata di settantotto giri:

> **Anche pagando il 33% invece del 52%, il candidato avrebbe fatto +0,90 — sotto
> il suo stesso cancello.** IRR a 33%: 11,73% contro 10,83% del benchmark.

Cioè: nemmeno in un mondo in cui ruotare 3,8 volte l'anno non facesse scattare la
riqualificazione a reddito d'impresa, questa strategia sarebbe passata. La soglia
di +1,00 punto fissata al giro 72 — scelta perché era sopra il rumore di misura
del progetto, non perché fosse comoda — l'avrebbe respinta lo stesso, per un
decimo di punto.

*(IRR e CAGR non sono la stessa metrica — money-weighted contro time-weighted —
quindi la differenza fra le due colonne non è «il costo fiscale». Il confronto che
conta è a metrica uguale: −0,95 con le aliquote vere, +0,90 con la stessa aliquota
per entrambi.)*

## G3, il cancello più forte in campione, è quello che crolla

| | train 1969-2009 | holdout 2010-2026 |
|---|---:|---:|
| finestre decennali positive | **93,1%** (27 su 29) | **37,5%** (3 su 8) |
| mediana degli extra | **+2,23** | **−0,16** |

Finestre decennali dentro l'holdout:

| 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| −2,43 | −1,79 | −3,49 | +1,44 | −0,03 | −0,28 | +0,51 | +0,22 |

Al giro 77 avevo previsto che G3 sarebbe stato **il cancello che uccideva il
candidato**, e G3 è il cancello che ha passato con il margine più largo: 93,1%
contro una soglia del 66,7%. Fuori campione la stessa misura fa **37,5%**.

**Un cancello che passa al 93% in campione e al 37% fuori non stava misurando la
stabilità: stava misurando il campione.** La ragione è nota dal giro 59 e non
l'avevo collegata: le ventinove finestre decennali del train si sovrappongono
quasi tutte fra loro, quindi «ventisette successi su ventinove» non sono
ventisette prove indipendenti — sono lo stesso pezzo di storia contato ventisette
volte. Era il difetto di D1 (85,5% di sovrapposizione media), applicato a un
cancello invece che a un'ipotesi.

## Train contro holdout, in cinque righe

| | train 1969-2009 | holdout 2010-2026 |
|---|---:|---:|
| IRR del candidato | 11,27% | 9,89% |
| **margine (mediana 12 calendari)** | **+1,18** | **−0,95** |
| rotazione | 3,284× | 3,804× |
| aliquota | 52% | 52% |
| max drawdown | −59,40% | −31,38% |

Lo scarto è di **2,13 punti**, ed è dello stesso ordine dei gradi di libertà che il
progetto ha misurato uno per uno: 3,94 lo skip (giro 76), 3,65 il calendario su un
top-5 (giro 68), 5,81-10,19 la finestra temporale (giro 59). **Il candidato non è
stato smentito da un evento raro: è rientrato nella dispersione che era già stata
misurata tre volte.**

## Cosa vale, adesso, il difetto di G2

Al giro 77 avevo messo a verbale — **prima** di conoscere questo risultato — che
il DSR protegge dalla selezione sbagliata: `var_sr` è stimata sulla dispersione
degli **Sharpe**, minuscola, mentre la selezione era avvenuta sui **margini di IRR
netta**, che nella famiglia variavano di 4,27 punti. Il DSR diede **0,9907**.

Il candidato ha poi perso di 0,95 fuori campione. Il difetto non è più
un'osservazione teorica: è **la spiegazione di come un candidato con DSR 0,9907
possa fallire**. Va misurato, ed è la voce O1.

## Il verdetto

**La conclusione del progetto non cambia, e adesso ha un test fuori campione a
sostenerla**: nessuna strategia attiva, fra le 1.402 configurazioni registrate,
batte un PAC buy&hold netto di fiscalità irlandese. L'unico candidato che sia mai
arrivato ai quattro cancelli li ha passati tutti in campione e ha perso **−0,95**
fuori, in dodici calendari su dodici, restando sotto la soglia anche
nell'ipotesi fiscale più generosa.

**L'holdout 2010-2026 è ora bruciato. Non si riapre.** Ogni voce successiva lavora
solo su 1969-2009.

**Tentativi cumulati a registro: 1.402.**

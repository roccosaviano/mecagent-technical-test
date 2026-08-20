# PAC 10.000 € + 700 €/mese — S&P 500, SPMO, SPXL

Banco di prova per una domanda semplice: *metto 10.000 € subito e 700 € al mese,
dove finisco fra 5, 10 e 15 anni?* — con tre strumenti diversi (indice puro,
momentum, leva 3x).

```
pip install numpy pandas requests      # unico prerequisito
python3 pac_data.py                    # scarica e mette in cache i dati in data/
python3 pac_lab.py                     # esegue lo studio -> out/pac_results.json
python3 pac_report.py                  # genera la pagina -> out/report.html
```

`pac_lab.py` stampa già tutte le tabelle a schermo; `out/report.html` è una
pagina autonoma (SVG inline, nessuna risorsa esterna) con gli stessi numeri più
i grafici.

## Che cosa fa, in una riga

Invece di scegliere un rendimento medio e proiettarlo, simula **lo stesso PAC a
partire da ogni singolo mese dal 1926 a oggi** e guarda la distribuzione dei
risultati: ~1.100 PAC completi per strumento su ogni orizzonte.

Il motivo è che un PAC non incassa la media, incassa la *sequenza*: i versamenti
degli ultimi anni pesano più di quelli dei primi, quindi lo stesso insieme di
rendimenti in ordine diverso produce montanti diversi. Su un prodotto a leva
questo smette di essere un dettaglio.

## Da dove vengono le serie

| serie | origine |
|---|---|
| fattori giornalieri (mercato USA total return, T-bill, momentum) | Ken French Data Library, dal 1926 |
| prezzi reali SPY / SPMO / SPXL | API Nasdaq, ultimi 10 anni |
| CPI USA | FRED `CPIAUCNS` |
| cambio EUR/USD | FRED `DEXUSEU`, dal 1999 |

Gli ETF non esistevano nel 1926 (SPMO è del 2015, SPXL del 2008), quindi le serie
lunghe sono **ricostruite**:

- **S&P 500** = fattore di mercato riscalato sul beta di SPY (0,96), meno il TER.
- **SPMO** = mercato + momentum con i pesi stimati su SPMO reale (beta mercato
  1,00, beta momentum 0,30), meno il TER, più i residui veri ripescati a caso
  con seme fisso perché il modello a due fattori spiega l'84% della varianza e il
  resto è rischio specifico che va rimesso.
  **L'alpha campionario (+3,3%/anno) è azzerato**: è figlio di un decennio d'oro
  per il momentum, proiettarlo per quindici anni sarebbe barare.
- **SPXL** = formula del 3x a reset giornaliero sull'indice: `3·r − 2·(T-bill +
  0,5%) − TER`, con floor a −100%.

### Validazione (2016-2026, 2.477 sedute)

| ETF | CAGR vero | ricostruito | vol vera | ricostruita | corr. giornaliera |
|---|---|---|---|---|---|
| SPY | 14,74% | 14,76% | 18,1% | 18,0% | 0,9932 |
| SPMO | 20,70% | 21,12% | 20,8% | 19,0% | 0,9169 |
| SPXL | 28,77% | 28,21% | 53,7% | 53,9% | 0,9943 |

(qui il modello gira completo, alpha incluso: serve a misurare la replica, non a
fare la previsione.)

## Risultati in sintesi — 15 anni, 136.000 € versati

| | p5 | mediana | p95 | IRR mediano | calo max tipico | P(sotto il versato) |
|---|---|---|---|---|---|---|
| S&P 500 | 192.203 | 348.947 | 576.549 | 10,8% | −33% | 0,2% |
| SPMO | 216.625 | 414.499 | 1.105.564 | 12,7% | −37% | 0,7% |
| SPXL | 91.456 | 709.988 | 5.957.394 | 18,4% | −82% | 11,5% |

Due numeri che valgono più della tabella:

- **SPMO senza premio momentum vale come l'S&P 500** (346.412 contro 348.947 di
  mediana). Tutto il suo vantaggio è un parametro solo.
- **Il peggior PAC in SPXL** (partenza marzo 1994) ha versato 136.000 € e ne ha
  riportati 22.813. Quello in S&P 500, nel suo peggior caso, ne ha riportati
  134.444.

## Limiti dichiarati

- Cento anni di storia americana sono *un solo* percorso, e le finestre si
  sovrappongono: le frequenze qui dentro non sono probabilità.
- Il costo della leva è tarato sul 2016-2026; nei periodi di tassi altissimi
  (1979-1982) potrebbe essere ottimista.
- Tutto al lordo del bollo titoli, e con l'ipotesi che i versamenti non si
  interrompano mai — che nel caso peggiore vuol dire continuare a versare 700 €
  al mese dentro un −80%.
- SPMO e SPXL sono ETF statunitensi: senza KID un broker europeo non li vende al
  dettaglio. I sostituti UCITS costano qualche decimo di punto in più all'anno.

Non è consulenza finanziaria: è un banco di prova.

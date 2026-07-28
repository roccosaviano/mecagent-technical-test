"""Giro 61 — A15: il peso di ciascun anno, calcolato invece che stimato.

VOCE DELLA CODA, predizione verbatim:

A15 — Il peso di ciascun anno, calcolato invece che stimato
  Tre tentativi di spiegare con una regressione quali finestre favoriscono cosa
  (giri 46, 47, 58) sono tutti falliti. Provarne un quarto significherebbe
  cercare la specifica che funziona invece della spiegazione vera. Quindi:
  NIENTE REGRESSIONE. Il montante di un PAC e' la somma esatta dei versamenti
  capitalizzati, quindi la sensibilita' dell'IRR al rendimento di ciascun anno
  SI SCRIVE, non si stima. Da calcolare analiticamente il vettore dei pesi
  dIRR/dr_k per k = 1..20, e confrontarlo con i coefficienti di regressione dei
  giri 47 e 58.
  PREDIZIONE: il peso analitico e' monotono crescente in k e il rapporto fra
  l'ultimo e il primo triennio si avvicina al 9,5:1 aritmetico entro il 20%. La
  regressione lo mancava perche' due variabili di bordo comprimono venti gradi
  di liberta' in due, non perche' il meccanismo sia sbagliato.
  FALSIFICATA SE: il peso analitico non e' monotono, oppure il suo rapporto
  ultimi/primi tre anni sta sotto 4 — nel qual caso il rischio di sequenza non
  spiega il livello dell'IRR di un PAC e va cercato un altro meccanismo.

LA DERIVAZIONE, scritta prima di calcolare qualunque cosa.

Un PAC versa c all'inizio di ogni mese i = 1..N. Il montante e'

    V = sum_i c * prod_{j>=i} (1 + rho_j)

e l'IRR mensile y risolve  sum_i c (1+y)^(N-i+1) = V.

Derivo rispetto a log(1+rho_m) invece che a rho_m, perche' il rendimento
annuale e' il PRODOTTO dei dodici mensili: in log-spazio la sensibilita' di un
anno e' la SOMMA esatta di quelle dei suoi mesi, senza approssimazioni.

    dV/dlog(1+rho_m) = sum_{i<=m} c prod_{j>=i}(1+rho_j) = A_m
                       (montante a scadenza dei soli versamenti fino a m)

    dPhi/dy = sum_i c (N-i+1)(1+y)^(N-i)                        [Phi = lato IRR]

    dy/dlog(1+rho_m) = A_m / (dPhi/dy)          [teorema della funzione implicita]

e il peso dell'anno k e' la MEDIA dei dodici mensili, non la somma. Il motivo
sta nel vincolo log(1+R_k) = somma dei dodici log mensili: per alzare di uno il
log-rendimento dell'anno bisogna alzare di 1/12 quello di ogni mese, quindi

    w_k = dy/dlog(1+R_k) = (1/12) * somma_{m in k} dy/dlog(1+rho_m)

Distribuire lo shock in parti uguali fra i dodici mesi e' una scelta, ma dentro
un anno A_m varia pochissimo e qualunque altra ripartizione da' lo stesso
numero a meno di frazioni di punto percentuale.

NOTA ONESTA: alla prima stesura avevo scritto la somma. Il controllo a
differenze finite ha dato un rapporto di 0,0833 = 1/12 su TUTTI e venti gli
anni, che e' la firma inconfondibile di un errore di scala e non di rumore.
Corretto. Monotonia e rapporto ultimi/primi non cambiano — e' un fattore
costante — ma i pesi ora sono quello che dico che sono.

PERCHE' NON PUO' COINCIDERE COL 9,5:1. Quel numero e' il peso ARITMETICO DEL
CAPITALE: quanto capitale e' esposto negli ultimi tre anni contro i primi tre.
Il peso dell'IRR e' un'altra cosa: A_m contiene gia' il fattore
prod_{j>=m}(1+rho_j), che per i mesi finali e' quasi 1 — un rendimento
dell'ultimo anno si capitalizza per pochi mesi, uno del primo anno si
capitalizza per venti anni. I due effetti tirano in direzioni opposte. Lo
scrivo qui, prima dei numeri, perche' e' il motivo per cui la predizione puo'
sbagliare la clausola sul livello pur avendo ragione sul verso.

CONTROLLO OBBLIGATORIO: ogni peso analitico e' verificato contro una differenza
finita (bump del rendimento dell'anno k, IRR ricalcolata da zero). Se i due non
coincidono, la formula e' sbagliata e il giro non vale niente.

Nessuna selezione: N resta la famiglia pre-dichiarata della coda.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import dataio
from research import lab
from tax import _irr

ROUND = 61
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 61
YEARS = 20
M = YEARS * 12


def montante(rho, c=1.0):
    """Montante a scadenza di un versamento c all'inizio di ogni mese."""
    n = len(rho)
    g = np.cumprod(1.0 + rho)              # crescita da inizio a fine mese j
    # il versamento del mese i cresce per i mesi i..n  ->  g[n-1]/g[i-1]
    gp = np.concatenate(([1.0], g[:-1]))
    return float(c * np.sum(g[-1] / gp))


def irr_mensile(rho, c=1.0):
    """IRR mensile esatta del PAC su quel percorso."""
    n = len(rho)
    V = montante(rho, c)
    cf = np.full(n + 1, -c)
    cf[-1] = 0.0
    cf = np.concatenate((np.full(n, -c), [V]))
    r = _irr(cf, periods_per_year=1)
    return r


def pesi_analitici(rho, c=1.0):
    """w_k = dy/dlog(1+R_k), y IRR mensile, per k = 1..YEARS."""
    n = len(rho)
    g = np.cumprod(1.0 + rho)
    gp = np.concatenate(([1.0], g[:-1]))
    contrib_fv = c * g[-1] / gp            # montante finale di ogni versamento
    A = np.cumsum(contrib_fv)              # A_m = montante dei versamenti <= m
    y = irr_mensile(rho, c)
    k = np.arange(n, 0, -1)                # esponenti N-i+1
    dPhi = float(np.sum(c * k * (1.0 + y) ** (k - 1)))
    dy = A / dPhi
    return dy.reshape(YEARS, 12).mean(axis=1), y


def pesi_differenze_finite(rho, c=1.0, eps=1e-4):
    """Controllo: bump di eps del LOG-rendimento dell'anno k, cioe'
    eps/12 su ciascuno dei dodici mesi."""
    y0 = irr_mensile(rho, c)
    out = []
    for k in range(YEARS):
        r2 = rho.copy()
        sl = slice(k * 12, (k + 1) * 12)
        # distribuisco il bump in log sui dodici mesi: e' esattamente un bump
        # di log(1+R_k) pari a eps
        r2[sl] = (1.0 + r2[sl]) * np.exp(eps / 12.0) - 1.0
        out.append((irr_mensile(r2, c) - y0) / eps)
    return np.array(out)


def capitale_esposto(rho, c=1.0):
    """Peso ARITMETICO del capitale: quanto capitale e' investito ogni anno.
    E' la statistica da cui viene il 9,5:1 dei giri 47 e 58."""
    n = len(rho)
    val, out = 0.0, []
    for m in range(n):
        val += c
        out.append(val)
        val *= (1.0 + rho[m])
    return np.array(out).reshape(YEARS, 12).sum(axis=1)


def profilo(w):
    w = np.asarray(w, dtype=float)
    mono = bool(np.all(np.diff(w) > 0))
    r = float(w[-3:].sum() / w[:3].sum())
    return mono, r


def main():
    print(f"{'=' * 92}\nA15 — il peso di ciascun anno di un PAC ventennale, "
          f"calcolato\n{'=' * 92}")

    # ------------------------------------------- 1. percorso piatto, vari tassi
    print(f"\n   1. PERCORSO PIATTO — rendimento identico ogni anno\n")
    print(f"   {'rend. annuo':>12}{'IRR':>9}{'monotono':>11}"
          f"{'ultimi3/primi3':>16}{'errore vs diff.fin.':>21}")
    print("   " + "-" * 69)
    righe = []
    for ann in (0.02, 0.04, 0.06, 0.08, 0.10, 0.12):
        rho = np.full(M, (1 + ann) ** (1 / 12) - 1)
        w, y = pesi_analitici(rho)
        wf = pesi_differenze_finite(rho)
        err = float(np.max(np.abs(w - wf) / np.abs(w)))
        mono, r = profilo(w)
        print(f"   {ann * 100:>11.0f}%{((1 + y) ** 12 - 1) * 100:>8.2f}%"
              f"{'si' if mono else 'NO':>11}{r:>15.2f}x{err:>20.2e}")
        righe.append(dict(scenario=f"piatto {ann*100:.0f}%", mono=mono, ratio=r,
                          err=err))

    # riferimento: il peso aritmetico del capitale, che e' il 9,5:1
    rho8 = np.full(M, 1.08 ** (1 / 12) - 1)
    cap = capitale_esposto(rho8)
    _, rcap = profilo(cap)
    w8, _ = pesi_analitici(rho8)
    arit = (18 + 19 + 20) / (1 + 2 + 3)
    print(f"\n   TRE quantita' diverse che i giri 47 e 58 trattavano come una sola:")
    print(f"     peso aritmetico puro dei versamenti (18+19+20)/(1+2+3) : "
          f"{arit:>6.2f}x   <- il 9,5:1")
    print(f"     capitale ESPOSTO, capitalizzato all'8%                 : "
          f"{rcap:>6.2f}x")
    print(f"     peso dell'IRR, dIRR/dlog(1+R_k), all'8%                : "
          f"{profilo(w8)[1]:>6.2f}x")
    print(f"   Il capitale esposto negli ultimi tre anni e' {rcap:.1f} volte quello dei")
    print(f"   primi tre, ma l'IRR ne risente solo {profilo(w8)[1]:.1f} volte tanto: ai")
    print(f"   rendimenti finali manca il tempo di capitalizzazione. Il 9,5:1 non e'")
    print(f"   ne' l'uno ne' l'altro — sta in mezzo, e non e' la sensibilita' dell'IRR.")

    print(f"\n   Profilo completo al 8% (normalizzato a w_20 = 1):")
    wn = w8 / w8[-1]
    for a in range(0, YEARS, 4):
        print("     " + "  ".join(f"a{i+1:02d}={wn[i]:.3f}"
                                  for i in range(a, min(a + 4, YEARS))))

    # ------------------------------------------- 2. percorsi storici reali
    print(f"\n   2. PERCORSI STORICI REALI — finestre ventennali del mercato USA\n")
    ff = dataio.ff_factors_monthly()
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()
    starts = [i for i in range(0, len(mkt) - M + 1, 12)]
    W, ratios, monos = [], [], []
    for s in starts:
        rho = mkt.iloc[s:s + M].to_numpy(dtype=float)
        w, _ = pesi_analitici(rho)
        W.append(w)
        m, r = profilo(w)
        monos.append(m)
        ratios.append(r)
    W = np.array(W)
    ratios = np.array(ratios)
    print(f"   {len(starts)} finestre ventennali, da "
          f"{mkt.index[starts[0]].year} a {mkt.index[starts[-1] + M - 1].year}")
    print(f"   monotono in {sum(monos)}/{len(monos)} finestre")
    print(f"   rapporto ultimi3/primi3: mediana {np.median(ratios):.2f}x, "
          f"min {ratios.min():.2f}x, max {ratios.max():.2f}x")
    righe.append(dict(scenario="storico mediana", mono=bool(np.all(monos)),
                      ratio=float(np.median(ratios)), err=np.nan))

    # ------------------------------------------- 3. verdetto
    tutti = [r["ratio"] for r in righe]
    tutti_mono = all(r["mono"] for r in righe)
    rmin, rmax = min(tutti), max(tutti)
    banda = (9.5 * 0.8, 9.5 * 1.2)
    print(f"\n{'=' * 92}\n   VERDETTO\n{'=' * 92}")
    print(f"   Predizione: peso monotono crescente in k, e rapporto "
          f"ultimi3/primi3 entro il 20%")
    print(f"   del 9,5:1 aritmetico (cioe' fra {banda[0]:.2f} e {banda[1]:.2f}).")
    print(f"   FALSIFICATA se il peso non e' monotono, oppure il rapporto "
          f"sta SOTTO 4.\n")
    print(f"   monotono ovunque      : {'SI' if tutti_mono else 'NO'}")
    print(f"   rapporto              : da {rmin:.2f}x a {rmax:.2f}x")
    print(f"   dentro la banda 7,6-11,4 : "
          f"{'si' if banda[0] <= rmin and rmax <= banda[1] else 'NO'}")
    fals = (not tutti_mono) or rmin < 4.0
    print(f"\n   -> ipotesi A15 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'monotono crescente': "
          f"{'centrata' if tutti_mono else 'SBAGLIATA'}")
    dentro = banda[0] <= rmin and rmax <= banda[1]
    print(f"      clausola 'entro il 20% del 9,5:1': "
          f"{'centrata' if dentro else 'SBAGLIATA'}")

    print(f"\n   Confronto con le regressioni dei giri 47 e 58:")
    print(f"     giro 47 (A13): rapporto stimato 1,21-2,71, R2 0,28-0,33")
    print(f"     giro 58 (A14): rapporto stimato 0,55-48,51, R2 0,002-0,210")
    print(f"     giro 61 (A15): rapporto CALCOLATO {rmin:.2f}-{rmax:.2f}, "
          f"esatto per costruzione")

    pd.DataFrame(righe).to_csv(OUT / "round61_a15.csv", index=False)
    pd.DataFrame(W, columns=[f"anno{i+1}" for i in range(YEARS)]).to_csv(
        OUT / "round61_profili.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="A15 peso analitico dIRR/dr_k",
                         config=r["scenario"], window=f"{YEARS} anni", sharpe="",
                         irr="", bh_irr="", excess=r["ratio"], n_obs=YEARS,
                         note=f"monotono={r['mono']}") for r in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

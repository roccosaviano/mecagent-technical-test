"""Giro 79 — O1: deflatare sul MARGINE invece che sullo Sharpe.

VOCE DELLA CODA, verbatim (committata al giro 78):

O1 — Il difetto di G2: deflatare sul margine, non sullo Sharpe
  Messo a verbale al giro 77 PRIMA di conoscere l'esito dell'holdout, e diventato
  al giro 78 la spiegazione di come un candidato con DSR 0,9907 possa perdere
  -0,95 fuori campione. La var_sr del Deflated Sharpe e' stimata sulla dispersione
  degli SHARPE della famiglia, che nel giro 77 era minuscola (SR0 0,0608), mentre
  la selezione era avvenuta sui MARGINI DI IRR NETTA, che nella stessa famiglia
  variavano di 4,27 punti.
  Da costruire: la versione MARGINE della statistica di Bailey-Lopez de Prado —
  soglia di massimo atteso su N estrazioni costruita sulla varianza dei margini di
  IRR netta invece che degli Sharpe — e applicarla ai dodici candidati del giro 72
  piu' le venti celle del giro 77.
  PREDIZIONE: il cancello sul margine AVREBBE RESPINTO il 12-3 top-5 mensile,
  perche' il massimo atteso di 20 estrazioni con dispersione 4,27 punti sta SOPRA
  +1,18. E respinge anche TUTTI gli altri candidati mai registrati, quindi non e'
  un cancello costruito su misura per il caso che ha fallito. Il rapporto fra la
  soglia sul margine e quella sullo Sharpe e' SUPERIORE A 3.
  FALSIFICATA SE: il cancello sul margine avrebbe LASCIATO PASSARE il candidato —
  nel qual caso il fallimento dell'holdout non e' spiegato dalla selezione e va
  cercato altrove — OPPURE se respinge cosi' tanto da respingere anche
  l'equal-weight contro il cap-weight, cioe' se non discrimina piu' niente.

=================== TRE LETTURE DICHIARATE PRIMA DI ESEGUIRE ===================

1. LA STATISTICA. Bailey-Lopez de Prado danno il massimo atteso di N estrazioni
   indipendenti da una normale:
       E[max] = mu + sigma * [ (1-g) * Phi^-1(1 - 1/N) + g * Phi^-1(1 - 1/(N e)) ]
   con g = costante di Eulero-Mascheroni. Sotto ipotesi nulla "nessuna strategia
   batte il benchmark" il margine atteso e' mu = 0, e sigma e' la deviazione
   standard dei margini DENTRO LA FAMIGLIA da cui e' stato preso il massimo.
   Riporto anche la variante centrata sulla media della famiglia, che e' l'altra
   lettura difendibile, perche' se il verdetto dipendesse da quale delle due si
   sceglie andrebbe detto.

2. IL RAPPORTO FRA LE DUE SOGLIE. La clausola "il rapporto fra la soglia sul
   margine e quella sullo Sharpe e' superiore a 3" e' ambigua: le due soglie sono
   in unita' diverse (punti di IRR contro Sharpe per periodo) e non si dividono.
   La leggo cosi', ed e' l'unica lettura senza unita' che conosco:
       rapporto = (soglia_margine / margine_osservato) / (SR0 / SR_osservato)
   cioe' quanto piu' esigente e' il cancello sul margine, misurato in frazione
   della statistica che deve superare. Dichiaro la lettura invece di sceglierla
   dopo aver visto quale numero mi conviene.

3. IL CONTROLLO. La clausola di falsificazione chiede che il cancello non
   respinga l'equal-weight contro il cap-weight. Applico il cancello CON LA N
   DELLA SELEZIONE CHE E' DAVVERO AVVENUTA: per l'equal-weight contro il
   cap-weight N = 1, perche' e' un confronto singolo pre-specificato e non il
   massimo di una griglia. Penalizzare una selezione che non c'e' stata non e'
   severita', e' un errore. Riporto comunque anche la versione sotto stress
   (stessa N e stessa sigma della famiglia del momentum), che e' la lettura piu'
   dura, cosi' chi non e' d'accordo con me ha il numero.

NOTA SU SIGMA E SUL CALENDARIO. I margini della famiglia sono tutti calcolati
contro lo stesso benchmark, quindi cambiare il calendario del benchmark li trasla
tutti della stessa costante e NON cambia sigma. Uso il solo calendario mediano del
giro 77 (ottobre) invece di rifare dodici simulazioni: la soglia non ne dipende.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import dataio
from research import lab, bench as B
from research.round76 import simula, pesi_top

ROUND = 79
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
MESE_BENCH = 10                      # il calendario mediano del giro 77
SKIP_FAM = (1, 2, 3, 4, 6)
TAGLIE_FAM = (3, 5, 10, 25)
K_CAND, TOP_CAND = 3, 5
MARG_CAND = 1.18                     # G1 del giro 77, mediana sui 12 calendari
EULERO = 0.5772156649015329

# numeri gia' registrati, non rimisurati qui
SR_CAND = 0.1755                     # Sharpe per periodo, giro 77
SR0_G2 = 0.0608                      # soglia di G2 sulla famiglia, giro 77
DSR_G2 = 0.9907
EW_VS_CAPW = 1.50                    # giro 60, premio di equal-weighting


def soglia_max(n, sigma, mu=0.0):
    """Massimo atteso di n estrazioni normali (Bailey & Lopez de Prado)."""
    if n < 2 or sigma <= 0:
        return mu
    a = st.norm.ppf(1.0 - 1.0 / n)
    b = st.norm.ppf(1.0 - 1.0 / (n * np.e))
    return mu + sigma * ((1.0 - EULERO) * a + EULERO * b)


def main():
    print(f"{'=' * 104}\nO1 — il cancello sul MARGINE contro il cancello sullo "
          f"SHARPE\n{'=' * 104}")

    # ------------------------------------------- famiglia A: i 12 del giro 72
    reg = pd.read_csv(lab.REGISTRY)
    g72 = reg[reg["round"] == 72].copy()
    marg_a = pd.to_numeric(g72["irr"], errors="coerce").to_numpy(dtype=float)
    nomi_a = g72["config"].tolist()

    # ------------------------------------------- famiglia B: le 20 del giro 77
    ind_g = dataio.ff_ind49_daily().dropna(axis=1, how="all").dropna()
    ind_g = ind_g[ind_g.index.year <= FINE]
    ind_m = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind_m = ind_m[ind_m.index.year <= FINE]
    ind_m.index = pd.DatetimeIndex(ind_m.index).to_period("M").to_timestamp("M")
    ind_m = ind_m[ind_g.columns]
    rf = dataio.ff_factors_monthly()["RF"]
    rf.index = pd.DatetimeIndex(rf.index).to_period("M").to_timestamp("M")

    def irr(net, turn):
        i = net.dropna().index
        return B.eval_stream("x", net.reindex(i), rf.reindex(i).fillna(0.0),
                             turn.reindex(i))

    W = pd.DataFrame(0.0, index=ind_m.index, columns=ind_m.columns)
    W.loc[W.index.month == MESE_BENCH] = 1.0 / ind_m.shape[1]
    bench = irr(*simula(ind_g, W, 0))
    mom = {k: (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(k)
           for k in SKIP_FAM}

    marg_b, nomi_b = [], []
    print(f"\n   famiglia del giro 77 (benchmark equal-weight annuale, "
          f"calendario mediano)")
    print(f"   {'margine per skip':<20}" + "".join(f"{'k=' + str(k):>9}"
                                                   for k in SKIP_FAM))
    for top in TAGLIE_FAM:
        riga = []
        for k in SKIP_FAM:
            r = irr(*simula(ind_g, pesi_top(mom[k], top), 0))
            riga.append(r["irr_ref"] - bench["irr_ref"])
            marg_b.append(riga[-1])
            nomi_b.append(f"12-{k} top-{top}")
        print(f"   {'top-' + str(top):<20}" + "".join(f"{v:>+9.2f}" for v in riga))
    marg_b = np.array(marg_b)

    # ---------------------------------------------------------- le due soglie
    print(f"\n{'=' * 104}\n   LE SOGLIE\n{'=' * 104}")
    print(f"   {'famiglia':<26}{'N':>4}{'media':>9}{'sigma':>9}"
          f"{'ampiezza':>10}{'soglia H0':>11}{'soglia su media':>17}")
    print("   " + "-" * 90)
    righe = []
    for nome, m in (("A — 12 candidati (giro 72)", marg_a),
                    ("B — 20 celle (giro 77)", marg_b)):
        n = len(m)
        sd = float(np.std(m, ddof=1))
        s0 = soglia_max(n, sd, 0.0)
        sm = soglia_max(n, sd, float(np.mean(m)))
        righe.append((nome, n, float(np.mean(m)), sd, s0, sm))
        print(f"   {nome:<26}{n:>4}{np.mean(m):>+9.2f}{sd:>9.2f}"
              f"{m.max() - m.min():>10.2f}{s0:>+11.2f}{sm:>+17.2f}")

    sd_b = righe[1][3]
    soglia_b = righe[1][4]
    soglia_b_media = righe[1][5]
    sd_a, soglia_a = righe[0][3], righe[0][4]

    # ---------------------------------------- il candidato contro i due cancelli
    print(f"\n{'=' * 104}\n   IL CANDIDATO CHE HA FALLITO L'HOLDOUT\n{'=' * 104}")
    print(f"   momentum 12-{K_CAND} top-{TOP_CAND} mensile   "
          f"margine in campione **+{MARG_CAND:.2f}**   "
          f"esito sull'holdout **−0,95**\n")
    print(f"   {'cancello':<34}{'osservato':>11}{'soglia':>10}"
          f"{'soglia/oss.':>13}{'esito':>10}")
    print("   " + "-" * 80)
    r_sharpe = SR0_G2 / SR_CAND
    r_marg = soglia_b / MARG_CAND
    print(f"   {'G2 come scritto (Sharpe)':<34}{SR_CAND:>11.4f}{SR0_G2:>10.4f}"
          f"{r_sharpe:>13.2f}{'PASSA':>10}")
    print(f"   {'G2 sul margine, H0 = 0':<34}{MARG_CAND:>+11.2f}"
          f"{soglia_b:>+10.2f}{r_marg:>13.2f}"
          f"{('PASSA' if MARG_CAND > soglia_b else 'RESPINTO'):>10}")
    print(f"   {'G2 sul margine, centrata su media':<34}{MARG_CAND:>+11.2f}"
          f"{soglia_b_media:>+10.2f}{soglia_b_media / MARG_CAND:>13.2f}"
          f"{('PASSA' if MARG_CAND > soglia_b_media else 'RESPINTO'):>10}")
    rapporto = r_marg / r_sharpe
    print(f"\n   rapporto fra le due esigenze (lettura dichiarata): "
          f"**{rapporto:.2f}×**   (previsto sopra 3)")

    # --------------------------------- il cancello applicato a tutti i candidati
    print(f"\n{'=' * 104}\n   IL CANCELLO APPLICATO A TUTTI, non solo a chi ha "
          f"fallito\n{'=' * 104}")
    passa_a = [(n, v) for n, v in zip(nomi_a, marg_a) if v > soglia_a]
    passa_b = [(n, v) for n, v in zip(nomi_b, marg_b) if v > soglia_b]
    print(f"   famiglia A (giro 72, N=12, soglia {soglia_a:+.2f}): "
          f"**{len(passa_a)}/12 passano**"
          f"   — il migliore e' {nomi_a[int(np.argmax(marg_a))]} "
          f"a {marg_a.max():+.2f}")
    print(f"   famiglia B (giro 77, N=20, soglia {soglia_b:+.2f}): "
          f"**{len(passa_b)}/20 passano**"
          f"   — il migliore e' {nomi_b[int(np.argmax(marg_b))]} "
          f"a {marg_b.max():+.2f}")
    for n, v in passa_a + passa_b:
        print(f"      passa: {n} a {v:+.2f}")

    # ------------------------------------------------------------- il controllo
    print(f"\n{'=' * 104}\n   IL CONTROLLO: il cancello discrimina ancora?"
          f"\n{'=' * 104}")
    print(f"   Oggetto: **equal-weight annuale contro cap-weight**, "
          f"+{EW_VS_CAPW:.2f} punti (giro 60).")
    print(f"   E' l'effetto strutturale piu' pulito del progetto e "
          f"**non e' stato selezionato**: un confronto singolo.\n")
    s_n1 = soglia_max(1, sd_b, 0.0)
    print(f"   {'lettura':<44}{'N':>4}{'soglia':>10}{'esito':>12}")
    print("   " + "-" * 72)
    print(f"   {'N della selezione avvenuta (dichiarata prima)':<44}{1:>4}"
          f"{s_n1:>+10.2f}"
          f"{('PASSA' if EW_VS_CAPW > s_n1 else 'RESPINTO'):>12}")
    print(f"   {'sotto stress: stessa N e sigma del momentum':<44}{20:>4}"
          f"{soglia_b:>+10.2f}"
          f"{('PASSA' if EW_VS_CAPW > soglia_b else 'RESPINTO'):>12}")

    # ------------------------------------------------------------- verdetto
    resp_cand = MARG_CAND <= soglia_b
    resp_tutti = (len(passa_a) == 0) and (len(passa_b) == 0)
    ctrl_ok = EW_VS_CAPW > s_n1
    rapp_ok = rapporto > 3.0
    print(f"\n{'=' * 104}\n   VERDETTO\n{'=' * 104}")
    print(f"   Predizione: il cancello sul margine RESPINGE il 12-3 top-5, "
          f"respinge anche tutti gli altri,")
    print(f"   e il rapporto fra le due soglie e' sopra 3.")
    print(f"   FALSIFICATA se il cancello LASCIA PASSARE il candidato, OPPURE se "
          f"respinge anche l'equal-weight")
    print(f"   contro il cap-weight.\n")
    print(f"   respinge il candidato          : "
          f"{'SI' if resp_cand else 'NO'}   ({MARG_CAND:+.2f} contro "
          f"{soglia_b:+.2f})")
    print(f"   respinge tutti gli altri       : "
          f"{'SI' if resp_tutti else 'NO'}   "
          f"({len(passa_a) + len(passa_b)} passanti su 32)")
    print(f"   rapporto sopra 3               : "
          f"{'SI' if rapp_ok else 'NO'}   ({rapporto:.2f}×)")
    print(f"   discrimina ancora (controllo)  : "
          f"{'SI' if ctrl_ok else 'NO'}")
    fals = (not resp_cand) or (not ctrl_ok)
    print(f"\n   -> ipotesi O1 {'FALSIFICATA' if fals else 'CONFERMATA'}")

    lab.log_trials([dict(round=ROUND, hypothesis="O1 cancello sul margine",
                         config=n, window=f"1969-{FINE}", sharpe="",
                         irr=v, bh_irr=soglia_b, excess=v - soglia_b,
                         n_obs=len(ind_g),
                         note=f"soglia N=20 sigma={sd_b:.3f}")
                    for n, v in zip(nomi_b, marg_b)])
    pd.DataFrame(dict(nome=nomi_b, margine=marg_b)).to_csv(
        OUT / "round79_o1.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

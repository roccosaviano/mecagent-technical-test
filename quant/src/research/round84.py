"""Giro 84 — O6: esiste una statistica in campione che avrebbe segnalato il candidato?

VOCE DELLA CODA, verbatim (committata al giro 81):

O6 — Esiste una statistica in campione che avrebbe segnalato il candidato?
  Il quadro dopo tre giri di autopsia: G1 e G2 lo avrebbero fermato con la soglia
  giusta (giro 79), G3 no in nessuna versione (giro 81), e il crollo del lordo da
  +6,50 a +0,31 (giro 80) non era visibile in campione per definizione. Resta una
  domanda sola: fra le statistiche calcolabili SUL SOLO TRAIN, ce n'e' una che
  avrebbe alzato la mano — al di la' del cancello sulla selezione, che non guarda
  il candidato ma la griglia?
  Il sospetto e' il PROFILO TEMPORALE: al giro 77 avevo messo a verbale che le
  uniche due finestre decennali negative erano LE ULTIME DUE (1999-2008 a -1,23,
  2000-2009 a -3,39), dopo cinque consecutive sopra +3. Quello e' un TREND, e
  nessun cancello lo guardava.
  Da misurare, sul solo 1969-2009, applicando a TUTTI E TREDICI i candidati (i
  dodici del giro 72 piu' il 12-3 top-5) una batteria di cinque statistiche
  pre-dichiarate: (1) pendenza OLS dell'extra decennale in funzione dell'anno di
  inizio; (2) extra dell'ultimo terzo del campione meno quello del primo terzo;
  (3) quota di finestre positive calcolata SOLO sull'ultimo decennio di finestre;
  (4) t-stat dell'extra mensile sull'ultimo terzo; (5) rapporto fra il numero di
  mesi positivi negli ultimi cinque anni e nei primi cinque.
  PREDIZIONE: LA PENDENZA (1) SEGNALA IL CANDIDATO, ed e' L'UNICA delle cinque a
  farlo con specificita' — cioe' segnala il 12-3 top-5 e NON PIU' DI TRE degli
  altri dodici. Le statistiche (3) e (5) sono troppo rumorose per discriminare
  (segnaleranno piu' di meta' dei candidati o nessuno), e la (4) non segnala
  perche' il t-stat mensile e' dominato dalla volatilita' e non dal trend.
  FALSIFICATA SE: NESSUNA delle cinque segnala il candidato — nel qual caso il
  fallimento dell'holdout non era visibile in campione con nessuno strumento e la
  selezione (giro 79) resta l'unica difesa possibile — OPPURE se PIU' DI TRE delle
  cinque lo segnalano, cioe' segnalare era facile e il progetto ha semplicemente
  guardato dalla parte sbagliata per settantasette giri.

============ COSA VUOL DIRE "SEGNALA", DICHIARATO PRIMA DI ESEGUIRE ============

La voce non definisce la soglia d'allarme, e senza una definizione scritta prima
il risultato lo scelgo io dopo. Le fisso qui, su basi interpretabili e non sui
dati:

  (1) PENDENZA      allarme se il calo implicito sull'arco degli anni di inizio
                    supera UN PUNTO: pendenza x (anno_max - anno_min) < -1,00.
  (2) TERZI         allarme se (extra ultimo terzo - extra primo terzo) < -1,00.
  (3) QUOTA RECENTE allarme se la quota di finestre positive sulle ULTIME DIECI
                    finestre e' sotto 2/3, cioe' la soglia di G3 applicata al solo
                    tratto recente.
  (4) T-STAT        allarme se il t-stat dell'extra mensile sull'ultimo terzo e'
                    <= 0, cioe' nell'ultimo terzo non c'e' vantaggio.
  (5) MESI POSITIVI allarme se il rapporto fra mesi positivi negli ultimi cinque
                    anni e nei primi cinque e' sotto 0,90.

E poiche' ogni soglia assoluta e' contestabile, riporto ANCHE una misura SENZA
SOGLIA: il RANGO del candidato fra i tredici su ciascuna statistica, dal peggiore
al migliore. Se il candidato e' primo su una statistica, quella statistica lo
distingue davvero; se e' settimo, nessuna scelta di soglia la salva.

MOTORI: ogni candidato nel motore in cui era stato misurato — i dodici del giro 72
nel mensile, il 12-3 top-5 nel giornaliero (giro 77). Stessa scelta del giro 81 e
per la stessa ragione: cambiare motore introduce 1,43 punti che non c'entrano.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import dataio
from research import lab, bench as B
from research.round72 import valuta, pesi_annuali, pesi_mensili, rot_vera
from research.round76 import simula, pesi_top

ROUND = 84
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
LUNG = 10
MESE_BENCH_D = 10
CAND = "12-3 top-5 mensile (il candidato)"

A_PENDENZA = -1.00
A_TERZI = -1.00
A_QUOTA = 2.0 / 3.0
A_TSTAT = 0.0
A_MESI = 0.90
N_RECENTI = 10


def main():
    ind_g = dataio.ff_ind49_daily().dropna(axis=1, how="all").dropna()
    ind_g = ind_g[ind_g.index.year <= FINE]
    ind_m = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind_m = ind_m[ind_m.index.year <= FINE]
    ind_m.index = pd.DatetimeIndex(ind_m.index).to_period("M").to_timestamp("M")
    ind_m = ind_m[ind_g.columns]
    rf = dataio.ff_factors_monthly()["RF"]
    rf.index = pd.DatetimeIndex(rf.index).to_period("M").to_timestamp("M")
    rf_m = rf.reindex(ind_m.index).fillna(0.0)
    y0, y1 = int(ind_m.index[0].year), FINE

    print(f"{'=' * 112}\nO6 — esiste una statistica in campione che avrebbe "
          f"segnalato il candidato?\n{'=' * 112}")
    print(f"   Train {y0}-{y1}, tredici candidati, cinque statistiche, soglie "
          f"d'allarme dichiarate nel codice.\n")

    def irr_fin(net, turn, a, b):
        i = net.index[(net.index.year >= a) & (net.index.year <= b)]
        s = net.reindex(i).dropna()
        if len(s) < 24:
            return None
        return B.eval_stream("x", s, rf.reindex(s.index).fillna(0.0),
                             turn.reindex(s.index))["irr_ref"]

    def statistiche(net_c, turn_c, net_b, turn_b):
        anni, ex = [], []
        for y in range(y0 + 3, y1 - LUNG + 2):
            x = irr_fin(net_c, turn_c, y, y + LUNG - 1)
            q = irr_fin(net_b, turn_b, y, y + LUNG - 1)
            if x is not None and q is not None:
                anni.append(y)
                ex.append(x - q)
        anni, ex = np.array(anni, dtype=float), np.array(ex)
        pend = np.polyfit(anni, ex, 1)[0]
        s1 = pend * (anni.max() - anni.min())

        idx = net_c.dropna().index.intersection(net_b.dropna().index)
        n3 = len(idx) // 3
        pr, ul = idx[:n3], idx[-n3:]
        e_pr = (irr_fin(net_c, turn_c, pr[0].year, pr[-1].year) -
                irr_fin(net_b, turn_b, pr[0].year, pr[-1].year))
        e_ul = (irr_fin(net_c, turn_c, ul[0].year, ul[-1].year) -
                irr_fin(net_b, turn_b, ul[0].year, ul[-1].year))
        s2 = e_ul - e_pr

        s3 = float(np.mean(ex[-N_RECENTI:] > 0))

        d = (net_c.reindex(idx) - net_b.reindex(idx)).dropna()
        du = d.reindex(ul).dropna()
        s4 = float(du.mean() / du.std(ddof=1) * np.sqrt(len(du)))

        p_ul = float((d.iloc[-60:] > 0).sum())
        p_pr = float((d.iloc[:60] > 0).sum())
        s5 = p_ul / p_pr if p_pr > 0 else np.nan
        return dict(pendenza=s1, terzi=s2, quota=s3, tstat=s4, mesi=s5)

    righe = {}

    # ------------------------------------------- il candidato, motore giornaliero
    score = (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(3)
    nc, tc = simula(ind_g, pesi_top(score, 5), 0)
    Wd = pd.DataFrame(0.0, index=ind_m.index, columns=ind_m.columns)
    Wd.loc[Wd.index.month == MESE_BENCH_D] = 1.0 / ind_m.shape[1]
    nb, tb = simula(ind_g, Wd, 0)
    righe[CAND] = statistiche(nc, tc, nb, tb)

    # ------------------------------------------- i dodici, motore mensile
    mom12 = (1 + ind_m).rolling(11).apply(np.prod, raw=True).shift(2)
    mom6 = (1 + ind_m).rolling(5).apply(np.prod, raw=True).shift(2)
    vol36 = ind_m.rolling(36).std().shift(1)
    mix = mom12.rank(axis=1, pct=True) + (-vol36).rank(axis=1, pct=True)
    cands = [("momentum 12-2 top-5 annuale", True, mom12, 5),
             ("momentum 12-2 top-10 annuale", True, mom12, 10),
             ("momentum 12-2 top-25 annuale", True, mom12, 25),
             ("momentum 6-2 top-10 annuale", True, mom6, 10),
             ("low-vol 36m top-10 annuale", True, -vol36, 10),
             ("low-vol 36m top-25 annuale", True, -vol36, 25),
             ("punteggio misto top-10 annuale", True, mix, 10),
             ("momentum 12-2 top-5 mensile", False, mom12, 5),
             ("H5 momentum top-10 mensile", False, mom12, 10),
             ("momentum 12-2 top-25 mensile", False, mom12, 25),
             ("H4 low-vol 36m top-10 mensile", False, -vol36, 10),
             ("C1 punteggio misto top-10 mensile", False, mix, 10)]
    bench_m = {m: valuta(ind_m, pesi_annuali(ind_m, m), rf_m) for m in range(1, 13)}
    turn_bm = {m: rot_vera(ind_m, pesi_annuali(ind_m, m)) for m in range(1, 13)}
    for nome, ann, sc, top in cands:
        if ann:
            mesi = {m: valuta(ind_m, pesi_annuali(ind_m, m, sc, top), rf_m)
                    for m in range(1, 13)}
            marg = {m: mesi[m]["irr_ref"] - bench_m[m]["irr_ref"] for m in mesi}
            med = float(np.median(list(marg.values())))
            mm = min(marg, key=lambda m: abs(marg[m] - med))
            W = pesi_annuali(ind_m, mm, sc, top)
        else:
            mm = 1
            W = pesi_mensili(sc, top)
        tu = rot_vera(ind_m, W)
        ne = ((W * ind_m).sum(axis=1) - tu * 0.0015).dropna()
        righe[nome] = statistiche(ne, tu, bench_m[mm]["net"], turn_bm[mm])

    df = pd.DataFrame(righe).T
    allarme = pd.DataFrame({
        "pendenza": df["pendenza"] < A_PENDENZA,
        "terzi": df["terzi"] < A_TERZI,
        "quota": df["quota"] < A_QUOTA,
        "tstat": df["tstat"] <= A_TSTAT,
        "mesi": df["mesi"] < A_MESI})

    print(f"   {'candidato':<36}{'(1) pend':>10}{'(2) terzi':>11}"
          f"{'(3) quota':>11}{'(4) t-stat':>12}{'(5) mesi':>10}{'allarmi':>9}")
    print("   " + "-" * 99)
    for nome in df.index:
        r, a = df.loc[nome], allarme.loc[nome]
        mk = lambda v, on: ("*" if on else " ")
        print(f"   {nome[:35]:<36}"
              f"{r['pendenza']:>9.2f}{mk(0, a['pendenza'])}"
              f"{r['terzi']:>10.2f}{mk(0, a['terzi'])}"
              f"{r['quota']:>10.0%}{mk(0, a['quota'])}"
              f"{r['tstat']:>11.2f}{mk(0, a['tstat'])}"
              f"{r['mesi']:>9.2f}{mk(0, a['mesi'])}"
              f"{int(a.sum()):>9}")
    print(f"   (* = allarme.  soglie: pend < {A_PENDENZA}, terzi < {A_TERZI}, "
          f"quota < {A_QUOTA:.0%}, t-stat <= {A_TSTAT}, mesi < {A_MESI})")

    # ------------------------------------------------------- specificita' e rango
    print(f"\n{'=' * 112}\n   QUANTE VOLTE OGNI STATISTICA ALZA LA MANO"
          f"\n{'=' * 112}")
    print(f"   {'statistica':<16}{'segnala il candidato':>24}"
          f"{'segnala altri':>16}{'totale su 13':>15}{'rango del cand.':>18}")
    print("   " + "-" * 91)
    ranghi = {}
    for st in ("pendenza", "terzi", "quota", "tstat", "mesi"):
        cand_on = bool(allarme.loc[CAND, st])
        altri = int(allarme[st].sum()) - int(cand_on)
        # rango: 1 = il peggiore (valore piu' basso = piu' allarmante)
        ordine = df[st].rank(method="min", ascending=True)
        ranghi[st] = int(ordine.loc[CAND])
        print(f"   {st:<16}{('SI' if cand_on else 'no'):>24}{altri:>16}"
              f"{int(allarme[st].sum()):>15}{ranghi[st]:>13} su 13")

    n_seg = int(allarme.loc[CAND].sum())
    spec_pend = int(allarme['pendenza'].sum()) - int(allarme.loc[CAND, 'pendenza'])

    # ------------------------------------------------------------- verdetto
    print(f"\n{'=' * 112}\n   VERDETTO\n{'=' * 112}")
    print(f"   Predizione: la PENDENZA segnala il candidato ed e' L'UNICA a farlo "
          f"con specificita' (non piu' di")
    print(f"   tre degli altri dodici). Le (3) e (5) sono troppo rumorose, la (4) "
          f"non segnala.")
    print(f"   FALSIFICATA se NESSUNA delle cinque segnala il candidato, OPPURE "
          f"se PIU' DI TRE lo segnalano.\n")
    p1 = bool(allarme.loc[CAND, "pendenza"])
    p2 = spec_pend <= 3
    p4 = not bool(allarme.loc[CAND, "tstat"])
    print(f"   la pendenza segnala il candidato     : {'SI' if p1 else 'NO'}"
          f"   (calo implicito {df.loc[CAND, 'pendenza']:+.2f} punti, "
          f"rango {ranghi['pendenza']}/13)")
    print(f"   e' specifica (<= 3 altri)            : {'SI' if p2 else 'NO'}"
          f"   ({spec_pend} altri)")
    print(f"   la (4) non segnala                   : {'SI' if p4 else 'NO'}"
          f"   (t-stat {df.loc[CAND, 'tstat']:+.2f})")
    print(f"   statistiche che segnalano il candidato: **{n_seg} su 5**")
    fals = (n_seg == 0) or (n_seg > 3)
    print(f"\n   -> ipotesi O6 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    if fals and n_seg == 0:
        print(f"      ramo 1: nessuno strumento in campione lo vedeva. La "
              f"selezione resta l'unica difesa.")
    elif fals:
        print(f"      ramo 2: segnalare era facile — {n_seg} statistiche su 5 "
              f"alzano la mano.")

    df.assign(**{f"allarme_{c}": allarme[c] for c in allarme}).to_csv(
        OUT / "round84_o6.csv")
    lab.log_trials([dict(round=ROUND, hypothesis="O6 statistiche di allarme",
                         config=n, window=f"{y0}-{FINE}", sharpe=df.loc[n, "tstat"],
                         irr=df.loc[n, "pendenza"], bh_irr=df.loc[n, "terzi"],
                         excess=df.loc[n, "quota"], n_obs=len(ind_m),
                         note=f"allarmi={int(allarme.loc[n].sum())}")
                    for n in df.index])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

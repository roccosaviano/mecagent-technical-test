"""Giro 68 — D10: il calendario del ribilanciamento come parametro libero.

VOCE DELLA CODA, predizione verbatim:

D10 — Il calendario del ribilanciamento e' un parametro libero mai contato
  Nata al giro 65. La stessa strategia — momentum 12-2, top-5, ribilanciamento
  annuale, 49 settori, 1969-2026 — vale +1,51 o -1,92 contro lo stesso benchmark
  a seconda che ribilanci a GENNAIO CIVILE o OGNI 12 MESI a partire dall'inizio
  del campione. Sono 3,43 punti da una scelta che nessuno dei sessantacinque giri
  ha mai dichiarato ne' contato nel registro dei tentativi. Un backtest con
  ribilanciamento annuale ha DODICI implementazioni, e finora ne e' stata usata
  una alla volta senza dirlo.
  Da misurare: per momentum top-5, top-10, top-25 annuale e per l'equal-weight
  annuale, tutte e DODICI le date di ribilanciamento (gennaio…dicembre), contro
  l'equal-weight annuale ribilanciato nello stesso mese. Riportare ampiezza,
  mediana e quante configurazioni battono il benchmark.
  PREDIZIONE: l'ampiezza fra il mese migliore e il peggiore supera 2 PUNTI di IRR
  per ogni strategia, la MEDIANA DEI DODICI E' NEGATIVA contro il benchmark per
  tutte, e MENO DI UN TERZO delle 48 configurazioni batte il proprio benchmark.
  Cioe': il +1,51 di gennaio e' il massimo di dodici estrazioni, non un risultato
  — e il registro va aumentato di 48 tentativi, non di 4.
  FALSIFICATA SE: l'ampiezza resta SOTTO 1 PUNTO per la maggioranza delle
  strategie — nel qual caso il calendario non e' un parametro libero e il
  conflitto fra i giri 64 e 65 ha un'altra causa da cercare — OPPURE la mediana
  dei dodici mesi e' POSITIVA per almeno una strategia, nel qual caso il
  vantaggio non dipende dalla scelta del mese e va portato al DSR.

TRE LETTURE FISSATE PRIMA DI CALCOLARE.

1. "AMPIEZZA" = massimo meno minimo dell'IRR sui dodici mesi, in LIVELLO. Va
   definita sul livello e non sull'extra-rendimento perche' per l'equal-weight
   annuale — che e' anche il benchmark — l'extra e' zero per costruzione, e una
   clausola che su una delle quattro strategie e' vera per definizione non e' un
   test. Sul livello invece l'equal-weight e' il CONTROLLO piu' informativo del
   giro: dice quanto il mese conta per un portafoglio passivo.

2. "MEDIANA NEGATIVA" = mediana dei dodici extra-rendimenti contro
   l'equal-weight annuale ribilanciato NELLO STESSO MESE. Per l'equal-weight
   contro se stesso vale esattamente 0, che non e' positivo: la clausola non
   scatta su di lui, ed e' giusto cosi'.

3. "BATTE IL PROPRIO BENCHMARK" = extra > 0. Le 48 configurazioni includono le 12
   dell'equal-weight contro se stesso, che valgono 0 e quindi non contano come
   vittorie. Lo dichiaro invece di escluderle, perche' escluderle cambierebbe il
   denominatore dopo aver visto i numeri.

FINESTRA. Uso 1969-2026 come i giri 64 e 65, altrimenti il confronto col +1,51 e
il -1,92 non e' comparabile. D10 misura la leva di un parametro su risultati gia'
registrati, non cerca un candidato nuovo. Riporto comunque anche 1969-2009 per
verificare che l'ampiezza non sia un fenomeno post-2010: se una configurazione
risultasse promuovibile andrebbe comunque rivalutata prima del 2010.

La rotazione e' quella VERA del giro 63 su entrambi i lati.
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
warnings.filterwarnings("ignore")

import config as C
import dataio
from research import lab, bench as B

ROUND = 68
OUT = Path(__file__).resolve().parents[2] / "out"
MESI = list(range(1, 13))
NOMI = ["gen", "feb", "mar", "apr", "mag", "giu",
        "lug", "ago", "set", "ott", "nov", "dic"]


def annuale(ind, mese, score=None, top=None):
    """Pesi TARGET di una strategia ribilanciata una volta l'anno nel `mese`.

    Fra un ribilanciamento e l'altro il target E' quello che si ha in mano: non
    si compra niente, quindi la rotazione vera e' zero negli altri undici mesi.
    Se `score` e' None il target al ribilanciamento e' 1/N (equal-weight).
    """
    n = ind.shape[1]
    w = np.ones(n) / n
    out = []
    for i, t in enumerate(ind.index):
        if t.month == mese:
            if score is None:
                w = np.ones(n) / n
            else:
                s = score.iloc[i]
                if s.notna().sum() >= top:
                    best = s.nlargest(top).index
                    w = np.zeros(n)
                    w[[ind.columns.get_loc(c) for c in best]] = 1.0 / top
        out.append(w.copy())
        g = w * (1 + ind.iloc[i].to_numpy(dtype=float))
        ssum = g.sum()
        w = g / ssum if ssum > 0 else w
    return pd.DataFrame(out, index=ind.index, columns=ind.columns)


def valuta(ind, Wt, rf):
    n = ind.shape[1]
    w = np.zeros(n)
    turns = []
    for i in range(len(ind)):
        tgt = Wt.iloc[i].to_numpy(dtype=float)
        turns.append(float(np.abs(tgt - w).sum() / 2.0))
        w = tgt
        g = w * (1 + ind.iloc[i].to_numpy(dtype=float))
        s = g.sum()
        w = g / s if s > 0 else w
    turn = pd.Series(turns, index=ind.index)
    net = ((Wt * ind).sum(axis=1) - turn * C.COST_ROUND_TRIP).dropna()
    r = B.eval_stream("x", net, rf.reindex(net.index).fillna(0.0),
                      turn.reindex(net.index))
    r["rot"] = float(turn.sum()) / (len(ind) / 12)
    r["net"] = net
    return r


def tabella(ind, rf, etichetta):
    mom12 = (1 + ind).rolling(11).apply(np.prod, raw=True).shift(2)
    strategie = [("equal-weight annuale", None, None),
                 ("momentum top-5 annuale", mom12, 5),
                 ("momentum top-10 annuale", mom12, 10),
                 ("momentum top-25 annuale", mom12, 25)]
    bench = {m: valuta(ind, annuale(ind, m), rf) for m in MESI}
    righe = []
    print(f"\n   {etichetta}  ({ind.index[0].year}-{ind.index[-1].year})\n")
    print(f"   {'strategia':<26}" + "".join(f"{x:>7}" for x in NOMI))
    print("   " + "-" * 110)
    for nome, sc, top in strategie:
        irr, extra = [], []
        for m in MESI:
            r = valuta(ind, annuale(ind, m, sc, top), rf)
            irr.append(r["irr_ref"])
            extra.append(r["irr_ref"] - bench[m]["irr_ref"])
            righe.append(dict(strategia=nome, mese=NOMI[m - 1], irr=r["irr_ref"],
                              extra=r["irr_ref"] - bench[m]["irr_ref"],
                              rot=r["rot"], aliq=r["rate_ref"],
                              bench=bench[m]["irr_ref"]))
        print(f"   {nome + ' (IRR)':<26}" + "".join(f"{x:>7.2f}" for x in irr))
        print(f"   {'  vs EW stesso mese':<26}"
              + "".join(f"{x:>+7.2f}" for x in extra))
    return righe, bench


def riassunto(righe):
    out = {}
    for nome in dict.fromkeys(r["strategia"] for r in righe):
        g = [r for r in righe if r["strategia"] == nome]
        irr = np.array([r["irr"] for r in g])
        ex = np.array([r["extra"] for r in g])
        out[nome] = dict(amp=float(irr.max() - irr.min()),
                         med_irr=float(np.median(irr)),
                         med_extra=float(np.median(ex)),
                         vince=int((ex > 0).sum()),
                         best=NOMI[int(np.argmax(ex))],
                         worst=NOMI[int(np.argmin(ex))],
                         amp_ex=float(ex.max() - ex.min()))
    return out


def main():
    ind_full = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind_full.index).fillna(0.0)

    print(f"{'=' * 116}\nD10 — dodici calendari di ribilanciamento per la stessa "
          f"strategia\n{'=' * 116}")

    righe, bench = tabella(ind_full, rf, "FINESTRA PRINCIPALE, come ai giri 64 e 65")
    R = riassunto(righe)

    print(f"\n   {'strategia':<26}{'ampiezza IRR':>14}{'mediana IRR':>13}"
          f"{'mediana extra':>15}{'vince':>8}{'migliore':>10}{'peggiore':>10}")
    print("   " + "-" * 96)
    for nome, d in R.items():
        print(f"   {nome:<26}{d['amp']:>13.2f}%{d['med_irr']:>12.2f}%"
              f"{d['med_extra']:>+14.2f}%{d['vince']:>5}/12{d['best']:>10}"
              f"{d['worst']:>10}")

    # controllo: l'ampiezza e' un fenomeno post-2010?
    ind_pre = ind_full[ind_full.index.year <= 2009]
    righe2, _ = tabella(ind_pre, rf, "CONTROLLO senza l'holdout")
    R2 = riassunto(righe2)
    print(f"\n   {'strategia':<26}{'ampiezza 1969-2026':>20}"
          f"{'ampiezza 1969-2009':>20}")
    print("   " + "-" * 66)
    for nome in R:
        print(f"   {nome:<26}{R[nome]['amp']:>19.2f}%{R2[nome]['amp']:>19.2f}%")

    # ------------------------------------------------------------- verdetto
    amp = {k: v["amp"] for k, v in R.items()}
    sopra2 = sum(1 for v in amp.values() if v > 2.0)
    sotto1 = sum(1 for v in amp.values() if v < 1.0)
    med_pos = [k for k, v in R.items() if v["med_extra"] > 0]
    vinc = sum(v["vince"] for v in R.values())
    tot = 12 * len(R)

    print(f"\n{'=' * 116}\n   VERDETTO\n{'=' * 116}")
    print(f"   Predizione: ampiezza sopra 2 punti per OGNI strategia, mediana "
          f"degli extra NEGATIVA per tutte,")
    print(f"   e meno di UN TERZO delle {tot} configurazioni batte il proprio "
          f"benchmark.")
    print(f"   FALSIFICATA se l'ampiezza resta sotto 1 punto per la MAGGIORANZA "
          f"delle strategie, OPPURE")
    print(f"   la mediana degli extra e' POSITIVA per almeno una strategia.\n")
    print(f"   ampiezza sopra 2 punti           : {sopra2}/{len(R)} strategie"
          f"   (previsto {len(R)}/{len(R)})")
    print(f"   ampiezza sotto 1 punto           : {sotto1}/{len(R)}"
          f"   (falsifica se maggioranza, cioe' >= {len(R) // 2 + 1})")
    print(f"   mediana degli extra positiva     : {len(med_pos)}"
          + (f"  ({', '.join(med_pos)})" if med_pos else "")
          + f"   (falsifica se >= 1)")
    print(f"   configurazioni che battono       : {vinc}/{tot} = "
          f"{vinc / tot * 100:.1f}%   (previsto <33,3%)")

    fals = (sotto1 >= len(R) // 2 + 1) or len(med_pos) >= 1
    print(f"\n   -> ipotesi D10 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'ampiezza > 2 punti ovunque': "
          f"{'centrata' if sopra2 == len(R) else 'SBAGLIATA'}")
    print(f"      clausola 'mediana degli extra negativa ovunque': "
          f"{'centrata' if not med_pos else 'SBAGLIATA'}")
    print(f"      clausola 'meno di un terzo vince': "
          f"{'centrata' if vinc / tot < 1 / 3 else 'SBAGLIATA'}")

    if med_pos:
        n_cum = lab.n_trials_so_far()
        print(f"\n   Mediana positiva: il vantaggio NON dipende dal mese e va "
              f"portato al DSR (N={n_cum}).")

    print(f"\n   Il conflitto fra i giri 64 e 65, riletto:")
    t5 = R["momentum top-5 annuale"]
    print(f"     top-5 annuale, extra da {t5['worst']} a {t5['best']}: "
          f"ampiezza {t5['amp_ex']:.2f} punti, mediana {t5['med_extra']:+.2f}")
    print(f"     il +1,51 del giro 65 era il mese di GENNAIO; la mediana dei "
          f"dodici e' {t5['med_extra']:+.2f}")

    pd.DataFrame(righe).to_csv(OUT / "round68_d10.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="D10 calendario del ribilanciamento",
                         config=f"{r['strategia']} {r['mese']}",
                         window=f"{ind_full.index[0].year}-{ind_full.index[-1].year}",
                         sharpe="", irr=r["irr"], bh_irr=r["bench"],
                         excess=r["extra"], n_obs=len(ind_full),
                         note=f"rot={r['rot']:.3f},aliq={r['aliq']}")
                    for r in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

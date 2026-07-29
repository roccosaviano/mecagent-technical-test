"""Giro 72 — K4: la regola per aprire l'holdout, scritta prima di guardare.

VOCE DELLA CODA, predizione verbatim (committata prima di eseguire):

K4 — La regola per aprire l'holdout, scritta prima di guardare
  L'holdout 2010-2026 non e' mai stato aperto in 68 giri, e il criterio per
  aprirlo e' sempre stato descritto a parole. Scriverlo dopo aver visto un
  candidato promettente non varrebbe niente. Va scritto ORA, che non c'e' nessun
  candidato: il migliore mai registrato e' +0,33 contro il proprio benchmark con
  DSR 0,9424 (giro 65).
  Da produrre: una regola eseguibile — soglie numeriche su margine, DSR,
  stabilita' su finestre mobili e sensibilita' al calendario — che decida da sola
  se un candidato merita l'holdout, piu' il conto di quanti dei 1.296 tentativi
  registrati la passerebbero (previsione: zero).
  PREDIZIONE: nessuno dei candidati mai registrati passa la regola, e la voce si
  chiude con l'holdout ancora sigillato. La soglia che eliminera' PIU' candidati
  non sara' il DSR ma la STABILITA' SUL CALENDARIO, il grado di liberta'
  scoperto al giro 68.
  FALSIFICATA SE: almeno un candidato gia' registrato passa tutte le soglie — nel
  qual caso l'holdout va aperto su quello, una volta sola, e il progetto finisce
  li'.

=========================== LA REGOLA ===========================

Quattro cancelli. Un candidato merita l'holdout SOLO se li passa TUTTI E QUATTRO.
Le soglie sono fissate qui, sopra il codice che le applica, e non si toccano piu'.

  G1  MARGINE
      IRR netta >= benchmark + 1,00 punto, dove il benchmark e' l'equal-weight
      ANNUALE dello stesso universo con la rotazione vera (il piu' severo
      implementabile, stabilito ai giri 60-64), e il margine e' la MEDIANA sui
      dodici calendari di ribilanciamento, non un mese scelto (giro 68).
      Perche' 1,00: e' sopra il rumore misurato al giro 63 sulla correzione della
      rotazione (0,32 medio, 1,35 massimo) e sopra la differenza fra le due
      convenzioni di rotazione. Sotto quella soglia non si distingue una
      strategia da un errore di misura.

  G2  DEFLATED SHARPE
      DSR > 0,95 su N = registro CUMULATO, con var_sr stimata sulla famiglia del
      giro e non sul registro intero (giro 65: sul registro intero SR0 esce 1,78
      per periodo, che non e' credibile).

  G3  STABILITA' NEL TEMPO
      extra-rendimento positivo in >= 2/3 delle finestre decennali mobili E
      mediana degli extra > 0. Due condizioni e non una, perche' il giro 62 ha
      trovato candidati che vincono spesso e rendono zero, e il giro 59 che la
      dispersione decennale e' di 5-10 punti.

  G4  INDIPENDENZA DAL CALENDARIO
      margine positivo in >= 10 dei 12 calendari di ribilanciamento. Una
      strategia a ribilanciamento mensile non ha questo grado di liberta' e passa
      G4 per costruzione: lo dichiaro invece di nasconderlo.
      Perche' 10 su 12: al giro 68 il momentum top-5 annuale vinceva in 5 mesi su
      12 e il suo +1,51 di gennaio era il massimo di dodici estrazioni.

Se un candidato passa tutti e quattro, l'holdout si apre UNA VOLTA SOLA, su
quello solo, e il risultato si registra qualunque sia. Se nessuno passa,
l'holdout resta sigillato e il progetto non ha prodotto una strategia.

===================================================================

L'INSIEME DEI CANDIDATI. "I 1.296 tentativi registrati" non e' letteralmente
applicabile: il registro contiene valutazioni su universi e finestre diversi,
molte non riproducibili in una griglia comune. Applico la regola all'insieme piu'
ampio che condivide universo e finestra — le famiglie provate sui 49 settori —
esattamente come al giro 62. E' una scelta restrittiva: se qualcosa passasse, si
vedrebbe qui.

Finestra 1969-2009: K4 decide se aprire l'holdout, quindi non puo' guardarlo.
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

ROUND = 72
OUT = Path(__file__).resolve().parents[2] / "out"
FINE = 2009
LUNG = 10

G1_MARGINE = 1.00
G2_DSR = 0.95
G3_QUOTA = 2.0 / 3.0
G4_CALENDARI = 10


def rot_vera(rets, Wt):
    n = rets.shape[1]
    w = np.zeros(n)
    turns = []
    for i in range(len(rets)):
        tgt = Wt.iloc[i].to_numpy(dtype=float)
        turns.append(float(np.abs(tgt - w).sum() / 2.0))
        w = tgt
        g = w * (1 + rets.iloc[i].to_numpy(dtype=float))
        s = g.sum()
        w = g / s if s > 0 else w
    return pd.Series(turns, index=rets.index)


def valuta(ind, Wt, rf, idx=None):
    turn = rot_vera(ind, Wt)
    net = ((Wt * ind).sum(axis=1) - turn * C.COST_ROUND_TRIP).dropna()
    if idx is not None:
        net, turn = net.reindex(idx).dropna(), turn.reindex(idx)
    r = B.eval_stream("x", net, rf.reindex(net.index).fillna(0.0),
                      turn.reindex(net.index))
    r["net"] = net
    return r


def pesi_annuali(ind, mese, score=None, top=None):
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


def pesi_mensili(score, top, asc=False):
    rk = score.rank(axis=1, ascending=asc)
    W = (rk <= top).astype(float)
    return W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ind = ind[ind.index.year <= FINE]
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    y0, y1 = ind.index[0].year, ind.index[-1].year

    print(f"{'=' * 108}\nK4 — la regola per aprire l'holdout, applicata ai "
          f"candidati del progetto\n{'=' * 108}")
    print(f"   Universo: 49 settori, {y0}-{y1}. **Holdout 2010-2026 non "
          f"guardato: e' la voce che decide se aprirlo.**")
    print(f"   Soglie: G1 margine >= {G1_MARGINE:.2f}, G2 DSR > {G2_DSR}, "
          f"G3 >= {G3_QUOTA:.1%} finestre e mediana > 0, "
          f"G4 >= {G4_CALENDARI}/12 calendari.\n")

    mom12 = (1 + ind).rolling(11).apply(np.prod, raw=True).shift(2)
    mom6 = (1 + ind).rolling(5).apply(np.prod, raw=True).shift(2)
    vol36 = ind.rolling(36).std().shift(1)
    mix = mom12.rank(axis=1, pct=True) + (-vol36).rank(axis=1, pct=True)

    # (nome, annuale?, score, top)  — score None = equal-weight
    cands = [
        ("momentum 12-2 top-5 annuale", True, mom12, 5),
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
        ("C1 punteggio misto top-10 mensile", False, mix, 10),
    ]

    # benchmark: equal-weight annuale, un calendario per mese
    bench = {m: valuta(ind, pesi_annuali(ind, m), rf) for m in range(1, 13)}
    spans = [(y, y + LUNG - 1) for y in range(y0 + 3, y1 - LUNG + 2)]

    def irr_finestra(net, turn, a, b):
        i = net.index[(net.index.year >= a) & (net.index.year <= b)]
        s = net.reindex(i).dropna()
        if len(s) < 100:
            return None
        return B.eval_stream("x", s, rf.reindex(s.index).fillna(0.0),
                             turn.reindex(s.index))["irr_ref"]

    righe = []
    for nome, ann, sc, top in cands:
        if ann:
            mesi = {m: valuta(ind, pesi_annuali(ind, m, sc, top), rf)
                    for m in range(1, 13)}
            marg = {m: mesi[m]["irr_ref"] - bench[m]["irr_ref"] for m in mesi}
            med = float(np.median(list(marg.values())))
            pos = sum(1 for v in marg.values() if v > 0)
            # il calendario mediano: quello il cui margine e' piu' vicino alla mediana
            mm = min(marg, key=lambda m: abs(marg[m] - med))
            best = mesi[mm]
        else:
            W = pesi_mensili(sc, top)
            best = valuta(ind, W, rf)
            med = best["irr_ref"] - bench[1]["irr_ref"]
            pos = 12          # nessun grado di liberta' sul calendario
            mm = 0
        turn = rot_vera(ind, pesi_annuali(ind, mm, sc, top) if ann
                        else pesi_mensili(sc, top))
        ex = []
        for a, b in spans:
            x = irr_finestra(best["net"], turn, a, b)
            bq = irr_finestra(bench[mm if ann else 1]["net"],
                              rot_vera(ind, pesi_annuali(ind, mm if ann else 1)),
                              a, b)
            if x is not None and bq is not None:
                ex.append(x - bq)
        ex = np.array(ex)
        righe.append(dict(nome=nome, margine=med, calendari=pos,
                          quota=float((ex > 0).mean()),
                          med_ex=float(np.median(ex)), net=best["net"],
                          mese=mm))

    # DSR con var_sr sulla famiglia di questo giro
    srs = []
    for r in righe:
        e = r["net"] - rf.reindex(r["net"].index).fillna(0.0)
        srs.append(float(e.mean() / e.std(ddof=1)))
    var_fam = float(np.var(srs, ddof=1))
    n_cum = lab.n_trials_so_far()
    for r in righe:
        d = lab.deflated_sharpe(r["net"], n_cum, var_sr=var_fam, rf=rf)
        r["dsr"] = float(d["dsr"]) if np.isfinite(d["dsr"]) else 0.0

    print(f"   var_sr sulla famiglia: {var_fam:.6f}   N cumulato: {n_cum}\n")
    print(f"   {'candidato':<36}{'G1 margine':>12}{'G2 DSR':>9}"
          f"{'G3 quota':>10}{'G3 mediana':>12}{'G4 cal.':>9}{'passa':>8}")
    print("   " + "-" * 96)
    for r in righe:
        g1 = r["margine"] >= G1_MARGINE
        g2 = r["dsr"] > G2_DSR
        g3 = r["quota"] >= G3_QUOTA and r["med_ex"] > 0
        g4 = r["calendari"] >= G4_CALENDARI
        r.update(g1=g1, g2=g2, g3=g3, g4=g4, passa=g1 and g2 and g3 and g4)
        segna = lambda ok: "si" if ok else "NO"
        print(f"   {r['nome']:<36}{r['margine']:>+9.2f} {segna(g1):>2}"
              f"{r['dsr']:>7.3f} {segna(g2):>1}{r['quota'] * 100:>7.0f}% "
              f"{segna(g3):>1}{r['med_ex']:>+10.2f}{r['calendari']:>7}/12 "
              f"{segna(g4):>1}{('PASSA' if r['passa'] else '—'):>7}")

    # ------------------------------------------------------------- verdetto
    passano = [r for r in righe if r["passa"]]
    K = len(righe)
    eliminati = {"G1 margine": sum(1 for r in righe if not r["g1"]),
                 "G2 DSR": sum(1 for r in righe if not r["g2"]),
                 "G3 stabilita'": sum(1 for r in righe if not r["g3"]),
                 "G4 calendario": sum(1 for r in righe if not r["g4"])}
    peggiore = max(eliminati, key=eliminati.get)

    print(f"\n{'=' * 108}\n   VERDETTO\n{'=' * 108}")
    print(f"   Predizione: nessun candidato passa, e la soglia che ne elimina "
          f"di piu' e' la STABILITA' SUL CALENDARIO.")
    print(f"   FALSIFICATA se almeno un candidato passa tutti e quattro i "
          f"cancelli.\n")
    print(f"   candidati valutati        : {K}")
    print(f"   che passano tutti e quattro: {len(passano)}"
          + (f"  ({', '.join(r['nome'] for r in passano)})" if passano else ""))
    print(f"\n   quanti ne elimina ciascun cancello (un candidato puo' essere "
          f"eliminato da piu' di uno):")
    for k, v in sorted(eliminati.items(), key=lambda x: -x[1]):
        print(f"     {k:<18}{v:>3}/{K}")
    print(f"   il cancello piu' selettivo e': **{peggiore}**"
          f"   (previsto: G4 calendario)")

    fals = len(passano) > 0
    print(f"\n   -> ipotesi K4 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'nessuno passa': "
          f"{'centrata' if not passano else 'SBAGLIATA'}")
    print(f"      clausola 'il calendario elimina piu' del DSR': "
          f"{'centrata' if eliminati['G4 calendario'] > eliminati['G2 DSR'] else 'SBAGLIATA'}")

    if passano:
        print(f"\n   L'HOLDOUT VA APERTO su {passano[0]['nome']}, una volta "
              f"sola. Non lo apro in questo giro: la regola dice CHE va aperto,")
        print(f"   e aprirlo e' un atto separato da registrare come tale.")
    else:
        print(f"\n   Nessun candidato merita l'holdout. **Resta sigillato.**")

    pd.DataFrame([{k: v for k, v in r.items() if k != "net"} for r in righe]
                 ).to_csv(OUT / "round72_k4.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="K4 regola per l'holdout",
                         config=r["nome"], window=f"{y0}-{y1}", sharpe="",
                         irr=r["margine"], bh_irr="", excess=r["med_ex"],
                         n_obs=len(spans),
                         note=f"dsr={r['dsr']:.3f},cal={r['calendari']}")
                    for r in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

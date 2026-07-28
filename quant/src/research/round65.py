"""Giro 65 — D8: quali verdetti sopravvivono alla correzione della rotazione.

VOCE DELLA CODA, predizione verbatim:

D8 — Quali verdetti "perde contro l'equal-weight" sopravvivono alla correzione
  Nata al giro 63. La correzione della rotazione vale 0,32 punti in media sui
  candidati, ma 1,35 punti sul solo equal-weight mensile, che e' il benchmark
  usato dai giri 30-43. L'asimmetria e' il punto: correggere sposta il METRO
  molto piu' dei MISURATI. Ne segue meccanicamente che ogni verdetto in cui un
  candidato perdeva contro l'equal-weight mensile per meno di ~1,35 punti e'
  sospetto, e al giro 63 ne ho controllati solo cinque. Il giro 63 ha gia'
  mostrato che uno dei cinque si ribalta.
  Da rifare: censire in QUEUE.md e nei mini-report TUTTI i verdetti la cui
  formula e' "il candidato X perde contro l'equal-weight di meno di 1,35 punti",
  rieseguirli con la rotazione vera su entrambi i lati, e riportare quanti
  cambiano segno.
  PREDIZIONE: i verdetti col margine sotto 1,35 punti sono FRA 4 E 10, e ne
  cambia segno MENO DI UN TERZO — perche' correggere alza anche la rotazione dei
  candidati, non solo quella del benchmark, e i due effetti si compensano in
  buona parte. Nessuno dei ribaltati supera comunque il DSR, quindi il numero di
  promozioni resta ZERO.
  FALSIFICATA SE: cambia segno PIU' DI META' dei verdetti col margine sotto 1,35
  punti — nel qual caso la correzione non e' una nota metodologica ma una
  revisione dei giri 30-43, e vanno rieseguiti tutti — OPPURE un candidato
  ribaltato supera il DSR 0,95 sul registro cumulato, nel qual caso c'e' per la
  prima volta qualcosa da portare all'holdout.

COME COSTRUISCO IL CENSIMENTO, dichiarato prima di calcolare.

"Il candidato X perde contro l'equal-weight di meno di 1,35 punti" va reso
operativo. Prendo TUTTE le coppie (candidato, equal-weight) che i giri 04, 05,
31, 34, 43 e 50 hanno effettivamente valutato e che sono riproducibili sullo
stesso universo, misuro il margine CON LA CONVENZIONE ORIGINALE — cioe' la
rotazione dei pesi target, quella di `bench.wbacktest`, che e' quella che quei
giri usavano — e tengo quelle con |margine| < 1,35.

Uso il valore assoluto e non solo i margini negativi: un verdetto "vince di
0,30" (F1, regioni top-1) e' esposto alla correzione esattamente quanto uno
"perde di 0,30", e escluderlo perche' ha il segno comodo sarebbe scegliere il
campione dopo aver visto i dati. Lo dichiaro qui.

Un verdetto "cambia segno" se il segno del margine e' diverso prima e dopo.

IL DSR si calcola solo sui ribaltati che diventano POSITIVI: un candidato che
resta sotto il proprio benchmark non e' promuovibile per definizione, come il
giro 64 ha gia' dovuto chiarire. N = registro cumulato, che e' la soglia del
progetto.
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
from research.round31 import hrp_weights, inv_var

ROUND = 65
OUT = Path(__file__).resolve().parents[2] / "out"
SOGLIA = 1.35


def rot_vera(rets, Wt):
    """|W_target,t - W_derivati,t| / 2 — quello che si compra e si vende."""
    n = rets.shape[1]
    w = np.zeros(n)
    turns = []
    for i in range(len(rets)):
        tgt = Wt.iloc[i].to_numpy(dtype=float)
        if tgt.sum() <= 0:
            tgt = w
        turns.append(float(np.abs(tgt - w).sum() / 2.0))
        w = tgt
        g = w * (1 + rets.iloc[i].to_numpy(dtype=float))
        s = g.sum()
        w = g / s if s > 0 else w
    return pd.Series(turns, index=rets.index)


def rot_target(Wt):
    """La convenzione originale: |W_target,t - W_target,t-1| / 2."""
    return Wt.diff().abs().sum(axis=1).fillna(Wt.abs().sum(axis=1)) / 2.0


def valuta(rets, Wt, rf, nome, vera):
    turn = rot_vera(rets, Wt) if vera else rot_target(Wt)
    net = ((Wt * rets).sum(axis=1) - turn * C.COST_ROUND_TRIP).dropna()
    r = B.eval_stream(nome, net, rf.reindex(net.index).fillna(0.0),
                      turn.reindex(net.index))
    r["net"] = net
    r["rot"] = float(turn.sum()) / (len(rets) / 12)
    return r


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    n = ind.shape[1]
    y0, y1 = ind.index[0].year, ind.index[-1].year

    print(f"{'=' * 106}\nD8 — i verdetti col margine dentro la correzione\n"
          f"{'=' * 106}")
    print(f"   Universo: 49 settori, {y0}-{y1}. Soglia del censimento: "
          f"|margine| < {SOGLIA} punti.\n")

    mom12 = (1 + ind).rolling(11).apply(np.prod, raw=True).shift(2)
    vol36 = ind.rolling(36).std().shift(1)
    keep = pd.Series(ind.index.month == 1, index=ind.index)

    def topw(score, top, asc=False):
        rk = score.rank(axis=1, ascending=asc)
        W = (rk <= top).astype(float)
        return W.div(W.sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)

    def annuale(W):
        return W.where(keep).ffill().fillna(0.0)

    def ottimizzato(metodo, lookback=60, rebal=12):
        W = pd.DataFrame(0.0, index=ind.index, columns=ind.columns)
        w = np.ones(n) / n
        for i in range(len(ind.index)):
            if i >= lookback and i % rebal == 0:
                win = ind.iloc[i - lookback:i]
                cov = win.cov() * 12
                w = hrp_weights(cov, win.corr()) if metodo == "hrp" else inv_var(cov)
            W.iloc[i] = w
        return W

    def ew_drift():
        w = np.ones(n) / n
        out = []
        for i, t in enumerate(ind.index):
            if t.month == 1:
                w = np.ones(n) / n
            out.append(w.copy())
            g = w * (1 + ind.iloc[i].to_numpy(dtype=float))
            s = g.sum()
            w = g / s if s > 0 else w
        return pd.DataFrame(out, index=ind.index, columns=ind.columns)

    EWM = pd.DataFrame(1.0 / n, index=ind.index, columns=ind.columns)
    EWA = ew_drift()
    mix = mom12.rank(axis=1, pct=True) + (-vol36).rank(axis=1, pct=True)
    px = (1 + ind.mean(axis=1)).cumprod()

    # (nome, pesi candidato, pesi benchmark, nome benchmark, giro)
    coppie = [
        ("HRP annuale", ottimizzato("hrp"), EWA, "EW annuale", "31 (A2)"),
        ("inverse-variance annuale", ottimizzato("invvar"), EWA, "EW annuale", "31/34"),
        ("H5 momentum top-10 mensile", topw(mom12, 10), EWM, "EW mensile", "05/43"),
        ("C1 punteggio misto top-10", topw(mix, 10), EWM, "EW mensile", "11/43"),
        ("H4 low-vol 36m top-10", topw(vol36, 10, asc=True), EWM, "EW mensile", "04/43"),
        ("low-vol 36m top-25 annuale", annuale(topw(vol36, 25, asc=True)), EWA, "EW annuale", "04"),
        ("momentum top-5 annuale", annuale(topw(mom12, 5)), EWM, "EW mensile", "50 (F2)"),
        ("momentum top-10 annuale", annuale(topw(mom12, 10)), EWM, "EW mensile", "50 (F2)"),
        ("momentum top-25 annuale", annuale(topw(mom12, 25)), EWM, "EW mensile", "50 (F2)"),
        ("momentum top-25 mensile", topw(mom12, 25), EWM, "EW mensile", "50 (F2)"),
        ("filtro di tendenza 10m", EWM.mul(B.ma_filter(px, 10), axis=0).fillna(0.0),
         EWM, "EW mensile", "G1"),
    ]

    righe = []
    print(f"   {'candidato':<30}{'benchmark':<13}{'giro':<9}"
          f"{'margine orig.':>14}{'margine vero':>14}{'in censimento':>15}"
          f"{'cambia segno':>14}")
    print("   " + "-" * 109)
    for nome, Wc, Wb, bnome, giro in coppie:
        a_c = valuta(ind, Wc, rf, nome, vera=False)
        a_b = valuta(ind, Wb, rf, bnome, vera=False)
        v_c = valuta(ind, Wc, rf, nome, vera=True)
        v_b = valuta(ind, Wb, rf, bnome, vera=True)
        m0 = a_c["irr_ref"] - a_b["irr_ref"]
        m1 = v_c["irr_ref"] - v_b["irr_ref"]
        dentro = abs(m0) < SOGLIA
        flip = dentro and ((m0 > 0) != (m1 > 0))
        righe.append(dict(candidato=nome, benchmark=bnome, giro=giro,
                          margine_orig=m0, margine_vero=m1, dentro=dentro,
                          flip=flip, irr_orig=a_c["irr_ref"],
                          irr_vero=v_c["irr_ref"], rot_orig=a_c["rot"],
                          rot_vera=v_c["rot"], rate_orig=a_c["rate_ref"],
                          rate_vero=v_c["rate_ref"], net=v_c["net"]))
        print(f"   {nome:<30}{bnome:<13}{giro:<9}{m0:>13.2f}%{m1:>13.2f}%"
              f"{'SI' if dentro else 'no':>15}"
              f"{('SI' if flip else 'no') if dentro else '-':>14}")

    cens = [r for r in righe if r["dentro"]]
    flips = [r for r in cens if r["flip"]]
    positivi = [r for r in flips if r["margine_vero"] > 0]

    print(f"\n   Perche' cambiano: il salto di aliquota\n")
    print(f"   {'candidato':<30}{'rot. orig.':>12}{'rot. vera':>11}"
          f"{'aliq. orig.':>13}{'aliq. vera':>12}")
    print("   " + "-" * 78)
    for r in cens:
        seg = " <-- salta" if r["rate_orig"] != r["rate_vero"] else ""
        print(f"   {r['candidato']:<30}{r['rot_orig']:>11.3f}x"
              f"{r['rot_vera']:>10.3f}x{r['rate_orig']:>12}%"
              f"{r['rate_vero']:>11}%{seg}")

    # ---------------------------------------------- il conflitto col giro 64
    # Il giro 64 dava il top-5 annuale a 8,73% con rotazione 1,022x e aliquota
    # 52%. Qui fa 12,16% con rotazione 0,962x e aliquota 33%. Stessa strategia,
    # stesso universo, stesso periodo: cambia SOLO il calendario del
    # ribilanciamento — `round50.rotate` ribilancia ogni 12 mesi a partire
    # dall'inizio del campione, `annuale()` ribilancia a gennaio. Va misurato,
    # non lasciato come discrepanza fra due giri.
    from research.round50 import rotate as rot50
    print(f"\n   IL CALENDARIO DEL RIBILANCIAMENTO — stessa strategia, "
          f"due implementazioni:\n")
    print(f"   {'strategia':<22}{'calendario':<26}{'rotaz.':>9}{'aliq.':>7}"
          f"{'IRR':>9}{'vs EW ann.':>12}")
    print("   " + "-" * 85)
    ewa_v = valuta(ind, EWA, rf, "EW annuale", vera=True)
    for top in (5, 10, 25):
        for etich, W in [("gennaio civile", annuale(topw(mom12, top))),
                         ("ogni 12 mesi dall'inizio", rot50(ind, top, 12))]:
            r = valuta(ind, W, rf, f"top-{top}", vera=True)
            print(f"   {'momentum top-' + str(top):<22}{etich:<26}"
                  f"{r['rot']:>8.3f}x{r['rate_ref']:>6}%{r['irr_ref']:>8.2f}%"
                  f"{r['irr_ref'] - ewa_v['irr_ref']:>+11.2f}")
    print(f"\n   EW annuale di riferimento: {ewa_v['irr_ref']:.2f}%")

    # ------------------------------------------------------------------ DSR
    n_cum = lab.n_trials_so_far()
    dsr_max = 0.0
    if positivi:
        print(f"\n   DSR dei ribaltati che diventano POSITIVI "
              f"(N = {n_cum}, registro cumulato):")
        # var_sr di default viene dal registro INTERO, che mescola famiglie con
        # profili di rischio diversi: produce SR0 per periodo implausibili.
        # Riporto anche la variante con var_sr calcolata sugli 11 candidati di
        # QUESTO giro, che e' la famiglia su cui si sta guardando.
        srs = []
        for r in righe:
            e = r["net"] - rf.reindex(r["net"].index).fillna(0.0)
            srs.append(float(e.mean() / e.std(ddof=1)))
        var_fam = float(np.var(srs, ddof=1))
        globals()["var_fam"] = var_fam
        print(f"     var_sr dagli 11 candidati di questo giro: {var_fam:.6f}")
        for r in positivi:
            d = lab.deflated_sharpe(r["net"], n_cum, rf=rf)
            d2 = lab.deflated_sharpe(r["net"], n_cum, var_sr=var_fam, rf=rf)
            dsr_max = max(dsr_max, max(d["dsr"] if np.isfinite(d["dsr"]) else 0.0,
                                       d2["dsr"] if np.isfinite(d2["dsr"]) else 0.0))
            print(f"     {r['candidato']:<30}SR {d['sr_period']:.4f}  "
                  f"SR0(registro) {d['sr0']:.4f} DSR {d['dsr']:.4f}  |  "
                  f"SR0(famiglia) {d2['sr0']:.4f} DSR {d2['dsr']:.4f}")
    else:
        print(f"\n   Nessun ribaltato diventa positivo: niente DSR da calcolare.")

    # ------------------------------------------------------------- verdetto
    K = len(cens)
    q = len(flips) / K if K else float("nan")
    print(f"\n{'=' * 106}\n   VERDETTO\n{'=' * 106}")
    print(f"   Predizione: i verdetti col margine sotto {SOGLIA} punti sono "
          f"FRA 4 E 10, ne cambia segno")
    print(f"   MENO DI UN TERZO, e nessun ribaltato supera il DSR.")
    print(f"   FALSIFICATA se cambia segno PIU' DI META', oppure un ribaltato "
          f"supera DSR 0,95.\n")
    print(f"   coppie valutate                  : {len(righe)}")
    print(f"   dentro il censimento (|m| < {SOGLIA}) : {K}"
          f"   (previsto fra 4 e 10)")
    print(f"   cambiano segno                   : {len(flips)}/{K}"
          + (f" = {q * 100:.1f}%" if K else "")
          + f"   (previsto <33,3%, falsifica sopra 50%)")
    print(f"   ribaltati che diventano positivi : {len(positivi)}")
    print(f"   DSR massimo fra questi           : "
          + (f"{dsr_max:.4f}" if positivi else "n.d."))
    fals = (K > 0 and q > 0.5) or dsr_max > 0.95
    print(f"\n   -> ipotesi D8 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'fra 4 e 10 verdetti': "
          f"{'centrata' if 4 <= K <= 10 else 'SBAGLIATA'}")
    print(f"      clausola 'meno di un terzo cambia segno': "
          f"{'centrata' if K and q < 1 / 3 else 'SBAGLIATA'}")
    print(f"      clausola 'promozioni zero': "
          f"{'centrata' if dsr_max <= 0.95 else 'SBAGLIATA'}")
    # La regola di promozione di STATE.md ha DUE condizioni, non una: battere il
    # benchmark E DSR > 0,95. La riga qui sotto le controlla entrambe, perche'
    # guardare solo il DSR e' incompleto — e' lo stesso chiarimento che il giro
    # 64 ha gia' dovuto fare.
    print(f"\n   La regola di promozione (STATE.md) richiede DUE condizioni:")
    print(f"   {'candidato':<30}{'vs EW mensile':>15}{'vs EW annuale':>15}"
          f"{'DSR max':>10}{'promuovibile':>14}")
    print("   " + "-" * 84)
    ewm_v = valuta(ind, EWM, rf, "EW mensile", vera=True)
    promuove = False
    for r in positivi:
        g_m = r["irr_vero"] - ewm_v["irr_ref"]
        g_a = r["irr_vero"] - ewa_v["irr_ref"]
        d2 = lab.deflated_sharpe(r["net"], n_cum, var_sr=var_fam, rf=rf)
        ok = g_a > 0 and d2["dsr"] > 0.95
        promuove = promuove or ok
        print(f"   {r['candidato']:<30}{g_m:>+14.2f}%{g_a:>+14.2f}%"
              f"{d2['dsr']:>10.4f}{'SI' if ok else 'no':>14}")
    print(f"\n   Promozioni: {'UNA' if promuove else 'ZERO'}. "
          f"Holdout ancora sigillato.")

    pd.DataFrame([{k: v for k, v in r.items() if k != "net"} for r in righe]
                 ).to_csv(OUT / "round65_d8.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="D8 verdetti dentro la correzione",
                         config=f"{r['candidato']} vs {r['benchmark']}",
                         window=f"{y0}-{y1}", sharpe="", irr=r["irr_vero"],
                         bh_irr=r["irr_vero"] - r["margine_vero"],
                         excess=r["margine_vero"], n_obs=len(ind),
                         note=f"orig={r['margine_orig']:.2f},flip={r['flip']}")
                    for r in righe])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

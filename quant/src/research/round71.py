"""Giro 71 — K3: il vantaggio del veicolo, rimisurato con la rotazione vera.

VOCE DELLA CODA, predizione verbatim (committata prima di eseguire):

K3 — Il vantaggio del veicolo, rimisurato con la rotazione vera
  Il giro 53 aveva trovato +2,77 punti dallo spostare la rotazione dentro un
  fondo UCITS invece di farla in conto proprio, poi corretti a +1,23 dopo il bug
  dei lotti ETF e a +0,34 dopo aver tassato i dividendi. Non e' mai stato
  rimisurato dopo i giri 63-68, che hanno cambiato come si misura la rotazione.
  PREDIZIONE: con la rotazione vera il vantaggio del veicolo CRESCE rispetto al
  +0,34, e finisce fra +0,5 e +2,0 punti, perche' la correzione colpisce chi ruota
  in conto proprio e non chi ruota dentro il fondo. Ma resta SOTTO i 2,77 del giro
  53, e SOTTO il divario che separa il momentum dall'equal-weight, quindi non
  salva nessuna strategia: sposta solo dove conviene tenerla.
  FALSIFICATA SE: il vantaggio risulta NEGATIVO, oppure SOPRA 2,77.

UN ERRORE NELLA VOCE, DICHIARATO PRIMA DI ESEGUIRE. Rileggendo il giro 53 e
STATE.md, i numeri che la voce incolla in una sola catena sono DUE quantita'
diverse:

  (a) "spostare la rotazione dentro il fondo" = +2,77
      stesso lordo, stesso regime CGT: cambia solo CHI realizza la plusvalenza.
      IRR(momentum senza realizzo) - IRR(momentum con realizzo sulla rotazione)

  (b) "vantaggio del veicolo" = +2,15 -> +1,23 (bug dei lotti ETF)
                                     -> +0,34 (dividendi tassati al detentore diretto)
      IRR(ETF UCITS) - IRR(detenzione diretta in CGT)

La voce dice "il vantaggio del veicolo ... cresce rispetto al +0,34 ... resta
sotto i 2,77": mescola (b) con (a). Non riscrivo la predizione — sarebbe
esattamente cio' che il protocollo vieta. Misuro ENTRAMBE, applico la condizione
di falsificazione a entrambe, e dichiaro l'ambiguita' qui invece di scegliere
dopo aver visto quale delle due mi conviene.

COSA CAMBIA RISPETTO AL GIRO 53. Solo la rotazione: |W_target - W_derivati| / 2
invece di |W_target - W_target precedente| / 2. Piu' i dividendi tassati al 52%
per chi detiene direttamente, che era gia' la correzione post-giro 53.

DIVIDENDI. I rendimenti di Ken French sono TOTAL RETURN. Per il detentore diretto
il dividendo e' tassato ogni anno al 52%, quindi va separato: rendimento di solo
prezzo = totale meno 2%/anno, e il 2% entra come div_yield. Dentro un fondo ad
accumulazione il dividendo non e' un evento tassabile per l'investitore.

FINESTRA: la stessa del giro 53, altrimenti il confronto col +2,77 non vale.
E' una rimisurazione di un risultato gia' registrato, non una ricerca di
candidati nuovi.
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
from tax import simulate_pac, CGT_SHARES, ETF_UCITS

ROUND = 71
OUT = Path(__file__).resolve().parents[2] / "out"
DIV = 0.02        # dividend yield annuo dell'azionario USA, come ai giri 53-56


def rot_vera(rets, Wt):
    """|W_target,t - W_derivati,t| / 2 — la convenzione dei giri 63-68."""
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


def pac(ret, rf, regime, realize=None, div=None):
    return simulate_pac(ret, regime, rf=rf.reindex(ret.index).fillna(0.0),
                        realize_frac=(realize.reindex(ret.index).clip(0, 1)
                                      if realize is not None else None),
                        div_yield=div, periods_per_year=12)


def main():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    mkt = (ff["Mkt-RF"] + ff["RF"]).dropna()
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()

    W = B.xs_momentum(ind, 12, 1, 10).shift(1).fillna(0.0)
    # lordo: identico al giro 53 (costi di transazione dentro), ma la rotazione
    # che genera il REALIZZO ora e' quella vera
    turn_53 = W.diff().abs().sum(axis=1).fillna(W.abs().sum(axis=1)) / 2.0
    turn_vera = rot_vera(ind, W)
    net_m = ((W * ind).sum(axis=1) - turn_vera * C.COST_ROUND_TRIP).dropna()

    ix = net_m.index.intersection(mkt.index)
    net_m = net_m.reindex(ix)
    t53, tve = turn_53.reindex(ix), turn_vera.reindex(ix)
    cap = mkt.reindex(ix)
    rfg = rf.reindex(ix).fillna(0.0)
    anni = len(ix) / 12
    dm = pd.Series(DIV / 12.0, index=ix)

    print(f"{'=' * 100}\nK3 — il vantaggio del veicolo con la rotazione vera\n"
          f"{'=' * 100}")
    print(f"   Finestra {ix[0].date()} → {ix[-1].date()} ({len(ix)} mesi), "
          f"la stessa del giro 53.")
    print(f"   Momentum settoriale top-10 mensile. Rotazione che genera il "
          f"realizzo:")
    print(f"     convenzione del giro 53 : {float(t53.sum()) / anni:.3f}x l'anno")
    print(f"     rotazione VERA          : {float(tve.sum()) / anni:.3f}x l'anno "
          f"({float(tve.sum()) / float(t53.sum()) - 1:+.1%})\n")

    # per il detentore diretto: prezzo separato dal dividendo
    net_m_px = net_m - DIV / 12.0
    cap_px = cap - DIV / 12.0

    combos = [
        ("momentum, rotazione MIA (CGT + div)", net_m_px, tve, CGT_SHARES, dm),
        ("momentum DENTRO un fondo, CGT", net_m, None, CGT_SHARES, None),
        ("momentum DENTRO un fondo, ETF UCITS", net_m, None, ETF_UCITS, None),
        ("cap-weight diretto (CGT + div)", cap_px, None, CGT_SHARES, dm),
        ("cap-weight via ETF UCITS", cap, None, ETF_UCITS, None),
    ]
    res = {}
    print(f"   {'configurazione':<40}{'CAGR':>9}{'IRR netta':>12}")
    print("   " + "-" * 61)
    for lbl, r_, rz, reg, dv in combos:
        p = pac(r_, rfg, reg, rz, dv)
        st = B.stats(r_)
        res[lbl] = p.irr_annual
        print(f"   {lbl:<40}{st['cagr']:>8.2f}%{p.irr_annual:>11.2f}%")

    a = (res["momentum DENTRO un fondo, CGT"]
         - res["momentum, rotazione MIA (CGT + div)"])
    # VERSO: STATE.md definisce il vantaggio come quello delle AZIONI DIRETTE
    # sull'ETF UCITS ("+0,34"). Lo tengo, altrimenti il confronto col registrato
    # ha il segno rovesciato.
    b = (res["cap-weight diretto (CGT + div)"] - res["cap-weight via ETF UCITS"])

    # DUE correzioni separate, per capire quale delle due muove il numero:
    #   rotazione vera invece di quella del giro 53
    #   dividendi tassati al detentore diretto, che il giro 53 non aveva
    p53 = pac(net_m_px, rfg, CGT_SHARES, t53, dm)
    a53 = res["momentum DENTRO un fondo, CGT"] - p53.irr_annual
    p_nodiv = pac(net_m, rfg, CGT_SHARES, tve, None)
    a_nodiv = res["momentum DENTRO un fondo, CGT"] - p_nodiv.irr_annual

    print(f"\n   LE DUE QUANTITA' CHE LA VOCE MESCOLA:\n")
    print(f"   (a) spostare la rotazione DENTRO il fondo      "
          f"{a:>+7.2f} punti   (giro 53: +2,77)")
    print(f"       scomposizione delle due correzioni:")
    print(f"         come il giro 53 (nessuna delle due)         "
          f"{a_nodiv - (a - a53):>+7.2f}")
    print(f"         + rotazione vera                            "
          f"{a - a53:>+7.2f}")
    print(f"         + dividendi tassati al detentore diretto    "
          f"{a - a_nodiv:>+7.2f}")
    print(f"   (b) vantaggio del veicolo, AZIONI DIRETTE sull'ETF "
          f"{b:>+7.2f} punti")
    print(f"       registrato: +0,34 (1990-2023), +0,56 (1990-2026), "
          f"qui su 1969-2026")

    # il termine di paragone: il divario momentum-equal-weight
    ewa = pd.DataFrame(0.0, index=ind.index, columns=ind.columns)
    w = np.ones(ind.shape[1]) / ind.shape[1]
    tmp = []
    for i, t in enumerate(ind.index):
        if t.month == 1:
            w = np.ones(ind.shape[1]) / ind.shape[1]
        tmp.append(w.copy())
        g = w * (1 + ind.iloc[i].to_numpy(dtype=float))
        s = g.sum()
        w = g / s if s > 0 else w
    ewa = pd.DataFrame(tmp, index=ind.index, columns=ind.columns)
    t_ew = rot_vera(ind, ewa).reindex(ix)
    net_ew = ((ewa * ind).sum(axis=1) - rot_vera(ind, ewa) * C.COST_ROUND_TRIP)
    net_ew = net_ew.reindex(ix)
    irr_ew = pac(net_ew - DIV / 12.0, rfg, CGT_SHARES, t_ew, dm).irr_annual
    divario = res["momentum, rotazione MIA (CGT + div)"] - irr_ew
    print(f"\n   Termine di paragone: equal-weight annuale diretto "
          f"{irr_ew:.2f}%,")
    print(f"   divario momentum-meno-equal-weight {divario:+.2f} punti.")

    # ------------------------------------------------------------- verdetto
    print(f"\n{'=' * 100}\n   VERDETTO\n{'=' * 100}")
    print(f"   Predizione: il vantaggio cresce rispetto al +0,34 e finisce fra "
          f"+0,5 e +2,0 punti,")
    print(f"   resta sotto i 2,77 del giro 53 e sotto il divario "
          f"momentum-equal-weight.")
    print(f"   FALSIFICATA se risulta NEGATIVO, oppure SOPRA 2,77.\n")
    for nome, v in (("(a) rotazione dentro il fondo", a),
                    ("(b) vantaggio del veicolo", b)):
        st = ("FALSIFICA (negativo)" if v < 0 else
              "FALSIFICA (sopra 2,77)" if v > 2.77 else "dentro i limiti")
        print(f"   {nome:<34}{v:>+8.2f} punti   {st}")
    fals = a < 0 or a > 2.77 or b < 0 or b > 2.77
    print(f"\n   -> ipotesi K3 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'fra +0,5 e +2,0': (a) "
          f"{'centrata' if 0.5 <= a <= 2.0 else 'SBAGLIATA'}, (b) "
          f"{'centrata' if 0.5 <= b <= 2.0 else 'SBAGLIATA'}")
    print(f"      clausola 'cresce rispetto al +0,34': (b) "
          f"{'centrata' if b > 0.34 else 'SBAGLIATA'}")
    print(f"      clausola 'sotto il divario momentum-equal-weight': (a) "
          f"{'centrata' if a < abs(divario) else 'SBAGLIATA'}")

    righe = [dict(quantita="a_rotazione_nel_fondo", valore=a, giro53=2.77),
             dict(quantita="a_con_rotazione_giro53", valore=a53, giro53=2.77),
             dict(quantita="b_vantaggio_veicolo", valore=b, giro53=0.34),
             dict(quantita="divario_mom_meno_ew", valore=divario, giro53=np.nan)]
    pd.DataFrame(righe).to_csv(OUT / "round71_k3.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="K3 vantaggio del veicolo",
                         config=lbl, window=f"{ix[0].year}-{ix[-1].year}",
                         sharpe="", irr=v, bh_irr="", excess="", n_obs=len(ix),
                         note="rotazione vera") for lbl, v in res.items()])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

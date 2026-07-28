"""Giro 64 — D7: F2 contro un equal-weight che paga il suo ribilanciamento.

VOCE DELLA CODA, predizione verbatim:

D7 — F2 rivalutata contro un equal-weight che paga il suo ribilanciamento
  Nata al giro 62. Il giro 50 (F2) ha concluso che nessuna delle 15 celle
  posizioni x frequenza batte l'equal-weight statico, col massimo a top-5 annuale
  10,02% contro 11,16%: -1,14 punti. Ma quel benchmark e' l'equal-weight
  GRATUITO — il giro 60 ha mostrato che `wbacktest` non gli addebita la rotazione
  di 0,20x/anno, che vale 1,35 punti. Con quella addebitata, l'equal-weight
  mensile vale 9,81% e l'annuale 10,65%, e il divario di F2 si chiuderebbe o si
  invertirebbe. Al giro 62 lo stesso candidato risulta +2,14 contro il cap-weight
  e +1,84 contro l'equal-weight in media su 46 finestre decennali.
  Da rifare: l'intera griglia di F2 (5 concentrazioni x 3 frequenze) contro
  l'equal-weight mensile e annuale CON LA ROTAZIONE DERIVATA, riportando IRR
  netta a 33% e 52% e il DSR su N = 15, che e' la dimensione della griglia.
  PREDIZIONE: il top-5 annuale supera l'equal-weight annuale correttamente
  addebitato di 0,5-2 punti, ma il DSR resta sotto 0,95 su N=15 e cresce a
  N=1.157 nel registro cumulato, quindi il verdetto di F2 regge come NON
  PROMOSSO. Cioe': il benchmark era sbagliato, la conclusione no.
  FALSIFICATA SE: il top-5 annuale resta SOTTO l'equal-weight annuale
  correttamente addebitato — nel qual caso il difetto di `wbacktest` non spostava
  nulla e F2 era giusta per intero — OPPURE il DSR supera 0,95, nel qual caso
  c'e' per la prima volta un candidato da portare all'holdout.

COSA RIUSO E COSA CAMBIO. La griglia e' quella del giro 50, importata dallo
stesso codice (`round50.rotate`, `round50.FREQS`): se la riscrivessi non starei
piu' rivalutando F2, starei facendo un'altra cosa. L'UNICA differenza e' come si
misura la rotazione, cioe' il punto della voce.

`rotate` restituisce pesi TARGET costanti fra un ribilanciamento e l'altro, che
e' la cosa giusta: sono i pesi che la strategia vuole. La rotazione vera e'
|W_tgt,t - W_der,t|/2, con W_der i pesi che risultano dal periodo precedente per
effetto dei rendimenti (giro 63).

I DUE BENCHMARK, entrambi con la rotazione vera:
  equal-weight MENSILE   target fisso a 1/N, ricomprato ogni mese
  equal-weight ANNUALE   1/N a gennaio, poi i pesi derivano fino al gennaio dopo
Il secondo va costruito facendo DERIVARE i pesi: tenere fermo il target a 1/N e
chiamarlo annuale e' ribilanciamento mensile travestito, l'errore in cui sono
cascato ai giri 60 e 63.

IL DSR. C'e' selezione — quindicicelle e si guarda la migliore — quindi
N = 15 e' il minimo onesto, e var_sr e' la dispersione degli Sharpe DENTRO la
griglia, che e' esattamente la famiglia su cui si sta scegliendo. Riporto anche
il DSR su N = registro cumulato, che e' la soglia vera del progetto.
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
from research.round50 import rotate, FREQS

ROUND = 64
OUT = Path(__file__).resolve().parents[2] / "out"
N_GRID = 15


def con_rotazione_vera(rets, Wt, cost=C.COST_ROUND_TRIP):
    """Rendimento netto e rotazione VERA di un portafoglio a pesi target."""
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
    turn = pd.Series(turns, index=rets.index)
    return (Wt * rets).sum(axis=1) - turn * cost, turn


def ew_annuale(rets):
    """1/N a gennaio, pesi che derivano fino al gennaio successivo."""
    n = rets.shape[1]
    w = np.ones(n) / n
    out = []
    for i, t in enumerate(rets.index):
        if t.month == 1:
            w = np.ones(n) / n
        out.append(w.copy())
        g = w * (1 + rets.iloc[i].to_numpy(dtype=float))
        s = g.sum()
        w = g / s if s > 0 else w
    return pd.DataFrame(out, index=rets.index, columns=rets.columns)


def main():
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all").dropna()
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"].reindex(ind.index).fillna(0.0)
    n = ind.shape[1]
    y0, y1 = ind.index[0].year, ind.index[-1].year
    anni = len(ind) / 12

    print(f"{'=' * 100}\nD7 — la griglia di F2 contro benchmark che pagano il "
          f"ribilanciamento\n{'=' * 100}")
    print(f"   Universo: 49 settori, {y0}-{y1}. Griglia e codice del giro 50, "
          f"rotazione del giro 63.\n")

    # ------------------------------------------------------- i due benchmark
    ewm = pd.DataFrame(1.0 / n, index=ind.index, columns=ind.columns)
    bench = {}
    for nm, W in [("equal-weight mensile", ewm), ("equal-weight annuale", ew_annuale(ind))]:
        net, turn = con_rotazione_vera(ind, W)
        r = B.eval_stream(nm, net.dropna(), rf, turn)
        r["rot"] = float(turn.sum()) / anni
        bench[nm] = r
    # e la versione GRATUITA, quella che F2 aveva usato
    net0, t0 = (ewm * ind).sum(axis=1), pd.Series(0.0, index=ind.index)
    bench["equal-weight GRATUITO (giro 50)"] = B.eval_stream(
        "gratuito", net0.dropna(), rf, t0)
    bench["equal-weight GRATUITO (giro 50)"]["rot"] = 0.0

    print(f"   {'benchmark':<36}{'rotaz.':>9}{'CAGR':>9}{'IRR 33%':>10}"
          f"{'IRR 52%':>10}{'IRR rif.':>10}")
    print("   " + "-" * 84)
    for nm, r in bench.items():
        print(f"   {nm:<36}{r['rot']:>8.3f}x{r['cagr']:>8.2f}%{r['irr']:>9.2f}%"
              f"{r['irr52']:>9.2f}%{r['irr_ref']:>9.2f}%")

    # ------------------------------------------------------------ la griglia
    celle = []
    for top in (1, 3, 5, 10, 25):
        for fname, step in FREQS.items():
            W = rotate(ind, top, step)
            net, turn = con_rotazione_vera(ind, W)
            net = net.dropna()
            r = B.eval_stream(f"top-{top} {fname}", net, rf, turn)
            r.update(top=top, freq=fname, rot=float(turn.sum()) / anni, net=net)
            celle.append(r)

    print(f"\n   IRR netta di riferimento (33% o 52% secondo la rotazione):\n")
    print(f"   {'posizioni':<12}" + "".join(f"{f:>16}" for f in FREQS))
    print("   " + "-" * 60)
    for top in (1, 3, 5, 10, 25):
        line = f"   {top:<12}"
        for fname in FREQS:
            c = next(x for x in celle if x["top"] == top and x["freq"] == fname)
            star = "*" if c["rate_ref"] == 52 else " "
            line += f"{c['irr_ref']:>14.2f}%{star}"
        print(line)
    print(f"   * oltre il 100% di rotazione l'anno -> valutata al 52%")

    print(f"\n   Rotazione vera di ogni cella (x/anno):\n")
    print(f"   {'posizioni':<12}" + "".join(f"{f:>16}" for f in FREQS))
    print("   " + "-" * 60)
    for top in (1, 3, 5, 10, 25):
        line = f"   {top:<12}"
        for fname in FREQS:
            c = next(x for x in celle if x["top"] == top and x["freq"] == fname)
            line += f"{c['rot']:>15.3f}x"
        print(line)

    # ------------------------------------------------------------ il confronto
    best = max(celle, key=lambda c: c["irr_ref"])
    t5a = next(c for c in celle if c["top"] == 5 and c["freq"] == "annuale")
    ewa = bench["equal-weight annuale"]
    ewm_r = bench["equal-weight mensile"]
    ewg = bench["equal-weight GRATUITO (giro 50)"]

    print(f"\n   Massimo della griglia: top-{best['top']} {best['freq']}, "
          f"{best['irr_ref']:.2f}% (rotazione {best['rot']:.3f}x)")
    print(f"\n   {'confronto':<44}{'divario':>10}")
    print("   " + "-" * 54)
    for nm, b in [("top-5 annuale vs EW annuale (vera)", ewa),
                  ("top-5 annuale vs EW mensile (vera)", ewm_r),
                  ("top-5 annuale vs EW GRATUITO (come F2)", ewg)]:
        print(f"   {nm:<44}{t5a['irr_ref'] - b['irr_ref']:>+9.2f}")
    print(f"   {'massimo della griglia vs EW annuale (vera)':<44}"
          f"{best['irr_ref'] - ewa['irr_ref']:>+9.2f}")
    print(f"\n   Per riferimento, F2 al giro 50 registrava: top-5 annuale "
          f"10,02% contro 11,16% = -1,14")

    # ------------------------------------------------------------------ DSR
    srs = []
    for c in celle:
        s = c["net"] - rf.reindex(c["net"].index).fillna(0.0)
        srs.append(float(s.mean() / s.std(ddof=1)))
    var_sr = float(np.var(srs, ddof=1))
    n_cum = lab.n_trials_so_far()
    print(f"\n   DSR del top-5 annuale — c'e' selezione, quindi N e' la griglia:")
    print(f"     dispersione degli Sharpe dentro la griglia: var_sr = "
          f"{var_sr:.6f}")
    dsr15 = lab.deflated_sharpe(t5a["net"], N_GRID, var_sr=var_sr, rf=rf)
    dsrc = lab.deflated_sharpe(t5a["net"], n_cum, var_sr=var_sr, rf=rf)
    dsrb = lab.deflated_sharpe(best["net"], N_GRID, var_sr=var_sr, rf=rf)
    print(f"     {'':<28}{'SR periodo':>12}{'SR0':>10}{'DSR':>9}")
    print(f"     {'top-5 annuale, N=15':<28}{dsr15['sr_period']:>12.4f}"
          f"{dsr15['sr0']:>10.4f}{dsr15['dsr']:>9.4f}")
    print(f"     {f'top-5 annuale, N={n_cum}':<28}{dsrc['sr_period']:>12.4f}"
          f"{dsrc['sr0']:>10.4f}{dsrc['dsr']:>9.4f}")
    print(f"     {'massimo griglia, N=15':<28}{dsrb['sr_period']:>12.4f}"
          f"{dsrb['sr0']:>10.4f}{dsrb['dsr']:>9.4f}")

    # ------------------------------------------------------------- verdetto
    gap = t5a["irr_ref"] - ewa["irr_ref"]
    print(f"\n{'=' * 100}\n   VERDETTO\n{'=' * 100}")
    print(f"   Predizione: il top-5 annuale supera l'equal-weight annuale "
          f"correttamente addebitato")
    print(f"   di 0,5-2 punti, ma il DSR resta sotto 0,95.")
    print(f"   FALSIFICATA se il top-5 annuale resta SOTTO l'equal-weight "
          f"annuale, OPPURE il DSR supera 0,95.\n")
    print(f"   divario top-5 annuale vs EW annuale : {gap:+.2f} punti"
          f"   (previsto +0,5/+2)")
    print(f"   DSR su N=15                         : {dsr15['dsr']:.4f}")
    print(f"   DSR su N={n_cum}                      : {dsrc['dsr']:.4f}")
    fals = (gap <= 0) or (dsr15["dsr"] > 0.95) or (dsrc["dsr"] > 0.95)
    print(f"\n   -> ipotesi D7 {'FALSIFICATA' if fals else 'CONFERMATA'}")
    print(f"      clausola 'divario fra +0,5 e +2': "
          f"{'centrata' if 0.5 <= gap <= 2.0 else 'SBAGLIATA'}")
    print(f"      clausola 'DSR sotto 0,95': "
          f"{'centrata' if dsr15['dsr'] <= 0.95 and dsrc['dsr'] <= 0.95 else 'SBAGLIATA'}")
    print(f"\n   Promozioni: "
          f"{'UNA — da portare all holdout' if dsrc['dsr'] > 0.95 else 'ZERO'}. "
          f"Holdout ancora sigillato.")

    df = pd.DataFrame([{k: v for k, v in c.items() if k not in ("net", "gross")}
                       for c in celle])
    df.to_csv(OUT / "round64_d7.csv", index=False)
    lab.log_trials([dict(round=ROUND, hypothesis="D7 F2 con rotazione vera",
                         config=f"top-{c['top']} {c['freq']}", window=f"{y0}-{y1}",
                         sharpe=c["sharpe"], irr=c["irr_ref"],
                         bh_irr=ewa["irr_ref"], excess=c["irr_ref"] - ewa["irr_ref"],
                         n_obs=c["n"], note=f"rot={c['rot']:.3f}")
                    for c in celle])
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

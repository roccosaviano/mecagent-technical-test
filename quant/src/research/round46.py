"""Giro 46 — A12: il multi-classe su finestre mobili di 20 anni.

VOCE DELLA CODA, predizione e falsificazione scritte prima:

  I giri 44 e 45 concludono che il multi-classe perde 2,4-3,9 punti contro
  l'azionario puro, ma su UNA SOLA finestra: 1962-2026. Da misurare su finestre
  mobili di 20 anni, passo 1 anno, con la ricostruzione migliorata del giro 45.
  PREDIZIONE: il multi-classe vince in una minoranza di finestre — fra il 15% e
  il 35% — e sono tutte e sole quelle centrate sui due mercati orso lunghi
  (1969-1982 e 2000-2012). L'ampiezza fra la finestra migliore e la peggiore
  supera 6 punti, cioe' e' piu' grande del divario medio.
  FALSIFICATA SE: il multi-classe vince in piu' della meta' delle finestre,
  oppure in nessuna.

COSA VUOL DIRE "FINESTRA" QUI. Non un ritaglio di una serie lunga: ogni finestra
e' un PAC completo e indipendente. Un investitore che comincia a versare 500 euro
al mese nel gennaio dell'anno Y e smette venti anni dopo. I pesi si ristimano
dentro la finestra, quindi i primi 36 mesi girano a pesi uguali per mancanza di
storia — esattamente come capiterebbe a quell'investitore, che non ha una
covarianza stimata il giorno in cui apre il conto.

E' il motivo per cui questa voce esiste: il divario medio su 64 anni e' una
statistica sulla storia, la distribuzione su finestre di 20 anni e' una
statistica su cio' che sarebbe capitato a una persona.

SULLA SOVRAPPOSIZIONE. Finestre di 20 anni a passo 1 condividono fino a 19 anni,
quindi le 44 osservazioni NON sono indipendenti: il numero effettivo e' piu'
vicino a 64/20 = 3. Non calcolo p-value su questa distribuzione e non lo farei —
D1 e' stata falsificata proprio per non aver visto un problema di questo tipo.
Qui la sovrapposizione e' dichiarata e la frazione di vittorie e' descrittiva.
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
from tax import simulate_pac, CGT_SHARES, TRADING_52
from research import lab, multidata as M
from research.round44 import weights_path
from research.round45 import bond_improved

ROUND = 46
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 60
WIN_Y = 20
METHODS = ("erc", "invvol", "6040", "equal")

# i due mercati orso lunghi nominati nella predizione
BEARS = ((1969, 1982), (2000, 2012))


def pac_irr(ret, rf, realize=None, regime=CGT_SHARES):
    r = simulate_pac(ret, regime, rf=rf.reindex(ret.index).fillna(0.0),
                     realize_frac=(realize.reindex(ret.index).clip(0, 1)
                                   if realize is not None else None),
                     periods_per_year=12)
    return r.irr_annual


def window_result(df, rf, method):
    """Una finestra = un PAC completo. Pesi stimati DENTRO la finestra."""
    W, turn = weights_path(df, method)
    gross = (W.shift(1).fillna(0.0) * df).sum(axis=1) - turn * C.COST_ROUND_TRIP
    g = gross.dropna()
    if len(g) < WIN_Y * 12 - 6:
        return None
    alloc = pac_irr(g, rf, turn.reindex(g.index))
    eqty = pac_irr(df["azionario"].reindex(g.index), rf)
    tpy = float(turn.sum()) / (len(g) / 12)
    return dict(alloc=alloc, eq=eqty, diff=alloc - eqty, turn=tpy,
                alloc52=pac_irr(g, rf, turn.reindex(g.index), TRADING_52))


def centred_on_bear(y0, y1):
    """La finestra e' 'centrata' su un mercato orso se il suo punto medio cade
    dentro uno dei due periodi nominati nella predizione."""
    mid = (y0 + y1) / 2
    return any(a <= mid <= b for a, b in BEARS)


def main():
    ffm = dataio.ff_factors_monthly()
    rf = ffm["RF"]
    eq = (ffm["Mkt-RF"] + ffm["RF"]).rename("azionario")
    bond = bond_improved().rename("decennale")
    full = pd.DataFrame({"azionario": eq, "decennale": bond}).dropna()

    y0, y1 = full.index[0].year, full.index[-1].year
    starts = [y for y in range(y0, y1 - WIN_Y + 2)]
    print("A12 — il multi-classe su finestre mobili di 20 anni")
    print(f"Dati {full.index[0].date()} -> {full.index[-1].date()}, "
          f"decennale con la ricostruzione MIGLIORATA del giro 45")
    print(f"{len(starts)} finestre di {WIN_Y} anni, passo 1 anno "
          f"({starts[0]}-{starts[0]+WIN_Y-1} ... {starts[-1]}-{starts[-1]+WIN_Y-1})")
    print("Ogni finestra e' un PAC completo e indipendente: chi comincia a")
    print("versare nell'anno Y e smette venti anni dopo. Pesi stimati DENTRO la")
    print("finestra, quindi i primi 36 mesi girano a pesi uguali.\n")

    res = {m: {} for m in METHODS}
    for s in starts:
        sub = full[(full.index.year >= s) & (full.index.year < s + WIN_Y)]
        if len(sub) < WIN_Y * 12 - 6:
            continue
        rfw = rf.reindex(sub.index).fillna(0.0)
        for m in METHODS:
            r = window_result(sub, rfw, m)
            if r:
                res[m][s] = r

    # -------------------------------------------------- tabella riassuntiva
    print(f"{'='*92}")
    print(f"{'allocazione':<14}{'finestre':>10}{'vinte':>10}{'quota':>9}"
          f"{'divario medio':>15}{'peggiore':>11}{'migliore':>11}{'ampiezza':>11}")
    print("   " + "-" * 88)
    rows = []
    for m in METHODS:
        d = np.array([v["diff"] for v in res[m].values()])
        wins = int((d > 0).sum())
        rows.append(dict(method=m, n=len(d), wins=wins,
                         share=wins / len(d) * 100, mean=d.mean(),
                         worst=d.min(), best=d.max(), span=d.max() - d.min()))
        print(f"{m:<14}{len(d):>10}{wins:>10}{wins/len(d)*100:>8.1f}%"
              f"{d.mean():>14.2f}%{d.min():>10.2f}%{d.max():>10.2f}%"
              f"{d.max()-d.min():>10.2f}%")

    # -------------------------------------------------- quali finestre vince
    print(f"\n{'='*92}\nLE FINESTRE IN CUI IL MULTI-CLASSE VINCE\n{'='*92}")
    for m in METHODS:
        won = sorted(s for s, v in res[m].items() if v["diff"] > 0)
        if not won:
            print(f"   {m:<10} nessuna")
            continue
        inb = [s for s in won if centred_on_bear(s, s + WIN_Y - 1)]
        print(f"   {m:<10} {len(won)} finestre, inizio: "
              f"{', '.join(str(s) for s in won)}")
        print(f"   {'':<10} centrate su un mercato orso lungo: "
              f"{len(inb)}/{len(won)}")

    # -------------------------------------------------- profilo temporale
    print(f"\n{'='*92}\nIL DIVARIO ANNO PER ANNO (ERC contro azionario)\n{'='*92}")
    e = res["erc"]
    print(f"   {'inizio':>8}{'fine':>7}{'alloc':>9}{'azion.':>9}"
          f"{'divario':>10}   {'':<20}")
    for s in sorted(e):
        v = e[s]
        bar = ("+" if v["diff"] > 0 else "-") * min(int(abs(v["diff"]) * 3), 26)
        mark = " <- orso" if centred_on_bear(s, s + WIN_Y - 1) else ""
        print(f"   {s:>8}{s+WIN_Y-1:>7}{v['alloc']:>8.2f}%{v['eq']:>8.2f}%"
              f"{v['diff']:>9.2f}%   {bar}{mark}")

    # -------------------------------------------------- verdetto
    print(f"\n{'='*92}\nVERDETTO SU A12\n{'='*92}")
    print("   Predizione: vince fra il 15% e il 35% delle finestre, tutte e sole")
    print("   quelle centrate sui due mercati orso lunghi; ampiezza oltre 6 punti.")
    print("   FALSIFICATA se vince in piu' della meta' delle finestre, o in nessuna.\n")
    for r in rows:
        v = "PIU' della meta'" if r["share"] > 50 else (
            "NESSUNA" if r["wins"] == 0 else "minoranza")
        print(f"   {r['method']:<10} quota di vittorie {r['share']:>5.1f}%  -> {v}")
    shares = [r["share"] for r in rows]
    fals = any(s > 50 for s in shares) or any(s == 0 for s in shares)
    print(f"\n   -> ipotesi A12 {'FALSIFICATA' if fals else 'CONFERMATA'}")

    # le clausole descrittive, verificate una per una
    print(f"\n   Le tre clausole della predizione, separatamente:")
    inband = all(15 <= s <= 35 for s in shares)
    print(f"   (a) quota fra il 15% e il 35%: {'SI' if inband else 'NO'} "
          f"(osservato {min(shares):.1f}% - {max(shares):.1f}%)")
    allbear = True
    for m in METHODS:
        won = [s for s, v in res[m].items() if v["diff"] > 0]
        if won and not all(centred_on_bear(s, s + WIN_Y - 1) for s in won):
            allbear = False
    print(f"   (b) tutte e sole centrate sui mercati orso: "
          f"{'SI' if allbear else 'NO'}")
    spans = [r["span"] for r in rows]
    print(f"   (c) ampiezza oltre 6 punti: "
          f"{'SI' if min(spans) > 6 else 'NO'} (osservato "
          f"{min(spans):.2f} - {max(spans):.2f} punti)")
    means = [abs(r["mean"]) for r in rows]
    verso = "PIU' GRANDE" if min(spans) > max(means) else "piu' piccola"
    print(f"       ampiezza contro divario medio: {min(spans):.2f} contro "
          f"{max(means):.2f} -> l'ampiezza e' {verso}")

    print(f"\n   NOTA. Le finestre si sovrappongono fino a 19 anni su 20: le "
          f"{len(starts)} osservazioni")
    print(f"   non sono indipendenti, il numero effettivo e' vicino a 3. La quota")
    print(f"   di vittorie e' descrittiva, non un test. Nessun candidato esce da")
    print(f"   qui: scegliere la finestra migliore fra {len(starts)} sovrapposte e'")
    print(f"   esattamente il tipo di selezione che il DSR esiste per punire.")

    lab.log_trials([dict(round=ROUND, hypothesis="A12 finestre mobili di 20 anni",
                         config=r["method"], window=f"{starts[0]}-{starts[-1]}",
                         sharpe="", irr="", bh_irr="", excess=r["mean"],
                         n_obs=r["n"],
                         note=f"vinte={r['wins']}/{r['n']},span={r['span']:.2f}")
                    for r in rows])
    pd.DataFrame([dict(method=m, start=s, **v)
                  for m in METHODS for s, v in res[m].items()]
                 ).to_csv(OUT / "round46_a12.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

"""Giro 47 — A13: il rischio di sequenza, misurato invece che dedotto.

VOCE DELLA CODA, predizione e falsificazione scritte prima:

  Il giro 46 ha trovato che le finestre in cui il multi-classe batte l'azionario
  sono tutte e sole quelle che finiscono fra il 2002 e il 2016. Il meccanismo
  proposto e' il rischio di sequenza. Da misurare direttamente: (i) regressione
  del divario di ogni finestra sul rendimento azionario degli ULTIMI 3 anni
  contro quello dei PRIMI 3; (ii) la stessa cosa con la ricostruzione
  obbligazionaria SEMPLICE, che copre 1962-2026 e recupera le 12 finestre perse.
  PREDIZIONE: il coefficiente sugli ultimi 3 anni e' negativo, di modulo almeno
  4 volte quello sui primi 3, e da solo spiega oltre meta' della varianza del
  divario. Sulla finestra estesa la quota di vittorie sale sopra il 50%.
  FALSIFICATA SE: i due coefficienti hanno modulo comparabile (rapporto sotto 2),
  o se il segno di quello sugli ultimi 3 anni e' positivo.

PERCHE' NON CALCOLO p-VALUE. Le finestre di 20 anni a passo 1 condividono fino a
19 anni: le osservazioni non sono indipendenti e il numero effettivo e' vicino a
64/20 = 3. Una regressione su dati cosi' sovrapposti ha coefficienti leggibili e
errori standard privi di significato. Riporto quindi coefficienti, rapporto e R2
come DESCRIZIONE della forma dei dati, e nessun test di significativita'. E' la
stessa disciplina del giro 46, e nasce dalla falsificazione di D1: una condizione
che si verifica da sola su campioni sovrapposti non e' un test.

UNA VERIFICA DIRETTA IN PIU'. La regressione mostra un'associazione. Il
meccanismo proposto — il capitale e' massimo alla fine, quindi gli ultimi anni
pesano di piu' — e' verificabile da solo, senza regressione: basta misurare
quanta parte del montante finale e' esposta al mercato in ciascun anno del piano.
Se il meccanismo e' quello, il peso dell'ultimo triennio deve essere di gran lunga
il piu' grande. La calcolo e la riporto accanto.
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
from research import lab
from research.round44 import weights_path
from research.round45 import bond_simple, bond_improved

ROUND = 47
OUT = Path(__file__).resolve().parents[2] / "out"
N_PREREG = 61
WIN_Y = 20
EDGE_Y = 3
METHODS = ("erc", "invvol", "6040", "equal")


def pac_irr(ret, rf, realize=None, regime=CGT_SHARES):
    r = simulate_pac(ret, regime, rf=rf.reindex(ret.index).fillna(0.0),
                     realize_frac=(realize.reindex(ret.index).clip(0, 1)
                                   if realize is not None else None),
                     periods_per_year=12)
    return r.irr_annual


def rolling_windows(full, rf, methods=METHODS):
    y0, y1 = full.index[0].year, full.index[-1].year
    out = []
    for s in range(y0, y1 - WIN_Y + 2):
        sub = full[(full.index.year >= s) & (full.index.year < s + WIN_Y)]
        if len(sub) < WIN_Y * 12 - 6:
            continue
        rfw = rf.reindex(sub.index).fillna(0.0)
        e = sub["azionario"]
        first = float((1 + e.iloc[:EDGE_Y * 12]).prod() ** (1 / EDGE_Y) - 1)
        last = float((1 + e.iloc[-EDGE_Y * 12:]).prod() ** (1 / EDGE_Y) - 1)
        eq_irr = pac_irr(e, rfw)
        row = dict(start=s, end=s + WIN_Y - 1, first3=first * 100,
                   last3=last * 100, eq=eq_irr)
        for m in methods:
            W, turn = weights_path(sub, m)
            g = ((W.shift(1).fillna(0.0) * sub).sum(axis=1)
                 - turn * C.COST_ROUND_TRIP).dropna()
            row[f"{m}_irr"] = pac_irr(g, rfw, turn.reindex(g.index))
            row[f"{m}_diff"] = row[f"{m}_irr"] - eq_irr
            row[f"{m}_turn"] = float(turn.sum()) / (len(g) / 12)
            row[f"{m}_irr52"] = pac_irr(g, rfw, turn.reindex(g.index), TRADING_52)
        out.append(row)
    return pd.DataFrame(out)


def ols(y, X):
    """Minimi quadrati con intercetta. Nessun errore standard: su finestre
    sovrapposte non significherebbe niente."""
    A = np.column_stack([np.ones(len(X))] + [X[:, j] for j in range(X.shape[1])])
    beta, *_ = np.linalg.lstsq(A, y, rcond=None)
    fit = A @ beta
    ss_res = float(((y - fit) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    return beta, (1 - ss_res / ss_tot if ss_tot > 0 else float("nan"))


def analyse(df, label):
    print(f"\n{'='*92}\n{label}\n{'='*92}")
    print(f"   {len(df)} finestre, da {df['start'].min()}-{df['end'].min()} "
          f"a {df['start'].max()}-{df['end'].max()}")
    print(f"\n   {'alloc':<10}{'vinte':>9}{'quota':>9}{'b(ultimi 3)':>14}"
          f"{'b(primi 3)':>13}{'rapporto':>11}{'R2 solo ultimi':>16}"
          f"{'R2 entrambi':>13}")
    print("   " + "-" * 92)
    rows = []
    for m in METHODS:
        y = df[f"{m}_diff"].to_numpy()
        Xb = df[["last3", "first3"]].to_numpy()
        beta, r2b = ols(y, Xb)
        b_last, b_first = beta[1], beta[2]
        _, r2_last = ols(y, df[["last3"]].to_numpy())
        _, r2_first = ols(y, df[["first3"]].to_numpy())
        ratio = abs(b_last) / abs(b_first) if b_first != 0 else float("inf")
        wins = int((y > 0).sum())
        rows.append(dict(label=label, method=m, n=len(df), wins=wins,
                         share=wins / len(df) * 100, b_last=b_last,
                         b_first=b_first, ratio=ratio, r2_last=r2_last,
                         r2_first=r2_first, r2_both=r2b, mean=float(y.mean())))
        print(f"   {m:<10}{wins:>6}/{len(df):<3}{wins/len(df)*100:>8.1f}%"
              f"{b_last:>14.3f}{b_first:>13.3f}{ratio:>11.2f}"
              f"{r2_last:>15.3f}{r2b:>13.3f}")
    print(f"\n   (b = variazione del divario, in punti di IRR, per ogni punto di")
    print(f"    rendimento azionario annuo in piu' nel triennio indicato)")
    return rows


def capital_weight_profile():
    """Quanta parte del montante finale e' esposta al mercato in ciascun anno.

    Verifica diretta del meccanismo, indipendente dalla regressione: con
    versamenti costanti, il capitale investito nell'anno k e' la somma dei
    versamenti fino a k. La quota di 'anni-capitale' spesi in ciascun anno e'
    il peso con cui il rendimento di quell'anno entra nel risultato.
    """
    yrs = np.arange(1, WIN_Y + 1)
    cap = yrs                      # capitale versato a inizio anno k, in mesi/12
    w = cap / cap.sum()
    return w


def main():
    ffm = dataio.ff_factors_monthly()
    rf = ffm["RF"]
    eq = (ffm["Mkt-RF"] + ffm["RF"]).rename("azionario")
    simple, _ = bond_simple()
    improved = bond_improved()

    print("A13 — il rischio di sequenza, misurato invece che dedotto")
    print(f"Finestre di {WIN_Y} anni, passo 1. Trienni di bordo: primi e ultimi "
          f"{EDGE_Y} anni.")

    # ---------------------------------------------- verifica del meccanismo
    w = capital_weight_profile()
    print(f"\n{'='*92}\nIL MECCANISMO, verificato senza regressione\n{'='*92}")
    print(f"   Con versamenti costanti per {WIN_Y} anni, la quota di capitale-anni")
    print(f"   esposta al mercato in ciascun anno del piano:")
    print(f"     primi {EDGE_Y} anni:  {w[:EDGE_Y].sum():>6.1%}")
    print(f"     ultimi {EDGE_Y} anni: {w[-EDGE_Y:].sum():>6.1%}")
    print(f"     rapporto ultimi/primi: {w[-EDGE_Y:].sum()/w[:EDGE_Y].sum():.2f}x")
    print(f"   E' il meccanismo proposto, e non dipende da nessun dato di mercato:")
    print(f"   e' aritmetica del piano di accumulo.")

    allrows = []
    # ---------------------------------------------- (ii) finestra estesa
    full_s = pd.DataFrame({"azionario": eq, "decennale": simple}).dropna()
    df_s = rolling_windows(full_s, rf)
    allrows += analyse(df_s, "RICOSTRUZIONE SEMPLICE — finestra estesa "
                             f"{full_s.index[0].year}-{full_s.index[-1].year}")

    # ---------------------------------------------- (i) confronto col giro 46
    full_i = pd.DataFrame({"azionario": eq, "decennale": improved}).dropna()
    df_i = rolling_windows(full_i, rf)
    allrows += analyse(df_i, "RICOSTRUZIONE MIGLIORATA — la finestra del giro 46 "
                             f"{full_i.index[0].year}-{full_i.index[-1].year}")

    # ---------------------------------------------- le finestre recuperate
    rec = df_s[~df_s["start"].isin(df_i["start"])]
    print(f"\n{'='*92}\nLE {len(rec)} FINESTRE RECUPERATE DALLA FINESTRA ESTESA\n{'='*92}")
    print(f"   {'inizio':>8}{'fine':>7}{'ERC':>9}{'azion.':>9}{'divario':>10}"
          f"{'ult.3 anni':>12}")
    for _, r in rec.iterrows():
        print(f"   {int(r['start']):>8}{int(r['end']):>7}{r['erc_irr']:>8.2f}%"
              f"{r['eq']:>8.2f}%{r['erc_diff']:>9.2f}%{r['last3']:>11.2f}%")
    if len(rec):
        print(f"\n   Vinte dal multi-classe: "
              f"{int((rec['erc_diff'] > 0).sum())}/{len(rec)}")

    # ---------------------------------------------- verdetto
    print(f"\n{'='*92}\nVERDETTO SU A13\n{'='*92}")
    print("   Predizione: b(ultimi 3) negativo, modulo almeno 4 volte b(primi 3),")
    print("   e da solo spiega oltre meta' della varianza. Sulla finestra estesa la")
    print("   quota di vittorie sale sopra il 50%.")
    print("   FALSIFICATA se il rapporto e' sotto 2, o se b(ultimi 3) e' positivo.\n")
    ext = [r for r in allrows if r["label"].startswith("RICOSTRUZIONE SEMPLICE")]
    for r in allrows:
        tag = "estesa" if r["label"].startswith("RICOSTRUZIONE SEMPLICE") else "giro 46"
        print(f"   {tag:<9}{r['method']:<10} b(ult)={r['b_last']:>7.3f} "
              f"{'(negativo)' if r['b_last'] < 0 else '(POSITIVO)'}  "
              f"rapporto {r['ratio']:>5.2f} "
              f"{'(>=2)' if r['ratio'] >= 2 else '(SOTTO 2)'}")
    fals = any(r["b_last"] > 0 or r["ratio"] < 2 for r in allrows)
    print(f"\n   -> ipotesi A13 {'FALSIFICATA' if fals else 'CONFERMATA'}")

    print(f"\n   Le clausole descrittive, separatamente:")
    r4 = all(r["ratio"] >= 4 for r in allrows)
    print(f"   (a) rapporto almeno 4: {'SI' if r4 else 'NO'} (osservato "
          f"{min(r['ratio'] for r in allrows):.2f} - "
          f"{max(r['ratio'] for r in allrows):.2f})")
    r2ok = all(r["r2_last"] > 0.5 for r in allrows)
    print(f"   (b) R2 dei soli ultimi 3 anni oltre 0,5: {'SI' if r2ok else 'NO'} "
          f"(osservato {min(r['r2_last'] for r in allrows):.3f} - "
          f"{max(r['r2_last'] for r in allrows):.3f})")
    sh = [r["share"] for r in ext]
    print(f"   (c) quota di vittorie sopra il 50% sulla finestra estesa: "
          f"{'SI' if all(s > 50 for s in sh) else 'NO'} "
          f"(osservato {min(sh):.1f}% - {max(sh):.1f}%)")

    print(f"\n   NOTA. Le finestre si sovrappongono fino a 19 anni su 20: nessun")
    print(f"   p-value, nessun errore standard. I coefficienti descrivono la forma")
    print(f"   dei dati, non provano una relazione. Nessun candidato esce da qui.")

    lab.log_trials([dict(round=ROUND, hypothesis="A13 rischio di sequenza",
                         config=f"{r['label'][:22]}|{r['method']}",
                         window="finestre di 20 anni", sharpe="", irr="",
                         bh_irr="", excess=r["mean"], n_obs=r["n"],
                         note=f"b_last={r['b_last']:.3f},ratio={r['ratio']:.2f},"
                              f"r2={r['r2_last']:.3f}") for r in allrows])
    pd.DataFrame(allrows).to_csv(OUT / "round47_a13.csv", index=False)
    df_s.to_csv(OUT / "round47_finestre_estese.csv", index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")


if __name__ == "__main__":
    main()

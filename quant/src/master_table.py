"""Tabella unica di tutti i metodi provati, con le metriche omogenee.

Le righe vengono da mercati, frequenze e finestre diversi. Metterle in una sola
tabella senza dirlo sarebbe fuorviante, quindi ogni riga porta il proprio
mercato, la propria finestra e il buy&hold DELLO STESSO mercato e periodo. La
colonna che conta e' 'vs B&H', non il CAGR assoluto: confrontare il CAGR di una
strategia su QQQ 2006-2026 con uno su CRSP 1947-2009 non significa niente.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "out"
RES = Path(__file__).resolve().parents[1] / "research"
ROWS = []


def add(gruppo, metodo, mercato, finestra, cagr=None, irr=None, vs=None,
        sharpe=None, dd=None, ops=None, dsr=None, esito="", nota=""):
    ROWS.append(dict(gruppo=gruppo, metodo=metodo, mercato=mercato,
                     finestra=finestra, cagr=cagr, irr=irr, vs=vs,
                     sharpe=sharpe, dd=dd, ops=ops, dsr=dsr, esito=esito,
                     nota=nota))


def f(x, suf="%", dec=2):
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) \
        else f"{x:.{dec}f}{suf}"


def main():
    # ---------------------------------------------------- studio principale
    try:
        st = json.load(open(OUT / "summary_table.json"))
        for r in st:
            g = {"C": "Benchmark passivi", "A": "Swing trading giornaliero",
                 "D": "Diversity-weighted (SPT)"}.get(r["group"], r["group"])
            add(g, r["name"], "S&P/CRSP", r["window"], cagr=r["cagr"],
                irr=r["irr"], vs=r["vs"], sharpe=r["sharpe"], dd=r["dd"],
                ops=r["trades"], nota="PAC 500/mese netto imposte IE")
    except FileNotFoundError:
        pass

    # ---------------------------------------------------- giri di ricerca
    wf = [
        ("H2 trend following multi-asset", "AQR Century", "1960-2009", 8.45, -0.40, 0.27, -68.1, 0.351, "respinta"),
        ("H4 tilt difensivo low-vol", "49 settori", "1947-2009", 10.42, +0.73, 0.58, -46.2, 0.989, "candidato"),
        ("H5 momentum settoriale", "49 settori", "1947-2009", 12.64, +2.95, 0.67, -60.8, 0.998, "candidato"),
        ("H6 stop loss / take profit mensili", "CRSP", "1960-2009", 8.31, -0.55, 0.29, -50.3, 0.442, "respinta"),
        ("H7 leva con margin call ESMA", "CRSP", "1960-2009", 4.68, -4.18, 0.14, -95.1, 0.141, "respinta"),
        ("H8 diversificazione geografica", "Dev/EM/JP/EU", "1996-2009", 2.14, -0.16, 0.25, -56.6, 0.163, "respinta"),
        ("H9 combinazione inverse-vol", "multi-asset", "1995-2009", -3.97, -6.85, -2.48, -39.2, 0.000, "respinta"),
        ("H11a composito momentum+low-vol", "49 settori", "1947-2009", 12.77, +3.08, 0.67, -60.2, 0.997, "candidato"),
        ("H11b Gross Profitability long-only", "OSAP quintili", "1985-2009", 8.94, +2.40, 0.59, -40.6, 0.788, "respinta"),
        ("H11c media dei due compositi", "misto", "1985-2009", 9.84, +3.30, 0.68, -47.3, 0.990, "candidato"),
        ("H12 momentum con isteresi", "49 settori", "1947-2009", 11.07, +1.38, 0.55, -53.1, 0.996, "candidato"),
    ]
    for m, mk, w, irr, vs, sh, dd, dsr, es in wf:
        add("Ricerca iterativa (walk-forward)", m, mk, w, irr=irr, vs=vs,
            sharpe=sh, dd=dd, dsr=dsr, esito=es, nota="IRR netta PAC")

    # ---------------------------------------------------- NASDAQ
    for m, irr, vs, sh, dd, ops in [
            ("Donchian breakout (parametri da CRSP)", 9.40, -1.03, 0.60, -28.2, 3.8),
            ("Trend + stop sigma (parametri da CRSP)", 8.07, -2.37, 0.51, -49.8, 8.1),
            ("RSI2 (parametri da CRSP)", 2.60, -7.83, -0.82, -19.9, 3.7),
            ("Down-streak (parametri da CRSP)", 1.88, -8.55, -1.41, -9.8, 3.5),
            ("Trend 10 mesi leva 1x", 7.92, -2.54, 0.37, -44.7, None),
            ("Trend 10 mesi leva 2x", 9.63, -0.83, 0.35, -74.5, None)]:
        add("Replica su NASDAQ", m, "NASDAQ Comp.", "1971-2026", irr=irr, vs=vs,
            sharpe=sh, dd=dd, ops=ops, esito="respinta",
            nota="parametri non riottimizzati")

    # ---------------------------------------------------- OHLCV reale
    try:
        d = pd.read_csv(OUT / "round15_ohlcv.csv")
        for _, r in d.iterrows():
            if r["metodo"] == "buy&hold":
                continue
            g = "ATR vero (OHLCV)" if "ATR" in r["gruppo"] else "VWAP intraday (OHLCV)"
            add(g, r["metodo"], r["gruppo"].split()[-1], r["finestra"],
                cagr=r["cagr"], vs=r["vs"], sharpe=r["sharpe"], dd=r["dd"],
                ops=r["trades"], esito="respinta",
                nota="CAGR lordo imposte, dati Twelve Data")
    except FileNotFoundError:
        pass

    # ---------------------------------------------------- non testabili
    for m, why in [
            ("Kronos (foundation model K-line)",
             "pesi scaricabili, ma serve OHLCV su universo ampio: la demo Twelve "
             "Data copre 2 simboli"),
            ("Bet Against Beta implementato davvero",
             "richiede leva e prestito titoli su 23 mercati"),
            ("Diversita' a livello di singolo titolo S&P 500",
             "richiede CRSP/Compustat firm-level"),
            ("SPY/IWM/EFA/EEM/GLD/TLT",
             "Yahoo 429 e Stooq anti-bot per tutta la sessione")]:
        add("Non testabile", m, "—", "—", esito="non eseguito", nota=why)

    # ---------------------------------------------------- stampa
    df = pd.DataFrame(ROWS)
    df.to_csv(OUT / "master_table.csv", index=False)

    print("# Tutti i metodi provati\n")
    print("La colonna che conta e' **vs B&H**: ogni riga e' confrontata col")
    print("buy&hold dello stesso mercato e della stessa finestra. I CAGR assoluti")
    print("di mercati e periodi diversi non sono confrontabili fra loro.\n")
    for g in df["gruppo"].unique():
        sub = df[df["gruppo"] == g].copy()
        if g != "Non testabile":
            sub = sub.sort_values("vs", ascending=False, na_position="last")
        print(f"\n## {g}\n")
        if g == "Non testabile":
            print("| Metodo | Perche' |")
            print("|---|---|")
            for _, r in sub.iterrows():
                print(f"| {r['metodo']} | {r['nota']} |")
            continue
        print("| Metodo | Mercato | Finestra | CAGR | IRR netta | vs B&H | "
              "Sharpe | Max DD | Op/anno | DSR | Esito |")
        print("|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
        for _, r in sub.iterrows():
            print(f"| {r['metodo']} | {r['mercato']} | {r['finestra']} | "
                  f"{f(r['cagr'])} | {f(r['irr'])} | {f(r['vs'])} | "
                  f"{f(r['sharpe'], '', 2)} | {f(r['dd'])} | "
                  f"{f(r['ops'], '', 1)} | {f(r['dsr'], '', 3)} | {r['esito']} |")

    n = len(df[df["gruppo"] != "Non testabile"])
    beat = df[(df["vs"].notna()) & (df["vs"] > 0)]
    print(f"\n---\n\n**{n} metodi valutati.** Battono il buy&hold del proprio "
          f"mercato: **{len(beat)}**.")
    reg = pd.read_csv(RES / "registry.csv") if (RES / "registry.csv").exists() else None
    if reg is not None:
        print(f"Tentativi a registro per il controllo multiple-testing: "
              f"**{len(reg)}**, piu' ~4.000 valutazioni interne al walk-forward.")


if __name__ == "__main__":
    main()

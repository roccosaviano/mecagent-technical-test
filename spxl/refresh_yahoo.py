"""
RIPESCAGGIO PAZIENTE DA YAHOO
=============================

Le serie prese da Nasdaq hanno un difetto preciso: il prezzo non e' corretto per
le distribuzioni. Su SPXL, che oggi distribuisce l'ordine dell'1-2% l'anno, il
rendimento risulta sottostimato di altrettanto, e la calibrazione del costo
della leva ne uscirebbe gonfiata di circa mezzo punto.

Yahoo pubblica l'AdjClose, che il problema non ce l'ha, ma limita per indirizzo
IP e qui l'indirizzo e' condiviso. Quindi: si riprova ogni PAUSA secondi finche'
non passa, si sovrascrive solo cio' che si e' riusciti a scaricare davvero, e si
puo' lasciar girare in sottofondo mentre la ricerca continua sui dati che ci
sono gia'.

    python3 refresh_yahoo.py [ore_massime]
"""
import os
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_data import DATA, p_yahoo   # noqa: E402

PAUSA = 240          # 4 minuti fra un tentativo e l'altro

# (ticker, file, righe minime perche' valga la pena sostituire il file esistente)
BERSAGLI = [
    ("SPXL",     "spxl",    3000),
    ("SPXS",     "spxs",    3000),
    ("SPY",      "spy",     6000),
    ("UPRO",     "upro",    3000),
    ("^SP500TR", "sp500tr", 5000),
    ("^GSPC",    "gspc",   24000),
]


def gia_buono(nome, minimo):
    path = os.path.join(DATA, f"{nome}.csv")
    if not os.path.exists(path):
        return False
    df = pd.read_csv(path)
    if len(df) < minimo:
        return False
    # se AdjClose e Close sono identici ovunque, il file viene da una fonte che
    # non corregge per i dividendi: vale la pena riprovare
    if {"AdjClose", "Close"} <= set(df.columns):
        if (df["AdjClose"] - df["Close"]).abs().max() < 1e-9:
            return False
    return True


def main(ore=6.0):
    scadenza = time.time() + ore * 3600
    restanti = [(t, n, m) for t, n, m in BERSAGLI if not gia_buono(n, m)]
    print(f"da ripescare: {[n for _, n, _ in restanti] or 'niente'}", flush=True)
    giro = 0
    while restanti and time.time() < scadenza:
        giro += 1
        ancora = []
        for tk, nome, minimo in restanti:
            try:
                df = p_yahoo(tk)
                if len(df) < minimo:
                    print(f"  giro {giro}: {nome} solo {len(df)} righe, riprovo", flush=True)
                    ancora.append((tk, nome, minimo))
                    continue
                df.to_csv(os.path.join(DATA, f"{nome}.csv"), index=False)
                print(f"  giro {giro}: {nome} aggiornato, {len(df)} righe "
                      f"{df.Date.iloc[0].date()} -> {df.Date.iloc[-1].date()}", flush=True)
            except Exception as e:
                ancora.append((tk, nome, minimo))
                print(f"  giro {giro}: {nome} ko ({str(e)[:40]})", flush=True)
            time.sleep(PAUSA)
        restanti = ancora
    print(f"\nfine. non ripescati: {[n for _, n, _ in restanti] or 'nessuno'}", flush=True)


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 6.0)

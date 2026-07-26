"""Giro 17 — Kronos: foundation model per K-line, testato davvero.

Modello: NeoQuasar/Kronos-base (102,3M parametri) + Kronos-Tokenizer-base,
architettura di Shiyu et al., "Kronos: A Foundation Model for the Language of
Financial Markets" (arXiv 2508.02739). Pesi scaricati da HuggingFace.

Dati: QQQ giornaliero OHLCV, 5000 barre 2006-2026 (Twelve Data).

Protocollo, senza look-ahead:
  a ogni data di ribilanciamento i, il contesto e' [i-L, i), cioe' si ferma
  alla barra precedente. Il modello prevede [i, i+H). La posizione applicata
  nei giorni [i, i+H) dipende solo da dati fino a i-1.

Segnale: long se il rendimento previsto sull'orizzonte H e' positivo, flat
altrimenti. E' la traduzione piu' diretta possibile di una previsione di
prezzo in una decisione, senza strati interpretativi che potrebbero
mascherare l'assenza di informazione.

Il numero che conta non e' il CAGR ma il TASSO DI CORRETTEZZA DIREZIONALE
rispetto al 50%: se il modello non batte il lancio di una moneta sulla
direzione, il resto e' rumore amplificato dalla leva del backtest.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, "/tmp/claude-0/-home-user-mecagent-technical-test/"
                   "1282c159-1b67-5dda-8a70-400c3f3d0cf1/scratchpad/kronos_pkg")

import config as C
from research import lab
from research.round15 import load, evaluate

ROUND = 17
LOOKBACK = 400          # contesto pieno: ora il carico e libero
HORIZON = 5             # orizzonte di previsione in sedute
STRIDE = 5              # ogni quante sedute si riprevede
N_PRED = 700            # campione piu ampio per il test direzionale


def main():
    from model import Kronos, KronosTokenizer, KronosPredictor

    df = load("QQQ", "1day").reset_index()
    df.columns = [c.lower() for c in df.columns]
    df = df.rename(columns={"index": "datetime"})
    df["amount"] = df["close"] * df["volume"]
    print(f"QQQ {df['datetime'].iloc[0].date()} -> {df['datetime'].iloc[-1].date()}"
          f"  ({len(df)} barre)")

    tok = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    mdl = Kronos.from_pretrained("NeoQuasar/Kronos-base")
    pred = KronosPredictor(mdl, tok, device="cpu", max_context=512)
    print(f"Kronos-base caricato: "
          f"{sum(p.numel() for p in mdl.parameters())/1e6:.1f}M parametri")

    starts = list(range(LOOKBACK, len(df) - HORIZON, STRIDE))
    starts = starts[-N_PRED:]
    print(f"Previsioni da fare: {len(starts)}, contesto {LOOKBACK} barre, "
          f"orizzonte {HORIZON} sedute, passo {STRIDE}")
    print(f"Finestra coperta: {df['datetime'].iloc[starts[0]].date()} -> "
          f"{df['datetime'].iloc[starts[-1]].date()}\n")

    recs = []
    t0 = time.time()
    for k, i in enumerate(starts):
        ctx = df.iloc[i - LOOKBACK:i]
        x = ctx[["open", "high", "low", "close", "volume", "amount"]].reset_index(drop=True)
        xt = ctx["datetime"].reset_index(drop=True)
        yt = df.iloc[i:i + HORIZON]["datetime"].reset_index(drop=True)
        try:
            out = pred.predict(df=x, x_timestamp=xt, y_timestamp=yt,
                               pred_len=HORIZON, T=1.0, top_p=0.9,
                               sample_count=1, verbose=False)
        except Exception as e:
            print(f"  previsione {k} fallita: {type(e).__name__}: {e}")
            continue
        last = float(ctx["close"].iloc[-1])
        pr = float(out["close"].iloc[-1]) / last - 1.0        # previsto su H
        ar = float(df["close"].iloc[i + HORIZON - 1]) / last - 1.0  # realizzato
        recs.append(dict(i=i, date=df["datetime"].iloc[i], pred=pr, actual=ar))
        if (k + 1) % 50 == 0:
            el = time.time() - t0
            print(f"  {k+1}/{len(starts)}  ({el:.0f}s, "
                  f"stimati {el/(k+1)*len(starts):.0f}s totali)")

    r = pd.DataFrame(recs)
    print(f"\nPrevisioni completate: {len(r)} in {time.time()-t0:.0f}s")

    # ---------------------------------------------------- diagnostica
    hit = float((np.sign(r["pred"]) == np.sign(r["actual"])).mean())
    n = len(r)
    se = np.sqrt(0.25 / n)
    z = (hit - 0.5) / se
    ic = float(np.corrcoef(r["pred"], r["actual"])[0, 1])
    from scipy import stats as st
    ric = float(st.spearmanr(r["pred"], r["actual"]).statistic)
    print(f"\n--- Il modello prevede la direzione? ---")
    print(f"  tasso di correttezza direzionale : {hit*100:.2f}%  "
          f"(n={n}, atteso 50%, z={z:+.2f})")
    print(f"  significativo al 5%              : "
          f"{'si' if abs(z) > 1.96 else 'NO'}")
    print(f"  correlazione previsto/realizzato : {ic:+.4f}")
    print(f"  RankIC (Spearman)                : {ric:+.4f}")
    print(f"  quota di previsioni rialziste    : {(r['pred']>0).mean()*100:.1f}%")
    print(f"  quota di realizzati rialzisti    : {(r['actual']>0).mean()*100:.1f}%")

    # ---------------------------------------------------- backtest
    px = load("QQQ", "1day")
    ret = px.close.pct_change().fillna(0.0)
    pos = pd.Series(0.0, index=px.index)
    for _, row in r.iterrows():
        i = int(row["i"])
        pos.iloc[i:i + HORIZON] = 1.0 if row["pred"] > 0 else 0.0
    span = slice(int(r["i"].iloc[0]), int(r["i"].iloc[-1]) + HORIZON)
    rr, pp = ret.iloc[span], pos.iloc[span]
    m = evaluate(rr, pp, 252)
    bh = evaluate(rr, pd.Series(1.0, index=rr.index), 252)
    print(f"\n--- Backtest sul segnale di Kronos ---")
    print(f"  finestra {rr.index[0].date()} -> {rr.index[-1].date()} "
          f"({len(rr)} sedute)")
    print(f"  {'':<22}{'CAGR':>9}{'Sharpe':>9}{'DD':>9}{'op/an':>8}{'%mkt':>7}")
    print(f"  {'Kronos long/flat':<22}{m['cagr']:>8.2f}%{m['sharpe']:>9.2f}"
          f"{m['dd']:>8.1f}%{m['trades']:>8.1f}{m['inmkt']:>6.0f}%")
    print(f"  {'buy&hold':<22}{bh['cagr']:>8.2f}%{bh['sharpe']:>9.2f}"
          f"{bh['dd']:>8.1f}%{0.0:>8.1f}{100.0:>6.0f}%")
    print(f"  {'differenza':<22}{m['cagr']-bh['cagr']:>+8.2f}%"
          f"{m['sharpe']-bh['sharpe']:>+9.2f}")

    lab.log_trials([dict(round=ROUND, hypothesis="H18 Kronos foundation model",
                         config=f"lookback={LOOKBACK},H={HORIZON},stride={STRIDE}",
                         window=f"{rr.index[0].date()}/{rr.index[-1].date()}",
                         sharpe=m["sharpe"], irr=m["cagr"], bh_irr=bh["cagr"],
                         excess=m["cagr"] - bh["cagr"], n_obs=len(rr),
                         note=f"hit={hit:.4f},IC={ic:.4f},RankIC={ric:.4f}")])
    r.to_csv(Path(__file__).resolve().parents[2] / "out" / "round17_kronos.csv",
             index=False)
    print(f"\nTentativi cumulati a registro: {lab.n_trials_so_far()}")
    return r, m, bh, hit, ic, ric


if __name__ == "__main__":
    main()

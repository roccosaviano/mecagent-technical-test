"""Valutazione walk-forward a finestre espandenti.

PERCHE'. Lo split unico TRAIN 1926-1989 / TEST 1990-2009 aveva un
disallineamento di regime: il TRAIN e' dominato da mercati toro lunghi e premia
la leva, il TEST contiene due crolli del 50% e la punisce. Un ottimizzatore
onesto sceglieva leva 2x su TRAIN e produceva -84% su TEST. Il problema era il
disegno, non le strategie.

Qui invece: ogni anno Y si ottimizza su TUTTO cio' che precede Y e si applica la
configurazione scelta durante Y. I rendimenti degli anni Y concatenati formano
una serie interamente out-of-sample, che attraversa tutti i regimi. Nessun
parametro ha mai visto il proprio anno di applicazione.

L'HOLDOUT (2010+) resta fuori: il walk-forward si ferma alla fine del TEST.
"""
import numpy as np
import pandas as pd

from research import lab


def walk_forward(build_fn, grid, index, rf, start_year=1960, end_year=2009,
                 min_train_months=240, score="irr"):
    """build_fn(cfg, window_index) -> (ret, realize) sulla finestra richiesta.

    Restituisce (serie OOS concatenata, scelte per anno, n_valutazioni).
    Ogni ottimizzazione annuale conta come len(grid) valutazioni: e' cio' che
    il DSR deve sapere.
    """
    from tax import simulate_pac, CGT_SHARES

    oos, rz_all, picks, n_eval = [], [], [], 0
    years = [y for y in range(start_year, end_year + 1)]
    for y in years:
        tr_idx = index[index.year < y]
        full_idx = index[index.year <= y]
        if len(tr_idx) < min_train_months or not (full_idx.year == y).any():
            continue
        best, bcfg = None, None
        for cfg in grid:
            r, rz = build_fn(cfg, tr_idx)
            if r is None or len(r) < min_train_months // 2:
                continue
            res = simulate_pac(r, CGT_SHARES, rf=rf.reindex(r.index).fillna(0.0),
                               realize_frac=rz)
            v = res.irr_annual if score == "irr" else lab.summarise(
                r, rf.reindex(r.index).fillna(0.0))["sharpe"]
            n_eval += 1
            if not np.isfinite(v):
                continue
            if best is None or v > best:
                best, bcfg = v, cfg
        if bcfg is None:
            continue
        # La configurazione scelta va fatta girare sull'INTERA storia fino a
        # fine anno Y, e poi si ritaglia il solo anno Y. Applicarla sui 12 mesi
        # isolati non funziona: le strategie hanno bisogno di storia per
        # scaldare gli indicatori, e lo stato (pesi, posizione aperta) deve
        # arrivare da prima. I parametri restano scelti senza vedere l'anno Y.
        r_full, rz_full = build_fn(bcfg, full_idx)
        if r_full is None or len(r_full) == 0:
            continue
        seg = r_full[r_full.index.year == y]
        if len(seg) == 0:
            continue
        oos.append(seg)
        # il realizzo da ribilanciamento va portato avanti insieme ai rendimenti:
        # senza, la strategia verrebbe tassata come un buy&hold e il turnover
        # risulterebbe gratuito, che e' il contrario del vincolo dominante qui
        if rz_full is not None:
            rz_all.append(pd.Series(rz_full).reindex(seg.index).fillna(0.0))
        else:
            rz_all.append(pd.Series(0.0, index=seg.index))
        picks.append((y, bcfg))
    if not oos:
        return pd.Series(dtype=float), pd.Series(dtype=float), picks, n_eval
    return (pd.concat(oos).sort_index(), pd.concat(rz_all).sort_index(),
            picks, n_eval)


def report(name, hyp_id, oos, realize, bench, rf, n_eval, round_id, extra=""):
    """Confronto contro il buy&hold sulla stessa finestra OOS, piu' DSR."""
    from tax import simulate_pac, CGT_SHARES

    idx = oos.index
    b = bench.reindex(idx).dropna()
    idx = idx.intersection(b.index)
    oos, b = oos.reindex(idx), b.reindex(idx)
    rfw = rf.reindex(idx).fillna(0.0)
    rz = (pd.Series(realize).reindex(idx).fillna(0.0)
          if realize is not None and len(realize) else None)

    res = simulate_pac(oos, CGT_SHARES, rf=rfw, realize_frac=rz)
    bh = simulate_pac(b, CGT_SHARES, rf=rfw)
    s, sb = lab.summarise(oos, rfw), lab.summarise(b, rfw)

    trials = [dict(round=round_id, hypothesis=hyp_id, config=f"walkforward:{name}",
                   window="WF-OOS", sharpe=s["sharpe"], irr=res.irr_annual,
                   bh_irr=bh.irr_annual, excess=res.irr_annual - bh.irr_annual,
                   n_obs=len(idx), note=f"n_eval={n_eval}")]
    lab.log_trials(trials)
    n_cum = lab.n_trials_so_far() + n_eval   # le valutazioni interne contano
    d = lab.deflated_sharpe(oos, n_cum, rf=rfw, round_id=round_id)

    if len(idx) == 0:
        print(f"\n{hyp_id} — {name}: nessun dato OOS, non valutabile")
        return None
    print(f"\n{'='*74}\n{hyp_id} — {name}{('  ' + extra) if extra else ''}")
    print(f"  finestra OOS {idx[0].date()} -> {idx[-1].date()} ({len(idx)} mesi), "
          f"{n_eval} valutazioni interne")
    print(f"  {'':<26}{'IRR':>9}{'Sharpe':>9}{'DD':>9}")
    print(f"  {'strategia':<26}{res.irr_annual:>8.2f}%{s['sharpe']:>9.2f}{res.max_dd:>8.1f}%")
    print(f"  {'buy&hold':<26}{bh.irr_annual:>8.2f}%{sb['sharpe']:>9.2f}{bh.max_dd:>8.1f}%")
    print(f"  {'differenza':<26}{res.irr_annual-bh.irr_annual:>+8.2f}%"
          f"{s['sharpe']-sb['sharpe']:>+9.2f}")
    if rz is not None:
        print(f"  turnover medio {rz.mean()*12*100:.0f}%/anno, "
              f"imposte pagate {res.taxes:,.0f} EUR contro {bh.taxes:,.0f} del buy&hold")
    verdict = "PROMUOVIBILE" if (d["dsr"] > 0.95 and res.irr_annual > bh.irr_annual) \
        else "respinta"
    print(f"  DSR {d['dsr']:.3f} (SR0 {d['sr0']*np.sqrt(12):.3f} ann., "
          f"N={n_cum})  ->  {verdict}")
    return dict(name=name, hyp=hyp_id, irr=res.irr_annual, bh=bh.irr_annual,
                excess=res.irr_annual - bh.irr_annual, sharpe=s["sharpe"],
                bh_sharpe=sb["sharpe"], dd=res.max_dd, dsr=d["dsr"],
                n_eval=n_eval, verdict=verdict, ret=oos)

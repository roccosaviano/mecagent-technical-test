"""Giri 03-09: tutte le ipotesi rimanenti, valutate in walk-forward.

H2 trend following multi-asset       H6 stop loss / take profit
H4 tilt difensivo a bassa rotazione  H7 leva con vincoli ESMA e margin call
H5 momentum settoriale cross-section H8 diversificazione geografica
H9 combinazione inverse-vol degli stream non correlati
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config as C
import dataio
from tax import simulate_pac, CGT_SHARES
from research import lab, multidata as M, run_round as R
from research import walkforward as WF

RESULTS = []


def _core():
    ff = dataio.ff_factors_monthly()
    rf = ff["RF"]
    eq = (ff["Mkt-RF"] + ff["RF"]).rename("eq")
    return ff, rf, eq


# ---------------------------------------------------------------- H2
def h2_trend(rf, eq):
    """Trend following multi-asset. Proxy a storia lunga: Century 'All asset
    classes Momentum' (1926+). TSMOM di AQR parte dal 1985 e non consente un
    TRAIN sufficiente, quindi lo uso solo come controprova sul periodo comune."""
    cen = M.century()
    col = next(c for c in cen.columns if c.startswith("All asset classes Momentum"))
    ov = cen[col].dropna()
    DRAG = 0.075 / 12.0        # stesso drag retail del giro 02, dichiarato
    df = pd.DataFrame({"eq": eq, "ov": ov}).dropna()

    def build(cfg, idx):
        w, rb, lv = cfg
        d = df.reindex(idx).dropna()
        if len(d) < 24:
            return None, None
        r, tn = R.blend({"eq": d["eq"], "ov": rf.reindex(d.index).fillna(0) + d["ov"] - DRAG},
                        {"eq": 1 - w, "ov": w}, rb)
        return R.lever(r, rf.reindex(r.index).fillna(0.0), lv), (tn + w).clip(0, 1)

    grid = [(w, rb, lv) for w in (0.0, 0.15, 0.3, 0.45)
            for rb in (12, 60) for lv in (1.0, 1.5)]
    oos, rzs, picks, ne, vsr = WF.walk_forward(build, grid, df.index, rf)
    return WF.report("trend following multi-asset (Century momentum)", "H2",
                     oos, rzs, df["eq"], rf, ne, 3,
                     extra=f"premio lordo {ov.mean()*1200:.2f}%/anno", var_sr=vsr)


# ---------------------------------------------------------------- H4
def h4_defensive(rf, eq):
    """Tilt difensivo long-only a bassissima rotazione: sovrappeso dei settori
    a volatilita' storica piu' bassa. E' il tilt piu' tax-efficient possibile
    perche' i pesi cambiano poco e il ribilanciamento e' annuale o quinquennale."""
    ind = dataio.ff_ind49_monthly()[0]
    ind = ind.dropna(axis=1, how="all")
    # La volatilita' rolling guarda solo indietro: calcolarla una volta sulla
    # serie intera e poi affettarla NON e' look-ahead, ed evita di ricalcolare
    # una rolling su 49 colonne a ogni anno del walk-forward.
    VOL = ind.rolling(60).std()

    def build(cfg, idx):
        n_sel, rb = cfg
        d = ind.reindex(idx).dropna(axis=1)
        if len(d) < 60 or d.shape[1] < n_sel:
            return None, None
        rets, turns, w = [], [], None
        vol = VOL.reindex(d.index)[d.columns]
        for i, t in enumerate(d.index):
            if i < 60:
                rets.append(np.nan); turns.append(0.0); continue
            if w is None or i % rb == 0:
                # volatilita' stimata SOLO sui 60 mesi precedenti
                v = vol.iloc[i - 1].dropna()
                sel = v.nsmallest(n_sel).index
                new = pd.Series(0.0, index=d.columns)
                new[sel] = 1.0 / n_sel
                turns.append(0.5 * float((new - (w if w is not None else 0)).abs().sum())
                             if w is not None else 1.0)
                w = new
            else:
                turns.append(0.0)
            r = d.iloc[i]
            rets.append(float((w * r).sum()) - turns[-1] * C.COST_ROUND_TRIP)
            g = w * (1 + r)
            w = g / g.sum()
        s = pd.Series(rets, index=d.index).dropna()
        return s, pd.Series(turns, index=d.index).reindex(s.index)

    grid = [(n, rb) for n in (10, 15, 20) for rb in (12, 60)]
    oos, rzs, picks, ne, vsr = WF.walk_forward(build, grid, ind.index, rf, start_year=1935)
    return WF.report("tilt difensivo settoriale (low-vol, long-only)", "H4",
                     oos, rzs, eq, rf, ne, 4, var_sr=vsr)


# ---------------------------------------------------------------- H5
def h5_momentum(rf, eq):
    """Momentum cross-sectional settoriale (Moskowitz-Grinblatt 1999):
    compra i settori con miglior rendimento a 12 mesi saltando l'ultimo.
    Long-only, quindi implementabile, ma ad alta rotazione: il test vero e'
    se la fiscalita' irlandese lo uccide."""
    ind = dataio.ff_ind49_monthly()[0].dropna(axis=1, how="all")
    # Momentum a 12 mesi saltando l'ultimo, precalcolato una volta sola.
    # In log-spazio invece di rolling.apply(np.prod): stesso risultato, ~100x.
    _lg = np.log1p(ind)
    MOM = {lk: np.expm1(_lg.rolling(lk).sum()).shift(2) for lk in (12,)}

    def build(cfg, idx):
        n_sel, look, rb = cfg
        d = ind.reindex(idx).dropna(axis=1)
        if len(d) < look + 12 or d.shape[1] < n_sel:
            return None, None
        mom = MOM[look].reindex(d.index)[d.columns]
        rets, turns, w = [], [], None
        for i in range(len(d)):
            if i < look + 2:
                rets.append(np.nan); turns.append(0.0); continue
            if w is None or i % rb == 0:
                m = mom.iloc[i].dropna()
                sel = m.nlargest(n_sel).index
                new = pd.Series(0.0, index=d.columns)
                new[sel] = 1.0 / n_sel
                turns.append(0.5 * float((new - (w if w is not None else 0)).abs().sum())
                             if w is not None else 1.0)
                w = new
            else:
                turns.append(0.0)
            r = d.iloc[i]
            rets.append(float((w * r).sum()) - turns[-1] * C.COST_ROUND_TRIP)
            g = w * (1 + r)
            w = g / g.sum()
        s = pd.Series(rets, index=d.index).dropna()
        return s, pd.Series(turns, index=d.index).reindex(s.index)

    grid = [(n, lk, rb) for n in (5, 10) for lk in (12,) for rb in (1, 3, 12)]
    oos, rzs, picks, ne, vsr = WF.walk_forward(build, grid, ind.index, rf, start_year=1935)
    return WF.report("momentum settoriale cross-sectional", "H5",
                     oos, rzs, eq, rf, ne, 5, var_sr=vsr)


# ---------------------------------------------------------------- H6
def h6_sl_tp(rf, eq):
    """Stop loss e take profit su CHIUSURE MENSILI.

    LIMITE DA DICHIARARE: senza High/Low giornalieri non posso simulare uno
    stop intraday. Uno stop mensile e' molto piu' permissivo di uno reale:
    ignora tutto cio' che accade dentro il mese. I risultati qui sopravvalutano
    la protezione di uno stop e sottovalutano quella di un take profit."""
    # media a 10 mesi precalcolata: serve come regola di RIENTRO dopo lo stop.
    lvl_idx = 100.0 * (1 + eq.fillna(0)).cumprod()
    MA10 = lvl_idx.rolling(10).mean()

    def build(cfg, idx):
        sl, tp = cfg
        r = eq.reindex(idx).dropna()
        ma = MA10.reindex(r.index)
        px = lvl_idx.reindex(r.index)
        if len(r) < 24:
            return None, None
        pos, out, turns = 1.0, [], []
        peak = entry = 1.0
        lvl = 1.0
        for i in range(len(r)):
            x = float(r.iloc[i])
            out.append(pos * x)
            turns.append(0.0)
            lvl *= (1 + pos * x)
            if pos > 0:
                peak = max(peak, lvl)
                hit_sl = sl is not None and lvl < peak * (1 - sl)
                hit_tp = tp is not None and lvl > entry * (1 + tp)
                if hit_sl or hit_tp:
                    pos = 0.0
                    turns[-1] = 1.0
            else:
                # rientro solo quando il prezzo torna sopra la media a 10 mesi:
                # senza una regola di rientro esplicita lo stop rientrerebbe il
                # mese dopo e non sarebbe uno stop.
                if pd.notna(ma.iloc[i]) and float(px.iloc[i]) > float(ma.iloc[i]):
                    pos, entry, peak = 1.0, lvl, lvl
                    turns[-1] = 1.0
        s_ = pd.Series(out, index=r.index)
        return s_, pd.Series(turns, index=r.index)

    grid = [(sl, tp) for sl in (None, 0.10, 0.20, 0.30) for tp in (None, 0.25, 0.50)]
    oos, rzs, picks, ne, vsr = WF.walk_forward(build, grid, eq.dropna().index, rf)
    return WF.report("stop loss / take profit su chiusure mensili", "H6",
                     oos, rzs, eq, rf, ne, 6,
                     extra="ATTENZIONE: stop su base mensile, non intraday", var_sr=vsr)


# ---------------------------------------------------------------- H7
def h7_leverage_margin(rf, eq):
    """Leva con vincolo di margine ESMA e liquidazione forzata.

    Novita' rispetto ai giri precedenti: qui la margin call e' MODELLATA. Con
    leva L il margine iniziale e' 1/L; se l'equity del conto scende sotto il 50%
    del margine richiesto, la posizione viene liquidata e si rientra il mese
    dopo. E' cio' che i backtest a leva normalmente ignorano."""
    MAINT = 0.5

    def build(cfg, idx):
        lv, = cfg
        r = eq.reindex(idx).dropna()
        if len(r) < 24:
            return None, None
        fin = rf.reindex(r.index).fillna(0.0) + C.FIN_SPREAD / 12.0
        out, live, cooldown = [], True, 0
        eqty = 1.0
        for i, x in enumerate(r):
            if not live:
                cooldown -= 1
                out.append(0.0)
                if cooldown <= 0:
                    live, eqty = True, 1.0
                continue
            gross = lv * float(x) - (lv - 1) * float(fin.iloc[i])
            eqty *= (1 + gross)
            out.append(gross)
            # equity per unita' di nozionale = eqty/lv; margine di mantenimento
            if eqty <= MAINT / lv:
                live, cooldown = False, 1
        s = pd.Series(out, index=r.index)
        return s, pd.Series(0.0, index=r.index)

    grid = [(lv,) for lv in (1.0, 1.5, 2.0, 3.0, 5.0)]
    oos, rzs, picks, ne, vsr = WF.walk_forward(build, grid, eq.dropna().index, rf)
    levs = [cfg[0] for _, cfg in picks]
    extra = (f"leva scelta piu' spesso: {max(set(levs), key=levs.count)}x"
             if levs else "nessuna scelta")
    return WF.report("leva con margin call ESMA modellata", "H7",
                     oos, rzs, eq, rf,
                     ne, 7, extra=extra, var_sr=vsr)


# ---------------------------------------------------------------- H8
def h8_geographic(rf, eq):
    """Diversificazione geografica pura, ZERO rotazione dopo l'acquisto.

    LIMITE: i fattori regionali di French partono dal 1990, quindi non c'e'
    TRAIN sulle finestre fisse. Il walk-forward parte dal 1996 con almeno 60
    mesi di storia. Storia piu' corta = risultato piu' fragile, lo dichiaro.
    """
    regs = {}
    for nm, key in (("Developed", "Developed_3_Factors"),
                    ("Emerging", "Emerging_5_Factors"),
                    ("Japan", "Japan_3_Factors"),
                    ("Europe", "Europe_3_Factors")):
        try:
            d = M.ff_region(key)
            regs[nm] = (d["Mkt-RF"] + d["RF"]).rename(nm)
        except Exception:
            pass
    if not regs:
        print("\nH8 — non testabile: nessun dato regionale caricato")
        return None
    df = pd.DataFrame({"US": eq, **regs}).dropna()

    def build(cfg, idx):
        mode, rb = cfg
        d = df.reindex(idx).dropna()
        if len(d) < 24:
            return None, None
        if mode == "US":
            w = {c: (1.0 if c == "US" else 0.0) for c in d.columns}
        elif mode == "equal":
            w = {c: 1.0 for c in d.columns}
        else:  # 60/40 US/resto
            w = {c: (0.6 if c == "US" else 0.4 / (len(d.columns) - 1)) for c in d.columns}
        r, tn = R.blend({c: d[c] for c in d.columns}, w, rb)
        return r, tn

    grid = [(m, rb) for m in ("US", "equal", "tilt") for rb in (12, 120)]
    oos, rzs, picks, ne, vsr = WF.walk_forward(build, grid, df.index, rf, start_year=1996,
                                     min_train_months=60)
    return WF.report("diversificazione geografica, rotazione minima", "H8",
                     oos, rzs, df["US"], rf, ne, 8,
                     extra="storia dal 1990: campione corto", var_sr=vsr)


# ---------------------------------------------------------------- H9
def h9_invvol(rf, eq):
    """Combinazione inverse-volatility degli stream meno correlati disponibili:
    azionario, decennale, e i premi Century per classe di asset. Pesi inversi
    alla volatilita' stimata sui 36 mesi precedenti, ribilanciamento annuale."""
    cen = M.century()
    cols = [c for c in cen.columns if c.endswith("Multi-style")
            and any(k in c for k in ("Fixed income", "Currencies", "Commodities"))]
    DRAG = 0.075 / 12.0
    parts = {"eq": eq, "bond": M.bond_total_return_monthly()}
    for c in cols:
        parts[c.split()[0].lower()] = cen[c].dropna() - DRAG
    df = pd.DataFrame(parts).dropna()
    VOL9 = df.rolling(36).std()

    def build(cfg, idx):
        rb, lv = cfg
        d = df.reindex(idx).dropna()
        if len(d) < 60:
            return None, None
        vol = VOL9.reindex(d.index)[d.columns]
        rets, turns, w = [], [], None
        for i in range(len(d)):
            if i < 36:
                rets.append(np.nan); turns.append(0.0); continue
            if w is None or i % rb == 0:
                v = vol.iloc[i - 1].replace(0, np.nan).dropna()
                iv = (1.0 / v)
                new = iv / iv.sum()
                new = new.reindex(d.columns).fillna(0.0)
                turns.append(0.5 * float((new - (w if w is not None else 0)).abs().sum())
                             if w is not None else 1.0)
                w = new
            else:
                turns.append(0.0)
            r = d.iloc[i]
            rets.append(float((w * r).sum()) - turns[-1] * C.COST_ROUND_TRIP)
            g = w * (1 + r)
            w = g / g.sum()
        s = pd.Series(rets, index=d.index).dropna()
        s = R.lever(s, rf.reindex(s.index).fillna(0.0), lv)
        return s, pd.Series(turns, index=d.index).reindex(s.index)

    grid = [(rb, lv) for rb in (12, 60) for lv in (1.0, 1.5, 2.0)]
    oos, rzs, picks, ne, vsr = WF.walk_forward(build, grid, df.index, rf, start_year=1970)
    return WF.report("combinazione inverse-vol multi-asset", "H9", oos, rzs,
                     df["eq"], rf, ne, 9, var_sr=vsr)


def main():
    ff, rf, eq = _core()
    out = []
    for fn in (h2_trend, h4_defensive, h5_momentum, h6_sl_tp,
               h7_leverage_margin, h8_geographic, h9_invvol):
        try:
            r = fn(rf, eq)
            if r:
                out.append(r)
        except Exception as e:
            print(f"\n{fn.__name__}: FALLITO {type(e).__name__}: {e}")
    print(f"\n{'='*74}\nRIEPILOGO")
    print(f"{'ip.':<5}{'strategia':<44}{'vs B&H':>9}{'DSR':>8}{'esito':>14}")
    for r in sorted(out, key=lambda d: -d["excess"]):
        print(f"{r['hyp']:<5}{r['name'][:43]:<44}{r['excess']:>+8.2f}%"
              f"{r['dsr']:>8.3f}{r['verdict']:>14}")
    promoted = [r for r in out if r["verdict"] == "PROMUOVIBILE"]
    print(f"\nPromuovibili: {len(promoted)}   tentativi cumulati a registro: "
          f"{lab.n_trials_so_far()}")
    return out


if __name__ == "__main__":
    main()

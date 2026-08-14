"""
VIX E BREADTH (S5TH) SONO PREDITTIVI DEL MERCATO?
=================================================
Uso:  python3 predictive_test.py            # studio completo
      python3 predictive_test.py --quick    # meno rotazioni bootstrap, gira in ~20s

La domanda "X e' predittivo" non ha una risposta sola, perche' nasconde tre domande
diverse che hanno tre risposte diverse:

  1) X contiene informazione statistica sui rendimenti futuri?
  2) X contiene informazione sul RISCHIO futuro (volatilita', drawdown)?
  3) usando X si guadagna piu' che stando fermi, dopo costi e tasse?

Questo script risponde a tutte tre separatamente, perche' e' normalissimo che la
risposta sia si', si', no: e' il caso base di quasi tutti gli indicatori noti.

COME SI EVITA DI PRENDERSI IN GIRO
  - segnale al tempo t = solo dati fino a t (percentili su finestra mobile, mai
    quantili di tutto il campione: quelli contengono il futuro)
  - i rendimenti forward si sovrappongono, quindi la t di OLS classica e' gonfiata.
    Si usano due difese: t di Newey-West (kernel di Bartlett, L = orizzonte) e un
    p-value da bootstrap di rotazione circolare, che rompe la relazione fra segnale
    e target conservando l'autocorrelazione di entrambi.
  - si conta quanti test si fanno: con 60 combinazioni segnale x orizzonte, qualche
    p < 0.05 esce per forza. La soglia va letta con Bonferroni in mano.
  - la parte "e' sfruttabile" usa gli stessi parametri di swing_harness.py (costi 0.15%
    round-trip, CGT 33%) con un motore che tiene la base di costo, perche' una strategia
    che dosa l'esposizione realizza plusvalenze a ogni riduzione e le deve pagare.
    Validazione SOLO out-of-sample sulla seconda meta' del campione.
  - ogni confronto e' in total return (chiusure aggiustate) e con la liquidita' remunerata
    al T-bill: senza queste due cose stare fuori dal mercato sembra gratis, e non lo e'.
"""
import sys

import numpy as np
import pandas as pd

import market_data as md
from swing_harness import CGT, COST_RT, buyhold

QUICK   = '--quick' in sys.argv
NROT    = 400 if QUICK else 3000      # rotazioni per il p-value bootstrap
HORIZ   = [5, 21, 63, 126, 252]       # orizzonti forward in sedute (1w, 1m, 3m, 6m, 1y)
PCT_WIN = 756                         # finestra per i percentili point-in-time (3 anni)
MIN_COV = 0.75                        # copertura minima dei costituenti per usare la breadth
rng     = np.random.default_rng(7)


# ============================================================ target: cosa vogliamo predire
def fwd_return(px, h):
    """Rendimento semplice fra t e t+h (sovrapposto: e' voluto, la statistica lo gestisce)."""
    return px.shift(-h) / px - 1


def fwd_vol(ret, h):
    """Volatilita' annualizzata realizzata nelle h sedute SUCCESSIVE a t."""
    return ret.rolling(h).std().shift(-h) * np.sqrt(252)


def fwd_maxdd(px, h):
    """Peggior drawdown fra t e t+h, misurato dal picco corrente (negativo)."""
    p = px.to_numpy(float)
    n = len(p)
    out = np.full(n, np.nan)
    for i in range(n - h):
        w = p[i:i + h + 1]
        out[i] = (w / np.maximum.accumulate(w) - 1).min()
    return pd.Series(out, index=px.index)


# ============================================================ statistica
def spearman(x, y):
    xr, yr = pd.Series(x).rank().to_numpy(copy=True), pd.Series(y).rank().to_numpy(copy=True)
    xr -= xr.mean(); yr -= yr.mean()
    d = np.sqrt((xr**2).sum() * (yr**2).sum())
    return float((xr * yr).sum() / d) if d else 0.0


def rotation_pvalue(x, y, h, nrot=NROT):
    """p-value a due code ruotando ciclicamente il target.

    L'ipotesi nulla non e' "y e' rumore bianco" (falsa e comodissima) ma
    "y e x non sono allineati": ruotando y si tiene la sua memoria interna e si
    distrugge solo la relazione. E' il null giusto per serie autocorrelate.
    """
    xr = pd.Series(x).rank().to_numpy(copy=True); xr -= xr.mean()
    yr = pd.Series(y).rank().to_numpy(copy=True); yr -= yr.mean()
    den = np.sqrt((xr**2).sum() * (yr**2).sum())
    ic = (xr * yr).sum() / den
    n = len(xr)
    shifts = rng.integers(h + 1, n - h - 1, size=nrot)
    null = np.array([abs((xr * np.roll(yr, s)).sum() / den) for s in shifts])
    return float(ic), float((null >= abs(ic)).mean())


def newey_west_t(x, y, lags):
    """t-stat di y = a + b*x con varianza HAC (Bartlett). Ritorna (beta, t)."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    X = np.column_stack([np.ones_like(x), x])
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ (X.T @ y)
    u = (y - X @ beta)[:, None] * X
    S = u.T @ u
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1)
        G = u[l:].T @ u[:-l]
        S += w * (G + G.T)
    V = xtx_inv @ S @ xtx_inv
    se = np.sqrt(max(V[1, 1], 1e-18))
    return float(beta[1]), float(beta[1] / se)


def nw_multi(y, X, lags):
    """OLS multivariata con errori HAC di Newey-West. Ritorna (t-stat per colonna, R2)."""
    y = np.asarray(y, float)
    Z = np.column_stack([np.ones(len(y))] + [np.asarray(X[c], float) for c in X.columns])
    xtx_inv = np.linalg.inv(Z.T @ Z)
    beta = xtx_inv @ (Z.T @ y)
    res = y - Z @ beta
    u = res[:, None] * Z
    S = u.T @ u
    for l in range(1, lags + 1):
        w = 1 - l / (lags + 1)
        G = u[l:].T @ u[:-l]
        S += w * (G + G.T)
    V = xtx_inv @ S @ xtx_inv
    t = beta / np.sqrt(np.maximum(np.diag(V), 1e-18))
    r2 = 1 - res.var() / y.var() if y.var() > 0 else 0.0
    return dict(zip(X.columns, t[1:])), float(r2)


def incremental_table(sig, target, cols, hlist, title):
    """I segnali messi insieme nella stessa regressione: chi resta in piedi?

    E' la domanda che conta quando due indicatori raccontano la stessa storia. Se la
    breadth perde la sua t quando accanto c'e' il VIX, non stava aggiungendo niente:
    era un secondo termometro nella stessa stanza.
    """
    print(f'\n{title}')
    print(f"{'oriz.':>7}{'n':>7}{'n eff':>7}" + ''.join(f'{c[:20]:>22}' for c in cols)
          + f"{'R2':>8}")
    print('-' * (21 + 22 * len(cols) + 8))
    for h in hlist:
        y = target[h]
        X = sig[cols]
        ok = y.notna() & X.notna().all(axis=1)
        if ok.sum() < 500: continue
        Xs = X[ok]
        Xs = (Xs - Xs.mean()) / Xs.std()          # standardizzati: le t sono confrontabili
        tt, r2 = nw_multi(y[ok], Xs, lags=h)
        print(f'{h:>7}{int(ok.sum()):>7}{int(ok.sum()/h):>7}'
              + ''.join(f'{tt[c]:>22.2f}' for c in cols) + f'{100*r2:>7.1f}%')
    print('   valori = t di Newey-West del coefficiente, regressori standardizzati.'
          '  |t| > 2 circa = significativo.')
    print('   n eff = finestre non sovrapposte: con n eff sotto ~25 la t e\' un numero'
          ' con la faccia\n   sicura, non un\'evidenza. Guardala prima di crederci.')


# ============================================================ segnali (solo info passata)
def pct_rank(s, win=PCT_WIN):
    """Percentile del valore corrente nella sua finestra mobile: 0 = minimo, 1 = massimo."""
    return s.rolling(win, min_periods=win // 3).rank(pct=True)


def breadth_series(df, min_cov=MIN_COV):
    """La serie di breadth da usare: S5TH vero se disponibile, altrimenti la replica
    limitata ai giorni con copertura sufficiente dei costituenti."""
    if 'S5TH_REAL' in df and df.S5TH_REAL.notna().sum() > 500:
        return df.S5TH_REAL
    if 'BREADTH' in df:
        return df.BREADTH.where(df.COVER >= min_cov)
    return None


def breadth_signals(b, px):
    """I segnali derivati dalla breadth, dato il livello b e il prezzo px."""
    sig = pd.DataFrame(index=b.index)
    sig['S5TH livello']       = b
    sig['S5TH percentile 3a'] = pct_rank(b)
    sig['S5TH var 21g']       = b - b.shift(21)
    sig['S5TH - sua MA50']    = b - b.rolling(50).mean()
    # divergenza: prezzo su nuovi massimi a 63g ma breadth sotto il suo massimo a 63g
    px_high = (px >= px.rolling(63).max() - 1e-9).astype(float)
    sig['divergenza prezzo/S5TH'] = px_high * (b - b.rolling(63).max())
    return sig


def build_signals(df):
    ret = df.ADJ.pct_change()
    rv21 = ret.rolling(21).std() * np.sqrt(252) * 100        # vol realizzata, in punti VIX
    sig = pd.DataFrame(index=df.index)

    # --- famiglia VIX
    sig['VIX livello']        = df.VIX
    sig['VIX percentile 3a']  = pct_rank(df.VIX)
    sig['VIX var 21g']        = df.VIX - df.VIX.shift(21)
    sig['VIX - vol realizz.'] = df.VIX - rv21               # premio al rischio di varianza
    sig['VIX3M/VIX (term)']   = df.VIX3M / df.VIX           # >1 = calma, <1 = stress

    # --- famiglia breadth: il S5TH vero se l'hai messo in data/s5th.csv, altrimenti la replica
    b = breadth_series(df)
    if b is not None:
        for c, v in breadth_signals(b, df.Close).items():
            sig[c] = v

    # --- baseline con cui confrontarsi: il trend del prezzo, gratis e noto da 90 anni
    sig['prezzo/MA200 (baseline)'] = df.Close / df.Close.rolling(200).mean() - 1
    return sig


# ============================================================ report: predittivita' pura
def ic_table(sig, target, name_target, hlist=HORIZ, title=''):
    print(f'\n{title}')
    print(f"{'segnale':<26}{'oriz.':>7}{'n':>7}{'n eff':>7}{'IC':>8}{'p rot':>8}{'t NW':>8}")
    print('-' * 71)
    rows = []
    for col in sig.columns:
        for h in hlist:
            x, y = sig[col], target[h]
            ok = x.notna() & y.notna()
            if ok.sum() < 500: continue
            xv, yv = x[ok].to_numpy(), y[ok].to_numpy()
            ic, p = rotation_pvalue(xv, yv, h)
            _, t = newey_west_t((xv - xv.mean()) / xv.std(), yv, lags=h)
            rows.append(dict(segnale=col, h=h, n=int(ok.sum()), ic=ic, p=p, t=t))
            star = '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
            print(f'{col:<26}{h:>7}{int(ok.sum()):>7}{int(ok.sum()/h):>7}'
                  f'{ic:>8.3f}{p:>8.3f}{t:>7.2f} {star}')
    print(f'   IC = correlazione di rango segnale -> {name_target}.  '
          f'n eff = osservazioni non sovrapposte.')
    return pd.DataFrame(rows)


# ============================================================ report: tabelle condizionali
def quintile_table(sig_col, target, h, label):
    """Rendimento forward medio per quintile del segnale, quintili point-in-time."""
    q = pct_rank(sig_col)
    y = target[h]
    ok = q.notna() & y.notna()
    q, y = q[ok], y[ok]
    ann = 252 / h
    print(f'\n{label}  (orizzonte {h} sedute, {len(y)} osservazioni)')
    print(f"{'quintile del segnale':<24}{'n':>7}{'media ann.':>12}{'mediana ann.':>14}{'positivi':>10}")
    print('-' * 67)
    for lo, hi, nm in [(0, .2, 'Q1 (piu\' basso)'), (.2, .4, 'Q2'), (.4, .6, 'Q3'),
                       (.6, .8, 'Q4'), (.8, 1.01, 'Q5 (piu\' alto)')]:
        m = (q >= lo) & (q < hi)
        if m.sum() < 30: continue
        yy = y[m]
        print(f'{nm:<24}{m.sum():>7}{100*yy.mean()*ann:>11.1f}%{100*yy.median()*ann:>13.1f}%'
              f'{100*(yy > 0).mean():>9.0f}%')
    print(f"{'--- tutto il campione':<24}{len(y):>7}{100*y.mean()*ann:>11.1f}%"
          f"{100*y.median()*ann:>13.1f}%{100*(y > 0).mean():>9.0f}%")


def cross_table(a, b, target, h, la, lb):
    """Interazione fra due segnali: terzili x terzili, rendimento forward annualizzato."""
    qa, qb, y = pct_rank(a), pct_rank(b), target[h]
    ok = qa.notna() & qb.notna() & y.notna()
    qa, qb, y = qa[ok], qb[ok], y[ok]
    ann = 252 / h
    band = [(0, 1/3, 'basso'), (1/3, 2/3, 'medio'), (2/3, 1.01, 'alto')]
    print(f'\nInterazione {la} x {lb} — rendimento annualizzato a {h} sedute '
          f'({len(y)} osservazioni)')
    print(f"{'':<14}" + ''.join(f'{lb} {n:<8}'[:14] for _, _, n in band))
    for loa, hia, na in band:
        cells = []
        for lob, hib, nb in band:
            m = (qa >= loa) & (qa < hia) & (qb >= lob) & (qb < hib)
            cells.append(f'{100*y[m].mean()*ann:>6.1f}% ({m.sum():>4})' if m.sum() >= 30
                         else f'{"-":>13}')
        print(f'{la} {na:<9}'[:14] + ''.join(f'{c:<14}' for c in cells))


# ============================================================ report: e' sfruttabile?
def rules(df, sig):
    """Regole long/flat costruite sui segnali. Ogni regola e' una famiglia con 1 parametro.

    Le soglie sui percentili sono point-in-time; quelle sulla breadth in livello
    assoluto (S5TH e' una percentuale, 50% ha lo stesso significato nel 1998 e oggi).
    """
    out = {}
    vixp = sig['VIX percentile 3a']
    out['VIX alto -> investito'] = {f'p>{q}': (vixp >= q).astype(float) for q in (.5, .7, .8, .9)}
    out['VIX basso -> investito'] = {f'p<{q}': (vixp <= q).astype(float) for q in (.5, .7, .8, .9)}
    if 'S5TH livello' in sig:
        b = sig['S5TH livello']
        out['S5TH sopra soglia'] = {f'>{t}%': (b >= t).astype(float) for t in (30, 40, 50, 60)}
        out['S5TH sotto soglia (contrarian)'] = {f'<{t}%': (b <= t).astype(float)
                                                 for t in (20, 30, 40, 50)}
        out['S5TH>soglia o VIX estremo'] = {
            f'>{t}%|p>.9': ((b >= t) | (vixp >= .9)).astype(float) for t in (30, 40, 50, 60)}
    ma = df.Close / df.Close.rolling(200).mean()
    out['prezzo>MA200 (baseline)'] = {'MA200': (ma >= 1).astype(float)}

    # Dosare l'esposizione invece di accenderla/spegnerla: e' il modo in cui la
    # previsione di volatilita' si usa davvero (vol targeting, nessuna leva).
    rv = df.ADJ.pct_change().rolling(21).std() * np.sqrt(252) * 100
    out['vol target da VIX'] = {f'{t}%': (t / df.VIX).clip(0, 1) for t in (10, 12, 15, 20)}
    out['vol target da vol realizz.'] = {f'{t}%': (t / rv).clip(0, 1) for t in (10, 12, 15, 20)}

    # esposizione costante: il confronto giusto per chi sta a mezzo carico senza previsioni
    out['statico (benchmark)'] = {f'{int(100*x)}%': pd.Series(x, index=df.index)
                                  for x in (0.6, 0.8, 1.0)}
    return out


def total_return_index(df):
    """Serie su cui si misura tutto: la chiusura aggiustata per dividendi (ADJ).

    Senza dividendi chi resta liquido non perde nulla e ogni filtro sembra migliore di
    quello che e': il ~1.8% l'anno di cedola e' esattamente il costo di stare fuori.
    """
    return df.ADJ if 'ADJ' in df else df.Close


def evaluate_scaled(df, pos, rf=None, cgt=CGT, cost=COST_RT / 2):
    """Conto economico con base di costo, per posizioni anche frazionarie.

    Serve perche' evaluate() di swing_harness tassa solo quando la posizione va a zero:
    corretto per una strategia on/off, regalo fiscale per una che dosa l'esposizione
    (ogni riduzione realizza plusvalenza e la tassa si paga). Qui si tiene traccia di
    valore, liquidita' e base di costo; ogni vendita paga la CGT sulla quota di gain,
    e alla fine si liquida tutto pagando l'imposta sul latente, come fa il buy&hold.
    """
    ret = df.Close.pct_change().fillna(0).to_numpy(float)
    w   = pos.reindex(df.index).fillna(0).clip(0, 1).to_numpy(float)
    rfv = (rf.reindex(df.index).fillna(0).to_numpy(float) if rf is not None
           else np.zeros(len(df)))
    V = B = 0.0                       # valore di mercato e base di costo della posizione
    C = 1.0                           # liquidita'
    taxes = turnover = 0.0
    eq_path = np.empty(len(w))
    for i in range(len(w)):
        V *= 1 + ret[i]
        C *= 1 + rfv[i]
        eq = V + C
        d = w[i] * eq - V             # quanto comprare (+) o vendere (-)
        if d > 0:
            d = min(d, C / (1 + cost))   # nessuna leva e cassa mai negativa
            V += d; C -= d; B += d
        elif d < 0:
            s = min(-d, V)
            gain = s * (1 - B / V) if V > 0 else 0.0
            tax = cgt * gain if gain > 0 else 0.0
            B *= 1 - s / V if V > 0 else 0.0
            V -= s; C += s - tax; taxes += tax
            d = -s
        fee = cost * abs(d)
        C -= fee
        turnover += abs(d) / eq if eq > 0 else 0.0
        eq_path[i] = V + C
    # Liquidazione finale: entra nel CAGR ma NON nella curva, altrimenti l'ultimo giorno
    # del campione appare come un crollo del 20% e falsa drawdown e Sharpe.
    gain = V - B
    final_tax = cgt * gain if gain > 0 else 0.0
    taxes += final_tax
    curve = pd.Series(eq_path, index=df.index)
    r = curve.pct_change().fillna(0)
    yrs = len(df) / 252
    return dict(cagr=((curve.iloc[-1] - final_tax) ** (1 / yrs) - 1) * 100,
                mdd=(curve / curve.cummax() - 1).min() * 100,
                sharpe=r.mean() / r.std() * np.sqrt(252) if r.std() > 0 else 0.0,
                expo=100 * w.mean(), turn_yr=turnover / yrs, taxes=taxes)


def tradability(df, sig, rf, skip=(), title=''):
    if title: print(title)
    dtr = df.assign(Close=total_return_index(df))   # tutto valutato in total return
    ins_end = len(df) // 2
    ins, oos = dtr.iloc[:ins_end], dtr.iloc[ins_end:]
    b_ins, b_oos = buyhold(ins), buyhold(oos)
    print(f'\nCampione: {df.index[0].date()} -> {df.index[-1].date()}')
    print(f'IN-SAMPLE  {ins.index[0].date()} -> {ins.index[-1].date()}    '
          f'buy&hold netto {b_ins["cagr"]:.2f}% (DD {b_ins["mdd"]:.1f}%)')
    print(f'OUT-SAMPLE {oos.index[0].date()} -> {oos.index[-1].date()}    '
          f'buy&hold netto {b_oos["cagr"]:.2f}% (DD {b_oos["mdd"]:.1f}%, '
          f'Sharpe {b_oos["sharpe"]:.2f}, lordo d\'imposta {b_oos["cagr_lordo"]:.2f}%)')
    print(f'\nOverlay long/flat o dosato, costi 0.15% r/t, liquidita\' al T-bill.')
    print(f'Due colonne di CAGR: ante-imposte e con CGT {CGT:.0%} pagata a ogni trade chiuso.')
    print(f"{'regola':<30}{'par':<9}{'IS netto':>9}{'OOS ante':>9}{'OOS netto':>10}"
          f"{'OOS DD':>8}{'Sharpe':>8}{'espos.':>8}{'turn/an':>8}")
    print('-' * 99)
    for fam, variants in rules(df, sig).items():
        if any(k in fam for k in skip): continue
        for par, pos in variants.items():
            pos = pos.shift(1).fillna(0)          # decidi con la chiusura di ieri, esegui oggi
            m_i = evaluate_scaled(ins, pos, rf=rf)
            m_o = evaluate_scaled(oos, pos, rf=rf)
            m_g = evaluate_scaled(oos, pos, rf=rf, cgt=0)
            flag = ''                              # margini minimi non sono vittorie
            if m_o['cagr'] > b_oos['cagr'] + 0.10:        flag += ' batte-B&H'
            if m_g['sharpe'] > b_oos['sharpe'] + 0.02:    flag += ' Sharpe>B&H'
            # DD e Sharpe dalla curva ante-imposte: i prelievi fiscali sono eventi
            # puntuali, dentro la serie giornaliera ne falserebbero la volatilita'.
            print(f'{fam:<30}{par:<9}{m_i["cagr"]:>8.2f}%{m_g["cagr"]:>8.2f}%{m_o["cagr"]:>9.2f}%'
                  f'{m_g["mdd"]:>7.1f}%{m_g["sharpe"]:>8.2f}'
                  f'{m_g["expo"]:>7.0f}%{m_g["turn_yr"]:>8.1f}{flag}')
    print(f'\nBuy&hold OOS: ante-imposte {b_oos["cagr_lordo"]:.2f}%, netto {b_oos["cagr"]:.2f}%, '
          f'DD {b_oos["mdd"]:.1f}%, Sharpe {b_oos["sharpe"]:.2f}, esposizione 100%')
    print('Il buy&hold paga la CGT una sola volta alla fine: parte del divario e\' '
          'differimento\nfiscale, non mancanza di segnale. Per questo c\'e\' la colonna ante-imposte.')


# ============================================================ main
def main():
    df = md.load_dataset()
    px = total_return_index(df)                   # prezzo + dividendi
    ret = px.pct_change()
    rf_ann = md.fred('DGS3MO').reindex(df.index).ffill() / 100
    rf = (rf_ann / 252) * (1 - CGT)               # T-bill netto d'imposta, giornaliero

    fwd_r  = {h: fwd_return(px, h) for h in HORIZ}
    fwd_v  = {h: fwd_vol(ret, h) for h in HORIZ}
    fwd_d  = {h: fwd_maxdd(px, h) for h in HORIZ}
    sig = build_signals(df)

    print('=' * 95)
    print('VIX E BREADTH (S5TH): STUDIO DI PREDITTIVITA\'')
    print('=' * 95)
    cov = df.COVER if 'COVER' in df else pd.Series(dtype=float)
    print(f'SPY {df.index[0].date()} -> {df.index[-1].date()} ({len(df)} sedute), '
          f'VIX da {df.VIX.first_valid_index().date()}')
    if len(cov):
        good = df.index[df.COVER >= MIN_COV]
        print(f'Replica S5TH: {df.BREADTH.first_valid_index().date()} -> '
              f'{df.BREADTH.last_valid_index().date()}, usata solo con copertura >= '
              f'{MIN_COV:.0%} dei costituenti: dal {good[0].date()} ({len(good)} sedute)')
        print(f'   copertura media nel periodo usato: {100*df.COVER.loc[good].mean():.1f}%, '
              f'membri mediani {df.NMEM.loc[good].median():.0f}')
        grp = df.COVER.groupby((df.index.year // 5) * 5)
        print('   copertura per quinquennio (quota di membri con prezzo disponibile):')
        print('     ' + '  '.join(f'{y}-{y+4}: {100*v:.0f}%' for y, v in grp.mean().items()))
        print('   I nomi mancanti sono quasi tutti titoli usciti dall\'indice e delistati:'
              '\n   dove la copertura e\' bassa la breadth ricostruita e\' distorta verso l\'alto.')
        if 'S5TH_REAL' in df and df.S5TH_REAL.notna().sum() > 500:
            both = df[['BREADTH', 'S5TH_REAL']].dropna()
            print(f'   S5TH reale da data/s5th.csv: usato al posto della replica. '
                  f'correlazione con la replica su {len(both)} sedute comuni: '
                  f'liv. {both.BREADTH.corr(both.S5TH_REAL):.3f}, '
                  f'var.giorn. {both.BREADTH.diff().corr(both.S5TH_REAL.diff()):.3f}')

    print('\n' + '=' * 95)
    print('1. PREDITTIVITA\' SUI RENDIMENTI')
    print('=' * 95)
    r1 = ic_table(sig, fwd_r, 'rendimento futuro',
                  title='IC di rango, p-value da rotazione circolare, t di Newey-West')
    ntest = len(r1)
    print(f'   {ntest} test: la soglia di Bonferroni al 5% e\' p < {0.05/max(ntest,1):.4f}, '
          f'non 0.05.')

    # Sensibilita': la stessa breadth su tutta la storia disponibile, copertura bassa inclusa.
    # Va guardata sapendo che prima del 2010 mancano i delistati e la breadth legge troppo alto.
    if 'BREADTH' in df:
        b_long = breadth_series(df, min_cov=0.0)
        ic_table(breadth_signals(b_long, df.Close), fwd_r, 'rendimento futuro',
                 hlist=[21, 63, 252],
                 title=f'Sensibilita\': stessa breadth su {b_long.first_valid_index().date()} -> '
                       f'{b_long.last_valid_index().date()} senza filtro di copertura\n'
                       f'(campione lungo ma distorto: dove mancano i delistati la breadth '
                       f'legge troppo alto)')

    print('\n' + '=' * 95)
    print('2. PREDITTIVITA\' SUL RISCHIO (volatilita\' e drawdown futuri)')
    print('=' * 95)
    ic_table(sig, fwd_v, 'volatilita\' futura', hlist=[21, 63, 252],
             title='Target: volatilita\' realizzata nelle sedute successive')
    ic_table(sig, fwd_d, 'drawdown futuro', hlist=[21, 63, 252],
             title='Target: peggior drawdown nelle sedute successive')

    if 'S5TH livello' in sig:
        print('\n' + '=' * 95)
        print('3. S5TH AGGIUNGE QUALCOSA AL VIX? (regressioni multivariate)')
        print('=' * 95)
        trio = ['VIX percentile 3a', 'S5TH livello', 'prezzo/MA200 (baseline)']
        incremental_table(sig, fwd_r, trio, HORIZ,
                          'Target: rendimento futuro — tutti insieme nella stessa regressione')
        incremental_table(sig, fwd_v, trio, [21, 63, 252],
                          'Target: volatilita\' futura')
        incremental_table(sig, fwd_d, trio, [21, 63, 252],
                          'Target: drawdown futuro')

    print('\n' + '=' * 95)
    print('4. TABELLE CONDIZIONALI (quintili point-in-time)')
    print('=' * 95)
    quintile_table(sig['VIX percentile 3a'], fwd_r, 63, 'VIX (percentile 3 anni)')
    quintile_table(sig['VIX percentile 3a'], fwd_r, 252, 'VIX (percentile 3 anni)')
    if 'S5TH livello' in sig:
        quintile_table(sig['S5TH livello'], fwd_r, 63, 'S5TH livello')
        quintile_table(sig['S5TH livello'], fwd_r, 252, 'S5TH livello')
        quintile_table(sig['S5TH livello'], fwd_v, 63, 'S5TH livello -> VOLATILITA\' futura')

    if 'S5TH livello' in sig:
        print('\n' + '=' * 95)
        print('5. INTERAZIONE VIX x S5TH')
        print('=' * 95)
        cross_table(sig['VIX percentile 3a'], sig['S5TH livello'], fwd_r, 63, 'VIX', 'S5TH')
        cross_table(sig['VIX percentile 3a'], sig['S5TH livello'], fwd_r, 252, 'VIX', 'S5TH')

    print('\n' + '=' * 95)
    print('6. E\' SFRUTTABILE? OVERLAY CON COSTI, TASSE E VALIDAZIONE OUT-OF-SAMPLE')
    print('=' * 95)
    tradability(df, sig, rf, skip=('S5TH',),
                title='\n--- 6a. campione pieno (regole su VIX e prezzo)')
    if 'S5TH livello' in sig and len(cov):
        # Le regole sulla breadth vanno provate solo dove la breadth esiste ed e' affidabile,
        # altrimenti mezzo in-sample sarebbe posizione zero per assenza di dato.
        sub = df.loc[df.index >= good[0]]
        tradability(sub, sig, rf,
                    title=f'\n--- 6b. sottocampione con S5TH affidabile '
                          f'({sub.index[0].date()} -> {sub.index[-1].date()}), tutte le regole')

    print('\n' + '=' * 95)
    print('COME LEGGERE QUESTO OUTPUT')
    print('=' * 95)
    print("""  - IC statisticamente significativo + overlay che perde contro il buy&hold non e'
    una contraddizione: significa che l'informazione c'e' ma il suo valore e' minore
    del costo di usarla (commissioni, tasse, tempo fuori mercato nei rimbalzi).
  - Guarda prima la colonna 'p rot' con Bonferroni in mano, poi 'OOS cagr'.
  - Un IC 0.05-0.10 su rendimenti a 3-12 mesi e' tipico di un segnale macro vero:
    spiega l'1% della varianza. Serve per dimensionare il rischio, non per fare timing.
  - Il confronto onesto per un filtro di trend non e' il buy&hold: e' prezzo>MA200,
    che costa zero e sta nella tabella. Se non lo batte, la breadth non serve.""")


if __name__ == '__main__':
    main()

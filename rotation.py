"""
BATTERE L'S&P 500 CON L'ORO E IL MOMENTUM?
==========================================
Uso:  python3 rotation.py

L'IDEA DA TESTARE
  Stare su S&P finche' sale, passare all'oro quando l'S&P si rompe. L'oro e' poco
  correlato all'azionario, quindi in teoria si cavalcano i rialzi e si evita di
  incassare i crolli. Facile a dirsi: qui si misura.

COSA SI CONFRONTA
  1) buy&hold S&P (il benchmark da battere)
  2) mix statici S&P/oro ribilanciati (nessuna previsione: cattura solo la
     diversificazione, ed e' il vero avversario di qualunque regola di momentum)
  3) momentum relativo: tieni quello dei due che e' andato meglio negli ultimi L mesi
  4) momentum assoluto con l'oro come rifugio: S&P se il suo momentum e' positivo,
     altrimenti oro (e' letteralmente la strategia della domanda)
  5) dual momentum alla Antonacci: il migliore dei due, ma se batte anche il T-bill,
     sennò liquidita'
  6) trend su media a 10 mesi, con l'oro al posto della liquidita'
  7) risk parity elementare: pesi inversi alla volatilita'

DUE CAMPIONI, PERCHE' UNO SOLO INGANNA
  LUNGO   1971-2026, mensile. Oro LBMA + S&P total return ricostruito (Shiller).
          Include il 1980-2000, in cui l'oro ha perso due terzi in termini reali:
          e' la parte che smonta le strategie con l'oro dentro, e va guardata.
  BREVE   2004-2026, giornaliero, con SPY e GLD veri: ETF realmente comprabili,
          drawdown misurati sul dato giornaliero, costi di gestione dentro il prezzo.

COSTI CONSIDERATI
  0.075% per lato di transazione, CGT 33% su ogni plusvalenza realizzata (con le
  minus che compensano le plus, come consente la normativa irlandese), spese di
  gestione annue sugli asset del campione lungo, liquidita' remunerata al T-bill
  netto d'imposta. Ribilanciare costa: chi ruota ogni mese paga la tassa ogni mese,
  mentre il buy&hold la paga una volta sola alla fine. Non e' un dettaglio, e' il
  motivo per cui molte strategie che "battono il mercato" lordo non lo battono netto.
"""
import numpy as np
import pandas as pd

import market_data as md
from swing_harness import CGT, COST_RT

COST     = COST_RT / 2                    # per lato
# Spread sul T-bill per il denaro preso a prestito. In swing_harness.py FIN_ANN e' un
# tasso all-in (benchmark + spread): qui il benchmark e' gia' il T-bill del periodo, quindi
# va sommato solo lo spread. 1.5% e' l'ordine di grandezza di un broker decente su conti
# piccoli; con 3% la leva peggiora, con 0.5% migliora di poco. Nessuna delle tre ribalta
# la conclusione.
FIN_SPR  = 0.015
EXPENSE  = {'SP500': 0.0009, 'ORO': 0.0040}   # spese annue di un ETF equivalente
START    = '1971-01-31'                   # oro libero di fluttuare: prima non ha senso


# ============================================================ dati
def panel_monthly():
    """Campione lungo mensile: S&P total return, oro, T-bill. Indici total return."""
    sh = md.shiller_monthly()
    gold = md.gold_monthly()
    tb = md.fred('TB3MS')
    tb.index = tb.index + pd.offsets.MonthEnd(0)

    r_sp = sh.PRICE.pct_change() + (sh.DIV / 12) / sh.PRICE.shift(1)   # prezzo + cedola
    sp = (1 + r_sp.fillna(0)).cumprod()
    df = pd.DataFrame({'SP500': sp, 'ORO': gold}).dropna()
    df = df.loc[df.index >= START]
    rf = (tb.reindex(df.index).ffill() / 100 / 12)
    return df / df.iloc[0], rf.rename('CASH')


def panel_daily():
    """Campione breve giornaliero con gli ETF veri: SPY e GLD, chiusure aggiustate."""
    spy = md.sa_history('SPY')
    gld = md.sa_history('GLD')
    df = pd.DataFrame({'SP500': spy['Adj'] if 'Adj' in spy else spy.Close,
                       'ORO': gld['Adj'] if 'Adj' in gld else gld.Close}).dropna()
    rf = md.fred('DGS3MO').reindex(df.index).ffill() / 100 / 252
    return df / df.iloc[0], rf.rename('CASH')


# ============================================================ motore di portafoglio
def evaluate_portfolio(px, w, rf, ppy, cgt=CGT, cost=COST, expense=None, band=0.0):
    """Portafoglio multi-asset con base di costo per asset, imposte e costi reali.

    px       indici total return degli asset (colonne)
    w        pesi obiettivo, GIA' decisi con i dati del periodo precedente
    rf       rendimento della liquidita' per periodo (lordo: qui viene tassato)
    band     ribilancia solo se lo scostamento supera questa soglia (in quota di
             patrimonio). Serve a non pagare tasse e commissioni per un 1% di deriva.

    Le minusvalenze alimentano un serbatoio che compensa le plusvalenze successive:
    e' cio' che la CGT irlandese consente, e non concederlo penalizzerebbe
    artificialmente le strategie che ruotano spesso.

    La leva e' dedotta dai pesi: se sommano a 1.3 si prendono a prestito 30 centesimi
    per euro, addebitati al T-bill + spread e senza scudo fiscale sugli interessi.
    Il ribilanciamento mensile deleva automaticamente dopo una perdita, che e' cio' che
    farebbe il broker, solo in modo piu' gentile.
    """
    assets = list(px.columns)
    ret = px.pct_change().fillna(0)
    exp_p = {a: (expense or {}).get(a, 0.0) / ppy for a in assets}
    wt = w.reindex(px.index).ffill().fillna(0.0)
    rf_gross = rf.reindex(px.index).fillna(0.0)
    rfv = rf_gross * (1 - cgt)                              # interessi attivi al netto d'imposta
    max_lev = max(1.0, float(wt.sum(axis=1).max()))

    V = {a: 0.0 for a in assets}
    B = {a: 0.0 for a in assets}
    C, taxes, turn, loss_pool = 1.0, 0.0, 0.0, 0.0
    curve, expo = np.empty(len(px)), {a: 0.0 for a in assets}

    for i in range(len(px)):
        for a in assets:
            V[a] *= 1 + ret[a].iat[i] - exp_p[a]
        C *= 1 + (rfv.iat[i] if C >= 0 else rf_gross.iat[i] + FIN_SPR / ppy)
        eq = sum(V.values()) + C
        if eq <= 0:
            curve[i] = eq
            continue
        target = {a: wt[a].iat[i] * eq for a in assets}
        if max(abs(target[a] - V[a]) for a in assets) / eq > band:
            for a in assets:                                   # prima le vendite
                s = min(V[a] - target[a], V[a])
                if s <= 1e-12: continue
                gain = s * (1 - B[a] / V[a]) if V[a] > 0 else 0.0
                if gain >= 0:
                    used = min(loss_pool, gain); loss_pool -= used
                    tax = cgt * (gain - used)
                else:
                    loss_pool += -gain; tax = 0.0
                B[a] *= 1 - s / V[a]
                V[a] -= s
                C += s - tax - cost * s
                taxes += tax; turn += s / eq
            need = sum(max(target[a] - V[a], 0.0) for a in assets)
            if need > 0:
                avail = (C + (max_lev - 1.0) * eq) / (1 + cost)
                scale = min(1.0, max(avail, 0.0) / need)       # leva solo quella dichiarata
                for a in assets:
                    d = max(target[a] - V[a], 0.0) * scale
                    if d <= 1e-12: continue
                    V[a] += d; B[a] += d
                    C -= d + cost * d
                    turn += d / eq
        curve[i] = sum(V.values()) + C
        for a in assets:
            expo[a] += V[a] / curve[i]

    gain_fin = sum(V[a] - B[a] for a in assets)                # liquidazione finale
    final_tax = cgt * max(gain_fin - loss_pool, 0.0)
    taxes += final_tax
    eqc = pd.Series(curve, index=px.index)
    r = eqc.pct_change().fillna(0)
    yrs = len(px) / ppy
    return dict(cagr=((eqc.iloc[-1] - final_tax) ** (1 / yrs) - 1) * 100,
                cagr_ante=(eqc.iloc[-1] ** (1 / yrs) - 1) * 100,
                mdd=(eqc / eqc.cummax() - 1).min() * 100,
                sharpe=r.mean() / r.std() * np.sqrt(ppy) if r.std() > 0 else 0.0,
                turn_yr=turn / yrs, taxes=taxes,
                expo={a: 100 * expo[a] / len(px) for a in assets},
                curve=eqc)


# ============================================================ strategie
def const_w(px, sp):
    """Pesi costanti: sp su S&P, il resto in oro."""
    return pd.DataFrame({'SP500': sp, 'ORO': 1 - sp}, index=px.index)


def monthly_decisions(w):
    """Aggiorna i pesi solo a fine mese e li tiene fermi in mezzo.

    Sui dati giornalieri e' indispensabile: un momentum a 12 mesi ricalcolato ogni giorno
    cambia idea per un decimale e ribalta il portafoglio decine di volte l'anno, pagando
    commissioni e CGT a ogni ripensamento. Queste strategie si decidono a fine mese.
    """
    eom = w.index.to_series().groupby([w.index.year, w.index.month]).transform('max')
    return w.where(w.index == eom).ffill().fillna(0.0)


def strategies(px, rf, ppy, lag=None):
    """Ogni voce e' una famiglia con un parametro. I pesi sono decisi al periodo t e
    applicati dopo `lag` periodi: e' lo shift che impedisce il look-ahead.

    Sul campione lungo lag=2 mesi, non 1. Motivo: le serie mensili storiche (oro LBMA e
    S&P di Shiller) sono MEDIE del mese, non chiusure. Il rendimento da media(t) a
    media(t+1) copre da meta' mese t a meta' mese t+1, quindi con lag=1 una strategia
    incasserebbe mezzo mese di movimento gia' avvenuto quando ha deciso: si comprerebbe
    il passato. Con lag=2 il segnale e il rendimento non si sovrappongono piu'.
    """
    m = max(1, ppy // 12)                       # periodi in un mese
    L12, L6, L3 = 12 * m, 6 * m, 3 * m
    lag = (2 if ppy <= 12 else 1) if lag is None else lag
    eom = (lambda w: w) if ppy <= 12 else monthly_decisions
    out = {}

    out['1. buy&hold S&P'] = {'-': const_w(px, 1.0)}
    out['2. mix statico, banda 5%'] = {f'{round(100*s)}/{round(100*(1-s))}': const_w(px, s)
                                       for s in (0.9, 0.8, 0.7, 0.6)}

    # momentum relativo: tutto su chi e' andato meglio
    for L, nm in ((L3, '3m'), (L6, '6m'), (L12, '12m')):
        r_sp, r_or = px.SP500.pct_change(L), px.ORO.pct_change(L)
        win = (r_sp >= r_or).astype(float)
        out.setdefault('3. momentum relativo', {})[nm] = eom(
            pd.DataFrame({'SP500': win, 'ORO': 1 - win}).shift(lag).fillna(0))

    # la strategia della domanda: S&P mentre sale, oro quando si rompe
    for L, nm in ((L6, 'mom 6m'), (L12, 'mom 12m')):
        up = (px.SP500.pct_change(L) > 0).astype(float)
        out.setdefault('4. S&P se sale, sennò oro', {})[nm] = eom(
            pd.DataFrame({'SP500': up, 'ORO': 1 - up}).shift(lag).fillna(0))
    ma = px.SP500 / px.SP500.rolling(10 * m).mean()
    out['4. S&P se sale, sennò oro']['MA10m'] = eom(pd.DataFrame(
        {'SP500': (ma >= 1).astype(float), 'ORO': (ma < 1).astype(float)}).shift(lag).fillna(0))

    # dual momentum: il migliore dei due, ma solo se batte la liquidita'
    for L, nm in ((L6, '6m'), (L12, '12m')):
        r_sp, r_or = px.SP500.pct_change(L), px.ORO.pct_change(L)
        r_cash = rf.rolling(L).sum()
        best_sp = (r_sp >= r_or) & (r_sp > r_cash)
        best_or = (r_or > r_sp) & (r_or > r_cash)
        out.setdefault('5. dual momentum', {})[nm] = eom(pd.DataFrame(
            {'SP500': best_sp.astype(float), 'ORO': best_or.astype(float)}).shift(lag).fillna(0))

    # risk parity elementare: peso inverso alla volatilita' a 12 mesi
    v_sp = px.SP500.pct_change().rolling(L12).std()
    v_or = px.ORO.pct_change().rolling(L12).std()
    k_sp = (1 / v_sp) / (1 / v_sp + 1 / v_or)
    out['6. risk parity (vol inversa)'] = {
        'banda 5%': eom(pd.DataFrame({'SP500': k_sp, 'ORO': 1 - k_sp}).shift(lag).fillna(0))}

    # L'unica strada che ha senso a priori: il mix diversificato ha Sharpe piu' alto ma
    # rende meno perche' rischia meno. Rialzando il rischio con la leva si vede se quello
    # Sharpe in piu' sopravvive al costo del denaro.
    out['7. mix 70/30 con leva'] = {f'{lev}x': const_w(px, 0.7) * lev
                                    for lev in (1.2, 1.3, 1.5)}
    return out


BANDED = ('2. mix statico', '6. risk parity', '7. mix 70/30 con leva')


def report(px, rf, ppy, label, expense=None, split=True):
    print('\n' + '=' * 108)
    print(f'{label}   {px.index[0].date()} -> {px.index[-1].date()}  '
          f'({len(px)} periodi, {len(px)/ppy:.1f} anni)')
    print('=' * 108)
    c = px.pct_change().corr().iloc[0, 1]
    print(f'Correlazione dei rendimenti S&P / oro sul campione: {c:+.3f}')

    segments = [('TUTTO', px.index)]
    if split:
        h = len(px) // 2
        segments += [('IS  (prima metà)', px.index[:h]), ('OOS (seconda metà)', px.index[h:])]

    for seg_name, idx in segments:
        sub = px.loc[idx] / px.loc[idx].iloc[0]
        print(f'\n--- {seg_name}: {idx[0].date()} -> {idx[-1].date()}')
        print(f"{'strategia':<32}{'par':<10}{'CAGR ante':>10}{'CAGR netto':>11}{'MDD':>8}"
              f"{'Sharpe':>8}{'% S&P':>7}{'% oro':>7}{'turn/an':>8}")
        print('-' * 101)
        base = None
        for fam, variants in strategies(px, rf, ppy).items():
            band = 0.05 if any(k in fam for k in BANDED) else 0.0
            for par, w in variants.items():
                m = evaluate_portfolio(sub, w.loc[idx], rf.loc[idx], ppy,
                                       expense=expense, band=band)
                if base is None: base = m
                flag = ''
                if m['cagr'] > base['cagr'] + 0.10:       flag += ' batte-S&P'
                if m['sharpe'] > base['sharpe'] + 0.02:   flag += ' Sharpe>S&P'
                print(f'{fam:<32}{par:<10}{m["cagr_ante"]:>9.2f}%{m["cagr"]:>10.2f}%'
                      f'{m["mdd"]:>7.1f}%{m["sharpe"]:>8.2f}{m["expo"]["SP500"]:>6.0f}%'
                      f'{m["expo"]["ORO"]:>6.0f}%{m["turn_yr"]:>8.2f}{flag}')


def decade_table(px, rf, ppy, expense=None):
    """Le stesse strategie decennio per decennio: e' qui che si vede la dipendenza dal regime."""
    print('\n' + '=' * 108)
    print('LO STESSO CONFRONTO, DECENNIO PER DECENNIO (CAGR netto)')
    print('=' * 108)
    picks = [('buy&hold S&P', '1. buy&hold S&P', '-'),
             ('mix 70/30', '2. mix statico, banda 5%', '70/30'),
             ('mom relativo 12m', '3. momentum relativo', '12m'),
             ('S&P se sale, sennò oro (12m)', '4. S&P se sale, sennò oro', 'mom 12m'),
             ('dual momentum 12m', '5. dual momentum', '12m')]
    strat = strategies(px, rf, ppy)
    decs = sorted({(y // 10) * 10 for y in px.index.year})
    print(f"{'strategia':<32}" + ''.join(f'{d}s'.rjust(9) for d in decs))
    print('-' * (32 + 9 * len(decs)))
    for nm, fam, par in picks:
        cells = []
        for d in decs:
            idx = px.index[(px.index.year >= d) & (px.index.year < d + 10)]
            if len(idx) < ppy * 3:
                cells.append('-'.rjust(9)); continue
            sub = px.loc[idx] / px.loc[idx].iloc[0]
            band = 0.05 if any(k in fam for k in BANDED) else 0.0
            m = evaluate_portfolio(sub, strat[fam][par].loc[idx], rf.loc[idx], ppy,
                                   expense=expense, band=band)
            cells.append(f'{m["cagr"]:>8.1f}%')
        print(f'{nm:<32}' + ''.join(cells))
    print('   decenni con meno di 3 anni di dati: esclusi.')


def main():
    px_m, rf_m = panel_monthly()
    report(px_m, rf_m, 12, 'CAMPIONE LUNGO — mensile, S&P total return (Shiller) e oro LBMA',
           expense=EXPENSE)
    decade_table(px_m, rf_m, 12, expense=EXPENSE)

    px_d, rf_d = panel_daily()
    report(px_d, rf_d, 252, 'CAMPIONE BREVE — giornaliero, SPY e GLD veri '
           '(spese di gestione già nei prezzi)')

    print('\n' + '=' * 108)
    print('COME LEGGERLO')
    print('=' * 108)
    print("""  - Il confronto che conta non e' contro il buy&hold: e' contro il MIX STATICO. Se una
    regola di momentum non batte un 70/30 ribilanciato, tutto il suo valore veniva dalla
    diversificazione, non dal segnale, e stai pagando tasse e commissioni per niente.
  - Guarda la colonna CAGR netto insieme al Sharpe: una strategia che rende meno con meta'
    del drawdown non e' peggiore, e' un'altra cosa. A parita' di rischio si confronta lo
    Sharpe, poi si sceglie il livello di esposizione.
  - La tabella per decenni e' il test vero: l'oro ha avuto vent'anni (1980-2000) in cui ha
    solo perso. Una strategia che campa sull'oro in quel periodo affonda, e nessuno ti
    garantisce che i prossimi vent'anni somiglino agli ultimi.
  - Non modellato: per un residente irlandese gli ETF UCITS ad accumulazione hanno exit tax
    41% con deemed disposal a 8 anni, che cambia i numeri assoluti. Il confronto relativo
    fra le strategie resta valido, il livello no.""")


if __name__ == '__main__':
    main()

"""Motore fiscale irlandese e simulatore di PAC.

Tre regimi, che differiscono in modo sostanziale:

  CGT_SHARES  azioni/CFD detenute direttamente. 33% su ogni posizione chiusa in
              utile, minusvalenze compensabili nell'anno e riportabili senza
              limite, esenzione personale di 1.270 EUR l'anno (non riportabile).
              I dividendi esteri sono tassati ogni anno al ~52%.

  ETF_UCITS   fondi UCITS. Exit tax 41% fino al 2025 e 38% dal 2026, dovuta alla
              vendita E al deemed disposal all'ottavo anniversario di OGNI lotto.
              Nessuna compensazione delle perdite fra lotti o fra anni. La tassa
              del deemed disposal viene pagata liquidando quote (l'alternativa,
              pagarla con denaro esterno, migliorerebbe il risultato e non
              sarebbe confrontabile con gli altri regimi).

  TRADING_52  stesso meccanismo di CGT_SHARES ma aliquota 52%: e' lo scenario di
              riqualificazione come attivita' commerciale, senza esenzione e
              senza il trattamento CGT delle minusvalenze.

Convenzione: le imposte sono SEMPRE pagate dal portafoglio, mai da denaro
esterno. Cosi' l'IRR confronta strategie a parita' di flussi di cassa versati.
"""
from dataclasses import dataclass, field
import numpy as np
import pandas as pd

from config import (CGT_RATE, CGT_EXEMPT_ANNUAL, ETF_EXIT_TAX, ETF_EXIT_TAX_PRE, DIRT_RATE,
                    ETF_EXIT_TAX_SWITCH, DEEMED_DISPOSAL_Y, DIV_RATE_FOREIGN,
                    TRADING_INCOME_RATE, COST_ROUND_TRIP, MONTHLY_CONTRIB)

CGT_SHARES, ETF_UCITS, TRADING_52 = "CGT_SHARES", "ETF_UCITS", "TRADING_52"


# ---------------------------------------------------------------- lotti ETF
@dataclass
class Lot:
    """Un acquisto ETF: quote, costo, e l'orologio degli 8 anni."""
    units: float
    basis: float          # costo fiscale totale del lotto, aggiornato dal deemed disposal
    bought: pd.Timestamp
    next_dd: pd.Timestamp  # prossimo deemed disposal


def _exit_rate(when):
    return ETF_EXIT_TAX if when.year >= ETF_EXIT_TAX_SWITCH else ETF_EXIT_TAX_PRE


# ---------------------------------------------------------------- risultato
@dataclass
class PacResult:
    dates: pd.DatetimeIndex
    value: pd.Series           # valore del portafoglio, netto delle imposte gia' pagate
    unit_nav: pd.Series        # NAV di una quota: serve per drawdown e Sharpe
    contributions: float
    taxes: float
    costs: float
    irr_annual: float
    max_dd: float
    sharpe: float
    trades_per_year: float
    n_trades: int
    final_net: float
    detail: dict = field(default_factory=dict)


def _irr(cashflows, periods_per_year=12):
    """IRR annualizzata di una serie di flussi periodici (segno: negativo = versato)."""
    cf = np.asarray(cashflows, dtype=float)
    if not (np.any(cf > 0) and np.any(cf < 0)):
        return np.nan
    k = np.arange(len(cf))

    def npv(r):
        # in log-spazio: (1+r)^k esplode in fretta su 400+ periodi
        return float(np.sum(cf * np.exp(-k * np.log1p(r))))

    # flussi convenzionali (versamenti negativi, un solo incasso finale positivo):
    # il VAN e' monotono decrescente in r, quindi la bisezione ha radice unica.
    lo, hi = -0.5, 1.0
    f_lo, f_hi = npv(lo), npv(hi)
    tries = 0
    while f_lo < 0 and tries < 40:      # allarga verso il basso se serve
        lo = (lo - 1.0) / 2 if lo > -0.999 else lo
        f_lo = npv(lo); tries += 1
    while f_hi > 0 and tries < 80:      # e verso l'alto
        hi *= 2; f_hi = npv(hi); tries += 1
    if f_lo * f_hi > 0 or not np.isfinite(f_lo) or not np.isfinite(f_hi):
        return np.nan
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        f_mid = npv(mid)
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    r_period = 0.5 * (lo + hi)
    return (1 + r_period) ** periods_per_year - 1


def first_of_month(idx):
    """Maschera booleana: primo periodo disponibile di ogni mese civile."""
    s = pd.Series(idx, index=idx)
    key = s.dt.to_period("M")
    return pd.Series(~key.duplicated(), index=idx)


def _xirr(dates, amounts):
    """IRR annua su flussi datati (act/365). Regge frequenze miste."""
    d = np.asarray([(t - dates[0]).days for t in dates], dtype=float) / 365.0
    cf = np.asarray(amounts, dtype=float)
    if not (np.any(cf > 0) and np.any(cf < 0)):
        return np.nan

    def npv(r):
        return float(np.sum(cf * np.exp(-d * np.log1p(r))))

    lo, hi = -0.9, 5.0
    f_lo, f_hi = npv(lo), npv(hi)
    if not (np.isfinite(f_lo) and np.isfinite(f_hi)) or f_lo * f_hi > 0:
        return np.nan
    for _ in range(300):
        mid = 0.5 * (lo + hi)
        f_mid = npv(mid)
        if f_lo * f_mid <= 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return 0.5 * (lo + hi)


def simulate_pac(gross_ret, regime, in_market=None, div_yield=None,
                 contrib=MONTHLY_CONTRIB, rf=None, cost_rt=COST_ROUND_TRIP,
                 turnover=None, periods_per_year=12, contrib_on=None,
                 realize_frac=None):
    """Simula un PAC su una serie di rendimenti periodici.

    gross_ret   rendimento lordo del veicolo nel periodo (gia' al netto dei costi
                di finanziamento della leva, se prevista), AL LORDO di imposte.
                Per le azioni dirette deve essere il rendimento di solo PREZZO:
                il dividendo entra separatamente da div_yield, perche' e'
                tassato ogni anno e non al realizzo.
    regime      CGT_SHARES | ETF_UCITS | TRADING_52
    in_market   serie 0/1: la strategia e' investita nel periodo. Un passaggio
                1->0 e' un realizzo. Se None, si assume sempre investito
                (buy & hold: unico realizzo alla fine).
    div_yield   quota di rendimento da dividendo del periodo (solo azioni dirette).
    turnover    serie di turnover per periodo (0-1) per imputare i costi quando la
                strategia ruota il portafoglio senza chiudere del tutto la posizione.
    realize_frac serie 0-1: quota di portafoglio venduta nel periodo, che REALIZZA
                la plusvalenza corrispondente anche senza uscire dal mercato. Serve
                al gruppo D, dove il ribilanciamento e' l'evento tassabile. Uso il
                costo medio invece del FIFO: il fisco irlandese applica il FIFO,
                che su un PAC crescente anticipa l'imposta, quindi questa ipotesi
                e' leggermente FAVOREVOLE al ribilanciamento.
    """
    idx = gross_ret.index
    n = len(idx)
    if in_market is None:
        in_market = pd.Series(1.0, index=idx)
    in_market = in_market.reindex(idx).fillna(0.0)
    if div_yield is None:
        div_yield = pd.Series(0.0, index=idx)
    div_yield = div_yield.reindex(idx).fillna(0.0)
    if turnover is None:
        turnover = in_market.diff().abs().fillna(in_market.abs())
    turnover = turnover.reindex(idx).fillna(0.0)
    if contrib_on is None:
        contrib_on = (first_of_month(idx) if periods_per_year > 12
                      else pd.Series(True, index=idx))
    contrib_on = contrib_on.reindex(idx).fillna(False).astype(bool)
    if realize_frac is not None:
        realize_frac = realize_frac.reindex(idx).fillna(0.0).clip(0.0, 1.0)
    if rf is not None:
        rf = rf.reindex(idx).ffill().fillna(0.0)   # allineato: sotto uso .iloc[i]

    etf = regime == ETF_UCITS
    rate = TRADING_INCOME_RATE if regime == TRADING_52 else CGT_RATE
    exempt = CGT_EXEMPT_ANNUAL if regime == CGT_SHARES else 0.0

    # stato
    lots = []                     # solo regime ETF
    units = 0.0                   # quote possedute (regimi non-ETF: quote sintetiche)
    nav = 100.0                   # NAV di una quota
    basis = 0.0                   # costo fiscale complessivo (regimi non-ETF)
    in_pos = False                # la strategia e' attualmente investita
    carry_loss = 0.0              # minusvalenze riportate
    year_gain = 0.0               # plusvalenze nette realizzate nell'anno corrente
    cur_year = idx[0].year
    taxes = costs = 0.0
    n_trades = 0
    values, navs, cashflows = [], [], []

    def pay_from_portfolio(amount):
        """Preleva imposte liquidando quote al NAV corrente.

        Le quote vendute escono PRO RATA da tutti i lotti: se si riducono solo
        le `units` globali e non i lotti, la somma dei lotti resta gonfia e ogni
        deemed disposal successivo calcola la plusvalenza su quote che non
        esistono piu'. Su 8 anni l'errore e' tollerabile, su 57 anni e sette
        cicli di deemed disposal azzera il portafoglio.
        """
        nonlocal units
        if amount <= 0 or nav <= 0 or units <= 0:
            return 0.0
        sold = min(units, amount / nav)
        frac = sold / units
        units -= sold
        for lot in lots:
            lot.basis -= lot.basis * frac
            lot.units -= lot.units * frac
        return sold * nav

    for i, t in enumerate(idx):
        r = float(gross_ret.iloc[i])
        pos = float(in_market.iloc[i])

        # --- fine anno fiscale: liquido il conto imposte dell'anno appena chiuso
        if t.year != cur_year:
            if not etf:
                taxable = max(0.0, year_gain - carry_loss)
                used = min(carry_loss, max(0.0, year_gain))
                carry_loss -= used
                if year_gain < 0:
                    carry_loss += -year_gain
                taxable = max(0.0, taxable - exempt)
                due = taxable * rate
                taxes += pay_from_portfolio(due)
            year_gain = 0.0
            cur_year = t.year

        # --- versamento del PAC (mensile, anche su serie giornaliere)
        if contrib_on.iloc[i]:
            buy_cost = contrib * (cost_rt / 2.0)
            costs += buy_cost
            invested = contrib - buy_cost
            new_units = invested / nav if nav > 0 else 0.0
            units += new_units
            cashflows.append((t, -contrib))
            if etf:
                lots.append(Lot(units=new_units, basis=invested, bought=t,
                                next_dd=t + pd.DateOffset(years=DEEMED_DISPOSAL_Y)))
            else:
                basis += invested

        # --- rendimento del periodo. La parte NON investita non sta ferma: e'
        #     liquidita' che rende il tasso risk-free al netto della DIRT 33%.
        #     Senza questo, una strategia che sta fuori dal mercato l'80% del
        #     tempo verrebbe penalizzata per un'ipotesi, non per i suoi meriti.
        cash_r = 0.0
        if rf is not None and pos < 1.0:
            rf_i = float(rf.iloc[i]) if i < len(rf) else 0.0
            cash_r = (1.0 - pos) * rf_i * (1.0 - DIRT_RATE)
        eff_r = pos * r + cash_r
        # costo di transazione sul turnover del periodo
        tc = float(turnover.iloc[i]) * (cost_rt / 2.0)
        costs += tc * units * nav
        nav *= (1.0 + eff_r - tc)

        # --- dividendi (solo azioni dirette): incassati e tassati ogni anno al 52%
        d = float(div_yield.iloc[i]) * pos
        if d != 0.0:
            gross_div = units * nav * d
            div_tax = gross_div * DIV_RATE_FOREIGN
            taxes += div_tax
            net_div = gross_div - div_tax
            # il dividendo netto viene reinvestito: aumenta il costo fiscale
            if nav > 0:
                units += net_div / nav
            if not etf:
                basis += net_div

        # --- realizzo da ribilanciamento: vendo una quota del portafoglio senza
        #     uscire dal mercato. La plusvalenza realizzata e' proporzionale.
        rf_i = float(realize_frac.iloc[i]) if realize_frac is not None else 0.0
        if rf_i > 0 and not etf:
            mv = units * nav
            unreal = mv - basis
            realized = unreal * rf_i
            year_gain += realized
            basis += realized          # la parte venduta e riacquistata alza il costo
            n_trades += 1
        elif rf_i > 0 and etf:
            # un ETF UCITS non realizza nulla ribilanciando AL SUO INTERNO: il
            # ribilanciamento avviene dentro il fondo, fuori dal perimetro fiscale.
            pass

        # --- realizzo: la strategia esce dalla posizione.
        # La plusvalenza si misura contro il COSTO FISCALE cumulato (basis), non
        # contro il valore del portafoglio al momento dell'ingresso: fra i due
        # istanti sono arrivati altri versamenti, che sono capitale e non utile.
        # Misurarla contro il valore d'ingresso tassa anche i versamenti.
        if not etf and in_pos and pos == 0:
            cur_value = units * nav
            year_gain += cur_value - basis
            basis = cur_value      # realizzato tutto: il nuovo costo e' il valore corrente
            n_trades += 1
            in_pos = False
        elif not etf and pos > 0:
            in_pos = True

        # --- deemed disposal ETF: ogni lotto al suo ottavo anniversario
        if etf:
            for lot in lots:
                if lot.next_dd <= t and lot.units > 0:
                    mv = lot.units * nav
                    gain = mv - lot.basis
                    if gain > 0:
                        due = gain * _exit_rate(t)
                        taxes += pay_from_portfolio(due)
                        # la tassa pagata si somma al costo: non si tassa due volte
                        lot.basis += gain
                    lot.next_dd = lot.next_dd + pd.DateOffset(years=DEEMED_DISPOSAL_Y)

        values.append(units * nav)
        navs.append(nav)

    # ------------------------------------------------ liquidazione finale
    final_value = units * nav
    if etf:
        # ogni lotto paga exit tax sulla plusvalenza residua; nessuna compensazione
        tot_units = sum(l.units for l in lots)
        scale = (units / tot_units) if tot_units > 0 else 0.0
        due = 0.0
        for lot in lots:
            u = lot.units * scale
            mv = u * nav
            b = lot.basis * (u / lot.units) if lot.units > 0 else 0.0
            gain = mv - b
            if gain > 0:
                due += gain * _exit_rate(idx[-1])
        taxes += due
        final_value -= due
        n_trades += 1
    else:
        cur_value = final_value
        year_gain += cur_value - basis     # base = versamenti + utili gia' tassati
        n_trades += 1
        taxable = max(0.0, year_gain - carry_loss)
        taxable = max(0.0, taxable - exempt)
        due = taxable * rate
        taxes += due
        final_value -= due

    cashflows.append((idx[-1], final_value))
    cf_dates = [d for d, _ in cashflows]
    cf_amts = [a for _, a in cashflows]
    n_contrib = sum(1 for a in cf_amts if a < 0)

    nav_s = pd.Series(navs, index=idx)
    val_s = pd.Series(values, index=idx)
    dd = float((nav_s / nav_s.cummax() - 1).min())
    net_r = nav_s.pct_change().dropna()
    if rf is not None:
        ex = net_r - rf.reindex(net_r.index).fillna(0.0)
    else:
        ex = net_r
    sharpe = float(ex.mean() / ex.std() * np.sqrt(periods_per_year)) if ex.std() > 0 else np.nan
    yrs = n / periods_per_year

    return PacResult(
        dates=idx, value=val_s, unit_nav=nav_s,
        contributions=contrib * n_contrib, taxes=taxes, costs=costs,
        irr_annual=_xirr(cf_dates, cf_amts) * 100,
        max_dd=dd * 100, sharpe=sharpe,
        trades_per_year=n_trades / yrs, n_trades=n_trades,
        final_net=final_value,
    )

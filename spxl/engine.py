"""
MOTORE DI BACKTEST — SPXL vs buy&hold S&P 500
=============================================

Tre pezzi, tenuti separati apposta:

  1. DATI      costruzione del pannello giornaliero (indice total return, tassi,
               volatilita' implicita) e SINTESI della serie SPXL prima del 2008.
  2. COSTI     spread, commissioni, expense ratio, costo di finanziamento della leva.
  3. FISCO     imposta sulle plusvalenze REALIZZATE, con compensazione perdite e
               pagamento a fine anno. E' la voce che uccide la maggior parte delle
               strategie attive e va modellata sul serio, non con una percentuale
               applicata al risultato finale.

Perche' sintetizzare SPXL invece di usare solo lo storico reale?
  SPXL esiste dal novembre 2008. Diciassette anni contengono UN solo mercato orso
  profondo (2022) piu' un crash lampo (2020): non bastano per distinguere un edge
  da una coincidenza. La sintesi ricostruisce il comportamento del fondo dal 1928
  usando la meccanica dichiarata (3x il rendimento GIORNALIERO dell'indice, meno
  finanziamento sul nozionale preso a prestito, meno spese) e viene poi CALIBRATA e
  VERIFICATA contro il fondo vero sul periodo in cui entrambi esistono.
  Se la sintesi non replica SPXL 2008-2026, non e' utilizzabile e il codice lo dice.
"""
from __future__ import annotations
import os
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
TRADING_DAYS = 252


# ==========================================================================
# 1. DATI
# ==========================================================================
def _read(name, date_col="Date"):
    p = os.path.join(DATA, f"{name}.csv")
    if not os.path.exists(p):
        return None
    df = pd.read_csv(p, parse_dates=[date_col]).set_index(date_col).sort_index()
    return df[~df.index.duplicated(keep="last")]


def load_raw():
    """Tutti i csv scaricati; quelli mancanti semplicemente non compaiono."""
    names = ["gspc", "divyield", "sp500tr", "spy", "spxl", "spxs", "sh", "upro",
             "vix", "vix3m", "bil", "dff", "dtb3", "dgs10"]
    out = {}
    for n in names:
        df = _read(n)
        if df is not None:
            out[n] = df
    return out


def build_index_total_return(raw):
    """
    Rendimenti TOTAL RETURN dell'S&P 500, la serie piu' lunga ottenibile.

    Ordine di preferenza:
      1. ^SP500TR, l'indice total return ufficiale (dal 1988), dove disponibile
      2. rendimento di prezzo + dividend yield del dataset Shiller (dal 1871)

    Il punto 2 spalma uniformemente sui giorni del mese un dividendo che nella
    realta' arriva a scatti trimestrali. Sul singolo giorno e' sbagliato, sul
    rendimento composto di un anno no, ed e' cio' che serve qui: i segnali si
    calcolano sui PREZZI, il total return entra solo nel conteggio del
    patrimonio. L'alternativa - ignorare i dividendi - toglierebbe al buy&hold
    tre o quattro punti l'anno nei decenni vecchi e falserebbe ogni confronto.
    """
    px = raw["gspc"]["Close"].astype(float)
    r_px = px.pct_change()

    if "divyield" in raw:
        y = raw["divyield"]["yield"].astype(float)
        yld = y.reindex(r_px.index.union(y.index)).ffill().reindex(r_px.index).ffill().bfill()
        if not (yld > 0).all():
            raise ValueError("dividend yield nullo o mancante: la serie non e' utilizzabile")
    else:
        # nessun dato sui dividendi: 2.5% e' l'ordine di grandezza del secolo,
        # ma e' un ripiego e va saputo
        yld = pd.Series(0.025, index=r_px.index)

    tr = r_px + yld / TRADING_DAYS

    if "sp500tr" in raw:
        off = raw["sp500tr"]["Close"].astype(float).pct_change()
        comune = tr.index.intersection(off.index)
        tr.loc[comune] = off.loc[comune]

    return pd.DataFrame({"px": px, "r_px": r_px, "r_tr": tr, "yld": yld}).dropna(subset=["r_px"])


def build_rates(raw, index):
    """
    Tasso a breve giornaliero = costo del denaro preso a prestito per la leva.

    DTB3 (T-bill 3 mesi) dove c'e', DFF (fed funds) come riempitivo, e prima del
    1954 il tasso non esiste su FRED: si usa una stima piatta d'epoca. Il forward
    fill copre weekend e festivi.
    """
    rf = pd.Series(np.nan, index=index)
    for key in ("dtb3", "dff"):
        if key in raw:
            s = raw[key].iloc[:, 0].astype(float) / 100.0
            rf = rf.fillna(s.reindex(index).ffill())
    # pre-1954: nessun dato FRED. 1% e' l'ordine di grandezza dei T-bill 1930-50.
    rf = rf.fillna(0.01).clip(lower=0.0)
    return rf


# ==========================================================================
# 2. SINTESI LETF
# ==========================================================================
#
# Un ETF a leva giornaliera ha una meccanica dichiarata e semplice:
#
#     r_fondo = L * r_indice  +  alpha  +  beta * r_breve
#
# dove alpha raccoglie cio' che si paga comunque (expense ratio, spread sugli
# swap) e beta * r_breve il costo o il ricavo del denaro. Per un 3x lungo la
# teoria dice beta ~ -2: si e' esposti per 3 avendo capitale 1, quindi si
# finanziano 2 unita'. Per un -3x dice beta ~ +4: chi e' corto per 3 e ha
# capitale 1 tiene a interesse 4 unita' di cassa.
#
# Invece di dare per buoni i numeri di prospetto, alpha e beta si STIMANO sul
# fondo vero con una regressione, e poi si verifica che beta somigli alla
# teoria. Se somiglia, la meccanica e' quella che si pensava e si puo'
# estrapolare indietro nel tempo con qualche fiducia. Se non somiglia, il
# modello e' sbagliato e va detto prima di costruirci sopra ottant'anni di
# storia inventata.

class LETFSpec:
    """Parametri di prospetto: servono da prior e da ripiego quando non c'e'
    abbastanza storia reale per stimare qualcosa."""

    def __init__(self, name, leva, er, spread):
        self.name, self.leva, self.er, self.spread = name, leva, er, spread

    def __repr__(self):
        return f"LETFSpec({self.name}, L={self.leva}, er={self.er:.4f}, spr={self.spread:.4f})"


SPEC_SPXL = LETFSpec("SPXL", +3.0, 0.0091, 0.0045)
SPEC_SPXS = LETFSpec("SPXS", -3.0, 0.0100, 0.0045)
SPEC_SH   = LETFSpec("SH",   -1.0, 0.0089, 0.0045)


def beta_teorico(leva):
    """Quante unita' di cassa si finanziano (segno negativo) o si incassano."""
    return -(leva - 1.0) if leva > 0 else (abs(leva) + 1.0)


class LETFModel:
    """
    Modello lineare del fondo a leva: r = L*r_indice + alpha + beta*rf/252.

    La moltiplicazione e' sul rendimento GIORNALIERO ed e' da li' che nasce il
    volatility drag: 3x al giorno non fa 3x nel lungo periodo, fa 3x meno circa
    L*(L-1)/2 * sigma^2 l'anno di erosione da varianza. Nessun parametro di
    questo modello lo cattura, e non serve: emerge da solo componendo i giorni.
    """

    def __init__(self, name, leva, alpha_daily, beta, origine="stimato", diag=None):
        self.name = name
        self.leva = leva
        self.alpha_daily = float(alpha_daily)
        self.beta = float(beta)
        self.origine = origine
        self.diag = diag or {}

    @classmethod
    def da_prospetto(cls, spec: LETFSpec):
        borrow = abs(spec.leva) - 1.0
        alpha = -(spec.er + borrow * spec.spread) / TRADING_DAYS
        return cls(spec.name, spec.leva, alpha, beta_teorico(spec.leva), "prospetto")

    def returns(self, r_index, rf):
        return self.leva * r_index + self.alpha_daily + self.beta * rf / TRADING_DAYS

    def __repr__(self):
        return (f"LETFModel({self.name} L={self.leva:+.0f} "
                f"alpha={self.alpha_daily*TRADING_DAYS:+.2%}/anno "
                f"beta={self.beta:+.2f} [{self.origine}])")


def _ols(y, X):
    """Minimi quadrati senza scipy. X gia' comprensivo della colonna di uno."""
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    ss_tot = ((y - y.mean()) ** 2).sum()
    r2 = 1 - (resid ** 2).sum() / ss_tot if ss_tot > 0 else np.nan
    return coef, resid, r2


def fit_letf(r_index, rf, r_real, leva, name="LETF", vincola_beta=False):
    """
    Stima alpha e beta sul fondo reale.

    vincola_beta  se True beta e' bloccato al valore teorico e si stima solo
                  alpha. Utile quando la storia reale e' corta: con pochi anni
                  e tassi quasi fermi, alpha e beta sono quasi collineari e la
                  regressione libera puo' dare un beta assurdo compensato da un
                  alpha altrettanto assurdo.
    """
    comune = r_index.index.intersection(r_real.dropna().index)
    ri = r_index.loc[comune].values
    rr = r_real.loc[comune].values
    rc = (rf.loc[comune] / TRADING_DAYS).values
    y = rr - leva * ri

    if vincola_beta:
        b = beta_teorico(leva)
        a = float((y - b * rc).mean())
        resid = y - a - b * rc
        r2 = np.nan
    else:
        coef, resid, r2 = _ols(y, np.column_stack([np.ones(len(y)), rc]))
        a, b = float(coef[0]), float(coef[1])

    diag = dict(
        giorni=len(comune), da=str(comune[0].date()), a_data=str(comune[-1].date()),
        alpha_ann=a * TRADING_DAYS, beta=b, beta_teorico=beta_teorico(leva),
        r2_residuo=r2,
        te_ann=float(np.std(resid) * np.sqrt(TRADING_DAYS)),
        vincolato=vincola_beta,
    )
    return LETFModel(name, leva, a, b, "vincolato" if vincola_beta else "stimato", diag)


def valida_modello(model: LETFModel, r_index, rf, r_real, taglio=None):
    """
    Quanto bene il modello replica il fondo vero.

    Se taglio e' una data, il modello viene ristimato SOLO sui dati precedenti e
    verificato su quelli successivi: e' la stessa disciplina che si pretende
    dalle strategie, applicata al modello che genera i dati su cui le strategie
    verranno testate. Un modello calibrato e verificato sullo stesso periodo
    direbbe soltanto che i minimi quadrati funzionano.
    """
    comune = r_index.index.intersection(r_real.dropna().index)
    if taglio is not None:
        t = pd.Timestamp(taglio)
        dentro = comune[comune < t]
        fuori = comune[comune >= t]
        if len(dentro) < 250 or len(fuori) < 250:
            return None
        m = fit_letf(r_index.loc[dentro], rf.loc[dentro], r_real.loc[dentro],
                     model.leva, model.name, model.origine == "vincolato")
        comune = fuori
    else:
        m = model

    syn = m.returns(r_index.loc[comune], rf.loc[comune])
    real = r_real.loc[comune]
    d = syn - real
    yrs = len(comune) / TRADING_DAYS
    return dict(
        periodo=f"{comune[0].date()} -> {comune[-1].date()}", giorni=len(comune),
        corr=float(np.corrcoef(syn, real)[0, 1]),
        te_ann=float(d.std() * np.sqrt(TRADING_DAYS)),
        drift_ann=float(d.mean() * TRADING_DAYS),
        cagr_syn=float((1 + syn).prod() ** (1 / yrs) - 1),
        cagr_real=float((1 + real).prod() ** (1 / yrs) - 1),
    )


# ==========================================================================
# 3. COSTI
# ==========================================================================
# Costo di UN LATO dell'operazione, in frazione del nozionale scambiato.
# Include mezzo spread denaro-lettera piu' slippage; la commissione di un broker
# retail moderno su questi volumi e' zero o quasi, ma teniamo un margine.
COST_ONE_WAY = {
    "SPXL": 0.0005,   # 5 bp: spread reale ~1-3 bp, il resto e' margine di sicurezza
    "SPXS": 0.0008,   # meno liquido
    "SH":   0.0006,
    "SPY":  0.0002,
    "CASH": 0.0,
}


# ==========================================================================
# 4. FISCO
# ==========================================================================
class TaxRegime:
    """
    Imposta sulle plusvalenze REALIZZATE.

    Il dettaglio che cambia tutto: il buy&hold realizza una volta sola, alla fine.
    Una strategia attiva realizza a ogni uscita e paga subito, perdendo per sempre
    il rendimento composto su quei soldi. Con aliquota 33% e trenta rotazioni
    l'anno, il freno e' dell'ordine di punti percentuali annui: nessuna strategia
    puo' essere valutata ignorandolo.

      rate         aliquota sulle plusvalenze
      div_rate     aliquota su dividendi e distribuzioni
      loss_offset  se le minusvalenze compensano le plusvalenze
      carry_years  anni di riporto delle minus non compensate (0 = nessun riporto)
      exemption    franchigia annua in valuta
      pay_lag_days quando esce la cassa rispetto alla fine dell'anno fiscale
    """
    def __init__(self, name, rate, div_rate=None, loss_offset=True,
                 carry_years=99, exemption=0.0, note=""):
        self.name = name
        self.rate = rate
        self.div_rate = rate if div_rate is None else div_rate
        self.loss_offset = loss_offset
        self.carry_years = carry_years
        self.exemption = exemption
        self.note = note

    def __repr__(self):
        return f"TaxRegime({self.name}, {self.rate:.0%})"


REGIMES = {
    # Irlanda, ETF statunitense trattato come azione ai fini CGT (posizione Revenue
    # per i fondi USA costituiti in forma societaria). Franchigia 1.270 EUR/anno.
    "IE_CGT":  TaxRegime("IE_CGT", 0.33, div_rate=0.41, loss_offset=True,
                         exemption=1270.0,
                         note="CGT 33% su realizzo, minus compensabili e riportabili"),
    # Irlanda, regime fondi: 41% con disposizione presunta a 8 anni e NESSUNA
    # compensazione delle perdite. Peggiore in quasi ogni scenario.
    "IE_FUND": TaxRegime("IE_FUND", 0.41, div_rate=0.41, loss_offset=False,
                         carry_years=0,
                         note="exit tax 41%, perdite non compensabili"),
    # Italia, ETF armonizzato: 26% ma con l'asimmetria che i proventi sono
    # redditi di capitale e le minus redditi diversi: le perdite NON abbattono
    # le plusvalenze da ETF. SPXL non e' armonizzato -> IRPEF marginale.
    "IT_26":   TaxRegime("IT_26", 0.26, div_rate=0.26, loss_offset=False,
                         carry_years=0,
                         note="26%, minus da ETF non compensabili con plus da ETF"),
    "IT_IRPEF":TaxRegime("IT_IRPEF", 0.43, div_rate=0.43, loss_offset=False,
                         carry_years=0,
                         note="ETF non armonizzato: tassazione a IRPEF marginale"),
    # Stati Uniti, conto tassabile: aliquota breve termine sulle posizioni < 1 anno.
    # Praticamente tutte le strategie qui sono a breve termine.
    "US_ST":   TaxRegime("US_ST", 0.408, div_rate=0.238, loss_offset=True,
                         carry_years=99,
                         note="37% + 3.8% NIIT su plus a breve termine"),
    # Conto esente (pensione, PEA, ISA...). Serve come limite superiore teorico.
    "NONE":    TaxRegime("NONE", 0.0, div_rate=0.0, note="nessuna imposta"),
}


class TaxBook:
    """
    Registro fiscale con contabilita' per anno solare.

    Accumula plus e minus realizzate durante l'anno, le compensa se il regime lo
    consente, applica la franchigia, e a fine anno preleva l'imposta dall'equity.
    Il prelievo e' cassa che esce davvero: entra nel drawdown, non e' un asterisco.
    """
    def __init__(self, regime: TaxRegime):
        self.r = regime
        self.gains = 0.0      # plusvalenze realizzate nell'anno corrente
        self.losses = 0.0     # minusvalenze (positive) realizzate nell'anno
        self.carry = 0.0      # minus riportate dagli anni precedenti
        self.paid = 0.0       # imposta totale versata
        self.year = None

    def realize(self, pnl):
        if pnl >= 0:
            self.gains += pnl
        else:
            self.losses += -pnl

    def settle(self):
        """Chiude l'anno fiscale e restituisce l'imposta dovuta."""
        if self.r.rate == 0:
            self.gains = self.losses = 0.0
            return 0.0
        if self.r.loss_offset:
            net = self.gains - self.losses - self.carry
            if net < 0:
                self.carry = -net if self.r.carry_years > 0 else 0.0
                net = 0.0
            else:
                self.carry = 0.0
        else:
            # senza compensazione si paga sulle plus lorde e le minus sono perse
            net = self.gains
            self.carry = 0.0
        taxable = max(0.0, net - self.r.exemption)
        tax = taxable * self.r.rate
        self.gains = self.losses = 0.0
        self.paid += tax
        return tax


# ==========================================================================
# 5. SIMULATORE
# ==========================================================================
class Instrument:
    """
    Uno strumento negoziabile.

      r_tot  rendimento totale giornaliero (prezzo + distribuzioni reinvestite)
      r_div  quota di r_tot che arriva come distribuzione tassabile subito.
             Per gli ETF a leva e' quasi zero; per SPY e' il dividendo, che in
             un conto tassabile si paga OGNI ANNO anche se non vendi mai.
             Ignorarlo regalerebbe al buy&hold un vantaggio che non ha.
      cost   costo di un lato in frazione del nozionale
    """
    __slots__ = ("name", "r_tot", "r_div", "cost")

    def __init__(self, name, r_tot, r_div=None, cost=None):
        self.name = name
        self.r_tot = np.nan_to_num(np.asarray(r_tot, dtype=float))
        self.r_div = (np.zeros_like(self.r_tot) if r_div is None
                      else np.nan_to_num(np.asarray(r_div, dtype=float)))
        self.cost = COST_ONE_WAY.get(name, 0.0005) if cost is None else cost


def simulate(dates, instruments, weights, regime: TaxRegime, cash_rate=None,
             exec_lag=1, capital=100_000.0, min_trade=0.002, rebal_days=None):
    """
    Esegue la strategia giorno per giorno. Restituisce il patrimonio NETTO di
    costi di transazione, costo della leva (gia' dentro i rendimenti LETF) e
    imposte effettivamente versate.

    weights   matrice (giorni x strumenti) di pesi OBIETTIVO calcolati con i dati
              fino alla CHIUSURA del giorno t. Con exec_lag=1 la posizione parte
              il giorno t+1: e' l'unica cosa che separa un backtest da una
              profezia. La quota non investita resta liquida e rende il tasso a
              breve.
    min_trade ribilanciamenti sotto questa soglia (in frazione del patrimonio)
              vengono ignorati. Serve a non pagare costi per aggiustamenti da
              mezzo punto base che nella realta' nessuno esegue.
    rebal_days maschera booleana dei giorni in cui e' permesso negoziare. Serve
              a distinguere la frequenza di RIBILANCIAMENTO dalla frequenza del
              SEGNALE: con pesi obiettivo costanti il portafoglio deriva ogni
              giorno, e riportarlo all'obiettivo tutti i giorni o una volta
              l'anno da' risultati diversi sia di rendimento sia di imposte.
              None significa: ogni volta che la deriva supera min_trade.

    Contabilita' fiscale: costo medio ponderato per strumento. Su strategie che
    entrano ed escono per intero coincide con FIFO e LIFO; la differenza
    emergerebbe solo con ingressi parziali ripetuti sullo stesso titolo.
    """
    n_days, n_inst = weights.shape
    R = np.column_stack([ins.r_tot for ins in instruments])
    D = np.column_stack([ins.r_div for ins in instruments])
    C = np.array([ins.cost for ins in instruments])

    # il segnale del giorno t comanda la posizione del giorno t+exec_lag
    if exec_lag > 0:
        W = np.vstack([np.zeros((exec_lag, n_inst)), weights[:-exec_lag]])
    else:
        W = weights.copy()
    W = np.nan_to_num(W)

    cash_daily = (np.zeros(n_days) if cash_rate is None
                  else np.asarray(cash_rate, dtype=float) / TRADING_DAYS)

    book = TaxBook(regime)
    income_year = 0.0                      # dividendi e interessi dell'anno in corso
    cash, pos, basis = capital, np.zeros(n_inst), np.zeros(n_inst)

    equity  = np.empty(n_days)
    exposure = np.empty(n_days)
    turnover = np.zeros(n_days)
    tax_flow = np.zeros(n_days)
    years = pd.DatetimeIndex(dates).year
    n_trades = 0

    for t in range(n_days):
        rt, dt_ = R[t], D[t]

        # ---- 1. il mercato muove le posizioni gia' aperte
        div = pos * dt_                    # parte distribuita, gia' reinvestita in r_tot
        pos = pos * (1.0 + rt)
        basis += div                       # reinvestire alza il costo fiscale
        interest = cash * cash_daily[t]
        cash += interest
        income_year += float(div.sum()) + max(interest, 0.0)
        nav = pos.sum() + cash

        # ---- 2. ribilanciamento verso i pesi obiettivo
        target = W[t] * nav
        delta = target - pos
        permesso = True if rebal_days is None else bool(rebal_days[t])
        # un cambio di segnale si esegue comunque: la maschera limita il
        # ribilanciamento verso un obiettivo fermo, non l'obbedienza al segnale
        if t > 0 and np.abs(W[t] - W[t - 1]).sum() > 1e-9:
            permesso = True
        if permesso and np.abs(delta).sum() / max(nav, 1e-12) > min_trade:
            for i in np.nonzero(delta < 0)[0]:
                if pos[i] <= 1e-12:
                    continue
                frac = min(1.0, -delta[i] / pos[i])
                book.realize(frac * (pos[i] - basis[i]))
                basis[i] *= (1.0 - frac)
            for i in np.nonzero(delta > 0)[0]:
                basis[i] += delta[i]
            fees = float(np.abs(delta) @ C)
            turnover[t] = float(np.abs(delta).sum()) / max(nav, 1e-12)
            n_trades += 1
            cash -= float(delta.sum()) + fees
            pos = target.copy()
            nav -= fees

        # ---- 3. chiusura dell'anno fiscale
        last_day = (t + 1 == n_days)
        if last_day or years[t + 1] != years[t]:
            tax = book.settle() + income_year * regime.div_rate
            income_year = 0.0
            if tax > 0:
                # si paga con la liquidita'; se non basta si vende in proporzione,
                # e quella vendita realizza plusvalenze che finiscono nell'anno dopo
                if cash < tax and pos.sum() > 0:
                    need = tax - cash
                    frac = min(1.0, need / pos.sum())
                    for i in range(n_inst):
                        if pos[i] > 1e-12:
                            book.realize(frac * (pos[i] - basis[i]))
                            basis[i] *= (1.0 - frac)
                    cash += float(pos.sum() * frac)
                    pos *= (1.0 - frac)
                cash -= tax
                tax_flow[t] = tax
                nav = pos.sum() + cash

        equity[t] = nav
        exposure[t] = pos.sum() / max(nav, 1e-12)

    # ---- 4. imposta latente sulla posizione ancora aperta a fine test
    latent = float(pos.sum() - basis.sum())
    exit_tax = max(0.0, latent - regime.exemption) * regime.rate if latent > 0 else 0.0

    idx = pd.DatetimeIndex(dates)
    return dict(
        equity=pd.Series(equity, index=idx),
        exposure=pd.Series(exposure, index=idx),
        turnover=pd.Series(turnover, index=idx),
        tax_flow=pd.Series(tax_flow, index=idx),
        tax_paid=book.paid,
        exit_tax=exit_tax,
        final_gross=float(equity[-1]),
        final_net=float(equity[-1] - exit_tax),
        n_rebal=n_trades,
        capital=capital,
    )


# ==========================================================================
# 6. METRICHE
# ==========================================================================
def _dd(curve):
    return curve / curve.cummax() - 1.0


def metrics(res, cash_rate=None, bench_equity=None):
    """
    Sintesi di una simulazione. Tutto al netto: se un numero e' lordo, il nome
    lo dice.

    La differenza fra CAGR lordo e netto e' il freno fiscale, e su una strategia
    che ruota spesso e' la voce piu' grande dopo il mercato stesso.
    """
    eq = res["equity"]
    r = eq.pct_change().fillna(0.0)
    yrs = len(eq) / TRADING_DAYS
    cap = res["capital"]

    cagr_g = (res["final_gross"] / cap) ** (1 / yrs) - 1
    cagr_n = (res["final_net"] / cap) ** (1 / yrs) - 1 if res["final_net"] > 0 else -1.0
    vol = r.std() * np.sqrt(TRADING_DAYS)

    if cash_rate is not None:
        ex = r - np.asarray(cash_rate) / TRADING_DAYS
    else:
        ex = r
    sharpe = ex.mean() / ex.std() * np.sqrt(TRADING_DAYS) if ex.std() > 0 else 0.0
    down = ex[ex < 0]
    sortino = (ex.mean() / down.std() * np.sqrt(TRADING_DAYS)) if len(down) and down.std() > 0 else 0.0

    dd = _dd(eq)
    mdd = float(dd.min())
    ulcer = float(np.sqrt((dd ** 2).mean()))
    # tempo per tornare al massimo precedente: quanto dura davvero il dolore
    under = (dd < -0.01).astype(int)
    runs, cur = [], 0
    for v in under:
        cur = cur + 1 if v else 0
        runs.append(cur)
    max_underwater = max(runs) / TRADING_DAYS if runs else 0.0

    roll12 = eq.pct_change(TRADING_DAYS).dropna()

    out = dict(
        cagr_net=cagr_n * 100, cagr_gross=cagr_g * 100,
        tax_drag=(cagr_g - cagr_n) * 100,
        vol=vol * 100, sharpe=sharpe, sortino=sortino,
        mdd=mdd * 100, calmar=(cagr_n / abs(mdd)) if mdd < 0 else np.inf,
        ulcer=ulcer * 100, underwater_yrs=max_underwater,
        expo=float(res["exposure"].mean()) * 100,
        turn_yr=float(res["turnover"].sum()) / yrs,
        rebal_yr=res["n_rebal"] / yrs,
        tax_paid=res["tax_paid"], exit_tax=res["exit_tax"],
        final_net=res["final_net"],
        worst12=float(roll12.min()) * 100 if len(roll12) else np.nan,
        best12=float(roll12.max()) * 100 if len(roll12) else np.nan,
        years=yrs,
    )
    if bench_equity is not None:
        b = bench_equity.reindex(eq.index).ffill()
        rel = (eq / eq.iloc[0]) / (b / b.iloc[0])
        out["vs_bench_cagr"] = (rel.iloc[-1] ** (1 / yrs) - 1) * 100
        # in quante finestre mobili di 3 e 5 anni si e' davanti al benchmark
        for w, lbl in ((3, "beat3y"), (5, "beat5y"), (10, "beat10y")):
            n = int(w * TRADING_DAYS)
            if len(rel) > n:
                out[lbl] = float((rel.pct_change(n).dropna() > 0).mean()) * 100
            else:
                out[lbl] = np.nan
    return out


# ---------------------------------------------------------------- statistica
def deflated_sharpe(sr_ann, n_obs, n_trials, sd_trials_ann, skew=0.0, kurt=3.0):
    """
    Deflated Sharpe Ratio (Bailey e Lopez de Prado, 2014).

    Se si provano N strategie, la migliore avra' uno Sharpe alto anche su dati
    puramente casuali: e' il massimo di N estrazioni, non una scoperta. Il dSR
    stima quale Sharpe ci si aspetterebbe dal solo caso, date N prove e data la
    DISPERSIONE degli Sharpe fra quelle prove, e chiede quanto la candidata lo
    superi. Sotto 0.95 il risultato non e' distinguibile dalla fortuna.

    Due dettagli che e' facile sbagliare e che cambiano completamente il numero:

      1. La soglia attesa dal caso e' proporzionale alla deviazione standard
         degli Sharpe fra i tentativi. Senza quel fattore la soglia risulta
         enorme e ogni strategia sembra rumore.
      2. Sharpe e numero di osservazioni devono stare nella stessa periodicita'.
         Qui si passa lo Sharpe ANNUALIZZATO e il numero di GIORNI, quindi si
         converte in giornaliero prima del confronto.

    skew e kurt sono quelli dei rendimenti della strategia: code spesse e
    asimmetria negativa rendono lo Sharpe stimato meno affidabile, e la formula
    ne tiene conto allargando l'intervallo.
    """
    from math import sqrt, erf, exp
    if n_trials < 2 or n_obs < 30 or not np.isfinite(sd_trials_ann) or sd_trials_ann <= 0:
        return np.nan
    eg = 0.5772156649                       # costante di Eulero-Mascheroni
    sr = sr_ann / np.sqrt(TRADING_DAYS)     # Sharpe per giorno
    sd = sd_trials_ann / np.sqrt(TRADING_DAYS)

    z1 = _norm_ppf(1 - 1.0 / n_trials)
    z2 = _norm_ppf(1 - 1.0 / (n_trials * exp(1)))
    sr0 = sd * ((1 - eg) * z1 + eg * z2)    # Sharpe atteso del migliore di N

    var = 1 - skew * sr + (kurt - 1) / 4.0 * sr ** 2
    if var <= 0:
        return np.nan
    stat = (sr - sr0) * sqrt(n_obs - 1) / sqrt(var)
    return 0.5 * (1 + erf(stat / sqrt(2)))


def _norm_ppf(p):
    """Inversa della normale standard (Acklam), evita di dipendere da scipy."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    pl, ph = 0.02425, 1 - 0.02425
    if p < pl:
        q = np.sqrt(-2 * np.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > ph:
        q = np.sqrt(-2 * np.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def block_bootstrap_pvalue(r_strat, r_bench, block=63, n_iter=2000, seed=0):
    """
    La differenza di rendimento medio e' spiegabile dal caso?

    Ricampiona a blocchi di un trimestre (per conservare l'autocorrelazione e i
    grappoli di volatilita', che il bootstrap iid distruggerebbe) la serie delle
    differenze giornaliere, e misura quanto spesso il caso produce un vantaggio
    grande almeno quanto quello osservato. p alto = non hai trovato niente.
    """
    d = np.asarray(r_strat) - np.asarray(r_bench)
    d = d[np.isfinite(d)]
    n = len(d)
    if n < block * 4:
        return np.nan
    obs = d.mean()
    dc = d - obs                      # sotto l'ipotesi nulla la media e' zero
    rng = np.random.default_rng(seed)
    nb = n // block
    starts = rng.integers(0, n - block, size=(n_iter, nb))
    idx = starts[:, :, None] + np.arange(block)[None, None, :]
    sims = dc[idx].reshape(n_iter, -1).mean(axis=1)
    return float((sims >= obs).mean())


# ==========================================================================
# 7. PERCORSO VELOCE PER LA SELEZIONE
# ==========================================================================
def quick_stats(W, R, C, cash_rate, exec_lag=1, min_trade=0.002):
    """
    Statistiche al LORDO delle imposte, calcolate in forma vettoriale.

    Il simulatore completo tiene la contabilita' fiscale giorno per giorno, e
    per farlo deve scorrere il calendario in Python. Va benissimo per misurare
    una candidata, ma nel walk-forward la stessa configurazione viene rivalutata
    migliaia di volte solo per ORDINARLA rispetto alle altre, e li' il costo
    diventa proibitivo.

    Qui si separano i due mestieri: questa funzione ordina, il simulatore
    misura. La separazione non e' solo di comodo, e' anche corretta come
    criterio: si sceglie sul rapporto rendimento/rischio al lordo, cioe' sulla
    qualita' del SEGNALE, e poi si misura quanto ne sopravvive al fisco. Se si
    selezionasse direttamente sul netto, il freno fiscale diventerebbe un
    ingrediente della scelta e non piu' un risultato da riportare.

    Restituisce Sharpe, CAGR lordo, ribasso massimo e rotazione annua.
    """
    n = W.shape[0]
    if exec_lag > 0:
        P = np.vstack([np.zeros((exec_lag, W.shape[1])), W[:-exec_lag]])
    else:
        P = W
    P = np.nan_to_num(P)

    scambi = np.abs(np.diff(P, axis=0, prepend=np.zeros((1, W.shape[1]))))
    # ribilanciamenti sotto soglia non si eseguono: senza questo filtro la
    # rotazione stimata sarebbe molto piu' alta di quella che si pagherebbe
    piccoli = scambi.sum(axis=1) <= min_trade
    scambi[piccoli] = 0.0

    liquido = 1.0 - P.sum(axis=1)
    lordo = (P * np.nan_to_num(R)).sum(axis=1) + liquido * cash_rate / TRADING_DAYS
    netto = lordo - scambi @ C

    sd = netto.std()
    ex = netto - cash_rate / TRADING_DAYS
    sharpe = ex.mean() / sd * np.sqrt(TRADING_DAYS) if sd > 0 else 0.0

    curva = np.cumprod(1.0 + netto)
    anni = n / TRADING_DAYS
    cagr = curva[-1] ** (1 / anni) - 1 if curva[-1] > 0 else -1.0
    mdd = float((curva / np.maximum.accumulate(curva) - 1).min())
    return dict(sharpe=float(sharpe), cagr=float(cagr) * 100, mdd=mdd * 100,
                turn_yr=float(scambi.sum()) / anni,
                expo=float(P.sum(axis=1).mean()) * 100)

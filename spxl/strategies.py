"""
LIBRERIA DI STRATEGIE
=====================

Regole del gioco, valide per ogni funzione di questo file:

  1. Il segnale del giorno t si calcola SOLO con dati chiusi al giorno t.
     Il ritardo di esecuzione lo aggiunge il simulatore (exec_lag), non le
     strategie: cosi' nessuno puo' dimenticarselo.
  2. Il segnale si calcola sull'INDICE, non su SPXL. Il fondo a leva e' solo
     il veicolo con cui si prende l'esposizione. Un segnale calcolato sui
     prezzi di SPXL sarebbe piu' rumoroso e non aggiungerebbe informazione.
  3. Ogni strategia restituisce una matrice di pesi obiettivo sugli strumenti
     dichiarati in ctx.instruments. Peso 0.6 su SPXL = 60% del patrimonio nel
     fondo 3x = 180% di esposizione all'indice. Il resto e' liquidita'.

Nessuna di queste e' inventata da zero: sono le famiglie che compaiono nella
letteratura sul market timing e sull'uso della leva. Il valore aggiunto qui non
sta nell'idea, sta nel misurarle con costi, imposte e validazione onesta.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

TRADING_DAYS = 252


# ==========================================================================
# CONTESTO: tutti gli indicatori precalcolati una volta sola
# ==========================================================================
class Ctx:
    """
    Contenitore dei dati di mercato con cache degli indicatori.

    Ricalcolare una media mobile a 200 giorni per ognuna delle migliaia di
    combinazioni testate sarebbe il collo di bottiglia dell'intera ricerca:
    qui si calcola una volta e si riusa.
    """

    def __init__(self, dates, px, r_px, r_tr, rf, vix=None, vix3m=None):
        self.dates = pd.DatetimeIndex(dates)
        self.px = pd.Series(np.asarray(px, float), index=self.dates)
        self.r_px = pd.Series(np.asarray(r_px, float), index=self.dates)
        self.r_tr = pd.Series(np.asarray(r_tr, float), index=self.dates)
        self.rf = pd.Series(np.asarray(rf, float), index=self.dates)
        self.vix = None if vix is None else pd.Series(np.asarray(vix, float), index=self.dates)
        self.vix3m = None if vix3m is None else pd.Series(np.asarray(vix3m, float), index=self.dates)
        self.n = len(self.dates)
        self._cache = {}
        # fine mese: usato dalle varianti a bassa rotazione
        self.month_end = pd.Series(
            self.dates.to_period("M") != pd.Series(self.dates).shift(-1).dt.to_period("M").values,
            index=self.dates).fillna(True)

    def _memo(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def sma(self, n):
        return self._memo(("sma", n), lambda: self.px.rolling(n, min_periods=n).mean())

    def ema(self, n):
        return self._memo(("ema", n), lambda: self.px.ewm(span=n, adjust=False, min_periods=n).mean())

    def vol(self, n):
        """Volatilita' realizzata annualizzata sui rendimenti di prezzo."""
        return self._memo(("vol", n),
                          lambda: self.r_px.rolling(n, min_periods=n).std() * np.sqrt(TRADING_DAYS))

    def ret(self, n):
        """Rendimento composto degli ultimi n giorni."""
        return self._memo(("ret", n), lambda: self.px / self.px.shift(n) - 1.0)

    def rsi(self, n):
        def _f():
            d = self.px.diff()
            up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
            dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
            return 100 - 100 / (1 + up / dn.replace(0, np.nan))
        return self._memo(("rsi", n), _f)

    def dd_from_high(self, n):
        """Scostamento dal massimo degli ultimi n giorni (numero <= 0)."""
        return self._memo(("ddh", n),
                          lambda: self.px / self.px.rolling(n, min_periods=1).max() - 1.0)

    def down_streak(self):
        """Numero di sedute negative consecutive fino a oggi incluso."""
        def _f():
            d = (self.r_px < 0).astype(int)
            grp = (d != d.shift()).cumsum()
            return d * (d.groupby(grp).cumcount() + 1)
        return self._memo(("streak",), _f)


# ==========================================================================
# UTILITA'
# ==========================================================================
def _hysteresis(above, below):
    """
    Macchina a due stati con soglie diverse per entrare e uscire.

    Con una soglia sola, un prezzo che oscilla attorno alla media genera decine
    di operazioni inutili: ognuna paga spread e, se in utile, imposta. La banda
    di isteresi e' il modo standard di spegnere quel rumore.

    above/below sono booleani: si entra quando above, si esce quando below,
    e nella zona intermedia si resta come si era.
    """
    a = np.asarray(above, dtype=bool)
    b = np.asarray(below, dtype=bool)
    out = np.zeros(len(a))
    on = False
    for i in range(len(a)):
        if not on and a[i]:
            on = True
        elif on and b[i]:
            on = False
        out[i] = 1.0 if on else 0.0
    return out


def _monthly(sig, month_end):
    """
    Congela il segnale fino al fine mese successivo.

    Serve a costruire, per ogni strategia giornaliera, la sua versione a
    rotazione mensile. Con imposta sul realizzato la frequenza di decisione e'
    una variabile di progetto quanto la soglia: e spesso conta di piu'.
    """
    s = pd.Series(np.asarray(sig, float), index=month_end.index)
    frozen = s.where(month_end.values).ffill()
    return frozen.fillna(0.0).values


def _weights(ctx, cols, series_map):
    """Assembla la matrice dei pesi nell'ordine di colonne richiesto."""
    W = np.zeros((ctx.n, len(cols)))
    for j, c in enumerate(cols):
        if c in series_map:
            W[:, j] = np.nan_to_num(np.asarray(series_map[c], float))
    return W


# ==========================================================================
# A. TREND: leva solo quando l'indice e' in tendenza rialzista
# ==========================================================================
def sma_trend(ctx, cols, n=200, band=0.0, w=1.0, monthly=False):
    """
    Il filtro piu' vecchio e piu' studiato che esista: dentro sopra la media
    mobile, fuori sotto.

    L'idea per cui vale la pena applicarlo a un 3x e' che il volatility drag
    esplode quando la volatilita' esplode, e la volatilita' esplode quasi solo
    sotto la media a 200 giorni. Stare fuori proprio li' non serve a "evitare
    le perdite": serve a evitare il regime in cui la leva giornaliera si
    autodistrugge.

    band  larghezza dell'isteresi in frazione della media (0.02 = 2%)
    """
    ma = ctx.sma(n)
    up = (ctx.px > ma * (1 + band)).fillna(False)
    dn = (ctx.px < ma * (1 - band)).fillna(True)
    sig = _hysteresis(up, dn) * w
    if monthly:
        sig = _monthly(sig, ctx.month_end)
    return _weights(ctx, cols, {"SPXL": sig})


def dual_sma(ctx, cols, fast=50, slow=200, w=1.0, monthly=False):
    """Incrocio di due medie: piu' lento a entrare, piu' lento a uscire."""
    f, s = ctx.sma(fast), ctx.sma(slow)
    sig = (f > s).fillna(False).astype(float).values * w
    if monthly:
        sig = _monthly(sig, ctx.month_end)
    return _weights(ctx, cols, {"SPXL": sig})


def abs_momentum(ctx, cols, n=252, w=1.0, monthly=True):
    """
    Momentum assoluto: investito se il rendimento a n giorni ha battuto il
    tasso privo di rischio, altrimenti liquido. E' la meta' "difensiva" del
    dual momentum di Antonacci, l'unica che serve quando l'universo e' un
    indice solo.
    """
    thr = ctx.rf.rolling(n, min_periods=1).mean() * (n / TRADING_DAYS)
    sig = (ctx.ret(n) > thr).fillna(False).astype(float).values * w
    if monthly:
        sig = _monthly(sig, ctx.month_end)
    return _weights(ctx, cols, {"SPXL": sig})


# ==========================================================================
# B. VOLATILITA': dosare la leva invece di accenderla e spegnerla
# ==========================================================================
def vol_target(ctx, cols, target=0.16, lookback=20, cap=1.0, floor=0.0,
               lev=3.0, monthly=False, step=0.10):
    """
    Volatility targeting: l'esposizione e' inversamente proporzionale alla
    volatilita' recente, per tenere il rischio del portafoglio su un livello
    costante invece di lasciarlo decidere al mercato.

    Su un fondo a leva ha un secondo effetto, piu' importante del primo: il
    drag da varianza cresce col QUADRATO della volatilita', quindi ridurre
    l'esposizione proprio quando la volatilita' sale taglia il drag dove fa
    male, non in modo uniforme.

    step  quantizzazione del peso: senza, si ribilancerebbe ogni giorno per
          frazioni di punto, pagando costi per nulla.
    """
    v = ctx.vol(lookback)
    raw = (target / v.replace(0, np.nan) / lev).clip(floor, cap)
    if step:
        raw = (raw / step).round() * step
    sig = raw.fillna(0.0).values
    if monthly:
        sig = _monthly(sig, ctx.month_end)
    return _weights(ctx, cols, {"SPXL": sig})


def vol_regime(ctx, cols, thr=0.20, lookback=20, w=1.0, band=0.15, monthly=False):
    """Tutto o niente in base alla volatilita' realizzata, con isteresi."""
    v = ctx.vol(lookback)
    sig = _hysteresis((v < thr * (1 - band)).fillna(False),
                      (v > thr * (1 + band)).fillna(True)) * w
    if monthly:
        sig = _monthly(sig, ctx.month_end)
    return _weights(ctx, cols, {"SPXL": sig})


def vix_filter(ctx, cols, thr=20.0, w=1.0, band=0.15, monthly=False):
    """
    Come sopra ma con la volatilita' IMPLICITA al posto di quella realizzata.
    Il VIX guarda avanti di 30 giorni invece che indietro: in teoria reagisce
    prima. Esiste solo dal 1990, quindi i test su questa famiglia sono piu'
    corti e vanno pesati di conseguenza.
    """
    if ctx.vix is None:
        return np.zeros((ctx.n, len(cols)))
    sig = _hysteresis((ctx.vix < thr * (1 - band)).fillna(False),
                      (ctx.vix > thr * (1 + band)).fillna(True)) * w
    if monthly:
        sig = _monthly(sig, ctx.month_end)
    return _weights(ctx, cols, {"SPXL": sig})


def vix_term(ctx, cols, thr=1.0, w=1.0, monthly=False):
    """
    Struttura a termine della volatilita': VIX3M/VIX sopra 1 (contango) segnala
    un mercato calmo, sotto 1 (backwardation) segnala stress in corso. E' il
    segnale che nel 2008 e nel 2020 si e' girato prima del prezzo.
    """
    if ctx.vix is None or ctx.vix3m is None:
        return np.zeros((ctx.n, len(cols)))
    ratio = ctx.vix3m / ctx.vix.replace(0, np.nan)
    sig = _hysteresis((ratio > thr).fillna(False), (ratio < thr).fillna(True)) * w
    if monthly:
        sig = _monthly(sig, ctx.month_end)
    return _weights(ctx, cols, {"SPXL": sig})


# ==========================================================================
# C. MEAN REVERSION: comprare la debolezza dentro un trend rialzista
# ==========================================================================
def rsi2(ctx, cols, entry=10, exit_n=5, trend=200, w=1.0):
    """
    Connors: sopra la media lunga, si compra l'ipervenduto a due giorni e si
    esce quando il prezzo torna sopra la media breve. Molte operazioni corte:
    e' esattamente il profilo che il fisco sul realizzato punisce di piu', ed
    e' il motivo per cui va testato con l'imposta accesa e non senza.
    """
    ma, r, ex = ctx.sma(trend), ctx.rsi(2), ctx.sma(exit_n)
    enter = ((ctx.px > ma) & (r < entry)).fillna(False).values
    leave = (ctx.px > ex).fillna(False).values
    out, on = np.zeros(ctx.n), False
    for i in range(ctx.n):
        if not on and enter[i]:
            on = True
        elif on and leave[i]:
            on = False
        out[i] = w if on else 0.0
    return _weights(ctx, cols, {"SPXL": out})


def dip_buy(ctx, cols, drop=0.05, window=20, trend=200, hold=10, w=1.0):
    """
    Compra un ribasso del drop% dal massimo delle ultime window sedute, purche'
    si resti sopra la media lunga, e tiene per hold giorni. Versione a durata
    fissa: evita di dover inventare anche una regola di uscita.
    """
    ma = ctx.sma(trend)
    trig = ((ctx.dd_from_high(window) <= -drop) & (ctx.px > ma)).fillna(False).values
    out = np.zeros(ctx.n)
    left = 0
    for i in range(ctx.n):
        if trig[i]:
            left = hold
        out[i] = w if left > 0 else 0.0
        left = max(0, left - 1)
    return _weights(ctx, cols, {"SPXL": out})


def streak_buy(ctx, cols, days=3, trend=200, w=1.0):
    """N sedute negative di fila sopra la media lunga: entra, esci al primo rialzo."""
    ma = ctx.sma(trend)
    st = ctx.down_streak()
    enter = ((ctx.px > ma) & (st >= days)).fillna(False).values
    leave = (ctx.r_px > 0).fillna(False).values
    out, on = np.zeros(ctx.n), False
    for i in range(ctx.n):
        if not on and enter[i]:
            on = True
        elif on and leave[i]:
            on = False
        out[i] = w if on else 0.0
    return _weights(ctx, cols, {"SPXL": out})


# ==========================================================================
# D. LATO SHORT
# ==========================================================================
def trend_long_short(ctx, cols, n=200, band=0.0, w_long=1.0, w_short=0.5):
    """
    Sopra la media si sta lunghi con SPXL, sotto si sta corti con SPXS.

    Attenzione a cosa si sta chiedendo: un 3x inverso perde su QUALSIASI
    mercato laterale, perche' il drag da varianza colpisce anche lo short, e i
    mercati sotto la media a 200 giorni sono i piu' volatili che esistano. Il
    peso short parte al 50% apposta: mettere 100% su SPXS e' una scommessa
    diversa, non una copertura.
    """
    ma = ctx.sma(n)
    up = (ctx.px > ma * (1 + band)).fillna(False)
    dn = (ctx.px < ma * (1 - band)).fillna(True)
    lng = _hysteresis(up, dn)
    return _weights(ctx, cols, {"SPXL": lng * w_long, "SPXS": (1 - lng) * w_short})


def short_on_stress(ctx, cols, n=200, vol_thr=0.25, lookback=20,
                    w_long=1.0, w_short=0.5):
    """
    Short solo quando DUE condizioni sono vere insieme: prezzo sotto la media
    lunga E volatilita' realizzata sopra soglia.

    Il doppio filtro esiste perche' lo short a leva guadagna solo nei crolli
    veloci e direzionali; nei ribassi lenti e disordinati perde anche quando ha
    ragione sulla direzione.
    """
    ma = ctx.sma(n)
    v = ctx.vol(lookback)
    lng = _hysteresis((ctx.px > ma).fillna(False), (ctx.px < ma).fillna(True))
    stress = ((ctx.px < ma) & (v > vol_thr)).fillna(False).astype(float).values
    return _weights(ctx, cols, {"SPXL": lng * w_long, "SPXS": stress * w_short})


def trend_defensive(ctx, cols, n=200, w_lev=1.0, w_base=1.0):
    """
    Tre stati invece di due: leva sopra la media, indice semplice appena sotto,
    liquidita' solo in caso di rottura netta. Chi esce del tutto dal mercato
    paga i falsi segnali due volte, perche' perde anche il rimbalzo.
    """
    ma = ctx.sma(n)
    ma_long = ctx.sma(min(n * 2, 400))
    lev = (ctx.px > ma).fillna(False)
    mid = ((ctx.px <= ma) & (ctx.px > ma_long)).fillna(False)
    return _weights(ctx, cols, {"SPXL": lev.astype(float).values * w_lev,
                                "SPY": mid.astype(float).values * w_base})


# ==========================================================================
# E. COMBINAZIONI
# ==========================================================================
def ensemble(ctx, cols, parts, w=1.0, step=0.25, monthly=False):
    """
    Media di piu' segnali binari: l'esposizione diventa graduale invece che
    tutto-o-niente.

    Il motivo non e' estetico. Un segnale singolo sbaglia in blocco; tre
    segnali scorrelati sbagliano a turno, e la media riduce la varianza delle
    decisioni senza ridurne il valore atteso. La quantizzazione a step evita
    che ogni minimo disaccordo generi un'operazione.

    parts  lista di (funzione, kwargs) che restituiscono pesi su SPXL
    """
    acc = np.zeros(ctx.n)
    for fn, kw in parts:
        W = fn(ctx, ["SPXL"], **kw)
        acc += W[:, 0]
    acc /= max(1, len(parts))
    if step:
        acc = np.round(acc / step) * step
    acc = np.clip(acc, 0, 1) * w
    if monthly:
        acc = _monthly(acc, ctx.month_end)
    return _weights(ctx, cols, {"SPXL": acc})


# ==========================================================================
# RIFERIMENTI
# ==========================================================================
def buy_hold_spy(ctx, cols):
    """Il benchmark: 100% indice, per sempre, senza mai toccare niente."""
    return _weights(ctx, cols, {"SPY": np.ones(ctx.n)})


def buy_hold_spxl(ctx, cols):
    """
    100% SPXL per sempre. Non e' una strategia, e' il termine di paragone che
    mostra quanto costa la leva quando non la si gestisce.
    """
    return _weights(ctx, cols, {"SPXL": np.ones(ctx.n)})

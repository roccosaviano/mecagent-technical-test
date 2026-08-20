"""
BANCO DI PROVA PAC — 10.000 EUR SUBITO + 700 EUR/MESE
=====================================================
Uso:  python3 pac_data.py     (una volta, scarica i dati in data/)
      python3 pac_lab.py      (esegue lo studio, scrive out/pac_results.json)

LA DOMANDA
  "Quanto avro' fra 5, 10, 15 anni mettendo 10k subito e 700 al mese su
   S&P 500 / SPMO (momentum) / SPXL (3x)?"

PERCHE' LA RISPOSTA NON E' UN NUMERO
  Un simulatore che ti dice "fra 15 anni avrai 340.000" ha scelto un rendimento
  medio e lo ha applicato ogni anno. Ma un PAC non incassa la media: incassa la
  SEQUENZA. Gli stessi rendimenti in ordine diverso danno montanti diversi,
  perche' i versamenti pesano piu' negli ultimi anni che nei primi. Su un
  prodotto a leva 3x questo effetto smette di essere un dettaglio e diventa
  tutta la storia.
  Qui, invece di una media, si simula il PAC su OGNI mese di partenza degli
  ultimi 100 anni e si guarda la distribuzione dei risultati.

COME SONO COSTRUITE LE SERIE (dettagli e validazione: sezione VALIDAZIONE)
  - S&P 500 : fattore di mercato USA total-return (Fama-French, dal 1926)
              riscalato sul beta di SPY, meno le commissioni dell'ETF.
  - SPMO    : replica fattoriale (mercato + momentum) con i pesi stimati sui
              dati reali di SPMO 2016-2026. Alpha azzerato per default: il
              +3%/anno di extra-rendimento del campione e' figlio di un decennio
              d'oro per il momentum, proiettarlo sarebbe barare.
  - SPXL    : formula del 3x a reset giornaliero applicata all'indice —
              3x il rendimento del giorno, meno il costo di finanziare 2 dollari
              presi a prestito, meno le spese. Ricostruisce lo SPXL reale con
              correlazione 0.998 e uno scarto di 0.3%/anno su 10 anni.

REGOLA D'ORO: guarda il quinto percentile, non la mediana. La mediana la incassi
solo se resti investito, e resti investito solo se il quinto percentile non ti
butta fuori.
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(HERE, "out")

# ---------------------------------------------------------------- parametri
PIC = 10_000.0          # versamento iniziale
MENSILE = 700.0         # versamento mensile
ORIZZONTI = (5, 10, 15)  # anni
COMMISSIONE = 1.0       # euro per ordine (Degiro/IBKR: ~1 EUR su un ETF USA)
INFLAZIONE = 0.02       # per convertire il montante in euro di oggi

# Costi annui dei prodotti (TER dichiarati).
TER = {"sp500": 0.0007,  # un ETF S&P 500 UCITS tipo CSPX/SPY5; SPY americano 0.0945%
       "spmo": 0.0033,   # Invesco S&P 500 Momentum
       "spxl": 0.0091}   # Direxion Daily S&P 500 Bull 3X
SPREAD_LEVA = 0.005     # spread sopra il T-bill sui 2 dollari presi a prestito
                        # (calibrato per far coincidere il 3x sintetico con SPXL reale)
# Rendimento da distribuzione: i prezzi Nasdaq sono lordi cedola, li riaggiungo
# come rateo costante. Serve solo in fase di calibrazione.
YIELD = {"SPY": 0.0125, "SPMO": 0.0070, "SPXL": 0.0100}

NOMI = {"sp500": "S&P 500", "spmo": "SPMO (momentum)", "spxl": "SPXL (3x)"}


# ---------------------------------------------------------------- dati
def carica():
    leggi = lambda f: pd.read_csv(os.path.join(DATA, f), index_col=0, parse_dates=True)
    return (leggi("ff_daily.csv.gz"), leggi("etf_daily.csv.gz"),
            leggi("cpi_monthly.csv.gz"), leggi("eurusd_daily.csv.gz"))


def ols(y, *regressori):
    """Minimi quadrati con intercetta. Ritorna (alpha, *beta, R2)."""
    X = np.column_stack([np.ones(len(y))] + [np.asarray(r) for r in regressori])
    b, *_ = np.linalg.lstsq(X, np.asarray(y), rcond=None)
    res = np.asarray(y) - X @ b
    r2 = 1 - (res ** 2).sum() / ((y - np.mean(y)) ** 2).sum()
    return list(b) + [r2]


def costruisci(ff, px, quota_alpha=0.0, seed=12345):
    """Serie giornaliere di rendimento totale, 1926 -> oggi, per i tre prodotti.

    La calibrazione usa la finestra in cui esistono sia i fattori sia i prezzi
    reali (2016-2026). Le serie ricostruite coprono tutto lo storico dei fattori.

    quota_alpha: quanta parte dell'alpha campionario di SPMO si porta avanti.
                 0 = nessuna (default, prudente), 1 = tutta (ottimista).
    """
    tr = px.pct_change()
    for c in tr:
        tr[c] = tr[c] + YIELD[c] / 252.0          # rateo dividendi
    d = tr.join(ff, how="inner").dropna()

    a_sp, b_sp, r2_sp = ols(d.SPY - d.RF, d.MktRF)
    a_mo, bm_mo, bq_mo, r2_mo = ols(d.SPMO - d.RF, d.MktRF, d.MOM)

    # SPMO: il modello a due fattori spiega l'84% della varianza giornaliera. Il
    # resto e' rischio specifico (SPMO ha ~100 titoli, non 500) e va rimesso, se
    # no le discese simulate escono piu' morbide del vero. Residui pescati a caso
    # dal campione reale, con seme fisso: riproducibile.
    res = (d.SPMO - d.RF) - (a_mo + bm_mo * d.MktRF + bq_mo * d.MOM)
    rng = np.random.default_rng(seed)
    rumore = rng.choice(res.values, size=len(ff), replace=True)

    # indice S&P 500 lordo di commissioni: e' il sottostante del 3x
    idx = ff.RF + b_sp * ff.MktRF

    r = pd.DataFrame(index=ff.index)
    r["sp500"] = idx - TER["sp500"] / 252.0
    r["spmo"] = (ff.RF + bm_mo * ff.MktRF + bq_mo * ff.MOM - TER["spmo"] / 252.0
                 + quota_alpha * a_mo + rumore)
    r["spxl"] = 3.0 * idx - 2.0 * (ff.RF + SPREAD_LEVA / 252.0) - TER["spxl"] / 252.0
    r = r.clip(lower=-1.0)                        # un ETF non puo' perdere piu' del 100%

    calib = dict(
        beta_sp500=b_sp, alpha_sp500=a_sp * 252, r2_sp500=r2_sp,
        beta_mkt_spmo=bm_mo, beta_mom_spmo=bq_mo, alpha_spmo=a_mo * 252, r2_spmo=r2_mo,
        quota_alpha=quota_alpha, vol_residua_spmo=float(res.std() * np.sqrt(252)),
        finestra=f"{d.index[0].date()} -> {d.index[-1].date()}", n_giorni=len(d))
    return r, calib, d


# ---------------------------------------------------------------- simulazione PAC
def giorni_versamento(idx):
    """Primo giorno di borsa di ogni mese (e' quando parte il bonifico)."""
    per = idx.to_period("M")
    return np.flatnonzero(~per.duplicated())


class Serie:
    """Una serie di rendimenti giornalieri piu' l'indice dei giorni di versamento."""

    def __init__(self, ret):
        self.idx = ret.index
        self.r = ret.values.astype(float)
        self.mesi_idx = giorni_versamento(ret.index)
        self.n_mesi = len(self.mesi_idx)


def simula(s, i0, mesi, pic=PIC, mensile=MENSILE, commissione=COMMISSIONE):
    """Un PAC, dal mese i0 per `mesi` mesi. Ritorna il percorso giornaliero.

    V_t = G_t * somma(C_i / G_i), con G = prodotto cumulato dei rendimenti:
    e' la stessa cosa di "compra quote ogni mese e tienile", scritta in modo
    vettoriale invece che con un ciclo.
    """
    if i0 + mesi >= s.n_mesi:
        return None
    a, b = s.mesi_idx[i0], s.mesi_idx[i0 + mesi]  # b = giorno del bilancio finale
    rr = s.r[a:b + 1]
    g = np.cumprod(1.0 + rr)

    c = np.zeros(len(rr))                         # cassa che entra, al netto commissioni
    versati = np.zeros(len(rr))                   # cassa che esce dalle tue tasche
    c[0] = pic + mensile - commissione            # il PIC entra insieme alla prima rata
    versati[0] = pic + mensile
    for k in range(1, mesi):
        j = s.mesi_idx[i0 + k] - a
        c[j] += mensile - commissione
        versati[j] += mensile
    versati = np.cumsum(versati)

    morto = int(np.argmax(g <= 0)) if (g <= 0).any() else -1
    if morto < 0:
        v = g * np.cumsum(c / g)
    else:
        # ETF azzerato (perdita del 100% in un giorno): il capitale gia' investito
        # e' perso, quello che versi dopo non ha piu' un fondo dove andare e resta cassa.
        v = np.zeros(len(rr))
        if morto > 0:
            v[:morto] = g[:morto] * np.cumsum(c[:morto] / g[:morto])
        v[morto:] = np.cumsum(c)[morto:] - np.cumsum(c)[max(morto - 1, 0)]
    return dict(valore=v, versato=versati, wipeout=morto >= 0,
                inizio=s.idx[a], fine=s.idx[b], giorni=b - a + 1)


def irr_annuo(mesi, pic, mensile, finale):
    """Rendimento monetario (IRR): l'unico tasso che ha senso su flussi ripetuti."""
    flussi = np.full(mesi + 1, -mensile)
    flussi[0] = -(pic + mensile)
    flussi[-1] += finale
    if finale <= 0:
        return -1.0
    lo, hi = -0.9999, 1.0
    npv = lambda x: np.sum(flussi / (1 + x) ** np.arange(len(flussi)))
    for _ in range(200):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (1 + (lo + hi) / 2) ** 12 - 1


def metriche(p, mesi, pic=PIC, mensile=MENSILE, deflatore=1.0):
    v, versato = p["valore"], p["versato"]
    finale = v[-1]
    picco = np.maximum.accumulate(v)
    dd = v / np.where(picco > 0, picco, 1) - 1
    return dict(
        inizio=str(p["inizio"].date()), fine=str(p["fine"].date()),
        finale=float(finale), versato=float(versato[-1]),
        moic=float(finale / versato[-1]),
        irr=float(irr_annuo(mesi, pic, mensile, finale)),
        maxdd=float(dd.min()),
        maxdd_eur=float((picco - v).max()),
        sotto_versato=float(np.mean(v < versato)),
        gap_peggiore=float((v - versato).min()),
        reale=float(finale / deflatore),          # montante in soldi del giorno di partenza
        infl=float(deflatore),
        wipeout=bool(p["wipeout"]))


# ---------------------------------------------------------------- studio rolling
PCT = [5, 10, 25, 50, 75, 90, 95]


def rolling(s, mesi, cpi=None, percorsi=False, **kw):
    """Simula il PAC su ogni mese di partenza disponibile.

    Con percorsi=True ritorna anche la matrice (finestre x mesi) dei valori a fine
    mese: serve per disegnare la fascia dei percentili nel tempo.
    """
    out, mat = [], []
    for i0 in range(s.n_mesi - mesi):
        p = simula(s, i0, mesi, **kw)
        if not p:
            continue
        defl = 1.0
        if cpi is not None:
            defl = float(cpi.asof(p["fine"]) / cpi.asof(p["inizio"]))
        out.append(metriche(p, mesi, kw.get("pic", PIC), kw.get("mensile", MENSILE), defl))
        if percorsi:
            tappe = s.mesi_idx[i0:i0 + mesi + 1] - s.mesi_idx[i0]
            mat.append(p["valore"][tappe])
    df = pd.DataFrame(out)
    return (df, np.array(mat)) if percorsi else df


def riassunto(df, mesi):
    q = lambda c: {f"p{p}": float(np.percentile(df[c], p)) for p in PCT}
    return dict(
        n=len(df), versato=float(df.versato.iloc[0]),
        finale=dict(min=float(df.finale.min()), max=float(df.finale.max()),
                    media=float(df.finale.mean()), **q("finale")),
        irr=dict(min=float(df.irr.min()), max=float(df.irr.max()), **q("irr")),
        moic=dict(min=float(df.moic.min()), max=float(df.moic.max()), **q("moic")),
        maxdd=dict(mediana=float(df.maxdd.median()), peggiore=float(df.maxdd.min()),
                   p10=float(np.percentile(df.maxdd, 10))),
        maxdd_eur=dict(mediana=float(df.maxdd_eur.median()), peggiore=float(df.maxdd_eur.max())),
        reale=dict(min=float(df.reale.min()), max=float(df.reale.max()), **q("reale")),
        p_perdita=float((df.finale < df.versato).mean()),
        p_perdita_reale=float((df.reale < df.versato).mean()),
        p_dimezzato=float((df.finale < df.versato * 0.5).mean()),
        sotto_versato=float(df.sotto_versato.median()),
        wipeout=float(df.wipeout.mean()))


# ---------------------------------------------------------------- tasse
def dopo_tasse(finale, versato, regime, anni, valore_a_8=None, versato_a_8=None):
    """Montante netto. Semplificato ma nella direzione giusta.

    it26      : Italia, 26% sulla plusvalenza al disinvestimento.
    ie_cgt33  : Irlanda, ETF USA trattati come azioni -> CGT 33% alla vendita.
    ie_ucits41: Irlanda, ETF UCITS -> exit tax 41% con deemed disposal a 8 anni.
                Il deemed disposal e' calcolato a livello di portafoglio invece
                che lotto per lotto: sottostima leggermente il prelievo.
    """
    gain = max(finale - versato, 0.0)
    if regime == "lordo":
        return finale
    if regime == "it26":
        return finale - 0.26 * gain
    if regime == "ie_cgt33":
        return finale - 0.33 * gain
    if regime == "ie_ucits41":
        if anni > 8 and valore_a_8 is not None:
            g8 = max(valore_a_8 - versato_a_8, 0.0)
            t8 = 0.41 * g8
            # la tassa pagata all'anno 8 esce dal portafoglio e smette di comporre
            quota = t8 / valore_a_8 if valore_a_8 > 0 else 0
            finale = finale * (1 - quota)
            gain = max(finale - (versato - t8), 0.0)
            return finale - 0.41 * max(gain, 0.0)
        return finale - 0.41 * gain
    raise ValueError(regime)


# ---------------------------------------------------------------- validazione
def validazione(d, c):
    """La ricostruzione riproduce gli ETF veri? Confronto sulla finestra comune.

    Qui il modello gira COMPLETO (alpha di SPMO incluso, nessun rumore): serve a
    misurare la qualita' della replica. Nello studio l'alpha viene poi azzerato,
    che e' una scelta prudenziale, non un difetto del modello.
    """
    idx = d.RF + c["beta_sp500"] * d.MktRF
    fit = pd.DataFrame({
        "sp500": idx - TER["sp500"] / 252.0,
        "spmo": (d.RF + c["alpha_spmo"] / 252 + c["beta_mkt_spmo"] * d.MktRF
                 + c["beta_mom_spmo"] * d.MOM),
        "spxl": 3.0 * idx - 2.0 * (d.RF + SPREAD_LEVA / 252.0) - TER["spxl"] / 252.0},
        index=d.index)
    out = {}
    n = len(d)
    cagr = lambda s: float((1 + s).prod() ** (252 / n) - 1)
    for tic, key in [("SPY", "sp500"), ("SPMO", "spmo"), ("SPXL", "spxl")]:
        reale, sint = d[tic], fit[key]
        out[key] = dict(ticker=tic, n=n,
                        cagr_reale=cagr(reale), cagr_sintetico=cagr(sint),
                        vol_reale=float(reale.std() * np.sqrt(252)),
                        vol_sintetica=float(sint.std() * np.sqrt(252)),
                        correlazione=float(np.corrcoef(reale, sint)[0, 1]),
                        scarto_annuo=cagr(sint) - cagr(reale))
    return out


# ---------------------------------------------------------------- main
def deterministico(tasso, mesi, pic=PIC, mensile=MENSILE):
    """Il numero che ti da' qualunque calcolatore online. Serve solo da paragone."""
    m = (1 + tasso) ** (1 / 12) - 1
    return pic * (1 + m) ** mesi + mensile * (((1 + m) ** mesi - 1) / m) * (1 + m)


def sensibilita_momentum(ff, calib, mesi):
    """E se il premio momentum non fosse piu' quello di cent'anni di dati?

    Tutto il vantaggio di SPMO nella simulazione viene da un solo numero: il
    premio medio del fattore momentum, moltiplicato per il beta 0.295 stimato su
    SPMO. Qui lo si taglia del 50% e del 100% e si guarda cosa resta.
    """
    out = {}
    premio = ff.MOM.mean()
    for taglio in (0.0, 0.5, 1.0):
        r = (ff.RF + calib["beta_mkt_spmo"] * ff.MktRF
             + calib["beta_mom_spmo"] * (ff.MOM - taglio * premio) - TER["spmo"] / 252.0)
        df = rolling(Serie(r.clip(lower=-1.0)), mesi)
        out[f"taglio_{int(taglio*100)}"] = dict(
            premio_annuo=float(calib["beta_mom_spmo"] * premio * (1 - taglio) * 252),
            mediana=float(df.finale.median()), p5=float(np.percentile(df.finale, 5)))
    return out


def in_euro(r, fx):
    """Gli stessi rendimenti visti da chi ha in tasca euro, non dollari.

    Un ETF americano quotato in dollari non ti espone al dollaro perche' e'
    quotato in dollari: ti espone perche' le aziende dentro incassano in dollari.
    Comprarlo in euro e rivenderlo in euro significa incassare anche il cambio.
    """
    x = fx.USD_per_EUR.reindex(r.index).ffill()   # dollari per euro
    valido = x.notna()
    var = x / x.shift(1)
    return ((1 + r[valido]) / var[valido] - 1).dropna()


def confronto_appaiato(dfs):
    """Sulle STESSE finestre, quante volte ognuno batte l'S&P 500 semplice."""
    base = dfs["sp500"].set_index("inizio").finale
    out = {}
    for k, df in dfs.items():
        s = df.set_index("inizio").finale
        comune = s.index.intersection(base.index)
        out[k] = dict(batte_sp500=float((s[comune] > base[comune]).mean()),
                      mediana_rapporto=float((s[comune] / base[comune]).median()),
                      peggiore_rapporto=float((s[comune] / base[comune]).min()))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    ff, px, cpi, fx = carica()
    r, calib, d = costruisci(ff, px)
    cpi_s = cpi.CPI
    serie = {k: Serie(r[k]) for k in ("sp500", "spmo", "spxl")}
    val = validazione(d, calib)

    print(f"\nFattori: {r.index[0].date()} -> {r.index[-1].date()}  ({len(r)} sedute)")
    print(f"Calibrazione su {calib['finestra']} ({calib['n_giorni']} sedute)\n")
    print(f"  S&P 500: beta {calib['beta_sp500']:.3f} su mercato USA, R2 {calib['r2_sp500']:.3f}")
    print(f"  SPMO   : beta mercato {calib['beta_mkt_spmo']:.3f}, beta momentum "
          f"{calib['beta_mom_spmo']:.3f}, R2 {calib['r2_spmo']:.3f}, "
          f"alpha campionario {calib['alpha_spmo']*100:+.2f}%/anno (azzerato nello studio)")
    print("\nVALIDAZIONE — serie ricostruita contro ETF reale (2016-2026)")
    print(f"  {'':8s}{'CAGR reale':>12}{'CAGR sint.':>12}{'vol reale':>11}{'vol sint.':>11}{'corr':>8}")
    for k, v in val.items():
        print(f"  {v['ticker']:8s}{v['cagr_reale']*100:11.2f}%{v['cagr_sintetico']*100:11.2f}%"
              f"{v['vol_reale']*100:10.1f}%{v['vol_sintetica']*100:10.1f}%{v['correlazione']:8.4f}")

    risultati = {"parametri": dict(pic=PIC, mensile=MENSILE, commissione=COMMISSIONE,
                                   inflazione=INFLAZIONE, ter=TER, spread_leva=SPREAD_LEVA),
                 "calibrazione": calib, "validazione": val,
                 "storico": {"da": str(r.index[0].date()), "a": str(r.index[-1].date())},
                 "orizzonti": {}}

    for anni in ORIZZONTI:
        mesi = anni * 12
        versato = PIC + MENSILE * mesi
        print(f"\n{'='*100}\nORIZZONTE {anni} ANNI — versati {versato:,.0f} EUR "
              f"({PIC:,.0f} subito + {MENSILE:,.0f} x {mesi} mesi)\n{'='*100}")
        print(f"{'':18s}{'finestre':>9}{'p5':>12}{'p25':>12}{'mediana':>12}{'p75':>12}"
              f"{'p95':>12}{'IRR med':>9}{'DD med':>8}{'P(perdita)':>11}")
        blocco, dfs = {}, {}
        for key in ("sp500", "spmo", "spxl"):
            df, mat = rolling(serie[key], mesi, cpi=cpi_s, percorsi=True)
            dfs[key] = df
            s = riassunto(df, mesi)
            blocco[key] = {"riassunto": s,
                           "finestre": df[["inizio", "finale", "reale", "irr", "maxdd", "moic"]]
                           .round(4).to_dict("list"),
                           "fascia": {f"p{p}": np.percentile(mat, p, axis=0).round(0).tolist()
                                      for p in (5, 25, 50, 75, 95)}}
            print(f"{NOMI[key]:18s}{s['n']:>9}{s['finale']['p5']:>12,.0f}"
                  f"{s['finale']['p25']:>12,.0f}{s['finale']['p50']:>12,.0f}"
                  f"{s['finale']['p75']:>12,.0f}{s['finale']['p95']:>12,.0f}"
                  f"{s['irr']['p50']*100:>8.1f}%{s['maxdd']['mediana']*100:>7.0f}%"
                  f"{s['p_perdita']*100:>10.1f}%")
        blocco["versato"] = [PIC + MENSILE * min(k + 1, mesi) for k in range(mesi + 1)]
        blocco["deterministico"] = {f"{int(t*100)}%": deterministico(t, mesi) for t in (0.05, 0.07, 0.10)}
        conf = confronto_appaiato(dfs)
        for key in ("spmo", "spxl"):
            blocco[key]["vs_sp500"] = conf[key]
            print(f"   {NOMI[key]:15s} batte l'S&P 500 nel {conf[key]['batte_sp500']*100:.0f}% "
                  f"delle finestre (rapporto mediano {conf[key]['mediana_rapporto']:.2f}x, "
                  f"peggiore {conf[key]['peggiore_rapporto']:.2f}x)")
        print(f"   in soldi di oggi (deflazionato con il CPI vero di ogni finestra): "
              f"mediana S&P 500 {blocco['sp500']['riassunto']['reale']['p50']:,.0f} EUR, "
              f"SPMO {blocco['spmo']['riassunto']['reale']['p50']:,.0f}, "
              f"SPXL {blocco['spxl']['riassunto']['reale']['p50']:,.0f}")
        risultati["orizzonti"][anni] = blocco

    # ---- e se il premio momentum si sgonfiasse?
    print(f"\n{'='*100}\nSENSIBILITA' — SPMO a 15 anni se il premio momentum si riduce\n{'='*100}")
    sm = sensibilita_momentum(ff, calib, 180)
    risultati["sensibilita_momentum"] = sm
    for k, v in sm.items():
        print(f"  premio momentum {'intero' if k=='taglio_0' else 'dimezzato' if k=='taglio_50' else 'azzerato':>10}"
              f"  ({v['premio_annuo']*100:+.2f}%/anno)  mediana {v['mediana']:>10,.0f} EUR"
              f"   p5 {v['p5']:>10,.0f} EUR")
    print(f"  (per confronto, S&P 500 a 15 anni: mediana "
          f"{risultati['orizzonti'][15]['sp500']['riassunto']['finale']['p50']:,.0f} EUR)")

    # ---- e se lo si guardasse da un conto in euro?
    print(f"\n{'='*100}\nSENSIBILITA' — lo stesso PAC visto in euro (cambio EUR/USD vero, dal 1999)\n{'='*100}")
    fxs = {}
    for key in ("sp500", "spmo", "spxl"):
        re_ = in_euro(r[key], fx)
        s_eur, s_usd = Serie(re_), Serie(r[key].reindex(re_.index))
        a = rolling(s_eur, 120).finale
        b = rolling(s_usd, 120).finale
        fxs[key] = dict(mediana_euro=float(a.median()), mediana_dollaro=float(b.median()),
                        n=int(len(a)), effetto=float(a.median() / b.median() - 1))
        print(f"  {NOMI[key]:18s} 10 anni, {fxs[key]['n']} finestre dal 1999: "
              f"mediana {a.median():>10,.0f} EUR  contro {b.median():>10,.0f} senza effetto cambio "
              f"({fxs[key]['effetto']*100:+.1f}%)")
    risultati["cambio"] = fxs

    # ---- e quanto ne resta dopo le tasse?
    print(f"\n{'='*100}\nTASSE — montante a 15 anni al netto, per regime (mediana delle finestre)\n{'='*100}")
    tax = {}
    for key in ("sp500", "spmo", "spxl"):
        s = serie[key]
        righe = []
        for i0 in range(s.n_mesi - 180):
            p = simula(s, i0, 180)
            if not p:
                continue
            g8 = s.mesi_idx[i0 + 96] - s.mesi_idx[i0]
            righe.append((p["valore"][-1], p["versato"][-1], p["valore"][g8], p["versato"][g8]))
        arr = np.array(righe)
        tax[key] = {reg: float(np.median([dopo_tasse(f, v, reg, 15, v8, vs8)
                                          for f, v, v8, vs8 in arr]))
                    for reg in ("lordo", "it26", "ie_cgt33", "ie_ucits41")}
        print(f"  {NOMI[key]:18s} lordo {tax[key]['lordo']:>11,.0f}   Italia 26% "
              f"{tax[key]['it26']:>11,.0f}   Irlanda CGT 33% {tax[key]['ie_cgt33']:>11,.0f}"
              f"   Irlanda UCITS 41% {tax[key]['ie_ucits41']:>11,.0f}")
    risultati["tasse"] = tax

    with open(os.path.join(OUT, "pac_results.json"), "w") as f:
        json.dump(risultati, f)
    print(f"\nScritto {os.path.join(OUT, 'pac_results.json')}")
    return risultati


if __name__ == "__main__":
    main()

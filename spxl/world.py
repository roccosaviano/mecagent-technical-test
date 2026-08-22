"""
COSTRUZIONE DEL MONDO DI SIMULAZIONE
====================================

Da csv grezzi a: un calendario, una serie di rendimenti per ogni strumento
negoziabile, un tasso a breve, e gli indicatori pronti per le strategie.

La decisione che conta e' qui dentro ed e' la GIUNTA fra SPXL sintetico e SPXL
reale. Dal 2008-11-05 in poi si usano i rendimenti veri del fondo, con tutti i
suoi difetti di replica. Prima si usa la sintesi, calibrata sul periodo in cui
i due coesistono. Se la sintesi non replicasse il fondo vero, la storia lunga
andrebbe buttata: per questo la verifica non e' opzionale e viene stampata.
"""
from __future__ import annotations
import numpy as np
import pandas as pd

from engine import (TRADING_DAYS, SPEC_SPXL, SPEC_SPXS, Instrument, LETFModel,
                    load_raw, build_index_total_return, build_rates,
                    fit_letf, valida_modello)


def _ret(df, col="AdjClose"):
    return df[col].astype(float).pct_change()


def ha_dividendi(df):
    """
    Il file e' corretto per le distribuzioni?

    Alcune fonti pubblicano solo il prezzo grezzo, con AdjClose uguale a Close.
    Usarle come rendimento totale toglierebbe in silenzio il dividendo, che su
    SPY vale un punto e mezzo l'anno: abbastanza da ribaltare qualunque
    confronto fra una strategia e il buy&hold. Meglio accorgersene qui.
    """
    if not {"AdjClose", "Close"} <= set(df.columns):
        return False
    return bool((df["AdjClose"].astype(float) - df["Close"].astype(float)).abs().max() > 1e-9)


def _div_component(df):
    """
    Quota di rendimento arrivata come distribuzione.

    AdjClose incorpora i dividendi reinvestiti, Close no: la differenza fra i
    due rendimenti e' il dividendo del giorno. In un conto tassabile quella
    parte si tassa ogni anno anche se non si vende mai, quindi va tenuta
    separata invece di sparire dentro il rendimento totale.
    """
    r_adj = df["AdjClose"].astype(float).pct_change()
    r_px = df["Close"].astype(float).pct_change()
    return (r_adj - r_px).clip(lower=0.0)


class World:
    """Tutto cio' che serve a lanciare un backtest, gia' allineato sul calendario."""

    def __init__(self, dates, ctx, instruments, cash_rate, cols, diagnostica):
        self.dates = dates
        self.ctx = ctx
        self.instruments = instruments
        self.cash_rate = cash_rate
        self.cols = cols
        self.diagnostica = diagnostica

    def slice(self, start=None, end=None):
        """Sottoperiodo, ricalcolando gli indicatori sulla finestra completa.

        Gli indicatori NON si ricalcolano sulla fetta: userebbero un warm-up
        cieco di 200 sedute all'inizio di ogni periodo out-of-sample. Si
        calcolano una volta sulla serie intera (guardano solo indietro, quindi
        non e' look-ahead) e poi si affetta il risultato.
        """
        m = np.ones(len(self.dates), dtype=bool)
        if start is not None:
            m &= self.dates >= pd.Timestamp(start)
        if end is not None:
            m &= self.dates <= pd.Timestamp(end)
        return np.nonzero(m)[0]


def build_world(verbose=True, letf_source="spliced"):
    """
    letf_source
      'spliced'  reale dal 2008-11, sintetico prima (predefinito)
      'synth'    sempre sintetico, per isolare l'effetto della replica
      'real'     solo il periodo in cui il fondo esiste davvero
    """
    raw = load_raw()
    for k in ("gspc",):
        if k not in raw:
            raise SystemExit(f"manca {k}.csv: rilancia fetch_data.py")

    idx = build_index_total_return(raw)
    dates = pd.DatetimeIndex(idx.index)
    rf = build_rates(raw, dates)

    diag = {}

    # ------------------------------------------------------------------
    # stima del modello di ogni fondo a leva sul suo storico reale
    # ------------------------------------------------------------------
    def _modello(key, spec):
        """
        Sceglie fra indice di prezzo e total return come base, e fra
        regressione libera e beta vincolato alla teoria, in base a chi replica
        meglio il fondo vero. La scelta e' fatta sui prezzi del PRODOTTO, non
        sui rendimenti di una strategia: non c'e' niente da sovradattare qui,
        si sta misurando quanto costa la leva.
        """
        if key not in raw:
            m = LETFModel.da_prospetto(spec)
            diag[spec.name] = {"stato": "nessuno storico reale, uso il prospetto",
                               "modello": repr(m)}
            return m, idx.r_tr
        real = _ret(raw[key]).reindex(dates)
        if real.notna().sum() < 400:
            m = LETFModel.da_prospetto(spec)
            diag[spec.name] = {"stato": "storico reale troppo corto", "modello": repr(m)}
            return m, idx.r_tr

        candidati = []
        for base_nome, base in (("prezzo", idx.r_px), ("total_return", idx.r_tr)):
            for vincola in (False, True):
                m = fit_letf(base, rf, real, spec.leva, spec.name, vincola)
                m.diag["base"] = base_nome
                candidati.append((m.diag["te_ann"], m, base))
        candidati.sort(key=lambda x: x[0])
        _, best, base = candidati[0]

        d = dict(best.diag)
        d["modello"] = repr(best)
        d["dentro_campione"] = valida_modello(best, base, rf, real)
        # verifica fuori campione: stima sulla prima meta', giudizio sulla seconda
        comune = base.index.intersection(real.dropna().index)
        meta = comune[len(comune) // 2]
        d["fuori_campione"] = valida_modello(best, base, rf, real, taglio=meta)
        d["alternative"] = [(m.diag["base"], m.origine, round(te, 5)) for te, m, _ in candidati]
        diag[spec.name] = d
        return best, base

    mod_l, base_l = _modello("spxl", SPEC_SPXL)
    mod_s, base_s = _modello("spxs", SPEC_SPXS)

    # ------------------------------------------------------------------
    # serie dei rendimenti per ogni strumento
    # ------------------------------------------------------------------
    def _build_letf(key, model, base):
        syn = pd.Series(model.returns(base, rf), index=dates)
        div = pd.Series(0.0, index=dates)
        if key in raw and not ha_dividendi(raw[key]):
            # fonte senza aggiustamento: i suoi rendimenti sarebbero il solo
            # prezzo, quindi sottostimati. Meglio il modello, che almeno e'
            # coerente con se stesso.
            diag.setdefault(model.name, {})["avviso"] = (
                "storico reale senza dividendi: uso il modello su tutto il periodo")
        elif key in raw and letf_source in ("spliced", "real"):
            real = _ret(raw[key]).reindex(dates)
            rdiv = _div_component(raw[key]).reindex(dates).fillna(0.0)
            inizio = real.first_valid_index()
            if letf_source == "real":
                syn, div = real.fillna(0.0), rdiv
            else:
                # dal primo giorno di quotazione in poi comandano i rendimenti
                # veri del fondo, con tutti i suoi difetti di replica
                syn = syn.where(dates < inizio, real.fillna(syn))
                div = div.where(dates < inizio, rdiv)
            diag.setdefault(model.name, {})["giunta"] = str(pd.Timestamp(inizio).date())
        return syn.fillna(0.0), div.fillna(0.0)

    r_spxl, d_spxl = _build_letf("spxl", mod_l, base_l)
    r_spxs, d_spxs = _build_letf("spxs", mod_s, base_s)

    # SPY: si usa il fondo reale solo se la fonte include i dividendi, altrimenti
    # l'indice total return, che li include per costruzione. Il dividendo resta
    # una colonna a parte perche' in un conto tassabile si paga ogni anno anche
    # a chi non vende mai.
    r_spy = idx.r_tr.copy()
    d_spy = (idx.r_tr - idx.r_px).clip(lower=0.0)
    if "spy" in raw and ha_dividendi(raw["spy"]):
        rs = _ret(raw["spy"]).reindex(dates)
        ds = _div_component(raw["spy"]).reindex(dates)
        first = rs.first_valid_index()
        r_spy = r_spy.where(dates < first, rs.fillna(r_spy))
        d_spy = d_spy.where(dates < first, ds.fillna(d_spy))

    instruments = [
        Instrument("SPXL", r_spxl.values, d_spxl.values),
        Instrument("SPXS", r_spxs.values, d_spxs.values),
        Instrument("SPY",  r_spy.values,  d_spy.values),
    ]
    cols = [i.name for i in instruments]

    from strategies import Ctx
    vix = raw["vix"]["Close"].astype(float).reindex(dates).ffill() if "vix" in raw else None
    vix3m = raw["vix3m"]["Close"].astype(float).reindex(dates).ffill() if "vix3m" in raw else None
    ctx = Ctx(dates, idx.px, idx.r_px, idx.r_tr, rf, vix, vix3m)

    w = World(dates, ctx, instruments, rf.values, cols, diag)

    if verbose:
        anni = len(dates) / TRADING_DAYS
        print(f"\nCalendario  {dates[0].date()} -> {dates[-1].date()}   "
              f"{len(dates)} sedute, {anni:.1f} anni")
        print(f"Tasso a breve  da {rf.iloc[0]:.2%} a {rf.iloc[-1]:.2%}, media {rf.mean():.2%}")
        print(f"Dividend yield indice  media {idx['yld'].mean():.2%}, "
              f"oggi {idx['yld'].iloc[-1]:.2%}")

        for nome, d in diag.items():
            print(f"\n--- {nome} " + "-" * (60 - len(nome)))
            if "modello" in d:
                print(f"  modello        {d['modello']}")
            if "stato" in d:
                print(f"  stato          {d['stato']}")
            if "beta" in d:
                print(f"  base indice    {d.get('base')}   "
                      f"stima su {d['giorni']} sedute ({d['da']} -> {d['a_data']})")
                print(f"  beta stimato   {d['beta']:+.2f}   teorico {d['beta_teorico']:+.2f}"
                      + ("   (vincolato)" if d.get("vincolato") else ""))
                print(f"  alpha          {d['alpha_ann']:+.2%} annuo "
                      f"(expense ratio + spread sugli swap)")
            for etichetta, chiave in (("dentro campione", "dentro_campione"),
                                      ("FUORI campione ", "fuori_campione")):
                v = d.get(chiave)
                if v:
                    print(f"  {etichetta}  {v['periodo']}  corr {v['corr']:.4f}  "
                          f"tracking error {v['te_ann']:.2%}  scarto {v['drift_ann']:+.2%}/anno  "
                          f"CAGR {v['cagr_syn']:+.1%} vs {v['cagr_real']:+.1%} reale")
            if "giunta" in d:
                print(f"  giunta         dati reali dal {d['giunta']}")
            if "avviso" in d:
                print(f"  AVVISO         {d['avviso']}")
    return w

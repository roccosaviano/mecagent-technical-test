"""
DATI PER LO STUDIO SU VIX E BREADTH (S5TH)
==========================================
Uso:  python3 market_data.py            # scarica/aggiorna la cache e scrive data/market_dataset.csv
      python3 market_data.py --no-breadth   # solo SPY + VIX (veloce, nessun download costituenti)

SORGENTI (tutte gratuite, nessuna API key)
  SPY   prezzi giornalieri dal 1993      -> stockanalysis.com  (proxy investibile dell'S&P 500)
  VIX   chiusura giornaliera dal 1990    -> FRED, serie VIXCLS
  VIX3M chiusura giornaliera dal 2007    -> FRED, serie VXVCLS (per la term structure)
  S5TH  % di titoli S&P 500 sopra la MA200 -> RICOSTRUITO, vedi sotto

PERCHE' S5TH VA RICOSTRUITO
  Il ticker S5TH (S&P 500 Members Above 200-Day Moving Average) e' un indice proprietario
  Bloomberg/S&P: non esiste un endpoint gratuito che ne dia la storia. Qui viene ricalcolato
  dal basso: composizione point-in-time dell'indice + prezzi dei singoli titoli.

  Composizione: lista storica giorno per giorno dal 1996 (repo pubblico fja05680/sp500,
  a sua volta derivata dal dataset di Clenow + aggiornamenti Wikipedia). Usare la
  composizione point-in-time invece di quella odierna elimina il look-ahead piu' grosso:
  se calcolassi la breadth del 2003 sui membri del 2026 starei misurando la salute di
  aziende selezionate perche' sono sopravvissute.

  Prezzi: stockanalysis.com ticker per ticker. Qui resta il limite vero: i titoli
  delistati/acquisiti spesso non hanno piu' storia disponibile gratuitamente. Per questo
  il dataset porta con se' la colonna COVER (quota di membri per cui il prezzo esiste):
  l'analisi va fatta solo dove COVER e' alta, e lo studio la taglia esplicitamente.

  La replica non sara' identica al S5TH di Bloomberg (che usa la sua definizione di
  membership intraday e i suoi aggiustamenti); serve a rispondere alla domanda
  "questa informazione e' predittiva?", non a fare arbitraggio sul decimale.
"""
import io, json, os, sys, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import requests

ROOT   = os.path.dirname(os.path.abspath(__file__))
CACHE  = os.path.join(ROOT, 'data_cache')
DATA   = os.path.join(ROOT, 'data')
PRICES = os.path.join(CACHE, 'prices')
# FRED chiude la connessione (timeout infinito) se lo User-Agent sembra un browser:
# per FRED e GitHub si lascia quello di default di requests, per stockanalysis serve un UA.
UA     = {'User-Agent': 'Mozilla/5.0 (research script; daily EOD data)'}
DATASET = os.path.join(DATA, 'market_dataset.csv')

PIT_URL = ('https://raw.githubusercontent.com/fja05680/sp500/master/'
           'S%26P%20500%20Historical%20Components%20%26%20Changes%20(Updated).csv')

for d in (CACHE, DATA, PRICES):
    os.makedirs(d, exist_ok=True)


# ------------------------------------------------------------------ HTTP + cache
def _get(url, path, ttl_days=5, tries=4, headers=None):
    """GET con cache su file. Rifa' la richiesta solo se il file manca o e' vecchio."""
    if os.path.exists(path):
        age = (time.time() - os.path.getmtime(path)) / 86400
        if age < ttl_days and os.path.getsize(path) > 0:
            return open(path, 'rb').read()
    err = None
    for k in range(tries):
        try:
            r = requests.get(url, headers=headers, timeout=90)
            if r.status_code == 200:
                open(path, 'wb').write(r.content)
                return r.content
            err = f'HTTP {r.status_code}'
        except Exception as e:                                    # rete instabile
            err = repr(e)
        time.sleep(2 ** k)
    if os.path.exists(path) and os.path.getsize(path) > 0:        # meglio vecchio che niente
        return open(path, 'rb').read()
    raise RuntimeError(f'{url} -> {err}')


def fred(series_id):
    """Serie giornaliera FRED come Series float indicizzata per data."""
    raw = _get(f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}',
               os.path.join(CACHE, f'fred_{series_id}.csv'))
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = ['date', 'v']
    s = pd.to_numeric(df.v, errors='coerce')                      # i festivi sono '.'
    s.index = pd.to_datetime(df.date)
    return s.dropna().rename(series_id)


def sa_history(symbol, ttl_days=5):
    """OHLC giornaliero completo da stockanalysis.com. None se il ticker non esiste piu'."""
    sym = symbol.replace('.', '-').replace('/', '-')              # BRK.B -> BRK-B
    path = os.path.join(PRICES, f'{sym}.json')
    url = f'https://stockanalysis.com/api/symbol/s/{sym}/history?range=Max&period=Daily'
    try:
        raw = _get(url, path, ttl_days=ttl_days, tries=2, headers=UA)
    except RuntimeError:
        open(path, 'w').write('{"status":404}')                   # negative caching
        return None
    try:
        rows = json.loads(raw).get('data')
    except Exception:
        return None
    if not rows:
        return None
    df = pd.DataFrame(rows)
    df.index = pd.to_datetime(df.t)
    out = pd.DataFrame(index=df.index.sort_values())
    for c_out, c_in in (('Open', 'o'), ('High', 'h'), ('Low', 'l'), ('Close', 'c'), ('Adj', 'a')):
        if c_in in df:
            out[c_out] = pd.to_numeric(df[c_in], errors='coerce').reindex(out.index)
    return out.dropna(subset=['Close'])


# ------------------------------------------------------------------ composizione indice
def sp500_membership():
    """DataFrame date -> set di ticker membri in quella data (point-in-time, dal 1996)."""
    raw = _get(PIT_URL, os.path.join(CACHE, 'sp500_pit.csv'), ttl_days=30)
    df = pd.read_csv(io.BytesIO(raw))
    df['date'] = pd.to_datetime(df.date)
    df['members'] = df.tickers.str.split(',').apply(lambda x: {t.strip() for t in x if t.strip()})
    return df.set_index('date').members.sort_index()


# ------------------------------------------------------------------ breadth (replica S5TH)
def build_breadth(ma=200, min_symbols=50, workers=4, verbose=True):
    """Ricostruisce % di membri S&P 500 sopra la propria media a `ma` giorni.

    Ritorna DataFrame con:
      BREADTH  percentuale di membri sopra la MA200 (0-100)
      COVER    quota di membri dell'indice per cui il prezzo esiste (0-1): il voto di fiducia
      NMEM     numero di membri con dato valido
    """
    mem = sp500_membership()
    universe = sorted(set().union(*mem.values))
    if verbose:
        print(f'[breadth] ticker mai entrati nell\'indice dal {mem.index[0].date()}: {len(universe)}')

    prices, missing = {}, []
    def work(t):
        try:
            h = sa_history(t)
        except Exception:
            h = None
        return t, (None if h is None or h.empty else h.Close)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        for i, (t, s) in enumerate(ex.map(work, universe), 1):
            if s is None: missing.append(t)
            else:         prices[t] = s
            if verbose and i % 100 == 0:
                print(f'[breadth] {i}/{len(universe)} scaricati, {len(missing)} senza storia')
    if verbose:
        print(f'[breadth] prezzi disponibili per {len(prices)}/{len(universe)} ticker '
              f'({100*len(prices)/len(universe):.0f}%)')

    px = pd.DataFrame(prices).sort_index()
    px = px[~px.index.duplicated(keep='last')]
    above = px > px.rolling(ma, min_periods=ma).mean()             # solo passato: nessun look-ahead
    have  = px.rolling(ma, min_periods=ma).mean().notna()          # chi ha abbastanza storia

    rows = []
    mem_dates = mem.index.values
    for day in px.index:
        j = np.searchsorted(mem_dates, np.datetime64(day), side='right') - 1
        if j < 0: continue
        members = [t for t in mem.iloc[j] if t in px.columns]
        if not members: continue
        h = have.loc[day, members]
        ok = [t for t in members if h[t]]
        if len(ok) < min_symbols: continue
        rows.append((day, 100 * above.loc[day, ok].mean(),
                     len(ok) / len(mem.iloc[j]), len(ok)))
    out = pd.DataFrame(rows, columns=['date', 'BREADTH', 'COVER', 'NMEM']).set_index('date')
    if verbose:
        print(f'[breadth] serie {out.index[0].date()} -> {out.index[-1].date()}, '
              f'copertura media {100*out.COVER.mean():.0f}%')
    return out


# ------------------------------------------------------------------ S5TH vero, se ce l'hai
def user_s5th():
    """Legge data/s5th.csv se esiste: export del S5TH vero da Bloomberg/TradingView.

    Formato: prima colonna la data, ultima colonna numerica il valore (0-100 o 0-1).
    Se c'e', lo studio lo usa al posto della replica e stampa la correlazione fra i due,
    che e' il modo piu' rapido per capire quanto vale la ricostruzione.
    """
    path = os.path.join(DATA, 's5th.csv')
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    num = [c for c in df.columns[1:] if pd.api.types.is_numeric_dtype(df[c])]
    if not num:
        return None
    dates = pd.to_datetime(df.iloc[:, 0], errors='coerce')
    s = pd.Series(pd.to_numeric(df[num[-1]], errors='coerce').to_numpy(), index=dates)
    s = s[s.index.notna()].dropna().sort_index()
    if s.max() <= 1.5:                                            # arriva in frazione, non in %
        s = s * 100
    return s.rename('S5TH_REAL')


# ------------------------------------------------------------------ dataset finale
def build_dataset(with_breadth=True, verbose=True):
    spy = sa_history('SPY')
    if spy is None:
        raise RuntimeError('SPY non scaricabile: controlla la rete')
    df = spy[['Open', 'High', 'Low', 'Close']].copy()
    # 'Adj' e' la chiusura aggiustata per dividendi e split: e' la serie total return,
    # quella con cui si confrontano onestamente strategie a esposizione diversa.
    df['ADJ']   = spy['Adj'] if 'Adj' in spy else spy['Close']
    df['VIX']   = fred('VIXCLS').reindex(df.index).ffill(limit=3)
    df['VIX3M'] = fred('VXVCLS').reindex(df.index).ffill(limit=3)
    if with_breadth:
        b = build_breadth(verbose=verbose)
        df = df.join(b)
    real = user_s5th()
    if real is not None:
        df['S5TH_REAL'] = real.reindex(df.index).ffill(limit=3)
        if verbose:
            print(f'[s5th] trovato data/s5th.csv: {real.index[0].date()} -> '
                  f'{real.index[-1].date()}, {len(real)} valori')
    df = df.dropna(subset=['Close', 'VIX'])
    df.index.name = 'Date'
    return df


def load_dataset(rebuild=False, with_breadth=True):
    """Il dataset committato se c'e', altrimenti lo ricostruisce dalle sorgenti."""
    if not rebuild and os.path.exists(DATASET):
        return pd.read_csv(DATASET, parse_dates=['Date'], index_col='Date')
    df = build_dataset(with_breadth=with_breadth)
    df.to_csv(DATASET, float_format='%.4f')
    return df


if __name__ == '__main__':
    df = build_dataset(with_breadth='--no-breadth' not in sys.argv)
    df.to_csv(DATASET, float_format='%.4f')
    print(f'\nscritto {DATASET}: {len(df)} sedute {df.index[0].date()} -> {df.index[-1].date()}')
    print(df.tail(3).to_string())

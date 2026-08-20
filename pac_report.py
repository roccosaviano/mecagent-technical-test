"""
DALLO STUDIO ALLA PAGINA
========================
Uso:  python3 pac_lab.py && python3 pac_report.py
      -> out/report.html   (pagina autonoma, nessuna risorsa esterna)

I grafici sono SVG generati qui: niente librerie, colori come variabili CSS
cosi' la pagina funziona in chiaro e in scuro. Sotto ogni grafico c'e' la
tabella con gli stessi numeri, che e' il modo piu' semplice per non dipendere
dal colore.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

SERIE = [("sp500", "S&P 500", "var(--s1)"),
         ("spmo", "SPMO momentum", "var(--s2)"),
         ("spxl", "SPXL 3x", "var(--s3)")]
NOME = {k: n for k, n, _ in SERIE}
COL = {k: c for k, _, c in SERIE}


# ---------------------------------------------------------------- formattazione
def eur(x, dec=0):
    """Formato italiano: punto per le migliaia, virgola per i decimali."""
    return f"{x:,.{dec}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def kilo(x):
    if x >= 1e6:
        return f"{x/1e6:.1f}M".replace(".0M", "M").replace(".", ",")
    if x >= 1e3:
        return f"{x/1e3:.0f}k"
    return f"{x:.0f}"


def pct(x, dec=0):
    return f"{x*100:.{dec}f}".replace(".", ",") + "%"


# ---------------------------------------------------------------- assi log
import math


def log_ticks(lo, hi):
    t = []
    e = math.floor(math.log10(lo))
    while 10 ** e <= hi * 1.5:
        for m in (1, 2, 5):
            v = m * 10 ** e
            if lo * 0.95 <= v <= hi * 1.05:
                t.append(v)
        e += 1
    return t


class LogX:
    def __init__(self, lo, hi, x0, x1):
        self.a, self.b, self.x0, self.x1 = math.log10(lo), math.log10(hi), x0, x1

    def __call__(self, v):
        v = max(v, 1e-9)
        return self.x0 + (math.log10(v) - self.a) / (self.b - self.a) * (self.x1 - self.x0)


class Lin:
    def __init__(self, lo, hi, x0, x1):
        self.lo, self.hi, self.x0, self.x1 = lo, hi, x0, x1

    def __call__(self, v):
        return self.x0 + (v - self.lo) / (self.hi - self.lo) * (self.x1 - self.x0)


# ---------------------------------------------------------------- grafico 1
def grafico_distribuzione(R):
    """Dove finisce il PAC: barra p5-p95, corpo p25-p75, tacca sulla mediana."""
    W, riga_h, pad_t = 860, 30, 34
    gruppi = [(a, R["orizzonti"][str(a)]) for a in (5, 10, 15)]
    H = pad_t + sum(len(SERIE) * riga_h + 52 for a, _ in gruppi) + 26
    L, Rt = 132, 34
    sc = LogX(20_000, 6_500_000, L, W - Rt)

    p = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" '
         f'aria-label="Distribuzione del montante finale per orizzonte e strumento">']
    for v in log_ticks(20_000, 6_500_000):
        x = sc(v)
        p.append(f'<line x1="{x:.1f}" y1="{pad_t-12}" x2="{x:.1f}" y2="{H-24}" class="grid"/>')
        p.append(f'<text x="{x:.1f}" y="{H-8}" class="tick mid">{kilo(v)}</text>')

    y = pad_t
    for anni, blocco in gruppi:
        versato = blocco["sp500"]["riassunto"]["versato"]
        xv = sc(versato)
        p.append(f'<text x="4" y="{y+4}" class="grouplab">{anni} anni</text>')
        p.append(f'<line x1="{xv:.1f}" y1="{y-10}" x2="{xv:.1f}" y2="{y+len(SERIE)*riga_h+4}" '
                 f'class="ref"/>')
        p.append(f'<text x="{xv:.1f}" y="{y-14}" class="reflab mid">versati {kilo(versato)} €</text>')
        for k, nome, col in SERIE:
            s = blocco[k]["riassunto"]["finale"]
            yy = y + riga_h * [i for i, (kk, _, _) in enumerate(SERIE) if kk == k][0] + 16
            a, b = sc(s["p5"]), sc(s["p95"])
            c, d = sc(s["p25"]), sc(s["p75"])
            m = sc(s["p50"])
            p.append(f'<g><title>{nome} — {anni} anni: mediana {eur(s["p50"])} €, '
                     f'da {eur(s["p5"])} (p5) a {eur(s["p95"])} (p95)</title>')
            p.append(f'<line x1="{a:.1f}" y1="{yy}" x2="{b:.1f}" y2="{yy}" '
                     f'stroke="{col}" stroke-width="2" stroke-linecap="round" opacity="0.45"/>')
            p.append(f'<rect x="{c:.1f}" y="{yy-6}" width="{max(d-c,2):.1f}" height="12" rx="4" '
                     f'fill="{col}" opacity="0.75"/>')
            p.append(f'<rect x="{m-1.5:.1f}" y="{yy-9}" width="3" height="18" rx="1.5" '
                     f'fill="{col}"/></g>')
            p.append(f'<text x="{L-10}" y="{yy+4}" class="rowlab end">{nome}</text>')
            p.append(f'<text x="{b+7:.1f}" y="{yy+4}" class="val">{kilo(s["p50"])}</text>')
        y += len(SERIE) * riga_h + 52
    p.append("</svg>")
    return "".join(p)


# ---------------------------------------------------------------- grafico 2
def grafico_per_partenza(R, anni=15):
    """Lo stesso PAC, cambiando solo il mese in cui parte."""
    W, H, L, Rt, T, B = 860, 380, 62, 116, 18, 44
    blocco = R["orizzonti"][str(anni)]
    versato = blocco["sp500"]["riassunto"]["versato"]
    tutti = [v for k, _, _ in SERIE for v in blocco[k]["finestre"]["finale"]]
    lo, hi = max(min(tutti), 5_000), max(tutti)
    sy = LogX(lo, hi, H - B, T)
    anni_x = [int(d[:4]) + (int(d[5:7]) - 1) / 12 for d in blocco["sp500"]["finestre"]["inizio"]]
    sx = Lin(min(anni_x), max(anni_x), L, W - Rt)

    p = [f'<svg viewBox="0 0 {W} {H}" class="chart" role="img" '
         f'aria-label="Montante a {anni} anni in funzione del mese di partenza">']
    for v in log_ticks(lo, hi):
        yy = sy(v)
        p.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{W-Rt}" y2="{yy:.1f}" class="grid"/>')
        p.append(f'<text x="{L-8}" y="{yy+4:.1f}" class="tick end">{kilo(v)}</text>')
    yv = sy(versato)
    p.append(f'<line x1="{L}" y1="{yv:.1f}" x2="{W-Rt}" y2="{yv:.1f}" class="ref"/>')
    p.append(f'<text x="{L+6}" y="{yv-7:.1f}" class="reflab">'
             f'capitale versato {kilo(versato)} €</text>')
    for d in range(1930, 2015, 10):
        if min(anni_x) <= d <= max(anni_x):
            x = sx(d)
            p.append(f'<line x1="{x:.1f}" y1="{T}" x2="{x:.1f}" y2="{H-B}" class="grid"/>')
            p.append(f'<text x="{x:.1f}" y="{H-B+18}" class="tick mid">{d}</text>')
    for k, nome, col in SERIE:
        pts = " ".join(f"{sx(a):.1f},{sy(v):.1f}"
                       for a, v in zip(anni_x, blocco[k]["finestre"]["finale"]))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="1.6" '
                 f'stroke-linejoin="round" opacity="0.92"><title>{nome}</title></polyline>')
        ultimo = blocco[k]["finestre"]["finale"][-1]
        p.append(f'<text x="{W-Rt+6}" y="{sy(ultimo)+4:.1f}" class="serielab" fill="{col}">{nome}</text>')
    p.append(f'<text x="{L}" y="{H-8}" class="tick">mese di partenza del PAC — '
             f'ogni punto è un PAC di {anni} anni intero</text>')
    p.append("</svg>")
    return "".join(p)


# ---------------------------------------------------------------- grafico 3
def grafico_fascia(R, anni=15):
    """Tre pannelli: mediana e fascia 5-95 del valore, mese per mese."""
    blocco = R["orizzonti"][str(anni)]
    versato = blocco["versato"]
    W, H = 286, 250
    L, Rt, T, B = 44, 10, 14, 34
    tutti = [v for k, _, _ in SERIE for v in blocco[k]["fascia"]["p95"]]
    lo, hi = 8_000, max(tutti)
    out = []
    for k, nome, col in SERIE:
        f = blocco[k]["fascia"]
        sy = LogX(lo, hi, H - B, T)
        sx = Lin(0, len(f["p50"]) - 1, L, W - Rt)
        p = [f'<svg viewBox="0 0 {W} {H}" class="chart small" role="img" '
             f'aria-label="Crescita del PAC su {nome}, mediana e fascia 5-95">']
        for v in log_ticks(lo, hi):
            yy = sy(v)
            p.append(f'<line x1="{L}" y1="{yy:.1f}" x2="{W-Rt}" y2="{yy:.1f}" class="grid"/>')
            p.append(f'<text x="{L-6}" y="{yy+4:.1f}" class="tick end">{kilo(v)}</text>')
        su = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(f["p95"]))
        giu = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in reversed(list(enumerate(f["p5"]))))
        p.append(f'<polygon points="{su} {giu}" fill="{col}" opacity="0.16"/>')
        for q, op, wdt in (("p25", 0.45, 1.2), ("p75", 0.45, 1.2)):
            pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(f[q]))
            p.append(f'<polyline points="{pts}" fill="none" stroke="{col}" '
                     f'stroke-width="{wdt}" opacity="{op}" stroke-dasharray="3 3"/>')
        pts = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(f["p50"]))
        p.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2"/>')
        vs = " ".join(f"{sx(i):.1f},{sy(v):.1f}" for i, v in enumerate(versato))
        p.append(f'<polyline points="{vs}" fill="none" class="ref-line"/>')
        for a in range(5, anni + 1, 5):
            x = sx(a * 12)
            p.append(f'<text x="{x:.1f}" y="{H-14}" class="tick mid">{a}a</text>')
        p.append(f'<text x="{L}" y="{T+2}" class="paneltitle" fill="{col}">{nome}</text>')
        p.append(f'<text x="{W-Rt}" y="{T+2}" class="tick end">mediana {kilo(f["p50"][-1])} €</text>')
        p.append("</svg>")
        out.append("".join(p))
    return out


# ---------------------------------------------------------------- tabelle
def tab_orizzonte(R, anni):
    b = R["orizzonti"][str(anni)]
    versato = b["sp500"]["riassunto"]["versato"]
    righe = []
    for k, nome, col in SERIE:
        s = b[k]["riassunto"]
        f, r = s["finale"], s["reale"]
        righe.append(f"""<tr>
          <th scope="row"><span class="dot" style="background:{col}"></span>{nome}</th>
          <td>{eur(f['p5'])}</td><td>{eur(f['p25'])}</td><td class="strong">{eur(f['p50'])}</td>
          <td>{eur(f['p75'])}</td><td>{eur(f['p95'])}</td>
          <td>{eur(r['p50'])}</td>
          <td>{pct(s['irr']['p50'],1)}</td>
          <td>{pct(s['maxdd']['mediana'])}</td>
          <td>{pct(s['p_perdita'],1)}</td></tr>""")
    return f"""<table>
      <caption>{anni} anni — {eur(versato)} € versati ({b['sp500']['riassunto']['n']} finestre storiche)</caption>
      <thead><tr><th scope="col">strumento</th><th scope="col">p5</th><th scope="col">p25</th>
      <th scope="col">mediana</th><th scope="col">p75</th><th scope="col">p95</th>
      <th scope="col">in € di oggi</th><th scope="col">IRR</th>
      <th scope="col">calo max</th>
      <th scope="col">P(&lt; versato)</th></tr></thead>
      <tbody>{''.join(righe)}</tbody></table>"""


def peggiore(R, anni, k):
    f = R["orizzonti"][str(anni)][k]["finestre"]
    i = min(range(len(f["finale"])), key=lambda j: f["finale"][j])
    return f["inizio"][i], f["finale"][i], f["irr"][i]


def migliore(R, anni, k):
    f = R["orizzonti"][str(anni)][k]["finestre"]
    i = max(range(len(f["finale"])), key=lambda j: f["finale"][j])
    return f["inizio"][i], f["finale"][i], f["irr"][i]


CSS = """
:root{
  color-scheme: light dark;
  --page:#f9f9f7; --surface:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781;
  --grid:#e1e0d9; --axis:#c3c2b7; --line:rgba(11,11,11,.10);
  --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --warn:#d03b3b;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --page:#0d0d0d; --surface:#1a1a19; --ink:#fff; --ink2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --line:rgba(255,255,255,.10);
  --s1:#3987e5; --s2:#d95926; --s3:#199e70; --warn:#e66767;
}}
:root[data-theme="dark"]{
  --page:#0d0d0d; --surface:#1a1a19; --ink:#fff; --ink2:#c3c2b7; --muted:#898781;
  --grid:#2c2c2a; --axis:#383835; --line:rgba(255,255,255,.10);
  --s1:#3987e5; --s2:#d95926; --s3:#199e70; --warn:#e66767;
}
*{box-sizing:border-box}
body{margin:0;background:var(--page);color:var(--ink);
  font:16px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased}
.wrap{max-width:940px;margin:0 auto;padding:40px 20px 80px}
header{margin:0 0 40px}
h1{font-size:34px;line-height:1.15;margin:0 0 10px;letter-spacing:-.02em}
h2{font-size:22px;margin:52px 0 6px;letter-spacing:-.01em}
h3{font-size:16px;margin:28px 0 6px}
p{margin:10px 0;color:var(--ink2)}
p.lead{font-size:18px;color:var(--ink)}
.sub{color:var(--muted);font-size:14px;margin:0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin:24px 0 8px}
.kpi{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 18px}
.kpi .lab{font-size:13px;color:var(--ink2);display:flex;align-items:center;gap:7px}
.kpi .num{font-size:30px;font-weight:600;letter-spacing:-.02em;margin:6px 0 2px}
.kpi .rng{font-size:13px;color:var(--muted)}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;flex:none}
figure{margin:22px 0 8px;background:var(--surface);border:1px solid var(--line);
  border-radius:12px;padding:16px 14px 10px;overflow-x:auto}
figcaption{font-size:13px;color:var(--muted);padding:2px 4px 0}
.chart{width:100%;height:auto;display:block}
.panels{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px}
.panels .chart{min-width:230px}
svg text{font:11px system-ui,-apple-system,sans-serif;fill:var(--muted)}
svg text.mid{text-anchor:middle} svg text.end{text-anchor:end}
svg text.rowlab{fill:var(--ink2);font-size:12px}
svg text.grouplab{fill:var(--ink);font-size:13px;font-weight:600}
svg text.val{fill:var(--ink2);font-size:11px;font-variant-numeric:tabular-nums}
svg text.serielab{font-size:11px;font-weight:600}
svg text.paneltitle{font-size:12px;font-weight:600}
svg text.reflab{fill:var(--muted);font-size:10.5px}
svg .grid{stroke:var(--grid);stroke-width:1}
svg .ref{stroke:var(--axis);stroke-width:1;stroke-dasharray:4 3}
svg .ref-line{stroke:var(--axis);stroke-width:1.4;stroke-dasharray:4 3;fill:none}
table{width:100%;border-collapse:collapse;font-size:13px;margin:14px 0 6px;
  font-variant-numeric:tabular-nums}
caption{text-align:left;font-size:13px;color:var(--muted);padding:6px 0 8px}
th,td{padding:6px 7px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th[scope=col]{color:var(--muted);font-weight:500;font-size:12px;text-align:right;
  border-bottom:1px solid var(--axis)}
thead th:first-child{text-align:left}
th[scope=row]{text-align:left;font-weight:500;display:flex;align-items:center;gap:8px;
  border-bottom:0}
tbody tr:last-child td{border-bottom:0}
td.strong{font-weight:600;color:var(--ink)}
.scroll{overflow-x:auto;margin:0 -2px}
.note{border-left:3px solid var(--axis);padding:2px 0 2px 16px;margin:18px 0}
.warnbox{border-left:3px solid var(--warn);padding:2px 0 2px 16px;margin:18px 0}
.warnbox strong{color:var(--ink)}
ul{color:var(--ink2);padding-left:20px} li{margin:6px 0}
footer{margin-top:56px;padding-top:18px;border-top:1px solid var(--line);
  font-size:13px;color:var(--muted)}
code{font:13px ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--surface);
  border:1px solid var(--line);border-radius:5px;padding:1px 5px}
"""


def pagina(R):
    q = R["orizzonti"]
    par = R["parametri"]
    kpis = []
    for k, nome, col in SERIE:
        s = q["15"][k]["riassunto"]
        kpis.append(f"""<div class="kpi"><div class="lab"><span class="dot"
          style="background:{col}"></span>{nome}</div>
          <div class="num">{eur(s['finale']['p50'])} €</div>
          <div class="rng">da {eur(s['finale']['p5'])} a {eur(s['finale']['p95'])} €
          &nbsp;·&nbsp; calo max tipico {pct(s['maxdd']['mediana'])}</div></div>""")

    fasce = grafico_fascia(R, 15)
    sm = R["sensibilita_momentum"]
    tax = R["tasse"]
    val = R["validazione"]
    cal = R["calibrazione"]
    fx = R["cambio"]

    pw15 = {k: peggiore(R, 15, k) for k, _, _ in SERIE}
    pw10 = {k: peggiore(R, 10, k) for k, _, _ in SERIE}
    mb15 = {k: migliore(R, 15, k) for k, _, _ in SERIE}

    tab_tasse = "".join(
        f"""<tr><th scope="row"><span class="dot" style="background:{c}"></span>{n}</th>
        <td>{eur(tax[k]['lordo'])}</td><td>{eur(tax[k]['it26'])}</td>
        <td>{eur(tax[k]['ie_cgt33'])}</td><td>{eur(tax[k]['ie_ucits41'])}</td></tr>"""
        for k, n, c in SERIE)

    tab_val = "".join(
        f"""<tr><th scope="row">{val[k]['ticker']}</th>
        <td>{pct(val[k]['cagr_reale'],2)}</td><td>{pct(val[k]['cagr_sintetico'],2)}</td>
        <td>{pct(val[k]['vol_reale'],1)}</td><td>{pct(val[k]['vol_sintetica'],1)}</td>
        <td>{val[k]['correlazione']:.4f}</td></tr>""" for k, _, _ in SERIE)

    tab_mom = "".join(
        f"""<tr><th scope="row">{lab}</th><td>{pct(sm[key]['premio_annuo'],2)}</td>
        <td>{eur(sm[key]['mediana'])}</td><td>{eur(sm[key]['p5'])}</td></tr>"""
        for key, lab in (("taglio_0", "premio storico intero"),
                         ("taglio_50", "premio dimezzato"),
                         ("taglio_100", "premio azzerato")))

    tab_peggio = "".join(
        f"""<tr><th scope="row"><span class="dot" style="background:{c}"></span>{n}</th>
        <td>{pw15[k][0][:7]}</td><td>{eur(pw15[k][1])}</td><td>{pct(pw15[k][2],1)}</td>
        <td>{mb15[k][0][:7]}</td><td>{eur(mb15[k][1])}</td></tr>"""
        for k, n, c in SERIE)

    return f"""<title>PAC 700 + 10k</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>{CSS}</style>
<div class="wrap">
<header>
  <h1>10.000 € subito, 700 € al mese: dove si va a finire</h1>
  <p class="sub">S&amp;P 500, SPMO (momentum) e SPXL (3x) su 5, 10 e 15 anni — simulati su
  ogni mese di partenza dal 1926 a oggi ({q['15']['sp500']['riassunto']['n']} PAC interi per
  strumento sull'orizzonte lungo), non su un rendimento medio inventato.</p>
</header>

<p class="lead">Su 15 anni versi <strong>136.000 €</strong>. Questo è il montante mediano
che i tre strumenti hanno prodotto sui cento anni di storia disponibili, con accanto il
quinto e il novantacinquesimo percentile: non è una previsione, è l'intervallo dentro
cui si è sempre finiti.</p>

<div class="kpis">{''.join(kpis)}</div>
<p class="sub">Valori nominali lordi di tasse. La stessa cosa in potere d'acquisto di oggi:
{eur(q['15']['sp500']['riassunto']['reale']['p50'])} · {eur(q['15']['spmo']['riassunto']['reale']['p50'])} ·
{eur(q['15']['spxl']['riassunto']['reale']['p50'])} €.</p>

<h2>La forma del risultato</h2>
<p>Ogni barra è la distribuzione dei montanti finali: la parte piena è metà dei casi
(dal 25° al 75° percentile), la linea sottile arriva dal 5° al 95°, la tacca è la mediana.
La riga tratteggiata è il capitale versato: a sinistra di quella riga hai perso soldi.</p>
<figure>{grafico_distribuzione(R)}
<figcaption>Montante finale in euro, scala logaritmica — senza logaritmo la barra di
SPXL renderebbe invisibili le altre due, ed è già un'informazione.</figcaption></figure>

<div class="scroll">{tab_orizzonte(R, 5)}{tab_orizzonte(R, 10)}{tab_orizzonte(R, 15)}</div>
<p class="sub">«in € di oggi» = la mediana deflazionata con l'inflazione vera di ogni
finestra. «calo max» = quanto è sceso il portafoglio dal suo massimo, nella finestra mediana:
sul PAC mediano a 15 anni sono {eur(q['15']['sp500']['riassunto']['maxdd_eur']['mediana'])} €
sull'S&amp;P 500 e {eur(q['15']['spxl']['riassunto']['maxdd_eur']['mediana'])} € su SPXL.
«IRR» è il rendimento monetario annuo, l'unico corretto quando versi ogni mese.</p>

<h2>Il mese in cui parti conta più di quanto pensi</h2>
<p>Stesso strumento, stessa durata, stesso versamento: cambia solo la data di partenza.
Su un PAC di 15 anni in S&amp;P 500 il divario fra il peggior punto d'ingresso e il migliore
è di cinque volte. Su SPXL è di cinquecento.</p>
<figure>{grafico_per_partenza(R, 15)}
<figcaption>Ogni punto è un PAC di 15 anni completo, posizionato sul mese in cui è
partito. Ultimo punto utile: {q['15']['sp500']['finestre']['inizio'][-1][:7]}.</figcaption></figure>

<div class="scroll"><table>
<caption>Le due estremità, 15 anni, 136.000 € versati</caption>
<thead><tr><th scope="col">strumento</th><th scope="col">peggior partenza</th>
<th scope="col">montante</th><th scope="col">IRR</th>
<th scope="col">miglior partenza</th><th scope="col">montante</th></tr></thead>
<tbody>{tab_peggio}</tbody></table></div>
<p class="sub">Il PAC in SPXL partito nel {pw15['spxl'][0][:7]} ha versato 136.000 € e ne ha
riportati {eur(pw15['spxl'][1])}: aveva accumulato per sei anni, ha perso il 99% fra il 2000
e il 2002, e ha finito sul fondo del 2009. Su 10 anni il peggior caso è
{eur(pw10['spxl'][1])} da 94.000 € versati.</p>

<h2>Come ci si arriva</h2>
<p>Il montante finale non dice cosa devi sopportare per ottenerlo. Qui c'è il valore del
portafoglio mese per mese: linea piena la mediana, tratteggiate il 25° e 75°, area chiara
dal 5° al 95°. La riga grigia è il capitale versato.</p>
<div class="panels">{''.join(fasce)}</div>
<p class="sub">Stessa scala logaritmica nei tre pannelli, quindi le pendenze sono
confrontabili. Su SPXL la fascia si apre da subito e non si richiude più: è la firma
della leva, che non aumenta il rendimento atteso in proporzione ma la dispersione sì.</p>

<h2>SPMO: tutto il vantaggio sta in un numero solo</h2>
<p>Nella simulazione SPMO batte l'S&amp;P 500 nell'{pct(q['15']['spmo']['vs_sp500']['batte_sp500'])}
delle finestre a 15 anni. Ma quel vantaggio non arriva da un'abilità del gestore: arriva
dal premio storico del fattore momentum moltiplicato per l'esposizione di SPMO
({eur(cal['beta_mom_spmo'],2)}). Se quel premio si dimezza — e negli ultimi vent'anni, al netto
dei costi di implementazione, si è compresso — metà del vantaggio sparisce. Se va a zero,
SPMO è l'S&amp;P 500 con lo 0,33% di commissioni e un po' più di rischio specifico.</p>
<div class="scroll"><table>
<caption>SPMO a 15 anni al variare del premio momentum (mediana S&amp;P 500 di riferimento:
{eur(q['15']['sp500']['riassunto']['finale']['p50'])} €)</caption>
<thead><tr><th scope="col">ipotesi</th><th scope="col">contributo del momentum</th>
<th scope="col">mediana</th><th scope="col">p5</th></tr></thead>
<tbody>{tab_mom}</tbody></table></div>
<div class="note"><p>L'alpha vero e proprio di SPMO nel decennio 2016-2026 è
{pct(cal['alpha_spmo'],2)} l'anno: enorme, e nello studio è stato <strong>azzerato</strong>.
Portarlo avanti per quindici anni avrebbe raddoppiato i numeri di SPMO senza uno straccio
di motivo per crederci.</p></div>

<h2>SPXL: cosa deve andare storto</h2>
<div class="warnbox">
<p><strong>Il 3x non è «l'S&amp;P 500 moltiplicato per tre».</strong> Replica tre volte il
movimento <em>giornaliero</em>, e ogni sera si riazzera. In un mercato che oscilla senza
andare da nessuna parte perde valore anche se l'indice torna al punto di partenza: dopo
un -10% e un +11,1% l'indice è pari, il 3x è sotto del 3%. Più la volatilità è alta,
più questo attrito morde.</p>
<p><strong>Paghi il denaro che non hai.</strong> Su ogni euro investito ce ne sono due presi
a prestito: il costo è il tasso a breve più uno spread. Con i tassi al 5% sono circa il
10% l'anno di zavorra prima ancora di guardare il mercato. Nel 1981 questo da solo bastava
a distruggere il prodotto.</p>
<p><strong>Il calo tipico è {pct(q['15']['spxl']['riassunto']['maxdd']['mediana'])}</strong>,
il peggiore {pct(q['15']['spxl']['riassunto']['maxdd']['peggiore'])}, e in euro sul portafoglio
mediano a 15 anni vuol dire vedere sparire
{eur(q['15']['spxl']['riassunto']['maxdd_eur']['mediana'])} €. Nella storia simulata non
succede mai che vada a zero in un giorno solo — servirebbe un -33,3% dell'indice, e il record
è -20,5% nel 1987 — ma nel {pct(q['15']['spxl']['riassunto']['p_perdita'],1)} delle finestre
a 15 anni si finisce sotto il capitale versato, contro lo
{pct(q['15']['sp500']['riassunto']['p_perdita'],1)} dell'S&amp;P 500.</p>
</div>
<p>Detto questo, i numeri non dicono «mai»: dicono che su 15 anni la mediana è
{eur(q['15']['spxl']['riassunto']['finale']['p50'])} € contro
{eur(q['15']['sp500']['riassunto']['finale']['p50'])} €, e che nel
{pct(q['15']['spxl']['vs_sp500']['batte_sp500'])} delle finestre ha vinto. È una scommessa
con valore atteso alto e coda sinistra che ti può togliere quindici anni di risparmi.
La dimensione sensata non è «tutto o niente»: è una quota che puoi permetterti di
azzerare senza cambiare i tuoi piani.</p>

<h2>Cosa si mangia il risultato</h2>
<div class="scroll"><table>
<caption>Montante mediano a 15 anni, al netto delle tasse sul capital gain</caption>
<thead><tr><th scope="col">strumento</th><th scope="col">lordo</th>
<th scope="col">Italia 26%</th><th scope="col">Irlanda CGT 33%</th>
<th scope="col">Irlanda UCITS 41% + deemed disposal</th></tr></thead>
<tbody>{tab_tasse}</tbody></table></div>
<ul>
<li><strong>Il regime fiscale pesa più della scelta fra S&amp;P 500 e SPMO.</strong> Fra
Italia 26% e Irlanda 41% con deemed disposal a 8 anni ballano
{eur(tax['sp500']['it26'] - tax['sp500']['ie_ucits41'])} € sullo stesso PAC in S&amp;P 500:
più di quanto separa l'S&amp;P 500 da SPMO al lordo.</li>
<li><strong>SPMO e SPXL sono ETF americani.</strong> Senza KID in italiano un broker europeo
non te li vende al dettaglio: si arriva agli stessi fattori con UCITS equivalenti (momentum:
iShares o Xtrackers MSCI USA Momentum; leva: certificati/ETP a leva 3x, che però sono
strumenti di debito con rischio emittente e costi di finanziamento peggiori). Le simulazioni
qui usano i prodotti americani: sui sostituti europei togli qualche decimo di punto l'anno.</li>
<li><strong>Il cambio.</strong> Versi euro, l'attivo sta in dollari. Sulle finestre a 10 anni
dal 1999 il cambio ha <em>aggiunto</em> il {pct(fx['sp500']['effetto'],1)} al risultato in
euro: è stato un colpo di fortuna, non una regola, e nei prossimi quindici anni può
benissimo essere lo stesso numero col segno meno.</li>
<li><strong>Le commissioni.</strong> Nello studio c'è {eur(par['commissione'],0)} € per
ordine mensile — lo 0,14% del versamento. Se il tuo broker ne prende 5 con lo 0,25% di
cambio valuta, su 15 anni è come pagare un altro mezzo punto di TER.</li>
</ul>

<h2>Come sono stati costruiti i numeri</h2>
<p>La domanda «quanto avrò fra 15 anni» non ha una risposta singola, e un simulatore che
te ne dà una sta scegliendo un rendimento medio al posto tuo. Qui si è fatto il contrario:
si è preso ogni singolo mese dal 1926 a oggi, si è fatto partire da lì un PAC completo
(10.000 € più 700 € al mese fino alla fine dell'orizzonte) e si sono raccolti tutti i
risultati. La mediana è il centro di quella nuvola, i percentili sono i suoi bordi.</p>
<p>Gli ETF di cui parliamo non esistevano nel 1926 (SPMO è del 2015, SPXL del 2008): le
serie lunghe sono <em>ricostruite</em> dai fattori di rendimento del mercato americano
(dati Fama-French, che includono i dividendi) usando i pesi stimati sui dieci anni di
storia vera dei tre prodotti. Il controllo che conta è questo: la ricostruzione, applicata
al periodo in cui gli ETF veri esistono, deve riprodurli.</p>
<div class="scroll"><table>
<caption>Ricostruzione contro ETF reale, {cal['finestra']} ({cal['n_giorni']} sedute)</caption>
<thead><tr><th scope="col">ETF</th><th scope="col">rendimento annuo vero</th>
<th scope="col">ricostruito</th><th scope="col">volatilità vera</th>
<th scope="col">ricostruita</th><th scope="col">correlazione giornaliera</th></tr></thead>
<tbody>{tab_val}</tbody></table></div>
<h3>Dove il modello è debole</h3>
<ul>
<li>Cento anni di storia americana sono <em>un solo</em> percorso, per giunta quello del
paese che ha vinto il secolo. Le finestre si sovrappongono, quindi «l'88% delle volte» non
è una probabilità: è una frequenza su campioni parenti fra loro.</li>
<li>SPMO è replicato con mercato + momentum, che spiegano l'{pct(cal['r2_spmo'],0)} della sua
varianza giornaliera; il resto è stato rimesso come rumore pescato dai residui veri, con
seme fisso. Non è lo stesso SPMO, è un fondo con la stessa esposizione ai fattori.</li>
<li>Il costo della leva è modellato come tasso a breve + {pct(par['spread_leva'],2)}. È
tarato sul 2016-2026 e riproduce SPXL con {pct(abs(val['spxl']['scarto_annuo']),2)} di scarto
annuo; nei periodi di tassi altissimi (1979-1982) potrebbe essere ottimista.</li>
<li>Tutto è al lordo del bollo titoli (0,2% l'anno in Italia) e assume che i versamenti
non vengano mai interrotti — l'ipotesi più fragile di tutte, visto che il caso peggiore
qui dentro chiede di continuare a versare 700 € al mese dentro un -80%.</li>
</ul>

<footer>Ricostruzione su dati Fama-French (Dartmouth), prezzi Nasdaq, CPI e cambio FRED.
Riproducibile con <code>python3 pac_data.py &amp;&amp; python3 pac_lab.py &amp;&amp;
python3 pac_report.py</code>. Non è consulenza finanziaria: è un banco di prova.</footer>
</div>"""


def main():
    R = json.load(open(os.path.join(OUT, "pac_results.json")))
    p = os.path.join(OUT, "report.html")
    with open(p, "w") as f:
        f.write(pagina(R))
    print(f"Scritto {p} ({os.path.getsize(p)/1024:.0f} KB)")


if __name__ == "__main__":
    main()

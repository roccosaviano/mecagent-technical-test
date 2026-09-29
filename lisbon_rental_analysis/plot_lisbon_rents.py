"""Affitti vs affitti brevi (Alojamento Local) vs inflazione a Lisbona, 2014-2025.

Fonti:
  - Affitti: INE Portugal, "Valor mediano das rendas de novos contratos de
    arrendamento de alojamentos familiares (€/m²)", comune di Lisbona.
    Indicatori 0009631 (2017-2023, cod. 1701106) e 0012600 (2020-2024, cod. 1A01106);
    gli anni in comune coincidono. Il sito INE blocca le connessioni automatiche,
    quindi i valori sono trascritti qui sotto.
  - Affitti brevi: Registo Nacional de Alojamento Local (RNAL), Turismo de Portugal,
    API https://webservices.turismodeportugal.pt/RNT_External/rest/RNT/list_RNAL?Concelho=Lisboa
    (contiene solo le registrazioni ATTIVE oggi: quelle cancellate non compaiono).
  - Inflazione: Eurostat HICP Portogallo, indice medio annuo (prc_hicp_aind, CP00).
"""
import collections
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import requests

HERE = Path(__file__).parent
RNAL_URL = "https://webservices.turismodeportugal.pt/RNT_External/rest/RNT/list_RNAL?Concelho=Lisboa"
HICP_URL = ("https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
            "prc_hicp_aind?geo=PT&coicop=CP00&unit=INX_A_AVG")

# INE, mediana €/m² nuovi contratti d'affitto, comune di Lisbona
RENT_EUR_M2 = {2017: 9.62, 2018: 11.16, 2019: 11.96, 2020: 11.46,
               2021: 11.24, 2022: 12.88, 2023: 15.22, 2024: 15.93}

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def fetch_hicp() -> pd.Series:
    d = requests.get(HICP_URL, timeout=60).json()
    idx = d["dimension"]["time"]["category"]["index"]
    return pd.Series({int(y): d["value"][str(i)] for y, i in idx.items() if str(i) in d["value"]})


def fetch_al_registrations() -> pd.Series:
    """Nuove registrazioni AL per anno (solo aggregati: nessun dato personale salvato)."""
    rows = requests.get(RNAL_URL, timeout=300).json()
    years = collections.Counter(int(r["RNAL_Registo"]["DataRegisto"][:4]) for r in rows)
    return pd.Series(years).sort_index()


def main() -> None:
    hicp = fetch_hicp()
    al_new = fetch_al_registrations()
    al_stock = al_new.cumsum()

    years = range(2014, 2026)
    df = pd.DataFrame(index=pd.Index(years, name="anno"))
    df["affitto_eur_m2"] = pd.Series(RENT_EUR_M2)
    df["hicp"] = hicp
    df["al_nuove_registrazioni"] = al_new.reindex(years, fill_value=0)
    df["al_stock_attivi_oggi"] = al_stock.reindex(years, method="ffill")
    df["affitto_idx_2017"] = df.affitto_eur_m2 / RENT_EUR_M2[2017] * 100
    df["hicp_idx_2017"] = df.hicp / hicp[2017] * 100
    df["affitto_reale_idx_2017"] = df.affitto_idx_2017 / df.hicp_idx_2017 * 100
    df.round(2).to_csv(HERE / "lisbon_data.csv")
    print(df.round(1).to_string())

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.5), sharex=True,
                                   gridspec_kw={"height_ratios": [3, 2], "hspace": 0.12})
    for ax in (ax1, ax2):
        ax.set_facecolor("white")
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.tick_params(colors=INK2, labelsize=10, length=0)
        for s in ax.spines.values():
            s.set_visible(False)
        ax.spines["bottom"].set_visible(True)
        ax.spines["bottom"].set_color(GRID)
        ax.axvspan(2019.75, 2021.5, color="#f1f0ec", zorder=0)  # COVID

    r = df.dropna(subset=["affitto_idx_2017"])
    lines = [
        (r.affitto_idx_2017, BLUE, "-", "Affitto nuovi contratti Lisbona (nominale)"),
        (r.affitto_reale_idx_2017, BLUE, "--", "Affitto al netto dell'inflazione"),
        (df.hicp_idx_2017.dropna().loc[2017:], ORANGE, "-", "Inflazione (HICP Portogallo)"),
    ]
    for s, c, ls, label in lines:
        ax1.plot(s.index, s.values, color=c, ls=ls, lw=2, marker="o", ms=5,
                 markeredgecolor="white", markeredgewidth=1.5, label=label)
        ax1.annotate(f"{s.iloc[-1]:.0f}", (s.index[-1], s.iloc[-1]), xytext=(6, 0),
                     textcoords="offset points", va="center", fontsize=10, color=INK)
    ax1.axhline(100, color=INK2, lw=0.8)
    ax1.set_ylabel("Indice, 2017 = 100", color=INK2)
    ax1.legend(frameon=False, loc="upper left", fontsize=10, labelcolor=INK)
    ax1.set_title("Lisbona: affitti, affitti brevi e inflazione", loc="left",
                  fontsize=15, color=INK, fontweight="bold", pad=26)
    ax1.text(0, 1.02, "Mediana €/m² dei nuovi contratti: 9,62 € (2017) → 15,93 € (2024), +66% "
             "contro +19% di inflazione", transform=ax1.transAxes, fontsize=10.5, color=INK2)
    ax1.text(2020.625, 165, "COVID", ha="center", fontsize=9, color=INK2)

    ax2.bar(df.index, df.al_nuove_registrazioni, color=AQUA, width=0.7, zorder=2)
    for x, v in df.al_nuove_registrazioni.items():
        if v > 0:
            ax2.annotate(f"{v:,}".replace(",", "."), (x, v), xytext=(0, 3),
                         textcoords="offset points", ha="center", fontsize=9, color=INK)
    ax2.set_ylabel("Nuove registrazioni AL\n(ancora attive oggi)", color=INK2)
    ax2.annotate("nov. 2018: stop a nuove\nlicenze nei quartieri storici",
                 (2018.35, 3500), xytext=(2019.2, 3200), fontsize=9, color=INK2,
                 arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax2.annotate("2023: Mais Habitação\n(congelamento nuove licenze)",
                 (2023.2, 450), xytext=(2022.6, 1700), fontsize=9, color=INK2,
                 arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax2.set_xticks(list(years))

    fig.text(0.125, 0.015,
             "Fonti: INE Portugal (rendas de novos contratos, comune di Lisbona); Turismo de Portugal, "
             "RNAL (registrazioni attive oggi, per anno di registrazione);\nEurostat HICP. "
             "Stock AL attivo oggi a Lisbona: " + f"{int(al_stock.iloc[-1]):,}".replace(",", ".") +
             " unità. Le licenze cancellate non sono nel registro, quindi gli anni passati sono sottostimati.",
             fontsize=8, color=INK2)
    fig.savefig(HERE / "lisbon_rents_al_inflation.png", dpi=160, bbox_inches="tight",
                facecolor="white")


if __name__ == "__main__":
    main()

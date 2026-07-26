#!/usr/bin/env bash
# Riscarica tutte le fonti in quant/data/. Nessuna richiede registrazione.
set -euo pipefail
D="$(dirname "$0")/data"; mkdir -p "$D"; cd "$D"
FF="https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp"
for f in F-F_Research_Data_Factors_daily_CSV F-F_Momentum_Factor_daily_CSV \
         49_Industry_Portfolios_daily_CSV 49_Industry_Portfolios_CSV \
         F-F_Research_Data_Factors_CSV F-F_Momentum_Factor_CSV \
         Portfolios_Formed_on_ME_CSV; do
  curl -sSL -o "$f.zip" "$FF/$f.zip" && unzip -oq "$f.zip" -d "$f"
done
curl -sSL -o bab.xlsx \
  "https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Betting-Against-Beta-Equity-Factors-Monthly.xlsx"
curl -sSL -o ie_data.xls \
  "https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/downloads/ie_data.xls"
# Open Source Asset Pricing (Chen & Zimmermann), ospitato su Google Drive
gd() { curl -sSL -o "$2" "https://drive.usercontent.google.com/download?id=$1&export=download&confirm=t"; }
gd 10sOryk_ddjkXagaajTKUk1nwJs2ZLRiI osap_ls_wide.csv
gd 1Sev9s6cPFUGgxp1pFiej0lGzpsMqJCI2 osap_signaldoc.csv
gd 1g7w-yQ6Cg2qbMEkER9Q3vgns4JszXQo6 osap_ports.csv
echo "fatto: $(ls | wc -l) elementi in $D"

# --- fonti multi-asset per la ricerca iterativa
curl -sSL -o "$D/aqr_century.xlsx" "$A/Century-of-Factor-Premia-Monthly.xlsx" 2>/dev/null || \
curl -sSL -o aqr_century.xlsx "https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Century-of-Factor-Premia-Monthly.xlsx"
curl -sSL -o aqr_vme.xlsx "https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Value-and-Momentum-Everywhere-Factors-Monthly.xlsx"
curl -sSL -o aqr_tsmom.xlsx "https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/Time-Series-Momentum-Factors-Monthly.xlsx"
for f in Developed_3_Factors Emerging_5_Factors Europe_3_Factors Japan_3_Factors Asia_Pacific_ex_Japan_3_Factors; do
  curl -sSL -o "$f.zip" "$FF/${f}_CSV.zip" && unzip -oq "$f.zip" -d "$f"
done
curl -sSL -o fred_DGS10.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"

# --- OHLCV reale (Twelve Data, chiave demo: solo AAPL e QQQ)
for spec in "QQQ 1day" "AAPL 1day" "QQQ 1h" "QQQ 15min"; do
  set -- $spec
  curl -sS "https://api.twelvedata.com/time_series?symbol=$1&interval=$2&apikey=demo&outputsize=5000&format=CSV&delimiter=," -o "td_$1_$2.csv"
done
curl -sSL -o fred_NASDAQCOM.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQCOM"
curl -sSL -o fred_NASDAQ100.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=NASDAQ100"

# --- crypto OHLCV multi-asset (OKX, senza chiave)
python3 "$(dirname "$0")/src/research/fetch_crypto.py" 2>/dev/null || true

# --- indici CBOE delle strategie in opzioni + VIX
for f in BXM PUT VIX; do
  curl -sSL -o "cboe_$f.csv" "https://cdn.cboe.com/api/global/us_indices/daily_prices/${f}_History.csv"
done
curl -sSL -o fred_VIXCLS.csv "https://fred.stlouisfed.org/graph/fredgraph.csv?id=VIXCLS"

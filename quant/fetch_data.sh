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

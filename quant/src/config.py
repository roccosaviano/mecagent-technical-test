"""Parametri fiscali, di costo e di simulazione. Un solo posto da modificare."""

# ---------------------------------------------------------------- fiscalita' IE
CGT_RATE          = 0.33    # capital gains su azioni e CFD, per posizione chiusa
CGT_EXEMPT_ANNUAL = 1270.0  # esenzione annua personale, non riportabile
ETF_EXIT_TAX      = 0.38    # exit tax fondi UCITS dal 1/1/2026 (era 0.41)
# Il backtest usa rendimenti storici, ma il regime fiscale che si applichera' e'
# quello futuro: l'orizzonte dell'utente (20-30 anni da oggi) sta tutto oltre il
# 2026, quindi l'aliquota rilevante e' 38% su tutto il percorso. Mettere 0.41 qui
# riproduce invece il trattamento storico (IRR piu' bassa di ~0,4 punti).
ETF_EXIT_TAX_PRE  = 0.38
ETF_EXIT_TAX_HIST = 0.41    # aliquota realmente in vigore fino al 31/12/2025
ETF_EXIT_TAX_SWITCH = 2026
DEEMED_DISPOSAL_Y = 8       # deemed disposal ogni 8 anni su ogni singolo lotto
DIRT_RATE         = 0.33    # ritenuta su interessi da liquidita'
DIV_RATE_FOREIGN  = 0.52    # dividendi esteri su azioni dirette: marginale+USC+PRSI
TRADING_INCOME_RATE = 0.52  # scenario riqualificazione come attivita' commerciale

# soglia oltre la quale segnalo anche lo scenario a 52%: Revenue guarda frequenza,
# organizzazione e intento speculativo (badges of trade), non c'e' un numero di legge.
# 100 op/anno e' la soglia che uso come bandiera, non come regola.
TRADE_COUNT_FLAG  = 100

# ---------------------------------------------------------------- costi
COST_ROUND_TRIP   = 0.0015  # 0,15% andata+ritorno, applicato meta' per lato
FIN_SPREAD        = 0.03    # spread sul finanziamento CFD, sopra il benchmark

# ---------------------------------------------------------------- PAC
MONTHLY_CONTRIB   = 500.0
LEVERAGE_GRID     = (1.0, 1.5, 2.0)

# ---------------------------------------------------------------- date chiave
# Group C: la finestra di calibrazione dichiarata dall'utente
CALIB_START = "1990-01"
CALIB_END   = "2023-12"

# ---------------------------------------------------------------- riferimenti attesi
# Valori dichiarati dall'utente come gate di correttezza sul buy&hold Shiller.
REF_BH_EQUITY_IRR = 8.21
REF_BH_EQUITY_DD  = -47.0
REF_BH_ETF_IRR    = 6.76
REF_TOLERANCE     = 0.75   # punti percentuali di scostamento ammessi sull'IRR

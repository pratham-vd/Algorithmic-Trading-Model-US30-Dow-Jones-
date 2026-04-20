import datetime

#Trading Settings
SYMBOL = "US30Cash"
TIMEFRAME = 1  # Standard M1 timeframe for reference, though we use tick data for entry

#Strategy Timings
TARGET_HOUR_IST = 20
TARGET_MINUTE_IST = 0
TARGET_SECOND_IST = 0
TRIGGER_OFFSET_SECONDS = 15  # Seconds before target time to place orders

#Order Parameters
PIPS_DISTANCE = 20     # Distance from market price for Stop orders
SL_PIPS = 20           # Stop Loss distance (at the level of the opposite order)
TP_PIPS = 30           # Take Profit distance
RISK_PERCENT = 33.33     # Percentage of account balance to risk per trade

#Broker/Instrument Specifics
POINT_VALUE = 1.0  # Assumed 1 point = 1 unit of currency for PnL per lot (often different for indices)
MARGIN_BUFFER = 0.90   # 90% of Free Margin used for max lot calculation (Safety Buffer)

MAGIC_NUMBER = 123456

#MT5 Account Credentials
MT5_LOGIN = 316286170       # Account Number (int)
MT5_PASSWORD = "Us30_livedemo"  # Password (string)
MT5_SERVER = "XMGlobal-MT5 7"    # Server Name (string) e.g., "MetaQuotes-Demo"

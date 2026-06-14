import pandas as pd
from datetime import datetime
from loguru import logger
from ..config.settings import settings

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

class RealMT5:
    """
    Real MetaTrader5 client for Windows execution.
    Automatically logs into the broker using credentials from .env.
    """

    def __init__(self, pair: str = "EURUSD"):
        self.pair = pair
        self.connected = False
        if mt5 is None:
            logger.error("MetaTrader5 package is not installed or you are not on Windows.")

    def connect(self) -> bool:
        if mt5 is None:
            return False
            
        logger.info("Initializing Real MetaTrader 5...")
        
        # Check if login details are provided
        if settings.MT5_LOGIN and settings.MT5_PASSWORD and settings.MT5_SERVER:
            logger.info(f"Connecting to account {settings.MT5_LOGIN} on server {settings.MT5_SERVER}...")
            # Initialize with specific path and credentials
            authorized = mt5.initialize(
                login=settings.MT5_LOGIN,
                password=settings.MT5_PASSWORD,
                server=settings.MT5_SERVER
            )
        else:
            logger.info("No credentials in .env. Initializing with default active MT5 terminal...")
            authorized = mt5.initialize()

        if not authorized:
            logger.error(f"Failed to connect to MT5. Error code: {mt5.last_error()}")
            self.connected = False
            return False

        # Verify login
        account_info = mt5.account_info()
        if account_info is None:
            logger.error("Failed to get account info. Login may have failed.")
            self.connected = False
            return False
            
        logger.success(f"Successfully connected to MT5! Account: {account_info.login} ({account_info.server})")
        self.connected = True
        return True

    def disconnect(self):
        if mt5 and self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Real MT5 disconnected.")

    def get_historical_data(self, bars: int = 500) -> pd.DataFrame:
        if not self.connected or mt5 is None:
            return pd.DataFrame()

        # Map string timeframe to MT5 constant (assuming M15 default)
        tf_map = {
            "M1": mt5.TIMEFRAME_M1,
            "M5": mt5.TIMEFRAME_M5,
            "M15": mt5.TIMEFRAME_M15,
            "H1": mt5.TIMEFRAME_H1,
            "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1,
        }
        mt5_tf = tf_map.get(settings.TIMEFRAME, mt5.TIMEFRAME_M15)

        logger.info(f"Fetching {bars} real candles for {self.pair}")
        rates = mt5.copy_rates_from_pos(self.pair, mt5_tf, 0, bars)

        if rates is None or len(rates) == 0:
            logger.error(f"Failed to fetch rates. Error: {mt5.last_error()}")
            return pd.DataFrame()

        # Convert to pandas DataFrame
        df = pd.DataFrame(rates)
        # Convert time in seconds into datetime
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        # Standardize volume column name to match MockMT5 and generic format
        if 'tick_volume' in df.columns:
            df['volume'] = df['tick_volume']
            
        logger.success(f"Fetched {len(df)} real candles from MT5")
        return df

    def get_current_price(self) -> dict:
        if not self.connected or mt5 is None:
            return {}

        tick = mt5.symbol_info_tick(self.pair)
        if tick is None:
            return {}

        return {
            "pair": self.pair,
            "bid": tick.bid,
            "ask": tick.ask,
            "time": datetime.fromtimestamp(tick.time).isoformat()
        }

    def get_account_info(self) -> dict:
        if not self.connected or mt5 is None:
            return {}

        account_info = mt5.account_info()
        if account_info is None:
            return {}

        return {
            "balance": account_info.balance,
            "equity": account_info.equity,
            "margin": account_info.margin,
            "free_margin": account_info.margin_free,
            "currency": account_info.currency
        }

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

class MockMT5:
    """
    Simulates MetaTrader5 behavior for Linux development.
    Real MT5 se replace karna ho toh sirf is class ko swap karo.
    """

    def __init__(self, pair: str = "EURUSD"):
        self.pair = pair
        self.connected = False
        self.base_price = 1.0840  # EURUSD starting price
        self.current_price = self.base_price
        logger.info(f"MockMT5 initialized for {pair}")

    def connect(self) -> bool:
        self.connected = True
        logger.success("MockMT5 connected (simulation mode)")
        return True

    def disconnect(self):
        self.connected = False
        logger.info("MockMT5 disconnected")

    def get_historical_data(self, bars: int = 500) -> pd.DataFrame:
        """500 historical M15 candles generate karo"""
        logger.info(f"Fetching {bars} historical candles for {self.pair}")

        now = datetime.now()
        dates = [now - timedelta(minutes=15 * i) for i in range(bars, 0, -1)]

        # Realistic price movement simulate karo
        returns = np.random.normal(0, 0.0003, bars)  # small movements
        prices = [self.current_price]

        for r in returns[1:]:
            prices.append(prices[-1] * (1 + r))

        # OHLCV banao
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
            spread = np.random.uniform(0.0001, 0.0005)
            high = close + abs(np.random.normal(0, 0.0003))
            low = close - abs(np.random.normal(0, 0.0003))
            open_price = prices[i - 1] if i > 0 else close
            volume = np.random.randint(100, 1000)

            data.append({
                "time": date,
                "open": round(open_price, 5),
                "high": round(high, 5),
                "low": round(low, 5),
                "close": round(close, 5),
                "volume": volume
            })

        df = pd.DataFrame(data)
        
        # Update current price state so next generation flows continuously
        self.current_price = round(prices[-1], 5)
        
        logger.success(f"Generated {len(df)} candles")
        return df

    def get_current_price(self) -> dict:
        """Live price simulate karo"""
        change = np.random.normal(0, 0.0002)
        self.current_price = round(self.current_price + change, 5)

        return {
            "pair": self.pair,
            "bid": self.current_price,
            "ask": round(self.current_price + 0.0001, 5),
            "time": datetime.now().isoformat()
        }

    def get_account_info(self) -> dict:
        """Demo account info"""
        return {
            "balance": 10000.0,
            "equity": 10124.50,
            "margin": 150.0,
            "free_margin": 9974.50,
            "currency": "USD"
        }
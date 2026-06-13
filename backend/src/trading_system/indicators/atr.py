import pandas as pd
from .base import BaseIndicator, IndicatorResult

class ATRIndicator(BaseIndicator):
    def __init__(self, period: int = 14):
        super().__init__("ATR")
        self.period = period

    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        self._validate(df, self.period + 1)

        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()

        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = true_range.ewm(com=self.period - 1, adjust=False).mean()
        value = round(atr.iloc[-1], 5)

        # ATR se volatility judge karo
        avg_price = df["close"].iloc[-1]
        atr_pct = (value / avg_price) * 100

        if atr_pct < 0.05:
            signal, confidence, reason = "NEUTRAL", 0.3, f"ATR {value} — low volatility, avoid trading"
        elif atr_pct > 0.15:
            signal, confidence, reason = "NEUTRAL", 0.5, f"ATR {value} — high volatility, be cautious"
        else:
            signal, confidence, reason = "BUY", 0.6, f"ATR {value} — normal volatility, good to trade"

        return IndicatorResult(self.name, signal, confidence, value, reason)
import pandas as pd
from .base import BaseIndicator, IndicatorResult

class BollingerIndicator(BaseIndicator):
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__("Bollinger")
        self.period = period
        self.std_dev = std_dev

    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        self._validate(df, self.period + 1)

        close = df["close"]
        mid = close.rolling(window=self.period).mean()
        std = close.rolling(window=self.period).std()

        upper = mid + (self.std_dev * std)
        lower = mid - (self.std_dev * std)

        current = close.iloc[-1]
        upper_val = round(upper.iloc[-1], 5)
        lower_val = round(lower.iloc[-1], 5)
        mid_val = round(mid.iloc[-1], 5)

        # Band width — squeeze detect karo
        bandwidth = round((upper_val - lower_val) / mid_val * 100, 4)

        if current <= lower_val:
            signal, confidence, reason = "BUY", 0.85, f"Price touching lower band {lower_val} — oversold"
        elif current >= upper_val:
            signal, confidence, reason = "SELL", 0.85, f"Price touching upper band {upper_val} — overbought"
        elif current < mid_val:
            signal, confidence, reason = "SELL", 0.50, f"Price below midline {mid_val}"
        elif current > mid_val:
            signal, confidence, reason = "BUY", 0.50, f"Price above midline {mid_val}"
        else:
            signal, confidence, reason = "NEUTRAL", 0.3, f"Price at midline {mid_val}"

        return IndicatorResult(self.name, signal, confidence, mid_val, reason)
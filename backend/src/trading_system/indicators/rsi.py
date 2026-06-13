import pandas as pd
from .base import BaseIndicator, IndicatorResult

class RSIIndicator(BaseIndicator):
    def __init__(self, period: int = 14):
        super().__init__("RSI")
        self.period = period

    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        self._validate(df, self.period + 1)

        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)

        avg_gain = gain.ewm(com=self.period - 1, adjust=False).mean()
        avg_loss = loss.ewm(com=self.period - 1, adjust=False).mean()

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        value = round(rsi.iloc[-1], 2)

        if value < 30:
            signal, confidence, reason = "BUY", 0.85, f"RSI {value} — oversold"
        elif value > 70:
            signal, confidence, reason = "SELL", 0.85, f"RSI {value} — overbought"
        elif value < 45:
            signal, confidence, reason = "BUY", 0.55, f"RSI {value} — leaning bullish"
        elif value > 55:
            signal, confidence, reason = "SELL", 0.55, f"RSI {value} — leaning bearish"
        else:
            signal, confidence, reason = "NEUTRAL", 0.3, f"RSI {value} — neutral zone"

        return IndicatorResult(self.name, signal, confidence, value, reason)
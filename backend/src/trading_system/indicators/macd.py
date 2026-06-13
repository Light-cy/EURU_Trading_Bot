import pandas as pd
from .base import BaseIndicator, IndicatorResult

class MACDIndicator(BaseIndicator):
    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__("MACD")
        self.fast = fast
        self.slow = slow
        self.signal_period = signal

    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        self._validate(df, self.slow + self.signal_period)

        ema_fast = df["close"].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=self.slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal_period, adjust=False).mean()
        histogram = macd_line - signal_line

        macd_val = round(macd_line.iloc[-1], 6)
        hist_val = histogram.iloc[-1]
        prev_hist = histogram.iloc[-2]

        if hist_val > 0 and prev_hist <= 0:
            signal, confidence, reason = "BUY", 0.88, "MACD bullish crossover"
        elif hist_val < 0 and prev_hist >= 0:
            signal, confidence, reason = "SELL", 0.88, "MACD bearish crossover"
        elif hist_val > 0:
            signal, confidence, reason = "BUY", 0.60, "MACD histogram positive"
        else:
            signal, confidence, reason = "SELL", 0.60, "MACD histogram negative"

        return IndicatorResult(self.name, signal, confidence, macd_val, reason)
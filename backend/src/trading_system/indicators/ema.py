import pandas as pd
from .base import BaseIndicator, IndicatorResult

class EMAIndicator(BaseIndicator):
    def __init__(self, fast: int = 20, slow: int = 50):
        super().__init__("EMA")
        self.fast = fast
        self.slow = slow

    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        self._validate(df, self.slow + 1)

        ema_fast = df["close"].ewm(span=self.fast, adjust=False).mean()
        ema_slow = df["close"].ewm(span=self.slow, adjust=False).mean()

        fast_val = round(ema_fast.iloc[-1], 5)
        slow_val = round(ema_slow.iloc[-1], 5)
        prev_fast = ema_fast.iloc[-2]
        prev_slow = ema_slow.iloc[-2]

        # Crossover detect karo
        crossover_up = prev_fast <= prev_slow and fast_val > slow_val
        crossover_down = prev_fast >= prev_slow and fast_val < slow_val

        if crossover_up:
            signal, confidence, reason = "BUY", 0.90, f"Bullish EMA crossover ({self.fast}/{self.slow})"
        elif crossover_down:
            signal, confidence, reason = "SELL", 0.90, f"Bearish EMA crossover ({self.fast}/{self.slow})"
        elif fast_val > slow_val:
            signal, confidence, reason = "BUY", 0.65, f"EMA{self.fast} above EMA{self.slow}"
        else:
            signal, confidence, reason = "SELL", 0.65, f"EMA{self.fast} below EMA{self.slow}"

        return IndicatorResult(self.name, signal, confidence, fast_val, reason)
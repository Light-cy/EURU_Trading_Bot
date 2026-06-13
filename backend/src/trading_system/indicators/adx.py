import pandas as pd
import numpy as np
from .base import BaseIndicator, IndicatorResult

class ADXIndicator(BaseIndicator):
    def __init__(self, period: int = 14):
        super().__init__("ADX")
        self.period = period

    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        self._validate(df, self.period * 2)

        high = df["high"]
        low = df["low"]
        close = df["close"]

        # True Range
        tr1 = high - low
        tr2 = (high - close.shift()).abs()
        tr3 = (low - close.shift()).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

        # Directional Movement
        dm_plus = high.diff()
        dm_minus = -low.diff()
        dm_plus = dm_plus.where((dm_plus > dm_minus) & (dm_plus > 0), 0)
        dm_minus = dm_minus.where((dm_minus > dm_plus) & (dm_minus > 0), 0)

        # Smoothed values
        atr = tr.ewm(com=self.period - 1, adjust=False).mean()
        di_plus = 100 * dm_plus.ewm(com=self.period - 1, adjust=False).mean() / atr
        di_minus = 100 * dm_minus.ewm(com=self.period - 1, adjust=False).mean() / atr

        # ADX
        dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus)
        adx = dx.ewm(com=self.period - 1, adjust=False).mean()

        adx_val = round(adx.iloc[-1], 2)
        di_plus_val = round(di_plus.iloc[-1], 2)
        di_minus_val = round(di_minus.iloc[-1], 2)

        if adx_val < 20:
            signal = "NEUTRAL"
            confidence = 0.2
            reason = f"ADX {adx_val} — weak trend, avoid"
        elif adx_val >= 20 and adx_val < 40:
            if di_plus_val > di_minus_val:
                signal, confidence, reason = "BUY", 0.70, f"ADX {adx_val} — moderate uptrend"
            else:
                signal, confidence, reason = "SELL", 0.70, f"ADX {adx_val} — moderate downtrend"
        else:
            if di_plus_val > di_minus_val:
                signal, confidence, reason = "BUY", 0.90, f"ADX {adx_val} — strong uptrend"
            else:
                signal, confidence, reason = "SELL", 0.90, f"ADX {adx_val} — strong downtrend"

        return IndicatorResult(self.name, signal, confidence, adx_val, reason)
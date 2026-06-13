import pandas as pd
from .base import BaseIndicator, IndicatorResult

class VWAPIndicator(BaseIndicator):
    def __init__(self):
        super().__init__("VWAP")

    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        self._validate(df, 10)

        # Typical price
        typical_price = (df["high"] + df["low"] + df["close"]) / 3

        # VWAP calculate karo
        cumulative_tp_vol = (typical_price * df["volume"]).cumsum()
        cumulative_vol = df["volume"].cumsum()
        vwap = cumulative_tp_vol / cumulative_vol

        vwap_val = round(vwap.iloc[-1], 5)
        current_price = df["close"].iloc[-1]
        diff_pct = ((current_price - vwap_val) / vwap_val) * 100

        if current_price > vwap_val and diff_pct > 0.02:
            signal, confidence, reason = "BUY", 0.75, f"Price {current_price} above VWAP {vwap_val} — bullish"
        elif current_price < vwap_val and diff_pct < -0.02:
            signal, confidence, reason = "SELL", 0.75, f"Price {current_price} below VWAP {vwap_val} — bearish"
        else:
            signal, confidence, reason = "NEUTRAL", 0.4, f"Price near VWAP {vwap_val} — no clear bias"

        return IndicatorResult(self.name, signal, confidence, vwap_val, reason)
import pandas as pd
from dataclasses import dataclass
from loguru import logger

@dataclass
class StructureResult:
    bos: str        # "BULLISH", "BEARISH", "NONE"
    choch: str      # "BULLISH", "BEARISH", "NONE"
    trend: str      # "UPTREND", "DOWNTREND", "RANGING"
    confidence: float
    reason: str

class MarketStructure:
    def __init__(self, lookback: int = 20):
        self.lookback = lookback

    def analyze(self, df: pd.DataFrame) -> StructureResult:
        if len(df) < self.lookback * 2:
            return StructureResult("NONE", "NONE", "RANGING", 0.3, "Not enough data")

        recent = df.tail(self.lookback * 2).copy()

        # Swing highs aur lows nikalo
        highs = self._get_swing_highs(recent)
        lows = self._get_swing_lows(recent)

        bos = "NONE"
        choch = "NONE"
        trend = "RANGING"
        confidence = 0.4
        reason = "No clear structure"

        if len(highs) >= 2 and len(lows) >= 2:
            # Higher highs + higher lows = uptrend
            hh = highs[-1] > highs[-2]
            hl = lows[-1] > lows[-2]
            lh = highs[-1] < highs[-2]
            ll = lows[-1] < lows[-2]

            if hh and hl:
                trend = "UPTREND"
                bos = "BULLISH"
                confidence = 0.80
                reason = "Higher Highs + Higher Lows — bullish BOS confirmed"
            elif lh and ll:
                trend = "DOWNTREND"
                bos = "BEARISH"
                confidence = 0.80
                reason = "Lower Highs + Lower Lows — bearish BOS confirmed"
            elif hh and ll:
                choch = "BULLISH"
                trend = "UPTREND"
                confidence = 0.70
                reason = "CHoCH detected — possible bullish reversal"
            elif lh and hl:
                choch = "BEARISH"
                trend = "DOWNTREND"
                confidence = 0.70
                reason = "CHoCH detected — possible bearish reversal"

        return StructureResult(bos, choch, trend, confidence, reason)

    def _get_swing_highs(self, df: pd.DataFrame, window: int = 5) -> list:
        highs = []
        for i in range(window, len(df) - window):
            if df["high"].iloc[i] == df["high"].iloc[i-window:i+window].max():
                highs.append(df["high"].iloc[i])
        return highs

    def _get_swing_lows(self, df: pd.DataFrame, window: int = 5) -> list:
        lows = []
        for i in range(window, len(df) - window):
            if df["low"].iloc[i] == df["low"].iloc[i-window:i+window].min():
                lows.append(df["low"].iloc[i])
        return lows
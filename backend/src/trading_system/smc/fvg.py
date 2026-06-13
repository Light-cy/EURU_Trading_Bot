import pandas as pd
from dataclasses import dataclass
from loguru import logger

@dataclass
class FVG:
    type: str    # "BULLISH", "BEARISH"
    top: float
    bottom: float

class FVGDetector:
    def detect(self, df: pd.DataFrame) -> dict:
        if len(df) < 10:
            return {"signal": "NEUTRAL", "confidence": 0.3,
                    "reason": "Not enough data", "fvg": None}

        recent = df.tail(50).copy().reset_index(drop=True)
        current_price = recent["close"].iloc[-1]

        fvgs = self._find_fvgs(recent)

        for fvg in reversed(fvgs):
            if fvg.bottom <= current_price <= fvg.top:
                signal = "BUY" if fvg.type == "BULLISH" else "SELL"
                return {
                    "signal": signal,
                    "confidence": 0.82,
                    "reason": f"Price inside {fvg.type} FVG ({fvg.bottom:.5f} - {fvg.top:.5f})",
                    "fvg": {"type": fvg.type, "top": fvg.top, "bottom": fvg.bottom}
                }

        return {
            "signal": "NEUTRAL",
            "confidence": 0.3,
            "reason": "No active Fair Value Gap",
            "fvg": None
        }

    def _find_fvgs(self, df: pd.DataFrame) -> list:
        fvgs = []
        for i in range(1, len(df) - 1):
            prev_high = df["high"].iloc[i-1]
            prev_low = df["low"].iloc[i-1]
            next_high = df["high"].iloc[i+1]
            next_low = df["low"].iloc[i+1]

            # Bullish FVG — gap between candle i-1 high and candle i+1 low
            if next_low > prev_high:
                fvgs.append(FVG("BULLISH", top=next_low, bottom=prev_high))

            # Bearish FVG — gap between candle i+1 high and candle i-1 low
            if prev_low > next_high:
                fvgs.append(FVG("BEARISH", top=prev_low, bottom=next_high))

        return fvgs
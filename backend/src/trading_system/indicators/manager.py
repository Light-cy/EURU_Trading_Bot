import pandas as pd
from loguru import logger
from .rsi import RSIIndicator
from .ema import EMAIndicator
from .macd import MACDIndicator
from .atr import ATRIndicator
from .vwap import VWAPIndicator
from .adx import ADXIndicator
from .bollinger import BollingerIndicator
from .base import IndicatorResult

class IndicatorManager:
    def __init__(self):
        self.indicators = [
            RSIIndicator(period=14),
            EMAIndicator(fast=20, slow=50),
            MACDIndicator(fast=12, slow=26, signal=9),
            ATRIndicator(period=14),
            VWAPIndicator(),
            ADXIndicator(period=14),
            BollingerIndicator(period=20, std_dev=2.0),
        ]
        logger.info(f"IndicatorManager ready — {len(self.indicators)} indicators loaded")

    def run_all(self, df: pd.DataFrame) -> dict:
        results = {}
        for indicator in self.indicators:
            try:
                result = indicator.calculate(df)
                results[result.name] = {
                    "signal": result.signal,
                    "confidence": result.confidence,
                    "value": result.value,
                    "reason": result.reason
                }
                logger.info(f"{result.name}: {result.signal} ({result.confidence}) — {result.reason}")
            except Exception as e:
                logger.error(f"{indicator.name} failed: {e}")

        return results
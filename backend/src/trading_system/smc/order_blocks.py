import pandas as pd
from dataclasses import dataclass
from typing import Optional
from loguru import logger

@dataclass
class OrderBlock:
    type: str        # "BULLISH", "BEARISH"
    top: float
    bottom: float
    index: int
    strength: float

class OrderBlockDetector:
    def __init__(self, lookback: int = 50):
        self.lookback = lookback

    def detect(self, df: pd.DataFrame) -> dict:
        if len(df) < self.lookback:
            return {"signal": "NEUTRAL", "confidence": 0.3,
                    "reason": "Not enough data", "ob": None}

        recent = df.tail(self.lookback).copy().reset_index(drop=True)
        current_price = recent["close"].iloc[-1]

        bullish_obs = self._find_bullish_obs(recent)
        bearish_obs = self._find_bearish_obs(recent)

        # Check karo price kisi OB ke andar hai
        for ob in reversed(bullish_obs):
            if ob.bottom <= current_price <= ob.top:
                return {
                    "signal": "BUY",
                    "confidence": 0.88,
                    "reason": f"Price inside bullish OB ({ob.bottom:.5f} - {ob.top:.5f})",
                    "ob": {"type": "BULLISH", "top": ob.top, "bottom": ob.bottom}
                }

        for ob in reversed(bearish_obs):
            if ob.bottom <= current_price <= ob.top:
                return {
                    "signal": "SELL",
                    "confidence": 0.88,
                    "reason": f"Price inside bearish OB ({ob.bottom:.5f} - {ob.top:.5f})",
                    "ob": {"type": "BEARISH", "top": ob.top, "bottom": ob.bottom}
                }

        return {
            "signal": "NEUTRAL",
            "confidence": 0.35,
            "reason": "Price not in any Order Block",
            "ob": None
        }

    def _find_bullish_obs(self, df: pd.DataFrame) -> list:
        obs = []
        for i in range(1, len(df) - 1):
            # Bearish candle followed by strong bullish move
            if (df["close"].iloc[i] < df["open"].iloc[i] and
                df["close"].iloc[i+1] > df["high"].iloc[i]):
                obs.append(OrderBlock(
                    type="BULLISH",
                    top=df["high"].iloc[i],
                    bottom=df["low"].iloc[i],
                    index=i,
                    strength=0.8
                ))
        return obs

    def _find_bearish_obs(self, df: pd.DataFrame) -> list:
        obs = []
        for i in range(1, len(df) - 1):
            # Bullish candle followed by strong bearish move
            if (df["close"].iloc[i] > df["open"].iloc[i] and
                df["close"].iloc[i+1] < df["low"].iloc[i]):
                obs.append(OrderBlock(
                    type="BEARISH",
                    top=df["high"].iloc[i],
                    bottom=df["low"].iloc[i],
                    index=i,
                    strength=0.8
                ))
        return obs
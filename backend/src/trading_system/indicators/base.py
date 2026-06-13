from abc import ABC, abstractmethod
import pandas as pd
from dataclasses import dataclass

@dataclass
class IndicatorResult:
    name: str
    signal: str        # "BUY", "SELL", "NEUTRAL"
    confidence: float  # 0.0 to 1.0
    value: float       # actual indicator value
    reason: str        # human readable

class BaseIndicator(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> IndicatorResult:
        pass

    def _validate(self, df: pd.DataFrame, min_rows: int):
        if len(df) < min_rows:
            raise ValueError(f"{self.name} needs at least {min_rows} candles")
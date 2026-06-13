import pandas as pd
from loguru import logger
from .structure import MarketStructure
from .order_blocks import OrderBlockDetector
from .fvg import FVGDetector

class SMCManager:
    def __init__(self):
        self.structure = MarketStructure(lookback=20)
        self.ob_detector = OrderBlockDetector(lookback=50)
        self.fvg_detector = FVGDetector()
        logger.info("SMCManager ready — Structure, OB, FVG loaded")

    def run_all(self, df: pd.DataFrame) -> dict:
        # Market Structure
        struct = self.structure.analyze(df)

        # Order Blocks
        ob = self.ob_detector.detect(df)

        # Fair Value Gaps
        fvg = self.fvg_detector.detect(df)

        results = {
            "structure": {
                "bos": struct.bos,
                "choch": struct.choch,
                "trend": struct.trend,
                "confidence": struct.confidence,
                "reason": struct.reason
            },
            "order_block": ob,
            "fvg": fvg
        }

        logger.info(f"Structure: {struct.trend} | BOS: {struct.bos} | CHoCH: {struct.choch}")
        logger.info(f"OB: {ob['signal']} — {ob['reason']}")
        logger.info(f"FVG: {fvg['signal']} — {fvg['reason']}")

        return results
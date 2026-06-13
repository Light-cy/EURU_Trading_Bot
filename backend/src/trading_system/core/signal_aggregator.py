import pandas as pd
from dataclasses import dataclass
from loguru import logger
from typing import Dict, List, Optional

@dataclass
class AggregatedSignal:
    """Combined signal from all indicators + SMC"""
    signal: str              # "BUY", "SELL", "NEUTRAL"
    overall_confidence: float  # 0.0 to 1.0
    buy_count: int
    sell_count: int
    neutral_count: int
    indicator_results: Dict
    smc_results: Dict
    ml_boosted: bool         # Whether ML boosted the confidence
    ml_score: Optional[float]  # ML model score if used
    reason: str


class SignalAggregator:
    """
    Combines indicator signals and SMC analysis to produce a single trading signal.
    Optionally uses XGBoost to boost confidence.
    
    Decision logic:
    - BUY: >= 60% of signals are BUY + SMC trend is bullish
    - SELL: >= 60% of signals are SELL + SMC trend is bearish
    - NEUTRAL: mixed signals or no clear consensus
    """

    def __init__(self, min_consensus: float = 0.60, ml_model=None):
        self.min_consensus = min_consensus
        self.ml_model = ml_model
        self.use_ml = ml_model is not None and ml_model.is_trained
        if self.use_ml:
            logger.info("SignalAggregator: XGBoost ML boosting enabled")
        else:
            logger.info("SignalAggregator: ML boosting disabled (NO_ML mode)")

    def aggregate(
        self,
        indicator_results: Dict,
        smc_results: Dict,
        df: Optional[pd.DataFrame] = None,
        min_confidence: float = 0.65
    ) -> AggregatedSignal:
        """
        Aggregate indicator + SMC signals, optionally boosted by ML
        
        Args:
            indicator_results: Dict from IndicatorManager.run_all()
            smc_results: Dict from SMCManager.run_all()
            df: Optional OHLCV DataFrame for ML prediction
            min_confidence: Minimum confidence threshold for BUY/SELL
            
        Returns:
            AggregatedSignal with final decision
        """
        
        # Count signals
        buy_count = 0
        sell_count = 0
        neutral_count = 0
        total_indicators = 0
        total_confidence = 0

        # Analyze indicators
        for ind_name, result in indicator_results.items():
            total_indicators += 1
            signal = result["signal"]
            confidence = result["confidence"]
            total_confidence += confidence

            if signal == "BUY":
                buy_count += 1
            elif signal == "SELL":
                sell_count += 1
            else:
                neutral_count += 1

        # Get consensus
        buy_pct = buy_count / total_indicators if total_indicators > 0 else 0
        sell_pct = sell_count / total_indicators if total_indicators > 0 else 0
        avg_confidence = total_confidence / total_indicators if total_indicators > 0 else 0

        # SMC signals
        struct_signal = smc_results.get("structure", {}).get("bos", "NONE")
        struct_trend = smc_results.get("structure", {}).get("trend", "RANGING")
        struct_confidence = smc_results.get("structure", {}).get("confidence", 0.5)

        ob_signal = smc_results.get("order_block", {}).get("signal", "NEUTRAL")
        ob_confidence = smc_results.get("order_block", {}).get("confidence", 0.5)

        fvg_signal = smc_results.get("fvg", {}).get("signal", "NEUTRAL")
        fvg_confidence = smc_results.get("fvg", {}).get("confidence", 0.5)

        # Final decision logic
        final_signal = "NEUTRAL"
        reason = ""
        ml_boosted = False
        ml_score = None

        if buy_pct >= self.min_consensus and avg_confidence >= min_confidence:
            if struct_trend == "UPTREND" or struct_signal == "BULLISH":
                final_signal = "BUY"
                reason = f"Strong buy consensus ({buy_pct:.0%}) + {struct_trend}"
            else:
                final_signal = "BUY"
                reason = f"Strong buy consensus ({buy_pct:.0%}) from indicators"

        elif sell_pct >= self.min_consensus and avg_confidence >= min_confidence:
            if struct_trend == "DOWNTREND" or struct_signal == "BEARISH":
                final_signal = "SELL"
                reason = f"Strong sell consensus ({sell_pct:.0%}) + {struct_trend}"
            else:
                final_signal = "SELL"
                reason = f"Strong sell consensus ({sell_pct:.0%}) from indicators"

        else:
            # Check for SMC-driven signals
            if ob_signal == "BUY" and fvg_signal == "BUY" and struct_trend == "UPTREND":
                final_signal = "BUY"
                reason = f"SMC alignment (OB+FVG+Structure)"
            elif ob_signal == "SELL" and fvg_signal == "SELL" and struct_trend == "DOWNTREND":
                final_signal = "SELL"
                reason = f"SMC alignment (OB+FVG+Structure)"
            else:
                final_signal = "NEUTRAL"
                reason = f"Mixed signals: {buy_pct:.0%} buy, {sell_pct:.0%} sell, {struct_trend}"

        # Calculate overall confidence (before ML)
        if final_signal == "BUY":
            overall_confidence = (buy_pct * avg_confidence + struct_confidence) / 2
        elif final_signal == "SELL":
            overall_confidence = (sell_pct * avg_confidence + struct_confidence) / 2
        else:
            overall_confidence = min(avg_confidence, struct_confidence) * 0.5

        # Apply ML boosting if enabled and BUY/SELL signal
        if self.use_ml and final_signal != "NEUTRAL" and df is not None:
            try:
                ml_result = self.ml_model.predict(df)
                ml_score = ml_result.get("ml_score", 0.0)
                
                # Only boost if ML agrees with signal
                if (final_signal == "BUY" and ml_result["signal"] == "BUY") or \
                   (final_signal == "SELL" and ml_result["signal"] == "SELL"):
                    overall_confidence = self.ml_model.boost_confidence(overall_confidence, ml_result)
                    ml_boosted = True
                    reason += f" [ML boosted: {ml_score:.2f}]"
                else:
                    logger.warning(
                        f"ML disagreed: Indicator={final_signal}, ML={ml_result['signal']}. "
                        f"Keeping indicator signal."
                    )
            except Exception as e:
                logger.warning(f"ML boosting failed: {e}")

        result = AggregatedSignal(
            signal=final_signal,
            overall_confidence=min(overall_confidence, 1.0),
            buy_count=buy_count,
            sell_count=sell_count,
            neutral_count=neutral_count,
            indicator_results=indicator_results,
            smc_results=smc_results,
            ml_boosted=ml_boosted,
            ml_score=ml_score,
            reason=reason
        )

        logger.info(
            f"Signal Aggregated: {final_signal} (confidence: {overall_confidence:.2f}) "
            f"{'[ML boosted]' if ml_boosted else '[NO_ML]'} — {reason}"
        )

        return result

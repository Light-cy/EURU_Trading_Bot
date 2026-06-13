import pandas as pd
from dataclasses import dataclass
from loguru import logger
from typing import Optional, Dict
import math


@dataclass
class RiskParameters:
    """Risk calculation result"""
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size: float
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    reason: str


class RiskManager:
    """
    Calculates position sizing and stop loss / take profit levels.
    Supports multiple strategies: fixed risk, Kelly criterion, etc.
    """

    def __init__(
        self,
        account_balance: float = 10000.0,
        risk_percent: float = 1.0,
        strategy: str = "fixed_risk"  # "fixed_risk" or "kelly"
    ):
        self.account_balance = account_balance
        self.risk_percent = risk_percent
        self.strategy = strategy
        logger.info(f"RiskManager initialized — {strategy} strategy, {risk_percent}% risk per trade")

    def calculate_position(
        self,
        current_price: float,
        stop_loss_pips: float,
        signal: str,  # "BUY" or "SELL"
        atr_value: Optional[float] = None,
        win_rate: float = 0.55,
        reward_risk_ratio: float = 2.0
    ) -> RiskParameters:
        """
        Calculate entry, SL, TP, and position size.
        
        Args:
            current_price: Current market price
            stop_loss_pips: SL distance in pips
            signal: "BUY" or "SELL"
            atr_value: ATR value for dynamic SL (optional)
            win_rate: Historical win rate for Kelly calculation
            reward_risk_ratio: TP to SL ratio (default 2:1)
            
        Returns:
            RiskParameters with full position details
        """

        # Use ATR if provided, otherwise use fixed SL
        if atr_value and atr_value > 0:
            sl_pips = atr_value * 100  # Convert to pips
            reason = f"ATR-based SL ({atr_value:.5f})"
        else:
            sl_pips = stop_loss_pips
            reason = f"Fixed SL ({stop_loss_pips} pips)"

        # Calculate SL and TP prices
        pip_value = 0.0001  # For most forex pairs (EURUSD, GBPUSD, etc)

        if signal == "BUY":
            stop_loss = current_price - (sl_pips * pip_value)
            take_profit = current_price + (sl_pips * reward_risk_ratio * pip_value)
        else:  # SELL
            stop_loss = current_price + (sl_pips * pip_value)
            take_profit = current_price - (sl_pips * reward_risk_ratio * pip_value)

        # Risk amount per trade
        risk_amount = self.account_balance * (self.risk_percent / 100)
        risk_pips = abs(current_price - stop_loss) / pip_value

        # Position size calculation
        if self.strategy == "kelly":
            # Kelly = (win_rate * reward_risk_ratio - (1 - win_rate)) / reward_risk_ratio
            kelly_pct = (
                (win_rate * reward_risk_ratio - (1 - win_rate)) / reward_risk_ratio
            )
            kelly_pct = max(0.01, min(kelly_pct, 0.25))  # Limit to 1-25%
            position_size = self.account_balance * kelly_pct / (risk_pips * 10)
            reason += f" | Kelly {kelly_pct:.2%}"
        else:  # fixed_risk (default)
            position_size = risk_amount / (risk_pips * 10) if risk_pips > 0 else 0

        reward_amount = position_size * reward_risk_ratio * risk_pips * pip_value

        # RRR validation
        rrr = reward_amount / risk_amount if risk_amount > 0 else 0

        result = RiskParameters(
            entry_price=current_price,
            stop_loss=round(stop_loss, 5),
            take_profit=round(take_profit, 5),
            position_size=round(position_size, 2),
            risk_amount=round(risk_amount, 2),
            reward_amount=round(reward_amount, 2),
            risk_reward_ratio=round(rrr, 2),
            reason=reason
        )

        logger.info(
            f"Risk Calc: Entry={current_price:.5f} | SL={result.stop_loss:.5f} | "
            f"TP={result.take_profit:.5f} | Size={result.position_size} lots | RRR={rrr:.2f}"
        )

        return result

    def validate_trade(
        self,
        entry_price: float,
        stop_loss: float,
        open_trades: int = 0,
        max_open_trades: int = 3,
        max_daily_loss_percent: float = 3.0,
        current_daily_loss: float = 0.0
    ) -> Dict[str, bool]:
        """
        Check if trade is valid based on risk limits.
        
        Returns:
            Dict with validation results
        """

        is_valid = True
        reasons = []

        # Check max open trades
        if open_trades >= max_open_trades:
            is_valid = False
            reasons.append(f"Max {max_open_trades} open trades reached")

        # Check daily loss limit
        daily_loss_pct = (current_daily_loss / self.account_balance) * 100
        if daily_loss_pct >= max_daily_loss_percent:
            is_valid = False
            reasons.append(f"Daily loss limit ({max_daily_loss_percent}%) reached")

        # Check SL placement
        risk_pips = abs(entry_price - stop_loss) / 0.0001
        if risk_pips < 10:  # Minimum 10 pips
            is_valid = False
            reasons.append(f"SL too close ({risk_pips} pips, min 10)")

        if risk_pips > 500:  # Maximum 500 pips
            is_valid = False
            reasons.append(f"SL too far ({risk_pips} pips, max 500)")

        return {
            "is_valid": is_valid,
            "reasons": reasons if not is_valid else ["Trade is valid"],
            "daily_loss_percent": round(daily_loss_pct, 2)
        }

    def update_account_balance(self, new_balance: float):
        """Update account balance after a trade closes"""
        self.account_balance = new_balance
        logger.info(f"Account balance updated to ${new_balance:.2f}")

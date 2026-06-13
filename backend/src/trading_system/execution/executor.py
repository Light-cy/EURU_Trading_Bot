import json
from dataclasses import dataclass
from loguru import logger
from typing import Optional, List
from datetime import datetime


@dataclass
class OpenPosition:
    """Represents an open trading position"""
    trade_id: int
    pair: str
    signal: str  # "BUY" or "SELL"
    entry_price: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    position_size: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pips: float

    def get_pnl_percent(self) -> float:
        """Calculate P&L percentage"""
        if self.signal == "BUY":
            pnl_pips = (self.current_price - self.entry_price) / 0.0001
        else:  # SELL
            pnl_pips = (self.entry_price - self.current_price) / 0.0001
        
        return (pnl_pips / (self.entry_price / 0.0001)) * 100


class TradeExecutor:
    """
    Executes trades and manages open positions.
    Can be used with real MT5 or MockMT5.
    """

    def __init__(self, mt5_client):
        """
        Initialize executor with MT5 client
        
        Args:
            mt5_client: Can be either MockMT5 or real MT5 API client
        """
        self.mt5 = mt5_client
        self.open_trades: List[OpenPosition] = []
        self.trade_counter = 1000
        self.trade_history = []
        logger.info("TradeExecutor initialized")

    def execute_buy(
        self,
        pair: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        confidence: float,
        indicator_signals: dict,
        smc_signals: dict
    ) -> dict:
        """
        Execute a BUY trade
        
        Returns:
            Dict with trade details or error
        """
        return self._execute_trade(
            "BUY",
            pair,
            entry_price,
            stop_loss,
            take_profit,
            position_size,
            confidence,
            indicator_signals,
            smc_signals
        )

    def execute_sell(
        self,
        pair: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        confidence: float,
        indicator_signals: dict,
        smc_signals: dict
    ) -> dict:
        """Execute a SELL trade"""
        return self._execute_trade(
            "SELL",
            pair,
            entry_price,
            stop_loss,
            take_profit,
            position_size,
            confidence,
            indicator_signals,
            smc_signals
        )

    def _execute_trade(
        self,
        signal: str,
        pair: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        confidence: float,
        indicator_signals: dict,
        smc_signals: dict
    ) -> dict:
        """Internal trade execution logic"""
        
        try:
            # Check MT5 connection
            if not self.mt5.connected:
                self.mt5.connect()

            # Create trade record
            self.trade_counter += 1
            trade_id = self.trade_counter

            # TODO: In production, send actual order to MT5
            # order_result = self.mt5.send_order(...)

            position = OpenPosition(
                trade_id=trade_id,
                pair=pair,
                signal=signal,
                entry_price=entry_price,
                entry_time=datetime.now(),
                stop_loss=stop_loss,
                take_profit=take_profit,
                position_size=position_size,
                current_price=entry_price,
                unrealized_pnl=0.0,
                unrealized_pnl_pips=0.0
            )

            self.open_trades.append(position)

            logger.success(
                f"Trade executed: ID={trade_id} {signal} {pair} @ {entry_price:.5f} "
                f"| SL={stop_loss:.5f} | TP={take_profit:.5f} | Size={position_size}"
            )

            return {
                "success": True,
                "trade_id": trade_id,
                "signal": signal,
                "pair": pair,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "position_size": position_size,
                "confidence": confidence,
                "entry_time": position.entry_time.isoformat()
            }

        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def close_position(self, trade_id: int, exit_price: float, reason: str = "Manual") -> dict:
        """Close an open position"""
        
        position = next((t for t in self.open_trades if t.trade_id == trade_id), None)

        if not position:
            logger.error(f"Trade ID {trade_id} not found")
            return {"success": False, "error": "Trade not found"}

        try:
            # Calculate P&L
            if position.signal == "BUY":
                pnl_pips = (exit_price - position.entry_price) / 0.0001
            else:  # SELL
                pnl_pips = (position.entry_price - exit_price) / 0.0001

            pnl = pnl_pips * position.position_size * 10  # Standard lot value
            pnl_percent = (pnl / position.entry_price) * 100

            # Close position
            self.open_trades.remove(position)

            closed_trade = {
                "trade_id": trade_id,
                "signal": position.signal,
                "pair": position.pair,
                "entry_price": position.entry_price,
                "exit_price": exit_price,
                "position_size": position.position_size,
                "pnl": round(pnl, 2),
                "pnl_pips": round(pnl_pips, 1),
                "pnl_percent": round(pnl_percent, 2),
                "entry_time": position.entry_time.isoformat(),
                "exit_time": datetime.now().isoformat(),
                "reason": reason
            }

            self.trade_history.append(closed_trade)

            logger.success(
                f"Trade closed: ID={trade_id} | P&L={pnl:.2f} ({pnl_pips} pips) | Reason: {reason}"
            )

            return {"success": True, "trade": closed_trade}

        except Exception as e:
            logger.error(f"Failed to close trade: {e}")
            return {"success": False, "error": str(e)}

    def update_prices(self, current_prices: dict) -> List[dict]:
        """Update current prices and return any trades that were auto-closed (SL/TP)"""
        closed_trades = []
        
        for position in list(self.open_trades):
            if position.pair in current_prices:
                position.current_price = current_prices[position.pair]

                # Update unrealized P&L
                if position.signal == "BUY":
                    pnl_pips = (position.current_price - position.entry_price) / 0.0001
                else:  # SELL
                    pnl_pips = (position.entry_price - position.current_price) / 0.0001

                position.unrealized_pnl_pips = pnl_pips
                position.unrealized_pnl = pnl_pips * position.position_size * 10

                # Check for SL/TP hit
                if position.signal == "BUY":
                    if position.current_price <= position.stop_loss:
                        res = self.close_position(position.trade_id, position.stop_loss, "Stop Loss")
                        if res["success"]: closed_trades.append(res["trade"])
                    elif position.current_price >= position.take_profit:
                        res = self.close_position(position.trade_id, position.take_profit, "Take Profit")
                        if res["success"]: closed_trades.append(res["trade"])

                else:  # SELL
                    if position.current_price >= position.stop_loss:
                        res = self.close_position(position.trade_id, position.stop_loss, "Stop Loss")
                        if res["success"]: closed_trades.append(res["trade"])
                    elif position.current_price <= position.take_profit:
                        res = self.close_position(position.trade_id, position.take_profit, "Take Profit")
                        if res["success"]: closed_trades.append(res["trade"])
                        
        return closed_trades

    def get_open_positions(self) -> List[dict]:
        """Get all open positions as dicts"""
        return [
            {
                "trade_id": p.trade_id,
                "pair": p.pair,
                "signal": p.signal,
                "entry_price": p.entry_price,
                "current_price": p.current_price,
                "stop_loss": p.stop_loss,
                "take_profit": p.take_profit,
                "position_size": p.position_size,
                "unrealized_pnl": p.unrealized_pnl,
                "unrealized_pnl_pips": p.unrealized_pnl_pips,
                "pnl_percent": p.get_pnl_percent()
            }
            for p in self.open_trades
        ]

    def get_total_unrealized_pnl(self) -> float:
        """Get total unrealized P&L across all positions"""
        return sum(p.unrealized_pnl for p in self.open_trades)

    def get_trade_history(self, limit: int = 10) -> list:
        """Get recent closed trades"""
        return self.trade_history[-limit:]

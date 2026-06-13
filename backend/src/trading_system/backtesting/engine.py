import pandas as pd
from loguru import logger
from typing import Dict, List, Optional
import os
from datetime import datetime

from ..indicators.manager import IndicatorManager
from ..smc.manager import SMCManager
from ..core.signal_aggregator import SignalAggregator
from ..risk.manager import RiskManager
from ..ai.model import XGBoostSignalModel

class BacktestTrade:
    def __init__(self, id: int, signal: str, entry_price: float, sl: float, tp: float, size: float, entry_time: datetime):
        self.id = id
        self.signal = signal
        self.entry_price = entry_price
        self.stop_loss = sl
        self.take_profit = tp
        self.position_size = size
        self.entry_time = entry_time
        
        self.status = "OPEN"
        self.exit_price = None
        self.exit_time = None
        self.pnl = 0.0

class Backtester:
    def __init__(self, df: pd.DataFrame, initial_balance: float = 10000.0, risk_percent: float = 1.0):
        self.df = df
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        
        # Initialize components
        self.indicators = IndicatorManager()
        self.smc = SMCManager()
        
        model_path = os.path.join(os.path.dirname(__file__), '../ai/xgboost_signal_model.pkl')
        self.ml_model = XGBoostSignalModel(model_path=model_path)
        self.ml_model.load()
        
        self.signal_aggregator = SignalAggregator(min_consensus=0.60, ml_model=self.ml_model)
        self.risk_manager = RiskManager(account_balance=initial_balance, risk_percent=risk_percent)
        
        self.open_trades: List[BacktestTrade] = []
        self.closed_trades: List[BacktestTrade] = []
        
        self.trade_counter = 0
        self.max_drawdown = 0.0
        self.peak_balance = initial_balance

    def update_open_trades(self, current_candle: pd.Series):
        """Check if any open trades hit TP or SL on the current candle."""
        high = current_candle['high']
        low = current_candle['low']
        
        trades_to_remove = []
        
        for trade in self.open_trades:
            closed = False
            exit_price = 0.0
            
            if trade.signal == "BUY":
                if low <= trade.stop_loss:
                    exit_price = trade.stop_loss
                    closed = True
                elif high >= trade.take_profit:
                    exit_price = trade.take_profit
                    closed = True
            else: # SELL
                if high >= trade.stop_loss:
                    exit_price = trade.stop_loss
                    closed = True
                elif low <= trade.take_profit:
                    exit_price = trade.take_profit
                    closed = True
                    
            if closed:
                trade.status = "CLOSED"
                trade.exit_price = exit_price
                trade.exit_time = current_candle['time']
                
                # Calculate PnL
                pip_value = 0.0001
                if trade.signal == "BUY":
                    pips = (exit_price - trade.entry_price) / pip_value
                else:
                    pips = (trade.entry_price - exit_price) / pip_value
                    
                trade.pnl = pips * trade.position_size * 0.0001 # position_size is in units
                self.current_balance += trade.pnl
                
                # Update peak and max drawdown
                if self.current_balance > self.peak_balance:
                    self.peak_balance = self.current_balance
                else:
                    drawdown = (self.peak_balance - self.current_balance) / self.peak_balance * 100
                    if drawdown > self.max_drawdown:
                        self.max_drawdown = drawdown
                        
                self.risk_manager.update_account_balance(self.current_balance)
                self.closed_trades.append(trade)
                trades_to_remove.append(trade)
                
        for t in trades_to_remove:
            self.open_trades.remove(t)

    def run(self, window_size: int = 200, step_size: int = 1):
        """Run the step-by-step backtest simulation."""
        total_bars = len(self.df)
        logger.info(f"Starting Backtest on {total_bars} bars with starting balance ${self.initial_balance}")
        
        if total_bars <= window_size:
            logger.error("Dataset too small for the given window size.")
            return
            
        for i in range(window_size, total_bars, step_size):
            # 1. Update open trades with current candle
            current_candle = self.df.iloc[i]
            self.update_open_trades(current_candle)
            
            # 2. Extract sliding window for indicators
            window = self.df.iloc[i - window_size : i + 1].copy()
            
            # Limit max open trades
            if len(self.open_trades) >= 3:
                continue
                
            # 3. Calculate indicators and SMC on the window
            try:
                ind_results = self.indicators.run_all(window)
                smc_results = self.smc.run_all(window)
                
                # 4. Aggregate signals
                signal = self.signal_aggregator.aggregate(
                    indicator_results=ind_results,
                    smc_results=smc_results,
                    df=window,
                    min_confidence=0.65
                )
                
                # 5. Execute virtual trade if signal is strong
                if signal.signal in ["BUY", "SELL"]:
                    current_price = current_candle['close']
                    atr_value = window['close'].pct_change().std() * 100 # Rough ATR approx
                    
                    risk_params = self.risk_manager.calculate_position(
                        current_price=current_price,
                        stop_loss_pips=max(20, min(50, atr_value)), # Bound between 20-50 pips
                        signal=signal.signal,
                        atr_value=None # Fallback to fixed pips logic
                    )
                    
                    validation = self.risk_manager.validate_trade(
                        entry_price=risk_params.entry_price,
                        stop_loss=risk_params.stop_loss,
                        open_trades=len(self.open_trades),
                        max_open_trades=3
                    )
                    
                    if validation["is_valid"]:
                        self.trade_counter += 1
                        new_trade = BacktestTrade(
                            id=self.trade_counter,
                            signal=signal.signal,
                            entry_price=risk_params.entry_price,
                            sl=risk_params.stop_loss,
                            tp=risk_params.take_profit,
                            size=risk_params.position_size,
                            entry_time=current_candle['time']
                        )
                        self.open_trades.append(new_trade)
                        
            except Exception as e:
                # Suppress errors to not stop the loop
                pass
                
        # Close remaining open trades at the last price
        last_price = self.df.iloc[-1]['close']
        for trade in list(self.open_trades):
            if trade.signal == "BUY":
                exit_price = last_price
            else:
                exit_price = last_price
                
            pip_value = 0.0001
            pips = (exit_price - trade.entry_price) / pip_value if trade.signal == "BUY" else (trade.entry_price - exit_price) / pip_value
            trade.pnl = pips * trade.position_size * 0.0001
            self.current_balance += trade.pnl
            self.closed_trades.append(trade)
            self.open_trades.remove(trade)
            
        return self.get_results()
        
    def get_results(self) -> Dict:
        wins = [t for t in self.closed_trades if t.pnl > 0]
        losses = [t for t in self.closed_trades if t.pnl <= 0]
        
        gross_profit = sum(t.pnl for t in wins)
        gross_loss = abs(sum(t.pnl for t in losses))
        
        win_rate = (len(wins) / len(self.closed_trades) * 100) if self.closed_trades else 0.0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float('inf') if gross_profit > 0 else 0.0
        
        return {
            "initial_balance": self.initial_balance,
            "final_balance": self.current_balance,
            "net_profit": self.current_balance - self.initial_balance,
            "total_trades": len(self.closed_trades),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "max_drawdown": self.max_drawdown,
            "wins": len(wins),
            "losses": len(losses)
        }

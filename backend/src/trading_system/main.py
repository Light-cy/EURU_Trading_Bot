import json
from loguru import logger
from typing import Optional, Dict

from .indicators.manager import IndicatorManager
from .smc.manager import SMCManager
from .core.signal_aggregator import SignalAggregator
from .risk.manager import RiskManager
from .database.models import DatabaseManager
from .execution.executor import TradeExecutor
from .market.mock_mt5 import MockMT5
from .market.real_mt5 import RealMT5
from .config.settings import settings
from .ai.model import XGBoostSignalModel


class TradingSystem:
    """
    Main orchestrator for the entire trading system.
    Coordinates: Market Data → Indicators → SMC → Signals → Risk → Execution
    """

    def __init__(self):
        logger.info("=" * 60)
        logger.info("🚀 XEPHY-AI Trading System Initializing")
        logger.info("=" * 60)

        # Initialize components
        self.settings = settings
        self.db = DatabaseManager()
        self.mt5 = self._init_mt5()
        self.indicators = IndicatorManager()
        self.smc = SMCManager()
        
        # Initialize ML model (optional)
        self.ml_model = self._init_ml_model()
        
        self.signal_aggregator = SignalAggregator(min_consensus=0.60, ml_model=self.ml_model)
        self.risk_manager = RiskManager(
            account_balance=10000.0,
            risk_percent=settings.RISK_PERCENT,
            strategy="fixed_risk"
        )
        self.executor = TradeExecutor(self.mt5)

        logger.success("✅ All components initialized successfully")

    def _init_mt5(self):
        """Initialize the configured development simulator or read-only MT5 client."""
        if settings.MOCK_MT5:
            if settings.ENV not in {"development", "test"}:
                raise RuntimeError(
                    "Synthetic market data is restricted to development and test."
                )
            logger.warning(
                "Using SYNTHETIC market data for development only; "
                "signals and paper results are not market evidence."
            )
            client = MockMT5(pair=settings.PAIR)
            client.connect()
            return client
        else:
            logger.info("📊 Using RealMT5 in read-only market/account mode")
            client = RealMT5(pair=settings.PAIR)
            success = client.connect()
            if not success:
                raise RuntimeError(
                    "MT5 connection was requested but failed. "
                    "Refusing to fall back to mock data."
                )
            return client

    def _init_ml_model(self):
        """Initialize XGBoost ML model (optional)"""
        if settings.USE_ML_MODEL:
            logger.info("🤖 Initializing XGBoost ML model...")
            ml_model = XGBoostSignalModel(expected_pair=settings.PAIR)
            ml_model.load()
            if ml_model.is_trained:
                logger.success("✅ ML model loaded and ready")
                return ml_model
            raise RuntimeError(
                "USE_ML_MODEL is enabled, but no valid trained model artifact is available."
            )
        else:
            logger.info("💡 ML mode disabled (NO_ML mode - using indicators only)")
            return None

    def run_analysis(self) -> Dict:
        """
        Execute one full trading cycle:
        1. Fetch historical data
        2. Run indicators
        3. Run SMC analysis
        4. Aggregate signals
        5. Calculate risk parameters
        6. Check if trade is valid
        7. Execute if needed
        
        Returns:
            Dict with analysis results
        """
        
        logger.info("=" * 60)
        logger.info("📈 Starting trading analysis cycle...")
        logger.info("=" * 60)

        try:
            # Step 1: Fetch data
            logger.info(f"1️⃣  Fetching market data for {self.settings.PAIR}...")
            df = self.mt5.get_historical_data(bars=500)
            
            if df is None or len(df) < 100:
                logger.error("❌ Insufficient data")
                return {"success": False, "error": "No market data"}

            logger.success(f"✅ Got {len(df)} candles")

            # Step 2: Run indicators
            logger.info("2️⃣  Running technical indicators...")
            indicator_results = self.indicators.run_all(df)
            logger.success("✅ Indicators complete")

            # Step 3: SMC Analysis
            logger.info("3️⃣  Running SMC analysis...")
            smc_results = self.smc.run_all(df)
            logger.success("✅ SMC complete")

            # Step 4: Aggregating signals
            logger.info("4️⃣  Aggregating signals & updating PnL...")
            current_price = df["close"].iloc[-1]
            atr_value = indicator_results.get("ATR", {}).get("value")
            
            # Update live PnL for existing open trades and catch any auto-closed trades
            closed_trades = self.executor.update_prices({self.settings.PAIR: current_price})
            
            # Sync balance for automatically closed trades (SL/TP)
            for ct in closed_trades:
                new_balance = self.risk_manager.account_balance + ct["pnl"]
                self.risk_manager.update_account_balance(new_balance)
            
            signal = self.signal_aggregator.aggregate(
                indicator_results=indicator_results,
                smc_results=smc_results,
                df=df,  # Pass dataframe for ML prediction
                min_confidence=settings.MIN_CONFIDENCE / 100
            )
            logger.success(f"✅ Signal: {signal.signal} (confidence: {signal.overall_confidence:.2f})")

            # Step 5: Risk calculation
            # Step 5: Risk calculation
            logger.info("5️⃣  Calculating risk parameters...")
            if signal.signal in ["BUY", "SELL"]:
                risk_params = self.risk_manager.calculate_position(
                    current_price=current_price,
                    stop_loss_pips=50,  # 50 pips default
                    signal=signal.signal,
                    atr_value=atr_value
                )
                logger.success(f"✅ Risk params calculated")
            else:
                risk_params = None
                logger.info("⏭️  Skipping risk calc (no BUY/SELL signal)")

            # Step 6: Validate trade
            logger.info("6️⃣  Validating trade...")
            open_trades = len(self.executor.open_trades)
            
            if risk_params:
                validation = self.risk_manager.validate_trade(
                    entry_price=risk_params.entry_price,
                    stop_loss=risk_params.stop_loss,
                    open_trades=open_trades,
                    max_open_trades=self.settings.MAX_OPEN_TRADES,
                    max_daily_loss_percent=self.settings.MAX_DAILY_LOSS
                )

                if not validation["is_valid"]:
                    logger.warning(f"❌ Trade validation failed: {validation['reasons']}")
                    risk_params = None
                else:
                    logger.success("✅ Trade is valid")

            # Step 7: Log signal to database
            indicator_json = json.dumps(indicator_results)
            smc_json = json.dumps(smc_results, default=str)
            
            self.db.log_signal(
                pair=self.settings.PAIR,
                signal=signal.signal,
                confidence=signal.overall_confidence,
                buy_count=signal.buy_count,
                sell_count=signal.sell_count,
                neutral_count=signal.neutral_count,
                reason=signal.reason,
                indicator_results=indicator_json,
                smc_results=smc_json
            )

            # Step 8: Execute if conditions met
            trade_result = None
            if signal.signal != "NEUTRAL" and risk_params and validation["is_valid"]:
                logger.info("8️⃣  Executing trade...")
                
                if signal.signal == "BUY":
                    trade_result = self.executor.execute_buy(
                        pair=self.settings.PAIR,
                        entry_price=risk_params.entry_price,
                        stop_loss=risk_params.stop_loss,
                        take_profit=risk_params.take_profit,
                        position_size=risk_params.position_size,
                        confidence=signal.overall_confidence,
                        indicator_signals=indicator_results,
                        smc_signals=smc_results
                    )
                else:  # SELL
                    trade_result = self.executor.execute_sell(
                        pair=self.settings.PAIR,
                        entry_price=risk_params.entry_price,
                        stop_loss=risk_params.stop_loss,
                        take_profit=risk_params.take_profit,
                        position_size=risk_params.position_size,
                        confidence=signal.overall_confidence,
                        indicator_signals=indicator_results,
                        smc_signals=smc_results
                    )

                if trade_result["success"]:
                    logger.success(f"✅ Trade executed: {trade_result['trade_id']}")
                    
                    # Store in database
                    self.db.add_trade(
                        pair=self.settings.PAIR,
                        signal=signal.signal,
                        entry_price=risk_params.entry_price,
                        stop_loss=risk_params.stop_loss,
                        take_profit=risk_params.take_profit,
                        position_size=risk_params.position_size,
                        confidence=signal.overall_confidence,
                        indicator_signals=indicator_json,
                        smc_signals=smc_json
                    )
            
            else:
                logger.info("⏭️  No trade execution (signal is NEUTRAL or validation failed)")

            # Compile results
            results = {
                "success": True,
                "pair": self.settings.PAIR,
                "current_price": current_price,
                "signal": signal.signal,
                "confidence": signal.overall_confidence,
                "buy_count": signal.buy_count,
                "sell_count": signal.sell_count,
                "neutral_count": signal.neutral_count,
                "reason": signal.reason,
                "indicator_results": signal.indicator_results,
                "smc_results": signal.smc_results,
                "ml_boosted": signal.ml_boosted,
                "ml_score": signal.ml_score,
                "ml_mode": "ENABLED" if signal.ml_boosted else "DISABLED (NO_ML)",
                "risk_params": {
                    "entry": risk_params.entry_price if risk_params else None,
                    "stop_loss": risk_params.stop_loss if risk_params else None,
                    "take_profit": risk_params.take_profit if risk_params else None,
                    "position_size": risk_params.position_size if risk_params else None,
                    "risk_amount": risk_params.risk_amount if risk_params else None,
                    "reward_amount": risk_params.reward_amount if risk_params else None,
                    "rrr": risk_params.risk_reward_ratio if risk_params else None
                } if risk_params else None,
                "trade_executed": trade_result["success"] if trade_result else False,
                "trade_id": trade_result.get("trade_id") if trade_result else None,
                "open_positions": len(self.executor.open_trades),
                "total_unrealized_pnl": self.executor.get_total_unrealized_pnl()
            }

            logger.info("=" * 60)
            logger.info("✅ Analysis cycle complete")
            logger.info("=" * 60)

            return results

        except Exception as e:
            logger.error(f"❌ Trading system error: {e}")
            return {"success": False, "error": str(e)}

    def get_system_status(self) -> Dict:
        """Get current system status"""
        return {
            "connected": self.mt5.connected,
            "pair": self.settings.PAIR,
            "timeframe": self.settings.TIMEFRAME,
            "account_balance": self.risk_manager.account_balance,
            "open_trades": len(self.executor.open_trades),
            "total_unrealized_pnl": self.executor.get_total_unrealized_pnl(),
            "market_data_mode": "synthetic_development" if self.settings.MOCK_MT5 else "mt5_read_only",
            "execution_mode": self.executor.EXECUTION_MODE
        }

    def get_open_positions(self) -> list:
        """Get all open positions"""
        return self.executor.get_open_positions()

    def close_position(self, trade_id: int, exit_price: float) -> Dict:
        """Close a specific position and update global account balance"""
        res = self.executor.close_position(trade_id, exit_price)
        if res.get("success"):
            new_balance = self.risk_manager.account_balance + res["trade"]["pnl"]
            self.risk_manager.update_account_balance(new_balance)
        return res

    def disconnect(self):
        """Cleanup and disconnect"""
        if hasattr(self.mt5, 'disconnect'):
            self.mt5.disconnect()
        logger.info("Trading system disconnected")

import os
import sys
from loguru import logger

# Ensure backend root is in Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.trading_system.backtesting.engine import Backtester
from src.trading_system.market.mock_mt5 import MockMT5

def main():
    # Disable excessive logging for speed
    logger.remove()
    logger.add(sys.stdout, level="WARNING")
    
    print("="*60)
    print("📈 XEPHY-AI Historical Backtester")
    print("="*60)
    
    print("Fetching historical data (2000 bars)...")
    mt5 = MockMT5(pair="EURUSD")
    df = mt5.get_historical_data(bars=2000)
    
    print("Initializing Backtesting Engine...")
    backtester = Backtester(df=df, initial_balance=10000.0, risk_percent=1.0)
    
    print("Running step-by-step simulation (this may take a few seconds)...")
    results = backtester.run(window_size=200, step_size=1)
    
    print("\n" + "="*60)
    print("📊 BACKTEST RESULTS")
    print("="*60)
    print(f"Total Trades : {results['total_trades']}")
    print(f"Wins / Losses: {results['wins']} / {results['losses']}")
    print(f"Win Rate     : {results['win_rate']:.2f}%")
    print(f"Profit Factor: {results['profit_factor']:.2f}")
    print(f"Max Drawdown : {results['max_drawdown']:.2f}%")
    print("-" * 60)
    print(f"Initial Bal  : ${results['initial_balance']:.2f}")
    print(f"Final Balance: ${results['final_balance']:.2f}")
    print(f"Net Profit   : ${results['net_profit']:.2f}")
    print("="*60)

if __name__ == "__main__":
    main()

import argparse
from pathlib import Path

from loguru import logger
import numpy as np
import pandas as pd

from src.trading_system.backtesting.engine import Backtester


def load_historical_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Historical data CSV not found: {path}")

    df = pd.read_csv(path)
    required_columns = {"time", "open", "high", "low", "close", "volume"}
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Historical data is missing required columns: {missing}")
    if len(df) < 201:
        raise ValueError("Historical CSV must contain at least 201 candles.")

    try:
        df["time"] = pd.to_datetime(df["time"], errors="raise", utc=True)
        df[list(required_columns - {"time"})] = df[
            list(required_columns - {"time"})
        ].apply(pd.to_numeric, errors="raise")
    except (TypeError, ValueError) as error:
        raise ValueError("Historical CSV contains invalid timestamps or prices.") from error

    if not df["time"].is_monotonic_increasing or df["time"].duplicated().any():
        raise ValueError("Historical candles must be in ascending, unique time order.")

    prices = df[["open", "high", "low", "close"]].to_numpy()
    if not np.isfinite(prices).all() or not np.isfinite(df["volume"].to_numpy()).all():
        raise ValueError("Historical candles must contain only finite numeric values.")
    if (
        (df["high"] < df[["open", "close", "low"]].max(axis=1)).any()
        or (df["low"] > df[["open", "close", "high"]].min(axis=1)).any()
        or (df["volume"] < 0).any()
    ):
        raise ValueError("Historical candles contain invalid OHLC or volume values.")

    return df


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Backtest on a caller-supplied historical OHLCV CSV."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        required=True,
        help="Historical data CSV with time, open, high, low, close, volume columns.",
    )
    args = parser.parse_args(argv)

    df = load_historical_csv(args.csv)
    logger.remove()
    logger.add(lambda message: print(message, end=""), level="WARNING")
    
    print("="*60)
    print("📈 XEPHY-AI Historical Backtester")
    print("="*60)
    
    print(f"Loaded {len(df)} candles from {args.csv}")
    print("Backtest results depend on the supplied dataset and omit unmodeled costs.")
    
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

import pandas as pd
import numpy as np
import os
from loguru import logger

from src.trading_system.ai.model import XGBoostSignalModel
from src.trading_system.market.real_mt5 import RealMT5
from src.trading_system.config.settings import settings

def generate_labels(df: pd.DataFrame, lookahead: int = 10, threshold: float = 0.001) -> np.ndarray:
    """
    Generate training labels based on future price movements.

    Args:
        df: DataFrame with OHLCV data
        lookahead: Number of periods to look ahead for price movement
        threshold: Percentage threshold to classify as BUY or SELL

    Returns:
        Numpy array of labels: 0=SELL, 1=NEUTRAL, 2=BUY
    """
    logger.info(f"Generating labels (lookahead={lookahead}, threshold={threshold*100}%)...")

    # Calculate future returns
    df['future_return'] = df['close'].shift(-lookahead) / df['close'] - 1.0

    # Initialize labels as NEUTRAL (1)
    labels = np.ones(len(df), dtype=int)

    # Mark BUY (2) where return is greater than positive threshold
    labels[df['future_return'] > threshold] = 2

    # Mark SELL (0) where return is less than negative threshold
    labels[df['future_return'] < -threshold] = 0

    # Drop rows with NaN future returns (last 'lookahead' rows)
    # We will slice the arrays later

    counts = np.bincount(labels[~np.isnan(df['future_return'])])
    logger.info(f"Label distribution - SELL: {counts[0] if len(counts)>0 else 0}, NEUTRAL: {counts[1] if len(counts)>1 else 0}, BUY: {counts[2] if len(counts)>2 else 0}")

    return labels

def main():
    logger.info("="*60)
    logger.info("🤖 Starting ML Model Training Pipeline")
    logger.info("="*60)

    if settings.MOCK_MT5:
        raise RuntimeError(
            "Model training is disabled with synthetic market data. "
            "Configure a real historical data source first."
        )

    # Initialize a real historical data source; never train on synthetic prices.
    logger.info("Using RealMT5 client for historical data...")
    mt5_client = RealMT5(pair=settings.PAIR)
    if not mt5_client.connect():
        raise RuntimeError(
            "MT5 connection failed; refusing to train on generated or stale data."
        )

    try:
        # Fetch historical data (larger dataset for training).
        df = mt5_client.get_historical_data(bars=5000)
        if df is None or len(df) < 100:
            raise RuntimeError("Not enough real market data to train the model.")

        # Save the real source data for reproducibility and inspection.
        dataset_path = os.path.join(
            os.path.dirname(__file__), f"training_dataset_{settings.PAIR}.csv"
        )
        df.to_csv(dataset_path, index=False)
        logger.success(f"💾 Dataset saved to: {dataset_path}")

        # Generate labels from subsequent market prices.
        lookahead = 15
        threshold = 0.0005
        labels = generate_labels(df, lookahead=lookahead, threshold=threshold)

        # The final lookahead rows have no future return label.
        df_train = df.iloc[:-lookahead].copy()
        labels_train = labels[:-lookahead]

        model_path = os.path.join(
            os.path.dirname(__file__), "xgboost_signal_model.pkl"
        )
        model = XGBoostSignalModel(model_path=model_path, expected_pair=settings.PAIR)

        logger.info("Starting model training. This may take a moment...")
        model.train(df_train, labels_train)

        if model.is_trained:
            model.save_training_metadata(
                data_source="mt5_read_only",
                pair=settings.PAIR,
                timeframe=settings.TIMEFRAME,
                dataset_path=dataset_path,
            )
            logger.success("✅ Training completed successfully!")
            logger.success(f"Model saved to: {model_path}")
        else:
            raise RuntimeError("Model training did not produce a trained model.")
    finally:
        mt5_client.disconnect()
        logger.info("Training data source disconnected.")

    logger.info("=" * 60)
    logger.info("Pipeline Finished")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()

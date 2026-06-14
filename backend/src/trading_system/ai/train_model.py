import pandas as pd
import numpy as np
import os
from loguru import logger
import sys

# Ensure backend root is in Python path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))

from src.trading_system.ai.model import XGBoostSignalModel
from src.trading_system.market.mock_mt5 import MockMT5
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
    
    # 1. Initialize MT5 client
    if settings.MOCK_MT5:
        logger.info("Using MockMT5 to generate synthetic training data...")
        mt5_client = MockMT5(pair=settings.PAIR)
    else:
        logger.info("Using RealMT5 client for live historical data...")
        mt5_client = RealMT5(pair=settings.PAIR)
        
    success = mt5_client.connect()
    
    if not success and not settings.MOCK_MT5:
        logger.warning("Real MT5 connection failed! Falling back to MockMT5 (Demo Mode)...")
        mt5_client = MockMT5(pair=settings.PAIR)
        mt5_client.connect()
    
    # 2. Fetch historical data (larger dataset for training)
    num_bars = 5000
    df = mt5_client.get_historical_data(bars=num_bars)
    
    if df is None or len(df) < 100:
        logger.error("Not enough data to train the model.")
        return
        
    # Save dataset to CSV for inspection/record
    dataset_path = os.path.join(os.path.dirname(__file__), f"training_dataset_{settings.PAIR}.csv")
    df.to_csv(dataset_path, index=False)
    logger.success(f"💾 Dataset saved to: {dataset_path}")
        
    # 3. Generate labels
    lookahead = 15 # Look ahead 15 candles
    threshold = 0.0005 # 0.05% move
    labels = generate_labels(df, lookahead=lookahead, threshold=threshold)
    
    # Drop the last 'lookahead' rows since we can't calculate future returns for them
    df_train = df.iloc[:-lookahead].copy()
    labels_train = labels[:-lookahead]
    
    # 4. Initialize and Train Model
    model_path = os.path.join(os.path.dirname(__file__), "xgboost_signal_model.pkl")
    model = XGBoostSignalModel(model_path=model_path)
    
    logger.info("Starting model training. This may take a moment...")
    model.train(df_train, labels_train)
    
    if model.is_trained:
        logger.success(f"✅ Training completed successfully!")
        logger.success(f"Model saved to: {model_path}")
    else:
        logger.error("❌ Training failed.")
        
    mt5_client.disconnect()
    logger.info("="*60)
    logger.info("Pipeline Finished")
    logger.info("="*60)

if __name__ == "__main__":
    main()

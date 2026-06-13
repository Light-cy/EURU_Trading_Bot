import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.preprocessing import StandardScaler
from loguru import logger
from typing import Dict, Tuple
import os
import joblib

class XGBoostSignalModel:
    """
    XGBoost model for predicting BUY/SELL signals
    Trains on historical indicator data to boost confidence scores
    """

    def __init__(self, model_path: str = None):
        """
        Initialize XGBoost model
        
        Args:
            model_path: Path to save/load trained model
        """
        self.model = None
        self.scaler = StandardScaler()
        self.model_path = model_path or "xgboost_signal_model.pkl"
        self.is_trained = False
        self.feature_names = []
        logger.info("XGBoostSignalModel initialized")

    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract features from OHLCV data for ML
        
        Returns:
            DataFrame with engineered features
        """
        features = pd.DataFrame()

        # Price features
        features['price_change'] = df['close'].pct_change()
        features['high_low_ratio'] = (df['high'] - df['low']) / df['close']
        features['close_open_ratio'] = (df['close'] - df['open']) / df['open']

        # Volume features
        features['volume_change'] = df['volume'].pct_change()
        features['volume_avg_ratio'] = df['volume'] / df['volume'].rolling(20).mean()

        # Momentum features
        features['rsi'] = self._calculate_rsi(df['close'], 14)
        features['momentum'] = df['close'].diff(10)
        features['acceleration'] = features['momentum'].diff()

        # Trend features
        ema_fast = df['close'].ewm(span=12).mean()
        ema_slow = df['close'].ewm(span=26).mean()
        features['ema_diff'] = ema_fast - ema_slow
        features['ema_diff_pct'] = (ema_fast - ema_slow) / df['close']

        # Volatility features
        features['volatility'] = df['close'].pct_change().rolling(14).std()
        features['volatility_ratio'] = features['volatility'] / features['volatility'].rolling(20).mean()

        # Support/Resistance
        features['distance_to_high'] = (df['high'].rolling(20).max() - df['close']) / df['close']
        features['distance_to_low'] = (df['close'] - df['low'].rolling(20).min()) / df['close']

        # Fill NaN values
        features = features.fillna(0)

        self.feature_names = features.columns.tolist()
        return features

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def train(self, df: pd.DataFrame, labels: np.ndarray):
        """
        Train XGBoost model on historical data
        
        Args:
            df: OHLCV dataframe
            labels: Binary labels (0=SELL, 1=BUY, 2=NEUTRAL)
        """
        try:
            logger.info("Training XGBoost model...")

            # Extract features
            X = self._extract_features(df)

            # Scale features
            X_scaled = self.scaler.fit_transform(X)

            # Train model
            self.model = XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                objective='multi:softmax',
                num_class=3,  # 0=SELL, 1=NEUTRAL, 2=BUY
                random_state=42,
                verbosity=0
            )

            self.model.fit(X_scaled, labels)
            self.is_trained = True

            # Save model
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.model_path.replace('.pkl', '_scaler.pkl'))

            logger.success(f"XGBoost model trained and saved to {self.model_path}")

        except Exception as e:
            logger.error(f"Model training failed: {e}")

    def load(self):
        """Load pre-trained model from disk"""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.model_path.replace('.pkl', '_scaler.pkl'))
                self.is_trained = True
                logger.success(f"Model loaded from {self.model_path}")
            else:
                logger.warning(f"Model file not found: {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")

    def predict(self, df: pd.DataFrame) -> Dict:
        """
        Predict signal using XGBoost
        
        Args:
            df: OHLCV dataframe
            
        Returns:
            Dict with signal and confidence
        """
        if not self.is_trained or self.model is None:
            logger.warning("Model not trained. Returning neutral signal.")
            return {"signal": "NEUTRAL", "confidence": 0.0, "ml_score": 0.0}

        try:
            # Extract features
            X = self._extract_features(df)
            X_scaled = self.scaler.transform(X)

            # Get prediction and probabilities
            prediction = self.model.predict(X_scaled[-1:])
            probabilities = self.model.predict_proba(X_scaled[-1:])

            # Map prediction to signal
            signal_map = {0: "SELL", 1: "NEUTRAL", 2: "BUY"}
            signal = signal_map[prediction[0]]

            # Get confidence (probability of predicted class)
            confidence = float(np.max(probabilities))

            logger.info(f"ML Prediction: {signal} (confidence: {confidence:.2f})")

            return {
                "signal": signal,
                "confidence": round(confidence, 2),
                "ml_score": round(confidence, 2),
                "probabilities": {
                    "SELL": round(probabilities[0][0], 2),
                    "NEUTRAL": round(probabilities[0][1], 2),
                    "BUY": round(probabilities[0][2], 2)
                }
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {"signal": "NEUTRAL", "confidence": 0.0, "ml_score": 0.0}

    def boost_confidence(self, indicator_confidence: float, ml_result: Dict) -> float:
        """
        Boost indicator confidence using ML prediction
        
        Args:
            indicator_confidence: Original indicator confidence (0-1)
            ml_result: ML prediction result dict
            
        Returns:
            Boosted confidence score
        """
        if ml_result["ml_score"] == 0.0:
            return indicator_confidence

        # Average indicator and ML confidence
        boosted = (indicator_confidence + ml_result["ml_score"]) / 2

        logger.info(
            f"Confidence boosted: {indicator_confidence:.2f} + "
            f"{ml_result['ml_score']:.2f} = {boosted:.2f}"
        )

        return min(boosted, 1.0)  # Cap at 1.0

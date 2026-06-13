from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    # Trading
    PAIR: str = os.getenv("PAIR", "EURUSD")
    TIMEFRAME: str = os.getenv("TIMEFRAME", "M15")
    RISK_PERCENT: float = float(os.getenv("RISK_PERCENT", 1.0))
    MIN_CONFIDENCE: float = float(os.getenv("MIN_CONFIDENCE", 85.0))
    MAX_DAILY_LOSS: float = float(os.getenv("MAX_DAILY_LOSS", 3.0))
    MAX_OPEN_TRADES: int = int(os.getenv("MAX_OPEN_TRADES", 3))

    # Environment
    ENV: str = os.getenv("ENV", "development")
    MOCK_MT5: bool = os.getenv("MOCK_MT5", "true").lower() == "true"
    LOOP_INTERVAL: int = int(os.getenv("LOOP_INTERVAL", 900)) # 900s = 15m
    
    # Machine Learning
    USE_ML_MODEL: bool = os.getenv("USE_ML_MODEL", "false").lower() == "true"

    # Flask
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "true").lower() == "true"

settings = Settings()
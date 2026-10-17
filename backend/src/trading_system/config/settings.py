from dotenv import load_dotenv
import os

load_dotenv()


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized not in {"true", "false"}:
        raise ValueError(f"{name} must be 'true' or 'false'.")
    return normalized == "true"


def _validate_market_data_mode(environment: str, synthetic_data_enabled: bool) -> None:
    if synthetic_data_enabled and environment not in {"development", "test"}:
        raise ValueError(
            "MOCK_MT5 is restricted to development and test environments."
        )


class Settings:
    # Trading
    PAIR: str = os.getenv("PAIR", "EURUSD")
    TIMEFRAME: str = os.getenv("TIMEFRAME", "M15")
    RISK_PERCENT: float = float(os.getenv("RISK_PERCENT", 1.0))
    MIN_CONFIDENCE: float = float(os.getenv("MIN_CONFIDENCE", 85.0))
    MAX_DAILY_LOSS: float = float(os.getenv("MAX_DAILY_LOSS", 3.0))
    MAX_OPEN_TRADES: int = int(os.getenv("MAX_OPEN_TRADES", 3))

    # Environment
    ENV: str = os.getenv("ENV", "development").strip().lower()
    MOCK_MT5: bool = _env_bool("MOCK_MT5", False)
    _validate_market_data_mode(ENV, MOCK_MT5)
    LOOP_INTERVAL: int = int(os.getenv("LOOP_INTERVAL", 900)) # 900s = 15m
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./trading_system.db")
    
    # Real MT5 Credentials
    MT5_LOGIN: int = int(os.getenv("MT5_LOGIN", 0)) if os.getenv("MT5_LOGIN") else 0
    MT5_PASSWORD: str = os.getenv("MT5_PASSWORD", "")
    MT5_SERVER: str = os.getenv("MT5_SERVER", "")
    
    # Machine Learning
    USE_ML_MODEL: bool = _env_bool("USE_ML_MODEL", False)

    # Flask
    FLASK_HOST: str = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT: int = int(os.getenv("FLASK_PORT", 5000))
    FLASK_DEBUG: bool = _env_bool("FLASK_DEBUG", True)
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]

settings = Settings()
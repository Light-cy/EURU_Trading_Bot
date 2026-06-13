from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from loguru import logger
import os

# Database setup
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./trading_system.db"  # SQLite for development
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Trade(Base):
    """Trade model — stores all executed trades"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String(20), default="EURUSD")
    signal = Column(String(10))  # BUY, SELL
    entry_price = Column(Float)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    position_size = Column(Float)
    status = Column(String(20), default="OPEN")  # OPEN, CLOSED, CANCELLED
    profit_loss = Column(Float, nullable=True)
    profit_loss_pips = Column(Float, nullable=True)
    profit_loss_percent = Column(Float, nullable=True)
    entry_time = Column(DateTime, default=datetime.utcnow)
    exit_time = Column(DateTime, nullable=True)
    close_reason = Column(String(100), nullable=True)  # SL, TP, Manual, etc
    indicator_signals = Column(Text)  # JSON string of indicator results
    smc_signals = Column(Text)  # JSON string of SMC results
    confidence = Column(Float)  # Signal confidence

    def __repr__(self):
        return f"<Trade {self.pair} {self.signal} @ {self.entry_price}>"


class SignalLog(Base):
    """Signal history — tracks all generated signals"""
    __tablename__ = "signal_logs"

    id = Column(Integer, primary_key=True, index=True)
    pair = Column(String(20), default="EURUSD")
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    signal = Column(String(10))  # BUY, SELL, NEUTRAL
    confidence = Column(Float)
    buy_count = Column(Integer)
    sell_count = Column(Integer)
    neutral_count = Column(Integer)
    reason = Column(String(500))
    indicator_results = Column(Text)  # JSON string
    smc_results = Column(Text)  # JSON string
    was_executed = Column(Boolean, default=False)

    def __repr__(self):
        return f"<SignalLog {self.signal} {self.confidence:.2f}>"


class AccountStats(Base):
    """Account statistics — daily/weekly performance tracking"""
    __tablename__ = "account_stats"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, unique=True, index=True)
    starting_balance = Column(Float)
    ending_balance = Column(Float)
    daily_profit_loss = Column(Float)
    daily_profit_loss_percent = Column(Float)
    trades_won = Column(Integer, default=0)
    trades_lost = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)

    def __repr__(self):
        return f"<AccountStats {self.date.date()} — {self.daily_profit_loss_percent:.2f}%>"


class DatabaseManager:
    """Database operations handler"""

    def __init__(self):
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.success("Database initialized")

    @staticmethod
    def get_session() -> Session:
        """Get a new database session"""
        return SessionLocal()

    @staticmethod
    def add_trade(
        pair: str,
        signal: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        position_size: float,
        confidence: float,
        indicator_signals: str,
        smc_signals: str
    ) -> Trade:
        """Add a new trade to database"""
        session = SessionLocal()
        trade = Trade(
            pair=pair,
            signal=signal,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            position_size=position_size,
            confidence=confidence,
            indicator_signals=indicator_signals,
            smc_signals=smc_signals,
            status="OPEN"
        )
        session.add(trade)
        session.commit()
        session.refresh(trade)
        logger.info(f"Trade added to database: ID={trade.id}")
        session.close()
        return trade

    @staticmethod
    def close_trade(
        trade_id: int,
        exit_price: float,
        close_reason: str = "Manual"
    ) -> Trade:
        """Close an open trade"""
        session = SessionLocal()
        trade = session.query(Trade).filter(Trade.id == trade_id).first()

        if trade:
            trade.exit_price = exit_price
            trade.status = "CLOSED"
            trade.exit_time = datetime.utcnow()
            trade.close_reason = close_reason

            # Calculate P&L
            if trade.signal == "BUY":
                pips = (exit_price - trade.entry_price) / 0.0001
            else:  # SELL
                pips = (trade.entry_price - exit_price) / 0.0001

            trade.profit_loss_pips = pips
            trade.profit_loss = pips * trade.position_size * 10  # Assuming standard lot
            trade.profit_loss_percent = (trade.profit_loss / trade.entry_price) * 100

            session.commit()
            logger.info(f"Trade closed: ID={trade.id}, P&L={trade.profit_loss:.2f}")
        session.close()
        return trade

    @staticmethod
    def log_signal(
        pair: str,
        signal: str,
        confidence: float,
        buy_count: int,
        sell_count: int,
        neutral_count: int,
        reason: str,
        indicator_results: str,
        smc_results: str
    ) -> SignalLog:
        """Log a generated signal"""
        session = SessionLocal()
        log = SignalLog(
            pair=pair,
            signal=signal,
            confidence=confidence,
            buy_count=buy_count,
            sell_count=sell_count,
            neutral_count=neutral_count,
            reason=reason,
            indicator_results=indicator_results,
            smc_results=smc_results
        )
        session.add(log)
        session.commit()
        session.close()
        return log

    @staticmethod
    def get_recent_trades(limit: int = 10) -> list:
        """Get recent trades"""
        session = SessionLocal()
        trades = session.query(Trade).order_by(Trade.entry_time.desc()).limit(limit).all()
        session.close()
        return trades

    @staticmethod
    def get_open_trades() -> list:
        """Get all open trades"""
        session = SessionLocal()
        trades = session.query(Trade).filter(Trade.status == "OPEN").all()
        session.close()
        return trades

    @staticmethod
    def get_signal_history(pair: str, days: int = 7) -> list:
        """Get signal history for a pair"""
        from datetime import timedelta
        session = SessionLocal()
        cutoff = datetime.utcnow() - timedelta(days=days)
        logs = session.query(SignalLog).filter(
            SignalLog.pair == pair,
            SignalLog.timestamp >= cutoff
        ).order_by(SignalLog.timestamp.desc()).all()
        session.close()
        return logs

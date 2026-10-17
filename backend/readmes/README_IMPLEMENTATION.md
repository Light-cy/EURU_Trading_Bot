# 🚀 Xephy-AI Trading System - Backend Implementation

Quantitative analysis and paper-trading prototype with technical indicators, SMC analysis, optional AI signals, and risk controls.

> **Execution limitation:** This project only simulates positions in memory. It does not submit broker orders, even when MT5 is used as a market-data source. Do not use it for live trading.

## 📋 What's Implemented

### ✅ Core Modules

1. **Market Data** (`market/mock_mt5.py`)
   - Synthetic MockMT5 adapter for explicit development/test UI flows only
   - Optional real MT5 market-data integration
   - OHLCV candle generation
   - Account info simulation

2. **Technical Indicators** (`indicators/`)
   - RSI, EMA, MACD, ATR, VWAP, ADX, Bollinger Bands
   - Base indicator framework
   - IndicatorManager orchestrates all

3. **Smart Money Concepts** (`smc/`)
   - Market Structure (BOS, CHoCH, trends)
   - Order Block Detection
   - Fair Value Gap Detection
   - SMCManager combines all

4. **Signal Aggregation** (`core/signal_aggregator.py`)
   - Combines indicator + SMC signals
   - Consensus-based decision logic
   - Confidence scoring
   - Smart filtering

5. **Risk Management** (`risk/manager.py`)
   - Position sizing (Fixed Risk & Kelly)
   - Stop Loss / Take Profit calculation
   - Trade validation
   - Risk limits enforcement

6. **Database** (`database/models.py`)
   - SQLAlchemy ORM
   - Trade history tracking
   - Signal logging
   - Account statistics

7. **Paper Execution** (`execution/executor.py`)
   - In-memory position management
   - Simulated P&L tracking
   - Simulated SL/TP automation
   - No broker order submission

8. **Trading Engine** (`main.py`)
   - Orchestrates all components
   - Full trading cycle: Data → Analysis → Execution
   - Logging and reporting

9. **Flask API** (`app.py`)
   - RESTful API endpoints
   - Real-time status & positions
   - Manual trigger analysis
   - Background analysis loop

---

## 🔄 Market Data Source

### Current Setup (Linux)
- Synthetic **MockMT5** is an explicit development-only adapter, not a market feed.
- It is disabled by default; set `MOCK_MT5=true` only in `ENV=development` or `ENV=test`.
- The dashboard labels its balances and quotes as synthetic. These values are not evidence for strategy performance.

The optional `RealMT5` adapter is read-only: it retrieves account details, a live quote, and account-wide realized deal results/costs. It does not enable order execution. If MT5 is selected but cannot connect, startup fails rather than silently switching to generated mock data.

Use `MOCK_MT5=true` only to exercise development UI flows. Model training refuses synthetic data, and real MT5 connection failure never falls back to generated prices. To inspect an MT5 account, use a supported Windows host with the MetaTrader 5 terminal installed and logged into a broker demo account, install the optional `MetaTrader5` Python package there, and leave `MOCK_MT5=false`. Store credentials in an untracked `.env`; never commit them. Keep the API private because authentication has not yet been implemented.

Unverified legacy training datasets and model artifacts have been removed.
ML remains disabled by default; startup requires a sidecar identifying
read-only MT5 data, the configured pair, and matching model/scaler hashes.
This is an integrity record, not cryptographic proof. Backtests accept only a
caller-provided OHLCV CSV and do not manufacture candles.

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### 2. Run Trading System
```bash
python app.py
```

Server starts at: `http://localhost:5000`

Run the focused core tests from the backend directory:

```bash
python -m unittest discover -s tests
```

### Database and migrations

**FYP database direction:** The proposal specifies MongoDB, so MongoDB is the
selected target. The current implementation remains SQLAlchemy/Alembic with
PostgreSQL configured in the active local environment and SQLite as the code
default. MongoDB support and a safe history transition have not been
implemented. Do not delete or overwrite existing relational database history.

The local default remains `sqlite:///./trading_system.db` (relative to the
backend working directory). Schema creation is managed by Alembic; the app now
fails with a migration instruction rather than creating tables on startup.
Run `alembic upgrade head` after configuring the database and before starting
the API.

For a user-local PostgreSQL cluster without admin privileges, see the setup
commands in the root README. Configure the untracked `backend/.env` with a
PostgreSQL `DATABASE_URL` that uses the cluster's local peer-authenticated
socket, then run the migration command from `backend/`. The initial migration
creates the trades, signal logs, and account statistics schema. When pointed at
a matching legacy SQLite schema, it versions existing tables and leaves their
records intact.

To copy SQLite history into PostgreSQL, back up the SQLite file first, migrate
the destination schema, and run:

```bash
python scripts/migrate_sqlite_to_postgres.py --source ./trading_system.db
```

The tool preserves primary keys, verifies matching columns and row counts,
updates PostgreSQL ID sequences, and refuses to import into non-empty history
tables. It does not alter the source SQLite database. Confirm the authoritative
SQLite file before transfer; do not delete a database to resolve a migration
error.

### 3. Trigger Analysis
```bash
curl -X POST http://localhost:5000/api/analyze
```

---

## 📡 API Endpoints

### System Management
- `GET /` → Health check
- `GET /api/status` → System status
- `GET /api/health` → Detailed health
- `GET /api/settings` → Current settings

### Analysis & Trading
- `POST /api/analyze` → Run one analysis cycle
- `POST /api/analysis/start` → Start background analysis
- `POST /api/analysis/stop` → Stop background analysis
- `GET /api/analysis/status` → Loop status

### Positions & Trades
- `GET /api/positions` → All open positions
- `POST /api/positions/{trade_id}` → Close position
- `GET /api/trades/recent?limit=10` → Recent closed trades
- `GET /api/account` → Read-only account details
- `GET /api/market/quote` → Current quote for the configured pair
- `GET /api/account/performance?days=30` → Realized account-wide results and broker costs

### Signals & History
- `GET /api/signals/history?pair=EURUSD&days=7` → Signal history

---

## ⚙️ Configuration (.env)

```
# Market
PAIR=EURUSD           # Trading pair
TIMEFRAME=M15         # Candle timeframe

# Trading
RISK_PERCENT=1.0      # Risk per trade
MIN_CONFIDENCE=85.0   # Signal confidence threshold
MAX_DAILY_LOSS=3.0    # Max daily loss %
MAX_OPEN_TRADES=3     # Max concurrent trades

# Mode
MOCK_MT5=true         # false = read-only MT5 account/market data
ENV=development       # development or production

# Server
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=true

# Browser access (comma-separated allowed frontend origins)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

---

## 🔄 Trading Flow

```
┌─────────────┐
│ Fetch Data  │ ← MockMT5 or Real MT5
└─────┬───────┘
      │
┌─────▼──────────────┐
│ Technical          │
│ Indicators (7)     │ ← RSI, EMA, MACD, ATR, etc
└─────┬──────────────┘
      │
┌─────▼──────────────┐
│ SMC Analysis       │ ← Structure, OB, FVG
└─────┬──────────────┘
      │
┌─────▼──────────────┐
│ Signal Aggregator  │ ← Combine signals
└─────┬──────────────┘
      │
┌─────▼──────────────┐
│ Risk Manager       │ ← SL, TP, Position size
└─────┬──────────────┘
      │
┌─────▼──────────────┐
│ Validate Trade     │ ← Check limits
└─────┬──────────────┘
      │
┌─────▼──────────────┐
│ Paper Execution    │ ← In-memory simulated position
└─────┬──────────────┘
      │
┌─────▼──────────────┐
│ Log to Database    │ ← Save history
└─────────────────────┘
```

---

## 📊 Database Schema

### trades
- trade_id, pair, signal (BUY/SELL)
- entry_price, exit_price
- stop_loss, take_profit, position_size
- profit_loss, status (OPEN/CLOSED)
- entry_time, exit_time, reason
- confidence score

### signal_logs
- timestamp, signal, confidence
- buy/sell/neutral counts
- reason and details
- indicator + SMC results as JSON

### account_stats
- daily stats: P&L, win rate, max drawdown
- performance metrics

---

## 🧪 Testing Signals

```bash
# Get mock price
curl http://localhost:5000/api/account

# Run analysis
curl -X POST http://localhost:5000/api/analyze

# Check positions
curl http://localhost:5000/api/positions

# View signals history
curl "http://localhost:5000/api/signals/history?days=7"
```

---

## 🎯 Next Steps / TODO

**Optional Enhancements:**

1. **AI Module** (`ai/`)
   - ML-based signal prediction
   - Feature engineering
   - Model training/inference

2. **News Analysis** (`news/`)
   - Real-time news sentiment
   - Economic calendar integration

3. **Advanced Risk**
   - Correlation analysis
   - Portfolio optimization
   - Drawdown recovery

4. **WebSocket Support**
   - Real-time position updates
   - Live price streaming
   - Multi-client support

5. **Backtesting Framework**
   - Historical data replay
   - Strategy optimization
   - Performance reporting

---

## 🔧 Troubleshooting

### "MockMT5 not connected"
```python
# Will auto-connect, but manually:
trading_system.mt5.connect()
```

### Database errors
```bash
# Inspect the configured database URL and apply schema migrations
alembic current
alembic upgrade head
```

### No signals generated
```
Check:
1. Minimum confidence (MIN_CONFIDENCE=85.0)
2. Indicator consensus (need 60%+)
3. Data available (500 candles loaded)
```

---

## 📝 Architecture Notes

**Design Principles:**
- ✅ Modular: Each component independent
- ✅ Extensible: Easy to add new indicators/strategies
- ✅ Platform-agnostic: MockMT5 ↔ Real MT5
- ✅ Versioned schema: Alembic migrations; PostgreSQL driver available
- ✅ Database-backed: All trades tracked
- ✅ API-driven: Full REST interface

**Key Classes:**
- `TradingSystem` - Main orchestrator
- `IndicatorManager` - Runs all indicators
- `SMCManager` - SMC analysis
- `SignalAggregator` - Signal combination
- `RiskManager` - Risk calculations
- `TradeExecutor` - Order management
- `DatabaseManager` - Data persistence

---

## 📚 Dependencies

- Flask, Flask-CORS
- Pandas, NumPy
- SQLAlchemy (ORM)
- Loguru (logging)
- MetaTrader5 (optional market-data connection; no order execution)
- scikit-learn, XGBoost (ML, for AI module)

All in `requirements.txt` ✅

---

**Status:** Research / paper-trading prototype; not production-ready
**Version:** 1.0.0

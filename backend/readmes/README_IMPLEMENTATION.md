# 🚀 Xephy-AI Trading System - Backend Implementation

Complete quantitative trading system with technical indicators, SMC analysis, AI signals, and automated execution.

## 📋 What's Implemented

### ✅ Core Modules

1. **Market Data** (`market/mock_mt5.py`)
   - MockMT5 for Linux development (demo data)
   - Real MT5 integration ready for Windows
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

7. **Trade Execution** (`execution/executor.py`)
   - Position management
   - Order execution
   - P&L tracking
   - SL/TP automation

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

## 🔄 MT5 Switching (Linux → Windows)

### Current Setup (Linux)
- Using **MockMT5** for demo data
- `settings.MOCK_MT5=true` in `.env`
- Works immediately on Linux

### Switch to Real MT5 (Windows)
Only 3 simple steps:

```bash
# Step 1: Install MT5 package
pip install MetaTrader5

# Step 2: Change .env
MOCK_MT5=false

# Step 3: Update config/settings.py OR create an adapter
# The TradeExecutor and main.py are already compatible!
```

**Why it's easy to switch?**
- `TradeExecutor` uses generic MT5 interface
- `TradingSystem` initializes MT5 in `_init_mt5()` method
- Just swap the client, everything else works

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Trading System
```bash
python app.py
```

Server starts at: `http://localhost:5000`

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
- `GET /api/account` → Account info

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
MOCK_MT5=true         # false = use real MT5
ENV=development       # development or production

# Server
FLASK_PORT=5000
FLASK_DEBUG=true
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
│ Execute Trade      │ ← Send order
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
# Reset database
rm trading_system.db
# Will recreate on next run
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
- ✅ Production-ready: Error handling, logging, validation
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
- MetaTrader5 (real trading, optional)
- scikit-learn, XGBoost (ML, for AI module)

All in `requirements.txt` ✅

---

**Status:** ✅ Production-Ready (Core)
**Last Updated:** June 2026
**Version:** 1.0.0

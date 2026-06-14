# 🎯 XEPHY-AI ARCHITECTURE DIAGRAM

## Complete System Flow

```
                    ┌─────────────────────────────────────────┐
                    │    Browser / Mobile Frontend             │
                    │     (React + Vite)                       │
                    └─────────────────┬───────────────────────┘
                                      │ HTTP/REST
                    ┌─────────────────▼───────────────────────┐
                    │     Flask API Server (app.py)            │
                    │  ✅ 15+ REST Endpoints                   │
                    │  ✅ CORS Enabled                         │
                    │  ✅ Error Handling                       │
                    │  ✅ Authentication Ready                 │
                    └─────────────────┬───────────────────────┘
                                      │ Python
                    ┌─────────────────▼───────────────────────┐
                    │   Trading System (main.py)               │
                    │  ✅ Orchestrates all components          │
                    │  ✅ Full trading cycle                   │
                    │  ✅ Error recovery                       │
                    │  ✅ System monitoring                    │
                    └──┬──────────┬──────────┬──────────┬──────┘
                       │          │          │          │
        ┌──────────────┘          │          │          └──────────────┐
        │                         │          │                         │
        ▼                         ▼          ▼                         ▼
   ┌────────────┐         ┌────────────┐  ┌────────────┐        ┌─────────────┐
   │ Indicators │         │    SMC     │  │  Signals   │        │    Risk     │
   │ Manager    │         │  Manager   │  │ Aggregator │        │   Manager   │
   │            │         │            │  │            │        │             │
   │ • RSI      │         │ • Structure│  │ • 60% vote │        │ • Position  │
   │ • EMA      │         │ • OB       │  │ • Confidence         │   Sizing    │
   │ • MACD     │         │ • FVG      │  │ • BUY/SELL │        │ • SL/TP     │
   │ • ATR      │         │            │  │ • Filtering          │ • Validation│
   │ • VWAP     │         └────────────┘  └────────────┘        │ • Limits    │
   │ • ADX      │                                                 │             │
   │ • Bollinger│                                                 └─────────────┘
   └────────────┘                                                       ▲
        ▲                                                               │
        │                                                               │
        │              ┌──────────────────────────────────┐            │
        │              │   Trade Executor                 │            │
        │              │  ✅ BUY/SELL Orders              │◄───────────┘
        │              │  ✅ Position Tracking            │
        │              │  ✅ SL/TP Automation             │
        │              │  ✅ P&L Calculation              │
        │              │  ✅ Trade History                │
        │              └──────────┬───────────────────────┘
        │                         │
        │        ┌────────────────┼────────────────┐
        │        │                │                │
        │        ▼                ▼                ▼
        │   ┌────────────┐   ┌────────────┐  ┌──────────────┐
        │   │ Database   │   │ Account    │  │ Trade Info   │
        │   │ (SQLite)   │   │ Monitoring │  │ / Positions  │
        │   │            │   │            │  │              │
        │   │ • Trades   │   │ • Balance  │  │ • Open       │
        │   │ • Signals  │   │ • P&L      │  │ • Closed     │
        │   │ • Stats    │   │ • Win Rate │  │ • History    │
        │   └────────────┘   └────────────┘  └──────────────┘
        │        ▲
        │        │ Logging & Persistence
        │        │
        └────────┴────────────────────────────────────────┐
                                                           │
                                    ┌──────────────────────▼──────┐
                                    │  Market Data Layer           │
                                    │                              │
                         ┌──────────┴──────────┐                   │
                         │                     │                   │
                         ▼                     ▼                   │
                    ┌──────────┐        ┌──────────────┐           │
                    │ MockMT5  │        │  Real MT5    │           │
                    │ (Linux)  │        │  (Windows)   │           │
                    │          │        │              │           │
                    │ MOCK_MT5 │        │ MOCK_MT5     │           │
                    │= true    │        │ = false      │           │
                    │          │        │              │           │
                    │ Demo Data│        │ Real Market  │           │
                    │ 500 OHLC │        │ Data         │           │
                    └──────────┘        └──────────────┘           │
                         ▲                     ▲                   │
                         │                     │                   │
                         └─────────────────────┴───────────────────┘
```

---

## Component Responsibilities

### 1️⃣ Flask API Server (`app.py`)
- Exposes REST endpoints
- Routes requests to TradingSystem
- Background analysis loop
- Real-time monitoring
- Error handling
- Logging

### 2️⃣ Trading System (`main.py`)
- Orchestrates full trading cycle
- Initializes all components
- Error recovery
- System status
- Logging

### 3️⃣ Market Data Layer
- **Linux**: MockMT5 (simulates MT5)
- **Windows**: Real MT5 (production)
- Same interface for both
- Auto-selection based on settings

### 4️⃣ Indicator Manager
- 7 technical indicators
- Each returns: signal + confidence
- Aggregates results
- Passes to SignalAggregator

### 5️⃣ SMC Manager
- Market Structure analysis
- Order Block detection
- Fair Value Gap detection
- Provides trading context

### 6️⃣ Signal Aggregator (`core/`)
- Combines 10+ signals
- 60% consensus voting
- Confidence scoring
- Final: BUY/SELL/NEUTRAL

### 7️⃣ Risk Manager (`risk/`)
- Position sizing
- Stop loss / Take profit
- Risk/Reward ratios
- Trade validation

### 8️⃣ Trade Executor (`execution/`)
- Execute buy/sell orders
- Track open positions
- Real-time P&L
- SL/TP automation
- Close positions

### 9️⃣ Database (`database/`)
- SQLAlchemy ORM
- Trade history
- Signal logs
- Account stats
- Audit trail

---

## Data Flow: One Complete Trading Cycle

```
Time: T0 = 00:00 (Analysis starts)

Step 1: Fetch Market Data (T0+1s)
  Market Data Layer (MockMT5 or MT5)
    ↓
  DataFrame (500 OHLC candles)

Step 2: Technical Analysis (T0+2s)
  Indicator Manager
    ├─ RSI(14)         → signal: SELL, conf: 0.85
    ├─ EMA(20/50)      → signal: BUY,  conf: 0.90
    ├─ MACD            → signal: SELL, conf: 0.75
    ├─ ATR(14)         → signal: BUY,  conf: 0.60
    ├─ VWAP            → signal: BUY,  conf: 0.75
    ├─ ADX(14)         → signal: SELL, conf: 0.70
    └─ Bollinger(20,2) → signal: BUY,  conf: 0.80
    
  Results:
    Buy:    4 signals (avg conf: 0.76)
    Sell:   3 signals (avg conf: 0.77)
    Neutral: 0

Step 3: SMC Analysis (T0+3s)
  SMC Manager
    ├─ Structure   → Trend: UPTREND, BOS: BULLISH, conf: 0.80
    ├─ OrderBlock  → Signal: BUY,    conf: 0.88
    └─ FVG         → Signal: BUY,    conf: 0.82

Step 4: Signal Aggregation (T0+4s)
  SignalAggregator
    ├─ Indicator consensus: 4/7 BUY (57% → below 60%)
    ├─ Confidence: 0.76
    ├─ SMC consensus: 2/3 BUY
    ├─ SMC trend: UPTREND
    ├─ Decision logic: SMC alignment overrides indicator split
    └─ Final → BUY (conf: 0.78)

Step 5: Risk Calculation (T0+5s)
  RiskManager
    ├─ Entry Price: 1.0850
    ├─ Current Price: 1.0847
    ├─ SL Distance: 50 pips
    ├─ Stop Loss: 1.0797
    ├─ Take Profit: 1.0950 (2:1 RRR)
    ├─ Risk Amount: $100 (1% of $10,000)
    ├─ Position Size: 1.5 lots/0.2
    ├─ Reward Amount: $200
    └─ RRR: 2.0

Step 6: Validation (T0+6s)
  RiskManager.validate_trade()
    ├─ Open trades: 0 < 3 ✅
    ├─ Daily loss: 0% < 3% ✅
    ├─ SL distance: 50 pips > 10 pips ✅
    ├─ SL distance: 50 pips < 500 pips ✅
    └─ Status: VALID ✅

Step 7: Order Execution (T0+7s)
  TradeExecutor
    ├─ Signal: BUY
    ├─ Create Position
    ├─ Trade ID: 1001
    ├─ Status: OPEN
    └─ Log to memory

Step 8: Database Logging (T0+8s)
  DatabaseManager
    ├─ Trade record:
    │  ├─ id: 1001
    │  ├─ pair: EURUSD
    │  ├─ signal: BUY
    │  ├─ entry_price: 1.0847
    │  ├─ stop_loss: 1.0797
    │  ├─ take_profit: 1.0950
    │  ├─ position_size: 1.5
    │  ├─ confidence: 0.78
    │  ├─ status: OPEN
    │  ├─ indicator_signals: {JSON}
    │  └─ smc_signals: {JSON}
    │
    └─ Signal record:
       ├─ timestamp: 2026-06-12 T00:08:00Z
       ├─ signal: BUY
       ├─ confidence: 0.78
       ├─ buy_count: 4
       ├─ sell_count: 3
       ├─ neutral_count: 0
       └─ was_executed: true

Step 9: Return Results (T0+9s)
  Flask → Frontend (JSON response)
  {
    "success": true,
    "signal": "BUY",
    "confidence": 0.78,
    "trade_executed": true,
    "trade_id": 1001,
    "open_positions": 1,
    "total_unrealized_pnl": 0.00
  }

Duration: ~9 seconds total ⚡
```

---

## MT5 Switching: Architecture

```
Settings (.env)
    │
    ├─ MOCK_MT5 = true   → Linux development
    │                      └─ MockMT5 class (demo data)
    │
    └─ MOCK_MT5 = false  → Windows production
                           └─ MetaTrader5 class (real data)

TradingSystem._init_mt5()
    │
    ├─ Check MOCK_MT5 flag
    │
    ├─ IF true:
    │  └─ from src.trading_system.market.mock_mt5 import MockMT5
    │     └─ return MockMT5(pair=settings.PAIR)
    │
    └─ IF false:
       └─ try:
          │  from src.trading_system.market.mt5 import MT5  # NEW
          │  return MT5(credentials)
          │
          └─ except: (fallback if import fails)
             └─ return MockMT5()  # Safe fallback

Both classes implement:
  ✅ connect()
  ✅ disconnect()
  ✅ get_historical_data(bars)
  ✅ get_current_price()
  ✅ get_account_info()

Downstream code doesn't care which one is used! ✅
```

---

## Database Schema

```
SQLite: trading_system.db

┌─────────────────────────────────────────┐
│            trades                        │
├─────────────────────────────────────────┤
│ id (PK)              INTEGER PRIMARY KEY│
│ pair                 VARCHAR(20)        │
│ signal               VARCHAR(10)        │ BUY / SELL
│ entry_price          FLOAT              │
│ exit_price           FLOAT (nullable)   │
│ stop_loss            FLOAT              │
│ take_profit          FLOAT              │
│ position_size        FLOAT              │
│ status               VARCHAR(20)        │ OPEN / CLOSED
│ profit_loss          FLOAT (nullable)   │
│ profit_loss_pips     FLOAT (nullable)   │
│ profit_loss_percent  FLOAT (nullable)   │
│ entry_time           DATETIME           │
│ exit_time            DATETIME (nullable)│
│ close_reason         VARCHAR(100)       │ SL, TP, Manual
│ confidence           FLOAT              │
│ indicator_signals    TEXT (JSON)        │
│ smc_signals          TEXT (JSON)        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│            signal_logs                   │
├─────────────────────────────────────────┤
│ id (PK)              INTEGER PRIMARY KEY│
│ timestamp            DATETIME (INDEX)   │
│ pair                 VARCHAR(20)        │
│ signal               VARCHAR(10)        │ BUY/SELL/NEUTRAL
│ confidence           FLOAT              │
│ buy_count            INTEGER            │
│ sell_count           INTEGER            │
│ neutral_count        INTEGER            │
│ reason               VARCHAR(500)       │
│ was_executed         BOOLEAN            │
│ indicator_results    TEXT (JSON)        │
│ smc_results          TEXT (JSON)        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│            account_stats                 │
├─────────────────────────────────────────┤
│ id (PK)              INTEGER PRIMARY KEY│
│ date                 DATETIME (UNIQUE)  │
│ starting_balance     FLOAT              │
│ ending_balance       FLOAT              │
│ daily_profit_loss    FLOAT              │
│ daily_profit_loss_% FLOAT              │
│ trades_won           INTEGER            │
│ trades_lost          INTEGER            │
│ total_trades         INTEGER            │
│ win_rate             FLOAT              │
│ max_drawdown         FLOAT              │
│ sharpe_ratio         FLOAT (nullable)   │
└─────────────────────────────────────────┘
```

---

## API Response Cycle

```
Request → Flask → TradingSystem → Components → Database → Response

1. HTTP Request arrives at Flask
   POST /api/analyze

2. Flask routes to app.py handler
   def run_analysis():

3. Calls trading_system.run_analysis()
   TradingSystem.run_analysis()

4. Full trading cycle executes
   - Fetch data
   - Analyze indicators
   - Analyze SMC
   - Aggregate signals
   - Calculate risk
   - Execute trade
   - Log to database

5. Results compiled
   results = {
     "success": True,
     "signal": "BUY",
     "confidence": 0.78,
     ...
   }

6. Flask returns JSON
   jsonify(results)

7. Response sent to client
   200 OK + JSON body

8. Client receives and updates UI
   React updates state
   Components re-render
```

---

## Deployment Topology

```
Development (Linux)
  ├─ MockMT5 (in-memory simulation)
  ├─ SQLite (file-based)
  ├─ Flask debug server
  └─ http://localhost:5000

Testing (Linux/Windows)
  ├─ Real MT5 or MockMT5
  ├─ SQLite or PostgreSQL
  ├─ Flask dev server
  └─ Local network access

Production (Windows)
  ├─ Real MetaTrader5
  ├─ PostgreSQL (remote)
  ├─ Gunicorn + Nginx
  ├─ Authentication + SSL
  ├─ Load balancing
  ├─ Database replication
  └─ https://trading.example.com
```

---

## Performance Targets

```
Full Trading Cycle:
  Data fetch:           1s
  Indicators:           2s
  SMC:                  1s
  Aggregation:          1s
  Risk:                 1s
  Validation:           0.5s
  Execution:            1s
  Database:             1s
  ─────────────────────────
  Total:                ~9s ⚡

API Response:
  Request → Response:   ~50ms (excluding analysis)
  
Throughput:
  Simultaneous clients: 100+
  Requests/sec:         1000+ (with WSGI)
```

---

This is the complete architecture! 🎉

# 🚀 Xephy-AI Trading System

Welcome to the **Xephy-AI Trading System**, a research and paper-trading prototype for analyzing markets with technical indicators, Smart Money Concepts (SMC), optional XGBoost signals, and risk-management rules.

> **Trading status:** This project does not submit orders to a broker. Positions are simulated in memory, even if a real MT5 market-data connection is configured. Do not use it to make live-trading or investment decisions.
>
> **Current scope:** The prototype currently analyzes one configured pair at a time (EURUSD by default). The multi-agent, multi-pair coordinator is a future development stage, not an implemented feature.

![Xephy-AI Dashboard UI](frontend/public/favicon.svg) <!-- Assuming logo or placeholder -->

---

## 📖 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Key Features](#-key-features)
3. [Quick Start Guide](#-quick-start-guide)
4. [Project Structure](#-project-structure)
5. [Documentation Links](#-documentation-links)

---

## 🏗 Architecture Overview

The system is split into two perfectly decoupled components:

1. **Python / Flask Backend (`/backend`)**: The analysis engine can use explicitly enabled synthetic development data or a configured MT5 data connection. It calculates technical indicators, detects SMC patterns, optionally applies an ML model, calculates risk, and simulates positions.
2. **React / Vite Frontend (`/frontend`)**: A dashboard for analysis, simulated positions, signal history, and manual control of the analysis loop.

---

## ✨ Key Features

- **Multi-Strategy Analysis:** Combines traditional indicators (RSI, MACD, EMA, Bollinger, VWAP, ADX, ATR) with institutional Smart Money Concepts (BOS, CHoCH, OBs, FVGs).
- **Configurable Risk Management:** Position sizes use a configured risk percentage and a 1:2 target risk/reward ratio, with ATR-based stop distances.
- **Paper Position Simulation:** In-memory positions are marked to the latest analysis price and simulated closed at their SL/TP levels.
- **Synthetic Development Mode:** Includes a `MockMT5` data generator for UI and integration development only. It is disabled by default, cannot be enabled outside development/test, and must not be used for model training or performance claims. MT5 connectivity does not enable broker order execution.
- **Model Provenance:** Unverified generated model artifacts are not shipped. ML startup requires a sidecar record identifying read-only MT5 data, the configured pair, and matching model/scaler hashes. Training is refused while synthetic market data is enabled. The sidecar is an integrity record, not a cryptographic signature.
- **Database Tracking:** Signal and trade history use SQLAlchemy and Alembic. PostgreSQL is configured in the current local environment; SQLite remains the code default for fresh setups.

> **Database direction:** The FYP proposal specifies MongoDB, and MongoDB is the
> selected target. The current code and local database still use PostgreSQL
> (with SQLite as the fresh-setup default); the MongoDB persistence path and a
> safe history transition are not implemented yet. The PostgreSQL setup below
> is only for running the current implementation. Preserve the existing
> PostgreSQL and SQLite data until a tested migration/retention plan is ready.

---

## ⚡ Quick Start Guide

To get the entire system up and running on your local machine, you will need two separate terminal windows.

### Terminal 1: Start the Backend (Engine)
Make sure you have Python 3.9+ installed.

The commands below apply to the current PostgreSQL-backed implementation; they
do not configure the planned MongoDB target.

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# Apply the versioned database schema (preserves existing matching SQLite tables)
alembic upgrade head

# 4. Start the Flask API and Trading Engine
python app.py
```
*The backend will be running on `http://localhost:5000`*

For a first-time, unprivileged user-local PostgreSQL setup, initialize and start a
dedicated cluster (use a separate port so it does not conflict with a system
PostgreSQL service):

```bash
mkdir -p "$HOME/.local/share/xephy-ai/postgres/socket"
initdb -D "$HOME/.local/share/xephy-ai/postgres/data" \
  --username="$USER" --auth-local=peer --auth-host=scram-sha-256
pg_ctl -D "$HOME/.local/share/xephy-ai/postgres/data" \
  -l "$HOME/.local/share/xephy-ai/postgres/postgres.log" \
  -o "-p 55432 -h 127.0.0.1 -k $HOME/.local/share/xephy-ai/postgres/socket" start
createdb -h "$HOME/.local/share/xephy-ai/postgres/socket" \
  -p 55432 -U "$USER" xephy_ai
```

On later starts, skip `initdb` and `createdb`; start the existing cluster with
the same `pg_ctl ... start` command.

Set `DATABASE_URL` in the untracked `backend/.env` to use the PostgreSQL socket.
URL-encode the absolute socket path (each `/` becomes `%2F`), for example:

```text
postgresql+psycopg://<your-linux-user>@/xephy_ai?host=%2Fhome%2F<your-linux-user>%2F.local%2Fshare%2Fxephy-ai%2Fpostgres%2Fsocket&port=55432
```

Then run `alembic upgrade head` from `backend/`. To copy the selected legacy
SQLite database, first make a backup and then run
`python scripts/migrate_sqlite_to_postgres.py --source ./trading_system.db`.
The transfer preserves primary keys, checks source/destination schemas and row
counts, and refuses to write if any destination history table is non-empty.
It leaves the SQLite file unchanged. Stop the user-local PostgreSQL cluster
when not in use with `pg_ctl -D "$HOME/.local/share/xephy-ai/postgres/data" stop`.

Run the focused backend tests from the `backend` directory:

```bash
python -m unittest discover -s tests
```

### Terminal 2: Start the Frontend (Dashboard)
Make sure you have Node.js 18+ installed.

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install Node dependencies
npm install

# 3. Start the Vite development server
npm run dev
```
*The dashboard will be running on `http://localhost:5173`. Open this URL in your browser.*

### Optional: inspect an MT5 demo account (read-only)

The MT5 adapter is read-only; it does not place, modify, or close broker orders. For a real account snapshot, use a supported Windows machine with the MetaTrader 5 terminal installed and signed into a **broker demo account**, install the optional `MetaTrader5` Python package in the backend environment, and set `MOCK_MT5=false` in an untracked `backend/.env`. When MT5 is selected but unavailable, the backend fails instead of silently substituting mock data. Keep the Flask API private; authentication is not implemented yet.

Synthetic data is opt-in with `MOCK_MT5=true` only when `ENV=development` or
`ENV=test`. It is generated for exercising development flows and is not market
history. Backtests require a caller-supplied OHLCV CSV; results are meaningful
only to the extent that the input data is authentic and the simulation models
relevant trading costs and execution conditions.

The dashboard/API can report account balance/equity, the configured pair's bid/ask, and account-wide realized results and broker costs for the last 30 days. Simulated positions remain paper trades and are separate from broker positions.

---

## 📂 Project Structure

```text
xephy-ai/
├── backend/                  # Python Quantitative Trading Engine
│   ├── app.py                # Flask API Entry Point
│   ├── requirements.txt      # Python Dependencies
│   └── src/trading_system/   # Core Logic (Indicators, SMC, Risk, Exec)
├── frontend/                 # React UI Dashboard
│   ├── src/                  # React Components, Pages, and API Services
│   ├── package.json          # Node Dependencies
│   └── tailwind.config.js    # UI Styling configurations
└── README.md                 # This file
```

---

## 📚 Documentation Links

For deeper dives into how each side of the system works, please refer to the dedicated READMEs:

- 🏗️ **[Platform Architecture & FYP Scope](ARCHITECTURE.md)** - Separates current prototype behavior from the target design, milestones, safety boundaries, and open decisions.
- ⚙️ **[Backend Implementation Details & Architecture](backend/readmes/README_IMPLEMENTATION.md)** - Explains the analysis, paper execution, and risk components.
- 🎨 **[Frontend Dashboard Guide](frontend/README.md)** - Details the UI components, state management polling, and UI deployment.

---
*Built for Precision. Designed for Performance.*

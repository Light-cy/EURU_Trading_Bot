# 🚀 Xephy-AI Trading System

Welcome to the **Xephy-AI Trading System**, a fully automated, quantitative trading bot and dashboard designed to analyze financial markets using Technical Indicators and Smart Money Concepts (SMC), make calculated decisions using Machine Learning (XGBoost), and execute trades safely via robust Risk Management protocols.

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

1. **Python / Flask Backend (`/backend`)**: The core quantitative engine. It connects to brokers (MetaTrader 5), fetches historical and live OHLCV data, calculates 7+ technical indicators, detects SMC patterns (Order Blocks, FVGs, Structure), applies ML models, handles risk/reward sizing, and logs trades to an SQLite database.
2. **React / Vite Frontend (`/frontend`)**: A beautifully crafted, responsive dashboard built with React and TailwindCSS. It polls the backend API to display live open trades, recent signal history, real-time PnL, and allows manual control over the trading engine.

---

## ✨ Key Features

- **Multi-Strategy Analysis:** Combines traditional indicators (RSI, MACD, EMA, Bollinger, VWAP, ADX, ATR) with institutional Smart Money Concepts (BOS, CHoCH, OBs, FVGs).
- **Strict Risk Management:** Hardcoded 1% risk-per-trade rule, utilizing a 1:2 Risk-Reward Ratio (RRR). Trades are automatically sized based on live ATR or fixed Stop Loss pips.
- **Auto-Close Mechanisms:** Live trades are tracked and closed automatically when hitting predefined SL/TP levels, or cleanly liquidated when the engine is manually stopped.
- **Mock Demo Mode:** Includes a fully functional `MockMT5` simulation engine for rapid testing on Linux/Mac, seamlessly hot-swappable to Real `MetaTrader5` on Windows.
- **Database Tracking:** Every signal generated and every trade taken is permanently logged to an SQLite database with detailed PnL calculations for post-trade analysis.

---

## ⚡ Quick Start Guide

To get the entire system up and running on your local machine, you will need two separate terminal windows.

### Terminal 1: Start the Backend (Engine)
Make sure you have Python 3.9+ installed.

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create and activate a virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the Flask API and Trading Engine
python app.py
```
*The backend will be running on `http://localhost:5000`*

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

- ⚙️ **[Backend Implementation Details & Architecture](backend/README_IMPLEMENTATION.md)** - Explains how indicators are calculated, how risk is managed, and how to switch to Live Real-Money trading via MT5.
- 🎨 **[Frontend Dashboard Guide](frontend/README.md)** - Details the UI components, state management polling, and UI deployment.

---
*Built for Precision. Designed for Performance.*

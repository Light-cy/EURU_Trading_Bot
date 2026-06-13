#!/bin/bash

cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python -m src.trading_system.backtesting.run_backtest

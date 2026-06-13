#!/bin/bash

# Ensure we are in the correct directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "============================================================"
echo "🚀 XEPHY-AI: Starting ML Model Training..."
echo "============================================================"

# Run the training script
python -m src.trading_system.ai.train_model

echo "============================================================"
echo "✅ Training Script Execution Finished"
echo "============================================================"

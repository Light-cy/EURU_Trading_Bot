# XGBoost ML Model Integration

> **Status:** Historical and not an evaluation of model quality. The former
> examples used synthetic or unvalidated data and have been removed. Do not
> interpret sample outputs or performance claims below as verified results.
> Current runtime configuration is startup-only, and ML startup fails when the
> model, scaler, or provenance sidecar is missing. The sidecar checks artifact
> integrity but is not cryptographically signed.

## Overview

The XEPHY-AI system now supports **optional XGBoost ML boosting** for signal confidence scoring.

**Two Modes Available:**

1. **NO_ML Mode** (Default) ✅
   - Uses only technical indicators + SMC
   - Model predictions are not used; strategy effectiveness is unvalidated
   - `USE_ML_MODEL=false` in .env

2. **ML Mode** (Optional)
   - Uses XGBoost to boost confidence scores
   - Requires a valid artifact and independent evaluation
   - `USE_ML_MODEL=true` in .env


## How It Works

### Signal Generation Flow

```
NO_ML Mode (Default):
  Indicators (7) + SMC (3) → Consensus Vote (60%) → Signal with Confidence

ML Mode (Optional):
  Indicators (7) + SMC (3) → Consensus Vote (60%) → Signal
                                                         ↓
                                          XGBoost Prediction
                                                         ↓
                                          Confidence Boosted
```

### Example

```
Without ML:
  BUY signal with 0.75 confidence

With ML (if it agrees):
  BUY signal with 0.82 confidence (boosted)

With ML (if it disagrees):
  Keeps indicator signal (doesn't boost)
```


## Setup

### 1. Default: NO_ML Mode

Already enabled. Just run:

```bash
python app.py
```

Response includes:
```json
{
  "signal": "BUY",
  "confidence": 0.78,
  "ml_boosted": false,
  "ml_score": null,
  "ml_mode": "DISABLED (NO_ML)"
}
```


### 2. Enable ML Mode

You need to:

1. **Train the model first** (see Training section below)
2. Update `.env`:
   ```
   USE_ML_MODEL=true
   ```
3. Restart server:
   ```bash
   python app.py
   ```

Response includes:
```json
{
  "signal": "BUY",
  "confidence": 0.85,
  "ml_boosted": true,
  "ml_score": 0.88,
  "ml_mode": "ENABLED"
}
```


## Training the ML Model

The current training command uses the configured real MT5 connection and refuses
to run when `MOCK_MT5=true`:

```bash
python -m src.trading_system.ai.train_model
```

This pipeline does not yet provide out-of-sample validation or establish
predictive value. Do not enable or present a resulting model as effective until
it has been independently evaluated on suitable, non-overlapping historical
data. Generated datasets and model files are local artifacts and are excluded
from version control.


## Features Extracted

The ML model uses these engineered features:

- **Price Movement**: % change, high-low ratio, close-open ratio
- **Volume**: Change ratio, average ratio
- **Momentum**: RSI, momentum, acceleration
- **Trend**: EMA differences, EMA % change
- **Volatility**: Volatility, volatility ratio
- **Support/Resistance**: Distance to highs/lows


## Comparison

| Aspect | NO_ML | ML Mode |
|--------|-------|---------|
| **Speed** | ⚡ Fast | Slower (+100ms) |
| **Accuracy** | Not measured | Not measured |
| **Complexity** | Simple | Complex |
| **Training** | None needed | Requires data |
| **Production** | Not production-ready | Not production-ready |
| **Interpretable** | ✅ Yes | No |


## API Response Format

### Both Modes Return

```json
{
  "success": true,
  "pair": "EURUSD",
  "signal": "BUY",
  "confidence": 0.78,
  "buy_count": 5,
  "sell_count": 1,
  "reason": "Strong buy consensus (71%) + UPTREND",
  
  // NEW: ML Information
  "ml_boosted": false,
  "ml_score": null,
  "ml_mode": "DISABLED (NO_ML)",
  
  "trade_executed": true,
  "open_positions": 1
}
```


## Configuration

`.env` options:

```bash
# Enable/Disable ML
USE_ML_MODEL=true    # Use ML boosting
USE_ML_MODEL=false   # NO_ML mode (default)

# Still compatible with MT5 switching
MOCK_MT5=true        # Linux (demo)
MOCK_MT5=false       # Windows (real MT5)
```


## Performance Impact

### NO_ML Mode (Default)
- Analysis time: ~9 seconds per cycle
- CPU usage: Low
- Memory: ~50MB

### ML Mode (Enabled)
- Analysis time: ~10 seconds per cycle (+1s for prediction)
- CPU usage: Medium
- Memory: ~150MB (with model)


## Troubleshooting

### "Model not trained" warning
```
Problem: Model file not found
Solution: Train the model first (see Training section)
Action: Set USE_ML_MODEL=false to use NO_ML mode
```

### ML disagrees with indicator
```
Example:
  Indicator: BUY (confidence 0.75)
  ML: SELL (confidence 0.80)
  
Result: Keeps indicator signal (doesn't boost)
Reason: Safety - only boost when signals align
```

### Slow performance
```
If ML mode is too slow:
1. Reduce sample size in training
2. Use smaller n_estimators (50 instead of 100)
3. Switch to NO_ML mode
```


## Future Improvements

- [ ] Save/load training statistics
- [ ] Cross-validation metrics
- [ ] Ensemble with multiple models
- [ ] Real-time model retraining
- [ ] Feature importance analysis
- [ ] Hyperparameter optimization


## Summary

✅ **NO_ML Mode** - Default; no model artifact required
- Jadi ke just press start and it works!

✅ **ML Mode** - Optional, needs training, can boost confidence
- Jadi ke you train model first, then enable it

Both work great! Choose based on your needs! 🚀

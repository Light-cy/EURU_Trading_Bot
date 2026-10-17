from flask import Flask, jsonify, request
from flask_cors import CORS
from loguru import logger
import threading
import time
from datetime import datetime
import json

from src.trading_system.main import TradingSystem
from src.trading_system.config.settings import settings

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=settings.CORS_ORIGINS)

# Initialize trading system
trading_system = TradingSystem()

# Background analyzer thread
analysis_thread = None
analysis_running = False
last_analysis_result = None


def run_analysis_loop():
    """Background thread that runs analysis every 15 minutes"""
    global analysis_running, last_analysis_result
    
    logger.info("🔄 Analysis loop started")
    
    while analysis_running:
        try:
            result = trading_system.run_analysis()
            if result.get("success"):
                last_analysis_result = result
            logger.info(f"Analysis complete: {result.get('signal', 'ERROR')}")
            # Sleep in chunks to allow fast interruption
            from src.trading_system.config.settings import settings
            slept = 0
            while slept < settings.LOOP_INTERVAL and analysis_running:
                time.sleep(1)
                slept += 1
        except Exception as e:
            logger.error(f"Analysis loop error: {e}")
            time.sleep(5)


# ======================== API ROUTES ========================

@app.route("/", methods=["GET"])
def hello():
    """Health check"""
    return jsonify({
        "status": "ok",
        "message": "Xephy-AI Trading System",
        "version": "1.0.0"
    })


@app.route("/api/status", methods=["GET"])
def get_status():
    """Get trading system status"""
    return jsonify(trading_system.get_system_status())


@app.route("/api/analyze", methods=["POST"])
def run_analysis():
    """
    Manually trigger analysis cycle
    
    POST /api/analyze
    """
    result = trading_system.run_analysis()
    return jsonify(result)


@app.route("/api/positions", methods=["GET"])
def get_positions():
    """Get all open positions"""
    return jsonify({
        "open_positions": trading_system.get_open_positions(),
        "total_unrealized_pnl": trading_system.executor.get_total_unrealized_pnl(),
        "count": len(trading_system.executor.open_trades)
    })


@app.route("/api/positions/<int:trade_id>", methods=["POST"])
def close_position(trade_id):
    """
    Close a specific position
    
    POST /api/positions/{trade_id}
    Body: {"exit_price": 1.0850}
    """
    data = request.get_json()
    exit_price = data.get("exit_price")

    if not exit_price:
        return jsonify({"error": "exit_price required"}), 400

    result = trading_system.close_position(trade_id, exit_price)
    return jsonify(result)


@app.route("/api/trades/recent", methods=["GET"])
def get_recent_trades():
    """Get recent closed trades"""
    limit = request.args.get("limit", 10, type=int)
    trades = trading_system.executor.get_trade_history(limit)
    return jsonify({"trades": trades, "count": len(trades)})


@app.route("/api/signals/history", methods=["GET"])
def get_signal_history():
    """Get signal history"""
    pair = request.args.get("pair", "EURUSD")
    days = request.args.get("days", 7, type=int)
    
    signals = trading_system.db.get_signal_history(pair, days)
    
    return jsonify({
        "pair": pair,
        "days": days,
        "signals": [
            {
                "timestamp": s.timestamp.isoformat(),
                "signal": s.signal,
                "confidence": s.confidence,
                "buy_count": s.buy_count,
                "sell_count": s.sell_count,
                "neutral_count": s.neutral_count,
                "reason": s.reason,
                "was_executed": s.was_executed,
                "indicator_results": json.loads(s.indicator_results) if s.indicator_results else None,
                "smc_results": json.loads(s.smc_results) if s.smc_results else None
            }
            for s in signals
        ],
        "count": len(signals)
    })


@app.route("/api/account", methods=["GET"])
def get_account_info():
    """Get read-only account details."""
    try:
        account = trading_system.mt5.get_account_info()
    except (RuntimeError, ValueError) as e:
        logger.error(f"Account information unavailable: {e}")
        return jsonify({"error": str(e)}), 503

    return jsonify({
        **account,
        "data_mode": (
            "synthetic_development" if settings.MOCK_MT5 else "mt5_read_only"
        ),
        "execution_mode": trading_system.executor.EXECUTION_MODE,
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/market/quote", methods=["GET"])
def get_market_quote():
    """Get a read-only quote for the configured pair."""
    try:
        market = trading_system.mt5.get_current_price()
    except (RuntimeError, ValueError) as e:
        logger.error(f"Market quote unavailable: {e}")
        return jsonify({"error": str(e)}), 503
    return jsonify(market)


@app.route("/api/account/performance", methods=["GET"])
def get_account_performance():
    """Get realized account-wide trading results and broker charges."""
    days = request.args.get("days", 30, type=int)
    if not hasattr(trading_system.mt5, "get_recent_performance"):
        return jsonify({
            "available": False,
            "reason": "Broker deal history is unavailable in mock mode"
        })

    try:
        performance = trading_system.mt5.get_recent_performance(days=days)
    except (RuntimeError, ValueError) as e:
        logger.error(f"Account performance unavailable: {e}")
        return jsonify({"error": str(e)}), 503

    return jsonify({"available": True, **performance})


@app.route("/api/analysis/start", methods=["POST"])
def start_analysis_loop():
    """Start automatic analysis loop"""
    global analysis_thread, analysis_running
    
    if analysis_running:
        return jsonify({"error": "Analysis loop already running"}), 400
    
    analysis_running = True
    analysis_thread = threading.Thread(target=run_analysis_loop, daemon=True)
    analysis_thread.start()
    
    logger.info("Analysis loop started")
    return jsonify({"status": "started", "message": "Analysis loop is running"})


@app.route("/api/analysis/stop", methods=["POST"])
def stop_analysis():
    """Stop the background analysis loop and close open trades"""
    global analysis_running
    if not analysis_running:
        return jsonify({"success": False, "error": "Analysis not running"})
        
    analysis_running = False
    
    # Auto-close all open trades at their current market price
    open_positions = trading_system.get_open_positions()
    closed_count = 0
    for pos in open_positions:
        trading_system.close_position(pos["trade_id"], pos["current_price"])
        closed_count += 1
        
    return jsonify({
        "success": True, 
        "message": f"Analysis stopped. Auto-closed {closed_count} open trades."
    })


@app.route("/api/analysis/status", methods=["GET"])
def analysis_status():
    """Check if background analysis loop is running"""
    return jsonify({
        "running": analysis_running,
        "thread_alive": analysis_thread.is_alive() if analysis_thread else False
    })


@app.route("/api/analysis/latest", methods=["GET"])
def get_latest_analysis():
    """Return the most recent analysis result from the background loop"""
    if last_analysis_result:
        return jsonify(last_analysis_result)
    else:
        return jsonify({"success": False, "error": "No analysis result available yet"})


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Get current trading settings"""
    from src.trading_system.config.settings import settings
    return jsonify({
        "pair": settings.PAIR,
        "timeframe": settings.TIMEFRAME,
        "risk_percent": settings.RISK_PERCENT,
        "min_confidence": settings.MIN_CONFIDENCE,
        "max_daily_loss": settings.MAX_DAILY_LOSS,
        "max_open_trades": settings.MAX_OPEN_TRADES,
        "market_data_mode": (
            "synthetic_development" if settings.MOCK_MT5 else "mt5_read_only"
        ),
        "ml_model_enabled": settings.USE_ML_MODEL,
        "ml_model_available": (
            trading_system.ml_model is not None
            and trading_system.ml_model.is_trained
        ),
        "loop_interval": settings.LOOP_INTERVAL,
        "environment": settings.ENV
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    """Detailed health check"""
    return jsonify({
        "status": "healthy",
        "system": trading_system.get_system_status(),
        "timestamp": datetime.now().isoformat()
    })


# ======================== ERROR HANDLERS ========================

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {e}")
    return jsonify({"error": "Internal server error"}), 500


# ======================== STARTUP/SHUTDOWN ========================

@app.before_request
def before_request():
    """Check system health before each request"""
    if not trading_system.mt5.connected:
        trading_system.mt5.connect()


@app.teardown_appcontext
def shutdown_session(exception=None):
    """Cleanup on shutdown"""
    pass


if __name__ == "__main__":
    from src.trading_system.config.settings import settings
    
    logger.info("=" * 60)
    logger.info("🚀 Starting Xephy-AI Trading System API Server")
    logger.info("=" * 60)
    
    try:
        app.run(
            host=settings.FLASK_HOST,
            port=settings.FLASK_PORT,
            debug=settings.FLASK_DEBUG,
            use_reloader=False  # Prevent double initialization
        )
    except KeyboardInterrupt:
        logger.info("🛑 Server shutdown requested")
        trading_system.disconnect()
    except Exception as e:
        logger.error(f"Server error: {e}")
        trading_system.disconnect()

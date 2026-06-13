import { useState, useEffect } from 'react';
import { getRecentTrades } from '../services/api';
import { History, TrendingUp, TrendingDown, Clock, ShieldAlert } from 'lucide-react';

const Trades = () => {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchTrades = async () => {
    try {
      const data = await getRecentTrades(50);
      if (data && data.trades) {
        setTrades(data.trades);
      }
    } catch (error) {
      console.error("Failed to fetch trades:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrades();
    const interval = setInterval(fetchTrades, 5000); // refresh every 5s
    return () => clearInterval(interval);
  }, []);

  const formatDate = (dateString) => {
    if (!dateString) return "—";
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent">
            Trades History
          </h1>
          <p className="text-gray-400 mt-1">View your recent closed positions and performance.</p>
        </div>
        <div className="bg-gray-800/50 p-3 rounded-lg border border-border flex items-center gap-3">
          <History className="text-indigo-400" size={24} />
          <div>
            <p className="text-sm text-gray-400">Total Trades</p>
            <p className="text-xl font-bold">{trades.length}</p>
          </div>
        </div>
      </div>

      <div className="bg-card rounded-xl border border-border overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-800/50 border-b border-border">
                <th className="p-4 text-gray-400 font-medium">Trade / Time</th>
                <th className="p-4 text-gray-400 font-medium">Type</th>
                <th className="p-4 text-gray-400 font-medium">Entry / Exit</th>
                <th className="p-4 text-gray-400 font-medium">Duration</th>
                <th className="p-4 text-gray-400 font-medium">Close Reason</th>
                <th className="p-4 text-right text-gray-400 font-medium">Profit/Loss</th>
              </tr>
            </thead>
            <tbody>
              {loading && trades.length === 0 ? (
                <tr>
                  <td colSpan="6" className="p-8 text-center text-gray-400">Loading history...</td>
                </tr>
              ) : trades.length === 0 ? (
                <tr>
                  <td colSpan="6" className="p-8 text-center text-gray-400">No trades history available yet.</td>
                </tr>
              ) : (
                trades.map((trade) => {
                  const isProfit = trade.pnl >= 0;
                  const isBuy = trade.signal === 'BUY';
                  
                  // Calculate duration if exit_time exists
                  let duration = "—";
                  if (trade.entry_time && trade.exit_time) {
                    const diffMs = new Date(trade.exit_time) - new Date(trade.entry_time);
                    const diffMins = Math.floor(diffMs / 60000);
                    const diffSecs = Math.floor((diffMs % 60000) / 1000);
                    duration = `${diffMins}m ${diffSecs}s`;
                  }

                  return (
                    <tr key={trade.trade_id} className="border-b border-border/50 hover:bg-gray-800/30 transition-colors">
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm text-gray-400">#{trade.trade_id}</span>
                          <span className="font-bold">{trade.pair}</span>
                        </div>
                        <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                          <Clock size={12} />
                          {formatDate(trade.entry_time)}
                        </div>
                      </td>
                      <td className="p-4">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          isBuy ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'
                        }`}>
                          {trade.signal}
                        </span>
                        <div className="text-xs text-gray-500 mt-1">
                          Lot: {trade.position_size}
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="font-mono text-sm">{trade.entry_price?.toFixed(5)}</div>
                        <div className="font-mono text-sm text-gray-400">→ {trade.exit_price?.toFixed(5)}</div>
                      </td>
                      <td className="p-4 text-sm text-gray-400">
                        {duration}
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-1 text-sm">
                          {trade.reason === "Take Profit" && <TrendingUp size={14} className="text-success" />}
                          {trade.reason === "Stop Loss" && <TrendingDown size={14} className="text-danger" />}
                          {trade.reason === "Manual" && <ShieldAlert size={14} className="text-warning" />}
                          <span className={
                            trade.reason === "Take Profit" ? "text-success" :
                            trade.reason === "Stop Loss" ? "text-danger" : "text-warning"
                          }>
                            {trade.reason || trade.close_reason || "System"}
                          </span>
                        </div>
                      </td>
                      <td className="p-4 text-right">
                        <div className={`text-lg font-bold ${isProfit ? 'text-success' : 'text-danger'}`}>
                          {isProfit ? '+' : ''}${trade.pnl?.toFixed(2) || trade.profit_loss?.toFixed(2) || "0.00"}
                        </div>
                        <div className={`text-xs ${isProfit ? 'text-success/70' : 'text-danger/70'}`}>
                          {isProfit ? '+' : ''}{trade.pnl_pips?.toFixed(1) || trade.profit_loss_pips?.toFixed(1) || "0.0"} pips
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default Trades;

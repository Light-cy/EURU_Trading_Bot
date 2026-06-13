import { useState, useEffect } from 'react';
import { Power, Activity, TrendingUp, DollarSign, BrainCircuit, Play, Square, Settings, Zap, Database } from 'lucide-react';
import { getStatus, getAnalyze, getAnalysisStatus, startAnalysis, stopAnalysis, getSignalsHistory, getPositions, getSettings, updateSettings, getLatestAnalysis } from '../services/api';

const Card = ({ children, className = "" }) => (
  <div className={`bg-card rounded-xl border border-border p-6 shadow-sm ${className}`}>
    {children}
  </div>
);

const StatCard = ({ title, value, subtitle, icon: Icon, colorClass = "text-primary", bgClass = "bg-primary/10" }) => (
  <Card className="flex items-center space-x-4">
    <div className={`p-4 rounded-lg ${bgClass}`}>
      <Icon size={24} className={colorClass} />
    </div>
    <div>
      <p className="text-gray-400 text-sm font-medium">{title}</p>
      <h3 className="text-2xl font-bold mt-1">{value}</h3>
      {subtitle && <p className="text-sm mt-1 text-gray-500">{subtitle}</p>}
    </div>
  </Card>
);

const Badge = ({ children, color = "gray" }) => {
  const colors = {
    green: "bg-success/20 text-success border-success/30",
    red: "bg-danger/20 text-danger border-danger/30",
    blue: "bg-primary/20 text-primary border-primary/30",
    gray: "bg-gray-800 text-gray-300 border-gray-700"
  };
  return (
    <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border uppercase tracking-wider ${colors[color] || colors.gray}`}>
      {children}
    </span>
  );
};

const Toggle = ({ label, enabled, onChange, icon: Icon }) => (
  <div className="flex items-center justify-between p-3 bg-gray-900 rounded-lg border border-border">
    <div className="flex items-center space-x-3">
      <div className={`p-2 rounded-md ${enabled ? 'bg-primary/20 text-primary' : 'bg-gray-800 text-gray-400'}`}>
        <Icon size={16} />
      </div>
      <span className="font-medium text-sm">{label}</span>
    </div>
    <button 
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${enabled ? 'bg-primary' : 'bg-gray-700'}`}
    >
      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${enabled ? 'translate-x-6' : 'translate-x-1'}`} />
    </button>
  </div>
);

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [sysStatus, setSysStatus] = useState({ running: false });
  const [account, setAccount] = useState({ balance: 10000, equity: 10000 });
  const [trades, setTrades] = useState({ count: 0, open_positions: [] });
  const [signals, setSignals] = useState([]);
  const [currentSignal, setCurrentSignal] = useState(null);
  const [sysSettings, setSysSettings] = useState({
    use_ml_model: false,
    mock_mt5: true,
    loop_interval: 900
  });

  const fetchData = async () => {
    try {
      const accRes = await getStatus().catch(() => ({ account_balance: 10000 }));
      setAccount({ balance: accRes.account_balance, equity: accRes.account_balance + (accRes.total_unrealized_pnl || 0) });
      
      const statRes = await getAnalysisStatus().catch(() => ({ running: false }));
      setSysStatus(statRes);

      const tradesRes = await getPositions().catch(() => ({ count: 0, open_positions: [] }));
      setTrades(tradesRes);

      const sigRes = await getSignalsHistory('EURUSD', 7).catch(() => ({ signals: [] }));
      setSignals(sigRes.signals || []);
      
      const latestRes = await getLatestAnalysis().catch(() => null);
      if (latestRes && latestRes.success) {
        setCurrentSignal(latestRes);
      } else if (sigRes.signals && sigRes.signals.length > 0) {
        setCurrentSignal(sigRes.signals[0]);
      } else {
        const anRes = await getAnalyze().catch(() => null);
        if (anRes) setCurrentSignal(anRes);
      }
      
      const setRes = await getSettings().catch(() => null);
      if (setRes) setSysSettings(setRes);

    } catch (e) {
      console.error("Error fetching dashboard data", e);
    } finally {
      if (loading) setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000); // 2 second polling for live UI
    return () => clearInterval(interval);
  }, []);

  const toggleEngine = async () => {
    try {
      if (sysStatus.running) {
        await stopAnalysis();
      } else {
        await startAnalysis();
      }
      fetchData();
    } catch (e) {
      console.error("Toggle error", e);
    }
  };

  const handleSettingChange = async (key, value) => {
    try {
      const updated = { ...sysSettings, [key]: value };
      setSysSettings(updated);
      await updateSettings({ [key]: value });
    } catch (e) {
      console.error("Failed to update setting", e);
    }
  };

  if (loading) return <div className="flex h-full items-center justify-center"><Activity className="animate-spin text-primary" size={40} /></div>;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-gray-400 mt-1">Xephy-AI Trading Control Center</p>
        </div>
        
        <Card className="flex items-center space-x-4 p-4 py-3 border-primary/30 bg-primary/5">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full animate-pulse ${sysStatus.running ? 'bg-success' : 'bg-danger'}`}></div>
            <span className="font-semibold">{sysStatus.running ? 'ENGINE ACTIVE' : 'ENGINE STOPPED'}</span>
          </div>
          <button 
            onClick={toggleEngine}
            className={`flex items-center space-x-2 px-6 py-2 rounded-lg font-bold transition-colors ${
              sysStatus.running 
                ? 'bg-danger/20 text-danger hover:bg-danger/30 border border-danger/30' 
                : 'bg-success/20 text-success hover:bg-success/30 border border-success/30'
            }`}
          >
            {sysStatus.running ? <Square size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
            <span>{sysStatus.running ? 'STOP TRADING' : 'START TRADING'}</span>
          </button>
        </Card>
      </div>

      {/* Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Account Balance" 
          value={`$${account.balance.toLocaleString(undefined, {minimumFractionDigits: 2})}`}
          icon={DollarSign} 
        />
        <StatCard 
          title="Equity" 
          value={`$${account.equity.toLocaleString(undefined, {minimumFractionDigits: 2})}`}
          icon={TrendingUp} 
          colorClass="text-success" 
          bgClass="bg-success/10" 
        />
        <StatCard 
          title="Open Trades" 
          value={trades.count} 
          icon={Activity} 
          colorClass="text-blue-400" 
          bgClass="bg-blue-400/10" 
        />
        <StatCard 
          title="ML Engine Status" 
          value={sysSettings.use_ml_model ? "ENABLED" : "DISABLED"} 
          subtitle={sysSettings.use_ml_model ? "XGBoost Active" : "Indicators Only"}
          icon={BrainCircuit} 
          colorClass={sysSettings.use_ml_model ? "text-purple-400" : "text-gray-500"} 
          bgClass={sysSettings.use_ml_model ? "bg-purple-400/10" : "bg-gray-800"} 
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Left Column: Hero & Trades */}
        <div className="lg:col-span-2 space-y-6">
          
          {/* Hero Section: Market Overview */}
          <Card className="border-primary/50 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none"></div>
            
            <h2 className="text-xl font-bold mb-6 flex items-center"><BrainCircuit className="mr-2 text-primary" /> AI Market Overview</h2>
            
            {currentSignal ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <div className="flex items-center space-x-3 mb-4">
                    <span className="text-3xl font-black">{currentSignal.pair || "EURUSD"}</span>
                    <Badge color={currentSignal.signal === "BUY" ? "green" : currentSignal.signal === "SELL" ? "red" : "gray"}>
                      {currentSignal.signal || "NEUTRAL"}
                    </Badge>
                  </div>
                  
                  <div className="mb-6">
                    <div className="flex justify-between text-sm mb-2">
                      <span className="text-gray-400">AI Confidence</span>
                      <span className="font-bold">{(currentSignal.confidence * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-gray-800 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${currentSignal.signal === "BUY" ? "bg-success" : currentSignal.signal === "SELL" ? "bg-danger" : "bg-primary"}`} 
                        style={{ width: `${(currentSignal.confidence * 100)}%` }}
                      ></div>
                    </div>
                  </div>
                  
                  <div className="p-4 bg-gray-900 rounded-lg border border-gray-800">
                    <span className="text-gray-400 text-sm block mb-1">Reasoning</span>
                    <p className="text-sm font-medium leading-relaxed">{currentSignal.reason || "Waiting for analysis..."}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-900/50 p-4 rounded-lg border border-border">
                    <p className="text-gray-400 text-sm mb-1">Entry Price</p>
                    <p className="text-xl font-mono">{currentSignal.risk_params?.entry || currentSignal.current_price || "—"}</p>
                  </div>
                  <div className="bg-gray-900/50 p-4 rounded-lg border border-border">
                    <p className="text-gray-400 text-sm mb-1">Lot Size</p>
                    <p className="text-xl font-mono">{currentSignal.risk_params?.position_size || "—"}</p>
                  </div>
                  <div className="bg-danger/10 p-4 rounded-lg border border-danger/20">
                    <p className="text-danger/80 text-sm mb-1">Stop Loss</p>
                    <p className="text-xl font-mono text-danger">{currentSignal.risk_params?.stop_loss || "—"}</p>
                  </div>
                  <div className="bg-success/10 p-4 rounded-lg border border-success/20">
                    <p className="text-success/80 text-sm mb-1">Take Profit</p>
                    <p className="text-xl font-mono text-success">{currentSignal.risk_params?.take_profit || "—"}</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">No market data available.</p>
            )}
          </Card>

          {/* Open Trades */}
          <Card>
            <h2 className="text-xl font-bold mb-6">Live Open Trades</h2>
            {trades.open_positions.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {trades.open_positions.map((trade, i) => (
                  <div key={i} className="bg-gray-900 border border-border rounded-lg p-4 flex justify-between items-center relative overflow-hidden">
                    <div className={`absolute left-0 top-0 bottom-0 w-1 ${trade.signal === 'BUY' ? 'bg-success' : 'bg-danger'}`}></div>
                    <div className="pl-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold">{trade.pair || "EURUSD"}</span>
                        <span className={`text-xs font-bold ${trade.signal === 'BUY' ? 'text-success' : 'text-danger'}`}>{trade.signal}</span>
                      </div>
                      <p className="text-sm text-gray-400 mt-1">Lot: {trade.position_size} | Entry: {trade.entry_price}</p>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold text-lg ${trade.unrealized_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                        {trade.unrealized_pnl >= 0 ? '+' : ''}${trade.unrealized_pnl?.toFixed(2) || "0.00"}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 bg-gray-900/50 rounded-lg border border-dashed border-gray-800">
                <p>No open trades at the moment.</p>
              </div>
            )}
          </Card>
          
        </div>

        {/* Right Column: Settings & Timeline */}
        <div className="space-y-6">
          
          {/* Live Settings Panel */}
          <Card className="border-border">
            <h2 className="text-xl font-bold mb-4 flex items-center"><Settings className="mr-2 text-gray-400" size={20} /> Demo Controls</h2>
            <div className="space-y-3">
              <Toggle 
                icon={BrainCircuit} 
                label="ML Engine (XGBoost)" 
                enabled={sysSettings.use_ml_model} 
                onChange={(v) => handleSettingChange('use_ml_model', v)} 
              />
              <Toggle 
                icon={Database} 
                label="Mock Data Feed" 
                enabled={sysSettings.mock_mt5} 
                onChange={(v) => handleSettingChange('mock_mt5', v)} 
              />
              <Toggle 
                icon={Zap} 
                label="Live Demo Speed (5s)" 
                enabled={sysSettings.loop_interval === 5} 
                onChange={(v) => handleSettingChange('loop_interval', v ? 5 : 900)} 
              />
            </div>
            {sysSettings.loop_interval === 5 && (
              <div className="mt-4 p-3 bg-primary/10 border border-primary/20 rounded-lg text-sm text-primary">
                ⚡ Demo mode is ON. The system is placing trades every 5 seconds.
              </div>
            )}
          </Card>

          {/* AI Decisions Timeline */}
          <Card className="h-full">
            <h2 className="text-xl font-bold mb-6">Recent AI Decisions</h2>
            <div className="space-y-6">
              {signals.length > 0 ? signals.slice(0, 5).map((sig, i) => (
                <div key={i} className="relative pl-6 border-l-2 border-gray-800 pb-2">
                  <div className={`absolute -left-[9px] top-0 w-4 h-4 rounded-full border-4 border-card ${
                    sig.signal === 'BUY' ? 'bg-success' : sig.signal === 'SELL' ? 'bg-danger' : 'bg-gray-500'
                  }`}></div>
                  
                  <div className="flex justify-between items-start mb-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold">{sig.pair || "EURUSD"}</span>
                      <span className={`text-xs font-bold ${
                        sig.signal === 'BUY' ? 'text-success' : sig.signal === 'SELL' ? 'text-danger' : 'text-gray-400'
                      }`}>{sig.signal}</span>
                    </div>
                    <span className="text-xs text-gray-500">{(sig.confidence * 100).toFixed(0)}%</span>
                  </div>
                  
                  <p className="text-sm text-gray-400 mt-2">{sig.reason}</p>
                </div>
              )) : (
                <p className="text-gray-500 text-sm">No recent signals found.</p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

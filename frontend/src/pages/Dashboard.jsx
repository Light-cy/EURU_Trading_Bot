import { useState, useEffect } from 'react';
import { Activity, TrendingUp, DollarSign, BrainCircuit, Play, Square, Settings, Zap, Database, BarChart2, Layers, Cpu } from 'lucide-react';
import { getStatus, getAnalyze, getAnalysisStatus, startAnalysis, stopAnalysis, getSignalsHistory, getPositions, getSettings, updateSettings, getLatestAnalysis } from '../services/api';

const Card = ({ children, className = "" }) => (
  <div className={`bg-slate-800/80 rounded-xl border border-slate-700/50 p-6 shadow-sm ${className}`}>
    {children}
  </div>
);

const StatCard = ({ title, value, subtitle, icon: Icon, colorClass = "text-primary", bgClass = "bg-primary/10" }) => (
  <Card className="flex items-center space-x-4">
    <div className={`p-2 rounded-lg ${bgClass}`}>
      <Icon size={16} className={colorClass} />
    </div>
    <div>
      <p className="text-slate-400 text-sm font-medium">{title}</p>
      <h3 className="text-2xl font-bold text-slate-50 mt-1">{value}</h3>
      {subtitle && <p className="text-sm mt-1 text-slate-500">{subtitle}</p>}
    </div>
  </Card>
);

const Badge = ({ children, color = "gray" }) => {
  const colors = {
    green: "bg-green-500/20 text-green-400 border-green-500/30",
    red: "bg-red-500/20 text-red-400 border-red-500/30",
    blue: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    gray: "bg-slate-800 text-slate-300 border-slate-700"
  };
  return (
    <span className={`px-2.5 py-1 rounded-md text-xs font-semibold border uppercase tracking-wider ${colors[color] || colors.gray}`}>
      {children}
    </span>
  );
};

const Toggle = ({ label, enabled, onChange, icon: Icon }) => (
  <div className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
    <div className="flex items-center space-x-3">
      <div className={`p-2 rounded-md ${enabled ? 'bg-primary/20 text-primary' : 'bg-slate-800 text-slate-400'}`}>
        <Icon size={16} />
      </div>
      <span className="font-medium text-sm text-slate-200">{label}</span>
    </div>
    <button
      onClick={() => onChange(!enabled)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${enabled ? 'bg-primary' : 'bg-slate-700'}`}
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
    const interval = setInterval(fetchData, 2000);
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

  // Derive Data for New Cards
  const indicators = currentSignal?.indicator_results || {
    EMA: { confidence: 0.82 },
    MACD: { confidence: 0.75 },
    RSI: { confidence: 0.61 },
    ADX: { confidence: 0.89 },
    ATR: { confidence: 0.72 }
  };

  const smc = currentSignal?.smc_results || {};
  const bos = smc.structure?.bos || "None";
  const trend = smc.structure?.trend || "Ranging";
  const obArray = smc.order_blocks || [];
  const ob = obArray.length > 0 ? obArray[0].type : "None";
  const fvgArray = smc.fvg || [];
  const fvg = fvgArray.length > 0 ? "PRESENT" : "NONE";
  const choc = smc.structure?.choc || false; // Mocking Liquidity Grab from CHoCH

  const finalConf = currentSignal ? Math.round(currentSignal.confidence * 100) : 84;
  const indVals = Object.values(indicators).map(i => i.confidence);
  const indConf = indVals.length > 0 ? Math.round((indVals.reduce((a, b) => a + b, 0) / indVals.length) * 100) : 78;
  const smcConf = finalConf > 0 ? Math.min(100, Math.max(0, Math.round((finalConf * 2) - indConf))) : 91;

  // Format reasoning string into bullet points
  const reasonText = currentSignal?.reason || "Waiting for analysis...";
  const reasonBullets = reasonText.split(/,|\n| and /).map(r => r.trim()).filter(r => r.length > 0);

  return (
    <div className="space-y-6 max-w-7xl mx-auto text-slate-50">

      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold">Dashboard</h1>
          <p className="text-slate-400 mt-1">Xephy-AI Trading Control Center</p>
        </div>

        <Card className="flex items-center space-x-4 p-4 py-3 border-primary/30 bg-primary/5">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full animate-pulse ${sysStatus.running ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="font-semibold">{sysStatus.running ? 'ENGINE ACTIVE' : 'ENGINE STOPPED'}</span>
          </div>
          <button
            onClick={toggleEngine}
            className={`flex items-center space-x-2 px-6 py-2 rounded-lg font-bold transition-colors ${sysStatus.running
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30 border border-red-500/30'
              : 'bg-green-500/20 text-green-400 hover:bg-green-500/30 border border-green-500/30'
              }`}
          >
            {sysStatus.running ? <Square size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" />}
            <span>{sysStatus.running ? 'STOP TRADING' : 'START TRADING'}</span>
          </button>
        </Card>
      </div>

      {/* 6. Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-2">
        <StatCard
          title="Account Balance"
          value={`$${account.balance.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          icon={DollarSign}
        />
        <StatCard
          title="Equity"
          value={`$${account.equity.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
          icon={TrendingUp}
          colorClass="text-green-400"
          bgClass="bg-green-500/10"
        />
        <StatCard
          title="Open Trades"
          value={trades.count}
          icon={Activity}
          colorClass="text-blue-400"
          bgClass="bg-blue-500/10"
        />
        <StatCard
          title="Market Status"
          value="ACTIVE"
          subtitle="EURUSD M15"
          icon={Database}
          colorClass="text-purple-400"
          bgClass="bg-purple-500/10"
        />
      </div>

      {/* NEW: 3 Column Analytics Grid (Temporarily 2 columns without SMC) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

        {/* 1. Indicator Confidence Breakdown */}
        <Card>
          <h2 className="text-lg font-bold mb-5 flex items-center"><BarChart2 className="mr-2 text-blue-400" size={20} /> Indicator Confidence</h2>
          <div className="space-y-4">
            {Object.entries(indicators).slice(0, 5).map(([name, data]) => {
              const val = Math.round(data.confidence * 100);
              return (
                <div key={name}>
                  <div className="flex justify-between text-sm mb-1.5 items-center">
                    <div className="flex items-center space-x-2">
                      <span className="font-semibold text-slate-300">{name}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${data.signal === 'BUY' ? 'bg-green-500/20 text-green-400' :
                          data.signal === 'SELL' ? 'bg-red-500/20 text-red-400' :
                            'bg-slate-700 text-slate-300'
                        }`}>
                        {data.signal || 'NEUTRAL'}
                      </span>
                    </div>
                    <span className="text-slate-400 font-mono">{val}%</span>
                  </div>
                  <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className={`h-full rounded-full transition-all duration-1000 ease-out ${data.signal === 'BUY' ? 'bg-green-500' :
                          data.signal === 'SELL' ? 'bg-red-500' :
                            'bg-slate-500'
                        }`}
                      style={{ width: `${val}%` }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>

        {/* 2. SMC Analysis Card (Temporarily deactivated) */}
        {/*
        <Card>
          <h2 className="text-lg font-bold mb-5 flex items-center"><Layers className="mr-2 text-purple-400" size={20} /> SMC Analysis</h2>
          <div className="space-y-4 pt-1">
            <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-700/30">
              <span className="text-slate-300 font-medium">BOS</span>
              <Badge color={bos !== "None" ? "green" : "gray"}>{bos !== "None" ? "YES" : "NO"}</Badge>
            </div>
            <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-700/30">
              <span className="text-slate-300 font-medium">Order Block</span>
              <Badge color={ob === "Bullish" ? "green" : ob === "Bearish" ? "red" : "gray"}>{ob.toUpperCase()}</Badge>
            </div>
            <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-700/30">
              <span className="text-slate-300 font-medium">Liquidity Grab</span>
              <Badge color={choc ? "green" : "gray"}>{choc ? "YES" : "NO"}</Badge>
            </div>
            <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-700/30">
              <span className="text-slate-300 font-medium">FVG</span>
              <Badge color={fvg === "PRESENT" ? "blue" : "gray"}>{fvg}</Badge>
            </div>
          </div>
        </Card>
        */}

        {/* 3. AI Confidence Card */}
        <Card>
          <h2 className="text-lg font-bold mb-2 flex items-center"><Cpu className="mr-2 text-green-400" size={20} /> AI Confidence</h2>
          <div className="flex flex-col items-center justify-center mb-6 mt-4">
            <div className="relative w-32 h-32 flex items-center justify-center">
              <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 128 128">
                <circle cx="64" cy="64" r="54" fill="none" stroke="currentColor" strokeWidth="10" className="text-slate-800" />
                <circle
                  cx="64" cy="64" r="54"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="10"
                  className={finalConf > 60 ? "text-green-500" : finalConf < 40 ? "text-red-500" : "text-blue-500"}
                  strokeDasharray="339.29"
                  strokeDashoffset={339.29 - (339.29 * finalConf) / 100}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
                />
              </svg>
              <div className="text-center z-10">
                <span className="text-3xl font-black">{finalConf}%</span>
                <span className="text-[10px] text-slate-400 block uppercase tracking-widest mt-1">Final</span>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm bg-slate-900/80 p-3 rounded-lg border border-slate-700/50">
              <span className="text-slate-400">Indicators Score</span>
              <span className="font-bold text-blue-400 text-base">{indConf}%</span>
            </div>

            <div className="flex justify-between items-center text-sm bg-slate-900/80 p-3 rounded-lg border border-slate-700/50">
              <span className="text-slate-400">SMC Score</span>
              <span className="font-bold text-purple-400 text-base">{smcConf}%</span>
            </div>

          </div>
        </Card>

      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Left Column */}
        <div className="lg:col-span-2 space-y-6">

          {/* 4. Improve AI Market Overview */}
          <Card className="border-primary/50 relative overflow-hidden bg-slate-800">
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full blur-3xl -mr-20 -mt-20 pointer-events-none"></div>

            <h2 className="text-xl font-bold mb-6 flex items-center"><BrainCircuit className="mr-2 text-primary" /> AI Market Overview</h2>

            {currentSignal ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Left Side: Summary & Reasoning */}
                <div className="flex flex-col h-full justify-between">
                  <div>
                    <div className="flex items-center justify-between mb-4 bg-slate-900/60 p-4 rounded-xl border border-slate-700/50">
                      <div>
                        <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Signal</p>
                        <Badge color={currentSignal.signal === "BUY" ? "green" : currentSignal.signal === "SELL" ? "red" : "gray"}>
                          {currentSignal.signal || "NEUTRAL"}
                        </Badge>
                      </div>
                      <div className="text-right">
                        <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Trend</p>
                        <span className="font-bold text-slate-200">{trend}</span>
                      </div>
                      <div className="text-right">
                        <p className="text-slate-400 text-xs uppercase tracking-wider mb-1">Confidence</p>
                        <span className="font-bold text-slate-200 text-lg">{finalConf}%</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-5 bg-slate-900/50 rounded-xl border border-slate-700/50 mt-4 flex-grow">
                    <span className="text-slate-400 text-sm font-bold uppercase tracking-wider block mb-3 border-b border-slate-800 pb-2">Reasoning</span>
                    <ul className="space-y-2">
                      {reasonBullets.map((bullet, idx) => (
                        <li key={idx} className="flex items-start text-sm text-slate-300">
                          <span className="text-primary mr-2 mt-0.5">•</span>
                          {bullet}
                        </li>
                      ))}
                      {reasonBullets.length === 0 && <li className="text-slate-500">Awaiting market conditions...</li>}
                    </ul>
                  </div>
                </div>

                {/* Right Side: Risk Params Grid */}
                <div className="grid grid-cols-2 gap-4 h-full">
                  <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-700/50 flex flex-col justify-center">
                    <p className="text-slate-400 text-xs uppercase tracking-wider mb-2">Entry Price</p>
                    <p className="text-2xl font-mono text-slate-100">{currentSignal.risk_params?.entry || currentSignal.current_price || "—"}</p>
                  </div>
                  <div className="bg-slate-900/80 p-5 rounded-xl border border-slate-700/50 flex flex-col justify-center">
                    <p className="text-slate-400 text-xs uppercase tracking-wider mb-2">Lot Size</p>
                    <p className="text-2xl font-mono text-slate-100">{currentSignal.risk_params?.position_size || "—"}</p>
                  </div>
                  <div className="bg-red-950/20 p-5 rounded-xl border border-red-500/20 flex flex-col justify-center">
                    <p className="text-red-400/80 text-xs uppercase tracking-wider mb-2">Stop Loss</p>
                    <p className="text-2xl font-mono text-red-400">{currentSignal.risk_params?.stop_loss || "—"}</p>
                  </div>
                  <div className="bg-green-950/20 p-5 rounded-xl border border-green-500/20 flex flex-col justify-center">
                    <p className="text-green-400/80 text-xs uppercase tracking-wider mb-2">Take Profit</p>
                    <p className="text-2xl font-mono text-green-400">{currentSignal.risk_params?.take_profit || "—"}</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-slate-500">No market data available.</p>
            )}
          </Card>

          {/* Open Trades (Kept as requested) */}
          <Card>
            <h2 className="text-xl font-bold mb-6">Live Open Trades</h2>
            {trades.open_positions.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {trades.open_positions.map((trade, i) => (
                  <div key={i} className="bg-slate-900 border border-slate-700/50 rounded-lg p-4 flex justify-between items-center relative overflow-hidden">
                    <div className={`absolute left-0 top-0 bottom-0 w-1 ${trade.signal === 'BUY' ? 'bg-green-500' : 'bg-red-500'}`}></div>
                    <div className="pl-2">
                      <div className="flex items-center space-x-2">
                        <span className="font-bold">{trade.pair || "EURUSD"}</span>
                        <span className={`text-xs font-bold ${trade.signal === 'BUY' ? 'text-green-400' : 'text-red-400'}`}>{trade.signal}</span>
                      </div>
                      <p className="text-sm text-slate-400 mt-1">Lot: {trade.position_size} | Entry: {trade.entry_price}</p>
                    </div>
                    <div className="text-right">
                      <p className={`font-bold text-lg ${trade.unrealized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {trade.unrealized_pnl >= 0 ? '+' : ''}${trade.unrealized_pnl?.toFixed(2) || "0.00"}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-slate-500 bg-slate-900/30 rounded-lg border border-dashed border-slate-700/50">
                <p>No open trades at the moment.</p>
              </div>
            )}
          </Card>

        </div>

        {/* Right Column */}
        <div className="space-y-6">

          {/* Live Settings Panel */}
          <Card className="border-border">
            <h2 className="text-xl font-bold mb-4 flex items-center"><Settings className="mr-2 text-slate-400" size={20} /> Demo Controls</h2>
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

          {/* 5. Add Recent AI Decisions Timeline */}
          <Card className="h-full">
            <h2 className="text-xl font-bold mb-6">Recent AI Decisions</h2>
            <div className="space-y-5">
              {signals.length > 0 ? signals.slice(0, 6).map((sig, i) => {
                const date = new Date(sig.timestamp || Date.now());
                const timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

                return (
                  <div key={i} className="relative pl-6 border-l-2 border-slate-700 pb-1">
                    <div className={`absolute -left-[9px] top-1 w-4 h-4 rounded-full border-4 border-slate-800 ${sig.signal === 'BUY' ? 'bg-green-500' : sig.signal === 'SELL' ? 'bg-red-500' : 'bg-slate-500'
                      }`}></div>

                    <div className="flex justify-between items-center bg-slate-900/40 p-2 rounded-md border border-slate-700/30">
                      <span className="font-mono text-slate-400 text-sm">{timeStr}</span>
                      <span className={`text-sm font-bold tracking-wider ${sig.signal === 'BUY' ? 'text-green-400' : sig.signal === 'SELL' ? 'text-red-400' : 'text-slate-400'
                        }`}>{sig.signal}</span>
                    </div>
                  </div>
                )
              }) : (
                <p className="text-slate-500 text-sm">No recent signals found.</p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

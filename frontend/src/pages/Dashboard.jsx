import { useState, useEffect } from 'react';
import { Activity, TrendingUp, DollarSign, BrainCircuit, Play, Square, Settings, Database, BarChart2, Layers, Cpu } from 'lucide-react';
import { getAccountInfo, getAccountPerformance, getMarketQuote, getAnalyze, getAnalysisStatus, startAnalysis, stopAnalysis, getSignalsHistory, getPositions, getSettings, getLatestAnalysis } from '../services/api';

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

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [sysStatus, setSysStatus] = useState({ running: false });
  const [account, setAccount] = useState({ balance: null, equity: null });
  const [accountSnapshot, setAccountSnapshot] = useState(null);
  const [accountPerformance, setAccountPerformance] = useState(null);
  const [trades, setTrades] = useState({ count: 0, open_positions: [] });
  const [signals, setSignals] = useState([]);
  const [currentSignal, setCurrentSignal] = useState(null);
  const [sysSettings, setSysSettings] = useState({
    ml_model_enabled: false,
    ml_model_available: false,
    market_data_mode: null,
  });

  const fetchData = async () => {
    try {
      const accountInfo = await getAccountInfo().catch(() => null);
      const marketQuote = await getMarketQuote().catch(() => null);
      setAccountSnapshot(accountInfo ? { ...accountInfo, market: marketQuote } : null);
      setAccount({
        balance: accountInfo?.balance ?? null,
        equity: accountInfo?.equity ?? null
      });
      const performance = await getAccountPerformance().catch(() => null);
      setAccountPerformance(performance?.available ? performance : null);

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

  if (loading) return <div className="flex h-full items-center justify-center"><Activity className="animate-spin text-primary" size={40} /></div>;

  const indicators = currentSignal?.indicator_results || {};

  const smc = currentSignal?.smc_results || {};
  const bos = smc.structure?.bos || "Unavailable";
  const trend = smc.structure?.trend || "Unavailable";
  const ob = smc.order_block?.ob?.type || "Unavailable";
  const fvg = smc.fvg?.signal || "Unavailable";
  const choch = smc.structure?.choch || "Unavailable";

  const finalConf = Number.isFinite(currentSignal?.confidence)
    ? Math.round(currentSignal.confidence * 100)
    : null;
  const indVals = Object.values(indicators)
    .map(indicator => indicator.confidence)
    .filter(Number.isFinite);
  const indConf = indVals.length > 0
    ? Math.round((indVals.reduce((total, value) => total + value, 0) / indVals.length) * 100)
    : null;
  const structureConfidence = Number.isFinite(smc.structure?.confidence)
    ? Math.round(smc.structure.confidence * 100)
    : null;
  const isSyntheticData = accountSnapshot?.data_mode === "synthetic_development";

  // Format reasoning string into bullet points
  const reasonText = currentSignal?.reason || "Waiting for analysis...";
  const reasonBullets = reasonText.split(/,|\n| and /).map(r => r.trim()).filter(r => r.length > 0);
  const accountCurrency = accountSnapshot?.currency || "USD";
  const formatAmount = value => value == null
    ? "Unavailable"
    : `${accountCurrency} ${Number(value).toFixed(2)}`;
  const market = accountSnapshot?.market;
  const brokerCosts = accountPerformance
    ? -(accountPerformance.commission + accountPerformance.swap + accountPerformance.fees)
    : null;

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
            <span>{sysStatus.running ? 'STOP PAPER ENGINE' : 'START PAPER ENGINE'}</span>
          </button>
        </Card>
      </div>

      {/* 6. Top Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-2">
        <StatCard
          title={isSyntheticData ? "Simulated Balance" : "Account Balance"}
          value={formatAmount(account.balance)}
          subtitle={isSyntheticData
            ? "Synthetic development value; not a broker account"
            : accountSnapshot?.server || "Account connection unavailable"}
          icon={DollarSign}
        />
        <StatCard
          title={isSyntheticData ? "Simulated Equity" : "Equity"}
          value={formatAmount(account.equity)}
          subtitle={isSyntheticData ? "Synthetic development value" : undefined}
          icon={TrendingUp}
          colorClass="text-green-400"
          bgClass="bg-green-500/10"
        />
        <StatCard
          title={`${market?.pair || sysSettings.pair || "Market"} Bid / Ask`}
          value={market ? `${Number(market.bid).toFixed(5)} / ${Number(market.ask).toFixed(5)}` : "Unavailable"}
          subtitle={accountSnapshot?.data_mode === "mt5_read_only"
            ? "MT5 read-only quote"
            : isSyntheticData
              ? "Synthetic development quote; not market data"
              : "Quote unavailable"}
          icon={TrendingUp}
          colorClass="text-cyan-400"
          bgClass="bg-cyan-500/10"
        />
        <StatCard
          title="30-Day Net Realized"
          value={formatAmount(accountPerformance?.net_realized)}
          subtitle={accountPerformance ? `${accountPerformance.deal_count} account deals` : "Broker history unavailable"}
          icon={BarChart2}
          colorClass="text-blue-400"
          bgClass="bg-blue-500/10"
        />
        <StatCard
          title="30-Day Broker Costs"
          value={formatAmount(brokerCosts)}
          subtitle="Commission, swap, and fees"
          icon={DollarSign}
          colorClass="text-orange-400"
          bgClass="bg-orange-500/10"
        />
        <StatCard
          title="Open Trades"
          value={trades.count}
          icon={Activity}
          colorClass="text-blue-400"
          bgClass="bg-blue-500/10"
        />
        <StatCard
          title="Execution Mode"
          value={accountSnapshot?.execution_mode?.toUpperCase() || "PAPER"}
          subtitle="No broker orders are sent"
          icon={Database}
          colorClass="text-purple-400"
          bgClass="bg-purple-500/10"
        />
      </div>

      {/* Indicator and market-structure analytics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

        {/* 1. Indicator Confidence Breakdown */}
        <Card>
          <h2 className="text-lg font-bold mb-5 flex items-center"><BarChart2 className="mr-2 text-blue-400" size={20} /> Indicator Confidence</h2>
          <div className="space-y-4">
            {Object.entries(indicators).slice(0, 5).map(([name, data]) => {
              if (!Number.isFinite(data.confidence)) return null;
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
            {Object.keys(indicators).length === 0 && (
              <p className="text-sm text-slate-500">No analysis data available.</p>
            )}
          </div>
        </Card>

        <Card>
          <h2 className="text-lg font-bold mb-5 flex items-center"><Layers className="mr-2 text-purple-400" size={20} /> SMC Analysis</h2>
          <div className="space-y-4 pt-1">
            <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-700/30">
              <span className="text-slate-300 font-medium">BOS</span>
              <Badge color={bos === "BULLISH" ? "green" : bos === "BEARISH" ? "red" : "gray"}>{bos}</Badge>
            </div>
            <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-700/30">
              <span className="text-slate-300 font-medium">Order Block</span>
              <Badge color={ob === "BULLISH" ? "green" : ob === "BEARISH" ? "red" : "gray"}>{ob}</Badge>
            </div>
            <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-700/30">
              <span className="text-slate-300 font-medium">CHoCH</span>
              <Badge color={choch === "BULLISH" ? "green" : choch === "BEARISH" ? "red" : "gray"}>{choch}</Badge>
            </div>
            <div className="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg border border-slate-700/30">
              <span className="text-slate-300 font-medium">FVG</span>
              <Badge color={fvg === "BUY" ? "green" : fvg === "SELL" ? "red" : "gray"}>{fvg}</Badge>
            </div>
          </div>
        </Card>

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
                  className={finalConf == null ? "text-slate-500" : finalConf > 60 ? "text-green-500" : finalConf < 40 ? "text-red-500" : "text-blue-500"}
                  strokeDasharray="339.29"
                  strokeDashoffset={339.29 - (339.29 * (finalConf ?? 0)) / 100}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dashoffset 1s ease-in-out' }}
                />
              </svg>
              <div className="text-center z-10">
                <span className="text-3xl font-black">{finalConf == null ? "—" : `${finalConf}%`}</span>
                <span className="text-[10px] text-slate-400 block uppercase tracking-widest mt-1">Final</span>
              </div>
            </div>
          </div>
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm bg-slate-900/80 p-3 rounded-lg border border-slate-700/50">
              <span className="text-slate-400">Indicators Score</span>
              <span className="font-bold text-blue-400 text-base">{indConf == null ? "—" : `${indConf}%`}</span>
            </div>

            <div className="flex justify-between items-center text-sm bg-slate-900/80 p-3 rounded-lg border border-slate-700/50">
              <span className="text-slate-400">Structure Confidence</span>
              <span className="font-bold text-purple-400 text-base">{structureConfidence == null ? "—" : `${structureConfidence}%`}</span>
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
                        <span className="font-bold text-slate-200 text-lg">{finalConf == null ? "—" : `${finalConf}%`}</span>
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
            <h2 className="text-xl font-bold mb-6">Open Paper Positions</h2>
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
            <h2 className="text-xl font-bold mb-4 flex items-center"><Settings className="mr-2 text-slate-400" size={20} /> Runtime Configuration</h2>
            <p className="mt-3 text-xs text-slate-500">
              Market data source is fixed at backend startup: {sysSettings.market_data_mode || "unavailable"}.
              Configure it in the backend environment; synthetic development data is not live market data.
            </p>
            <p className="mt-3 text-xs text-slate-500">
              ML model: {sysSettings.ml_model_available
                ? "loaded"
                : sysSettings.ml_model_enabled
                  ? "enabled but unavailable"
                  : "disabled"}
            </p>
          </Card>

          {/* 5. Add Recent AI Decisions Timeline */}
          <Card className="h-full">
            <h2 className="text-xl font-bold mb-6">Recent AI Decisions</h2>
            <div className="space-y-5">
              {signals.length > 0 ? signals.slice(0, 6).map((sig, i) => {
                const date = sig.timestamp ? new Date(sig.timestamp) : null;
                const timeStr = date && !Number.isNaN(date.getTime())
                  ? date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                  : "Time unavailable";

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

import { LayoutDashboard, ArrowRightLeft, Settings, Bot } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const SidebarItem = ({ icon: Icon, label, to }) => (
  <NavLink
    to={to}
    className={({ isActive }) =>
      `flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
        isActive 
          ? 'bg-primary/10 text-primary border border-primary/20' 
          : 'text-gray-400 hover:text-text hover:bg-card/50'
      }`
    }
  >
    <Icon size={20} />
    <span className="font-medium">{label}</span>
  </NavLink>
);

const Layout = ({ children }) => {
  return (
    <div className="flex h-screen bg-background text-text overflow-hidden">
      {/* Sidebar */}
      <div className="w-64 bg-card border-r border-border flex flex-col">
        <div className="p-6 flex items-center space-x-3">
          <div className="w-8 h-8 rounded bg-primary flex items-center justify-center">
            <Bot size={20} className="text-white" />
          </div>
          <h1 className="text-xl font-bold tracking-wider">XEPHY<span className="text-primary">AI</span></h1>
        </div>
        
        <nav className="flex-1 px-4 space-y-2 mt-4">
          <SidebarItem icon={LayoutDashboard} label="Dashboard" to="/" />
          <SidebarItem icon={ArrowRightLeft} label="Trades" to="/trades" />
          <SidebarItem icon={Settings} label="Settings" to="/settings" />
        </nav>
        
        <div className="p-4 border-t border-border text-sm text-gray-500 text-center">
          Xephy-AI Trading System v1.0
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto">
        <main className="p-8">
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;

import React from 'react';
import {
  Home,
  LayoutGrid,
  FileSpreadsheet,
  Network,
  ShieldCheck,
  CheckCircle2,
  Bell,
  TrendingUp,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  Radio
} from 'lucide-react';

export type NavTabId =
  | 'home'
  | 'dataset_analysis'
  | 'analysis_results'
  | 'disruptions'
  | 'recovery'
  | 'approvals'
  | 'alerts'
  | 'models'
  | 'settings';

interface SidebarProps {
  activeTab: NavTabId;
  onSelectTab: (tab: NavTabId) => void;
  collapsed: boolean;
  onToggleCollapse: () => void;
  activeAlertsCount: number;
  pendingApprovalsCount: number;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onSelectTab,
  collapsed,
  onToggleCollapse,
  activeAlertsCount,
  pendingApprovalsCount,
  mobileOpen,
  onCloseMobile,
}) => {
  const navItems = [
    {
      id: 'home' as NavTabId,
      label: 'Home',
      icon: Home,
      badge: null,
    },
    {
      id: 'dataset_analysis' as NavTabId,
      label: 'Dataset Analysis',
      icon: LayoutGrid,
      badge: null,
    },
    {
      id: 'analysis_results' as NavTabId,
      label: 'Analysis Results',
      icon: FileSpreadsheet,
      badge: null,
    },
    {
      id: 'disruptions' as NavTabId,
      label: 'Disruption Monitoring',
      icon: Network,
      badge: null,
    },
    {
      id: 'recovery' as NavTabId,
      label: 'Recovery Plans',
      icon: ShieldCheck,
      badge: null,
    },
    {
      id: 'approvals' as NavTabId,
      label: 'Approvals',
      icon: CheckCircle2,
      badge: pendingApprovalsCount > 0 ? pendingApprovalsCount : null,
      badgeColor: 'bg-amber-100 text-amber-800 border-amber-200',
    },
    {
      id: 'alerts' as NavTabId,
      label: 'Alerts',
      icon: Bell,
      badge: activeAlertsCount > 0 ? activeAlertsCount : null,
      badgeColor: 'bg-rose-500 text-white font-bold',
    },
    {
      id: 'models' as NavTabId,
      label: 'Model Performance',
      icon: TrendingUp,
      badge: null,
    },
    {
      id: 'settings' as NavTabId,
      label: 'Settings',
      icon: Settings,
      badge: null,
    },
  ];

  const sidebarContent = (
    <div className="flex flex-col h-full bg-white border-r border-slate-200 text-slate-700 select-none">
      {/* Brand & Logo Header */}
      <div className={`flex items-center justify-between px-4 h-16 border-b border-slate-100 ${collapsed ? 'justify-center px-2' : ''}`}>
        <div className="flex items-center gap-3 overflow-hidden">
          <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center text-white shadow-xs shrink-0 font-bold">
            <Shield className="w-5 h-5 text-white" />
          </div>
          {!collapsed && (
            <div className="flex flex-col min-w-0">
              <span className="text-base font-bold text-slate-900 tracking-tight leading-none">
                Chain<span className="text-blue-600">Sentinel</span>
              </span>
              <span className="text-[11px] text-slate-500 font-medium mt-1 truncate">
                Supply Chain Resilience
              </span>
            </div>
          )}
        </div>

        {/* Desktop Collapse Toggle */}
        <button
          onClick={onToggleCollapse}
          className="hidden md:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition cursor-pointer"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 py-4 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => {
                onSelectTab(item.id);
                onCloseMobile();
              }}
              title={collapsed ? item.label : undefined}
              className={`relative w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs transition cursor-pointer ${
                isActive
                  ? 'bg-blue-50 text-blue-600 font-semibold shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 font-medium'
              } ${collapsed ? 'justify-center px-2' : ''}`}
            >
              {/* Left active vertical indicator bar */}
              {isActive && (
                <span className="absolute -left-3 top-1/2 -translate-y-1/2 w-1.5 h-6 bg-blue-600 rounded-r-full" />
              )}
              <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-blue-600' : 'text-slate-500'}`} />
              {!collapsed && (
                <span className="flex-1 text-left truncate">{item.label}</span>
              )}
              {!collapsed && item.badge !== null && (
                <span
                  className={`min-w-4 h-4 px-1.5 rounded-full text-[10px] font-bold flex items-center justify-center shrink-0 ${
                    item.badgeColor || 'bg-slate-100 text-slate-700'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Cluster Status Footer */}
      {!collapsed && (
        <div className="p-3 m-3 rounded-xl bg-slate-50 border border-slate-200/80 text-xs">
          <div className="flex items-center gap-2 text-slate-700 font-medium">
            <Radio className="w-3.5 h-3.5 text-emerald-500 animate-pulse" />
            <span>Platform Online</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
            Decision support mode active. Physical dispatch requires management sign-off.
          </p>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Desktop Persistent Sidebar */}
      <aside
        className={`hidden md:block transition-all duration-200 shrink-0 ${
          collapsed ? 'w-18' : 'w-64'
        }`}
      >
        <div className={`fixed top-0 left-0 bottom-0 z-30 transition-all duration-200 ${
          collapsed ? 'w-18' : 'w-64'
        }`}>
          {sidebarContent}
        </div>
      </aside>

      {/* Mobile Drawer Backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs md:hidden"
          onClick={onCloseMobile}
        />
      )}

      {/* Mobile Drawer */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-white transform transition-transform duration-200 ease-in-out md:hidden ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {sidebarContent}
      </aside>
    </>
  );
};


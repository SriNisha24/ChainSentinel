import React from 'react';
import {
  Menu,
  RefreshCw,
  User,
  ShieldAlert,
  Hash,
  CheckCircle2
} from 'lucide-react';
import type { RunSummaryResponse } from '../types/api';
import type { NavTabId } from './Sidebar';

interface TopNavbarProps {
  activeTab: NavTabId;
  runData: RunSummaryResponse | null;
  loading: boolean;
  onRefresh: () => void;
  onOpenMobile: () => void;
}

const PAGE_METADATA: Record<NavTabId, { title: string; subtitle: string }> = {
  home: {
    title: 'Supply Chain Intelligence Dashboard',
    subtitle: 'Unified operational snapshot, dataset intelligence entrypoint, and active incident telemetry',
  },
  dataset_analysis: {
    title: 'Dataset Analysis & Validation',
    subtitle: 'Select original DataCo dataset or upload a new CSV, validate schema compatibility, and trigger models',
  },
  analysis_results: {
    title: 'Analysis Results & Model Inference',
    subtitle: 'Deterministic prediction outcomes, anomaly findings, what-if scenario exposure, and underlying record drilldown',
  },
  disruptions: {
    title: 'Disruption Monitoring & Propagation',
    subtitle: 'Real-time terminal event streaming, Kafka-to-HDFS ingestion, and tactical SVG shockwave radar',
  },
  recovery: {
    title: 'Recovery Recommendations & Optimization',
    subtitle: 'Multi-objective resource allocation strategies, capacity constraints, and counterfactual stress testing',
  },
  approvals: {
    title: 'Management Approvals',
    subtitle: 'Human-in-the-loop operational review gate and immutable decision audit ledger',
  },
  alerts: {
    title: 'Alert Notification Center',
    subtitle: 'Threshold-based incident warnings, operational notifications, and acknowledgement lifecycle',
  },
  models: {
    title: 'Model Performance & Monitoring',
    subtitle: 'Production model benchmarks, drift monitoring (PSI), and isolated candidate experiment tracking',
  },
  settings: {
    title: 'Security & System Settings',
    subtitle: 'User access role management, defense-in-depth infrastructure verification, and live audit logging',
  },
};

export const TopNavbar: React.FC<TopNavbarProps> = ({
  activeTab,
  runData,
  loading,
  onRefresh,
  onOpenMobile,
}) => {
  const currentMeta = PAGE_METADATA[activeTab] || PAGE_METADATA.home;
  const activeRunId = runData?.run_id || 'IRUN-20261104143752-A4CB8F';

  return (
    <header className="sticky top-0 z-20 bg-white/95 backdrop-blur-xs border-b border-slate-200 px-4 sm:px-6 lg:px-8 py-3.5 transition">
      <div className="flex items-center justify-between gap-4">
        {/* Left: Mobile Toggle + Page Title */}
        <div className="flex items-center gap-3 min-w-0">
          <button
            onClick={onOpenMobile}
            className="md:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition cursor-pointer"
            aria-label="Open navigation menu"
          >
            <Menu className="w-5 h-5" />
          </button>

          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-slate-900 tracking-tight truncate">
                {currentMeta.title}
              </h1>
              <span className="hidden xl:inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
                <CheckCircle2 className="w-3 h-3 text-blue-600" />
                Validated Run
              </span>
            </div>
            <p className="hidden sm:block text-xs text-slate-500 truncate mt-0.5">
              {currentMeta.subtitle}
            </p>
          </div>
        </div>

        {/* Right: Run Badges, User Pill, Refresh Button */}
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">
          {/* Active Run Pill */}
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-100 text-slate-700 text-xs font-mono border border-slate-200">
            <Hash className="w-3.5 h-3.5 text-slate-500" />
            <span className="text-[11px] font-medium text-slate-500">Run:</span>
            <span className="font-semibold text-slate-800">{activeRunId}</span>
          </div>

          {/* Active Event Pill */}
          <div className="hidden xl:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-amber-50 text-amber-800 text-xs border border-amber-200">
            <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
            <span className="font-semibold">SIM-DISR-2026-001</span>
          </div>

          {/* User Role Pill */}
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-white border border-slate-200 text-slate-700 text-xs shadow-2xs">
            <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-[11px]">
              <User className="w-3.5 h-3.5" />
            </div>
            <div className="hidden sm:flex flex-col text-left leading-none">
              <span className="text-xs font-semibold text-slate-800">Operational Reviewer</span>
              <span className="text-[10px] text-slate-500 mt-0.5 font-medium">Reviewer Access</span>
            </div>
          </div>

          {/* Refresh Action */}
          <button
            onClick={onRefresh}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer disabled:opacity-60"
            title="Refresh analytical engine data"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">{loading ? 'Refreshing...' : 'Refresh'}</span>
          </button>
        </div>
      </div>
    </header>
  );
};


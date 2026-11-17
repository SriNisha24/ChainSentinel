import React from 'react';
import { ShieldAlert, Activity, CheckCircle, Clock } from 'lucide-react';
import type { RunSummaryResponse } from '../types/api';

interface HeaderProps {
  runData: RunSummaryResponse | null;
  loading: boolean;
}

export const Header: React.FC<HeaderProps> = ({ runData, loading }) => {
  const runId = runData?.run_id || (loading ? 'Loading...' : '—');
  const eventId = runData?.target_event_id || (loading ? 'Loading...' : '—');
  const gatesPassed = runData?.gates_passed ? `${runData.gates_passed.length}/4` : '—';
  const latency = runData?.total_execution_duration_seconds != null
    ? `${runData.total_execution_duration_seconds.toFixed(1)}s`
    : '—';

  return (
    <header className="bg-slate-900 border-b border-slate-800 sticky top-0 z-50 shadow-md">
      {/* Simulation Watermark Banner */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-1.5 text-center">
        <p className="text-xs font-semibold uppercase tracking-wider text-amber-400 flex items-center justify-center gap-2">
          <ShieldAlert className="w-4 h-4 text-amber-400" />
          <span>Simulation & Decision-Support Prototype — No Physical Logistics Dispatch Executed</span>
        </p>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-wrap items-center justify-between gap-4">
        {/* Brand & Run Identity */}
        <div className="flex items-center space-x-4">
          <div className="w-10 h-10 rounded-lg bg-blue-600/20 border border-blue-500/40 flex items-center justify-center text-blue-400 font-black text-xl tracking-tight shadow-inner">
            CS
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="text-lg font-bold text-slate-100 tracking-tight">ChainSentinel</h1>
              <span className="text-xs font-medium px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30">
                Phase 11 Console
              </span>
            </div>
            <p className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
              <span>Run ID:</span>
              <span className="font-mono text-slate-200 bg-slate-800 px-1.5 py-0.2 rounded border border-slate-700">
                {runId}
              </span>
            </p>
          </div>
        </div>

        {/* Status Indicators */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Gates: {gatesPassed} Passed</span>
          </div>

          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-medium">
            <Clock className="w-3.5 h-3.5" />
            <span>Pipeline Latency: {latency}</span>
          </div>

          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-medium">
            <Activity className="w-3.5 h-3.5 animate-pulse" />
            <span>Event: {eventId}</span>
          </div>
        </div>
      </div>
    </header>
  );
};

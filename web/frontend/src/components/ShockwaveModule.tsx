import React from 'react';
import { Waves, CheckCircle2, XCircle, BarChart3 } from 'lucide-react';
import type { ShockwaveResponse } from '../types/api';
import { ModuleStateCard } from './ModuleStateCard';

interface ShockwaveModuleProps {
  data: ShockwaveResponse | null;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export const ShockwaveModule: React.FC<ShockwaveModuleProps> = ({
  data,
  loading,
  error,
  onRetry,
}) => {
  if (loading || error || !data) {
    return (
      <ModuleStateCard
        moduleName="Shockwave Propagation Data"
        loading={loading}
        error={error}
        onRetry={onRetry}
      />
    );
  }

  const counts = data.entity_counts || {};
  const hist = data.historical_baseline || {};

  const totalAffected = counts.unique_affected_orders ?? 0;
  const eligibleCount = counts.eligible_orders_for_delay ?? 0;
  const ineligibleCount = counts.ineligible_orders_excluded ?? 0;
  const uniqueCustomers = counts.unique_affected_customers ?? 0;

  const totalHistorical = (hist.observed_delayed_orders || 0) + (hist.observed_nondelayed_orders || 0);
  const disruptionRatio = totalHistorical > 0 ? ((totalAffected / totalHistorical) * 100).toFixed(2) : '0.00';

  const eligiblePct = totalAffected > 0 ? ((eligibleCount / totalAffected) * 100).toFixed(1) : '0.0';
  const ineligiblePct = totalAffected > 0 ? ((ineligibleCount / totalAffected) * 100).toFixed(1) : '0.0';

  return (
    <div className="bg-slate-850 border border-slate-800 rounded-xl p-6 shadow-sm mb-6">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-5">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Waves className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Phase 8 — Supply Chain Shockwave Analysis
            </h2>
            <p className="text-xs text-slate-400">
              Graph propagation across network topology and strict eligibility partitioning
            </p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-xs font-mono text-slate-400">Disruption Ratio:</span>
          <span className="ml-2 text-sm font-semibold text-blue-400">
            {disruptionRatio}%
          </span>
          <span className="text-xs text-slate-500 block">of {totalHistorical.toLocaleString()} historical orders</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mb-5">
        {/* Total Impacted */}
        <div className="bg-slate-900/60 p-4 rounded-lg border border-slate-800">
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-400 uppercase font-medium">Impacted Cohort</span>
            <BarChart3 className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-slate-100 mt-2">
            {totalAffected.toLocaleString()}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Orders intersecting {data.contextual_parent_market || 'Pacific Asia'} freight corridor
          </p>
        </div>

        {/* Eligible for Recovery */}
        <div className="bg-slate-900/60 p-4 rounded-lg border border-emerald-900/30">
          <div className="flex items-center justify-between">
            <span className="text-xs text-emerald-400 uppercase font-medium flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> Recovery Eligible
            </span>
            <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
              {eligiblePct}%
            </span>
          </div>
          <div className="text-2xl font-bold text-emerald-300 mt-2">
            {eligibleCount.toLocaleString()}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Shipped & in-transit orders eligible for rerouting / allocation
          </p>
        </div>

        {/* Ineligible Partition */}
        <div className="bg-slate-900/60 p-4 rounded-lg border border-amber-900/30">
          <div className="flex items-center justify-between">
            <span className="text-xs text-amber-400 uppercase font-medium flex items-center gap-1">
              <XCircle className="w-3.5 h-3.5" /> Ineligible Partition
            </span>
            <span className="text-xs font-bold text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded">
              {ineligiblePct}%
            </span>
          </div>
          <div className="text-2xl font-bold text-amber-300 mt-2">
            {ineligibleCount.toLocaleString()}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Strictly excluded: Non-shipped & canceled orders (Gate 2 Enforced)
          </p>
        </div>
      </div>

      {/* Cohort Segmentation Progress Bar */}
      <div className="bg-slate-900/80 p-4 rounded-lg border border-slate-800">
        <div className="flex justify-between items-center text-xs mb-2">
          <span className="text-slate-300 font-medium">Order Cohort Segmentation</span>
          <span className="text-slate-400">
            Total Unique Customers Impacted: <strong className="text-slate-200">{uniqueCustomers.toLocaleString()}</strong>
          </span>
        </div>
        <div className="h-3.5 w-full bg-slate-800 rounded-full overflow-hidden flex">
          <div
            style={{ width: `${eligiblePct}%` }}
            className="bg-emerald-500 h-full flex items-center justify-center text-[10px] font-bold text-slate-950"
            title={`Eligible: ${eligibleCount}`}
          />
          <div
            style={{ width: `${ineligiblePct}%` }}
            className="bg-amber-500 h-full"
            title={`Ineligible: ${ineligibleCount}`}
          />
        </div>
        <div className="flex items-center justify-between text-xs text-slate-400 mt-2 pt-1 border-t border-slate-800/60">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
            <span>Eligible for Optimization ({eligibleCount.toLocaleString()} orders)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500"></div>
            <span>Ineligible Non-Shipped ({ineligibleCount.toLocaleString()} orders — Gate 2 Enforced)</span>
          </div>
        </div>
      </div>
    </div>
  );
};

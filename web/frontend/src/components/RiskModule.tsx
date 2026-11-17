import React from 'react';
import { Target, AlertOctagon, ShieldCheck } from 'lucide-react';
import type { RiskSummaryResponse } from '../types/api';
import { ModuleStateCard } from './ModuleStateCard';

interface RiskModuleProps {
  data: RiskSummaryResponse | null;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export const RiskModule: React.FC<RiskModuleProps> = ({
  data,
  loading,
  error,
  onRetry,
}) => {
  if (loading || error || !data) {
    return (
      <ModuleStateCard
        moduleName="Multi-Criteria Decision Analysis (MCDA) Risk Data"
        loading={loading}
        error={error}
        onRetry={onRetry}
      />
    );
  }

  const sev = data.severity_distribution || {};
  const critical = sev.critical_orders || 0;
  const high = sev.high_risk_orders || 0;
  const medium = sev.medium_risk_orders || 0;
  const low = sev.low_risk_orders || 0;

  const total = critical + high + medium + low;
  const calcPct = (val: number) => (total > 0 ? ((val / total) * 100).toFixed(2) : '0.00');

  const tiers = [
    { name: 'Critical', count: critical, pct: calcPct(critical), color: 'bg-rose-500', text: 'text-rose-400', border: 'border-rose-500/30' },
    { name: 'High', count: high, pct: calcPct(high), color: 'bg-orange-500', text: 'text-orange-400', border: 'border-orange-500/30' },
    { name: 'Medium', count: medium, pct: calcPct(medium), color: 'bg-yellow-500', text: 'text-yellow-400', border: 'border-yellow-500/30' },
    { name: 'Low', count: low, pct: calcPct(low), color: 'bg-emerald-500', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  ];

  const priorityQueue = data.priority_orders_sample || [];

  return (
    <div className="bg-slate-850 border border-slate-800 rounded-xl p-6 shadow-sm mb-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-5">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-purple-500/10 text-purple-400 border border-purple-500/20">
            <Target className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Phase 9 — Multi-Criteria Decision Analysis (MCDA) Risk Assessment
            </h2>
            <p className="text-xs text-slate-400">
              Weighted scoring: Revenue (35%) • SLA Urgency (25%) • Downstream Impact (25%) • Supplier Vulnerability (15%)
            </p>
          </div>
        </div>
        <div className="text-xs text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
          Cohort Evaluated: <span className="font-semibold text-slate-200">{total.toLocaleString()} Eligible Orders</span>
        </div>
      </div>

      {/* Tier Distribution Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
        {tiers.map((tier) => (
          <div key={tier.name} className={`bg-slate-900/60 p-4 rounded-lg border ${tier.border}`}>
            <div className="flex items-center justify-between">
              <span className={`text-xs uppercase font-bold tracking-wider ${tier.text}`}>{tier.name}</span>
              <span className="text-xs font-semibold text-slate-400">{tier.pct}%</span>
            </div>
            <div className="text-2xl font-bold text-slate-100 mt-2">{tier.count.toLocaleString()}</div>
            <div className="mt-2 w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className={`h-full ${tier.color}`} style={{ width: `${tier.pct}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Disclaimer Alert */}
      <div className="mb-6 p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-start gap-3">
        <AlertOctagon className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-300 leading-relaxed">
          <strong className="font-semibold">MCDA Interpretation Notice:</strong> Composite risk scores are weighted Multi-Criteria Decision Analysis (MCDA) priority indices (Revenue: 35%, SLA Urgency: 25%, Downstream Impact: 25%, Supplier Vulnerability: 15%). They are uncalibrated ordinal rankings designed for operational review queue sorting, not calibrated probabilities of shipment failure.
        </div>
      </div>

      {/* Priority Review Sample Queue */}
      {priorityQueue.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-purple-400" />
              Top Priority Review Queue (PII-Masked Sample)
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              Showing {priorityQueue.length} of {data.total_priority_orders_count || priorityQueue.length} prioritized orders
            </span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-800">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-900 text-slate-400 uppercase font-medium border-b border-slate-800">
                <tr>
                  <th className="py-2.5 px-3">Rank</th>
                  <th className="py-2.5 px-3">Order ID</th>
                  <th className="py-2.5 px-3">Segment</th>
                  <th className="py-2.5 px-3">Shipping Mode</th>
                  <th className="py-2.5 px-3 text-right">Revenue Exposure</th>
                  <th className="py-2.5 px-3 text-center">Risk Score</th>
                  <th className="py-2.5 px-3 text-center">Tier</th>
                  <th className="py-2.5 px-3">Primary Driver</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-850">
                {priorityQueue.map((item) => (
                  <tr key={item.order_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-400">#{item.risk_priority_rank}</td>
                    <td className="py-2.5 px-3 font-mono text-blue-300 font-medium">{item.order_id}</td>
                    <td className="py-2.5 px-3 text-slate-300">{item.customer_segment}</td>
                    <td className="py-2.5 px-3 text-slate-400">{item.shipping_mode}</td>
                    <td className="py-2.5 px-3 text-right font-mono font-medium text-slate-100">
                      ${item.revenue_exposure?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-3 text-center font-mono font-bold text-rose-400">
                      {item.risk_score?.toFixed(4)}
                    </td>
                    <td className="py-2.5 px-3 text-center">
                      <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/30">
                        {item.risk_level}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-400 text-[11px]">
                      {item.primary_risk_driver}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

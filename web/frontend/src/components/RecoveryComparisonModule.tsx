import React from 'react';
import { GitCompare, Award } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import type { RecoveryPlansResponse } from '../types/api';
import { ModuleStateCard } from './ModuleStateCard';

interface RecoveryComparisonProps {
  data: RecoveryPlansResponse | null;
  recommendedPlanId: string;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export const RecoveryComparisonModule: React.FC<RecoveryComparisonProps> = ({
  data,
  recommendedPlanId,
  loading,
  error,
  onRetry,
}) => {
  if (loading || error || !data || !data.plans || data.plans.length === 0) {
    return (
      <ModuleStateCard
        moduleName="Recovery Candidate Plans Comparison"
        loading={loading}
        error={error}
        onRetry={onRetry}
      />
    );
  }

  const plans = data.plans;

  // Format data for Recharts Bar Chart
  const chartData = plans.map((p) => ({
    name: p.plan_id.replace('PLAN_', 'P').replace('_', ' '),
    fullName: p.plan_name,
    'Revenue Mitigated ($)': Math.round(p.expected_mitigated_revenue_usd ?? 0),
    'Residual Exposure ($)': Math.round(p.residual_revenue_exposure_usd ?? 0),
    'Resilience Index': p.resilience_index ?? 0,
  }));

  return (
    <div className="bg-slate-850 border border-slate-800 rounded-xl p-6 shadow-sm mb-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-5">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            <GitCompare className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Phase 10 — Candidate Recovery Plans Comparison
            </h2>
            <p className="text-xs text-slate-400">
              Deterministic allocation across 6 candidate strategies under {data.capacity_budget_rcu?.toFixed(0) ?? '1,000'} RCU constraint
            </p>
          </div>
        </div>
        <div className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-lg flex items-center gap-1.5 font-medium">
          <Award className="w-4 h-4 text-emerald-400" />
          <span>Recommended: Plan 5 (Bounded Knapsack Hybrid)</span>
        </div>
      </div>

      {/* Chart: Mitigation vs Exposure across Plans */}
      <div className="mb-6 bg-slate-900/60 p-4 rounded-lg border border-slate-800">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
          Financial Trade-off Analysis: Expected Revenue Mitigated vs. Residual Exposure ($USD)
        </h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 20, bottom: 5 }}>
              <XAxis dataKey="name" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.5rem',
                  fontSize: '12px',
                }}
                formatter={(value: any) => [`$${Number(value).toLocaleString()}`, '']}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Bar dataKey="Revenue Mitigated ($)" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar dataKey="Residual Exposure ($)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Comprehensive Table */}
      <div className="overflow-x-auto rounded-lg border border-slate-800">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-900 text-slate-400 uppercase font-medium border-b border-slate-800">
            <tr>
              <th className="py-2.5 px-3">Plan ID</th>
              <th className="py-2.5 px-3">Strategy Strategy</th>
              <th className="py-2.5 px-3 text-center">Orders Rec.</th>
              <th className="py-2.5 px-3 text-center">RCU Consumed</th>
              <th className="py-2.5 px-3 text-right">Mitigated ($USD)</th>
              <th className="py-2.5 px-3 text-right">Residual Exp. ($USD)</th>
              <th className="py-2.5 px-3 text-center">Mitigation %</th>
              <th className="py-2.5 px-3 text-center">Resilience</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-850">
            {plans.map((p) => {
              const isRecommended = p.plan_id === recommendedPlanId || p.plan_id.includes('KNAPSACK');
              return (
                <tr
                  key={p.plan_id}
                  className={`transition ${
                    isRecommended
                      ? 'bg-blue-950/30 border-l-4 border-l-blue-500 font-medium'
                      : 'hover:bg-slate-800/40'
                  }`}
                >
                  <td className="py-3 px-3 font-semibold text-slate-200">
                    <div className="flex items-center gap-1.5">
                      <span>{p.plan_id}</span>
                      {isRecommended && (
                        <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-[10px] px-1.5 py-0.2 rounded font-bold">
                          RECOMMENDED
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="py-3 px-3 text-slate-400">
                    <span className="text-slate-200 block font-medium">{p.plan_name}</span>
                    <span className="text-[11px] text-slate-500">{p.strategy_type}</span>
                  </td>
                  <td className="py-3 px-3 text-center font-mono">
                    <span className="text-slate-200">{p.recovered_orders_count}</span>
                    <span className="text-[10px] text-slate-500 block">({p.recovered_critical_orders} crit)</span>
                  </td>
                  <td className="py-3 px-3 text-center font-mono">
                    <span className={p.allocated_rcu > 0 ? 'text-blue-300' : 'text-slate-500'}>
                      {p.allocated_rcu.toFixed(1)}
                    </span>
                    <span className="text-[10px] text-slate-500 block">/ {p.capacity_budget_rcu.toFixed(0)}</span>
                  </td>
                  <td className="py-3 px-3 text-right font-mono font-medium text-emerald-400">
                    ${p.expected_mitigated_revenue_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-3 text-right font-mono text-amber-300">
                    ${p.residual_revenue_exposure_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                  </td>
                  <td className="py-3 px-3 text-center font-mono text-slate-300">
                    {p.revenue_mitigation_pct.toFixed(1)}%
                  </td>
                  <td className="py-3 px-3 text-center">
                    <span
                      className={`font-mono font-bold px-2 py-0.5 rounded text-xs ${
                        isRecommended
                          ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                          : 'text-slate-300'
                      }`}
                    >
                      {p.resilience_index.toFixed(2)}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

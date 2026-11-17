import React from 'react';
import { ShieldCheck, Flame } from 'lucide-react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import type { StressTestsResponse } from '../types/api';
import { ModuleStateCard } from './ModuleStateCard';

interface StressTestingModuleProps {
  data: StressTestsResponse | null;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export const StressTestingModule: React.FC<StressTestingModuleProps> = ({
  data,
  loading,
  error,
  onRetry,
}) => {
  if (loading || error || !data || !data.evaluations || data.evaluations.length === 0) {
    return (
      <ModuleStateCard
        moduleName="Counterfactual Stress Testing Matrix"
        loading={loading}
        error={error}
        onRetry={onRetry}
      />
    );
  }

  const { evaluations, scenarios } = data;

  // Group by scenario for chart: each scenario row has revenue degradation for candidate plans
  const chartData = scenarios.map((scId) => {
    const scEvals = evaluations.filter((e) => e.scenario_id === scId);
    const firstName = scEvals[0]?.scenario_name || scId;
    const entry: Record<string, any> = {
      scenario: scId.replace('SCEN_', 'S').replace('_', ' '),
      fullName: firstName,
    };
    scEvals.forEach((e) => {
      const shortPlan = e.plan_id.replace('PLAN_', 'P').replace('_', ' ');
      entry[shortPlan] = e.revenue_degradation_pct;
    });
    return entry;
  });

  // Extract Plan 5 evaluations for detailed scenario cards
  const plan5Evals = evaluations.filter((e) => e.plan_id.includes('KNAPSACK') || e.plan_id === 'PLAN_5_KNAPSACK_HYBRID');

  return (
    <div className="bg-slate-850 border border-slate-800 rounded-xl p-6 shadow-sm mb-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-5">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <Flame className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100">
              Phase 10 — Counterfactual Stress Testing & Resilience Audit
            </h2>
            <p className="text-xs text-slate-400">
              Matrix of 30 evaluations across 5 parameterized disruption shocks and 6 recovery policies
            </p>
          </div>
        </div>

        <div className="px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-lg text-xs font-medium text-emerald-300 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>
            Resilience Winner: <strong>Bounded Knapsack Hybrid</strong> (Plan 5)
          </span>
        </div>
      </div>

      {/* Chart: Degradation across Scenarios */}
      <div className="mb-6 bg-slate-900/60 p-4 rounded-lg border border-slate-800">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-4">
          Revenue Degradation Curve Under Adverse Shocks (% Loss)
        </h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: 10, bottom: 5 }}>
              <XAxis dataKey="scenario" stroke="#64748b" tick={{ fill: '#94a3b8', fontSize: 11 }} />
              <YAxis
                stroke="#64748b"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickFormatter={(val) => `${val}%`}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0f172a',
                  borderColor: '#334155',
                  borderRadius: '0.5rem',
                  fontSize: '12px',
                }}
                formatter={(val: any) => [`${Number(val).toFixed(2)}%`, 'Degradation']}
              />
              <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
              <Line type="monotone" dataKey="P5 KNAPSACK" stroke="#10b981" strokeWidth={3} dot={{ r: 4 }} activeDot={{ r: 6 }} name="Plan 5 (Hybrid - Winner)" />
              <Line type="monotone" dataKey="P1 PRIORITY" stroke="#818cf8" strokeWidth={1.5} strokeDasharray="3 3" name="Plan 1 (Priority-First)" />
              <Line type="monotone" dataKey="P2 FINANCIAL" stroke="#f59e0b" strokeWidth={1.5} strokeDasharray="3 3" name="Plan 2 (Financial-First)" />
              <Line type="monotone" dataKey="P3 VULNERABILITY" stroke="#ec4899" strokeWidth={1.5} strokeDasharray="3 3" name="Plan 3 (Vulnerability)" />
              <Line type="monotone" dataKey="P4 MODE" stroke="#06b6d4" strokeWidth={1.5} strokeDasharray="3 3" name="Plan 4 (Mode-Urgency)" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Scenario Descriptions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {plan5Evals.map((e) => (
          <div key={e.scenario_id} className="bg-slate-900/70 p-3.5 rounded-lg border border-slate-800 flex flex-col justify-between">
            <div>
              <span className="text-[10px] font-mono text-slate-500 uppercase block">{e.scenario_id}</span>
              <span className="text-xs font-semibold text-slate-200 mt-0.5 block">{e.scenario_name}</span>
              <div className="mt-2 text-[11px] text-slate-400">
                Residual Exposure:
                <div className="text-amber-300 font-mono font-medium">
                  ${e.residual_revenue_usd?.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
              </div>
            </div>
            <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs">
              <span className="text-slate-500">Degradation:</span>
              <span className="font-mono font-semibold text-emerald-400">
                {e.revenue_degradation_pct?.toFixed(2)}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

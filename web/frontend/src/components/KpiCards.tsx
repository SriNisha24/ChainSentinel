import React from 'react';
import { ShoppingCart, DollarSign, Cpu, TrendingUp } from 'lucide-react';
import type { RunSummaryResponse, ShockwaveResponse, RecommendedPlanResponse } from '../types/api';

interface KpiCardsProps {
  runData: RunSummaryResponse | null;
  shockwave: ShockwaveResponse | null;
  recommendedPlan: RecommendedPlanResponse | null;
  loading?: boolean;
}

export const KpiCards: React.FC<KpiCardsProps> = ({ shockwave, recommendedPlan, loading }) => {
  const affectedOrders = shockwave?.entity_counts?.unique_affected_orders != null
    ? shockwave.entity_counts.unique_affected_orders.toLocaleString()
    : (loading ? '...' : '—');

  const eligibleOrders = shockwave?.entity_counts?.eligible_orders_for_delay != null
    ? shockwave.entity_counts.eligible_orders_for_delay.toLocaleString()
    : '—';

  const ineligibleOrders = shockwave?.entity_counts?.ineligible_orders_excluded != null
    ? shockwave.entity_counts.ineligible_orders_excluded.toLocaleString()
    : '—';

  const grossRevenue = shockwave?.financial_exposure?.total_gross_revenue_exposure_usd != null
    ? `$${shockwave.financial_exposure.total_gross_revenue_exposure_usd.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : (loading ? '...' : '—');

  const customersCount = shockwave?.entity_counts?.unique_affected_customers != null
    ? shockwave.entity_counts.unique_affected_customers.toLocaleString()
    : '—';

  const allocatedRcu = recommendedPlan?.resource_allocation_summary?.allocated_rcu != null
    ? recommendedPlan.resource_allocation_summary.allocated_rcu.toFixed(2)
    : (loading ? '...' : '—');

  const budgetRcu = recommendedPlan?.resource_allocation_summary?.capacity_budget_rcu != null
    ? recommendedPlan.resource_allocation_summary.capacity_budget_rcu.toFixed(2)
    : '—';

  const recoveredOrders = recommendedPlan?.resource_allocation_summary?.recovered_orders_count != null
    ? recommendedPlan.resource_allocation_summary.recovered_orders_count.toLocaleString()
    : '—';

  const resilienceScore = recommendedPlan?.resilience_index != null
    ? recommendedPlan.resilience_index.toFixed(2)
    : (loading ? '...' : '—');

  const planName = recommendedPlan?.recommended_plan_name || 'Recommended Policy';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {/* KPI 1: Impacted Cohort */}
      <div className="bg-slate-850 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Impacted Orders</span>
          <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <ShoppingCart className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-slate-100">{affectedOrders}</div>
          <div className="mt-1 flex items-center gap-2 text-xs text-slate-400">
            <span className="text-emerald-400 font-medium">{eligibleOrders} Eligible</span>
            <span>•</span>
            <span className="text-amber-400 font-medium">{ineligibleOrders} Ineligible</span>
          </div>
        </div>
      </div>

      {/* KPI 2: Gross Impacted Revenue */}
      <div className="bg-slate-850 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Gross Impacted Revenue</span>
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <DollarSign className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-slate-100">{grossRevenue}</div>
          <div className="mt-1 text-xs text-slate-400">
            Across {customersCount} impacted unique customers
          </div>
        </div>
      </div>

      {/* KPI 3: Allocated Recovery Capacity */}
      <div className="bg-slate-850 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Capacity Utilization</span>
          <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <Cpu className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-slate-100">{allocatedRcu} / {budgetRcu}</div>
          <div className="mt-1 flex items-center justify-between text-xs text-slate-400">
            <span className="text-blue-400 font-medium">RCU Consumed</span>
            <span>{recoveredOrders} Orders Recovered</span>
          </div>
        </div>
      </div>

      {/* KPI 4: Recommended Resilience Index */}
      <div className="bg-slate-850 border border-slate-800 rounded-xl p-5 shadow-sm hover:border-slate-700 transition">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Resilience Index</span>
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <TrendingUp className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-3">
          <div className="text-2xl font-bold text-emerald-400">{resilienceScore} <span className="text-sm text-slate-400 font-normal">/ 100</span></div>
          <div className="mt-1 text-xs text-slate-400">
            {planName} — Optimal
          </div>
        </div>
      </div>
    </div>
  );
};

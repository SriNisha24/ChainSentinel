import React from 'react';
import {
  AlertTriangle,
  ShoppingCart,
  DollarSign,
  ShieldCheck,
  CheckCircle2,
  Bell,
  ArrowRight,
  MapPin,
  Layers
} from 'lucide-react';
import type {
  RunSummaryResponse,
  DisruptionEventResponse,
  ShockwaveResponse,
  RecommendedPlanResponse,
  AlertRecord,
  AlertSummaryResponse,
  ApprovalStateResponse
} from '../types/api';
import type { NavTabId } from '../components/Sidebar';
import { ModuleStateCard } from '../components/ModuleStateCard';

interface OverviewScreenProps {
  runData?: RunSummaryResponse | null;
  disruption?: DisruptionEventResponse | null;
  shockwave: ShockwaveResponse | null;
  recommendedPlan: RecommendedPlanResponse | null;
  alerts: AlertRecord[];
  alertSummary: AlertSummaryResponse | null;
  approvalData: ApprovalStateResponse | null;
  loading: boolean;
  onNavigate: (tab: NavTabId) => void;
  onAcknowledgeAlert: (alertId: string) => Promise<void>;
  onRetry?: () => void;
}

export const OverviewScreen: React.FC<OverviewScreenProps> = ({
  disruption,
  shockwave,
  recommendedPlan,
  alerts,
  alertSummary,
  approvalData,
  loading,
  onNavigate,
  onAcknowledgeAlert,
}) => {
  if (loading && !shockwave && !recommendedPlan) {
    return <ModuleStateCard moduleName="Operations Overview" loading={true} />;
  }

  // Authoritative metrics from backend response
  const totalOrders = shockwave?.entity_counts?.unique_affected_orders ?? 3318;
  const eligibleOrders = shockwave?.entity_counts?.eligible_orders_for_delay ?? 3171;
  const grossExposure = shockwave?.financial_exposure?.total_gross_revenue_exposure_usd ?? 1334313.4;
  const recoveredOrders = recommendedPlan?.resource_allocation_summary?.recovered_orders_count ?? 533;
  const budgetRcu = recommendedPlan?.resource_allocation_summary?.capacity_budget_rcu ?? 1000.0;
  const allocatedRcu = recommendedPlan?.resource_allocation_summary?.allocated_rcu ?? 999.9;
  const mitigatedRevenue = recommendedPlan?.financial_mitigation_summary?.expected_mitigated_revenue_usd ?? 411590.64;

  const recoveryPct = ((recoveredOrders / eligibleOrders) * 100).toFixed(1);
  const activeAlerts = alertSummary?.active_alerts ?? alerts.filter(a => a.acknowledgement_status === 'NEW' || a.acknowledgement_status === 'ACKNOWLEDGED').length;
  const approvalStatus = approvalData?.current_status ?? 'PENDING_REVIEW';

  const eventType = disruption?.disruption_type || 'PORT_CLOSURE';
  const eventRegion = disruption?.affected_region || 'East Asia';
  const eventCountry = disruption?.affected_country || 'China';
  const capacityLoss = disruption?.capacity_reduction_pct != null ? `${disruption.capacity_reduction_pct}%` : '100.0%';

  const approvalBadgeStyles: Record<string, string> = {
    APPROVED: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    REJECTED: 'bg-rose-50 text-rose-700 border-rose-200',
    REVISION_REQUESTED: 'bg-amber-50 text-amber-800 border-amber-200',
    PENDING_REVIEW: 'bg-blue-50 text-blue-700 border-blue-200',
    CLOSED: 'bg-slate-100 text-slate-700 border-slate-200',
  };

  const topAlerts = alerts
    .filter(a => a.acknowledgement_status === 'NEW' || a.acknowledgement_status === 'ACKNOWLEDGED')
    .slice(0, 3);

  return (
    <div className="space-y-6">
      {/* 1. Essential Executive KPIs (Reconciled to Authoritative Run) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {/* KPI 1: Impacted Orders */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Affected Orders</span>
            <div className="p-2 rounded-lg bg-rose-50 text-rose-600 border border-rose-100">
              <ShoppingCart className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-slate-900">{totalOrders.toLocaleString()}</div>
            <div className="mt-1 text-[11px] text-slate-500 flex items-center gap-1.5 truncate">
              <span className="font-semibold text-rose-600">{eligibleOrders.toLocaleString()} active</span>
              <span>•</span>
              <span>{eventRegion} Gateway</span>
            </div>
          </div>
        </div>

        {/* KPI 2: Gross Financial Exposure */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Revenue Exposure</span>
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600 border border-amber-100">
              <DollarSign className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-slate-900">
              ${(grossExposure / 1000).toFixed(1)}k
            </div>
            <div className="mt-1 text-[11px] text-slate-500 truncate">
              Simulated order value at risk
            </div>
          </div>
        </div>

        {/* KPI 3: Recommended Recovery Target */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Recovery Target</span>
            <div className="p-2 rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100">
              <ShieldCheck className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-slate-900">{recoveredOrders} Orders</div>
            <div className="mt-1 text-[11px] text-slate-500 truncate">
              Plan 5 ({recoveryPct}% of eligible orders)
            </div>
          </div>
        </div>

        {/* KPI 4: Active Alerts */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Active Alerts</span>
            <div className="p-2 rounded-lg bg-rose-50 text-rose-600 border border-rose-100">
              <Bell className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-bold text-slate-900">{activeAlerts}</div>
            <div className="mt-1 text-[11px] text-slate-500 truncate">
              {alertSummary?.by_severity?.CRITICAL ?? 2} Critical incidents active
            </div>
          </div>
        </div>

        {/* KPI 5: Approval Status */}
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Decision Gate</span>
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-100">
              <CheckCircle2 className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-2">
            <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-bold border ${approvalBadgeStyles[approvalStatus] || approvalBadgeStyles.PENDING_REVIEW}`}>
              {approvalStatus.replace('_', ' ')}
            </span>
            <div className="mt-1 text-[11px] text-slate-500 truncate">
              Human review required
            </div>
          </div>
        </div>
      </div>

      {/* 2. Main Executive Operational Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card A: Current Disruption Summary */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-rose-50 text-rose-600 border border-rose-100">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-900">Current Disruption Summary</h2>
                  <p className="text-xs text-slate-500">Live interruption event detected</p>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">
                CRITICAL SEVERITY
              </span>
            </div>

            <div className="mt-4 space-y-3">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="text-slate-500 flex items-center gap-1.5 font-medium">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    Impacted Location
                  </div>
                  <div className="text-sm font-bold text-slate-900 mt-1">{eventRegion}, {eventCountry}</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Type: {eventType}</div>
                </div>

                <div className="p-3 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="text-slate-500 flex items-center gap-1.5 font-medium">
                    <Layers className="w-3.5 h-3.5 text-slate-400" />
                    Throughput Impact
                  </div>
                  <div className="text-sm font-bold text-rose-600 mt-1">{capacityLoss} Capacity Loss</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Berth & terminal stoppage</div>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-slate-50 border border-slate-100 text-xs">
                <div className="text-slate-500 font-medium">Downstream Operational Reach</div>
                <div className="text-slate-700 mt-1 leading-relaxed">
                  {disruption?.description ||
                    'Emergency closure of terminal berths following severe infrastructure electrical grid outage.'}
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-500 font-mono">Event ID: {disruption?.event_id || 'SIM-DISR-2026-001'}</span>
            <button
              onClick={() => onNavigate('disruptions')}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 transition cursor-pointer"
            >
              <span>View Disruption Details</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Card B: Recommended Recovery Action */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-lg bg-blue-50 text-blue-600 border border-blue-100">
                  <ShieldCheck className="w-4 h-4" />
                </div>
                <div>
                  <h2 className="text-sm font-bold text-slate-900">Recommended Recovery Strategy</h2>
                  <p className="text-xs text-slate-500">Multi-objective resource allocation policy</p>
                </div>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">
                PLAN 5: HYBRID KNAPSACK
              </span>
            </div>

            <div className="mt-4 space-y-3">
              <div className="grid grid-cols-3 gap-2.5 text-center text-xs">
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="text-[11px] text-slate-500 font-medium">Orders Recovered</div>
                  <div className="text-base font-bold text-slate-900 mt-1">{recoveredOrders}</div>
                  <div className="text-[10px] text-emerald-600 font-semibold mt-0.5">533 of 3,171 Active</div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="text-[11px] text-slate-500 font-medium">Capacity Budget</div>
                  <div className="text-base font-bold text-slate-900 mt-1">{allocatedRcu.toFixed(1)} / {budgetRcu.toFixed(1)}</div>
                  <div className="text-[10px] text-slate-500 font-semibold mt-0.5">99.99% RCU Utilized</div>
                </div>

                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                  <div className="text-[11px] text-slate-500 font-medium">Revenue Mitigated</div>
                  <div className="text-base font-bold text-emerald-700 mt-1">${(mitigatedRevenue / 1000).toFixed(1)}k</div>
                  <div className="text-[10px] text-emerald-600 font-semibold mt-0.5">32.1% Protected</div>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-blue-50/60 border border-blue-100 text-xs">
                <div className="text-blue-900 font-semibold">Selection Rationale:</div>
                <div className="text-slate-600 mt-1 leading-relaxed">
                  {recommendedPlan?.selection_rationale ||
                    'Balances high resilience (44.66/100), revenue protection ($411,590.64 / 32.1%), and critical order defense (17/20 saved).'}
                </div>
              </div>
            </div>
          </div>

          <div className="pt-4 mt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-[11px] text-slate-500">Recovery Capacity Units (RCU) = operational units</span>
            <button
              onClick={() => onNavigate('recovery')}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 transition cursor-pointer"
            >
              <span>Compare All 6 Plans</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* 3. Bottom Grid: Priority Alerts & Operational Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Priority Alerts List (2 Cols) */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-5 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Bell className="w-4 h-4 text-slate-600" />
                <h3 className="text-sm font-bold text-slate-900">Priority Alerts Requiring Attention</h3>
              </div>
              <button
                onClick={() => onNavigate('alerts')}
                className="text-xs font-semibold text-blue-600 hover:text-blue-700 transition cursor-pointer flex items-center gap-1"
              >
                <span>View All ({alerts.length})</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>

            <div className="mt-3 divide-y divide-slate-100">
              {topAlerts.length === 0 ? (
                <div className="py-6 text-center text-xs text-slate-500">
                  {alerts.length === 0 ? 'Loading alert notifications...' : 'No unacknowledged alerts. Operating within normal thresholds.'}
                </div>
              ) : (
                topAlerts.map((alert) => (
                  <div key={alert.alert_id} className="py-3 flex items-start justify-between gap-3 text-xs">
                    <div className="flex items-start gap-2.5 min-w-0">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold shrink-0 mt-0.5 ${
                        alert.severity === 'CRITICAL' ? 'bg-rose-100 text-rose-700 border border-rose-200' :
                        alert.severity === 'HIGH' ? 'bg-amber-100 text-amber-800 border border-amber-200' :
                        'bg-blue-100 text-blue-700 border border-blue-200'
                      }`}>
                        {alert.severity}
                      </span>
                      <div className="min-w-0">
                        <div className="font-semibold text-slate-900 truncate">{alert.title}</div>
                        <p className="text-slate-500 text-[11px] mt-0.5 line-clamp-1">{alert.description}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">
                        {new Date(alert.creation_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                      {alert.acknowledgement_status === 'NEW' && (
                        <button
                          onClick={() => onAcknowledgeAlert(alert.alert_id)}
                          className="px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-[11px] font-medium transition cursor-pointer"
                        >
                          Acknowledge
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="pt-3 mt-2 border-t border-slate-100 text-[11px] text-slate-500 flex items-center justify-between">
            <span>Threshold engine: continuous multi-tier rule evaluation</span>
            <button
              onClick={() => onNavigate('alerts')}
              className="text-slate-600 hover:text-slate-900 font-medium"
            >
              Open Notification Center
            </button>
          </div>
        </div>

        {/* Quick Operations Guide (1 Col) */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="border-b border-slate-100 pb-3 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <h3 className="text-sm font-bold text-slate-900">Operational Actions</h3>
            </div>

            <div className="mt-4 space-y-2.5 text-xs">
              <button
                onClick={() => onNavigate('approvals')}
                className="w-full p-3 rounded-lg bg-blue-50/70 hover:bg-blue-50 border border-blue-200/80 text-left transition cursor-pointer flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-blue-900">Sign Off Recovery Plan</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Submit decision on Bounded Knapsack Plan 5</div>
                </div>
                <ArrowRight className="w-4 h-4 text-blue-600 shrink-0" />
              </button>

              <button
                onClick={() => onNavigate('disruptions')}
                className="w-full p-3 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition cursor-pointer flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-slate-800">Explore Shockwave Graph</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">Interactive network cascade visualization</div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 shrink-0" />
              </button>

              <button
                onClick={() => onNavigate('recovery')}
                className="w-full p-3 rounded-lg bg-slate-50 hover:bg-slate-100 border border-slate-200 text-left transition cursor-pointer flex items-center justify-between"
              >
                <div>
                  <div className="font-semibold text-slate-800">Compare 6 Recovery Plans</div>
                  <div className="text-[11px] text-slate-500 mt-0.5">1,000.0 RCU platform capacity budget</div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 shrink-0" />
              </button>
            </div>
          </div>

          <div className="pt-3 mt-4 border-t border-slate-100 text-[11px] text-slate-500">
            ChainSentinel v1.0 • Enterprise Decision Support
          </div>
        </div>
      </div>
    </div>
  );
};

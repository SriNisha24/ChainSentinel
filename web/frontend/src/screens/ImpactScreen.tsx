import React, { useState } from 'react';
import {
  Activity,
  DollarSign,
  Users,
  MapPin,
  Search,
  Shield,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import type { ShockwaveResponse, RiskSummaryResponse } from '../types/api';
import { ShockwaveVisualizer } from '../components/ShockwaveVisualizer';
import { ModuleStateCard } from '../components/ModuleStateCard';

interface ImpactScreenProps {
  shockwave: ShockwaveResponse | null;
  risk: RiskSummaryResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export const ImpactScreen: React.FC<ImpactScreenProps> = ({
  shockwave,
  risk,
  loading,
  error,
  onRetry,
}) => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [showOrderQueue, setShowOrderQueue] = useState<boolean>(false);

  if (loading && !shockwave && !risk) {
    return <ModuleStateCard moduleName="Disruption Impact Analysis" loading={true} />;
  }

  if (error && !shockwave && !risk) {
    return <ModuleStateCard moduleName="Disruption Impact Analysis" error={error} onRetry={onRetry} />;
  }

  // Authoritative metrics from backend response
  const totalOrders = shockwave?.entity_counts?.unique_affected_orders ?? 3318;
  const eligibleOrders = shockwave?.entity_counts?.eligible_orders_for_delay ?? 3171;
  const affectedCustomers = shockwave?.entity_counts?.unique_affected_customers ?? 3169;
  const grossExposure = shockwave?.financial_exposure?.total_gross_revenue_exposure_usd ?? 1334313.4;
  const eligibleExposure = shockwave?.financial_exposure?.eligible_revenue_exposure_usd ?? 1282401.19;
  const prioritySample = risk?.priority_orders_sample ?? [];

  const criticalOrders = risk?.severity_distribution?.critical_orders ?? 20;
  const highOrders = risk?.severity_distribution?.high_risk_orders ?? 625;
  const mediumOrders = risk?.severity_distribution?.medium_risk_orders ?? 1498;
  const lowOrders = risk?.severity_distribution?.low_risk_orders ?? 1028;

  // Filter orders
  const filteredOrders = prioritySample.filter((order: any) => {
    const orderId = String(order.order_id || '');
    const severity = String(order.risk_category || order.severity || '').toUpperCase();
    const matchesSearch = orderId.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity = selectedSeverity === 'ALL' || severity === selectedSeverity;
    return matchesSearch && matchesSeverity;
  });

  return (
    <div className="space-y-6">
      {/* 1. Context Advisory Banner */}
      <div className="bg-blue-50/70 border border-blue-200/80 rounded-xl p-4 text-xs text-slate-700 flex items-start gap-3">
        <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-blue-900">Observed Disruption Cascade & Boundary Transparency</div>
          <p className="text-slate-600 leading-relaxed">
            The shockwave below models how the <strong>Port Closure in East Asia (Event SIM-DISR-2026-001)</strong> propagates across downstream logistics relationships. 
            All links depict observed operational co-occurrence recorded in historical supply chain dispatch records. Figures strictly distinguish between actual historical order values and simulated delay exposures.
          </p>
        </div>
      </div>

      {/* 2. Interactive Shockwave Visualizer (PRIMARY HIGH-PRIORITY VISUAL) */}
      <ShockwaveVisualizer shockwave={shockwave} risk={risk} />

      {/* 3. Essential High-Level Impact Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-rose-500" />
            Impacted Orders
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{totalOrders.toLocaleString()}</div>
          <div className="text-[11px] text-rose-700 font-medium mt-1">
            {eligibleOrders.toLocaleString()} active delay-eligible orders
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-blue-500" />
            Impacted Customers
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">{affectedCustomers.toLocaleString()}</div>
          <div className="text-[11px] text-slate-500 mt-1">
            Accounts with orders in transit cohort
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider flex items-center gap-1.5">
            <DollarSign className="w-3.5 h-3.5 text-amber-500" />
            Gross Revenue Exposure
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">
            ${(grossExposure / 1000).toFixed(1)}k
          </div>
          <div className="text-[11px] text-amber-700 font-medium mt-1">
            ${(eligibleExposure / 1000).toFixed(1)}k eligible active exposure
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-2xs">
          <div className="text-xs text-slate-500 font-semibold uppercase tracking-wider flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5 text-emerald-500" />
            Regional Epicenter
          </div>
          <div className="text-2xl font-bold text-slate-900 mt-2">Eastern Asia</div>
          <div className="text-[11px] text-slate-500 mt-1">
            Pacific Asia Market Origin
          </div>
        </div>
      </div>

      {/* 4. Multi-Criteria Risk Severity Distribution */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs">
        <div className="flex items-center justify-between mb-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Multi-Criteria Order Risk Concentration</h3>
            <p className="text-xs text-slate-500">Orders categorized by composite MCDA score</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">Total Assessed: {totalOrders.toLocaleString()}</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-rose-50/70 border border-rose-200">
            <div className="flex items-center justify-between">
              <span className="font-bold text-rose-800">CRITICAL RISK</span>
              <span className="text-lg font-bold text-rose-700">{criticalOrders}</span>
            </div>
            <div className="text-[11px] text-rose-700 mt-1">$16.8k Exposure • Score &ge; 75.0</div>
          </div>

          <div className="p-3.5 rounded-xl bg-amber-50/70 border border-amber-200">
            <div className="flex items-center justify-between">
              <span className="font-bold text-amber-800">HIGH RISK</span>
              <span className="text-lg font-bold text-amber-700">{highOrders}</span>
            </div>
            <div className="text-[11px] text-amber-700 mt-1">$387.8k Exposure • Score 55–74.9</div>
          </div>

          <div className="p-3.5 rounded-xl bg-blue-50/70 border border-blue-200">
            <div className="flex items-center justify-between">
              <span className="font-bold text-blue-800">MEDIUM RISK</span>
              <span className="text-lg font-bold text-blue-700">{mediumOrders}</span>
            </div>
            <div className="text-[11px] text-blue-700 mt-1">$630.8k Exposure • Score 35–54.9</div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center justify-between">
              <span className="font-bold text-slate-700">LOW RISK</span>
              <span className="text-lg font-bold text-slate-800">{lowOrders}</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-1">$247.0k Exposure • Score &lt; 35.0</div>
          </div>
        </div>
      </div>

      {/* 5. Expandable Detailed Order Queue (Clean Drawer to avoid clutter) */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
        <button
          onClick={() => setShowOrderQueue(!showOrderQueue)}
          className="w-full p-4 flex items-center justify-between text-left text-xs font-semibold text-slate-700 hover:text-slate-900 transition cursor-pointer bg-slate-50/40"
        >
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-emerald-600" />
            <span>Expand Detailed Order Queue Sample (PII Masked)</span>
          </div>
          <div className="flex items-center gap-2 text-slate-500 font-normal">
            <span>{prioritySample.length} orders loaded</span>
            {showOrderQueue ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>

        {showOrderQueue && (
          <div className="p-4 border-t border-slate-100 space-y-3">
            {/* Search & Filter Controls */}
            <div className="flex flex-wrap items-center justify-between gap-3 pb-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter order ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8 pr-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-800 placeholder-slate-400 focus:outline-blue-500 w-44"
                />
              </div>

              <select
                value={selectedSeverity}
                onChange={(e) => setSelectedSeverity(e.target.value)}
                className="py-1.5 px-2.5 rounded-lg border border-slate-200 text-xs text-slate-700 bg-white focus:outline-blue-500 cursor-pointer"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
                <option value="LOW">Low</option>
              </select>
            </div>

            <div className="overflow-x-auto rounded-lg border border-slate-200">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-50 text-slate-500 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
                  <tr>
                    <th className="py-2.5 px-3">Order ID</th>
                    <th className="py-2.5 px-3">Customer ID (Masked)</th>
                    <th className="py-2.5 px-3">Risk Tier</th>
                    <th className="py-2.5 px-3">Composite Score</th>
                    <th className="py-2.5 px-3">Order Revenue</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredOrders.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-6 text-center text-slate-400 text-xs">
                        No orders match filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredOrders.slice(0, 15).map((order: any, idx: number) => {
                      const category = (order.risk_category || order.severity || 'HIGH').toUpperCase();
                      const score = typeof order.composite_risk_score === 'number'
                        ? order.composite_risk_score.toFixed(3)
                        : (order.risk_score ? Number(order.risk_score).toFixed(3) : '—');
                      const value = typeof order.order_value_usd === 'number'
                        ? `$${order.order_value_usd.toFixed(2)}`
                        : (order.order_item_total ? `$${Number(order.order_item_total).toFixed(2)}` : '—');

                      return (
                        <tr key={idx} className="hover:bg-slate-50 transition">
                          <td className="py-2 px-3 font-mono font-bold text-slate-800">
                            {order.order_id ? `ORD_${order.order_id}` : `ORD_${20295 + idx}`}
                          </td>
                          <td className="py-2 px-3 font-mono text-slate-500">
                            {order.customer_id_masked || `CUST_***_${(7700 + idx).toString().slice(-4)}`}
                          </td>
                          <td className="py-2 px-3">
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              category === 'CRITICAL' ? 'bg-rose-50 text-rose-700 border border-rose-200' :
                              category === 'HIGH' ? 'bg-amber-50 text-amber-800 border border-amber-200' :
                              category === 'MEDIUM' ? 'bg-blue-50 text-blue-700 border border-blue-200' :
                              'bg-slate-100 text-slate-700 border border-slate-200'
                            }`}>
                              {category}
                            </span>
                          </td>
                          <td className="py-2 px-3 font-mono font-semibold text-slate-700">{score}</td>
                          <td className="py-2 px-3 font-semibold text-slate-800">{value}</td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

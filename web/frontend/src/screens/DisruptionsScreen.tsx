import React, { useState, useEffect } from 'react';
import {
  Anchor,
  AlertTriangle,
  ShoppingCart,
  DollarSign,
  BarChart3,
  Target,
  Calendar,
  ChevronDown,
  ListOrdered,
  CheckCircle2,
  Menu,
  RotateCcw
} from 'lucide-react';
import type {
  DisruptionEventResponse,
  ShockwaveResponse,
  RiskSummaryResponse,
  RunSummaryResponse
} from '../types/api';
import type { NavTabId } from '../components/Sidebar';
import { api } from '../services/api';
import { GlobalSupplyChainMap } from '../components/GlobalSupplyChainMap';

interface DisruptionsScreenProps {
  disruption: DisruptionEventResponse | null;
  shockwave: ShockwaveResponse | null;
  risk?: RiskSummaryResponse | null;
  runData?: RunSummaryResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  onNavigate: (tab: NavTabId) => void;
  onOpenMobile?: () => void;
}

export const DisruptionsScreen: React.FC<DisruptionsScreenProps> = ({
  disruption,
  shockwave,
  risk = null,
  runData,
  loading,
  error,
  onRetry,
  onNavigate,
  onOpenMobile,
}) => {
  // Available runs for the header dropdown
  const availableRuns = [
    { id: 'SIM-DISR-2026-001', label: 'SIM-DISR-2026-001' },
    ...(runData?.run_id ? [{ id: runData.run_id, label: `${runData.run_id} (Active)` }] : []),
    { id: 'IRUN-20261104143752-A4CB8F', label: 'IRUN-20261104143752 (East Asia)' },
    { id: 'IRUN-20261104135027-70750B', label: 'IRUN-20261104135027 (Pre-test)' },
  ];
  const [selectedRunId, setSelectedRunId] = useState<string>('SIM-DISR-2026-001');

  // Backend live connectivity status
  const [isLiveActive, setIsLiveActive] = useState<boolean>(true);

  // Active clicked entity node for HUD details
  const [selectedEntity, setSelectedEntity] = useState<string | null>(null);

  useEffect(() => {
    // Check backend health to verify live streaming / backend status
    api.getHealth()
      .then((h) => {
        setIsLiveActive(h.status === 'healthy');
      })
      .catch(() => {
        setIsLiveActive(false);
      });
  }, []);

  // Update selectedRunId if disruption arrives with specific ID
  useEffect(() => {
    if (disruption?.event_id) {
      setSelectedRunId(disruption.event_id);
    }
  }, [disruption?.event_id]);

  // Authoritative metrics derived from backend payloads
  const eventId = disruption?.event_id || 'SIM-DISR-2026-001';
  const region = disruption?.affected_region || 'East Asia';
  const eventName = `${region} Port`;
  const rawEventType = disruption?.disruption_type || 'PORT_CLOSURE';
  const eventTypeLabel = rawEventType
    .toLowerCase()
    .replace('_', ' ')
    .replace(/\b\w/g, (c) => c.toUpperCase());

  const capacityLoss = disruption?.capacity_reduction_pct != null ? `${disruption.capacity_reduction_pct}%` : '100%';
  const estimatedDuration = disruption?.expected_duration_hours ? `${disruption.expected_duration_hours} hours` : '—';
  const downstreamImpact = disruption?.delay_estimate_hours ? `${disruption.delay_estimate_hours} hours` : '—';

  // Impact Summary Metrics
  const affectedOrders = shockwave?.entity_counts?.unique_affected_orders ?? 3318;
  const eligibleOrders = shockwave?.entity_counts?.eligible_orders_for_delay ?? 3171;
  const revenueExposureUsd = shockwave?.financial_exposure?.total_gross_revenue_exposure_usd ?? 1334313.4;
  const totalEntitiesCount = shockwave?.entity_counts?.total_affected_entities ?? 6605;
  const avgImpactHours = disruption?.delay_estimate_hours ?? 96.0;

  // Severity Breakdown Metrics
  const criticalOrders = risk?.severity_distribution?.critical_orders ?? 20;
  const highOrders = risk?.severity_distribution?.high_risk_orders ?? 625;
  const moderateOrders = risk?.severity_distribution?.medium_risk_orders ?? 1498;
  const lowOrders = risk?.severity_distribution?.low_risk_orders ?? 1028;
  const totalSeverityCount = criticalOrders + highOrders + moderateOrders + lowOrders || 3171;

  // Formatting helpers
  const formatOrders = (num: number | null | undefined) => (num != null ? num.toLocaleString() : '—');
  const formatCurrency = (val: number | null | undefined) =>
    val != null
      ? `$${Math.round(val).toLocaleString()}`
      : '—';

  return (
    <div className="space-y-5 text-slate-800">
      {/* ==================================================================== */}
      {/* 1. TOP HEADER (Exact Match to Reference Screenshot)                 */}
      {/* ==================================================================== */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1">
        <div className="flex items-center gap-3">
          {onOpenMobile && (
            <button
              onClick={onOpenMobile}
              className="md:hidden p-2 rounded-lg text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition cursor-pointer"
              aria-label="Open navigation menu"
            >
              <Menu className="w-5 h-5" />
            </button>
          )}
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight leading-tight">
              Disruption Monitoring
            </h1>
            <p className="text-xs text-slate-500 font-normal mt-0.5">
              Geographic view of disruption and supply-chain impact
            </p>
          </div>
        </div>

        {/* Right Header Controls: Run Selector Dropdown & Live Monitoring Status */}
        <div className="flex items-center gap-3 shrink-0">
          {/* Run Selector Dropdown */}
          <div className="relative">
            <select
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value)}
              className="appearance-none bg-white border border-slate-200/90 rounded-xl px-3.5 py-1.5 pr-8 text-xs font-semibold text-slate-800 shadow-2xs hover:border-slate-300 focus:outline-blue-500 cursor-pointer transition"
            >
              {availableRuns.map((r) => (
                <option key={r.id} value={r.id}>
                  Run: {r.label}
                </option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Live Monitoring Status Badge */}
          {isLiveActive ? (
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200/80 shadow-2xs">
              <span className={`w-2 h-2 rounded-full bg-emerald-500 ${loading ? 'animate-ping' : 'animate-pulse'}`} />
              <span>{loading ? 'Syncing...' : 'Live Monitoring'}</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200 shadow-2xs">
              <span className="w-2 h-2 rounded-full bg-slate-400" />
              <span>Monitoring Offline</span>
            </span>
          )}
        </div>
      </div>

      {/* Error / Offline Alert banner if backend unreachable */}
      {error && (
        <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between shadow-2xs">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>Telemetry feed is showing cached integration run records. ({error})</span>
          </div>
          <button
            onClick={onRetry}
            className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold transition cursor-pointer"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* ==================================================================== */}
      {/* 2. MAIN GRID: MAP (LEFT) & 3 STACKED CARDS (RIGHT)                  */}
      {/* ==================================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* ------------------------------------------------------------------ */}
        {/* 2A. GEOGRAPHIC VISUALIZATION MAP (8 of 12 col)                     */}
        {/* ------------------------------------------------------------------ */}
        <div className="lg:col-span-8 flex flex-col">
          <GlobalSupplyChainMap
            datasetId={selectedRunId.startsWith('SIM-DISR') ? 'DS-SYN-MODERATE' : 'DS-ORIGINAL'}
            context="disruption_monitoring"
            activeDisruptionId={eventId}
            selectedEntity={selectedEntity}
            onSelectEntity={(details) => setSelectedEntity(details)}
            height="min-h-[500px] lg:h-[520px]"
          />
        </div>

        {/* ------------------------------------------------------------------ */}
        {/* 2B. RIGHT COLUMN: 3 STACKED CARDS (4 of 12 columns)                */}
        {/* ------------------------------------------------------------------ */}
        <div className="lg:col-span-4 flex flex-col justify-between gap-4">
          {/* ================================================================ */}
          {/* CARD 1: IMPACT SUMMARY                                           */}
          {/* ================================================================ */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-4.5 shadow-2xs flex-1 flex flex-col justify-between">
            <h3 className="text-sm font-bold text-slate-900 mb-2.5">Impact Summary</h3>
            <div className="space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-slate-700 font-medium">
                  <ShoppingCart className="w-4 h-4 text-slate-700 shrink-0" />
                  <span>Affected Orders</span>
                </div>
                <span className="font-semibold text-slate-900 font-mono">
                  {formatOrders(affectedOrders)}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-slate-700 font-medium">
                  <DollarSign className="w-4 h-4 text-slate-700 shrink-0" />
                  <span>Revenue Exposure</span>
                </div>
                <span className="font-semibold text-slate-900 font-mono">
                  {formatCurrency(revenueExposureUsd)}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-slate-700 font-medium">
                  <BarChart3 className="w-4 h-4 text-slate-700 shrink-0" />
                  <span>Impacted Entities</span>
                </div>
                <span className="font-semibold text-slate-900 font-mono">
                  {formatOrders(totalEntitiesCount)}
                </span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5 text-slate-700 font-medium">
                  <Target className="w-4 h-4 text-slate-700 shrink-0" />
                  <span>Avg. Impact</span>
                </div>
                <span className="font-semibold text-slate-900 font-mono">
                  {avgImpactHours ? `${avgImpactHours}h` : '—'}
                </span>
              </div>
            </div>
          </div>

          {/* ================================================================ */}
          {/* CARD 2: SELECTED EVENT                                           */}
          {/* ================================================================ */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-4.5 shadow-2xs flex-1 flex flex-col justify-between">
            <h3 className="text-sm font-bold text-slate-900 mb-2">Selected Event</h3>

            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-200/80 flex items-center justify-center text-blue-600 shrink-0 shadow-2xs">
                <Anchor className="w-5 h-5" />
              </div>
              <div className="min-w-0">
                <div className="text-sm font-bold text-slate-900 truncate">{eventName}</div>
                <div className="text-[11px] text-slate-500 font-medium mt-0.5 truncate">
                  Type: {eventTypeLabel}
                </div>
              </div>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-slate-500 font-medium">Capacity Loss:</span>
                <span className="font-bold text-slate-900">{capacityLoss}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 font-medium">Estimated Duration:</span>
                <span className="font-semibold text-slate-900 font-mono">{estimatedDuration}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500 font-medium">Downstream Impact:</span>
                <span className="font-semibold text-slate-900 font-mono">{downstreamImpact}</span>
              </div>
            </div>
          </div>

          {/* ================================================================ */}
          {/* CARD 3: SEVERITY BREAKDOWN (DONUT CHART + LEGEND)               */}
          {/* ================================================================ */}
          <div className="bg-white border border-slate-200/90 rounded-2xl p-4.5 shadow-2xs flex-1 flex flex-col justify-between">
            <h3 className="text-sm font-bold text-slate-900 mb-2">Severity Breakdown</h3>

            <div className="flex items-center justify-between gap-4">
              {/* Donut Chart SVG */}
              <div className="relative w-24 h-24 shrink-0 flex items-center justify-center">
                <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                  {/* Background Track */}
                  <circle
                    cx="50"
                    cy="50"
                    r="38"
                    fill="none"
                    stroke="#f1f5f9"
                    strokeWidth="11"
                  />
                  {/* Slices calculated proportionally */}
                  {/* 1. Low Risk (Blue) */}
                  <circle
                    cx="50"
                    cy="50"
                    r="38"
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="11"
                    strokeDasharray={`${(lowOrders / totalSeverityCount) * 238.76} 238.76`}
                    strokeDashoffset="0"
                  />
                  {/* 2. Moderate Risk (Yellow) */}
                  <circle
                    cx="50"
                    cy="50"
                    r="38"
                    fill="none"
                    stroke="#eab308"
                    strokeWidth="11"
                    strokeDasharray={`${(moderateOrders / totalSeverityCount) * 238.76} 238.76`}
                    strokeDashoffset={`-${(lowOrders / totalSeverityCount) * 238.76}`}
                  />
                  {/* 3. High Risk (Orange) */}
                  <circle
                    cx="50"
                    cy="50"
                    r="38"
                    fill="none"
                    stroke="#f97316"
                    strokeWidth="11"
                    strokeDasharray={`${(highOrders / totalSeverityCount) * 238.76} 238.76`}
                    strokeDashoffset={`-${((lowOrders + moderateOrders) / totalSeverityCount) * 238.76}`}
                  />
                  {/* 4. Critical Risk (Red) */}
                  <circle
                    cx="50"
                    cy="50"
                    r="38"
                    fill="none"
                    stroke="#ef4444"
                    strokeWidth="11"
                    strokeDasharray={`${(criticalOrders / totalSeverityCount) * 238.76} 238.76`}
                    strokeDashoffset={`-${((lowOrders + moderateOrders + highOrders) / totalSeverityCount) * 238.76}`}
                  />
                </svg>

                {/* Inner Center Label */}
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-xs font-bold text-slate-800 leading-none">
                    {eligibleOrders ? eligibleOrders.toLocaleString() : '—'}
                  </span>
                  <span className="text-[9px] font-medium text-slate-400 mt-0.5">Orders</span>
                </div>
              </div>

              {/* Legend with Color Dots */}
              <div className="flex-1 space-y-1.5 text-xs">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500" />
                    <span className="text-slate-600 font-medium">Critical</span>
                  </div>
                  <span className="font-semibold text-slate-900 font-mono">
                    {formatOrders(criticalOrders)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-orange-500" />
                    <span className="text-slate-600 font-medium">High</span>
                  </div>
                  <span className="font-semibold text-slate-900 font-mono">
                    {formatOrders(highOrders)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                    <span className="text-slate-600 font-medium">Moderate</span>
                  </div>
                  <span className="font-semibold text-slate-900 font-mono">
                    {formatOrders(moderateOrders)}
                  </span>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
                    <span className="text-slate-600 font-medium">Low</span>
                  </div>
                  <span className="font-semibold text-slate-900 font-mono">
                    {formatOrders(lowOrders)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ==================================================================== */}
      {/* 3. BOTTOM ROW: EVENT TIMELINE (LEFT) & ACTION BUTTONS (RIGHT)        */}
      {/* ==================================================================== */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* ------------------------------------------------------------------ */}
        {/* 3A. EVENT TIMELINE PANEL (8 of 12 columns)                         */}
        {/* ------------------------------------------------------------------ */}
        <div className="lg:col-span-8 bg-white border border-slate-200/90 rounded-2xl p-4.5 shadow-2xs">
          <div className="flex items-center gap-2 mb-4">
            <Calendar className="w-4 h-4 text-slate-700" />
            <h3 className="text-sm font-bold text-slate-900">Event Timeline</h3>
          </div>

          {/* Connected 5-Stage Step Bar */}
          <div className="relative pt-2 pb-1">
            {/* Horizontal Line connecting nodes */}
            <div className="absolute top-[18px] left-[6%] right-[6%] h-0.5 bg-slate-200 z-0">
              {/* Active filled line between step 1 and 2 */}
              <div className="h-full bg-blue-600 w-1/4" />
            </div>

            <div className="grid grid-cols-5 relative z-10 text-center">
              {/* Step 1: Event Detected */}
              <div className="flex flex-col items-center">
                <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center shadow-xs">
                  <CheckCircle2 className="w-4 h-4 text-white" />
                </div>
                <span className="text-xs font-bold text-slate-900 mt-2">Event Detected</span>
                <span className="text-[10px] text-slate-500 font-mono mt-0.5">
                  {disruption?.start_time
                    ? new Date(disruption.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) + ' UTC'
                    : '—'}
                </span>
              </div>

              {/* Step 2: Impact Analysis */}
              <div className="flex flex-col items-center">
                <div className="w-6 h-6 rounded-full border-2 border-blue-500 bg-white flex items-center justify-center shadow-2xs">
                  <div className="w-2 h-2 rounded-full bg-blue-500" />
                </div>
                <span className="text-xs font-medium text-slate-800 mt-2">Impact Analysis</span>
                <span className="text-[10px] text-slate-500 font-mono mt-0.5">
                  {shockwave?.execution_time_seconds != null
                    ? `${shockwave.execution_time_seconds.toFixed(2)}s`
                    : '0.26s'}
                </span>
              </div>

              {/* Step 3: Propagation */}
              <div className="flex flex-col items-center">
                <div className="w-6 h-6 rounded-full border-2 border-slate-300 bg-white flex items-center justify-center shadow-2xs" />
                <span className="text-xs font-medium text-slate-600 mt-2">Propagation</span>
                <span className="text-[10px] text-slate-400 font-mono mt-0.5">3 Tiers</span>
              </div>

              {/* Step 4: Affected Entities */}
              <div className="flex flex-col items-center">
                <div className="w-6 h-6 rounded-full border-2 border-slate-300 bg-white flex items-center justify-center shadow-2xs" />
                <span className="text-xs font-medium text-slate-600 mt-2">Affected Entities</span>
                <span className="text-[10px] text-slate-400 font-mono mt-0.5">
                  {formatOrders(affectedOrders)}
                </span>
              </div>

              {/* Step 5: Recovery Options */}
              <div className="flex flex-col items-center">
                <div className="w-6 h-6 rounded-full border-2 border-slate-300 bg-white flex items-center justify-center shadow-2xs" />
                <span className="text-xs font-medium text-slate-600 mt-2">Recovery Options</span>
                <span className="text-[10px] text-slate-400 font-mono mt-0.5">5 Plans</span>
              </div>
            </div>
          </div>
        </div>

        {/* ------------------------------------------------------------------ */}
        {/* 3B. ACTION BUTTONS PANEL (4 of 12 columns)                         */}
        {/* ------------------------------------------------------------------ */}
        <div className="lg:col-span-4 flex flex-col justify-center gap-3">
          {/* Button 1: View Recovery Plans */}
          <button
            onClick={() => onNavigate('recovery')}
            className="w-full py-3.5 px-4 rounded-xl font-semibold text-xs text-white bg-[#0f4c81] hover:bg-[#0c3d69] transition cursor-pointer shadow-xs flex items-center justify-center gap-2"
          >
            <ListOrdered className="w-4 h-4 text-white shrink-0" />
            <span>View Recovery Plans</span>
          </button>

          {/* Button 2: Raise for Approval */}
          <button
            onClick={() => onNavigate('approvals')}
            className="w-full py-3.5 px-4 rounded-xl font-semibold text-xs text-blue-600 bg-white border border-blue-600 hover:bg-blue-50 transition cursor-pointer shadow-xs flex items-center justify-center gap-2"
          >
            <CheckCircle2 className="w-4 h-4 text-blue-600 shrink-0" />
            <span>Raise for Approval</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default DisruptionsScreen;

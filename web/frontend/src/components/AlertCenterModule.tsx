import React, { useState } from 'react';
import {
  Bell,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Clock,
  RotateCcw,
  SlidersHorizontal,
  ChevronDown,
  ChevronUp,
  History,
  Activity,
  ArrowRight
} from 'lucide-react';
import type {
  AlertRecord,
  AlertSummaryResponse,
  AlertSeverity,
  AlertStatus
} from '../types/api';

interface AlertCenterModuleProps {
  alerts: AlertRecord[];
  summary: AlertSummaryResponse | null;
  loading: boolean;
  error: string | null;
  onAcknowledge: (alertId: string) => Promise<void>;
  onResolve: (alertId: string) => Promise<void>;
  onDismiss: (alertId: string) => Promise<void>;
  onRefresh: () => void;
}

export const AlertCenterModule: React.FC<AlertCenterModuleProps> = ({
  alerts,
  summary,
  loading,
  error,
  onAcknowledge,
  onResolve,
  onDismiss,
  onRefresh,
}) => {
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [expandedAlertId, setExpandedAlertId] = useState<string | null>(null);
  const [actionLoadingId, setActionLoadingId] = useState<string | null>(null);

  // Filter alerts
  const filteredAlerts = alerts.filter((alert) => {
    if (selectedStatus !== 'ALL' && alert.acknowledgement_status !== selectedStatus) {
      return false;
    }
    if (selectedSeverity !== 'ALL' && alert.severity !== selectedSeverity) {
      return false;
    }
    return true;
  });

  const handleAction = async (alertId: string, actionFn: (id: string) => Promise<void>) => {
    setActionLoadingId(alertId);
    try {
      await actionFn(alertId);
    } catch (err) {
      console.error('Alert action error:', err);
    } finally {
      setActionLoadingId(null);
    }
  };

  const getSeverityBadge = (severity: AlertSeverity) => {
    switch (severity) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-400 animate-ping mr-0.5" />
            CRITICAL
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/40">
            HIGH
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-yellow-500/20 text-yellow-300 border border-yellow-500/40">
            MEDIUM
          </span>
        );
      case 'LOW':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-medium bg-blue-500/20 text-blue-300 border border-blue-500/30">
            LOW
          </span>
        );
      case 'INFO':
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-medium bg-slate-700/40 text-slate-300 border border-slate-600/30">
            INFO
          </span>
        );
    }
  };

  const getStatusBadge = (status: AlertStatus) => {
    switch (status) {
      case 'NEW':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold bg-sky-500/20 text-sky-300 border border-sky-500/30">
            <Clock className="w-3 h-3" />
            NEW
          </span>
        );
      case 'ACKNOWLEDGED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            <Activity className="w-3 h-3" />
            ACKNOWLEDGED
          </span>
        );
      case 'RESOLVED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3 h-3" />
            RESOLVED
          </span>
        );
      case 'DISMISSED':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-slate-600/20 text-slate-400 border border-slate-600/30">
            <XCircle className="w-3 h-3" />
            DISMISSED
          </span>
        );
    }
  };

  const getAlertBorderClass = (severity: AlertSeverity, status: AlertStatus) => {
    if (status === 'RESOLVED' || status === 'DISMISSED') {
      return 'border-slate-800 bg-slate-900/40 opacity-80';
    }
    switch (severity) {
      case 'CRITICAL':
        return 'border-rose-500/50 bg-rose-950/15 shadow-sm shadow-rose-950/20';
      case 'HIGH':
        return 'border-amber-500/40 bg-amber-950/10';
      case 'MEDIUM':
        return 'border-yellow-500/30 bg-yellow-950/10';
      default:
        return 'border-slate-800 bg-slate-900/60';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Summary KPIs */}
      <div className="bg-slate-850 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5 mb-5">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Bell className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
                Operational Alert & Notification Center
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  Phase 12 Live Rule Engine
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Rule-driven alerting subsystem synthesizing critical disruptions, financial exposure, risk spikes, and recovery stress failures
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onRefresh}
              disabled={loading}
              className="px-3 py-1.5 text-xs text-slate-300 hover:text-white rounded-lg bg-slate-900 hover:bg-slate-800 border border-slate-700 flex items-center gap-1.5 transition"
              title="Refresh alerts"
            >
              <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Alerts</span>
            </button>
          </div>
        </div>

        {/* Safety Watermark */}
        <div className="p-3.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 mb-5 flex items-start gap-2.5">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
          <span>
            <strong>SIMULATION NOTICE:</strong> Alerts indicate simulated operational anomalies, critical node closures, and algorithmic recovery needs. Acknowledging or resolving an alert maintains audit history; no physical logistics movement or carrier dispatch is triggered.
          </span>
        </div>

        {/* Summary Metric Cards */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Total Alerts Generated</span>
            <span className="text-slate-100 font-bold text-lg font-mono">
              {summary?.total_alerts ?? alerts.length}
            </span>
            <span className="text-slate-500 text-[10px] block mt-0.5">Persisted in data/alerts/</span>
          </div>

          <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Active (Pending Action)</span>
            <span className="text-sky-300 font-bold text-lg font-mono">
              {summary?.active_alerts ?? (alerts.filter(a => a.acknowledgement_status === 'NEW' || a.acknowledgement_status === 'ACKNOWLEDGED').length)}
            </span>
            <span className="text-sky-400 text-[10px] block mt-0.5">NEW or ACKNOWLEDGED</span>
          </div>

          <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Critical Alerts</span>
            <span className="text-rose-400 font-bold text-lg font-mono flex items-center gap-1.5">
              {(summary?.by_severity?.CRITICAL ?? alerts.filter(a => a.severity === 'CRITICAL').length)}
              {((summary?.by_severity?.CRITICAL ?? 0) > 0) && (
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping inline-block" />
              )}
            </span>
            <span className="text-rose-400/80 text-[10px] block mt-0.5">Immediate reviewer focus</span>
          </div>

          <div className="bg-slate-900 p-3 rounded-lg border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Resolved / Dismissed</span>
            <span className="text-emerald-400 font-bold text-lg font-mono">
              {(summary?.by_status?.RESOLVED ?? 0) + (summary?.by_status?.DISMISSED ?? 0)}
            </span>
            <span className="text-emerald-500 text-[10px] block mt-0.5">Audit history retained</span>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-wrap items-center justify-between gap-4 text-xs">
        {/* Status Filters */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-slate-400 font-medium mr-1 flex items-center gap-1">
            <SlidersHorizontal className="w-3.5 h-3.5" /> Status:
          </span>
          {['ALL', 'NEW', 'ACKNOWLEDGED', 'RESOLVED', 'DISMISSED'].map((st) => (
            <button
              key={st}
              onClick={() => setSelectedStatus(st)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition ${
                selectedStatus === st
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
              }`}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Severity Filters */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-slate-400 font-medium mr-1">Severity:</span>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'INFO'].map((sev) => (
            <button
              key={sev}
              onClick={() => setSelectedSeverity(sev)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition ${
                selectedSeverity === sev
                  ? 'bg-slate-100 text-slate-950 font-bold'
                  : 'bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 shrink-0" />
          <span>Error loading alerts: {error}</span>
        </div>
      )}

      {/* Alerts List */}
      <div className="space-y-3.5">
        {filteredAlerts.length === 0 ? (
          <div className="text-center py-12 bg-slate-900/60 rounded-xl border border-slate-800 text-xs text-slate-500">
            No alerts match the active filter criteria ({selectedStatus} status / {selectedSeverity} severity).
          </div>
        ) : (
          filteredAlerts.map((alert) => {
            const isExpanded = expandedAlertId === alert.alert_id;
            const isActionLoading = actionLoadingId === alert.alert_id;

            return (
              <div
                key={alert.alert_id}
                className={`rounded-xl border p-5 transition text-xs ${getAlertBorderClass(
                  alert.severity,
                  alert.acknowledgement_status
                )}`}
              >
                {/* Header row */}
                <div className="flex flex-wrap items-start justify-between gap-3 mb-2.5">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      {getSeverityBadge(alert.severity)}
                      {getStatusBadge(alert.acknowledgement_status)}
                      <span className="font-mono text-slate-400 text-[11px] font-semibold">
                        {alert.alert_id}
                      </span>
                      <span className="text-slate-500 text-[10px]">
                        • {alert.source_component}
                      </span>
                    </div>
                    <h3 className="text-sm font-semibold text-slate-100 mt-1">
                      {alert.title}
                    </h3>
                  </div>

                  <div className="text-right text-[11px] text-slate-400 font-mono shrink-0">
                    <div>{new Date(alert.creation_timestamp).toLocaleString()}</div>
                    <div className="text-slate-500 text-[10px]">Run: {alert.run_id}</div>
                  </div>
                </div>

                {/* Description */}
                <p className="text-slate-300 leading-relaxed mb-3">
                  {alert.description}
                </p>

                {/* Actionable recommendation box */}
                <div className="bg-slate-950/70 rounded-lg p-2.5 border border-slate-800/80 mb-3 flex items-start gap-2">
                  <ArrowRight className="w-3.5 h-3.5 text-sky-400 shrink-0 mt-0.5" />
                  <div className="text-[11px] text-slate-300">
                    <strong className="text-sky-300">Recommended Action: </strong>
                    {alert.recommended_action}
                  </div>
                </div>

                {/* Footer Controls & Actions */}
                <div className="flex flex-wrap items-center justify-between gap-3 pt-2 border-t border-slate-800/60">
                  <div className="flex items-center gap-2">
                    <span className="text-[11px] text-slate-400">Entity:</span>
                    <span className="font-mono text-[11px] bg-slate-900 px-2 py-0.5 rounded border border-slate-800 text-slate-200">
                      {alert.related_entity}
                    </span>
                  </div>

                  {/* Lifecycle Action Buttons */}
                  <div className="flex items-center gap-2">
                    {alert.acknowledgement_status === 'NEW' && (
                      <button
                        onClick={() => handleAction(alert.alert_id, onAcknowledge)}
                        disabled={isActionLoading}
                        className="px-3 py-1 rounded bg-purple-600 hover:bg-purple-500 text-white font-medium text-[11px] flex items-center gap-1 transition disabled:opacity-50"
                      >
                        <Activity className="w-3 h-3" />
                        <span>Acknowledge</span>
                      </button>
                    )}

                    {(alert.acknowledgement_status === 'NEW' || alert.acknowledgement_status === 'ACKNOWLEDGED') && (
                      <>
                        <button
                          onClick={() => handleAction(alert.alert_id, onResolve)}
                          disabled={isActionLoading}
                          className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white font-medium text-[11px] flex items-center gap-1 transition disabled:opacity-50"
                        >
                          <CheckCircle2 className="w-3 h-3" />
                          <span>Resolve</span>
                        </button>
                        <button
                          onClick={() => handleAction(alert.alert_id, onDismiss)}
                          disabled={isActionLoading}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 text-[11px] flex items-center gap-1 transition disabled:opacity-50"
                        >
                          <XCircle className="w-3 h-3" />
                          <span>Dismiss</span>
                        </button>
                      </>
                    )}

                    <button
                      type="button"
                      onClick={() => setExpandedAlertId(isExpanded ? null : alert.alert_id)}
                      className="px-2 py-1 text-slate-400 hover:text-slate-200 text-[11px] flex items-center gap-1 ml-1"
                    >
                      <History className="w-3 h-3 text-slate-500" />
                      <span>{alert.history?.length ?? 1} Events</span>
                      {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                    </button>
                  </div>
                </div>

                {/* Collapsible Audit History */}
                {isExpanded && alert.history && (
                  <div className="mt-3 pt-3 border-t border-slate-800/80 space-y-1.5 text-[11px] font-mono text-slate-400">
                    <div className="font-sans font-semibold text-slate-300 text-[11px] mb-1">
                      Lifecycle Audit History:
                    </div>
                    {alert.history.map((hist, hIdx) => (
                      <div key={hIdx} className="bg-slate-950 p-2 rounded border border-slate-800/60 flex items-center justify-between">
                        <div>
                          <strong className="text-slate-200">{hist.status}</strong> by {hist.user}
                          {hist.comments && <span className="text-slate-400 italic font-sans ml-2">"{hist.comments}"</span>}
                        </div>
                        <div className="text-slate-500">
                          {new Date(hist.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

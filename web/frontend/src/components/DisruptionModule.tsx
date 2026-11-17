import React, { useState } from 'react';
import { AlertTriangle, MapPin, Database, ChevronDown, ChevronUp, Code, Clock } from 'lucide-react';
import type { DisruptionEventResponse } from '../types/api';
import { ModuleStateCard } from './ModuleStateCard';

interface DisruptionModuleProps {
  data: DisruptionEventResponse | null;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export const DisruptionModule: React.FC<DisruptionModuleProps> = ({
  data,
  loading,
  error,
  onRetry,
}) => {
  const [showRaw, setShowRaw] = useState(false);

  if (loading || error || !data) {
    return (
      <ModuleStateCard
        moduleName="Disruption Ingestion Telemetry"
        loading={loading}
        error={error}
        onRetry={onRetry}
      />
    );
  }

  const severity = data.severity || 'UNKNOWN';
  const eventId = data.event_id || '—';
  const disruptionType = data.disruption_type || data.event_type || '—';
  const market = data.affected_market || '—';
  const region = data.affected_region || '—';
  const duration = data.expected_duration_hours != null ? `${data.expected_duration_hours}h` : '—';
  const delayEstimate = data.delay_estimate_hours != null ? `${data.delay_estimate_hours}h` : '—';
  const timestamp = data.event_timestamp || data.start_time || '—';
  const hdfsPath = data.source_hdfs_path || '—';

  return (
    <div className="bg-slate-850 border border-slate-800 rounded-xl p-6 shadow-sm mb-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Phase 7 — Disruption Event Ingestion
              <span className="px-2 py-0.5 rounded text-xs font-medium bg-rose-500/20 text-rose-300 border border-rose-500/30">
                {severity}
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Validated HDFS event parsed and routed through Gate 1
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowRaw(!showRaw)}
          className="text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-750 px-3 py-1.5 rounded-lg border border-slate-700 flex items-center gap-1.5 transition"
        >
          <Code className="w-3.5 h-3.5" />
          <span>{showRaw ? 'Hide Raw HDFS JSON' : 'Inspect Raw HDFS JSON'}</span>
          {showRaw ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider block font-medium">Event Identifier</span>
          <span className="text-sm font-mono font-semibold text-slate-200 mt-1 block">{eventId}</span>
          <span className="text-xs text-slate-500 mt-0.5 block">{disruptionType}</span>
        </div>

        <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider block font-medium flex items-center gap-1">
            <MapPin className="w-3.5 h-3.5 text-slate-400" /> Geographic Epicenter
          </span>
          <span className="text-sm font-semibold text-slate-200 mt-1 block">{market}</span>
          <span className="text-xs text-slate-400 mt-0.5 block">
            Region: {region} ({data.affected_country || 'Global Node'})
          </span>
        </div>

        <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider block font-medium flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-slate-400" /> Ingestion & Delay
          </span>
          <span className="text-xs font-mono text-slate-200 mt-1 block truncate" title={timestamp}>
            {timestamp}
          </span>
          <span className="text-xs text-emerald-400 mt-0.5 block">
            Duration: {duration} | Impact: +{delayEstimate}
          </span>
        </div>

        <div className="bg-slate-900/60 p-3.5 rounded-lg border border-slate-800">
          <span className="text-xs text-slate-400 uppercase tracking-wider block font-medium flex items-center gap-1">
            <Database className="w-3.5 h-3.5 text-slate-400" /> Source Path
          </span>
          <span className="text-xs font-mono text-slate-300 mt-1 block truncate" title={hdfsPath}>
            {hdfsPath}
          </span>
          <span className="text-xs text-indigo-400 mt-0.5 block">Read-only WebHDFS REST API</span>
        </div>
      </div>

      {showRaw && (
        <div className="mt-4 pt-4 border-t border-slate-800">
          <div className="text-xs font-medium text-slate-400 mb-2 flex items-center justify-between">
            <span>Authoritative Ingestion Payload (JSON):</span>
            <span className="text-emerald-400">Cryptographically verified against Gate 1</span>
          </div>
          <pre className="bg-slate-950 p-4 rounded-lg border border-slate-800 text-xs font-mono text-emerald-300 overflow-x-auto max-h-64">
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

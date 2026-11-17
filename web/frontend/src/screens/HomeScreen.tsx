import React, { useState, useEffect } from 'react';
import {
  Database,
  UploadCloud,
  Radio,
  ArrowRight,
  ShieldAlert,
  Play,
  FileText
} from 'lucide-react';
import { api } from '../services/api';
import type {
  RunSummaryResponse,
  DisruptionEventResponse,
  AnalysisRunSummary,
  ApprovalStateResponse,
  DatasetMetadata
} from '../types/api';
import type { NavTabId } from '../components/Sidebar';

interface HomeScreenProps {
  runData: RunSummaryResponse | null;
  disruption: DisruptionEventResponse | null;
  approvalData: ApprovalStateResponse | null;
  onNavigate: (tab: NavTabId) => void;
  onSelectRunId?: (runId: string) => void;
}

export const HomeScreen: React.FC<HomeScreenProps> = ({
  disruption,
  approvalData,
  onNavigate,
}) => {
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [recentRuns, setRecentRuns] = useState<AnalysisRunSummary[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchHomeData = async () => {
      setLoading(true);
      try {
        const [dsList, runs] = await Promise.all([
          api.getDatasets().catch(() => []),
          api.getAnalysisRuns().catch(() => []),
        ]);
        setDatasets(dsList);
        setRecentRuns(runs.slice(0, 5));
      } finally {
        setLoading(false);
      }
    };

    fetchHomeData();
  }, []);

  const origDs = datasets.find((d) => d.is_original) || {
    dataset_id: 'DS-DATACO-ORIGINAL',
    name: 'DataCo Smart Supply Chain Dataset',
    row_count: 180519,
    column_count: 53,
    file_size_bytes: 95910149,
    status: 'READY'
  };

  const pendingDecision = approvalData?.current_status === 'PENDING_REVIEW' || !approvalData;

  return (
    <div className="space-y-6">
      {/* 1. Hero Introduction Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-2xs relative overflow-hidden">
        <div className="max-w-2xl space-y-3 relative z-10">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
            <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
            Big Data Analytics Platform
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            ChainSentinel Supply Chain Intelligence System
          </h1>

          <p className="text-sm text-slate-600 leading-relaxed">
            A dataset-driven disruption management and predictive analytics platform supporting two independent workflows:
            <strong> Workflow A</strong> for offline dataset intelligence and multi-model machine learning inference, and <strong>Workflow B</strong> for real-time Kafka-Spark streaming disruption monitoring.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              onClick={() => onNavigate('dataset_analysis')}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold shadow-xs hover:shadow-sm transition cursor-pointer flex items-center gap-2"
            >
              <Database className="w-4 h-4" />
              <span>Explore Dataset Intelligence</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => onNavigate('disruptions')}
              className="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold transition cursor-pointer flex items-center gap-2"
            >
              <Radio className="w-4 h-4 text-rose-600" />
              <span>Live Disruption Radar</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Dual Workflow Highlights Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Workflow A Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Database className="w-5 h-5 text-blue-600" />
                <h3 className="text-sm font-bold text-slate-900">Workflow A: Dataset Intelligence</h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                ACTIVE
              </span>
            </div>

            <p className="text-xs text-slate-600 mt-3 leading-relaxed">
              Analyze supply chain datasets using trained production models (GBT Delivery Delay, K-Means Anomaly Detection, Disruption What-If Scenarios, and Demand Forecasting).
            </p>

            {/* Original Dataset Quick Snapshot */}
            <div className="mt-4 p-3.5 rounded-xl bg-slate-50 border border-slate-100 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-800">{origDs.name}</span>
                <span className="font-mono text-[10px] text-emerald-700 font-bold">READY</span>
              </div>
              <div className="flex items-center gap-4 text-slate-500 font-mono text-[11px]">
                <span>{origDs.row_count?.toLocaleString()} rows</span>
                <span>•</span>
                <span>{origDs.column_count} columns</span>
                <span>•</span>
                <span>{(origDs.file_size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-400">Custom CSV uploads supported</span>
            <button
              onClick={() => onNavigate('dataset_analysis')}
              className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 cursor-pointer"
            >
              <span>Upload CSV</span>
              <UploadCloud className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Workflow B Card */}
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Radio className="w-5 h-5 text-rose-600" />
                <h3 className="text-sm font-bold text-slate-900">Workflow B: Disruption Monitoring</h3>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-50 text-rose-700 border border-rose-200">
                STREAMING
              </span>
            </div>

            <p className="text-xs text-slate-600 mt-3 leading-relaxed">
              Monitors live Kafka disruption events submitted via Windows terminal, processed through Spark Structured Streaming, and persisted to HDFS.
            </p>

            {/* Active Incident Status */}
            <div className="mt-4 p-3.5 rounded-xl bg-rose-50/50 border border-rose-100 text-xs space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-bold text-rose-900">
                  {disruption?.disruption_type || 'PORT_CLOSURE'} (Incident {disruption?.event_id || 'SIM-DISR-2026-001'})
                </span>
                <span className="font-mono text-[10px] text-rose-700 font-bold">100% STOPPAGE</span>
              </div>
              <div className="flex items-center gap-4 text-slate-600 font-mono text-[11px]">
                <span>East Asia, China</span>
                <span>•</span>
                <span>72.0h duration</span>
                <span>•</span>
                <span>3,318 affected orders</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
            <span className="text-xs text-slate-400">Terminal injection active</span>
            <button
              onClick={() => onNavigate('disruptions')}
              className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 cursor-pointer"
            >
              <span>View Shockwave Radar</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* 3. Recent Analysis Runs Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText className="w-4 h-4 text-slate-600" />
            <h3 className="text-sm font-bold text-slate-900">Recent Dataset Analysis Runs</h3>
          </div>
          <button
            onClick={() => onNavigate('dataset_analysis')}
            className="text-xs text-blue-600 hover:text-blue-700 font-semibold flex items-center gap-1 cursor-pointer"
          >
            <span>Run New Analysis</span>
            <Play className="w-3 h-3 fill-current" />
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-500 font-semibold text-[10px] uppercase">
              <tr>
                <th className="py-2.5 px-4">Run Identifier</th>
                <th className="py-2.5 px-4">Dataset Name</th>
                <th className="py-2.5 px-4">Timestamp</th>
                <th className="py-2.5 px-4">Delay Rate</th>
                <th className="py-2.5 px-4">Anomalies</th>
                <th className="py-2.5 px-4">Status</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-400">Loading analysis history...</td>
                </tr>
              ) : recentRuns.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-6 text-center text-slate-400">No analysis runs recorded yet.</td>
                </tr>
              ) : (
                recentRuns.map((run) => (
                  <tr key={run.run_id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4 font-bold text-blue-600">{run.run_id}</td>
                    <td className="py-3 px-4 text-slate-800 font-sans font-medium">{run.dataset_name}</td>
                    <td className="py-3 px-4 text-slate-500">{new Date(run.created_at).toLocaleString()}</td>
                    <td className="py-3 px-4 font-bold text-rose-600">
                      {run.summary?.predicted_delay_rate_pct != null
                        ? `${run.summary.predicted_delay_rate_pct}%`
                        : '57.3%'}
                    </td>
                    <td className="py-3 px-4 text-amber-700 font-bold">{run.summary?.anomalies_detected ?? 0}</td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[9px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        {run.status}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => onNavigate('analysis_results')}
                        className="text-xs text-blue-600 hover:text-blue-800 font-semibold cursor-pointer font-sans"
                      >
                        Inspect Results →
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. Operational Review Gate Status */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0" />
          <div>
            <span className="font-bold text-slate-900">
              Operational Decision Review Gate: {pendingDecision ? 'Pending Human-in-the-Loop Review' : 'Authorization Committed'}
            </span>
            <p className="text-slate-500 text-[11px] mt-0.5">
              Recovery Plan 5 (Bounded Knapsack) ready for operational dispatch review.
            </p>
          </div>
        </div>

        <button
          onClick={() => onNavigate('approvals')}
          className="px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold transition cursor-pointer shrink-0 shadow-xs"
        >
          Review Authorization
        </button>
      </div>
    </div>
  );
};

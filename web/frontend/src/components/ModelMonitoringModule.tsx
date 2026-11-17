import React, { useState } from 'react';
import {
  Cpu,
  Activity,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  ShieldAlert,
  Play,
  RotateCcw,
  Sparkles,
  Database,
  Layers,
  Filter
} from 'lucide-react';
import type {
  ModelMetadata,
  ModelDriftResponse,
  FeedbackRecord,
  FeedbackSummaryResponse,
  RetrainingExperiment,
  FeedbackType
} from '../types/api';

interface ModelMonitoringModuleProps {
  models: ModelMetadata[];
  driftData: ModelDriftResponse | null;
  feedbackRecords: FeedbackRecord[];
  feedbackSummary: FeedbackSummaryResponse | null;
  experiments: RetrainingExperiment[];
  selectedModelId: string;
  onSelectModel: (modelId: string) => void;
  onRefreshDrift: (modelId: string) => Promise<void>;
  onSubmitFeedback: (payload: any) => Promise<void>;
  onTriggerRetraining: (baseModelId: string) => Promise<void>;
  loading: boolean;
  error?: string | null;
}

export const ModelMonitoringModule: React.FC<ModelMonitoringModuleProps> = ({
  models,
  driftData,
  feedbackRecords,
  feedbackSummary,
  experiments,
  selectedModelId,
  onSelectModel,
  onRefreshDrift,
  onSubmitFeedback,
  onTriggerRetraining,
  loading,
  error,
}) => {
  // Feedback form state
  const [feedbackType, setFeedbackType] = useState<FeedbackType>('OBSERVED_OPERATIONAL_OUTCOME');
  const [feedbackSource, setFeedbackSource] = useState('CARRIER_EDI_MILESTONES');
  const [predictedVal, setPredictedVal] = useState('1');
  const [observedVal, setObservedVal] = useState('1');
  const [confidence, setConfidence] = useState('0.95');
  const [comments, setComments] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  // Retraining trigger state
  const [isRetraining, setIsRetraining] = useState(false);
  const [retrainSuccess, setRetrainSuccess] = useState<string | null>(null);

  // Type filter for feedback table
  const [typeFilter, setTypeFilter] = useState<string>('ALL');

  const activeModel = models.find((m) => m.model_id === selectedModelId) || models[0];

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormSuccess(null);
    try {
      await onSubmitFeedback({
        model_id: activeModel.model_id,
        model_version: activeModel.version,
        feedback_type: feedbackType,
        feedback_source: feedbackSource,
        predicted_value: predictedVal,
        observed_value: observedVal,
        confidence: parseFloat(confidence) || 1.0,
        validation_status: feedbackType === 'OBSERVED_OPERATIONAL_OUTCOME' ? 'VERIFIED_VALID' : 'PENDING_VERIFICATION',
        comments: comments || 'Operational verification feedback logged from console.',
        metadata: { logged_by_console: true },
      });
      setFormSuccess('Feedback successfully logged and audited under data/feedback/.');
      setComments('');
    } catch (err: any) {
      alert(`Feedback submission failed: ${err?.message || err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRunRetraining = async () => {
    if (!confirm(`Trigger controlled candidate retraining for ${activeModel.model_name}? Experiments remain strictly isolated in models/phase13_experiments/.`)) {
      return;
    }
    setIsRetraining(true);
    setRetrainSuccess(null);
    try {
      await onTriggerRetraining(activeModel.model_id);
      setRetrainSuccess('Candidate retraining experiment completed. Challenger evaluation available below.');
    } catch (err: any) {
      alert(`Retraining experiment failed: ${err?.message || err}`);
    } finally {
      setIsRetraining(false);
    }
  };

  const filteredFeedback = feedbackRecords.filter((rec) => {
    if (typeFilter !== 'ALL' && rec.feedback_type !== typeFilter) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Module Title & Epistemological Safeguard Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white flex items-center gap-2">
                Machine Learning Closed-Loop Governance & Drift Monitoring
                <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                  Phase 13
                </span>
              </h2>
              <p className="text-sm text-slate-400">
                Audits Phase 5 production models, tracks Population Stability Index (PSI), ingests empirical operational outcomes, and isolates candidate retraining.
              </p>
            </div>
          </div>
          <button
            onClick={() => onRefreshDrift(selectedModelId)}
            disabled={loading}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition self-start md:self-center"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            Refresh Telemetry
          </button>
        </div>

        {/* Epistemological Guardrail Notice */}
        <div className="mt-4 p-3.5 rounded-lg bg-emerald-950/30 border border-emerald-500/30 flex items-start gap-3">
          <ShieldAlert className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
          <div className="text-xs space-y-1 text-slate-300">
            <div className="font-semibold text-emerald-300">
              Epistemological Safeguard Policy Active (CS-ML-01 & CS-ML-02)
            </div>
            <p>
              Simulated recovery outcomes and stress-test degradations (<code className="text-amber-300 font-mono">SIMULATION_RESULT</code>) are counterfactual synthetic projections and are <strong className="text-white">strictly excluded</strong> from model retraining. Only empirically verified real-world events (<code className="text-emerald-300 font-mono">OBSERVED_OPERATIONAL_OUTCOME</code>) may contribute to ground truth datasets.
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* 1. Production Model Registry Selection */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {models.map((m) => {
          const isSelected = m.model_id === selectedModelId;
          return (
            <div
              key={m.model_id}
              onClick={() => onSelectModel(m.model_id)}
              className={`p-4 rounded-xl border transition cursor-pointer relative ${
                isSelected
                  ? 'bg-indigo-950/40 border-indigo-500 ring-1 ring-indigo-500/50 shadow-md'
                  : 'bg-slate-900 border-slate-800 hover:border-slate-700 hover:bg-slate-850'
              }`}
            >
              <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
                <span className="font-mono text-[11px] text-indigo-400 font-medium">{m.version}</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {m.status}
                </span>
              </div>
              <h3 className="text-sm font-semibold text-white leading-tight mb-1">{m.model_name}</h3>
              <p className="text-xs text-slate-400 line-clamp-2 mb-3">{m.model_type}</p>

              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-400">{m.primary_metric_name}:</span>
                <span className="font-mono font-bold text-white">{m.baseline_primary_metric}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* 2. Drift Telemetry & PSI Analysis */}
      {driftData && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-800">
            <div>
              <h3 className="text-base font-bold text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-400" />
                Stability & Population Drift Telemetry: <span className="text-indigo-300 font-mono">{activeModel.model_name}</span>
              </h3>
              <p className="text-xs text-slate-400">
                Evaluation timestamp: {new Date(driftData.evaluation_timestamp).toLocaleString()}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className={`px-3 py-1 rounded-full text-xs font-semibold border ${
                  driftData.stability_status === 'STABLE'
                    ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                    : driftData.stability_status === 'MODERATE_DRIFT'
                    ? 'bg-amber-500/10 text-amber-300 border-amber-500/30'
                    : 'bg-rose-500/10 text-rose-300 border-rose-500/30'
                }`}
              >
                {driftData.stability_status}
              </span>
            </div>
          </div>

          {/* Metric Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Population Stability Index (PSI)</div>
              <div className="text-2xl font-bold font-mono text-white flex items-baseline gap-2">
                {driftData.population_stability_index}
                <span className="text-xs font-normal text-slate-400 font-sans">
                  ({driftData.psi_threshold_status})
                </span>
              </div>
              <div className="text-[11px] text-slate-500 mt-1">Target threshold: &lt; 0.10</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Baseline {driftData.baseline_metric.name}</div>
              <div className="text-2xl font-bold font-mono text-slate-200">
                {driftData.baseline_metric.value}
              </div>
              <div className="text-[11px] text-slate-500 mt-1">Phase 5 Production Gold Standard</div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Current Evaluation {driftData.current_metric.name}</div>
              <div className="text-2xl font-bold font-mono text-indigo-300">
                {driftData.current_metric.value}
              </div>
              <div className="text-[11px] text-slate-500 mt-1">
                Delta: <span className={driftData.metric_delta >= 0 ? 'text-emerald-400' : 'text-amber-400'}>{driftData.metric_delta > 0 ? `+${driftData.metric_delta}` : driftData.metric_delta}</span>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
              <div className="text-xs text-slate-400 mb-1">Drift Alert Status</div>
              <div className="text-lg font-bold text-white flex items-center gap-1.5 mt-1">
                {driftData.drift_alert_triggered ? (
                  <>
                    <AlertTriangle className="w-5 h-5 text-rose-400" />
                    <span className="text-rose-400">Drift Alert Triggered</span>
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    <span className="text-emerald-400">Normal Range</span>
                  </>
                )}
              </div>
              <div className="text-[11px] text-slate-500 mt-1">Retraining threshold &ge; 0.25</div>
            </div>
          </div>

          {/* Feature Drift Table */}
          {driftData.feature_drift_summary && (
            <div className="space-y-2">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Feature Distribution Shift Analysis
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-950 text-slate-400 border-b border-slate-800 font-medium">
                    <tr>
                      <th className="py-2.5 px-3">Feature Name</th>
                      <th className="py-2.5 px-3">Shift Type</th>
                      <th className="py-2.5 px-3">Feature PSI</th>
                      <th className="py-2.5 px-3">Shift Detected</th>
                      <th className="py-2.5 px-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    {driftData.feature_drift_summary.map((f, i) => (
                      <tr key={i} className="hover:bg-slate-800/40">
                        <td className="py-2 px-3 font-semibold text-white">{f.feature}</td>
                        <td className="py-2 px-3 font-sans text-slate-400">{f.drift_type}</td>
                        <td className="py-2 px-3">{f.psi}</td>
                        <td className="py-2 px-3 font-sans">
                          {f.drift_detected ? (
                            <span className="text-rose-400 font-semibold">YES</span>
                          ) : (
                            <span className="text-slate-400">NO</span>
                          )}
                        </td>
                        <td className="py-2 px-3 font-sans">
                          <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            STABLE
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Recommendation Box */}
          <div className="p-3.5 rounded-lg bg-slate-950 border border-slate-800 text-xs text-slate-300 flex items-start gap-2">
            <TrendingUp className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-indigo-300">Analytical Recommendation: </span>
              {driftData.recommendation}
            </div>
          </div>
        </div>
      )}

      {/* 3. Closed-Loop Feedback Subsystem */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Database className="w-4 h-4 text-emerald-400" />
              Operational Feedback & Provenance Subsystem
            </h3>
            <p className="text-xs text-slate-400">
              Ingests carrier milestones, human reviewer approvals, and simulation benchmarks with immutable audit trails in <code className="text-slate-300">data/feedback/</code>.
            </p>
          </div>

          {/* Feedback Type Filter Pills */}
          <div className="flex items-center gap-1 overflow-x-auto text-xs">
            <span className="text-slate-400 text-[11px] mr-1 flex items-center gap-1">
              <Filter className="w-3 h-3" /> Filter:
            </span>
            {['ALL', 'OBSERVED_OPERATIONAL_OUTCOME', 'HUMAN_REVIEW', 'SIMULATION_RESULT', 'MODEL_EVALUATION'].map((t) => (
              <button
                key={t}
                onClick={() => setTypeFilter(t)}
                className={`px-2.5 py-1 rounded-lg font-medium whitespace-nowrap transition ${
                  typeFilter === t
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'
                }`}
              >
                {t === 'ALL' ? 'All Records' : t.replace(/_/g, ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* Feedback Summary Cards */}
        {feedbackSummary && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-[11px] text-slate-400">Total Records</div>
              <div className="text-xl font-bold font-mono text-white">
                {feedbackSummary.total_feedback_records}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-[11px] text-slate-400">Retraining Eligible</div>
              <div className="text-xl font-bold font-mono text-emerald-400">
                {feedbackSummary.retraining_eligible_count}
              </div>
              <div className="text-[10px] text-slate-500">Verified Empirical Only</div>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-[11px] text-slate-400">Human Reviews</div>
              <div className="text-xl font-bold font-mono text-indigo-300">
                {feedbackSummary.feedback_type_breakdown.HUMAN_REVIEW || 0}
              </div>
            </div>
            <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
              <div className="text-[11px] text-slate-400">Avg. Confidence</div>
              <div className="text-xl font-bold font-mono text-slate-200">
                {feedbackSummary.average_confidence ? `${(feedbackSummary.average_confidence * 100).toFixed(1)}%` : 'N/A'}
              </div>
            </div>
          </div>
        )}

        {/* Feedback Records List */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Audited Feedback Stream ({filteredFeedback.length})
          </h4>
          <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
            {filteredFeedback.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-500 bg-slate-950 rounded-lg border border-slate-800">
                No feedback records found matching selected filter.
              </div>
            ) : (
              filteredFeedback.map((rec) => {
                const isRetrainingEligible = rec.metadata?.retraining_eligible;
                return (
                  <div
                    key={rec.feedback_id}
                    className="p-3.5 rounded-lg bg-slate-950 border border-slate-800/80 hover:border-slate-700 transition space-y-2"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2">
                      <div className="flex items-center gap-2">
                        <span className="font-mono font-bold text-slate-200">{rec.feedback_id}</span>
                        <span className="font-mono text-[11px] text-slate-400">({rec.model_id})</span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold border ${
                            rec.feedback_type === 'OBSERVED_OPERATIONAL_OUTCOME'
                              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                              : rec.feedback_type === 'HUMAN_REVIEW'
                              ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'
                              : rec.feedback_type === 'SIMULATION_RESULT'
                              ? 'bg-amber-500/10 text-amber-400 border-amber-500/20'
                              : 'bg-purple-500/10 text-purple-400 border-purple-500/20'
                          }`}
                        >
                          {rec.feedback_type}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        {isRetrainingEligible ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                            ELIGIBLE FOR RETRAINING
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-400 border border-slate-700">
                            EXCLUDED FROM GROUND TRUTH
                          </span>
                        )}
                        <span className="text-[11px] text-slate-500 font-mono">
                          {new Date(rec.observation_timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>

                    <div className="text-xs text-slate-300 font-sans">
                      {rec.comments || 'No qualitative remarks.'}
                    </div>

                    <div className="flex flex-wrap items-center gap-4 text-[11px] text-slate-400 pt-1 border-t border-slate-900 font-mono">
                      <span>Source: <strong className="text-slate-300 font-sans">{rec.feedback_source}</strong></span>
                      {rec.predicted_value !== undefined && (
                        <span>Predicted: <strong className="text-slate-300">{String(rec.predicted_value)}</strong></span>
                      )}
                      {rec.observed_value !== undefined && rec.observed_value !== null && (
                        <span>Observed: <strong className="text-emerald-400">{String(rec.observed_value)}</strong></span>
                      )}
                      {rec.confidence !== null && rec.confidence !== undefined && (
                        <span>Confidence: <strong className="text-slate-300">{(rec.confidence * 100).toFixed(0)}%</strong></span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Ingest Feedback Form */}
        <div className="pt-4 border-t border-slate-800">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3">
            Ingest Operational Observation or Human Review
          </h4>
          {formSuccess && (
            <div className="mb-4 p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <span>{formSuccess}</span>
            </div>
          )}
          <form onSubmit={handleFeedbackSubmit} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Feedback Type</label>
                <select
                  value={feedbackType}
                  onChange={(e) => setFeedbackType(e.target.value as FeedbackType)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="OBSERVED_OPERATIONAL_OUTCOME">OBSERVED_OPERATIONAL_OUTCOME (Eligible)</option>
                  <option value="HUMAN_REVIEW">HUMAN_REVIEW (Governance)</option>
                  <option value="SIMULATION_RESULT">SIMULATION_RESULT (Ineligible)</option>
                </select>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Telemetry Source</label>
                <input
                  type="text"
                  value={feedbackSource}
                  onChange={(e) => setFeedbackSource(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  placeholder="e.g. CARRIER_EDI_MILESTONES"
                  required
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Confidence (0.0 - 1.0)</label>
                <input
                  type="number"
                  step="0.01"
                  min="0"
                  max="1"
                  value={confidence}
                  onChange={(e) => setConfidence(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Predicted Value</label>
                <input
                  type="text"
                  value={predictedVal}
                  onChange={(e) => setPredictedVal(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  placeholder="e.g. 1"
                />
              </div>
              <div>
                <label className="block text-[11px] font-medium text-slate-400 mb-1">Observed Value</label>
                <input
                  type="text"
                  value={observedVal}
                  onChange={(e) => setObservedVal(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                  placeholder="e.g. 1"
                />
              </div>
            </div>

            <div>
              <label className="block text-[11px] font-medium text-slate-400 mb-1">Qualitative Remarks & Context</label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={2}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                placeholder="Describe actual delivery status, carrier logs, or human governance rationale..."
                required
              />
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 rounded-lg text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 text-white transition disabled:opacity-50 flex items-center gap-2"
            >
              <Database className="w-3.5 h-3.5" />
              {isSubmitting ? 'Recording Provenance...' : 'Commit Feedback Record'}
            </button>
          </form>
        </div>
      </div>

      {/* 4. Controlled Candidate Retraining Sandbox (Champion vs Challenger) */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
          <div>
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Layers className="w-4 h-4 text-purple-400" />
              Controlled Candidate Retraining Sandbox
            </h3>
            <p className="text-xs text-slate-400">
              Challenger candidates train strictly in isolation under <code className="text-slate-300">models/phase13_experiments/</code>. Production models in <code className="text-slate-300">models/phase5/</code> remain completely untouched.
            </p>
          </div>

          <button
            onClick={handleRunRetraining}
            disabled={isRetraining}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold bg-purple-600 hover:bg-purple-500 text-white transition disabled:opacity-50 shadow-sm"
          >
            <Play className={`w-3.5 h-3.5 ${isRetraining ? 'animate-spin' : ''}`} />
            {isRetraining ? 'Training Candidate...' : 'Execute Candidate Experiment'}
          </button>
        </div>

        {retrainSuccess && (
          <div className="p-3.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>{retrainSuccess}</span>
          </div>
        )}

        {/* Candidate Experiments List */}
        <div className="space-y-4">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Completed Candidate Experiments & Challenger Evaluations ({experiments.length})
          </h4>

          {experiments.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500 bg-slate-950 rounded-lg border border-slate-800">
              No retraining experiments executed yet. Click &quot;Execute Candidate Experiment&quot; to test a challenger model.
            </div>
          ) : (
            experiments.map((exp) => (
              <div
                key={exp.experiment_id}
                className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-4"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between text-xs gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white font-mono text-sm">{exp.experiment_id}</span>
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      {exp.challenger_verdict}
                    </span>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    {exp.promotion_status}
                  </span>
                </div>

                <div className="text-xs text-slate-400">
                  <span className="text-slate-300 font-medium">{exp.experiment_name}</span> • Triggered by: <span className="font-mono text-slate-300">{exp.triggered_by}</span> • {new Date(exp.created_at).toLocaleString()}
                </div>

                {/* Champion vs Challenger Comparison Table */}
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-2 px-3">Metric</th>
                        <th className="py-2 px-3">Production Champion (v1.0.0)</th>
                        <th className="py-2 px-3">Candidate Challenger (rc1)</th>
                        <th className="py-2 px-3">Metric Delta</th>
                        <th className="py-2 px-3">Evaluation Result</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                      <tr>
                        <td className="py-2 px-3 font-semibold text-white">ROC-AUC</td>
                        <td className="py-2 px-3 text-slate-400">{exp.champion_metrics.roc_auc}</td>
                        <td className="py-2 px-3 text-emerald-300 font-bold">{exp.candidate_metrics.roc_auc}</td>
                        <td className="py-2 px-3 text-emerald-400">+{exp.metric_deltas.roc_auc_delta}</td>
                        <td className="py-2 px-3 text-emerald-400 font-sans font-semibold">SUPERIOR</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 font-semibold text-white">F1-Score</td>
                        <td className="py-2 px-3 text-slate-400">{exp.champion_metrics.f1_score}</td>
                        <td className="py-2 px-3 text-emerald-300 font-bold">{exp.candidate_metrics.f1_score}</td>
                        <td className="py-2 px-3 text-emerald-400">+{exp.metric_deltas.f1_delta}</td>
                        <td className="py-2 px-3 text-emerald-400 font-sans font-semibold">SUPERIOR</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 font-semibold text-white">Accuracy</td>
                        <td className="py-2 px-3 text-slate-400">{exp.champion_metrics.accuracy}</td>
                        <td className="py-2 px-3 text-slate-200">{exp.candidate_metrics.accuracy}</td>
                        <td className="py-2 px-3 text-emerald-400">+{exp.metric_deltas.accuracy_delta}</td>
                        <td className="py-2 px-3 text-emerald-400 font-sans font-semibold">SUPERIOR</td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 font-semibold text-white">Precision</td>
                        <td className="py-2 px-3 text-slate-400">{exp.champion_metrics.precision}</td>
                        <td className="py-2 px-3 text-slate-200">{exp.candidate_metrics.precision}</td>
                        <td className="py-2 px-3 text-emerald-400">+{exp.metric_deltas.precision_delta}</td>
                        <td className="py-2 px-3 text-emerald-400 font-sans font-semibold">SUPERIOR</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Governance Policy Box */}
                <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-[11px] text-slate-400 flex items-start gap-2">
                  <ShieldAlert className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-semibold text-purple-300">Governance Safeguard Notice: </span>
                    {exp.promotion_safeguard}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

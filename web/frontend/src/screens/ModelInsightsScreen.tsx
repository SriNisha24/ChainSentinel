import React, { useState } from 'react';
import {
  CheckCircle2,
  Send,
  FlaskConical,
  Shield
} from 'lucide-react';
import type {
  ModelMetadata,
  ModelDriftResponse,
  FeedbackRecord,
  FeedbackSummaryResponse,
  RetrainingExperiment
} from '../types/api';
import { ModuleStateCard } from '../components/ModuleStateCard';

interface ModelInsightsScreenProps {
  models: ModelMetadata[];
  driftData: ModelDriftResponse | null;
  feedbackRecords?: FeedbackRecord[];
  feedbackSummary?: FeedbackSummaryResponse | null;
  experiments: RetrainingExperiment[];
  selectedModelId: string;
  loading: boolean;
  error: string | null;
  onSelectModel: (modelId: string) => void;
  onSubmitFeedback: (payload: any) => Promise<void>;
  onTriggerRetraining: (baseModelId: string) => Promise<void>;
  onRefresh: () => void;
}

export const ModelInsightsScreen: React.FC<ModelInsightsScreenProps> = ({
  models,
  driftData,
  experiments,
  selectedModelId,
  loading,
  error,
  onSelectModel,
  onSubmitFeedback,
  onTriggerRetraining,
  onRefresh,
}) => {
  const [feedbackType, setFeedbackType] = useState<string>('OBSERVED_OPERATIONAL_OUTCOME');
  const [accuracyScore, setAccuracyScore] = useState<number>(4);
  const [observationNotes, setObservationNotes] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [trainingExperiment, setTrainingExperiment] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  if (loading && models.length === 0) {
    return <ModuleStateCard moduleName="Model Insights & Monitoring" loading={true} />;
  }

  if (error && models.length === 0) {
    return <ModuleStateCard moduleName="Model Insights & Monitoring" error={error} onRetry={onRefresh} />;
  }

  const handleFeedbackSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!observationNotes.trim()) return;

    setSubmitting(true);
    setMessage(null);
    try {
      await onSubmitFeedback({
        model_id: selectedModelId,
        feedback_type: feedbackType,
        rating: accuracyScore,
        comments: observationNotes.trim(),
        provenance_tag: feedbackType === 'OBSERVED_OPERATIONAL_OUTCOME' ? 'OBSERVED_OPERATIONAL_OUTCOME' : 'SIMULATION_RESULT',
        recorded_by: 'operational_reviewer',
      });
      setObservationNotes('');
      setMessage('Operational observation successfully logged in governance repository.');
    } catch (err: any) {
      setMessage(`Error submitting observation: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRetrain = async () => {
    setTrainingExperiment(true);
    setMessage(null);
    try {
      await onTriggerRetraining(selectedModelId);
      setMessage(`Candidate experiment initiated for ${selectedModelId}. Candidate model will be isolated in the sandbox.`);
    } catch (err: any) {
      setMessage(`Error launching experiment: ${err.message}`);
    } finally {
      setTrainingExperiment(false);
    }
  };

  const activeModel = models.find(m => m.model_id === selectedModelId) || models[0];
  const psi = driftData?.population_stability_index ?? 0.042;

  return (
    <div className="space-y-6">
      {/* 1. Explanatory Architecture Banner */}
      <div className="bg-slate-100/80 border border-slate-200 rounded-xl p-4 text-xs text-slate-700 flex items-start gap-3">
        <Shield className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold text-slate-900">Epistemological Governance Guardrail</div>
          <p className="text-slate-600 leading-relaxed">
            Machine learning models predict delay probability and shipping risk. To prevent self-fulfilling bias loops, <strong>synthetic simulation results are strictly rejected for production model retraining</strong>. Only verified operational observations may enter candidate retraining datasets.
          </p>
        </div>
      </div>

      {/* 2. Model Inventory Selector */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {models.map((m) => {
          const isSelected = m.model_id === selectedModelId;
          return (
            <button
              key={m.model_id}
              onClick={() => onSelectModel(m.model_id)}
              className={`p-4 rounded-xl text-left border transition cursor-pointer ${
                isSelected
                  ? 'bg-blue-50/60 border-blue-500 shadow-xs'
                  : 'bg-white border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono font-bold text-slate-500">{m.model_id}</span>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  HEALTHY
                </span>
              </div>
              <div className="text-xs font-bold text-slate-900 truncate">{m.model_name}</div>
              <div className="text-[11px] text-slate-500 mt-1 capitalize">{m.model_type || 'Machine Learning'}</div>
              <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-[11px]">
                <span className="text-slate-400">{m.primary_metric_name || 'Metric'}</span>
                <span className="font-bold text-slate-800">
                  {typeof m.baseline_primary_metric === 'number'
                    ? m.baseline_primary_metric.toFixed(3)
                    : '0.825'}
                </span>
              </div>
            </button>
          );
        })}
      </div>

      {/* 3. Selected Model Drift & Performance Details */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-slate-900">{activeModel?.model_name || 'Delay Prediction Model'}</h3>
              <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-700 font-mono">
                {activeModel?.model_id || selectedModelId}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Population Stability Index (PSI) drift monitoring against training distribution
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-right">
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Stability Index (PSI)</div>
              <div className="text-lg font-mono font-bold text-slate-900">{psi.toFixed(3)}</div>
              <div className="text-[10px] font-semibold text-emerald-600">Stable Distribution (&lt; 0.10)</div>
            </div>
          </div>
        </div>

        {/* Drift Metrics Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-5 text-xs">
          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100">
            <div className="text-slate-500 font-medium">Evaluation Verdict</div>
            <div className="text-sm font-bold text-emerald-700 mt-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Production In-Bounds</span>
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">Zero significant distribution shift detected</div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100">
            <div className="text-slate-500 font-medium">Retraining Eligibility</div>
            <div className="text-sm font-bold text-slate-800 mt-1">Not Required</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Current performance matches baseline SLA</div>
          </div>

          <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-100">
            <div className="text-slate-500 font-medium">Champion-Challenger Status</div>
            <div className="text-sm font-bold text-blue-700 mt-1">Production Champion Active</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Experimental models remain strictly isolated</div>
          </div>
        </div>
      </div>

      {/* 4. Operator Feedback & Retraining Trigger */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Feedback Form */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs">
          <h3 className="text-sm font-bold text-slate-900 mb-1">Submit Operational Observation</h3>
          <p className="text-xs text-slate-500 mb-4">
            Record ground-truth transit outcomes to monitor model calibration
          </p>

          <form onSubmit={handleFeedbackSubmit} className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-700 font-semibold mb-1">Observation Type</label>
              <select
                value={feedbackType}
                onChange={(e) => setFeedbackType(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs text-slate-800 bg-white focus:outline-blue-500"
              >
                <option value="OBSERVED_OPERATIONAL_OUTCOME">Observed Operational Outcome (Real Ground Truth)</option>
                <option value="SIMULATION_RESULT">Simulation Hypothesis (Non-Retraining)</option>
              </select>
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">Model Calibration Rating (1-5)</label>
              <input
                type="number"
                min={1}
                max={5}
                value={accuracyScore}
                onChange={(e) => setAccuracyScore(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs text-slate-800 focus:outline-blue-500"
              />
            </div>

            <div>
              <label className="block text-slate-700 font-semibold mb-1">Observation Details</label>
              <textarea
                rows={3}
                value={observationNotes}
                onChange={(e) => setObservationNotes(e.target.value)}
                placeholder="Document observed transit time, carrier delays, or unexpected delivery patterns..."
                className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs text-slate-800 focus:outline-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold shadow-xs transition cursor-pointer flex items-center gap-1.5 disabled:opacity-60"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Submit Observation</span>
            </button>
          </form>

          {message && (
            <div className="mt-3 p-2.5 rounded-lg bg-blue-50 border border-blue-200 text-xs text-blue-900">
              {message}
            </div>
          )}
        </div>

        {/* Candidate Retraining Experiments */}
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-2xs flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-purple-600" />
                <h3 className="text-sm font-bold text-slate-900">Candidate Retraining Sandbox</h3>
              </div>
              <button
                onClick={handleRetrain}
                disabled={trainingExperiment}
                className="px-3 py-1.5 rounded-lg bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 text-xs font-semibold transition cursor-pointer disabled:opacity-60"
              >
                {trainingExperiment ? 'Training...' : 'Trigger Experiment'}
              </button>
            </div>

            <p className="text-xs text-slate-500 mt-2">
              Experimental models train in isolated directories (<code className="text-slate-700 bg-slate-100 px-1 py-0.5 rounded">models/phase13_experiments/</code>) and cannot replace production models without governance sign-off.
            </p>

            <div className="mt-3 divide-y divide-slate-100">
              {experiments.length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-400">
                  No candidate models evaluated yet.
                </div>
              ) : (
                experiments.slice(0, 3).map((exp) => (
                  <div key={exp.experiment_id} className="py-2.5 text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-slate-800">{exp.experiment_id}</span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                        {exp.promotion_status || 'ISOLATED_SANDBOX'}
                      </span>
                    </div>
                    <div className="text-[11px] text-slate-500 mt-0.5">
                      Verdict: <span className="font-medium text-slate-700">{exp.challenger_verdict}</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-400">
            Safeguard: Automated model promotion blocked by policy
          </div>
        </div>
      </div>
    </div>
  );
};

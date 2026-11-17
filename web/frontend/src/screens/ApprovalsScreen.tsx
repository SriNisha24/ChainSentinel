import React, { useState } from 'react';
import {
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  History,
  AlertTriangle,
  Info
} from 'lucide-react';
import type {
  RecommendedPlanResponse,
  ApprovalStateResponse,
  ApprovalDecisionPayload,
  AlertRecord
} from '../types/api';
import { ModuleStateCard } from '../components/ModuleStateCard';

interface ApprovalsScreenProps {
  runId: string;
  eventId: string;
  recommendedPlan?: RecommendedPlanResponse | null;
  approvalData: ApprovalStateResponse | null;
  alerts?: AlertRecord[];
  loading: boolean;
  error: string | null;
  onSubmitDecision: (payload: ApprovalDecisionPayload) => Promise<void>;
  onRefresh: () => void;
}

export const ApprovalsScreen: React.FC<ApprovalsScreenProps> = ({
  runId,
  eventId,
  recommendedPlan,
  approvalData,
  loading,
  error,
  onSubmitDecision,
  onRefresh,
}) => {
  const [reviewerName, setReviewerName] = useState<string>('sarah_jenkins');
  const [reviewerRole, setReviewerRole] = useState<string>('REVIEWER');
  const [comments, setComments] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [formError, setFormError] = useState<string | null>(null);

  if (loading && !approvalData) {
    return <ModuleStateCard moduleName="Management Approvals" loading={true} />;
  }

  if (error && !approvalData) {
    return <ModuleStateCard moduleName="Management Approvals" error={error} onRetry={onRefresh} />;
  }

  const currentStatus = approvalData?.current_status ?? 'PENDING_REVIEW';
  const history = approvalData?.history ?? [];

  // Authoritative metrics from recommended plan
  const planName = recommendedPlan?.recommended_plan_name || 'Plan 5 (Hybrid Knapsack - Greedy + MCDA)';
  const recOrders = recommendedPlan?.resource_allocation_summary?.recovered_orders_count ?? 533;
  const unrecOrders = recommendedPlan?.resource_allocation_summary?.unrecovered_orders_count ?? 2638;
  const totalEligible = recOrders + unrecOrders;
  const recoveryPct = totalEligible > 0 ? ((recOrders / totalEligible) * 100).toFixed(1) : '16.8';
  const critRec = recommendedPlan?.risk_mitigation_summary?.recovered_critical_orders ?? 17;
  const critUnrec = recommendedPlan?.risk_mitigation_summary?.unrecovered_critical_orders ?? 3;
  const critTotal = critRec + critUnrec;
  const mitigatedRev = recommendedPlan?.financial_mitigation_summary?.expected_mitigated_revenue_usd ?? 411590.64;
  const residualRev = recommendedPlan?.financial_mitigation_summary?.residual_revenue_exposure_usd ?? 870810.55;
  const allocatedRcu = recommendedPlan?.resource_allocation_summary?.allocated_rcu ?? 999.9;
  const budgetRcu = recommendedPlan?.resource_allocation_summary?.capacity_budget_rcu ?? 1000.0;
  const unusedRcu = (budgetRcu - allocatedRcu).toFixed(1);

  const handleAction = async (action: 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED' | 'CLOSED') => {
    if (!reviewerName.trim()) {
      setFormError('Please enter your reviewer name or ID.');
      return;
    }
    if (!comments.trim()) {
      setFormError('Please provide a mandatory decision comment/rationale.');
      return;
    }

    setFormError(null);
    setSubmitting(true);
    try {
      await onSubmitDecision({
        run_id: runId,
        decision_status: action,
        reviewer_username: reviewerName.trim(),
        reviewer_role: reviewerRole,
        reviewer_comments: comments.trim(),
      });
      setComments('');
    } catch (err: any) {
      setFormError(err?.message || 'Failed to submit decision.');
    } finally {
      setSubmitting(false);
    }
  };

  const statusBadge = (st: string) => {
    switch (st) {
      case 'APPROVED':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">APPROVED</span>;
      case 'REJECTED':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-rose-50 text-rose-700 border border-rose-200">REJECTED</span>;
      case 'REVISION_REQUESTED':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200">REVISION REQUESTED</span>;
      case 'CLOSED':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-slate-100 text-slate-700 border border-slate-200">CLOSED</span>;
      default:
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-50 text-blue-700 border border-blue-200">PENDING REVIEW</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Decision Boundary Advisory Banner */}
      <div className="bg-blue-50/70 border border-blue-200/80 rounded-xl p-4 text-xs text-blue-900 flex items-start gap-3">
        <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-bold">Human-in-the-Loop Governance Boundary</div>
          <div className="text-slate-600 leading-relaxed">
            Approving a strategy logs an immutable, cryptographic authorization in the system audit ledger. <strong>This does not execute physical automated dispatch</strong>—warehouse and transportation teams execute reroutes through their operational dispatch consoles.
          </div>
        </div>
      </div>

      {/* 2. Disruption & Recommendation Summary Header */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">Operational Review Gate</span>
              <span className="text-slate-300">•</span>
              <span className="font-mono text-xs font-semibold text-slate-600">Event: {eventId}</span>
            </div>
            <h2 className="text-lg font-bold text-slate-900 mt-1">
              Recovery Authorization for {planName}
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Review analytical findings, risk tradeoffs, and commit the official operational decision
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="text-right">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Current State</div>
              <div className="mt-1">{statusBadge(currentStatus)}</div>
            </div>
          </div>
        </div>

        {/* Benefits vs Risks Split */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-5 text-xs">
          <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-100">
            <div className="font-bold text-emerald-900 flex items-center gap-1.5 mb-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Expected Operational Benefits</span>
            </div>
            <ul className="space-y-1.5 text-slate-700">
              <li>• <strong>{recOrders.toLocaleString()} of {totalEligible.toLocaleString()} customer orders recovered</strong> ({recoveryPct}% recovery rate under budget).</li>
              <li>• <strong>{critRec} of {critTotal} Critical risk orders ({critTotal > 0 ? ((critRec / critTotal) * 100).toFixed(0) : 85}%)</strong> expedited via priority capacity.</li>
              <li>• <strong>${mitigatedRev.toLocaleString(undefined, { maximumFractionDigits: 0 })} in revenue protected</strong> through optimal knapsack allocation.</li>
              <li>• <strong>{allocatedRcu.toFixed(1)} RCU utilized</strong> of {budgetRcu.toFixed(1)} RCU budget ({unusedRcu} RCU safety buffer retained).</li>
            </ul>
          </div>

          <div className="p-4 rounded-xl bg-amber-50/50 border border-amber-100">
            <div className="font-bold text-amber-900 flex items-center gap-1.5 mb-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Operational Risks & Limitations</span>
            </div>
            <ul className="space-y-1.5 text-slate-700">
              <li>• <strong>{unrecOrders.toLocaleString()} orders remain unmitigated</strong> due to {budgetRcu.toFixed(0)} RCU capacity ceiling.</li>
              <li>• <strong>${residualRev.toLocaleString(undefined, { maximumFractionDigits: 0 })} in residual exposure</strong> requires proactive customer communications.</li>
              <li>• Regional port disruption ({eventId}) requires carrier confirmation within 4 hours.</li>
              <li>• Involves multi-carrier re-routing across alternate regional logistics corridors.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 3. Decision Submission Console */}
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-2xs">
        <h3 className="text-sm font-bold text-slate-900 mb-1">Submit Management Decision</h3>
        <p className="text-xs text-slate-500 mb-4">
          All decisions are signed and stored immutably in the JSON audit ledger with reviewer credentials
        </p>

        {formError && (
          <div className="p-3 mb-4 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-800">
            {formError}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4 text-xs">
          <div>
            <label className="block text-slate-700 font-semibold mb-1">Reviewer Username / ID</label>
            <input
              type="text"
              value={reviewerName}
              onChange={(e) => setReviewerName(e.target.value)}
              placeholder="e.g., s_jenkins"
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs text-slate-800 focus:outline-blue-500"
            />
          </div>

          <div>
            <label className="block text-slate-700 font-semibold mb-1">Authorization Role</label>
            <select
              value={reviewerRole}
              onChange={(e) => setReviewerRole(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs text-slate-800 bg-white focus:outline-blue-500 cursor-pointer"
            >
              <option value="REVIEWER">Operational Reviewer</option>
              <option value="SUPPLY_CHAIN_MANAGER">Supply Chain Manager</option>
              <option value="OPERATIONS_DIRECTOR">Operations Director</option>
              <option value="ADMIN">System Administrator</option>
            </select>
          </div>
        </div>

        <div className="mb-4 text-xs">
          <label className="block text-slate-700 font-semibold mb-1">
            Decision Comments / Justification <span className="text-rose-500">*</span>
          </label>
          <textarea
            rows={3}
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            placeholder="Document the operational rationale for this decision (e.g., 'Plan 5 balances critical order protection while staying within weekend overtime limits')..."
            className="w-full px-3 py-2 rounded-lg border border-slate-200 text-xs text-slate-800 focus:outline-blue-500"
          />
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap items-center gap-3 pt-2">
          <button
            onClick={() => handleAction('APPROVED')}
            disabled={submitting}
            className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-xs transition cursor-pointer disabled:opacity-60"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Approve Plan 5</span>
          </button>

          <button
            onClick={() => handleAction('REVISION_REQUESTED')}
            disabled={submitting}
            className="px-4 py-2 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-xs transition cursor-pointer disabled:opacity-60"
          >
            <HelpCircle className="w-4 h-4" />
            <span>Request Revision</span>
          </button>

          <button
            onClick={() => handleAction('REJECTED')}
            disabled={submitting}
            className="px-4 py-2 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-xs transition cursor-pointer disabled:opacity-60"
          >
            <XCircle className="w-4 h-4" />
            <span>Reject Plan</span>
          </button>

          <button
            onClick={() => handleAction('CLOSED')}
            disabled={submitting}
            className="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold flex items-center gap-1.5 transition cursor-pointer disabled:opacity-60"
          >
            <Clock className="w-4 h-4" />
            <span>Close Incident</span>
          </button>
        </div>
      </div>

      {/* 4. Immutable Decision Receipts History Table */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-2xs overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-slate-600" />
            <h3 className="text-sm font-bold text-slate-900">Decision Receipt Ledger</h3>
          </div>
          <span className="text-xs text-slate-500 font-mono">{history.length} Receipts Recorded</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-50 text-slate-500 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Receipt ID</th>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Decision</th>
                <th className="py-3 px-4">Reviewer</th>
                <th className="py-3 px-4">Role</th>
                <th className="py-3 px-4">Comments / Audit Trace</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {history.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-400 text-xs">
                    No decisions recorded yet for this run.
                  </td>
                </tr>
              ) : (
                history.map((rec) => (
                  <tr key={rec.approval_id} className="hover:bg-slate-50/70 transition">
                    <td className="py-3 px-4 font-mono font-bold text-blue-600">{rec.approval_id}</td>
                    <td className="py-3 px-4 font-mono text-slate-500">
                      {new Date(rec.decision_timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-4">{statusBadge(rec.decision_status)}</td>
                    <td className="py-3 px-4 font-semibold text-slate-800">{rec.reviewer?.username || 'reviewer'}</td>
                    <td className="py-3 px-4 text-slate-600">{rec.reviewer?.role || 'Reviewer'}</td>
                    <td className="py-3 px-4 text-slate-600 max-w-xs truncate" title={rec.reviewer_comments}>
                      {rec.reviewer_comments}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

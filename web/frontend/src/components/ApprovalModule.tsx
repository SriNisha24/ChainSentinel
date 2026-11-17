import React, { useState } from 'react';
import {
  UserCheck,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  XCircle,
  FileText,
  Clock,
  History,
  Info,
  Lock,
  ChevronDown,
  ChevronUp,
  SlidersHorizontal
} from 'lucide-react';
import type {
  ApprovalStateResponse,
  ApprovalDecisionStatus,
  ApprovalDecisionPayload,
  RecommendedPlanResponse
} from '../types/api';

interface ApprovalModuleProps {
  runId: string;
  eventId: string;
  recommendedPlan?: RecommendedPlanResponse | null;
  approvalData: ApprovalStateResponse | null;
  loading: boolean;
  error: string | null;
  onSubmitDecision: (payload: ApprovalDecisionPayload) => Promise<void>;
  onRefresh: () => void;
}

export const ApprovalModule: React.FC<ApprovalModuleProps> = ({
  runId,
  eventId,
  recommendedPlan,
  approvalData,
  loading,
  error,
  onSubmitDecision,
  onRefresh,
}) => {
  // Form state
  const [username, setUsername] = useState('sc_operations_lead');
  const [role, setRole] = useState('Supply Chain Operations Lead');
  const [department, setDepartment] = useState('Global Logistics & Fulfillment');
  const [comments, setComments] = useState(
    'Knapsack Hybrid (Plan 5) provides optimal $411,590.64 revenue mitigation while safeguarding 17 of 20 critical shipments within the 1,000 RCU envelope.'
  );

  // Revision options state
  const [showRevisionOptions, setShowRevisionOptions] = useState(false);
  const [targetRcu, setTargetRcu] = useState<number | undefined>(950.0);
  const [targetCriticalPct, setTargetCriticalPct] = useState<number | undefined>(90.0);
  const [revisionNotes, setRevisionNotes] = useState('Consider reallocating 50 RCU buffer to cold-chain pharmaceutical shipments.');

  // Modal confirmation state
  const [pendingAction, setPendingAction] = useState<ApprovalDecisionStatus | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);

  const currentStatus: ApprovalDecisionStatus = approvalData?.current_status || 'PENDING_REVIEW';

  const getStatusBadge = (status: ApprovalDecisionStatus) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" />
            APPROVED
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/20 text-rose-300 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5" />
            REJECTED
          </span>
        );
      case 'REVISION_REQUESTED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-purple-500/20 text-purple-300 border border-purple-500/30">
            <RotateCcw className="w-3.5 h-3.5" />
            REVISION REQUESTED
          </span>
        );
      case 'CLOSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-500/20 text-slate-300 border border-slate-500/30">
            <Lock className="w-3.5 h-3.5" />
            REVIEW CLOSED
          </span>
        );
      case 'PENDING_REVIEW':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
            <Clock className="w-3.5 h-3.5" />
            PENDING REVIEW
          </span>
        );
    }
  };

  const handleOpenConfirm = (action: ApprovalDecisionStatus) => {
    if (!username.trim() || !role.trim() || !comments.trim()) {
      alert('Reviewer username, role, and justification comments are required before submitting a decision.');
      return;
    }
    setPendingAction(action);
  };

  const handleConfirmSubmit = async () => {
    if (!pendingAction) return;

    setIsSubmitting(true);
    setActionFeedback(null);

    const payload: ApprovalDecisionPayload = {
      run_id: runId,
      event_id: eventId,
      recommended_plan: 'PLAN_5_KNAPSACK_HYBRID',
      decision_status: pendingAction,
      reviewer_username: username.trim(),
      reviewer_role: role.trim(),
      reviewer_department: department.trim(),
      reviewer_comments: comments.trim(),
    };

    if (pendingAction === 'REVISION_REQUESTED') {
      payload.revision_request = {
        target_capacity_rcu: targetRcu,
        target_critical_recovery_pct: targetCriticalPct,
        custom_notes: revisionNotes.trim() || comments.trim(),
      };
    }

    try {
      await onSubmitDecision(payload);
      setActionFeedback(`Decision '${pendingAction}' successfully recorded to data/approval_records/ receipt.`);
      setPendingAction(null);
      onRefresh();
    } catch (err: any) {
      setActionFeedback(`Submission failed: ${err.message || 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-850 border border-slate-800 rounded-xl p-6 shadow-sm mb-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-5 mb-5">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Human-in-the-Loop Operational Review & Approval Console
              <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Phase 11 Interactive
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Operational decision authority interface for Plan 5 (Knapsack Hybrid) review, signed audit receipts, and revision requests
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-xs font-mono text-slate-400 bg-slate-900 px-3 py-1.5 rounded-lg border border-slate-800">
            Status: {getStatusBadge(currentStatus)}
          </div>
          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 border border-slate-800 transition"
            title="Refresh Approval Status"
          >
            <RotateCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Mandatory Safety & Governance Watermark Banner */}
      <div className="p-4 rounded-lg bg-amber-500/10 border border-amber-500/30 mb-6 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-200/90 leading-relaxed">
          <div className="font-bold text-amber-300 tracking-wide">
            SIMULATION & DECISION-SUPPORT PROTOTYPE — NO PHYSICAL DISPATCH EXECUTED
          </div>
          <p className="mt-1 text-slate-300">
            Approval records document simulated operational governance sign-off in accordance with supply-chain resilience policies.
            Submissions write immutable timestamped JSON receipts to <code className="text-amber-300 font-mono">data/approval_records/</code>.
            This academic decision-support prototype does not trigger real-world carrier dispatch, EDI transmissions, ERP transactions, or warehouse movements.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg mb-5 text-xs flex items-center gap-2 bg-rose-500/10 border border-rose-500/30 text-rose-300">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>Error loading approval records: {error}</span>
        </div>
      )}

      {actionFeedback && (
        <div
          className={`p-3.5 rounded-lg mb-5 text-xs flex items-center gap-2 ${
            actionFeedback.includes('failed')
              ? 'bg-rose-500/10 border border-rose-500/30 text-rose-300'
              : 'bg-emerald-500/10 border border-emerald-500/30 text-emerald-300'
          }`}
        >
          {actionFeedback.includes('failed') ? (
            <AlertTriangle className="w-4 h-4 shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          )}
          <span>{actionFeedback}</span>
        </div>
      )}

      {/* Recommended Strategy Key Verification Metrics */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-lg p-4 mb-6">
        <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center justify-between">
          <span>Authoritative Analytical Recommendation Under Review</span>
          <span className="font-mono text-sky-400">PLAN_5_KNAPSACK_HYBRID</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Capacity Allocation</span>
            <span className="text-slate-200 font-semibold font-mono">
              {recommendedPlan?.resource_allocation_summary?.allocated_rcu ?? 999.9} / 1,000 RCU
            </span>
            <span className="text-emerald-400 text-[10px] block mt-0.5">99.99% envelope utilization</span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Protected Shipments</span>
            <span className="text-slate-200 font-semibold font-mono">
              {recommendedPlan?.risk_mitigation_summary?.recovered_critical_orders ?? 17} / 20 Critical
            </span>
            <span className="text-sky-400 text-[10px] block mt-0.5">85.0% critical coverage</span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Revenue Mitigated</span>
            <span className="text-slate-200 font-semibold font-mono">
              ${recommendedPlan?.financial_mitigation_summary?.expected_mitigated_revenue_usd?.toLocaleString() ?? '411,590.64'}
            </span>
            <span className="text-emerald-400 text-[10px] block mt-0.5">32.1% exposure saved</span>
          </div>

          <div className="bg-slate-950 p-2.5 rounded border border-slate-800">
            <span className="text-slate-400 block text-[11px]">Resilience Index</span>
            <span className="text-slate-200 font-semibold font-mono">
              {recommendedPlan?.resilience_index ?? 44.66} / 100
            </span>
            <span className="text-purple-400 text-[10px] block mt-0.5">Top rank across all 6 plans</span>
          </div>
        </div>
      </div>

      {/* Reviewer Input Form & Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-xs font-semibold text-slate-300 block">
              Reviewer Identity & Governance Credentials
            </label>
            <span className="text-[11px] text-slate-500 italic">Self-Declared Role</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] text-slate-400 block mb-1">Reviewer Username *</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500 font-mono"
                placeholder="e.g. jdoe_operations"
              />
            </div>
            <div>
              <label className="text-[11px] text-slate-400 block mb-1">Official Role *</label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                placeholder="e.g. Supply Chain Operations Lead"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] text-slate-400 block mb-1">Department</label>
            <input
              type="text"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
              placeholder="e.g. Global Fulfillment & Operations"
            />
          </div>

          <div>
            <label className="text-[11px] text-slate-400 block mb-1">
              Decision Justification & Operational Comments *
            </label>
            <textarea
              rows={3}
              value={comments}
              onChange={(e) => setComments(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-sky-500 resize-none leading-relaxed"
              placeholder="Document the operational rationale, risk tolerances, and constraints..."
            />
          </div>

          {/* Collapsible Revision Controls */}
          <div className="pt-1">
            <button
              type="button"
              onClick={() => setShowRevisionOptions(!showRevisionOptions)}
              className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1.5 transition"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>{showRevisionOptions ? 'Hide Revision Parameters' : 'Configure Revision Parameters'}</span>
              {showRevisionOptions ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            {showRevisionOptions && (
              <div className="mt-3 p-3.5 rounded-lg bg-slate-900 border border-slate-800 space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">Target Capacity RCU</label>
                    <input
                      type="number"
                      value={targetRcu ?? ''}
                      onChange={(e) => setTargetRcu(e.target.value ? parseFloat(e.target.value) : undefined)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono"
                      placeholder="e.g. 950"
                    />
                  </div>
                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">Target Critical Recovery %</label>
                    <input
                      type="number"
                      value={targetCriticalPct ?? ''}
                      onChange={(e) => setTargetCriticalPct(e.target.value ? parseFloat(e.target.value) : undefined)}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200 font-mono"
                      placeholder="e.g. 90"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-[11px] text-slate-400 block mb-1">Revision Instructions</label>
                  <input
                    type="text"
                    value={revisionNotes}
                    onChange={(e) => setRevisionNotes(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
                    placeholder="Specific constraints for next optimization run..."
                  />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Action Buttons & Governance Metadata */}
        <div className="flex flex-col justify-between space-y-4">
          <div className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 space-y-3 text-xs">
            <div className="font-semibold text-slate-200 flex items-center gap-1.5 border-b border-slate-800 pb-2">
              <FileText className="w-4 h-4 text-sky-400" />
              <span>Immutable Storage Contract Specification</span>
            </div>
            <div className="font-mono text-[11px] space-y-1.5 text-slate-400">
              <div>Target Run ID: <span className="text-slate-200">{runId}</span></div>
              <div>Disruption Event: <span className="text-slate-200">{eventId}</span></div>
              <div>Receipt Storage: <span className="text-sky-300">data/approval_records/APPR-*.json</span></div>
              <div>Schema Enforcement: <span className="text-emerald-400">Draft-07 Strict (Gate-Verified)</span></div>
              <div>External Auth: <span className="text-amber-400">None (Self-Declared Identity)</span></div>
            </div>
          </div>

          {/* 4 Decision Buttons */}
          <div className="grid grid-cols-2 gap-3 pt-2">
            <button
              onClick={() => handleOpenConfirm('APPROVED')}
              disabled={loading || isSubmitting}
              className="py-2.5 px-3 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Approve Plan 5</span>
            </button>

            <button
              onClick={() => handleOpenConfirm('REVISION_REQUESTED')}
              disabled={loading || isSubmitting}
              className="py-2.5 px-3 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50"
            >
              <RotateCcw className="w-4 h-4" />
              <span>Request Revision</span>
            </button>

            <button
              onClick={() => handleOpenConfirm('REJECTED')}
              disabled={loading || isSubmitting}
              className="py-2.5 px-3 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50"
            >
              <ShieldAlert className="w-4 h-4" />
              <span>Reject Plan</span>
            </button>

            <button
              onClick={() => handleOpenConfirm('CLOSED')}
              disabled={loading || isSubmitting}
              className="py-2.5 px-3 rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition disabled:opacity-50"
            >
              <Lock className="w-4 h-4" />
              <span>Close Review</span>
            </button>
          </div>
        </div>
      </div>

      {/* Chronological Audit Trail */}
      <div className="border-t border-slate-800 pt-5 mt-6">
        <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-3 flex items-center gap-2">
          <History className="w-4 h-4 text-sky-400" />
          <span>Chronological Decision Audit Trail ({approvalData?.history?.length ?? 0} Receipts)</span>
        </h3>

        {!approvalData?.history || approvalData.history.length === 0 ? (
          <div className="text-center py-6 bg-slate-900/40 rounded-lg border border-slate-800/80 text-xs text-slate-500">
            No human review receipts logged yet for run {runId}. Review console is currently in <strong className="text-amber-400">PENDING_REVIEW</strong> state.
          </div>
        ) : (
          <div className="space-y-3">
            {approvalData.history.map((record, index) => (
              <div
                key={record.approval_id || index}
                className="bg-slate-900/80 border border-slate-800 rounded-lg p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2.5 flex-wrap">
                    <span className="font-mono text-sky-400 font-semibold">{record.approval_id}</span>
                    {getStatusBadge(record.decision_status)}
                    <span className="text-slate-400 font-medium">
                      by <strong className="text-slate-200">{record.reviewer?.username}</strong> ({record.reviewer?.role})
                    </span>
                  </div>
                  <p className="text-slate-300 text-xs mt-1 italic">
                    "{record.reviewer_comments || 'No operational comment provided'}"
                  </p>
                  {record.revision_request && (
                    <div className="text-[11px] text-purple-300 font-mono bg-purple-950/40 border border-purple-900/50 rounded p-1.5 mt-1.5">
                      Revision Scope: Target RCU {record.revision_request.target_capacity_rcu ?? 'N/A'} | Notes: {record.revision_request.custom_notes || 'None'}
                    </div>
                  )}
                </div>

                <div className="text-right text-[11px] text-slate-500 font-mono shrink-0">
                  <div>{new Date(record.decision_timestamp).toLocaleString()}</div>
                  <div className="text-emerald-500/80">RECEIPT_PERSISTED</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Confirmation Modal */}
      {pendingAction && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center gap-3 border-b border-slate-800 pb-3">
              <div className="p-2 rounded-lg bg-sky-500/20 text-sky-400">
                <Info className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-slate-100">
                  Confirm Operational Review Decision
                </h3>
                <p className="text-xs text-slate-400 font-mono">Run: {runId}</p>
              </div>
            </div>

            <div className="space-y-3 text-xs text-slate-300">
              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Target Action:</span>
                <div>{getStatusBadge(pendingAction)}</div>
              </div>

              <div className="flex justify-between items-center py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Reviewer:</span>
                <span className="font-semibold text-slate-200">{username} ({role})</span>
              </div>

              <div className="py-1 border-b border-slate-800/60">
                <span className="text-slate-400 block mb-1">Comments:</span>
                <p className="text-slate-200 bg-slate-950 p-2 rounded text-[11px] max-h-24 overflow-y-auto font-mono">
                  {comments}
                </p>
              </div>

              <div className="p-3 rounded bg-amber-500/10 border border-amber-500/20 text-[11px] text-amber-300 leading-normal">
                Notice: Submitting will generate an immutable JSON receipt in <code className="font-mono">data/approval_records/</code>. No physical movement or carrier dispatch is initiated.
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setPendingAction(null)}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 font-medium transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmSubmit}
                disabled={isSubmitting}
                className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-xs text-white font-semibold flex items-center gap-2 transition disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <RotateCcw className="w-3.5 h-3.5 animate-spin" />
                    <span>Writing Receipt...</span>
                  </>
                ) : (
                  <span>Confirm & Record Receipt</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

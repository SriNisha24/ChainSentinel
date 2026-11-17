import React from 'react';
import { UserCheck, ShieldCheck, Lock, AlertCircle, FileSignature } from 'lucide-react';

export const ApprovalPlaceholder: React.FC = () => {
  return (
    <div className="bg-slate-850 border border-slate-800 rounded-xl p-6 shadow-sm mb-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-4 mb-5">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <UserCheck className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-100 flex items-center gap-2">
              Human-in-the-Loop Operational Review & Approval Console
              <span className="px-2 py-0.5 rounded text-xs font-semibold bg-sky-500/20 text-sky-300 border border-sky-500/30">
                Task 11D Architecture Preview
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Interactive human decision gate interface for review, audit notes, and signed approval
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-amber-400 bg-amber-500/10 border border-amber-500/30 px-3 py-1.5 rounded-lg font-medium">
          <Lock className="w-3.5 h-3.5" />
          <span>Actions Inactive — Planned for Task 11D</span>
        </div>
      </div>

      <div className="p-4 rounded-lg bg-slate-900/80 border border-slate-800 mb-5 flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
        <div className="text-xs text-slate-300 leading-relaxed">
          <strong className="text-sky-300 font-semibold">Human approval workflow — planned for Task 11D.</strong>
          <p className="mt-1 text-slate-400">
            In accordance with Task 11B/11C implementation scope, this panel displays the architectural schema for operational sign-off.
            The underlying storage contract (<code className="text-slate-300">data/approval_records/schema.json</code>) has been prepared and verified.
            Live interactive approval POST operations, state transitions, and audit records will be activated in Task 11D.
          </p>
        </div>
      </div>

      {/* Mock Review Form (Disabled) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5 opacity-75">
        <div className="space-y-4">
          <div>
            <label className="text-xs font-medium text-slate-400 block mb-1">
              Reviewing Officer / Role
            </label>
            <input
              type="text"
              disabled
              value="Supply Chain Operations Lead (Simulated Role)"
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-400 cursor-not-allowed"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-slate-400 block mb-1">
              Approval Justification & Operational Notes
            </label>
            <textarea
              disabled
              rows={3}
              value="Knapsack Hybrid (Plan 5) provides optimal $411,590.64 revenue mitigation while safeguarding 17 of 20 critical shipments within the 1,000 RCU envelope."
              className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-400 cursor-not-allowed resize-none"
            />
          </div>
        </div>

        <div className="space-y-4 flex flex-col justify-between">
          <div className="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2 text-xs">
            <div className="text-slate-300 font-medium flex items-center gap-1.5">
              <FileSignature className="w-4 h-4 text-sky-400" />
              <span>Target Approval Contract</span>
            </div>
            <div className="text-slate-400 font-mono text-[11px] space-y-1">
              <div>Record Path: <span className="text-slate-300">data/approval_records/APPR-*.json</span></div>
              <div>Schema Version: <span className="text-slate-300">1.0.0 (Gate-Verified)</span></div>
              <div>Decision Status: <span className="text-amber-400">PENDING_TASK_11D</span></div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              disabled
              className="flex-1 py-2.5 px-4 rounded-lg bg-emerald-700/40 text-emerald-300/60 border border-emerald-600/30 text-xs font-semibold cursor-not-allowed flex items-center justify-center gap-2"
              title="Disabled — Planned for Task 11D"
            >
              <ShieldCheck className="w-4 h-4" />
              <span>Approve Plan 5 (Task 11D)</span>
            </button>

            <button
              disabled
              className="py-2.5 px-4 rounded-lg bg-slate-800 text-slate-500 border border-slate-700 text-xs font-medium cursor-not-allowed"
              title="Disabled — Planned for Task 11D"
            >
              <span>Reject / Override</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};


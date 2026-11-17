import React from 'react';
import { Loader2, AlertCircle, RefreshCw, Info } from 'lucide-react';

interface ModuleStateCardProps {
  moduleName: string;
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
  emptyMessage?: string;
}

export const ModuleStateCard: React.FC<ModuleStateCardProps> = ({
  moduleName,
  loading,
  error,
  onRetry,
  emptyMessage,
}) => {
  if (loading) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center shadow-xs mb-6 flex flex-col items-center justify-center min-h-[160px]">
        <Loader2 className="w-7 h-7 text-blue-600 animate-spin mb-3" />
        <div className="text-sm font-semibold text-slate-800">
          Loading {moduleName}...
        </div>
        <p className="text-xs text-slate-500 mt-1">
          Retrieving live data from the ChainSentinel analytics engine...
        </p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50/60 border border-rose-200 rounded-xl p-6 shadow-xs mb-6 flex items-start gap-4">
        <div className="p-2.5 rounded-lg bg-rose-100 text-rose-600 border border-rose-200 shrink-0 mt-0.5">
          <AlertCircle className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-semibold text-rose-900">
            Failed to Load {moduleName}
          </h3>
          <p className="text-xs text-rose-800 mt-1 font-mono bg-white/80 p-2.5 rounded border border-rose-200 break-words">
            {error}
          </p>
          <p className="text-xs text-slate-600 mt-2">
            Ensure the backend API service is running at <code className="bg-white px-1.5 py-0.5 rounded border border-slate-200 text-slate-700">http://127.0.0.1:8001</code>.
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-xs font-medium text-white flex items-center gap-1.5 transition shadow-xs cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry {moduleName}</span>
            </button>
          )}
        </div>
      </div>
    );
  }

  if (emptyMessage) {
    return (
      <div className="bg-white border border-slate-200 rounded-xl p-8 text-center shadow-xs mb-6 flex flex-col items-center justify-center min-h-[140px]">
        <div className="p-2.5 rounded-lg bg-blue-50 text-blue-600 border border-blue-100 mb-3">
          <Info className="w-5 h-5" />
        </div>
        <div className="text-sm font-semibold text-slate-800">No Data Available</div>
        <p className="text-xs text-slate-500 mt-1 max-w-md">{emptyMessage}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-3 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-xs font-medium text-slate-700 flex items-center gap-1.5 transition cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        )}
      </div>
    );
  }

  return null;
};

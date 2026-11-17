import type {
  HealthResponse,
  RunSummaryResponse,
  DisruptionEventResponse,
  ShockwaveResponse,
  RiskSummaryResponse,
  RecoveryPlansResponse,
  RecommendedPlanResponse,
  StressTestsResponse,
  LineageResponse,
  ApprovalStateResponse,
  ApprovalRecord,
  ApprovalDecisionPayload,
  AlertRecord,
  AlertSummaryResponse,
  FeedbackRecord,
  FeedbackSummaryResponse,
  ModelMetadata,
  ModelDriftResponse,
  RetrainingExperiment,
  UserSession,
  AuditLogRecord,
  DatasetMetadata,
  DatasetPreview,
  DatasetUploadResponse,
  AnalysisRunSummary,
  AnalysisRunDetail,
  PaginatedRecordsResponse,
  DatasetGeoResponse
} from '../types/api';

// Direct 127.0.0.1:8001 is prioritized, followed by Vite dev proxy /api
const API_ENDPOINTS = [
  'http://127.0.0.1:8000/api',
  '/api',
  'http://localhost:8000/api',
];

async function fetchWithTimeout(url: string, timeoutMs: number = 4000): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { signal: controller.signal });
    clearTimeout(id);
    return response;
  } catch (err) {
    clearTimeout(id);
    throw err;
  }
}

async function fetchJson<T>(path: string): Promise<T> {
  let lastNetworkError: Error | null = null;
  let lastHttpStatus: number | null = null;
  let lastHttpDetail: string | null = null;

  for (const baseUrl of API_ENDPOINTS) {
    try {
      const url = `${baseUrl}${path}`;
      const response = await fetchWithTimeout(url);
      if (response.ok) {
        return await response.json();
      }

      lastHttpStatus = response.status;
      const errorText = await response.text();
      try {
        const errorJson = JSON.parse(errorText);
        lastHttpDetail = errorJson.detail || errorText;
      } catch {
        lastHttpDetail = errorText || response.statusText;
      }

      // If server returned 404, it is actively running but missing this specific endpoint
      if (response.status === 404) {
        break; // Stop falling back; server is up and definitively returned 404
      }
    } catch (err: any) {
      lastNetworkError = err;
    }
  }

  if (lastHttpStatus === 404) {
    throw new Error(
      `HTTP 404 Not Found at ${path}. The FastAPI backend is running but this route is not registered in the active server process. (Restart backend with: python -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8001 --reload)`
    );
  }

  if (lastHttpStatus !== null) {
    throw new Error(
      `HTTP ${lastHttpStatus} Error at ${path}: ${lastHttpDetail || 'Server error'}`
    );
  }

  throw new Error(
    `Failed to connect to ChainSentinel backend at ${path}. Backend process appears unavailable on port 8001. ` +
    `Start backend manually with: python -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8001 --reload (${lastNetworkError?.message || 'Connection failed'})`
  );
}

async function postJson<T>(path: string, body: any): Promise<T> {
  let lastNetworkError: Error | null = null;
  let lastHttpStatus: number | null = null;
  let lastHttpDetail: string | null = null;

  for (const baseUrl of API_ENDPOINTS) {
    try {
      const url = `${baseUrl}${path}`;
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      if (response.ok) {
        return await response.json();
      }

      lastHttpStatus = response.status;
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      lastHttpDetail = errorData.detail || response.statusText;

      if (response.status === 404 || response.status === 400 || response.status === 422) {
        break;
      }
    } catch (err: any) {
      lastNetworkError = err;
    }
  }

  if (lastHttpStatus !== null) {
    throw new Error(`HTTP ${lastHttpStatus} at ${path}: ${lastHttpDetail || 'Request failed'}`);
  }

  throw new Error(
    `Failed to submit request to ${path}. Ensure backend is running on port 8001 (${lastNetworkError?.message || 'Connection error'})`
  );
}

export const api = {
  getHealth: () => fetchJson<HealthResponse>('/health'),
  getRunSummary: () => fetchJson<RunSummaryResponse>('/run'),
  getDisruption: () => fetchJson<DisruptionEventResponse>('/disruption'),
  getShockwave: () => fetchJson<ShockwaveResponse>('/shockwave'),
  getRisk: (sampleLimit: number = 50) => fetchJson<RiskSummaryResponse>(`/risk?sample_limit=${sampleLimit}`),
  getRecoveryPlans: () => fetchJson<RecoveryPlansResponse>('/recovery/plans'),
  getRecommendedPlan: () => fetchJson<RecommendedPlanResponse>('/recovery/recommended'),
  getStressTests: () => fetchJson<StressTestsResponse>('/recovery/stress-tests'),
  getLineage: () => fetchJson<LineageResponse>('/lineage'),
  getApprovalState: (runId: string) => fetchJson<ApprovalStateResponse>(`/approvals/${runId}`),
  submitApprovalDecision: (payload: ApprovalDecisionPayload) => postJson<ApprovalRecord>('/approvals/decision', payload),
  getAlerts: (status?: string, severity?: string, alertType?: string, runId?: string) => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (severity) params.append('severity', severity);
    if (alertType) params.append('alert_type', alertType);
    if (runId) params.append('run_id', runId);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return fetchJson<AlertRecord[]>(`/alerts${qs}`);
  },
  getAlertsSummary: (runId?: string) => {
    const qs = runId ? `?run_id=${runId}` : '';
    return fetchJson<AlertSummaryResponse>(`/alerts/summary${qs}`);
  },
  getAlertDetail: (alertId: string) => fetchJson<AlertRecord>(`/alerts/${alertId}`),
  acknowledgeAlert: (alertId: string, user: string = 'operational_reviewer', comments: string = '') =>
    postJson<AlertRecord>(`/alerts/${alertId}/acknowledge`, { user, comments }),
  resolveAlert: (alertId: string, user: string = 'operational_reviewer', comments: string = '') =>
    postJson<AlertRecord>(`/alerts/${alertId}/resolve`, { user, comments }),
  dismissAlert: (alertId: string, user: string = 'operational_reviewer', comments: string = '') =>
    postJson<AlertRecord>(`/alerts/${alertId}/dismiss`, { user, comments }),
  evaluateAlerts: (runId?: string) => {
    const qs = runId ? `?run_id=${runId}` : '';
    return postJson<AlertRecord[]>(`/alerts/evaluate${qs}`, {});
  },
  getModels: () => fetchJson<ModelMetadata[]>('/models'),
  getModelDrift: (modelId: string) => fetchJson<ModelDriftResponse>(`/models/${modelId}/drift`),
  getFeedback: (modelId?: string, feedbackType?: string, validationStatus?: string, runId?: string) => {
    const params = new URLSearchParams();
    if (modelId) params.append('model_id', modelId);
    if (feedbackType) params.append('feedback_type', feedbackType);
    if (validationStatus) params.append('validation_status', validationStatus);
    if (runId) params.append('run_id', runId);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return fetchJson<FeedbackRecord[]>(`/feedback${qs}`);
  },
  getFeedbackSummary: (modelId?: string) => {
    const qs = modelId ? `?model_id=${modelId}` : '';
    return fetchJson<FeedbackSummaryResponse>(`/feedback/summary${qs}`);
  },
  getFeedbackDetail: (feedbackId: string) => fetchJson<FeedbackRecord>(`/feedback/${feedbackId}`),
  createFeedback: (payload: any) => postJson<FeedbackRecord>('/feedback', payload),
  updateFeedbackStatus: (feedbackId: string, validation_status: string, actor: string = 'governance_officer', comments: string = '') =>
    postJson<FeedbackRecord>(`/feedback/${feedbackId}/status`, { validation_status, actor, comments }),
  getExperiments: () => fetchJson<RetrainingExperiment[]>('/models/experiments'),
  triggerRetrainingExperiment: (payload?: any) =>
    postJson<RetrainingExperiment>('/models/retrain-experiment', payload || {}),
  getAuthMe: () => fetchJson<UserSession>('/auth/me'),
  getAuditLogs: (limit: number = 50) => fetchJson<AuditLogRecord[]>(`/audit/logs?limit=${limit}`),

  // Dataset Intelligence (Workflow A)
  getDatasets: () => fetchJson<DatasetMetadata[]>('/datasets'),
  getDataset: (datasetId: string) => fetchJson<DatasetMetadata>(`/datasets/${datasetId}`),
  getDatasetPreview: (datasetId: string, limit: number = 15) =>
    fetchJson<DatasetPreview>(`/datasets/${datasetId}/preview?limit=${limit}`),
  uploadDataset: async (file: File): Promise<DatasetUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    let lastError: any = null;
    for (const baseUrl of API_ENDPOINTS) {
      try {
        const url = `${baseUrl}/datasets/upload`;
        const response = await fetch(url, {
          method: 'POST',
          body: formData,
        });
        if (response.ok) {
          return await response.json();
        }
        const errText = await response.text();
        throw new Error(`Upload error (${response.status}): ${errText}`);
      } catch (err) {
        lastError = err;
      }
    }
    throw lastError || new Error('Failed to upload dataset.');
  },
  triggerAnalysis: (datasetId: string, maxRows: number = 5000) =>
    postJson<AnalysisRunDetail>(`/analysis/${datasetId}/run?max_rows=${maxRows}`, {}),
  getAnalysisRuns: (datasetId?: string) => {
    const qs = datasetId ? `?dataset_id=${encodeURIComponent(datasetId)}` : '';
    return fetchJson<AnalysisRunSummary[]>(`/analysis/runs${qs}`);
  },
  getAnalysisRun: (runId: string) => fetchJson<AnalysisRunDetail>(`/analysis/runs/${runId}`),
  getAnalysisRunRecords: (
    runId: string,
    task: string = 'delay',
    page: number = 1,
    pageSize: number = 25,
    filterStatus?: string
  ) => {
    const params = new URLSearchParams({ task, page: String(page), page_size: String(pageSize) });
    if (filterStatus) params.append('filter_status', filterStatus);
    return fetchJson<PaginatedRecordsResponse>(`/analysis/runs/${runId}/records?${params.toString()}`);
  },
  getDatasetGeoFeatures: (datasetId: string, filterType: string = 'all', maxRecords: number = 5000) => {
    const params = new URLSearchParams({ filter_type: filterType, max_records: String(maxRecords) });
    return fetchJson<DatasetGeoResponse>(`/datasets/${encodeURIComponent(datasetId)}/geo?${params.toString()}`);
  },
};

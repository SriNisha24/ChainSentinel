import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, type NavTabId } from './components/Sidebar';
import { TopNavbar } from './components/TopNavbar';
import { HomeScreen } from './screens/HomeScreen';
import { DatasetAnalysisScreen } from './screens/DatasetAnalysisScreen';
import { AnalysisResultsScreen } from './screens/AnalysisResultsScreen';
import { DisruptionsScreen } from './screens/DisruptionsScreen';
import { RecoveryPlansScreen } from './screens/RecoveryPlansScreen';
import { ApprovalsScreen } from './screens/ApprovalsScreen';
import { AlertsScreen } from './screens/AlertsScreen';
import { ModelInsightsScreen } from './screens/ModelInsightsScreen';
import { SettingsScreen } from './screens/SettingsScreen';
import { api } from './services/api';
import type {
  RunSummaryResponse,
  DisruptionEventResponse,
  ShockwaveResponse,
  RiskSummaryResponse,
  RecoveryPlansResponse,
  RecommendedPlanResponse,
  StressTestsResponse,
  ApprovalStateResponse,
  ApprovalDecisionPayload,
  AlertRecord,
  AlertSummaryResponse,
  ModelMetadata,
  ModelDriftResponse,
  FeedbackRecord,
  FeedbackSummaryResponse,
  RetrainingExperiment,
  AnalysisRunDetail
} from './types/api';
import { AlertCircle } from 'lucide-react';

const getInitialTab = (): NavTabId => {
  if (typeof window !== 'undefined') {
    const hash = window.location.hash.replace('#', '') as NavTabId;
    const validTabs: NavTabId[] = [
      'home', 'dataset_analysis', 'analysis_results', 'disruptions', 'recovery', 'approvals', 'alerts', 'models', 'settings'
    ];
    if (validTabs.includes(hash)) return hash;
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab') as NavTabId;
    if (validTabs.includes(tabParam)) return tabParam;
  }
  return 'home';
};

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<NavTabId>(getInitialTab);
  const [sidebarCollapsed, setSidebarCollapsed] = useState<boolean>(false);
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const [globalLoading, setGlobalLoading] = useState<boolean>(true);

  // Workflow A State
  const [activeRunDetail, setActiveRunDetail] = useState<AnalysisRunDetail | null>(null);

  // Analytical module state payloads (Workflow B & existing pipelines)
  const [runData, setRunData] = useState<RunSummaryResponse | null>(null);
  const [disruption, setDisruption] = useState<DisruptionEventResponse | null>(null);
  const [shockwave, setShockwave] = useState<ShockwaveResponse | null>(null);
  const [_risk, setRisk] = useState<RiskSummaryResponse | null>(null);
  const [plans, setPlans] = useState<RecoveryPlansResponse | null>(null);
  const [recommendedPlan, setRecommendedPlan] = useState<RecommendedPlanResponse | null>(null);
  const [stressTests, setStressTests] = useState<StressTestsResponse | null>(null);
  const [approvalData, setApprovalData] = useState<ApprovalStateResponse | null>(null);
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);
  const [alertSummary, setAlertSummary] = useState<AlertSummaryResponse | null>(null);

  // Model Monitoring state
  const [models, setModels] = useState<ModelMetadata[]>([]);
  const [driftData, setDriftData] = useState<ModelDriftResponse | null>(null);
  const [feedbackRecords, setFeedbackRecords] = useState<FeedbackRecord[]>([]);
  const [feedbackSummary, setFeedbackSummary] = useState<FeedbackSummaryResponse | null>(null);
  const [experiments, setExperiments] = useState<RetrainingExperiment[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('delay_model_v1');

  // Granular loading & error states
  const [errors, setErrors] = useState<Record<string, string | null>>({
    run: null,
    disruption: null,
    shockwave: null,
    risk: null,
    plans: null,
    recommended: null,
    stress: null,
    approval: null,
    alerts: null,
    models: null,
  });

  const [loadingStates, setLoadingStates] = useState<Record<string, boolean>>({
    run: true,
    disruption: true,
    shockwave: true,
    risk: true,
    plans: true,
    recommended: true,
    stress: true,
    approval: true,
    alerts: true,
    models: true,
  });

  // Individual fetchers for graceful isolation and retries
  const fetchRun = useCallback(async () => {
    setLoadingStates((prev) => ({ ...prev, run: true }));
    setErrors((prev) => ({ ...prev, run: null }));
    try {
      const data = await api.getRunSummary();
      setRunData(data);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, run: err?.message || 'Failed to load run summary' }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, run: false }));
    }
  }, []);

  const fetchDisruption = useCallback(async () => {
    setLoadingStates((prev) => ({ ...prev, disruption: true }));
    setErrors((prev) => ({ ...prev, disruption: null }));
    try {
      const data = await api.getDisruption();
      setDisruption(data);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, disruption: err?.message || 'Failed to load disruption event' }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, disruption: false }));
    }
  }, []);

  const fetchShockwave = useCallback(async () => {
    setLoadingStates((prev) => ({ ...prev, shockwave: true }));
    setErrors((prev) => ({ ...prev, shockwave: null }));
    try {
      const data = await api.getShockwave();
      setShockwave(data);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, shockwave: err?.message || 'Failed to load shockwave data' }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, shockwave: false }));
    }
  }, []);

  const fetchRisk = useCallback(async () => {
    setLoadingStates((prev) => ({ ...prev, risk: true }));
    setErrors((prev) => ({ ...prev, risk: null }));
    try {
      const data = await api.getRisk(50);
      setRisk(data);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, risk: err?.message || 'Failed to load risk data' }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, risk: false }));
    }
  }, []);

  const fetchPlans = useCallback(async () => {
    setLoadingStates((prev) => ({ ...prev, plans: true }));
    setErrors((prev) => ({ ...prev, plans: null }));
    try {
      const data = await api.getRecoveryPlans();
      setPlans(data);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, plans: err?.message || 'Failed to load recovery candidate plans' }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, plans: false }));
    }
  }, []);

  const fetchRecommended = useCallback(async () => {
    setLoadingStates((prev) => ({ ...prev, recommended: true }));
    setErrors((prev) => ({ ...prev, recommended: null }));
    try {
      const data = await api.getRecommendedPlan();
      setRecommendedPlan(data);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, recommended: err?.message || 'Failed to load recommended plan details' }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, recommended: false }));
    }
  }, []);

  const fetchStress = useCallback(async () => {
    setLoadingStates((prev) => ({ ...prev, stress: true }));
    setErrors((prev) => ({ ...prev, stress: null }));
    try {
      const data = await api.getStressTests();
      setStressTests(data);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, stress: err?.message || 'Failed to load stress tests' }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, stress: false }));
    }
  }, []);

  const fetchApproval = useCallback(async () => {
    setLoadingStates((prev) => ({ ...prev, approval: true }));
    setErrors((prev) => ({ ...prev, approval: null }));
    const activeRunId = runData?.run_id || 'IRUN-20261104143752-A4CB8F';
    try {
      const data = await api.getApprovalState(activeRunId);
      setApprovalData(data);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, approval: err?.message || 'Failed to load approval status' }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, approval: false }));
    }
  }, [runData?.run_id]);

  const fetchAlerts = useCallback(async () => {
    setLoadingStates((prev) => ({ ...prev, alerts: true }));
    setErrors((prev) => ({ ...prev, alerts: null }));
    const activeRunId = runData?.run_id || 'IRUN-20261104143752-A4CB8F';
    try {
      const [alertsData, summaryData] = await Promise.all([
        api.getAlerts(undefined, undefined, undefined, activeRunId),
        api.getAlertsSummary(activeRunId),
      ]);
      setAlerts(alertsData);
      setAlertSummary(summaryData);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, alerts: err?.message || 'Failed to load alerts' }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, alerts: false }));
    }
  }, [runData?.run_id]);

  const handleAcknowledgeAlert = useCallback(async (alertId: string) => {
    await api.acknowledgeAlert(alertId);
    await fetchAlerts();
  }, [fetchAlerts]);

  const handleResolveAlert = useCallback(async (alertId: string) => {
    await api.resolveAlert(alertId);
    await fetchAlerts();
  }, [fetchAlerts]);

  const handleDismissAlert = useCallback(async (alertId: string) => {
    await api.dismissAlert(alertId);
    await fetchAlerts();
  }, [fetchAlerts]);

  const handleSubmitDecision = useCallback(async (payload: ApprovalDecisionPayload) => {
    await api.submitApprovalDecision(payload);
    await fetchApproval();
    await fetchAlerts();
  }, [fetchApproval, fetchAlerts]);

  const fetchModelsData = useCallback(async (targetModelId?: string) => {
    setLoadingStates((prev) => ({ ...prev, models: true }));
    setErrors((prev) => ({ ...prev, models: null }));
    const modelToFetch = targetModelId || selectedModelId;
    try {
      const [modelsList, drift, feedback, fdbkSummary, exps] = await Promise.all([
        api.getModels(),
        api.getModelDrift(modelToFetch),
        api.getFeedback(),
        api.getFeedbackSummary(),
        api.getExperiments(),
      ]);
      setModels(modelsList);
      setDriftData(drift);
      setFeedbackRecords(feedback);
      setFeedbackSummary(fdbkSummary);
      setExperiments(exps);
    } catch (err: any) {
      setErrors((prev) => ({ ...prev, models: err?.message || 'Failed to load model monitoring data' }));
    } finally {
      setLoadingStates((prev) => ({ ...prev, models: false }));
    }
  }, [selectedModelId]);

  const handleSelectModel = useCallback(async (modelId: string) => {
    setSelectedModelId(modelId);
    try {
      const drift = await api.getModelDrift(modelId);
      setDriftData(drift);
    } catch (err: any) {
      console.error('Failed to load drift for model:', modelId, err);
    }
  }, []);

  const handleSubmitFeedback = useCallback(async (payload: any) => {
    await api.createFeedback(payload);
    await fetchModelsData();
  }, [fetchModelsData]);

  const handleTriggerRetraining = useCallback(async (baseModelId: string) => {
    await api.triggerRetrainingExperiment({ base_model_id: baseModelId });
    await fetchModelsData();
  }, [fetchModelsData]);

  const fetchAll = useCallback(async () => {
    setGlobalLoading(true);
    await Promise.allSettled([
      fetchRun(),
      fetchDisruption(),
      fetchShockwave(),
      fetchRisk(),
      fetchPlans(),
      fetchRecommended(),
      fetchStress(),
      fetchApproval(),
      fetchAlerts(),
      fetchModelsData(),
    ]);
    setGlobalLoading(false);
  }, [
    fetchRun,
    fetchDisruption,
    fetchShockwave,
    fetchRisk,
    fetchPlans,
    fetchRecommended,
    fetchStress,
    fetchApproval,
    fetchAlerts,
    fetchModelsData,
  ]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const activeAlertsCount =
    alertSummary?.active_alerts ??
    alerts.filter((a) => a.acknowledgement_status === 'NEW' || a.acknowledgement_status === 'ACKNOWLEDGED').length;

  const pendingApprovalsCount = approvalData?.current_status === 'PENDING_REVIEW' ? 1 : 0;
  const hasAnyError = Object.values(errors).some((e) => e !== null);

  const handleSelectTab = (tab: NavTabId) => {
    setActiveTab(tab);
    if (typeof window !== 'undefined') {
      window.location.hash = tab;
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex font-sans antialiased">
      {/* 1. Persistent Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={handleSelectTab}
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        activeAlertsCount={activeAlertsCount}
        pendingApprovalsCount={pendingApprovalsCount}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      {/* 2. Main Application Column */}
      <div className="flex-1 flex flex-col min-w-0 transition-all duration-200">
        {activeTab !== 'disruptions' && (
          <TopNavbar
            activeTab={activeTab}
            runData={runData}
            loading={globalLoading}
            onRefresh={fetchAll}
            onOpenMobile={() => setMobileOpen(true)}
          />
        )}

        {/* Global Error Banner */}
        {hasAnyError && (
          <div className="mx-4 sm:mx-6 lg:mx-8 mt-4 p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center justify-between shadow-2xs">
            <div className="flex items-center gap-2.5">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>
                One or more data modules could not reach the backend service at <code className="bg-white px-1.5 py-0.5 rounded border border-amber-200 font-mono text-slate-800">http://127.0.0.1:8001/api</code>. Verify FastAPI is running.
              </span>
            </div>
            <button
              onClick={fetchAll}
              className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white font-semibold transition cursor-pointer shrink-0 ml-4 shadow-2xs"
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* 3. Screen Views Container */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8 max-w-7xl w-full mx-auto">
          {activeTab === 'home' && (
            <HomeScreen
              runData={runData}
              disruption={disruption}
              approvalData={approvalData}
              onNavigate={handleSelectTab}
              onSelectRunId={async (runId) => {
                try {
                  const run = await api.getAnalysisRun(runId);
                  setActiveRunDetail(run);
                } catch {
                  // Fallback: the screen will load it by selectedRunId
                }
                handleSelectTab('analysis_results');
              }}
            />
          )}

          {activeTab === 'dataset_analysis' && (
            <DatasetAnalysisScreen
              onAnalysisStarted={(run) => {
                setActiveRunDetail(run);
                handleSelectTab('analysis_results');
              }}
              onNavigateToResults={() => handleSelectTab('analysis_results')}
            />
          )}

          {activeTab === 'analysis_results' && (
            <AnalysisResultsScreen
              activeRunDetail={activeRunDetail}
              onSelectRunId={async (runId) => {
                try {
                  const run = await api.getAnalysisRun(runId);
                  setActiveRunDetail(run);
                } catch {
                  // Handled within component
                }
              }}
            />
          )}

          {activeTab === 'disruptions' && (
            <DisruptionsScreen
              disruption={disruption}
              shockwave={shockwave}
              risk={_risk}
              runData={runData}
              loading={loadingStates.disruption}
              error={errors.disruption}
              onRetry={fetchDisruption}
              onNavigate={handleSelectTab}
              onOpenMobile={() => setMobileOpen(true)}
            />
          )}

          {activeTab === 'recovery' && (
            <RecoveryPlansScreen
              plans={plans}
              recommendedPlan={recommendedPlan}
              stressTests={stressTests}
              loading={loadingStates.plans || loadingStates.recommended}
              error={errors.plans || errors.recommended}
              onRetry={() => {
                fetchPlans();
                fetchRecommended();
                fetchStress();
              }}
            />
          )}

          {activeTab === 'approvals' && (
            <ApprovalsScreen
              runId={runData?.run_id || 'IRUN-20261104143752-A4CB8F'}
              eventId={disruption?.event_id || 'SIM-DISR-2026-001'}
              recommendedPlan={recommendedPlan}
              approvalData={approvalData}
              alerts={alerts}
              loading={loadingStates.approval}
              error={errors.approval}
              onSubmitDecision={handleSubmitDecision}
              onRefresh={fetchApproval}
            />
          )}

          {activeTab === 'alerts' && (
            <AlertsScreen
              alerts={alerts}
              summary={alertSummary}
              loading={loadingStates.alerts}
              error={errors.alerts}
              onAcknowledge={handleAcknowledgeAlert}
              onResolve={handleResolveAlert}
              onDismiss={handleDismissAlert}
              onRefresh={fetchAlerts}
            />
          )}

          {activeTab === 'models' && (
            <ModelInsightsScreen
              models={models}
              driftData={driftData}
              feedbackRecords={feedbackRecords}
              feedbackSummary={feedbackSummary}
              experiments={experiments}
              selectedModelId={selectedModelId}
              loading={loadingStates.models}
              error={errors.models}
              onSelectModel={handleSelectModel}
              onSubmitFeedback={handleSubmitFeedback}
              onTriggerRetraining={handleTriggerRetraining}
              onRefresh={() => fetchModelsData()}
            />
          )}

          {activeTab === 'settings' && (
            <SettingsScreen onRefreshAll={fetchAll} />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;

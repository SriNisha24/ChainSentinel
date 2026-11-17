// ChainSentinel Phase 11 — Frontend TypeScript Data Contracts
// Matches the FastAPI Pydantic response models in web/backend/models/schemas.py

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  authoritative_run_id: string;
  active_event_id: string;
  data_source_directory: string;
}

export interface RunSummaryResponse {
  run_id: string;
  target_event_id: string;
  status: string;
  execution_start: string;
  execution_end: string;
  stages_completed: string[];
  gates_passed: string[];
  total_execution_duration_seconds: number;
  run_directory: string;
  authoritative_budget_rcu: number;
}

export interface DisruptionEventResponse {
  event_id: string;
  event_type: string;
  disruption_type: string;
  affected_market: string;
  affected_region: string;
  affected_country: string;
  severity: string;
  start_time: string;
  expected_duration_hours: number;
  capacity_reduction_pct: number;
  delay_estimate_hours: number;
  source: string;
  source_confidence: number;
  description: string;
  event_timestamp: string;
  kafka_partition?: number | null;
  kafka_offset?: number | null;
  is_valid: boolean;
  ingestion_timestamp?: string | null;
  source_hdfs_path?: string | null;
  extraction_timestamp?: string | null;
}

export interface ShockwaveEntityCounts {
  total_affected_entities: number;
  unique_affected_orders: number;
  eligible_orders_for_delay: number;
  ineligible_orders_excluded: number;
  unique_affected_customers: number;
  unique_affected_products: number;
  unique_affected_shipping_modes: number;
  unique_affected_regions: number;
  unique_affected_markets: number;
  unique_affected_categories: number;
}

export interface ShockwaveFinancialExposure {
  total_gross_revenue_exposure_usd: number;
  total_gross_profit_exposure_usd: number;
  eligible_revenue_exposure_usd: number;
  eligible_profit_exposure_usd: number;
  ineligible_revenue_excluded_usd: number;
  ineligible_profit_excluded_usd: number;
  accounting_note: string;
}

export interface ShockwaveHistoricalBaseline {
  observed_delayed_orders: number;
  observed_nondelayed_orders: number;
  baseline_delay_rate_pct: number;
}

export interface ShockwaveScenarioProjection {
  scenario_assumed_delay_rate_pct: number;
  scenario_total_assumed_delayed_orders: number;
  scenario_newly_assumed_delayed_orders: number;
  unaffected_eligible_orders: number;
  calculation_nature: string;
  event_delay_estimate_hours: number;
  event_delay_estimate_applied_to_orders: boolean;
}

export interface ShockwaveResponse {
  shockwave_id: string;
  source_event_id: string;
  source_disruption_type: string;
  severity: string;
  source_event_confidence: number;
  capacity_reduction_pct: number;
  event_delay_estimate_hours: number;
  epicenter_nodes: string[];
  contextual_parent_market: string;
  entity_counts: ShockwaveEntityCounts;
  financial_exposure: ShockwaveFinancialExposure;
  historical_baseline: ShockwaveHistoricalBaseline;
  scenario_projection: ShockwaveScenarioProjection;
  assumption_flags: string[];
  execution_time_seconds: number;
}

export interface SeverityDistribution {
  critical_orders: number;
  high_risk_orders: number;
  medium_risk_orders: number;
  low_risk_orders: number;
  ineligible_non_shipped_orders: number;
}

export interface PriorityOrderItem {
  order_id: string;
  risk_score: number;
  risk_level: string;
  risk_priority_rank: number;
  revenue_exposure: number;
  shipping_mode: string;
  customer_segment: string;
  scheduled_transit_days: number;
  primary_risk_driver: string;
  has_pre_existing_anomaly: boolean;
}

export interface RiskSummaryResponse {
  risk_assessment_id: string;
  source_event_id: string;
  shockwave_id: string;
  assessment_timestamp: string;
  score_calibration_status: string;
  order_cohort_summary: Record<string, any>;
  severity_distribution: SeverityDistribution;
  financial_reconciliation: Record<string, any>;
  dimension_weights: Record<string, number>;
  severity_thresholds: Record<string, number>;
  priority_orders_sample: PriorityOrderItem[];
  total_priority_orders_count: number;
}

export interface CandidatePlanItem {
  plan_id: string;
  plan_name: string;
  strategy_type: string;
  capacity_budget_rcu: number;
  allocated_rcu: number;
  unused_rcu: number;
  utilization_pct: number;
  recovered_orders_count: number;
  unrecovered_orders_count: number;
  recovered_critical_orders: number;
  unrecovered_critical_orders: number;
  recovered_high_orders: number;
  unrecovered_high_orders: number;
  expected_mitigated_revenue_usd: number;
  residual_revenue_exposure_usd: number;
  revenue_mitigation_pct: number;
  expected_mitigated_profit_usd: number;
  residual_profit_exposure_usd: number;
  expected_mitigated_risk_points: number;
  residual_risk_points: number;
  effectiveness_score: number;
  robustness_score: number;
  worst_case_survival_score: number;
  resilience_index: number;
  utility_score: number;
}

export interface RecoveryPlansResponse {
  recovery_run_id: string;
  capacity_budget_rcu: number;
  plans: CandidatePlanItem[];
}

export interface RecommendedPlanResponse {
  recommended_plan_id: string;
  recommended_plan_name: string;
  strategy_type: string;
  resilience_index: number;
  utility_score: number;
  selection_rationale: string;
  resource_allocation_summary: {
    capacity_budget_rcu: number;
    allocated_rcu: number;
    unused_rcu: number;
    capacity_utilization_pct: number;
    recovered_orders_count: number;
    unrecovered_orders_count: number;
  };
  financial_mitigation_summary: {
    total_eligible_revenue_usd: number;
    expected_mitigated_revenue_usd: number;
    residual_revenue_exposure_usd: number;
    revenue_mitigation_pct: number;
  };
  risk_mitigation_summary: {
    total_eligible_risk_points: number;
    expected_mitigated_risk_points: number;
    residual_risk_points: number;
    recovered_critical_orders: number;
    unrecovered_critical_orders: number;
    recovered_high_orders: number;
    unrecovered_high_orders: number;
  };
  resilience_components: Record<string, any>;
  counterfactual_stress_summary: Array<{
    scenario_id: string;
    scenario_name: string;
    residual_revenue_usd: number;
    revenue_degradation_pct: number;
    unrecovered_critical_orders: number;
  }>;
  academic_assumptions: string[];
  execution_time_seconds: number;
}

export interface StressTestScenarioItem {
  plan_id: string;
  scenario_id: string;
  scenario_name: string;
  mitigated_revenue_usd: number;
  residual_revenue_usd: number;
  revenue_degradation_pct: number;
  unrecovered_critical_orders: number;
}

export interface StressTestsResponse {
  scenarios: string[];
  plans: string[];
  evaluations: StressTestScenarioItem[];
  total_evaluations_count: number;
}

export interface LineageResponse {
  run_id: string;
  target_event_id: string;
  orchestrator_version: string;
  start_time: string;
  end_time: string;
  status: string;
  stages: Record<string, any>;
  validation_gates: Record<string, any>;
  authoritative_rcu_budget?: number;
}

export type ApprovalDecisionStatus =
  | 'PENDING_REVIEW'
  | 'APPROVED'
  | 'REJECTED'
  | 'REVISION_REQUESTED'
  | 'CLOSED';

export interface ReviewerProfile {
  username: string;
  role: string;
  department?: string;
}

export interface RevisionRequestPayload {
  target_capacity_rcu?: number;
  excluded_modes?: string[];
  target_critical_recovery_pct?: number;
  custom_notes?: string;
}

export interface ApprovalRecord {
  approval_id: string;
  run_id: string;
  event_id: string;
  recommended_plan: string;
  decision_status: ApprovalDecisionStatus;
  reviewer: ReviewerProfile;
  decision_timestamp: string;
  reviewer_comments?: string;
  revision_request?: RevisionRequestPayload | null;
  simulation_watermark: string;
  simulation_only: boolean;
  physical_dispatch_executed: boolean;
}

export interface ApprovalStateResponse {
  run_id: string;
  event_id: string;
  recommended_plan: string;
  current_status: ApprovalDecisionStatus;
  total_decisions_count: number;
  latest_decision?: ApprovalRecord | null;
  history: ApprovalRecord[];
  simulation_only: boolean;
  physical_dispatch_executed: boolean;
  simulation_watermark: string;
}

export interface ApprovalDecisionPayload {
  run_id?: string;
  event_id?: string;
  recommended_plan?: string;
  decision_status: ApprovalDecisionStatus;
  reviewer_username: string;
  reviewer_role: string;
  reviewer_department?: string;
  reviewer_comments: string;
  revision_request?: RevisionRequestPayload | null;
}

// ==============================================================================
// ALERT NOTIFICATION DATA CONTRACTS (PHASE 12)
// ==============================================================================

export type AlertSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
export type AlertStatus = 'NEW' | 'ACKNOWLEDGED' | 'RESOLVED' | 'DISMISSED';

export interface AlertHistoryItem {
  status: string;
  timestamp: string;
  user: string;
  comments?: string | null;
}

export interface AlertRecord {
  alert_id: string;
  event_id: string;
  run_id: string;
  alert_type: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  source_component: string;
  creation_timestamp: string;
  acknowledgement_status: AlertStatus;
  related_entity: string;
  recommended_action: string;
  simulation_only: boolean;
  history: AlertHistoryItem[];
  acknowledged_timestamp?: string | null;
  resolved_timestamp?: string | null;
}

export interface AlertSummaryResponse {
  total_alerts: number;
  active_alerts: number;
  by_status: Record<AlertStatus, number>;
  by_severity: Record<AlertSeverity, number>;
  has_critical_alerts: boolean;
  simulation_only: boolean;
}

// ==============================================================================
// CLOSED-LOOP LEARNING & MODEL MONITORING (PHASE 13)
// ==============================================================================

export type FeedbackType =
  | 'OBSERVED_OPERATIONAL_OUTCOME'
  | 'HUMAN_REVIEW'
  | 'SIMULATION_RESULT'
  | 'MODEL_EVALUATION';

export type ValidationStatus =
  | 'PENDING_VERIFICATION'
  | 'VERIFIED_VALID'
  | 'REJECTED_INVALID'
  | 'SUPERSEDED';

export interface FeedbackRecord {
  feedback_id: string;
  run_id?: string | null;
  event_id?: string | null;
  approval_id?: string | null;
  model_id: string;
  model_version: string;
  feedback_type: FeedbackType;
  predicted_value?: any;
  observed_value?: any;
  feedback_source: string;
  observation_timestamp: string;
  confidence?: number | null;
  validation_status: ValidationStatus;
  comments?: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface FeedbackSummaryResponse {
  total_feedback_records: number;
  model_filter?: string | null;
  feedback_type_breakdown: Record<FeedbackType, number>;
  validation_status_breakdown: Record<ValidationStatus, number>;
  retraining_eligible_count: number;
  average_confidence?: number | null;
  timestamp: string;
}

export interface ModelMetadata {
  model_id: string;
  model_name: string;
  model_type: string;
  status: string;
  version: string;
  deployed_date: string;
  primary_metric_name: string;
  baseline_primary_metric: number;
  baseline_metrics: Record<string, any>;
  key_features: string[];
  leakage_safeguards: string;
}

export interface ModelDriftResponse {
  model_id: string;
  model_version: string;
  evaluation_timestamp: string;
  stability_status: 'STABLE' | 'MODERATE_DRIFT' | 'SIGNIFICANT_DRIFT';
  population_stability_index: number;
  psi_threshold_status: string;
  baseline_metric: { name: string; value: number };
  current_metric: { name: string; value: number };
  metric_delta: number;
  drift_alert_triggered: boolean;
  feature_drift_summary?: Array<{
    feature: string;
    drift_type: string;
    drift_detected: boolean;
    psi: number;
  }>;
  psi_bucket_breakdown?: Array<{
    bucket_index: number;
    range: [number, number];
    expected_count: number;
    actual_count: number;
    expected_pct: number;
    actual_pct: number;
    psi_contribution: number;
  }>;
  recommendation: string;
}

export interface RetrainingExperiment {
  experiment_id: string;
  experiment_name: string;
  base_model_id: string;
  candidate_model_id: string;
  created_at: string;
  triggered_by: string;
  isolation_path: string;
  hyperparameters: Record<string, any>;
  training_dataset_summary: Record<string, any>;
  champion_metrics: Record<string, any>;
  candidate_metrics: Record<string, any>;
  metric_deltas: Record<string, number>;
  challenger_verdict: string;
  promotion_status: string;
  promotion_safeguard: string;
}

export interface UserSession {
  username: string;
  full_name: string;
  role: string;
  department: string;
  authenticated: boolean;
  expires_at?: string | null;
}

export interface AuditLogRecord {
  audit_id: string;
  timestamp: string;
  event_type: string;
  action: string;
  actor: string;
  role: string;
  ip_address: string;
  status: string;
  details: Record<string, any>;
}

// ==============================================================================
// DATASET INTELLIGENCE CONTRACTS
// ==============================================================================

export interface ModelCompatibility {
  status: 'COMPATIBLE' | 'PARTIAL' | 'INCOMPATIBLE';
  match_pct: number;
  matched_features: string[];
  missing_features: string[];
}

export interface DatasetProfile {
  row_count: number;
  column_count: number;
  columns: string[];
  normalized_columns: string[];
  encoding: string;
  missing_summary: Record<string, {
    normalized_name: string;
    dtype: string;
    sample_null_pct: number;
  }>;
  model_compatibility: {
    delay_prediction_v1: ModelCompatibility;
    anomaly_detection_v1: ModelCompatibility;
    disruption_impact_v1: ModelCompatibility;
    demand_forecasting_v1: ModelCompatibility;
  };
}

export interface DatasetMetadata {
  dataset_id: string;
  name: string;
  filename?: string | null;
  description: string;
  file_size_bytes: number;
  created_at: string;
  is_original: boolean;
  is_synthetic?: boolean;
  row_count: number;
  column_count: number;
  encoding: string;
  status: string;
  scenario?: Record<string, any>;
  model_compatibility?: Record<string, any>;
  profile?: DatasetProfile;
}

export interface DatasetPreview {
  dataset_id: string;
  name: string;
  row_count: number;
  column_count: number;
  columns: string[];
  records: Record<string, any>[];
}

export interface DatasetUploadResponse {
  success: boolean;
  message: string;
  dataset: DatasetMetadata;
}

export interface AnalysisRunSummary {
  run_id: string;
  dataset_id: string;
  dataset_name: string;
  created_at: string;
  completed_at?: string | null;
  status: string;
  total_records: number;
  models_executed: string[];
  summary: {
    predicted_delay_rate_pct: number;
    anomalies_detected: number;
    critical_anomalies?: number;
    scenarios_evaluated: number;
    forecast_daily_demand: number;
    capacity_shortfall_orders?: number;
  };
  provenance: string;
}

export interface AnalysisRunDetail {
  run_id: string;
  dataset_id: string;
  dataset_name: string;
  created_at: string;
  completed_at?: string | null;
  duration_seconds: number;
  status: string;
  total_records: number;
  models_executed: string[];
  warnings: string[];
  summary: {
    predicted_delay_rate_pct: number;
    anomalies_detected: number;
    critical_anomalies: number;
    scenarios_evaluated: number;
    forecast_daily_demand: number;
    capacity_shortfall_orders: number;
  };
  results: {
    delay_prediction?: {
      status: string;
      model_id: string;
      model_name: string;
      benchmark_accuracy: number;
      benchmark_roc_auc: number;
      total_records_evaluated: number;
      predicted_delayed_count: number;
      predicted_ontime_count: number;
      predicted_delay_rate_pct: number;
      risk_tier_counts: Record<string, number>;
      sample_predictions: Array<{
        record_id: string;
        order_id: string;
        shipping_mode: string;
        scheduled_days: number;
        product_price: number;
        quantity: number;
        predicted_delay_probability: number;
        predicted_status: string;
        risk_tier: string;
        primary_driver: string;
      }>;
    };
    anomaly_detection?: {
      status: string;
      model_id: string;
      model_name: string;
      total_records_evaluated: number;
      anomalies_detected: number;
      anomaly_rate_pct: number;
      critical_anomalies_count: number;
      category_summary: Record<string, number>;
      sample_anomalies: Array<{
        record_id: string;
        order_id: string;
        order_profit: number;
        order_total: number;
        discount: number;
        cluster_center: number;
        anomaly_score: number;
        anomaly_class: string;
        explanation: string;
        is_anomaly: boolean;
      }>;
    };
    disruption_impact?: {
      status: string;
      model_id: string;
      model_name: string;
      total_dataset_records: number;
      scenarios_evaluated: number;
      scenario_results: Array<{
        scenario_id: string;
        scenario_name: string;
        category: string;
        hypothesis: string;
        impacted_order_items: number;
        impacted_unique_orders: number;
        order_cohort_pct: number;
        revenue_exposure_usd: number;
        profit_exposure_usd: number;
        simulated_delay_shock_days: number;
        capacity_reduction_pct: number;
        severity: string;
      }>;
    };
    demand_forecasting?: {
      status: string;
      model_id: string;
      model_name: string;
      forecast_horizon_days: number;
      baseline_daily_demand: number;
      available_daily_capacity: number;
      target_utilization_pct: number;
      days_with_shortfall: number;
      total_shortfall_orders: number;
      forecast_timeline: Array<{
        day: number;
        forecasted_demand: number;
        available_capacity: number;
        required_capacity: number;
        utilization_pct: number;
        capacity_shortfall: number;
        safety_buffer: number;
        status: string;
      }>;
    };
  };
  provenance: string;
  is_historical: boolean;
}

export interface PaginatedRecordsResponse {
  run_id: string;
  task: string;
  total_records: number;
  page: number;
  page_size: number;
  total_pages: number;
  records: Record<string, any>[];
}

export interface GeoMarker {
  id: string;
  name: string;
  type: 'ORIGIN_HUB' | 'DESTINATION_ORDER' | 'DISRUPTION_HOTSPOT' | 'CUSTOMER_CONSIGNEE';
  lat: number;
  lon: number;
  provenance: string;
  provenance_label: string;
  records_count: number;
  delayed_count: number;
  delay_pct: number;
  revenue_exposure_usd: number;
  severity: 'CRITICAL' | 'HIGH' | 'NOMINAL';
  region?: string;
  market?: string;
  status?: string;
  note?: string;
}

export interface GeoFlow {
  id: string;
  from_lat: number;
  from_lon: number;
  from_name: string;
  to_lat: number;
  to_lon: number;
  to_name: string;
  volume_records: number;
  delayed_volume: number;
  delay_pct: number;
  is_disrupted: boolean;
  color: string;
  provenance: string;
  provenance_label: string;
}

export interface DatasetGeoResponse {
  dataset_id: string;
  filter_type: string;
  total_records_analyzed: number;
  total_dataset_rows: number;
  detected_fields: string[];
  summary: {
    total_markers: number;
    origin_nodes: number;
    destination_nodes: number;
    hotspots_count: number;
    total_revenue_exposure_usd: number;
    delayed_records_count: number;
    avg_delay_rate_pct: number;
  };
  markers: GeoMarker[];
  flows: GeoFlow[];
}






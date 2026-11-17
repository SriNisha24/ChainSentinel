"""
ChainSentinel Phase 11 — Authoritative Data Loader Service
Location: web/backend/services/data_loader.py

Provides strictly read-only, safe, and cached data ingestion from the
authoritative integration run (IRUN-20261104143752-A4CB8F).
Includes PII masking and robust error handling.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import pandas as pd

logger = logging.getLogger("ChainSentinel.DataLoader")
logging.basicConfig(level=logging.INFO)

# Root directory resolution
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, "..", "..", ".."))
DEFAULT_RUN_ID = "IRUN-20261104143752-A4CB8F"


class DataLoaderError(Exception):
    """Raised when an analytical artifact cannot be loaded or parsed."""
    pass


class RunDataLoader:
    """
    Read-only data loader that reads, parses, and formats outputs from
    ChainSentinel integration runs.
    """

    def __init__(self, run_id: str = DEFAULT_RUN_ID, base_runs_dir: Optional[str] = None):
        self.run_id = run_id
        self.base_runs_dir = base_runs_dir or os.path.join(PROJECT_ROOT, "data", "integration_runs")
        self.run_dir = os.path.join(self.base_runs_dir, self.run_id)

        if not os.path.exists(self.run_dir):
            raise DataLoaderError(f"Target integration run directory does not exist: {self.run_dir}")

        # In-memory caches
        self._cache: Dict[str, Any] = {}

    def _load_json(self, relative_path: str) -> Dict[str, Any]:
        """Loads and parses a JSON file safely from the run directory."""
        if relative_path in self._cache:
            return self._cache[relative_path]

        full_path = os.path.join(self.run_dir, relative_path)
        if not os.path.exists(full_path):
            raise DataLoaderError(f"Artifact not found: {relative_path}")

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self._cache[relative_path] = data
                return data
        except json.JSONDecodeError as e:
            raise DataLoaderError(f"Malformed JSON in artifact {relative_path}: {e}")

    def _load_csv(self, relative_path: str) -> pd.DataFrame:
        """Loads a CSV file safely from the run directory."""
        cache_key = f"csv:{relative_path}"
        if cache_key in self._cache:
            return self._cache[cache_key].copy()

        full_path = os.path.join(self.run_dir, relative_path)
        if not os.path.exists(full_path):
            raise DataLoaderError(f"Artifact not found: {relative_path}")

        try:
            df = pd.read_csv(full_path)
            self._cache[cache_key] = df
            return df.copy()
        except Exception as e:
            raise DataLoaderError(f"Error reading CSV artifact {relative_path}: {e}")

    # ==========================================================================
    # 1. RUN & LINEAGE
    # ==========================================================================

    def get_run_summary(self) -> Dict[str, Any]:
        """Returns the executive run summary."""
        summary = self._load_json("run_summary.json")
        lineage = self._load_json("lineage.json")

        t_start = summary.get("execution_start")
        t_end = summary.get("execution_end")
        
        # Calculate total duration if available
        duration = 0.0
        if "stages" in lineage:
            for s in lineage["stages"].values():
                duration += s.get("duration_seconds", 0.0)

        return {
            "run_id": summary.get("run_id", self.run_id),
            "target_event_id": summary.get("target_event_id", "SIM-DISR-2026-001"),
            "status": summary.get("status", "UNKNOWN"),
            "execution_start": t_start or "",
            "execution_end": t_end or "",
            "stages_completed": summary.get("stages_completed", []),
            "gates_passed": summary.get("gates_passed", []),
            "total_execution_duration_seconds": round(duration, 3),
            "run_directory": self.run_dir,
            "authoritative_budget_rcu": 1000.0
        }

    def get_lineage(self) -> Dict[str, Any]:
        """Returns the full end-to-end lineage record."""
        return self._load_json("lineage.json")

    # ==========================================================================
    # 2. DISRUPTION EVENT
    # ==========================================================================

    def get_disruption_event(self) -> Dict[str, Any]:
        """Returns the extracted disruption event with HDFS transport metadata."""
        event = self._load_json(os.path.join("input", "event.json"))
        meta = self._load_json(os.path.join("input", "extraction_metadata.json"))

        return {
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "disruption_type": event.get("disruption_type"),
            "affected_market": event.get("affected_market"),
            "affected_region": event.get("affected_region"),
            "affected_country": event.get("affected_country"),
            "severity": event.get("severity"),
            "start_time": event.get("start_time"),
            "expected_duration_hours": event.get("expected_duration_hours", 0.0),
            "capacity_reduction_pct": event.get("capacity_reduction_pct", 0.0),
            "delay_estimate_hours": event.get("delay_estimate_hours", 0.0),
            "source": event.get("source"),
            "source_confidence": event.get("source_confidence", 0.0),
            "description": event.get("description"),
            "event_timestamp": event.get("event_timestamp"),
            "kafka_partition": event.get("kafka_partition"),
            "kafka_offset": event.get("kafka_offset"),
            "is_valid": event.get("is_valid", True),
            "ingestion_timestamp": event.get("ingestion_timestamp"),
            "source_hdfs_path": meta.get("source_path"),
            "extraction_timestamp": meta.get("extraction_timestamp")
        }

    # ==========================================================================
    # 3. SHOCKWAVE PROPAGATION
    # ==========================================================================

    def get_shockwave_data(self) -> Dict[str, Any]:
        """Returns the shockwave impact summary and baseline comparisons."""
        sum_data = self._load_json(os.path.join("phase8", "shockwave_summary.json"))

        counts = sum_data.get("entity_counts", {})
        fin = sum_data.get("financial_exposure", {})
        hist = sum_data.get("delay_projections", {}).get("historical_baseline", {})
        scen = sum_data.get("delay_projections", {}).get("scenario_projection", {})
        meta = sum_data.get("execution_metadata", {})

        return {
            "shockwave_id": sum_data.get("shockwave_id"),
            "source_event_id": sum_data.get("source_event_id"),
            "source_disruption_type": sum_data.get("source_disruption_type"),
            "severity": sum_data.get("severity"),
            "source_event_confidence": sum_data.get("source_event_confidence", 0.98),
            "capacity_reduction_pct": sum_data.get("capacity_reduction_pct", 100.0),
            "event_delay_estimate_hours": sum_data.get("event_delay_estimate_hours", 96.0),
            "epicenter_nodes": sum_data.get("epicenter_nodes", []),
            "contextual_parent_market": sum_data.get("contextual_parent_market", "MKT_Pacific_Asia"),
            "entity_counts": counts,
            "financial_exposure": fin,
            "historical_baseline": hist,
            "scenario_projection": scen,
            "assumption_flags": sum_data.get("assumption_flags", []),
            "execution_time_seconds": meta.get("execution_time_seconds", 0.259)
        }

    # ==========================================================================
    # 4. RISK ASSESSMENT & PRIORITY QUEUE
    # ==========================================================================

    def get_risk_summary(self, sample_limit: int = 50) -> Dict[str, Any]:
        """Returns the multi-criteria risk assessment summary and sanitized priority orders."""
        r_sum = self._load_json(os.path.join("phase9", "risk_summary.json"))
        df_prio = self._load_csv(os.path.join("phase9", "risk_priority_orders.csv"))

        # PII Masking: Ensure only operational attributes are exposed
        # Allowed fields: entity_id (as order_id), risk_score, risk_level, risk_priority_rank,
        # revenue_exposure, shipping_mode, customer_segment, scheduled_transit_days, primary_risk_driver
        sample_records = []
        for _, row in df_prio.head(sample_limit).iterrows():
            sample_records.append({
                "order_id": str(row.get("entity_id", "")),
                "risk_score": float(row.get("risk_score", 0.0)),
                "risk_level": str(row.get("risk_level", "")),
                "risk_priority_rank": int(row.get("risk_priority_rank", 0)),
                "revenue_exposure": float(row.get("revenue_exposure", 0.0)),
                "shipping_mode": str(row.get("shipping_mode", "Standard Class")),
                "customer_segment": str(row.get("customer_segment", "Consumer")),
                "scheduled_transit_days": int(row.get("scheduled_transit_days", 4)),
                "primary_risk_driver": str(row.get("primary_risk_driver", "Delivery Urgency")),
                "has_pre_existing_anomaly": bool(row.get("has_pre_existing_anomaly", False))
            })

        return {
            "risk_assessment_id": r_sum.get("risk_assessment_id"),
            "source_event_id": r_sum.get("source_event_id"),
            "shockwave_id": r_sum.get("shockwave_id"),
            "assessment_timestamp": r_sum.get("assessment_timestamp"),
            "score_calibration_status": r_sum.get("score_calibration_status"),
            "order_cohort_summary": r_sum.get("order_cohort_summary", {}),
            "severity_distribution": r_sum.get("severity_distribution", {}),
            "financial_reconciliation": r_sum.get("financial_reconciliation", {}),
            "dimension_weights": r_sum.get("dimension_weights", {}),
            "severity_thresholds": r_sum.get("severity_thresholds", {}),
            "priority_orders_sample": sample_records,
            "total_priority_orders_count": len(df_prio)
        }

    # ==========================================================================
    # 5. RECOVERY PLANNING & OPTIMIZATION
    # ==========================================================================

    def get_recovery_plans(self) -> Dict[str, Any]:
        """Returns the comparative metrics for all six candidate recovery plans."""
        df_plans = self._load_csv(os.path.join("phase10", "recovery_plans_comparison.csv"))
        sum_data = self._load_json(os.path.join("phase10", "recovery_summary.json"))

        plans_list = []
        for _, row in df_plans.iterrows():
            plans_list.append({
                "plan_id": str(row.get("plan_id")),
                "plan_name": str(row.get("plan_name")),
                "strategy_type": str(row.get("strategy_type")),
                "capacity_budget_rcu": float(row.get("capacity_budget_rcu", 1000.0)),
                "allocated_rcu": float(row.get("allocated_rcu", 0.0)),
                "unused_rcu": float(row.get("unused_rcu", 0.0)),
                "utilization_pct": float(row.get("utilization_pct", 0.0)),
                "recovered_orders_count": int(row.get("recovered_orders_count", 0)),
                "unrecovered_orders_count": int(row.get("unrecovered_orders_count", 0)),
                "recovered_critical_orders": int(row.get("recovered_critical_orders", 0)),
                "unrecovered_critical_orders": int(row.get("unrecovered_critical_orders", 0)),
                "recovered_high_orders": int(row.get("recovered_high_orders", 0)),
                "unrecovered_high_orders": int(row.get("unrecovered_high_orders", 0)),
                "expected_mitigated_revenue_usd": float(row.get("expected_mitigated_revenue_usd", 0.0)),
                "residual_revenue_exposure_usd": float(row.get("residual_revenue_exposure_usd", 0.0)),
                "revenue_mitigation_pct": float(row.get("revenue_mitigation_pct", 0.0)),
                "expected_mitigated_profit_usd": float(row.get("expected_mitigated_profit_usd", 0.0)),
                "residual_profit_exposure_usd": float(row.get("residual_profit_exposure_usd", 0.0)),
                "expected_mitigated_risk_points": float(row.get("expected_mitigated_risk_points", 0.0)),
                "residual_risk_points": float(row.get("residual_risk_points", 0.0)),
                "effectiveness_score": float(row.get("effectiveness_score", 0.0)),
                "robustness_score": float(row.get("robustness_score", 0.0)),
                "worst_case_survival_score": float(row.get("worst_case_survival_score", 0.0)),
                "resilience_index": float(row.get("resilience_index", 0.0)),
                "utility_score": float(row.get("utility_score", 0.0))
            })

        return {
            "recovery_run_id": sum_data.get("recovery_run_id", ""),
            "capacity_budget_rcu": float(sum_data.get("capacity_budget_rcu", 1000.0)),
            "plans": plans_list
        }

    def get_recommended_plan(self) -> Dict[str, Any]:
        """Returns the full explainability payload for the recommended plan."""
        rec_data = self._load_json(os.path.join("phase10", "recovery_plan_recommended.json"))

        meta = rec_data.get("execution_metadata", {})
        return {
            "recommended_plan_id": rec_data.get("recommended_plan_id"),
            "recommended_plan_name": rec_data.get("recommended_plan_name"),
            "strategy_type": rec_data.get("strategy_type"),
            "resilience_index": rec_data.get("resilience_index", 44.66),
            "utility_score": rec_data.get("utility_score", 0.6481),
            "selection_rationale": rec_data.get("selection_rationale"),
            "resource_allocation_summary": rec_data.get("resource_allocation_summary", {}),
            "financial_mitigation_summary": rec_data.get("financial_mitigation_summary", {}),
            "risk_mitigation_summary": rec_data.get("risk_mitigation_summary", {}),
            "resilience_components": rec_data.get("resilience_components", {}),
            "counterfactual_stress_summary": rec_data.get("counterfactual_stress_summary", []),
            "academic_assumptions": rec_data.get("academic_assumptions", []),
            "execution_time_seconds": meta.get("execution_time_seconds", 0.66)
        }

    def get_stress_tests(self) -> Dict[str, Any]:
        """Returns the complete 30-scenario counterfactual stress evaluation matrix."""
        df_stress = self._load_csv(os.path.join("phase10", "resilience_stress_matrix.csv"))

        evaluations = []
        for _, row in df_stress.iterrows():
            evaluations.append({
                "plan_id": str(row.get("plan_id")),
                "scenario_id": str(row.get("scenario_id")),
                "scenario_name": str(row.get("scenario_name")),
                "mitigated_revenue_usd": float(row.get("mitigated_revenue_usd", 0.0)),
                "residual_revenue_usd": float(row.get("residual_revenue_usd", 0.0)),
                "revenue_degradation_pct": float(row.get("revenue_degradation_pct", 0.0)),
                "unrecovered_critical_orders": int(row.get("unrecovered_critical_orders", 0))
            })

        unique_plans = df_stress["plan_id"].unique().tolist()
        unique_scenarios = df_stress["scenario_id"].unique().tolist()

        return {
            "scenarios": unique_scenarios,
            "plans": unique_plans,
            "evaluations": evaluations,
            "total_evaluations_count": len(evaluations)
        }


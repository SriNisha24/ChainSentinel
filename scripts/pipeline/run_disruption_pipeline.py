#!/usr/bin/env python3
"""
ChainSentinel — Phase 10: End-to-End Sequential Pipeline Orchestrator
======================================================================
Module: scripts/pipeline/run_disruption_pipeline.py
Version: 1.0.0
Framework: Pure Python 3.12 (Subprocess + Standard Library)
Execution Environment: Windows host (E:\\BDA\\ChainSentinel\\python-env)

Purpose:
    Safely orchestrates the full ChainSentinel disruption management pipeline:
        Phase 7 (Extracted HDFS Event)
        -> Phase 8 (Shockwave Propagation)
        -> Phase 9 (Impact Risk Analysis)
        -> Phase 10 (Recovery Planning & Resilience Optimization)
        -> Run Lineage & Decision Artifact Export

Key Guarantees:
    - Default Dry-Run Mode: Generates execution plan, validates schemas, verifies isolation,
      without launching analytical batch processes.
    - Zero Production Overwrite: Strictly writes to `data/integration_runs/<run_id>/`.
    - Zero Spark Contention: Runs host-side using explicit `python-env` interpreter.
    - Rigorous Validation Gates (Gates 1 to 4): Halts immediately upon any anomaly,
      discrepancy, or budget violation.
    - Full Traceability: Exports unified `lineage.json` and `run_summary.json`.
"""

import os
import sys
import json
import time
import uuid
import argparse
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

# Add adapters and streaming paths
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

adapters_dir = os.path.join(project_root, "scripts", "adapters")
if adapters_dir not in sys.path:
    sys.path.insert(0, adapters_dir)

from extract_disruption_event import (
    HDFSEventExtractionAdapter,
    DisruptionExtractionError,
    validate_disruption_dict,
    REQUIRED_FIELDS
)


# ==============================================================================
# 1. ORCHESTRATOR CONFIGURATION & CONSTANTS
# ==============================================================================

AUTHORITATIVE_RCU_BUDGET = 1000.0
DEFAULT_PYTHON_BIN = os.path.join(project_root, "python-env", "Scripts", "python.exe")


class PipelineGateError(Exception):
    """Raised when a stage validation gate fails."""
    def __init__(self, gate_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(f"[{gate_id}] {message}")
        self.gate_id = gate_id
        self.details = details or {}


# ==============================================================================
# 2. DISRUPTION PIPELINE ORCHESTRATOR CLASS
# ==============================================================================

class DisruptionPipelineOrchestrator:
    """
    Coordinates stage-by-stage execution, data contract enforcement,
    and validation gates for ChainSentinel integration runs.
    """

    def __init__(
        self,
        event_id: str = "SIM-DISR-2026-001",
        run_id: Optional[str] = None,
        base_runs_dir: Optional[str] = None,
        python_bin: Optional[str] = None,
        hdfs_dir: str = "/chainsentinel/streaming/disruption_ingestion",
        docker_container: str = "chainsentinel-namenode",
        local_mock_dir: Optional[str] = None
    ):
        self.event_id = event_id
        self.run_id = run_id or f"IRUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        self.base_runs_dir = os.path.abspath(base_runs_dir or os.path.join(project_root, "data", "integration_runs"))
        self.run_dir = os.path.join(self.base_runs_dir, self.run_id)
        self.python_bin = python_bin or DEFAULT_PYTHON_BIN
        self.hdfs_dir = hdfs_dir
        self.docker_container = docker_container
        self.local_mock_dir = local_mock_dir

        # Define isolated subdirectories
        self.input_dir = os.path.join(self.run_dir, "input")
        self.phase8_dir = os.path.join(self.run_dir, "phase8")
        self.phase9_dir = os.path.join(self.run_dir, "phase9")
        self.phase10_dir = os.path.join(self.run_dir, "phase10")
        self.phase10_charts_dir = os.path.join(self.phase10_dir, "charts")

        # Ingestion Adapter
        self.adapter = HDFSEventExtractionAdapter(hdfs_dir=self.hdfs_dir, docker_container=self.docker_container)

        # Lineage and execution state
        self.lineage: Dict[str, Any] = {
            "run_id": self.run_id,
            "target_event_id": self.event_id,
            "orchestrator_version": "1.0.0",
            "start_time": None,
            "end_time": None,
            "status": "INITIALIZED",
            "stages": {},
            "validation_gates": {},
            "authoritative_rcu_budget": AUTHORITATIVE_RCU_BUDGET
        }

    # --------------------------------------------------------------------------
    # Output Isolation Verification
    # --------------------------------------------------------------------------
    def verify_isolation_guarantees(self) -> Tuple[bool, List[str]]:
        """
        Verifies that target run directories are completely disjoint from production outputs.
        """
        protected_paths = [
            os.path.abspath(os.path.join(project_root, "data", "phase8", "output", "task8d_corrected")),
            os.path.abspath(os.path.join(project_root, "data", "phase9", "output")),
            os.path.abspath(os.path.join(project_root, "data", "phase10", "output")),
            os.path.abspath(os.path.join(project_root, "reports", "phase10")),
            os.path.abspath(os.path.join(project_root, "data", "clean_parquet")),
            os.path.abspath(os.path.join(project_root, "data", "phase6"))
        ]

        violations = []
        target_paths = [self.input_dir, self.phase8_dir, self.phase9_dir, self.phase10_dir, self.phase10_charts_dir]

        for tp in target_paths:
            abs_tp = os.path.abspath(tp)
            for pp in protected_paths:
                if abs_tp == pp or abs_tp.startswith(pp + os.sep):
                    violations.append(f"Target path {abs_tp} collides with protected path {pp}")

        return len(violations) == 0, violations

    # --------------------------------------------------------------------------
    # Stage 1: Phase 7 Event Extraction & Gate 1 Validation
    # --------------------------------------------------------------------------
    def stage_1_extract_event(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Extracts disruption event and enforces Validation Gate 1."""
        print(f"\n[STAGE 1] Extracting Disruption Event '{self.event_id}'...")
        t0 = time.time()
        
        event_file, meta_file = self.adapter.extract_and_stage(
            event_id=self.event_id,
            target_dir=self.input_dir,
            run_id=self.run_id,
            local_mock_dir=self.local_mock_dir
        )

        with open(event_file, "r", encoding="utf-8") as f:
            event_dict = json.load(f)
        with open(meta_file, "r", encoding="utf-8") as f:
            meta_dict = json.load(f)

        # Enforce Gate 1
        self._validate_gate_1(event_dict, event_file)

        duration = round(time.time() - t0, 3)
        self.lineage["stages"]["stage_1_event_extraction"] = {
            "status": "SUCCESS",
            "duration_seconds": duration,
            "event_file": event_file,
            "metadata_file": meta_file,
            "source_type": meta_dict.get("source_type"),
            "event_timestamp": event_dict.get("event_timestamp")
        }
        print(f"[STAGE 1 COMPLETED] Extracted & Validated in {duration}s -> {event_file}")
        return event_dict, meta_dict

    def _validate_gate_1(self, event_dict: Dict[str, Any], event_file: str):
        """Validation Gate 1: Strict Event Schema and Integrity Check."""
        gate_id = "GATE_1_EVENT_INTEGRITY"
        print(f" -> Evaluating {gate_id}...")
        
        if not os.path.exists(event_file):
            raise PipelineGateError(gate_id, f"Event file does not exist: {event_file}")

        is_valid, errors = validate_disruption_dict(event_dict)
        if not is_valid:
            raise PipelineGateError(gate_id, f"Event schema validation failed: {'; '.join(errors)}")

        if event_dict.get("event_id") != self.event_id:
            raise PipelineGateError(
                gate_id,
                f"Event ID mismatch: expected '{self.event_id}', found '{event_dict.get('event_id')}'"
            )

        # Check timestamp
        ts = event_dict.get("event_timestamp")
        if not ts:
            raise PipelineGateError(gate_id, "Missing mandatory 'event_timestamp'")

        self.lineage["validation_gates"][gate_id] = {
            "status": "PASSED",
            "event_id": self.event_id,
            "disruption_type": event_dict.get("disruption_type"),
            "severity": event_dict.get("severity"),
            "timestamp_verified": ts
        }
        print(f" -> {gate_id}: PASSED")

    # --------------------------------------------------------------------------
    # Stage 2: Phase 8 Shockwave Engine Execution & Gate 2 Validation
    # --------------------------------------------------------------------------
    def stage_2_run_shockwave(self) -> Dict[str, Any]:
        """Executes Phase 8 shockwave propagation and enforces Validation Gate 2."""
        print(f"\n[STAGE 2] Executing Phase 8 Shockwave Engine...")
        t0 = time.time()
        os.makedirs(self.phase8_dir, exist_ok=True)

        engine_script = os.path.join(project_root, "docker", "spark", "batch", "phase8", "shockwave_engine.py")
        config_path = os.path.join(project_root, "docker", "spark", "batch", "phase8", "shockwave_config.json")
        nodes_path = os.path.join(project_root, "data", "phase6", "graph_nodes.csv")
        edges_path = os.path.join(project_root, "data", "phase6", "graph_edges.csv")
        parquet_path = os.path.join(project_root, "data", "clean_parquet")
        event_path = os.path.join(self.input_dir, "event.json")

        cmd = [
            self.python_bin, engine_script,
            "--event", event_path,
            "--nodes", nodes_path,
            "--edges", edges_path,
            "--parquet", parquet_path,
            "--config", config_path,
            "--output-dir", self.phase8_dir
        ]

        res = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        if res.returncode != 0:
            raise PipelineGateError("GATE_2_SHOCKWAVE", f"Shockwave engine failed with exit code {res.returncode}:\n{res.stderr.strip()}")

        # Load generated summary
        summary_path = os.path.join(self.phase8_dir, "shockwave_summary.json")
        entities_path = os.path.join(self.phase8_dir, "shockwave_entities.csv")

        if not os.path.exists(summary_path) or not os.path.exists(entities_path):
            raise PipelineGateError("GATE_2_SHOCKWAVE", "Shockwave output files were not generated.")

        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        # Enforce Gate 2
        self._validate_gate_2(summary, entities_path)

        duration = round(time.time() - t0, 3)
        self.lineage["stages"]["stage_2_shockwave"] = {
            "status": "SUCCESS",
            "duration_seconds": duration,
            "shockwave_id": summary.get("shockwave_id"),
            "unique_affected_orders": summary["entity_counts"]["unique_affected_orders"],
            "eligible_orders": summary["entity_counts"]["eligible_orders_for_delay"],
            "ineligible_orders": summary["entity_counts"]["ineligible_orders_excluded"],
            "gross_revenue_usd": summary["financial_exposure"]["total_gross_revenue_exposure_usd"],
            "eligible_revenue_usd": summary["financial_exposure"]["eligible_revenue_exposure_usd"]
        }
        print(f"[STAGE 2 COMPLETED] Shockwave finished in {duration}s -> Shockwave ID: {summary.get('shockwave_id')}")
        return summary

    def _validate_gate_2(self, summary: Dict[str, Any], entities_path: str):
        """Validation Gate 2: Cohort counts, lineage match, and financial reconciliation."""
        gate_id = "GATE_2_SHOCKWAVE_RECONCILIATION"
        print(f" -> Evaluating {gate_id}...")

        if summary.get("source_event_id") != self.event_id:
            raise PipelineGateError(gate_id, f"Shockwave source_event_id mismatch: {summary.get('source_event_id')} vs {self.event_id}")

        counts = summary.get("entity_counts", {})
        total_orders = counts.get("unique_affected_orders", 0)
        eligible_orders = counts.get("eligible_orders_for_delay", 0)
        ineligible_orders = counts.get("ineligible_orders_excluded", 0)

        if total_orders <= 0:
            raise PipelineGateError(gate_id, f"Affected order count must be > 0. Found: {total_orders}")

        if total_orders != (eligible_orders + ineligible_orders):
            raise PipelineGateError(
                gate_id,
                f"Cohort count mismatch: total({total_orders}) != eligible({eligible_orders}) + ineligible({ineligible_orders})"
            )

        fin = summary.get("financial_exposure", {})
        gross_rev = fin.get("total_gross_revenue_exposure_usd", 0.0)
        elig_rev = fin.get("eligible_revenue_exposure_usd", 0.0)
        inel_rev = fin.get("ineligible_revenue_excluded_usd", 0.0)

        if abs(gross_rev - (elig_rev + inel_rev)) > 0.05:
            raise PipelineGateError(
                gate_id,
                f"Financial reconciliation error: gross({gross_rev}) != elig({elig_rev}) + inel({inel_rev})"
            )

        self.lineage["validation_gates"][gate_id] = {
            "status": "PASSED",
            "shockwave_id": summary.get("shockwave_id"),
            "total_orders": total_orders,
            "eligible_orders": eligible_orders,
            "ineligible_orders": ineligible_orders,
            "gross_revenue_usd": gross_rev,
            "eligible_revenue_usd": elig_rev,
            "ineligible_revenue_usd": inel_rev
        }
        print(f" -> {gate_id}: PASSED (Orders: {total_orders:,} = {eligible_orders:,} elig + {ineligible_orders:,} inelig | Gross: ${gross_rev:,.2f})")

    # --------------------------------------------------------------------------
    # Stage 3: Phase 9 Impact Risk Engine Execution & Gate 3 Validation
    # --------------------------------------------------------------------------
    def stage_3_run_risk_analysis(self) -> Dict[str, Any]:
        """Executes Phase 9 impact risk analysis and enforces Validation Gate 3."""
        print(f"\n[STAGE 3] Executing Phase 9 Impact Assessment & Risk Analysis Engine...")
        t0 = time.time()
        os.makedirs(self.phase9_dir, exist_ok=True)

        engine_script = os.path.join(project_root, "docker", "spark", "batch", "phase9", "impact_risk_engine.py")
        config_path = os.path.join(project_root, "docker", "spark", "batch", "phase9", "risk_scoring_config.json")
        clean_parquet = os.path.join(project_root, "data", "clean_parquet")
        anomaly_results = os.path.join(project_root, "reports", "phase5", "step2_anomaly_results.csv")
        graph_nodes = os.path.join(project_root, "data", "phase6", "graph_nodes.csv")

        cmd = [
            self.python_bin, engine_script,
            "--config", config_path,
            "--shockwave-dir", self.phase8_dir,
            "--clean-parquet", clean_parquet,
            "--anomaly-results", anomaly_results,
            "--graph-nodes", graph_nodes,
            "--output-dir", self.phase9_dir
        ]

        res = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        if res.returncode != 0:
            raise PipelineGateError("GATE_3_RISK", f"Risk engine failed with exit code {res.returncode}:\n{res.stderr.strip()}")

        summary_path = os.path.join(self.phase9_dir, "risk_summary.json")
        assessments_path = os.path.join(self.phase9_dir, "risk_assessments.csv")
        priority_path = os.path.join(self.phase9_dir, "risk_priority_orders.csv")

        if not os.path.exists(summary_path) or not os.path.exists(assessments_path):
            raise PipelineGateError("GATE_3_RISK", "Risk assessment outputs were not generated.")

        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        # Enforce Gate 3
        self._validate_gate_3(summary, assessments_path, priority_path)

        duration = round(time.time() - t0, 3)
        self.lineage["stages"]["stage_3_risk_analysis"] = {
            "status": "SUCCESS",
            "duration_seconds": duration,
            "risk_assessment_id": summary.get("risk_assessment_id"),
            "total_assessed_orders": summary["order_cohort_summary"]["total_assessed_orders"],
            "eligible_active_orders": summary["order_cohort_summary"]["eligible_active_orders"],
            "ineligible_orders": summary["order_cohort_summary"]["ineligible_non_shipped_orders"],
            "critical_orders": summary["severity_distribution"]["critical_orders"],
            "high_risk_orders": summary["severity_distribution"]["high_risk_orders"],
            "gross_revenue_usd": summary["financial_reconciliation"]["total_gross_revenue_usd"]
        }
        print(f"[STAGE 3 COMPLETED] Risk Analysis finished in {duration}s -> Risk ID: {summary.get('risk_assessment_id')}")
        return summary

    def _validate_gate_3(self, summary: Dict[str, Any], assessments_path: str, priority_path: str):
        """Validation Gate 3: Exact cohort preservation, severity distribution, and financial consistency."""
        gate_id = "GATE_3_RISK_COHORT_INTEGRITY"
        print(f" -> Evaluating {gate_id}...")

        # Cross-reference with Phase 8
        p8_stage = self.lineage["stages"].get("stage_2_shockwave", {})
        expected_total = p8_stage.get("unique_affected_orders")
        expected_gross = p8_stage.get("gross_revenue_usd")

        cohort = summary.get("order_cohort_summary", {})
        total_assessed = cohort.get("total_assessed_orders")
        eligible_orders = cohort.get("eligible_active_orders")
        ineligible_orders = cohort.get("ineligible_non_shipped_orders")

        if expected_total is not None and total_assessed != expected_total:
            raise PipelineGateError(
                gate_id,
                f"Cohort count mismatch between Phase 8 ({expected_total}) and Phase 9 ({total_assessed})"
            )

        if total_assessed != (eligible_orders + ineligible_orders):
            raise PipelineGateError(
                gate_id,
                f"Phase 9 internal cohort mismatch: {total_assessed} != {eligible_orders} + {ineligible_orders}"
            )

        fin = summary.get("financial_reconciliation", {})
        gross_rev = fin.get("total_gross_revenue_usd", 0.0)
        if expected_gross is not None and abs(gross_rev - expected_gross) > 0.05:
            raise PipelineGateError(
                gate_id,
                f"Revenue mismatch between Phase 8 (${expected_gross:,.2f}) and Phase 9 (${gross_rev:,.2f})"
            )

        sev = summary.get("severity_distribution", {})
        crit = sev.get("critical_orders", 0)
        high = sev.get("high_risk_orders", 0)

        self.lineage["validation_gates"][gate_id] = {
            "status": "PASSED",
            "risk_assessment_id": summary.get("risk_assessment_id"),
            "total_assessed_orders": total_assessed,
            "eligible_active_orders": eligible_orders,
            "ineligible_non_shipped_orders": ineligible_orders,
            "critical_orders": crit,
            "high_risk_orders": high,
            "gross_revenue_usd": gross_rev
        }
        print(f" -> {gate_id}: PASSED (Total: {total_assessed:,} | Crit: {crit}, High: {high} | Rev: ${gross_rev:,.2f})")

    # --------------------------------------------------------------------------
    # Stage 4: Phase 10 Recovery Planning & Gate 4 Validation
    # --------------------------------------------------------------------------
    def stage_4_run_recovery(self) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Executes Phase 10 recovery optimization and enforces Validation Gate 4."""
        print(f"\n[STAGE 4] Executing Phase 10 Recovery Planning & Resilience Optimization Engine...")
        t0 = time.time()
        os.makedirs(self.phase10_dir, exist_ok=True)
        os.makedirs(self.phase10_charts_dir, exist_ok=True)

        engine_script = os.path.join(project_root, "docker", "spark", "batch", "phase10", "recovery_engine.py")
        config_path = os.path.join(project_root, "docker", "spark", "batch", "phase10", "recovery_config.json")
        risk_assessments = os.path.join(self.phase9_dir, "risk_assessments.csv")
        risk_priority = os.path.join(self.phase9_dir, "risk_priority_orders.csv")
        risk_summary = os.path.join(self.phase9_dir, "risk_summary.json")

        cmd = [
            self.python_bin, engine_script,
            "--config", config_path,
            "--risk-assessments", risk_assessments,
            "--risk-priority", risk_priority,
            "--risk-summary", risk_summary,
            "--output-dir", self.phase10_dir,
            "--reports-dir", self.phase10_charts_dir
        ]

        res = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        if res.returncode != 0:
            raise PipelineGateError("GATE_4_RECOVERY", f"Recovery engine failed with exit code {res.returncode}:\n{res.stderr.strip()}")

        summary_path = os.path.join(self.phase10_dir, "recovery_summary.json")
        rec_plan_path = os.path.join(self.phase10_dir, "recovery_plan_recommended.json")
        alloc_path = os.path.join(self.phase10_dir, "recovery_order_allocations.csv")
        stress_path = os.path.join(self.phase10_dir, "resilience_stress_matrix.csv")

        if not os.path.exists(summary_path) or not os.path.exists(rec_plan_path) or not os.path.exists(alloc_path):
            raise PipelineGateError("GATE_4_RECOVERY", "Recovery engine outputs were not generated.")

        with open(summary_path, "r", encoding="utf-8") as f:
            recovery_summary = json.load(f)
        with open(rec_plan_path, "r", encoding="utf-8") as f:
            recommended_plan = json.load(f)

        # Enforce Gate 4
        self._validate_gate_4(recovery_summary, recommended_plan, alloc_path, stress_path)

        duration = round(time.time() - t0, 3)
        self.lineage["stages"]["stage_4_recovery_optimization"] = {
            "status": "SUCCESS",
            "duration_seconds": duration,
            "recovery_run_id": recovery_summary.get("recovery_run_id"),
            "recommended_plan_id": recommended_plan.get("recommended_plan_id"),
            "recommended_plan_name": recommended_plan.get("recommended_plan_name"),
            "resilience_index": recommended_plan.get("resilience_index"),
            "allocated_rcu": recommended_plan["resource_allocation_summary"]["allocated_rcu"],
            "recovered_orders_count": recommended_plan["resource_allocation_summary"]["recovered_orders_count"],
            "mitigated_revenue_usd": recommended_plan["financial_mitigation_summary"]["expected_mitigated_revenue_usd"]
        }
        print(f"[STAGE 4 COMPLETED] Recovery Optimization finished in {duration}s -> Plan: {recommended_plan.get('recommended_plan_id')}")
        return recovery_summary, recommended_plan

    def _validate_gate_4(
        self,
        summary: Dict[str, Any],
        rec_plan: Dict[str, Any],
        alloc_path: str,
        stress_path: str
    ):
        """Validation Gate 4: Budget adherence, ineligible order zero-spend, and complete stress matrix."""
        gate_id = "GATE_4_OPTIMIZATION_BOUNDS"
        print(f" -> Evaluating {gate_id}...")

        # 1. Budget Adherence Check
        res_summary = rec_plan.get("resource_allocation_summary", {})
        allocated_rcu = res_summary.get("allocated_rcu", 0.0)
        budget = summary.get("capacity_budget_rcu", 0.0)

        if budget != AUTHORITATIVE_RCU_BUDGET:
            raise PipelineGateError(
                gate_id,
                f"Authoritative budget discrepancy: configured {budget} != expected {AUTHORITATIVE_RCU_BUDGET}"
            )

        if allocated_rcu > budget:
            raise PipelineGateError(
                gate_id,
                f"Budget violation: allocated RCU ({allocated_rcu:.2f}) exceeds budget ({budget:.2f})"
            )

        # 2. Check Allocations CSV for Ineligible Orders
        # Ineligible orders must have x_{i,p} == 0 across all plans
        with open(alloc_path, "r", encoding="utf-8") as f:
            header = f.readline().strip().split(",")
            is_elig_idx = header.index("is_eligible_for_delay") if "is_eligible_for_delay" in header else -1
            # Check all plan allocation columns
            plan_col_indices = [i for i, h in enumerate(header) if h.startswith("allocated_plan_")]

            if is_elig_idx != -1 and plan_col_indices:
                for line_no, line in enumerate(f, start=2):
                    parts = line.strip().split(",")
                    is_elig = parts[is_elig_idx].lower() in ["true", "1"]
                    if not is_elig:
                        for p_idx in plan_col_indices:
                            val = parts[p_idx].strip()
                            if val not in ["0", "0.0", "False", "false", ""]:
                                raise PipelineGateError(
                                    gate_id,
                                    f"Ineligible order received non-zero allocation at row {line_no}: column {header[p_idx]} = {val}"
                                )

        # 3. Check Stress Matrix
        with open(stress_path, "r", encoding="utf-8") as f:
            stress_rows = len(f.readlines()) - 1
            if stress_rows != 30: # 6 plans * 5 scenarios = 30 evaluations
                raise PipelineGateError(
                    gate_id,
                    f"Incomplete stress test evaluation matrix: expected 30 rows, found {stress_rows}"
                )

        # 4. Check Financial Mitigation Consistency
        fin_mit = rec_plan.get("financial_mitigation_summary", {})
        mit_rev = fin_mit.get("expected_mitigated_revenue_usd", 0.0)
        res_rev = fin_mit.get("residual_revenue_exposure_usd", 0.0)
        tot_elig = fin_mit.get("total_eligible_revenue_usd", 0.0)

        if abs((mit_rev + res_rev) - tot_elig) > 0.10:
            raise PipelineGateError(
                gate_id,
                f"Financial mitigation reconciliation error: mitigated({mit_rev}) + residual({res_rev}) != eligible({tot_elig})"
            )

        self.lineage["validation_gates"][gate_id] = {
            "status": "PASSED",
            "capacity_budget_rcu": budget,
            "allocated_rcu": allocated_rcu,
            "capacity_utilization_pct": res_summary.get("capacity_utilization_pct"),
            "recovered_orders_count": res_summary.get("recovered_orders_count"),
            "resilience_index": rec_plan.get("resilience_index"),
            "stress_evaluations_count": stress_rows
        }
        print(f" -> {gate_id}: PASSED (RCU Allocated: {allocated_rcu:,.1f} / {budget:,.1f} | Recovered: {res_summary.get('recovered_orders_count'):,} orders | Resilience: {rec_plan.get('resilience_index')})")

    # --------------------------------------------------------------------------
    # Finalize Lineage and Run Summary
    # --------------------------------------------------------------------------
    def finalize_run(self, final_status: str = "SUCCESS"):
        """Exports unified lineage record and run summary."""
        self.lineage["status"] = final_status
        self.lineage["end_time"] = datetime.now(timezone.utc).isoformat()

        lineage_path = os.path.join(self.run_dir, "lineage.json")
        summary_path = os.path.join(self.run_dir, "run_summary.json")

        with open(lineage_path, "w", encoding="utf-8") as f:
            json.dump(self.lineage, f, indent=2)

        run_summary = {
            "run_id": self.run_id,
            "target_event_id": self.event_id,
            "status": final_status,
            "execution_start": self.lineage.get("start_time"),
            "execution_end": self.lineage.get("end_time"),
            "stages_completed": list(self.lineage.get("stages", {}).keys()),
            "gates_passed": [k for k, v in self.lineage.get("validation_gates", {}).items() if v.get("status") == "PASSED"],
            "run_directory": self.run_dir
        }

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(run_summary, f, indent=2)

        return lineage_path, summary_path

    # --------------------------------------------------------------------------
    # Dry-Run Mode Planner
    # --------------------------------------------------------------------------
    def execute_dry_run(self) -> Dict[str, Any]:
        """
        Executes safe dry-run mode:
        - Extracts event and validates schema
        - Verifies output isolation
        - Confirms presence of all upstream dependencies and scripts
        - Generates execution plan without running batch compute
        """
        print("\n" + "=" * 78)
        print(f"CHAINSETINEL PIPELINE ORCHESTRATOR — DRY RUN MODE")
        print(f"Run ID:   {self.run_id}")
        print(f"Event ID: {self.event_id}")
        print(f"Target:   {self.run_dir}")
        print("=" * 78)

        self.lineage["start_time"] = datetime.now(timezone.utc).isoformat()
        os.makedirs(self.run_dir, exist_ok=True)

        # 1. Verify Isolation
        is_isolated, violations = self.verify_isolation_guarantees()
        if not is_isolated:
            raise PipelineGateError("ISOLATION_CHECK", f"Output isolation violated: {'; '.join(violations)}")
        print("[CHECK 1] Output isolation verified: Zero collision with production folders.")

        # 2. Extract Event & Validate Gate 1
        event_dict, meta_dict = self.stage_1_extract_event()
        print(f"[CHECK 2] Phase 7 event verified: {event_dict.get('disruption_type')} in {event_dict.get('affected_market')}")

        # 3. Verify Downstream Dependencies
        scripts_to_check = [
            ("Phase 8 Engine", os.path.join(project_root, "docker", "spark", "batch", "phase8", "shockwave_engine.py")),
            ("Phase 8 Config", os.path.join(project_root, "docker", "spark", "batch", "phase8", "shockwave_config.json")),
            ("Phase 9 Engine", os.path.join(project_root, "docker", "spark", "batch", "phase9", "impact_risk_engine.py")),
            ("Phase 9 Config", os.path.join(project_root, "docker", "spark", "batch", "phase9", "risk_scoring_config.json")),
            ("Phase 10 Engine", os.path.join(project_root, "docker", "spark", "batch", "phase10", "recovery_engine.py")),
            ("Phase 10 Config", os.path.join(project_root, "docker", "spark", "batch", "phase10", "recovery_config.json")),
            ("Graph Nodes", os.path.join(project_root, "data", "phase6", "graph_nodes.csv")),
            ("Graph Edges", os.path.join(project_root, "data", "phase6", "graph_edges.csv")),
            ("Clean Parquet", os.path.join(project_root, "data", "clean_parquet"))
        ]

        missing_deps = []
        for name, path in scripts_to_check:
            if not os.path.exists(path):
                missing_deps.append(f"{name} ({path})")

        if missing_deps:
            raise PipelineGateError("DEPENDENCY_CHECK", f"Missing upstream dependencies: {', '.join(missing_deps)}")
        print(f"[CHECK 3] All {len(scripts_to_check)} analytical dependencies verified present.")

        # 4. Generate Dry-Run Plan
        plan = {
            "run_id": self.run_id,
            "mode": "DRY_RUN",
            "event_id": self.event_id,
            "event_summary": {
                "event_type": event_dict.get("event_type"),
                "disruption_type": event_dict.get("disruption_type"),
                "severity": event_dict.get("severity"),
                "market": event_dict.get("affected_market"),
                "expected_duration_hours": event_dict.get("expected_duration_hours")
            },
            "authoritative_budget_rcu": AUTHORITATIVE_RCU_BUDGET,
            "isolated_paths": {
                "run_directory": self.run_dir,
                "input_event": os.path.join(self.input_dir, "event.json"),
                "phase8_output": self.phase8_dir,
                "phase9_output": self.phase9_dir,
                "phase10_output": self.phase10_dir,
                "phase10_charts": self.phase10_charts_dir
            },
            "scheduled_stages": [
                {"stage": 1, "name": "Extract & Validate Event", "status": "COMPLETED_IN_DRY_RUN"},
                {"stage": 2, "name": "Shockwave Propagation", "status": "READY_FOR_EXECUTION"},
                {"stage": 3, "name": "Impact Risk Assessment", "status": "READY_FOR_EXECUTION"},
                {"stage": 4, "name": "Recovery Planning & Stress Testing", "status": "READY_FOR_EXECUTION"},
                {"stage": 5, "name": "Unified Lineage Finalization", "status": "READY_FOR_EXECUTION"}
            ],
            "dry_run_timestamp": datetime.now(timezone.utc).isoformat()
        }

        plan_path = os.path.join(self.run_dir, "run_plan.json")
        with open(plan_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)

        self.finalize_run(final_status="DRY_RUN_PASSED")

        print("\n" + "=" * 78)
        print("DRY RUN VALIDATION SUCCEEDED:")
        print(f" - Run Directory: {self.run_dir}")
        print(f" - Staged Event:  {os.path.join(self.input_dir, 'event.json')}")
        print(f" - Execution Plan:{plan_path}")
        print("All validation checks, schema verifications, and isolation bounds PASSED.")
        print("=" * 78)
        return plan

    # --------------------------------------------------------------------------
    # Live Isolated Execution Mode
    # --------------------------------------------------------------------------
    def execute_pipeline(self) -> Dict[str, Any]:
        """
        Executes all stages sequentially with strict validation gate enforcement.
        """
        print("\n" + "=" * 78)
        print(f"CHAINSETINEL PIPELINE ORCHESTRATOR — ISOLATED LIVE EXECUTION")
        print(f"Run ID:   {self.run_id}")
        print(f"Event ID: {self.event_id}")
        print(f"Target:   {self.run_dir}")
        print("=" * 78)

        self.lineage["start_time"] = datetime.now(timezone.utc).isoformat()
        os.makedirs(self.run_dir, exist_ok=True)

        # 0. Check Isolation
        is_isolated, violations = self.verify_isolation_guarantees()
        if not is_isolated:
            raise PipelineGateError("ISOLATION_CHECK", f"Output isolation violated: {'; '.join(violations)}")

        try:
            # Stage 1: Extraction & Gate 1
            event_dict, meta_dict = self.stage_1_extract_event()

            # Stage 2: Shockwave & Gate 2
            p8_summary = self.stage_2_run_shockwave()

            # Stage 3: Risk Assessment & Gate 3
            p9_summary = self.stage_3_run_risk_analysis()

            # Stage 4: Recovery Planning & Gate 4
            p10_summary, rec_plan = self.stage_4_run_recovery()

            # Finalize
            lineage_path, summary_path = self.finalize_run(final_status="SUCCESS")

            print("\n" + "=" * 78)
            print("END-TO-END PIPELINE EXECUTION COMPLETED SUCCESSFULLY!")
            print(f" - Run Directory:   {self.run_dir}")
            print(f" - Lineage Record:  {lineage_path}")
            print(f" - Run Summary:     {summary_path}")
            print(f" - Recommended Plan:{rec_plan.get('recommended_plan_id')} ({rec_plan.get('recommended_plan_name')})")
            print(f" - Resilience Index:{rec_plan.get('resilience_index')} / 100")
            print("=" * 78)

            return {
                "run_id": self.run_id,
                "status": "SUCCESS",
                "recommended_plan": rec_plan.get("recommended_plan_id"),
                "resilience_index": rec_plan.get("resilience_index"),
                "run_dir": self.run_dir
            }

        except PipelineGateError as e:
            print(f"\n[FATAL ERROR] Pipeline halted at {e.gate_id}: {e}", file=sys.stderr)
            self.finalize_run(final_status=f"FAILED_{e.gate_id}")
            raise


# ==============================================================================
# 3. CLI ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="ChainSentinel End-to-End Sequential Disruption Pipeline Orchestrator"
    )
    parser.add_argument("--event-id", "-e", default="SIM-DISR-2026-001", help="Disruption event ID to process")
    parser.add_argument("--run-id", default=None, help="Execution run identifier (auto-generated if omitted)")
    parser.add_argument("--runs-dir", default=None, help="Base directory for integration run outputs")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Execute dry-run validation mode (DEFAULT)")
    parser.add_argument("--execute", action="store_true", default=False, help="Explicitly execute full isolated pipeline")
    parser.add_argument("--hdfs-dir", default="/chainsentinel/streaming/disruption_ingestion", help="HDFS source directory")
    parser.add_argument("--local-mock-dir", default=None, help="Optional local directory of mock part files for offline testing")
    parser.add_argument("--python-bin", default=None, help="Path to python-env executable")
    parser.add_argument("--container", default="chainsentinel-namenode", help="NameNode Docker container name")

    args = parser.parse_args()

    # Determine execution mode: --execute overrides default --dry-run
    is_live_execute = args.execute

    orchestrator = DisruptionPipelineOrchestrator(
        event_id=args.event_id,
        run_id=args.run_id,
        base_runs_dir=args.runs_dir,
        python_bin=args.python_bin,
        hdfs_dir=args.hdfs_dir,
        docker_container=args.container,
        local_mock_dir=args.local_mock_dir
    )

    try:
        if is_live_execute:
            orchestrator.execute_pipeline()
        else:
            orchestrator.execute_dry_run()
        sys.exit(0)
    except Exception as e:
        print(f"\nExecution terminated with error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


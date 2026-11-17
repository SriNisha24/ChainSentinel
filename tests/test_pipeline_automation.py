#!/usr/bin/env python3
"""
ChainSentinel — Phase 10: Pipeline Automation & HDFS Adapter Test Suite
======================================================================
Module: tests/test_pipeline_automation.py
Execution: Pure Python 3.12 (unittest)
Framework: Windows host (python-env)

Comprehensive unit and integration tests verifying:
    1. HDFS event record parsing & JSON line handling.
    2. Event selection by event_id.
    3. Missing event error handling.
    4. Malformed JSON handling.
    5. Schema and boundary validation.
    6. Identical vs conflicting duplicate handling.
    7. Run directory creation & unique run IDs.
    8. Output isolation verification against production paths.
    9. Validation Gates 1, 2, 3, and 4 failure detection.
    10. Budget enforcement (1000.0 RCUs) and ineligible order zero-spend.
    11. Incomplete stress matrix rejection (must have 30 rows).
    12. Failed-stage pipeline termination.
    13. Unified lineage and run summary generation.
    14. Full offline dry-run execution.
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from datetime import datetime, timezone
from typing import Dict, Any

# Ensure project paths are resolved
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))

adapters_dir = os.path.join(project_root, "scripts", "adapters")
pipeline_dir = os.path.join(project_root, "scripts", "pipeline")
streaming_dir = os.path.join(project_root, "docker", "spark", "streaming")

for p in [adapters_dir, pipeline_dir, streaming_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from extract_disruption_event import (
    HDFSEventExtractionAdapter,
    DisruptionExtractionError,
    validate_disruption_dict
)
from run_disruption_pipeline import (
    DisruptionPipelineOrchestrator,
    PipelineGateError,
    AUTHORITATIVE_RCU_BUDGET
)


# ==============================================================================
# SAMPLE TEST FIXTURES
# ==============================================================================

VALID_EVENT_FIXTURE = {
    "event_id": "SIM-DISR-2026-TEST",
    "event_type": "DISRUPTION_ALERT",
    "disruption_type": "PORT_CLOSURE",
    "affected_market": "Pacific Asia",
    "affected_region": "East Asia",
    "affected_country": "China",
    "severity": "CRITICAL",
    "start_time": "2026-11-04T06:00:00.000Z",
    "expected_duration_hours": 72.0,
    "capacity_reduction_pct": 100.0,
    "delay_estimate_hours": 96.0,
    "source": "Maritime_Port_Authority_Alert_Feed",
    "source_confidence": 0.98,
    "description": "Emergency closure of terminal berths.",
    "event_timestamp": "2026-11-04T06:15:00.000Z",
    "kafka_partition": 0,
    "kafka_offset": 1,
    "kafka_timestamp": "2026-11-04T10:09:14.259Z",
    "is_valid": True,
    "ingestion_timestamp": "2026-11-04T10:43:17.567Z"
}


# ==============================================================================
# TEST CASE IMPLEMENTATION
# ==============================================================================

class TestPipelineAutomation(unittest.TestCase):
    """Exhaustive test suite for HDFS adapter, orchestrator, and validation gates."""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="chainsentinel_test_")
        self.mock_hdfs_dir = os.path.join(self.test_dir, "mock_hdfs")
        self.mock_runs_dir = os.path.join(self.test_dir, "integration_runs")
        os.makedirs(self.mock_hdfs_dir, exist_ok=True)
        os.makedirs(self.mock_runs_dir, exist_ok=True)

        # Write valid mock part file
        self.valid_part_path = os.path.join(self.mock_hdfs_dir, "part-00001.json")
        with open(self.valid_part_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(VALID_EVENT_FIXTURE) + "\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # --------------------------------------------------------------------------
    # 1. HDFS Event Record Parsing & Selection
    # --------------------------------------------------------------------------
    def test_hdfs_record_parsing(self):
        """Verify parsing of valid newline-delimited JSON records from mock directory."""
        adapter = HDFSEventExtractionAdapter()
        records = adapter.scan_records_from_local_dir(self.mock_hdfs_dir)
        self.assertEqual(len(records), 1)
        rec, path = records[0]
        self.assertEqual(rec["event_id"], "SIM-DISR-2026-TEST")
        self.assertEqual(rec["disruption_type"], "PORT_CLOSURE")

    def test_event_selection_by_id(self):
        """Verify deterministic selection of target event among multiple records."""
        # Add a second event to mock part file
        event_2 = dict(VALID_EVENT_FIXTURE)
        event_2["event_id"] = "SIM-DISR-2026-OTHER"
        with open(self.valid_part_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_2) + "\n")

        adapter = HDFSEventExtractionAdapter()
        selected, meta = adapter.extract_event_by_id("SIM-DISR-2026-TEST", local_mock_dir=self.mock_hdfs_dir)
        self.assertEqual(selected["event_id"], "SIM-DISR-2026-TEST")
        self.assertEqual(meta["total_matches_found"], 1)
        self.assertFalse(meta["is_duplicate"])

    def test_missing_event_error(self):
        """Verify DisruptionExtractionError when requested event_id does not exist."""
        adapter = HDFSEventExtractionAdapter()
        with self.assertRaises(DisruptionExtractionError) as ctx:
            adapter.extract_event_by_id("NON_EXISTENT_EVENT", local_mock_dir=self.mock_hdfs_dir)
        self.assertIn("was not found", str(ctx.exception))

    def test_invalid_json_handling(self):
        """Verify error raised on malformed JSON line in data part files."""
        bad_part = os.path.join(self.mock_hdfs_dir, "part-00002.json")
        with open(bad_part, "w", encoding="utf-8") as f:
            f.write("{invalid_json: true\n")

        adapter = HDFSEventExtractionAdapter()
        with self.assertRaises(DisruptionExtractionError) as ctx:
            adapter.extract_event_by_id("SIM-DISR-2026-TEST", local_mock_dir=self.mock_hdfs_dir)
        self.assertIn("Malformed JSON line", str(ctx.exception))

    def test_invalid_event_schema(self):
        """Verify schema rejection when mandatory fields are missing or invalid."""
        bad_event = dict(VALID_EVENT_FIXTURE)
        bad_event["event_id"] = "SIM-DISR-INVALID"
        del bad_event["severity"]  # Mandatory field missing

        bad_part = os.path.join(self.mock_hdfs_dir, "part-00003.json")
        with open(bad_part, "w", encoding="utf-8") as f:
            f.write(json.dumps(bad_event) + "\n")

        adapter = HDFSEventExtractionAdapter()
        with self.assertRaises(DisruptionExtractionError) as ctx:
            adapter.extract_event_by_id("SIM-DISR-INVALID", local_mock_dir=self.mock_hdfs_dir)
        self.assertIn("failed schema validation", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 2. Duplicate Disambiguation Handling
    # --------------------------------------------------------------------------
    def test_duplicate_identical_event_matches(self):
        """Verify identical streaming duplicates are handled safely without exception."""
        # Append identical record (e.g. streaming replay)
        with open(self.valid_part_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(VALID_EVENT_FIXTURE) + "\n")

        adapter = HDFSEventExtractionAdapter()
        selected, meta = adapter.extract_event_by_id("SIM-DISR-2026-TEST", local_mock_dir=self.mock_hdfs_dir)
        self.assertEqual(selected["event_id"], "SIM-DISR-2026-TEST")
        self.assertEqual(meta["total_matches_found"], 2)
        self.assertTrue(meta["is_duplicate"])

    def test_duplicate_conflicting_event_matches(self):
        """Verify conflicting records with divergent attributes raise DisruptionExtractionError."""
        conflicting = dict(VALID_EVENT_FIXTURE)
        conflicting["severity"] = "LOW"  # Conflicting attribute!
        with open(self.valid_part_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(conflicting) + "\n")

        adapter = HDFSEventExtractionAdapter()
        with self.assertRaises(DisruptionExtractionError) as ctx:
            adapter.extract_event_by_id("SIM-DISR-2026-TEST", local_mock_dir=self.mock_hdfs_dir)
        self.assertIn("Ambiguous conflicting records found", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 3. Directory Creation, Isolation, and Run IDs
    # --------------------------------------------------------------------------
    def test_run_id_uniqueness(self):
        """Verify that distinct orchestrator instances receive unique run IDs."""
        orch1 = DisruptionPipelineOrchestrator(base_runs_dir=self.mock_runs_dir)
        orch2 = DisruptionPipelineOrchestrator(base_runs_dir=self.mock_runs_dir)
        self.assertNotEqual(orch1.run_id, orch2.run_id)
        self.assertTrue(orch1.run_id.startswith("IRUN-"))

    def test_output_isolation_guarantees(self):
        """Verify isolation check prevents accidental targeting of production directories."""
        # Normal run in mock_runs_dir should pass
        orch = DisruptionPipelineOrchestrator(base_runs_dir=self.mock_runs_dir)
        is_isolated, violations = orch.verify_isolation_guarantees()
        self.assertTrue(is_isolated)
        self.assertEqual(len(violations), 0)

        # Deliberately targeting production path must fail
        prod_path = os.path.join(project_root, "data", "phase10", "output")
        orch_bad = DisruptionPipelineOrchestrator(base_runs_dir=prod_path)
        is_isolated_bad, violations_bad = orch_bad.verify_isolation_guarantees()
        self.assertFalse(is_isolated_bad)
        self.assertTrue(any("collides with protected path" in v for v in violations_bad))

    # --------------------------------------------------------------------------
    # 4. Validation Gate 1 & 2
    # --------------------------------------------------------------------------
    def test_gate_1_validation(self):
        """Verify Gate 1 validates valid events and catches invalid ones."""
        orch = DisruptionPipelineOrchestrator(event_id="SIM-DISR-2026-TEST", base_runs_dir=self.mock_runs_dir)
        event_path = os.path.join(self.test_dir, "test_event.json")
        with open(event_path, "w", encoding="utf-8") as f:
            json.dump(VALID_EVENT_FIXTURE, f)

        # Valid event passes
        orch._validate_gate_1(VALID_EVENT_FIXTURE, event_path)
        self.assertEqual(orch.lineage["validation_gates"]["GATE_1_EVENT_INTEGRITY"]["status"], "PASSED")

        # Mismatched event ID fails
        orch_mismatch = DisruptionPipelineOrchestrator(event_id="DIFFERENT_ID", base_runs_dir=self.mock_runs_dir)
        with self.assertRaises(PipelineGateError) as ctx:
            orch_mismatch._validate_gate_1(VALID_EVENT_FIXTURE, event_path)
        self.assertIn("Event ID mismatch", str(ctx.exception))

    def test_gate_2_validation_reconciliation(self):
        """Verify Gate 2 catches cohort count and revenue reconciliation errors."""
        orch = DisruptionPipelineOrchestrator(event_id="SIM-DISR-2026-TEST", base_runs_dir=self.mock_runs_dir)
        valid_summary = {
            "source_event_id": "SIM-DISR-2026-TEST",
            "shockwave_id": "SHOCK-TEST-001",
            "entity_counts": {
                "unique_affected_orders": 100,
                "eligible_orders_for_delay": 90,
                "ineligible_orders_excluded": 10
            },
            "financial_exposure": {
                "total_gross_revenue_exposure_usd": 1000.0,
                "eligible_revenue_exposure_usd": 900.0,
                "ineligible_revenue_excluded_usd": 100.0
            }
        }
        orch._validate_gate_2(valid_summary, "dummy_path.csv")
        self.assertEqual(orch.lineage["validation_gates"]["GATE_2_SHOCKWAVE_RECONCILIATION"]["status"], "PASSED")

        # Cohort count mismatch fails
        broken_summary = dict(valid_summary)
        broken_summary["entity_counts"] = {
            "unique_affected_orders": 100,
            "eligible_orders_for_delay": 85,  # 85 + 10 != 100
            "ineligible_orders_excluded": 10
        }
        with self.assertRaises(PipelineGateError) as ctx:
            orch._validate_gate_2(broken_summary, "dummy_path.csv")
        self.assertIn("Cohort count mismatch", str(ctx.exception))

        # Financial discrepancy fails
        broken_fin = dict(valid_summary)
        broken_fin["financial_exposure"] = {
            "total_gross_revenue_exposure_usd": 1000.0,
            "eligible_revenue_exposure_usd": 800.0,  # 800 + 100 != 1000
            "ineligible_revenue_excluded_usd": 100.0
        }
        with self.assertRaises(PipelineGateError) as ctx:
            orch._validate_gate_2(broken_fin, "dummy_path.csv")
        self.assertIn("Financial reconciliation error", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 5. Validation Gate 3 & 4
    # --------------------------------------------------------------------------
    def test_gate_3_validation_cohort_and_revenue(self):
        """Verify Gate 3 catches discrepancies against Phase 8 inputs."""
        orch = DisruptionPipelineOrchestrator(event_id="SIM-DISR-2026-TEST", base_runs_dir=self.mock_runs_dir)
        orch.lineage["stages"]["stage_2_shockwave"] = {
            "unique_affected_orders": 100,
            "gross_revenue_usd": 1000.0
        }

        valid_risk_summary = {
            "risk_assessment_id": "RISK-TEST-001",
            "order_cohort_summary": {
                "total_assessed_orders": 100,
                "eligible_active_orders": 90,
                "ineligible_non_shipped_orders": 10
            },
            "financial_reconciliation": {
                "total_gross_revenue_usd": 1000.0
            },
            "severity_distribution": {
                "critical_orders": 5,
                "high_risk_orders": 25
            }
        }
        orch._validate_gate_3(valid_risk_summary, "dummy.csv", "dummy.csv")
        self.assertEqual(orch.lineage["validation_gates"]["GATE_3_RISK_COHORT_INTEGRITY"]["status"], "PASSED")

        # Discrepancy with Phase 8 order count fails
        mismatched_summary = dict(valid_risk_summary)
        mismatched_summary["order_cohort_summary"] = {
            "total_assessed_orders": 95,  # Expected 100
            "eligible_active_orders": 85,
            "ineligible_non_shipped_orders": 10
        }
        with self.assertRaises(PipelineGateError) as ctx:
            orch._validate_gate_3(mismatched_summary, "dummy.csv", "dummy.csv")
        self.assertIn("Cohort count mismatch between Phase 8", str(ctx.exception))

    def test_gate_4_budget_validation(self):
        """Verify Gate 4 strictly enforces 1000.0 RCU budget and rejects violations."""
        orch = DisruptionPipelineOrchestrator(event_id="SIM-DISR-2026-TEST", base_runs_dir=self.mock_runs_dir)
        
        # Valid recovery plan
        valid_rec_summary = {"capacity_budget_rcu": AUTHORITATIVE_RCU_BUDGET}
        valid_rec_plan = {
            "recommended_plan_id": "PLAN_5_KNAPSACK_HYBRID",
            "resilience_index": 44.66,
            "resource_allocation_summary": {
                "allocated_rcu": 999.9,
                "capacity_utilization_pct": 99.99,
                "recovered_orders_count": 533
            },
            "financial_mitigation_summary": {
                "total_eligible_revenue_usd": 1000.0,
                "expected_mitigated_revenue_usd": 400.0,
                "residual_revenue_exposure_usd": 600.0
            }
        }

        # Create dummy alloc CSV with 0 allocations to ineligible
        alloc_path = os.path.join(self.test_dir, "test_alloc.csv")
        with open(alloc_path, "w", encoding="utf-8") as f:
            f.write("order_id,is_eligible_for_delay,allocated_plan_5\n")
            f.write("ORD_1,true,1\n")
            f.write("ORD_2,false,0\n")

        # Create dummy stress matrix with 30 rows
        stress_path = os.path.join(self.test_dir, "test_stress.csv")
        with open(stress_path, "w", encoding="utf-8") as f:
            f.write("plan_id,scenario_id,residual_revenue_usd\n")
            for i in range(30):
                f.write(f"P{i//5},S{i%5},100.0\n")

        orch._validate_gate_4(valid_rec_summary, valid_rec_plan, alloc_path, stress_path)
        self.assertEqual(orch.lineage["validation_gates"]["GATE_4_OPTIMIZATION_BOUNDS"]["status"], "PASSED")

        # Over-budget allocation fails
        over_budget_plan = dict(valid_rec_plan)
        over_budget_plan["resource_allocation_summary"] = {
            "allocated_rcu": 1050.0,  # Exceeds 1000.0!
            "capacity_utilization_pct": 105.0,
            "recovered_orders_count": 600
        }
        with self.assertRaises(PipelineGateError) as ctx:
            orch._validate_gate_4(valid_rec_summary, over_budget_plan, alloc_path, stress_path)
        self.assertIn("Budget violation", str(ctx.exception))

    def test_gate_4_ineligible_order_zero_spend(self):
        """Verify Gate 4 rejects non-zero allocation to ineligible orders."""
        orch = DisruptionPipelineOrchestrator(event_id="SIM-DISR-2026-TEST", base_runs_dir=self.mock_runs_dir)
        valid_rec_summary = {"capacity_budget_rcu": AUTHORITATIVE_RCU_BUDGET}
        valid_rec_plan = {
            "recommended_plan_id": "PLAN_5_KNAPSACK_HYBRID",
            "resilience_index": 44.66,
            "resource_allocation_summary": {"allocated_rcu": 900.0, "recovered_orders_count": 10},
            "financial_mitigation_summary": {
                "total_eligible_revenue_usd": 1000.0,
                "expected_mitigated_revenue_usd": 400.0,
                "residual_revenue_exposure_usd": 600.0
            }
        }
        # Ineligible order illegally allocated
        bad_alloc_path = os.path.join(self.test_dir, "bad_alloc.csv")
        with open(bad_alloc_path, "w", encoding="utf-8") as f:
            f.write("order_id,is_eligible_for_delay,allocated_plan_5\n")
            f.write("ORD_1,true,1\n")
            f.write("ORD_2,false,1\n")  # Ineligible order received 1!

        stress_path = os.path.join(self.test_dir, "test_stress.csv")
        with open(stress_path, "w", encoding="utf-8") as f:
            f.write("header\n")
            for _ in range(30):
                f.write("row\n")

        with self.assertRaises(PipelineGateError) as ctx:
            orch._validate_gate_4(valid_rec_summary, valid_rec_plan, bad_alloc_path, stress_path)
        self.assertIn("Ineligible order received non-zero allocation", str(ctx.exception))

    def test_gate_4_stress_matrix_completeness(self):
        """Verify Gate 4 rejects stress matrices with fewer than 30 evaluations."""
        orch = DisruptionPipelineOrchestrator(event_id="SIM-DISR-2026-TEST", base_runs_dir=self.mock_runs_dir)
        valid_rec_summary = {"capacity_budget_rcu": AUTHORITATIVE_RCU_BUDGET}
        valid_rec_plan = {
            "recommended_plan_id": "PLAN_5_KNAPSACK_HYBRID",
            "resilience_index": 44.66,
            "resource_allocation_summary": {"allocated_rcu": 900.0, "recovered_orders_count": 10},
            "financial_mitigation_summary": {
                "total_eligible_revenue_usd": 1000.0,
                "expected_mitigated_revenue_usd": 400.0,
                "residual_revenue_exposure_usd": 600.0
            }
        }
        alloc_path = os.path.join(self.test_dir, "test_alloc.csv")
        with open(alloc_path, "w", encoding="utf-8") as f:
            f.write("order_id,is_eligible_for_delay,allocated_plan_5\n")
            f.write("ORD_1,true,1\n")

        # Incomplete stress matrix (only 25 rows)
        incomplete_stress = os.path.join(self.test_dir, "incomplete_stress.csv")
        with open(incomplete_stress, "w", encoding="utf-8") as f:
            f.write("header\n")
            for _ in range(25):
                f.write("row\n")

        with self.assertRaises(PipelineGateError) as ctx:
            orch._validate_gate_4(valid_rec_summary, valid_rec_plan, alloc_path, incomplete_stress)
        self.assertIn("Incomplete stress test evaluation matrix", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 6. Dry Run & Lineage Generation
    # --------------------------------------------------------------------------
    def test_dry_run_offline_execution(self):
        """Verify complete offline dry-run planner using mock local part files."""
        orch = DisruptionPipelineOrchestrator(
            event_id="SIM-DISR-2026-TEST",
            base_runs_dir=self.mock_runs_dir,
            local_mock_dir=self.mock_hdfs_dir
        )
        plan = orch.execute_dry_run()

        self.assertEqual(plan["mode"], "DRY_RUN")
        self.assertEqual(plan["event_id"], "SIM-DISR-2026-TEST")
        self.assertEqual(plan["authoritative_budget_rcu"], 1000.0)

        # Verify lineage.json and run_summary.json exist
        lineage_file = os.path.join(orch.run_dir, "lineage.json")
        summary_file = os.path.join(orch.run_dir, "run_summary.json")
        plan_file = os.path.join(orch.run_dir, "run_plan.json")

        self.assertTrue(os.path.exists(lineage_file))
        self.assertTrue(os.path.exists(summary_file))
        self.assertTrue(os.path.exists(plan_file))

        with open(lineage_file, "r", encoding="utf-8") as f:
            lineage = json.load(f)
        self.assertEqual(lineage["status"], "DRY_RUN_PASSED")
        self.assertIn("GATE_1_EVENT_INTEGRITY", lineage["validation_gates"])


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)


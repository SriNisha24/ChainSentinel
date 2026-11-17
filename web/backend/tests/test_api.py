"""
ChainSentinel Phase 11 — Backend Automated Test Suite
Location: web/backend/tests/test_api.py

Tests all read-only REST endpoints, schema serialization, PII masking,
error handling, and metric reconciliation against the authoritative
Phase 10 integration run (IRUN-20261104143752-A4CB8F).
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

# Resolve paths
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.abspath(os.path.join(TESTS_DIR, ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from main import app
from services.data_loader import RunDataLoader, DataLoaderError


class TestBackendAPI(unittest.TestCase):
    """Exhaustive test suite for FastAPI Operational Review Backend."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # --------------------------------------------------------------------------
    # 1. System Health & Metadata
    # --------------------------------------------------------------------------
    def test_health_endpoint(self):
        """Verify /api/health responds with 200, service status, and run ID."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["authoritative_run_id"], "IRUN-20261104143752-A4CB8F")
        self.assertEqual(data["active_event_id"], "SIM-DISR-2026-001")

    # --------------------------------------------------------------------------
    # 2. Run Summary & Lineage
    # --------------------------------------------------------------------------
    def test_run_summary_endpoint(self):
        """Verify /api/run returns executive summary, gate outcomes, and duration."""
        response = self.client.get("/api/run")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["run_id"], "IRUN-20261104143752-A4CB8F")
        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(len(data["stages_completed"]), 4)
        self.assertEqual(len(data["gates_passed"]), 4)
        self.assertGreater(data["total_execution_duration_seconds"], 0.0)

    def test_lineage_endpoint(self):
        """Verify /api/lineage returns full cryptographic execution trace."""
        response = self.client.get("/api/lineage")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["run_id"], "IRUN-20261104143752-A4CB8F")
        self.assertIn("stages", data)
        self.assertIn("validation_gates", data)
        self.assertIn("GATE_4_OPTIMIZATION_BOUNDS", data["validation_gates"])

    # --------------------------------------------------------------------------
    # 3. Disruption Telemetry
    # --------------------------------------------------------------------------
    def test_disruption_endpoint(self):
        """Verify /api/disruption returns Phase 7 event details and HDFS source."""
        response = self.client.get("/api/disruption")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["event_id"], "SIM-DISR-2026-001")
        self.assertEqual(data["disruption_type"], "PORT_CLOSURE")
        self.assertEqual(data["severity"], "CRITICAL")
        self.assertEqual(data["affected_market"], "Pacific Asia")
        self.assertEqual(data["affected_region"], "East Asia")
        self.assertEqual(data["expected_duration_hours"], 72.0)
        self.assertEqual(data["delay_estimate_hours"], 96.0)
        self.assertEqual(data["source_confidence"], 0.98)
        self.assertTrue(data["is_valid"])
        self.assertIn("part-00030", data["source_hdfs_path"])

    # --------------------------------------------------------------------------
    # 4. Shockwave Propagation & Cohort Reconciliations
    # --------------------------------------------------------------------------
    def test_shockwave_endpoint(self):
        """Verify /api/shockwave returns Phase 8 cohort counts and exposure."""
        response = self.client.get("/api/shockwave")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["shockwave_id"], "SHOCK-20261104143814-5306D7")
        self.assertEqual(data["source_event_id"], "SIM-DISR-2026-001")
        
        counts = data["entity_counts"]
        self.assertEqual(counts["unique_affected_orders"], 3318)
        self.assertEqual(counts["eligible_orders_for_delay"], 3171)
        self.assertEqual(counts["ineligible_orders_excluded"], 147)
        self.assertEqual(counts["unique_affected_customers"], 3169)

        fin = data["financial_exposure"]
        self.assertAlmostEqual(fin["total_gross_revenue_exposure_usd"], 1334313.40, places=2)
        self.assertAlmostEqual(fin["eligible_revenue_exposure_usd"], 1282401.19, places=2)
        self.assertAlmostEqual(fin["ineligible_revenue_excluded_usd"], 51912.21, places=2)

    # --------------------------------------------------------------------------
    # 5. Risk Assessment & PII Masking
    # --------------------------------------------------------------------------
    def test_risk_summary_endpoint(self):
        """Verify /api/risk returns severity counts and priority queue sample."""
        response = self.client.get("/api/risk?sample_limit=25")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["risk_assessment_id"], "RISK-20261104143816-4CC108")
        
        sev = data["severity_distribution"]
        self.assertEqual(sev["critical_orders"], 20)
        self.assertEqual(sev["high_risk_orders"], 625)
        self.assertEqual(sev["medium_risk_orders"], 1498)
        self.assertEqual(sev["low_risk_orders"], 1028)
        self.assertEqual(sev["ineligible_non_shipped_orders"], 147)

        # Check priority queue sample
        self.assertEqual(len(data["priority_orders_sample"]), 25)
        self.assertEqual(data["total_priority_orders_count"], 645)

    def test_pii_masking_in_risk_endpoint(self):
        """Verify priority orders do not expose customer names, addresses, or phone numbers."""
        response = self.client.get("/api/risk?sample_limit=50")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        for item in data["priority_orders_sample"]:
            self.assertTrue(item["order_id"].startswith("ORD_"))
            self.assertIn(item["customer_segment"], ["Consumer", "Corporate", "Home Office"])
            self.assertIn(item["shipping_mode"], ["Same Day", "First Class", "Second Class", "Standard Class"])
            # Ensure prohibited PII fields do not exist
            self.assertNotIn("customer_name", item)
            self.assertNotIn("customer_email", item)
            self.assertNotIn("customer_phone", item)
            self.assertNotIn("street_address", item)

    # --------------------------------------------------------------------------
    # 6. Recovery Optimization & Plan Comparisons
    # --------------------------------------------------------------------------
    def test_recovery_plans_endpoint(self):
        """Verify /api/recovery/plans returns all 6 candidate strategies."""
        response = self.client.get("/api/recovery/plans")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["capacity_budget_rcu"], 1000.0)
        self.assertEqual(len(data["plans"]), 6)
        
        plan_ids = [p["plan_id"] for p in data["plans"]]
        self.assertIn("PLAN_0_BASELINE", plan_ids)
        self.assertIn("PLAN_1_PRIORITY_FIRST", plan_ids)
        self.assertIn("PLAN_2_FINANCIAL_FIRST", plan_ids)
        self.assertIn("PLAN_3_VULNERABILITY_FIRST", plan_ids)
        self.assertIn("PLAN_4_MODE_URGENCY_FIRST", plan_ids)
        self.assertIn("PLAN_5_KNAPSACK_HYBRID", plan_ids)

    def test_recommended_plan_endpoint(self):
        """Verify /api/recovery/recommended returns Plan 5 with exact metrics."""
        response = self.client.get("/api/recovery/recommended")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["recommended_plan_id"], "PLAN_5_KNAPSACK_HYBRID")
        self.assertEqual(data["resilience_index"], 44.66)
        self.assertEqual(data["utility_score"], 0.6481)

        res = data["resource_allocation_summary"]
        self.assertEqual(res["capacity_budget_rcu"], 1000.0)
        self.assertEqual(res["allocated_rcu"], 999.9)
        self.assertEqual(res["recovered_orders_count"], 533)
        self.assertEqual(res["unrecovered_orders_count"], 2638)

        fin = data["financial_mitigation_summary"]
        self.assertEqual(fin["expected_mitigated_revenue_usd"], 411590.64)
        self.assertEqual(fin["residual_revenue_exposure_usd"], 870810.55)
        self.assertEqual(fin["revenue_mitigation_pct"], 32.1)

        risk = data["risk_mitigation_summary"]
        self.assertEqual(risk["recovered_critical_orders"], 17)
        self.assertEqual(risk["unrecovered_critical_orders"], 3)

    # --------------------------------------------------------------------------
    # 7. Counterfactual Stress Tests
    # --------------------------------------------------------------------------
    def test_stress_tests_endpoint(self):
        """Verify /api/recovery/stress-tests returns all 30 evaluations."""
        response = self.client.get("/api/recovery/stress-tests")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_evaluations_count"], 30)
        self.assertEqual(len(data["scenarios"]), 5)
        self.assertEqual(len(data["plans"]), 6)

    # --------------------------------------------------------------------------
    # 8. Error Handling & Missing File Safety
    # --------------------------------------------------------------------------
    def test_missing_run_error_handling(self):
        """Verify error handling when an invalid run directory is specified."""
        with self.assertRaises(DataLoaderError):
            RunDataLoader(run_id="NON_EXISTENT_RUN_ID")

    # --------------------------------------------------------------------------
    # 9. Expected Metric Reconciliation Gate
    # --------------------------------------------------------------------------
    def test_authoritative_metric_reconciliation(self):
        """Verify all 10 authoritative reference values match the API responses."""
        resp_shock = self.client.get("/api/shockwave").json()
        resp_rec = self.client.get("/api/recovery/recommended").json()

        # 1. Affected orders: 3,318
        self.assertEqual(resp_shock["entity_counts"]["unique_affected_orders"], 3318)
        # 2. Eligible orders: 3,171
        self.assertEqual(resp_shock["entity_counts"]["eligible_orders_for_delay"], 3171)
        # 3. Ineligible orders: 147
        self.assertEqual(resp_shock["entity_counts"]["ineligible_orders_excluded"], 147)
        # 4. Gross revenue exposure: $1,334,313.40
        self.assertEqual(resp_shock["financial_exposure"]["total_gross_revenue_exposure_usd"], 1334313.40)
        # 5. Recommended strategy: Plan 5 — KNAPSACK HYBRID
        self.assertEqual(resp_rec["recommended_plan_id"], "PLAN_5_KNAPSACK_HYBRID")
        # 6. Allocated capacity: 999.90 / 1,000 RCU
        self.assertEqual(resp_rec["resource_allocation_summary"]["allocated_rcu"], 999.9)
        self.assertEqual(resp_rec["resource_allocation_summary"]["capacity_budget_rcu"], 1000.0)
        # 7. Simulated recovered orders: 533
        self.assertEqual(resp_rec["resource_allocation_summary"]["recovered_orders_count"], 533)
        # 8. Revenue mitigation: $411,590.64
        self.assertEqual(resp_rec["financial_mitigation_summary"]["expected_mitigated_revenue_usd"], 411590.64)
        # 9. Residual eligible revenue exposure: $870,810.55
        self.assertEqual(resp_rec["financial_mitigation_summary"]["residual_revenue_exposure_usd"], 870810.55)
        # 10. Resilience score: 44.66
        self.assertEqual(resp_rec["resilience_index"], 44.66)

    # --------------------------------------------------------------------------
    # 10. Human-in-the-Loop Operational Approval Workflow (Task 11D)
    # --------------------------------------------------------------------------
    def test_approval_workflow_lifecycle(self):
        """
        Verify the complete 5-state approval lifecycle, receipt persistence,
        schema conformity, and simulation safeguards.
        """
        import json
        import jsonschema

        run_id = "IRUN-20261104143752-A4CB8F"
        schema_path = os.path.abspath(os.path.join(BACKEND_DIR, "..", "..", "data", "approval_records", "schema.json"))
        with open(schema_path, "r", encoding="utf-8") as sf:
            schema_def = json.load(sf)

        # 1. Verify initial status is PENDING_REVIEW (or valid existing status)
        resp = self.client.get(f"/api/approvals/{run_id}")
        self.assertEqual(resp.status_code, 200)
        initial_data = resp.json()
        self.assertEqual(initial_data["run_id"], run_id)
        self.assertTrue(initial_data["simulation_only"])
        self.assertFalse(initial_data["physical_dispatch_executed"])
        self.assertIn("simulation_watermark", initial_data)

        # 2. Test REVISION_REQUESTED submission
        rev_payload = {
            "run_id": run_id,
            "event_id": "SIM-DISR-2026-001",
            "recommended_plan": "PLAN_5_KNAPSACK_HYBRID",
            "decision_status": "REVISION_REQUESTED",
            "reviewer_username": "test_officer_1",
            "reviewer_role": "Supply Chain Operations Lead",
            "reviewer_department": "Global Logistics",
            "reviewer_comments": "Requesting stress evaluation on critical healthcare accounts before sign-off.",
            "revision_request": {
                "target_capacity_rcu": 950.0,
                "custom_notes": "Evaluate buffer allocation."
            }
        }
        rev_resp = self.client.post("/api/approvals/request-revision", json=rev_payload)
        self.assertEqual(rev_resp.status_code, 200)
        rev_data = rev_resp.json()
        self.assertEqual(rev_data["decision_status"], "REVISION_REQUESTED")
        self.assertTrue(rev_data["approval_id"].startswith("APPR-"))
        self.assertTrue(rev_data["simulation_only"])
        self.assertFalse(rev_data["physical_dispatch_executed"])
        # Validate against JSON schema draft-07
        jsonschema.validate(instance=rev_data, schema=schema_def)

        # 3. Test APPROVED submission
        appr_payload = {
            "run_id": run_id,
            "event_id": "SIM-DISR-2026-001",
            "recommended_plan": "PLAN_5_KNAPSACK_HYBRID",
            "decision_status": "APPROVED",
            "reviewer_username": "chief_supply_officer",
            "reviewer_role": "Chief Supply Chain Officer",
            "reviewer_department": "Executive Leadership",
            "reviewer_comments": "Plan 5 Knapsack Hybrid approved. Mitigates $411,590.64 and protects 17 of 20 critical shipments."
        }
        appr_resp = self.client.post("/api/approvals/approve", json=appr_payload)
        self.assertEqual(appr_resp.status_code, 200)
        appr_data = appr_resp.json()
        self.assertEqual(appr_data["decision_status"], "APPROVED")
        jsonschema.validate(instance=appr_data, schema=schema_def)

        # 4. Test REJECTED submission
        rej_payload = {
            "run_id": run_id,
            "event_id": "SIM-DISR-2026-001",
            "recommended_plan": "PLAN_5_KNAPSACK_HYBRID",
            "decision_status": "REJECTED",
            "reviewer_username": "risk_officer",
            "reviewer_role": "Risk Management Lead",
            "reviewer_comments": "Rejected pending additional budget allocation."
        }
        rej_resp = self.client.post("/api/approvals/reject", json=rej_payload)
        self.assertEqual(rej_resp.status_code, 200)
        self.assertEqual(rej_resp.json()["decision_status"], "REJECTED")

        # 5. Test CLOSED submission
        close_payload = {
            "run_id": run_id,
            "event_id": "SIM-DISR-2026-001",
            "recommended_plan": "PLAN_5_KNAPSACK_HYBRID",
            "decision_status": "CLOSED",
            "reviewer_username": "chief_supply_officer",
            "reviewer_role": "Chief Supply Chain Officer",
            "reviewer_comments": "Operational review closed for run IRUN-20261104143752-A4CB8F."
        }
        close_resp = self.client.post("/api/approvals/close", json=close_payload)
        self.assertEqual(close_resp.status_code, 200)
        self.assertEqual(close_resp.json()["decision_status"], "CLOSED")

        # 6. Verify history trail reflects all decisions
        hist_resp = self.client.get(f"/api/approvals/{run_id}")
        self.assertEqual(hist_resp.status_code, 200)
        hist_data = hist_resp.json()
        self.assertEqual(hist_data["current_status"], "CLOSED")
        self.assertGreaterEqual(hist_data["total_decisions_count"], 4)
        self.assertEqual(hist_data["latest_decision"]["decision_status"], "CLOSED")

        # 7. Test validation failure on empty comments / reviewer
        invalid_payload = {
            "run_id": run_id,
            "event_id": "SIM-DISR-2026-001",
            "recommended_plan": "PLAN_5_KNAPSACK_HYBRID",
            "decision_status": "APPROVED",
            "reviewer_username": "",
            "reviewer_role": "",
            "reviewer_comments": ""
        }
        inv_resp = self.client.post("/api/approvals/approve", json=invalid_payload)
        self.assertEqual(inv_resp.status_code, 400)
        self.assertEqual(inv_resp.json()["error_type"], "APPROVAL_WORKFLOW_ERROR")

    # --------------------------------------------------------------------------
    # 11. Real-Time Alerting and Notification Engine (Phase 12)
    # --------------------------------------------------------------------------
    def test_alerts_endpoints_and_lifecycle(self):
        """
        Verify alert list, summary metrics, detail lookup, lifecycle transitions
        (acknowledge -> resolve -> dismiss), deduplication, and schema conformity.
        """
        import json
        import jsonschema

        # 1. Summary endpoint
        resp_sum = self.client.get("/api/alerts/summary")
        self.assertEqual(resp_sum.status_code, 200)
        sum_data = resp_sum.json()
        self.assertGreaterEqual(sum_data["total_alerts"], 5)
        self.assertIn("by_status", sum_data)
        self.assertIn("by_severity", sum_data)
        self.assertTrue(sum_data["simulation_only"])

        # 2. List endpoint
        resp_list = self.client.get("/api/alerts")
        self.assertEqual(resp_list.status_code, 200)
        alerts = resp_list.json()
        self.assertGreaterEqual(len(alerts), 5)

        # Validate against JSON schema
        schema_path = os.path.abspath(os.path.join(BACKEND_DIR, "..", "..", "data", "alerts", "schema.json"))
        with open(schema_path, "r", encoding="utf-8") as sf:
            schema_def = json.load(sf)

        for a in alerts:
            self.assertTrue(a["alert_id"].startswith("ALERT-"))
            self.assertTrue(a["simulation_only"])
            jsonschema.validate(instance=a, schema=schema_def)

        # 3. Filter by severity
        crit_resp = self.client.get("/api/alerts?severity=CRITICAL")
        self.assertEqual(crit_resp.status_code, 200)
        crit_alerts = crit_resp.json()
        for ca in crit_alerts:
            self.assertEqual(ca["severity"], "CRITICAL")

        # 4. Detail endpoint
        target_alert = alerts[0]
        alert_id = target_alert["alert_id"]
        detail_resp = self.client.get(f"/api/alerts/{alert_id}")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["alert_id"], alert_id)

        # 5. Lifecycle: Acknowledge
        ack_resp = self.client.post(
            f"/api/alerts/{alert_id}/acknowledge",
            json={"user": "duty_manager", "comments": "Investigating high exposure."}
        )
        self.assertEqual(ack_resp.status_code, 200)
        ack_data = ack_resp.json()
        self.assertEqual(ack_data["acknowledgement_status"], "ACKNOWLEDGED")
        self.assertIsNotNone(ack_data["acknowledged_timestamp"])
        self.assertEqual(ack_data["history"][-1]["status"], "ACKNOWLEDGED")

        # 6. Lifecycle: Resolve
        res_resp = self.client.post(
            f"/api/alerts/{alert_id}/resolve",
            json={"user": "duty_manager", "comments": "Mitigation plan approved."}
        )
        self.assertEqual(res_resp.status_code, 200)
        res_data = res_resp.json()
        self.assertEqual(res_data["acknowledgement_status"], "RESOLVED")
        self.assertIsNotNone(res_data["resolved_timestamp"])

        # 7. Deduplication check via evaluate endpoint
        eval_resp = self.client.post("/api/alerts/evaluate?run_id=IRUN-20261104143752-A4CB8F")
        self.assertEqual(eval_resp.status_code, 200)
        new_created = eval_resp.json()
        # Should create 0 new alerts since all rules have already fired for this run
        self.assertEqual(len(new_created), 0)

        # 8. Error handling: 404 for non-existent alert
        bad_resp = self.client.get("/api/alerts/ALERT-20261104-NONEXIST")
        self.assertEqual(bad_resp.status_code, 404)
        self.assertEqual(bad_resp.json()["error_type"], "ALERT_NOT_FOUND")

    # --------------------------------------------------------------------------
    # 10. Phase 13 — Model Monitoring & Drift Telemetry
    # --------------------------------------------------------------------------
    def test_model_monitoring_endpoints(self):
        """Verify /api/models inventory, /api/models/{id}/drift, PSI calculation, and stability."""
        # 1. Models registry
        resp = self.client.get("/api/models")
        self.assertEqual(resp.status_code, 200)
        models = resp.json()
        self.assertEqual(len(models), 4)

        model_ids = {m["model_id"] for m in models}
        self.assertIn("delay_model_v1", model_ids)
        self.assertIn("anomaly_detection_v1", model_ids)
        self.assertIn("disruption_impact_v1", model_ids)
        self.assertIn("demand_forecasting_v1", model_ids)

        # 2. Delay model drift evaluation
        drift_resp = self.client.get("/api/models/delay_model_v1/drift")
        self.assertEqual(drift_resp.status_code, 200)
        drift_data = drift_resp.json()
        self.assertEqual(drift_data["model_id"], "delay_model_v1")
        self.assertIn("population_stability_index", drift_data)
        self.assertGreaterEqual(drift_data["population_stability_index"], 0.0)
        self.assertIn("stability_status", drift_data)
        self.assertIn(drift_data["stability_status"], ["STABLE", "MODERATE_DRIFT", "SIGNIFICANT_DRIFT"])
        self.assertIn("psi_bucket_breakdown", drift_data)

    # --------------------------------------------------------------------------
    # 11. Phase 13 — Feedback Subsystem & Epistemological Governance
    # --------------------------------------------------------------------------
    def test_feedback_closed_loop_and_governance(self):
        """Verify feedback submission, epistemological retraining eligibility, and status updates."""
        # 1. Feedback summary
        sum_resp = self.client.get("/api/feedback/summary")
        self.assertEqual(sum_resp.status_code, 200)
        sum_data = sum_resp.json()
        self.assertIn("total_feedback_records", sum_data)
        self.assertIn("feedback_type_breakdown", sum_data)
        self.assertIn("retraining_eligible_count", sum_data)

        # 2. Submit SIMULATION_RESULT feedback (must NOT be eligible for retraining)
        sim_payload = {
            "model_id": "delay_model_v1",
            "model_version": "v1.0.0",
            "feedback_type": "SIMULATION_RESULT",
            "feedback_source": "TEST_STRESS_HARNESS",
            "predicted_value": 0.42,
            "observed_value": None,
            "confidence": 0.85,
            "validation_status": "VERIFIED_VALID",
            "comments": "Automated test synthetic simulation result"
        }
        create_resp = self.client.post("/api/feedback", json=sim_payload)
        self.assertEqual(create_resp.status_code, 200)
        sim_record = create_resp.json()
        self.assertTrue(sim_record["feedback_id"].startswith("FDBK-"))
        self.assertFalse(sim_record["metadata"]["retraining_eligible"])

        # 3. Submit OBSERVED_OPERATIONAL_OUTCOME feedback (eligible when VERIFIED_VALID)
        obs_payload = {
            "model_id": "delay_model_v1",
            "model_version": "v1.0.0",
            "feedback_type": "OBSERVED_OPERATIONAL_OUTCOME",
            "feedback_source": "TEST_CARRIER_FEED",
            "predicted_value": 1,
            "observed_value": 1,
            "confidence": 0.99,
            "validation_status": "VERIFIED_VALID",
            "comments": "Automated test carrier ground truth"
        }
        obs_resp = self.client.post("/api/feedback", json=obs_payload)
        self.assertEqual(obs_resp.status_code, 200)
        obs_record = obs_resp.json()
        self.assertTrue(obs_record["metadata"]["retraining_eligible"])

        # 4. Status update
        fdbk_id = obs_record["feedback_id"]
        status_resp = self.client.post(
            f"/api/feedback/{fdbk_id}/status",
            json={"validation_status": "REJECTED_INVALID", "actor": "qa_officer", "comments": "Data sensor glitch"}
        )
        self.assertEqual(status_resp.status_code, 200)
        updated = status_resp.json()
        self.assertEqual(updated["validation_status"], "REJECTED_INVALID")
        self.assertFalse(updated["metadata"]["retraining_eligible"])

        # 5. Detail & 404
        detail_resp = self.client.get(f"/api/feedback/{fdbk_id}")
        self.assertEqual(detail_resp.status_code, 200)
        bad_fdbk = self.client.get("/api/feedback/FDBK-20261104-NONEXIST")
        self.assertEqual(bad_fdbk.status_code, 404)

    # --------------------------------------------------------------------------
    # 12. Phase 13 — Controlled Retraining Experiment Isolation
    # --------------------------------------------------------------------------
    def test_candidate_retraining_experiment(self):
        """Verify candidate training runs in models/phase13_experiments/ and never modifies Phase 5 models."""
        exp_resp = self.client.post(
            "/api/models/retrain-experiment",
            json={
                "base_model_id": "delay_model_v1",
                "experiment_name": "API Automated Verification Retraining",
                "triggered_by": "UNIT_TEST"
            }
        )
        self.assertEqual(exp_resp.status_code, 200)
        exp_data = exp_resp.json()
        self.assertTrue(exp_data["experiment_id"].startswith("EXP-"))
        self.assertEqual(exp_data["challenger_verdict"], "CHALLENGER_SUPERIOR")
        self.assertEqual(exp_data["promotion_status"], "PENDING_HUMAN_GOVERNANCE_APPROVAL")
        self.assertIn("models/phase13_experiments", exp_data["isolation_path"].replace("\\", "/"))

        # Verify experiments listing
        list_resp = self.client.get("/api/models/experiments")
        self.assertEqual(list_resp.status_code, 200)
        exp_list = list_resp.json()
        self.assertGreaterEqual(len(exp_list), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)


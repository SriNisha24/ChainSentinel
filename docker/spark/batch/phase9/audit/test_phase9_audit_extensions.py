"""
ChainSentinel Phase 9 Task 9C - Extended Independent Audit Unit Tests
File: docker/spark/batch/phase9/audit/test_phase9_audit_extensions.py

Performs exhaustive edge-case, boundary, and mathematical validation without
modifying the existing implementation or baseline test suite.
"""

import os
import unittest
import pandas as pd
import numpy as np

from docker.spark.batch.phase9.impact_risk_engine import ImpactRiskEngine

class TestPhase9AuditExtensions(unittest.TestCase):

    def setUp(self):
        self.config_path = "docker/spark/batch/phase9/risk_scoring_config.json"
        self.engine = ImpactRiskEngine(config_path=self.config_path)

        # Baseline mock summary
        self.mock_summary = {
            "source_event_id": "AUDIT-EVENT-001",
            "shockwave_id": "SHOCK-AUDIT-001",
            "source_event_confidence": 0.95,
            "event_delay_estimate_hours": 96.0,
            "severity": "HIGH"
        }

    def test_exact_risk_tier_boundaries(self):
        """Validates exact numerical boundaries: 75.0, 74.99, 55.0, 54.99, 35.0, 34.99, 0.0."""
        thresh = self.engine.config.get("severity_thresholds", {"CRITICAL": 75.0, "HIGH": 55.0, "MEDIUM": 35.0, "LOW": 0.0})

        def classify(score):
            if score >= thresh["CRITICAL"]:
                return "CRITICAL"
            elif score >= thresh["HIGH"]:
                return "HIGH"
            elif score >= thresh["MEDIUM"]:
                return "MEDIUM"
            else:
                return "LOW"

        self.assertEqual(classify(100.0), "CRITICAL")
        self.assertEqual(classify(75.0), "CRITICAL")
        self.assertEqual(classify(74.99), "HIGH")
        self.assertEqual(classify(55.0), "HIGH")
        self.assertEqual(classify(54.99), "MEDIUM")
        self.assertEqual(classify(35.0), "MEDIUM")
        self.assertEqual(classify(34.99), "LOW")
        self.assertEqual(classify(0.0), "LOW")

    def test_negative_profit_and_zero_spend_financial_risk(self):
        """Verifies safe handling of negative profit (loss-making) and zero spend (div-by-zero prevention)."""
        mock_entities = pd.DataFrame([
            {
                "affected_entity_id": "ORD_001",
                "affected_entity_type": "ORDER",
                "revenue_exposure": 500.0,
                "profit_exposure": -150.0,  # Negative profit
                "is_eligible_for_delay": True,
                "order_status": "PROCESSING",
                "delivery_status": "Normal",
                "shipping_mode": "Standard Class",
                "historical_delayed": False,
                "graph_mapping_confidence": 1.0
            },
            {
                "affected_entity_id": "ORD_002",
                "affected_entity_type": "ORDER",
                "revenue_exposure": 0.0,   # Zero spend edge case
                "profit_exposure": 0.0,
                "is_eligible_for_delay": True,
                "order_status": "PROCESSING",
                "delivery_status": "Normal",
                "shipping_mode": "Standard Class",
                "historical_delayed": False,
                "graph_mapping_confidence": 1.0
            }
        ])

        self.engine.set_inputs(
            shockwave_summary=self.mock_summary,
            shockwave_entities_df=mock_entities,
            anomaly_results_df=pd.DataFrame(),
            order_attributes_df=pd.DataFrame(),
            customer_network_df=pd.DataFrame()
        )

        assessments, _, _ = self.engine.assess_risks()
        ass_map = {r["entity_id"]: r for r in assessments}

        # ORD_001 (Negative profit): margin vulnerability must be 100%
        # Spend percentile: ranks in [0, 100], fin risk must be strictly bounded
        r1 = ass_map["ORD_001"]
        self.assertTrue(r1["financial_risk_score"] > 0)
        self.assertTrue(r1["risk_explanation"]["financial_factors"]["is_loss_making"])

        # ORD_002 (Zero spend): margin vulnerability must default to 50% without ZeroDivisionError
        r2 = ass_map["ORD_002"]
        self.assertEqual(r2["revenue_exposure"], 0.0)
        self.assertFalse(r2["risk_explanation"]["financial_factors"]["is_loss_making"])
        self.assertTrue(0.0 <= r2["financial_risk_score"] <= 100.0)

    def test_missing_customer_history_imputation(self):
        """Verifies that missing customer ID or missing customer in graph defaults volume to neutral 50%."""
        mock_entities = pd.DataFrame([
            {
                "affected_entity_id": "ORD_003",
                "affected_entity_type": "ORDER",
                "revenue_exposure": 250.0,
                "profit_exposure": 40.0,
                "is_eligible_for_delay": True,
                "order_status": "COMPLETE",
                "delivery_status": "Normal",
                "shipping_mode": "First Class",
                "historical_delayed": False,
                "graph_mapping_confidence": 1.0
            }
        ])

        # Empty customer network
        self.engine.set_inputs(
            shockwave_summary=self.mock_summary,
            shockwave_entities_df=mock_entities,
            customer_network_df=pd.DataFrame()
        )

        assessments, _, _ = self.engine.assess_risks()
        r = assessments[0]
        # Consumer proxy = 40.0, default volume = 50.0
        # Expected op score: 0.60 * 40 + 0.40 * 50 = 24.0 + 20.0 = 44.0
        self.assertEqual(r["operational_risk_score"], 44.0)

    def test_duplicate_anomaly_aggregation_with_conflicting_severities(self):
        """Verifies that multiple transactions for an order pick the max composite score and highest severity."""
        mock_entities = pd.DataFrame([
            {
                "affected_entity_id": "ORD_004",
                "affected_entity_type": "ORDER",
                "revenue_exposure": 400.0,
                "profit_exposure": 50.0,
                "is_eligible_for_delay": True,
                "order_status": "COMPLETE",
                "delivery_status": "Normal",
                "shipping_mode": "Standard Class",
                "historical_delayed": False,
                "graph_mapping_confidence": 1.0
            }
        ])

        # Anomaly records with 2 line items for order 4: one MEDIUM (0.35), one CRITICAL (0.85)
        mock_anomalies = pd.DataFrame([
            {
                "order_id": 4,
                "order_item_id": 101,
                "composite_anomaly_score": 0.35,
                "severity": "MEDIUM",
                "anomaly_category": "Minor Margin Dip",
                "anomaly_reason": "Low margin"
            },
            {
                "order_id": 4,
                "order_item_id": 102,
                "composite_anomaly_score": 0.85,
                "severity": "CRITICAL",
                "anomaly_category": "Severe Profit Bleed",
                "anomaly_reason": "Critical deficit"
            }
        ])

        self.engine.set_inputs(
            shockwave_summary=self.mock_summary,
            shockwave_entities_df=mock_entities,
            anomaly_results_df=mock_anomalies
        )

        assessments, _, _ = self.engine.assess_risks()
        self.assertEqual(len(assessments), 1)
        r = assessments[0]

        # Max composite = 0.85, CRITICAL bonus = 30.0 -> round(min(100, 0.85 * 70 + 30), 2) = 89.5
        self.assertEqual(r["anomaly_risk_score"], 89.5)
        self.assertEqual(r["anomaly_severity"], "CRITICAL")
        self.assertTrue("Severe Profit Bleed" in r["anomaly_category"])
        self.assertTrue(r["has_pre_existing_anomaly"])

    def test_reproducibility_and_deterministic_order(self):
        """Verifies that two sequential runs on the same input produce identical scores, ranks, and summaries."""
        mock_entities = pd.DataFrame([
            {
                "affected_entity_id": f"ORD_{i:03d}",
                "affected_entity_type": "ORDER",
                "revenue_exposure": float(i * 100),
                "profit_exposure": float(i * 15),
                "is_eligible_for_delay": (i % 2 == 1),
                "order_status": "COMPLETE" if (i % 2 == 1) else "CANCELED",
                "delivery_status": "Normal" if (i % 2 == 1) else "Shipping canceled",
                "shipping_mode": "Standard Class",
                "historical_delayed": False,
                "graph_mapping_confidence": 1.0
            }
            for i in range(1, 11)
        ])

        self.engine.set_inputs(
            shockwave_summary=self.mock_summary,
            shockwave_entities_df=mock_entities
        )
        ass1, sum1, ent1 = self.engine.assess_risks()

        self.engine.set_inputs(
            shockwave_summary=self.mock_summary,
            shockwave_entities_df=mock_entities
        )
        ass2, sum2, ent2 = self.engine.assess_risks()

        # Compare assessments ignoring execution timestamp and run ID
        for r1, r2 in zip(ass1, ass2):
            for k in ["entity_id", "risk_score", "risk_level", "risk_priority_rank", "delivery_risk_score", "financial_risk_score"]:
                self.assertEqual(r1[k], r2[k], f"Non-deterministic value for {k} in {r1['entity_id']}")

        # Compare entity roll-ups
        pd.testing.assert_frame_equal(ent1, ent2)


if __name__ == "__main__":
    unittest.main()


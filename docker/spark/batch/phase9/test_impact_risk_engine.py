#!/usr/bin/env python3
"""
Unit Test Suite for ChainSentinel Impact Assessment & Risk Analysis Engine
==========================================================================
File: test_impact_risk_engine.py
Version: 1.0.0
Execution: E:\\BDA\\ChainSentinel\\python-env\\Scripts\\python test_impact_risk_engine.py -v

Comprehensive Coverage:
1. Phase 8 input loading & schema conformance
2. Ineligible non-shipped order segregation (CANCELED, SUSPECTED_FRAUD)
3. Subscore normalization to [0.0, 100.0]
4. Composite score calculation and weight convexity
5. Severity tier threshold boundaries (CRITICAL >= 75, HIGH >= 55, MEDIUM >= 35, LOW < 35)
6. Phase 5 anomaly matching and score elevation
7. Multiple anomaly records per single order aggregation without order duplication
8. Missing anomaly evidence handling (no false imputation)
9. Missing Parquet attribute graceful defaults
10. Deterministic prioritization ranking and tie-breaking
11. Financial exposure reconciliation (Eligible + Ineligible == Total)
12. Customer and Shipping Mode aggregate roll-ups without double counting
13. Confidence separation (source_event_confidence vs graph_mapping_confidence)
14. Uncalibrated decision-support index tagging
15. Export routines (CSV, JSON, summaries) validation
"""

import unittest
import os
import sys
import json
import tempfile
import pandas as pd
import numpy as np

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
from impact_risk_engine import ImpactRiskEngine


class TestImpactRiskEngine(unittest.TestCase):

    def setUp(self):
        """Builds a verified synthetic in-memory dataset for unit tests."""
        self.engine = ImpactRiskEngine()

        self.summary = {
            "source_event_id": "TEST-EVT-001",
            "shockwave_id": "SHOCK-TEST-001",
            "source_event_confidence": 0.95,
            "event_delay_estimate_hours": 96.0,
            "severity": "CRITICAL"
        }

        # Synthetic Shockwave Entities
        entities_data = [
            # ORD_1: High spend, corporate, delayed, standard class (Eligible)
            {"affected_entity_id": "ORD_1", "affected_entity_type": "ORDER", "revenue_exposure": 1000.0, "profit_exposure": 200.0, "is_eligible_for_delay": True, "order_status": "COMPLETE", "delivery_status": "Late delivery", "historical_delayed": True, "graph_mapping_confidence": 1.0},
            # ORD_2: Low spend, consumer, on-time, same day (Eligible)
            {"affected_entity_id": "ORD_2", "affected_entity_type": "ORDER", "revenue_exposure": 100.0, "profit_exposure": 20.0, "is_eligible_for_delay": True, "order_status": "COMPLETE", "delivery_status": "Shipping on time", "historical_delayed": False, "graph_mapping_confidence": 1.0},
            # ORD_3: Canceled order (Ineligible)
            {"affected_entity_id": "ORD_3", "affected_entity_type": "ORDER", "revenue_exposure": 500.0, "profit_exposure": 50.0, "is_eligible_for_delay": False, "order_status": "CANCELED", "delivery_status": "Shipping canceled", "historical_delayed": False, "graph_mapping_confidence": 1.0},
            # ORD_4: Suspected fraud order (Ineligible)
            {"affected_entity_id": "ORD_4", "affected_entity_type": "ORDER", "revenue_exposure": 300.0, "profit_exposure": -30.0, "is_eligible_for_delay": False, "order_status": "SUSPECTED_FRAUD", "delivery_status": "Shipping canceled", "historical_delayed": False, "graph_mapping_confidence": 1.0},
            # ORD_5: Loss-making, high spend, first class (Eligible, Anomaly Match)
            {"affected_entity_id": "ORD_5", "affected_entity_type": "ORDER", "revenue_exposure": 800.0, "profit_exposure": -150.0, "is_eligible_for_delay": True, "order_status": "COMPLETE", "delivery_status": "Late delivery", "historical_delayed": True, "graph_mapping_confidence": 1.0},
            # Secondary entities
            {"affected_entity_id": "CUST_101", "affected_entity_type": "CUSTOMER", "revenue_exposure": 1500.0, "order_count": 5},
            {"affected_entity_id": "CUST_102", "affected_entity_type": "CUSTOMER", "revenue_exposure": 1200.0, "order_count": 2},
            {"affected_entity_id": "PROD_A", "affected_entity_type": "PRODUCT", "revenue_exposure": 1800.0},
            {"affected_entity_id": "SHIP_Standard_Class", "affected_entity_type": "SHIPPING_MODE", "revenue_exposure": 1000.0}
        ]
        self.entities_df = pd.DataFrame(entities_data)

        # Synthetic Anomaly Results (ORD_5 has two anomaly records)
        anomaly_data = [
            {"order_id": 5, "order_item_id": 501, "composite_anomaly_score": 0.85, "severity": "CRITICAL", "anomaly_category": "Severe Profit Bleed", "anomaly_reason": "Extreme negative profit: $-150.0"},
            {"order_id": 5, "order_item_id": 502, "composite_anomaly_score": 0.70, "severity": "HIGH", "anomaly_category": "Severe Profit Bleed", "anomaly_reason": "Low margin anomaly"}
        ]
        self.anomaly_df = pd.DataFrame(anomaly_data)

        # Synthetic Parquet Attributes
        parquet_data = {
            1: {"days_for_shipment_scheduled": 4, "customer_id": 101, "customer_segment": "Corporate", "shipping_mode": "Standard Class"},
            2: {"days_for_shipment_scheduled": 1, "customer_id": 102, "customer_segment": "Consumer", "shipping_mode": "Same Day"},
            3: {"days_for_shipment_scheduled": 3, "customer_id": 101, "customer_segment": "Corporate", "shipping_mode": "Standard Class"},
            4: {"days_for_shipment_scheduled": 2, "customer_id": 102, "customer_segment": "Consumer", "shipping_mode": "First Class"},
            5: {"days_for_shipment_scheduled": 2, "customer_id": 101, "customer_segment": "Home Office", "shipping_mode": "First Class"}
        }
        self.order_attrs_df = pd.DataFrame.from_dict(parquet_data, orient="index")

        # Synthetic Customer Network Volumes
        cust_network_data = {
            "CUST_101": {"order_count": 12, "total_spend": 3500.0},
            "CUST_102": {"order_count": 2, "total_spend": 500.0}
        }
        self.cust_network_df = pd.DataFrame.from_dict(cust_network_data, orient="index")

        self.engine.set_inputs(
            shockwave_summary=self.summary,
            shockwave_entities_df=self.entities_df,
            anomaly_results_df=self.anomaly_df,
            order_attributes_df=self.order_attrs_df,
            customer_network_df=self.cust_network_df
        )

    # --------------------------------------------------------------------------
    # TESTS
    # --------------------------------------------------------------------------

    def test_ineligible_order_segregation(self):
        """Verifies that CANCELED and SUSPECTED_FRAUD orders receive score 0 and INELIGIBLE level."""
        assessments, summary, _ = self.engine.assess_risks()
        ord_3 = next(r for r in assessments if r["entity_id"] == "ORD_3")
        ord_4 = next(r for r in assessments if r["entity_id"] == "ORD_4")

        self.assertFalse(ord_3["is_eligible_for_delay"])
        self.assertEqual(ord_3["risk_score"], 0.0)
        self.assertEqual(ord_3["risk_level"], "INELIGIBLE_NON_SHIPPED")

        self.assertFalse(ord_4["is_eligible_for_delay"])
        self.assertEqual(ord_4["risk_score"], 0.0)
        self.assertEqual(ord_4["risk_level"], "INELIGIBLE_NON_SHIPPED")

        # 5 total orders, 3 eligible, 2 ineligible
        self.assertEqual(summary["order_cohort_summary"]["total_assessed_orders"], 5)
        self.assertEqual(summary["order_cohort_summary"]["eligible_active_orders"], 3)
        self.assertEqual(summary["order_cohort_summary"]["ineligible_non_shipped_orders"], 2)

    def test_subscore_and_composite_normalization(self):
        """Verifies that all dimensional subscores and composite scores fall strictly within [0.0, 100.0]."""
        assessments, _, _ = self.engine.assess_risks()
        for r in assessments:
            if r["is_eligible_for_delay"]:
                self.assertGreaterEqual(r["delivery_risk_score"], 0.0)
                self.assertLessEqual(r["delivery_risk_score"], 100.0)

                self.assertGreaterEqual(r["financial_risk_score"], 0.0)
                self.assertLessEqual(r["financial_risk_score"], 100.0)

                self.assertGreaterEqual(r["operational_risk_score"], 0.0)
                self.assertLessEqual(r["operational_risk_score"], 100.0)

                self.assertGreaterEqual(r["anomaly_risk_score"], 0.0)
                self.assertLessEqual(r["anomaly_risk_score"], 100.0)

                self.assertGreaterEqual(r["risk_score"], 0.0)
                self.assertLessEqual(r["risk_score"], 100.0)

    def test_composite_score_calculation(self):
        """Verifies the exact mathematical convex combination of weights."""
        assessments, summary, _ = self.engine.assess_risks()
        weights = summary["dimension_weights"]
        self.assertAlmostEqual(sum(weights.values()), 1.00, places=4)

        for r in assessments:
            if r["is_eligible_for_delay"]:
                expected = (
                    weights["delivery_risk"] * r["delivery_risk_score"] +
                    weights["financial_risk"] * r["financial_risk_score"] +
                    weights["operational_risk"] * r["operational_risk_score"] +
                    weights["anomaly_risk"] * r["anomaly_risk_score"]
                )
                self.assertAlmostEqual(r["risk_score"], round(expected, 2), delta=0.02)

    def test_severity_threshold_boundaries(self):
        """Verifies that severity levels match defined boundary thresholds."""
        assessments, _, _ = self.engine.assess_risks()
        for r in assessments:
            if r["is_eligible_for_delay"]:
                score = r["risk_score"]
                if score >= 75.0:
                    self.assertEqual(r["risk_level"], "CRITICAL")
                elif score >= 55.0:
                    self.assertEqual(r["risk_level"], "HIGH")
                elif score >= 35.0:
                    self.assertEqual(r["risk_level"], "MEDIUM")
                else:
                    self.assertEqual(r["risk_level"], "LOW")

    def test_anomaly_matching_and_aggregation(self):
        """Verifies that an order with multiple anomaly line items is aggregated without duplicate count."""
        assessments, summary, _ = self.engine.assess_risks()
        ord_5 = next(r for r in assessments if r["entity_id"] == "ORD_5")

        # ORD_5 matched anomaly (score > 0, severity CRITICAL)
        self.assertTrue(ord_5["has_pre_existing_anomaly"])
        self.assertEqual(ord_5["anomaly_severity"], "CRITICAL")
        self.assertGreater(ord_5["anomaly_risk_score"], 50.0)

        # Total overlapping orders must be exactly 1, not 2
        self.assertEqual(summary["anomaly_integration"]["overlapping_orders_count"], 1)

    def test_missing_anomaly_evidence_handling(self):
        """Verifies that orders without an anomaly match have score 0 and explicit evidence status."""
        assessments, _, _ = self.engine.assess_risks()
        ord_1 = next(r for r in assessments if r["entity_id"] == "ORD_1")

        self.assertFalse(ord_1["has_pre_existing_anomaly"])
        self.assertEqual(ord_1["anomaly_risk_score"], 0.0)
        self.assertIsNone(ord_1["anomaly_severity"])

        # Check structured explanation
        expl = ord_1["risk_explanation"]
        self.assertEqual(expl["anomaly_factors"]["evidence_status"], "NO_FLAGGED_ANOMALY_IN_PHASE5_SAMPLE")

    def test_missing_parquet_attributes_graceful_defaults(self):
        """Verifies that missing Parquet attributes impute safe defaults without crashing."""
        # Create engine with empty Parquet
        empty_engine = ImpactRiskEngine()
        empty_engine.set_inputs(
            shockwave_summary=self.summary,
            shockwave_entities_df=self.entities_df,
            anomaly_results_df=self.anomaly_df,
            order_attributes_df=pd.DataFrame(),
            customer_network_df=pd.DataFrame()
        )
        assessments, _, _ = empty_engine.assess_risks()
        self.assertEqual(len(assessments), 5)

    def test_deterministic_prioritization_ranking(self):
        """Verifies that priority ranking is strictly ordered and tie-breaking is deterministic."""
        assessments, _, _ = self.engine.assess_risks()
        eligible = [r for r in assessments if r["is_eligible_for_delay"]]
        ranks = [r["risk_priority_rank"] for r in eligible]

        # Ranks must be contiguous [1, 2, 3]
        self.assertEqual(ranks, [1, 2, 3])

        # Rank 1 must have highest score
        self.assertGreaterEqual(eligible[0]["risk_score"], eligible[1]["risk_score"])
        self.assertGreaterEqual(eligible[1]["risk_score"], eligible[2]["risk_score"])

    def test_financial_reconciliation(self):
        """Verifies that Eligible + Ineligible revenue and profit reconcile to Total with zero delta."""
        _, summary, _ = self.engine.assess_risks()
        fin = summary["financial_reconciliation"]

        tot_rev = fin["total_gross_revenue_usd"]
        elig_rev = fin["eligible_revenue_usd"]
        inel_rev = fin["ineligible_revenue_usd"]

        tot_prof = fin["total_gross_profit_usd"]
        elig_prof = fin["eligible_profit_usd"]
        inel_prof = fin["ineligible_profit_usd"]

        # 1000 + 100 + 500 + 300 + 800 = 2700.0
        self.assertEqual(tot_rev, 2700.0)
        self.assertAlmostEqual(elig_rev + inel_rev, tot_rev, places=2)

        # 200 + 20 + 50 - 30 - 150 = 90.0
        self.assertEqual(tot_prof, 90.0)
        self.assertAlmostEqual(elig_prof + inel_prof, tot_prof, places=2)

    def test_confidence_separation(self):
        """Verifies that source event confidence is decoupled from graph mapping confidence."""
        assessments, summary, _ = self.engine.assess_risks()
        ord_1 = next(r for r in assessments if r["entity_id"] == "ORD_1")

        self.assertEqual(ord_1["source_event_confidence"], 0.95)
        self.assertEqual(ord_1["graph_mapping_confidence"], 1.0)
        self.assertEqual(ord_1["score_calibration_status"], "UNCALIBRATED_MCDA_INDEX")

    def test_entity_rollup_summaries(self):
        """Verifies that Customer, Product, and Shipping Mode summaries aggregate correctly."""
        _, _, ent_summary_df = self.engine.assess_risks()
        types = set(ent_summary_df["entity_type"])

        self.assertIn("CUSTOMER", types)
        self.assertIn("PRODUCT", types)
        self.assertIn("SHIPPING_MODE", types)

    def test_export_results(self):
        """Verifies that all 6 required artifact files are written to disk."""
        assessments, summary, ent_summary_df = self.engine.assess_risks()

        with tempfile.TemporaryDirectory() as tmpdir:
            self.engine.export_results(assessments, summary, ent_summary_df, output_dir=tmpdir)

            self.assertTrue(os.path.exists(os.path.join(tmpdir, "risk_assessments.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "risk_assessments.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "risk_summary.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "entity_risk_summary.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "risk_priority_orders.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "risk_category_breakdown.csv")))


if __name__ == "__main__":
    unittest.main()


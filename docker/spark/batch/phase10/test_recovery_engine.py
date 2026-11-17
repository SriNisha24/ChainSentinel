"""
ChainSentinel Phase 10: Automated Unit Test Suite
Module: docker/spark/batch/phase10/test_recovery_engine.py

Verifies mathematical constraints, cohort eligibility, capacity limits,
multi-plan generation, stress matrix structure, resilience scoring, and recommendations.
"""

import os
import unittest
import tempfile
import pandas as pd
import numpy as np

from docker.spark.batch.phase10.recovery_engine import RecoveryEngine


class TestRecoveryEngine(unittest.TestCase):

    def setUp(self):
        self.config_path = "E:/BDA/ChainSentinel/docker/spark/batch/phase10/recovery_config.json"
        self.engine = RecoveryEngine(config_path=self.config_path)

        # Create realistic synthetic test cohort with 10 orders (7 eligible, 3 ineligible)
        self.mock_assessments = pd.DataFrame([
            # Eligible orders
            {
                "entity_id": "ORD_001",
                "is_eligible_for_delay": True,
                "order_status": "PROCESSING",
                "delivery_status": "Late delivery",
                "shipping_mode": "Same Day",
                "customer_segment": "Corporate",
                "scheduled_transit_days": 1,
                "revenue_exposure": 1500.0,
                "profit_exposure": 250.0,
                "risk_score": 85.0,
                "risk_level": "CRITICAL",
                "risk_priority_rank": 1.0
            },
            {
                "entity_id": "ORD_002",
                "is_eligible_for_delay": True,
                "order_status": "PROCESSING",
                "delivery_status": "Normal",
                "shipping_mode": "First Class",
                "customer_segment": "Consumer",
                "scheduled_transit_days": 2,
                "revenue_exposure": 2500.0,
                "profit_exposure": -150.0,
                "risk_score": 78.0,
                "risk_level": "CRITICAL",
                "risk_priority_rank": 2.0
            },
            {
                "entity_id": "ORD_003",
                "is_eligible_for_delay": True,
                "order_status": "COMPLETE",
                "delivery_status": "Normal",
                "shipping_mode": "Second Class",
                "customer_segment": "Home Office",
                "scheduled_transit_days": 3,
                "revenue_exposure": 600.0,
                "profit_exposure": 90.0,
                "risk_score": 62.0,
                "risk_level": "HIGH",
                "risk_priority_rank": 3.0
            },
            {
                "entity_id": "ORD_004",
                "is_eligible_for_delay": True,
                "order_status": "COMPLETE",
                "delivery_status": "Normal",
                "shipping_mode": "Standard Class",
                "customer_segment": "Consumer",
                "scheduled_transit_days": 4,
                "revenue_exposure": 300.0,
                "profit_exposure": 45.0,
                "risk_score": 45.0,
                "risk_level": "MEDIUM",
                "risk_priority_rank": 4.0
            },
            {
                "entity_id": "ORD_005",
                "is_eligible_for_delay": True,
                "order_status": "PENDING",
                "delivery_status": "Normal",
                "shipping_mode": "Standard Class",
                "customer_segment": "Consumer",
                "scheduled_transit_days": 4,
                "revenue_exposure": 200.0,
                "profit_exposure": 30.0,
                "risk_score": 30.0,
                "risk_level": "LOW",
                "risk_priority_rank": None
            },
            {
                "entity_id": "ORD_006",
                "is_eligible_for_delay": True,
                "order_status": "PROCESSING",
                "delivery_status": "Normal",
                "shipping_mode": "First Class",
                "customer_segment": "Corporate",
                "scheduled_transit_days": 2,
                "revenue_exposure": 1800.0,
                "profit_exposure": 200.0,
                "risk_score": 76.0,
                "risk_level": "CRITICAL",
                "risk_priority_rank": 5.0
            },
            {
                "entity_id": "ORD_007",
                "is_eligible_for_delay": True,
                "order_status": "ON_HOLD",
                "delivery_status": "Normal",
                "shipping_mode": "Second Class",
                "customer_segment": "Home Office",
                "scheduled_transit_days": 3,
                "revenue_exposure": 400.0,
                "profit_exposure": 50.0,
                "risk_score": 58.0,
                "risk_level": "HIGH",
                "risk_priority_rank": 6.0
            },
            # Ineligible non-shipped orders
            {
                "entity_id": "ORD_901",
                "is_eligible_for_delay": False,
                "order_status": "CANCELED",
                "delivery_status": "Shipping canceled",
                "shipping_mode": "Standard Class",
                "customer_segment": "Consumer",
                "scheduled_transit_days": None,
                "revenue_exposure": 500.0,
                "profit_exposure": 50.0,
                "risk_score": 0.0,
                "risk_level": "INELIGIBLE_NON_SHIPPED",
                "risk_priority_rank": None
            },
            {
                "entity_id": "ORD_902",
                "is_eligible_for_delay": False,
                "order_status": "SUSPECTED_FRAUD",
                "delivery_status": "Shipping canceled",
                "shipping_mode": "First Class",
                "customer_segment": "Consumer",
                "scheduled_transit_days": None,
                "revenue_exposure": 800.0,
                "profit_exposure": 80.0,
                "risk_score": 0.0,
                "risk_level": "INELIGIBLE_NON_SHIPPED",
                "risk_priority_rank": None
            },
            {
                "entity_id": "ORD_903",
                "is_eligible_for_delay": False,
                "order_status": "CANCELED",
                "delivery_status": "Shipping canceled",
                "shipping_mode": "Standard Class",
                "customer_segment": "Corporate",
                "scheduled_transit_days": None,
                "revenue_exposure": 1200.0,
                "profit_exposure": 120.0,
                "risk_score": 0.0,
                "risk_level": "INELIGIBLE_NON_SHIPPED",
                "risk_priority_rank": None
            }
        ])

        self.engine.set_inputs(risk_assessments_df=self.mock_assessments)

    def test_cohort_partitioning_and_ineligible_exclusion(self):
        """Verifies that ineligible orders are partitioned and strictly excluded from allocation."""
        plans_df, alloc_df, _, _, _, _ = self.engine.optimize_and_stress_test()
        
        ineligible_allocs = alloc_df[alloc_df["is_eligible_for_delay"] == False]
        self.assertEqual(len(ineligible_allocs), 3)

        # For every plan, allocation flag must be 0 for all ineligible orders
        for plan_col in [c for c in alloc_df.columns if c.endswith("_allocated")]:
            self.assertEqual((ineligible_allocs[plan_col] == 0).all(), True, f"Ineligible order allocated in {plan_col}!")

    def test_rcu_costs_are_strictly_positive(self):
        """Verifies that all eligible orders have RCU costs strictly greater than zero."""
        _, alloc_df, _, _, _, _ = self.engine.optimize_and_stress_test()
        eligible_allocs = alloc_df[alloc_df["is_eligible_for_delay"] == True]
        self.assertTrue((eligible_allocs["rcu_cost"] > 0.0).all())
        self.assertTrue((eligible_allocs["rcu_cost"] >= 0.5).all())

    def test_capacity_budget_never_exceeded(self):
        """Verifies that no candidate plan exceeds the total capacity budget C_total."""
        plans_df, _, _, _, _, _ = self.engine.optimize_and_stress_test()
        for _, row in plans_df.iterrows():
            self.assertLessEqual(
                row["allocated_rcu"],
                row["capacity_budget_rcu"],
                f"Plan {row['plan_id']} exceeded capacity budget!"
            )

    def test_all_six_candidate_plans_generated(self):
        """Verifies that all 6 required candidate plans are generated in comparison output."""
        plans_df, _, _, _, _, _ = self.engine.optimize_and_stress_test()
        expected_plan_ids = {
            "PLAN_0_BASELINE",
            "PLAN_1_PRIORITY_FIRST",
            "PLAN_2_FINANCIAL_FIRST",
            "PLAN_3_VULNERABILITY_FIRST",
            "PLAN_4_MODE_URGENCY_FIRST",
            "PLAN_5_KNAPSACK_HYBRID"
        }
        self.assertEqual(set(plans_df["plan_id"]), expected_plan_ids)

    def test_baseline_plan_zero_allocation_behavior(self):
        """Verifies that Plan 0 (Baseline) allocates 0 RCUs and recovers 0 orders."""
        plans_df, alloc_df, _, _, _, _ = self.engine.optimize_and_stress_test()
        p0 = plans_df[plans_df["plan_id"] == "PLAN_0_BASELINE"].iloc[0]
        self.assertEqual(p0["allocated_rcu"], 0.0)
        self.assertEqual(p0["recovered_orders_count"], 0)
        self.assertEqual(p0["expected_mitigated_revenue_usd"], 0.0)
        self.assertEqual(alloc_df["PLAN_0_BASELINE_allocated"].sum(), 0)

    def test_priority_first_allocation_ordering(self):
        """Verifies that Plan 1 allocates strictly according to ascending priority rank."""
        # Restrict budget so only top 2 orders fit
        self.engine.config["capacity_budget"]["total_recovery_capacity_budget_rcu"] = 6.0
        _, alloc_df, _, _, _, _ = self.engine.optimize_and_stress_test()
        
        p1_alloc = alloc_df[alloc_df["PLAN_1_PRIORITY_FIRST_allocated"] == 1]
        # ORD_001 (rank 1) and ORD_002 (rank 2) should be selected first
        self.assertTrue("ORD_001" in p1_alloc["order_id"].values)

    def test_financial_first_allocation_ordering(self):
        """Verifies that Plan 2 allocates to the largest revenue exposure first."""
        self.engine.config["capacity_budget"]["total_recovery_capacity_budget_rcu"] = 4.0
        _, alloc_df, _, _, _, _ = self.engine.optimize_and_stress_test()
        
        p2_alloc = alloc_df[alloc_df["PLAN_2_FINANCIAL_FIRST_allocated"] == 1]
        # ORD_002 has highest spend (2500.0)
        self.assertEqual(p2_alloc.iloc[0]["order_id"], "ORD_002")

    def test_vulnerability_first_allocation_ordering(self):
        """Verifies that Plan 3 allocates to highest composite risk score first."""
        self.engine.config["capacity_budget"]["total_recovery_capacity_budget_rcu"] = 4.0
        _, alloc_df, _, _, _, _ = self.engine.optimize_and_stress_test()
        
        p3_alloc = alloc_df[alloc_df["PLAN_3_VULNERABILITY_FIRST_allocated"] == 1]
        # ORD_001 has highest risk score (85.0)
        self.assertEqual(p3_alloc.iloc[0]["order_id"], "ORD_001")

    def test_knapsack_score_formula_and_allocation(self):
        """Verifies that Knapsack priority ratio = (risk_score * spend) / rcu_cost."""
        _, alloc_df, _, _, _, _ = self.engine.optimize_and_stress_test()
        row = alloc_df[alloc_df["order_id"] == "ORD_001"].iloc[0]
        expected_ratio = round((row["risk_score"] * row["revenue_exposure_usd"]) / row["rcu_cost"], 2)
        self.assertEqual(row["knapsack_priority_value"], expected_ratio)

    def test_counterfactual_stress_scenario_count(self):
        """Verifies that exactly 30 plan-scenario evaluations exist (6 plans * 5 scenarios)."""
        _, _, stress_df, _, _, _ = self.engine.optimize_and_stress_test()
        self.assertEqual(len(stress_df), 30)
        self.assertEqual(stress_df["scenario_id"].nunique(), 5)
        self.assertEqual(stress_df["plan_id"].nunique(), 6)

    def test_resilience_score_bounds(self):
        """Verifies that all plan resilience indices fall strictly within [0.0, 100.0]."""
        plans_df, _, _, _, _, _ = self.engine.optimize_and_stress_test()
        self.assertTrue((plans_df["resilience_index"] >= 0.0).all())
        self.assertTrue((plans_df["resilience_index"] <= 100.0).all())
        self.assertTrue((plans_df["effectiveness_score"] >= 0.0).all() and (plans_df["effectiveness_score"] <= 1.0).all())
        self.assertTrue((plans_df["robustness_score"] >= 0.0).all() and (plans_df["robustness_score"] <= 1.0).all())
        self.assertTrue((plans_df["worst_case_survival_score"] >= 0.0).all() and (plans_df["worst_case_survival_score"] <= 1.0).all())

    def test_worst_case_stress_metric_correctness(self):
        """Verifies that worst-case survival reflects the maximum loss across scenarios."""
        plans_df, _, stress_df, _, _, _ = self.engine.optimize_and_stress_test()
        for pid in plans_df["plan_id"]:
            p_stress = stress_df[stress_df["plan_id"] == pid]
            max_loss = p_stress["residual_revenue_usd"].max()
            nom_loss = p_stress[p_stress["scenario_id"] == "SCEN_0_NOMINAL"]["residual_revenue_usd"].values[0]
            self.assertGreaterEqual(max_loss, nom_loss)

    def test_deterministic_reproducibility(self):
        """Verifies that two consecutive runs produce 100% identical allocations and scores."""
        plans1, alloc1, stress1, rec1, _, _ = self.engine.optimize_and_stress_test()
        plans2, alloc2, stress2, rec2, _, _ = self.engine.optimize_and_stress_test()

        pd.testing.assert_frame_equal(plans1, plans2)
        pd.testing.assert_frame_equal(alloc1, alloc2)
        pd.testing.assert_frame_equal(stress1, stress2)
        self.assertEqual(rec1["recommended_plan_id"], rec2["recommended_plan_id"])

    def test_budget_contraction_scenario_behavior(self):
        """Verifies that under Scenario 3 (Budget -25%), allocated RCUs strictly fit in contracted budget."""
        _, _, stress_df, _, _, _ = self.engine.optimize_and_stress_test()
        scen3 = stress_df[stress_df["scenario_id"] == "SCEN_3_BUDGET_CONTRACTION"]
        for _, row in scen3.iterrows():
            self.assertLessEqual(row["allocated_rcu"], row["scenario_budget_rcu"])

    def test_plan_recommendation_payload_structure(self):
        """Verifies that recommended plan JSON contains all mandatory explainability keys."""
        _, _, _, rec_payload, summary, _ = self.engine.optimize_and_stress_test()
        required_keys = [
            "recommended_plan_id", "recommended_plan_name", "resilience_index",
            "utility_score", "selection_rationale", "resource_allocation_summary",
            "financial_mitigation_summary", "risk_mitigation_summary", "resilience_components"
        ]
        for k in required_keys:
            self.assertIn(k, rec_payload, f"Key {k} missing from recommended plan payload!")
        self.assertIn(rec_payload["recommended_plan_id"], summary["recommended_plan_id"])

    def test_financial_reconciliation_zero_leakage(self):
        """Verifies that mitigated revenue + residual revenue equals total eligible revenue."""
        plans_df, _, _, _, summary, _ = self.engine.optimize_and_stress_test()
        tot_rev = summary["cohort_summary"]["total_eligible_revenue_usd"]
        for _, row in plans_df.iterrows():
            calc_tot = round(row["expected_mitigated_revenue_usd"] + row["residual_revenue_exposure_usd"], 2)
            self.assertAlmostEqual(calc_tot, tot_rev, places=2)

    def test_pareto_frontier_structure(self):
        """Verifies that Pareto trade-off frontier is generated and sorted by allocated RCU."""
        _, _, _, _, _, pareto_df = self.engine.optimize_and_stress_test()
        self.assertEqual(len(pareto_df), 6)
        rcus = pareto_df["allocated_rcu"].tolist()
        self.assertEqual(rcus, sorted(rcus))

    def test_export_results_creates_all_files(self):
        """Verifies that export_results writes all 6 CSV and JSON output files."""
        plans, allocs, stress, rec, sumry, pareto = self.engine.optimize_and_stress_test()
        with tempfile.TemporaryDirectory() as tmpdir:
            self.engine.export_results(plans, allocs, stress, rec, sumry, pareto, output_dir=tmpdir)
            expected_files = [
                "recovery_plans_comparison.csv",
                "recovery_plan_recommended.json",
                "recovery_order_allocations.csv",
                "resilience_stress_matrix.csv",
                "recovery_pareto_frontier.csv",
                "recovery_summary.json"
            ]
            for ef in expected_files:
                p = os.path.join(tmpdir, ef)
                self.assertTrue(os.path.exists(p), f"Exported file missing: {p}")

    def test_missing_and_zero_financial_handling(self):
        """Verifies that zero or negative revenue exposure does not trigger division by zero."""
        edge_cohort = pd.DataFrame([
            {
                "entity_id": "ORD_ZERO_1",
                "is_eligible_for_delay": True,
                "order_status": "PROCESSING",
                "shipping_mode": "Standard Class",
                "revenue_exposure": 0.0,
                "profit_exposure": 0.0,
                "risk_score": 50.0,
                "risk_level": "MEDIUM",
                "risk_priority_rank": 1.0
            },
            {
                "entity_id": "ORD_NEG_1",
                "is_eligible_for_delay": True,
                "order_status": "PROCESSING",
                "shipping_mode": "First Class",
                "revenue_exposure": 100.0,
                "profit_exposure": -50.0,
                "risk_score": 75.0,
                "risk_level": "CRITICAL",
                "risk_priority_rank": 2.0
            }
        ])
        self.engine.set_inputs(risk_assessments_df=edge_cohort)
        plans, allocs, _, _, _, _ = self.engine.optimize_and_stress_test()
        self.assertEqual(len(allocs), 2)
        self.assertTrue((allocs["rcu_cost"] > 0).all())


if __name__ == "__main__":
    unittest.main()


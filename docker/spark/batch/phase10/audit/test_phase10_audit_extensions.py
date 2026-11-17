"""
ChainSentinel Phase 10: Extended Independent Audit Unit Tests
Module: docker/spark/batch/phase10/audit/test_phase10_audit_extensions.py

Validates extreme edge cases, zero/insufficient budgets, exact budget boundaries,
utility weight totals, scenario exposure balancing, and missing attribute resilience.
"""

import os
import unittest
import pandas as pd
import numpy as np

from docker.spark.batch.phase10.recovery_engine import RecoveryEngine


class TestPhase10AuditExtensions(unittest.TestCase):

    def setUp(self):
        self.config_path = "docker/spark/batch/phase10/recovery_config.json"
        self.engine = RecoveryEngine(config_path=self.config_path)

        self.mock_cohort = pd.DataFrame([
            {
                "entity_id": "ORD_AUDIT_1",
                "is_eligible_for_delay": True,
                "order_status": "PROCESSING",
                "shipping_mode": "Standard Class",
                "revenue_exposure": 500.0,
                "profit_exposure": 50.0,
                "risk_score": 80.0,
                "risk_level": "CRITICAL",
                "risk_priority_rank": 1.0,
                "scheduled_transit_days": 2
            },
            {
                "entity_id": "ORD_AUDIT_2",
                "is_eligible_for_delay": True,
                "order_status": "COMPLETE",
                "shipping_mode": "Same Day",
                "revenue_exposure": 2000.0,
                "profit_exposure": 300.0,
                "risk_score": 90.0,
                "risk_level": "CRITICAL",
                "risk_priority_rank": 2.0,
                "scheduled_transit_days": 1
            },
            {
                "entity_id": "ORD_INELIG_1",
                "is_eligible_for_delay": False,
                "order_status": "CANCELED",
                "shipping_mode": "Standard Class",
                "revenue_exposure": 1000.0,
                "profit_exposure": 100.0,
                "risk_score": 0.0,
                "risk_level": "INELIGIBLE_NON_SHIPPED",
                "risk_priority_rank": None,
                "scheduled_transit_days": None
            }
        ])
        self.engine.set_inputs(risk_assessments_df=self.mock_cohort)

    def test_zero_recovery_budget_handling(self):
        """Verifies that with zero recovery budget (C_total = 0.0), all plans allocate 0 RCUs."""
        self.engine.config["capacity_budget"]["total_recovery_capacity_budget_rcu"] = 0.0
        plans_df, alloc_df, _, _, _, _ = self.engine.optimize_and_stress_test()
        
        for _, r in plans_df.iterrows():
            self.assertEqual(r["allocated_rcu"], 0.0)
            self.assertEqual(r["recovered_orders_count"], 0)

        # All allocation flags must be 0
        for col in [c for c in alloc_df.columns if c.endswith("_allocated")]:
            self.assertEqual(alloc_df[col].sum(), 0)

    def test_insufficient_budget_for_cheapest_order(self):
        """Verifies that when budget is smaller than the cheapest order cost, 0 orders are allocated."""
        # Minimum cost is >= 0.5, set budget to 0.2
        self.engine.config["capacity_budget"]["total_recovery_capacity_budget_rcu"] = 0.2
        plans_df, alloc_df, _, _, _, _ = self.engine.optimize_and_stress_test()
        
        for _, r in plans_df.iterrows():
            self.assertEqual(r["allocated_rcu"], 0.0)
            self.assertEqual(r["recovered_orders_count"], 0)

    def test_exact_budget_boundary_allocation(self):
        """Verifies that an order costing exactly the remaining budget is successfully allocated."""
        # ORD_AUDIT_1 with Standard Class ($500) costs 1.0 * (1 + ln(1 + 0.5)) = 1.41 RCU
        costs = self.engine._calculate_rcu_costs(self.mock_cohort.iloc[:1])
        exact_cost = float(costs.iloc[0])
        
        self.engine.config["capacity_budget"]["total_recovery_capacity_budget_rcu"] = exact_cost
        plans_df, alloc_df, _, _, _, _ = self.engine.optimize_and_stress_test()
        
        p1 = plans_df[plans_df["plan_id"] == "PLAN_1_PRIORITY_FIRST"].iloc[0]
        self.assertEqual(p1["recovered_orders_count"], 1)
        self.assertAlmostEqual(p1["allocated_rcu"], exact_cost, places=2)
        self.assertAlmostEqual(p1["unused_rcu"], 0.0, places=2)

    def test_recommendation_and_resilience_weights_sum_to_one(self):
        """Verifies that recommendation weights and resilience metric weights both sum to 1.0."""
        res_weights = self.engine.config["resilience_scoring_weights"]
        self.assertAlmostEqual(sum(res_weights.values()), 1.0, places=6)

        rec_weights = self.engine.config["plan_recommendation_weights"]
        self.assertAlmostEqual(sum(rec_weights.values()), 1.0, places=6)

    def test_compound_demand_surge_financial_balance(self):
        """Verifies that under Scenario 4 (Demand Surge 1.15x), Mitigated + Residual = 1.15 * Base."""
        plans_df, _, stress_df, _, summary, _ = self.engine.optimize_and_stress_test()
        tot_rev = summary["cohort_summary"]["total_eligible_revenue_usd"]
        expected_surge_rev = round(tot_rev * 1.15, 2)

        scen4 = stress_df[stress_df["scenario_id"] == "SCEN_4_COMPOUND_SHOCK"]
        for _, row in scen4.iterrows():
            actual_sum = round(row["mitigated_revenue_usd"] + row["residual_revenue_usd"], 2)
            self.assertAlmostEqual(actual_sum, expected_surge_rev, places=2)


if __name__ == "__main__":
    unittest.main()


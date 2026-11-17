"""
ChainSentinel Phase 10: Recovery Planning & Resilience-Aware Optimization Engine
Module: docker/spark/batch/phase10/recovery_engine.py

Purpose:
Transforms Phase 8 shockwave propagation and Phase 9 impact risk assessments into
actionable, multi-criteria recovery alternatives. Evaluates plans across five
counterfactual disruption stress scenarios, computes dynamic resilience indices,
and selects the recommended resilient recovery plan.

Architecture:
Runs host-side in Windows Python virtual environment (python-env) using vectorized
NumPy and Pandas algorithms. Zero cluster contention on active Spark streaming jobs.
"""

import os
import sys
import json
import time
import uuid
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd

# Set Matplotlib headless backend
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns


class RecoveryEngine:
    """
    Core Optimization and Counterfactual Stress-Testing Engine for Phase 10.
    """

    def __init__(self, config_path: str = "docker/spark/batch/phase10/recovery_config.json"):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        
        # Ingestion state
        self.risk_assessments_df: Optional[pd.DataFrame] = None
        self.risk_priority_df: Optional[pd.DataFrame] = None
        self.risk_summary: Optional[Dict[str, Any]] = None

    def _load_config(self, path: str) -> Dict[str, Any]:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_inputs(
        self,
        risk_assessments_path: Optional[str] = None,
        risk_priority_path: Optional[str] = None,
        risk_summary_path: Optional[str] = None
    ):
        """Loads Phase 9 authoritative assessment inputs."""
        paths = self.config.get("default_paths", {})
        ass_path = risk_assessments_path or paths.get("risk_assessments", "data/phase9/output/risk_assessments.csv")
        prio_path = risk_priority_path or paths.get("risk_priority_orders", "data/phase9/output/risk_priority_orders.csv")
        sum_path = risk_summary_path or paths.get("risk_summary", "data/phase9/output/risk_summary.json")

        if not os.path.exists(ass_path):
            raise FileNotFoundError(f"Phase 9 risk assessments CSV not found at: {ass_path}")
        self.risk_assessments_df = pd.read_csv(ass_path)
        print(f"[INFO] Loaded {len(self.risk_assessments_df):,} order risk assessments from: {ass_path}")

        if not os.path.exists(prio_path):
            raise FileNotFoundError(f"Phase 9 priority queue CSV not found at: {prio_path}")
        self.risk_priority_df = pd.read_csv(prio_path)
        print(f"[INFO] Loaded {len(self.risk_priority_df):,} high-priority orders from: {prio_path}")

        if os.path.exists(sum_path):
            with open(sum_path, "r", encoding="utf-8") as f:
                self.risk_summary = json.load(f)
            print(f"[INFO] Loaded Phase 9 executive risk summary from: {sum_path}")
        else:
            print(f"[WARN] Phase 9 risk summary JSON not found at: {sum_path}. Proceeding with CSV metrics.")
            self.risk_summary = {}

    def set_inputs(
        self,
        risk_assessments_df: pd.DataFrame,
        risk_priority_df: Optional[pd.DataFrame] = None,
        risk_summary: Optional[Dict[str, Any]] = None
    ):
        """Direct in-memory injection of inputs (useful for testing)."""
        self.risk_assessments_df = risk_assessments_df.copy()
        self.risk_priority_df = risk_priority_df.copy() if risk_priority_df is not None else pd.DataFrame()
        self.risk_summary = risk_summary or {}

    def _calculate_rcu_costs(self, df: pd.DataFrame) -> pd.Series:
        """
        Calculates Normalized Recovery Capacity Units (RCUs) for each eligible order:
        cost = base_rcu(mode) * (1.0 + ln(1.0 + max(0, revenue) / scaling_factor))
        """
        cost_params = self.config.get("cost_parameters", {})
        base_map = cost_params.get("base_rcu_by_shipping_mode", {
            "Same Day": 2.0, "First Class": 1.5, "Second Class": 1.25, "Standard Class": 1.0
        })
        scale = float(cost_params.get("spend_log_scaling_factor", 1000.0))
        min_cost = float(cost_params.get("min_rcu_cost", 0.5))

        base_costs = df["shipping_mode"].map(base_map).fillna(1.0)
        spends = df["revenue_exposure"].fillna(0.0).clip(lower=0.0)
        spend_multipliers = 1.0 + np.log1p(spends / scale)
        
        calculated_costs = np.round(base_costs * spend_multipliers, 2)
        return calculated_costs.clip(lower=min_cost)

    def optimize_and_stress_test(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any], pd.DataFrame]:
        """
        Executes candidate plan generation, knapsack capacity allocation,
        counterfactual stress-testing, resilience index scoring, and plan recommendation.
        
        Returns:
            (plans_comparison_df, order_allocations_df, stress_matrix_df, recommended_plan_dict, pareto_frontier_df)
        """
        if self.risk_assessments_df is None:
            raise RuntimeError("Inputs not loaded. Call load_inputs() or set_inputs() first.")

        t_start = time.time()
        df = self.risk_assessments_df.copy()

        # ----------------------------------------------------------------------
        # 1. COHORT SEGREGATION & FEATURE ENRICHMENT
        # ----------------------------------------------------------------------
        total_orders = len(df)
        eligible_mask = (df["is_eligible_for_delay"] == True)
        eligible_df = df[eligible_mask].copy()
        ineligible_df = df[~eligible_mask].copy()

        n_eligible = len(eligible_df)
        n_ineligible = len(ineligible_df)
        print(f"[INFO] Partitioned cohort: {n_eligible:,} eligible orders, {n_ineligible:,} ineligible non-shipped orders.")

        # Compute RCU costs for eligible orders
        eligible_df["rcu_cost"] = self._calculate_rcu_costs(eligible_df)
        ineligible_df["rcu_cost"] = 0.0

        # Compute Knapsack priority ratio: (risk_score * revenue_exposure) / rcu_cost
        spends = eligible_df["revenue_exposure"].fillna(0.0).clip(lower=0.0)
        risk_scores = eligible_df["risk_score"].fillna(0.0)
        eligible_df["knapsack_priority_value"] = np.round((risk_scores * spends) / eligible_df["rcu_cost"], 2)
        ineligible_df["knapsack_priority_value"] = 0.0

        # Mode urgency score mapping
        mode_urgency_map = {"Same Day": 100.0, "First Class": 75.0, "Second Class": 50.0, "Standard Class": 25.0}
        if "shipping_mode" in eligible_df.columns:
            eligible_df["mode_urgency_score"] = eligible_df["shipping_mode"].map(mode_urgency_map).fillna(25.0)
        else:
            eligible_df["mode_urgency_score"] = 25.0
        ineligible_df["mode_urgency_score"] = 0.0

        # Transit buffer urgency: (4 - days_sched) / 3 * 100
        if "scheduled_transit_days" in eligible_df.columns:
            days_sched = eligible_df["scheduled_transit_days"].fillna(3.0).clip(lower=1.0, upper=4.0)
        else:
            days_sched = pd.Series(3.0, index=eligible_df.index)
        eligible_df["scheduled_transit_buffer_urgency"] = np.round((4.0 - days_sched) / 3.0 * 100.0, 2)
        ineligible_df["scheduled_transit_buffer_urgency"] = 0.0

        # Fill priority rank for non-priority orders to large integer
        if "risk_priority_rank" in eligible_df.columns:
            eligible_df["risk_priority_rank_clean"] = eligible_df["risk_priority_rank"].fillna(999999).astype(int)
        else:
            eligible_df["risk_priority_rank_clean"] = 999999
        ineligible_df["risk_priority_rank_clean"] = 999999

        # Ensure entity_id is string
        eligible_df["entity_id"] = eligible_df["entity_id"].astype(str)
        ineligible_df["entity_id"] = ineligible_df["entity_id"].astype(str)

        # Baseline portfolio metrics (Eligible Active Cohort)
        total_eligible_revenue = float(eligible_df["revenue_exposure"].sum())
        total_eligible_profit = float(eligible_df["profit_exposure"].sum())
        total_eligible_risk_points = float(eligible_df["risk_score"].sum())
        total_critical_orders = int((eligible_df["risk_level"] == "CRITICAL").sum())
        total_high_orders = int((eligible_df["risk_level"] == "HIGH").sum())

        budget_cfg = self.config.get("capacity_budget", {})
        c_total = float(budget_cfg.get("total_recovery_capacity_budget_rcu", 1000.0))
        print(f"[INFO] Bounded recovery capacity budget: {c_total:,.1f} RCUs.")

        # Effectiveness parameters
        eff_params = self.config.get("effectiveness_parameters", {})
        base_nom_eff = float(eff_params.get("base_nominal_effectiveness", 0.85))
        mode_eff_map = eff_params.get("mode_effectiveness_modifiers", {
            "Same Day": 0.90, "First Class": 0.88, "Second Class": 0.85, "Standard Class": 0.82
        })
        eligible_df["nominal_effectiveness"] = eligible_df["shipping_mode"].map(mode_eff_map).fillna(base_nom_eff)
        ineligible_df["nominal_effectiveness"] = 0.0

        # ----------------------------------------------------------------------
        # 2. GENERATE SIX CANDIDATE RECOVERY PLANS
        # ----------------------------------------------------------------------
        candidate_plan_defs = self.config.get("candidate_plans", [])
        plan_allocations: Dict[str, pd.Series] = {}
        plan_metrics: List[Dict[str, Any]] = []

        # Order allocation tracking table
        allocations_df = pd.concat([eligible_df, ineligible_df], ignore_index=True)

        for p_def in candidate_plan_defs:
            p_id = p_def["plan_id"]
            p_name = p_def["name"]
            stype = p_def["strategy_type"]
            sort_keys = p_def.get("sort_keys", ["risk_score"])
            sort_asc = p_def.get("sort_ascending", [False])

            if stype == "DO_NOTHING":
                # Plan 0: Baseline
                alloc_flags = pd.Series(0, index=eligible_df.index)
            else:
                # Sort eligible orders deterministically
                sorted_eligible = eligible_df.sort_values(by=sort_keys, ascending=sort_asc)
                
                # Greedily allocate capacity up to c_total
                costs = sorted_eligible["rcu_cost"].values
                cum_costs = np.cumsum(costs)
                selected_indices = sorted_eligible.index[cum_costs <= c_total]
                
                alloc_flags = pd.Series(0, index=eligible_df.index)
                alloc_flags.loc[selected_indices] = 1

            # Save allocation flags for this plan
            plan_allocations[p_id] = alloc_flags

            # Nominal performance metrics
            allocated_orders = eligible_df[alloc_flags == 1]
            n_recovered = len(allocated_orders)
            rcu_used = float(allocated_orders["rcu_cost"].sum())
            rcu_unused = max(0.0, c_total - rcu_used)

            # Expected nominal mitigation
            mitigated_rev = float((allocated_orders["revenue_exposure"] * allocated_orders["nominal_effectiveness"]).sum())
            mitigated_prof = float((allocated_orders["profit_exposure"] * allocated_orders["nominal_effectiveness"]).sum())
            mitigated_risk = float((allocated_orders["risk_score"] * allocated_orders["nominal_effectiveness"]).sum())

            res_rev = total_eligible_revenue - mitigated_rev
            res_prof = total_eligible_profit - mitigated_prof
            res_risk = total_eligible_risk_points - mitigated_risk

            # Unrecovered critical and high orders
            unrecovered_critical = int(((eligible_df["risk_level"] == "CRITICAL") & (alloc_flags == 0)).sum())
            unrecovered_high = int(((eligible_df["risk_level"] == "HIGH") & (alloc_flags == 0)).sum())

            recovered_critical = total_critical_orders - unrecovered_critical
            recovered_high = total_high_orders - unrecovered_high

            plan_metrics.append({
                "plan_id": p_id,
                "plan_name": p_name,
                "strategy_type": stype,
                "capacity_budget_rcu": c_total,
                "allocated_rcu": round(rcu_used, 2),
                "unused_rcu": round(rcu_unused, 2),
                "utilization_pct": round((rcu_used / c_total) * 100.0, 2) if c_total > 0 else 0.0,
                "recovered_orders_count": n_recovered,
                "unrecovered_orders_count": n_eligible - n_recovered,
                "recovered_critical_orders": recovered_critical,
                "unrecovered_critical_orders": unrecovered_critical,
                "recovered_high_orders": recovered_high,
                "unrecovered_high_orders": unrecovered_high,
                "expected_mitigated_revenue_usd": round(mitigated_rev, 2),
                "residual_revenue_exposure_usd": round(res_rev, 2),
                "revenue_mitigation_pct": round((mitigated_rev / total_eligible_revenue) * 100.0, 2) if total_eligible_revenue > 0 else 0.0,
                "expected_mitigated_profit_usd": round(mitigated_prof, 2),
                "residual_profit_exposure_usd": round(res_prof, 2),
                "expected_mitigated_risk_points": round(mitigated_risk, 2),
                "residual_risk_points": round(res_risk, 2),
                "risk_mitigation_pct": round((mitigated_risk / total_eligible_risk_points) * 100.0, 2) if total_eligible_risk_points > 0 else 0.0
            })

        plans_df = pd.DataFrame(plan_metrics)

        # ----------------------------------------------------------------------
        # 3. COUNTERFACTUAL STRESS-TESTING ENGINE (30 Plan-Scenario Evaluations)
        # ----------------------------------------------------------------------
        scenarios = self.config.get("counterfactual_stress_scenarios", [])
        stress_results: List[Dict[str, Any]] = []

        baseline_nominal_damage = plans_df.loc[plans_df["plan_id"] == "PLAN_0_BASELINE", "residual_revenue_exposure_usd"].values[0]

        for p_def in candidate_plan_defs:
            p_id = p_def["plan_id"]
            p_name = p_def["name"]
            base_alloc = plan_allocations[p_id]

            for scen in scenarios:
                s_id = scen["scenario_id"]
                s_name = scen["name"]
                budget_mult = float(scen.get("budget_multiplier", 1.0))
                eff_mult = float(scen.get("effectiveness_multiplier", 1.0))
                demand_mult = float(scen.get("demand_surge_multiplier", 1.0))
                carrier_mult = float(scen.get("carrier_capacity_multiplier", 1.0))

                # Effective scenario budget
                scen_budget = c_total * budget_mult

                # If budget contracts, enforce contracted budget limit on base allocations
                if p_id == "PLAN_0_BASELINE":
                    scen_alloc = pd.Series(0, index=eligible_df.index)
                else:
                    sorted_p_orders = eligible_df.loc[base_alloc[base_alloc == 1].index]
                    cum_scen_costs = np.cumsum(sorted_p_orders["rcu_cost"].values)
                    valid_indices = sorted_p_orders.index[cum_scen_costs <= scen_budget]
                    scen_alloc = pd.Series(0, index=eligible_df.index)
                    scen_alloc.loc[valid_indices] = 1

                scen_recovered_orders = eligible_df[scen_alloc == 1]
                scen_n_recovered = len(scen_recovered_orders)
                scen_rcu_used = float(scen_recovered_orders["rcu_cost"].sum())
                scen_rcu_unused = max(0.0, scen_budget - scen_rcu_used)

                # Adjusted effectiveness under stress (carrier crunch / compounding shock)
                scen_order_eff = scen_recovered_orders["nominal_effectiveness"] * eff_mult

                # Mitigated exposures
                scen_mit_rev = float((scen_recovered_orders["revenue_exposure"] * scen_order_eff).sum())
                scen_mit_prof = float((scen_recovered_orders["profit_exposure"] * scen_order_eff).sum())
                scen_mit_risk = float((scen_recovered_orders["risk_score"] * scen_order_eff).sum())

                # Residual exposures under demand surge multiplier
                scen_base_rev = total_eligible_revenue * demand_mult
                scen_res_rev = max(0.0, scen_base_rev - scen_mit_rev)
                scen_res_prof = max(0.0, (total_eligible_profit * demand_mult) - scen_mit_prof)
                scen_res_risk = max(0.0, (total_eligible_risk_points * demand_mult) - scen_mit_risk)

                scen_unrec_crit = int(((eligible_df["risk_level"] == "CRITICAL") & (scen_alloc == 0)).sum())
                scen_unrec_high = int(((eligible_df["risk_level"] == "HIGH") & (scen_alloc == 0)).sum())

                # Degradation relative to nominal plan performance
                nom_res_rev = plans_df.loc[plans_df["plan_id"] == p_id, "residual_revenue_exposure_usd"].values[0]
                rev_degradation_pct = round(((scen_res_rev - nom_res_rev) / (nom_res_rev + 1e-6)) * 100.0, 2)

                stress_results.append({
                    "plan_id": p_id,
                    "plan_name": p_name,
                    "scenario_id": s_id,
                    "scenario_name": s_name,
                    "scenario_budget_rcu": round(scen_budget, 2),
                    "allocated_rcu": round(scen_rcu_used, 2),
                    "unused_rcu": round(scen_rcu_unused, 2),
                    "effective_recovered_orders": scen_n_recovered,
                    "unrecovered_orders": n_eligible - scen_n_recovered,
                    "unrecovered_critical_orders": scen_unrec_crit,
                    "unrecovered_high_orders": scen_unrec_high,
                    "mitigated_revenue_usd": round(scen_mit_rev, 2),
                    "residual_revenue_usd": round(scen_res_rev, 2),
                    "mitigated_profit_usd": round(scen_mit_prof, 2),
                    "residual_profit_usd": round(scen_res_prof, 2),
                    "residual_risk_points": round(scen_res_risk, 2),
                    "revenue_degradation_pct": rev_degradation_pct
                })

        stress_matrix_df = pd.DataFrame(stress_results)

        # ----------------------------------------------------------------------
        # 4. RESILIENCE SCORING INDEX (R_p = 100 * (0.50*E + 0.30*B + 0.20*W))
        # ----------------------------------------------------------------------
        res_weights = self.config.get("resilience_scoring_weights", {"effectiveness_weight": 0.50, "robustness_weight": 0.30, "worst_case_weight": 0.20})
        w_eff = float(res_weights.get("effectiveness_weight", 0.50))
        w_rob = float(res_weights.get("robustness_weight", 0.30))
        w_wc = float(res_weights.get("worst_case_weight", 0.20))

        resilience_scores: Dict[str, Dict[str, float]] = {}

        for p_id in plans_df["plan_id"]:
            p_stress = stress_matrix_df[stress_matrix_df["plan_id"] == p_id]
            nom_row = p_stress[p_stress["scenario_id"] == "SCEN_0_NOMINAL"].iloc[0]

            # 1. Effectiveness: Normalized nominal revenue mitigation
            eff_score = float(nom_row["mitigated_revenue_usd"] / (baseline_nominal_damage + 1e-6))
            eff_score = max(0.0, min(1.0, eff_score))

            # 2. Robustness: Inverted standard deviation of residual loss across all 5 scenarios
            res_losses = p_stress["residual_revenue_usd"].values
            mu_loss = np.mean(res_losses)
            sigma_loss = np.std(res_losses)
            cv_loss = (sigma_loss / (mu_loss + 1e-6))  # Coefficient of variation
            rob_score = max(0.0, min(1.0, 1.0 - cv_loss))

            # 3. Worst-Case Survival: Performance retention in worst stress scenario
            worst_loss = np.max(res_losses)
            worst_baseline = np.max(stress_matrix_df[stress_matrix_df["plan_id"] == "PLAN_0_BASELINE"]["residual_revenue_usd"].values)
            wc_score = max(0.0, min(1.0, 1.0 - (worst_loss / (worst_baseline + 1e-6))))

            composite_resilience = round(100.0 * (w_eff * eff_score + w_rob * rob_score + w_wc * wc_score), 2)

            resilience_scores[p_id] = {
                "effectiveness_score": round(eff_score, 4),
                "robustness_score": round(rob_score, 4),
                "worst_case_score": round(wc_score, 4),
                "resilience_index": composite_resilience
            }

        # Merge resilience metrics into plans_df
        plans_df["effectiveness_score"] = plans_df["plan_id"].apply(lambda pid: resilience_scores[pid]["effectiveness_score"])
        plans_df["robustness_score"] = plans_df["plan_id"].apply(lambda pid: resilience_scores[pid]["robustness_score"])
        plans_df["worst_case_survival_score"] = plans_df["plan_id"].apply(lambda pid: resilience_scores[pid]["worst_case_score"])
        plans_df["resilience_index"] = plans_df["plan_id"].apply(lambda pid: resilience_scores[pid]["resilience_index"])

        # ----------------------------------------------------------------------
        # 5. MULTI-ATTRIBUTE PLAN RECOMMENDATION
        # ----------------------------------------------------------------------
        rec_weights = self.config.get("plan_recommendation_weights", {
            "resilience_index_weight": 0.40,
            "residual_revenue_mitigation_weight": 0.25,
            "critical_orders_saved_weight": 0.20,
            "rcu_cost_efficiency_weight": 0.15
        })

        # Calculate multi-attribute utility score
        max_resilience = plans_df["resilience_index"].max()
        plans_df["utility_score"] = np.round(
            rec_weights["resilience_index_weight"] * (plans_df["resilience_index"] / (max_resilience + 1e-6)) +
            rec_weights["residual_revenue_mitigation_weight"] * (plans_df["revenue_mitigation_pct"] / 100.0) +
            rec_weights["critical_orders_saved_weight"] * (plans_df["recovered_critical_orders"] / (total_critical_orders + 1e-6)) +
            rec_weights["rcu_cost_efficiency_weight"] * (1.0 - plans_df["allocated_rcu"] / (c_total + 1e-6)),
            4
        )

        # Sort plans by utility score descending
        plans_df = plans_df.sort_values(by=["utility_score", "resilience_index", "revenue_mitigation_pct"], ascending=[False, False, False]).reset_index(drop=True)
        recommended_row = plans_df.iloc[0]
        recommended_plan_id = recommended_row["plan_id"]
        print(f"[INFO] Recommended Plan: {recommended_plan_id} ({recommended_row['plan_name']}) with Resilience Index {recommended_row['resilience_index']}")

        # ----------------------------------------------------------------------
        # 6. ORDER ALLOCATIONS TABLE PREPARATION
        # ----------------------------------------------------------------------
        order_alloc_records = []
        for _, row in eligible_df.iterrows():
            eid = row["entity_id"]
            rec = {
                "order_id": eid,
                "is_eligible_for_delay": True,
                "order_status": row.get("order_status", "COMPLETE"),
                "shipping_mode": row.get("shipping_mode", "Standard Class"),
                "customer_segment": row.get("customer_segment", "Consumer"),
                "scheduled_transit_days": row.get("scheduled_transit_days", 3),
                "revenue_exposure_usd": float(row.get("revenue_exposure", 0.0)),
                "profit_exposure_usd": float(row.get("profit_exposure", 0.0)),
                "risk_score": float(row.get("risk_score", 0.0)),
                "risk_level": row.get("risk_level", "LOW"),
                "risk_priority_rank": row.get("risk_priority_rank"),
                "rcu_cost": float(row["rcu_cost"]),
                "knapsack_priority_value": float(row["knapsack_priority_value"])
            }
            for p_def in candidate_plan_defs:
                pid = p_def["plan_id"]
                rec[f"{pid}_allocated"] = int(plan_allocations[pid].get(row.name, 0))
            order_alloc_records.append(rec)

        for _, row in ineligible_df.iterrows():
            eid = row["entity_id"]
            rec = {
                "order_id": eid,
                "is_eligible_for_delay": False,
                "order_status": row.get("order_status", "CANCELED"),
                "shipping_mode": row.get("shipping_mode", "Standard Class"),
                "customer_segment": row.get("customer_segment", "Consumer"),
                "scheduled_transit_days": None,
                "revenue_exposure_usd": float(row.get("revenue_exposure", 0.0)),
                "profit_exposure_usd": float(row.get("profit_exposure", 0.0)),
                "risk_score": 0.0,
                "risk_level": "INELIGIBLE_NON_SHIPPED",
                "risk_priority_rank": None,
                "rcu_cost": 0.0,
                "knapsack_priority_value": 0.0
            }
            for p_def in candidate_plan_defs:
                pid = p_def["plan_id"]
                rec[f"{pid}_allocated"] = 0
            order_alloc_records.append(rec)

        order_allocations_df = pd.DataFrame(order_alloc_records)

        # ----------------------------------------------------------------------
        # 7. PARETO TRADE-OFF FRONTIER TABLE
        # ----------------------------------------------------------------------
        pareto_df = plans_df[[
            "plan_id", "plan_name", "allocated_rcu", "residual_revenue_exposure_usd",
            "residual_risk_points", "unrecovered_critical_orders", "resilience_index"
        ]].copy().sort_values(by="allocated_rcu")

        # ----------------------------------------------------------------------
        # 8. RECOMMENDED PLAN EXPLAINABILITY PAYLOAD
        # ----------------------------------------------------------------------
        recommended_plan_payload = {
            "recommended_plan_id": recommended_plan_id,
            "recommended_plan_name": recommended_row["plan_name"],
            "strategy_type": recommended_row["strategy_type"],
            "resilience_index": float(recommended_row["resilience_index"]),
            "utility_score": float(recommended_row["utility_score"]),
            "selection_rationale": (
                f"Selected {recommended_row['plan_name']} as the optimal balance between high resilience "
                f"({recommended_row['resilience_index']}/100), revenue protection "
                f"(${recommended_row['expected_mitigated_revenue_usd']:,.2f} / {recommended_row['revenue_mitigation_pct']}%), "
                f"and critical order defense ({recommended_row['recovered_critical_orders']}/{total_critical_orders} saved)."
            ),
            "resource_allocation_summary": {
                "capacity_budget_rcu": c_total,
                "allocated_rcu": float(recommended_row["allocated_rcu"]),
                "unused_rcu": float(recommended_row["unused_rcu"]),
                "capacity_utilization_pct": float(recommended_row["utilization_pct"]),
                "recovered_orders_count": int(recommended_row["recovered_orders_count"]),
                "unrecovered_orders_count": int(recommended_row["unrecovered_orders_count"])
            },
            "financial_mitigation_summary": {
                "total_eligible_revenue_usd": total_eligible_revenue,
                "expected_mitigated_revenue_usd": float(recommended_row["expected_mitigated_revenue_usd"]),
                "residual_revenue_exposure_usd": float(recommended_row["residual_revenue_exposure_usd"]),
                "revenue_mitigation_pct": float(recommended_row["revenue_mitigation_pct"])
            },
            "risk_mitigation_summary": {
                "total_eligible_risk_points": total_eligible_risk_points,
                "expected_mitigated_risk_points": float(recommended_row["expected_mitigated_risk_points"]),
                "residual_risk_points": float(recommended_row["residual_risk_points"]),
                "recovered_critical_orders": int(recommended_row["recovered_critical_orders"]),
                "unrecovered_critical_orders": int(recommended_row["unrecovered_critical_orders"]),
                "recovered_high_orders": int(recommended_row["recovered_high_orders"]),
                "unrecovered_high_orders": int(recommended_row["unrecovered_high_orders"])
            },
            "resilience_components": {
                "effectiveness_component": float(recommended_row["effectiveness_score"]),
                "robustness_component": float(recommended_row["robustness_score"]),
                "worst_case_survival_component": float(recommended_row["worst_case_survival_score"]),
                "weights": res_weights
            },
            "counterfactual_stress_summary": stress_matrix_df[stress_matrix_df["plan_id"] == recommended_plan_id][[
                "scenario_id", "scenario_name", "residual_revenue_usd", "revenue_degradation_pct", "unrecovered_critical_orders"
            ]].to_dict(orient="records"),
            "academic_assumptions": self.config.get("academic_assumptions", []),
            "execution_metadata": {
                "execution_timestamp": datetime.now(timezone.utc).isoformat(),
                "execution_time_seconds": round(time.time() - t_start, 4),
                "framework": "Host Python + NumPy + Pandas",
                "version": self.config.get("version", "1.0.0")
            }
        }

        # Global recovery summary
        recovery_summary = {
            "recovery_run_id": f"REC-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}",
            "execution_timestamp": datetime.now(timezone.utc).isoformat(),
            "cohort_summary": {
                "total_assessed_orders": total_orders,
                "eligible_active_orders": n_eligible,
                "ineligible_quarantined_orders": n_ineligible,
                "total_eligible_revenue_usd": round(total_eligible_revenue, 2),
                "total_eligible_profit_usd": round(total_eligible_profit, 2),
                "total_critical_orders": total_critical_orders,
                "total_high_orders": total_high_orders
            },
            "capacity_budget_rcu": c_total,
            "recommended_plan_id": recommended_plan_id,
            "plans_ranked": plans_df[["plan_id", "plan_name", "resilience_index", "revenue_mitigation_pct", "allocated_rcu", "utility_score"]].to_dict(orient="records"),
            "execution_metadata": {
                "execution_time_seconds": round(time.time() - t_start, 4),
                "framework": "Host Python + NumPy + Pandas",
                "version": self.config.get("version", "1.0.0")
            }
        }

        return plans_df, order_allocations_df, stress_matrix_df, recommended_plan_payload, recovery_summary, pareto_df

    def generate_visualizations(
        self,
        plans_df: pd.DataFrame,
        stress_matrix_df: pd.DataFrame,
        pareto_df: pd.DataFrame,
        output_dir: str
    ):
        """Generates 5 informative charts under reports/phase10/."""
        os.makedirs(output_dir, exist_ok=True)
        sns.set_theme(style="whitegrid", palette="muted")

        # 1. Plan Comparison Bar Chart (Revenue Mitigation & Critical Orders Saved)
        fig, ax1 = plt.subplots(figsize=(10, 5))
        color = "tab:blue"
        ax1.set_title("Candidate Recovery Plans — Revenue Mitigation & Critical Orders Saved", fontsize=13, weight="bold")
        ax1.bar(plans_df["plan_id"], plans_df["revenue_mitigation_pct"], color=color, alpha=0.7, label="Revenue Mitigated (%)")
        ax1.set_ylabel("Revenue Mitigated (%)", color=color, fontsize=11)
        ax1.tick_params(axis="y", labelcolor=color)
        ax1.set_ylim(0, 100)
        plt.xticks(rotation=20, ha="right")

        ax2 = ax1.twinx()
        color = "tab:red"
        ax2.plot(plans_df["plan_id"], plans_df["recovered_critical_orders"], color=color, marker="o", linewidth=2.5, label="Critical Orders Saved")
        ax2.set_ylabel("Critical Orders Saved (Count)", color=color, fontsize=11)
        ax2.tick_params(axis="y", labelcolor=color)
        ax2.set_ylim(0, 22)
        fig.tight_layout()
        chart1_path = os.path.join(output_dir, "plan_comparison.png")
        plt.savefig(chart1_path, dpi=200)
        plt.close()

        # 2. Recovery Resource Allocation (RCU Used vs Unused)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_title("Recovery Resource Allocation by Plan (Capacity = 1,000 RCUs)", fontsize=13, weight="bold")
        p_ids = plans_df["plan_id"]
        used = plans_df["allocated_rcu"]
        unused = plans_df["unused_rcu"]
        ax.bar(p_ids, used, label="Allocated RCUs", color="#2ca02c", alpha=0.8)
        ax.bar(p_ids, unused, bottom=used, label="Unused RCUs", color="#d62728", alpha=0.3)
        ax.set_ylabel("Recovery Capacity Units (RCUs)", fontsize=11)
        ax.legend(loc="upper left")
        plt.xticks(rotation=20, ha="right")
        fig.tight_layout()
        chart2_path = os.path.join(output_dir, "recovery_resource_allocation.png")
        plt.savefig(chart2_path, dpi=200)
        plt.close()

        # 3. Residual Exposure Comparison
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_title("Residual Revenue Exposure by Plan Across Disruption", fontsize=13, weight="bold")
        sns.barplot(data=plans_df, x="plan_id", y="residual_revenue_exposure_usd", palette="Blues_d", ax=ax)
        ax.set_ylabel("Residual Revenue Exposure (USD)", fontsize=11)
        for p in ax.patches:
            val = p.get_height()
            if val > 0:
                ax.annotate(f"${val:,.0f}", (p.get_x() + p.get_width() / 2., val / 2),
                            ha="center", va="center", color="white", weight="bold", fontsize=9)
        plt.xticks(rotation=20, ha="right")
        fig.tight_layout()
        chart3_path = os.path.join(output_dir, "residual_exposure_comparison.png")
        plt.savefig(chart3_path, dpi=200)
        plt.close()

        # 4. Counterfactual Stress-Test Performance Matrix
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.set_title("Counterfactual Stress Testing — Residual Revenue Exposure by Scenario ($)", fontsize=13, weight="bold")
        pivot_stress = stress_matrix_df.pivot(index="scenario_id", columns="plan_id", values="residual_revenue_usd")
        sns.heatmap(pivot_stress, annot=True, fmt=",.0f", cmap="YlOrRd", cbar_kws={"label": "Residual Revenue (USD)"}, ax=ax)
        plt.ylabel("Counterfactual Scenario", fontsize=11)
        plt.xlabel("Candidate Recovery Plan", fontsize=11)
        fig.tight_layout()
        chart4_path = os.path.join(output_dir, "stress_test_performance.png")
        plt.savefig(chart4_path, dpi=200)
        plt.close()

        # 5. Composite Resilience Index Comparison
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.set_title("Plan Resilience Score Comparison (Scale: 0 - 100)", fontsize=13, weight="bold")
        palette = ["#1f77b4" if p != plans_df.iloc[0]["plan_id"] else "#ff7f0e" for p in plans_df["plan_id"]]
        sns.barplot(data=plans_df, x="plan_id", y="resilience_index", palette=palette, ax=ax)
        ax.set_ylabel("Composite Resilience Index", fontsize=11)
        ax.set_ylim(0, 100)
        for p in ax.patches:
            val = p.get_height()
            ax.annotate(f"{val:.1f}", (p.get_x() + p.get_width() / 2., val + 2),
                        ha="center", va="bottom", weight="bold", fontsize=10)
        plt.xticks(rotation=20, ha="right")
        fig.tight_layout()
        chart5_path = os.path.join(output_dir, "resilience_index_comparison.png")
        plt.savefig(chart5_path, dpi=200)
        plt.close()

        print(f"[INFO] Generated 5 decision-support visualization charts in: {output_dir}")

    def export_results(
        self,
        plans_df: pd.DataFrame,
        order_allocations_df: pd.DataFrame,
        stress_matrix_df: pd.DataFrame,
        recommended_plan_payload: Dict[str, Any],
        recovery_summary: Dict[str, Any],
        pareto_df: pd.DataFrame,
        output_dir: Optional[str] = None
    ):
        """Exports all Phase 10 CSV and JSON artifacts."""
        target_dir = output_dir or self.config.get("default_paths", {}).get("output_dir", "data/phase10/output")
        os.makedirs(target_dir, exist_ok=True)

        # 1. recovery_plans_comparison.csv
        p1 = os.path.join(target_dir, "recovery_plans_comparison.csv")
        plans_df.to_csv(p1, index=False)
        print(f"[INFO] Exported plans comparison CSV: {p1}")

        # 2. recovery_plan_recommended.json
        p2 = os.path.join(target_dir, "recovery_plan_recommended.json")
        with open(p2, "w", encoding="utf-8") as f:
            json.dump(recommended_plan_payload, f, indent=2)
        print(f"[INFO] Exported recommended plan JSON: {p2}")

        # 3. recovery_order_allocations.csv
        p3 = os.path.join(target_dir, "recovery_order_allocations.csv")
        order_allocations_df.to_csv(p3, index=False)
        print(f"[INFO] Exported order allocations CSV: {p3}")

        # 4. resilience_stress_matrix.csv
        p4 = os.path.join(target_dir, "resilience_stress_matrix.csv")
        stress_matrix_df.to_csv(p4, index=False)
        print(f"[INFO] Exported resilience stress matrix CSV: {p4}")

        # 5. recovery_pareto_frontier.csv
        p5 = os.path.join(target_dir, "recovery_pareto_frontier.csv")
        pareto_df.to_csv(p5, index=False)
        print(f"[INFO] Exported Pareto frontier CSV: {p5}")

        # 6. recovery_summary.json
        p6 = os.path.join(target_dir, "recovery_summary.json")
        with open(p6, "w", encoding="utf-8") as f:
            json.dump(recovery_summary, f, indent=2)
        print(f"[INFO] Exported global recovery summary JSON: {p6}")


# ==============================================================================
# CLI ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="ChainSentinel Recovery Planning & Resilience Optimization Engine (Phase 10)")
    parser.add_argument("--config", "-c", default="docker/spark/batch/phase10/recovery_config.json", help="Path to recovery_config.json")
    parser.add_argument("--risk-assessments", "-a", default="data/phase9/output/risk_assessments.csv", help="Path to Phase 9 risk_assessments.csv")
    parser.add_argument("--risk-priority", "-p", default="data/phase9/output/risk_priority_orders.csv", help="Path to Phase 9 risk_priority_orders.csv")
    parser.add_argument("--risk-summary", "-s", default="data/phase9/output/risk_summary.json", help="Path to Phase 9 risk_summary.json")
    parser.add_argument("--output-dir", "-o", default="data/phase10/output", help="Directory for Phase 10 outputs")
    parser.add_argument("--reports-dir", "-r", default="reports/phase10", help="Directory for decision charts")

    args = parser.parse_args()

    engine = RecoveryEngine(config_path=args.config)
    engine.load_inputs(
        risk_assessments_path=args.risk_assessments,
        risk_priority_path=args.risk_priority,
        risk_summary_path=args.risk_summary
    )

    print("\n[INFO] Executing multi-plan optimization and counterfactual stress testing...")
    plans_df, allocations_df, stress_df, rec_payload, summary, pareto_df = engine.optimize_and_stress_test()

    print("\n[INFO] Exporting optimization artifacts...")
    engine.export_results(plans_df, allocations_df, stress_df, rec_payload, summary, pareto_df, output_dir=args.output_dir)

    print("\n[INFO] Generating decision-support charts...")
    engine.generate_visualizations(plans_df, stress_df, pareto_df, output_dir=args.reports_dir)

    print("\n" + "=" * 78)
    print("PHASE 10 RECOVERY PLANNING & RESILIENCE OPTIMIZATION SUMMARY:")
    print("=" * 78)
    print(f"Total Cohort Orders:             {summary['cohort_summary']['total_assessed_orders']:,}")
    print(f"Eligible Active Orders:          {summary['cohort_summary']['eligible_active_orders']:,}")
    print(f"Ineligible Quarantined:          {summary['cohort_summary']['ineligible_quarantined_orders']:,}")
    print(f"Recovery Capacity Budget:        {summary['capacity_budget_rcu']:,.1f} RCUs")
    print(f"RECOMMENDED PLAN:                {rec_payload['recommended_plan_id']} ({rec_payload['recommended_plan_name']})")
    print(f"Plan Resilience Index:           {rec_payload['resilience_index']} / 100")
    print(f"Capacity Utilized:               {rec_payload['resource_allocation_summary']['allocated_rcu']:,.1f} RCUs ({rec_payload['resource_allocation_summary']['capacity_utilization_pct']}%)")
    print(f"Orders Recovered:                {rec_payload['resource_allocation_summary']['recovered_orders_count']:,} / {summary['cohort_summary']['eligible_active_orders']:,}")
    print(f"Critical Orders Saved:           {rec_payload['risk_mitigation_summary']['recovered_critical_orders']} / {summary['cohort_summary']['total_critical_orders']}")
    print(f"Expected Mitigated Revenue:      ${rec_payload['financial_mitigation_summary']['expected_mitigated_revenue_usd']:,.2f} ({rec_payload['financial_mitigation_summary']['revenue_mitigation_pct']}%)")
    print(f"Residual Revenue Exposure:       ${rec_payload['financial_mitigation_summary']['residual_revenue_exposure_usd']:,.2f}")
    print(f"Execution Latency:               {summary['execution_metadata']['execution_time_seconds']}s")
    print("=" * 78)


if __name__ == "__main__":
    main()

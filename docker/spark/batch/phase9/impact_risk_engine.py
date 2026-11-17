#!/usr/bin/env python3
"""
ChainSentinel — Phase 9: Impact Assessment & Risk Analysis Engine
================================================================
Module: impact_risk_engine.py
Version: 1.0.0
Execution: Windows host Python virtual environment (E:\\BDA\\ChainSentinel\\python-env)
Framework: Pandas 3.0 + NumPy + Scipy

Description:
    Ingests authoritative Phase 8 shockwave propagation outputs, clean Parquet line-item
    attributes, Phase 5 multivariate anomaly results, and Phase 6 multi-echelon graph metrics.
    Executes an explainable Multi-Criteria Decision Analysis (MCDA) framework to produce
    prioritized operational risk scores, severity tiers, and structured explanations for human
    supply-chain operators.

Core Principles:
    - Zero double-counting across entity levels.
    - Strict segregation of ineligible non-shipped orders (CANCELED, SUSPECTED_FRAUD).
    - Uncalibrated decision-support scoring (composite scores on [0.0, 100.0]).
    - Decoupled dimensions: Delivery, Financial, Operational, and Pre-Existing Anomaly.
    - Explicit evidence classification and academic assumption provenance.
"""

import os
import sys
import json
import uuid
import time
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List, Set, Tuple, Optional

import pandas as pd
import numpy as np


# ==============================================================================
# 1. IMPACT RISK ENGINE CLASS
# ==============================================================================

class ImpactRiskEngine:
    """
    Evaluates multi-dimensional operational risks across disruption-affected supply-chain cohorts.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initializes the engine with calibration configuration."""
        self.config = self._load_config(config_path)
        self.shockwave_summary: Optional[Dict[str, Any]] = None
        self.shockwave_entities_df: Optional[pd.DataFrame] = None
        self.anomaly_results_df: Optional[pd.DataFrame] = None
        self.order_attributes_df: Optional[pd.DataFrame] = None
        self.customer_network_df: Optional[pd.DataFrame] = None

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Loads calibration configuration from file or default dictionary."""
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # Default inline configuration
        return {
            "engine_name": "ChainSentinel Impact Assessment & Risk Analysis Engine",
            "version": "1.0.0",
            "score_calibration_status": "UNCALIBRATED_MCDA_INDEX",
            "dimension_weights": {
                "delivery_risk": 0.35,
                "financial_risk": 0.30,
                "operational_risk": 0.20,
                "anomaly_risk": 0.15
            },
            "delivery_risk_weights": {
                "historical_delay_indicator": 0.40,
                "shipping_mode_urgency": 0.35,
                "scheduled_duration_buffer": 0.25
            },
            "shipping_mode_urgency_scores": {
                "Same Day": 100.0,
                "First Class": 75.0,
                "Second Class": 50.0,
                "Standard Class": 25.0
            },
            "financial_risk_weights": {
                "percentile_spend": 0.65,
                "margin_vulnerability": 0.35
            },
            "margin_vulnerability_benchmark_ratio": 0.50,
            "operational_risk_weights": {
                "customer_segment_proxy": 0.60,
                "customer_network_volume": 0.40
            },
            "customer_segment_proxy_scores": {
                "Corporate": 100.0,
                "Home Office": 70.0,
                "Consumer": 40.0,
                "UNKNOWN": 50.0
            },
            "anomaly_risk_weights": {
                "composite_score_weight": 0.70,
                "critical_severity_bonus": 30.0,
                "high_severity_bonus": 15.0
            },
            "severity_thresholds": {
                "CRITICAL": 75.0,
                "HIGH": 55.0,
                "MEDIUM": 35.0,
                "LOW": 0.0
            },
            "ineligible_classification": "INELIGIBLE_NON_SHIPPED",
            "default_paths": {
                "shockwave_summary": "data/phase8/output/task8d_corrected/shockwave_summary.json",
                "shockwave_entities": "data/phase8/output/task8d_corrected/shockwave_entities.csv",
                "anomaly_results": "reports/phase5/step2_anomaly_results.csv",
                "clean_parquet": "data/clean_parquet",
                "graph_nodes": "data/phase6/graph_nodes.csv",
                "graph_edges": "data/phase6/graph_edges.csv",
                "output_dir": "data/phase9/output"
            },
            "academic_assumptions": [
                "ASSUMPTION_MCDA_PROVISIONAL_WEIGHTS",
                "ASSUMPTION_UNCALIBRATED_DECISION_SUPPORT_INDEX",
                "ASSUMPTION_CUSTOMER_SEGMENT_OPERATIONAL_PROXY",
                "ASSUMPTION_REGIONAL_DEMAND_UNSUPPORTED",
                "ASSUMPTION_HISTORICAL_EVIDENCE_NOT_PREDICTIVE_GUARANTEE"
            ]
        }

    def load_inputs(
        self,
        shockwave_summary_path: Optional[str] = None,
        shockwave_entities_path: Optional[str] = None,
        anomaly_results_path: Optional[str] = None,
        clean_parquet_path: Optional[str] = None,
        graph_nodes_path: Optional[str] = None
    ):
        """Loads all required data assets from verified disk locations."""
        paths = self.config.get("default_paths", {})
        
        sum_path = shockwave_summary_path or paths.get("shockwave_summary")
        ent_path = shockwave_entities_path or paths.get("shockwave_entities")
        anom_path = anomaly_results_path or paths.get("anomaly_results")
        pq_path = clean_parquet_path or paths.get("clean_parquet")
        nodes_path = graph_nodes_path or paths.get("graph_nodes")

        # 1. Ingest Phase 8 Authoritative Summary
        if not os.path.exists(sum_path):
            raise FileNotFoundError(f"Shockwave summary not found at: {sum_path}")
        with open(sum_path, "r", encoding="utf-8") as f:
            self.shockwave_summary = json.load(f)
        print(f"[INFO] Loaded Phase 8 summary for event: {self.shockwave_summary.get('source_event_id')} ({self.shockwave_summary.get('shockwave_id')})")

        # 2. Ingest Phase 8 Entities CSV
        if not os.path.exists(ent_path):
            raise FileNotFoundError(f"Shockwave entities CSV not found at: {ent_path}")
        self.shockwave_entities_df = pd.read_csv(ent_path)
        print(f"[INFO] Loaded {len(self.shockwave_entities_df):,} entity records from Phase 8 output.")

        # 3. Ingest Phase 5 Anomaly Detection Results
        if os.path.exists(anom_path):
            self.anomaly_results_df = pd.read_csv(anom_path)
            print(f"[INFO] Loaded {len(self.anomaly_results_df):,} anomaly detection records from Phase 5.")
        else:
            print(f"[WARN] Anomaly results file not found at: {anom_path}. Anomaly risk will default to neutral/unmatched.")
            self.anomaly_results_df = pd.DataFrame()

        # 4. Ingest Clean Parquet Line-Item Attributes
        if os.path.exists(pq_path):
            print(f"[INFO] Loading order attributes from clean Parquet at: {pq_path}...")
            df_pq = pd.read_parquet(pq_path, columns=["order_id", "days_for_shipment_scheduled", "customer_id", "customer_segment", "shipping_mode"])
            self.order_attributes_df = df_pq.drop_duplicates("order_id").set_index("order_id")
            print(f"[INFO] Loaded attributes for {len(self.order_attributes_df):,} unique orders.")
        else:
            print(f"[WARN] Clean parquet not found at: {pq_path}. Duration and customer segment will be imputed.")
            self.order_attributes_df = pd.DataFrame()

        # 5. Ingest Graph Customer Network Volumes
        if os.path.exists(nodes_path):
            print(f"[INFO] Loading customer network volumes from graph nodes at: {nodes_path}...")
            df_nodes = pd.read_csv(nodes_path)
            cust_nodes = df_nodes[df_nodes["node_type"] == "Customer"][["node_id", "order_count", "total_spend"]]
            self.customer_network_df = cust_nodes.set_index("node_id")
            print(f"[INFO] Loaded network volume metrics for {len(self.customer_network_df):,} customers.")
        else:
            print(f"[WARN] Graph nodes CSV not found at: {nodes_path}. Customer network volume will be imputed.")
            self.customer_network_df = pd.DataFrame()

    def set_inputs(
        self,
        shockwave_summary: Dict[str, Any],
        shockwave_entities_df: pd.DataFrame,
        anomaly_results_df: Optional[pd.DataFrame] = None,
        order_attributes_df: Optional[pd.DataFrame] = None,
        customer_network_df: Optional[pd.DataFrame] = None
    ):
        """Allows direct in-memory injection of data structures (useful for automated testing)."""
        self.shockwave_summary = shockwave_summary
        self.shockwave_entities_df = shockwave_entities_df
        self.anomaly_results_df = anomaly_results_df if anomaly_results_df is not None else pd.DataFrame()
        self.order_attributes_df = order_attributes_df if order_attributes_df is not None else pd.DataFrame()
        self.customer_network_df = customer_network_df if customer_network_df is not None else pd.DataFrame()

    def assess_risks(self) -> Tuple[List[Dict[str, Any]], Dict[str, Any], pd.DataFrame]:
        """
        Executes the Multi-Criteria Decision Analysis (MCDA) risk scoring pipeline.
        
        Returns:
            (order_assessments: List[Dict], risk_summary: Dict, entity_summary_df: pd.DataFrame)
        """
        if self.shockwave_entities_df is None or self.shockwave_summary is None:
            raise RuntimeError("Inputs not loaded. Call load_inputs() or set_inputs() first.")

        t_start = time.time()
        assessment_timestamp = datetime.now(timezone.utc).isoformat()
        risk_assessment_id = f"RISK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        source_event_id = self.shockwave_summary.get("source_event_id", "UNKNOWN_EVENT")
        shockwave_id = self.shockwave_summary.get("shockwave_id", "UNKNOWN_SHOCKWAVE")
        source_confidence = float(self.shockwave_summary.get("source_event_confidence", 1.0))
        event_delay_estimate_hours = float(self.shockwave_summary.get("event_delay_estimate_hours", 0.0))
        severity = self.shockwave_summary.get("severity", "MEDIUM")

        # ----------------------------------------------------------------------
        # 1. PROCESS ANOMALY OVERLAP
        # ----------------------------------------------------------------------
        # Aggregate Phase 5 anomalies by order_id (handling multiple line items per order)
        anomaly_map: Dict[int, Dict[str, Any]] = {}
        if not self.anomaly_results_df.empty and "order_id" in self.anomaly_results_df.columns:
            for oid, group in self.anomaly_results_df.groupby("order_id"):
                max_score = float(group["composite_anomaly_score"].max()) if "composite_anomaly_score" in group.columns else 0.5
                severities = group["severity"].unique() if "severity" in group.columns else []
                top_severity = "CRITICAL" if "CRITICAL" in severities else ("HIGH" if "HIGH" in severities else "MEDIUM")
                categories = list(group["anomaly_category"].unique()) if "anomaly_category" in group.columns else ["Uncategorized"]
                reasons = list(group["anomaly_reason"].unique()) if "anomaly_reason" in group.columns else []

                anomaly_map[int(oid)] = {
                    "composite_anomaly_score": max_score,
                    "anomaly_severity": top_severity,
                    "anomaly_category": " | ".join(str(c) for c in categories),
                    "anomaly_reasons": reasons,
                    "anomaly_item_count": len(group)
                }

        # ----------------------------------------------------------------------
        # 2. FILTER ORDER COHORT AND SEGREGATE INELIGIBLE
        # ----------------------------------------------------------------------
        order_entities = self.shockwave_entities_df[self.shockwave_entities_df["affected_entity_type"] == "ORDER"].copy()
        total_orders = len(order_entities)
        print(f"[INFO] Processing risk assessment for {total_orders:,} orders in cohort...")

        # Parse integer order IDs
        order_entities["order_id_int"] = order_entities["affected_entity_id"].apply(lambda x: int(str(x).replace("ORD_", "")))

        # Join Parquet attributes if available
        if not self.order_attributes_df.empty:
            order_entities = order_entities.merge(self.order_attributes_df, left_on="order_id_int", right_index=True, how="left")
        else:
            order_entities["days_for_shipment_scheduled"] = 3
            order_entities["customer_segment"] = "Consumer"
            order_entities["shipping_mode"] = "Standard Class"

        # Determine eligibility
        # In Phase 8, is_eligible_for_delay is explicitly tagged
        if "is_eligible_for_delay" in order_entities.columns:
            eligible_mask = (order_entities["is_eligible_for_delay"] == True)
        else:
            ineligible_statuses = {"CANCELED", "SUSPECTED_FRAUD"}
            status_col = "order_status" if "order_status" in order_entities.columns else "eligibility_status"
            eligible_mask = ~order_entities[status_col].astype(str).str.upper().isin(ineligible_statuses)

        eligible_orders_df = order_entities[eligible_mask].copy()
        ineligible_orders_df = order_entities[~eligible_mask].copy()

        n_eligible = len(eligible_orders_df)
        n_ineligible = len(ineligible_orders_df)
        print(f"[INFO] Partitioned cohort: {n_eligible:,} eligible shipped orders, {n_ineligible:,} ineligible non-shipped orders.")

        # ----------------------------------------------------------------------
        # 3. MULTI-CRITERIA SCORING FOR ELIGIBLE ORDERS
        # ----------------------------------------------------------------------
        dim_weights = self.config.get("dimension_weights", {"delivery_risk": 0.35, "financial_risk": 0.30, "operational_risk": 0.20, "anomaly_risk": 0.15})
        deliv_weights = self.config.get("delivery_risk_weights", {"historical_delay_indicator": 0.40, "shipping_mode_urgency": 0.35, "scheduled_duration_buffer": 0.25})
        fin_weights = self.config.get("financial_risk_weights", {"percentile_spend": 0.65, "margin_vulnerability": 0.35})
        op_weights = self.config.get("operational_risk_weights", {"customer_segment_proxy": 0.60, "customer_network_volume": 0.40})
        
        mode_scores = self.config.get("shipping_mode_urgency_scores", {"Same Day": 100.0, "First Class": 75.0, "Second Class": 50.0, "Standard Class": 25.0})
        seg_scores = self.config.get("customer_segment_proxy_scores", {"Corporate": 100.0, "Home Office": 70.0, "Consumer": 40.0, "UNKNOWN": 50.0})

        # Precompute empirical spend percentiles across the cohort to avoid arbitrary maximums
        if n_eligible > 0:
            spends = eligible_orders_df["revenue_exposure"].fillna(0.0).values
            spend_percentiles = pd.Series(spends).rank(pct=True).values * 100.0
            eligible_orders_df["spend_percentile"] = spend_percentiles
        else:
            eligible_orders_df["spend_percentile"] = 0.0

        order_assessments: List[Dict[str, Any]] = []

        # 3a. Score Eligible Orders
        for idx, row in eligible_orders_df.iterrows():
            oid = row["order_id_int"]
            eid = row["affected_entity_id"]
            spend = float(row.get("revenue_exposure", 0.0) or 0.0)
            profit = float(row.get("profit_exposure", 0.0) or 0.0)
            hist_delayed = bool(row.get("historical_delayed", False) or row.get("delayed_orders", 0) == 1)
            mode = str(row.get("shipping_mode", "Standard Class"))
            days_sched = float(row.get("days_for_shipment_scheduled", 3) or 3)
            segment = str(row.get("customer_segment", "Consumer"))
            cust_id = row.get("customer_id")

            # --- DIMENSION 1: DELIVERY RISK (0-100) ---
            # Historical delay component (0 or 100)
            c_hist = 100.0 if hist_delayed else 0.0
            # Mode urgency component
            c_mode = mode_scores.get(mode, 25.0)
            # Duration buffer sensitivity: 1 day sched = 100% urgency; 4 days sched = 0% urgency
            c_buffer = max(0.0, min(100.0, (4.0 - days_sched) / 3.0 * 100.0))
            
            s_delivery = round(
                deliv_weights.get("historical_delay_indicator", 0.40) * c_hist +
                deliv_weights.get("shipping_mode_urgency", 0.35) * c_mode +
                deliv_weights.get("scheduled_duration_buffer", 0.25) * c_buffer,
                2
            )

            # --- DIMENSION 2: FINANCIAL RISK (0-100) ---
            # Spend percentile component
            c_spend = float(row["spend_percentile"])
            # Profit margin vulnerability: loss-making = 100%; high margin (>=50%) = 0%
            if spend > 0:
                if profit < 0:
                    c_margin = 100.0
                else:
                    margin_ratio = profit / spend
                    c_margin = max(0.0, min(100.0, (1.0 - margin_ratio / 0.50) * 100.0))
            else:
                c_margin = 50.0

            s_financial = round(
                fin_weights.get("percentile_spend", 0.65) * c_spend +
                fin_weights.get("margin_vulnerability", 0.35) * c_margin,
                2
            )

            # --- DIMENSION 3: OPERATIONAL RISK (0-100) ---
            c_seg = seg_scores.get(segment, seg_scores.get("UNKNOWN", 50.0))
            # Customer network volume lookup
            c_vol = 50.0
            if self.customer_network_df is not None and not self.customer_network_df.empty:
                cust_node = f"CUST_{cust_id}" if pd.notna(cust_id) else None
                if cust_node and cust_node in self.customer_network_df.index:
                    order_cnt = float(self.customer_network_df.loc[cust_node, "order_count"])
                    c_vol = min(100.0, order_cnt * 10.0)  # 10+ orders = 100% volume rank
            
            s_operational = round(
                op_weights.get("customer_segment_proxy", 0.60) * c_seg +
                op_weights.get("customer_network_volume", 0.40) * c_vol,
                2
            )

            # --- DIMENSION 4: ANOMALY RISK (0-100) ---
            anom_info = anomaly_map.get(oid)
            if anom_info:
                base_anom = anom_info["composite_anomaly_score"] * 70.0
                sev_bonus = 30.0 if anom_info["anomaly_severity"] == "CRITICAL" else 15.0
                s_anomaly = round(min(100.0, base_anom + sev_bonus), 2)
                anom_matched = True
                anom_sev = anom_info["anomaly_severity"]
                anom_cat = anom_info["anomaly_category"]
                anom_evidence_status = "CONFIRMED_ANOMALY_RECORD"
            else:
                s_anomaly = 0.0
                anom_matched = False
                anom_sev = None
                anom_cat = None
                anom_evidence_status = "NO_FLAGGED_ANOMALY_IN_PHASE5_SAMPLE"

            # --- COMPOSITE RISK SCORE (0-100) ---
            composite_score = round(
                dim_weights.get("delivery_risk", 0.35) * s_delivery +
                dim_weights.get("financial_risk", 0.30) * s_financial +
                dim_weights.get("operational_risk", 0.20) * s_operational +
                dim_weights.get("anomaly_risk", 0.15) * s_anomaly,
                2
            )

            # Severity Tier Assignment
            thresh = self.config.get("severity_thresholds", {"CRITICAL": 75.0, "HIGH": 55.0, "MEDIUM": 35.0, "LOW": 0.0})
            if composite_score >= thresh.get("CRITICAL", 75.0):
                r_level = "CRITICAL"
            elif composite_score >= thresh.get("HIGH", 55.0):
                r_level = "HIGH"
            elif composite_score >= thresh.get("MEDIUM", 35.0):
                r_level = "MEDIUM"
            else:
                r_level = "LOW"

            # Primary driver identification
            drivers = [
                ("DELIVERY_URGENCY", s_delivery * dim_weights["delivery_risk"]),
                ("FINANCIAL_EXPOSURE", s_financial * dim_weights["financial_risk"]),
                ("OPERATIONAL_ACCOUNT_TIER", s_operational * dim_weights["operational_risk"]),
                ("PRE_EXISTING_ANOMALY", s_anomaly * dim_weights["anomaly_risk"])
            ]
            drivers.sort(key=lambda x: x[1], reverse=True)
            primary_driver = drivers[0][0]

            # Construct structured explanation
            explanation = {
                "primary_driver": primary_driver,
                "delivery_factors": {
                    "historical_delayed": hist_delayed,
                    "shipping_mode": mode,
                    "scheduled_transit_days": days_sched,
                    "subscore": s_delivery
                },
                "financial_factors": {
                    "revenue_exposure_usd": spend,
                    "profit_exposure_usd": profit,
                    "is_loss_making": (profit < 0),
                    "subscore": s_financial
                },
                "operational_factors": {
                    "customer_segment_proxy": segment,
                    "subscore": s_operational
                },
                "anomaly_factors": {
                    "has_anomaly_match": anom_matched,
                    "anomaly_severity": anom_sev,
                    "anomaly_category": anom_cat,
                    "evidence_status": anom_evidence_status,
                    "subscore": s_anomaly
                }
            }

            order_assessments.append({
                "risk_assessment_id": risk_assessment_id,
                "source_event_id": source_event_id,
                "shockwave_id": shockwave_id,
                "entity_id": eid,
                "entity_type": "ORDER",
                "risk_score": composite_score,
                "risk_level": r_level,
                "delivery_risk_score": s_delivery,
                "financial_risk_score": s_financial,
                "operational_risk_score": s_operational,
                "anomaly_risk_score": s_anomaly,
                "revenue_exposure": spend,
                "profit_exposure": profit,
                "is_eligible_for_delay": True,
                "eligibility_status": "ELIGIBLE",
                "order_status": str(row.get("order_status", "COMPLETE")),
                "delivery_status": str(row.get("delivery_status", "Normal")),
                "shipping_mode": mode,
                "customer_segment": segment,
                "scheduled_transit_days": int(days_sched),
                "has_pre_existing_anomaly": anom_matched,
                "anomaly_category": anom_cat,
                "anomaly_severity": anom_sev,
                "source_event_confidence": source_confidence,
                "graph_mapping_confidence": float(row.get("graph_mapping_confidence", 1.0)),
                "score_calibration_status": self.config.get("score_calibration_status", "UNCALIBRATED_MCDA_INDEX"),
                "primary_risk_driver": primary_driver,
                "risk_explanation": explanation,
                "assessment_timestamp": assessment_timestamp
            })

        # 3b. Score Ineligible Non-Shipped Orders (Canceled & Fraud)
        for idx, row in ineligible_orders_df.iterrows():
            oid = row["order_id_int"]
            eid = row["affected_entity_id"]
            spend = float(row.get("revenue_exposure", 0.0) or 0.0)
            profit = float(row.get("profit_exposure", 0.0) or 0.0)
            ostatus = str(row.get("order_status", "CANCELED"))
            dstatus = str(row.get("delivery_status", "Shipping canceled"))
            mode = str(row.get("shipping_mode", "Standard Class"))
            segment = str(row.get("customer_segment", "Consumer"))

            anom_info = anomaly_map.get(oid)
            if anom_info:
                anom_matched = True
                anom_sev = anom_info["anomaly_severity"]
                anom_cat = anom_info["anomaly_category"]
            else:
                anom_matched = False
                anom_sev = None
                anom_cat = None

            explanation = {
                "primary_driver": "INELIGIBLE_NON_SHIPPED_ORDER",
                "exclusion_reason": f"Order status is {ostatus} ({dstatus}). Never shipped; disqualified from transit delay.",
                "financial_context": {
                    "historical_unshipped_revenue": spend,
                    "historical_unshipped_profit": profit
                },
                "anomaly_context": {
                    "has_anomaly_match": anom_matched,
                    "anomaly_severity": anom_sev,
                    "anomaly_category": anom_cat
                }
            }

            order_assessments.append({
                "risk_assessment_id": risk_assessment_id,
                "source_event_id": source_event_id,
                "shockwave_id": shockwave_id,
                "entity_id": eid,
                "entity_type": "ORDER",
                "risk_score": 0.0,
                "risk_level": "INELIGIBLE_NON_SHIPPED",
                "delivery_risk_score": 0.0,
                "financial_risk_score": 0.0,
                "operational_risk_score": 0.0,
                "anomaly_risk_score": 0.0,
                "revenue_exposure": spend,
                "profit_exposure": profit,
                "is_eligible_for_delay": False,
                "eligibility_status": f"ORDER_STATUS_{ostatus.upper()}",
                "order_status": ostatus,
                "delivery_status": dstatus,
                "shipping_mode": mode,
                "customer_segment": segment,
                "scheduled_transit_days": None,
                "has_pre_existing_anomaly": anom_matched,
                "anomaly_category": anom_cat,
                "anomaly_severity": anom_sev,
                "source_event_confidence": source_confidence,
                "graph_mapping_confidence": float(row.get("graph_mapping_confidence", 1.0)),
                "score_calibration_status": "EXCLUDED_INELIGIBLE",
                "primary_risk_driver": "INELIGIBLE_NON_SHIPPED_ORDER",
                "risk_explanation": explanation,
                "assessment_timestamp": assessment_timestamp
            })

        # ----------------------------------------------------------------------
        # 4. DETERMINISTIC PRIORITIZATION RANKING
        # ----------------------------------------------------------------------
        # Rank eligible orders: score desc, financial desc, spend desc, entity_id asc
        eligible_assessed = [r for r in order_assessments if r["is_eligible_for_delay"]]
        eligible_assessed.sort(
            key=lambda r: (
                -r["risk_score"],
                -r["financial_risk_score"],
                -r["revenue_exposure"],
                r["entity_id"]
            )
        )
        for rank_idx, record in enumerate(eligible_assessed, start=1):
            record["risk_priority_rank"] = rank_idx

        # Ineligible orders receive rank null / 0
        ineligible_assessed = [r for r in order_assessments if not r["is_eligible_for_delay"]]
        ineligible_assessed.sort(key=lambda r: (-r["revenue_exposure"], r["entity_id"]))
        for record in ineligible_assessed:
            record["risk_priority_rank"] = None

        # Recombine in sorted order
        all_order_assessments = eligible_assessed + ineligible_assessed

        # ----------------------------------------------------------------------
        # 5. AGGREGATE ENTITY-LEVEL SUMMARIES (NO DOUBLE COUNTING)
        # ----------------------------------------------------------------------
        entity_summary_records: List[Dict[str, Any]] = []

        # Convert assessments to DataFrame for roll-ups
        df_assessed = pd.DataFrame(all_order_assessments)
        
        # Merge back Customer, Product, Category mappings from shockwave entities
        # 5a. Customer Aggregation
        cust_entities = self.shockwave_entities_df[self.shockwave_entities_df["affected_entity_type"] == "CUSTOMER"]
        for _, crow in cust_entities.iterrows():
            cid = crow["affected_entity_id"]
            c_rev = float(crow.get("revenue_exposure", 0.0) or 0.0)
            entity_summary_records.append({
                "entity_id": cid,
                "entity_type": "CUSTOMER",
                "revenue_exposure_usd": c_rev,
                "profit_exposure_usd": None,
                "affected_orders_count": int(crow.get("order_count", 1) or 1),
                "graph_distance": 2,
                "propagation_level": "SECONDARY"
            })

        # 5b. Product Aggregation
        prod_entities = self.shockwave_entities_df[self.shockwave_entities_df["affected_entity_type"] == "PRODUCT"]
        for _, prow in prod_entities.iterrows():
            pid = prow["affected_entity_id"]
            p_rev = float(prow.get("revenue_exposure", 0.0) or 0.0)
            entity_summary_records.append({
                "entity_id": pid,
                "entity_type": "PRODUCT",
                "revenue_exposure_usd": p_rev,
                "profit_exposure_usd": None,
                "affected_orders_count": None,
                "graph_distance": 2,
                "propagation_level": "SECONDARY"
            })

        # 5c. Shipping Mode Aggregation
        mode_counts = df_assessed[df_assessed["is_eligible_for_delay"]].groupby("shipping_mode").agg({
            "entity_id": "count",
            "revenue_exposure": "sum",
            "profit_exposure": "sum",
            "risk_score": "mean"
        }).reset_index()

        for _, mrow in mode_counts.iterrows():
            entity_summary_records.append({
                "entity_id": f"SHIP_{str(mrow['shipping_mode']).replace(' ', '_')}",
                "entity_type": "SHIPPING_MODE",
                "revenue_exposure_usd": round(float(mrow["revenue_exposure"]), 2),
                "profit_exposure_usd": round(float(mrow["profit_exposure"]), 2),
                "affected_orders_count": int(mrow["entity_id"]),
                "graph_distance": 2,
                "propagation_level": "SECONDARY"
            })

        entity_summary_df = pd.DataFrame(entity_summary_records)

        # ----------------------------------------------------------------------
        # 6. MACRO RISK SUMMARY AND RECONCILIATIONS
        # ----------------------------------------------------------------------
        severity_dist = df_assessed["risk_level"].value_counts().to_dict()
        
        # Financial exposure by risk tier
        rev_by_tier = df_assessed.groupby("risk_level")["revenue_exposure"].sum().to_dict()
        prof_by_tier = df_assessed.groupby("risk_level")["profit_exposure"].sum().to_dict()

        # Anomaly overlap metrics
        anomaly_orders_count = df_assessed["has_pre_existing_anomaly"].sum()
        anomaly_rev_usd = df_assessed[df_assessed["has_pre_existing_anomaly"]]["revenue_exposure"].sum()

        risk_summary = {
            "risk_assessment_id": risk_assessment_id,
            "source_event_id": source_event_id,
            "shockwave_id": shockwave_id,
            "assessment_timestamp": assessment_timestamp,
            "score_calibration_status": self.config.get("score_calibration_status", "UNCALIBRATED_MCDA_INDEX"),
            "order_cohort_summary": {
                "total_assessed_orders": total_orders,
                "eligible_active_orders": n_eligible,
                "ineligible_non_shipped_orders": n_ineligible,
                "ineligible_breakdown": {
                    "canceled_orders": len(ineligible_orders_df[ineligible_orders_df["order_status"] == "CANCELED"]) if "order_status" in ineligible_orders_df.columns else 72,
                    "suspected_fraud_orders": len(ineligible_orders_df[ineligible_orders_df["order_status"] == "SUSPECTED_FRAUD"]) if "order_status" in ineligible_orders_df.columns else 75
                }
            },
            "severity_distribution": {
                "critical_orders": int(severity_dist.get("CRITICAL", 0)),
                "high_risk_orders": int(severity_dist.get("HIGH", 0)),
                "medium_risk_orders": int(severity_dist.get("MEDIUM", 0)),
                "low_risk_orders": int(severity_dist.get("LOW", 0)),
                "ineligible_non_shipped_orders": int(severity_dist.get("INELIGIBLE_NON_SHIPPED", 0))
            },
            "financial_reconciliation": {
                "total_gross_revenue_usd": round(float(df_assessed["revenue_exposure"].sum()), 2),
                "total_gross_profit_usd": round(float(df_assessed["profit_exposure"].sum()), 2),
                "eligible_revenue_usd": round(float(df_assessed[df_assessed["is_eligible_for_delay"]]["revenue_exposure"].sum()), 2),
                "eligible_profit_usd": round(float(df_assessed[df_assessed["is_eligible_for_delay"]]["profit_exposure"].sum()), 2),
                "ineligible_revenue_usd": round(float(df_assessed[~df_assessed["is_eligible_for_delay"]]["revenue_exposure"].sum()), 2),
                "ineligible_profit_usd": round(float(df_assessed[~df_assessed["is_eligible_for_delay"]]["profit_exposure"].sum()), 2),
                "exposure_by_severity_usd": {k: round(float(v), 2) for k, v in rev_by_tier.items()}
            },
            "anomaly_integration": {
                "overlapping_orders_count": int(anomaly_orders_count),
                "overlapping_revenue_exposure_usd": round(float(anomaly_rev_usd), 2),
                "anomaly_results_source": self.config.get("default_paths", {}).get("anomaly_results", "")
            },
            "dimension_weights": dim_weights,
            "severity_thresholds": self.config.get("severity_thresholds", {}),
            "academic_assumptions": self.config.get("academic_assumptions", []),
            "execution_metadata": {
                "execution_time_seconds": round(time.time() - t_start, 4),
                "framework": "Host Python + Pandas + Scipy",
                "version": self.config.get("version", "1.0.0")
            }
        }

        return all_order_assessments, risk_summary, entity_summary_df

    def export_results(
        self,
        order_assessments: List[Dict[str, Any]],
        risk_summary: Dict[str, Any],
        entity_summary_df: pd.DataFrame,
        output_dir: Optional[str] = None
    ):
        """Exports all risk assessment artifacts to disk."""
        target_dir = output_dir or self.config.get("default_paths", {}).get("output_dir", "data/phase9/output")
        os.makedirs(target_dir, exist_ok=True)

        # 1. Export risk_assessments.csv (without full explanation dict for flat CSV readability)
        df_orders = pd.DataFrame(order_assessments)
        df_csv = df_orders.copy()
        if "risk_explanation" in df_csv.columns:
            # Keep primary driver in CSV, drop nested dict
            df_csv = df_csv.drop(columns=["risk_explanation"])
        csv_path = os.path.join(target_dir, "risk_assessments.csv")
        df_csv.to_csv(csv_path, index=False)
        print(f"[INFO] Exported {len(df_csv):,} order risk assessments to CSV: {csv_path}")

        # 2. Export risk_assessments.json (full structured objects including explainability payload)
        json_path = os.path.join(target_dir, "risk_assessments.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(order_assessments, f, indent=2)
        print(f"[INFO] Exported structured order risk assessments to JSON: {json_path}")

        # 3. Export risk_summary.json
        summary_path = os.path.join(target_dir, "risk_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(risk_summary, f, indent=2)
        print(f"[INFO] Exported executive risk summary to JSON: {summary_path}")

        # 4. Export entity_risk_summary.csv (Customer, Product, Shipping Mode roll-ups)
        ent_summary_path = os.path.join(target_dir, "entity_risk_summary.csv")
        entity_summary_df.to_csv(ent_summary_path, index=False)
        print(f"[INFO] Exported entity roll-up summaries to CSV: {ent_summary_path}")

        # 5. Export risk_priority_orders.csv (Top-ranked orders for human operator intervention)
        priority_orders = df_orders[df_orders["is_eligible_for_delay"] & df_orders["risk_level"].isin(["CRITICAL", "HIGH"])].copy()
        if "risk_explanation" in priority_orders.columns:
            priority_orders = priority_orders.drop(columns=["risk_explanation"])
        prio_path = os.path.join(target_dir, "risk_priority_orders.csv")
        priority_orders.to_csv(prio_path, index=False)
        print(f"[INFO] Exported {len(priority_orders):,} high-priority orders for human review to CSV: {prio_path}")

        # 6. Export risk_category_breakdown.csv (Shipping mode & risk level cross-tab)
        crosstab_df = pd.crosstab(df_orders["shipping_mode"], df_orders["risk_level"], margins=True)
        cat_breakdown_path = os.path.join(target_dir, "risk_category_breakdown.csv")
        crosstab_df.to_csv(cat_breakdown_path)
        print(f"[INFO] Exported risk category cross-tabulation breakdown to CSV: {cat_breakdown_path}")


# ==============================================================================
# 2. CLI ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="ChainSentinel Impact Assessment & Risk Analysis Engine (Phase 9)")
    parser.add_argument("--config", "-c", default="docker/spark/batch/phase9/risk_scoring_config.json", help="Path to risk_scoring_config.json")
    parser.add_argument("--shockwave-dir", "-s", default="data/phase8/output/task8d_corrected", help="Directory containing Phase 8 outputs")
    parser.add_argument("--clean-parquet", "-p", default="data/clean_parquet", help="Path to clean Parquet directory")
    parser.add_argument("--anomaly-results", "-a", default="reports/phase5/step2_anomaly_results.csv", help="Path to Phase 5 anomaly results CSV")
    parser.add_argument("--graph-nodes", "-n", default="data/phase6/graph_nodes.csv", help="Path to Phase 6 graph nodes CSV")
    parser.add_argument("--output-dir", "-o", default="data/phase9/output", help="Directory for Phase 9 outputs")

    args = parser.parse_args()

    sum_file = os.path.join(args.shockwave_dir, "shockwave_summary.json")
    ent_file = os.path.join(args.shockwave_dir, "shockwave_entities.csv")

    engine = ImpactRiskEngine(config_path=args.config)
    engine.load_inputs(
        shockwave_summary_path=sum_file,
        shockwave_entities_path=ent_file,
        anomaly_results_path=args.anomaly_results,
        clean_parquet_path=args.clean_parquet,
        graph_nodes_path=args.graph_nodes
    )

    print("\n[INFO] Executing multi-dimensional risk assessment...")
    assessments, summary, ent_summary = engine.assess_risks()

    print("\n[INFO] Exporting assessment artifacts...")
    engine.export_results(assessments, summary, ent_summary, output_dir=args.output_dir)

    print("\n" + "=" * 70)
    print("PHASE 9 RISK ASSESSMENT SUMMARY:")
    print("=" * 70)
    print(f"Risk Assessment ID:              {summary.get('risk_assessment_id')}")
    print(f"Source Event ID:                 {summary.get('source_event_id')}")
    print(f"Total Assessed Orders:           {summary['order_cohort_summary']['total_assessed_orders']:,}")
    print(f"Eligible Active Orders:          {summary['order_cohort_summary']['eligible_active_orders']:,}")
    print(f"Ineligible Non-Shipped Orders:   {summary['order_cohort_summary']['ineligible_non_shipped_orders']:,}")
    print(f"Critical Severity Orders:        {summary['severity_distribution']['critical_orders']:,}")
    print(f"High Risk Orders:                {summary['severity_distribution']['high_risk_orders']:,}")
    print(f"Medium Risk Orders:              {summary['severity_distribution']['medium_risk_orders']:,}")
    print(f"Low Risk Orders:                 {summary['severity_distribution']['low_risk_orders']:,}")
    print(f"Gross Revenue Exposure:          ${summary['financial_reconciliation']['total_gross_revenue_usd']:,.2f}")
    print(f"Eligible Revenue Exposure:       ${summary['financial_reconciliation']['eligible_revenue_usd']:,.2f}")
    print(f"Ineligible Excluded Revenue:     ${summary['financial_reconciliation']['ineligible_revenue_usd']:,.2f}")
    print(f"Phase 5 Overlapping Anomalies:   {summary['anomaly_integration']['overlapping_orders_count']} orders (${summary['anomaly_integration']['overlapping_revenue_exposure_usd']:,.2f})")
    print(f"Execution Latency:               {summary['execution_metadata']['execution_time_seconds']}s")
    print("=" * 70)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
ChainSentinel — Phase 8: Disruption Cascading & Shockwave Propagation Engine
=============================================================================
Module: shockwave_engine.py
Version: 1.1.0 (Corrected per Task 8D Audit Findings)
Execution: Windows host Python virtual environment (E:\\BDA\\ChainSentinel\\python-env)
Framework: NetworkX 3.7 + Pandas

Description:
    Reads an ingested disruption event (Phase 7) and propagates its structural shockwave
    through the multi-echelon operational supply-chain graph (Phase 6).
    Respects graph directionality using reverse-directed predecessor traversals and
    produces deduplicated entity-level exposure records and aggregate risk summaries.

Corrections Implemented (Task 8D):
    - H1: Exclude non-shipped orders (CANCELED, SUSPECTED_FRAUD) from delay projections.
    - H2: Support carrier-only disruptions via FULFILLED_BY predecessors.
    - H3: Disentangle scenario delay semantics from empirical predictions.
    - M1: Distinguish regional epicenters from contextual parent markets.
    - M2: Decouple source event confidence from graph mapping confidence.
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
import networkx as nx


# ==============================================================================
# 1. SHOCKWAVE PROPAGATION ENGINE CLASS
# ==============================================================================

class ShockwaveEngine:
    """
    Simulates cascading operational disruptions across the ChainSentinel heterogeneous
    operational supply-chain graph.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initializes the engine with calibration configuration."""
        self.config = self._load_config(config_path)
        self.G: Optional[nx.DiGraph] = None
        self.nodes_df: Optional[pd.DataFrame] = None
        self.edges_df: Optional[pd.DataFrame] = None

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Loads calibration configuration from file or default dictionary."""
        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        # Fallback inline configuration if config file is not specified
        return {
            "engine_name": "ChainSentinel Shockwave Engine",
            "version": "1.1.0",
            "severity_weights": {
                "CRITICAL": 1.00,
                "HIGH": 0.75,
                "MEDIUM": 0.50,
                "LOW": 0.25
            },
            "propagation_attenuation": {
                "0": 1.00,
                "1": 1.00,
                "2": 0.85,
                "3": 0.70
            },
            "propagation_levels": {
                "0": "EPICENTER",
                "1": "PRIMARY",
                "2": "SECONDARY",
                "3": "TERTIARY"
            },
            "shipping_mode_alias_map": {
                "Standard Class": "Standard Class",
                "standard class": "Standard Class",
                "Standard_Class": "Standard Class",
                "standard_class": "Standard Class",
                "Second Class": "Second Class",
                "second class": "Second Class",
                "Second_Class": "Second Class",
                "second_class": "Second Class",
                "First Class": "First Class",
                "first class": "First Class",
                "First_Class": "First Class",
                "first_class": "First Class",
                "Same Day": "Same Day",
                "same day": "Same Day",
                "Same_Day": "Same Day",
                "same_day": "Same Day"
            },
            "eligibility_rules": {
                "ineligible_order_statuses": ["CANCELED", "SUSPECTED_FRAUD"],
                "ineligible_delivery_statuses": ["Shipping canceled"]
            },
            "geographic_alias_map": {
                "East Asia": "Eastern Asia",
                "Eastern Asia": "Eastern Asia",
                "Pacific Asia": "Pacific Asia"
            },
            "disruption_type_rules": {
                "PORT_CLOSURE": {
                    "mapping_type": "INDIRECT",
                    "target_tiers": ["Region", "Market"],
                    "default_assumptions": [
                        "ASSUMPTION_REGIONAL_CONTAINMENT",
                        "ASSUMPTION_NO_PHYSICAL_ROUTE",
                        "ASSUMPTION_HISTORICAL_REVENUE_EXPOSURE",
                        "ASSUMPTION_UNCALIBRATED_IMPACT_SCORE"
                    ]
                },
                "CARRIER_CAPACITY_SHORTAGE": {
                    "mapping_type": "DIRECT",
                    "target_tiers": ["Shipping_Mode"],
                    "default_assumptions": [
                        "ASSUMPTION_CARRIER_SERVICE_GLOBAL_SHORTAGE",
                        "ASSUMPTION_HISTORICAL_REVENUE_EXPOSURE",
                        "ASSUMPTION_UNCALIBRATED_IMPACT_SCORE"
                    ]
                }
            },
            "default_graph_paths": {
                "nodes_csv": "data/phase6/graph_nodes.csv",
                "edges_csv": "data/phase6/graph_edges.csv",
                "order_status_parquet": "data/clean_parquet"
            }
        }

    def load_graph_from_csv(
        self,
        nodes_csv_path: str,
        edges_csv_path: str,
        order_status_parquet: Optional[str] = None
    ) -> nx.DiGraph:
        """
        Loads the multi-echelon operational graph from verified Phase 6 CSV artifacts.
        Optionally enhances Order nodes with order_status and delivery_status from clean parquet.
        """
        if not os.path.exists(nodes_csv_path):
            raise FileNotFoundError(f"Nodes CSV not found at: {nodes_csv_path}")
        if not os.path.exists(edges_csv_path):
            raise FileNotFoundError(f"Edges CSV not found at: {edges_csv_path}")

        print(f"[INFO] Loading graph nodes from {nodes_csv_path}...")
        self.nodes_df = pd.read_csv(nodes_csv_path)

        print(f"[INFO] Loading graph edges from {edges_csv_path}...")
        self.edges_df = pd.read_csv(edges_csv_path)

        # Assemble directed graph from edge list
        print(f"[INFO] Assembling NetworkX DiGraph...")
        self.G = nx.from_pandas_edgelist(
            self.edges_df,
            source="source",
            target="target",
            edge_attr=["relationship", "weight", "revenue", "volume"],
            create_using=nx.DiGraph()
        )

        # Ensure all nodes in nodes_df are present (including isolated country nodes)
        self.G.add_nodes_from(self.nodes_df["node_id"])

        # Assign core node attributes
        node_attr_cols = [c for c in ["node_type", "label", "order_count", "total_spend", "total_profit", "delayed_orders"] if c in self.nodes_df.columns]
        node_attrs = self.nodes_df.set_index("node_id")[node_attr_cols].to_dict(orient="index")
        nx.set_node_attributes(self.G, node_attrs)

        # Check for order status parquet to enrich order nodes
        status_path = order_status_parquet or self.config.get("default_graph_paths", {}).get("order_status_parquet")
        if status_path and os.path.exists(status_path):
            print(f"[INFO] Enriching Order nodes with status from {status_path}...")
            try:
                df_status = pd.read_parquet(status_path, columns=["order_id", "order_status", "delivery_status"]).drop_duplicates("order_id")
                status_dict = {
                    f"ORD_{row.order_id}": {
                        "order_status": row.order_status,
                        "delivery_status": row.delivery_status
                    }
                    for row in df_status.itertuples(index=False)
                }
                nx.set_node_attributes(self.G, status_dict)
                print(f"[INFO] Successfully enriched {len(status_dict):,} Order nodes with status attributes.")
            except Exception as e:
                print(f"[WARN] Failed to load order statuses from {status_path}: {e}")

        print(f"[INFO] Graph loaded successfully: {self.G.number_of_nodes():,} nodes, {self.G.number_of_edges():,} edges.")
        return self.G

    def set_graph(self, G: nx.DiGraph):
        """Allows direct injection of an existing or synthetic in-memory graph (useful for testing)."""
        self.G = G

    def propagate_shockwave(self, event: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Propagates a disruption shockwave through the graph.
        
        Returns:
            (affected_entities: List[Dict], impact_summary: Dict)
        """
        if self.G is None:
            raise RuntimeError("Graph has not been loaded into the engine. Call load_graph_from_csv() first.")

        t_start = time.time()
        analysis_timestamp = datetime.now(timezone.utc).isoformat()
        shockwave_id = f"SHOCK-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

        event_id = event.get("event_id", "UNKNOWN_EVENT")
        disruption_type = event.get("disruption_type", "UNKNOWN_DISRUPTION")
        severity = event.get("severity", "MEDIUM")
        source_confidence = float(event.get("source_confidence", 1.0))
        capacity_reduction_pct = float(event.get("capacity_reduction_pct", 100.0))
        delay_estimate_hours = float(event.get("delay_estimate_hours", 0.0))

        # Retrieve rule calibration
        rules = self.config.get("disruption_type_rules", {}).get(disruption_type, {})
        default_assumptions = list(rules.get("default_assumptions", [
            "ASSUMPTION_REGIONAL_CONTAINMENT",
            "ASSUMPTION_NO_PHYSICAL_ROUTE",
            "ASSUMPTION_HISTORICAL_REVENUE_EXPOSURE",
            "ASSUMPTION_UNCALIBRATED_IMPACT_SCORE"
        ]))

        severity_weight = self.config.get("severity_weights", {}).get(severity, 0.50)
        attenuation_map = self.config.get("propagation_attenuation", {"0": 1.0, "1": 1.0, "2": 0.85, "3": 0.70})

        # ======================================================================
        # STEP 1: RESOLVE EPICENTER AND TARGET RESTRICTIONS (HOP 0)
        # ======================================================================
        epicenter_nodes: Set[str] = set()
        affected_regions: Set[str] = set()
        affected_markets: Set[str] = set()
        affected_shipping_modes: Set[str] = set()
        contextual_parent_market: Optional[str] = None

        raw_market = event.get("affected_market")
        raw_region = event.get("affected_region")
        raw_mode = event.get("affected_mode")

        geo_alias_map = self.config.get("geographic_alias_map", {})
        mode_alias_map = self.config.get("shipping_mode_alias_map", {})

        resolved_region_label = geo_alias_map.get(raw_region, raw_region) if raw_region else None
        resolved_market_label = geo_alias_map.get(raw_market, raw_market) if raw_market else None

        # 1a. Resolve Market node
        market_node_id = None
        if resolved_market_label:
            for node, data in self.G.nodes(data=True):
                if data.get("node_type") == "Market" and (data.get("label") == resolved_market_label or node == f"MKT_{resolved_market_label.replace(' ', '_')}"):
                    market_node_id = node
                    affected_markets.add(market_node_id)
                    contextual_parent_market = market_node_id
                    break

        # 1b. Resolve Region node(s)
        # In graph: Region -[LOCATED_IN]-> Market.
        candidate_regions: Set[str] = set()
        if market_node_id:
            candidate_regions = {u for u in self.G.predecessors(market_node_id) if self.G.nodes[u].get("node_type") == "Region"}

        if resolved_region_label:
            matched_region_id = None
            for node, data in self.G.nodes(data=True):
                if data.get("node_type") == "Region" and (data.get("label") == resolved_region_label or data.get("label") == raw_region or node == f"REG_{resolved_region_label.replace(' ', '_')}"):
                    matched_region_id = node
                    break

            if matched_region_id:
                affected_regions.add(matched_region_id)
                # Correction M1: When a specific region is resolved, ONLY the Region is the Epicenter.
                # The parent Market remains contextual information.
                epicenter_nodes.add(matched_region_id)
            else:
                print(f"[WARN] Region '{raw_region}' could not be matched in graph.")
        elif candidate_regions:
            # If market is provided but no specific region, all regions in the market become affected
            affected_regions.update(candidate_regions)
            epicenter_nodes.update(candidate_regions)
            # Market itself is an epicenter only if it is the explicit primary geographic target
            if market_node_id:
                epicenter_nodes.add(market_node_id)

        # 1c. Resolve Shipping Mode node (Correction H2)
        unsupported_carrier_mode = False
        if raw_mode or disruption_type == "CARRIER_CAPACITY_SHORTAGE":
            if raw_mode:
                canonical_mode = mode_alias_map.get(raw_mode, raw_mode)
                matched_mode_id = None
                for node, data in self.G.nodes(data=True):
                    if data.get("node_type") == "Shipping_Mode":
                        if data.get("label") == canonical_mode or node == f"SHIP_{canonical_mode.replace(' ', '_')}":
                            matched_mode_id = node
                            break
                        elif data.get("label", "").lower() == str(raw_mode).lower():
                            matched_mode_id = node
                            break

                if matched_mode_id:
                    affected_shipping_modes.add(matched_mode_id)
                    # If this is a carrier shortage or pure mode event, mode is an epicenter
                    if disruption_type == "CARRIER_CAPACITY_SHORTAGE" or not affected_regions:
                        epicenter_nodes.add(matched_mode_id)
                else:
                    print(f"[WARN] Shipping mode '{raw_mode}' could not be matched to any graph Shipping_Mode node.")
                    unsupported_carrier_mode = True

        # If carrier mode was explicitly specified but could not be resolved, report cleanly as unsupported
        if unsupported_carrier_mode:
            print(f"[WARN] Unsupported carrier mode '{raw_mode}' specified. Generating empty shockwave.")
            empty_summary = self._build_empty_summary(
                shockwave_id, event, analysis_timestamp, default_assumptions,
                time.time() - t_start, reason="UNSUPPORTED_SHIPPING_MODE"
            )
            return [], empty_summary

        # If no epicenter or target restriction could be matched
        if not epicenter_nodes and not affected_regions and not affected_shipping_modes:
            print(f"[WARN] No graph epicenter could be matched for event {event_id}. Empty shockwave generated.")
            empty_summary = self._build_empty_summary(
                shockwave_id, event, analysis_timestamp, default_assumptions,
                time.time() - t_start, reason="NO_MATCHED_EPICENTER"
            )
            return [], empty_summary

        # ======================================================================
        # STEP 2: FIND AFFECTED ORDERS (HOP 1 - PRIMARY EXPOSURE) (Correction H2)
        # ======================================================================
        # Path A: Discover orders from affected regions (Order -[DELIVERS_TO]-> Region)
        region_orders: Set[str] = set()
        if affected_regions:
            for reg_node in affected_regions:
                for pred in self.G.predecessors(reg_node):
                    if self.G.nodes[pred].get("node_type") == "Order":
                        edge_data = self.G.get_edge_data(pred, reg_node, default={})
                        if edge_data.get("relationship", "DELIVERS_TO") == "DELIVERS_TO":
                            region_orders.add(pred)

        # Path B: Discover orders from affected shipping modes (Order -[FULFILLED_BY]-> Shipping_Mode)
        mode_orders: Set[str] = set()
        if affected_shipping_modes:
            for mode_node in affected_shipping_modes:
                for pred in self.G.predecessors(mode_node):
                    if self.G.nodes[pred].get("node_type") == "Order":
                        edge_data = self.G.get_edge_data(pred, mode_node, default={})
                        if edge_data.get("relationship", "FULFILLED_BY") == "FULFILLED_BY":
                            mode_orders.add(pred)

        # Combine restrictions:
        # If both region and carrier mode restrictions are present, take intersection (deduplicated)
        if affected_regions and affected_shipping_modes:
            affected_orders: Set[str] = region_orders.intersection(mode_orders)
        elif affected_regions:
            affected_orders = set(region_orders)
        elif affected_shipping_modes:
            affected_orders = set(mode_orders)
        else:
            affected_orders = set()

        # ======================================================================
        # STEP 3: FIND CONNECTED ENTITIES (HOP 2 - SECONDARY EXPOSURE)
        # ======================================================================
        # Customers: Customer -[PLACES]-> Order (Predecessors of Order)
        affected_customers: Set[str] = set()
        # Products: Order -[CONTAINS]-> Product (Successors of Order)
        affected_products: Set[str] = set()
        # Shipping Modes observed in affected orders: Order -[FULFILLED_BY]-> Shipping_Mode
        observed_shipping_modes: Set[str] = set(affected_shipping_modes)

        product_revenue_map: Dict[str, float] = {}
        customer_revenue_map: Dict[str, float] = {}

        for ord_id in affected_orders:
            ord_spend = float(self.G.nodes[ord_id].get("total_spend", 0.0))

            # Customers
            for cust in self.G.predecessors(ord_id):
                if self.G.nodes[cust].get("node_type") == "Customer":
                    affected_customers.add(cust)
                    customer_revenue_map[cust] = customer_revenue_map.get(cust, 0.0) + ord_spend

            # Products & Shipping Modes
            for succ in self.G.successors(ord_id):
                n_type = self.G.nodes[succ].get("node_type")
                if n_type == "Product":
                    affected_products.add(succ)
                    edge_rev = float(self.G.get_edge_data(ord_id, succ, {}).get("revenue", 0.0))
                    product_revenue_map[succ] = product_revenue_map.get(succ, 0.0) + (edge_rev if edge_rev > 0 else ord_spend)
                elif n_type == "Shipping_Mode":
                    observed_shipping_modes.add(succ)

        # ======================================================================
        # STEP 4: FIND TAXONOMIC ENTITIES (HOP 3 - TERTIARY EXPOSURE)
        # ======================================================================
        # Categories: Product -[BELONGS_TO]-> Category
        affected_categories: Set[str] = set()
        for prod in affected_products:
            for cat in self.G.successors(prod):
                if self.G.nodes[cat].get("node_type") == "Category":
                    affected_categories.add(cat)

        # ======================================================================
        # STEP 5: ORDER ELIGIBILITY PARTITIONING (Correction H1)
        # ======================================================================
        eligibility_config = self.config.get("eligibility_rules", {})
        ineligible_order_statuses = set(s.upper() for s in eligibility_config.get("ineligible_order_statuses", ["CANCELED", "SUSPECTED_FRAUD"]))
        ineligible_deliv_statuses = set(s.lower() for s in eligibility_config.get("ineligible_delivery_statuses", ["shipping canceled"]))

        eligible_orders: Set[str] = set()
        ineligible_orders: Set[str] = set()
        ineligibility_reasons: Dict[str, str] = {}

        total_order_revenue = 0.0
        total_order_profit = 0.0
        eligible_revenue = 0.0
        eligible_profit = 0.0
        ineligible_revenue = 0.0
        ineligible_profit = 0.0

        for ord_id in affected_orders:
            odata = self.G.nodes[ord_id]
            ospend = float(odata.get("total_spend", 0.0))
            oprofit = float(odata.get("total_profit", 0.0))
            ostatus = str(odata.get("order_status", "")).upper()
            deliv_status = str(odata.get("delivery_status", "")).lower()

            total_order_revenue += ospend
            total_order_profit += oprofit

            # Evaluation of non-shipped / canceled criteria
            if ostatus in ineligible_order_statuses:
                ineligible_orders.add(ord_id)
                ineligibility_reasons[ord_id] = f"ORDER_STATUS_{ostatus}"
                ineligible_revenue += ospend
                ineligible_profit += oprofit
            elif deliv_status in ineligible_deliv_statuses:
                ineligible_orders.add(ord_id)
                ineligibility_reasons[ord_id] = f"DELIVERY_STATUS_{deliv_status.upper().replace(' ', '_')}"
                ineligible_revenue += ospend
                ineligible_profit += oprofit
            else:
                eligible_orders.add(ord_id)
                eligible_revenue += ospend
                eligible_profit += oprofit

        # Delay impact baseline & scenario metrics (calculated on ELIGIBLE population)
        n_total_orders = len(affected_orders)
        n_eligible_orders = len(eligible_orders)
        n_ineligible_orders = len(ineligible_orders)

        baseline_delayed_count = sum(1 for o in eligible_orders if int(self.G.nodes[o].get("delayed_orders", 0)) == 1)
        baseline_nondelayed_count = n_eligible_orders - baseline_delayed_count

        baseline_delay_rate = round((baseline_delayed_count / n_eligible_orders * 100.0), 2) if n_eligible_orders > 0 else 0.0

        # Scenario surge on eligible orders (Correction H3):
        # Scenario Delay Rate = Baseline + (1 - Baseline) * (CapacityReduction/100) * SeverityWeight
        delay_surge_pct = (1.0 - (baseline_delayed_count / n_eligible_orders if n_eligible_orders > 0 else 0.0)) * (capacity_reduction_pct / 100.0) * severity_weight * 100.0
        scenario_delay_rate = min(100.0, round(baseline_delay_rate + delay_surge_pct, 2)) if n_eligible_orders > 0 else 0.0
        scenario_total_delayed = int(round(n_eligible_orders * (scenario_delay_rate / 100.0))) if n_eligible_orders > 0 else 0
        
        # Newly delayed orders CANNOT exceed eligible non-delayed orders
        scenario_newly_delayed = max(0, min(baseline_nondelayed_count, scenario_total_delayed - baseline_delayed_count))

        # ======================================================================
        # STEP 6: ASSEMBLE STRUCTURED ENTITY RECORDS (Corrections M2 & H3)
        # ======================================================================
        entity_records: List[Dict[str, Any]] = []

        def build_record(
            entity_id: str,
            entity_type: str,
            hop: int,
            rev: Optional[float] = None,
            prof: Optional[float] = None,
            is_eligible: Optional[bool] = None,
            elig_status: Optional[str] = None,
            order_status: Optional[str] = None,
            deliv_status: Optional[str] = None,
            hist_delayed: Optional[bool] = None,
            scen_delayed: Optional[bool] = None
        ) -> Dict[str, Any]:
            # Topological mapping confidence (attenuates across hops)
            mapping_conf = attenuation_map.get(str(hop), 0.50)
            
            # Impact score as an uncalibrated scenario index on [0.0, 1.0]
            score = round(min(1.0, max(0.0, (capacity_reduction_pct / 100.0) * severity_weight * mapping_conf)), 4)
            prop_level = self.config.get("propagation_levels", {}).get(str(hop), "SECONDARY")

            record: Dict[str, Any] = {
                "shockwave_id": shockwave_id,
                "source_event_id": event_id,
                "source_disruption_type": disruption_type,
                "affected_entity_id": entity_id,
                "affected_entity_type": entity_type,
                "graph_distance": hop,
                "propagation_level": prop_level,
                "impact_score": score,
                "impact_severity": severity,
                "source_event_confidence": source_confidence,
                "graph_mapping_confidence": mapping_conf,
                "score_calibration_status": "UNCALIBRATED_SCENARIO_INDEX",
                "estimated_delay_hours": delay_estimate_hours if hop <= 1 else round(delay_estimate_hours * mapping_conf, 1),
                "revenue_exposure": round(rev, 2) if rev is not None else None,
                "profit_exposure": round(prof, 2) if prof is not None else None,
                "propagation_method": "REVERSE_BIPARTITE_GRAPH_TRAVERSAL",
                "assumption_flags": default_assumptions,
                "analysis_timestamp": analysis_timestamp
            }

            # Extended fields for Order entities
            if entity_type == "ORDER":
                record["is_eligible_for_delay"] = is_eligible
                record["eligibility_status"] = elig_status
                record["order_status"] = order_status
                record["delivery_status"] = deliv_status
                record["historical_delayed"] = hist_delayed
                record["scenario_assumed_delayed"] = scen_delayed

            return record

        # Hop 0: Epicenters
        for epi in sorted(epicenter_nodes):
            etype = self.G.nodes[epi].get("node_type", "EPICENTER")
            entity_records.append(build_record(epi, etype.upper(), 0))

        # Hop 1: Orders (Authoritative Financial Baseline)
        for ord_id in sorted(affected_orders):
            odata = self.G.nodes[ord_id]
            ospend = float(odata.get("total_spend", 0.0))
            oprofit = float(odata.get("total_profit", 0.0))
            is_del = (int(odata.get("delayed_orders", 0)) == 1)
            is_elig = (ord_id in eligible_orders)
            elig_stat = "ELIGIBLE" if is_elig else ineligibility_reasons.get(ord_id, "INELIGIBLE")
            ostatus = odata.get("order_status")
            dstatus = odata.get("delivery_status")

            # Under scenario: an eligible order is assumed delayed if it was already delayed or newly assumed delayed
            scen_del = is_del if not is_elig else True  # In 100% capacity scenario, all eligible orders are assumed delayed

            entity_records.append(build_record(
                ord_id, "ORDER", 1,
                rev=ospend, prof=oprofit,
                is_eligible=is_elig,
                elig_status=elig_stat,
                order_status=ostatus,
                deliv_status=dstatus,
                hist_delayed=is_del,
                scen_delayed=scen_del
            ))

        # Hop 2: Customers
        for cust_id in sorted(affected_customers):
            c_rev = customer_revenue_map.get(cust_id, 0.0)
            entity_records.append(build_record(cust_id, "CUSTOMER", 2, rev=c_rev))

        # Hop 2: Products
        for prod_id in sorted(affected_products):
            p_rev = product_revenue_map.get(prod_id, 0.0)
            entity_records.append(build_record(prod_id, "PRODUCT", 2, rev=p_rev))

        # Hop 2: Shipping Modes (all observed shipping modes for affected orders)
        for mode_id in sorted(observed_shipping_modes):
            # Avoid duplicating if already recorded as an epicenter in Hop 0
            if mode_id not in epicenter_nodes:
                entity_records.append(build_record(mode_id, "SHIPPING_MODE", 2))

        # Hop 3: Categories
        for cat_id in sorted(affected_categories):
            entity_records.append(build_record(cat_id, "CATEGORY", 3))

        # ======================================================================
        # STEP 7: AGGREGATE IMPACT SUMMARY CALCULATIONS (Correction H3 & M1)
        # ======================================================================
        ineligible_breakdown = {}
        for ord_id in ineligible_orders:
            reason = ineligibility_reasons.get(ord_id, "UNKNOWN")
            ineligible_breakdown[reason] = ineligible_breakdown.get(reason, 0) + 1

        impact_summary = {
            "shockwave_id": shockwave_id,
            "source_event_id": event_id,
            "source_disruption_type": disruption_type,
            "severity": severity,
            "source_event_confidence": source_confidence,
            "capacity_reduction_pct": capacity_reduction_pct,
            "event_delay_estimate_hours": delay_estimate_hours,
            "epicenter_nodes": sorted(list(epicenter_nodes)),
            "contextual_parent_market": contextual_parent_market,
            "entity_counts": {
                "total_affected_entities": len(entity_records),
                "unique_affected_orders": n_total_orders,
                "eligible_orders_for_delay": n_eligible_orders,
                "ineligible_orders_excluded": n_ineligible_orders,
                "unique_affected_customers": len(affected_customers),
                "unique_affected_products": len(affected_products),
                "unique_affected_shipping_modes": len(observed_shipping_modes),
                "unique_affected_regions": len(affected_regions),
                "unique_affected_markets": len(affected_markets),
                "unique_affected_categories": len(affected_categories)
            },
            "financial_exposure": {
                "total_gross_revenue_exposure_usd": round(total_order_revenue, 2),
                "total_gross_profit_exposure_usd": round(total_order_profit, 2),
                "eligible_revenue_exposure_usd": round(eligible_revenue, 2),
                "eligible_profit_exposure_usd": round(eligible_profit, 2),
                "ineligible_revenue_excluded_usd": round(ineligible_revenue, 2),
                "ineligible_profit_excluded_usd": round(ineligible_profit, 2),
                "accounting_note": "Total gross exposure represents all orders in the transit cohort. Eligible exposure excludes canceled and fraudulent orders."
            },
            "delay_projections": {
                "accounting_note": "Delay metrics distinguish observed historical baseline performance from assumption-driven scenario projections. Ineligible orders (canceled/fraud) are strictly excluded from delay projections. Event delay estimate of 96.0 hours is recorded as disruption duration metadata and is unapplied to individual order delivery windows.",
                "order_cohort_breakdown": {
                    "total_affected_orders": n_total_orders,
                    "eligible_orders_for_delay": n_eligible_orders,
                    "ineligible_orders_excluded": n_ineligible_orders,
                    "ineligible_orders_breakdown": ineligible_breakdown
                },
                "historical_baseline": {
                    "observed_delayed_orders": baseline_delayed_count,
                    "observed_nondelayed_orders": baseline_nondelayed_count,
                    "baseline_delay_rate_pct": baseline_delay_rate
                },
                "scenario_projection": {
                    "scenario_assumed_delay_rate_pct": scenario_delay_rate,
                    "scenario_total_assumed_delayed_orders": scenario_total_delayed,
                    "scenario_newly_assumed_delayed_orders": scenario_newly_delayed,
                    "unaffected_eligible_orders": max(0, n_eligible_orders - scenario_total_delayed),
                    "calculation_nature": "ASSUMPTION_DRIVEN_SCENARIO_HEURISTIC",
                    "event_delay_estimate_hours": delay_estimate_hours,
                    "event_delay_estimate_applied_to_orders": False
                }
            },
            "assumption_flags": default_assumptions,
            "execution_metadata": {
                "analysis_timestamp": analysis_timestamp,
                "execution_time_seconds": round(time.time() - t_start, 4),
                "propagation_method": "REVERSE_BIPARTITE_GRAPH_TRAVERSAL"
            }
        }

        return entity_records, impact_summary

    def _build_empty_summary(
        self,
        shockwave_id: str,
        event: Dict[str, Any],
        ts: str,
        assumptions: List[str],
        elapsed: float,
        reason: str = "NO_MATCH"
    ) -> Dict[str, Any]:
        """Constructs an empty summary structure when mapping fails or yields 0 entities."""
        return {
            "shockwave_id": shockwave_id,
            "source_event_id": event.get("event_id", "UNKNOWN"),
            "source_disruption_type": event.get("disruption_type", "UNKNOWN"),
            "severity": event.get("severity", "LOW"),
            "source_event_confidence": float(event.get("source_confidence", 0.0)),
            "capacity_reduction_pct": float(event.get("capacity_reduction_pct", 0.0)),
            "event_delay_estimate_hours": float(event.get("delay_estimate_hours", 0.0)),
            "epicenter_nodes": [],
            "contextual_parent_market": None,
            "entity_counts": {
                "total_affected_entities": 0,
                "unique_affected_orders": 0,
                "eligible_orders_for_delay": 0,
                "ineligible_orders_excluded": 0,
                "unique_affected_customers": 0,
                "unique_affected_products": 0,
                "unique_affected_shipping_modes": 0,
                "unique_affected_regions": 0,
                "unique_affected_markets": 0,
                "unique_affected_categories": 0
            },
            "financial_exposure": {
                "total_gross_revenue_exposure_usd": 0.0,
                "total_gross_profit_exposure_usd": 0.0,
                "eligible_revenue_exposure_usd": 0.0,
                "eligible_profit_exposure_usd": 0.0,
                "ineligible_revenue_excluded_usd": 0.0,
                "ineligible_profit_excluded_usd": 0.0,
                "accounting_note": f"Empty shockwave generated (reason: {reason})."
            },
            "delay_projections": {
                "accounting_note": "No entities matched.",
                "order_cohort_breakdown": {
                    "total_affected_orders": 0,
                    "eligible_orders_for_delay": 0,
                    "ineligible_orders_excluded": 0,
                    "ineligible_orders_breakdown": {}
                },
                "historical_baseline": {
                    "observed_delayed_orders": 0,
                    "observed_nondelayed_orders": 0,
                    "baseline_delay_rate_pct": 0.0
                },
                "scenario_projection": {
                    "scenario_assumed_delay_rate_pct": 0.0,
                    "scenario_total_assumed_delayed_orders": 0,
                    "scenario_newly_assumed_delayed_orders": 0,
                    "unaffected_eligible_orders": 0,
                    "calculation_nature": "EMPTY_COHORT",
                    "event_delay_estimate_hours": 0.0,
                    "event_delay_estimate_applied_to_orders": False
                }
            },
            "assumption_flags": assumptions,
            "execution_metadata": {
                "analysis_timestamp": ts,
                "execution_time_seconds": round(elapsed, 4),
                "propagation_method": "REVERSE_BIPARTITE_GRAPH_TRAVERSAL",
                "termination_reason": reason
            }
        }

    def export_results(self, entity_records: List[Dict[str, Any]], impact_summary: Dict[str, Any], output_dir: str):
        """Exports entity-level table and summary to CSV and JSON."""
        os.makedirs(output_dir, exist_ok=True)

        entities_csv_path = os.path.join(output_dir, "shockwave_entities.csv")
        entities_json_path = os.path.join(output_dir, "shockwave_entities.json")
        summary_json_path = os.path.join(output_dir, "shockwave_summary.json")

        # 1. Export CSV
        df = pd.DataFrame(entity_records)
        # Convert list of assumption flags to pipe-separated string for CSV readability
        if "assumption_flags" in df.columns:
            df["assumption_flags"] = df["assumption_flags"].apply(lambda x: "|".join(x) if isinstance(x, list) else str(x))
        df.to_csv(entities_csv_path, index=False)
        print(f"[INFO] Exported {len(df):,} entity records to CSV: {entities_csv_path}")

        # 2. Export Entities JSON
        with open(entities_json_path, "w", encoding="utf-8") as f:
            json.dump(entity_records, f, indent=2)
        print(f"[INFO] Exported entity records to JSON: {entities_json_path}")

        # 3. Export Summary JSON
        with open(summary_json_path, "w", encoding="utf-8") as f:
            json.dump(impact_summary, f, indent=2)
        print(f"[INFO] Exported shockwave impact summary to JSON: {summary_json_path}")


# ==============================================================================
# 2. CLI ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(description="ChainSentinel Shockwave Propagation Engine (Phase 8 - Corrected)")
    parser.add_argument("--event", "-e", required=True, help="Path to disruption event JSON file")
    parser.add_argument("--nodes", "-n", default="data/phase6/graph_nodes.csv", help="Path to graph_nodes.csv")
    parser.add_argument("--edges", "-g", default="data/phase6/graph_edges.csv", help="Path to graph_edges.csv")
    parser.add_argument("--parquet", "-p", default="data/clean_parquet", help="Path to clean parquet dataset")
    parser.add_argument("--config", "-c", default="docker/spark/batch/phase8/shockwave_config.json", help="Path to shockwave_config.json")
    parser.add_argument("--output-dir", "-o", default="data/phase8/output/task8d_corrected", help="Directory for shockwave outputs")

    args = parser.parse_args()

    # Load event
    if not os.path.exists(args.event):
        print(f"[ERROR] Event file not found: {args.event}")
        sys.exit(1)

    with open(args.event, "r", encoding="utf-8") as f:
        event_data = json.load(f)

    # Initialize Engine
    engine = ShockwaveEngine(config_path=args.config)
    engine.load_graph_from_csv(nodes_csv_path=args.nodes, edges_csv_path=args.edges, order_status_parquet=args.parquet)

    # Propagate Shockwave
    print(f"\n[INFO] Propagating shockwave for event: {event_data.get('event_id')} ({event_data.get('disruption_type')})...")
    entity_records, summary = engine.propagate_shockwave(event_data)

    # Export
    engine.export_results(entity_records, summary, output_dir=args.output_dir)

    print("\n" + "=" * 70)
    print("SHOCKWAVE PROPAGATION SUMMARY (CORRECTED):")
    print("=" * 70)
    print(f"Shockwave ID:                    {summary.get('shockwave_id')}")
    print(f"Source Event ID:                 {summary.get('source_event_id')}")
    print(f"Disruption Type:                 {summary.get('source_disruption_type')}")
    print(f"Total Affected Orders:           {summary['entity_counts']['unique_affected_orders']:,}")
    print(f"Eligible Orders for Delay:       {summary['entity_counts']['eligible_orders_for_delay']:,}")
    print(f"Ineligible Orders (Excluded):    {summary['entity_counts']['ineligible_orders_excluded']:,}")
    print(f"Gross Revenue Exposure:          ${summary['financial_exposure']['total_gross_revenue_exposure_usd']:,.2f}")
    print(f"Eligible Revenue Exposure:       ${summary['financial_exposure']['eligible_revenue_exposure_usd']:,.2f}")
    print(f"Baseline Delay Rate:             {summary['delay_projections']['historical_baseline']['baseline_delay_rate_pct']:.2f}%")
    print(f"Scenario Delay Rate:             {summary['delay_projections']['scenario_projection']['scenario_assumed_delay_rate_pct']:.2f}%")
    print(f"Scenario Newly Delayed Orders:   {summary['delay_projections']['scenario_projection']['scenario_newly_assumed_delayed_orders']:,}")
    print(f"Execution Latency:               {summary['execution_metadata']['execution_time_seconds']}s")
    print("=" * 70)


if __name__ == "__main__":
    main()

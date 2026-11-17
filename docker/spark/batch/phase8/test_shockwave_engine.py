#!/usr/bin/env python3
"""
Unit Test Suite for ChainSentinel Shockwave Propagation Engine
==============================================================
File: test_shockwave_engine.py
Version: 1.1.0 (Expanded for Task 8D Corrections)
Execution: E:\\BDA\\ChainSentinel\\python-env\\Scripts\\python test_shockwave_engine.py -v

Comprehensive Coverage:
1. Directed predecessor traversal (reverse walk from Region to Order)
2. Market-to-region-to-order hierarchical resolution
3. Unsupported disruption mapping and graceful fallback
4. Duplicate-path prevention and entity deduplication
5. Unique order counting without double-counting
6. Unique order-item financial aggregation
7. Missing or malformed event fields
8. Missing graph nodes / unknown epicenter handling
9. Empty affected cohorts handling
10. Assumption flag presence and schema conformance
11. Severity classification and attenuation scaling
12. Output schema validation against expected fields
13. Canceled-order exclusion (Correction H1)
14. Suspected-fraud-order exclusion (Correction H1)
15. Baseline delay rate denominator alignment (Correction H1)
16. Newly delayed ceiling bounds (Correction H1)
17. Already-delayed orders not double counted (Correction H1)
18. Carrier-only disruption propagation (Correction H2)
19. Region-only disruption propagation (Correction H2)
20. Combined region and carrier restrictions intersection (Correction H2)
21. Unsupported carrier mapping handling (Correction H2)
22. Market context vs regional epicenter distinction (Correction M1)
23. Confidence separation (source vs graph mapping) (Correction M2)
24. 96-hour duration unapplied to individual orders (Correction H3)
25. Empty eligible cohort handling (Edge Case)
"""

import unittest
import os
import sys
import json
import tempfile
import networkx as nx

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))
from shockwave_engine import ShockwaveEngine


class TestShockwaveEngine(unittest.TestCase):

    def setUp(self):
        """Builds a verified synthetic in-memory graph for unit tests."""
        self.engine = ShockwaveEngine()
        self.G = nx.DiGraph()

        # Nodes
        # Market
        self.G.add_node("MKT_Pacific_Asia", node_type="Market", label="Pacific Asia", order_count=4, total_spend=2500.0)
        self.G.add_node("MKT_Europe", node_type="Market", label="Europe", order_count=1, total_spend=500.0)

        # Region
        self.G.add_node("REG_Eastern_Asia", node_type="Region", label="Eastern Asia", order_count=4, total_spend=2500.0)
        self.G.add_node("REG_Western_Europe", node_type="Region", label="Western Europe", order_count=1, total_spend=500.0)

        # Shipping Modes
        self.G.add_node("SHIP_Standard_Class", node_type="Shipping_Mode", label="Standard Class", order_count=2, total_spend=1500.0)
        self.G.add_node("SHIP_Second_Class", node_type="Shipping_Mode", label="Second Class", order_count=1, total_spend=600.0)
        self.G.add_node("SHIP_First_Class", node_type="Shipping_Mode", label="First Class", order_count=2, total_spend=900.0)

        # Orders:
        # ORD_101: Shipped, historically delayed
        self.G.add_node("ORD_101", node_type="Order", label="ORD_101", total_spend=1000.0, total_profit=200.0, delayed_orders=1, order_status="COMPLETE", delivery_status="Late delivery")
        # ORD_102: Shipped, on time
        self.G.add_node("ORD_102", node_type="Order", label="ORD_102", total_spend=500.0, total_profit=50.0, delayed_orders=0, order_status="COMPLETE", delivery_status="Shipping on time")
        # ORD_103: Canceled order (ineligible)
        self.G.add_node("ORD_103", node_type="Order", label="ORD_103", total_spend=600.0, total_profit=60.0, delayed_orders=0, order_status="CANCELED", delivery_status="Shipping canceled")
        # ORD_104: Suspected fraud order (ineligible)
        self.G.add_node("ORD_104", node_type="Order", label="ORD_104", total_spend=400.0, total_profit=40.0, delayed_orders=0, order_status="SUSPECTED_FRAUD", delivery_status="Shipping canceled")
        # ORD_201: European order
        self.G.add_node("ORD_201", node_type="Order", label="ORD_201", total_spend=500.0, total_profit=100.0, delayed_orders=0, order_status="COMPLETE", delivery_status="Shipping on time")

        # Customers
        self.G.add_node("CUST_01", node_type="Customer", label="CUST_01", order_count=3, total_spend=2100.0)
        self.G.add_node("CUST_02", node_type="Customer", label="CUST_02", order_count=2, total_spend=900.0)

        # Products
        self.G.add_node("PROD_A", node_type="Product", label="Kayak", order_count=3, total_spend=1800.0)
        self.G.add_node("PROD_B", node_type="Product", label="Paddle", order_count=2, total_spend=700.0)

        # Categories
        self.G.add_node("CAT_WaterSports", node_type="Category", label="Water Sports")

        # Directed Edges:
        # Region -> Market (LOCATED_IN)
        self.G.add_edge("REG_Eastern_Asia", "MKT_Pacific_Asia", relationship="LOCATED_IN", weight=1.0)
        self.G.add_edge("REG_Western_Europe", "MKT_Europe", relationship="LOCATED_IN", weight=1.0)

        # Order -> Region (DELIVERS_TO)
        self.G.add_edge("ORD_101", "REG_Eastern_Asia", relationship="DELIVERS_TO", weight=1.0)
        self.G.add_edge("ORD_102", "REG_Eastern_Asia", relationship="DELIVERS_TO", weight=1.0)
        self.G.add_edge("ORD_103", "REG_Eastern_Asia", relationship="DELIVERS_TO", weight=1.0)
        self.G.add_edge("ORD_104", "REG_Eastern_Asia", relationship="DELIVERS_TO", weight=1.0)
        self.G.add_edge("ORD_201", "REG_Western_Europe", relationship="DELIVERS_TO", weight=1.0)

        # Customer -> Order (PLACES)
        self.G.add_edge("CUST_01", "ORD_101", relationship="PLACES", weight=1.0)
        self.G.add_edge("CUST_01", "ORD_102", relationship="PLACES", weight=1.0)
        self.G.add_edge("CUST_01", "ORD_103", relationship="PLACES", weight=1.0)
        self.G.add_edge("CUST_02", "ORD_104", relationship="PLACES", weight=1.0)
        self.G.add_edge("CUST_02", "ORD_201", relationship="PLACES", weight=1.0)

        # Order -> Product (CONTAINS)
        self.G.add_edge("ORD_101", "PROD_A", relationship="CONTAINS", weight=1.0, revenue=800.0)
        self.G.add_edge("ORD_101", "PROD_B", relationship="CONTAINS", weight=1.0, revenue=200.0)
        self.G.add_edge("ORD_102", "PROD_A", relationship="CONTAINS", weight=1.0, revenue=500.0)
        self.G.add_edge("ORD_103", "PROD_A", relationship="CONTAINS", weight=1.0, revenue=600.0)
        self.G.add_edge("ORD_104", "PROD_B", relationship="CONTAINS", weight=1.0, revenue=400.0)
        self.G.add_edge("ORD_201", "PROD_A", relationship="CONTAINS", weight=1.0, revenue=500.0)

        # Order -> Shipping_Mode (FULFILLED_BY)
        self.G.add_edge("ORD_101", "SHIP_Standard_Class", relationship="FULFILLED_BY", weight=1.0)
        self.G.add_edge("ORD_102", "SHIP_Standard_Class", relationship="FULFILLED_BY", weight=1.0)
        self.G.add_edge("ORD_103", "SHIP_Second_Class", relationship="FULFILLED_BY", weight=1.0)
        self.G.add_edge("ORD_104", "SHIP_First_Class", relationship="FULFILLED_BY", weight=1.0)
        self.G.add_edge("ORD_201", "SHIP_First_Class", relationship="FULFILLED_BY", weight=1.0)

        # Product -> Category (BELONGS_TO)
        self.G.add_edge("PROD_A", "CAT_WaterSports", relationship="BELONGS_TO", weight=1.0)
        self.G.add_edge("PROD_B", "CAT_WaterSports", relationship="BELONGS_TO", weight=1.0)

        self.engine.set_graph(self.G)

    # --------------------------------------------------------------------------
    # ORIGINAL TESTS (UPDATED FOR CORRECTIONS)
    # --------------------------------------------------------------------------

    def test_directed_predecessor_traversal(self):
        """Verifies that reverse-directed walk correctly discovers orders from disrupted Region."""
        event = {
            "event_id": "TEST-001",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL",
            "source_confidence": 1.0,
            "capacity_reduction_pct": 100.0
        }
        records, summary = self.engine.propagate_shockwave(event)
        order_records = [r for r in records if r["affected_entity_type"] == "ORDER"]
        order_ids = {r["affected_entity_id"] for r in order_records}

        # Must discover all 4 Eastern Asia orders (ORD_101, 102, 103, 104), but NOT ORD_201
        self.assertEqual(order_ids, {"ORD_101", "ORD_102", "ORD_103", "ORD_104"})
        self.assertEqual(summary["entity_counts"]["unique_affected_orders"], 4)

    def test_market_to_region_resolution(self):
        """Verifies that an event with only Market resolves all child Regions."""
        event = {
            "event_id": "TEST-002",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "severity": "HIGH",
            "source_confidence": 0.9,
            "capacity_reduction_pct": 50.0
        }
        records, summary = self.engine.propagate_shockwave(event)
        self.assertIn("MKT_Pacific_Asia", summary["epicenter_nodes"])
        self.assertIn("REG_Eastern_Asia", summary["epicenter_nodes"])
        self.assertEqual(summary["entity_counts"]["unique_affected_orders"], 4)

    def test_alias_reconciliation(self):
        """Verifies that 'East Asia' is reconciled to 'Eastern Asia' via alias map."""
        event = {
            "event_id": "TEST-003",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": "East Asia",
            "severity": "CRITICAL"
        }
        records, summary = self.engine.propagate_shockwave(event)
        self.assertIn("REG_Eastern_Asia", summary["epicenter_nodes"])
        self.assertEqual(summary["entity_counts"]["unique_affected_orders"], 4)

    def test_unsupported_disruption_mapping(self):
        """Verifies that an unsupported or unresolvable market/region produces an empty cohort cleanly."""
        event = {
            "event_id": "TEST-004",
            "disruption_type": "UNKNOWN_EVENT_TYPE",
            "affected_market": "Antarctica",
            "affected_region": "South Pole",
            "severity": "LOW"
        }
        records, summary = self.engine.propagate_shockwave(event)
        self.assertEqual(len(records), 0)
        self.assertEqual(summary["entity_counts"]["unique_affected_orders"], 0)
        self.assertEqual(summary["financial_exposure"]["total_gross_revenue_exposure_usd"], 0.0)

    def test_duplicate_path_prevention(self):
        """Verifies that an entity reached via multiple paths is recorded exactly once."""
        event = {
            "event_id": "TEST-005",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL"
        }
        records, summary = self.engine.propagate_shockwave(event)
        entity_ids = [r["affected_entity_id"] for r in records]
        self.assertEqual(len(entity_ids), len(set(entity_ids)))

    def test_unique_order_counting(self):
        """Verifies that each affected order is counted exactly once."""
        event = {
            "event_id": "TEST-006",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL"
        }
        _, summary = self.engine.propagate_shockwave(event)
        self.assertEqual(summary["entity_counts"]["unique_affected_orders"], 4)

    def test_financial_aggregation_no_double_counting(self):
        """Verifies that Order-level financial exposures sum correctly without double-counting."""
        event = {
            "event_id": "TEST-007",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL"
        }
        _, summary = self.engine.propagate_shockwave(event)
        # 1000 + 500 + 600 + 400 = 2500.0 gross revenue
        # 200 + 50 + 60 + 40 = 350.0 gross profit
        self.assertEqual(summary["financial_exposure"]["total_gross_revenue_exposure_usd"], 2500.0)
        self.assertEqual(summary["financial_exposure"]["total_gross_profit_exposure_usd"], 350.0)
        # Eligible: ORD_101 (1000) + ORD_102 (500) = 1500.0 revenue, 250.0 profit
        self.assertEqual(summary["financial_exposure"]["eligible_revenue_exposure_usd"], 1500.0)
        self.assertEqual(summary["financial_exposure"]["eligible_profit_exposure_usd"], 250.0)

    def test_missing_or_malformed_event_fields(self):
        """Verifies graceful handling when optional event fields are missing or None."""
        event = {
            "event_id": "TEST-008",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": None,
            "severity": "MEDIUM"
        }
        records, summary = self.engine.propagate_shockwave(event)
        self.assertGreater(summary["entity_counts"]["unique_affected_orders"], 0)

    def test_assumption_flags_presence(self):
        """Verifies that required academic assumption flags are populated."""
        event = {
            "event_id": "TEST-009",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL"
        }
        records, summary = self.engine.propagate_shockwave(event)
        self.assertIn("ASSUMPTION_REGIONAL_CONTAINMENT", summary["assumption_flags"])
        self.assertIn("ASSUMPTION_NO_PHYSICAL_ROUTE", summary["assumption_flags"])
        self.assertIn("ASSUMPTION_HISTORICAL_REVENUE_EXPOSURE", summary["assumption_flags"])

    def test_severity_classification_and_attenuation(self):
        """Verifies that impact score scales with severity and attenuates across hops."""
        event_crit = {
            "event_id": "TEST-010-C",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL",
            "source_confidence": 1.0,
            "capacity_reduction_pct": 100.0
        }
        records_crit, _ = self.engine.propagate_shockwave(event_crit)
        ord_crit = next(r for r in records_crit if r["affected_entity_id"] == "ORD_101")
        prod_crit = next(r for r in records_crit if r["affected_entity_id"] == "PROD_A")

        # Hop 1 (Order): weight 1.0 * attenuation 1.0 = 1.0
        self.assertEqual(ord_crit["impact_score"], 1.0)
        # Hop 2 (Product): weight 1.0 * attenuation 0.85 = 0.85
        self.assertEqual(prod_crit["impact_score"], 0.85)

    def test_output_schema_validation(self):
        """Verifies that all mandatory fields are present in every entity record."""
        event = {
            "event_id": "TEST-011",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": "Eastern Asia",
            "severity": "HIGH",
            "source_confidence": 0.95,
            "delay_estimate_hours": 48.0
        }
        records, _ = self.engine.propagate_shockwave(event)
        required_fields = [
            "shockwave_id", "source_event_id", "source_disruption_type",
            "affected_entity_id", "affected_entity_type", "graph_distance",
            "propagation_level", "impact_score", "impact_severity",
            "source_event_confidence", "graph_mapping_confidence",
            "score_calibration_status", "propagation_method", "assumption_flags",
            "analysis_timestamp"
        ]
        for r in records:
            for rf in required_fields:
                self.assertIn(rf, r)
                self.assertIsNotNone(r[rf])

    def test_export_results(self):
        """Verifies that CSV and JSON export routines run and write valid artifacts."""
        event = {
            "event_id": "TEST-012",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL"
        }
        records, summary = self.engine.propagate_shockwave(event)

        with tempfile.TemporaryDirectory() as tmpdir:
            self.engine.export_results(records, summary, tmpdir)
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "shockwave_entities.csv")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "shockwave_entities.json")))
            self.assertTrue(os.path.exists(os.path.join(tmpdir, "shockwave_summary.json")))

    # --------------------------------------------------------------------------
    # TASK 8D EXPANDED TESTS
    # --------------------------------------------------------------------------

    def test_canceled_and_fraud_order_exclusion(self):
        """Correction H1: Verifies that CANCELED and SUSPECTED_FRAUD orders are excluded from delay metrics."""
        event = {
            "event_id": "TEST-013-ELIG",
            "disruption_type": "PORT_CLOSURE",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL",
            "capacity_reduction_pct": 100.0
        }
        records, summary = self.engine.propagate_shockwave(event)
        deliv = summary["delay_projections"]["order_cohort_breakdown"]

        # 4 total orders, 2 eligible (ORD_101, ORD_102), 2 ineligible (ORD_103 canceled, ORD_104 fraud)
        self.assertEqual(deliv["total_affected_orders"], 4)
        self.assertEqual(deliv["eligible_orders_for_delay"], 2)
        self.assertEqual(deliv["ineligible_orders_excluded"], 2)
        self.assertEqual(deliv["ineligible_orders_breakdown"].get("ORDER_STATUS_CANCELED"), 1)
        self.assertEqual(deliv["ineligible_orders_breakdown"].get("ORDER_STATUS_SUSPECTED_FRAUD"), 1)

        # Check entity record flags for ORD_103 and ORD_104
        ord_103 = next(r for r in records if r["affected_entity_id"] == "ORD_103")
        ord_104 = next(r for r in records if r["affected_entity_id"] == "ORD_104")
        self.assertFalse(ord_103["is_eligible_for_delay"])
        self.assertEqual(ord_103["eligibility_status"], "ORDER_STATUS_CANCELED")
        self.assertFalse(ord_104["is_eligible_for_delay"])
        self.assertEqual(ord_104["eligibility_status"], "ORDER_STATUS_SUSPECTED_FRAUD")

    def test_historical_baseline_denominator_alignment(self):
        """Correction H1: Baseline delay rate must use the eligible population as denominator."""
        event = {
            "event_id": "TEST-014-DENOM",
            "disruption_type": "PORT_CLOSURE",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL",
            "capacity_reduction_pct": 100.0
        }
        _, summary = self.engine.propagate_shockwave(event)
        base = summary["delay_projections"]["historical_baseline"]

        # Eligible orders: 2. Observed delayed: 1 (ORD_101). Baseline rate = 1 / 2 = 50.0%
        # (NOT 1 / 4 = 25.0% which would happen if canceled orders were in denominator)
        self.assertEqual(base["observed_delayed_orders"], 1)
        self.assertEqual(base["observed_nondelayed_orders"], 1)
        self.assertEqual(base["baseline_delay_rate_pct"], 50.0)

    def test_newly_delayed_ceiling(self):
        """Correction H1: Newly delayed orders cannot exceed eligible non-delayed orders."""
        event = {
            "event_id": "TEST-015-CEILING",
            "disruption_type": "PORT_CLOSURE",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL",
            "capacity_reduction_pct": 100.0
        }
        _, summary = self.engine.propagate_shockwave(event)
        scen = summary["delay_projections"]["scenario_projection"]

        # Non-delayed eligible orders = 1 (ORD_102). Newly delayed MUST be exactly 1, NOT 3!
        self.assertEqual(scen["scenario_newly_assumed_delayed_orders"], 1)
        self.assertEqual(scen["scenario_total_assumed_delayed_orders"], 2)

    def test_carrier_only_propagation(self):
        """Correction H2: Carrier-only disruption discovers orders without requiring region."""
        event = {
            "event_id": "TEST-016-CARRIER",
            "disruption_type": "CARRIER_CAPACITY_SHORTAGE",
            "affected_mode": "Standard Class",
            "severity": "HIGH",
            "capacity_reduction_pct": 50.0
        }
        records, summary = self.engine.propagate_shockwave(event)
        order_records = [r for r in records if r["affected_entity_type"] == "ORDER"]
        order_ids = {r["affected_entity_id"] for r in order_records}

        # ORD_101 and ORD_102 are fulfilled by Standard Class
        self.assertEqual(order_ids, {"ORD_101", "ORD_102"})
        self.assertEqual(summary["entity_counts"]["unique_affected_orders"], 2)
        self.assertIn("SHIP_Standard_Class", summary["epicenter_nodes"])

    def test_region_only_propagation(self):
        """Correction H2: Region-only disruption discovers all orders in region regardless of carrier."""
        event = {
            "event_id": "TEST-017-REGION",
            "disruption_type": "PORT_CLOSURE",
            "affected_region": "Western Europe",
            "severity": "MEDIUM",
            "capacity_reduction_pct": 50.0
        }
        records, summary = self.engine.propagate_shockwave(event)
        order_records = [r for r in records if r["affected_entity_type"] == "ORDER"]
        self.assertEqual(len(order_records), 1)
        self.assertEqual(order_records[0]["affected_entity_id"], "ORD_201")

    def test_combined_region_and_carrier_intersection(self):
        """Correction H2: Combined region + carrier restricts to intersection without duplication."""
        # In Eastern Asia: ORD_101 (Standard), ORD_102 (Standard), ORD_103 (Second), ORD_104 (First)
        # Restrict to Eastern Asia + Second Class -> only ORD_103
        event = {
            "event_id": "TEST-018-COMBINED",
            "disruption_type": "CARRIER_CAPACITY_SHORTAGE",
            "affected_region": "Eastern Asia",
            "affected_mode": "Second Class",
            "severity": "HIGH",
            "capacity_reduction_pct": 50.0
        }
        records, summary = self.engine.propagate_shockwave(event)
        order_records = [r for r in records if r["affected_entity_type"] == "ORDER"]
        self.assertEqual(len(order_records), 1)
        self.assertEqual(order_records[0]["affected_entity_id"], "ORD_103")

    def test_unsupported_carrier_mapping(self):
        """Correction H2: Unsupported carrier produces empty cohort with clean termination reason."""
        event = {
            "event_id": "TEST-019-BADCARRIER",
            "disruption_type": "CARRIER_CAPACITY_SHORTAGE",
            "affected_mode": "Hyperloop Drone Freight",
            "severity": "CRITICAL"
        }
        records, summary = self.engine.propagate_shockwave(event)
        self.assertEqual(len(records), 0)
        self.assertEqual(summary["entity_counts"]["unique_affected_orders"], 0)
        self.assertEqual(summary["execution_metadata"].get("termination_reason"), "UNSUPPORTED_SHIPPING_MODE")

    def test_market_context_vs_regional_epicenter(self):
        """Correction M1: When region is resolved, Market is contextual parent, not Hop 0 epicenter."""
        event = {
            "event_id": "TEST-020-MKTCTX",
            "disruption_type": "PORT_CLOSURE",
            "affected_market": "Pacific Asia",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL"
        }
        records, summary = self.engine.propagate_shockwave(event)

        # Region IS in epicenters; Market is NOT in epicenters
        self.assertIn("REG_Eastern_Asia", summary["epicenter_nodes"])
        self.assertNotIn("MKT_Pacific_Asia", summary["epicenter_nodes"])
        self.assertEqual(summary["contextual_parent_market"], "MKT_Pacific_Asia")

    def test_confidence_separation(self):
        """Correction M2: Source event confidence and graph mapping confidence must be separate."""
        event = {
            "event_id": "TEST-021-CONF",
            "disruption_type": "PORT_CLOSURE",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL",
            "source_confidence": 0.88
        }
        records, summary = self.engine.propagate_shockwave(event)
        self.assertEqual(summary["source_event_confidence"], 0.88)

        ord_record = next(r for r in records if r["affected_entity_id"] == "ORD_101")
        # source_event_confidence should be 0.88; graph_mapping_confidence should be 1.0 (Hop 1)
        self.assertEqual(ord_record["source_event_confidence"], 0.88)
        self.assertEqual(ord_record["graph_mapping_confidence"], 1.0)
        self.assertEqual(ord_record["score_calibration_status"], "UNCALIBRATED_SCENARIO_INDEX")

    def test_duration_metadata_unapplied_to_delay(self):
        """Correction H3: 96-hour estimate is reported as metadata, not applied to change individual outcomes."""
        event = {
            "event_id": "TEST-022-DUR",
            "disruption_type": "PORT_CLOSURE",
            "affected_region": "Eastern Asia",
            "severity": "CRITICAL",
            "delay_estimate_hours": 96.0
        }
        records, summary = self.engine.propagate_shockwave(event)
        scen = summary["delay_projections"]["scenario_projection"]
        self.assertEqual(scen["event_delay_estimate_hours"], 96.0)
        self.assertFalse(scen["event_delay_estimate_applied_to_orders"])

    def test_empty_eligible_cohort(self):
        """Edge Case: If all orders in cohort are canceled, eligible count is 0 and no crash occurs."""
        G_empty = nx.DiGraph()
        G_empty.add_node("REG_Test", node_type="Region", label="Test Region")
        G_empty.add_node("ORD_C1", node_type="Order", label="ORD_C1", total_spend=100.0, order_status="CANCELED", delivery_status="Shipping canceled")
        G_empty.add_edge("ORD_C1", "REG_Test", relationship="DELIVERS_TO")
        
        test_engine = ShockwaveEngine()
        test_engine.set_graph(G_empty)

        event = {
            "event_id": "TEST-023-EMPTY-ELIG",
            "disruption_type": "PORT_CLOSURE",
            "affected_region": "Test Region",
            "severity": "CRITICAL",
            "capacity_reduction_pct": 100.0
        }
        records, summary = test_engine.propagate_shockwave(event)
        deliv = summary["delay_projections"]["order_cohort_breakdown"]
        self.assertEqual(deliv["total_affected_orders"], 1)
        self.assertEqual(deliv["eligible_orders_for_delay"], 0)
        self.assertEqual(deliv["ineligible_orders_excluded"], 1)
        self.assertEqual(summary["delay_projections"]["scenario_projection"]["scenario_newly_assumed_delayed_orders"], 0)


if __name__ == "__main__":
    unittest.main()

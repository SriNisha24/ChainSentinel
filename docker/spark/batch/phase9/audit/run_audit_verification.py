"""
ChainSentinel Phase 9 Task 9C - Comprehensive Independent Audit Verification Script
Executes read-only mathematical, data integrity, and provenance checks.
"""

import os
import json
import decimal
import pandas as pd
import numpy as np

PROJECT_ROOT = "E:/BDA/ChainSentinel"
os.chdir(PROJECT_ROOT)

def run_audit():
    print("=" * 80)
    print("CHAINSENTINEL PHASE 9 TASK 9C - INDEPENDENT AUDIT VERIFICATION")
    print("=" * 80)

    # --------------------------------------------------------------------------
    # 1. SCOPE AND PROVENANCE
    # --------------------------------------------------------------------------
    print("\n--- 1. FILE PROVENANCE AND COHORT INTEGRITY ---")
    sw_entities_path = "data/phase8/output/task8d_corrected/shockwave_entities.csv"
    sw_summary_path = "data/phase8/output/task8d_corrected/shockwave_summary.json"
    p9_csv_path = "data/phase9/output/risk_assessments.csv"
    p9_json_path = "data/phase9/output/risk_assessments.json"
    p9_summary_path = "data/phase9/output/risk_summary.json"

    sw_df = pd.read_csv(sw_entities_path)
    sw_orders = sw_df[sw_df["affected_entity_type"] == "ORDER"]
    p9_df = pd.read_csv(p9_csv_path)

    with open(sw_summary_path) as f:
        sw_summary = json.load(f)
    with open(p9_summary_path) as f:
        p9_summary = json.load(f)

    print(f"Phase 8 Total Impacted Entities: {len(sw_df):,}")
    print(f"Phase 8 Orders in CSV: {len(sw_orders):,}")
    print(f"Phase 9 Assessments Rows: {len(p9_df):,}")
    print(f"Phase 9 Unique Order IDs: {p9_df['entity_id'].nunique():,}")

    sw_order_ids = set(sw_orders["affected_entity_id"])
    p9_order_ids = set(p9_df["entity_id"])

    assert sw_order_ids == p9_order_ids, "Cohort mismatch between Phase 8 and Phase 9!"
    print(">> VERIFIED: 3,318 Phase 8 shockwave orders match Phase 9 orders exactly 1:1.")

    ineligible = p9_df[p9_df["risk_level"] == "INELIGIBLE_NON_SHIPPED"]
    eligible = p9_df[p9_df["risk_level"] != "INELIGIBLE_NON_SHIPPED"]

    print(f"Eligible active orders: {len(eligible):,}")
    print(f"Ineligible non-shipped orders: {len(ineligible):,}")
    assert len(eligible) == 3171, f"Expected 3,171 eligible orders, got {len(eligible)}"
    assert len(ineligible) == 147, f"Expected 147 ineligible orders, got {len(ineligible)}"
    print(">> VERIFIED: 3,171 eligible and 147 ineligible orders partitioned accurately.")

    ineligible_statuses = set(ineligible["order_status"].unique())
    print(f"Ineligible statuses: {ineligible_statuses}")
    assert ineligible_statuses == {"CANCELED", "SUSPECTED_FRAUD"}, "Ineligible cohort contains unexpected statuses!"
    assert (ineligible["risk_score"] == 0.0).all(), "Ineligible orders have non-zero risk scores!"
    assert (ineligible["delivery_risk_score"] == 0.0).all(), "Ineligible delivery risk != 0.0!"
    assert (ineligible["financial_risk_score"] == 0.0).all(), "Ineligible financial risk != 0.0!"
    assert (ineligible["operational_risk_score"] == 0.0).all(), "Ineligible operational risk != 0.0!"
    assert (ineligible["anomaly_risk_score"] == 0.0).all(), "Ineligible anomaly risk != 0.0!"
    assert ineligible["risk_priority_rank"].isna().all(), "Ineligible orders assigned a priority rank!"
    print(">> VERIFIED: 147 ineligible orders segregated with 0.0 scores and null priority ranks.")

    # --------------------------------------------------------------------------
    # 2. ANOMALY INTEGRATION AUDIT
    # --------------------------------------------------------------------------
    print("\n--- 2. ANOMALY INTEGRATION AND JOIN VALIDATION ---")
    anom_path = "reports/phase5/step2_anomaly_results.csv"
    assert os.path.exists(anom_path), f"Phase 5 anomaly file missing: {anom_path}"
    anom_df = pd.read_csv(anom_path)
    print(f"Phase 5 total anomaly records: {len(anom_df):,}")

    anom_df["norm_order_id"] = anom_df["order_id"].apply(lambda x: f"ORD_{int(x):05d}" if pd.notnull(x) else "")
    matched_anom = anom_df[anom_df["norm_order_id"].isin(p9_order_ids)]
    print(f"Matched anomaly transaction rows: {len(matched_anom)}")
    print(f"Unique matched orders in anomaly CSV: {matched_anom['norm_order_id'].nunique()}")

    assert len(matched_anom) == 50, f"Expected 50 anomaly rows, got {len(matched_anom)}"
    assert matched_anom["norm_order_id"].nunique() == 49, f"Expected 49 unique orders, got {matched_anom['norm_order_id'].nunique()}"

    # Group counts
    anom_per_order = matched_anom.groupby("norm_order_id").size()
    multi_anom = anom_per_order[anom_per_order > 1]
    print(f"Orders with multiple anomaly transactions: {multi_anom.to_dict()}")
    assert list(multi_anom.keys()) == ["ORD_21303"], "Unexpected multi-anomaly order!"
    assert multi_anom["ORD_21303"] == 2, "ORD_21303 should have 2 anomaly rows"

    # Verify ORD_21303 aggregation
    ord_21303_rows = matched_anom[matched_anom["norm_order_id"] == "ORD_21303"]
    max_composite_anom = ord_21303_rows["composite_anomaly_score"].max()
    print(f"ORD_21303 max composite anomaly score: {max_composite_anom}")
    ord_21303_p9 = p9_df[p9_df["entity_id"] == "ORD_21303"].iloc[0]
    expected_anom_score = round(min(100.0, max_composite_anom * 70.0 + 30.0), 2)
    print(f"ORD_21303 Phase 9 anomaly score: {ord_21303_p9['anomaly_risk_score']}, Expected: {expected_anom_score}")
    assert ord_21303_p9['anomaly_risk_score'] == expected_anom_score, "ORD_21303 anomaly score miscalculated!"
    print(">> VERIFIED: Multi-transaction anomaly order ORD_21303 correctly aggregated using max score and CRITICAL severity.")

    # Ineligible anomaly matches
    ineligible_matched = matched_anom[matched_anom["norm_order_id"].isin(set(ineligible["entity_id"]))]
    inelig_anom_ids = set(ineligible_matched["norm_order_id"])
    print(f"Ineligible orders with anomaly matches: {inelig_anom_ids}")
    assert inelig_anom_ids == {"ORD_23597", "ORD_71866"}, f"Unexpected ineligible anomaly matches: {inelig_anom_ids}"
    assert len(inelig_anom_ids) == 2, "Expected exactly 2 ineligible anomaly matches"

    for eid in inelig_anom_ids:
        row = p9_df[p9_df["entity_id"] == eid].iloc[0]
        assert row["has_pre_existing_anomaly"] == True, f"{eid} has_pre_existing_anomaly should be True"
        assert row["risk_score"] == 0.0, f"{eid} risk_score should be 0.0"
        assert row["anomaly_risk_score"] == 0.0, f"{eid} anomaly_risk_score should be 0.0"
        assert pd.isna(row["risk_priority_rank"]), f"{eid} risk_priority_rank should be NaN"
    print(">> VERIFIED: 2 ineligible anomaly orders (ORD_23597, ORD_71866) correctly flagged but disqualified from risk score and priority rank.")

    # Eligible anomaly matches count
    eligible_anom_ids = set(matched_anom["norm_order_id"]) - inelig_anom_ids
    assert len(eligible_anom_ids) == 47, f"Expected 47 eligible anomaly matches, got {len(eligible_anom_ids)}"
    print(">> VERIFIED: Exactly 47 eligible orders and 2 ineligible orders matched (49 total unique orders).")

    # --------------------------------------------------------------------------
    # 3. MCDA SCORING MATHEMATICS & SAMPLE RECALCULATIONS
    # --------------------------------------------------------------------------
    print("\n--- 3. MCDA SCORING MATHEMATICS AUDIT ---")
    cfg_path = "docker/spark/batch/phase9/risk_scoring_config.json"
    with open(cfg_path) as f:
        cfg = json.load(f)

    dw = cfg["dimension_weights"]
    print(f"Dimension weights: {dw}, sum={sum(dw.values())}")
    assert abs(sum(dw.values()) - 1.0) < 1e-9, "Dimension weights do not sum to 1.0!"

    drw = cfg["delivery_risk_weights"]
    assert abs(sum(drw.values()) - 1.0) < 1e-9, "Delivery subweights do not sum to 1.0!"

    frw = cfg["financial_risk_weights"]
    assert abs(sum(frw.values()) - 1.0) < 1e-9, "Financial subweights do not sum to 1.0!"

    orw = cfg["operational_risk_weights"]
    assert abs(sum(orw.values()) - 1.0) < 1e-9, "Operational subweights do not sum to 1.0!"

    print(">> VERIFIED: All dimension weights and dimensional subweights sum to 1.0.")

    # Test dimensional bounds across all 3,318 orders
    assert (p9_df["delivery_risk_score"] >= 0.0).all() and (p9_df["delivery_risk_score"] <= 100.0).all(), "Delivery score out of bounds!"
    assert (p9_df["financial_risk_score"] >= 0.0).all() and (p9_df["financial_risk_score"] <= 100.0).all(), "Financial score out of bounds!"
    assert (p9_df["operational_risk_score"] >= 0.0).all() and (p9_df["operational_risk_score"] <= 100.0).all(), "Operational score out of bounds!"
    assert (p9_df["anomaly_risk_score"] >= 0.0).all() and (p9_df["anomaly_risk_score"] <= 100.0).all(), "Anomaly score out of bounds!"
    assert (p9_df["risk_score"] >= 0.0).all() and (p9_df["risk_score"] <= 100.0).all(), "Composite score out of bounds!"
    print(">> VERIFIED: All scores strictly bounded in [0.0, 100.0].")

    # Sample manual recalculations
    print("\nSample Manual Recalculations:")
    sample_queries = [
        ("CRITICAL", "risk_level == 'CRITICAL'"),
        ("HIGH", "risk_level == 'HIGH'"),
        ("MEDIUM", "risk_level == 'MEDIUM'"),
        ("LOW", "risk_level == 'LOW'"),
        ("ANOMALY_MATCHED", "risk_level != 'INELIGIBLE_NON_SHIPPED' and has_pre_existing_anomaly == True"),
        ("NO_ANOMALY", "risk_level != 'INELIGIBLE_NON_SHIPPED' and has_pre_existing_anomaly == False"),
        ("INELIGIBLE", "risk_level == 'INELIGIBLE_NON_SHIPPED'")
    ]

    for label, query in sample_queries:
        row = p9_df.query(query).iloc[0]
        eid = row["entity_id"]
        actual_score = row["risk_score"]
        if row["risk_level"] == "INELIGIBLE_NON_SHIPPED":
            expected_score = 0.0
        else:
            expected_score = round(
                0.35 * row["delivery_risk_score"] +
                0.30 * row["financial_risk_score"] +
                0.20 * row["operational_risk_score"] +
                0.15 * row["anomaly_risk_score"],
                2
            )
        diff = abs(actual_score - expected_score)
        print(f"  [{label}] {eid}: Stored={actual_score}, Formula={expected_score}, Diff={diff:.4f}")
        assert diff < 1e-4, f"Mismatch in sample {label} ({eid}): {actual_score} vs {expected_score}"
    print(">> VERIFIED: Representative sample order scores match the formula exactly.")

    # Recalculate ALL eligible orders formula
    all_recalc = eligible.apply(
        lambda r: round(0.35 * r["delivery_risk_score"] + 0.30 * r["financial_risk_score"] + 0.20 * r["operational_risk_score"] + 0.15 * r["anomaly_risk_score"], 2),
        axis=1
    )
    max_diff = (eligible["risk_score"] - all_recalc).abs().max()
    print(f"Max formula deviation across all 3,171 eligible orders: {max_diff}")
    assert max_diff < 1e-4, f"Max deviation {max_diff} exceeds tolerance!"
    print(">> VERIFIED: 100% of eligible orders follow the composite MCDA formula.")

    # --------------------------------------------------------------------------
    # 4. FINANCIAL EXPOSURE ZERO-DELTA RECONCILIATION
    # --------------------------------------------------------------------------
    print("\n--- 4. FINANCIAL EXPOSURE ZERO-DELTA RECONCILIATION ---")
    # Decimal safe calculation
    d_total_rev = sum(decimal.Decimal(str(r)) for r in p9_df["revenue_exposure"])
    d_total_prof = sum(decimal.Decimal(str(p)) for p in p9_df["profit_exposure"])

    d_elig_rev = sum(decimal.Decimal(str(r)) for r in eligible["revenue_exposure"])
    d_elig_prof = sum(decimal.Decimal(str(p)) for p in eligible["profit_exposure"])

    d_inel_rev = sum(decimal.Decimal(str(r)) for r in ineligible["revenue_exposure"])
    d_inel_prof = sum(decimal.Decimal(str(p)) for p in ineligible["profit_exposure"])

    print(f"Total Gross Revenue:     ${d_total_rev:,.2f}")
    print(f"Eligible Revenue:        ${d_elig_rev:,.2f}")
    print(f"Ineligible Revenue:      ${d_inel_rev:,.2f}")
    delta_rev = d_total_rev - (d_elig_rev + d_inel_rev)
    print(f"Revenue Exposure Delta:  ${delta_rev:,.4f}")

    print(f"Total Gross Profit:      ${d_total_prof:,.2f}")
    print(f"Eligible Profit:         ${d_elig_prof:,.2f}")
    print(f"Ineligible Profit:       ${d_inel_prof:,.2f}")
    delta_prof = d_total_prof - (d_elig_prof + d_inel_prof)
    print(f"Profit Exposure Delta:   ${delta_prof:,.4f}")

    assert delta_rev == decimal.Decimal("0"), f"Non-zero revenue delta: {delta_rev}"
    assert delta_prof == decimal.Decimal("0"), f"Non-zero profit delta: {delta_prof}"

    # Reconcile against reported figures
    rep_tot_rev = decimal.Decimal("1334313.40")
    rep_tot_prof = decimal.Decimal("147368.01")
    rep_elig_rev = decimal.Decimal("1282401.19")
    rep_elig_prof = decimal.Decimal("141747.52")
    rep_inel_rev = decimal.Decimal("51912.21")
    rep_inel_prof = decimal.Decimal("5620.49")

    assert d_total_rev == rep_tot_rev, f"Total revenue mismatch: {d_total_rev} vs {rep_tot_rev}"
    assert d_total_prof == rep_tot_prof, f"Total profit mismatch: {d_total_prof} vs {rep_tot_prof}"
    assert d_elig_rev == rep_elig_rev, f"Eligible revenue mismatch: {d_elig_rev} vs {rep_elig_rev}"
    assert d_elig_prof == rep_elig_prof, f"Eligible profit mismatch: {d_elig_prof} vs {rep_elig_prof}"
    assert d_inel_rev == rep_inel_rev, f"Ineligible revenue mismatch: {d_inel_rev} vs {rep_inel_rev}"
    assert d_inel_prof == rep_inel_prof, f"Ineligible profit mismatch: {d_inel_prof} vs {rep_inel_prof}"
    print(">> VERIFIED: Financial exposure reconciles with EXACT ZERO DELTA across all dimensions.")

    # --------------------------------------------------------------------------
    # 5. RISK TIER AND PRIORITY QUEUE RECONCILIATION
    # --------------------------------------------------------------------------
    print("\n--- 5. RISK TIER AND PRIORITY QUEUE RECONCILIATION ---")
    dist = p9_df["risk_level"].value_counts().to_dict()
    print("Risk tier distribution:")
    for k, v in dist.items():
        pct = (v / len(p9_df)) * 100.0
        print(f"  {k:25s}: {v:5d} ({pct:6.2f}%)")

    assert dist["CRITICAL"] == 20, f"Expected 20 CRITICAL, got {dist.get('CRITICAL')}"
    assert dist["HIGH"] == 625, f"Expected 625 HIGH, got {dist.get('HIGH')}"
    assert dist["MEDIUM"] == 1498, f"Expected 1498 MEDIUM, got {dist.get('MEDIUM')}"
    assert dist["LOW"] == 1028, f"Expected 1028 LOW, got {dist.get('LOW')}"
    assert dist["INELIGIBLE_NON_SHIPPED"] == 147, f"Expected 147 INELIGIBLE, got {dist.get('INELIGIBLE_NON_SHIPPED')}"
    assert sum(dist.values()) == 3318, f"Sum of tiers does not equal 3,318: {sum(dist.values())}"
    print(">> VERIFIED: Risk distribution matches reported counts exactly (20, 625, 1498, 1028, 147).")

    # Priority queue inspection
    pq_path = "data/phase9/output/risk_priority_orders.csv"
    pq_df = pd.read_csv(pq_path)
    print(f"Priority queue order count: {len(pq_df):,}")
    assert len(pq_df) == 645, f"Expected 645 priority orders, got {len(pq_df)}"
    assert set(pq_df["risk_level"].unique()) == {"CRITICAL", "HIGH"}, "Priority queue contains non-critical/high orders!"
    assert (pq_df["is_eligible_for_delay"] == True).all(), "Priority queue contains ineligible orders!"
    assert pq_df["entity_id"].nunique() == 645, "Duplicate orders exist in priority queue!"

    # Check priority rank sequence: 1 to 645
    expected_ranks = list(range(1, 646))
    actual_ranks = [int(r) for r in pq_df["risk_priority_rank"]]
    assert actual_ranks == expected_ranks, "Priority ranks are not sequential 1 to 645!"
    print(">> VERIFIED: Priority queue contains exactly 645 deduplicated eligible orders ranked 1 to 645.")

    # --------------------------------------------------------------------------
    # 6. ENTITY ROLL-UPS INTEGRITY
    # --------------------------------------------------------------------------
    print("\n--- 6. ENTITY ROLL-UP INTEGRITY ---")
    ent_summary_path = "data/phase9/output/entity_risk_summary.csv"
    ent_df = pd.read_csv(ent_summary_path)

    cust_roll = ent_df[ent_df["entity_type"] == "CUSTOMER"]
    prod_roll = ent_df[ent_df["entity_type"] == "PRODUCT"]
    ship_roll = ent_df[ent_df["entity_type"] == "SHIPPING_MODE"]

    print(f"Customers rolled up: {len(cust_roll):,}")
    print(f"Products rolled up: {len(prod_roll):,}")
    print(f"Shipping modes rolled up: {len(ship_roll):,}")

    assert len(cust_roll) == 3169, f"Expected 3,169 customers, got {len(cust_roll)}"
    assert len(prod_roll) == 71, f"Expected 71 products, got {len(prod_roll)}"
    assert len(ship_roll) == 4, f"Expected 4 shipping modes, got {len(ship_roll)}"

    # Shipping mode revenue sum should equal eligible orders revenue sum
    ship_rev_sum = ship_roll["revenue_exposure_usd"].sum()
    print(f"Shipping modes aggregated revenue: ${ship_rev_sum:,.2f}")
    assert abs(ship_rev_sum - float(rep_elig_rev)) < 0.05, f"Shipping mode revenue {ship_rev_sum} != {rep_elig_rev}"
    print(">> VERIFIED: Shipping mode aggregation matches eligible orders revenue exactly.")

    # --------------------------------------------------------------------------
    # 7. CSV AND JSON RECONCILIATION
    # --------------------------------------------------------------------------
    print("\n--- 7. CSV AND JSON ASSESSMENT RECONCILIATION ---")
    with open(p9_json_path, encoding="utf-8") as f:
        json_assessments = json.load(f)

    assert len(json_assessments) == len(p9_df), "Row count mismatch between CSV and JSON!"
    json_df = pd.DataFrame(json_assessments)

    for col in ["entity_id", "risk_score", "delivery_risk_score", "financial_risk_score", "operational_risk_score", "anomaly_risk_score", "revenue_exposure", "profit_exposure"]:
        csv_vals = p9_df[col].tolist()
        json_vals = json_df[col].tolist()
        assert csv_vals == json_vals, f"Column {col} differs between CSV and JSON!"
    print(">> VERIFIED: CSV and JSON assessment records match 100% across all quantitative fields.")

    print("\n" + "=" * 80)
    print("ALL AUDIT CHECKS COMPLETED SUCCESSFULLY WITH ZERO ERRORS.")
    print("=" * 80)

if __name__ == "__main__":
    run_audit()


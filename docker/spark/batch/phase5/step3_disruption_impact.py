"""
ChainSentinel - Phase 5: Machine Learning and Predictive Analytics
Model 3: Disruption Impact Feasibility and Scenario-Based Impact Estimation

Executes what-if scenario simulations over the DataCo supply chain dataset to quantify
operational and financial exposure under controlled hypothetical disruptions:
  - Regional port / customs logjams
  - Express airfreight freezes
  - Trans-Pacific container shortages
  - Systemic carrier capacity crunches

Calculates distinct order-level and item-level impacts, revenue/profit exposure,
simulated transit delay shocks, regional and shipping mode breakdowns, and severity grading.
"""

import os
import sys
import time
import json
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, StringType, IntegerType
)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase5_Model3_DisruptionImpact")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
CONFIG_FILE = "/opt/spark-data/phase5_models/disruption_impact_v1/scenario_config.json"
OUTPUT_DIR = "/opt/spark-data/phase5_output"
LOCAL_MODEL_DIR = "/opt/spark-data/phase5_models/disruption_impact_v1"
HDFS_MODEL_DIR = "hdfs://namenode:8020/chainsentinel/models/phase5/disruption_impact_v1"


def assign_severity(revenue_exposure, impacted_orders, delay_rate_increase_pct):
    """Assigns operational severity based on transparent multi-criteria thresholds."""
    if revenue_exposure >= 10000000.0 or impacted_orders >= 20000 or delay_rate_increase_pct >= 25.0:
        return "CRITICAL"
    elif revenue_exposure >= 5000000.0 or impacted_orders >= 10000 or delay_rate_increase_pct >= 15.0:
        return "HIGH"
    elif revenue_exposure >= 1500000.0 or impacted_orders >= 3000 or delay_rate_increase_pct >= 5.0:
        return "MEDIUM"
    else:
        return "LOW"


def run_pipeline():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)

    spark = SparkSession.builder \
        .appName("ChainSentinel-Phase5-Model3-DisruptionImpact") \
        .config("spark.sql.shuffle.partitions", "8") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading cleaned dataset from: {HDFS_DATASET}")
    df = spark.read.parquet(HDFS_DATASET)
    total_records = df.count()
    logger.info(f"Total dataset records: {total_records:,}")

    # Load Scenario Configuration
    logger.info(f"Loading scenario configuration from: {CONFIG_FILE}")
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    scenarios = config["disruption_scenarios"]

    # 1. BASELINE OPERATIONAL & FINANCIAL AUDIT
    # Filter completed shipments for delay simulation (excluding canceled shipments)
    clean_df = df.filter(F.col("delivery_status") != "Shipping canceled")
    valid_items = clean_df.count()
    valid_orders = clean_df.select("order_id").distinct().count()

    total_revenue_baseline = clean_df.select(F.round(F.sum("order_item_total"), 2)).first()[0]
    total_profit_baseline = clean_df.select(F.round(F.sum("order_profit_per_order"), 2)).first()[0]

    baseline_delayed_items = clean_df.filter(F.col("is_delayed") == 1).count()
    baseline_delayed_orders = clean_df.filter(F.col("is_delayed") == 1).select("order_id").distinct().count()

    baseline_item_delay_rate = round(baseline_delayed_items / valid_items * 100, 2)
    baseline_order_delay_rate = round(baseline_delayed_orders / valid_orders * 100, 2)

    logger.info(f"Baseline: Valid Orders={valid_orders:,}, Items={valid_items:,}, Delayed Orders={baseline_delayed_orders:,} ({baseline_order_delay_rate}%), Revenue=${total_revenue_baseline:,.2f}")

    # 2. EXECUTE SCENARIO SIMULATIONS
    scenario_comparison_records = []
    regional_impact_records = []
    shipping_mode_impact_records = []

    for sc in scenarios:
        sc_id = sc["scenario_id"]
        sc_name = sc["name"]
        sc_cat = sc["category"]
        params = sc["parameters"]

        target_markets = params["target_markets"]
        target_regions = params["target_regions"]
        target_modes = params["target_shipping_modes"]
        delay_shock = float(params["delay_shock_days"])
        capacity_reduction_pct = float(params["capacity_reduction_pct"])

        logger.info(f"\n--- Simulating Scenario: {sc_name} (Shock: +{delay_shock} days, Capacity: -{capacity_reduction_pct}%) ---")

        # Build filter condition for in-scope shipments
        cond = (F.col("market").isin(target_markets)) & (F.col("shipping_mode").isin(target_modes))
        if target_regions and len(target_regions) > 0:
            cond = cond & (F.col("order_region").isin(target_regions))

        in_scope_df = clean_df.filter(cond)
        in_scope_items = in_scope_df.count()
        in_scope_orders = in_scope_df.select("order_id").distinct().count()

        if in_scope_items == 0:
            logger.warning(f"Scenario {sc_id} matched 0 records! Skipping...")
            continue

        # In-scope Financial Exposure (Distinct order level aggregation)
        revenue_exposure = round(float(in_scope_df.select(F.sum("order_item_total")).first()[0] or 0.0), 2)
        profit_exposure = round(float(in_scope_df.select(F.sum("order_profit_per_order")).first()[0] or 0.0), 2)

        # Baseline in-scope delay
        in_scope_base_delayed_orders = in_scope_df.filter(F.col("is_delayed") == 1).select("order_id").distinct().count()
        in_scope_base_delay_rate = round(in_scope_base_delayed_orders / in_scope_orders * 100, 2)

        # Simulate Transit Delay Shock
        # New simulated real shipping days = days_for_shipping_real + delay_shock
        # Delayed if simulated_real_days > days_for_shipment_scheduled
        simulated_df = in_scope_df.withColumn(
            "simulated_shipping_days",
            F.col("days_for_shipping_real") + F.lit(delay_shock)
        ).withColumn(
            "scenario_is_delayed",
            F.when(F.col("simulated_shipping_days") > F.col("days_for_shipment_scheduled"), 1).otherwise(0)
        )

        scenario_delayed_orders = simulated_df.filter(F.col("scenario_is_delayed") == 1).select("order_id").distinct().count()
        scenario_delay_rate = round(scenario_delayed_orders / in_scope_orders * 100, 2)
        newly_delayed_orders = scenario_delayed_orders - in_scope_base_delayed_orders
        delay_rate_increase = round(scenario_delay_rate - in_scope_base_delay_rate, 2)

        # Capacity Bottleneck Stranded Orders
        stranded_orders = int(round(in_scope_orders * (capacity_reduction_pct / 100.0)))
        stranded_revenue = round(revenue_exposure * (capacity_reduction_pct / 100.0), 2)

        # Global Network Repercussion
        global_scenario_delayed_orders = (valid_orders - in_scope_orders) + scenario_delayed_orders
        global_adjusted_delayed_orders = baseline_delayed_orders + newly_delayed_orders
        global_scenario_delay_rate = round(global_adjusted_delayed_orders / valid_orders * 100, 2)

        # Severity
        severity = assign_severity(revenue_exposure, in_scope_orders, delay_rate_increase)

        logger.info(f"[{sc_id}] Scope: {in_scope_orders:,} orders ({in_scope_items:,} items)")
        logger.info(f"[{sc_id}] Financial Exposure: Revenue=${revenue_exposure:,.2f}, Profit=${profit_exposure:,.2f}")
        logger.info(f"[{sc_id}] Delay Impact: In-Scope Baseline={in_scope_base_delay_rate}% -> Scenario={scenario_delay_rate}% (+{delay_rate_increase}%)")
        logger.info(f"[{sc_id}] Newly Delayed Orders: +{newly_delayed_orders:,} orders | Stranded Orders: {stranded_orders:,}")
        logger.info(f"[{sc_id}] Assigned Severity: {severity}")

        scenario_comparison_records.append({
            "scenario_id": sc_id,
            "scenario_name": sc_name,
            "category": sc_cat,
            "impacted_orders": in_scope_orders,
            "impacted_order_items": in_scope_items,
            "revenue_exposure": revenue_exposure,
            "profit_exposure": profit_exposure,
            "baseline_in_scope_delay_rate": in_scope_base_delay_rate,
            "scenario_delay_rate": scenario_delay_rate,
            "delay_rate_increase_pct": delay_rate_increase,
            "newly_delayed_orders": newly_delayed_orders,
            "stranded_orders": stranded_orders,
            "stranded_revenue": stranded_revenue,
            "global_delay_rate": global_scenario_delay_rate,
            "severity": severity
        })

        # Regional Impact Breakdown
        reg_agg = simulated_df.groupBy("market", "order_region").agg(
            F.countDistinct("order_id").alias("reg_orders"),
            F.count("*").alias("reg_items"),
            F.round(F.sum("order_item_total"), 2).alias("reg_revenue"),
            F.round(F.sum("order_profit_per_order"), 2).alias("reg_profit"),
            F.sum("is_delayed").alias("reg_base_delayed_items"),
            F.sum("scenario_is_delayed").alias("reg_scen_delayed_items")
        ).collect()

        for r in reg_agg:
            base_r_rate = round(r["reg_base_delayed_items"] / r["reg_items"] * 100, 2)
            scen_r_rate = round(r["reg_scen_delayed_items"] / r["reg_items"] * 100, 2)
            regional_impact_records.append({
                "scenario_id": sc_id,
                "market": r["market"],
                "order_region": r["order_region"],
                "orders": r["reg_orders"],
                "order_items": r["reg_items"],
                "revenue_exposure": float(r["reg_revenue"] or 0.0),
                "profit_exposure": float(r["reg_profit"] or 0.0),
                "baseline_delay_rate": base_r_rate,
                "scenario_delay_rate": scen_r_rate,
                "delay_rate_increase": round(scen_r_rate - base_r_rate, 2)
            })

        # Shipping Mode Impact Breakdown
        mode_agg = simulated_df.groupBy("shipping_mode").agg(
            F.countDistinct("order_id").alias("mode_orders"),
            F.count("*").alias("mode_items"),
            F.round(F.sum("order_item_total"), 2).alias("mode_revenue"),
            F.round(F.sum("order_profit_per_order"), 2).alias("mode_profit"),
            F.sum("is_delayed").alias("mode_base_delayed_items"),
            F.sum("scenario_is_delayed").alias("mode_scen_delayed_items")
        ).collect()

        for m in mode_agg:
            base_m_rate = round(m["mode_base_delayed_items"] / m["mode_items"] * 100, 2)
            scen_m_rate = round(m["mode_scen_delayed_items"] / m["mode_items"] * 100, 2)
            shipping_mode_impact_records.append({
                "scenario_id": sc_id,
                "shipping_mode": m["shipping_mode"],
                "orders": m["mode_orders"],
                "order_items": m["mode_items"],
                "revenue_exposure": float(m["mode_revenue"] or 0.0),
                "profit_exposure": float(m["mode_profit"] or 0.0),
                "baseline_delay_rate": base_m_rate,
                "scenario_delay_rate": scen_m_rate,
                "delay_rate_increase": round(scen_m_rate - base_m_rate, 2)
            })

    # 3. EXPORT CSV DELIVERABLES
    logger.info("Exporting CSV deliverables...")

    # CSV 1: Scenario Comparison
    csv_comp_path = os.path.join(OUTPUT_DIR, "step3_scenario_comparison.csv")
    with open(csv_comp_path, "w", encoding="utf-8") as f:
        headers = [
            "scenario_id", "scenario_name", "category", "impacted_orders",
            "impacted_order_items", "revenue_exposure", "profit_exposure",
            "baseline_in_scope_delay_rate", "scenario_delay_rate",
            "delay_rate_increase_pct", "newly_delayed_orders",
            "stranded_orders", "stranded_revenue", "global_delay_rate", "severity"
        ]
        f.write(",".join(headers) + "\n")
        for sc in scenario_comparison_records:
            f.write(f"\"{sc['scenario_id']}\",\"{sc['scenario_name']}\",\"{sc['category']}\",{sc['impacted_orders']},{sc['impacted_order_items']},{sc['revenue_exposure']},{sc['profit_exposure']},{sc['baseline_in_scope_delay_rate']},{sc['scenario_delay_rate']},{sc['delay_rate_increase_pct']},{sc['newly_delayed_orders']},{sc['stranded_orders']},{sc['stranded_revenue']},{sc['global_delay_rate']},\"{sc['severity']}\"\n")

    # CSV 2: Regional Impact
    csv_reg_path = os.path.join(OUTPUT_DIR, "step3_regional_impact.csv")
    with open(csv_reg_path, "w", encoding="utf-8") as f:
        headers = ["scenario_id", "market", "order_region", "orders", "order_items", "revenue_exposure", "profit_exposure", "baseline_delay_rate", "scenario_delay_rate", "delay_rate_increase"]
        f.write(",".join(headers) + "\n")
        for r in regional_impact_records:
            f.write(f"\"{r['scenario_id']}\",\"{r['market']}\",\"{r['order_region']}\",{r['orders']},{r['order_items']},{r['revenue_exposure']},{r['profit_exposure']},{r['baseline_delay_rate']},{r['scenario_delay_rate']},{r['delay_rate_increase']}\n")

    # CSV 3: Shipping Mode Impact
    csv_mode_path = os.path.join(OUTPUT_DIR, "step3_shipping_mode_impact.csv")
    with open(csv_mode_path, "w", encoding="utf-8") as f:
        headers = ["scenario_id", "shipping_mode", "orders", "order_items", "revenue_exposure", "profit_exposure", "baseline_delay_rate", "scenario_delay_rate", "delay_rate_increase"]
        f.write(",".join(headers) + "\n")
        for m in shipping_mode_impact_records:
            f.write(f"\"{m['scenario_id']}\",\"{m['shipping_mode']}\",{m['orders']},{m['order_items']},{m['revenue_exposure']},{m['profit_exposure']},{m['baseline_delay_rate']},{m['scenario_delay_rate']},{m['delay_rate_increase']}\n")

    # JSON Summary Payload
    summary_payload = {
        "step": 3,
        "task": "Model 3: Disruption Impact Feasibility & Scenario-Based Impact Estimation",
        "feasibility_status": "Direct ML prediction unsupported; Scenario-based Shockwave Engine fully implemented",
        "baseline": {
            "total_completed_orders": valid_orders,
            "total_completed_order_items": valid_items,
            "baseline_delayed_orders": baseline_delayed_orders,
            "baseline_order_delay_rate_pct": baseline_order_delay_rate,
            "total_revenue_baseline": total_revenue_baseline,
            "total_profit_baseline": total_profit_baseline
        },
        "scenarios_evaluated": scenario_comparison_records,
        "top_regional_impacts": sorted(regional_impact_records, key=lambda x: x["revenue_exposure"], reverse=True)[:10],
        "shipping_mode_impacts": shipping_mode_impact_records
    }

    json_path = os.path.join(OUTPUT_DIR, "step3_impact_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    logger.info("Model 3 scenario execution, impact calculation, and deliverable export complete.")
    spark.stop()


if __name__ == "__main__":
    run_pipeline()


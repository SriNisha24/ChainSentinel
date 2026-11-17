"""
ChainSentinel - Phase 3 EDA: Step 3
Delivery Delay and Shipping Mode Analysis

Analyzes overall disruption rate, delivery status distribution, delay rates
by shipping mode, scheduled vs actual transit metrics, canceled order treatment,
and temporal delay patterns across months and years.
"""

import os
import json
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase3_Step3")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
OUTPUT_DIR = "/opt/spark-data/eda_output"

def run_step3():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    spark = SparkSession.builder \
        .appName("ChainSentinel-EDA-Step3") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading HDFS Parquet dataset from {HDFS_DATASET}...")
    df = spark.read.parquet(HDFS_DATASET)
    total_records = df.count()

    # 1. Overall late delivery metrics
    late_count = df.filter(F.col("is_delayed") == 1).count()
    late_pct = round(late_count / total_records * 100, 2)
    logger.info(f"Overall Late Deliveries: {late_count} / {total_records} ({late_pct}%)")

    # 2. Delivery Status distribution
    status_df = df.groupBy("delivery_status").agg(
        F.count("*").alias("count"),
        F.sum("is_delayed").alias("delayed_count"),
        F.sum("is_canceled").alias("canceled_count")
    ).orderBy(F.desc("count"))
    status_rows = status_df.collect()

    status_list = []
    for r in status_rows:
        status_list.append({
            "delivery_status": r["delivery_status"],
            "count": int(r["count"]),
            "percentage": round(int(r["count"]) / total_records * 100, 2),
            "delayed_count": int(r["delayed_count"]),
            "delayed_percentage": round(int(r["delayed_count"]) / int(r["count"]) * 100, 2) if r["count"] > 0 else 0.0,
            "canceled_count": int(r["canceled_count"])
        })

    # Save delivery status CSV
    with open(os.path.join(OUTPUT_DIR, "step3_delivery_status.csv"), "w", encoding="utf-8") as f:
        f.write("delivery_status,count,percentage,delayed_count,delayed_percentage,canceled_count\n")
        for s in status_list:
            f.write(f"{s['delivery_status']},{s['count']},{s['percentage']},{s['delayed_count']},{s['delayed_percentage']},{s['canceled_count']}\n")

    # 3. Delay rates by Shipping Mode
    shipping_df = df.groupBy("shipping_mode").agg(
        F.count("*").alias("total_orders"),
        F.sum("is_delayed").alias("delayed_orders"),
        F.round(F.mean("days_for_shipment_scheduled"), 2).alias("avg_scheduled_days"),
        F.round(F.mean("days_for_shipping_real"), 2).alias("avg_real_days"),
        F.round(F.mean("transit_delay_days"), 2).alias("avg_delay_days"),
        F.round(F.mean("order_to_shipping_hours"), 2).alias("avg_order_to_ship_hours"),
        F.min("days_for_shipping_real").alias("min_real_days"),
        F.max("days_for_shipping_real").alias("max_real_days")
    ).orderBy(F.desc("total_orders"))
    shipping_rows = shipping_df.collect()

    shipping_list = []
    for r in shipping_rows:
        tot = int(r["total_orders"])
        dly = int(r["delayed_orders"])
        rate = round(dly / tot * 100, 2)
        shipping_list.append({
            "shipping_mode": r["shipping_mode"],
            "total_orders": tot,
            "delayed_orders": dly,
            "delay_rate_pct": rate,
            "avg_scheduled_days": float(r["avg_scheduled_days"]),
            "avg_real_days": float(r["avg_real_days"]),
            "avg_delay_days": float(r["avg_delay_days"]),
            "avg_order_to_ship_hours": float(r["avg_order_to_ship_hours"]),
            "min_real_days": int(r["min_real_days"]),
            "max_real_days": int(r["max_real_days"])
        })

    # Save shipping mode delays CSV
    with open(os.path.join(OUTPUT_DIR, "step3_shipping_mode_delays.csv"), "w", encoding="utf-8") as f:
        f.write("shipping_mode,total_orders,delayed_orders,delay_rate_pct,avg_scheduled_days,avg_real_days,avg_delay_days,avg_order_to_ship_hours,min_real_days,max_real_days\n")
        for s in shipping_list:
            f.write(f"{s['shipping_mode']},{s['total_orders']},{s['delayed_orders']},{s['delay_rate_pct']},{s['avg_scheduled_days']},{s['avg_real_days']},{s['avg_delay_days']},{s['avg_order_to_ship_hours']},{s['min_real_days']},{s['max_real_days']}\n")

    # 4. Scheduled vs Actual Shipping Days Cross-Tabulation
    crosstab_df = df.crosstab("days_for_shipment_scheduled", "days_for_shipping_real").orderBy("days_for_shipment_scheduled_days_for_shipping_real")
    crosstab_rows = [r.asDict() for r in crosstab_df.collect()]

    # 5. Canceled Shipments analysis
    canceled_df = df.filter(F.col("delivery_status") == "Shipping canceled")
    canceled_stats = canceled_df.select(
        F.count("*").alias("canceled_total"),
        F.sum("is_delayed").alias("canceled_marked_delayed"),
        F.sum(F.when(F.col("days_for_shipping_real") > F.col("days_for_shipment_scheduled"), 1).otherwise(0)).alias("canceled_exceeded_sla_count"),
        F.round(F.mean("days_for_shipping_real"), 2).alias("canceled_avg_real_days")
    ).collect()[0]

    canceled_summary = {
        "canceled_total": int(canceled_stats["canceled_total"]),
        "canceled_marked_delayed": int(canceled_stats["canceled_marked_delayed"]),
        "canceled_exceeded_sla_count": int(canceled_stats["canceled_exceeded_sla_count"]),
        "canceled_avg_real_days": float(canceled_stats["canceled_avg_real_days"])
    }

    # 6. Monthly & Yearly Delay Trends
    monthly_df = df.groupBy("order_year", "order_month").agg(
        F.count("*").alias("total_orders"),
        F.sum("is_delayed").alias("delayed_orders"),
        F.round(F.sum("is_delayed") / F.count("*") * 100, 2).alias("delay_rate_pct")
    ).orderBy("order_year", "order_month")
    monthly_rows = monthly_df.collect()

    monthly_list = []
    for r in monthly_rows:
        monthly_list.append({
            "order_year": int(r["order_year"]),
            "order_month": int(r["order_month"]),
            "total_orders": int(r["total_orders"]),
            "delayed_orders": int(r["delayed_orders"]),
            "delay_rate_pct": float(r["delay_rate_pct"])
        })

    # Save monthly delays CSV
    with open(os.path.join(OUTPUT_DIR, "step3_monthly_delays.csv"), "w", encoding="utf-8") as f:
        f.write("order_year,order_month,total_orders,delayed_orders,delay_rate_pct\n")
        for m in monthly_list:
            f.write(f"{m['order_year']},{m['order_month']},{m['total_orders']},{m['delayed_orders']},{m['delay_rate_pct']}\n")

    step3_summary = {
        "step": 3,
        "title": "Delivery Delay and Shipping Mode Analysis",
        "total_records": total_records,
        "overall_delayed_count": late_count,
        "overall_delay_rate_pct": late_pct,
        "delivery_status_distribution": status_list,
        "shipping_mode_delays": shipping_list,
        "scheduled_vs_actual_crosstab": crosstab_rows,
        "canceled_shipments_analysis": canceled_summary,
        "monthly_delay_trends": monthly_list
    }

    with open(os.path.join(OUTPUT_DIR, "step3_summary.json"), "w", encoding="utf-8") as f:
        json.dump(step3_summary, f, indent=2)

    logger.info("Step 3 successfully completed. Output written to eda_output.")
    spark.stop()

if __name__ == "__main__":
    run_step3()


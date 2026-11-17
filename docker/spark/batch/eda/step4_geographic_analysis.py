"""
ChainSentinel - Phase 3 EDA: Step 4
Geographic and Regional Analysis

Evaluates delivery performance and delay vulnerability across destination markets,
regions, and countries, as well as origin customer geography and coordinate distributions.
"""

import os
import json
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase3_Step4")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
OUTPUT_DIR = "/opt/spark-data/eda_output"

def run_step4():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    spark = SparkSession.builder \
        .appName("ChainSentinel-EDA-Step4") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading HDFS Parquet dataset from {HDFS_DATASET}...")
    df = spark.read.parquet(HDFS_DATASET)
    total_records = df.count()

    # 1. Performance by Market
    market_df = df.groupBy("market").agg(
        F.count("*").alias("total_orders"),
        F.sum("is_delayed").alias("delayed_orders"),
        F.round(F.sum("is_delayed") / F.count("*") * 100, 2).alias("delay_rate_pct"),
        F.round(F.sum("order_item_total"), 2).alias("total_sales"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.round(F.mean("transit_delay_days"), 2).alias("avg_delay_days")
    ).orderBy(F.desc("total_orders"))
    market_rows = market_df.collect()

    market_list = []
    for r in market_rows:
        market_list.append({
            "market": r["market"],
            "total_orders": int(r["total_orders"]),
            "delayed_orders": int(r["delayed_orders"]),
            "delay_rate_pct": float(r["delay_rate_pct"]),
            "total_sales": float(r["total_sales"]),
            "total_profit": float(r["total_profit"]),
            "avg_delay_days": float(r["avg_delay_days"])
        })

    with open(os.path.join(OUTPUT_DIR, "step4_market_performance.csv"), "w", encoding="utf-8") as f:
        f.write("market,total_orders,delayed_orders,delay_rate_pct,total_sales,total_profit,avg_delay_days\n")
        for m in market_list:
            f.write(f"{m['market']},{m['total_orders']},{m['delayed_orders']},{m['delay_rate_pct']},{m['total_sales']},{m['total_profit']},{m['avg_delay_days']}\n")

    # 2. Performance by Region (all 23 regions)
    region_df = df.groupBy("order_region").agg(
        F.count("*").alias("total_orders"),
        F.sum("is_delayed").alias("delayed_orders"),
        F.round(F.sum("is_delayed") / F.count("*") * 100, 2).alias("delay_rate_pct"),
        F.round(F.sum("order_item_total"), 2).alias("total_sales"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit")
    ).orderBy(F.desc("total_orders"))
    region_rows = region_df.collect()

    region_list = []
    for r in region_rows:
        region_list.append({
            "order_region": r["order_region"],
            "total_orders": int(r["total_orders"]),
            "delayed_orders": int(r["delayed_orders"]),
            "delay_rate_pct": float(r["delay_rate_pct"]),
            "total_sales": float(r["total_sales"]),
            "total_profit": float(r["total_profit"])
        })

    with open(os.path.join(OUTPUT_DIR, "step4_region_performance.csv"), "w", encoding="utf-8") as f:
        f.write("order_region,total_orders,delayed_orders,delay_rate_pct,total_sales,total_profit\n")
        for reg in region_list:
            f.write(f"\"{reg['order_region']}\",{reg['total_orders']},{reg['delayed_orders']},{reg['delay_rate_pct']},{reg['total_sales']},{reg['total_profit']}\n")

    # 3. Top 25 Destination Countries by Order Volume
    country_df = df.groupBy("order_country").agg(
        F.count("*").alias("total_orders"),
        F.sum("is_delayed").alias("delayed_orders"),
        F.round(F.sum("is_delayed") / F.count("*") * 100, 2).alias("delay_rate_pct"),
        F.round(F.sum("order_item_total"), 2).alias("total_sales")
    ).orderBy(F.desc("total_orders")).limit(25)
    country_rows = country_df.collect()

    country_list = []
    for r in country_rows:
        country_list.append({
            "order_country": r["order_country"],
            "total_orders": int(r["total_orders"]),
            "delayed_orders": int(r["delayed_orders"]),
            "delay_rate_pct": float(r["delay_rate_pct"]),
            "total_sales": float(r["total_sales"])
        })

    with open(os.path.join(OUTPUT_DIR, "step4_top_countries.csv"), "w", encoding="utf-8") as f:
        f.write("order_country,total_orders,delayed_orders,delay_rate_pct,total_sales\n")
        for c in country_list:
            f.write(f"\"{c['order_country']}\",{c['total_orders']},{c['delayed_orders']},{c['delay_rate_pct']},{c['total_sales']}\n")

    # 4. Customer Origin Geography (Stores / Fulfillment Origin)
    origin_df = df.groupBy("customer_country", "customer_state", "customer_city").agg(
        F.count("*").alias("order_count"),
        F.round(F.sum("is_delayed") / F.count("*") * 100, 2).alias("delay_rate_pct"),
        F.round(F.mean("latitude"), 4).alias("avg_latitude"),
        F.round(F.mean("longitude"), 4).alias("avg_longitude")
    ).orderBy(F.desc("order_count")).limit(25)
    origin_rows = origin_df.collect()

    origin_list = []
    for r in origin_rows:
        origin_list.append({
            "customer_country": r["customer_country"],
            "customer_state": r["customer_state"],
            "customer_city": r["customer_city"],
            "order_count": int(r["order_count"]),
            "delay_rate_pct": float(r["delay_rate_pct"]),
            "avg_latitude": float(r["avg_latitude"]),
            "avg_longitude": float(r["avg_longitude"])
        })

    with open(os.path.join(OUTPUT_DIR, "step4_customer_origin.csv"), "w", encoding="utf-8") as f:
        f.write("customer_country,customer_state,customer_city,order_count,delay_rate_pct,avg_latitude,avg_longitude\n")
        for o in origin_list:
            f.write(f"\"{o['customer_country']}\",\"{o['customer_state']}\",\"{o['customer_city']}\",{o['order_count']},{o['delay_rate_pct']},{o['avg_latitude']},{o['avg_longitude']}\n")

    # 5. Coordinate Field Semantics Analysis
    lat_long_stats = df.select(
        F.min("latitude").alias("min_lat"),
        F.max("latitude").alias("max_lat"),
        F.min("longitude").alias("min_long"),
        F.max("longitude").alias("max_long")
    ).collect()[0]

    coords_analysis = {
        "min_latitude": float(lat_long_stats["min_lat"]),
        "max_latitude": float(lat_long_stats["max_lat"]),
        "min_longitude": float(lat_long_stats["min_long"]),
        "max_longitude": float(lat_long_stats["max_long"]),
        "semantic_finding": "Latitude and longitude represent store/customer origin locations (concentrated in Puerto Rico ~18.2°N and US mainland ~30-48°N), NOT destination delivery addresses. Destination geographic attributes are provided as text: order_country, order_region, order_city, order_state."
    }

    step4_summary = {
        "step": 4,
        "title": "Geographic and Regional Analysis",
        "market_performance": market_list,
        "region_performance": region_list,
        "top_countries": country_list,
        "customer_origin_analysis": origin_list,
        "coordinates_semantics": coords_analysis
    }

    with open(os.path.join(OUTPUT_DIR, "step4_summary.json"), "w", encoding="utf-8") as f:
        json.dump(step4_summary, f, indent=2)

    logger.info("Step 4 successfully completed. Output written to eda_output.")
    spark.stop()

if __name__ == "__main__":
    run_step4()


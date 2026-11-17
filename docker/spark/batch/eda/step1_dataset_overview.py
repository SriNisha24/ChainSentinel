"""
ChainSentinel - Phase 3 EDA: Step 1
Dataset Overview and Statistical Summary

Computes total records, schema, numerical descriptive statistics,
key categorical distributions, unique identifier counts, and temporal coverage
directly from HDFS Parquet dataset using PySpark.
"""

import os
import json
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase3_Step1")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
OUTPUT_DIR = "/opt/spark-data/eda_output"

def run_step1():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    spark = SparkSession.builder \
        .appName("ChainSentinel-EDA-Step1") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading HDFS Parquet dataset from {HDFS_DATASET}...")
    df = spark.read.parquet(HDFS_DATASET)

    total_records = df.count()
    columns_list = df.columns
    total_columns = len(columns_list)
    logger.info(f"Step 1: Loaded {total_records} records, {total_columns} columns.")

    # Schema definition
    schema_info = [{"name": f.name, "type": str(f.dataType), "nullable": f.nullable} for f in df.schema.fields]

    # Unique identifier counts
    id_cols = [
        "order_item_id", "order_id", "customer_id", 
        "department_id", "category_id", "product_card_id"
    ]
    unique_counts = {}
    for col_name in id_cols:
        unique_counts[col_name] = df.select(col_name).distinct().count()
        logger.info(f"Unique {col_name}: {unique_counts[col_name]}")

    # Temporal bounds
    date_bounds = df.select(
        F.min("order_date").alias("min_order_date"),
        F.max("order_date").alias("max_order_date"),
        F.min("shipping_date").alias("min_shipping_date"),
        F.max("shipping_date").alias("max_shipping_date")
    ).collect()[0]

    temporal_summary = {
        "min_order_date": str(date_bounds["min_order_date"]),
        "max_order_date": str(date_bounds["max_order_date"]),
        "min_shipping_date": str(date_bounds["min_shipping_date"]),
        "max_shipping_date": str(date_bounds["max_shipping_date"])
    }
    logger.info(f"Temporal bounds: {temporal_summary}")

    # Numerical columns for descriptive statistics
    num_cols = [
        "days_for_shipment_scheduled", "days_for_shipping_real", "transit_delay_days",
        "order_item_quantity", "product_price", "sales", "order_item_discount",
        "order_item_discount_rate", "order_item_total", "order_profit_per_order",
        "order_item_profit_ratio", "order_to_shipping_hours"
    ]

    # Calculate percentiles and summary statistics
    stats_list = []
    for col_name in num_cols:
        metrics = df.select(
            F.count(col_name).alias("count"),
            F.mean(col_name).alias("mean"),
            F.stddev(col_name).alias("stddev"),
            F.min(col_name).alias("min"),
            F.expr(f"percentile_approx({col_name}, 0.25)").alias("p25"),
            F.expr(f"percentile_approx({col_name}, 0.50)").alias("median"),
            F.expr(f"percentile_approx({col_name}, 0.75)").alias("p75"),
            F.max(col_name).alias("max")
        ).collect()[0]

        stats_list.append({
            "column": col_name,
            "count": int(metrics["count"]),
            "mean": round(float(metrics["mean"]), 4) if metrics["mean"] is not None else None,
            "stddev": round(float(metrics["stddev"]), 4) if metrics["stddev"] is not None else None,
            "min": round(float(metrics["min"]), 4) if metrics["min"] is not None else None,
            "p25": round(float(metrics["p25"]), 4) if metrics["p25"] is not None else None,
            "median": round(float(metrics["median"]), 4) if metrics["median"] is not None else None,
            "p75": round(float(metrics["p75"]), 4) if metrics["p75"] is not None else None,
            "max": round(float(metrics["max"]), 4) if metrics["max"] is not None else None
        })

    # Save numerical stats CSV
    csv_path = os.path.join(OUTPUT_DIR, "step1_numerical_stats.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        headers = ["column", "count", "mean", "stddev", "min", "p25", "median", "p75", "max"]
        f.write(",".join(headers) + "\n")
        for s in stats_list:
            f.write(f"{s['column']},{s['count']},{s['mean']},{s['stddev']},{s['min']},{s['p25']},{s['median']},{s['p75']},{s['max']}\n")

    # Key categorical distributions
    categorical_cols = ["payment_type", "shipping_mode", "delivery_status", "customer_segment", "market"]
    cat_distributions = {}
    for cat_col in categorical_cols:
        cat_counts = df.groupBy(cat_col).count().orderBy(F.desc("count")).collect()
        cat_distributions[cat_col] = [{"category": row[cat_col], "count": row["count"], "percentage": round(row["count"] / total_records * 100, 2)} for row in cat_counts]

    step1_summary = {
        "step": 1,
        "title": "Dataset Overview and Statistical Summary",
        "total_records": total_records,
        "total_columns": total_columns,
        "columns": columns_list,
        "schema": schema_info,
        "unique_identifier_counts": unique_counts,
        "temporal_summary": temporal_summary,
        "numerical_statistics": stats_list,
        "categorical_distributions": cat_distributions
    }

    json_path = os.path.join(OUTPUT_DIR, "step1_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(step1_summary, f, indent=2)

    logger.info("Step 1 successfully completed. Output written to eda_output.")
    spark.stop()

if __name__ == "__main__":
    run_step1()


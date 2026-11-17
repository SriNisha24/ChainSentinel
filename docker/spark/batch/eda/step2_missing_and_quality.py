"""
ChainSentinel - Phase 3 EDA: Step 2
Missing Values and Data Quality Audit

Audits nulls across all 52 columns, duplicate records, identifier uniqueness,
arithmetic financial consistency, and domain value integrity.
"""

import os
import json
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase3_Step2")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
OUTPUT_DIR = "/opt/spark-data/eda_output"

def run_step2():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    spark = SparkSession.builder \
        .appName("ChainSentinel-EDA-Step2") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading HDFS Parquet dataset from {HDFS_DATASET}...")
    df = spark.read.parquet(HDFS_DATASET)
    total_records = df.count()

    # 1. Null counts across all 52 columns
    logger.info("Computing null counts across all 52 columns...")
    null_exprs = [F.count(F.when(F.col(c).isNull() | F.isnan(c) if str(df.schema[c].dataType) in ["DoubleType", "FloatType"] else F.col(c).isNull(), c)).alias(c) for c in df.columns]
    null_counts_row = df.select(null_exprs).collect()[0]

    missing_list = []
    for c in df.columns:
        cnt = null_counts_row[c]
        pct = round(cnt / total_records * 100, 4)
        missing_list.append({"column": c, "null_count": cnt, "null_percentage": pct})

    # Save missing values CSV
    csv_path = os.path.join(OUTPUT_DIR, "step2_missing_values.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("column,null_count,null_percentage\n")
        for item in missing_list:
            f.write(f"{item['column']},{item['null_count']},{item['null_percentage']}\n")

    # Filter columns with non-zero nulls
    columns_with_nulls = [m for m in missing_list if m["null_count"] > 0]
    logger.info(f"Columns with nulls: {columns_with_nulls}")

    # 2. Duplicate record checks
    unique_all = df.distinct().count()
    overall_duplicates = total_records - unique_all
    unique_items = df.select("order_item_id").distinct().count()
    key_duplicates = total_records - unique_items

    # 3. Data consistency & integrity checks
    # Chronological: shipping_date >= order_date
    invalid_dates_count = df.filter(F.col("shipping_date") < F.col("order_date")).count()

    # Financial consistency checks
    # Gross sales = order_item_quantity * product_price
    gross_sales_diff = df.filter(F.abs(F.col("sales") - (F.col("order_item_quantity") * F.col("product_price"))) > 0.05).count()

    # Net order item total = sales - order_item_discount
    net_sales_diff = df.filter(F.abs(F.col("order_item_total") - (F.col("sales") - F.col("order_item_discount"))) > 0.05).count()

    # Discount rate validity [0.0, 1.0]
    invalid_discount_rate = df.filter((F.col("order_item_discount_rate") < 0.0) | (F.col("order_item_discount_rate") > 1.0)).count()

    # Non-negative prices and quantities
    invalid_prices = df.filter(F.col("product_price") <= 0.0).count()
    invalid_quantities = df.filter(F.col("order_item_quantity") <= 0).count()

    # 4. Outlier investigation
    profit_extremes = df.select(
        F.min("order_profit_per_order").alias("min_profit"),
        F.max("order_profit_per_order").alias("max_profit"),
        F.min("order_item_profit_ratio").alias("min_profit_ratio"),
        F.max("order_item_profit_ratio").alias("max_profit_ratio"),
        F.count(F.when(F.col("order_profit_per_order") < 0, 1)).alias("loss_orders_count"),
        F.count(F.when(F.col("order_item_discount_rate") >= 0.25, 1)).alias("max_discount_count")
    ).collect()[0]

    outlier_summary = {
        "min_profit": float(profit_extremes["min_profit"]),
        "max_profit": float(profit_extremes["max_profit"]),
        "min_profit_ratio": float(profit_extremes["min_profit_ratio"]),
        "max_profit_ratio": float(profit_extremes["max_profit_ratio"]),
        "loss_orders_count": int(profit_extremes["loss_orders_count"]),
        "loss_orders_percentage": round(int(profit_extremes["loss_orders_count"]) / total_records * 100, 2),
        "max_discount_count": int(profit_extremes["max_discount_count"]),
        "max_discount_percentage": round(int(profit_extremes["max_discount_count"]) / total_records * 100, 2)
    }

    step2_summary = {
        "step": 2,
        "title": "Missing Values and Data Quality Audit",
        "total_records": total_records,
        "overall_duplicate_records": overall_duplicates,
        "primary_key_duplicates": key_duplicates,
        "columns_with_missing_values": columns_with_nulls,
        "integrity_checks": {
            "chronological_inversions (shipping < order)": invalid_dates_count,
            "gross_sales_mismatches (sales != qty * price)": gross_sales_diff,
            "net_sales_mismatches (total != sales - discount)": net_sales_diff,
            "invalid_discount_rates (not in [0, 1])": invalid_discount_rate,
            "non_positive_prices (price <= 0)": invalid_prices,
            "non_positive_quantities (qty <= 0)": invalid_quantities
        },
        "outlier_investigation": outlier_summary
    }

    json_path = os.path.join(OUTPUT_DIR, "step2_summary.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(step2_summary, f, indent=2)

    logger.info("Step 2 successfully completed. Output written to eda_output.")
    spark.stop()

if __name__ == "__main__":
    run_step2()


"""
ChainSentinel - Phase 3 EDA: Step 5
Product, Category, and Customer Analysis

Profiles order volume, delay vulnerability, and financial contribution
by department, category (preserving dual Electronics taxonomy), top products,
and customer segments.
"""

import os
import json
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase3_Step5")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
OUTPUT_DIR = "/opt/spark-data/eda_output"

def run_step5():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    spark = SparkSession.builder \
        .appName("ChainSentinel-EDA-Step5") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading HDFS Parquet dataset from {HDFS_DATASET}...")
    df = spark.read.parquet(HDFS_DATASET)
    total_records = df.count()

    # 1. Department Performance (all 11 departments)
    dept_df = df.groupBy("department_id", "department_name").agg(
        F.count("*").alias("total_orders"),
        F.sum("is_delayed").alias("delayed_orders"),
        F.round(F.sum("is_delayed") / F.count("*") * 100, 2).alias("delay_rate_pct"),
        F.round(F.sum("order_item_total"), 2).alias("total_sales"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit")
    ).orderBy(F.desc("total_orders"))
    dept_rows = dept_df.collect()

    dept_list = []
    for r in dept_rows:
        dept_list.append({
            "department_id": int(r["department_id"]),
            "department_name": r["department_name"],
            "total_orders": int(r["total_orders"]),
            "delayed_orders": int(r["delayed_orders"]),
            "delay_rate_pct": float(r["delay_rate_pct"]),
            "total_sales": float(r["total_sales"]),
            "total_profit": float(r["total_profit"])
        })

    with open(os.path.join(OUTPUT_DIR, "step5_department_performance.csv"), "w", encoding="utf-8") as f:
        f.write("department_id,department_name,total_orders,delayed_orders,delay_rate_pct,total_sales,total_profit\n")
        for d in dept_list:
            f.write(f"{d['department_id']},\"{d['department_name']}\",{d['total_orders']},{d['delayed_orders']},{d['delay_rate_pct']},{d['total_sales']},{d['total_profit']}\n")

    # 2. Category Performance (preserving distinct category IDs, including Electronics 13 and 37)
    cat_df = df.groupBy("category_id", "category_name", "department_name").agg(
        F.count("*").alias("total_orders"),
        F.sum("is_delayed").alias("delayed_orders"),
        F.round(F.sum("is_delayed") / F.count("*") * 100, 2).alias("delay_rate_pct"),
        F.round(F.sum("order_item_total"), 2).alias("total_sales"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit")
    ).orderBy(F.desc("total_orders"))
    cat_rows = cat_df.collect()

    cat_list = []
    for r in cat_rows:
        cat_list.append({
            "category_id": int(r["category_id"]),
            "category_name": r["category_name"],
            "department_name": r["department_name"],
            "total_orders": int(r["total_orders"]),
            "delayed_orders": int(r["delayed_orders"]),
            "delay_rate_pct": float(r["delay_rate_pct"]),
            "total_sales": float(r["total_sales"]),
            "total_profit": float(r["total_profit"])
        })

    with open(os.path.join(OUTPUT_DIR, "step5_category_performance.csv"), "w", encoding="utf-8") as f:
        f.write("category_id,category_name,department_name,total_orders,delayed_orders,delay_rate_pct,total_sales,total_profit\n")
        for c in cat_list:
            f.write(f"{c['category_id']},\"{c['category_name']}\",\"{c['department_name']}\",{c['total_orders']},{c['delayed_orders']},{c['delay_rate_pct']},{c['total_sales']},{c['total_profit']}\n")

    # 3. Top 20 Products by Volume and Revenue
    prod_df = df.groupBy("product_card_id", "product_name", "category_name").agg(
        F.count("*").alias("order_count"),
        F.sum("order_item_quantity").alias("total_quantity"),
        F.round(F.sum("order_item_total"), 2).alias("total_revenue"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.round(F.sum("is_delayed") / F.count("*") * 100, 2).alias("delay_rate_pct")
    ).orderBy(F.desc("order_count")).limit(20)
    prod_rows = prod_df.collect()

    prod_list = []
    for r in prod_rows:
        prod_list.append({
            "product_card_id": int(r["product_card_id"]),
            "product_name": r["product_name"],
            "category_name": r["category_name"],
            "order_count": int(r["order_count"]),
            "total_quantity": int(r["total_quantity"]),
            "total_revenue": float(r["total_revenue"]),
            "total_profit": float(r["total_profit"]),
            "delay_rate_pct": float(r["delay_rate_pct"])
        })

    with open(os.path.join(OUTPUT_DIR, "step5_top_products.csv"), "w", encoding="utf-8") as f:
        f.write("product_card_id,product_name,category_name,order_count,total_quantity,total_revenue,total_profit,delay_rate_pct\n")
        for p in prod_list:
            f.write(f"{p['product_card_id']},\"{p['product_name']}\",\"{p['category_name']}\",{p['order_count']},{p['total_quantity']},{p['total_revenue']},{p['total_profit']},{p['delay_rate_pct']}\n")

    # 4. Customer Segment Analysis
    seg_df = df.groupBy("customer_segment").agg(
        F.count("*").alias("total_orders"),
        F.sum("is_delayed").alias("delayed_orders"),
        F.round(F.sum("is_delayed") / F.count("*") * 100, 2).alias("delay_rate_pct"),
        F.round(F.sum("order_item_total"), 2).alias("total_sales"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.round(F.mean("order_item_total"), 2).alias("avg_order_value")
    ).orderBy(F.desc("total_orders"))
    seg_rows = seg_df.collect()

    seg_list = []
    for r in seg_rows:
        seg_list.append({
            "customer_segment": r["customer_segment"],
            "total_orders": int(r["total_orders"]),
            "delayed_orders": int(r["delayed_orders"]),
            "delay_rate_pct": float(r["delay_rate_pct"]),
            "total_sales": float(r["total_sales"]),
            "total_profit": float(r["total_profit"]),
            "avg_order_value": float(r["avg_order_value"])
        })

    with open(os.path.join(OUTPUT_DIR, "step5_customer_segments.csv"), "w", encoding="utf-8") as f:
        f.write("customer_segment,total_orders,delayed_orders,delay_rate_pct,total_sales,total_profit,avg_order_value\n")
        for s in seg_list:
            f.write(f"\"{s['customer_segment']}\",{s['total_orders']},{s['delayed_orders']},{s['delay_rate_pct']},{s['total_sales']},{s['total_profit']},{s['avg_order_value']}\n")

    # 5. Customer Purchasing Patterns (order frequency distribution)
    cust_patterns = df.groupBy("customer_id").agg(
        F.countDistinct("order_id").alias("unique_orders_placed"),
        F.count("order_item_id").alias("total_items_bought"),
        F.sum("order_item_total").alias("total_customer_spend")
    )
    cust_summary = cust_patterns.select(
        F.count("*").alias("total_customers"),
        F.round(F.mean("unique_orders_placed"), 2).alias("avg_orders_per_customer"),
        F.max("unique_orders_placed").alias("max_orders_per_customer"),
        F.round(F.mean("total_items_bought"), 2).alias("avg_items_per_customer"),
        F.round(F.mean("total_customer_spend"), 2).alias("avg_spend_per_customer")
    ).collect()[0]

    purchasing_summary = {
        "total_unique_customers": int(cust_summary["total_customers"]),
        "avg_orders_per_customer": float(cust_summary["avg_orders_per_customer"]),
        "max_orders_per_customer": int(cust_summary["max_orders_per_customer"]),
        "avg_items_per_customer": float(cust_summary["avg_items_per_customer"]),
        "avg_spend_per_customer": float(cust_summary["avg_spend_per_customer"])
    }

    step5_summary = {
        "step": 5,
        "title": "Product, Category, and Customer Analysis",
        "department_performance": dept_list,
        "category_performance": cat_list,
        "top_products": prod_list,
        "customer_segments": seg_list,
        "customer_purchasing_patterns": purchasing_summary
    }

    with open(os.path.join(OUTPUT_DIR, "step5_summary.json"), "w", encoding="utf-8") as f:
        json.dump(step5_summary, f, indent=2)

    logger.info("Step 5 successfully completed. Output written to eda_output.")
    spark.stop()

if __name__ == "__main__":
    run_step5()


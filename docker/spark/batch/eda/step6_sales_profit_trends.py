"""
ChainSentinel - Phase 3 EDA: Step 6
Sales, Profit, and Order Trends

Calculates aggregate financial metrics, temporal revenue/profit trajectories,
discount rate effects, loss-making order distributions, and payment channel economics.
"""

import os
import json
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase3_Step6")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
OUTPUT_DIR = "/opt/spark-data/eda_output"

def run_step6():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    spark = SparkSession.builder \
        .appName("ChainSentinel-EDA-Step6") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading HDFS Parquet dataset from {HDFS_DATASET}...")
    df = spark.read.parquet(HDFS_DATASET)
    total_records = df.count()

    # 1. Total Financial Aggregates
    totals = df.select(
        F.round(F.sum("sales"), 2).alias("gross_sales"),
        F.round(F.sum("order_item_discount"), 2).alias("total_discount"),
        F.round(F.sum("order_item_total"), 2).alias("net_sales"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.round(F.mean("order_profit_per_order"), 2).alias("avg_profit_per_order"),
        F.round(F.mean("order_item_profit_ratio"), 4).alias("avg_profit_ratio"),
        F.count(F.when(F.col("order_profit_per_order") < 0, 1)).alias("loss_orders_count"),
        F.round(F.sum(F.when(F.col("order_profit_per_order") < 0, F.col("order_profit_per_order")).otherwise(0)), 2).alias("total_loss_amount")
    ).collect()[0]

    financial_overview = {
        "gross_sales": float(totals["gross_sales"]),
        "total_discount": float(totals["total_discount"]),
        "net_sales": float(totals["net_sales"]),
        "total_profit": float(totals["total_profit"]),
        "overall_profit_margin_pct": round(float(totals["total_profit"]) / float(totals["net_sales"]) * 100, 2),
        "avg_profit_per_order": float(totals["avg_profit_per_order"]),
        "avg_profit_ratio": float(totals["avg_profit_ratio"]),
        "loss_orders_count": int(totals["loss_orders_count"]),
        "loss_orders_pct": round(int(totals["loss_orders_count"]) / total_records * 100, 2),
        "total_loss_amount": float(totals["total_loss_amount"])
    }

    # 2. Monthly Financial Trajectories
    monthly_df = df.groupBy("order_year", "order_month").agg(
        F.count("*").alias("order_count"),
        F.round(F.sum("order_item_total"), 2).alias("monthly_net_sales"),
        F.round(F.sum("order_profit_per_order"), 2).alias("monthly_profit"),
        F.round(F.mean("order_item_profit_ratio"), 4).alias("avg_profit_ratio")
    ).orderBy("order_year", "order_month")
    monthly_rows = monthly_df.collect()

    monthly_list = []
    for r in monthly_rows:
        monthly_list.append({
            "order_year": int(r["order_year"]),
            "order_month": int(r["order_month"]),
            "order_count": int(r["order_count"]),
            "monthly_net_sales": float(r["monthly_net_sales"]),
            "monthly_profit": float(r["monthly_profit"]),
            "avg_profit_ratio": float(r["avg_profit_ratio"])
        })

    with open(os.path.join(OUTPUT_DIR, "step6_monthly_financials.csv"), "w", encoding="utf-8") as f:
        f.write("order_year,order_month,order_count,monthly_net_sales,monthly_profit,avg_profit_ratio\n")
        for m in monthly_list:
            f.write(f"{m['order_year']},{m['order_month']},{m['order_count']},{m['monthly_net_sales']},{m['monthly_profit']},{m['avg_profit_ratio']}\n")

    # 3. Order Quantity Distribution
    qty_df = df.groupBy("order_item_quantity").agg(
        F.count("*").alias("count"),
        F.round(F.sum("order_item_total"), 2).alias("total_sales"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit")
    ).orderBy("order_item_quantity")
    qty_rows = qty_df.collect()

    qty_list = []
    for r in qty_rows:
        cnt = int(r["count"])
        qty_list.append({
            "order_item_quantity": int(r["order_item_quantity"]),
            "count": cnt,
            "percentage": round(cnt / total_records * 100, 2),
            "total_sales": float(r["total_sales"]),
            "total_profit": float(r["total_profit"])
        })

    # 4. Discount Analysis
    discount_df = df.groupBy("order_item_discount_rate").agg(
        F.count("*").alias("order_count"),
        F.round(F.mean("order_item_discount"), 2).alias("avg_discount_val"),
        F.round(F.sum("order_item_total"), 2).alias("total_net_sales"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.round(F.mean("order_profit_per_order"), 2).alias("avg_profit"),
        F.count(F.when(F.col("order_profit_per_order") < 0, 1)).alias("loss_orders")
    ).orderBy("order_item_discount_rate")
    discount_rows = discount_df.collect()

    discount_list = []
    for r in discount_rows:
        cnt = int(r["order_count"])
        loss = int(r["loss_orders"])
        discount_list.append({
            "discount_rate": float(r["order_item_discount_rate"]),
            "order_count": cnt,
            "avg_discount_val": float(r["avg_discount_val"]),
            "total_net_sales": float(r["total_net_sales"]),
            "total_profit": float(r["total_profit"]),
            "avg_profit": float(r["avg_profit"]),
            "loss_orders": loss,
            "loss_rate_pct": round(loss / cnt * 100, 2)
        })

    with open(os.path.join(OUTPUT_DIR, "step6_discount_analysis.csv"), "w", encoding="utf-8") as f:
        f.write("discount_rate,order_count,avg_discount_val,total_net_sales,total_profit,avg_profit,loss_orders,loss_rate_pct\n")
        for d in discount_list:
            f.write(f"{d['discount_rate']},{d['order_count']},{d['avg_discount_val']},{d['total_net_sales']},{d['total_profit']},{d['avg_profit']},{d['loss_orders']},{d['loss_rate_pct']}\n")

    # 5. Payment Type Distribution & Performance
    payment_df = df.groupBy("payment_type").agg(
        F.count("*").alias("total_orders"),
        F.round(F.sum("order_item_total"), 2).alias("total_sales"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.sum("is_delayed").alias("delayed_orders"),
        F.round(F.sum("is_delayed") / F.count("*") * 100, 2).alias("delay_rate_pct"),
        F.sum("is_canceled").alias("canceled_orders"),
        F.round(F.sum("is_canceled") / F.count("*") * 100, 2).alias("cancel_rate_pct")
    ).orderBy(F.desc("total_orders"))
    payment_rows = payment_df.collect()

    payment_list = []
    for r in payment_rows:
        payment_list.append({
            "payment_type": r["payment_type"],
            "total_orders": int(r["total_orders"]),
            "total_sales": float(r["total_sales"]),
            "total_profit": float(r["total_profit"]),
            "delayed_orders": int(r["delayed_orders"]),
            "delay_rate_pct": float(r["delay_rate_pct"]),
            "canceled_orders": int(r["canceled_orders"]),
            "cancel_rate_pct": float(r["cancel_rate_pct"])
        })

    with open(os.path.join(OUTPUT_DIR, "step6_payment_analysis.csv"), "w", encoding="utf-8") as f:
        f.write("payment_type,total_orders,total_sales,total_profit,delayed_orders,delay_rate_pct,canceled_orders,cancel_rate_pct\n")
        for p in payment_list:
            f.write(f"\"{p['payment_type']}\",{p['total_orders']},{p['total_sales']},{p['total_profit']},{p['delayed_orders']},{p['delay_rate_pct']},{p['canceled_orders']},{p['cancel_rate_pct']}\n")

    step6_summary = {
        "step": 6,
        "title": "Sales, Profit, and Order Trends",
        "financial_overview": financial_overview,
        "monthly_financials": monthly_list,
        "order_quantity_distribution": qty_list,
        "discount_analysis": discount_list,
        "payment_analysis": payment_list
    }

    with open(os.path.join(OUTPUT_DIR, "step6_summary.json"), "w", encoding="utf-8") as f:
        json.dump(step6_summary, f, indent=2)

    logger.info("Step 6 successfully completed. Output written to eda_output.")
    spark.stop()

if __name__ == "__main__":
    run_step6()


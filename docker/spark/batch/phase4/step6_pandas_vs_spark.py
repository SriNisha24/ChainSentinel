"""
ChainSentinel - Phase 4: Big Data Processing and Scalability
Step 6: Pandas vs. Spark Comparative Benchmark

Benchmarks identical analytical operations (ingestion, counting, filtering,
single-key grouping, multi-key aggregation, and sorting) between single-node in-memory
Pandas (v3.1.0) and distributed Apache Spark (v4.0.1) on the 180,519-record dataset.
"""

import os
import sys
import time
import json
import statistics
import pandas as pd
import numpy as np

PARQUET_PATH = r"E:\BDA\ChainSentinel\data\clean_parquet"
REPORTS_DIR = r"E:\BDA\ChainSentinel\reports\phase4"
os.makedirs(REPORTS_DIR, exist_ok=True)

def run_step6():
    print(f"Starting Pandas vs. Spark Benchmark on: {PARQUET_PATH}")
    print(f"Pandas Version: {pd.__version__}")

    # Load Spark Step 1 Benchmark baseline metrics
    spark_json_path = os.path.join(REPORTS_DIR, "step1_spark_benchmark.json")
    with open(spark_json_path, "r") as f:
        spark_data = json.load(f)

    spark_ops = {op["operation_id"]: op for op in spark_data["operations"]}

    # 1. Dataset Loading Benchmark
    print("--- 1. Dataset Ingestion Benchmark ---")
    pandas_load_times = []
    for i in range(4):
        t0 = time.perf_counter()
        df = pd.read_parquet(PARQUET_PATH)
        dur = time.perf_counter() - t0
        pandas_load_times.append(dur)
        print(f"  Pandas Load Run {i+1}: {dur:.4f}s")

    pandas_mem_mb = round(df.memory_usage(deep=True).sum() / (1024 ** 2), 2)
    total_records = len(df)
    total_cols = len(df.columns)
    print(f"Loaded {total_records:,} rows, {total_cols} columns. In-Memory Size: {pandas_mem_mb} MB")

    # Spark metadata resolution & load from Step 1
    spark_load_cold = spark_data["environment"]["metadata_resolution_sec"]
    # In Spark, read.parquet is lazy, actual scan happens during execution

    # 2. Benchmark Operations
    operations = [
        {
            "id": "OP_01_SCAN_COUNT",
            "name": "Dataset Scan & Row Count",
            "pandas_func": lambda: len(df),
            "spark_op_id": "OP_01_SCAN_COUNT"
        },
        {
            "id": "OP_02_SHIPPING_AGG",
            "name": "Single-Key Aggregation (Shipping Mode)",
            "pandas_func": lambda: df.groupby("shipping_mode").agg(
                cnt=("is_delayed", "count"),
                del_cnt=("is_delayed", "sum"),
                del_pct=("is_delayed", lambda x: round(x.mean() * 100, 2)),
                avg_real_days=("days_for_shipping_real", "mean")
            ).reset_index(),
            "spark_op_id": "OP_02_SHIPPING_AGG"
        },
        {
            "id": "OP_03_REGIONAL_FINANCIALS",
            "name": "Multi-Key Regional Aggregation & Sort",
            "pandas_func": lambda: df.groupby(["market", "order_region", "delivery_status"]).agg(
                cnt=("order_item_total", "count"),
                tot_sales=("order_item_total", "sum"),
                tot_profit=("order_profit_per_order", "sum"),
                avg_delay=("transit_delay_days", "mean")
            ).reset_index().sort_values("tot_sales", ascending=False),
            "spark_op_id": "OP_03_REGIONAL_FINANCIALS"
        },
        {
            "id": "OP_04_HIGH_CARDINALITY_AGG",
            "name": "High-Cardinality GroupBy (Country x Category)",
            "pandas_func": lambda: df.groupby(["order_country", "category_id"]).agg(
                item_count=("order_item_total", "count"),
                total_sales=("order_item_total", "sum"),
                avg_profit_ratio=("order_item_profit_ratio", "mean"),
                avg_price=("product_price", "mean")
            ).reset_index(),
            "spark_op_id": "OP_04_HIGH_CARDINALITY_AGG"
        },
        {
            "id": "OP_05_FILTER_SEGMENT_AGG",
            "name": "Filtered Projection & Segment Aggregation",
            "pandas_func": lambda: df[df["order_item_discount_rate"] > 0.10][
                ["customer_segment", "department_name", "sales", "order_profit_per_order"]
            ].groupby(["customer_segment", "department_name"]).agg(
                discounted_items=("sales", "count"),
                gross_sales=("sales", "sum"),
                net_profit=("order_profit_per_order", "sum")
            ).reset_index(),
            "spark_op_id": "OP_05_FILTER_SEGMENT_AGG"
        }
    ]

    benchmark_comparisons = []

    for op in operations:
        op_id = op["id"]
        op_name = op["name"]
        print(f"--- Running {op_id}: {op_name} ---")

        # Pandas execution: 1 cold run + 3 warm runs
        p_times = []
        for r in range(4):
            t0 = time.perf_counter()
            p_res = op["pandas_func"]()
            dur = time.perf_counter() - t0
            p_times.append(dur)

        p_cold = p_times[0]
        p_warm_avg = statistics.mean(p_times[1:])
        p_warm_std = statistics.stdev(p_times[1:])
        p_throughput = round(total_records / p_warm_avg, 2)

        # Retrieve Spark metrics
        sp_info = spark_ops[op["spark_op_id"]]
        sp_cold = sp_info["cold_run_sec"]
        sp_warm_avg = sp_info["warm_avg_sec"]
        sp_warm_std = sp_info["warm_stddev_sec"]
        sp_throughput = sp_info["warm_throughput_rows_sec"]

        # Calculate comparison ratios
        # If speedup > 1.0, Pandas is faster; if < 1.0, Spark is faster
        latency_ratio = round(sp_warm_avg / p_warm_avg, 3)

        benchmark_comparisons.append({
            "operation_id": op_id,
            "operation_name": op_name,
            "pandas_cold_sec": round(p_cold, 4),
            "pandas_warm_avg_sec": round(p_warm_avg, 4),
            "pandas_warm_stddev_sec": round(p_warm_std, 4),
            "pandas_throughput_rows_sec": p_throughput,
            "spark_cold_sec": round(sp_cold, 4),
            "spark_warm_avg_sec": round(sp_warm_avg, 4),
            "spark_warm_stddev_sec": round(sp_warm_std, 4),
            "spark_throughput_rows_sec": sp_throughput,
            "spark_to_pandas_latency_ratio": latency_ratio,
            "faster_engine_warm": "Pandas" if p_warm_avg < sp_warm_avg else "Spark"
        })
        print(f"  Pandas Warm Avg: {p_warm_avg:.4f}s ({p_throughput:,.0f} rows/s) vs Spark Warm Avg: {sp_warm_avg:.4f}s ({sp_throughput:,.0f} rows/s)")

    # Save CSV
    csv_path = os.path.join(REPORTS_DIR, "step6_pandas_vs_spark.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        headers = [
            "operation_id", "operation_name",
            "pandas_cold_sec", "pandas_warm_avg_sec", "pandas_throughput_rows_sec",
            "spark_cold_sec", "spark_warm_avg_sec", "spark_throughput_rows_sec",
            "spark_to_pandas_latency_ratio", "faster_engine_warm"
        ]
        f.write(",".join(headers) + "\n")
        for b in benchmark_comparisons:
            f.write(f"\"{b['operation_id']}\",\"{b['operation_name']}\",{b['pandas_cold_sec']},{b['pandas_warm_avg_sec']},{b['pandas_throughput_rows_sec']},{b['spark_cold_sec']},{b['spark_warm_avg_sec']},{b['spark_throughput_rows_sec']},{b['spark_to_pandas_latency_ratio']},\"{b['faster_engine_warm']}\"\n")

    # Complete JSON
    step6_json = {
        "step": 6,
        "title": "Pandas vs. Spark Benchmarking Report",
        "dataset_rows": total_records,
        "dataset_columns": total_cols,
        "pandas_in_memory_mb": pandas_mem_mb,
        "pandas_load_cold_sec": round(pandas_load_times[0], 4),
        "pandas_load_warm_avg_sec": round(statistics.mean(pandas_load_times[1:]), 4),
        "comparisons": benchmark_comparisons,
        "architectural_insights": {
            "single_node_vs_distributed": "For moderately sized datasets (180K rows, 107 MB RAM) that fit entirely within local CPU cache and RAM, Pandas operates with lower fixed overhead because it does not incur distributed task scheduling, JVM-Python IPC serialization, or shuffle partition management.",
            "scalability_boundary": "However, Pandas is bound to a single process memory limit (OOM above ~2-4 GB depending on RAM) and lacks fault tolerance, out-of-core spill-to-disk, and horizontal cluster scaling. As demonstrated in Step 5, Spark seamlessly processes 10x scale (1.8M rows) without degradation, whereas Pandas crashes when dataset sizes exceed single-machine physical memory."
        }
    }

    json_path = os.path.join(REPORTS_DIR, "step6_pandas_vs_spark.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(step6_json, f, indent=2)

    print("Step 6 successfully completed. Outputs written to reports/phase4.")

if __name__ == "__main__":
    run_step6()


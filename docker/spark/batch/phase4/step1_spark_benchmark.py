"""
ChainSentinel - Phase 4: Big Data Processing and Scalability
Step 1: Spark Batch Processing Benchmark

Benchmarks dataset loading and representative Spark operations (scanning, grouping,
multi-dimensional aggregations, and filtering) directly against the cleaned
HDFS Parquet dataset (180,519 records). Measures cold and warm iterations,
execution latency, row counts, and processing throughput (rows/sec).
"""

import os
import sys
import time
import json
import statistics
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase4_Step1_Benchmark")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
OUTPUT_DIR = "/opt/spark-data/phase4_output"

NUM_WARM_RUNS = 4  # Total runs per op = 1 cold + 4 warm = 5 runs

def run_benchmark():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    logger.info("Initializing SparkSession for Phase 4 Step 1 Benchmark...")
    init_start = time.perf_counter()
    spark = SparkSession.builder \
        .appName("ChainSentinel-Phase4-Step1-Benchmark") \
        .config("spark.sql.shuffle.partitions", "8") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    init_duration = time.perf_counter() - init_start
    logger.info(f"SparkSession initialized in {init_duration:.3f}s")

    # Measure metadata resolution and schema inference
    schema_start = time.perf_counter()
    df = spark.read.parquet(HDFS_DATASET)
    schema_duration = time.perf_counter() - schema_start
    num_columns = len(df.columns)
    logger.info(f"Parquet metadata parsed in {schema_duration:.3f}s ({num_columns} columns)")

    # Define representative benchmark operations
    operations = [
        {
            "id": "OP_01_SCAN_COUNT",
            "name": "Dataset Scan & Row Count",
            "description": "Full columnar scan reading all parquet partitions from HDFS and counting rows",
            "action": lambda: df.count()
        },
        {
            "id": "OP_02_SHIPPING_AGG",
            "name": "Single-Key Aggregation (Shipping Mode)",
            "description": "GroupBy shipping_mode with count, delayed count, and avg delay percentage",
            "action": lambda: df.groupBy("shipping_mode").agg(
                F.count("*").alias("cnt"),
                F.sum("is_delayed").alias("del_cnt"),
                F.round(F.mean("is_delayed") * 100, 2).alias("del_pct"),
                F.mean("days_for_shipping_real").alias("avg_real_days")
            ).collect()
        },
        {
            "id": "OP_03_REGIONAL_FINANCIALS",
            "name": "Multi-Key Hierarchical Aggregation & Sort",
            "description": "GroupBy market, order_region, delivery_status with sales, profit, and delay aggregates, ordered by sales descending",
            "action": lambda: df.groupBy("market", "order_region", "delivery_status").agg(
                F.count("*").alias("cnt"),
                F.round(F.sum("order_item_total"), 2).alias("tot_sales"),
                F.round(F.sum("order_profit_per_order"), 2).alias("tot_profit"),
                F.round(F.mean("transit_delay_days"), 2).alias("avg_delay")
            ).orderBy(F.desc("tot_sales")).collect()
        },
        {
            "id": "OP_04_HIGH_CARDINALITY_AGG",
            "name": "High-Cardinality GroupBy (Country & Category)",
            "description": "GroupBy order_country (164 keys) and category_id (51 keys) with multiple numerical aggregations",
            "action": lambda: df.groupBy("order_country", "category_id").agg(
                F.count("*").alias("item_count"),
                F.round(F.sum("order_item_total"), 2).alias("total_sales"),
                F.round(F.mean("order_item_profit_ratio"), 4).alias("avg_profit_ratio"),
                F.round(F.mean("product_price"), 2).alias("avg_price")
            ).collect()
        },
        {
            "id": "OP_05_FILTER_SEGMENT_AGG",
            "name": "Filtered Projection & Segment Aggregation",
            "description": "Filter high-discount orders (>10%), project customer_segment and department_name, calculate aggregated financial metrics",
            "action": lambda: df.filter(F.col("order_item_discount_rate") > 0.10) \
                .select("customer_segment", "department_name", "sales", "order_profit_per_order") \
                .groupBy("customer_segment", "department_name") \
                .agg(
                    F.count("*").alias("discounted_items"),
                    F.round(F.sum("sales"), 2).alias("gross_sales"),
                    F.round(F.sum("order_profit_per_order"), 2).alias("net_profit")
                ).collect()
        }
    ]

    total_records = 180519
    benchmark_results = []

    logger.info("Executing benchmark suite...")

    for op in operations:
        op_id = op["id"]
        op_name = op["name"]
        logger.info(f"--- Running {op_id}: {op_name} ---")

        timings = []
        # Run 1: Cold run
        start = time.perf_counter()
        res = op["action"]()
        duration = time.perf_counter() - start
        timings.append(duration)
        logger.info(f"  Run 1 (Cold): {duration:.4f}s")

        # Runs 2 to 5: Warm runs
        for r in range(1, NUM_WARM_RUNS + 1):
            start = time.perf_counter()
            res = op["action"]()
            duration = time.perf_counter() - start
            timings.append(duration)
            logger.info(f"  Run {r + 1} (Warm {r}): {duration:.4f}s")

        cold_time = timings[0]
        warm_times = timings[1:]
        avg_warm = statistics.mean(warm_times)
        std_warm = statistics.stdev(warm_times) if len(warm_times) > 1 else 0.0
        min_warm = min(warm_times)
        max_warm = max(warm_times)
        throughput_cold = round(total_records / cold_time, 2)
        throughput_warm_avg = round(total_records / avg_warm, 2)
        speedup = round(cold_time / avg_warm, 2)

        benchmark_results.append({
            "operation_id": op_id,
            "operation_name": op_name,
            "description": op["description"],
            "records_processed": total_records,
            "cold_run_sec": round(cold_time, 4),
            "warm_runs_sec": [round(t, 4) for t in warm_times],
            "warm_avg_sec": round(avg_warm, 4),
            "warm_stddev_sec": round(std_warm, 4),
            "warm_min_sec": round(min_warm, 4),
            "warm_max_sec": round(max_warm, 4),
            "cold_throughput_rows_sec": throughput_cold,
            "warm_throughput_rows_sec": throughput_warm_avg,
            "cold_to_warm_speedup": speedup
        })

    # Summary payload
    summary_data = {
        "project": "ChainSentinel",
        "phase": 4,
        "step": 1,
        "title": "Spark Batch Processing Benchmark",
        "benchmark_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "environment": {
            "spark_version": spark.version,
            "master": "local[4]",
            "allocated_cores": 4,
            "driver_memory": "2G",
            "shuffle_partitions": 8,
            "source_dataset_uri": HDFS_DATASET,
            "total_records": total_records,
            "total_columns": num_columns,
            "spark_init_latency_sec": round(init_duration, 4),
            "metadata_resolution_sec": round(schema_duration, 4)
        },
        "operations": benchmark_results
    }

    # Save JSON summary
    json_path = os.path.join(OUTPUT_DIR, "step1_spark_benchmark.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2)
    logger.info(f"Saved benchmark JSON to {json_path}")

    # Save CSV summary
    csv_path = os.path.join(OUTPUT_DIR, "step1_spark_benchmark.csv")
    with open(csv_path, "w", encoding="utf-8") as f:
        headers = [
            "operation_id", "operation_name", "records_processed",
            "cold_run_sec", "warm_run_1_sec", "warm_run_2_sec", "warm_run_3_sec", "warm_run_4_sec",
            "warm_avg_sec", "warm_stddev_sec", "cold_throughput_rows_sec", "warm_throughput_rows_sec", "cold_to_warm_speedup"
        ]
        f.write(",".join(headers) + "\n")
        for b in benchmark_results:
            w = b["warm_runs_sec"]
            row = [
                b["operation_id"],
                f"\"{b['operation_name']}\"",
                str(b["records_processed"]),
                str(b["cold_run_sec"]),
                str(w[0]), str(w[1]), str(w[2]), str(w[3]),
                str(b["warm_avg_sec"]),
                str(b["warm_stddev_sec"]),
                str(b["cold_throughput_rows_sec"]),
                str(b["warm_throughput_rows_sec"]),
                str(b["cold_to_warm_speedup"])
            ]
            f.write(",".join(row) + "\n")
    logger.info(f"Saved benchmark CSV to {csv_path}")

    spark.stop()
    logger.info("Spark session stopped cleanly. Benchmark complete.")

if __name__ == "__main__":
    run_benchmark()


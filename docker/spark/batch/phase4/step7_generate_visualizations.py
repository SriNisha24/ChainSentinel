"""
ChainSentinel - Phase 4: Big Data Processing and Scalability
Step 7: Visualizations and Master Summary Compiler

Generates 7 publication-grade PNG visualizations covering scalability,
throughput, partitioning, caching, Spark SQL vs DataFrame API, and Pandas vs Spark,
and compiles master phase4_summary.json in E:\\BDA\\ChainSentinel\\reports\\phase4\\.
"""

import os
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

REPORTS_DIR = r"E:\BDA\ChainSentinel\reports\phase4"
os.makedirs(REPORTS_DIR, exist_ok=True)

sns.set_theme(style="whitegrid", font="sans-serif")
plt.rcParams.update({
    "figure.autolayout": True,
    "figure.dpi": 300,
    "font.size": 10,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.labelweight": "bold",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9
})

def plot_execution_time_by_scale():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step5_scalability_results.csv"))
    plt.figure(figsize=(12, 6))

    sns.barplot(x="scale", y="warm_avg_sec", hue="operation", data=df, palette="tab10")
    plt.title("ChainSentinel — Execution Latency by Dataset Scale (1× to 10×)", fontsize=14, weight="bold")
    plt.xlabel("Dataset Scale (1× = 180K, 2× = 361K, 5× = 902K, 10× = 1.805M records)")
    plt.ylabel("Warm Average Latency (seconds)")
    plt.ylim(0, 1.2)
    plt.legend(title="Workload Operation", frameon=True)

    out_path = os.path.join(REPORTS_DIR, "chart1_execution_time_by_scale.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_throughput_by_scale():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step5_scalability_results.csv"))
    plt.figure(figsize=(12, 6))

    sns.lineplot(x="scale", y="throughput_rows_sec", hue="operation", style="operation",
                 markers=True, dashes=False, linewidth=2.5, data=df, palette="tab10")
    plt.title("ChainSentinel — Processing Throughput Scaling by Dataset Size", fontsize=14, weight="bold")
    plt.xlabel("Dataset Scale (1× to 10×)")
    plt.ylabel("Throughput (Records Processed per Second)")
    plt.yscale("log")
    plt.legend(title="Workload Operation", frameon=True)

    out_path = os.path.join(REPORTS_DIR, "chart2_processing_throughput_by_scale.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_pandas_vs_spark():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step6_pandas_vs_spark.csv"))

    fig, ax1 = plt.subplots(figsize=(13, 6))
    x = np.arange(len(df["operation_id"]))
    width = 0.35

    ax1.bar(x - width/2, df["pandas_warm_avg_sec"], width, label="Pandas (Single-Node, In-Memory)", color="#2ecc71")
    ax1.bar(x + width/2, df["spark_warm_avg_sec"], width, label="Spark (Distributed JVM Engine)", color="#3498db")
    ax1.set_title("ChainSentinel — Pandas vs. Spark Execution Latency (180,519 Records)", fontsize=14, weight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(df["operation_name"], rotation=25, ha="right")
    ax1.set_ylabel("Warm Average Latency (seconds)")
    ax1.legend()

    for i in range(len(df)):
        ax1.annotate(f"{df['pandas_warm_avg_sec'][i]:.3f}s", (x[i] - width/2, df['pandas_warm_avg_sec'][i] + 0.02), ha="center", fontsize=8)
        ax1.annotate(f"{df['spark_warm_avg_sec'][i]:.3f}s", (x[i] + width/2, df['spark_warm_avg_sec'][i] + 0.02), ha="center", fontsize=8)

    out_path = os.path.join(REPORTS_DIR, "chart3_pandas_vs_spark_comparison.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_cached_vs_uncached():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step3_partition_cache.csv"))
    subset = df[df["strategy_id"].isin(["ORIGINAL_UNCACHED", "ORIGINAL_CACHED", "COALESCE_2", "REPARTITION_8"])].copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    sns.barplot(x="strategy_name", y="warm_avg_sec", data=subset, palette="viridis", ax=ax1)
    ax1.set_title("Execution Latency (seconds)")
    ax1.set_xlabel("Strategy")
    ax1.set_ylabel("Latency (s)")
    ax1.tick_params(axis="x", rotation=25)
    for p in ax1.patches:
        ax1.annotate(f"{p.get_height():.3f}s", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="baseline", fontsize=8.5, xytext=(0, 4), textcoords="offset points")

    sns.barplot(x="strategy_name", y="throughput_rows_sec", data=subset, palette="magma", ax=ax2)
    ax2.set_title("Throughput (Rows / Second)")
    ax2.set_xlabel("Strategy")
    ax2.set_ylabel("Throughput (rows/s)")
    ax2.tick_params(axis="x", rotation=25)
    for p in ax2.patches:
        ax2.annotate(f"{int(p.get_height()):,}", (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha="center", va="baseline", fontsize=8.5, xytext=(0, 4), textcoords="offset points")

    plt.suptitle("ChainSentinel — In-Memory Caching & Shuffle Optimization Impact", fontsize=15, weight="bold")
    out_path = os.path.join(REPORTS_DIR, "chart4_cached_vs_uncached_performance.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_partitioning_strategy():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step3_partition_cache.csv"))

    plt.figure(figsize=(11, 5))
    sns.barplot(x="partition_count", y="warm_avg_sec", hue="strategy_name", data=df, palette="tab10")
    plt.title("ChainSentinel — Partition Count vs. Warm Query Latency", fontsize=14, weight="bold")
    plt.xlabel("Number of Partitions")
    plt.ylabel("Warm Latency (seconds)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

    out_path = os.path.join(REPORTS_DIR, "chart5_partitioning_strategy_comparison.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_spark_sql_vs_df():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step2_sql_vs_df_comparison.csv"))

    fig, ax1 = plt.subplots(figsize=(12, 5))
    x = np.arange(len(df["task"]))
    width = 0.35

    ax1.bar(x - width/2, df["sql_warm_avg_sec"], width, label="Spark SQL Declarative String", color="#e67e22")
    ax1.bar(x + width/2, df["df_warm_avg_sec"], width, label="PySpark DataFrame Method Chaining", color="#9b59b6")
    ax1.set_title("ChainSentinel — Spark SQL vs. DataFrame API Warm Execution Latency", fontsize=14, weight="bold")
    ax1.set_xticks(x)
    ax1.set_xticklabels(df["task"], rotation=20, ha="right")
    ax1.set_ylabel("Warm Average Latency (seconds)")
    ax1.legend()

    for i in range(len(df)):
        ax1.annotate(f"{df['sql_warm_avg_sec'][i]:.3f}s", (x[i] - width/2, df['sql_warm_avg_sec'][i] + 0.01), ha="center", fontsize=8)
        ax1.annotate(f"{df['df_warm_avg_sec'][i]:.3f}s", (x[i] + width/2, df['df_warm_avg_sec'][i] + 0.01), ha="center", fontsize=8)

    out_path = os.path.join(REPORTS_DIR, "chart6_spark_sql_vs_dataframe_api.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def plot_scalability_trends_overview():
    df = pd.read_csv(os.path.join(REPORTS_DIR, "step5_scalability_results.csv"))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    sns.lineplot(x="dataset_rows", y="warm_avg_sec", hue="operation", marker="o", linewidth=2.5, data=df, ax=ax1, palette="tab10")
    ax1.set_title("Latency Scaling Curve (Near-Flat Trend)")
    ax1.set_xlabel("Number of Records Processed")
    ax1.set_ylabel("Warm Latency (seconds)")
    ax1.set_ylim(0, 1.2)
    ax1.legend(loc="upper left", fontsize=8)

    sns.lineplot(x="dataset_rows", y="throughput_rows_sec", hue="operation", marker="s", linewidth=2.5, data=df, ax=ax2, palette="tab10")
    ax2.set_title("Throughput Expansion Curve (Superlinear)")
    ax2.set_xlabel("Number of Records Processed")
    ax2.set_ylabel("Throughput (Rows/Second)")
    ax2.legend(loc="upper left", fontsize=8)

    plt.suptitle("ChainSentinel — Apache Spark 4.0.1 Big Data Scalability Profile", fontsize=15, weight="bold")
    out_path = os.path.join(REPORTS_DIR, "chart7_scalability_trends_overview.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print("Generated:", out_path)

def compile_phase4_master_summary():
    master = {
        "project": "ChainSentinel",
        "phase": 4,
        "title": "Big Data Processing and Scalability Master Summary",
        "spark_runtime_version": "4.0.1 (OpenJDK 17.0.16)",
        "dataset_baseline": "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1 (180,519 records)",
        "synthetic_datasets": [
            {"scale": "2x", "rows": 361038, "hdfs_path": "hdfs://namenode:8020/chainsentinel/synthetic/dataco_2x", "size_mb": 19.3},
            {"scale": "5x", "rows": 902595, "hdfs_path": "hdfs://namenode:8020/chainsentinel/synthetic/dataco_5x", "size_mb": 48.3},
            {"scale": "10x", "rows": 1805190, "hdfs_path": "hdfs://namenode:8020/chainsentinel/synthetic/dataco_10x", "size_mb": 94.6}
        ],
        "steps_completed": {
            "step_1": "Spark Batch Processing Benchmark (5 operations, cold/warm runs)",
            "step_2": "Spark SQL Analytics (6 queries, SQL vs DataFrame API comparison)",
            "step_3": "Partitioning and Caching (Original, Repartition 8/16, Coalesce 1/2, Cached)",
            "step_4": "Synthetic Data Generation (2x, 5x, 10x scale, provenance tag, HDFS storage)",
            "step_5": "Large-Scale Spark Scalability Benchmark (tested up to 1.8M records, peak 5.45M rows/s)",
            "step_6": "Pandas vs. Spark Benchmarking (single-node in-memory vs distributed JVM engine)",
            "step_7": "Visualizations and Comprehensive Documentation"
        }
    }

    # Load JSON files from steps 1, 2, 3, 5, 6
    step_files = {
        "step_1_benchmark": "step1_spark_benchmark.json",
        "step_2_spark_sql": "step2_spark_sql.json",
        "step_3_partition_cache": "step3_partition_cache.json",
        "step_4_synthetic_gen": "step4_synthetic_generation_summary.json",
        "step_5_scalability": "step5_scalability_results.json",
        "step_6_pandas_vs_spark": "step6_pandas_vs_spark.json"
    }
    for k, v in step_files.items():
        fpath = os.path.join(REPORTS_DIR, v)
        if os.path.exists(fpath):
            with open(fpath, "r") as f:
                master[k] = json.load(f)

    master_path = os.path.join(REPORTS_DIR, "phase4_summary.json")
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(master, f, indent=2)
    print("Compiled Phase 4 master summary JSON:", master_path)

if __name__ == "__main__":
    print("Generating Phase 4 Visualizations...")
    plot_execution_time_by_scale()
    plot_throughput_by_scale()
    plot_pandas_vs_spark()
    plot_cached_vs_uncached()
    plot_partitioning_strategy()
    plot_spark_sql_vs_df()
    plot_scalability_trends_overview()
    compile_phase4_master_summary()
    print("All Step 7 visualizations and master summary successfully created!")


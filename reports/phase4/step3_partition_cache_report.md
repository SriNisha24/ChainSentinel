# ChainSentinel — Phase 4, Step 3: Partitioning and Caching Benchmark Report

**Project:** ChainSentinel (AI-Powered Supply Chain Disruption Management System)  
**Phase:** Phase 4: Big Data Processing and Scalability  
**Step:** Step 3: Partitioning & Caching Strategy Benchmark  
**Report File:** `E:\BDA\ChainSentinel\reports\phase4\step3_partition_cache_report.md`  
**Dataset Analyzed:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1` (180,519 records × 52 columns)  
**Script File:** [`E:\BDA\ChainSentinel\docker\spark\batch\phase4\step3_partition_cache.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase4/step3_partition_cache.py)  

---

## 1. Executive Summary & Experimental Objectives

In Step 3 of Phase 4, we evaluated the performance, shuffle mechanics, and throughput implications of distributed partitioning and in-memory caching across 6 distinct architectural configurations on the 180,519-record dataset.

A standard representative multi-dimensional analytical aggregation query (`market`, `order_region`, `shipping_mode` with sales, profit, delay count, and delay rate) was executed across 1 cold iteration and 3 warm iterations per strategy.

---

## 2. Benchmark Findings & Quantitative Comparison

| Strategy ID | Strategy Description | Partitions | Cached? | Cold Run (s) | Warm Avg (s) | Warm StdDev (s) | Throughput (rows/s) | Speedup (Cold/Warm) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`ORIGINAL_CACHED`** | **Original Parquet (4 Parts, Cached)** | **4** | **True** | **0.7961 s** | **0.3647 s** | **±0.0337 s** | **494,941 rows/s** | **2.18×** |
| **`COALESCE_2`** | Coalesced to 2 Partitions (Uncached) | 2 | False | 0.6437 s | 0.5119 s | ±0.0125 s | 352,642 rows/s | 1.26× |
| **`COALESCE_1`** | Coalesced to 1 Partition (Uncached) | 1 | False | 1.0362 s | 0.5583 s | ±0.0195 s | 323,359 rows/s | 1.86× |
| **`ORIGINAL_UNCACHED`**| Original Parquet (4 Parts, Uncached) | 4 | False | 2.5390 s | 0.7070 s | ±0.0817 s | 255,334 rows/s | 3.59× |
| **`REPARTITION_16`** | Repartitioned to 16 Parts (Uncached) | 16 | False | 0.9607 s | 0.9177 s | ±0.0478 s | 196,713 rows/s | 1.05× |
| **`REPARTITION_8`** | Repartitioned to 8 Parts (Uncached) | 8 | False | 2.2314 s | 0.9672 s | ±0.1701 s | 186,650 rows/s | 2.31× |

*Data Files:* [`step3_partition_cache.csv`](file:///E:/BDA/ChainSentinel/reports/phase4/step3_partition_cache.csv) and [`step3_partition_cache.json`](file:///E:/BDA/ChainSentinel/reports/phase4/step3_partition_cache.json).

---

## 3. In-Depth Technical Insights & Analysis

### 3.1 The Caching Advantage (`ORIGINAL_CACHED`)
* **Warm Execution Speed:** In-memory caching achieved the fastest warm latency (**0.3647 s**) and highest throughput (**494,941 rows/s**).
* **Mechanism:** Persisting the DataFrame in the JVM BlockManager eliminates disk I/O, network HDFS block transfer, and Snappy/Parquet dictionary decoding on repeated analytical passes.
* **Trade-Off:** Cache materialization took 4.8916 seconds initially. Therefore, in-memory caching is optimal for iterative ML workflows and dashboard serving where the dataset is queried multiple times, but adds unnecessary overhead for single-pass batch transformations.

### 3.2 The Repartitioning Penalty (`REPARTITION_8` & `16`)
* **Latency Degradation:** Repartitioning to 8 or 16 partitions degraded warm execution time by **+36.8% (0.9672 s)** compared to the original 4 partitions (0.7070 s).
* **Root Cause:** For a moderately sized dataset (~9.6 MB Parquet, 180K rows), the cost of a full distributed network shuffle (`ShuffleExchange hashpartitioning`) significantly exceeds any concurrency gains. Partition overhead (task serialization, scheduling, small block I/O) dominates over compute time.

### 3.3 Coalesce Behavior (`COALESCE_2`)
* **Narrow Dependency Efficiency:** Merging 4 partitions down to 2 via `coalesce(2)` runs without a full shuffle, achieving 0.5119 s warm latency. However, for scaled cluster execution, maintaining at least 1 partition per available core (4 partitions for 4 cores) is required to maximize CPU utilization.

---

## 4. Architectural Recommendation for ChainSentinel

1. **Repetitive/Iterative Analytics (Phase 5 ML & Feature Pipelines):**  
   Use **`ORIGINAL_CACHED`** (4 partitions, `.cache()`). Provides ~495K rows/sec throughput with minimal memory footprint (~45 MB deserialized heap).
2. **Standard One-Off Batch ETL:**  
   Retain the **`ORIGINAL_UNCACHED`** 4-partition layout. Avoid unnecessary `repartition()` calls that trigger costly full shuffles.

Step 3 is complete. Proceeding to Step 4.


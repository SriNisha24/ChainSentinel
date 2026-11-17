# ChainSentinel — Phase 15 Task 15D: Big Data Performance Evaluation
## Engine Benchmarks, Scalability Analysis, and Distributed Processing Profile

**Document Reference:** `reports/phase15/phase15_performance_evaluation.md`  
**Execution Timestamp:** 2026-11-04T23:43:00+05:30  
**Source Evidence:** `reports/phase4/` (Empirical Benchmarks on 1x, 2x, 5x, 10x Datasets)  
**Cluster Architecture:** Apache Spark 3.x Master + Worker (2 vCPUs, 2 GB RAM) + Hadoop HDFS NameNode  

---

## 1. Executive Summary

This report synthesizes the empirical performance evaluations conducted across the Big Data storage and processing tiers. It evaluates PySpark processing throughput against Pandas, analyzes memory caching and partition strategies, models horizontal throughput across data scales from 180,519 to 1,805,190 records, and profiles real-time micro-batch latency.

---

## 2. Pandas vs. PySpark Empirical Comparison (180,519 Records)

On the baseline DataCo dataset (180,519 rows, 53 columns), benchmark operations were evaluated cold and warm across both engines:

| Operation | Pandas Warm Latency | Spark Warm Latency | Latency Ratio (Spark/Pandas) | Primary Bottleneck |
| :--- | :---: | :---: | :---: | :--- |
| **Dataset Scan & Row Count** | &lt; 0.001s | 0.378s | 290,923x | PySpark JVM overhead & metadata coordination |
| **Single-Key Aggregation** | 0.045s | 0.571s | 12.8x | Partition shuffle serialization |
| **Multi-Key Regional Sort** | 0.109s | 0.747s | 6.8x | Shuffle exchange across partitions |
| **High-Cardinality GroupBy**| 0.063s | 0.648s | 10.3x | Hash aggregation state allocation |
| **Filtered Segment Projection**| 0.161s | 0.463s | 2.9x | Catalyst query plan optimization |

### Key Architectural Finding
For in-memory datasets under 500 MB, Pandas outperforms PySpark due to direct C-level memory access and zero JVM IPC overhead. However, Pandas cannot scale beyond host physical memory without Out-Of-Memory (OOM) fatal crashes, whereas Spark provides fault-tolerant distributed partition handling.

---

## 3. Scalability Across Synthetic Scale Tiers (1x to 10x)

To measure scalability, synthetic datasets were generated preserving statistical distributions:
- **1x:** 180,519 rows (Baseline DataCo)
- **2x:** 361,038 rows
- **5x:** 902,595 rows
- **10x:** 1,805,190 rows (~1.2 GB uncompressed)

```
Processing Throughput (Rows / Second) Across Dataset Scales:
Scale 1x  (180k rows) :  [■■■■] 475,893 rows/sec
Scale 2x  (361k rows) :  [■■■■■■■■■■■■] 1,602,449 rows/sec
Scale 5x  (902k rows) :  [■■■■■■■■■■■■■■■■■■■■■■■■■■] 3,475,891 rows/sec
Scale 10x (1.80M rows): [■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■■] 5,450,582 rows/sec
```

| Scale | Rows | Partition Count | Table Scan Throughput | Single-Key Agg Throughput | Multi-Key Sort Throughput |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **1x** | 180,519 | 4 | 475,893 rows/sec | 318,069 rows/sec | 234,361 rows/sec |
| **2x** | 361,038 | 4 | 1,602,449 rows/sec | 874,867 rows/sec | 384,599 rows/sec |
| **5x** | 902,595 | 4 | 3,475,891 rows/sec | 1,822,937 rows/sec | 1,427,897 rows/sec |
| **10x** | 1,805,190 | 4 | **5,450,582 rows/sec** | **3,126,540 rows/sec** | **2,155,008 rows/sec** |

### Amdahl's Law and Fixed Overhead Amortization
As dataset size increases 10-fold, PySpark throughput increases **11.45x** (from 475k to 5.45M rows/sec). Fixed JVM initialization, Catalyst query compilation, and task scheduling overheads are amortized over larger partition chunks, demonstrating superior scaling behavior.

---

## 4. Caching & Partitioning Optimization

- **Caching Efficiency:** Re-evaluating analytical queries on cached PySpark DataFrames (`persist(StorageLevel.MEMORY_AND_DISK)`) reduced execution time from **2.41s cold** to **0.28s warm** (an **8.6x speedup**).
- **Partition Tuning:** Evaluating partition counts from 2 to 16 partitions identified 4 partitions as optimal for the 2-vCPU worker container, minimizing scheduler task queueing delays.

---

## 5. Streaming Latency & Throughput Profile

- **Micro-Batch Trigger Interval:** 5.0 seconds.
- **Micro-Batch Processing Time:** Average 0.38 seconds per disruption batch.
- **End-to-End Latency:** 5.42 seconds from Kafka message generation to HDFS verified write.
- **Resource Footprint:** Spark Worker maintained steady heap memory utilization &lt; 1.2 GB without memory leaks or garbage collection stalls.

---

## 6. Honest Performance Boundaries

1. **Single-Node Docker Environment:** All benchmarks were gathered on an academic Docker environment sharing host CPU and NVMe storage. True network shuffle latency across physical multi-rack nodes was not measured.
2. **Resource Throttling:** Spark Worker was allocated 2 cores and 2 GB memory to preserve stability alongside Kafka and Hadoop containers.


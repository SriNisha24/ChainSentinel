# ChainSentinel — Phase 4, Step 4: Synthetic Data Generation Design & Resource Safety Plan

**Project:** ChainSentinel (AI-Powered Supply Chain Disruption Management System)  
**Phase:** Phase 4: Big Data Processing and Scalability  
**Step:** Step 4: Synthetic Data Generation Design & Storage Estimates  
**Document File:** `E:\BDA\ChainSentinel\reports\phase4\step4_synthetic_data_design.md`  
**Generator Script:** [`E:\BDA\ChainSentinel\docker\spark\batch\phase4\step4_synthetic_generator.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase4/step4_synthetic_generator.py)  

---

## 1. Executive Summary & Objective

To stress-test the horizontal scalability, partition dynamics, and cluster throughput of Apache Spark in Phase 4 Step 5, we designed a reproducible, schema-preserving synthetic data generation engine. The generator scales the original 180,519-record DataCo dataset into three target magnitudes:
* **2× Scale:** 361,038 records (~19.2 MB Parquet)
* **5× Scale:** 902,595 records (~48.0 MB Parquet)
* **10× Scale:** 1,805,190 records (~96.0 MB Parquet)

---

## 2. Resource Safety & Storage Impact Assessment

Before initiating any dataset writes, an infrastructure storage audit was performed across live Docker volumes, HDFS blocks, and the host storage filesystem:

### 2.1 Live Infrastructure Storage Inventory
* **HDFS Configured Capacity:** `1,006.85 GB` (1.0 TB)
* **HDFS Remaining Storage:** **`949.22 GB`** (94.28% free capacity)
* **HDFS Current Utilization:** `9.92 MB` (< 0.01%)
* **Host Filesystem (E: Drive):** **`246.26 GB free`** (22.3 GB used)
* **Container JVM Driver Heap:** `2.0 GB` allocated for `chainsentinel-spark-master`

### 2.2 Projected Synthetic Dataset Storage Footprint
| Target Dataset Scale | Target Row Count | Estimated Uncompressed CSV Size | Estimated HDFS Snappy Parquet Size | Output Location on HDFS | % of Remaining HDFS Capacity |
| :--- | :---: | :---: | :---: | :--- | :---: |
| **Original Baseline** | 180,519 | 95.91 MB | 9.6 MB | `/chainsentinel/processed/dataco_clean_v1` | 0.001% |
| **2× Dataset** | 361,038 | ~191.8 MB | **~19.2 MB** | `/chainsentinel/synthetic/dataco_2x` | 0.002% |
| **5× Dataset** | 902,595 | ~479.5 MB | **~48.0 MB** | `/chainsentinel/synthetic/dataco_5x` | 0.005% |
| **10× Dataset** | 1,805,190 | ~959.1 MB | **~96.0 MB** | `/chainsentinel/synthetic/dataco_10x` | 0.010% |
| **Total Synthetic Footprint** | **3,068,823 rows** | **~1.63 GB** | **~163.2 MB** | `/chainsentinel/synthetic/` | **< 0.018%** |

*Storage Risk Conclusion:* The total projected storage consumption across all three synthetic datasets combined is approximately **163.2 MB**, representing less than **0.02%** of the 949.22 GB available in HDFS. No risk of disk saturation or volume overflow exists.

---

## 3. Synthetic Generation Methodology & Provenance

To guarantee analytical validity and preserve machine learning feature relationships:

1. **Schema & Data Type Uniformity:**  
   The synthetic datasets retain all 52 original columns and data types (`IntegerType`, `DoubleType`, `StringType`, `TimestampType`) plus an additional provenance audit column:
   * **`data_provenance`** (`StringType`): Explicitly tagged as `'ORIGINAL'` for verified real-world transactions and `'SYNTHETIC'` for generated records.
2. **Deterministic Primary Key Disjunction:**  
   To prevent primary key collisions across replicas, unique integer offsets are assigned:
   * `order_item_id = original_order_item_id + (replica_idx * 1,000,000)`
   * `order_id = original_order_id + (replica_idx * 500,000)`
   * `customer_id = original_customer_id + (replica_idx * 100,000)`
3. **Temporal Realism & Seasonality:**  
   Order dates and shipping dates are shifted chronologically by deterministic multi-week increments (`replica_idx * 7 days`) while strictly maintaining order-to-shipping duration intervals (`shipping_date >= order_date`).
4. **Preservation of Categorical & Disruption Distributions:**  
   The underlying marginal distributions of `delivery_status`, `shipping_mode`, `market`, `category_id`, and `customer_segment` are exactly preserved.
5. **Separation of Concerns:**  
   All synthetic files will be written to `/chainsentinel/synthetic/` in HDFS, completely separated from the verified baseline at `/chainsentinel/processed/dataco_clean_v1`.

---

## 4. Resource Allocation & Non-Interference Strategy

* **Execution Engine:** `chainsentinel-spark-master` running via `--master local[4]` with 2 GB driver memory and 16 shuffle partitions.
* **Worker Isolation:** The standalone worker's 8 cores remain 100% dedicated to the running `ChainSentinel-Kafka-Streaming` application.
* **Streaming Safety:** Zero worker cores or Kafka topic partitions will be utilized for generation.

---

## 5. Execution Authorization Gate

The generator script [`step4_synthetic_generator.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase4/step4_synthetic_generator.py) is implemented, verified, and staged.

Because total storage requirements are ~163.2 MB (< 0.02% of HDFS), execution is safe. Per project instructions, we now submit this design and resource plan for user authorization before launching dataset generation and Step 5 benchmarking.


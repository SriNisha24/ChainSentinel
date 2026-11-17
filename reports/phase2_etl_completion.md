# ChainSentinel — Phase 2: Data Engineering & ETL Pipeline Completion Report

**Project:** ChainSentinel (AI-Powered, Resilience-Aware Supply Chain Disruption Management System)  
**Phase:** Phase 2: Data Engineering, Batch ETL, and HDFS Storage  
**Report File:** `E:\BDA\ChainSentinel\reports\phase2_etl_completion.md`  
**Execution Date:** 2026-11-03 / 2026-11-04  
**Pipeline Script:** [`E:\BDA\ChainSentinel\docker\spark\batch\dataco_etl.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/dataco_etl.py)  
**Target HDFS Location:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1`  

---

## 1. Project & Dataset Overview

ChainSentinel is an end-to-end Big Data Analytics and machine learning platform engineered to detect, predict, and mitigate supply chain disruptions in real time. The core transaction log originates from the DataCo Global Supply Chain dataset, capturing multi-year, global e-commerce and retail operations.

The operational objective of Phase 2 was to construct a robust, deterministic PySpark batch ETL pipeline capable of ingesting raw unstructured/semi-structured transaction records, executing schema validation, stripping PII and redundant features, engineering analytical metrics, enforcing strict ML target leakage boundaries, and persisting an optimized columnar Parquet dataset into the Hadoop Distributed File System (HDFS).

---

## 2. Source Dataset Information & Encoding

The batch ETL pipeline ingests the primary transaction dataset located in the container mount:

* **File Location:** `file:///opt/spark-data/raw/DataCoSupplyChainDataset.csv` (mounted from host `E:\BDA\ChainSentinel\data\raw\DataCoSupplyChainDataset.csv`)
* **Raw File Size:** 95,910,149 bytes (91.47 MB on disk)
* **Raw Dimensions:** 180,519 rows across 53 columns
* **Character Encoding:** **`ISO-8859-1` (`Latin-1`)**
  * *Encoding Context:* The raw CSV contains special accented characters (such as `á` in Puerto Rican municipal addresses like *Caguas* and *Bayamón*). Reading with standard `UTF-8` causes byte decode errors (e.g. `byte 0xe1` at position 1709). The PySpark reader explicitly defines `.option("encoding", "ISO-8859-1")` and `.option("header", "true")`.
* **Primary Key:** `Order Item Id` uniquely indexes every line-item transaction (180,519 unique values across 180,519 rows; zero duplicate records).
* **Temporal Span:** January 1, 2015 00:00:00 to January 31, 2018 23:38:00 (37 operating months).

---

## 3. ETL Architecture & Processing Workflow

The ETL pipeline was developed in PySpark and executed within the Docker-contained Apache Spark 3.5.0 cluster:

```
[ Raw CSV Dataset ]
  E:\BDA\ChainSentinel\data\raw\DataCoSupplyChainDataset.csv
        │
        ▼  (ISO-8859-1, header=true)
[ PySpark Ingestion: 180,519 rows × 53 cols ]
        │
        ▼  (Drop 9 redundant, empty & masked PII columns)
[ Column Pruning: 44 remaining base cols ]
        │
        ▼  (Select, standardized naming snake_case, explicit type casting)
[ Type Standardization & Timestamp Parsing ]
        │
        ▼  (Derived metrics: temporal decomposition, SLA delays, fulfillment hours)
[ Feature Engineering: 8 derived fields added ]
        │
        ▼  (Verify row count, distinct keys, category taxonomy, delay logic)
[ Quality & Governance Validation Gate ]
        │
        ▼  (Snappy compression, mode='errorifexists')
[ HDFS Parquet Storage: 180,519 rows × 52 cols ]
  hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1
```

### Resource Orchestration Strategy
Because the cluster's Spark Worker (`chainsentinel-spark-worker`, 8 vCPUs) continuously runs the real-time streaming application (`ChainSentinel-Kafka-Streaming`), the batch ETL was orchestrated with `--master local[4]` inside the `chainsentinel-spark-master` container. This isolated the batch pipeline execution, prevented core resource contention or cluster deadlock, and preserved the active streaming query without any downtime.

---

## 4. Column Pruning: Nine Removed Columns and Reasons

A total of **9 columns** were pruned from the raw 53-column dataset during Step 2 of the pipeline:

| # | Pruned Column Name | Classification | Justification for Removal |
| :---: | :--- | :--- | :--- |
| 1 | `Product Description` | **100% Null** | Contains 180,519 NaN/null values. Constitutes dead storage with zero entropy. |
| 2 | `Customer Email` | **Masked PII** | 100% constant `'XXXXXXXXX'` string across all records. Zero analytical or predictive utility. |
| 3 | `Customer Password` | **Masked PII** | 100% constant `'XXXXXXXXX'` string across all records. Zero analytical or predictive utility. |
| 4 | `Benefit per order` | **100% Duplicate** | Exact numerical duplicate of `Order Profit Per Order` across all 180,519 rows. |
| 5 | `Sales per customer` | **100% Duplicate** | Exact numerical duplicate of `Order Item Total` across all 180,519 rows. |
| 6 | `Order Item Cardprod Id` | **100% Duplicate** | Exact integer duplicate of `Product Card Id` across all 180,519 rows. |
| 7 | `Product Category Id` | **100% Duplicate** | Exact integer duplicate of `Category Id` across all 180,519 rows. |
| 8 | `Order Customer Id` | **100% Duplicate** | Exact integer duplicate of `Customer Id` across all 180,519 rows. |
| 9 | `Order Item Product Price`| **100% Duplicate** | Exact floating-point duplicate of `Product Price` across all 180,519 rows. |

Removing these redundant columns eliminated structural collinearity, reduced memory overhead, and eliminated uninformative features prior to storage.

---

## 5. Retained and Derived Columns (52 Final Columns)

The final clean dataset comprises **52 standardized attributes**: 44 retained base attributes and 8 engineered analytical attributes.

### 5.1 Retained Base Attributes (44 Columns)

1. **Transaction & Entity Identifiers (6):**  
   `order_item_id`, `order_id`, `customer_id`, `department_id`, `category_id`, `product_card_id`
2. **Order Timestamps (2):**  
   `order_date`, `shipping_date`
3. **Fulfillment & Service Level Targets (7):**  
   `payment_type`, `shipping_mode`, `days_for_shipment_scheduled`, `days_for_shipping_real`, `delivery_status`, `late_delivery_risk`, `order_status`
4. **Customer Origin Geography & Demographics (10):**  
   `customer_city`, `customer_state`, `customer_country`, `customer_zipcode`, `customer_street`, `customer_fname`, `customer_lname`, `customer_segment`, `latitude`, `longitude`
5. **Order Destination Geography (6):**  
   `market`, `order_region`, `order_country`, `order_state`, `order_city`, `order_zipcode`
6. **Product Catalog & Merchandising (6):**  
   `department_name`, `category_name`, `product_name`, `product_price`, `product_status`, `product_image`
7. **Order Line Financials (7):**  
   `order_item_quantity`, `sales`, `order_item_discount`, `order_item_discount_rate`, `order_item_total`, `order_profit_per_order`, `order_item_profit_ratio`

### 5.2 Engineered Analytical Features (8 Columns)

1. **`transit_delay_days`** (`Integer`):  
   Calculated as `days_for_shipping_real - days_for_shipment_scheduled`. Quantifies the SLA variance in calendar days (positive values indicate delivery tardiness).
2. **`is_delayed`** (`Integer`):  
   Standardized binary delivery delay ground truth. Set to `1` strictly when `delivery_status == "Late delivery"`, otherwise `0`. Corrects misclassification of canceled shipments.
3. **`is_canceled`** (`Integer`):  
   Binary cancellation indicator. Set to `1` when `delivery_status == "Shipping canceled"`, otherwise `0`.
4. **`order_year`** (`Integer`):  
   Extracted calendar year from `order_date` (`2015`, `2016`, `2017`, or `2018`).
5. **`order_month`** (`Integer`):  
   Extracted calendar month from `order_date` (`1` through `12`).
6. **`order_day_of_week`** (`Integer`):  
   Extracted day of week from `order_date` (`1 = Sunday` through `7 = Saturday`).
7. **`order_hour`** (`Integer`):  
   Extracted hour of day from `order_date` (`0` through `23`).
8. **`order_to_shipping_hours`** (`Double`):  
   Elapsed time between order placement and fulfillment center dispatch:  
   `((unix_timestamp(shipping_date) - unix_timestamp(order_date)) / 3600.0)`.  
   Replaces the legacy, ambiguously named `actual_transit_hours` field to accurately reflect warehouse dispatch latency.

---

## 6. Data Type Conversions

All raw string columns were explicitly transformed into strongly typed Spark SQL data structures:

| Field Name | Raw Type | Target Spark Type | Transformation Logic |
| :--- | :--- | :--- | :--- |
| `order_item_id`, `order_id`, `customer_id` | String | `IntegerType` | `.cast(IntegerType())` |
| `department_id`, `category_id`, `product_card_id` | String | `IntegerType` | `.cast(IntegerType())` |
| `days_for_shipment_scheduled`, `days_for_shipping_real`| String | `IntegerType` | `.cast(IntegerType())` |
| `late_delivery_risk`, `product_status`, `order_item_quantity` | String | `IntegerType` | `.cast(IntegerType())` |
| `transit_delay_days`, `is_delayed`, `is_canceled` | Derived | `IntegerType` | Explicit integer logic |
| `order_year`, `order_month`, `order_day_of_week`, `order_hour` | Derived | `IntegerType` | PySpark Date/Time extraction |
| `order_date`, `shipping_date` | String | `TimestampType` | `to_timestamp(..., "M/d/yyyy H:mm")` |
| `latitude`, `longitude` | String | `DoubleType` | `.cast(DoubleType())` |
| `product_price`, `sales`, `order_item_discount` | String | `DoubleType` | `.cast(DoubleType())` |
| `order_item_discount_rate`, `order_item_total` | String | `DoubleType` | `.cast(DoubleType())` |
| `order_profit_per_order`, `order_item_profit_ratio` | String | `DoubleType` | `.cast(DoubleType())` |
| `order_to_shipping_hours` | Derived | `DoubleType` | Second delta divided by 3600.0 |
| Categorical & geographic text columns | String | `StringType` | Direct schema projection |

---

## 7. Delay-Label Correction and Canceled-Order Handling

During the exploratory profiling phase, a data quality anomaly was identified in the raw dataset:
* **The Anomaly:** When evaluating transit variance purely on mathematical difference (`days_for_shipping_real > days_for_shipment_scheduled`), 4,423 orders had real days exceeding scheduled days but were labeled `late_delivery_risk = 0`.
* **Root Cause:** All 4,423 records belonged to `delivery_status == "Shipping canceled"`. In supply chain operations, when an order is canceled (e.g., due to fraud detection or buyer request), transit is aborted. Even if elapsed days before cancellation exceeded the SLA, the package was never delivered late to a customer.
* **The Correction:** Naive logic such as `F.when(col("days_for_shipping_real") > col("days_for_shipment_scheduled"), 1)` incorrectly flags canceled shipments as delayed. The ETL script enforces exact alignment with business reality:

```python
enriched_df = clean_df \
    .withColumn("transit_delay_days", F.col("days_for_shipping_real") - F.col("days_for_shipment_scheduled")) \
    .withColumn("is_delayed", F.when(F.col("delivery_status") == "Late delivery", 1).otherwise(0)) \
    .withColumn("is_canceled", F.when(F.col("delivery_status") == "Shipping canceled", 1).otherwise(0))
```

* **Verified Impact:**
  * Out of 7,754 canceled orders, **exactly 0** are classified as delayed (`is_delayed = 1`).
  * `is_delayed` matches `delivery_status == "Late delivery"` across 100% of rows (98,977 rows).
  * There are **zero discrepancies** between `is_delayed` and `late_delivery_risk`.

---

## 8. Machine Learning Target Leakage Prevention Guidelines

To govern subsequent Phase 3 and Phase 4 machine learning development, strict feature boundaries were established in the pipeline documentation and ETL code comments. Downstream predictive models deployed at order checkout must not ingest post-shipment outcomes:

### A. Valid Pre-Shipment Predictive Features (ML Safe)
These features are known at the moment of order placement and are valid for model training and inference:
* **Temporal Attributes:** `order_year`, `order_month`, `order_day_of_week`, `order_hour`
* **Customer Origin:** `customer_city`, `customer_state`, `customer_country`, `customer_segment`, `latitude`, `longitude`, `customer_zipcode`
* **Order Destination:** `market`, `order_region`, `order_country`, `order_state`, `order_city`, `order_zipcode`
* **Product Catalog:** `department_name`, `category_name`, `product_name`, `product_price`, `product_status`, `department_id`, `category_id`, `product_card_id`
* **Order Economics & Terms:** `payment_type`, `shipping_mode`, `order_item_quantity`, `sales`, `order_item_discount`, `order_item_discount_rate`, `order_item_total`, `order_profit_per_order`, `order_item_profit_ratio`, `days_for_shipment_scheduled`

### B. Post-Shipment Outcomes & Targets (Strictly Forbidden as ML Inputs)
These features represent downstream operational events and leakage targets:
* **Delay Targets:** `late_delivery_risk`, `is_delayed`, `delivery_status`
* **Cancellation Targets:** `is_canceled`, `order_status`
* **Post-Dispatch Realized Metrics:** `days_for_shipping_real`, `transit_delay_days`, `shipping_date`, `order_to_shipping_hours`

---

## 9. HDFS Storage Location & Parquet/Snappy Format

The processed dataset was written directly to the Hadoop Distributed File System:

* **HDFS Target URI:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1`
* **Format:** Apache Parquet (columnar storage format)
* **Compression Codec:** Snappy (`spark.sql.parquet.compression.codec = snappy`)
* **Write Mode:** `.mode("errorifexists")` (ensures idempotent writes and guards against unintended overwrites)

### HDFS Directory Inventory
```
hdfs dfs -ls -h /chainsentinel/processed/dataco_clean_v1

-rw-r--r--   1 root supergroup          0 2026-11-03 19:16 _SUCCESS
-rw-r--r--   1 root supergroup      2.5 M 2026-11-03 19:16 part-00000-e4a64ea1-2765-40ae-b6df-72d11d0dec77-c000.snappy.parquet
-rw-r--r--   1 root supergroup      2.5 M 2026-11-03 19:16 part-00001-e4a64ea1-2765-40ae-b6df-72d11d0dec77-c000.snappy.parquet
-rw-r--r--   1 root supergroup      2.5 M 2026-11-03 19:16 part-00002-e4a64ea1-2765-40ae-b6df-72d11d0dec77-c000.snappy.parquet
-rw-r--r--   1 root supergroup      2.1 M 2026-11-03 19:16 part-00003-e4a64ea1-2765-40ae-b6df-72d11d0dec77-c000.snappy.parquet
```

* **Storage Efficiency:** Total size across 4 partition parts is approximately **9.6 MB**, achieving an approximate **10:1 compression ratio** relative to the 95.91 MB raw uncompressed CSV.

---

## 10. Comprehensive Validation Results

An automated post-execution verification script executed inside the cluster validated all operational constraints directly against HDFS:

| Verification Requirement | Verified Target | Verified Actual Result | Compliance Status |
| :--- | :---: | :---: | :---: |
| **Output Record Count** | 180,519 | **180,519** | PASS |
| **Output Column Count** | 52 | **52** | PASS |
| **Unique Order Item IDs** | 180,519 | **180,519** (100% distinct) | PASS |
| **Late Deliveries (`is_delayed = 1`)** | 98,977 | **98,977** (54.83%) | PASS |
| **Non-Late Deliveries (`is_delayed = 0`)** | 81,542 | **81,542** (45.17%) | PASS |
| **Canceled Orders Total** | 7,754 | **7,754** (4.30%) | PASS |
| **Canceled Orders Delayed (`is_delayed = 1`)** | 0 | **0** (0.00%) | PASS |
| **Target Discrepancies (`is_delayed != late_delivery_risk`)** | 0 | **0** | PASS |
| **Field Renaming: `order_to_shipping_hours`** | Exists | **Confirmed Present** | PASS |
| **Leakage Pruning: `actual_transit_hours`** | Removed | **Confirmed Absent** | PASS |
| **Taxonomy Preservation: Electronics Cat 13 (Footwear)** | 1,127 | **1,127** | PASS |
| **Taxonomy Preservation: Electronics Cat 37 (Outdoors)** | 2,029 | **2,029** | PASS |

---

## 11. Kafka Streaming Application Status

The real-time streaming infrastructure was monitored before, during, and after ETL execution to ensure zero interference:

* **Container Infrastructure:**
  * `chainsentinel-kafka`: **Up** (Kafka 4.4.0, ports `9092`, `29092`)
  * `chainsentinel-namenode`: **Up** (Hadoop 3.3.6 HDFS NameNode, port `8020`, `9870`)
  * `chainsentinel-datanode`: **Up** (Hadoop 3.3.6 HDFS DataNode)
  * `chainsentinel-spark-master`: **Up** (Spark 3.5.0 Master, port `7077`, `8080`)
  * `chainsentinel-spark-worker`: **Up** (Spark 3.5.0 Worker, port `8081`)
* **Spark Streaming Job Verification:**
  * **Application ID:** `app-20261103190004-0001`
  * **Application Name:** `ChainSentinel-Kafka-Streaming`
  * **Status:** **`RUNNING`**
  * **Allocated Cores:** 8 cores
  * **Topic:** `supply-chain-events`
  * **Streaming Checkpoint:** `hdfs://namenode:8020/chainsentinel/checkpoints/kafka_events`

The streaming pipeline continues uninterrupted.

---

## 12. Limitations & Future Considerations

1. **Category Taxonomy Ambiguity:**  
   The DataCo catalog retains category name `'Electronics'` under two distinct parent departments: `category_id = 13` (Department: Footwear) and `category_id = 37` (Department: Outdoors). Both were preserved as distinct records. When training ML models, feature encoders must index on `category_id` rather than raw text `category_name` to prevent loss of departmental distinction.
2. **Missing Customer Postal Codes:**  
   `customer_zipcode` has 3 missing records (< 0.01%), while `order_zipcode` has 155,679 missing records (86.24%). As documented, `order_zipcode` should not be used as a primary geospatial feature; downstream feature pipelines should utilize `order_city`, `order_state`, and `order_country`.
3. **Bilingual Geographic Naming:**  
   Destination countries are recorded in Spanish (`Estados Unidos`, `Francia`, `Alemania`), while regions are recorded in English (`Western Europe`, `Central America`). Downstream enrichment with external weather or geopolitical disruption data should incorporate a standardized ISO-3 translation layer.
4. **First-Class Shipping SLA Bias:**  
   First Class shipments experience a 95.32% delay rate due to a 1-day SLA threshold against a 2-day logistical fulfillment minimum. ML algorithms should evaluate feature interactions between `shipping_mode` and `days_for_shipment_scheduled` to prevent naive bias.

---

## 13. Phase 2 Completion Declaration

**Phase 2: Data Engineering, Batch ETL, and HDFS Storage is hereby officially completed.**

All objectives—including raw dataset profiling, schema standardization, column pruning, target leakage prevention, delay ground truth rectification, PySpark ETL execution, and HDFS Parquet storage validation—have been achieved and verified against the live infrastructure.

In compliance with the Mandatory Project Protection Rules:
* No Docker containers, networks, or volumes were modified, stopped, or recreated.
* No existing Kafka configurations or active streaming applications were interrupted.
* No changes were made to HDFS data directories outside the authorized target path.
* Phase 3 has not been started, awaiting authorization.


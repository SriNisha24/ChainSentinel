# ChainSentinel — Phase 5: Machine Learning & Predictive Analytics Readiness Report

**Project:** ChainSentinel (AI-Powered Supply Chain Disruption Management System)  
**Phase:** Phase 5: Machine Learning and Predictive Analytics  
**Document File:** `E:\BDA\ChainSentinel\reports\phase5\phase5_readiness_report.md`  
**Date of Audit:** 2026-11-04  
**Cluster Architecture:** Apache Spark 4.0.1 (OpenJDK 17.0.16) on Hadoop HDFS 3.3.6 & Python 3.10/3.11  

---

## 1. Executive Summary & Readiness Verdict

An initial inspection and environment readiness audit was performed across the ChainSentinel project infrastructure to verify all dependencies, runtime engines, data pipelines, and libraries prior to developing predictive models.

### Readiness Verdict: **BLOCKED PENDING DEPENDENCY APPROVAL**
* **The Blocker:** While Apache Spark 4.0.1 and Hadoop HDFS are healthy and operational, the Spark container's internal Python 3.10 runtime lacks the **`numpy`** package. In PySpark, importing `pyspark.ml` (machine learning classification, feature pipelines, and evaluation metrics) strictly requires `numpy` at module initialization and raises `ModuleNotFoundError: No module named 'numpy'`.
* **Action Required:** In strict compliance with **Mandatory Project Protection Rule 7** and **Section 2 of the Phase 5 instructions**, execution has stopped to request explicit approval to install `numpy` (and optionally `scipy`) inside the Spark containers (`chainsentinel-spark-master` and `chainsentinel-spark-worker`), and optionally `scikit-learn` inside the host `python-env`.

---

## 2. Infrastructure & Storage Inventory

| Infrastructure Asset | Specification / Metric | Current Status | Observational Notes |
| :--- | :--- | :---: | :--- |
| **Apache Spark Runtime** | Spark 4.0.1 (OpenJDK 17.0.16) | **HEALTHY** | Active on Master and Worker nodes |
| **Kafka Streaming Job** | `ChainSentinel-Kafka-Streaming` (`app-20261103190004-0001`) | **RUNNING** | Continuously active on 8 worker cores; 0 downtime |
| **HDFS Master & Worker** | Hadoop 3.3.6 (NameNode:8020, DataNode) | **HEALTHY** | All 5 Docker containers Up |
| **HDFS Total Capacity** | `1,006.85 GB` (1.0 TB) | **HEALTHY** | 9.92 MB current production DFS usage |
| **HDFS Available Space** | **`949.22 GB remaining`** (94.28% free) | **HEALTHY** | Abundant storage for models and data |
| **Host Storage (E: Drive)** | **`246.26 GB free`** (22.3 GB used) | **HEALTHY** | Local drive has ample space for artifacts |
| **Driver Heap Memory** | `2.0 GB` allocated on Spark Master | **HEALTHY** | Sufficient for batch model training |

---

## 3. Dataset Inspection & Schema Verification

The cleaned historical dataset in HDFS was inspected and verified readable:
* **HDFS URI:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1`
* **Format:** Apache Parquet with Snappy compression (4 partition files, ~9.6 MB total)
* **Total Records:** **180,519 rows**
* **Total Columns:** **52 columns**
* **Verified Primary Key:** `order_item_id` (180,519 distinct keys, 100% unique)
* **Temporal Bounds:** January 1, 2015 00:00:00 to January 31, 2018 23:38:00 (37 months)

### Schema Inventory (52 Columns)
1. **Identifiers (6):** `order_item_id`, `order_id`, `customer_id`, `department_id`, `category_id`, `product_card_id`
2. **Timestamps (2):** `order_date`, `shipping_date`
3. **Fulfillment & Status (7):** `payment_type`, `shipping_mode`, `days_for_shipment_scheduled`, `days_for_shipping_real`, `delivery_status`, `late_delivery_risk`, `order_status`
4. **Customer Origin Geography (10):** `customer_city`, `customer_state`, `customer_country`, `customer_zipcode`, `customer_street`, `customer_fname`, `customer_lname`, `customer_segment`, `latitude`, `longitude`
5. **Destination Geography (6):** `market`, `order_region`, `order_country`, `order_state`, `order_city`, `order_zipcode`
6. **Product Catalog (6):** `department_name`, `category_name`, `product_name`, `product_price`, `product_status`, `product_image`
7. **Financials & Economics (7):** `order_item_quantity`, `sales`, `order_item_discount`, `order_item_discount_rate`, `order_item_total`, `order_profit_per_order`, `order_item_profit_ratio`
8. **Engineered Analytical Metrics (8):** `transit_delay_days`, `is_delayed`, `is_canceled`, `order_year`, `order_month`, `order_day_of_week`, `order_hour`, `order_to_shipping_hours`

---

## 4. Target Feasibility & Data Leakage Governance

### 4.1 Primary Target Definition & Verification
* **Target Field:** `is_delayed` (IntegerType: 0 or 1).
* **Target Class Distribution:**
  * Positive Class (`is_delayed = 1`): **98,977 records (54.83%)** — exact match with `delivery_status == "Late delivery"`.
  * Negative Class (`is_delayed = 0`): **81,542 records (45.17%)** — comprises Advance Shipping (41,592), Shipping On Time (32,196), and Canceled Shipments (7,754).
* **Late Delivery Risk Agreement:** Verified `0` discrepancies between `is_delayed` and `late_delivery_risk`.
* **Canceled Orders Policy:** All **7,754 canceled orders** (`delivery_status == "Shipping canceled"`) represent aborted shipments where delivery was never completed. In accordance with Section 3 instructions, canceled shipments will be **explicitly filtered out** from the primary shipment delay classifier training and evaluation datasets, leaving **172,765 valid completed shipments** (98,977 delayed = 57.29%, 73,788 on-time/early = 42.71%).

### 4.2 Data Leakage Governance Boundaries
To guarantee pre-shipment validity, features are categorized into strict boundaries:
* **Valid Pre-Shipment Predictive Features:**
  * SLA & Fulfillment Policy: `shipping_mode`, `days_for_shipment_scheduled`, `payment_type`
  * Temporal / Calendar: `order_year`, `order_month`, `order_day_of_week`, `order_hour`
  * Product & Catalog: `department_id`, `category_id`, `product_price`
  * Destination Geography: `market`, `order_region`, `order_country`
  * Customer & Sourcing: `customer_segment`, `customer_state`, `latitude`, `longitude`
  * Commercial Terms: `order_item_quantity`, `sales`, `order_item_discount`, `order_item_discount_rate`, `order_item_total`
* **FORBIDDEN Post-Shipment & Leakage Variables (Strictly Excluded):**
  * `delivery_status`, `is_delayed`, `late_delivery_risk`, `days_for_shipping_real`, `transit_delay_days`, `order_to_shipping_hours`, `shipping_date`, `order_status`, `is_canceled`
  * Primary / Foreign Identifiers: `order_item_id`, `order_id`, `customer_id`, `customer_street`, `customer_fname`, `customer_lname`, `customer_zipcode`, `order_zipcode`

---

## 5. Library & Dependency Inventory

### 5.1 Spark Master Container Runtime (`chainsentinel-spark-master`)
* **Python Runtime:** Python 3.10.12
* **Installed Packages:**
  * `pip`: 22.0.2
  * `setuptools`: 59.6.0
  * `wheel`: 0.37.1
* **CRITICAL MISSING DEPENDENCY:** **`numpy`**
  * *Impact:* Attempting to import `from pyspark.ml.classification import LogisticRegression` fails with:
    ```
    ModuleNotFoundError: No module named 'numpy'
    ```
  * PySpark MLlib relies on `numpy` arrays for feature vector metadata, parameter serialization, and evaluation metrics.

### 5.2 Host Python Environment (`E:\BDA\ChainSentinel\python-env\`)
* **Python Runtime:** Python 3.11.2
* **Installed Packages:**
  * `pandas`: 3.1.0
  * `numpy`: 2.5.4
  * `pyarrow`: 26.0.1
  * `matplotlib`: 3.11.2
  * `seaborn`: 0.13.2
* **Installed Visualization Stack:** Ready for high-resolution PNG rendering (confusion matrices, ROC curves, feature importance).
* **Missing Host ML Packages (Optional):** `scikit-learn` and `scipy` are not currently installed on the host.

---

## 6. Proposed Dependency Resolution & Approval Request

To execute Phase 5 model development, the following non-destructive package installations are proposed:

1. **Inside Spark Containers (`chainsentinel-spark-master` and `chainsentinel-spark-worker`):**
   * Command: `docker exec chainsentinel-spark-master python3 -m pip install numpy` (and optionally `scipy`)
   * Purpose: Unlocks native PySpark MLlib (`pyspark.ml.classification`, `pyspark.ml.feature`, `pyspark.ml.evaluation`) for distributed Logistic Regression, Random Forest, and GBTClassifier training.
2. **Inside Host Python Environment (`E:\BDA\ChainSentinel\python-env\`):**
   * Command: `E:\BDA\ChainSentinel\python-env\Scripts\python.exe -m pip install scikit-learn scipy`
   * Purpose: Provides advanced client-side evaluation metrics (PR-AUC, ROC curves, classification reports) and supports Model 2 anomaly detection algorithms.

---

## 7. Next Steps Upon User Authorization

Upon receiving your approval:
1. Install `numpy` in the Spark container and `scikit-learn` in the host environment.
2. Verify PySpark MLlib pipeline imports.
3. Implement and train **Model 1: Shipment Delay Prediction** (Logistic Regression, Random Forest, GBT) with chronological temporal splitting.
4. Implement **Model 2: Supply-Chain Anomaly Detection** (IQR, Z-score, multi-dimensional statistical profiling).
5. Produce **Model 3: Disruption Impact Feasibility Assessment**.
6. Implement **Model 4: Demand / Capacity Forecasting Baseline**.
7. Persist models to `models/phase5/` and HDFS `/chainsentinel/models/phase5/`.
8. Generate all Phase 5 visualizations and final completion documentation.

*Phase 5 execution is currently paused awaiting your explicit approval to install the required Python packages.*


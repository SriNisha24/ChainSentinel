# ChainSentinel — Dataset Backend Capability Audit
## Architecture, Models, Data Provenance, and Gap Analysis for Dataset-Driven Intelligence

**Audit Date:** November 5, 2026  
**System Location:** `E:\BDA\ChainSentinel`  
**Audit Purpose:** Comprehensive inspection of the existing Big Data Analytics assets to establish a concrete capability inventory and roadmap for unified Dataset Intelligence (Workflow A) and Live Disruption Monitoring (Workflow B).

---

## 1. Executive Summary & Inventory Findings

ChainSentinel comprises extensive analytical engines built across 15 project phases. Our audit verified the exact state of code, data artifacts, production models, API endpoints, and storage systems:

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 CHAINSENTINEL DUAL-WORKFLOW TOPOLOGY                               │
├──────────────────────────────────────────────────┬─────────────────────────────────────────────────┤
│          WORKFLOW A: DATASET INTELLIGENCE        │      WORKFLOW B: LIVE DISRUPTION MONITORING     │
│   (Upload/Select CSV -> Validate -> Models)      │   (Terminal JSON -> Kafka -> Spark -> HDFS)     │
├──────────────────────────────────────────────────┼─────────────────────────────────────────────────┤
│ [DataCo Original] OR [Uploaded CSV]              │ Windows Terminal JSON Event Injection           │
│   │                                              │   │                                             │
│   ▼                                              │   ▼                                             │
│ Schema Normalization & Validation (20 Features)  │ Apache Kafka Broker:9092 (disruption-events)    │
│   │                                              │   │                                             │
│   ▼                                              │   ▼                                             │
│ ML Model Execution:                              │ Spark Structured Streaming (Ingestion/Filter)   │
│   • Delay Prediction (GBT / Tree Ensemble)       │   │                                             │
│   • Anomaly Detection (K-Means & Statistical)    │   ▼                                             │
│   • Disruption Impact (What-If Scenarios)        │ Hadoop HDFS 3.3.6:8020 (Checkpoints & Events)   │
│   • Demand Forecasting (Capacity Planning)       │   │                                             │
│   │                                              │   ▼                                             │
│   ▼                                              │ Downstream Analytical Pipelines:                │
│ Isolated Run Storage: data/analysis_runs/<id>/   │   • Phase 8 Shockwave Engine                    │
│   │                                              │   • Phase 9 MCDA Risk Assessment                │
│   ▼                                              │   • Phase 10 Recovery Knapsack Optimization     │
│ React Frontend: Dataset Analysis & Results View  │ React Frontend: Control-Room Shockwave Radar    │
└──────────────────────────────────────────────────┴─────────────────────────────────────────────────┘
```

---

## 2. Comprehensive Asset & Codebase Inventory

### 2.1 Datasets & Data Storage
1. **Original Raw DataCo Dataset:**
   - **Path:** `data/raw/DataCoSupplyChainDataset.csv`
   - **Size:** 95,910,149 bytes (~91.5 MB)
   - **Encoding:** ISO-8859-1 (Latin-1)
   - **Rows:** 180,519 transactions
   - **Columns:** 53 raw columns with mixed casing and parenthetical annotations (e.g., `Days for shipping (real)`, `order date (DateOrders)`).
   - **Quality Profile:** Zero missing values in core transactional keys (`Order Id`, `Product Price`, `Sales`), 100% null in `Product Description`, masked PII in `Customer Email` (`XXXXXXXXX`).
2. **Cleaned & Processed Parquet Storage:**
   - **Path:** `data/clean_parquet/` (4 Snappy-compressed partitions, 10.1 MB total).
   - **ETL Definition:** `docker/spark/batch/dataco_etl.py` standardizes 52 attributes, parses timestamps (`order_date`, `shipping_date`), standardizes currency and coordinates, and derives analytical targets (`is_delayed`, `transit_delay_days`).
3. **Historical Integration Run:**
   - **Authoritative Baseline Run:** `data/integration_runs/IRUN-20261104143752-A4CB8F/`
   - **Event ID:** `SIM-DISR-2026-001` (Port Closure, East Asia / China).
   - **Contains:** Phase 8 Shockwave outputs, Phase 9 Risk scoring, Phase 10 Knapsack recovery plans (Plan 5 recommended).

---

## 3. Production Machine Learning Models Inspection (Phase 5)

ChainSentinel includes 4 trained production machine learning model tasks stored under `models/phase5/`:

### 3.1 Model 1: Pre-Shipment Delivery Delay Prediction (`delay_model_v1`)
- **Objective:** Predict binary probability that an order will experience a shipping delay before dispatch.
- **Target Variable:** `is_delayed` (Binary: 1 = Late delivery, 0 = On time / advance).
- **Production Algorithm:** Gradient-Boosted Trees (GBT Classifier, test ROC-AUC = 0.775, Precision = 0.780).
- **Required Pre-Shipment Predictive Features (20 Total):**
  - **Categorical (6):** `shipping_mode`, `market`, `order_region`, `customer_segment`, `payment_type`, `department_name`.
  - **Numerical (14):** `days_for_shipment_scheduled`, `order_year`, `order_month`, `order_day_of_week`, `order_hour`, `product_price`, `order_item_quantity`, `sales`, `order_item_discount`, `order_item_discount_rate`, `order_item_total`, `order_profit_per_order`, `latitude`, `longitude`.
- **Strict Leakage Prevention:** Post-shipment features are strictly forbidden during inference:
  `delivery_status`, `days_for_shipping_real`, `transit_delay_days`, `order_to_shipping_hours`, `shipping_date`, `late_delivery_risk`, `order_status`, `is_canceled`.

### 3.2 Model 2: Supply Chain Anomaly Detection (`anomaly_detection_v1`)
- **Objective:** Dual-method multivariate outlier and operational bleed detection.
- **Artifact:** `models/phase5/anomaly_detection_v1/anomaly_thresholds.json`
- **Methodology:**
  1. Standard scaler transformation (7 features with calibrated `mean` and `std`).
  2. K-Means Euclidean distance scoring ($k=6$ cluster centers).
  3. Statistical rule evaluation (`profit_severe_loss` < -$166.73, `profit_critical_loss` < -$500.00, `discount_high_outlier` > $103.46).
- **Required Features (7 Numerical):**
  `product_price`, `order_item_quantity`, `order_item_discount`, `order_item_discount_rate`, `order_item_total`, `order_profit_per_order`, `days_for_shipment_scheduled`.

### 3.3 Model 3: Disruption Impact Scenario Estimation (`disruption_impact_v1`)
- **Objective:** What-if simulation engine modeling geographic port strikes, air cargo halts, container shortages, and peak carrier crunches.
- **Artifact:** `models/phase5/disruption_impact_v1/scenario_config.json`
- **Scenarios Evaluated:**
  - `SCENARIO_1_LATAM_PORT_CONGESTION` (35% capacity loss, 2-day delay shock).
  - `SCENARIO_2_EUROPE_AIRFREIGHT_FREEZE` (50% air capacity drop, 3-day delay shock).
  - `SCENARIO_3_PACIFIC_CONTAINER_SLOWDOWN` (25% capacity drop, 2-day delay shock).
  - `SCENARIO_4_GLOBAL_CARRIER_CRUNCH` (20% global capacity drop across all modes).
- **Compatibility Requirement:** Requires `market`, `order_region`, `shipping_mode`, `order_item_total`, and `order_profit_per_order`.

### 3.4 Model 4: Demand & Capacity Forecasting (`demand_forecasting_v1`)
- **Objective:** Daily order volume forecast and warehouse dispatch capacity requirement estimation.
- **Artifact:** `models/phase5/demand_forecasting_v1/model_metadata.json`
- **Features:** Lagged daily order volume (`lag_1`, `lag_2`, `lag_7`, `ma_7`, `ma_14`) and calendar features.
- **Capacity Planner:** Computes `required_capacity = forecasted_demand / target_utilization`, identifies capacity shortfalls and safety buffer orders.

---

## 4. Current State vs. Missing Capabilities Gap Analysis

| Functional Domain | Existing Implementation | Missing / Required Implementation | Action Required |
| :--- | :--- | :--- | :--- |
| **Dataset Selection** | Static path `data/clean_parquet/` hardcoded in Phase 11 backend loader. | Dynamic selection API supporting original DataCo CSV and uploaded CSVs. | Build `DatasetService` with catalog metadata and preview endpoints. |
| **CSV Upload** | Non-existent in backend. | Secure multipart upload, safe filename sanitization, size limits, format validation. | Create `POST /api/datasets/upload` with isolated directory storage. |
| **Dataset Validation** | Scripts validate DataCo columns during Spark ETL. | Runtime validation reporting missing columns, data types, missing values, duplicates, and model compatibility. | Implement lightweight validator in Python (pandas/pyarrow) returning structured diagnostics. |
| **Model Inference Engine** | Offline batch Spark inference scripts (`predict_delay.py`, `predict_anomalies.py`). | In-process, lightweight, real-time Python inference engine executable on uploaded datasets without overloading Spark. | Implement `InferenceEngine` in Python using calibrated weights, K-Means centers, and decision trees. |
| **Run Isolation & History** | Single integration run `IRUN-20261104143752-A4CB8F` hardcoded in `data_loader.py`. | Multi-dataset, multi-run isolation storing execution artifacts in `data/analysis_runs/<run_id>/`. | Create `AnalysisRunManager` preserving full run provenance and retrieval. |
| **Backend API Routing** | REST endpoints in `main.py` serve Phase 11 integration run outputs. | Endpoints for dataset catalog, upload, preview, analysis trigger, run history, and run inspection. | Mount `/api/datasets` and `/api/analysis` routers in `main.py`. |
| **Frontend Navigation** | 8 technical tabs centered around an operational metrics dashboard. | 9 enterprise navigation items focused on Dataset Analysis and results inspection. | Redesign frontend layout and build dedicated `DatasetAnalysisScreen` and `AnalysisResultsScreen`. |
| **Shockwave Radar** | Supply-chain SVG symbols implemented in `ShockwaveVisualizer.tsx`. | Seamless integration into Disruption Monitoring screen with honest operational lineage. | Preserve tactical control-room visualizer with recognized symbols. |

---

## 5. Architectural Blueprint for Implementation

1. **Safety & Zero-Spark Overload Guarantee:**
   - As mandated, we will NOT submit heavy Spark batch jobs that conflict with the running Spark Streaming application.
   - All dataset validation, CSV parsing, and model inference will be executed directly via Python (`pandas`, `numpy`, `scipy`) using the mathematically calibrated weights and parameters from `models/phase5/`.
2. **Strict Dataset & Run Isolation:**
   - Uploaded datasets stored exclusively under `data/datasets/uploaded/` with unique IDs (`DS-<timestamp>-<hash>`).
   - Original DataCo registered as immutable dataset `DS-DATACO-ORIGINAL`.
   - Every analysis run generates an isolated directory: `data/analysis_runs/<run_id>/run_results.json`.
3. **Genuine Predictions & Leakage Defense:**
   - Pre-shipment inference strictly forbids post-shipment target fields.
   - Incompatible datasets receive detailed compatibility warnings explaining which models can run and which cannot.


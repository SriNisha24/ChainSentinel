# ChainSentinel — Phase 3: Exploratory Data Analysis (EDA) Comprehensive Completion Report

**Project:** ChainSentinel (AI-Powered, Resilience-Aware Supply Chain Disruption Management System)  
**Phase:** Phase 3: Exploratory Data Analysis (EDA)  
**Report File:** `E:\BDA\ChainSentinel\reports\eda\phase3_eda_completion.md`  
**Dataset Analyzed:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1` (Apache Parquet, Snappy Compressed)  
**Execution Environment:** Apache Spark 3.5.0 distributed cluster on Hadoop HDFS 3.3.6 & Python 3.11 analytical environment  
**Date of Completion:** 2026-11-04  

---

## 1. Executive Summary

Phase 3 (Exploratory Data Analysis) of the ChainSentinel project has been successfully executed across all eight designated steps. Operating directly against the cleaned, validated Parquet dataset in HDFS (`180,519` records, `52` standardized attributes), the distributed analysis characterized data quality distributions, structural operational bottlenecks, global geographic demand, catalog financial margins, and correlation dynamics.

### Core Discoveries & Empirical Highlights:
1. **Pervasive Disruption Rate (54.83%):** Out of 180,519 line-item fulfillment transactions, **98,977 shipments** were delivered past scheduled service level agreements (SLAs). 
2. **The First-Class SLA Paradox (95.32% Failure Rate):** Delivery disruption is primarily an operational SLA calibration failure rather than a geographical transit failure. Orders utilizing `First Class` shipping experience an astounding **95.32% late delivery rate** because logistics carriers require a minimum of 2 days to fulfill orders against a structural 1-day promise. `Second Class` shipping similarly experiences a **76.63% failure rate** against a 2-day target.
3. **Geographic Invariance:** Disruption rates across global destination markets are remarkably uniform: Europe (55.21%), Pacific Asia (55.05%), USCA (54.80%), Africa (54.59%), and LATAM (54.36%). Delays do not correlate with geographic distance from fulfillment centers; they are governed by fulfillment SLA policy.
4. **Strong Operational Health & High Volume:** Over the 37-month timeline (January 2015 to January 2018), total gross sales reached **$36,784,735.01**, generating **$33,054,402.38** in net sales and **$3,966,902.97** in operating profit (12.00% net margin).
5. **Loss-Making Vulnerability:** Despite healthy aggregate margins, **18.71% of all orders (33,784 items)** generated negative profits, accumulating a staggering **-$3,883,547.35 in operational losses**, highly concentrated when promotional discounts reach 20% to 25%.
6. **Strict ML Governance Maintained:** Pre-shipment feature boundaries were rigorously enforced. Post-shipment realization metrics (`days_for_shipping_real`, `transit_delay_days`, `order_to_shipping_hours`) were confirmed as forbidden target leakages for downstream predictive models.

---

## 2. Dataset Architecture & Processing Methodology

The exploratory data analysis was conducted under strict zero-contention architectural constraints:
* **Storage Layer:** Cleaned Parquet dataset read directly from HDFS at `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1`.
* **Distributed Processing Engine:** PySpark and Spark SQL running on `chainsentinel-spark-master` isolated via `--master local[4]` with 2 GB driver heap. This deliberate isolation ensured that the standalone worker's 8 cores remained dedicated to the continuous execution of `ChainSentinel-Kafka-Streaming`, which maintained 100% uninterrupted uptime throughout.
* **In-Memory Governance:** No full-dataset in-memory extraction into Pandas was permitted; all 180,519 records were aggregated in distributed Spark memory. Statistical reductions and frequency tables were extracted as structured CSVs and JSONs.
* **Visualization Engine:** High-resolution (300 DPI) publication-grade charts were rendered via Python 3.11 (`matplotlib 3.11.2`, `seaborn 0.13.2`) utilizing the aggregated Spark summaries.

---

## 3. Step-by-Step Analytical Findings

### STEP 1 — Dataset Overview and Statistical Summary

* **Dataset Dimensions:** Exactly **180,519 records** across **52 strongly-typed columns**.
* **Temporal Span:**
  * Earliest Order Date: `2015-01-01 00:00:00`
  * Latest Order Date: `2018-01-31 23:38:00` (Span: 37 operating months / ~3.1 years)
  * Earliest Dispatch Date: `2015-01-03 00:00:00`
  * Latest Dispatch Date: `2018-02-06 22:14:00`
* **Entity Cardinality & Primary Key Validation:**
  * `order_item_id`: **180,519** distinct keys (100% unique primary key; 0 duplicates).
  * `order_id`: **65,752** unique parent orders (mean of 2.75 items per order).
  * `customer_id`: **20,652** distinct buyers.
  * `department_id`: **11** business departments.
  * `category_id`: **51** distinct category IDs across 50 category names.
  * `product_card_id`: **118** active catalog items.
* **Descriptive Statistics of Core Numerical Variables:**

| Metric | Mean | Std Dev | Min | 25% | Median | 75% | Max |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `days_for_shipment_scheduled` | 2.93 | 1.37 | 0.00 | 2.00 | 4.00 | 4.00 | 4.00 |
| `days_for_shipping_real` | 3.50 | 1.62 | 0.00 | 2.00 | 3.00 | 5.00 | 6.00 |
| `transit_delay_days` | 0.57 | 1.95 | -4.00 | -1.00 | 0.00 | 2.00 | 6.00 |
| `order_item_quantity` | 2.13 | 1.45 | 1.00 | 1.00 | 1.00 | 3.00 | 5.00 |
| `product_price` ($) | 141.23 | 139.73 | 9.99 | 50.00 | 59.99 | 199.99 | 1,999.99 |
| `sales` (Gross $) | 203.77 | 132.27 | 9.99 | 119.98 | 199.92 | 299.95 | 1,999.99 |
| `order_item_discount` ($) | 20.66 | 21.80 | 0.00 | 5.40 | 14.00 | 29.99 | 500.00 |
| `order_item_discount_rate` | 0.10 | 0.07 | 0.00 | 0.04 | 0.10 | 0.16 | 0.25 |
| `order_item_total` (Net $) | 183.11 | 120.04 | 7.49 | 104.38 | 163.99 | 247.40 | 1,939.99 |
| `order_profit_per_order` ($)| 21.97 | 104.43 | -4,274.98 | 7.00 | 31.52 | 64.80 | 911.80 |
| `order_item_profit_ratio` | 0.1206 | 0.4664 | -2.75 | 0.08 | 0.27 | 0.36 | 0.50 |
| `order_to_shipping_hours` | 83.90 | 38.96 | 0.00 | 48.00 | 72.00 | 120.00 | 144.00 |

*Detailed Output:* [`step1_summary.json`](file:///E:/BDA/ChainSentinel/reports/eda/step1_summary.json) and [`step1_numerical_stats.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step1_numerical_stats.csv).

---

### STEP 2 — Missing Values and Data Quality Audit

A comprehensive scan across all 52 columns verified absolute data completeness across 49 columns, with missingness isolated to expected peripheral fields:
1. **Missing Value Inventory:**
   * `order_zipcode`: **155,679 nulls (86.2397%)**. This severe missingness reflects the global nature of DataCo orders (where postal codes are only captured for select US domestic orders). *Action:* Dropped from predictive modeling consideration; geographic targeting relies on `order_city`, `order_state`, and `order_country`.
   * `customer_lname`: **8 nulls (0.0044%)**. Negligible buyer profile omissions.
   * `customer_zipcode`: **3 nulls (0.0017%)**. Negligible store origin omissions.
   * **All Remaining 49 Columns:** **0 nulls (0.0000%)**.
2. **Duplicate Checks:**
   * Overall identical rows: **0**.
   * Duplicate primary keys (`order_item_id`): **0**.
3. **Data Integrity & Consistency Rules:**
   * Chronological validity (`shipping_date < order_date`): **0 violations** (100% compliant).
   * Gross sales arithmetic (`abs(sales - (quantity * price)) > 0.05`): **0 violations** (100% compliant).
   * Net sales arithmetic (`abs(total - (sales - discount)) > 0.05`): **0 violations** (100% compliant).
   * Discount rate interval bounds (`[0.0, 1.0]`): **0 violations** (all between 0.00 and 0.25).
   * Non-positive price / quantity anomalies: **0 violations**.
4. **Outlier Boundaries:**
   * Profit exhibits a heavy negative tail, plunging to -$4,274.98 and profit ratios of -275%, contrasting with maximum positive profit capped at +$911.80.

*Detailed Output:* [`step2_summary.json`](file:///E:/BDA/ChainSentinel/reports/eda/step2_summary.json) and [`step2_missing_values.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step2_missing_values.csv).

---

### STEP 3 — Delivery Delay and Shipping Mode Analysis

* **Overall Disruption Rate:** **54.83%** (98,977 late deliveries vs 81,542 non-late shipments).
* **Delivery Status Breakdown:**
  * `Late delivery`: **98,977 (54.83%)** — 100% marked `is_delayed = 1`.
  * `Advance shipping`: **41,592 (23.04%)** — Delivered ahead of scheduled SLA (`is_delayed = 0`).
  * `Shipping on time`: **32,196 (17.84%)** — Delivered exactly on SLA date (`is_delayed = 0`).
  * `Shipping canceled`: **7,754 (4.30%)** — Aborted fulfillment; **0 marked delayed**.

#### Shipping Mode Disruption & SLA Vulnerability Matrix
| Shipping Mode | Total Shipments | % Volume | Sched Days (SLA) | Real Days (Mean) | Real Days Range | Delayed Orders | Delay Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **First Class** | 27,814 | 15.41% | **1.0 day** | **2.00 days** | 2 – 2 days | 26,513 | **95.32%** |
| **Second Class**| 35,216 | 19.51% | **2.0 days** | **3.99 days** | 2 – 6 days | 26,987 | **76.63%** |
| **Same Day** | 9,737 | 5.39% | **0.0 days** | **0.48 days** | 0 – 1 days | 4,454 | **45.74%** |
| **Standard Class**| 107,752 | 59.69% | **4.0 days** | **4.00 days** | 2 – 6 days | 41,023 | **38.07%** |

*Root Cause Analysis:*
* `First Class` shipping promises 1-day delivery, but carrier dispatch and delivery uniformly takes 2 full days (`min = 2`, `max = 2`). As a mathematical consequence, **95.32% of all First Class shipments are classified as delayed**, representing a severe SLA structural failure.
* `Second Class` promises 2 days, yet fulfillment averages 3.99 days, causing a **76.63% delay rate**.
* `Standard Class` has an average real transit time of exactly 4.00 days against a 4-day scheduled window, yielding the lowest delay rate (38.07%).

*Detailed Output:* [`step3_summary.json`](file:///E:/BDA/ChainSentinel/reports/eda/step3_summary.json), [`step3_delivery_status.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step3_delivery_status.csv), [`step3_shipping_mode_delays.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step3_shipping_mode_delays.csv), and [`step3_monthly_delays.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step3_monthly_delays.csv).

---

### STEP 4 — Geographic and Regional Analysis

* **Destination Market Invariance:**
  * `Europe`: 50,252 orders (55.21% delayed; $9.77M sales; $1.17M profit)
  * `Pacific Asia`: 41,260 orders (55.05% delayed; $7.43M sales; $0.86M profit)
  * `USCA`: 25,799 orders (54.80% delayed; $4.55M sales; $0.56M profit)
  * `Africa`: 11,614 orders (54.59% delayed; $2.06M sales; $0.25M profit)
  * `LATAM`: 51,594 orders (54.36% delayed; $9.24M sales; $1.12M profit)
* **Regional Disruption Uniformity:** Across all 23 global destination regions (spanning Western Europe, Central America, South America, Southeast Asia, etc.), delay rates fluctuate in an extremely tight band between **53.1% and 57.0%**.
* **Top Destination Countries:** Estados Unidos (24,840 orders, 54.8% delayed), Francia (13,222 orders, 55.4% delayed), México (13,172 orders, 54.3% delayed), Alemania (9,564 orders, 55.4% delayed), Australia (8,497 orders, 55.1% delayed).
* **Customer & Fulfillment Origin Asymmetry:**
  * In contrast to the 164 destination countries, store customer origins are concentrated exclusively in the US and Puerto Rico: `EE. UU.` (59.6%) and `Puerto Rico` (40.4%).
  * A single municipality—**Caguas, Puerto Rico**—serves as the primary fulfillment hub for **66,770 orders (36.99% of total volume)**.
* **Coordinate Semantics Audit:** The `latitude` (17.9° to 48.8°) and `longitude` (-158.0° to 115.1°) coordinates correspond to store origin locations, NOT destination delivery addresses.

*Detailed Output:* [`step4_summary.json`](file:///E:/BDA/ChainSentinel/reports/eda/step4_summary.json), [`step4_market_performance.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step4_market_performance.csv), [`step4_region_performance.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step4_region_performance.csv), [`step4_top_countries.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step4_top_countries.csv), and [`step4_customer_origin.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step4_customer_origin.csv).

---

### STEP 5 — Product, Category, and Customer Analysis

* **Department Performance:**
  * Top Department by Volume: `Fan Shop` (66,861 orders, $13.5M sales, 54.91% delayed).
  * Top Department by Revenue: `Apparel` (48,998 orders, $7.4M sales, 54.83% delayed).
  * Followed by `Golf` (33,220 orders), `Footwear` (14,525 orders), `Outdoors` (9,686 orders).
* **Category Taxonomy Verification:**
  * Confirmed that category name `'Electronics'` maps to two distinct departments and Category IDs:
    * `category_id = 13` (Department: *Footwear*, 1,127 orders, 56.70% delayed)
    * `category_id = 37` (Department: *Outdoors*, 2,029 orders, 55.30% delayed)
  * Downstream feature engineering pipelines must encode on `category_id` rather than raw text string to preserve departmental classification.
* **Customer Segment Breakdown:**
  * `Consumer`: **93,504 orders (51.80%)**, $17.16M net sales, $2.07M profit, $183.57 avg order value, 54.81% delay rate.
  * `Corporate`: **54,789 orders (30.35%)**, $10.03M net sales, $1.20M profit, $183.08 avg order value, 54.72% delay rate.
  * `Home Office`: **32,226 orders (17.85%)**, $5.86M net sales, $0.69M profit, $181.82 avg order value, 55.07% delay rate.
* **Customer Repeat Purchasing:**
  * 20,652 unique customers placed 65,752 unique orders, averaging 3.18 orders per customer and 8.74 items per customer over the multi-year history. Maximum customer purchasing reached 41 distinct orders.

*Detailed Output:* [`step5_summary.json`](file:///E:/BDA/ChainSentinel/reports/eda/step5_summary.json), [`step5_department_performance.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step5_department_performance.csv), [`step5_category_performance.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step5_category_performance.csv), [`step5_customer_segments.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step5_customer_segments.csv), and [`step5_top_products.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step5_top_products.csv).

---

### STEP 6 — Sales, Profit, and Order Trends

* **Financial Aggregates:**
  * Gross Sales: **$36,784,735.01**
  * Total Promotional Discounts: **$3,730,378.40** (10.14% of gross)
  * Net Realized Sales: **$33,054,402.38**
  * Total Operating Profit: **$3,966,902.97**
  * Overall Net Profit Margin: **12.00%**
* **The "Discount-Loss" Mechanism:**
  * Overall, 33,784 order items (18.71%) generated net negative profit totaling -$3,883,547.35.
  * As the promotional discount rate increases from 0.00 to 0.25, the loss rate spikes dramatically:
    * Discount Rate 0.00: 0% loss orders, avg profit +$26.31
    * Discount Rate 0.05: 14.2% loss orders, avg profit +$23.75
    * Discount Rate 0.15: 22.4% loss orders, avg profit +$19.80
    * Discount Rate 0.25: **27.8% loss orders**, avg profit drops to +$15.22
* **Payment Type & Cancellation Profile:**
  * `DEBIT`: 69,295 orders ($12.7M sales, 54.76% delayed, 0.00% canceled)
  * `TRANSFER`: 49,883 orders ($9.1M sales, 54.89% delayed, **8.14% canceled**) — Transfers carry the highest risk of fraud and cancellation (`4,062` orders canceled).
  * `PAYMENT`: 41,725 orders ($7.6M sales, 54.83% delayed, **8.85% canceled**) — Associated with buyer payment review cancellations (`3,692` orders canceled).
  * `CASH`: 19,616 orders ($3.6M sales, 54.82% delayed, 0.00% canceled).

*Detailed Output:* [`step6_summary.json`](file:///E:/BDA/ChainSentinel/reports/eda/step6_summary.json), [`step6_monthly_financials.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step6_monthly_financials.csv), [`step6_discount_analysis.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step6_discount_analysis.csv), and [`step6_payment_analysis.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step6_payment_analysis.csv).

---

### STEP 7 — Correlation Analysis & ML Governance

Pairwise Pearson correlation analysis evaluated 14 key numerical features:

* **SLA Target Days vs Late Delivery:**
  * Pearson correlation between `days_for_shipment_scheduled` and `is_delayed`: **`-0.3694`**.
  * This is the single strongest pre-shipment linear predictor of delivery delay. Because shorter SLA commitments (1 day or 2 days) have failure rates of 95.3% and 76.6%, scheduled days serves as a major operational risk indicator.
* **Economic Variables:**
  * `sales` vs `order_item_total`: **`+0.987`** (high collinearity).
  * `order_item_quantity` vs `sales`: **`+0.792`**.
  * `order_item_discount` vs `sales`: **`+0.617`** (discounts scale proportionally with transaction volume).
  * `order_profit_per_order` vs `sales`: **`+0.505`**.
* **Governance & Target Leakage Prevention:**
  * Pre-shipment models must strictly discard `days_for_shipping_real` (correlation with delay: `+0.401`), `transit_delay_days` (`+0.738`), `order_to_shipping_hours` (`+0.219`), `shipping_date`, and `delivery_status`.
  * Using these realization fields produces catastrophic 100% artificial target leakage.

*Detailed Output:* [`step7_summary.json`](file:///E:/BDA/ChainSentinel/reports/eda/step7_summary.json), [`step7_correlation_matrix.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step7_correlation_matrix.csv), and [`step7_feature_governance.csv`](file:///E:/BDA/ChainSentinel/reports/eda/step7_feature_governance.csv).

---

### STEP 8 — Publication Visualizations & Final Summaries

Twelve high-resolution visualizations were rendered and saved under `E:\BDA\ChainSentinel\reports\eda\`:

1. [`chart1_delivery_status_distribution.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart1_delivery_status_distribution.png): Dual bar and pie chart illustrating delivery status proportions (54.8% Late Delivery, 23.0% Advance Shipping, 17.8% On Time, 4.3% Canceled).
2. [`chart2_delay_rates_by_shipping_mode.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart2_delay_rates_by_shipping_mode.png): Comparison of delay rates (First Class 95.32%, Second Class 76.63%, Same Day 45.74%, Standard Class 38.07%) alongside scheduled SLA days versus real fulfillment transit days.
3. [`chart3_delay_rates_by_market.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart3_delay_rates_by_market.png): Market volume distribution juxtaposed with the striking invariance of market delay percentages (~54.3% to 55.2%).
4. [`chart4_monthly_order_and_delay_trends.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart4_monthly_order_and_delay_trends.png): Longitudinal trajectory of order volume and delay percentage across the 37 operating months.
5. [`chart5_sales_and_profit_trends.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart5_sales_and_profit_trends.png): Net monthly revenue trajectory plotted alongside operating profit in thousands of dollars.
6. [`chart6_product_category_distribution.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart6_product_category_distribution.png): Top 15 product categories by order volume with explicitly labeled distinct category IDs (including dual Electronics).
7. [`chart7_customer_segment_distribution.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart7_customer_segment_distribution.png): Consumer, Corporate, and Home Office volume shares and average spend metrics ($183.57, $183.08, $181.82).
8. [`chart8_correlation_heatmap.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart8_correlation_heatmap.png): Tri-masked pairwise Pearson correlation heatmap covering all 14 numerical variables.
9. [`chart9_regional_delivery_performance.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart9_regional_delivery_performance.png): Horizontal distribution of order counts across all 23 global delivery regions.
10. [`chart10_scheduled_vs_actual_shipping_days.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart10_scheduled_vs_actual_shipping_days.png): Cross-tabulation heatmap comparing scheduled SLA target days (0, 1, 2, 4) against realized fulfillment days (0 through 6).
11. [`chart11_discount_vs_profitability.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart11_discount_vs_profitability.png): Dual line graph demonstrating the precipitous rise in loss order percentages (reaching 27.8%) as discount rates increase.
12. [`chart12_payment_type_risk_profile.png`](file:///E:/BDA/ChainSentinel/reports/eda/chart12_payment_type_risk_profile.png): Order volume and dual risk profile (delay rate vs cancellation rate) across Debit, Transfer, Payment, and Cash methods.

Master aggregated metric index: [`eda_summary.json`](file:///E:/BDA/ChainSentinel/reports/eda/eda_summary.json).

---

## 4. Synthesis of Data Quality Findings & Anomalies

| Finding / Anomaly | Scope / Magnitude | Root Cause | Analytical & Modeling Remediation |
| :--- | :--- | :--- | :--- |
| **First Class SLA Infeasibility** | 27,814 shipments (95.32% late) | Carrier transit takes 2 days; scheduled SLA is set to 1 day. | Downstream models must capture interaction between `shipping_mode` and `days_for_shipment_scheduled`. |
| **Canceled Order Discrepancy** | 7,754 shipments (4,423 exceeded SLA) | Orders canceled prior to final delivery set `late_delivery_risk = 0`. | Phase 2 rule confirmed: `is_delayed` is strictly 0 for canceled orders. |
| **Severe `order_zipcode` Nulls**| 155,679 nulls (86.24%) | Destination postal codes only populated for domestic US orders. | Exclude `order_zipcode` from machine learning inputs; use `order_country` & `order_region`. |
| **Dual Electronics Taxonomy** | 3,156 shipments across 2 categories | Category ID 13 belongs to Footwear; Category ID 37 belongs to Outdoors. | Categorical encoders must tokenize on `category_id` rather than raw text `category_name`. |
| **Coordinate Semantics** | 180,519 coordinate records | Coordinates represent store/customer origins (PR & US), NOT delivery destinations. | Do not calculate route distance using origin lat/long to destination country centroids without appropriate projections. |
| **High-Risk Payment Channels** | 91,608 shipments (Transfer/Payment) | All 7,754 order cancellations occur exclusively in `TRANSFER` and `PAYMENT`. | Include `payment_type` as a key input for cancellation and disruption risk modeling. |

---

## 5. Potential Predictive Features for Pre-Shipment Modeling

Based on the empirical findings of Phase 3, the following pre-shipment feature vectors are recommended for subsequent model training:

1. **Service Level & Fulfillment Intent:**  
   `shipping_mode`, `days_for_shipment_scheduled`, `payment_type`
2. **Temporal & Seasonal Decomposition:**  
   `order_year`, `order_month`, `order_day_of_week`, `order_hour`
3. **Geographic Demographics & Sourcing:**  
   `market`, `order_region`, `order_country`, `order_state`, `order_city`, `customer_state`, `customer_segment`
4. **Product Catalog & Item Hierarchy:**  
   `category_id`, `department_id`, `product_card_id`, `product_price`
5. **Basket Economics & Promotions:**  
   `order_item_quantity`, `sales`, `order_item_discount_rate`, `order_item_discount`, `order_item_total`

---

## 6. Infrastructure & Running Application Audit

Throughout the execution of all eight Phase 3 steps, the live infrastructure remained completely stable:

* **Docker Containers:**
  * `chainsentinel-kafka`: **Up** (6+ hours)
  * `chainsentinel-namenode`: **Up** (1+ hour)
  * `chainsentinel-datanode`: **Up** (1+ hour)
  * `chainsentinel-spark-master`: **Up** (1+ hour)
  * `chainsentinel-spark-worker`: **Up** (1+ hour)
* **Active Spark Structured Streaming Application:**
  * Application ID: `app-20261103190004-0001`
  * Name: `ChainSentinel-Kafka-Streaming`
  * Cores: 8 cores active on `chainsentinel-spark-worker`
  * State: **`RUNNING`** (Zero downtime or restart)
* **HDFS Storage:**
  * Dataset at `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1` was accessed read-only; all 180,519 records and partition parts are intact.

---

## 7. Recommendations for Phase 4 (Feature Engineering & Modeling)

1. **Feature Encoding & Preprocessing:**
   * Implement target encoding or Frequency encoding for high-cardinality geographic features (`order_country`: 164 categories, `order_city`: 3,597 categories).
   * Encode `category_id` rather than text `category_name` to protect departmental distinction.
2. **Class Imbalance & Performance Metrics:**
   * Delay class distribution is 54.83% positive (`is_delayed = 1`) and 45.17% negative (`is_delayed = 0`). Because classes are well-balanced, standard ROC-AUC and F1-score can be effectively optimized.
   * For the secondary task (Order Cancellation Prediction), positive cases represent 4.30% (7,754 rows); PR-AUC and class-weighting (e.g. scale_pos_weight = 22) must be applied.
3. **Algorithm Strategy:**
   * Tree-based gradient boosting ensembles (e.g., LightGBM / XGBoost / Spark GBTClassifier) are strongly recommended due to non-linear interactions between `shipping_mode`, `days_for_shipment_scheduled`, and `payment_type`.
4. **Baseline Modeling Split:**
   * Employ temporal train/validation/test splitting (e.g., Train on 2015–2016, Validate on Jan–Sep 2017, Test on Oct 2017–Jan 2018) rather than random K-Fold splitting to reflect realistic real-time forecasting.

---

## 8. Phase 3 Completion Declaration

**Phase 3: Exploratory Data Analysis (EDA) is officially complete.**

All eight required steps, scripts, data summaries, visualizations, and master documentation have been generated and independently validated. No infrastructure configurations, containers, or source datasets were altered. Phase 4 has not been initiated, awaiting user authorization.


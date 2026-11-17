# ChainSentinel — Phase 5, Model 2: Supply-Chain Anomaly Detection Report

**Project:** ChainSentinel — Autonomous Supply Chain Risk & Predictive Analytics  
**Phase:** Phase 5 — Machine Learning and Predictive Analytics  
**Component:** Model 2 — Supply-Chain Anomaly Detection  
**Execution Timestamp:** 2026-11-04  
**Engine:** Apache Spark 4.0.1 / PySpark MLlib (`StandardScaler`, `KMeans`) & Host Python 3.10  
**Dataset:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1` (180,519 records × 52 columns)

---

## 1. Executive Summary & Objective

In Phase 5 of the ChainSentinel project, **Model 2: Supply-Chain Anomaly Detection** has been implemented, executed, evaluated, visualised, and persisted. 

The primary business objective is to identify highly unusual, irregular, or economically hazardous patterns in supply-chain transactions without relying on artificial or unavailable ground-truth labels. The unsupervised pipeline detects:
- Catastrophic operational profit bleed (transactions losing up to -$4,274.98).
- Disproportionate discounts and margin inversions (maximum discounts on high-value orders resulting in net operational deficits).
- Extreme high-value transaction outliers.
- Complex multivariate operational anomalies across 7-dimensional standardized business feature space.

### Summary Metrics:
- **Total Records Analyzed:** **180,519 transactions** (100% evaluated).
- **Method A (Robust Statistical / IQR):** Flagged **8,909 transactions** (**4.94%**).
- **Method B (Multivariate $K$-Means Centroid Distance):** Flagged **3,711 transactions** (**2.06%**) at the empirical $P_{98}$ cutoff ($d \ge 3.755$).
- **Consensus Flags (Both Methods Agree):** **3,312 transactions** (**1.83%**), Jaccard similarity = **0.3558**.
- **Ensemble Union (Total Unique Anomalies):** **9,308 transactions** (**5.16%**).
- **Multi-Tier Operational Severity:**
  - **CRITICAL:** 1,251 transactions (**0.69%**)
  - **HIGH:** 1,726 transactions (**0.96%**)
  - **MEDIUM:** 6,331 transactions (**3.51%**)
  - **LOW:** 2,870 transactions (**1.59%**)
  - **NORMAL:** 168,341 transactions (**93.25%**)
- **Temporal Stability:** Anomaly rates remain stable across calendar years: 2015 (**4.81%**), 2016 (**4.77%**), 2017 (**6.05%**), 2018 (**4.38%**).

---

## 2. Dataset Description & Readiness

- **Dataset Path:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1`
- **Total Rows:** 180,519
- **Total Columns:** 52
- **Null / Missing Value Audit:** All 7 selected numerical features and 5 categorical context columns contain **0 null and 0 NaN values** (100% clean).
- **Preservation of Loss Records:** Zero negative-profit orders were removed. In total, **33,784 records (18.71%)** exhibit negative profit, extending down to -$4,274.98. These records represent essential operational risk signals.

---

## 3. Feature Selection & Data Governance

### 3.1 Excluded Leakage & Identifier Fields
In strict adherence to project protection rules and sound ML governance:
1. **Model 1 Target & Post-Shipment Actuals Excluded:** `is_delayed`, `late_delivery_risk`, `delivery_status`, `days_for_shipping_real`, `transit_delay_days`, `order_to_shipping_hours`, `shipping_date`.
2. **Customer PII & Non-Generalizable Text Excluded:** Customer names, emails, passwords, street addresses, and zip codes.
3. **Transaction Identifiers:** `order_id`, `order_item_id`, and `order_date` were preserved exclusively for record tracking in output deliverables and were **never fed into model feature matrices**.

### 3.2 Selected Feature Space (7 Numerical Features)
To prevent collinearity distortion (specifically between gross `sales` and `order_item_total`, where $r = 0.9897$), the multivariate feature space retained the net received cashflow and core operational drivers:

```python
mv_num_cols = [
    "product_price",                # Catalog unit list price
    "order_item_quantity",          # Units purchased per order item (discrete 1 to 5)
    "order_item_discount",          # Absolute currency discount amount deducted
    "order_item_discount_rate",     # Fractional discount rate applied (0.00 to 0.25)
    "order_item_total",             # Net transaction cashflow received after discount
    "order_profit_per_order",       # Operational net margin recorded
    "days_for_shipment_scheduled"   # Contractual delivery SLA window (0 to 4 days)
]
```

---

## 4. Preprocessing & Scaling

1. **Standardization:**
   Because features operate across vastly disparate physical units (e.g., dollar amounts in thousands vs discount rates in hundredths), raw features were transformed via PySpark `StandardScaler`:
   $$z_j = \frac{x_j - \mu_j}{\sigma_j}$$
   Mean and standard deviation vectors were computed and saved in the artifact metadata:
   - `product_price`: $\mu = 141.23, \sigma = 139.73$
   - `order_item_quantity`: $\mu = 2.13, \sigma = 1.45$
   - `order_item_discount`: $\mu = 20.66, \sigma = 21.80$
   - `order_item_discount_rate`: $\mu = 0.10, \sigma = 0.07$
   - `order_item_total`: $\mu = 183.11, \sigma = 120.04$
   - `order_profit_per_order`: $\mu = 21.98, \sigma = 104.43$
   - `days_for_shipment_scheduled`: $\mu = 2.93, \sigma = 1.37$
2. **Vector Assembly:** Consolidated into a unified 7-dimensional dense vector `scaled_features`.

---

## 5. Dual Anomaly Detection Algorithms

### Method A: Robust Statistical Anomaly Detection (Rule-Based & IQR)
Applies non-parametric, quantile-derived threshold logic to isolate single-vector operational breakdowns:
1. **Extreme Operational Loss:** $\text{profit} \le Q_{25} - 3 \times IQR = 6.91 - 3(57.88) = -\$166.73$.
2. **Critical Operational Loss:** $\text{profit} \le -\$500.00$.
3. **High-Value Transaction Outlier:** $\text{total} \ge Q_{75} + 3 \times IQR = 247.40 + 3(143.02) = \$676.46$.
4. **Excessive Discount Inversion:** $\text{discount} \ge \$103.46$ OR ($\text{discount\_rate} \ge 20\%$ with negative profit on orders $\ge \$200$).
5. **Compound Volume Inversion:** Bulk purchase ($\text{quantity} \ge 4$) + high discount ($\ge 20\%$) resulting in substantial deficit ($\le -\$50$).

Composite Statistical Anomaly Score ($S_{\text{stat}} \in [0.0, 1.0]$):
$$S_{\text{stat}} = 0.40 \cdot I_{\text{loss}} + 0.30 \cdot I_{\text{discount}} + 0.20 \cdot I_{\text{compound}} + 0.10 \cdot I_{\text{value}}$$
Flagged if $S_{\text{stat}} \ge 0.20$.

### Method B: Multivariate Distance-to-Centroid Anomaly Detection ($K$-Means)
- Unsupervised $K$-Means clustering ($K=6$, `maxIter=25`, `seed=42`) fitted on the 7-dimensional standardized feature space.
- Clusters naturally partition the operational landscape (e.g., volume apparel, high-margin equipment, loss-leader promotions, luxury goods).
- For each record $x$, Euclidean distance to its assigned cluster centroid $c_k$ is calculated:
  $$d(x, c_k) = \sqrt{\sum_{j=1}^7 (z_j - c_{k,j})^2}$$
- **Empirical Distance Percentile Cutoffs:**
  - $P_{90} = 2.486$
  - $P_{95} = 2.960$ (Marginal baseline)
  - $P_{98} = 3.755$ (Multivariate anomaly boundary: Method B flag)
  - $P_{99} = 4.830$ (High anomaly threshold)
  - $P_{99.5} = 6.162$
  - $P_{99.9} = 8.202$ (Ceiling distance for score normalization)

Multivariate Anomaly Score ($S_{\text{mv}} \in [0.0, 1.0]$):
$$S_{\text{mv}} = \min\left(1.0, \frac{d(x, c_k)}{P_{99.9}}\right)$$

---

## 6. Ensemble Scoring & Multi-Tier Severity Architecture

### 6.1 Composite Anomaly Score
$$S_{\text{composite}} = 0.50 \cdot S_{\text{stat}} + 0.50 \cdot S_{\text{mv}}$$
Ensemble flag: $\text{anomaly\_flag} = 1$ if Method A or Method B is triggered.

### 6.2 Rigorous Severity Grading Framework
Severity is assigned deterministically based on documented statistical risk criteria:

| Severity Level | Definition & Trigger Criteria | Count | % of Total | Operational Action |
| :--- | :--- | :---: | :---: | :--- |
| **CRITICAL** | $\text{profit} \le -\$500$ OR (Method A Flag AND $d \ge P_{99.5}$) | 1,251 | 0.69% | Immediate management hold; pricing & contract audit. |
| **HIGH** | $S_{\text{composite}} \ge 0.45$ OR $d \ge P_{99.0}$ ($d \ge 4.83$) | 1,726 | 0.96% | Priority review by commercial billing & logistics team. |
| **MEDIUM** | Standard anomaly flagged by Method A or Method B ($d \ge P_{98}$) | 6,331 | 3.51% | Flagged for automated margin reconciliation queue. |
| **LOW** | Marginal multivariate deviation ($P_{95} \le d < P_{98}$) | 2,870 | 1.59% | Logged for statistical trend monitoring. |
| **NORMAL** | Standard business transaction | 168,341 | 93.25% | Automated standard workflow pass-through. |

---

## 7. Actual Results & Anomaly Typology Breakdown

Extracted directly from [`step2_anomaly_category_summary.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_anomaly_category_summary.csv):

| Anomaly Category | Description & Characteristics | Flagged Count | % of Dataset |
| :--- | :--- | :---: | :---: |
| **Normal Transaction** | Within standard operational and economic parameters | 171,412 | 94.96% |
| **Operational Margin Loss** | Profit below IQR boundary ($-\$166.73$ to $-\$500.00$) | 4,748 | 2.63% |
| **Compound Multi-Vector Anomaly** | Joint failure across both statistical and multivariate distance models | 2,152 | 1.19% |
| **Severe Profit Bleed** | Catastrophic operational loss exceeding $-\$500.00$ (down to $-\$4,274.98$) | 1,160 | 0.64% |
| **Excessive Discount Inversion** | High discount paired with negative profit on high-value orders | 644 | 0.36% |
| **Multivariate Distribution Outlier** | Geometric distance anomaly ($d \ge 3.755$) without single-rule breaches | 251 | 0.14% |
| **High-Value Transaction Outlier** | Unusually high transaction cashflow ($> \$676.46$) | 152 | 0.08% |
| **Total Unique Anomalies** | **Union of all flagged irregular transactions** | **9,308** | **5.16%** |

---

## 8. Cross-Method Comparison & Temporal Stability

### 8.1 Method Overlap & Consensus
Extracted from [`step2_anomaly_method_comparison.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_anomaly_method_comparison.csv):
- **Method A Flags (Statistical):** 8,909 transactions (4.94%).
- **Method B Flags (Multivariate):** 3,711 transactions (2.06%).
- **Consensus Flags (Both Methods Agree):** **3,312 transactions (1.83%)**.
  - **89.25% of Method B flags are corroborated by Method A.**
  - **Jaccard Similarity Index:** **0.3558**.

### 8.2 Chronological Stability
Evaluated by grouping transactions by `order_year`:

| Year | Total Transactions | Flagged Anomalies | Anomaly Rate (%) | Mean Anomaly Score | Stability Assessment |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **2015** | 62,650 | 3,011 | **4.81%** | 0.1065 | **Stable Baseline** |
| **2016** | 62,550 | 2,984 | **4.77%** | 0.1065 | **Zero Temporal Drift** |
| **2017** | 53,196 | 3,220 | **6.05%** | 0.1140 | **Slight Upward Variance** |
| **2018 (Jan)**| 2,123 | 93 | **4.38%** | 0.1120 | **Consistent Rate** |

The anomaly rate fluctuates within a narrow band (4.38% to 6.05%), confirming that the unsupervised thresholding logic does not overfit to specific years and is robust against temporal drift.

---

## 9. Representative Anomaly Case Studies

Extracted from the top-ranked transactions in [`step2_anomaly_results.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_anomaly_results.csv):

### Case 1: Catastrophic Commercial Loss (Order Item #102604)
- **Product:** Soleus GPS Watch (Apparel)
- **Financials:** Sales = $1,999.99, Discount = $400.00 (20%), Net Total = $1,599.99
- **Profit:** **-$4,274.98** (Net Margin: -267%)
- **Model Diagnostics:** Centroid Distance = **11.48** ($> P_{99.9}$), Composite Score = **0.900**, Severity = **CRITICAL**
- **Root Cause:** Excessive promotional discounting on luxury high-cost goods combined with severe regional logistics overhead.

### Case 2: Maximum Discount Margin Inversion (Order Item #45129)
- **Product:** Field & Stream Sportsman 16 Gun Fire Safe (Fan Shop)
- **Financials:** Sales = $1,999.99, Discount = $500.00 (25% max rate), Net Total = $1,499.99
- **Profit:** **-$1,199.99**
- **Model Diagnostics:** Centroid Distance = **8.92** ($> P_{99.9}$), Composite Score = **0.850**, Severity = **CRITICAL**
- **Root Cause:** Bulk promotional campaign policy flaw allowing max discount on overweight items with massive freight expenses.

### Case 3: High-Value Multi-Item Outlier (Order Item #12108)
- **Product:** Perfect Fitness Rip Deck (Fitness)
- **Financials:** Quantity = 5, Sales = $299.95, Discount = $0.00, Net Total = $299.95
- **Profit:** +$143.98
- **Model Diagnostics:** Centroid Distance = **3.82** ($> P_{98}$), Severity = **MEDIUM**, Category = **Multivariate Distribution Outlier**
- **Root Cause:** Healthy non-anomalous profit, but geometric feature combination is isolated from standard cluster densities.

---

## 10. Visualizations & Analytical Artifacts

The following 7 charts were generated and saved to [`reports/phase5/`](file:///E:/BDA/ChainSentinel/reports/phase5/):

1. **Score Distribution:** [`reports/phase5/step2_score_distribution.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_score_distribution.png)  
   Histogram of composite anomaly scores demonstrating clean concentration among normal records and a distinct long-tail high-risk tier.
2. **Normal vs Flagged Distribution:** [`reports/phase5/step2_normal_vs_flagged.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_normal_vs_flagged.png)  
   Bar chart illustrating the 94.84% normal vs 5.16% anomaly operational split across 180,519 records.
3. **Anomaly Typology Breakdown:** [`reports/phase5/step2_anomaly_categories.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_anomaly_categories.png)  
   Horizontal bar chart ranking anomaly categories by volume (led by Operational Margin Loss and Compound Multi-Vector Anomalies).
4. **Severity Distribution:** [`reports/phase5/step2_severity_distribution.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_severity_distribution.png)  
   Multi-tier distribution showing 1,251 Critical and 1,726 High severity interventions.
5. **Discount vs Profit Anomaly Patterns:** [`reports/phase5/step2_discount_vs_profit.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_discount_vs_profit.png)  
   Scatter plot mapping transaction loss severity against dollar discount amounts.
6. **Quantity vs Sales Patterns:** [`reports/phase5/step2_quantity_vs_sales.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_quantity_vs_sales.png)  
   Scatter plot showing discrete quantity boundaries (1–5) and sales outliers.
7. **Method Comparison & Overlap:** [`reports/phase5/step2_method_comparison.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_method_comparison.png)  
   Consensus overlap diagram confirming that 89.25% of multivariate distance outliers are verified by statistical rules.

---

## 11. Reusable Inference Script (`predict_anomalies.py`)

A production-ready inference engine has been developed at [`docker/spark/batch/phase5/predict_anomalies.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase5/predict_anomalies.py).

### Verification:
Execution with `--sample` yielded:
```text
+-------------+----------------+----------------------+-----------------------+--------+-----------------------------+--------------------------------------------------------------------+
|order_item_id|order_item_total|order_profit_per_order|composite_anomaly_score|severity|anomaly_category             |anomaly_reason                                                      |
+-------------+----------------+----------------------+-----------------------+--------+-----------------------------+--------------------------------------------------------------------+
|ITEM-001     |749.96          |-650.0                |0.7235                 |CRITICAL|Severe Profit Bleed          |Extreme negative profit: $-650.0                                    |
|ITEM-002     |599.97          |-180.5                |0.9500                 |CRITICAL|Compound Multi-Vector Anomaly|Joint statistical & multivariate outlier (dist=8.41, profit=$-180.5)|
|ITEM-003     |54.99           |24.5                  |0.0575                 |NORMAL  |Normal Transaction           |Within standard operational parameters                              |
+-------------+----------------+----------------------+-----------------------+--------+-----------------------------+--------------------------------------------------------------------+
```
- Case 1 (Heavy loss -$650): Accurately flagged as **CRITICAL** (`Severe Profit Bleed`).
- Case 2 (25% discount + -$180.50 loss): Accurately flagged as **CRITICAL** (`Compound Multi-Vector Anomaly`).
- Case 3 (Standard $54.99 purchase + $24.50 profit): Evaluated as **NORMAL** (score = 0.0575).

---

## 12. Deliverables Summary

| Artifact | Type | Path | Status |
| :--- | :--- | :--- | :---: |
| **Model 2 Training Pipeline** | PySpark Batch | [`docker/spark/batch/phase5/step2_anomaly_detection.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase5/step2_anomaly_detection.py) | **Verified** |
| **Reusable Inference Engine** | PySpark Inference | [`docker/spark/batch/phase5/predict_anomalies.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase5/predict_anomalies.py) | **Verified** |
| **Readiness Audit Report** | Markdown | [`reports/phase5/step2_anomaly_readiness.md`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_anomaly_readiness.md) | **Verified** |
| **Formal Model 2 Report** | Markdown | [`reports/phase5/step2_anomaly_detection_report.md`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_anomaly_detection_report.md) | **Verified** |
| **Top Flagged Results (1,000 rows)**| CSV | [`reports/phase5/step2_anomaly_results.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_anomaly_results.csv) | **Verified** |
| **Category Summary** | CSV | [`reports/phase5/step2_anomaly_category_summary.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_anomaly_category_summary.csv) | **Verified** |
| **Method Comparison Table** | CSV | [`reports/phase5/step2_anomaly_method_comparison.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_anomaly_method_comparison.csv) | **Verified** |
| **Summary Metrics Payload** | JSON | [`reports/phase5/step2_anomaly_summary.json`](file:///E:/BDA/ChainSentinel/reports/phase5/step2_anomaly_summary.json) | **Verified** |
| **Trained KMeans Artifact (Local)** | Spark Model | [`models/phase5/anomaly_detection_v1`](file:///E:/BDA/ChainSentinel/models/phase5/anomaly_detection_v1) | **Verified** |
| **Trained KMeans Artifact (HDFS)** | HDFS Distributed Model | `/chainsentinel/models/phase5/anomaly_detection_v1` | **Verified** |
| **Thresholds & Metadata File** | JSON | [`models/phase5/anomaly_detection_v1/anomaly_thresholds.json`](file:///E:/BDA/ChainSentinel/models/phase5/anomaly_detection_v1/anomaly_thresholds.json) | **Verified** |
| **Analytical Visualizations (7)** | PNG Charts | [`reports/phase5/step2_*.png`](file:///E:/BDA/ChainSentinel/reports/phase5) | **Verified** |

---

## 13. Methodological Limitations & Unsupervised Reality

1. **Unsupervised Nature:** In the absence of audited ground-truth fraud or commercial crime labels, conventional supervised metrics (Precision, Recall, ROC-AUC) cannot be computed. Detected records represent **statistical and operational anomalies**, not confirmed fraud.
2. **Accounting Conventions:** The dataset records negative profit on certain product lines that may represent legitimate commercial "loss-leader" marketing strategies rather than supply-chain sabotage or rogue pricing.
3. **Threshold Sensitivity:** The multivariate $P_{98}$ cutoff represents a business tuning parameter. Lowering to $P_{95}$ increases flagged volume to ~7%, whereas raising to $P_{99}$ isolates only the top 1% extreme deviations.

---

## 14. Infrastructure & Model 1 Integrity Sign-Off
- **Zero Disruptions:** All 5 Docker containers (`chainsentinel-kafka`, `chainsentinel-namenode`, `chainsentinel-datanode`, `chainsentinel-spark-master`, `chainsentinel-spark-worker`) remain actively `RUNNING`.
- **Spark Streaming Intact:** `ChainSentinel-Kafka-Streaming` (`app-20261103190004-0001`) actively processing streaming events.
- **Model 1 Untouched:** [`models/phase5/delay_model_v1`](file:///E:/BDA/ChainSentinel/models/phase5/delay_model_v1) and all Model 1 reports and scripts remain 100% unaltered.


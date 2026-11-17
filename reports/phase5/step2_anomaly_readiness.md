# ChainSentinel — Phase 5, Model 2: Supply-Chain Anomaly Detection Readiness Audit

**Project:** ChainSentinel — Autonomous Supply Chain Risk & Predictive Analytics  
**Phase:** Phase 5 — Machine Learning and Predictive Analytics  
**Component:** Model 2 — Supply-Chain Anomaly Detection Readiness & Variable Audit  
**Date:** 2026-11-04  
**Engine:** Apache Spark 4.0.1 / PySpark MLlib & Host Python 3.10  
**Dataset:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1` (180,519 records × 52 columns)

---

## 1. Executive Summary

This readiness audit establishes the empirical and mathematical foundation for **Model 2: Supply-Chain Anomaly Detection**. The objective is to design and benchmark unsupervised statistical and multivariate anomaly detection pipelines capable of identifying operational irregularities, excessive discounts, severe transaction losses, and unusual purchasing behavior without relying on artificial ground-truth labels.

### Key Readiness Findings:
1. **Dataset Volume & Completeness:** Exactly **180,519 records** and 52 columns. Null and NaN counts across all candidate numerical and categorical features are **precisely 0** (100% clean).
2. **Extreme Profit Losses:** 33,784 transactions (**18.71%**) exhibit negative profit, extending down to a catastrophic minimum of **-$4,274.98**. Exactly 131 transactions have sales > $500 combined with operational losses exceeding -$100.
3. **Severe Multicollinearity:** `sales` and `order_item_total` exhibit a Pearson correlation of **0.9897** ($\approx 0.99$). Retaining both in distance-based multivariate models would create redundant dimensional distortion.
4. **Bounded Variables:** `order_item_quantity` is strictly discrete in $[1, 5]$ (zero records exceed 5). `order_item_discount_rate` is strictly capped at $0.25$ ($25\%$).
5. **Environment Capabilities:** PySpark MLlib natively provides `pyspark.ml.clustering.KMeans` (distance-to-centroid anomaly detection), `pyspark.ml.feature.PCA` (reconstruction error anomaly detection), `StandardScaler`, and `RobustScaler`. Host Python has `matplotlib` and `pandas` for publication-quality visual artifacts.

---

## 2. Environment & Dependency Audit

- **Cluster Infrastructure:**
  - `chainsentinel-spark-master`: Apache Spark 4.0.1, Python 3.10.12, NumPy 2.2.6 (verified).
  - `chainsentinel-namenode` & `chainsentinel-datanode`: Hadoop 3.3.6 HDFS (verified).
  - `chainsentinel-kafka`: Kafka 3.7.0 (verified).
  - Background Streaming Job: `ChainSentinel-Kafka-Streaming` (`RUNNING` on 8 worker cores).
- **Available Machine Learning Modules:**
  - `pyspark.ml.clustering`: `KMeans`, `BisectingKMeans`, `GaussianMixture` (verified).
  - `pyspark.ml.feature`: `PCA`, `StandardScaler`, `RobustScaler`, `VectorAssembler`, `OneHotEncoder`, `StringIndexer` (verified).
  - `pyspark.ml.stat`: `Correlation` (verified).
- **Host Analytics Modules:**
  - `pandas` (v2.2.3), `matplotlib` (v3.10.0), `numpy` (v2.0.2).
- **Dependency Policy Compliance:** No new packages or Docker infrastructure modifications are required.

---

## 3. Dataset Integrity & Candidate Feature Profiles

### 3.1 Null Count Verification
Executed across all 180,519 records in `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1`:

| Candidate Column | Data Type | Null Count | NaN Count | Missing % |
| :--- | :--- | :---: | :---: | :---: |
| `order_item_quantity` | DoubleType | 0 | 0 | 0.00% |
| `product_price` | DoubleType | 0 | 0 | 0.00% |
| `sales` | DoubleType | 0 | 0 | 0.00% |
| `order_item_discount` | DoubleType | 0 | 0 | 0.00% |
| `order_item_discount_rate` | DoubleType | 0 | 0 | 0.00% |
| `order_item_total` | DoubleType | 0 | 0 | 0.00% |
| `order_profit_per_order` | DoubleType | 0 | 0 | 0.00% |
| `days_for_shipment_scheduled` | IntegerType | 0 | 0 | 0.00% |
| `shipping_mode` | StringType | 0 | — | 0.00% |
| `market` | StringType | 0 | — | 0.00% |
| `order_region` | StringType | 0 | — | 0.00% |
| `department_name` | StringType | 0 | — | 0.00% |

---

### 3.2 Candidate Numerical Distributions & Extreme Values

| Feature | Min | Median ($P_{50}$) | Mean | Max | StdDev | Skewness | Kurtosis | $IQR$ Outlier Count (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `product_price` | $9.99 | $59.99 | $141.23 | $1,999.99 | $139.73 | +3.19 | +23.31 | 2,048 (1.13%) |
| `sales` | $9.99 | $199.92 | $203.77 | $1,999.99 | $132.27 | +2.88 | +23.94 | 488 (0.27%) |
| `order_item_discount` | $0.00 | $14.00 | $20.66 | $500.00 | $21.80 | +3.04 | +25.23 | 7,537 (4.18%) |
| `order_item_discount_rate` | 0.00 | 0.09 | 0.10 | 0.25 | 0.07 | +0.34 | -0.90 | 0 (0.00%) |
| `order_item_total` | $7.49 | $163.99 | $183.11 | $1,939.99 | $120.04 | +2.89 | +23.92 | 1,943 (1.08%) |
| `order_profit_per_order` | **-$4,274.98** | $31.50 | $21.98 | $911.80 | $104.43 | **-4.74** | **+71.38** | **18,916 (10.48%)** |
| `order_item_quantity` | 1.0 | 1.0 | 2.13 | 5.0 | 1.45 | +0.88 | -0.75 | 0 (0.00%) |
| `days_for_shipment_scheduled` | 0.0 | 4.0 | 2.93 | 4.0 | 1.37 | -0.73 | -1.02 | 0 (0.00%) |

#### Distribution Takeaways:
1. **Profit Anomaly Severity:** `order_profit_per_order` exhibits extreme negative skewness (-4.74) and massive kurtosis (71.38), driven by massive losses reaching -$4,274.98. The 1st percentile ($P_{01}$) is -$430.46, indicating a persistent tail of toxic transactions.
2. **Right-Skewed Economic Variables:** `product_price`, `sales`, and `order_item_discount` exhibit high positive skewness (~3.0). Standard Gaussian Z-scores would misclassify normal high-value catalog items as anomalies; robust IQR or log1p transformations are mathematically required.
3. **Strict Parameter Bounds:** `order_item_quantity` is discrete $\{1, 2, 3, 4, 5\}$, and `order_item_discount_rate` is discrete-bounded $[0.00, 0.25]$. Neither can produce classical univariate outliers on its own, but their **combinations** (e.g. max quantity + max discount + severe loss) represent potent multivariate anomaly signals.

---

### 3.3 Pearson Correlation & Redundancy Analysis

Computed via PySpark `Correlation.corr` over the 180,519 records:

```text
Correlation Matrix:
                       quantity   price   sales   discount  disc_rate   total   profit   sched_days
order_item_quantity      1.0000 -0.4762  0.1064    0.0654    -0.0000   0.1054   0.0157    -0.0029
product_price           -0.4762  1.0000  0.7899    0.4881     0.0003   0.7818   0.1035     0.0069
sales                    0.1064  0.7899  1.0000    0.6174     0.0003   0.9897   0.1318     0.0063
order_item_discount      0.0654  0.4881  0.6174    1.0000     0.6600   0.4987   0.0648     0.0029
order_item_discount_rate-0.0000  0.0003  0.0003    0.6600     1.0000  -0.1195  -0.0186     0.0001
order_item_total         0.1054  0.7818  0.9897    0.4987    -0.1195   1.0000   0.1335     0.0064
order_profit_per_order   0.0157  0.1035  0.1318    0.0648    -0.0186   0.1335   1.0000    -0.0002
days_for_shipment_sched -0.0029  0.0069  0.0063    0.0029     0.0001   0.0064  -0.0002     1.0000
```

#### Multicollinearity Resolution:
- **`sales` vs `order_item_total` ($r = 0.9897$):** Because $\text{order\_item\_total} = \text{sales} - \text{order\_item\_discount}$, including all three creates direct linear dependence. In the multivariate feature matrix, we retain **`order_item_total`** (net received cashflow), **`order_item_discount`** (absolute margin loss), and **`order_item_discount_rate`**, dropping gross `sales` from distance-based models to eliminate redundant variance inflation.
- **`product_price` vs `order_item_total` ($r = 0.7818$):** Retaining both is justified because product price measures luxury catalog tier, whereas total reflects final transaction volume.

---

## 4. Exclusion & Data Governance Safeguards

In strict compliance with Phase 5 Model 2 instructions:

1. **Model 1 Target & Post-Shipment Actuals Excluded:**
   - Prohibited fields: `is_delayed`, `late_delivery_risk`, `delivery_status`, `days_for_shipping_real`, `transit_delay_days`, `order_to_shipping_hours`, `shipping_date`.
   - Reason: These describe delivery logistics latency and would conflate shipment delays with operational business anomalies.
2. **Customer PII & High-Cardinality Identifiers Excluded:**
   - Excluded from modeling: `customer_fname`, `customer_lname`, `customer_email`, `customer_password`, `customer_street`, `customer_zipcode`, `customer_city`, `customer_state`, `customer_country`, `order_city`, `order_state`, `order_country`.
   - Record identifiers (`order_id`, `order_item_id`, `order_date`) are preserved strictly for traceability in the final output table, not as model inputs.
3. **No Ground-Truth Fraud Assumptions:**
   - Findings will be classified as operational and commercial anomalies, **never labeled as fraud**.

---

## 5. Dual Anomaly Detection Architecture Selection

To satisfy the multi-method comparative requirement:

### Method A: Robust Statistical Anomaly Detection (Rule-Based & IQR Composite)
- Computes distribution-free, quantile-based anomaly flags across 4 key operational risk vectors:
  1. **Extreme Loss Anomaly:** Profit $< Q_{25} - 3 \times IQR$ (severe financial bleed).
  2. **Margin Erosion Anomaly:** Maximum discount ($25\%$) paired with negative profit on high-value orders ($> \$200$).
  3. **High-Value Outlier Anomaly:** Net total $> Q_{75} + 3 \times IQR$ ($> \$676.60$).
  4. **Volume & Discount Anomaly:** Bulk purchase (`quantity == 5`) with top-tier discount ($> \$66.73$).
- Yields deterministic, easily interpretable anomaly categories and a composite statistical score.

### Method B: Multivariate Distance-to-Centroid Anomaly Detection (K-Means Clustering)
- Encapsulates scaled numerical features (`product_price`, `order_item_total`, `order_item_discount`, `order_item_discount_rate`, `order_profit_per_order`, `days_for_shipment_scheduled`) using `RobustScaler` / `StandardScaler`.
- Fits an optimal unsupervised $K$-Means clustering model ($K=6$).
- Computes Euclidean distance $d(x, c_k)$ from each transaction to its assigned cluster centroid $c_k$.
- Derives a continuous, normalized multivariate anomaly score $[0.0, 1.0]$ based on empirical distance percentiles ($P_{95}$, $P_{99}$, $P_{99.9}$).

---

## 6. Readiness Verification Checklist

- [x] Schema & column semantics audited.
- [x] All 180,519 rows verified; zero missing numerical values.
- [x] Skewness, ranges, and kurtosis computed.
- [x] Collinearity evaluated; redundant `sales` eliminated from distance matrix.
- [x] Target and leakage fields permanently quarantined.
- [x] Host and container analytics packages verified.
- [x] Dual-methodology framework established.

**Status:** **READY FOR MODEL 2 IMPLEMENTATION**


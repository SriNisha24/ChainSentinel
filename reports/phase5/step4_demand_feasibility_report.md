# ChainSentinel — Phase 5, Model 4: Demand Data Feasibility Audit

**Component:** Model 4 — Demand Forecasting and Capacity Planning Analytics  
**Date:** November 2026  
**Audited Dataset:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1`  
**Execution Environment:** Apache Spark 4.0.1 on Docker cluster (`chainsentinel-spark-master`)  
**Status:** **FEASIBILITY APPROVED WITH METHODOLOGICAL CONSTRAINTS**

---

## 1. Executive Summary

Prior to developing predictive forecasting models and capacity estimation logic for **Model 4 (Demand Forecasting and Capacity Planning Analytics)**, a data feasibility audit was conducted across the cleaned historical DataCo dataset in HDFS.

The purpose of this audit is to rigorously determine:
1. Whether the historical temporal depth, resolution, and continuity support defensible time-series forecasting.
2. The exact mathematical distinction between **distinct orders** and **line items** to prevent order double-counting.
3. The viability of forecasting across multiple organizational hierarchies: network-wide, market-level, region-level, and shipping-mode level.
4. The presence of seasonality, drift, or synthetic regime shifts that dictate model selection and evaluation splits.

### Key Feasibility Findings
* **Temporal Continuity:** 1,127 consecutive calendar days spanning **January 1, 2015 to January 31, 2018** (36 complete months + 1 month). **Zero missing calendar days** were detected.
* **Order vs. Line-Item Distinction:** The dataset comprises **65,752 distinct orders** totaling **180,519 order items** (averaging **2.745 items per order**). Order demand forecasting must strictly aggregate by `order_id` to avoid a 2.75× demand inflation.
* **Network-Wide Demand Stability:** Daily network demand exhibits an average of **58.34 orders/day** with a very tight variance (minimum 47, maximum 69 orders/day).
* **Weekly Seasonality Absence:** Daily order volume is completely uniformly distributed across all seven days of the week (~14.25% to 14.34% per day), indicating synthetic generation that lacks standard retail weekday/weekend cycles.
* **Late-2017 Structural Regime Shift:** Between October 2017 and January 2018, the data exhibits a structural disruption: daily orders rise to ~68–69 orders/day while the line-item ratio collapses from ~3.0 items/order to strictly 1.0 item/order.
* **Granularity Recommendation:**
  - **Network-wide daily and weekly demand:** Defensible and robust.
  - **Market-level demand (5 markets):** Defensible; all 5 markets have continuous order flow.
  - **Shipping-mode demand (4 modes):** Defensible; all 4 modes have continuous daily observations.
  - **Regional demand (23 regions):** **Sparse tails.** Top regions (Western Europe, Central America) have continuous daily activity, while peripheral regions (e.g., Central Asia: 184 orders across 3 years; Canada: 309 orders) are highly intermittent. Full-scale regression across all 23 regions is methodologically invalid; regional forecasting must focus exclusively on high-volume hubs.

---

## 2. Dataset Dimensions & Temporal Coverage

| Dimension | Count / Range | Feasibility Assessment |
|---|---|---|
| **Total Processed Records** | 180,519 rows | Matches baseline across all Phase 4 & 5 models |
| **Distinct Order IDs** | 65,752 orders | Authoritative demand metric |
| **Distinct Customers** | 20,652 customers | Customer base volume |
| **Items per Order Ratio** | 2.745 items / order | Confirms mandatory `countDistinct("order_id")` |
| **Minimum Order Date** | `2015-01-01` | Start of temporal sequence |
| **Maximum Order Date** | `2018-01-31` | End of temporal sequence |
| **Total Calendar Span** | 1,127 days (163 weeks, 37 months) | Sufficient sample size for chronological splits |
| **Active Days with Orders** | 1,127 days (100.0%) | Complete temporal continuity |
| **Missing Calendar Days** | **0 days** | No zero-demand interpolation required at network level |

---

## 3. Order Volume Distributions & Demand Patterns

### 3.1 Daily Demand Characteristics
Across the 1,127 active days:
* **Mean Daily Orders:** 58.34 orders / day
* **Standard Deviation:** $\sim 3.82$ orders / day
* **Minimum Daily Orders:** 47 orders / day
* **Maximum Daily Orders:** 69 orders / day

### 3.2 Day-of-Week Distribution (Day Seasonality Audit)

| Day of Week | Day Index | Distinct Orders | % Share | Total Items | Avg Item Value |
|---|:---:|:---:|:---:|:---:|:---:|
| **Sunday** | 1 | 9,367 | 14.25% | 25,946 | $183.48 |
| **Monday** | 2 | 9,368 | 14.25% | 25,786 | $183.87 |
| **Tuesday** | 3 | 9,395 | 14.29% | 25,622 | $182.33 |
| **Wednesday** | 4 | 9,397 | 14.29% | 25,587 | $178.58 |
| **Thursday** | 5 | 9,395 | 14.29% | 25,752 | $182.79 |
| **Friday** | 6 | 9,400 | 14.30% | 25,925 | $183.98 |
| **Saturday** | 7 | 9,430 | 14.34% | 25,901 | $186.67 |

**Observation:** There is no traditional commercial weekend dip or Monday surge. Daily volume varies by less than 1% across all seven days. Models relying heavily on day-of-week cyclicality will find virtually zero seasonal variance.

---

## 4. Monthly Timeline & Structural Shift Audit

The monthly order timeline reveals two distinct phases in the DataCo dataset:

```
[Phase A: Stable Multi-Item Operations]            [Phase B: Single-Item Regime Shift]
 2015-01 to 2017-09 (33 months)                      2017-10 to 2018-01 (4 months)
 ~1,700 - 1,800 orders/month                        ~2,050 - 2,125 orders/month
 ~5,100 - 5,400 items/month (~3.0 items/order)      ~2,050 - 2,255 items/month (1.0 item/order)
 Revenue: ~$900K - $1.0M/month                      Revenue: drops to ~$300K - $560K/month
```

| Year-Month | Days | Distinct Orders | Total Items | Ratio (Items/Order) | Monthly Revenue |
|---|:---:|:---:|:---:|:---:|:---:|
| **2015-01** | 31 | 1,787 | 5,322 | 2.98 | $945,382.16 |
| **2015-06** | 30 | 1,725 | 5,134 | 2.98 | $920,242.06 |
| **2015-12** | 31 | 1,805 | 5,371 | 2.98 | $950,526.92 |
| **2016-06** | 30 | 1,690 | 5,054 | 2.99 | $901,448.01 |
| **2016-12** | 31 | 1,763 | 5,269 | 2.99 | $932,112.89 |
| **2017-01** | 31 | 1,745 | 5,217 | 2.99 | $925,472.62 |
| **2017-08** | 31 | 1,768 | 5,305 | 3.00 | $996,507.88 |
| **2017-09** | 30 | 1,723 | 5,189 | 3.01 | $1,027,111.73 |
| **2017-10** | 31 | **2,101** | 2,255 | **1.07** | $966,081.41 |
| **2017-11** | 30 | **2,055** | 2,055 | **1.00** | $563,393.47 |
| **2017-12** | 31 | **2,124** | 2,124 | **1.00** | $452,741.53 |
| **2018-01** | 31 | **2,123** | 2,123 | **1.00** | $297,952.05 |

### Audit Implication
* In October 2017, distinct order demand increased by approximately **19.5%** (from ~57 orders/day to ~68.5 orders/day), while item-level basket size collapsed.
* Because Model 1 and Model 2 used **September 1, 2017** as the chronological test set boundary, the Model 4 test set will naturally evaluate how well forecasting algorithms adapt to this structural shift.

---

## 5. Granularity & Hierarchy Feasibility

### 5.1 Market-Level Demand (5 Markets)
All 5 global commercial markets possess sufficient historical density for independent time-series aggregation:

| Market | Distinct Orders | % Share | Total Items | Total Revenue | Daily Order Rate |
|---|:---:|:---:|:---:|:---:|:---:|
| **Europe** | 18,561 | 28.23% | 50,252 | $9,769,198.32 | 16.47 / day |
| **Pacific Asia** | 17,577 | 26.73% | 41,260 | $7,434,262.65 | 15.60 / day |
| **LATAM** | 17,181 | 26.13% | 51,594 | $9,235,762.09 | 15.24 / day |
| **USCA** | 8,579 | 13.05% | 25,799 | $4,553,499.92 | 7.61 / day |
| **Africa** | 3,854 | 5.86% | 11,614 | $2,061,679.39 | 3.42 / day |
| **Total** | **65,752** | **100.00%** | **180,519** | **$31,054,402.37** | **58.34 / day** |

*Status: **FEASIBLE** for multi-market forecasting.*

---

### 5.2 Shipping-Mode Demand (4 Modes)
All 4 fulfillment modes have consistent continuous operations:

| Shipping Mode | Distinct Orders | % Share | Total Items | Total Revenue | Daily Order Rate |
|---|:---:|:---:|:---:|:---:|:---:|
| **Standard Class** | 39,324 | 59.81% | 107,752 | $19,792,221.24 | 34.89 / day |
| **Second Class** | 12,778 | 19.43% | 35,216 | $6,416,528.54 | 11.34 / day |
| **First Class** | 10,079 | 15.33% | 27,814 | $5,100,451.07 | 8.94 / day |
| **Same Day** | 3,571 | 5.43% | 9,737 | $1,745,201.53 | 3.17 / day |
| **Total** | **65,752** | **100.00%** | **180,519** | **$31,054,402.37** | **58.34 / day** |

*Status: **FEASIBLE** for fulfillment capacity mode forecasting.*

---

### 5.3 Regional Demand Sparsity (23 Regions)
Analysis of the 23 regions reveals severe distributional skew:
* **High-Density Core:** Western Europe (10,010 orders; ~8.88/day), Central America (9,396 orders; ~8.34/day), South America (4,979 orders), Oceania (4,362 orders), Southeast Asia (4,356 orders).
* **Sparse Peripheral Tails:** Central Asia (184 orders across 1,127 days = **0.16 orders/day**, or 1 order every 6 days), Canada (309 orders = **0.27 orders/day**), Southern Africa (398 orders = **0.35 orders/day**).

**Feasibility Decision on Regional Granularity:**
Fitting continuous daily regression models across all 23 individual regions would violate time-series statistical validity due to zero-inflated, intermittent demand on 12 of the 23 regions. Therefore, regional forecasting will be restricted to **the top operational hubs** (Western Europe, Central America, South America, Oceania, Southeast Asia) where continuous daily demand exists.

---

## 6. Recommended Forecasting Methodology & Pipeline Architecture

### 6.1 Chronological Splits
To maintain strict methodological alignment with Phase 5 Model 1 and Model 2:
* **Training Set:** `2015-01-01` to `2016-12-31` (731 days, ~64.9% of data).
* **Validation Set:** `2017-01-01` to `2017-08-31` (243 days, ~21.5% of data).
* **Test Set:** `2017-09-01` to `2018-01-31` (153 days, ~13.6% of data).

*Strict Rule:* Zero data shuffling. Observations are strictly ordered in time.

### 6.2 Feature Engineering (Zero Leakage)
* **Lag Features:** Strictly past observations: $y_{t-1}, y_{t-2}, y_{t-3}, y_{t-7}, y_{t-14}$.
* **Rolling Statistics:** Backward rolling 7-day and 14-day means excluding $y_t$:
  $$\mu_{7, t} = \frac{1}{7}\sum_{k=1}^7 y_{t-k}$$
* **Calendar Signals:** Day of week, day of month, month of year.

### 6.3 Baseline & Candidate Models
1. **Historical Naive Baseline (Lag 1):** $\hat{y}_t = y_{t-1}$
2. **Seasonal Naive Baseline (Lag 7):** $\hat{y}_t = y_{t-7}$
3. **Rolling Moving Average Baseline (MA-7):** $\hat{y}_t = \frac{1}{7}\sum_{k=1}^7 y_{t-k}$
4. **PySpark ML GBTRegressor / LinearRegression:** Machine learning regression with engineered autoregressive lag and rolling features.

### 6.4 Evaluation Metrics
* **MAE** (Mean Absolute Error): Average magnitude of errors in orders.
* **RMSE** (Root Mean Squared Error): Penalizes larger forecasting errors.
* **WAPE** (Weighted Absolute Percentage Error): Scale-independent error:
  $$\text{WAPE} = \frac{\sum |y_t - \hat{y}_t|}{\sum y_t} \times 100\%$$
* **MAPE** (Mean Absolute Percentage Error): Included for percentage comparison, with documented zero-risk checks.

---

## 7. Capacity Planning Formulation (Hypothetical Architecture)

Because actual warehouse, carrier, and production capacity records do not exist in DataCo, capacity planning will be implemented as an **independent, transparent scenario estimator**:

1. **Required Processing Capacity ($C_{\text{req}}$):**
   $$C_{\text{req}}(t) = \frac{\hat{y}_t}{\text{Target Utilization}}$$
2. **Capacity Utilization ($U(t)$):**
   $$U(t) = \frac{\hat{y}_t}{C_{\text{avail}}}$$
3. **Capacity Shortfall ($S(t)$):**
   $$S(t) = \max\left(0, \hat{y}_t - C_{\text{avail}}\right)$$
4. **Safety Buffer ($B(t)$):**
   $$B(t) = C_{\text{avail}} \times \text{Buffer Factor}$$

Scenarios to evaluate:
* **Scenario A (Normal Baseline Operations):** Available Capacity = 65 orders/day, Target Utilization = 85%.
* **Scenario B (Demand Surge / Promotion):** +20% demand shock against normal capacity.
* **Scenario C (Seasonal Peak):** +35% demand shock.
* **Scenario D (Carrier / Facility Constraint):** -25% available capacity reduction (e.g., labor shortage or maintenance).

---

## 8. Feasibility Verdict & Sign-Off

* [x] **Temporal Depth:** 1,127 continuous days — **EXCELLENT**
* [x] **Continuity:** Zero missing calendar days — **EXCELLENT**
* [x] **Granularity Feasibility:** Network, 5 Markets, 4 Shipping Modes, Top Regional Hubs — **APPROVED**
* [x] **Avoid Sparse Tails:** Peripheral regional series excluded from continuous regression — **APPROVED**
* [x] **Order vs Item Distinction:** Strictly using `countDistinct("order_id")` — **MANDATORY**
* [x] **Methodological Separation:** Demand forecasting strictly separated from hypothetical capacity planning — **VERIFIED**

**Conclusion:** Data feasibility audit is complete. Proceeding to **Steps 2 through 7 (Aggregation, Modeling, Forecasting, Capacity Planning, and Reporting)**.


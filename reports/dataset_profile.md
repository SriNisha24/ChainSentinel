# ChainSentinel — Phase 1: Dataset Inspection and Profiling Report

**Project:** ChainSentinel (AI-Powered, Resilience-Aware Supply-Chain Disruption Management System)  
**Task:** Phase 1: Dataset Inspection, Profiling, and Data-Quality Audit  
**Dataset Directory:** `E:\BDA\ChainSentinel\data\raw\`  
**Generated On:** 2026-11-03 22:34 IST  
**Profiling Tool:** Reusable chunked profiling script `E:\BDA\ChainSentinel\docker\spark\batch\profile_dataco_raw.py`  

---

## 1. Executive Summary & Raw Directory Inventory

A complete, read-only inspection and chunked profiling analysis was conducted across all raw data assets in `E:\BDA\ChainSentinel\data\raw\`. No files were altered, moved, deleted, or transformed.

### Raw Files Inventory
| Filename | Extension | Size (Bytes) | Size (MB) | Format | Last Modified | Role / Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DataCoSupplyChainDataset.csv` | `.csv` | 95,910,149 | 91.47 MB | Delimited text (CSV, Latin-1) | 2026-11-03 19:35:39 | **Main Core Dataset** (Supply chain transactions) |
| `DescriptionDataCoSupplyChain.csv` | `.csv` | 3,444 | 0.003 MB | Delimited text (CSV, Latin-1) | 2026-11-03 19:35:39 | **Data Dictionary** (Metadata definitions) |
| `tokenized_access_logs.csv` | `.csv` | 95,446,364 | 91.02 MB | Delimited text (CSV, UTF-8) | 2026-11-03 19:35:41 | **Supporting Clickstream Dataset** (E-commerce web access logs) |
| `hdfs_test.txt` | `.txt` | 44 | < 0.001 MB | Plain text (ASCII) | 2026-11-03 17:51:33 | **System Verification Artifact** (HDFS connectivity probe) |

---

## 2. Main Dataset Architecture (`DataCoSupplyChainDataset.csv`)

### 2.1 Volume, Encoding & Dimensions
* **Total Rows:** `180,519` records `[VERIFIED]`
* **Total Columns:** `53` fields `[VERIFIED]`
* **Character Encoding:** **`ISO-8859-1` / `Latin-1` (or `cp1252`)** `[VERIFIED]`  
  *Critical Finding:* Loading this file with default `UTF-8` raises a fatal `UnicodeDecodeError` at position 1709 (`byte 0xe1` representing `á` in Puerto Rican city/street addresses). Ingestion pipelines in PySpark and Pandas must explicitly specify `encoding='ISO-8859-1'` or `latin1`.
* **Primary Key / Uniqueness:**  
  * `Order Item Id`: `180,519` unique values out of `180,519` rows (`0` duplicate records). Each row represents a single line-item within an order.
* **Higher-Level Entity Cardinalities:**  
  * `Order Id`: `65,752` unique orders (average of `2.75` line-items per order).
  * `Customer Id`: `20,652` unique customers.
  * `Product Name`: `118` distinct products.
  * `Category Name`: `50` product categories (spanning `51` Category IDs).

### 2.2 Temporal Coverage
* **Order Date Range (`order date (DateOrders)`):**  
  * Minimum: `2015-01-01 00:00:00`
  * Maximum: `2018-01-31 23:38:00` (Span: 37 months / ~3.1 years) `[VERIFIED]`
* **Shipping Date Range (`shipping date (DateOrders)`):**  
  * Minimum: `2015-01-03 00:00:00`
  * Maximum: `2018-02-06 22:14:00` `[VERIFIED]`
* **Chronological Validity:** Zero records possess a shipping timestamp preceding the order timestamp (`Negative shipping diff count: 0`) `[VERIFIED]`.

---

## 3. Comprehensive Column Inventory & Data Quality Profiling

The table below catalogs all 53 columns, their verified data types, null counts, unique cardinality, and data-quality findings:

| # | Column Name | Inferred Type | Null Count | Null % | Unique Values | Data Quality & Architectural Notes |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | `Type` | Object (String) | 0 | 0.0% | 4 | Payment methods: `DEBIT`, `TRANSFER`, `PAYMENT`, `CASH`. |
| 2 | `Days for shipping (real)` | Int64 | 0 | 0.0% | 7 | Actual elapsed shipping days (Range: 0 to 6 days). |
| 3 | `Days for shipment (scheduled)` | Int64 | 0 | 0.0% | 4 | SLA target shipping days (Strictly 0, 1, 2, or 4 days). |
| 4 | `Benefit per order` | Float64 | 0 | 0.0% | 21,998 | Profit/loss. **100% duplicate of `Order Profit Per Order`**. |
| 5 | `Sales per customer` | Float64 | 0 | 0.0% | 2,927 | Net order item total. **100% duplicate of `Order Item Total`**. |
| 6 | `Delivery Status` | Object (String) | 0 | 0.0% | 4 | `Advance shipping`, `Late delivery`, `Shipping canceled`, `Shipping on time`. |
| 7 | `Late_delivery_risk` | Int64 (Binary) | 0 | 0.0% | 2 | Primary classification target (1 = Late, 0 = Not Late). |
| 8 | `Category Id` | Int64 | 0 | 0.0% | 51 | **100% duplicate of `Product Category Id`**. |
| 9 | `Category Name` | Object (String) | 0 | 0.0% | 50 | Category name. Note: `Electronics` maps to 2 Category IDs (13 & 37). |
| 10 | `Customer City` | Object (String) | 0 | 0.0% | 563 | Store/customer origin city. 37.0% (`66,770`) originate from `Caguas`. |
| 11 | `Customer Country` | Object (String) | 0 | 0.0% | 2 | Customer countries: `EE. UU.` (USA) and `Puerto Rico`. |
| 12 | `Customer Email` | Object (String) | 0 | 0.0% | 1 | **100% Masked / Zero Variance**: All values are `'XXXXXXXXX'`. |
| 13 | `Customer Fname` | Object (String) | 0 | 0.0% | 782 | Customer first name. |
| 14 | `Customer Id` | Int64 | 0 | 0.0% | 20,652 | **100% duplicate of `Order Customer Id`**. |
| 15 | `Customer Lname` | Object (String) | **8** | < 0.01% | 1,109 | Customer last name (8 missing values). |
| 16 | `Customer Password` | Object (String) | 0 | 0.0% | 1 | **100% Masked / Zero Variance**: All values are `'XXXXXXXXX'`. |
| 17 | `Customer Segment` | Object (String) | 0 | 0.0% | 3 | Segments: `Consumer` (51.8%), `Corporate` (30.4%), `Home Office` (17.9%). |
| 18 | `Customer State` | Object (String) | 0 | 0.0% | 46 | State/territory of store origin (Puerto Rico, California, etc.). |
| 19 | `Customer Street` | Object (String) | 0 | 0.0% | 7,458 | Customer street address. |
| 20 | `Customer Zipcode` | Float64 | **3** | < 0.01% | 995 | Customer postal code (3 missing values; parsed as float). |
| 21 | `Department Id` | Int64 | 0 | 0.0% | 11 | Department identifier. |
| 22 | `Department Name` | Object (String) | 0 | 0.0% | 11 | Department label (e.g., Apparel, Fan Shop, Fitness, Golf). |
| 23 | `Latitude` | Float64 | 0 | 0.0% | 11,250 | Store origin latitude. |
| 24 | `Longitude` | Float64 | 0 | 0.0% | 4,487 | Store origin longitude. |
| 25 | `Market` | Object (String) | 0 | 0.0% | 5 | Destination markets: `LATAM`, `Europe`, `Pacific Asia`, `USCA`, `Africa`. |
| 26 | `Order City` | Object (String) | 0 | 0.0% | 3,597 | Destination city. |
| 27 | `Order Country` | Object (String) | 0 | 0.0% | 164 | Destination country (Written in Spanish, e.g., `Estados Unidos`, `Francia`). |
| 28 | `Order Customer Id` | Int64 | 0 | 0.0% | 20,652 | **100% duplicate of `Customer Id`**. |
| 29 | `order date (DateOrders)` | Object (DateTime) | 0 | 0.0% | 65,752 | Timestamp of order placement (`M/D/YYYY H:MM`). |
| 30 | `Order Id` | Int64 | 0 | 0.0% | 65,752 | Unique order code (parent entity). |
| 31 | `Order Item Cardprod Id` | Int64 | 0 | 0.0% | 118 | **100% duplicate of `Product Card Id`**. |
| 32 | `Order Item Discount` | Float64 | 0 | 0.0% | 1,017 | Monetary discount applied to order line. |
| 33 | `Order Item Discount Rate` | Float64 | 0 | 0.0% | 18 | Discount rate (0.00 to 0.25 in stepped intervals). |
| 34 | `Order Item Id` | Int64 | 0 | 0.0% | 180,519 | **Dataset Primary Key** (Unique line item ID). |
| 35 | `Order Item Product Price` | Float64 | 0 | 0.0% | 75 | **100% duplicate of `Product Price`**. |
| 36 | `Order Item Profit Ratio` | Float64 | 0 | 0.0% | 162 | Profit margin ratio (Range: -2.75 to 0.50). |
| 37 | `Order Item Quantity` | Int64 | 0 | 0.0% | 5 | Items purchased per line item (Integer: 1 to 5). |
| 38 | `Sales` | Float64 | 0 | 0.0% | 193 | Gross sales (`Order Item Quantity * Product Price`). |
| 39 | `Order Item Total` | Float64 | 0 | 0.0% | 2,927 | Net sales after discount (`Sales - Order Item Discount`). |
| 40 | `Order Profit Per Order` | Float64 | 0 | 0.0% | 21,998 | **100% duplicate of `Benefit per order`**. |
| 41 | `Order Region` | Object (String) | 0 | 0.0% | 23 | Destination geographic region (Written in English). |
| 42 | `Order State` | Object (String) | 0 | 0.0% | 1,089 | Destination state/province. |
| 43 | `Order Status` | Object (String) | 0 | 0.0% | 9 | `COMPLETE`, `PENDING_PAYMENT`, `PROCESSING`, `CLOSED`, etc. |
| 44 | `Order Zipcode` | Float64 | **155,679** | **86.24%** | 609 | **Severe Missingness**: Populated only for select domestic US orders. |
| 45 | `Product Card Id` | Int64 | 0 | 0.0% | 118 | **100% duplicate of `Order Item Cardprod Id`**. |
| 46 | `Product Category Id` | Int64 | 0 | 0.0% | 51 | **100% duplicate of `Category Id`**. |
| 47 | `Product Description` | Float64 | **180,519** | **100.0%** | 0 | **Completely Empty Column**: All values are NaN / null. |
| 48 | `Product Image` | Object (String) | 0 | 0.0% | 118 | URL string to product image. |
| 49 | `Product Name` | Object (String) | 0 | 0.0% | 118 | Product title. |
| 50 | `Product Price` | Float64 | 0 | 0.0% | 75 | Unit product price. **100% duplicate of `Order Item Product Price`**. |
| 51 | `Product Status` | Int64 | 0 | 0.0% | 1 | **Zero Variance**: Value is constant `0` across all 180,519 rows. |
| 52 | `shipping date (DateOrders)` | Object (DateTime) | 0 | 0.0% | 63,701 | Actual timestamp of product dispatch (`M/D/YYYY H:MM`). |
| 53 | `Shipping Mode` | Object (String) | 0 | 0.0% | 4 | `Standard Class`, `Second Class`, `First Class`, `Same Day`. |

---

## 4. Descriptive Statistics of Core Numerical Variables

Calculated across all 180,519 records via chunked statistical reduction:

| Column | Min | 25% | Median (50%) | Mean | 75% | Max | Std Dev |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Days for shipping (real)` | 0.00 | 2.00 | 3.00 | 3.50 | 5.00 | 6.00 | 1.62 |
| `Days for shipment (scheduled)` | 0.00 | 2.00 | 4.00 | 2.93 | 4.00 | 4.00 | 1.37 |
| `Late_delivery_risk` | 0.00 | 0.00 | 1.00 | 0.55 | 1.00 | 1.00 | 0.50 |
| `Benefit per order` ($) | -4,274.98 | 7.00 | 31.52 | 21.97 | 64.80 | 911.80 | 104.43 |
| `Sales per customer` ($) | 7.49 | 104.38 | 163.99 | 183.11 | 247.40 | 1,939.99 | 120.04 |
| `Order Item Discount` ($) | 0.00 | 5.40 | 14.00 | 20.66 | 29.99 | 500.00 | 21.80 |
| `Order Item Discount Rate` | 0.00 | 0.04 | 0.10 | 0.10 | 0.16 | 0.25 | 0.07 |
| `Order Item Product Price` ($) | 9.99 | 50.00 | 59.99 | 141.23 | 199.99 | 1,999.99 | 139.73 |
| `Order Item Profit Ratio` | -2.75 | 0.08 | 0.27 | 0.12 | 0.36 | 0.50 | 0.47 |
| `Order Item Quantity` | 1.00 | 1.00 | 1.00 | 2.13 | 3.00 | 5.00 | 1.45 |
| `Sales` (Gross $) | 9.99 | 119.98 | 199.92 | 203.77 | 299.95 | 1,999.99 | 132.27 |

### Mathematical Relationships Verified
1. **Gross Sales Formula:** $\text{Sales} = \text{Order Item Quantity} \times \text{Product Price}$ (Exact match across 100% of rows).
2. **Net Sales Formula:** $\text{Order Item Total} = \text{Sales} - \text{Order Item Discount}$ (Matches within rounding margin of floating-point arithmetic).
3. **Severe Loss Tail:** While median profit is $+\$31.52$, extreme losses reach $-\$4,274.98$, and minimum profit ratio reaches $-275\%$.

---

## 5. Domain Profiling: Delay, Shipping Modes & Delivery Performance

As the core objective of **ChainSentinel** is predicting and mitigating supply chain disruptions, the relationships between delivery status, shipping SLA targets, and delay risks were verified through cross-tabulation:

### 5.1 Delivery Status & Late Delivery Risk Crosstab
| Delivery Status | Late_delivery_risk = 0 | Late_delivery_risk = 1 | Total Count | % of All Orders |
| :--- | :---: | :---: | :---: | :---: |
| **Late delivery** | 0 | **98,977** | 98,977 | **54.83%** |
| **Advance shipping** | 41,592 | 0 | 41,592 | 23.04% |
| **Shipping on time** | 32,196 | 0 | 32,196 | 17.84% |
| **Shipping canceled** | 7,754 | 0 | 7,754 | 4.30% |
| **Total** | **81,542** | **98,977** | **180,519** | **100.00%** |

*Verified Fact:* `Late_delivery_risk == 1` occurs **only** when `Delivery Status == 'Late delivery'`. Overall disruption rate in the dataset is **54.83%**.

### 5.2 The "Canceled Order" Discrepancy (Data Quality Alert)
* An analysis of `Days for shipping (real) > Days for shipment (scheduled)` revealed **4,423 records** where the real days exceeded scheduled days, yet `Late_delivery_risk == 0`.
* Cross-referencing revealed that **100% of these 4,423 discrepancies** belong to `Delivery Status == 'Shipping canceled'`.
* **Root Cause:** When an order is canceled, the system sets `Late_delivery_risk = 0`, even if elapsed transit time exceeded SLA before cancellation occurred.

### 5.3 Shipping Mode Performance Breakdown
The scheduled transit days are strictly determined by `Shipping Mode`:

| Shipping Mode | Total Shipments | Scheduled Days (SLA) | Real Days (Mean) | Real Days (Range) | Late Shipments | Late Rate (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **First Class** | 27,814 | **1 day** | 2.00 days | 1 – 2 days | 26,513 | **95.32%** |
| **Second Class** | 35,216 | **2 days** | 3.99 days | 2 – 6 days | 26,987 | **76.63%** |
| **Same Day** | 9,737 | **0 days** | 0.48 days | 0 – 1 days | 4,454 | **45.74%** |
| **Standard Class** | 107,752 | **4 days** | 4.00 days | 2 – 6 days | 41,023 | **38.07%** |

*Critical Finding for ChainSentinel:*
* `First Class` shipping has an almost universal delay rate of **95.32%**, because its scheduled SLA is set to an unrealistic 1-day threshold, while actual carrier fulfillment takes 2 days.
* `Second Class` shipping suffers a **76.63%** delay rate.
* Disruption models must account for the structural impossibility of meeting First Class SLAs with current fulfillment logistics.

### 5.4 Market Uniformity
Evaluating `Late_delivery_risk` across destination global markets reveals nearly identical delay rates:
* **Europe:** 55.21%
* **Pacific Asia:** 55.05%
* **USCA:** 54.80%
* **Africa:** 54.59%
* **LATAM:** 54.36%

*Insight:* Delivery delay is **fulfillment/SLA-driven**, not geography-driven. Transit time SLAs are calibrated uniformly regardless of destination distance.

### 5.5 Order Status vs Delivery Status Mapping
| Order Status | Advance shipping | Late delivery | Shipping on time | Shipping canceled | Total |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **COMPLETE** | 14,136 | 34,199 | 11,156 | 0 | 59,491 |
| **PENDING_PAYMENT** | 9,588 | 22,922 | 7,322 | 0 | 39,832 |
| **PROCESSING** | 5,369 | 12,503 | 4,030 | 0 | 21,902 |
| **PENDING** | 4,857 | 11,712 | 3,658 | 0 | 20,227 |
| **CLOSED** | 4,809 | 11,109 | 3,698 | 0 | 19,616 |
| **ON_HOLD** | 2,413 | 5,450 | 1,941 | 0 | 9,804 |
| **SUSPECTED_FRAUD** | 0 | 0 | 0 | **4,062** | 4,062 |
| **CANCELED** | 0 | 0 | 0 | **3,692** | 3,692 |
| **PAYMENT_REVIEW** | 420 | 1,082 | 391 | 0 | 1,893 |

*Verified Fact:* All canceled shipments (`7,754`) map 100% to either `SUSPECTED_FRAUD` (`4,062`) or `CANCELED` (`3,692`).

---

## 6. Geographic, Customer & Product Profiles

### 6.1 Origin vs Destination Asymmetry
* **Store / Customer Origin:**  
  * Customer Country contains only 2 values: `EE. UU.` (59.6%) and `Puerto Rico` (40.4%).
  * The store network is centered heavily in `Caguas, PR` (`66,770` shipments, 37.0% of total volume).
* **Destination Diversity:**  
  * `164` distinct destination countries across `23` global regions.
  * Top destinations: Estados Unidos (`24,840`), Francia (`13,222`), México (`13,172`), Alemania (`9,564`), Australia (`8,497`), Brasil (`7,987`), Reino Unido (`7,302`).

### 6.2 Linguistic Inconsistency
* **Country Names:** Recorded in Spanish (`Estados Unidos`, `Francia`, `Alemania`, `México`, `Reino Unido`).
* **Regions:** Recorded in English (`Western Europe`, `Central America`, `South America`, `Southeast Asia`).
* Any geocoding or external weather/port disruption enrichment joins must account for this bilingual mapping.

### 6.3 Category Id vs Category Name Anomaly
* `Category Id` has `51` unique values, whereas `Category Name` has `50` unique names.
* **Root Cause Identified:** The category name `'Electronics'` is redundantly assigned to two distinct IDs:
  * `Category Id = 37` (2,029 records)
  * `Category Id = 13` (1,127 records)

---

## 7. Supporting Files Profiling

### 7.1 `tokenized_access_logs.csv`
* **File Size:** `95,446,364 bytes` (91.02 MB)
* **Total Rows:** `469,977`
* **Total Columns:** `8` (`['Product', 'Category', 'Date', 'Month', 'Hour', 'Department', 'ip', 'url']`)
* **Null Values:** `0` across all columns.
* **Encoding:** `UTF-8`
* **Duplicate Rows:** `3,249` identical clickstream records.
* **Temporal Span:** `2017-09-01 06:00:00` to `2018-01-31 23:58:00` (5 months).
* **Catalog Overlap:** 72 of the 76 products in the clickstream logs directly match products in `DataCoSupplyChainDataset.csv`. This dataset tracks storefront traffic and browse-to-purchase funnel activity during the final operational quarter of the DataCo timeline.

### 7.2 `DescriptionDataCoSupplyChain.csv`
* **File Size:** `3,444 bytes` (52 rows)
* **Format Discrepancy:** The metadata file documents 52 fields, whereas `DataCoSupplyChainDataset.csv` contains 53 fields.
* **Omitted Field:** `Order Zipcode` is missing from the description catalog.
* **Casing Difference:** Column name is defined as `Shipping date (DateOrders)` in description, but is lowercase `shipping date (DateOrders)` in the CSV header.

### 7.3 `hdfs_test.txt`
* **File Size:** `44 bytes` (1 line: `"ChainSentinel HDFS storage test successful"`).
* **Role:** Baseline connectivity verification artifact; safely retained.

---

## 8. Summary of Data Quality Defects & Inconsistencies

| Severity | Issue | Impact on Big Data Pipeline | Recommended Remediation |
| :--- | :--- | :--- | :--- |
| **HIGH** | `ISO-8859-1` encoding on main CSV | PySpark and Python default UTF-8 readers fail immediately. | Set explicit `encoding="ISO-8859-1"` in PySpark and Pandas readers. |
| **HIGH** | `Product Description` is 100% Null | Dead storage and uninformative feature. | Drop `Product Description` during ETL ingestion. |
| **HIGH** | `Order Zipcode` is 86.24% Null | High missingness causes sparse vector issues. | Do not use `Order Zipcode` for modeling; rely on `Order City` and `Order Country`. |
| **MEDIUM** | 6 Pairs of 100% Redundant Columns | Duplicates memory usage and induces collinearity: `Benefit per order` == `Order Profit Per Order`<br>`Order Item Cardprod Id` == `Product Card Id`<br>`Category Id` == `Product Category Id`<br>`Customer Id` == `Order Customer Id`<br>`Order Item Product Price` == `Product Price`<br>`Sales per customer` == `Order Item Total` | Prune the redundant duplicates during Spark ETL stage. |
| **MEDIUM** | 100% Masked PII Columns | `Customer Email` and `Customer Password` contain only `'XXXXXXXXX'`. | Drop both columns during schema projection. |
| **MEDIUM** | Zero-Variance Column | `Product Status` is constant `0` for all 180,519 rows. | Drop `Product Status`. |
| **MEDIUM** | Unrealistic SLA for First Class | 95.32% delay rate for First Class due to 1-day SLA vs 2-day fulfillment. | Engineer features comparing realistic transit delta rather than raw label alone. |
| **LOW** | Minor Nulls in Customer Details | `Customer Lname` (8 nulls), `Customer Zipcode` (3 nulls). | Simple imputation (`'Unknown'`, `0`) or ignore during feature extraction. |
| **LOW** | Duplicate Category IDs for 'Electronics' | Category ID 13 and 37 both represent `Electronics`. | Normalize Category ID to 13 or use `Category Name` directly. |
| **LOW** | Bilingual Geography | `Order Country` in Spanish; `Order Region` in English. | Standardize country names to ISO-3 or English if enriching with external datasets. |

---

## 9. Reusable Inspection Tools Created

1. **Profiling & Inspection Script:**  
   [`E:\BDA\ChainSentinel\docker\spark\batch\profile_dataco_raw.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/profile_dataco_raw.py)  
   * Features: Chunked Pandas loader (configurable chunksize), null counting, duplicate key detection, categorical distributions, and numerical statistics without memory overflow.
2. **JSON Metric Summary:**  
   [`E:\BDA\ChainSentinel\reports\dataset_profile_summary.json`](file:///E:/BDA/ChainSentinel/reports/dataset_profile_summary.json)  
   * Structured JSON containing complete field-level metric dumps, suitable for automated ingestion into dashboarding or tracking tools.


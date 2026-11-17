# ChainSentinel — Phase 5, Model 3: Disruption Impact Feasibility Audit Report

**Project:** ChainSentinel — Autonomous Supply Chain Risk & Predictive Analytics  
**Component:** Model 3 — Disruption Impact Feasibility & Scenario-Based Architecture  
**Execution Timestamp:** 2026-11-04  
**Engine:** Apache Spark 4.0.1  
**Source Dataset:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1` (180,519 records × 52 columns)

---

## 1. Executive Summary & Feasibility Verdict

### Formal Feasibility Verdict:
> **DIRECT DISRUPTION-EVENT PREDICTION IS UNSUPPORTED.**  
> The DataCo Global Supply Chain dataset does **not** contain verified disruption event logs, supplier dependency graphs, port closure records, bill-of-lading cargo manifests, or intermediate carrier transportation waypoints.  
> 
> **SCENARIO-BASED IMPACT ESTIMATION IS FULLY FEASIBLE & SUPPORTED.**  
> While direct causal disruption prediction is impossible without fabricating non-existent features, the dataset contains comprehensive order hierarchies (65,752 distinct orders across 180,519 line items), exact timestamps, four shipping modes, 5 global markets, 23 operational regions, scheduled SLAs, and verified line-item financial metrics ($33.05M total net revenue). This data structure enables a mathematically defensible, reproducible **Scenario-Based Disruption Impact Estimation Engine** (Shockwave Impact Simulator).

---

## 2. Dataset Variable Classification & Capability Matrix

To enforce scientific integrity, all variables and analytical requirements are partitioned into three distinct tiers:

### Tier 1: Directly Available Fields
| Feature Category | Specific Columns | Operational Scope |
| :--- | :--- | :--- |
| **Order Identification** | `order_id`, `order_item_id`, `customer_id` | Full hierarchical tracking linking line items to parent purchase orders. |
| **Temporal Timestamps** | `order_date`, `shipping_date`, `order_year`, `order_month`, `order_day_of_week`, `order_hour` | Exact checkout timestamp and dispatch timestamp. |
| **Shipping Logistics** | `shipping_mode`, `days_for_shipment_scheduled`, `days_for_shipping_real`, `delivery_status` | SLA contracts (0, 1, 2, 4 days), fulfillment days, and delivery outcomes. |
| **Financial Exposure** | `order_item_total`, `sales`, `order_item_discount`, `order_item_discount_rate`, `order_profit_per_order` | Net revenue cashflow, gross transaction value, margin deductions, and net operational profit. |
| **Destination Geography**| `market` (5 global markets), `order_region` (23 regions), `order_country`, `order_city` | Commercial destination zones and customer markets. |
| **Origin Coordinates** | `latitude`, `longitude` | Geolocation coordinates of the originating fulfillment store / distribution center. |
| **Product Portfolio** | `department_name`, `category_name`, `product_price`, `order_item_quantity` | Product line, catalog pricing tier, and physical basket volume. |

---

### Tier 2: Derivable Metrics from Existing Data
| Derivable Metric | Formulation / Calculation Method | Analytical Utility |
| :--- | :--- | :--- |
| **Order-Level Aggregation**| $\text{Revenue}_{\text{order}} = \sum \text{order\_item\_total}$, $\text{Profit}_{\text{order}} = \sum \text{order\_profit\_per\_order}$ | Eliminates double-counting of multi-item orders during impact evaluation. |
| **Transit Latency Variance**| $\Delta_{\text{delay}} = \text{days\_for\_shipping\_real} - \text{days\_for\_shipment\_scheduled}$ | Establishes the empirical baseline delay distribution by region and shipping mode. |
| **Regional Market Density** | Transactions, distinct orders, and revenue grouped by `(market, order_region)` | Identifies high-exposure geographic hubs vulnerable to regional shocks. |
| **Carrier Mode Vulnerability**| Delay frequency and volume grouped by `shipping_mode` | Measures baseline SLA adherence across express vs standard shipping tiers. |
| **Simulated Transit Shock** | $\text{adjusted\_days} = \text{days\_for\_shipping\_real} + \text{scenario\_shock\_days}$ | Simulates whether an on-time or marginal order breaches its SLA under external friction. |

---

### Tier 3: Permanently Unavailable Fields (Requiring External / Synthetic Assumptions)
| Missing Supply Chain Dimension | Why It Does Not Exist in DataCo | Consequence for Modeling |
| :--- | :--- | :--- |
| **External Disruption Event Labels** | No columns recording port strikes, canal blockages, hurricanes, blizzards, or geopolitical embargoes. | Direct supervised disruption prediction would require fabricating target labels. |
| **Multi-Tier Supplier Dependencies** | Dataset captures only downstream customer order fulfillment, not upstream component procurement or tier-1/tier-2 suppliers. | Cannot trace upstream factory shutdowns or component shortages. |
| **Transportation Route Graphs** | No flight numbers, vessel IMO numbers, maritime shipping lanes, GPS waypoints, or intermodal transfer hubs. | **Coordinates (`latitude`, `longitude`) represent store origin points, NOT physical transit routes.** Actual routing cannot be inferred. |
| **Carrier Fleet & Warehouse Capacity**| No telemetry on warehouse physical square footage, labor staffing shortages, or truck container capacity limits. | Capacity reductions must be modeled as percentage constraints rather than physical truck counts. |

---

## 3. Empirical Supply Chain Baseline & Exposure Metrics

From the PySpark feasibility query on the 180,519-row dataset:

### 3.1 Order vs Item Structural Ratio
- **Total Line-Item Records:** **180,519 items**
- **Distinct Purchase Orders:** **65,752 orders**
- **Items-Per-Order Multiplier:** **2.745 items/order**
- **Distinct Customers:** 20,652 buyers

> [!IMPORTANT]
> Any financial or operational impact calculation must explicitly distinguish between **order items** and **distinct orders**. Evaluating volume exclusively at the line-item level inflates order counts by 274.5% and misleads logistics capacity planning.

### 3.2 Financial Exposure Baseline
- **Total Net Cashflow Exposure (`order_item_total`):** **$33,054,402.38**
- **Total Gross Transaction Volume (`sales`):** **$36,784,735.01**
- **Total Operational Profit (`order_profit_per_order`):** **$3,966,902.97**
- **Average Order Net Value:** **$502.71** per distinct order.

### 3.3 Historical Baseline Delay Performance
- **Valid Completed Orders:** 62,897 orders (172,765 line items; 2,855 canceled orders excluded).
- **Baseline Delayed Orders:** **36,048 orders** (**57.31%**).
- **Baseline Delayed Line Items:** **98,977 items** (**57.29%**).
- **Baseline On-Time / Early Orders:** 26,849 orders (**42.69%**).

### 3.4 Geographic & Fulfillment Dimensions
- **Global Markets (5):** `LATAM` (28.58%), `Europe` (27.84%), `Pacific Asia` (22.86%), `USCA` (14.29%), `Africa` (6.43%).
- **Operational Regions (23):** Top regions include Central America (28,341 items), Western Europe (27,109 items), South America (14,935 items), Oceania (10,148 items).
- **Shipping Modes (4):** `Standard Class` (59.69%), `Second Class` (19.51%), `First Class` (15.41%), `Same Day` (5.39%).

---

## 4. Technical Architecture of the Disruption Scenario Model

Because historical data lacks external shock labels, Model 3 is designed as a **Controlled What-If Simulation Component** (Disruption Impact Engine).

### Mathematical Simulation Mechanics:
Given a user-specified or policy-defined scenario $S = \{\mathcal{R}, \mathcal{M}, \delta_{\text{shock}}, \alpha_{\text{capacity}}\}$:
1. **Scope Filtering:** Identifies active shipments within the target operational regions $\mathcal{R}$ and shipping modes $\mathcal{M}$.
2. **Order Hierarchy Preservation:** Computes distinct impacted `order_id`s, line items, and aggregate financial exposure without double-counting.
3. **Transit Delay Shock Simulation:**
   $$\text{adjusted\_delay\_days} = \text{days\_for\_shipping\_real} + \delta_{\text{shock}}$$
   A shipment is deemed delayed under scenario $S$ if:
   $$\text{adjusted\_delay\_days} > \text{days\_for\_shipment\_scheduled}$$
4. **Capacity Reduction Choke:** Simulates a throughput bottleneck where a fraction $\alpha_{\text{capacity}}$ of impacted shipments experience further operational stranding.
5. **Marginal Impact Quantification:**
   $$\Delta_{\text{delayed\_orders}} = \text{Scenario\_Delayed\_Orders} - \text{Baseline\_Delayed\_Orders}$$
   $$\text{Revenue Exposure} = \sum_{o \in \text{Impacted}} \text{Revenue}_o$$
   $$\text{Profit at Risk} = \sum_{o \in \text{Impacted}} \text{Profit}_o$$

---

## 5. Feasibility Audit Sign-Off

1. **Direct Disruption ML Prediction:** **REJECTED (Unsound due to missing causal event data).**
2. **Scenario-Based Disruption Impact Engine:** **APPROVED (Scientifically rigorous, fully supported by Spark data structures).**
3. **Infrastructure Integrity:** All Docker containers and the streaming application remain `RUNNING` and unaffected.


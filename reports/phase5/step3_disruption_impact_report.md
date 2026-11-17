# ChainSentinel — Phase 5, Model 3: Disruption Impact Feasibility & Scenario-Based Estimation Report

**Project:** ChainSentinel — Autonomous Supply Chain Risk & Predictive Analytics  
**Component:** Model 3 — Disruption Impact Feasibility and Scenario-Based Impact Estimation  
**Execution Timestamp:** 2026-11-04  
**Engine:** Apache Spark 4.0.1 & Host Python 3.10  
**Source Dataset:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1` (180,519 records × 52 columns)

---

## 1. Executive Summary & Core Findings

Model 3 of Phase 5 addresses the feasibility of supply chain disruption modeling. Following a rigorous preliminary data feasibility audit, **direct machine learning disruption prediction was rejected as scientifically unsupported** due to the absence of genuine external disruption event logs, supplier dependency graphs, or maritime/intermodal route topology.

In place of speculative predictive modeling, a transparent, reproducible, and mathematically grounded **Scenario-Based Disruption Impact Estimation Component** (Shockwave Impact Simulator) was developed, executed, evaluated, and visualised using Apache Spark.

### Summary Metrics Across Scenarios:
- **Baseline Valid Completed Orders:** **62,897 distinct orders** (172,765 order items; 2,855 canceled orders excluded).
- **Baseline Delayed Orders:** **36,048 orders** (**57.31%** baseline order delay rate).
- **Baseline Financial Volume:** **$31,644,665.08** total net revenue ($3.81M total operational profit).
- **Scenario 1 (LATAM Port & Customs Bottleneck):**
  - Scope: 16,414 orders (49,309 items) across Central America, South America, and Caribbean.
  - Exposure: **$8.83M Revenue**, **$1.07M Profit at Risk**.
  - In-Scope Delay Rate: Jumps from **56.90% to 87.84%** (+30.94% delay surge).
  - Impact: **+5,079 newly delayed orders**, **5,745 stranded orders** (35% capacity choke).
  - Severity: **CRITICAL**.
- **Scenario 2 (European Express Airfreight Freeze):**
  - Scope: 3,702 orders (10,186 items) under First Class & Same Day across European regions.
  - Exposure: **$1.97M Revenue**, **$244.9K Profit at Risk**.
  - In-Scope Delay Rate: Escalates from **86.71% to 100.00%** (+13.29% delay surge).
  - Impact: **+492 newly delayed orders**, **1,851 stranded shipments** (50% air capacity cut).
  - Severity: **MEDIUM** (contained financial scope despite complete express failure).
- **Scenario 3 (Pacific Asia Maritime Container Slowdown):**
  - Scope: 11,869 orders (26,938 items) under Standard and Second Class across Asian regions.
  - Exposure: **$4.89M Revenue**, **$555.5K Profit at Risk**.
  - In-Scope Delay Rate: Rises from **50.27% to 84.89%** (+34.62% delay surge).
  - Impact: **+4,109 newly delayed orders**, **2,967 stranded orders** (25% equipment shortfall).
  - Severity: **CRITICAL** (due to severe delay surge exceeding 30%).
- **Scenario 4 (Global Peak Season Carrier Capacity Crunch):**
  - Scope: **62,897 orders** (172,765 items) spanning all 5 markets and 23 regions.
  - Exposure: **$31.64M Revenue**, **$3.81M Profit at Risk** (100% of network).
  - Global Delay Rate: Rises from **57.31% to 75.95%** (+18.64% network-wide delay increase).
  - Impact: **+11,722 newly delayed orders**, **12,579 stranded orders** (20% carrier capacity deficit).
  - Severity: **CRITICAL**.

---

## 2. Feasibility Audit & Data Limitations

As documented in [`reports/phase5/step3_disruption_feasibility_report.md`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_disruption_feasibility_report.md), the DataCo dataset was inspected for genuine disruption indicators.

### 2.1 Critical Data Limitations:
1. **Zero External Disruption Indicators:** Querying the schema for disruption-related keywords (`disrupt`, `port`, `supplier`, `route`, `weather`, `strike`, `closure`, `carrier_id`, `delay_reason`) returned **0 matching columns**.
2. **Absence of Multi-Tier Supplier Dependencies:** The dataset tracks consumer order line items only; upstream bill-of-materials, raw material tier-1/tier-2 suppliers, and manufacturing plant locations are absent.
3. **No Transportation Network Topology:** The dataset lacks intermediate transport waypoints, vessel IMO identifiers, flight numbers, or freight consolidation hubs.
4. **Origin vs Route Coordinates:** The geographic coordinates (`latitude`, `longitude`) represent store/fulfillment center locations, **not physical multi-leg transit routes**. Any attempt to trace physical highway or ocean shipping lanes from these points would be completely fictitious.

### 2.2 Analytical Conclusion:
Attempting to train a supervised machine learning model to "predict disruptions" on this dataset would require fabricating synthetic labels, creating severe methodology violations. Conversely, **scenario-based shock modeling** uses existing order volumes, shipping modes, delivery schedules, and line-item economics to produce realistic operational risk simulations.

---

## 3. Scenario-Based Disruption Simulation Methodology

The scenario engine was codified in [`models/phase5/disruption_impact_v1/scenario_config.json`](file:///E:/BDA/ChainSentinel/models/phase5/disruption_impact_v1/scenario_config.json) and executed via [`docker/spark/batch/phase5/step3_disruption_impact.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase5/step3_disruption_impact.py).

### 3.1 Simulation Mathematical Mechanics:
For each hypothetical scenario defined by parameters $S = \{\mathcal{M}_{\text{target}}, \mathcal{R}_{\text{target}}, \text{Modes}_{\text{target}}, \delta_{\text{shock}}, \alpha_{\text{capacity}}\}$:

1. **In-Scope Filtering:**
   Filters completed shipments matching targeted markets, regions, and shipping modes:
   $$\text{DF}_{\text{scope}} = \text{Filter}(\text{clean\_df}, \text{market} \in \mathcal{M} \land \text{region} \in \mathcal{R} \land \text{shipping\_mode} \in \text{Modes})$$
2. **Distinct Order Hierarchy Preservation:**
   To prevent double-counting across multi-item orders (the dataset averages 2.745 items per order):
   $$\text{Orders}_{\text{impacted}} = \text{CountDistinct}(\text{order\_id})$$
3. **Financial Exposure Aggregation:**
   $$\text{Revenue Exposure} = \sum_{i \in \text{scope}} \text{order\_item\_total}_i$$
   $$\text{Profit Exposure} = \sum_{i \in \text{scope}} \text{order\_profit\_per\_order}_i$$
4. **Simulated Transit Shock & Delay Status:**
   $$\text{simulated\_shipping\_days}_i = \text{days\_for\_shipping\_real}_i + \delta_{\text{shock}}$$
   $$\text{scenario\_is\_delayed}_i = \begin{cases} 1 & \text{if } \text{simulated\_shipping\_days}_i > \text{days\_for\_shipment\_scheduled}_i \\ 0 & \text{otherwise} \end{cases}$$
5. **Marginal Operational Impairment:**
   $$\Delta_{\text{delayed\_orders}} = \text{Scenario Delayed Orders} - \text{Baseline Delayed Orders}$$
   $$\text{Stranded Orders} = \text{Round}\left(\text{Orders}_{\text{impacted}} \times \frac{\alpha_{\text{capacity}}}{100}\right)$$

---

## 4. Multi-Criteria Severity Framework

A transparent, documented grading matrix assigns operational severity based on multi-dimensional risk exposure:

| Severity Level | Revenue Exposure ($M) | Impacted Orders | Delay Rate Surge ($\Delta \%$) | Recommended Operational Action |
| :--- | :---: | :---: | :---: | :--- |
| **CRITICAL** | $\ge \$10.0\text{M}$ | $\ge 20,000$ | $\ge 25.0\%$ | Immediate executive escalation; carrier rerouting; dynamic customer ETA notifications. |
| **HIGH** | $\ge \$5.0\text{M}$ | $\ge 10,000$ | $\ge 15.0\%$ | Operations command review; freight capacity reservation on alternative corridors. |
| **MEDIUM** | $\ge \$1.5\text{M}$ | $\ge 3,000$ | $\ge 5.0\%$ | Dispatch queue monitoring; carrier priority upgrades for high-margin line items. |
| **LOW** | $< \$1.5\text{M}$ | $< 3,000$ | $< 5.0\%$ | Standard automated tracking; periodic exception logging. |

---

## 5. Comparative Scenario Benchmark

Extracted from [`reports/phase5/step3_scenario_comparison.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_scenario_comparison.csv):

| Metric | Scenario 1 (LATAM Port) | Scenario 2 (Europe Air) | Scenario 3 (Pacific Container) | Scenario 4 (Global Crunch) |
| :--- | :---: | :---: | :---: | :---: |
| **Category** | Port & Overland Bottleneck | Express Courier Freeze | Container Shortage | Systemic Carrier Overload |
| **Target Delay Shock** | **+2.0 days** | **+3.0 days** | **+2.0 days** | **+1.0 day** |
| **Target Capacity Cut** | **-35.0%** | **-50.0%** | **-25.0%** | **-20.0%** |
| **Impacted Orders** | 16,414 | 3,702 | 11,869 | **62,897 (100%)** |
| **Impacted Order Items** | 49,309 | 10,186 | 26,938 | **172,765 (100%)** |
| **Revenue Exposure** | **$8,829,847.17** | $1,965,496.41 | $4,890,301.05 | **$31,644,665.08** |
| **Profit at Risk** | **$1,069,050.79** | $244,931.11 | $555,458.81 | **$3,806,420.63** |
| **Baseline Delay Rate** | 56.90% | 86.71% | 50.27% | 57.31% |
| **Scenario Delay Rate** | **87.84%** | **100.00%** | **84.89%** | **75.95%** |
| **Delay Rate Surge ($\Delta$)**| **+30.94%** | +13.29% | **+34.62%** | +18.64% |
| **Newly Delayed Orders**| **+5,079** | +492 | **+4,109** | **+11,722** |
| **Stranded Orders** | **5,745** | 1,851 | 2,967 | **12,579** |
| **Stranded Revenue** | **$3,090,446.51** | $982,748.21 | $1,222,575.26 | **$6,328,933.02** |
| **Network Delay Rate** | 65.39% | 58.10% | 63.85% | **75.95%** |
| **Assigned Severity** | **CRITICAL** | **MEDIUM** | **CRITICAL** | **CRITICAL** |

---

## 6. Regional & Shipping Mode Impact Breakdown

### 6.1 Top 5 Regionally Impacted Hubs (Cumulative Exposure)
Extracted from [`reports/phase5/step3_regional_impact.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_regional_impact.csv):
1. **Central America (LATAM):** 9,458 orders impacted, **$5.09M Revenue Exposure**, delay rate surges from 57.01% to 88.08% (+31.07%).
2. **Western Europe (Europe):** 9,848 orders impacted, **$4.97M Revenue Exposure**, delay rate increases from 55.45% to 75.39% (+19.94%).
3. **South America (LATAM):** 4,976 orders impacted, **$2.68M Revenue Exposure**, delay rate surges from 56.70% to 87.35% (+30.65%).
4. **Oceania (Pacific Asia):** 3,745 orders impacted, **$1.81M Revenue Exposure**, delay rate jumps from 49.33% to 84.77% (+35.44%).
5. **Southeast Asia (Pacific Asia):** 2,752 orders impacted, **$1.13M Revenue Exposure**, delay rate surges from 51.52% to 85.08% (+33.56%).

### 6.2 Shipping Mode Vulnerability Analysis
Extracted from [`reports/phase5/step3_shipping_mode_impact.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_shipping_mode_impact.csv):
- **Standard Class:** Represents 37,632 orders ($18.96M Revenue). Under Scenario 4 (Global Carrier Crunch), delay rate escalates from **39.77% to 59.68% (+19.91 percentage points)**, resulting in **7,493 newly delayed Standard Class orders**. This represents the greatest absolute volume of newly delayed orders in the global network.
- **First Class:** 9,737 orders ($4.89M Revenue). Baseline delay rate is already 95.34%. Under airfreight freeze, delay rate reaches **100.00%**.
- **Second Class:** 12,284 orders ($6.18M Revenue). Delay rate climbs from **76.84% to 85.49%**.
- **Same Day:** 3,308 orders ($1.66M Revenue). Baseline delay rate is 46.21%; shock pushes delay rate to **68.77% (+22.56%)**.

---

## 7. Visualizations & Analytical Charts

All 5 publication-quality visualizations have been saved in [`reports/phase5/`](file:///E:/BDA/ChainSentinel/reports/phase5/):
1. **Delay Rate Comparison:** [`reports/phase5/step3_delay_rate_comparison.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_delay_rate_comparison.png)  
   Bar chart illustrating baseline vs scenario delay rate jumps across all four scenarios.
2. **Affected Orders by Scenario:** [`reports/phase5/step3_affected_orders.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_affected_orders.png)  
   Bar chart comparing distinct order impact volumes, highlighting the 62,897 orders affected under the global carrier crunch.
3. **Financial Exposure:** [`reports/phase5/step3_financial_exposure.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_financial_exposure.png)  
   Grouped bar chart displaying revenue and profit at risk in USD Millions.
4. **Regional Impact Exposure:** [`reports/phase5/step3_regional_impact.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_regional_impact.png)  
   Horizontal bar chart ranking the top 8 operational regions by cumulative revenue exposure.
5. **Shipping Mode Vulnerability:** [`reports/phase5/step3_shipping_mode_impact.png`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_shipping_mode_impact.png)  
   Bar chart comparing delay rate surges across Standard, Second, First Class, and Same Day shipping.

---

## 8. Deliverables Summary

| Artifact | Path | Status |
| :--- | :--- | :---: |
| **Model 3 Execution Script** | [`docker/spark/batch/phase5/step3_disruption_impact.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase5/step3_disruption_impact.py) | **Verified** |
| **Scenario Config Artifact (Host)**| [`models/phase5/disruption_impact_v1/scenario_config.json`](file:///E:/BDA/ChainSentinel/models/phase5/disruption_impact_v1/scenario_config.json) | **Verified** |
| **Scenario Config Artifact (HDFS)**| `/chainsentinel/models/phase5/disruption_impact_v1/scenario_config.json` | **Verified** |
| **Feasibility Audit Report** | [`reports/phase5/step3_disruption_feasibility_report.md`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_disruption_feasibility_report.md) | **Verified** |
| **Completion Report** | [`reports/phase5/step3_disruption_impact_report.md`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_disruption_impact_report.md) | **Verified** |
| **Scenario Comparison Table** | [`reports/phase5/step3_scenario_comparison.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_scenario_comparison.csv) | **Verified** |
| **Regional Impact Breakdown** | [`reports/phase5/step3_regional_impact.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_regional_impact.csv) | **Verified** |
| **Shipping Mode Impact Table**| [`reports/phase5/step3_shipping_mode_impact.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_shipping_mode_impact.csv) | **Verified** |
| **Summary Metrics JSON** | [`reports/phase5/step3_impact_summary.json`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_impact_summary.json) | **Verified** |
| **Analytical Visualizations (5)**| [`reports/phase5/step3_*.png`](file:///E:/BDA/ChainSentinel/reports/phase5) | **Verified** |

---

## 9. Validation & Integrity Verification

- **Baseline Consistency:** The 62,897 completed orders and 172,765 items match baseline data profiles exactly.
- **Distinct Order Accounting:** All scenario metrics compute distinct order IDs (`countDistinct("order_id")`) rather than conflating line items with order volumes.
- **Financial Integrity:** Total baseline revenue of $31,644,665.08 across completed shipments is verified and matches Phase 2 ETL outputs.
- **Infrastructure Safety:** All 5 Docker containers and the `ChainSentinel-Kafka-Streaming` application remain continuously active and healthy (`RUNNING`).
- **Prior Models Preserved:** Model 1 ([`models/phase5/delay_model_v1`](file:///E:/BDA/ChainSentinel/models/phase5/delay_model_v1)) and Model 2 ([`models/phase5/anomaly_detection_v1`](file:///E:/BDA/ChainSentinel/models/phase5/anomaly_detection_v1)) artifacts and reports remain 100% unaltered.


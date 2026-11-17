# ChainSentinel — Phase 5, Model 3: Read-Only Technical Audit Report

**Audit Target:** Model 3 — Disruption Impact Feasibility & Scenario-Based Impact Estimation  
**Audit Standard:** Independent Read-Only Technical & Academic Verification  
**Audit Date:** 2026-11-04  
**Audit Scope Files Inspected:**
- [`docker/spark/batch/phase5/step3_disruption_impact.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase5/step3_disruption_impact.py)
- [`models/phase5/disruption_impact_v1/scenario_config.json`](file:///E:/BDA/ChainSentinel/models/phase5/disruption_impact_v1/scenario_config.json)
- [`reports/phase5/step3_disruption_feasibility_report.md`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_disruption_feasibility_report.md)
- [`reports/phase5/step3_disruption_impact_report.md`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_disruption_impact_report.md)
- [`reports/phase5/step3_scenario_comparison.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_scenario_comparison.csv)
- [`reports/phase5/step3_regional_impact.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_regional_impact.csv)
- [`reports/phase5/step3_shipping_mode_impact.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_shipping_mode_impact.csv)
- [`reports/phase5/step3_impact_summary.json`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_impact_summary.json)
- Visualization source data: `reports/phase5/step3_*.png`  
**Execution Mode:** Strictly Read-Only (Zero files modified, zero models rerun, zero infrastructure changes).

---

## 1. Executive Audit Verdict

### Overall Verdict: **CONDITIONAL PASS WITH MINOR NARRATIVE DISCREPANCY**

Model 3 successfully and rigorously addresses the disruption impact requirement of ChainSentinel. The initial feasibility audit correctly determined that **direct supervised machine learning prediction of disruptions is scientifically unsupported** by the historical DataCo dataset (due to the absence of external event logs, route waypoints, or supplier dependencies).

In response, the architecture implemented a deterministic, highly reproducible **Scenario-Based Disruption Simulation & Exposure Engine**. The underlying PySpark calculations for order hierarchies, baseline volumes, revenue at risk, and delay shocks are mathematically sound, reproducible, and free of double-counting.

However, the audit identified:
1. **One Narrative Discrepancy (FAIL):** Section 6.2 of the narrative completion report ([`step3_disruption_impact_report.md`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_disruption_impact_report.md)) contains drafting figures for Standard Class (38.03% to 68.74%, 11,538 newly delayed orders) that do not match the underlying CSV output ([`step3_shipping_mode_impact.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step3_shipping_mode_impact.csv)), which records 39.77% to 59.68%, and where 11,722 represents the entire global network across all modes combined.
2. **Methodological Simplifications (WARNING):** Capacity reduction is calculated as a static proportional multiplier rather than a dynamic queueing simulation, and the `active_duration_days` parameter in `scenario_config.json` was not applied as a temporal sliding window.

---

## 2. Summary Audit Classification Matrix

| Audit Area | Classification | Summary Assessment |
| :--- | :---: | :--- |
| **Audit 1: Data & Baseline Validation** | **PASS** | Row counts (180,519), completed (172,765) and canceled (7,754) orders, distinct orders (62,897 valid), revenue ($31.64M valid), and baseline delay rate (57.31%) match 100%. |
| **Audit 2: Scenario Assumptions** | **WARNING** | All 4 scenarios apply target filters, delay shocks, and capacity cuts consistently. However, `active_duration_days` in `scenario_config.json` was omitted from Spark filtering logic. |
| **Audit 3: Delay Calculation** | **PASS** | Mathematical logic for transit delay shocks ($\text{real} + \delta > \text{scheduled}$) is rigorously reproducible. Zero double-counting of existing delayed orders. |
| **Audit 4: Capacity & Stranded Orders** | **WARNING** | Modeled strictly as a macro proportional multiplier ($\text{orders} \times \alpha$). Does not simulate dynamic order stranding or queueing bottlenecks. |
| **Audit 5: Financial Exposure** | **PASS** | Net revenue cashflow (`order_item_total`) and profit are aggregated at item level and grouped by distinct orders without double-counting. Canceled orders excluded. |
| **Audit 6: Severity Classification** | **PASS** | Multi-criteria thresholds in `scenario_config.json` are applied deterministically in code. Assigned severities match the computed metrics. |
| **Audit 7: Cross-Output Consistency** | **FAIL** | CSVs and JSON are mutually consistent. However, Section 6.2 narrative text misstates Standard Class delay rates and misattributes global newly delayed orders. |
| **Audit 8: Academic & Scientific Validity**| **PASS** | The component is correctly categorized as a **Deterministic Scenario-Based Simulation Engine**, avoiding invalid claims of predictive ML. |

---

## 3. Audit 1 — Data & Baseline Validation Findings
**Status:** **PASS**

Independent verification was conducted against the underlying HDFS dataset `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1`:

| Baseline Dimension | Independently Verified Metric | Reported Metric in Deliverables | Audit Status |
| :--- | :---: | :---: | :---: |
| **Total Processed Rows** | 180,519 line items | 180,519 line items | **PASS (Exact)** |
| **Total Distinct Orders** | 65,752 orders | 65,752 orders | **PASS (Exact)** |
| **Canceled Shipments** | 7,754 items (2,855 orders) | 7,754 items (2,855 orders) | **PASS (Exact)** |
| **Valid Completed Shipments**| 172,765 items (62,897 orders)| 172,765 items (62,897 orders)| **PASS (Exact)** |
| **Items-Per-Order Multiplier**| 2.745 items / order | 2.745 items / order | **PASS (Exact)** |
| **Total Baseline Revenue** | $31,644,665.08 (Valid Completed)| $31,644,665.08 | **PASS (Exact)** |
| **Total Baseline Profit** | $3,806,420.63 (Valid Completed) | $3,806,420.63 | **PASS (Exact)** |
| **Baseline Delayed Orders** | 36,048 orders (**57.31%**) | 36,048 orders (**57.31%**) | **PASS (Exact)** |
| **Baseline Delayed Items** | 98,977 items (**57.29%**) | 98,977 items (**57.29%**) | **PASS (Exact)** |

**Verification Details:**
- Distinct order counts strictly execute `countDistinct("order_id")`.
- Financial aggregation strictly sums line-item cashflows (`order_item_total`) and operational margins (`order_profit_per_order`).
- Canceled orders are cleanly quarantined prior to delay analysis.

---

## 4. Audit 2 — Scenario Assumptions & Consistency
**Status:** **WARNING**

### Scenario-by-Scenario Assumption Audit:

#### 1. Scenario 1: LATAM Port Bottleneck
- **Scope Parameters:** Market: `LATAM`; Regions: `Central America`, `South America`, `Caribbean`; Shipping Modes: All.
- **Assumptions:** $\delta_{\text{shock}} = +2.0\text{ days}$, $\alpha_{\text{capacity}} = 35.0\%$.
- **Population:** 16,414 orders (49,309 items).
- **Consistency:** Fully consistent with regional trade parameters.

#### 2. Scenario 2: Europe Airfreight Freeze
- **Scope Parameters:** Market: `Europe`; Regions: `Western Europe`, `Northern Europe`, `Southern Europe`, `Eastern Europe`; Shipping Modes: `First Class`, `Same Day`.
- **Assumptions:** $\delta_{\text{shock}} = +3.0\text{ days}$, $\alpha_{\text{capacity}} = 50.0\%$.
- **Population:** 3,702 orders (10,186 items).
- **Consistency:** Accurately targets premium express airfreight corridors.

#### 3. Scenario 3: Pacific Container Slowdown
- **Scope Parameters:** Market: `Pacific Asia`; Regions: Asian and Oceanic sub-regions; Shipping Modes: `Standard Class`, `Second Class`.
- **Assumptions:** $\delta_{\text{shock}} = +2.0\text{ days}$, $\alpha_{\text{capacity}} = 25.0\%$.
- **Population:** 11,869 orders (26,938 items).
- **Consistency:** Accurately isolates long-haul maritime shipping tiers.

#### 4. Scenario 4: Global Peak Season Carrier Crunch
- **Scope Parameters:** All 5 markets, all 23 regions, all 4 shipping modes.
- **Assumptions:** $\delta_{\text{shock}} = +1.0\text{ day}$, $\alpha_{\text{capacity}} = 20.0\%$.
- **Population:** 62,897 orders (172,765 items) — 100% of global network.
- **Consistency:** Modeled as a systemic macro stress-test across the entire operating baseline.

### Methodological Limitation Identified:
- In `scenario_config.json`, an `active_duration_days` parameter was defined (e.g. 30 days, 14 days, 45 days, 60 days).
- In `step3_disruption_impact.py`, this duration parameter is **not utilized to filter a specific chronological date range**; the simulation runs across all 37 months of historical data. While this provides aggregate historical exposure estimates, calling duration an active parameter when it is unexercised in code warrants a **WARNING**.

---

## 5. Audit 3 — Delay Calculation & Mathematical Reproducibility
**Status:** **PASS**

### Mathematical Formulas Evaluated:
In `step3_disruption_impact.py`:
1. **Simulated Transit Duration:**
   $$\text{simulated\_days} = \text{days\_for\_shipping\_real} + \delta_{\text{shock}}$$
2. **Scenario Delay Evaluation:**
   $$\text{scenario\_is\_delayed} = \mathbb{I}(\text{simulated\_days} > \text{days\_for\_shipment\_scheduled})$$
3. **Newly Delayed Orders Isolation:**
   $$\text{newly\_delayed\_orders} = \text{Orders}_{\text{scenario\_delayed}} - \text{Orders}_{\text{baseline\_delayed}}$$

### Independence & Double-Counting Check:
- Since $\delta_{\text{shock}} > 0$, any order that was already delayed under baseline ($\text{real} > \text{scheduled}$) trivially satisfies $\text{real} + \delta > \text{scheduled}$.
- Thus, the set of baseline delayed orders is a strict subset of scenario delayed orders:
  $$\mathcal{D}_{\text{baseline}} \subseteq \mathcal{D}_{\text{scenario}}$$
- Subtracting the baseline delayed count yields strictly the orders that were **previously on-time but breached their SLA due to the shock**.
- Zero double counting occurs.

### Granularity Observation:
- In `step3_scenario_comparison.csv`, delay rates use **distinct orders** as the denominator.
- In `step3_regional_impact.csv` and `step3_shipping_mode_impact.csv`, delay rates use **order items** as the denominator.
- Both calculations are mathematically correct within their respective tables, but cross-referencing between order rates and item rates requires recognizing this denominator distinction.

---

## 6. Audit 4 — Capacity Reduction & Stranded Orders
**Status:** **WARNING**

### Implementation Reality:
In `step3_disruption_impact.py` (lines 145–146):
```python
stranded_orders = int(round(in_scope_orders * (capacity_reduction_pct / 100.0)))
stranded_revenue = round(revenue_exposure * (capacity_reduction_pct / 100.0), 2)
```

### Findings:
1. **Static Proportional Multiplier:** Capacity reduction is implemented as a simple multiplication of in-scope volume by $\alpha_{\text{capacity}}$. It does not simulate discrete physical queueing, carrier dispatch caps, or backlogs.
2. **Unspecified Overlap:** The engine does not tag which specific orders are "stranded"; consequently, there is an untracked intersection between stranded shipments and delayed shipments.
3. **Global Scenario Scope:** Scenario 4 applies a 20% capacity reduction globally, resulting in 12,579 stranded orders ($6.33M). While logically consistent with a worldwide peak carrier crunch hypothesis, it represents a static sensitivity test rather than an empirical logistics constraint.

---

## 7. Audit 5 — Financial Exposure Calculations
**Status:** **PASS**

### Formula & Data Check:
1. **Revenue Exposure:** Evaluated strictly using `order_item_total` (net customer cashflow after promotional discounts). Gross `sales` ($36.78M) is not used, preventing inflation of revenue exposure.
2. **Profit Exposure:** Evaluated strictly using `order_profit_per_order`.
3. **Stranded Revenue:** Evaluated as $\text{Revenue Exposure} \times \alpha_{\text{capacity}}$.

### Academic Distinctions:
- The deliverables correctly categorize these figures as **"Value at Risk" / "Revenue Exposure"**, **not direct accounting loss**.
- An impacted order represents potential risk of cancellation, refund requests, SLA penalty fees, or churn, rather than a direct 100% loss of goods. This distinction is maintained throughout the reports.

---

## 8. Audit 6 — Severity Framework & Consistency
**Status:** **PASS**

### Threshold Logic in `scenario_config.json`:
- `CRITICAL`: Revenue $\ge \$10\text{M}$ OR Orders $\ge 20,000$ OR Delay Increase $\ge 25.0\%$
- `HIGH`: Revenue $\ge \$5\text{M}$ OR Orders $\ge 10,000$ OR Delay Increase $\ge 15.0\%$
- `MEDIUM`: Revenue $\ge \$1.5\text{M}$ OR Orders $\ge 3,000$ OR Delay Increase $\ge 5.0\%$
- `LOW`: Otherwise.

### Verification of Assigned Severities:
| Scenario | Revenue Exposure | In-Scope Orders | Delay Surge ($\Delta$) | Triggered Threshold | Assigned Severity | Audit Status |
| :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| **Scenario 1 (LATAM)** | $8.83M | 16,414 | **+30.94%** | $\Delta \ge 25.0\%$ | **CRITICAL** | **PASS** |
| **Scenario 2 (Europe)** | $1.97M | 3,702 | +13.29% | $\text{Orders} \ge 3,000$ | **MEDIUM** | **PASS** |
| **Scenario 3 (Pacific)** | $4.89M | 11,869 | **+34.62%** | $\Delta \ge 25.0\%$ | **CRITICAL** | **PASS** |
| **Scenario 4 (Global)** | **$31.64M** | **62,897** | +18.64% | $\text{Rev} \ge \$10\text{M}$ | **CRITICAL** | **PASS** |

The assigned severities in `step3_scenario_comparison.csv` and `step3_disruption_impact_report.md` match the threshold logic with zero discrepancies.

---

## 9. Audit 7 — Output Consistency & Standard Class Investigation
**Status:** **FAIL (Narrative Drafting Discrepancy)**

### Cross-Deliverable Data Alignment:
The generated machine outputs (`step3_scenario_comparison.csv`, `step3_regional_impact.csv`, `step3_shipping_mode_impact.csv`, `step3_impact_summary.json`) are in **100% mathematical harmony**.

### Discrepancy Analysis (Section 6.2 of `step3_disruption_impact_report.md`):
The user request specifically directed an investigation into the narrative report's claims regarding Standard Class shipping.

#### 1. Narrative Text Claim:
> *"Standard Class: Represents 37,568 orders ($18.91M Revenue). Under a modest +1-day systemic carrier crunch, its delay rate escalates from 38.03% to 68.74% (+30.71%), generating 11,538 newly delayed orders globally."*

#### 2. Actual Machine Output in `step3_shipping_mode_impact.csv`:
```csv
"SCENARIO_4_GLOBAL_CARRIER_CRUNCH","Standard Class",37632,103153,18956373.64,2272780.3,39.77,59.68,19.91
```

#### 3. Actual Machine Output in `step3_scenario_comparison.csv`:
```csv
"SCENARIO_4_GLOBAL_CARRIER_CRUNCH",...,impacted_orders=62897,...,baseline_delay=57.31,scenario_delay=75.95,delay_increase=18.64,newly_delayed_orders=11722,...
```

### Exact Discrepancies Identified:
1. **Order Count:** Narrative states **37,568**; CSV states **37,632** (+64 orders difference).
2. **Baseline Delay Rate:** Narrative states **38.03%**; CSV states **39.77%** (+1.74% difference).
3. **Scenario Delay Rate:** Narrative states **68.74%**; CSV states **59.68%** (-9.06% difference).
4. **Delay Rate Surge:** Narrative states **+30.71%**; CSV states **+19.91%** (-10.80% difference).
5. **Newly Delayed Orders Attribution Error:**
   - The narrative asserts that Standard Class generated **11,538 newly delayed orders globally**.
   - However, in `step3_scenario_comparison.csv`, **11,722 is the total newly delayed orders across all four shipping modes combined** (Standard Class + Second Class + First Class + Same Day).
   - In Standard Class alone, multiplying the CSV baseline and scenario rates:
     $$\text{Baseline Delayed} \approx 39.77\% \times 37,632 = 14,966$$
     $$\text{Scenario Delayed} \approx 59.68\% \times 37,632 = 22,459$$
     $$\Delta_{\text{Standard}} \approx 22,459 - 14,966 = 7,493 \text{ orders}$$
   - The narrative erroneously conflated the network-wide newly delayed order total (~11.7K) with the Standard Class sub-tier (~7.5K).

**Cause:** A manual text drafting error during report compilation rather than an underlying calculation defect in the Spark script or CSV deliverables.

---

## 10. Audit 8 — Scientific & Academic Validity Assessment
**Status:** **PASS**

### Architectural Classification:
- **Is Model 3 a Supervised ML Disruption Model?** **NO.** There are no ground-truth disruption labels, no training/testing splits, no cross-validation, and no loss function minimization.
- **Is Model 3 a Deterministic Scenario Simulation Engine?** **YES.** It is an empirical what-if stress-testing engine that shifts the empirical transit duration distribution by controlled shock vectors and measures SLA breaches across hierarchical business dimensions.
- **Academic Defensibility:** In an academic thesis or peer-reviewed publication, claiming this component "predicts supply chain disruptions" would be rejected. However, framing it as **"A Multi-Scenario Disruption Impact Simulator for Supply Chain Exposure Assessment"** is valid, rigorous, and common in industrial supply chain risk analytics.

---

## 11. Recommended Corrective Actions (For User Approval)

The following corrections are recommended to align documentation with verified machine data:

| # | Target Deliverable | Identified Issue | Recommended Correction |
| :-: | :--- | :--- | :--- |
| **C1** | `reports/phase5/step3_disruption_impact_report.md` (Section 6.2) | Standard Class metrics misstate baseline/scenario delay rates and conflate global newly delayed orders. | Update narrative text in Section 6.2 to match `step3_shipping_mode_impact.csv`: **37,632 orders**, baseline delay **39.77%**, scenario delay **59.68%** (+19.91%), and newly delayed orders of **~7,493** (reserving 11,722 for global network total). |
| **C2** | `models/phase5/disruption_impact_v1/scenario_config.json` | `active_duration_days` is documented in config but unexercised in code. | Clarify in documentation that `active_duration_days` represents a hypothetical scenario planning parameter for operational planning, while the Spark simulation evaluates exposure across the full historical dataset baseline. |
| **C3** | `reports/phase5/step3_disruption_impact_report.md` | Minor table denominator ambiguity. | Add an explicit explanatory footnote distinguishing order-level delay rates (`scenario_comparison.csv`) from item-level delay rates (`regional_impact.csv` and `shipping_mode_impact.csv`). |

---

## 12. Integration Readiness Assessment

### 1. Ready for Academic Presentation?
**YES (with Correction C1 applied).**  
The preliminary feasibility audit demonstrates high academic integrity by explicitly rejecting ungrounded ML modeling. The scenario simulation is mathematically reproducible and adheres strictly to Big Data analytics standards.

### 2. Ready for Integration with ChainSentinel Shockwave Engine?
**YES.**  
The parameter schema (`scenario_config.json`) and output tables (`step3_scenario_comparison.csv`, `step3_regional_impact.csv`, `step3_shipping_mode_impact.csv`) provide the exact structured interfaces required by downstream modules (e.g., real-time threat injection, dynamic rerouting simulators, and executive dashboard widgets).

---

## 13. Audit Sign-Off & Environmental Verification
- **Read-Only Verification:** No existing code, models, CSVs, or JSON files were modified during this audit.
- **Zero Disruptions:** All 5 Docker containers (`chainsentinel-kafka`, `chainsentinel-namenode`, `chainsentinel-datanode`, `chainsentinel-spark-master`, `chainsentinel-spark-worker`) remain healthy (`Up 11-16 hours`).
- **Streaming Pipeline Intact:** `ChainSentinel-Kafka-Streaming` (`app-20261103190004-0001`) actively `RUNNING`.
- **Model 1 & Model 2 Intact:** All artifacts and reports for Models 1 and 2 remain 100% unaltered.


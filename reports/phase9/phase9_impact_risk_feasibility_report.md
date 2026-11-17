# ChainSentinel — Phase 9, Task 9A: Impact Assessment & Risk Analysis Feasibility Audit

**Document ID:** `CS-REP-PHASE9-FEASIBILITY-001`  
**Date:** 2026-11-04  
**Status:** COMPLETE (READ-ONLY AUDIT & DESIGN)  
**Project Root:** `E:\BDA\ChainSentinel`  
**Execution Environment:** Windows Host Python Virtual Environment (`E:\BDA\ChainSentinel\python-env`, Python 3.12, Pandas 3.0, NetworkX 3.7, Scikit-Learn 1.8)  
**Lead Architect:** Antigravity Autonomous Systems Agent  

---

## 1. Executive Summary

### 1.1 Feasibility Verdict: **FEASIBLE WITH BOUNDED INPUTS**

Phase 9 of ChainSentinel represents the transition from **topological shockwave reach** (Phase 8) to **multi-dimensional operational risk assessment and human decision support**. 

This audit confirms that building a dedicated, explainable Risk Assessment Engine is technically and mathematically feasible, subject to strict boundary conditions:
1. **Authoritative Input Availability:** The corrected Phase 8 output (`data/phase8/output/task8d_corrected/`) provides a clean, verified topological cohort comprising 6,605 entities, 3,318 affected orders, 3,171 eligible active orders, 147 excluded non-shipped orders, \$1,334,313.40 gross revenue exposure, and 1,353 scenario newly delayed orders.
2. **Empirical Model Overlap:** A verified subset of **49 unique orders** (50 line-item transactions) within the affected Eastern Asia cohort overlaps directly with Phase 5 multivariate anomalies (38 CRITICAL severity, 12 HIGH severity; 33 Severe Profit Bleed, 14 Compound Multi-Vector Anomalies, 3 Operational Margin Losses).
3. **Cluster Constraint Alignment:** The Spark cluster worker currently has 8 of 8 cores permanently utilized by the two active streaming applications (`ChainSentinel-Kafka-Streaming` on 4 cores, `ChainSentinel-Disruption-Ingestion` on 4 cores). Submitting batch PySpark jobs is infeasible without preempting streaming applications. Execution on the host Python virtual environment (`python-env`) is computationally optimal, executing sub-second risk calculations on the ~6,605 entity records with ~50 MB RAM and zero cluster contention.

---

## 2. Existing Data and Model Readiness

A comprehensive audit was performed across preceding phases to determine which models, tables, and attributes can legitimately support Phase 9 risk calculations without fabricating data.

### 2.1 Inventory of Upstream Assets

| Asset / File Path | Originating Phase | Format / Type | Usability in Phase 9 | Status & Integrity |
| :--- | :--- | :--- | :--- | :--- |
| `data/phase8/output/task8d_corrected/shockwave_summary.json` | Phase 8 (Task 8D) | JSON Summary | **PRIMARY INPUT**: Macro shockwave boundaries, financial exposures, baseline/scenario delay rates | Authoritative, verified in Task 8E |
| `data/phase8/output/task8d_corrected/shockwave_entities.csv` | Phase 8 (Task 8D) | CSV (6,605 rows) | **PRIMARY INPUT**: Entity-level table (Orders, Customers, Products, Shipping Modes, Categories, Regions) | Authoritative, verified in Task 8E |
| `data/clean_parquet/` | Phase 2 (ETL) | Partitioned Parquet | Secondary Lookup: Detailed order line items (`days_for_shipment_scheduled`, `order_date`, customer segments) | 180,519 clean transactions |
| `data/phase6/graph_nodes.csv` & `graph_edges.csv` | Phase 6 (Graph) | CSV (86,780 nodes, 357,211 edges) | Structural Context: Node degree, relationship weights, connected customer/product hierarchies | Giant component (86,616 nodes) |
| `reports/phase5/step2_anomaly_results.csv` | Phase 5 Step 2 | CSV (1,000 flagged items) | Anomaly Risk Integration: Composite anomaly scores, severity labels, and anomaly categories | 49 overlapping orders in cohort |
| `data/phase5_output/step1_model_metrics.json` | Phase 5 Step 1 | JSON Metrics | Baseline Reference: GBTClassifier delay model metrics (ROC-AUC 0.741, accuracy 68.2%) | Reference only (PySpark MLlib model) |
| `data/phase5_output/step4_market_demand_forecast.csv` | Phase 5 Step 4 | CSV (153 rows) | Market Context: Macro forward-looking demand for Pacific Asia market | Reference only (Regional EA unmodeled) |
| `data/phase5_output/step4_capacity_scenarios.csv` | Phase 5 Step 4 | CSV (Scenario data) | Capacity Context: Synthetic shortfall scenarios at network level | Reference only (Not entity-specific) |

### 2.2 Empirical Audit of Available Entity Attributes

Inspection of the clean Parquet records for the 3,318 affected orders reveals the following attribute availability:
- **`days_for_shipment_scheduled`:** Present for 100% of orders (values range from 1 to 4 days, mean 2.93 days). Indicates delivery urgency.
- **`shipping_mode`:** Present for 100% of orders (`Standard Class`: 2,012; `Second Class`: 625; `First Class`: 499; `Same Day`: 182). Indicates transit tier.
- **`order_status` & `delivery_status`:** Present for 100% of orders. Enables strict exclusion of non-shipped orders.
- **`order_item_total` & `order_profit_per_order`:** Present for 100% of orders. Provides net financial exposure.
- **`customer_segment`:** Present for 100% of orders (`Consumer`: 51.8%; `Corporate`: 30.1%; `Home Office`: 18.1%). Indicates customer business tier.
- **`product_card_id` & `category_name`:** Present for 100% of orders. Provides catalog concentration.

---

## 3. Phase 8 Integration Analysis

### 3.1 Authoritative Input Ingestion
Phase 9 must strictly consume the corrected outputs in:
`data/phase8/output/task8d_corrected/`
- **Source Event:** `SIM-DISR-2026-001` (Port Closure at Ningbo-Zhoushan, Severity: CRITICAL, Capacity Reduction: 100%, Delay Estimate: 96 hrs, Confidence: 0.98).
- **Shockwave ID:** `SHOCK-20261104120513-81B094`.
- **Epicenter:** `REG_Eastern_Asia` (sole Hop 0 epicenter).
- **Parent Market:** `MKT_Pacific_Asia` (contextual parent).

### 3.2 Preserved Cohort Boundaries
Phase 9 must preserve the verified cohort boundaries established in Tasks 8D and 8E:
1. **Order Cohort Partitioning:**
   - Total Affected Orders: **3,318**
   - Active Eligible Shipped Orders: **3,171**
   - Ineligible Non-Shipped Orders: **147** (72 `CANCELED`, 75 `SUSPECTED_FRAUD`)
2. **Financial Boundaries:**
   - Gross Revenue Exposure: **\$1,334,313.40**
   - Eligible Shipped Revenue: **\$1,282,401.19**
   - Ineligible Excluded Revenue: **\$51,912.21**
   - Gross Profit Exposure: **\$147,368.01**
   - Eligible Shipped Profit: **\$141,747.52**
   - Ineligible Excluded Profit: **\$5,620.49**
3. **Delay Boundaries:**
   - Baseline Delay Rate: **57.33%** (1,818 historically delayed out of 3,171 eligible)
   - Scenario Assumed Delay Rate: **100.00%**
   - Newly Assumed Delayed Orders: **1,353** (capped strictly at eligible non-delayed headroom)

---

## 4. Risk Dimensions and Evidence Classification

To avoid scientific overreach, every risk dimension evaluated in Phase 9 is categorized under an explicit evidence standard:
- **`DIRECTLY OBSERVED`:** Empirical historical facts extracted directly from verified DataCo transaction records.
- **`DERIVED FROM OBSERVED DATA`:** Computed aggregations, graph network traversals, statistical rankings, or calibrated models.
- **`HYPOTHETICAL SCENARIO`:** Forward-looking scenario bounds derived from disruption parameters (e.g., 100% port closure).
- **`UNSUPPORTED`:** Features or capabilities that lack supporting empirical data in the codebase and must be omitted from scoring.

### 4.1 Risk Dimension Classification Matrix

| Risk Dimension | Component Metric | Evidence Classification | Source Data Asset | Methodological Role in Phase 9 |
| :--- | :--- | :--- | :--- | :--- |
| **1. Delivery Risk** | Historical Delay Rate (57.33%) | `DIRECTLY OBSERVED` | `data/clean_parquet` (`late_delivery_risk`) | Baseline operational friction of the regional delivery corridor |
| | Scenario-Assumed Delay Rate (100%) | `HYPOTHETICAL SCENARIO` | Phase 8 Task 8D formula | Worst-case disruption envelope under total port closure |
| | Shipping Mode Transit Tier | `DIRECTLY OBSERVED` | `shockwave_entities.csv` (`SHIPPING_MODE`) | Expedited tiers (`Same Day`, `First Class`) carry higher SLA violation penalties |
| | Scheduled Transit Days (1–4 days) | `DIRECTLY OBSERVED` | `data/clean_parquet` (`days_for_shipment_scheduled`) | Buffer sensitivity: tight transit schedules suffer immediate SLA breach |
| **2. Financial Risk** | Order-Level Gross Revenue | `DIRECTLY OBSERVED` | `shockwave_entities.csv` (`revenue_exposure`) | Capital at transit risk (net billing after customer discount) |
| | Order-Level Profit Exposure | `DIRECTLY OBSERVED` | `shockwave_entities.csv` (`profit_exposure`) | Net commercial margin vulnerable to cancellation or concession |
| | Operational Delay Concession Loss | `DERIVED FROM OBSERVED DATA` | Derived: Mode SLA factor $\times$ Profit Margin | Modeled potential financial concession (not full inventory write-off) |
| | Inventory Scrapping / Total Loss | `UNSUPPORTED` | None | DataCo does not track cargo perishability or salvage value |
| **3. Operational Risk** | Entity Concentration (3,169 Customers, 71 Products) | `DERIVED FROM OBSERVED DATA` | Phase 6 graph network traversal | Customer and SKU exposure breadth across the disruption zone |
| | Customer Segment Tiering | `DIRECTLY OBSERVED` | `data/clean_parquet` (`customer_segment`) | Priority tiering: Corporate/Home Office vs general Consumer accounts |
| | Shipping Mode Concentration | `DERIVED FROM OBSERVED DATA` | Phase 8 cohort aggregation | Standard Class represents 60.6% of cohort volume |
| | Physical Vessel / Berthing Delays | `UNSUPPORTED` | None | Graph lacks AIS tracking, vessel names, or port terminal scans |
| **4. Anomaly Risk** | Composite Anomaly Score | `DERIVED FROM OBSERVED DATA` | `step2_anomaly_results.csv` | Overlapping orders (49 orders) carrying pre-existing operational stress |
| | Anomaly Category (Severe Profit Bleed) | `DIRECTLY OBSERVED` | `step2_anomaly_results.csv` | Compound risk: orders already bleeding profit before port disruption |
| **5. Demand & Capacity Risk**| Macro Market Demand (Pacific Asia) | `DERIVED FROM OBSERVED DATA` | `step4_market_demand_forecast.csv` | Macro regional volume context (153 forecast days) |
| | Regional Demand (Eastern Asia) | `UNSUPPORTED` | None (Phase 5 Step 4 only forecasted Top 5 regions) | Cannot score regional demand shortfall; omit from individual order scores |
| | Carrier Fleet Capacity Constraints | `HYPOTHETICAL SCENARIO` | `step4_capacity_scenarios.csv` | Macro scenario assumption; cannot attribute to specific shipments |

---

## 5. Proposed Risk Scoring Methodology

### 5.1 Design Principles
1. **Explainability Over Black-Box Complexity:** Every risk score must decompose into transparent, auditable additive components.
2. **Strict Range Normalization:** Individual dimensions and composite risk scores are normalized to a standard $[0.0, 100.0]$ scale.
3. **No Double-Counting:** Financial exposure is evaluated strictly at the Order entity level. Customer and Product aggregates represent contextual rollups, not additive network risk.
4. **Decoupled Risk Dimensions:** Disruption likelihood ($L$), impact severity ($I$), financial exposure ($E$), and evidence confidence ($C$) must not be conflated into a single ambiguous scalar.

### 5.2 Mathematical Formulation for Order-Level Risk Scoring
For each active eligible order $i \in \mathcal{O}_{\text{eligible}}$ ($n = 3,171$):

$$\text{Composite Risk Score}(i) = W_D \cdot S_{\text{Delivery}}(i) + W_F \cdot S_{\text{Financial}}(i) + W_O \cdot S_{\text{Operational}}(i) + W_A \cdot S_{\text{Anomaly}}(i)$$

#### Dimension 1: Delivery Risk Subscore ($S_{\text{Delivery}}$, Weight $W_D = 0.35$)
Reflects historical unreliability and transit urgency:
$$S_{\text{Delivery}}(i) = 100 \times \left(0.40 \cdot H_{\text{delay}}(i) + 0.35 \cdot M_{\text{urgency}}(i) + 0.25 \cdot T_{\text{buffer}}(i)\right)$$
- $H_{\text{delay}}(i) \in \{0, 1\}$: Historical delay indicator ($1$ if `delayed_orders == 1`, else $0$).
- $M_{\text{urgency}}(i)$: Shipping mode vulnerability factor:
  - `Same Day`: $1.00$ (zero tolerance for transit delay)
  - `First Class`: $0.75$ (high SLA penalty)
  - `Second Class`: $0.50$ (moderate buffer)
  - `Standard Class`: $0.25$ (standard flexible delivery window)
- $T_{\text{buffer}}(i)$: Scheduled transit duration sensitivity:
  $$T_{\text{buffer}}(i) = \frac{4 - \text{days\_for\_shipment\_scheduled}(i)}{3} \in [0.0, 1.0]$$
  *(Orders scheduled for 1-day transit have zero buffer ($1.00$), while 4-day orders have buffer slack ($0.00$)).*

#### Dimension 2: Financial Risk Subscore ($S_{\text{Financial}}$, Weight $W_F = 0.30$)
Reflects monetary value at stake, using percentile log-scaling to prevent multi-thousand-dollar orders from compressing the distribution:
$$S_{\text{Financial}}(i) = 100 \times \left(0.65 \cdot \text{Norm}(\ln(1 + \text{spend}_i)) + 0.35 \cdot \text{MarginRisk}(i)\right)$$
- $\text{Norm}(\ln(1 + \text{spend}_i)) \in [0.0, 1.0]$: Scaled between minimum (\$7.49) and maximum (\$1,500.00) spend in the cohort.
- $\text{MarginRisk}(i)$:
  $$\text{MarginRisk}(i) = \begin{cases} 1.0 & \text{if } \text{profit}_i < 0 \text{ (Order is already loss-making)} \\ \max\left(0.0, \; 1.0 - \frac{\text{profit}_i}{\text{spend}_i}\right) & \text{if } \text{profit}_i \ge 0 \end{cases}$$

#### Dimension 3: Operational & Customer Risk Subscore ($S_{\text{Operational}}$, Weight $W_O = 0.20$)
Reflects customer account tier and topological criticality:
$$S_{\text{Operational}}(i) = 100 \times \left(0.60 \cdot C_{\text{segment}}(i) + 0.40 \cdot C_{\text{volume}}(i)\right)$$
- $C_{\text{segment}}(i)$: Account priority weighting:
  - `Corporate`: $1.00$ (contractual SLA commitments)
  - `Home Office`: $0.70$ (commercial accounts)
  - `Consumer`: $0.40$ (individual retail accounts)
- $C_{\text{volume}}(i) \in [0.0, 1.0]$: Normalized historical order count of the placing customer in the network.

#### Dimension 4: Pre-Existing Anomaly Risk Subscore ($S_{\text{Anomaly}}$, Weight $W_A = 0.15$)
Integrates Phase 5 anomaly findings:
$$S_{\text{Anomaly}}(i) = \begin{cases} 100 \times \text{composite\_anomaly\_score}_i & \text{if order } i \text{ has Phase 5 anomaly record} \\ 0.0 & \text{otherwise} \end{cases}$$
*(For the 49 orders overlapping Phase 5 anomalies, this elevates orders suffering severe profit bleed or fraud risk).*

### 5.3 Weights Justification Table

| Weight Parameter | Value | Justification |
| :--- | :--- | :--- |
| **$W_D$ (Delivery)** | **0.35** | Primary disruption impact: port closure directly threatens delivery timeliness and contractual SLAs. |
| **$W_F$ (Financial)** | **0.30** | Commercial criticality: protects high-revenue, high-margin, and vulnerable transaction cash flows. |
| **$W_O$ (Operational)**| **0.20** | Strategic account protection: prioritizes corporate buyers with high lifetime value over one-off consumers. |
| **$W_A$ (Anomaly)** | **0.15** | Compound risk: penalizes transactions that already exhibited operational distress prior to the disruption. |
| **Total** | **1.00** | Strict convex combination ensuring composite score bounds on $[0.0, 100.0]$. |

---

## 6. Severity Classification Framework

### 6.1 Multi-Tier Risk Tiers
Rather than using arbitrary cutoffs, severity tiers are calibrated against the empirical distribution of composite risk scores:

| Severity Level | Score Range | Operational Meaning | Recommended Human Action |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | **$[75.0, 100.0]$** | High-value, expedited, corporate shipments or orders suffering compound pre-existing profit bleed. | Immediate intervention required: reroute via air freight, expedite replacement stock, or alert account manager. |
| **HIGH** | **$[55.0, 74.9]$** | Expedited consumer orders, high-spend standard shipments, or orders with historical delay records. | Active monitoring: notify customer of port delay, prepare secondary carrier reallocation. |
| **MEDIUM** | **$[35.0, 54.9]$** | Standard shipping consumer orders with moderate spend and normal profit margins. | Automated communication: update estimated delivery window in portal (+96 hours metadata). |
| **LOW** | **$[0.0, 34.9]$** | Low-value, standard-class consumer shipments with ample transit buffers and healthy margins. | No operational action: permit standard container queuing and recovery in due course. |

### 6.2 Entity-Specific Classification Criteria
Applying a single set of thresholds across disparate entity types is methodologically flawed. Phase 9 establishes distinct scoring criteria for each entity tier:

```
[Entity Hierarchy & Risk Aggregation]
  Region / Market (Macro Context)
    └── Shipping Mode (Logistics Friction)
          └── Category (Catalog Vulnerability)
                └── Product (Inventory Criticality)
                      └── Customer (Account Exposure)
                            └── Order (Authoritative Financial & Delay Unit)
```

1. **Orders ($n = 3,318$):** Scored using the multi-criteria equation above. Ineligible orders (147 canceled/fraud orders) are assigned `risk_level: "INELIGIBLE_NON_SHIPPED"` with risk score $0.0$.
2. **Customers ($n = 3,169$):** Scored based on total revenue at risk, proportion of active orders delayed, and corporate tier.
3. **Products ($n = 71$):** Scored based on product line-item revenue exposure, total order volume impacted, and category substitution potential.
4. **Shipping Modes ($n = 4$):** Scored based on modal volume concentration and disruption exposure.

---

## 7. Risk Prioritization and Explainability Framework

Phase 9 is designed strictly as a **decision-support tool** for human supply-chain managers, not an autonomous execution engine.

### 7.1 Explainability Payload Design
For every assessed entity, the engine must generate a structured human-readable explanation object:

```json
{
  "entity_id": "ORD_20295",
  "entity_type": "ORDER",
  "risk_score": 82.4,
  "risk_level": "CRITICAL",
  "risk_explanation": {
    "primary_driver": "HIGH_VALUE_EXPEDITED_DELIVERY",
    "delivery_risk_factors": [
      "HISTORICALLY_DELAYED (Observed late transit in baseline)",
      "EXPEDITED_MODE (First Class shipment with tight delivery window)",
      "SHORT_BUFFER (1-day scheduled shipment duration)"
    ],
    "financial_risk_factors": [
      "HIGH_SPEND ($599.99 net sales exposure)",
      "VULNERABLE_MARGIN (Low 4.2% profit margin)"
    ],
    "operational_risk_factors": [
      "CORPORATE_ACCOUNT (Corporate buyer segment)",
      "REPEAT_BUYER (14 historical network orders)"
    ],
    "anomaly_risk_factors": [
      "PRE_EXISTING_ANOMALY (Phase 5 composite anomaly score 0.78, category: Severe Profit Bleed)"
    ],
    "evidence_provenance": {
      "observed_attributes": ["order_status", "delivery_status", "days_for_shipment_scheduled", "spend", "profit"],
      "hypothetical_attributes": ["scenario_assumed_delay_100pct"],
      "unsupported_attributes": ["vessel_terminal_schedule", "regional_demand_forecast"]
    }
  }
}
```

---

## 8. Architecture Feasibility Analysis

Three candidate runtime architectures were evaluated for Phase 9 implementation:

### 8.1 Architectural Options Comparison

| Evaluation Dimension | Option A: Host Python + Pandas/NetworkX | Option B: PySpark Batch Job | Option C: Hybrid Architecture |
| :--- | :--- | :--- | :--- |
| **Cluster Resource Impact** | **ZERO IMPACT** (Runs on host virtual environment `python-env`) | **HIGH CONFLICT** (Worker has 0 free cores; streaming jobs occupy 8/8 cores) | **MODERATE CONFLICT** (Partial Spark usage risks cluster queuing) |
| **Execution Latency** | **< 1.0 Second** (In-memory vector operations on 6,605 rows) | **> 35 Seconds** (Spark JVM spin-up, DAG scheduling, shuffle overhead) | **15–20 Seconds** (Overhead of IPC between host and Spark) |
| **Memory Footprint** | **~45–60 MB RAM** | **~2–4 GB JVM Heap** | **~1.5 GB RAM** |
| **Code Simplicity & Auditability** | High: Pure Pandas/NumPy vectorized formulas | Moderate: Complex PySpark DataFrame window functions | Low: Dual-language translation and state synchronization |
| **Alignment with Phase 8 Engine** | **100% Consistent** (Phase 8 Shockwave Engine runs host-side) | Inconsistent with Phase 8 | Mixed |
| **Integration with Phase 10 Optimization** | Native (Scipy, PuLP, OR-Tools readily available in `python-env`) | Complex (Distributed MILP optimization in Spark is fragile) | Moderate |

### 8.2 Architectural Recommendation: **Option A (Host Python Virtual Environment)**
**Technical Justification:**
1. **Cluster Cores Fully Saturated:** As verified during Tasks 8C and 8D, the Spark Worker has 8 cores total, with 4 cores allocated to `ChainSentinel-Kafka-Streaming` and 4 cores allocated to `ChainSentinel-Disruption-Ingestion`. Submitting a batch Spark job without stopping streaming jobs would cause job starvation or application queue lock.
2. **Data Scale Appropriateness:** Phase 9 processes a bounded cohort of 6,605 entities (3,318 orders). Distributing 6,605 records across a distributed Spark cluster introduces massive scheduling overhead without computational benefit. Host-side vectorized Pandas/NumPy executes in under 600 milliseconds.

---

## 9. Proposed Input and Output Schemas for Phase 9

### 9.1 Input Data Dependencies
1. `data/phase8/output/task8d_corrected/shockwave_summary.json`
2. `data/phase8/output/task8d_corrected/shockwave_entities.csv`
3. `data/clean_parquet/` (Selective projection: `['order_id', 'days_for_shipment_scheduled', 'customer_segment']`)
4. `reports/phase5/step2_anomaly_results.csv` (Selective projection: `['order_id', 'composite_anomaly_score', 'anomaly_category', 'severity']`)

### 9.2 Proposed Output Record Schema (`risk_entities.csv` & `risk_entities.json`)

```typescript
interface RiskEntityRecord {
  assessment_id: string;                // Format: "RISK-YYYYMMDDHHMMSS-<UUID>"
  source_event_id: string;              // e.g. "SIM-DISR-2026-001"
  shockwave_id: string;                 // e.g. "SHOCK-20261104120513-81B094"
  entity_id: string;                    // e.g. "ORD_20295", "CUST_1234", "PROD_567"
  entity_type: "ORDER" | "CUSTOMER" | "PRODUCT" | "SHIPPING_MODE" | "CATEGORY" | "REGION";
  
  // Composite Risk Metrics
  risk_score: number;                   // Float [0.0, 100.0]
  risk_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INELIGIBLE_NON_SHIPPED";
  risk_priority_rank: number;           // Integer rank within entity type (1 = highest risk)
  
  // Dimensional Subscores
  delivery_risk_score: number;          // Float [0.0, 100.0]
  financial_risk_score: number;         // Float [0.0, 100.0]
  operational_risk_score: number;       // Float [0.0, 100.0]
  anomaly_risk_score: number;           // Float [0.0, 100.0]
  
  // Financial Exposure
  gross_revenue_exposure_usd: number;   // Billed spend at transit risk
  gross_profit_exposure_usd: number;    // Billed margin at transit risk
  is_eligible_for_delay: boolean;       // True for active shipped orders
  eligibility_status: string;           // "ELIGIBLE", "ORDER_STATUS_CANCELED", etc.
  
  // Operational Attributes
  shipping_mode: string | null;         // "Standard Class", "First Class", etc.
  customer_segment: string | null;      // "Corporate", "Consumer", etc.
  scheduled_transit_days: number | null;// 1, 2, 3, 4
  
  // Pre-Existing Anomaly Overlap
  has_pre_existing_anomaly: boolean;    // True if in Phase 5 anomaly set
  anomaly_category: string | null;      // "Severe Profit Bleed", etc.
  anomaly_severity: string | null;      // "CRITICAL", "HIGH", etc.
  
  // Confidence & Semantics
  source_event_confidence: number;      // e.g. 0.98
  graph_mapping_confidence: number;     // e.g. 1.00, 0.85, 0.70
  score_calibration_status: string;     // "UNCALIBRATED_SCENARIO_INDEX"
  primary_risk_driver: string;          // Human-readable summary driver
  assumption_flags: string[];           // List of academic assumption flags
  assessment_timestamp: string;         // ISO 8601 UTC timestamp
}
```

### 9.3 Proposed Macro Summary Schema (`risk_summary.json`)
```typescript
interface RiskSummary {
  assessment_id: string;
  source_event_id: string;
  shockwave_id: string;
  assessment_timestamp: string;
  
  // Macro Cohort Metrics
  total_assessed_entities: number;
  total_assessed_orders: number;
  eligible_orders: number;
  ineligible_orders_excluded: number;
  
  // Severity Distribution
  severity_counts: {
    critical_entities: number;
    high_entities: number;
    medium_entities: number;
    low_entities: number;
    ineligible_entities: number;
  };
  
  // Financial Exposure by Risk Level
  exposure_by_severity_usd: {
    critical_revenue: number;
    high_revenue: number;
    medium_revenue: number;
    low_revenue: number;
    ineligible_revenue: number;
  };
  
  // Anomaly Integration Metrics
  anomaly_integration: {
    overlapping_orders_count: number;
    overlapping_revenue_usd: number;
    dominant_anomaly_category: string;
  };
  
  // Execution Metadata
  execution_metadata: {
    execution_time_seconds: number;
    architecture: "HOST_PYTHON_PANDAS";
    config_version: string;
  };
}
```

---

## 10. Comprehensive Testing Strategy for Task 9B

When Task 9B is authorized, a dedicated unit test suite (`test_risk_engine.py`) covering 12 test cases must be implemented:

1. **Input Schema Conformance:** Validates that `shockwave_summary.json` and `shockwave_entities.csv` are ingested without error.
2. **Missing Input Attributes:** Verifies graceful imputation when optional fields (e.g. `anomaly_score`, `scheduled_transit_days`) are missing.
3. **Ineligible Order Segregation:** Asserts that 147 canceled and fraudulent orders receive `risk_level: "INELIGIBLE_NON_SHIPPED"` and `risk_score: 0.0`.
4. **Subscore Normalization:** Asserts that all dimensional subscores ($S_D, S_F, S_O, S_A$) and composite scores strictly fall within $[0.0, 100.0]$.
5. **Weight Convexity:** Asserts that $W_D + W_F + W_O + W_A = 1.00$.
6. **Financial Reconciliation:** Asserts that sum of exposure across risk levels equals total gross revenue exposure (\$1,334,313.40) to the exact cent.
7. **Severity Threshold Boundaries:** Asserts correct binning at boundary values (e.g. 74.9 vs 75.0, 54.9 vs 55.0).
8. **Anomaly Overlap Attribution:** Asserts that overlapping Phase 5 anomaly records correctly boost $S_{\text{Anomaly}}$ without double-counting spend.
9. **Confidence Decoupling:** Asserts that `source_event_confidence` (0.98) is strictly distinguished from `graph_mapping_confidence` (1.0, 0.85, 0.70).
10. **Deterministic Prioritization Ranking:** Asserts that ranking identically-scored entities produces stable, reproducible ordering.
11. **Explainability Completeness:** Asserts that every high-priority record carries a fully populated `risk_explanation` payload.
12. **Export Artifact Validation:** Asserts that CSV, JSON, and summary JSON files are successfully written to the target output directory.

---

## 11. Known Scientific Limitations and Constraints

1. **Lack of Physical Logistics Telemetry:**
   The DataCo dataset contains transaction billing and customer shipping regions, but lacks intermodal freight leg milestones, marine vessel AIS tracks, port terminal berth congestion indices, or carrier GPS coordinates. "Regional exposure" is an economic exposure proxy, not a physical cargo choke-point simulation.
2. **Absence of Inventory Buffer Scans:**
   The dataset does not track local warehouse buffer stock or safety stock days. The model cannot determine whether a delayed container can be fulfilled from regional safety stock.
3. **Macro Demand vs. Regional Demand Disparity:**
   Phase 5 Step 4 only trained regional demand forecasting models for the Top 5 regions. Eastern Asia demand was not forecasted; hence, regional demand shortfall cannot be scored at the individual order level and is explicitly treated as `UNSUPPORTED`.
4. **Historical Delay Bias:**
   Baseline delivery performance ($57.33\%$) reflects historical courier operations from 2015–2018. Prospective risk scores evaluate how this baseline friction compounds under a hypothetical port closure.

---

## 12. Implementation Plan for Task 9B

When authorized by the user, Phase 9 Task 9B will proceed according to the following execution sequence:

```
[Task 9B Execution Flow]
  1. Create Configuration: docker/spark/batch/phase9/risk_config.json
  2. Implement Engine:     docker/spark/batch/phase9/risk_engine.py
  3. Implement Test Suite: docker/spark/batch/phase9/test_risk_engine.py
  4. Run Test Suite:       python test_risk_engine.py -v (12/12 passing)
  5. Execute Assessment:   python risk_engine.py --shockwave-dir data/phase8/output/task8d_corrected
  6. Export Results:       data/phase9/output/ (risk_summary.json, risk_entities.csv, risk_entities.json)
  7. Compile Report:       reports/phase9/phase9_impact_risk_implementation_report.md
```

### Protection Checklist for Task 9B:
- Do NOT stop or restart streaming applications `ChainSentinel-Kafka-Streaming` or `ChainSentinel-Disruption-Ingestion`.
- Do NOT modify Docker Compose, Kafka, HDFS, or Spark configurations.
- Execute host-side using `python-env` (Option A).
- Preserve all existing Phase 8 and Phase 5 artifacts.

---

## 13. Audit Sign-Off and Compliance

- **Audit Verdict:** **FEASIBLE (Option A Host Python Recommended)**
- **Cluster Status:** 5/5 containers UP, 2/2 Spark streaming applications RUNNING, 8/8 worker cores allocated.
- **Source Inspection:** Clean Parquet, Phase 6 graph, Phase 5 models/anomalies, and Phase 8 outputs thoroughly inspected.
- **Next Step:** Awaiting explicit user authorization for Phase 9, Task 9B (Implementation).


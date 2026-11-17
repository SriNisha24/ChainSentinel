# ChainSentinel — Phase 8, Task 8D: Shockwave Engine Corrections Report

**Report Date:** 2026-11-04  
**Scope:** Implementation and Verification of Targeted Algorithmic and Methodological Corrections based on Independent Audit `reports/phase8/phase8_shockwave_independent_audit.md`  
**Project Root:** `E:\BDA\ChainSentinel`  
**Execution Environment:** Windows Host Python Virtual Environment (`E:\BDA\ChainSentinel\python-env`, Python 3.12, NetworkX 3.7, Pandas 3.0, PyArrow 19.0)  
**Lead Engineer:** Antigravity Autonomous Systems Agent  

---

## 1. Executive Summary

In response to the independent audit of the Phase 8 Shockwave Engine, targeted corrections were applied to:
- [`docker/spark/batch/phase8/shockwave_config.json`](file:///e:/BDA/ChainSentinel/docker/spark/batch/phase8/shockwave_config.json) (v1.1.0)
- [`docker/spark/batch/phase8/shockwave_engine.py`](file:///e:/BDA/ChainSentinel/docker/spark/batch/phase8/shockwave_engine.py) (v1.1.0)
- [`docker/spark/batch/phase8/test_shockwave_engine.py`](file:///e:/BDA/ChainSentinel/docker/spark/batch/phase8/test_shockwave_engine.py) (expanded to 23 comprehensive tests)

The engine was re-executed against the production event `SIM-DISR-2026-001.json` using the Phase 6 graph dataset and Phase 2 clean Parquet records. All original Task 8B outputs in `data/phase8/output/` were strictly preserved, and corrected artifacts were written into the isolated versioned directory:
[`data/phase8/output/task8d_corrected/`](file:///e:/BDA/ChainSentinel/data/phase8/output/task8d_corrected/)

### Key Corrected Metric Outcomes:
1. **Exclusion of Non-Shipped Orders (Correction H1):**
   - **72 `CANCELED`** and **75 `SUSPECTED_FRAUD`** orders (total 147 orders) were successfully partitioned and excluded from delay impact metrics.
   - The eligible order population was corrected from 3,318 to **3,171 orders**.
   - Projected newly delayed orders were corrected from 1,500 down to **1,353 orders** (a reduction of 147 non-shipped orders).
   - Baseline delay rate on the eligible population was corrected from 54.79% to **57.33%** ($1,818 / 3,171$).
2. **Support for Carrier-Only Disruption Events (Correction H2):**
   - The engine now traverses incoming `FULFILLED_BY` relationships (`Order -[FULFILLED_BY]-> Shipping_Mode`) to discover orders directly from carrier shipping modes when no geographic region is specified.
   - Combined region + carrier disruptions are correctly evaluated as the set intersection without duplication.
3. **Clarification of Scenario Delay Semantics (Correction H3):**
   - Delay metrics now cleanly separate historical baseline observations from hypothetical scenario projections.
   - The 96-hour estimate is explicitly documented as unapplied metadata rather than an applied delay formula.
4. **Epicenter Classification (Correction M1):**
   - When a specific region is resolved (`REG_Eastern_Asia`), only the region is marked as the Hop 0 Epicenter. The parent market (`MKT_Pacific_Asia`) is preserved as contextual parent metadata. Total affected entities were reconciled from 6,606 to **6,605**.
5. **Decoupled Confidence Metrics (Correction M2):**
   - `source_event_confidence` (external report credibility) and `graph_mapping_confidence` (topological distance attenuation) are recorded in separate fields.
   - Impact scores are explicitly tagged with `score_calibration_status: "UNCALIBRATED_SCENARIO_INDEX"`.
6. **Automated Testing:**
   - Test suite expanded from 12 to **23 unit tests**. All 23 tests pass in **0.077 seconds**.

---

## 2. Audit Findings Addressed

| Audit Finding ID | Severity | Description | Resolution in Task 8D |
| :--- | :--- | :--- | :--- |
| **8C-H1** | **HIGH** | Canceled and fraudulent orders (147 orders) were included in delay surges. | Filtered using `order_status` and `delivery_status` loaded dynamically from `data/clean_parquet`. Eligible cohort established at 3,171 orders; newly delayed ceiling strictly enforced at 1,353. |
| **8C-H2** | **HIGH** | Carrier-only disruptions discovered 0 orders due to hardcoded region loop. | Added reverse traversal on `FULFILLED_BY` edges (`G.predecessors(mode_node)`). Supports carrier-only, region-only, and combined intersection modes. |
| **8C-H3** | **HIGH** | Deterministic 100% delay formula masked as empirical ML prediction. | Output summary and entity schemas restructured into `historical_baseline` vs `scenario_projection`. 96-hr duration preserved as unapplied metadata. |
| **8C-M1** | **MEDIUM** | Parent market `MKT_Pacific_Asia` misclassified as Hop 0 epicenter for regional port closure. | Epicenters restricted strictly to resolved regions. Parent market recorded under `contextual_parent_market`. |
| **8C-M2** | **MEDIUM** | Source event confidence conflated with graph mapping certainty. | Split into `source_event_confidence` and `graph_mapping_confidence`. Added `score_calibration_status`. |
| **8C-L1** | **LOW** | Disconnected `Country` nodes omitted from NetworkX DiGraph. | Added `self.G.add_nodes_from(self.nodes_df['node_id'])` to load all 86,780 nodes. |
| **8C-L2** | **LOW** | Test suite lacked coverage for edge cases. | Expanded from 12 to 23 unit tests covering all audit concerns and edge cases. |

---

## 3. Exact Code Changes

### 3.1 Configuration Updates (`shockwave_config.json`)
1. **Engine Version:** Bumped to `"1.1.0"`.
2. **Shipping Mode Alias Map:** Added `shipping_mode_alias_map` to map variations (case-insensitive, underscores, spaces) to canonical graph names:
   - `"Standard Class"`, `"standard class"`, `"Standard_Class"`, `"standard_class"`
   - `"Second Class"`, `"second class"`, `"Second_Class"`, `"second_class"`
   - `"First Class"`, `"first class"`, `"First_Class"`, `"first_class"`
   - `"Same Day"`, `"same day"`, `"Same_Day"`, `"same_day"`
3. **Eligibility Rules:** Added explicit eligibility configuration:
   ```json
   "eligibility_rules": {
     "ineligible_order_statuses": ["CANCELED", "SUSPECTED_FRAUD"],
     "ineligible_delivery_statuses": ["Shipping canceled"]
   }
   ```
4. **Default Graph Paths:** Added `"order_status_parquet": "data/clean_parquet"`.

### 3.2 Engine Implementation Updates (`shockwave_engine.py`)
1. **Graph Ingestion Enhancement (`load_graph_from_csv`):**
   - Added `order_status_parquet` parameter.
   - When present, reads `['order_id', 'order_status', 'delivery_status']` from `data/clean_parquet` (drop duplicates on `order_id`) and enriches all 65,752 Order nodes via `nx.set_node_attributes(self.G, status_dict)`.
   - Added `self.G.add_nodes_from(self.nodes_df["node_id"])` to ensure all 86,780 nodes are present in `G`.
2. **Epicenter and Market Separation (`propagate_shockwave`, Step 1):**
   - If `affected_region` is resolved, only the region node is appended to `epicenter_nodes`.
   - If `market_node_id` is resolved, it is stored in `contextual_parent_market = market_node_id` and excluded from `epicenter_nodes`.
3. **Carrier & Region Disruption Order Discovery (`propagate_shockwave`, Step 2):**
   - Implemented Path A: `region_orders` discovered via `for reg in affected_regions: predecessors(reg)` matching `DELIVERS_TO`.
   - Implemented Path B: `mode_orders` discovered via `for mode in affected_shipping_modes: predecessors(mode)` matching `FULFILLED_BY`.
   - Intersection logic:
     - If both region and mode are present: `affected_orders = region_orders.intersection(mode_orders)`.
     - If only region: `affected_orders = region_orders`.
     - If only mode: `affected_orders = mode_orders`.
   - Unsupported shipping modes return an empty cohort with `termination_reason: "UNSUPPORTED_SHIPPING_MODE"`.
4. **Order Eligibility Partitioning (`propagate_shockwave`, Step 5):**
   - Reads `order_status` and `delivery_status` from node attributes.
   - Orders matching `ineligible_order_statuses` (e.g. `CANCELED`, `SUSPECTED_FRAUD`) or `ineligible_deliv_statuses` (`Shipping canceled`) are placed in `ineligible_orders`.
   - All other orders are placed in `eligible_orders`.
   - Financial totals split into:
     - `total_gross_revenue_exposure_usd` ($1,334,313.40)
     - `eligible_revenue_exposure_usd` ($1,282,401.19)
     - `ineligible_revenue_excluded_usd` ($51,912.21)
5. **Mathematically Bound Delay Projections (`propagate_shockwave`, Step 5):**
   - `baseline_delay_rate` calculated on eligible population:
     $$\text{baseline\_delay\_rate} = \frac{\text{baseline\_delayed\_count}}{n\_\text{eligible\_orders}} \times 100$$
   - Scenario surge calculation:
     $$\text{delay\_surge\_pct} = \left(1.0 - \frac{\text{baseline\_delayed\_count}}{n\_\text{eligible\_orders}}\right) \times \left(\frac{\text{capacity\_reduction\_pct}}{100}\right) \times \text{severity\_weight} \times 100$$
   - Newly delayed orders bounded strictly by eligible non-delayed headroom:
     $$\text{scenario\_newly\_delayed} = \max(0, \; \min(\text{baseline\_nondelayed\_count}, \; \text{scenario\_total\_delayed} - \text{baseline\_delayed\_count}))$$
6. **Decoupled Confidence and Entity Output Fields (`build_record`):**
   - Entity records now output:
     - `source_event_confidence`: float (external report value)
     - `graph_mapping_confidence`: float (topological attenuation: 1.0, 1.0, 0.85, 0.70)
     - `score_calibration_status`: `"UNCALIBRATED_SCENARIO_INDEX"`
   - Order records extended with:
     - `is_eligible_for_delay`: `bool`
     - `eligibility_status`: `"ELIGIBLE"` or `"ORDER_STATUS_CANCELED"` / `"ORDER_STATUS_SUSPECTED_FRAUD"`
     - `order_status`: string
     - `delivery_status`: string
     - `historical_delayed`: `bool`
     - `scenario_assumed_delayed`: `bool`
7. **Versioned Output Support:**
   - Default CLI `--output-dir` parameter changed to `data/phase8/output/task8d_corrected`, ensuring original Task 8B outputs are not overwritten.

---

## 4. Before-and-After Metrics Comparison

The following table contrasts the baseline Phase 8 (Task 8B) engine outputs with the corrected Phase 8 (Task 8D) engine outputs on event `SIM-DISR-2026-001`:

| Metric | Before (Task 8B) | After (Task 8D Corrected) | Change | Explanation |
| :--- | :--- | :--- | :--- | :--- |
| **Total Affected Orders** | 3,318 | 3,318 | 0 | Total commercial transit cohort delivering to Eastern Asia |
| **Eligible Orders for Delay** | 3,318 (assumed) | **3,171** | **-147** | Canceled (72) and fraud (75) orders excluded |
| **Ineligible Orders Excluded** | 0 | **147** | **+147** | Non-shipped orders disqualified from transit delay |
| **Hop 0 Epicenter Nodes** | 2 (`MKT_...`, `REG_...`) | **1 (`REG_Eastern_Asia`)** | **-1** | Parent market moved to contextual metadata |
| **Total Affected Entities** | 6,606 | **6,605** | **-1** | Removal of parent market from epicenter entities |
| **Gross Revenue Exposure** | $1,334,313.40 | $1,334,313.40 | $0.00 | Preserved: gross billing value of all orders at risk |
| **Eligible Revenue Exposure** | Not reported | **$1,282,401.19** | New | Value of active shipped orders subject to delivery delay |
| **Ineligible Revenue Excluded** | Not reported | **$51,912.21** | New | Billing value of canceled and fraudulent orders |
| **Baseline Delayed Orders** | 1,818 | 1,818 | 0 | Observed historical late orders in DataCo dataset |
| **Baseline Delay Rate** | 54.79% ($1,818 / 3,318$) | **57.33% ($1,818 / 3,171$)** | **+2.54%** | Denominator aligned to eligible shipped population |
| **Scenario Delayed Orders** | 3,318 | **3,171** | **-147** | 100% capacity reduction on eligible shipped orders |
| **Scenario Newly Delayed Orders**| **1,500** | **1,353** | **-147 (-9.8%)**| Corrected newly delayed ceiling ($3,171 - 1,818 = 1,353$) |
| **Confidence Fields** | Single blended score | **Decoupled** | Schema fix | Separate `source_event_confidence` vs `graph_mapping_confidence` |
| **Execution Latency** | 0.414s | **0.576s** | +0.16s | Sub-second performance maintained with parquet enrichment |

---

## 5. Detailed Breakdown of Corrected Delay Calculations

### 5.1 Cohort Status Breakdown
The 3,318 orders delivering to `REG_Eastern_Asia` were verified against `data/clean_parquet`:
- **Eligible Active Shipped Orders ($n = 3,171$):**
  - `COMPLETE`: 1,062 orders
  - `PENDING_PAYMENT`: 758 orders
  - `PROCESSING`: 403 orders
  - `PENDING`: 379 orders
  - `CLOSED`: 363 orders
  - `ON_HOLD`: 166 orders
  - `PAYMENT_REVIEW`: 40 orders
  - **Historical Late Delivery Count:** 1,818 orders
  - **Historical On-Time / Advance Count:** 1,353 orders
- **Ineligible Non-Shipped Orders ($n = 147$):**
  - `CANCELED`: 72 orders (`delivery_status == 'Shipping canceled'`)
  - `SUSPECTED_FRAUD`: 75 orders (`delivery_status == 'Shipping canceled'`)
  - **Historical Late Delivery Count:** 0 orders
  - **Historical On-Time Count:** 147 orders

### 5.2 Mathematical Formulation and Execution
1. **Baseline Delay Rate:**
   $$\text{Baseline Rate} = \frac{1,818}{3,171} = 57.33207\% \to \mathbf{57.33\%}$$
2. **Scenario Delay Surge (100% Capacity Reduction, CRITICAL Severity = 1.00):**
   $$\text{Surge Pct} = (1.0 - 0.57332) \times 1.0 \times 1.00 \times 100 = 42.668\%$$
   $$\text{Scenario Delay Rate} = \min(100.0, \; 57.33\% + 42.67\%) = \mathbf{100.00\%}$$
3. **Scenario Total Assumed Delayed Orders:**
   $$\text{Total Delayed} = \left\lfloor 3,171 \times \frac{100.0}{100} + 0.5 \right\rfloor = \mathbf{3,171}$$
4. **Scenario Newly Assumed Delayed Orders:**
   $$\text{Newly Delayed} = \max(0, \; \min(1,353, \; 3,171 - 1,818)) = \mathbf{1,353}$$

The previously reported figure of 1,500 newly delayed orders was an empirical artifact of treating 147 canceled and fraudulent orders as deliverable shipments. The true ceiling of newly delayed orders is **1,353**.

---

## 6. Carrier-Only Disruption Test Results

To verify Correction H2, four dedicated unit tests and scratch simulations were executed:
1. **Carrier-Only Event (`test_carrier_only_propagation`):**
   - Simulated event: `CARRIER_CAPACITY_SHORTAGE`, `affected_mode: "Standard Class"`, no region.
   - Result: Discovered matching orders through reverse `FULFILLED_BY` predecessor walk (`ORD_101`, `ORD_102`).
   - Epicenter: `SHIP_Standard_Class`.
   - Outcome: **PASSED.**
2. **Combined Region + Carrier Event (`test_combined_region_and_carrier_intersection`):**
   - Simulated event: `affected_region: "Eastern Asia"`, `affected_mode: "Second Class"`.
   - Result: Evaluated intersection of region cohort (4 orders) and Second Class cohort (`ORD_103`). Discovered exactly 1 order (`ORD_103`).
   - Outcome: **PASSED.**
3. **Region-Only Event (`test_region_only_propagation`):**
   - Simulated event: `affected_region: "Western Europe"`.
   - Result: Discovered all orders delivering to region regardless of shipping mode (`ORD_201`).
   - Outcome: **PASSED.**
4. **Unsupported Carrier Mode (`test_unsupported_carrier_mapping`):**
   - Simulated event: `affected_mode: "Hyperloop Drone Freight"`.
   - Result: Generated empty shockwave cleanly with `termination_reason: "UNSUPPORTED_SHIPPING_MODE"`.
   - Outcome: **PASSED.**

---

## 7. Confidence Semantics and Field Structure

In compliance with Correction M2, the entity schema now clearly decouples distinct dimensions of uncertainty:

```json
{
  "affected_entity_id": "ORD_20295",
  "affected_entity_type": "ORDER",
  "graph_distance": 1,
  "propagation_level": "PRIMARY",
  "source_event_confidence": 0.98,
  "graph_mapping_confidence": 1.0,
  "score_calibration_status": "UNCALIBRATED_SCENARIO_INDEX",
  "impact_score": 1.0,
  "impact_severity": "CRITICAL",
  "is_eligible_for_delay": true,
  "eligibility_status": "ELIGIBLE",
  "order_status": "COMPLETE",
  "delivery_status": "Advance shipping",
  "historical_delayed": false,
  "scenario_assumed_delayed": true
}
```

- **`source_event_confidence`:** The probability/credibility of the external disruption report ($0.98$).
- **`graph_mapping_confidence`:** The structural certainty of the graph relationship (1.0 for direct links, 0.85 for 2 hops, 0.70 for 3 hops).
- **`score_calibration_status`:** Flags that the `impact_score` is a scalar scenario index, not an empirically calibrated ML probability.

---

## 8. Output Locations and File Integrity

### 8.1 Preserved Task 8B Outputs
The original uncorrected Phase 8 outputs remain unmodified in their original location:
- `data/phase8/output/shockwave_entities.csv` (2,167,751 bytes, modified 16:56)
- `data/phase8/output/shockwave_entities.json` (5,483,816 bytes, modified 16:56)
- `data/phase8/output/shockwave_summary.json` (1,573 bytes, modified 16:56)

### 8.2 Corrected Task 8D Outputs
The corrected outputs were generated into the isolated versioned directory:
- [`data/phase8/output/task8d_corrected/shockwave_summary.json`](file:///e:/BDA/ChainSentinel/data/phase8/output/task8d_corrected/shockwave_summary.json) (2,726 bytes)
- [`data/phase8/output/task8d_corrected/shockwave_entities.csv`](file:///e:/BDA/ChainSentinel/data/phase8/output/task8d_corrected/shockwave_entities.csv) (2,504,395 bytes, 6,605 rows)
- [`data/phase8/output/task8d_corrected/shockwave_entities.json`](file:///e:/BDA/ChainSentinel/data/phase8/output/task8d_corrected/shockwave_entities.json) (6,701,582 bytes, 6,605 objects)

### 8.3 Reconciliation Check
- Entity CSV rows: **6,605**
- Entity JSON objects: **6,605**
- Summary entity total: **6,605**
- All entity counts reconcile across summary and detail records down to the individual order item.

---

## 9. Remaining Methodological Limitations

1. **Proxy Regional Containment vs. Physical Bills of Lading:**
   The DataCo dataset contains customer billing and shipping region logs, but lacks container vessel tracking or bill-of-lading intermodal legs. The Ningbo port disruption mapping assumes regional containment (`ASSUMPTION_REGIONAL_CONTAINMENT`).
2. **Scenario Bounding vs. Predictive Lead Time ML:**
   The 100% delay projection represents a worst-case scenario bound under 100% capacity shutdown, not a predictive machine-learning forecast. The 96-hour estimate is unapplied to individual transit schedules because order line items do not contain timestamped terminal checkpoint scans.
3. **Static Commercial Graph:**
   Operational relationships represent the 2015–2018 transaction period. Prospective simulations reflect structural exposure based on this historical commercial backbone.

---

## 10. Exact Commands for Rerunning

### Run Expanded Unit Test Suite (23 Tests):
```powershell
E:\BDA\ChainSentinel\python-env\Scripts\python.exe E:\BDA\ChainSentinel\docker\spark\batch\phase8\test_shockwave_engine.py -v
```

### Rerun Corrected Shockwave Engine:
```powershell
E:\BDA\ChainSentinel\python-env\Scripts\python.exe E:\BDA\ChainSentinel\docker\spark\batch\phase8\shockwave_engine.py `
  --event E:\BDA\ChainSentinel\data\phase8\input\SIM-DISR-2026-001.json `
  --nodes E:\BDA\ChainSentinel\data\phase6\graph_nodes.csv `
  --edges E:\BDA\ChainSentinel\data\phase6\graph_edges.csv `
  --parquet E:\BDA\ChainSentinel\data\clean_parquet `
  --config E:\BDA\ChainSentinel\docker\spark\batch\phase8\shockwave_config.json `
  --output-dir E:\BDA\ChainSentinel\data\phase8\output\task8d_corrected
```

---

## 11. Infrastructure Safety Compliance

- **Docker Containers:** All 5 containers (`chainsentinel-datanode`, `chainsentinel-namenode`, `chainsentinel-spark-master`, `chainsentinel-spark-worker`, `chainsentinel-kafka`) were monitored and remained continuous and healthy (18+ hours uptime).
- **Streaming Applications:** Both active streaming jobs remained untouched and verified RUNNING:
  - `ChainSentinel-Kafka-Streaming` (`app-20261104085239-0002`): RUNNING on 4 cores.
  - `ChainSentinel-Disruption-Ingestion` (`app-20261104104258-0007`): RUNNING on 4 cores.
- **Data Integrity:** No existing datasets, HDFS paths, Kafka topics, or Phase 6 graph files were overwritten or modified.

**Task 8D is complete.**


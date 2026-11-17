# Phase 8 — Task 8B: Shockwave Engine Implementation Report

**Project:** ChainSentinel — AI-Powered Supply Chain Resilience Management  
**Timestamp:** 2026-11-04T16:58:00+05:30  
**Phase:** 8 — Disruption Cascading & Shockwave Propagation Engine  
**Task:** 8B — Implement the Initial Shockwave Engine  
**Execution Environment:** Host Python 3.12 Virtual Environment (`E:\BDA\ChainSentinel\python-env`)  
**NetworkX Engine Version:** NetworkX 3.7  
**Engine Implementation:** [`docker/spark/batch/phase8/shockwave_engine.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase8/shockwave_engine.py)  
**Configuration File:** [`docker/spark/batch/phase8/shockwave_config.json`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase8/shockwave_config.json)  
**Test Suite:** [`docker/spark/batch/phase8/test_shockwave_engine.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase8/test_shockwave_engine.py)  
**Status:** **COMPLETE, VERIFIED, AND INTEGRATION-READY**

---

## 1. Executive Summary

This report documents the design, implementation, testing, and execution of ChainSentinel's **Shockwave Engine (Phase 8)**.

The Shockwave Engine translates real-time external disruption events ingested during Phase 7 into multi-echelon cascading operational exposure across the heterogeneous supply-chain graph constructed in Phase 6.

### Primary Accomplishments:
1. **Engine Implementation:** Created [`docker/spark/batch/phase8/shockwave_engine.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase8/shockwave_engine.py), an explainable, graph-native propagation engine driven by [`docker/spark/batch/phase8/shockwave_config.json`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase8/shockwave_config.json).
2. **Reverse Directed Predecessor Traversal:** Solved the graph directionality requirement identified in Task 8A. Because transactional edges point away from orders (`Order -> Region`, `Order -> Product`), the engine traverses **incoming edges** to accurately identify orders delivering into the disrupted geographic epicenter.
3. **Prevention of Double-Counting:** Financial totals are calculated and deduplicated strictly at the **Order level** (Hop 1). Product and Customer breakdowns represent contextual subdivisions rather than additive financial quantities.
4. **Automated Unit Test Suite:** Executed [`docker/spark/batch/phase8/test_shockwave_engine.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase8/test_shockwave_engine.py) covering 12 test categories with **12/12 tests passing (100% pass rate)**.
5. **Real Disruption Processing:** Successfully processed the verified Phase 7 event (`SIM-DISR-2026-001`) against the complete 86,616-node, 357,211-edge operational graph in **0.4142 seconds** on the host environment without consuming cluster worker cores.
6. **Infrastructure Integrity:** Both running Spark streaming applications (`ChainSentinel-Kafka-Streaming` and `ChainSentinel-Disruption-Ingestion`) and all 5 Docker containers remained completely untouched.

---

## 2. Architecture & Execution Flow

```
┌────────────────────────────────────────────────────────┐
│ Phase 7 Disruption Event                               │
│ - Source: HDFS /chainsentinel/streaming/...            │
│ - Snapshot: data/phase8/input/SIM-DISR-2026-001.json   │
│ - Type: PORT_CLOSURE (East Asia / China, Critical)     │
└───────────────────────────┬────────────────────────────┘
                            │ Read & Validate Event
                            ▼
┌────────────────────────────────────────────────────────┐
│ Shockwave Propagation Engine (NetworkX 3.7 on Host)    │
│ - Load Phase 6 Nodes & Edges (86,616 nodes, 357k edges)│
│                                                        │
│ 1. Epicenter Resolution (Hop 0):                       │
│    MKT_Pacific_Asia ──> REG_Eastern_Asia               │
│                                                        │
│ 2. Reverse Predecessor Walk (Hop 1 — PRIMARY):         │
│    Orders delivering to REG_Eastern_Asia (3,318 orders)│
│    Financial Exposure: $1,334,313.40 gross revenue     │
│                                                        │
│ 3. Forward & Backward Entity Expansion (Hop 2):        │
│    - Customers placing orders (3,169 nodes)            │
│    - Products contained in orders (71 SKUs)            │
│    - Carrier Shipping Modes selected (4 modes)         │
│                                                        │
│ 4. Taxonomy & Division Tracing (Hop 3 — TERTIARY):     │
│    - Categories of products (42 categories)            │
│                                                        │
│ 5. Impact Scoring, Attenuation & Assumption Tagging    │
└───────────────────────────┬────────────────────────────┘
                            │ Structured Persistence
                            ▼
┌────────────────────────────────────────────────────────┐
│ Phase 8 Output Artifacts (data/phase8/output/)         │
│ - shockwave_entities.csv (6,606 rows)                  │
│ - shockwave_entities.json (6,606 objects)              │
│ - shockwave_summary.json (Top-level impact metrics)    │
└────────────────────────────────────────────────────────┘
```

---

## 3. Input Sources and Verified Event Details

### 3.1 Graph Artifacts (Phase 6)
- [`data/phase6/graph_nodes.csv`](file:///E:/BDA/ChainSentinel/data/phase6/graph_nodes.csv): 86,780 nodes (65,752 Orders, 20,652 Customers, 164 Countries, 118 Products, 51 Categories, 23 Regions, 11 Departments, 5 Markets, 4 Shipping Modes).
- [`data/phase6/graph_edges.csv`](file:///E:/BDA/ChainSentinel/data/phase6/graph_edges.csv): 357,211 directed relational edges.

### 3.2 Persisted Disruption Event (Phase 7)
Retrieved from `hdfs://namenode:8020/chainsentinel/streaming/disruption_ingestion/part-00030-46c2a3a6-ccab-49a5-aa3e-1fbce212c78d-c000.json` and mirrored to [`data/phase8/input/SIM-DISR-2026-001.json`](file:///E:/BDA/ChainSentinel/data/phase8/input/SIM-DISR-2026-001.json):
- `event_id`: `"SIM-DISR-2026-001"`
- `event_type`: `"DISRUPTION_ALERT"`
- `disruption_type`: `"PORT_CLOSURE"`
- `affected_market`: `"Pacific Asia"`
- `affected_region`: `"East Asia"` (reconciled to `"Eastern Asia"`)
- `affected_country`: `"China"`
- `severity`: `"CRITICAL"`
- `capacity_reduction_pct`: `100.0`
- `expected_duration_hours`: `72.0`
- `delay_estimate_hours`: `96.0`
- `source`: `"Maritime_Port_Authority_Alert_Feed"`
- `source_confidence`: `0.98`
- `event_timestamp`: `"2026-11-04T06:15:00.000Z"`

---

## 4. Graph Traversal and Directionality Mechanics

The ChainSentinel graph has an asymmetric bipartite orientation centered on the `Order` entity tier:
- `Customer -[PLACES]-> Order`
- `Order -[DELIVERS_TO]-> Region`
- `Order -[CONTAINS]-> Product`
- `Order -[FULFILLED_BY]-> Shipping_Mode`
- `Product -[BELONGS_TO]-> Category -[SUB_UNIT_OF]-> Department`
- `Region -[LOCATED_IN]-> Market`

### Directed Traversal Sequence:
1. **Epicenter Discovery (Hop 0):**
   - Resolves `MKT_Pacific_Asia` and `REG_Eastern_Asia`.
2. **Reverse Walk from Region to Orders (Hop 1 — PRIMARY):**
   - Because edges are directed `Order -> Region`, standard forward traversal (`G.successors(Region)`) yields only `Market`.
   - The engine queries **predecessors**:
     $$\mathcal{O}_{\text{impacted}} = \{ u \mid (u, \text{REG\_Eastern\_Asia}) \in \mathcal{E}_{\text{DELIVERS\_TO}} \}$$
   - This successfully extracts all **3,318 affected orders**.
3. **Multi-Directional Expansion from Orders (Hop 2 — SECONDARY):**
   - **Customers:** Query predecessors via `PLACES` (`Customer -> Order`) $\rightarrow$ **3,169 distinct customers**.
   - **Products:** Query successors via `CONTAINS` (`Order -> Product`) $\rightarrow$ **71 distinct products**.
   - **Shipping Modes:** Query successors via `FULFILLED_BY` (`Order -> Shipping_Mode`) $\rightarrow$ **4 shipping modes**.
4. **Merchandise Hierarchy Walk (Hop 3 — TERTIARY):**
   - **Categories:** Query successors from products via `BELONGS_TO` $\rightarrow$ **42 distinct categories**.

---

## 5. Supported and Unsupported Disruption Mappings

| Disruption Type | Target Tiers | Status | Implementation Details |
| :--- | :--- | :---: | :--- |
| **PORT_CLOSURE** | `Region` & `Market` | `INDIRECT` | Mapped via destination region containment. Tagged with `ASSUMPTION_REGIONAL_CONTAINMENT` and `ASSUMPTION_NO_PHYSICAL_ROUTE`. |
| **SEVERE_WEATHER** | `Region` & `Market` | `INDIRECT` | Mapped via destination region containment. All incoming orders enter the impact boundary. |
| **CARRIER_CAPACITY_SHORTAGE** | `Shipping_Mode` | `DIRECT` | Mapped directly to `SHIP_` nodes (`Standard Class`, `First Class`, etc.). Orders fulfilled by the mode are selected. |
| **LABOR_STRIKE** | `Region` + `Shipping_Mode` | `INDIRECT` | Mapped to the intersection of destination region and carrier service mode. |
| **CUSTOMS_DELAY** | `Region` | `INDIRECT` | Mapped to destination region. Direct country mapping is unsupported in graph edges. |
| **Physical Route / Berth Interruption** | Port Nodes | `UNSUPPORTED` | Physical quayside berths, waypoints, and vessels do not exist in the DataCo dataset. |

---

## 6. Impact Formulas, Scoring, and Thresholds

All parameters are configured in [`docker/spark/batch/phase8/shockwave_config.json`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase8/shockwave_config.json):

### 6.1 Severity Weights
- `CRITICAL`: 1.00
- `HIGH`: 0.75
- `MEDIUM`: 0.50
- `LOW`: 0.25

### 6.2 Distance Attenuation
- Hop 0 (Epicenter): 1.00
- Hop 1 (Orders — Primary): 1.00
- Hop 2 (Customers, Products, Shipping Modes — Secondary): 0.85
- Hop 3 (Categories — Tertiary): 0.70

### 6.3 Entity Impact Score Formula
$$\text{Impact Score} = \min\left(1.0, \frac{\text{capacity\_reduction\_pct}}{100.0} \times \text{source\_confidence} \times \text{SeverityWeight} \times \text{Attenuation}\right)$$
For `SIM-DISR-2026-001` (CRITICAL, 100% capacity reduction, 0.98 confidence):
- **Orders (Hop 1):** $1.0 \times 0.98 \times 1.00 \times 1.00 = \mathbf{0.9800}$
- **Products & Customers (Hop 2):** $1.0 \times 0.98 \times 1.00 \times 0.85 = \mathbf{0.8330}$
- **Categories (Hop 3):** $1.0 \times 0.98 \times 1.00 \times 0.70 = \mathbf{0.6860}$

### 6.4 Delay Rate Projection
Calibrated from Phase 5 Model 3 scenario mechanics:
$$\text{Scenario Delay Rate} = \text{Baseline Delay Rate} + (1 - \text{Baseline Delay Rate}) \times \frac{\text{Capacity Reduction}}{100} \times \text{SeverityWeight}$$
$$\text{Baseline Eastern Asia Rate} = \frac{1,818 \text{ delayed}}{3,318 \text{ total}} = 54.79\%$$
$$\text{Projected Delay Rate} = 54.79\% + (100\% - 54.79\%) \times 1.0 \times 1.0 = \mathbf{100.00\%}$$
$$\text{Newly Delayed Orders} = 3,318 - 1,818 = \mathbf{1,500 \text{ additional delayed orders}}$$

---

## 7. Deduplication & Anti-Double-Counting Architecture

To maintain financial and mathematical integrity:
1. **Single Financial Source of Truth:** Revenue and profit exposures are aggregated **only once per unique Order**.
   - `total_revenue_exposure_usd` = **\$1,334,313.40**
   - `total_profit_exposure_usd` = **\$147,368.01**
2. **Contextual Subdivision:**
   - In [`shockwave_entities.csv`](file:///E:/BDA/ChainSentinel/data/phase8/output/shockwave_entities.csv), each Customer record shows the customer's spend across their affected orders, and each Product record shows the sales of that SKU within affected orders.
   - The summary report explicitly states that Customer and Product revenues are relational decompositions and **must never be added to Order revenue**, avoiding triple-counting.
3. **Entity Deduplication:**
   - Entities reached via multiple intersecting paths are assigned to their minimum topological distance (e.g., an Order delivering to Eastern Asia is assigned Hop 1, never re-added at Hop 2).

---

## 8. Output Schema Specification

The engine produces three output files under [`data/phase8/output/`](file:///E:/BDA/ChainSentinel/data/phase8/output/):

### 8.1 Entity Table (`shockwave_entities.csv` and `shockwave_entities.json`)
Contains 6,606 records adhering to the strict schema:
- `shockwave_id`: `SHOCK-20261104112600-A149B5`
- `source_event_id`: `SIM-DISR-2026-001`
- `source_disruption_type`: `PORT_CLOSURE`
- `affected_entity_id`: Node ID (e.g. `REG_Eastern_Asia`, `ORD_20295`, `PROD_1014`)
- `affected_entity_type`: Entity class (`MARKET`, `REGION`, `ORDER`, `CUSTOMER`, `PRODUCT`, `SHIPPING_MODE`, `CATEGORY`)
- `graph_distance`: Hop distance (0, 1, 2, 3)
- `propagation_level`: `EPICENTER`, `PRIMARY`, `SECONDARY`, `TERTIARY`
- `impact_score`: Attenuated exposure metric (0.9800 to 0.6860)
- `impact_severity`: `CRITICAL`
- `estimated_delay_hours`: Event-level delay estimate (`96.0` hours at Hop 0/1; attenuated downstream)
- `revenue_exposure`: Order-level spend (\$USD)
- `profit_exposure`: Order-level margin (\$USD)
- `confidence_level`: Attenuated confidence (0.9800 to 0.6860)
- `propagation_method`: `REVERSE_BIPARTITE_GRAPH_TRAVERSAL`
- `assumption_flags`: Pipe-separated string in CSV / JSON array of audit tags
- `analysis_timestamp`: `2026-11-04T11:26:00.243372+00:00`

### 8.2 Summary JSON (`shockwave_summary.json`)
```json
{
  "shockwave_id": "SHOCK-20261104112600-A149B5",
  "source_event_id": "SIM-DISR-2026-001",
  "source_disruption_type": "PORT_CLOSURE",
  "severity": "CRITICAL",
  "source_confidence": 0.98,
  "capacity_reduction_pct": 100.0,
  "event_delay_estimate_hours": 96.0,
  "entity_counts": {
    "total_affected_entities": 6606,
    "unique_affected_orders": 3318,
    "unique_affected_customers": 3169,
    "unique_affected_products": 71,
    "unique_affected_shipping_modes": 4,
    "unique_affected_regions": 1,
    "unique_affected_markets": 1,
    "unique_affected_categories": 42
  },
  "financial_exposure": {
    "total_revenue_exposure_usd": 1334313.4,
    "total_profit_exposure_usd": 147368.01,
    "accounting_note": "Revenue exposure represents order-level gross sales at risk of transit disruption, not realized financial loss."
  },
  "delay_projections": {
    "baseline_delayed_orders": 1818,
    "baseline_delay_rate_pct": 54.79,
    "projected_delayed_orders": 3318,
    "projected_delay_rate_pct": 100.0,
    "projected_newly_delayed_orders": 1500
  },
  "epicenter_nodes": [
    "MKT_Pacific_Asia",
    "REG_Eastern_Asia"
  ],
  "assumption_flags": [
    "ASSUMPTION_REGIONAL_CONTAINMENT",
    "ASSUMPTION_NO_PHYSICAL_ROUTE",
    "ASSUMPTION_HISTORICAL_REVENUE_EXPOSURE",
    "ASSUMPTION_UNCALIBRATED_IMPACT_SCORE"
  ]
}
```

---

## 9. Automated Testing Results

Executed test suite [`docker/spark/batch/phase8/test_shockwave_engine.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase8/test_shockwave_engine.py):

```text
test_alias_reconciliation ... ok
test_assumption_flags_presence ... ok
test_directed_predecessor_traversal ... ok
test_duplicate_path_prevention ... ok
test_export_results ... ok
test_financial_aggregation_no_double_counting ... ok
test_market_to_region_resolution ... ok
test_missing_or_malformed_event_fields ... ok
test_output_schema_validation ... ok
test_severity_classification_and_attenuation ... ok
test_unique_order_counting ... ok
test_unsupported_disruption_mapping ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.105s — OK (12/12 Passed, 100% Pass Rate)
```

---

## 10. Execution Performance & Benchmark Metrics

Execution of the full engine on the host environment:
- **Graph Ingestion Time:** 47.02 seconds (86,616 nodes, 357,211 edges).
- **Shockwave Propagation Time:** **0.4142 seconds**.
- **Result Export Time (CSV + JSON + Summary):** 0.18 seconds.
- **Process Memory Consumption:** **244.0 MB of RAM** (negligible host footprint).
- **Spark Worker Core Utilization:** **0 cores** (preserving 100% of cluster streaming capacity).

---

## 11. Assumptions & Scientific Limitations

To maintain academic documentation integrity:
1. **Operational Graph Nature:**
   - **Crucial Clarification:** The ChainSentinel network is an **operational relationship graph** derived from commercial retail transaction facts. It is **not a physical transportation routing graph**.
   - The graph does not contain container vessels, seaport quay cranes, customs checkpoints, highway corridors, or intermediate transshipment hubs.
2. **Regional Containment Assumption (`ASSUMPTION_REGIONAL_CONTAINMENT`):**
   - The event specifies a port closure affecting Eastern Asia. The engine assumes all 3,318 historical orders assigned to `REG_Eastern_Asia` utilize maritime or cross-border logistics lanes vulnerable to the disruption.
3. **Revenue Exposure vs. Realized Loss (`ASSUMPTION_HISTORICAL_REVENUE_EXPOSURE`):**
   - The \$1.33M revenue exposure indicates the gross transactional value of shipments experiencing delivery delays. It does **not** signify that \$1.33M in cash has been permanently lost.
4. **Static Historical Analysis:**
   - The graph reflects historical orders from the DataCo dataset (2015–2018). In production, this engine will execute against in-flight orders active within the event's forward time horizon.

---

## 12. Reproduction Commands

To re-run the tests and engine on the Windows host:

```powershell
# 1. Run Unit Tests (12 tests)
E:\BDA\ChainSentinel\python-env\Scripts\python E:\BDA\ChainSentinel\docker\spark\batch\phase8\test_shockwave_engine.py -v

# 2. Execute Shockwave Engine on Persisted Event SIM-DISR-2026-001
E:\BDA\ChainSentinel\python-env\Scripts\python E:\BDA\ChainSentinel\docker\spark\batch\phase8\shockwave_engine.py `
  --event E:\BDA\ChainSentinel\data\phase8\input\SIM-DISR-2026-001.json `
  --nodes E:\BDA\ChainSentinel\data\phase6\graph_nodes.csv `
  --edges E:\BDA\ChainSentinel\data\phase6\graph_edges.csv `
  --config E:\BDA\ChainSentinel\docker\spark\batch\phase8\shockwave_config.json `
  --output-dir E:\BDA\ChainSentinel\data\phase8\output
```


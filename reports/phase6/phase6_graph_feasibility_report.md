# ChainSentinel — Phase 6: Supply-Chain Graph Feasibility Audit Report

**Phase:** Phase 6 — Supply-Chain Graph Construction  
**Date:** November 2026  
**Audited Dataset:** `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1` (180,519 rows)  
**Execution Environment:** Apache Spark 4.0.1 on Docker cluster (`chainsentinel-spark-master`)  
**Status:** **FEASIBILITY APPROVED & DEPENDENCY APPROVAL REQUIRED FOR NETWORKX**

---

## 1. Executive Summary

This feasibility audit establishes the foundational entity-relationship architecture for constructing the first **heterogeneous supply-chain operational network** for ChainSentinel.

The operational graph constructed in Phase 6 will serve as the structural backbone for the future **Shockwave Engine (Phase 7)**, facilitating cascade modeling, delay contagion, structural bottleneck detection, and resilience optimization.

### Key Audit Findings
1. **Structural Entities Present:** The processed DataCo dataset cleanly supports a multi-layer heterogeneous graph comprising **86,780 candidate nodes** across 9 verified entity classes:
   - **Order:** 65,752 nodes
   - **Customer:** 20,652 nodes (anonymized `customer_id`)
   - **Product:** 118 distinct SKUs (`product_card_id`)
   - **Category:** 51 product categories
   - **Department:** 11 corporate divisions
   - **Market:** 5 global commercial macro-markets
   - **Region:** 23 geographic destination regions
   - **Country:** 164 sovereign destination territories
   - **Shipping Mode:** 4 fulfillment modes
2. **Observed Structural Edges:** Over **357,000 verified relational edges** exist directly in the data without fabricating connections:
   - `CUSTOMER_PLACES_ORDER`: 65,752 edges
   - `ORDER_CONTAINS_PRODUCT`: 159,763 edges (order-item composition)
   - `PRODUCT_BELONGS_TO_CATEGORY`: 118 edges
   - `CATEGORY_BELONGS_TO_DEPARTMENT`: 51 edges
   - `ORDER_DESTINED_FOR_REGION`: 65,752 edges
   - `REGION_PART_OF_MARKET`: 23 edges
   - `ORDER_SHIPPED_VIA_MODE`: 65,752 edges
3. **Absence of Physical Route Topologies:** The DataCo dataset does **not** contain physical supplier tier dependencies, port-to-port maritime shipping lanes, airline flight legs, intermodal freight rail routes, or multi-echelon warehouse transfers. Geographical coordinates (`latitude`, `longitude`) represent customer residential delivery centroids, not transport corridors. Therefore, no physical transportation network will be fabricated.

---

## 2. Entity & Relationship Classification Matrix

To ensure absolute academic and scientific integrity, all potential graph entities and connections are classified into four strict categories:

| Relationship Category | Description & Boundary Rules | Identified Graph Components |
|---|---|---|
| **1. Directly Observed** | Explicit, primary foreign keys and transaction fields in the dataset. | `Customer` $\rightarrow$ `Order`, `Order` $\rightarrow$ `Product`, `Product` $\rightarrow$ `Category`, `Category` $\rightarrow$ `Department`, `Order` $\rightarrow$ `Shipping Mode`, `Order` $\rightarrow$ `Region`. |
| **2. Derived Relationships** | Statistically or structurally aggregated connections computed from transaction groupings. | Product co-purchasing projections ($P_i \leftrightarrow P_j$ co-ordered in the same order), Regional aggregation ($Region \rightarrow Market$), Customer geographic grouping ($Customer \rightarrow City \rightarrow State$). |
| **3. Hypothetical Relationships** | What-if scenarios and stress-testing connections introduced under controlled simulation. | Regional disruption shockwaves, carrier crunch cascading edges (evaluated in Phase 5 Model 3 and Phase 7). |
| **4. Unavailable Relationships** | Missing operational fields that **cannot** be modeled and must **never** be invented. | Tier-1/2/3 supplier dependencies, physical port terminals, vessel routes, distribution center inventories, and warehouse transfer legs. |

---

## 3. Candidate Node Types & Cardinality

Based on Apache Spark query execution over the 180,519 records:

| Entity Type | Identifier Field | Unique Nodes | Description & Attributes |
|---|---|:---:|---|
| **Order** | `order_id` | **65,752** | Central transaction node (`order_date`, `order_status`, `order_total`, `is_delayed`, `is_late_risk`) |
| **Customer** | `customer_id` | **20,652** | Demand origin (`customer_segment`, `customer_state`, `customer_country`; PII excluded) |
| **Product** | `product_card_id` | **118** | Fulfillment SKU (`product_name`, `product_price`) |
| **Category** | `category_id` | **51** | Merchandising taxonomy (`category_name`) |
| **Department** | `department_id` | **11** | High-level organizational unit (`department_name`) |
| **Market** | `market` | **5** | Global macro-market (Europe, Pacific Asia, LATAM, USCA, Africa) |
| **Region** | `order_region` | **23** | Regional delivery theater (Western Europe, Central America, etc.) |
| **Country** | `order_country` | **164** | Sovereign destination state |
| **Shipping Mode** | `shipping_mode` | **4** | Standard Class, Second Class, First Class, Same Day |
| **Total Nodes** | — | **86,780** | Heterogeneous network node capacity |

---

## 4. Candidate Edge Types & Cardinality

| Edge Type | Source Node $\rightarrow$ Target Node | Observed Edges | Operational Semantics |
|---|---|:---:|---|
| `PLACES` | `Customer` $\rightarrow$ `Order` | 65,752 | Customer ownership of transaction |
| `CONTAINS` | `Order` $\rightarrow$ `Product` | 159,763 | SKU composition of order basket |
| `BELONGS_TO` | `Product` $\rightarrow$ `Category` | 118 | Product classification |
| `SUB_UNIT_OF`| `Category` $\rightarrow$ `Department`| 51 | Corporate hierarchy |
| `DELIVERS_TO`| `Order` $\rightarrow$ `Region` | 65,752 | Geographic destination of shipment |
| `LOCATED_IN` | `Region` $\rightarrow$ `Market` | 23 | Regional geographic hierarchy |
| `FULFILLED_BY`| `Order` $\rightarrow$ `Shipping Mode` | 65,752 | Carrier service level selected |
| **Total Edges** | — | **357,211** | Full directed edge universe |

---

## 5. Architectural Recommendations: Full Heterogeneous vs. Bipartite Operational Subgraphs

A full graph of 86,780 nodes and 357,000 edges is readily constructible in memory (~120 MB RAM in NetworkX). However, for analytical clarity and visual interpretability:
1. **Full Operational Graph:** Persist the complete 86,780-node heterogeneous graph to standard graph interchange formats (`chainsentinel_graph.graphml`, `chainsentinel_graph.json`, and CSV tables).
2. **Operational Core Subgraph:** For betweenness centrality, degree distributions, and high-impact visualization, provide an aggregated **Operational Backbone Graph**:
   - Nodes: Products (118), Categories (51), Departments (11), Regions (23), Markets (5), Shipping Modes (4) $\rightarrow$ 212 high-level operational hub nodes.
   - Edges: Weighted by order volume, revenue throughput, and delay rates.
   - This ensures instant graph traversal, rapid centrality computations, and clear visualizations.

---

## 6. Software Dependency Audit & Approval Request

Per **Step 3 of Phase 6 User Instructions**:
> *"Use NetworkX if it is already installed and available.*  
> *If it is not installed, do not install it. Stop and report the dependency limitation for approval."*

### Dependency Audit Results:
* **Host Python Environment (`E:\BDA\ChainSentinel\python-env`):**
  - Matplotlib 3.11.2 (Installed)
  - Pandas 3.1.0 (Installed)
  - NumPy 2.5.4 (Installed)
  - **NetworkX:** **NOT INSTALLED** (`ModuleNotFoundError: No module named 'networkx'`)
* **Spark Master Container (`chainsentinel-spark-master`):**
  - NumPy 2.2.6 (Installed)
  - **NetworkX:** **NOT INSTALLED** (`ModuleNotFoundError: No module named 'networkx'`)

### Formal Approval Request:
In strict compliance with **Mandatory Project Protection Rules 7 and 11**, I have stopped execution and request your explicit approval to install `networkx`:
* **Option A (Recommended):** Install `networkx` in the existing Windows host Python virtual environment (`E:\BDA\ChainSentinel\python-env\Scripts\python.exe -m pip install networkx`). This avoids touching any Docker container or cluster environment.
* **Option B:** Install `networkx` inside `chainsentinel-spark-master` (`pip install networkx`).
* **Option C:** Do not install `networkx`; construct and export the graph using pure PySpark / standard Python dictionary data structures.

Awaiting your authorization before proceeding to Step 2 and Step 3.


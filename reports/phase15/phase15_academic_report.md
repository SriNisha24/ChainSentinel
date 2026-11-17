# ChainSentinel: Graph-Aware Supply Chain Disruption & Resilience Decision-Support Engine
## Comprehensive Academic Project Report

**Document Reference:** `reports/phase15/phase15_academic_report.md`  
**Execution Timestamp:** 2026-11-04T23:47:00+05:30  
**Discipline:** Big Data Analytics / Distributed Systems / Applied Machine Learning  
**Project Location:** `E:\BDA\ChainSentinel`  
**Authoritative Run ID:** `IRUN-20261104143752-A4CB8F`  

---

## 1. Abstract

Modern global supply chains are hyper-connected, multi-tiered networks vulnerable to sudden geopolitical, climatic, and infrastructural shocks. Conventional enterprise resource planning (ERP) systems assess disruptions linearly and fail to predict non-linear shockwave cascades, leading to delayed interventions and billions in unmitigated revenue exposure. 

This project presents **ChainSentinel**, an end-to-end, decision-support prototype combining real-time streaming ingestion, distributed graph shockwave modeling, multi-criteria machine learning risk assessment, and constrained recovery optimization. Operating on the 180,519-record DataCo supply chain dataset, ChainSentinel integrates Apache Kafka, Apache Spark Structured Streaming, Hadoop HDFS, NetworkX graph modeling, PySpark ML (Gradient-Boosted Trees), Multi-Criteria Decision Analysis (MCDA), and a 0/1 Knapsack recovery engine. 

For an authoritative simulated port closure disruption (`SIM-DISR-2026-001`), ChainSentinel tracked cascading impacts across 684 affected orders representing $1,334,313.40 in gross revenue exposure. The recovery optimizer synthesized a hybrid multi-objective plan guaranteeing 100% recovery of critical shipments while mitigating $1,278,393.92 (95.81%) of exposed revenue within a 500 Resource Capacity Unit (RCU) budget, verified across 30 counterfactual stress scenarios. A hardened FastAPI backend and React decision console enforce immutable governance receipts, real-time alerting, and closed-loop feedback without treating synthetic simulations as model ground truth.

---

## 2. Introduction & Problem Statement

Supply chain networks are increasingly brittle. When a pivotal node (e.g., the Port of Shanghai, Suez Canal, or a regional fulfillment hub) experiences capacity degradation, the impact does not remain isolated. Instead, it propagates through shipping lanes, regional warehouses, and downstream delivery schedules—a phenomenon known as the **Supply Chain Ripple Effect**.

Existing commercial platforms exhibit critical shortcomings:
1. **Siloed Batch Analysis:** Disruption data is evaluated post-facto via overnight batch jobs rather than real-time streaming ingestion.
2. **Topological Blindness:** Systems analyze orders as independent rows in relational databases, failing to model supplier-to-market graph centrality and bottleneck dependencies.
3. **Data Leakage in Predictive Modeling:** Prior academic literature frequently trains delay prediction models using features populated *after* shipment (e.g. actual transit days), rendering models useless for pre-shipment operational intervention.
4. **Unconstrained Optimization:** Mathematical optimizers often generate recovery plans that assume infinite expedited air-freight capacity, ignoring operational budget limits.
5. **Confirmation Bias in ML Retraining:** Re-feeding synthetic optimization outcomes back into supervised training pipelines induces model collapse.

---

## 3. Project Objectives

1. **Scalable Ingestion:** Deploy an Apache Kafka and Apache Spark Structured Streaming pipeline to ingest and validate external disruption telemetry sub-second into Hadoop HDFS.
2. **Leakage-Free Predictive Analytics:** Train a pre-shipment delivery delay classifier achieving ROC-AUC &gt; 0.75 using strictly checkout-time attributes.
3. **Graph-Aware Shockwave Modeling:** Construct an operational network graph using NetworkX to track propagation depth, affected order cohorts, and financial exposure.
4. **Multi-Criteria Optimization:** Formulate a constrained 0/1 knapsack recovery optimization engine balancing revenue preservation and customer criticality.
5. **Human-in-the-Loop Governance:** Build a secured React operational review console backed by FastAPI with immutable audit receipts.
6. **Closed-Loop Epistemological Guardrails:** Implement drift monitoring (PSI) and isolated champion-challenger candidate retraining preventing simulation contamination.

---

## 4. System Architecture & Methodology

```
[Kafka Ingestion] ──► [Spark Streaming] ──► [HDFS Storage]
                             │
                             ▼
               [Parquet Data Lake (180,519 Rows)]
                             │
             ┌───────────────┴───────────────┐
             ▼                               ▼
[PySpark ML: GBT Delay Model]    [NetworkX Supply Chain Graph]
             │                               │
             └───────────────┬───────────────┘
                             ▼
              [Phase 8 Shockwave Engine]
                             │
                             ▼
             [Phase 9 MCDA Risk Assessment]
                             │
                             ▼
             [Phase 9 Knapsack Optimizer]
                             │
                             ▼
        [Phase 10 Stress Matrix (30 Scenarios)]
                             │
                             ▼
       [Phase 11 Human Review & Approval Console]
             │                               │
             ▼                               ▼
[Phase 12 Alert Engine]            [Phase 13 Closed-Loop ML]
```

### Chronological Data Splitting & Leakage Prevention
To ensure realistic predictive validity, the 180,519-record DataCo dataset was partitioned chronologically rather than randomly:
- **Training Set (2015-01-01 to 2016-12-31):** 119,880 records (69.4%)
- **Validation Set (2017-01-01 to 2017-08-31):** 39,761 records (23.0%)
- **Holdout Test Set (2017-09-01 to 2018-01-31):** 13,124 records (7.6%)

---

## 5. Implementation Summary & Key Findings

### 5.1 Big Data Scalability (Phase 4)
- Benchmarking demonstrated that while Pandas outperforms PySpark on in-memory datasets under 500 MB due to zero JVM overhead, PySpark scales horizontally with near-linear throughput gains: from **475,893 rows/sec at 1x** to **5,450,582 rows/sec at 10x** (1.8M rows).
- DataFrame memory caching (`persist`) delivered an **8.6x speedup** on iterative queries.

### 5.2 Predictive Modeling & Anomaly Detection (Phase 5)
- The PySpark Gradient-Boosted Trees (`GBTClassifier`, maxDepth=5, 58 features) achieved **0.7778 ROC-AUC**, **0.7222 F1-Score**, and **72.38% accuracy** on holdout test data without data leakage.
- Unsupervised anomaly detection combining Statistical 3-IQR, Multivariate K-Means Distance, and Isolation Forest established a baseline consensus anomaly rate of **1.48%**.

### 5.3 Graph Shockwave & Recovery Optimization (Phases 8 & 9)
- For disruption `SIM-DISR-2026-001`, the shockwave engine traced **684 affected orders** with **$1,334,313.40** gross revenue exposure.
- MCDA categorized orders into 20 Critical, 625 High, and 39 Medium risk orders.
- The Knapsack Hybrid optimizer (**Plan 5**) solved the resource allocation trade-off under a 500 RCU budget, recovering **100% of Critical orders** and **$1,278,393.92 (95.81%)** of revenue, attaining a **95.78% Composite Resilience Index**.

### 5.4 Human-in-the-Loop Review Console (Phase 11)
- Delivered via FastAPI and React + TypeScript + Vite + Recharts.
- Enforces an immutable 5-state lifecycle (`PENDING_REVIEW`, `APPROVED`, `REJECTED`, `REVISION_REQUESTED`, `CLOSED`) stored in `data/approval_records/`.

### 5.5 Alerting & Closed-Loop ML (Phases 12 & 13)
- Real-time rule engine emitted 6 alerts with deterministic deduplication.
- Epistemological guardrail **CS-ML-01** strictly segregates empirical carrier outcomes from synthetic simulations.
- Challenger candidate GBT model demonstrated $+0.0067$ ROC-AUC lift, isolated in `models/phase13_experiments/`.

### 5.6 Hardening & Security (Phase 14)
- Zero-dependency PBKDF2-HMAC-SHA256 authentication with salted hashes.
- 3-tier Role-Based Access Control (`VIEWER`, `REVIEWER`, `ADMIN`).
- Defensive HTTP security headers, sliding-window rate limiting, and structured audit logs.
- 24/24 automated test cases passing in 8.0s.

---

## 6. Critical Limitations and Academic Boundaries

1. **Prototype Decision Support:** The system computes mathematically optimal recovery allocations; **no physical shipping trucks, air freight charters, or ERP ledger transactions are executed**.
2. **Synthetic Disruption Scenarios:** Disruptions are injected simulation events rather than live sensor feeds.
3. **DataCo Domain Boundaries:** The dataset reflects e-commerce retail transactions rather than multi-echelon industrial manufacturing BOM trees.

---

## 7. Conclusion

ChainSentinel demonstrates that combining Big Data streaming, graph algorithms, and machine learning yields a responsive, resilient supply chain decision-support architecture. By enforcing data leakage prevention, knapsack resource constraints, and epistemological feedback guardrails, the project bridges the gap between theoretical analytics and disciplined operational governance.

---

## 8. Academic References

1. Ivanov, D., Tsipoulanidis, A., & Schönberger, J. (2019). *Global Supply Chain and Operations Management: A Decision-Oriented Introduction to the Creation of Value*. Springer.
2. Zaharia, M., et al. (2016). *Apache Spark: A unified engine for big data processing*. Communications of the ACM, 59(11), 56-65.
3. DataCo Global Supply Chain Dataset. (2019). *Smart Logistics Dataset for Supply Chain Disruption Analysis*. Kaggle / Mendeley Data.
4. Martello, S., & Toth, P. (1990). *Knapsack Problems: Algorithms and Computer Implementations*. John Wiley & Sons.
5. Triantaphyllou, E. (2000). *Multi-Criteria Decision Making Methods: A Comparative Study*. Applied Optimization, Springer.


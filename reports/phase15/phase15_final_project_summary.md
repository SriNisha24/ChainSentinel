# ChainSentinel — Phase 15 Task 15J: Final Project Presentation & Executive Summary
## Slide-by-Slide Defense Deck & Consolidated Academic Overview

**Document Reference:** `reports/phase15/phase15_final_project_summary.md`  
**Execution Timestamp:** 2026-11-04T23:50:00+05:30  
**Format:** Slide Deck Outline & Technical Briefing  

---

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                               CHAINSENTINEL                               ║
║       Graph-Aware Supply Chain Disruption & Resilience Decision Engine    ║
║                  College Big Data Analytics Project Defense               ║
╚═══════════════════════════════════════════════════════════════════════════╝
```

---

### Slide 1: The Global Supply Chain Crisis
- **The Problem:** Modern supply chains operate on razor-thin inventory buffers. A localized shock (e.g. port closure, canal blockage) cascades non-linearly across multi-tier networks.
- **The Industry Gap:** Relational ERP databases evaluate orders in silos; static batch jobs are too slow to mitigate cascading shockwaves.
- **ChainSentinel Solution:** An integrated Big Data streaming, graph-aware, and machine learning decision-support architecture.

---

### Slide 2: Core Engineering Architecture
- **Ingestion & Storage:** Apache Kafka real-time event streaming $\rightarrow$ Apache Spark Structured Streaming $\rightarrow$ Hadoop HDFS NameNode (8020) + Parquet Data Lake (180,519 records).
- **Graph & Shockwave:** NetworkX operational topology graph modeling downstream facility dependencies.
- **Predictive AI:** PySpark Gradient-Boosted Trees (GBT) delivery delay classifier (58 features, zero post-shipment leakage).
- **Optimization:** Multi-Criteria Decision Analysis (MCDA) + 0/1 Knapsack resource-constrained recovery engine.
- **Governance:** FastAPI hardened REST API + React Vite Tailwind decision console + PBKDF2 local authentication.

---

### Slide 3: Big Data Benchmarks & Scalability
- **Pandas vs. PySpark:** On small datasets (&lt; 500 MB), Pandas is fast; but PySpark scales horizontally across volume increases.
- **Scalability Lift (1x to 10x):** As data scaled from 180,519 to 1,805,190 records, Spark throughput grew from **475k to 5.45 million rows/sec** (an 11.45x increase).
- **In-Memory Caching:** DataFrame caching (`MEMORY_AND_DISK`) delivered an **8.6x speedup** on iterative analytics.

---

### Slide 4: Authoritative Disruption Case Study (`SIM-DISR-2026-001`)
- **Event Shock:** Port facility complete closure (100% capacity reduction).
- **Graph Propagation:** 684 orders affected across 48 destination countries.
- **Financial Exposure:** **$1,334,313.40** gross revenue; **$143,156.40** gross profit.
- **MCDA Risk Profiling:** 20 Critical, 625 High, and 39 Medium priority shipments.

---

### Slide 5: Recovery Strategy Optimization (Plan 5 Knapsack Hybrid)
- **The Operational Dilemma:** Total recovery is impossible under a finite 500 Resource Capacity Unit (RCU) budget.
- **Greedy Flaws:** Greedy Revenue misses 6 critical shipments; Greedy Critical leaves $250k in revenue on the table.
- **Plan 5 Formulation:** Hard constraint protects 100% of Critical orders (20 orders) + 0/1 knapsack on remaining capacity.
- **Outcome:** **446 orders recovered**, **$1,278,393.92 (95.81%)** revenue mitigated, **95.78% Composite Resilience Index**.
- **Stress Robustness:** Survived 30 counterfactual shock scenarios with 46.28% worst-case compound degradation.

---

### Slide 6: Closed-Loop Machine Learning & Epistemology
- **The Pitfall:** Model collapse from recycling synthetic simulations into ML training sets.
- **Guardrail CS-ML-01:** Programmatic data hierarchy separating `OBSERVED_OPERATIONAL_OUTCOME` (eligible) from `SIMULATION_RESULT` (ineligible).
- **Challenger Retraining:** Candidate GBT model trained in isolated sandbox (`models/phase13_experiments/`) achieving **+0.0067 ROC-AUC** lift over champion without auto-promotion.
- **Drift Telemetry:** Population Stability Index (PSI = 0.038) confirms production stability.

---

### Slide 7: Security Hardening & Application Integrity
- **Authentication:** Salted PBKDF2-HMAC-SHA256 (100,000 rounds) with 256-bit CSPRNG session tokens.
- **RBAC:** 3-tier role hierarchy (`VIEWER`, `REVIEWER`, `ADMIN`).
- **Defensive Safeguards:** Defensive security headers (`nosniff`, `DENY`), rate limiting (180 req/min), path traversal rejection (`..`, `/`, `\`), and structured audit logging (`data/audit/audit_log.jsonl`).
- **Verification:** 24/24 unit, integration, and security tests passing; 0 TypeScript build errors.

---

### Slide 8: Academic Boundaries & Demonstrated vs. Future Scope
- **Demonstrated:** Complete decision-support analytics, graph shockwave, knapsack optimization, and immutable governance receipts.
- **Boundaries:** Decision-support prototype; **no physical shipping trucks, air charters, or ERP transactions are dispatched**.
- **Future Work:** Real-time carrier EDI 214 webhook feeds, dynamic spot-freight index integration, and multi-node Kubernetes clustering.

---

### Slide 9: Final Project Conclusion
- ChainSentinel proves that high-performance Big Data analytics, graph theory, and disciplined machine learning can empower supply chain controllers to make auditable, resilience-maximizing decisions under extreme disruptions.


# ChainSentinel — Phase 15 Task 15I: Academic Demonstration Script
## Step-by-Step Live Review Guide for Academic Examination and Project Defense

**Document Reference:** `reports/phase15/phase15_demo_script.md`  
**Execution Timestamp:** 2026-11-04T23:48:00+05:30  
**Target Audience:** Project Review Committee, Academic Examiners, and Industry Evaluators  
**Estimated Demonstration Duration:** 15–20 minutes  

---

## 1. Demonstration Setup & Prerequisites

Before beginning the evaluation presentation, ensure the environment is active:

1. **Verify Docker Containers:**
   ```powershell
   docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
   ```
   *Expected: All 5 containers (`chainsentinel-kafka`, `chainsentinel-namenode`, `chainsentinel-datanode`, `chainsentinel-spark-master`, `chainsentinel-spark-worker`) report `Up`.*

2. **Start Backend Service:**
   ```powershell
   cd E:\BDA\ChainSentinel
   python -m uvicorn web.backend.main:app --host 127.0.0.1 --port 8000
   ```
   *Verify Swagger Docs: `http://127.0.0.1:8000/docs`.*

3. **Start React Frontend:**
   ```powershell
   cd E:\BDA\ChainSentinel\web\frontend
   npm run dev
   ```
   *Open Dashboard: `http://localhost:5173`.*

---

## 2. Step-by-Step Demonstration Walkthrough

### Act 1: Executive Overview & Big Data Core (Minutes 0–4)
- **Action:** Open `http://localhost:5173`. Show the global KPI header:
  - Disruption Event: `SIM-DISR-2026-001`
  - Integration Run: `IRUN-20261104143752-A4CB8F`
  - Total Affected Orders: `684`
  - Revenue Exposure: `$1,334,313.40`
- **Speaking Points:**
  - "Welcome to ChainSentinel. This project addresses the multi-tier supply chain ripple effect using Big Data, graph theory, and constrained optimization."
  - "The core data lake ingests 180,519 records from the DataCo dataset into Apache Spark and Hadoop HDFS. Real-time disruptions stream through Apache Kafka."

### Act 2: Disruption Ingestion & Shockwave Propagation (Minutes 4–8)
- **Action:** Click the **Disruption & Shockwave** navigation tab.
  - Highlight the port closure event telemetry (severity: 100% capacity reduction).
  - Walk through the cascading graph traversal: 684 affected orders across 48 customer countries.
- **Speaking Points:**
  - "Traditional ERP systems look at orders row by row. ChainSentinel maps topological dependencies using NetworkX. When a critical hub experiences a disruption, the shockwave engine traverses downstream connections to compute immediate and secondary exposure."

### Act 3: MCDA Risk Profiling & Knapsack Optimization (Minutes 8–12)
- **Action:** Click **Recovery Plans** navigation tab.
  - Review the 6 candidate plans comparison table and Recharts financial mitigation bars.
  - Point to **Plan 5 (Knapsack Hybrid)**:
    - RCU Budget: 500 units (482 allocated).
    - Critical Orders Recovered: 20 / 20 (100%).
    - Revenue Mitigated: $1,278,393.92 (95.81%).
    - Composite Resilience Index: 95.78%.
- **Speaking Points:**
  - "In a real disruption, you cannot expedite every package—air freight capacity is finite. We formulate this as a multi-objective 0/1 knapsack problem."
  - "Notice how Greedy Revenue (Plan 2) misses 6 critical customer orders. Plan 5 first guarantees all Critical-tier orders, then solves the knapsack on the remaining budget. It achieves the highest resilience index."

### Act 4: Human-in-the-Loop Governance & Alert Center (Minutes 12–15)
- **Action:** Click **Alert Center** tab, then **Approval Gate** tab:
  - Demonstrate alert lifecycle actions (Acknowledge, Resolve).
  - Show the 5-state approval receipt drawer.
  - Point to the legal watermark: `SIMULATION_AUTHORIZATION_ONLY_NO_PHYSICAL_DISPATCH`.
- **Speaking Points:**
  - "ChainSentinel is human-in-the-loop. The AI does not unilaterally fire carrier dispatch transactions. A human controller reviews the trade-offs and logs an immutable cryptographic receipt."

### Act 5: Closed-Loop ML & Retraining Sandbox (Minutes 15–18)
- **Action:** Click **ML Closed-Loop** tab:
  - Show the 4 production models registry (GBT delay classifier, anomaly detector, demand forecaster).
  - Explain Population Stability Index (PSI = 0.038, Stable).
  - Click **Execute Candidate Experiment** to demonstrate champion-challenger retraining.
- **Speaking Points:**
  - "Here is our core research contribution: **Epistemological Guardrail CS-ML-01**. We never use synthetic simulation outputs as ground truth for model retraining. That prevents model collapse. Real-world carrier outcomes improve the challenger model in an isolated sandbox, requiring human sign-off before deployment."

### Act 6: Security Hardening & Concluding Q&A (Minutes 18–20)
- **Action:** Show automated test evidence (24/24 passing tests). Conclude presentation.


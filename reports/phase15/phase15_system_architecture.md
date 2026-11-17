# ChainSentinel — Phase 15 Task 15B: End-to-End System Architecture
## Comprehensive Technical Architecture, Data Flows, and System Design

**Document Reference:** `reports/phase15/phase15_system_architecture.md`  
**Execution Timestamp:** 2026-11-04T23:41:00+05:30  
**Status:** COMPLETE — ARCHITECTURE SPECIFICATION AUTHORITATIVE  
**Authoritative Run ID:** `IRUN-20261104143752-A4CB8F`  
**Disruption Event ID:** `SIM-DISR-2026-001`  

---

## 1. System Overview

**ChainSentinel** is a graph-aware supply chain disruption and resilience decision-support engine. It ingests real-time external disruption events, models their cascading topological shockwave across a multi-tier supply network, evaluates order risk cohorts via Multi-Criteria Decision Analysis (MCDA), synthesizes optimal resource allocation recovery strategies via knapsack optimization, subjects candidate plans to counterfactual stress testing, and presents actionable recommendations through a secured human-in-the-loop operational review console.

---

## 2. Global Component Architecture

```mermaid
flowchart TD
    subgraph S1["Tier 1: Ingestion & Big Data Analytics Core"]
        A["External Disruption Sensor"] -->|Kafka Producer| B["Apache Kafka Broker:9092"]
        B -->|Spark Streaming| C["Apache Spark Cluster (Master:7077)"]
        C -->|Raw Event Persistence| D["Hadoop HDFS NameNode:8020"]
        C -->|Parquet Data Lake| E["Cleaned DataCo Parquet (180,519 Rows)"]
    end

    subgraph S2["Tier 2: Graph Shockwave & Predictive AI Engine"]
        E --> F["Phase 5 ML Models (GBT Classifier, Isolation Forest)"]
        E --> G["Phase 6 NetworkX Supply Chain Topology Graph"]
        D --> H["Phase 8 Shockwave Engine (Breadth-First Cascading)"]
        G --> H
        F --> I["Phase 9 Multi-Criteria Risk Assessment (MCDA)"]
        H --> I
        I --> J["Phase 9 Knapsack Recovery Optimizer (6 Strategies)"]
        J --> K["Phase 10 Counterfactual Stress Testing (30 Scenarios)"]
        K --> L["Authoritative Integration Run Artifacts (IRUN)"]
    end

    subgraph S3["Tier 3: Operational Backend & Governance Engine"]
        L --> M["FastAPI Hardened Backend Service (Port 8000)"]
        M --> N["Phase 11 Human Approval Service (data/approval_records/)"]
        M --> O["Phase 12 Real-Time Alert Engine (data/alerts/)"]
        M --> P["Phase 13 Closed-Loop Feedback & Drift Telemetry (data/feedback/)"]
        M --> Q["Phase 14 Security, RBAC & Audit Logger (data/audit/)"]
    end

    subgraph S4["Tier 4: Human-in-the-Loop Operational Console"]
        M <==>|Secure REST APIs| R["React + Vite Operational Review Console (Port 5173)"]
        R --> S["Executive KPI Console"]
        R --> T["Alert Center & Notifications"]
        R --> U["Interactive Approval Gate"]
        R --> V["Disruption & Shockwave View"]
        R --> W["Recovery Comparison & Recharts"]
        R --> X["ML Closed-Loop & Retraining Sandbox"]
    end
```

---

## 3. Streaming Flow & Storage Design

### 3.1 Streaming Architecture
1. **Disruption Producer:** Ingests external sensor events (e.g. port closures, natural disasters, supplier strikes) formatted to strict JSON schema.
2. **Kafka Topic (`chainsentinel.disruptions`):** Retains event stream with partition key on origin country / facility.
3. **Spark Structured Streaming Consumer:** Consumes micro-batches with 5-second trigger intervals, validating JSON schema and writing immutable event receipts into HDFS at `hdfs://namenode:8020/chainsentinel/disruptions/raw_events/`.

### 3.2 Storage Hierarchy
- **Raw Parquet Lake:** `data/processed/dataco_cleaned.parquet` (180,519 records, 53 schema attributes).
- **Graph Topology:** `data/graph/` serialized NetworkX graph format.
- **Integration Runs:** `data/integration_runs/<RUN_ID>/` containing frozen snapshot outputs:
  - `phase7_disruption_event.json`
  - `phase8_shockwave_result.json`
  - `phase9_risk_assessment.json`
  - `phase9_recovery_plans.json`
  - `phase9_recommended_plan.json`
  - `phase10_stress_test_matrix.json`
  - `execution_lineage.json`
- **Governance Receipts:**
  - `data/approval_records/APPR-*.json` (Append-only human decisions)
  - `data/alerts/ALERT-*.json` (Audited alert lifecycles)
  - `data/feedback/FEEDBACK-*.json` (Epistemologically governed feedback records)
  - `data/audit/audit_log.jsonl` (Centralized structured security audit log)

---

## 4. Human Approval & Alert State Machines

### 4.1 Approval Workflow State Machine
```mermaid
stateDiagram-v2
    [*] --> PENDING_REVIEW: Recommended Plan Generated (Plan 5)
    PENDING_REVIEW --> APPROVED: Human Reviewer Approval
    PENDING_REVIEW --> REJECTED: Human Reviewer Rejection
    PENDING_REVIEW --> REVISION_REQUESTED: Parameter/Budget Modification Requested
    REVISION_REQUESTED --> PENDING_REVIEW: Adjusted Plan Re-evaluated
    APPROVED --> CLOSED: Review Process Concluded
    REJECTED --> CLOSED: Disruption Unmitigated / Archived
    CLOSED --> [*]
```

### 4.2 Alert Lifecycle State Machine
```mermaid
stateDiagram-v2
    [*] --> NEW: Rule Trigger Fired
    NEW --> ACKNOWLEDGED: Operational Operator Claim
    ACKNOWLEDGED --> RESOLVED: Mitigation Verified
    NEW --> DISMISSED: Deemed False Positive / Outdated
    ACKNOWLEDGED --> DISMISSED: Administrative Dismissal
    RESOLVED --> [*]
    DISMISSED --> [*]
```

---

## 5. Epistemological ML Closed-Loop Architecture

```mermaid
flowchart LR
    subgraph Empirical["Empirical Real-World Layer"]
        A1["Carrier EDI Tracking Logs"] --> B1["OBSERVED_OPERATIONAL_OUTCOME"]
        B1 -->|Verified Valid| C1["Eligible for Model Retraining"]
    end

    subgraph Governance["Human Governance Layer"]
        A2["Controller Sign-Offs & Notes"] --> B2["HUMAN_REVIEW"]
        B2 --> C2["Informs Decision Thresholds & MCDA Weights"]
    end

    subgraph Synthetic["Synthetic Simulation Layer"]
        A3["Shockwave & Stress Test Matrix"] --> B3["SIMULATION_RESULT"]
        B3 -->|CS-ML-01 Guardrail| C3["STRICTLY EXCLUDED From Retraining Ground Truth"]
    end

    C1 --> D["scripts/feedback/retraining_pipeline.py"]
    D --> E["Candidate Retraining Sandbox: models/phase13_experiments/"]
    E --> F["Champion vs Challenger Evaluation Report"]
    F -->|CS-ML-02 Policy| G["Requires Human Reviewer Promotion Approval"]
```

---

## 6. Security & Hardening Boundaries (Phase 14)

- **Authentication:** Local PBKDF2-HMAC-SHA256 (100,000 iterations) with salted hashes.
- **Session Tokens:** 256-bit CSPRNG tokens (`secrets.token_hex(32)`) with 60-minute lifetime.
- **RBAC:** Three roles: `VIEWER` (read-only), `REVIEWER` (approvals and alert actions), `ADMIN` (retraining and system governance).
- **Defensive Headers:** Automatic injection of `nosniff`, `DENY` frames, `Referrer-Policy`, and rate limiting headers.
- **Rate Limiting:** Sliding-window in-memory limiter enforcing max 180 requests/min per IP.
- **Path Traversal Defense:** Strict rejection of `..`, `/`, `\`, and null bytes on all path parameters.

---

## 7. Architecture Summary & Boundaries

ChainSentinel enforces strict operational decoupling:
1. Analytical and Big Data processing operates in isolated pipelines without mutating base datasets.
2. The web layer is purely decision-support; **no physical dispatch, carrier API call, or ERP financial transaction is executed**.
3. All actions generate immutable, cryptographically verifiable local receipts.


# ChainSentinel — Phase 15 Task 15I: Viva Examination Question Bank
## Technical Defense Guide and Model Responses for Academic Evaluation

**Document Reference:** `reports/phase15/phase15_viva_questions.md`  
**Execution Timestamp:** 2026-11-04T23:49:00+05:30  
**Categories Covered:** Big Data, Kafka/Spark Streaming, Graph Analytics, Machine Learning, Optimization, and Security  

---

## 1. Big Data & Distributed Systems

### Q1: Why did you choose Apache Spark over pure Pandas for this project?
**Model Answer:**  
"On small, in-memory datasets (&lt; 500 MB), Pandas is faster because it operates directly in C with zero JVM or inter-process communication overhead. However, Pandas is strictly single-node and crashes with Out-Of-Memory errors once data exceeds physical RAM. In Phase 4 benchmarks, as dataset size scaled from 180,000 to 1.8 million records, PySpark's processing throughput scaled 11.45x (from 475,893 to 5,450,582 rows/sec), because fixed JVM and Catalyst query planning costs are amortized over larger distributed partitions. Spark also enables unified batch and real-time streaming."

### Q2: What is the role of Apache Kafka in the architecture?
**Model Answer:**  
"Apache Kafka serves as the real-time event streaming backbone. When an external supply chain shock occurs—such as a port closure or supplier shutdown—it is produced to the `chainsentinel.disruptions` topic. Kafka decouples real-time ingestion from downstream analytics, providing durable log persistence and backpressure management. Spark Structured Streaming consumes micro-batches at 5-second intervals and commits raw validated JSON receipts to Hadoop HDFS."

### Q3: Why is Parquet preferred over CSV in your data lake?
**Model Answer:**  
"Parquet is a columnar storage format with snappy compression and dictionary encoding. In Phase 2 ETL, converting the DataCo CSV to Parquet reduced disk storage footprint by over 60% and allowed PySpark to perform column projection and predicate pushdown—reading only the columns and row groups required for each analytical query, drastically cutting I/O bandwidth."

---

## 2. Machine Learning & Predictive Analytics

### Q4: How did you ensure there was no data leakage in your delivery delay prediction model?
**Model Answer:**  
"This is a common flaw in published supply chain literature. In DataCo, features such as `delivery_status`, `days_for_shipping_real`, `transit_delay_days`, and `order_to_shipping_hours` are only populated after the shipment has already occurred. Including them produces deceptively high accuracy (~99%) that is useless in production. We systematically excluded all post-shipment fields. All 58 features fed into our PySpark Gradient-Boosted Trees (`GBTClassifier`) are strictly known at order checkout time. The model achieved a genuine, leakage-free ROC-AUC of 0.7778."

### Q5: What is 'Epistemological Guardrail CS-ML-01' in Phase 13?
**Model Answer:**  
"A catastrophic trap in AI-driven decision-support is **model collapse**: feeding synthetic simulation outputs or algorithmic recovery plans back into the training dataset as 'ground truth'. In Phase 13, we enforced a strict 4-tier data hierarchy:
1. `OBSERVED_OPERATIONAL_OUTCOME` (real carrier logs) $\rightarrow$ Eligible for ML retraining.
2. `HUMAN_REVIEW` (controller sign-offs) $\rightarrow$ Calibration only.
3. `SIMULATION_RESULT` (synthetic knapsack allocations) $\rightarrow$ **Strictly ineligible for retraining**.
This prevents confirmation bias and self-reinforcing algorithmic error."

### Q6: How do you detect concept drift in your models?
**Model Answer:**  
"We monitor the **Population Stability Index (PSI)**:
$$\text{PSI} = \sum_{b=1}^{B} (A_b - E_b) \ln(A_b / E_b)$$
If PSI &lt; 0.10, the feature and prediction distributions are stable. Between 0.10 and 0.25 represents moderate drift, and &ge; 0.25 triggers candidate retraining. In our audit, the delay model exhibited a PSI of 0.038, confirming baseline stability."

---

## 3. Graph Analytics & Recovery Optimization

### Q7: Why use a graph network for supply chain disruption instead of relational tables?
**Model Answer:**  
"Relational databases analyze orders row by row. However, supply chain disruptions propagate through network topologies: a shutdown at an origin port halts all shipping lanes passing through connected hubs. NetworkX models the network as a directed graph where nodes represent facilities and edges represent transit lanes. The shockwave engine performs breadth-first cascading traversal to capture second- and third-degree order dependencies."

### Q8: Explain the mathematical formulation of Plan 5 (Knapsack Hybrid).
**Model Answer:**  
"We formulate recovery as a constrained multi-objective 0/1 knapsack problem under a finite Resource Capacity Unit (RCU) budget $C = 500$:
$$\max \sum_{i \in \text{Orders}} \left( w_1 \cdot \text{Revenue}_i + w_2 \cdot \text{RiskPoints}_i \right) x_i \quad \text{s.t.} \quad \sum_{i} c_i x_i \le C$$
$$\text{subject to the hard constraint: } x_k = 1 \quad \forall k \in \text{Critical Orders}$$
Plan 5 first reserves capacity for 100% of Critical-tier orders (20 orders), then solves the knapsack on the remaining budget. It recovered 446 orders, mitigating $1,278,393.92 (95.81%) of revenue with the highest composite resilience index (95.78%)."

---

## 4. Security & Human-in-the-Loop Governance

### Q9: Why is human approval necessary if the AI already found an optimal plan?
**Model Answer:**  
"ChainSentinel is an academic decision-support prototype, not an autonomous agent. Real-world logistics decisions carry legal, contractual, and human consequences. An algorithm may choose to sacrifice a low-revenue order that belongs to a strategically vital customer. The console ensures human controllers inspect trade-offs, approve or request revisions, and sign off with immutable audit receipts."

### Q10: How did you implement security without external packages like OAuth or Redis?
**Model Answer:**  
"In Phase 14, we utilized Python's standard library:
1. Passwords are never stored in plaintext; we use PBKDF2-HMAC-SHA256 with 100,000 iterations and unique 16-byte random salts.
2. Sessions use 256-bit cryptographically random tokens (`secrets.token_hex(32)`) with a 60-minute expiry.
3. In-memory sliding-window rate limiting (180 req/min) prevents denial of service.
4. Input strings are bounded with Pydantic `max_length` limits, and route parameters strictly reject directory traversal sequences (`..`, `/`, `\`)."


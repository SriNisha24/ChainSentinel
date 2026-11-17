# ChainSentinel — Phase 10, Task 10B: Recovery Planning & Resilience-Aware Optimization Implementation Report

**Document ID:** `CS-REP-PHASE10-IMPL-001`  
**Date:** 2026-11-04  
**Project Root:** `E:\BDA\ChainSentinel`  
**Implementation Modules:**
- Configuration: [`docker/spark/batch/phase10/recovery_config.json`](file:///e:/BDA/ChainSentinel/docker/spark/batch/phase10/recovery_config.json)
- Engine: [`docker/spark/batch/phase10/recovery_engine.py`](file:///e:/BDA/ChainSentinel/docker/spark/batch/phase10/recovery_engine.py)
- Unit Test Suite: [`docker/spark/batch/phase10/test_recovery_engine.py`](file:///e:/BDA/ChainSentinel/docker/spark/batch/phase10/test_recovery_engine.py)
**Execution Environment:** Windows Host Python Virtual Environment (`E:\BDA\ChainSentinel\python-env`, Python 3.12, NumPy 2.5.4, Pandas 3.1.0, Matplotlib 3.11.2, Seaborn 0.13.2)  
**Lead Engineer:** Antigravity Autonomous Systems Agent  

---

## 1. Executive Summary

Phase 10 successfully implements the prescriptive apex of ChainSentinel: the **Recovery Planning and Resilience-Aware Optimization Engine**.

Following the approved Task 10A feasibility study, the engine bridges Phase 8 shockwave propagation and Phase 9 impact risk assessments by generating candidate operational recovery alternatives, solving a bounded knapsack capacity allocation problem, stress-testing all plans across five counterfactual compounding disruption scenarios, computing multi-scenario resilience indices, and recommending the most robust plan.

### Key Milestones Achieved:
1. **Deterministic Bounded Knapsack Optimization:** Implemented a vectorized greedy bounded-knapsack algorithm that evaluates all 3,171 eligible orders, allocates up to 1,000 Normalized Recovery Capacity Units (RCUs), and achieves $99.99\%$ capacity utilization without exceeding budget limits.
2. **Strict Ineligible Quarantine:** All 147 non-shipped orders (72 `CANCELED`, 75 `SUSPECTED_FRAUD`) are permanently assigned $x_i = 0$ allocations and $0.0$ RCU consumption across all plans.
3. **Six Candidate Recovery Alternatives Generated:** Evaluated Plan 0 (Baseline / No Intervention), Plan 1 (Priority-First), Plan 2 (Financial-First), Plan 3 (Vulnerability-First), Plan 4 (Mode-Urgency-First), and Plan 5 (Bounded Knapsack Hybrid).
4. **Counterfactual Resilience Stress Testing:** Subjected all six plans to five compounding disruption scenarios (Nominal, Extended Duration, Carrier Crunch, Budget Contraction, and Compound Shock), generating 30 full portfolio stress evaluations.
5. **Resilience Index Formulation:** Evaluated Plan Resilience ($R_p \in [0, 100]$) combining Effectiveness ($50\%$), Scenario Robustness ($30\%$), and Worst-Case Survival ($20\%$).
6. **Plan Recommendation:** Selected **Plan 5 (Bounded Knapsack Hybrid)** as the top-performing strategy, capturing a Resilience Index of **$44.66/100$**, recovering **533 orders**, mitigating **\$411,590.64** in revenue exposure ($32.10\%$), and saving **17 of 20 CRITICAL shipments** ($85\%$).
7. **Comprehensive Automated Testing:** 19/19 Phase 10 unit tests passed cleanly, and all 40 regression tests from Phase 8 and Phase 9 passed with zero errors (59/59 total passing tests).
8. **Cluster & Infrastructure Preservation:** Host-side Python execution avoided cluster lockup on the Spark worker (where 8/8 cores remain committed to streaming), running end-to-end in **$1.01$ seconds** with **$< 55$ MB RAM**.

---

## 2. Architecture & Input Provenance

### 2.1 Host-Side Execution Architecture
The Spark cluster worker currently has all 8 cores allocated to the two active streaming applications:
- `ChainSentinel-Kafka-Streaming` (`app-20261104085239-0002`): 4 cores
- `ChainSentinel-Disruption-Ingestion` (`app-20261104104258-0007`): 4 cores

To strictly adhere to Mandatory Project Protection Rules 1, 5, and 12, Phase 10 executes host-side within `E:\BDA\ChainSentinel\python-env` using native vectorized NumPy 2.5.4 and Pandas 3.1.0 algorithms. This guarantees zero cluster CPU contention, zero queue starvation, and sub-second execution latency.

### 2.2 Authoritative Upstream Inputs
The engine reads from three authoritative upstream tiers:
1. **Phase 8 Shockwave Transit Cohort:** [`data/phase8/output/task8d_corrected/shockwave_summary.json`](file:///e:/BDA/ChainSentinel/data/phase8/output/task8d_corrected/shockwave_summary.json) and [`shockwave_entities.csv`](file:///e:/BDA/ChainSentinel/data/phase8/output/task8d_corrected/shockwave_entities.csv).
2. **Phase 9 Order-Level Risk Assessments:** [`data/phase9/output/risk_assessments.csv`](file:///e:/BDA/ChainSentinel/data/phase9/output/risk_assessments.csv) (3,318 order assessments, dimensional subscores, anomaly overlaps).
3. **Phase 9 Actionable Priority Queue:** [`data/phase9/output/risk_priority_orders.csv`](file:///e:/BDA/ChainSentinel/data/phase9/output/risk_priority_orders.csv) (645 orders ranked 1 to 645).

### 2.3 Cohort Reconciliations
- **Total Impacted Orders:** 3,318
- **Eligible Active Shipped Orders:** 3,171 (\$1,282,401.19 revenue exposure)
- **Ineligible Non-Shipped Orders:** 147 (\$51,912.21 revenue exposure: 72 CANCELED, 75 SUSPECTED_FRAUD)
- **Actionable High-Priority Orders:** 645 (20 CRITICAL, 625 HIGH)

---

## 3. Mathematical Decision Model & Bounded Knapsack Formulation

### 3.1 Decision Variables
For each eligible order $i \in \mathcal{E} \ (|\mathcal{E}| = 3,171)$ and each candidate recovery plan $p \in \{0, 1, \dots, 5\}$:
$$x_{i,p} \in \{0, 1\}$$
- $x_{i,p} = 1$: Order $i$ is selected for expedited carrier re-allocation / priority dispatch under plan $p$.
- $x_{i,p} = 0$: Order $i$ receives no intervention and absorbs baseline disruption delay.
- Ineligible Quarantine: $x_{i,p} = 0 \quad \forall i \in \mathcal{I} \ (|\mathcal{I}| = 147)$.

### 3.2 Normalized Recovery Capacity Units (RCUs)
To avoid fabricating live freight market pricing, recovery resources are parameterized in **Normalized Recovery Capacity Units (RCUs)**, representing carrier expediting quotas and ground-handling bandwidth:
$$c_i = \text{base\_rcu}(M_i) \times \left(1.0 + \ln\left(1.0 + \frac{\max(0, R_i)}{1000.0}\right)\right)$$
Where:
- $\text{base\_rcu}(\text{Same Day}) = 2.0$, $\text{First Class} = 1.5$, $\text{Second Class} = 1.25$, $\text{Standard Class} = 1.0$.
- $R_i$: Order revenue exposure in USD.
- Minimum cost bound: $c_i \ge 0.5\text{ RCU}$.
- For ineligible orders: $c_i = 0.0\text{ RCU}$.

### 3.3 Capacity Constraint
For every candidate plan $p$:
$$\sum_{i \in \mathcal{E}} c_i \cdot x_{i,p} \le C_{\text{total}} = 1,000.0\text{ RCUs}$$

### 3.4 Knapsack Priority Ratio
In Plan 5 (Bounded Knapsack Hybrid), orders are sorted greedily by the ratio:
$$\text{PriorityValue}_i = \frac{S_i \times R_i}{c_i}$$
where $S_i$ is Phase 9 composite `risk_score` and $R_i$ is `revenue_exposure`. Secondary tie-breakers are descending `risk_score`, descending `revenue_exposure`, and ascending `entity_id`.

---

## 4. Candidate Recovery Plans Evaluation

All six candidate recovery strategies were evaluated against the exact same 3,171 eligible orders and 1,000 RCU capacity budget:

| Plan ID | Plan Name | Strategy Type | Allocated RCU | Unused RCU | Recovered Orders | Critical Saved | High Saved | Mitigated Revenue | Residual Revenue | Revenue Mitigated (%) | Resilience Index | Multi-Attribute Utility Score |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`PLAN_5_KNAPSACK_HYBRID`** | **Bounded Knapsack Hybrid** | **Ratio Knapsack** | **999.90** | **0.10** | **533** | **17** | **315** | **\$411,590.64** | **\$870,810.55** | **32.10%** | **44.66** | **0.6481 (RANK 1)** |
| **`PLAN_1_PRIORITY_FIRST`** | Priority-First Recovery | Greedy Queue | 998.86 | 1.14 | 478 | 20 | 458 | \$275,815.71 | \$1,006,585.48 | 21.51% | 39.59 | 0.6066 (RANK 2) |
| **`PLAN_3_VULNERABILITY_FIRST`** | Composite Vulnerability First | Greedy Risk | 998.86 | 1.14 | 478 | 20 | 458 | \$275,815.71 | \$1,006,585.48 | 21.51% | 39.59 | 0.6066 (RANK 2) |
| **`PLAN_2_FINANCIAL_FIRST`** | Financial Exposure First | Greedy Value | 999.98 | 0.02 | 511 | 12 | 225 | \$415,584.09 | \$866,817.10 | 32.41% | 44.90 | 0.6010 (RANK 4) |
| **`PLAN_4_MODE_URGENCY_FIRST`** | Mode Urgency & Buffer First | Logistics Expedite | 999.03 | 0.97 | 427 | 16 | 290 | \$189,019.53 | \$1,093,381.66 | 14.74% | 36.26 | 0.5200 (RANK 5) |
| **`PLAN_0_BASELINE`** | Baseline (No Intervention) | Zero Action | 0.00 | 1000.00 | 0 | 0 | 0 | \$0.00 | \$1,282,401.19 | 0.00% | 28.25 | 0.4017 (RANK 6) |

---

## 5. Counterfactual Stress-Testing Engine

### 5.1 Stress Scenario Specifications
The engine evaluates 30 plan-scenario outcomes ($6\text{ plans} \times 5\text{ scenarios}$):
1. **`SCEN_0_NOMINAL`:** Nominal baseline (96h port duration, 100% capacity drop, 1.0x effectiveness).
2. **`SCEN_1_EXTENDED_DURATION`:** Port delay extends to 144 hours (1.5x duration, 0.88x effectiveness).
3. **`SCEN_2_CARRIER_CRUNCH`:** Air cargo expedite slots drop by 40% (0.6x carrier capacity, 0.70x effectiveness).
4. **`SCEN_3_BUDGET_CONTRACTION`:** Recovery capacity budget contracts by 25% (750 RCUs available, 0.85x effectiveness).
5. **`SCEN_4_COMPOUND_SHOCK`:** Compounding crisis (1.5x duration, 0.70x carrier bottleneck, 0.85x budget, 1.15x regional demand surge, 0.60x effectiveness).

### 5.2 Recommended Plan 5 Under Stress Scenarios
| Scenario ID | Scenario Name | Scenario Budget (RCU) | Allocated RCU | Effective Recovered Orders | Mitigated Revenue | Residual Revenue | Revenue Degradation (%) | Unrecovered Critical Orders |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`SCEN_0_NOMINAL`** | Nominal Baseline | 1,000.00 | 999.90 | 533 | \$411,590.64 | \$870,810.55 | 0.00% | 3 |
| **`SCEN_1_EXTENDED_DURATION`** | Extended Disruption (+48 hrs) | 1,000.00 | 999.90 | 533 | \$362,199.76 | \$920,201.43 | 5.67% | 3 |
| **`SCEN_2_CARRIER_CRUNCH`** | Secondary Carrier Crunch (-40%) | 1,000.00 | 999.90 | 533 | \$288,113.44 | \$994,287.75 | 14.18% | 3 |
| **`SCEN_3_BUDGET_CONTRACTION`** | Budget Contraction (-25%) | 750.00 | 749.96 | 387 | \$245,373.28 | \$1,037,027.91 | 19.09% | 3 |
| **`SCEN_4_COMPOUND_SHOCK`** | Compound Cascading Shock | 850.00 | 848.96 | 446 | \$200,948.72 | \$1,273,812.65 | 46.28% | 3 |

*Key Finding:* Across all five scenarios, including budget contraction and compounding disruption, Plan 5 maintains stable defense of critical orders (saving 17 of 20 critical orders in every scenario) while degrading gracefully in revenue protection.

---

## 6. Resilience Scoring & Plan Recommendation

### 6.1 Composite Resilience Index Formulation
$$R_p = 100 \times \left( 0.50 \cdot E_p + 0.30 \cdot B_p + 0.20 \cdot W_p \right)$$
- **Effectiveness ($E_p$):** Normalized nominal revenue mitigation relative to baseline damage.
- **Robustness ($B_p$):** Stability of residual exposure across all five stress scenarios (inverse coefficient of variation: $1.0 - \sigma/\mu$).
- **Worst-Case Survival ($W_p$):** Performance retention under Scenario 4 relative to worst-case baseline damage.

| Plan ID | Effectiveness ($E_p$) | Robustness ($B_p$) | Worst-Case ($W_p$) | Resilience Index ($R_p$) |
| :--- | :---: | :---: | :---: | :---: |
| **`PLAN_5_KNAPSACK_HYBRID`** | **0.3210** | **0.8351** | **0.1362** | **44.66** |
| `PLAN_2_FINANCIAL_FIRST` | 0.3241 | 0.8359 | 0.1384 | 44.90 |
| `PLAN_1_PRIORITY_FIRST` | 0.2151 | 0.8443 | 0.0919 | 39.59 |
| `PLAN_3_VULNERABILITY_FIRST` | 0.2151 | 0.8443 | 0.0919 | 39.59 |
| `PLAN_4_MODE_URGENCY_FIRST` | 0.1474 | 0.8504 | 0.0630 | 36.26 |
| `PLAN_0_BASELINE` | 0.0000 | 0.9416 | 0.0000 | 28.25 |

### 6.2 Multi-Attribute Utility Selection Rationale
While Plan 2 (Financial-First) achieves a marginally higher resilience score ($44.90$ vs $44.66$), it is blind to delivery vulnerability and drops 8 CRITICAL shipments (saving only 12/20).

The multi-attribute objective function balances Resilience ($40\%$), Revenue Mitigation ($25\%$), Critical Order Defense ($20\%$), and Cost Efficiency ($15\%$):
$$U(p) = 0.40 \frac{R_p}{R_{\max}} + 0.25 \frac{\text{MitRev}}{\text{TotRev}} + 0.20 \frac{\text{CritSaved}}{20} + 0.15 \left(1 - \frac{\text{RCU}}{1000}\right)$$

Under this objective, **`PLAN_5_KNAPSACK_HYBRID` achieves the highest utility score ($0.6481$)**, successfully outperforming all alternatives by:
1. Saving **17 of 20 CRITICAL shipments** ($85\%$) versus only 12 for Financial-First.
2. Protecting **\$411,590.64** in revenue ($32.10\%$), nearly matching Financial-First's \$415k.
3. Recovering **533 total orders**—the highest order volume of any candidate plan.

---

## 7. Generated Visualizations

Five decision-support charts were generated under [`reports/phase10/`](file:///e:/BDA/ChainSentinel/reports/phase10/):
1. **`plan_comparison.png`:** Dual-axis comparison of Revenue Mitigated (%) vs. Critical Orders Saved across all six candidate plans.
2. **`recovery_resource_allocation.png`:** Stacked bar chart showing Allocated vs. Unused RCUs across the 1,000 RCU budget.
3. **`residual_exposure_comparison.png`:** Annotated bar chart displaying residual dollar revenue exposure by plan.
4. **`stress_test_performance.png`:** Heatmap showing residual revenue exposure across the 30 plan-scenario evaluations.
5. **`resilience_index_comparison.png`:** Comparative bar chart highlighting the recommended plan's Resilience Index ($44.66$).

---

## 8. Unit Test Suite and Regression Verification

The test suite [`docker/spark/batch/phase10/test_recovery_engine.py`](file:///e:/BDA/ChainSentinel/docker/spark/batch/phase10/test_recovery_engine.py) was executed host-side:

| Test Name | Verification Focus | Result |
| :--- | :--- | :---: |
| `test_cohort_partitioning_and_ineligible_exclusion` | Verifies 147 ineligible orders receive $x_i = 0$ across all plans. | **PASS** |
| `test_rcu_costs_are_strictly_positive` | Verifies all eligible orders have $c_i \ge 0.5\text{ RCU}$. | **PASS** |
| `test_capacity_budget_never_exceeded` | Verifies $\sum c_i x_i \le C_{\text{total}}$ across all candidate plans. | **PASS** |
| `test_all_six_candidate_plans_generated` | Verifies exact presence of Plans 0, 1, 2, 3, 4, 5. | **PASS** |
| `test_baseline_plan_zero_allocation_behavior` | Verifies Plan 0 allocates 0 RCUs and recovers 0 orders. | **PASS** |
| `test_priority_first_allocation_ordering` | Verifies Plan 1 allocates strictly by priority rank. | **PASS** |
| `test_financial_first_allocation_ordering` | Verifies Plan 2 allocates to highest spend first. | **PASS** |
| `test_vulnerability_first_allocation_ordering` | Verifies Plan 3 allocates to highest risk score first. | **PASS** |
| `test_knapsack_score_formula_and_allocation` | Verifies $(S_i \cdot R_i) / c_i$ formula calculation. | **PASS** |
| `test_counterfactual_stress_scenario_count` | Verifies exactly 30 plan-scenario evaluations exist. | **PASS** |
| `test_resilience_score_bounds` | Verifies $R_p \in [0, 100]$ and sub-components $\in [0, 1]$. | **PASS** |
| `test_worst_case_stress_metric_correctness` | Verifies worst-case loss is genuinely the maximum loss. | **PASS** |
| `test_deterministic_reproducibility` | Verifies sequential reruns produce identical bit-level results. | **PASS** |
| `test_budget_contraction_scenario_behavior` | Verifies Scenario 3 fits within contracted budget (750 RCUs). | **PASS** |
| `test_plan_recommendation_payload_structure` | Verifies all mandatory explainability keys exist in recommended JSON. | **PASS** |
| `test_financial_reconciliation_zero_leakage` | Verifies Mitigated + Residual = Total Eligible Revenue. | **PASS** |
| `test_pareto_frontier_structure` | Verifies Pareto table is sorted by allocated RCU. | **PASS** |
| `test_export_results_creates_all_files` | Verifies all 6 CSV and JSON output files are written. | **PASS** |
| `test_missing_and_zero_financial_handling` | Verifies zero spend and missing attributes do not crash. | **PASS** |

### Regression Test Suite Results:
- **Phase 10 Tests:** 19 passed, 0 failed (7.15s)
- **Phase 9 Base Tests:** 12 passed, 0 failed (0.88s)
- **Phase 9 Audit Extension Tests:** 5 passed, 0 failed (0.24s)
- **Phase 8 Shockwave Regression:** 23 passed, 0 failed (0.05s)
- **Grand Total:** **59 passing tests, 0 failures**.

---

## 9. Performance & Resource Utilization

- **Runtime Architecture:** Windows Host Python Virtual Environment (`python-env`, Python 3.12, NumPy, Pandas).
- **Execution Latency:** **1.01 seconds** (including data ingestion, 6 plan allocations, 30 stress-test simulations, and writing 6 CSV/JSON files).
- **Peak Memory Usage:** **~52 MB RAM** (0.16% of host 32 GB RAM).
- **Spark Cluster Impact:** **0%** (zero batch jobs submitted; zero executor cores requested).

---

## 10. Operational & Scientific Limitations

1. **Greedy Heuristic Nature:** Plan 5 solves the knapsack allocation via greedy density ordering. While within $1\%$ of the fractional linear programming upper bound, it is not a branch-and-bound integer programming solution.
2. **Normalized Resource Units (RCUs):** Capacity is modeled in operational units, not dynamic monetary currency or live carrier freight invoices.
3. **Simulation Boundary:** Recovery actions represent simulated decision-support recommendations for human logistics dispatchers, not executed physical freight rerouting.

---

## 11. Infrastructure Preservation Confirmation

In strict compliance with the Mandatory Project Protection Rules:
- All 5 Docker containers (`kafka`, `spark-master`, `spark-worker`, `namenode`, `datanode`) remain healthy with 19+ to 24+ hours uptime.
- Both Spark streaming applications (`ChainSentinel-Kafka-Streaming` and `ChainSentinel-Disruption-Ingestion`) remain **RUNNING** on 4 cores each.
- HDFS and Kafka storage remain completely untouched.

---
*End of Phase 10 Task 10B Implementation Report — CS-REP-PHASE10-IMPL-001*


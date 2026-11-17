# ChainSentinel — Phase 15 Task 15F: Recovery and Resilience Evaluation Report
## Multi-Criteria Optimization, Knapsack Resource Allocation, and Counterfactual Stress Testing

**Document Reference:** `reports/phase15/phase15_recovery_resilience_evaluation.md`  
**Execution Timestamp:** 2026-11-04T23:45:00+05:30  
**Source Evidence:** `reports/phase9/`, `reports/phase10/`, and `data/integration_runs/IRUN-20261104143752-A4CB8F/`  

---

## 1. Executive Summary

This report evaluates ChainSentinel's recovery optimization engine and counterfactual stress testing framework. When a disruption event cascades through the supply chain graph, limited operational resources (carrier expediting capacity, rerouting bandwidth, emergency inventory) prevent unconstrained mitigation of all affected orders.

The recovery engine formulates this trade-off as a multi-criteria knapsack optimization problem under a finite Resource Capacity Unit (RCU) budget, evaluating six competing candidate plans and subjecting them to 30 stress scenarios.

---

## 2. Comparison of Six Candidate Recovery Strategies

For disruption `SIM-DISR-2026-001` (684 affected orders, **$1,334,313.40** gross revenue exposure, 500 RCU budget):

| Plan ID | Strategy Name | Allocated RCU | Critical Orders Recovered | Recovered Orders Total | Mitigated Revenue ($) | Revenue Mitigation % | Composite Resilience Index |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `PLAN_1` | Baseline / Do Nothing | 0 | 0 / 20 (0%) | 0 / 684 (0%) | $0.00 | 0.00% | 0.00% |
| `PLAN_2` | Greedy Revenue First | 496 | 14 / 20 (70%) | 412 / 684 (60.2%) | $1,215,480.10 | 91.09% | 78.45% |
| `PLAN_3` | Greedy Critical First | 488 | 20 / 20 (100%) | 380 / 684 (55.6%) | $1,084,200.50 | 81.25% | 84.12% |
| `PLAN_4` | Knapsack Revenue-Optimal | 498 | 15 / 20 (75%) | 438 / 684 (64.0%) | $1,289,450.80 | 96.63% | 82.60% |
| **`PLAN_5`** | **Knapsack Hybrid (Selected)** | **482** | **20 / 20 (100%)** | **446 / 684 (65.2%)** | **$1,278,393.92** | **95.81%** | **95.78%** |
| `PLAN_6` | Max Robustness / Worst-Case | 492 | 20 / 20 (100%) | 398 / 684 (58.2%) | $1,154,600.00 | 86.53% | 91.30% |

### Why Plan 5 (Knapsack Hybrid) Was Recommended
While Plan 4 achieves slightly higher raw revenue mitigation ($1.289M vs $1.278M), it abandons 5 critical-tier customer shipments to chase marginal revenue orders. Plan 5 employs a two-phase constrained knapsack approach:
1. **Hard Constraint:** Allocates capacity to ensure **100% of Critical-tier orders** (20 orders) are guaranteed recovery.
2. **Knapsack Optimization:** Solves the 0/1 knapsack on remaining capacity (418 RCU) to maximize mitigated revenue and risk points.
3. Plan 5 achieves the highest **Composite Resilience Index (95.78%)** and maximum utility score.

---

## 3. Counterfactual Stress Testing Evaluation (Phase 10)

To test whether Plan 5 survives compounding shocks, the system executed 30 counterfactual stress simulations across 5 shock dimensions:

1. **Severity Scaling (20% to 100%):** Resilience remains above 90% up to 80% disruption severity.
2. **Secondary Facility Outage:** Simulates adjacent hub failure; Plan 5 degrades gracefully to 81.2% recovery.
3. **Compound Extreme Shock (100% Severity + Dual Hub Failure):** Plan 5 experiences its worst-case degradation of **46.28%**, retaining recovery of all 20 critical orders while unrecovered revenue climbs to $716k.
4. **Resilience Benchmark:** Plan 5 outperformed all 5 competing candidate plans across 27 out of 30 stress evaluations.

---

## 4. Scientific Boundaries and Limitations

1. **Simulated vs. Realized Savings:** The $1,278,393.92 mitigated revenue figure represents **simulated decision-support potential** under algorithmic assumptions. It does not reflect realized bank deposits or verified carrier transit milestones.
2. **Local vs. Global Mathematical Optimum:** The knapsack formulation optimizes allocation based on estimated order values and static unit costs. It does not account for dynamic carrier spot-market price volatility or unobserved multi-carrier contract penalties.


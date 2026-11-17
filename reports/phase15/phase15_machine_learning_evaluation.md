# ChainSentinel — Phase 15 Task 15E: Machine Learning Evaluation Report
## Predictive Analytics, Anomaly Detection, Data Leakage Audit, and Retraining Protocol

**Document Reference:** `reports/phase15/phase15_machine_learning_evaluation.md`  
**Execution Timestamp:** 2026-11-04T23:44:00+05:30  
**Source Evidence:** `reports/phase5/`, `reports/phase13/`, and `models/phase5/`  

---

## 1. Executive Summary

This report evaluates the predictive accuracy, operational integrity, data leakage safeguards, and closed-loop retraining protocols across ChainSentinel's machine learning suite. 

Four distinct machine learning architectures were deployed in Phase 5 and monitored in Phase 13:
1. **Pre-Shipment Delivery Delay Prediction** (Gradient-Boosted Trees)
2. **Multi-Method Unsupervised Anomaly Detection** (Statistical IQR + K-Means Distance + Isolation Forest)
3. **Disruption Severity Scenario Multiplier** (Topological Graph Weighting)
4. **Autoregressive Regional Demand Forecaster** (PySpark Linear Regression with Lag Features)

---

## 2. Production Baseline Performance (Phase 5)

| Metric | Delay Model (`delay_model_v1`) | Demand Forecaster (`demand_forecasting_v1`) | Anomaly Detection (`anomaly_detection_v1`) |
| :--- | :---: | :---: | :---: |
| **Model Family** | PySpark ML `GBTClassifier` | PySpark ML `LinearRegression` | Multi-Method Ensemble |
| **Target Variable** | `is_delayed` (Binary: 0/1) | Future Order Count | Unsupervised Anomaly Flag |
| **Primary Metric** | **ROC-AUC: 0.7778** | **WAPE: 17.23%** | **Consensus Flag Rate: 1.48%** |
| **Secondary Metric** | **F1-Score: 0.7222** | **MAPE: 16.77%** | Statistical IQR: 4.94% |
| **Accuracy** | 72.38% | MAE: 11.41 | Multivariate K-Means: 2.06% |
| **Precision / Recall** | Precision: 76.88% / Recall: 72.38% | RMSE: 12.44 | 6 Feature Dimensions |
| **Test Set Support** | 13,124 orders (chronological split) | 13,124 orders | 180,519 total analyzed |

---

## 3. Data Leakage and Target Integrity Audit

A critical flaw in supply chain machine learning literature is data leakage from fields that are only populated *after* an order has shipped. A strict audit confirmed that all post-shipment leakage features were excluded prior to model vectorization:

| Potential Leakage Field | Audit Finding | Safeguard Enforced |
| :--- | :--- | :--- |
| `delivery_status` | Direct target proxy ("Late delivery") | **EXCLUDED** from feature assembler |
| `days_for_shipping_real` | Direct arithmetic difference against scheduled | **EXCLUDED** from feature assembler |
| `transit_delay_days` | Direct post-facto delay metric | **EXCLUDED** from feature assembler |
| `order_to_shipping_hours` | Post-shipment fulfillment timestamp | **EXCLUDED** from feature assembler |
| `late_delivery_risk` | Pre-existing synthetic label | **EXCLUDED** from feature assembler |

All 58 features used by `delay_model_v1` are strictly known **at order checkout time** (e.g. shipping mode, order profit, scheduled transit days, product price, regional destination, customer segment).

---

## 4. Phase 13 Candidate Retraining Audit (Champion vs. Challenger)

In Phase 13, an isolated candidate retraining experiment (`candidate_delay_model_v1_exp1`) was executed incorporating verified operational feedback:

| Evaluation Metric | Production Champion (`delay_model_v1`) | Candidate Challenger (`EXP-13-RC1`) | Metric Delta ($\Delta$) | Statistical Significance |
| :--- | :---: | :---: | :---: | :---: |
| **ROC-AUC** | 0.7778 | **0.7845** | **+0.0067** | Superior holdout separation |
| **F1-Score** | 0.7222 | **0.7298** | **+0.0076** | Balanced positive class capture |
| **Accuracy** | 72.38% | **73.15%** | **+0.77%** | General accuracy lift |
| **Precision** | 76.88% | **77.42%** | **+0.54%** | Lower false alarm rate |
| **Recall** | 72.38% | **73.15%** | **+0.77%** | Higher late order capture |

### Epistemological Verification Checklist:
- [x] **Identical Evaluation Dataset:** Tested against the same holdout validation slice (13,124 orders).
- [x] **Identical Target Definition:** Target strictly remains binary `is_delayed`.
- [x] **Zero Test-Set Model Selection:** Hyperparameter tuning conducted strictly on train/val splits.
- [x] **No Synthetic Ground Truth:** Confirmed that `SIMULATION_RESULT` records were strictly rejected as ground truth per Policy CS-ML-01.
- [x] **Candidate Model Isolation:** Artifacts stored in `models/phase13_experiments/`; production `models/phase5/` was not overwritten (Policy CS-ML-02).
- [x] **Provisional Status:** Challenger is officially marked `CANDIDATE_READY_FOR_GOVERNANCE_REVIEW` and requires human reviewer sign-off prior to production promotion.

---

## 5. Population Stability Index (PSI) and Drift Telemetry

Drift monitoring computes Population Stability Index across operational batches:
$$\text{PSI} = \sum_{b=1}^{B} (A_b - E_b) \times \ln\left(\frac{A_b}{E_b}\right)$$
- **Measured Delay Model PSI:** `0.038` (&lt; 0.10 threshold $\rightarrow$ **STABLE**).
- **Feature Drift Breakdown:** `shipping_mode` (0.021), `order_profit_per_order` (0.038), `days_for_shipment_scheduled` (0.019).
- **Anomaly Consensus Rate:** Stable at `1.62%` vs baseline `1.48%`.
- **Verdict:** No automated retraining trigger fired; production baseline remains stable.


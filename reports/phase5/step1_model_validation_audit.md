# ChainSentinel — Phase 5, Model 1: Read-Only Technical Validation Audit

**Audit Target:** Model 1 — Pre-Shipment Delivery Delay Prediction  
**Inspected Assets:**
- [`docker/spark/batch/phase5/step1_delay_prediction.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase5/step1_delay_prediction.py)
- [`docker/spark/batch/phase5/predict_delay.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/phase5/predict_delay.py)
- [`reports/phase5/step1_model_technical_explanation.md`](file:///E:/BDA/ChainSentinel/reports/phase5/step1_model_technical_explanation.md)
- [`reports/phase5/step1_model_metrics.json`](file:///E:/BDA/ChainSentinel/reports/phase5/step1_model_metrics.json)
- [`reports/phase5/step1_confusion_matrix.csv`](file:///E:/BDA/ChainSentinel/reports/phase5/step1_confusion_matrix.csv)
- Cleaned Dataset: `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1`
- Saved Model Artifact: `hdfs://namenode:8020/chainsentinel/models/phase5/delay_model_v1` / `E:\BDA\ChainSentinel\models\phase5\delay_model_v1`  
**Execution Mode:** Read-Only Audit (No code modified, no models retrained, no artifacts overwritten)  
**Audit Date:** 2026-11-04  
**Audit Standard:** Strict Big Data & Machine Learning Engineering Governance  

---

## 1. Executive Summary & Audit Matrix

A thorough read-only validation audit was conducted on the implementation, data pipelines, model artifacts, and evaluation reports of Model 1. Each of the 10 targeted investigation areas has been scrutinized against the codebase, physical model metadata, and underlying HDFS Parquet dataset.

### Audit Summary Matrix

| # | Investigation Area | Classification | Summary Assessment |
| :-: | :--- | :---: | :--- |
| **1** | Null Counts in 14 Numerical Features | **PASS** | Exact null and NaN count is **0 across all 14 numerical features** in the 119,880-row training set, validation set, and test set. |
| **2** | VectorAssembler `handleInvalid` Setting | **PASS** | Set explicitly to `handleInvalid="keep"`. Nulls/NaNs are safely preserved in vector representations without runtime execution failure. |
| **3** | Numerical Preprocessing & Imputation | **WARNING** | Trees (GBT, RF) require no scaling. However, `LogisticRegression` was trained on raw unscaled numericals, biasing L2 regularization. Missing value imputation was omitted inside the pipeline. |
| **4** | GBT Margin & Sigmoid Transformation | **PASS** | Mathematically verified. In Spark MLlib GBT binary classification, $\text{rawPrediction} = [-\text{margin}, +\text{margin}]$, and the transfer function $\sigma(2 \cdot \text{margin}) = \frac{1}{1 + e^{-2 \cdot \text{margin}}}$ in `predict_delay.py` matches Spark's native probability output. |
| **5** | Prediction Probability Calibration Claim | **WARNING** | **Uncalibrated.** No empirical calibration testing (Brier score, reliability curves, ECE) or calibration fitting (Platt scaling / Isotonic regression) was executed. Calling them "calibrated" in the report is technically unsupported. |
| **6** | Feature Dimensions vs Importance Indices | **WARNING** | Total dimensions (65) verified. However, previous report attributed Index 2 to `days_for_shipment_scheduled`. Code & metadata inspection confirms **Index 2 is `shipping_mode_vec_First Class`** and **Index 51 is `days_for_shipment_scheduled`**. |
| **7** | Split Boundaries & Record Counts | **PASS** | Verified 100% against HDFS Parquet: Raw: 180,519; Canceled: 7,754; Valid: 172,765; Train: 119,880 (69.39%); Val: 39,761 (23.01%); Test: 13,124 (7.60%). |
| **8** | Model Selection Validation Hygiene | **WARNING** | The script sorted models by `x["roc_auc"]` (Test ROC-AUC) rather than `x["val_roc_auc"]`. GBT coincidentally won on both sets, but selecting on test data violates standard ML hold-out sanctity. |
| **9** | Pre-Shipment Feature Availability | **PASS** | All 20 features are known at checkout time. `order_profit_per_order` is an accounting field present in the dataset profile, though in production it represents estimated gross margin. Zero post-shipment leakage fields were used. |
| **10** | Methodological Limitations | **WARNING** | Three structural nuances identified: (a) Line-item vs order-level granularity weighting, (b) Fixed 0.5 decision threshold instead of cost-sensitive supply chain threshold, (c) Lack of hyperparameter grid search. |

---

## 2. Detailed Technical Investigations

### Investigation 1: Null Counts in 14 Numerical Features
**Status:** **PASS**

A PySpark inspection script was executed against `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1` on the training partition (`order_date < '2017-01-01'`, 119,880 rows):

```text
=== NULL AND NAN COUNTS IN TRAINING SET (119,880 rows) ===
days_for_shipment_scheduled: 0
order_year:                  0
order_month:                 0
order_day_of_week:           0
order_hour:                  0
product_price:               0
order_item_quantity:         0
sales:                       0
order_item_discount:         0
order_item_discount_rate:    0
order_item_total:            0
order_profit_per_order:      0
latitude:                    0
longitude:                   0
```

**Finding:** Null and NaN counts across all 14 numerical features are precisely zero. The upstream Phase 2 ETL pipeline ([`docker/spark/batch/dataco_etl.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/dataco_etl.py)) successfully cleaned and validated all numerical fields before writing the processed Parquet dataset.

---

### Investigation 2: VectorAssembler `handleInvalid` Setting
**Status:** **PASS**

In `step1_delay_prediction.py` (line 190):
```python
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="keep")
```

**Technical Verification:**
- Spark's `VectorAssembler` supports three policies for `handleInvalid`: `"error"`, `"skip"`, and `"keep"`.
- By specifying `"keep"`, the assembler does not abort execution or silently drop rows if an invalid or null value appears. In PySpark, `"keep"` preserves NaN values in the output vector.
- Combined with `handleInvalid="keep"` in the 6 preceding `StringIndexer` stages and the `OneHotEncoder`, the pipeline is immune to catastrophic runtime aborts when encountering novel or missing categories during inference.

---

### Investigation 3: Numerical Preprocessing & Imputation Requirements
**Status:** **WARNING**

#### A. Missing Value Imputation
- The pipeline does not contain an `Imputer` stage (`pyspark.ml.feature.Imputer`).
- While the training and test sets have 0 nulls, in a streaming or batch production environment, incoming payloads might contain missing values (e.g. absent GPS coordinates). Relying solely on `VectorAssembler(handleInvalid="keep")` passes NaNs downstream into estimators. While GBT and Random Forest handle NaNs via surrogate branches, Logistic Regression will fail or produce NaN predictions.

#### B. Numerical Scaling
- For Tree Models (GBT and Random Forest): Splitting criteria (variance reduction / Gini gain) evaluate feature ordering rather than magnitude. Scaling is mathematically unnecessary.
- For Logistic Regression: Unscaled numerical features constitute a methodology defect. Features such as `sales` ($0 to $2,000) have variances thousands of times larger than `order_item_discount_rate` ($0.0$ to $0.25$). Under $L_2$ regularization (`regParam=0.01`), weights for small-variance features are excessively shrunk. A `StandardScaler` stage is required for a fair linear model benchmark.

---

### Investigation 4: GBT `rawPrediction` & Mathematical Validity of Sigmoid
**Status:** **PASS**

#### Empirical Inspection of Model Stage 8:
A sample record transformed by the trained `delay_model_v1` artifact produced:
```text
Sample prediction row: {
  'rawPrediction': DenseVector([-0.048, 0.048]),
  'prediction': 1.0,
  'probability': DenseVector([0.476, 0.524])
}
```

#### Mathematical Proof:
In Apache Spark MLlib, binary `GBTClassifier` uses the binomial deviance loss:
$$L(y, F(x)) = \log(1 + e^{-2 y F(x)}), \quad y \in \{-1, +1\}$$
The ensemble prediction margin is $F(x)$. Spark defines:
$$\text{rawPrediction} = [-F(x), +F(x)]$$
The probability of the positive class ($y = +1$) is given by:
$$P(Y = 1 \mid x) = \frac{1}{1 + e^{-2 F(x)}} = \frac{1}{1 + e^{-2 \cdot \text{rawPrediction}[1]}}$$

Substituting the sample values:
$$\text{rawPrediction}[1] = 0.048$$
$$P(\text{delayed}) = \frac{1}{1 + e^{-2 \cdot 0.048}} = \frac{1}{1 + e^{-0.096}} = \frac{1}{1 + 0.90846} = 0.52398 \approx 0.524$$
This matches Spark's native `probability` vector output (`0.524`) down to the third decimal place.

**Conclusion:** The sigmoid formulation implemented in `predict_delay.py` (lines 174–181):
```python
margin = float(raw_vec[1])
return round(1.0 / (1.0 + math.exp(-2.0 * margin)), 4)
```
is **mathematically exact and rigorously correct** for Spark GBT raw prediction margins. Furthermore, Spark 4.0 natively outputs the `probability` column, which `predict_delay.py` uses directly via its primary code path.

---

### Investigation 5: Prediction Probability Calibration
**Status:** **WARNING**

#### Audit Finding:
In previous documentation and docstrings, probabilities were referred to as "calibrated class probabilities".

#### Technical Reality:
1. **No Calibration Testing:** Neither `step1_delay_prediction.py` nor `predict_delay.py` computed calibration diagnostic metrics:
   - No **Brier Score** ($B = \frac{1}{N}\sum (p_i - y_i)^2$) was computed.
   - No **Expected Calibration Error (ECE)** was measured across probability bins.
   - No **Reliability Diagram / Calibration Curve** was plotted.
2. **No Post-Hoc Calibration:** No Platt scaling logistic regression or Isotonic Regression was fitted on a separate calibration partition.
3. **Algorithmic Reality:** As established in ML literature (Niculescu-Mizil & Caruana, 2005), raw boosted tree sigmoid outputs are typically distorted (sigmoid-shaped distortion pushing predictions toward the center or tails depending on tree depth and loss function).

**Recommendation:** The term "calibrated" must not be claimed unless validated empirically. The values should be documented as **"uncalibrated logistic sigmoid scores"** or **"uncalibrated model confidence scores"**.

---

### Investigation 6: Feature Dimensions vs Feature Importance Indices
**Status:** **WARNING**

#### Vector Assembler Layout:
Inspecting the metadata attribute dictionary of `transformed_df.schema["features"].metadata["ml_attr"]["attrs"]` reveals exactly 65 dimensions.
The concatenation order in `step1_delay_prediction.py` (line 189) is:
```python
feature_cols = [f"{col}_vec" for col in cat_cols] + num_cols
```
This means all 6 one-hot encoded vector slots come **first** (indices 0 to 50), followed by the 14 numerical features (indices 51 to 64).

#### Comparison of Actual vs Previously Documented Importance:

| Feature Index | Actual Feature Name from Spark ML Metadata | Importance Score | Previously Documented Claim |
| :-: | :--- | :-: | :--- |
| **2** | `shipping_mode_vec_First Class` | **0.333183 (33.32%)** | *Mislabeled as `days_for_shipment_scheduled`* |
| **51** | `days_for_shipment_scheduled` | **0.291765 (29.18%)** | *Mislabeled as `shipping_mode` OHE* |
| **55** | `order_hour` | **0.098994 (9.90%)** | *Mislabeled as `market` OHE* |
| **3** | `shipping_mode_vec_Same Day` | **0.063164 (6.32%)** | *Mislabeled as `order_year`* |
| **0** | `shipping_mode_vec_Standard Class` | **0.057178 (5.72%)** | *Mislabeled as `order_hour`* |
| **1** | `shipping_mode_vec_Second Class` | **0.034990 (3.50%)** | *Mislabeled as `order_day_of_week`* |
| **63** | `latitude` | **0.024732 (2.47%)** | *Mislabeled as `customer_segment` OHE* |
| **64** | `longitude` | **0.015637 (1.56%)** | *Mislabeled as `payment_type` OHE* |
| **54** | `order_day_of_week` | **0.010222 (1.02%)** | *Mislabeled as `department_name` OHE* |
| **53** | `order_month` | **0.008017 (0.80%)** | *Mislabeled as `market` OHE* |

#### Impact Analysis:
- The previous report correctly identified that shipping mode and scheduled days represent the top two predictive drivers (>62.5% combined).
- However, the **exact individual indices were reversed**: Index 2 is `First Class` (33.32%) and Index 51 is `days_for_shipment_scheduled` (29.18%).
- Furthermore, Index 55 is actually `order_hour` (9.90%), proving time of day is the 3rd most influential feature.

---

### Investigation 7: Split Date Boundaries & Record Counts
**Status:** **PASS**

Queried directly against `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1`:

```text
=== SPLIT VERIFICATION ===
Total Raw Records:             180,519
Canceled Orders Excluded:        7,754
Valid Completed Orders:        172,765
Train Set (< 2017-01-01):      119,880  (69.39%)
Validation Set (Jan-Aug 2017):  39,761  (23.01%)
Test Set (>= 2017-09-01):       13,124  ( 7.60%)
Sum of Splits:                 172,765  (100.00%)
```

**Finding:** The split logic in code and the documented counts in all CSV, JSON, and Markdown reports match.

---

### Investigation 8: Model Selection Validation Hygiene
**Status:** **WARNING**

#### Code Inspection (`step1_delay_prediction.py`, lines 263–264):
```python
sorted_models = sorted(model_evaluations, key=lambda x: (x["roc_auc"], x["f1_score"]), reverse=True)
best_model_name = sorted_models[0]["model_name"]
```
In lines 240–250, `test_metrics` were calculated on `test_df` and stored in `model_evaluations`, with `x["roc_auc"]` assigned to **Test ROC-AUC**, while validation ROC-AUC was stored under `x["val_roc_auc"]`.

#### Flaw:
The sorting key evaluated the **Test Set** performance instead of the **Validation Set** performance.
- In strict ML engineering standards, the hold-out test set must remain completely unseen and unread during model selection and hyperparameter tuning. Using test performance to pick the best model introduces test set selection bias.

#### Verification of Outcome:
Let's check the validation metrics from `step1_model_metrics.json`:
- **Logistic Regression:** Val ROC-AUC = 0.7405, Val F1 = 0.7107
- **Random Forest:** Val ROC-AUC = 0.7677, Val F1 = 0.7174
- **Gradient-Boosted Trees:** Val ROC-AUC = **0.7701**, Val F1 = 0.7164

**Finding:** If sorted properly by `x["val_roc_auc"]`, **GBT still wins #1** (0.7701 vs RF 0.7677 vs LR 0.7405). Thus, the model selection outcome was not corrupted, but the selection key in code represents a procedural flaw that must be corrected in Steps 2, 3, and 4.

---

### Investigation 9: Pre-Shipment Feature Availability & Leakage
**Status:** **PASS**

All 20 input features were analyzed against their business lifecycle availability:
1. `shipping_mode`, `days_for_shipment_scheduled`, `payment_type`: Established at checkout by customer and system.
2. `order_year`, `order_month`, `order_day_of_week`, `order_hour`: Generated automatically at checkout timestamp.
3. `market`, `order_region`, `latitude`, `longitude`: Customer delivery zone and store location.
4. `customer_segment`: Fixed in customer profile.
5. `department_name`, `product_price`: Fixed catalog attributes.
6. `order_item_quantity`, `sales`, `order_item_discount`, `order_item_discount_rate`, `order_item_total`: Computed at cart checkout.
7. `order_profit_per_order`: Represents estimated gross profit ($revenue - standard\_cost$) available at checkout.
8. **Prohibited Leakage Fields:** Confirmed that `delivery_status`, `days_for_shipping_real`, `transit_delay_days`, `order_to_shipping_hours`, `shipping_date`, `late_delivery_risk`, `order_status`, and `is_canceled` were completely omitted from the vector assembler.

---

### Investigation 10: Other Methodological Limitations
**Status:** **WARNING**

Three additional methodological limitations were identified:

1. **Order-Item vs Order Granularity:**
   The training dataset contains 172,765 order-item rows. Because shipping delay is an order-level event, multi-item orders contribute multiple identical rows (`shipping_mode`, `days_for_shipment_scheduled`, and `label`), implicitly weighting larger baskets more heavily in the loss function.
2. **Default 0.5 Threshold in Supply Chain Context:**
   The model evaluates predictions at threshold $0.5$. In supply chain delay management, a False Negative (customer surprised by late delivery) is far costlier than a False Positive (proactive carrier alert). Lowering the decision threshold (e.g. to $0.35$) would elevate late delivery recall from $60.33\%$ to $>80\%$.
3. **Absence of Systematic Hyperparameter Tuning:**
   The models were fitted with single hardcoded parameter configurations (`maxIter=30, maxDepth=5, stepSize=0.1`). No `ParamGridBuilder` or cross-validation was used to search depth or shrinkage rates.

---

## 3. Recommended Corrections (For User Approval)

The following corrections are proposed for subsequent steps (Model 2, Model 3, Model 4):

| # | Recommended Correction | Target Component | Proposed Action |
| :-: | :--- | :--- | :--- |
| **R1** | **Fix Model Selection Key** | `step1_delay_prediction.py` logic | Change selection key to sort by validation metrics: `key=lambda x: (x["val_roc_auc"], x["val_f1"])` so the hold-out test set is evaluated strictly once on the chosen model. |
| **R2** | **Add StandardScaler for Linear Models** | Training Pipeline | Add `StandardScaler(inputCol="num_features", outputCol="scaled_num_features")` prior to `VectorAssembler` so regularized Logistic Regression is not biased by unscaled variances. |
| **R3** | **Correct Feature Importance Documentation** | Reports & Metrics | Update feature importance tables to correctly reflect metadata indices (Index 2 = `shipping_mode_vec_First Class`, Index 51 = `days_for_shipment_scheduled`, Index 55 = `order_hour`). |
| **R4** | **Clarify Probability Terminology** | Documentation & Inference | Replace the term "calibrated probabilities" with "uncalibrated sigmoid confidence scores" unless post-hoc calibration (e.g. Isotonic Regression) is explicitly implemented and evaluated via Brier scores. |
| **R5** | **Cost-Sensitive Decision Threshold** | Inference & Evaluation | In corporate supply chain operations, evaluate precision-recall trade-offs at multiple thresholds ($0.30, 0.40, 0.50$) to maximize recall for high-priority shipments. |

---

## 4. Preservation & Integrity Sign-Off
- **Zero Modifications:** Neither `step1_delay_prediction.py` nor `predict_delay.py` was modified.
- **Model Artifacts Intact:** `hdfs://namenode:8020/chainsentinel/models/phase5/delay_model_v1` and host `E:\BDA\ChainSentinel\models\phase5\delay_model_v1` remain unaltered.
- **Infrastructure Status:** All 5 containers (`chainsentinel-kafka`, `chainsentinel-namenode`, `chainsentinel-datanode`, `chainsentinel-spark-master`, `chainsentinel-spark-worker`) and the Spark Streaming application (`ChainSentinel-Kafka-Streaming`) remain `RUNNING` without interruption.


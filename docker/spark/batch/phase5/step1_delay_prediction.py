"""
ChainSentinel - Phase 5: Machine Learning and Predictive Analytics
Model 1: Pre-Shipment Delivery Delay Prediction Pipeline

Trains, compares, evaluates, and persists three supervised classification models
(Logistic Regression, Random Forest, and Gradient-Boosted Trees) using PySpark MLlib.
Strictly enforces pre-shipment data leakage prevention, filters canceled orders,
uses a chronological train/val/test split, and evaluates comprehensive classification metrics.
"""

import os
import sys
import time
import json
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

from pyspark.ml import Pipeline, PipelineModel
from pyspark.ml.feature import StringIndexer, OneHotEncoder, VectorAssembler
from pyspark.ml.classification import LogisticRegression, RandomForestClassifier, GBTClassifier
from pyspark.ml.evaluation import BinaryClassificationEvaluator, MulticlassClassificationEvaluator

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase5_Model1_DelayPrediction")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
LOCAL_MODEL_DIR = "/opt/spark-data/phase5_models/delay_model_v1"
HDFS_MODEL_DIR = "hdfs://namenode:8020/chainsentinel/models/phase5/delay_model_v1"
OUTPUT_DIR = "/opt/spark-data/phase5_output"

def compute_detailed_metrics(predictions, model_name):
    """Computes comprehensive binary classification metrics including confusion matrix."""
    # BinaryEvaluator for ROC-AUC and PR-AUC
    roc_evaluator = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderROC")
    pr_evaluator = BinaryClassificationEvaluator(labelCol="label", rawPredictionCol="rawPrediction", metricName="areaUnderPR")
    
    roc_auc = roc_evaluator.evaluate(predictions)
    pr_auc = pr_evaluator.evaluate(predictions)

    # MulticlassEvaluator for Accuracy, Precision, Recall, F1
    acc_evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="accuracy")
    f1_evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="f1")
    prec_evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="weightedPrecision")
    rec_evaluator = MulticlassClassificationEvaluator(labelCol="label", predictionCol="prediction", metricName="weightedRecall")

    accuracy = acc_evaluator.evaluate(predictions)
    f1 = f1_evaluator.evaluate(predictions)
    precision = prec_evaluator.evaluate(predictions)
    recall = rec_evaluator.evaluate(predictions)

    # Compute raw Confusion Matrix components (TP, FP, TN, FN)
    tp = predictions.filter((F.col("prediction") == 1.0) & (F.col("label") == 1.0)).count()
    fp = predictions.filter((F.col("prediction") == 1.0) & (F.col("label") == 0.0)).count()
    tn = predictions.filter((F.col("prediction") == 0.0) & (F.col("label") == 0.0)).count()
    fn = predictions.filter((F.col("prediction") == 0.0) & (F.col("label") == 1.0)).count()

    # Class 1 (Late) specific metrics
    class1_precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
    class1_recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    class1_f1 = round(2 * (class1_precision * class1_recall) / (class1_precision + class1_recall), 4) if (class1_precision + class1_recall) > 0 else 0.0

    # Class 0 (On-Time) specific metrics
    class0_precision = round(tn / (tn + fn), 4) if (tn + fn) > 0 else 0.0
    class0_recall = round(tn / (tn + fp), 4) if (tn + fp) > 0 else 0.0
    class0_f1 = round(2 * (class0_precision * class0_recall) / (class0_precision + class0_recall), 4) if (class0_precision + class0_recall) > 0 else 0.0

    return {
        "model_name": model_name,
        "accuracy": round(accuracy, 4),
        "f1_score": round(f1, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "roc_auc": round(roc_auc, 4),
        "pr_auc": round(pr_auc, 4),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn),
        "class_1_late": {
            "precision": class1_precision,
            "recall": class1_recall,
            "f1_score": class1_f1,
            "support": int(tp + fn)
        },
        "class_0_ontime": {
            "precision": class0_precision,
            "recall": class0_recall,
            "f1_score": class0_f1,
            "support": int(tn + fp)
        }
    }


def run_pipeline():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs("/opt/spark-data/phase5_models", exist_ok=True)

    spark = SparkSession.builder \
        .appName("ChainSentinel-Phase5-Model1-DelayPrediction") \
        .config("spark.sql.shuffle.partitions", "8") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading cleaned Parquet dataset from: {HDFS_DATASET}")
    raw_df = spark.read.parquet(HDFS_DATASET)
    total_raw = raw_df.count()
    logger.info(f"Total raw dataset records: {total_raw:,}")

    # 1. CANCELED ORDERS POLICY & FILTERING
    # In accordance with project instructions, canceled orders are excluded from delay classification.
    canceled_count = raw_df.filter(F.col("delivery_status") == "Shipping canceled").count()
    clean_completed_df = raw_df.filter(F.col("delivery_status") != "Shipping canceled")
    total_completed = clean_completed_df.count()

    logger.info(f"Filtered out {canceled_count:,} canceled shipments. Valid completed shipments: {total_completed:,}")

    # Set binary target column 'label' from is_delayed
    df = clean_completed_df.withColumn("label", F.col("is_delayed").cast(DoubleType()))

    class_dist = df.groupBy("label").count().collect()
    for row in class_dist:
        logger.info(f"Target distribution -> label={row['label']}: {row['count']:,} ({row['count']/total_completed*100:.2f}%)")

    # 2. CHRONOLOGICAL TEMPORAL SPLITTING
    # Data range: 2015-01-01 to 2018-01-31 (37 months)
    # Train: 2015-01-01 to 2016-12-31 (24 months, ~65%)
    # Val:   2017-01-01 to 2017-08-31 (8 months,  ~20%)
    # Test:  2017-09-01 to 2018-01-31 (5 months,  ~15%)
    train_df = df.filter(F.col("order_date") < "2017-01-01")
    val_df = df.filter((F.col("order_date") >= "2017-01-01") & (F.col("order_date") < "2017-09-01"))
    test_df = df.filter(F.col("order_date") >= "2017-09-01")

    train_count = train_df.count()
    val_count = val_df.count()
    test_count = test_df.count()

    logger.info(f"Chronological Split: Train={train_count:,} ({train_count/total_completed*100:.1f}%), "
                f"Val={val_count:,} ({val_count/total_completed*100:.1f}%), "
                f"Test={test_count:,} ({test_count/total_completed*100:.1f}%)")

    # Cache training and validation DataFrames
    train_df = train_df.cache()
    val_df = val_df.cache()
    test_df = test_df.cache()

    # 3. FEATURE SELECTION (STRICT PRE-SHIPMENT GOVERNANCE)
    cat_cols = [
        "shipping_mode",
        "market",
        "order_region",
        "customer_segment",
        "payment_type",
        "department_name"
    ]

    num_cols = [
        "days_for_shipment_scheduled",
        "order_year",
        "order_month",
        "order_day_of_week",
        "order_hour",
        "product_price",
        "order_item_quantity",
        "sales",
        "order_item_discount",
        "order_item_discount_rate",
        "order_item_total",
        "order_profit_per_order",
        "latitude",
        "longitude"
    ]

    logger.info(f"Pre-shipment Features Selected: {len(cat_cols)} Categorical, {len(num_cols)} Numerical")

    # Build Preprocessing Pipeline stages (Fitted on Train only)
    indexers = [
        StringIndexer(inputCol=col, outputCol=f"{col}_idx", handleInvalid="keep")
        for col in cat_cols
    ]

    encoder = OneHotEncoder(
        inputCols=[f"{col}_idx" for col in cat_cols],
        outputCols=[f"{col}_vec" for col in cat_cols],
        handleInvalid="keep"
    )

    feature_cols = [f"{col}_vec" for col in cat_cols] + num_cols
    assembler = VectorAssembler(inputCols=feature_cols, outputCol="features", handleInvalid="keep")

    preproc_stages = indexers + [encoder, assembler]

    # 4. MODEL TRAINING & TUNING
    models_to_train = [
        {
            "name": "Logistic Regression",
            "estimator": LogisticRegression(
                featuresCol="features", labelCol="label",
                maxIter=25, regParam=0.01, elasticNetParam=0.0
            )
        },
        {
            "name": "Random Forest",
            "estimator": RandomForestClassifier(
                featuresCol="features", labelCol="label",
                numTrees=60, maxDepth=8, seed=42
            )
        },
        {
            "name": "Gradient-Boosted Trees (GBT)",
            "estimator": GBTClassifier(
                featuresCol="features", labelCol="label",
                maxIter=30, maxDepth=5, seed=42
            )
        }
    ]

    trained_pipelines = {}
    model_evaluations = []
    confusion_matrices = []

    for m in models_to_train:
        m_name = m["name"]
        logger.info(f"--- Training Model: {m_name} ---")
        full_pipeline = Pipeline(stages=preproc_stages + [m["estimator"]])

        t0 = time.perf_counter()
        pipeline_model = full_pipeline.fit(train_df)
        train_duration = time.perf_counter() - t0
        logger.info(f"Fitted {m_name} in {train_duration:.2f}s")

        # Evaluate on Validation set
        val_preds = pipeline_model.transform(val_df)
        val_metrics = compute_detailed_metrics(val_preds, m_name)
        logger.info(f"[{m_name}] Val Set -> ROC-AUC: {val_metrics['roc_auc']:.4f}, F1: {val_metrics['f1_score']:.4f}, Acc: {val_metrics['accuracy']:.4f}")

        # Evaluate on Hold-out Test set
        t_eval0 = time.perf_counter()
        test_preds = pipeline_model.transform(test_df)
        test_metrics = compute_detailed_metrics(test_preds, m_name)
        eval_duration = time.perf_counter() - t_eval0
        logger.info(f"[{m_name}] Test Set -> ROC-AUC: {test_metrics['roc_auc']:.4f}, PR-AUC: {test_metrics['pr_auc']:.4f}, F1: {test_metrics['f1_score']:.4f}, Acc: {test_metrics['accuracy']:.4f}")

        test_metrics["training_time_sec"] = round(train_duration, 2)
        test_metrics["evaluation_time_sec"] = round(eval_duration, 2)
        test_metrics["val_roc_auc"] = val_metrics["roc_auc"]
        test_metrics["val_f1"] = val_metrics["f1_score"]

        model_evaluations.append(test_metrics)
        trained_pipelines[m_name] = pipeline_model

        confusion_matrices.append({
            "model_name": m_name,
            "true_positives": test_metrics["true_positives"],
            "false_positives": test_metrics["false_positives"],
            "true_negatives": test_metrics["true_negatives"],
            "false_negatives": test_metrics["false_negatives"]
        })

    # 5. SELECT BEST MODEL & PERSIST ARTIFACT
    # Ranked primarily by ROC-AUC and F1-Score
    sorted_models = sorted(model_evaluations, key=lambda x: (x["roc_auc"], x["f1_score"]), reverse=True)
    best_model_name = sorted_models[0]["model_name"]
    best_pipeline_model = trained_pipelines[best_model_name]
    logger.info(f"Selected Best Model: {best_model_name} (ROC-AUC: {sorted_models[0]['roc_auc']}, F1: {sorted_models[0]['f1_score']})")

    # Persist Best PipelineModel locally and to HDFS
    logger.info(f"Saving best model pipeline to local container mount: {LOCAL_MODEL_DIR}")
    best_pipeline_model.write().overwrite().save(LOCAL_MODEL_DIR)

    logger.info(f"Saving best model pipeline to HDFS: {HDFS_MODEL_DIR}")
    best_pipeline_model.write().overwrite().save(HDFS_MODEL_DIR)

    # Verify reloading
    logger.info("Testing model reload from disk...")
    reloaded_local = PipelineModel.load(LOCAL_MODEL_DIR)
    reload_test_preds = reloaded_local.transform(test_df.limit(10))
    reload_count = reload_test_preds.count()
    logger.info(f"Successfully reloaded model and generated predictions for {reload_count} sample records.")

    # 6. EXTRACT FEATURE IMPORTANCE IF TREE-BASED
    feature_importance_list = []
    if best_model_name in ["Random Forest", "Gradient-Boosted Trees (GBT)"]:
        tree_stage = best_pipeline_model.stages[-1]
        raw_importances = tree_stage.featureImportances.toArray()
        # Get metadata feature names from VectorAssembler output
        sample_transformed = best_pipeline_model.stages[len(preproc_stages)-1].transform(
            best_pipeline_model.stages[len(preproc_stages)-2].transform(
                best_pipeline_model.stages[0].transform(train_df.limit(2))
            )
        ) if False else None  # Approximate with index labels
        for idx, imp in enumerate(raw_importances):
            feature_importance_list.append({"feature_index": idx, "importance": round(float(imp), 6)})
        feature_importance_list = sorted(feature_importance_list, key=lambda x: x["importance"], reverse=True)[:20]

    # 7. EXPORT CSV AND JSON DELIVERABLES
    # CSV 1: Model Comparison
    csv_comp_path = os.path.join(OUTPUT_DIR, "step1_model_comparison.csv")
    with open(csv_comp_path, "w", encoding="utf-8") as f:
        headers = ["model_name", "accuracy", "f1_score", "precision", "recall", "roc_auc", "pr_auc", "val_roc_auc", "training_time_sec"]
        f.write(",".join(headers) + "\n")
        for m in model_evaluations:
            f.write(f"\"{m['model_name']}\",{m['accuracy']},{m['f1_score']},{m['precision']},{m['recall']},{m['roc_auc']},{m['pr_auc']},{m['val_roc_auc']},{m['training_time_sec']}\n")

    # CSV 2: Confusion Matrix
    csv_cm_path = os.path.join(OUTPUT_DIR, "step1_confusion_matrix.csv")
    with open(csv_cm_path, "w", encoding="utf-8") as f:
        headers = ["model_name", "true_positives", "false_positives", "true_negatives", "false_negatives"]
        f.write(",".join(headers) + "\n")
        for cm in confusion_matrices:
            f.write(f"\"{cm['model_name']}\",{cm['true_positives']},{cm['false_positives']},{cm['true_negatives']},{cm['false_negatives']}\n")

    # JSON: Complete Metric Dump
    summary_payload = {
        "step": 1,
        "task": "Model 1: Pre-Shipment Delivery Delay Prediction",
        "dataset": {
            "total_raw_records": total_raw,
            "canceled_orders_excluded": canceled_count,
            "valid_completed_records": total_completed,
            "chronological_split": {
                "train_records": train_count,
                "train_date_range": "2015-01-01 to 2016-12-31",
                "val_records": val_count,
                "val_date_range": "2017-01-01 to 2017-08-31",
                "test_records": test_count,
                "test_date_range": "2017-09-01 to 2018-01-31"
            }
        },
        "target_variable": "is_delayed",
        "features": {
            "categorical": cat_cols,
            "numerical": num_cols,
            "excluded_leakage_fields": [
                "delivery_status", "days_for_shipping_real", "transit_delay_days",
                "order_to_shipping_hours", "shipping_date", "late_delivery_risk",
                "order_status", "is_canceled"
            ]
        },
        "model_evaluations": model_evaluations,
        "best_model": {
            "selected_model": best_model_name,
            "local_artifact_path": LOCAL_MODEL_DIR,
            "hdfs_artifact_path": HDFS_MODEL_DIR,
            "top_feature_importances": feature_importance_list
        }
    }

    json_path = os.path.join(OUTPUT_DIR, "step1_model_metrics.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    logger.info("Model 1 training, evaluation, persistence, and reporting completed successfully.")
    spark.stop()

if __name__ == "__main__":
    run_pipeline()


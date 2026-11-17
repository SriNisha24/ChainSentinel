"""
ChainSentinel - Phase 5: Machine Learning and Predictive Analytics
Model 2: Supply-Chain Anomaly Detection Pipeline

Implements and benchmarks two unsupervised anomaly detection methods:
  Method A: Robust Statistical & Rule-Based Anomaly Detection (IQR, compound domain rules)
  Method B: Multivariate Distance-to-Centroid Anomaly Detection (K-Means on Robust/StandardScaled space)

Generates anomaly scores, multi-tier severity classifications (LOW, MEDIUM, HIGH, CRITICAL),
computes cross-method overlap and chronological stability, exports CSV/JSON deliverables,
and persists versioned model/threshold artifacts to local storage and HDFS.
"""

import os
import sys
import time
import json
import math
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType, StringType, IntegerType, BooleanType, StructType, StructField
)
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans, KMeansModel

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase5_Model2_AnomalyDetection")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
LOCAL_MODEL_DIR = "/opt/spark-data/phase5_models/anomaly_detection_v1"
HDFS_MODEL_DIR = "hdfs://namenode:8020/chainsentinel/models/phase5/anomaly_detection_v1"
OUTPUT_DIR = "/opt/spark-data/phase5_output"


def run_pipeline():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)

    spark = SparkSession.builder \
        .appName("ChainSentinel-Phase5-Model2-AnomalyDetection") \
        .config("spark.sql.shuffle.partitions", "8") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading cleaned dataset from: {HDFS_DATASET}")
    df = spark.read.parquet(HDFS_DATASET)
    total_records = df.count()
    logger.info(f"Total input transaction records: {total_records:,}")

    # 1. FEATURE SELECTION & GOVERNANCE
    # Numerical features selected for multivariate distance modeling
    mv_num_cols = [
        "product_price",
        "order_item_quantity",
        "order_item_discount",
        "order_item_discount_rate",
        "order_item_total",
        "order_profit_per_order",
        "days_for_shipment_scheduled"
    ]

    # Cast numericals
    for col in mv_num_cols:
        df = df.withColumn(col, F.col(col).cast(DoubleType()))

    # Traceability & context columns
    context_cols = [
        "order_item_id",
        "order_id",
        "order_date",
        "order_year",
        "shipping_mode",
        "market",
        "order_region",
        "department_name",
        "customer_segment",
        "sales"
    ]

    working_df = df.select(*(context_cols + mv_num_cols))

    # 2. METHOD A: ROBUST STATISTICAL ANOMALY DETECTION (IQR & DOMAIN RULES)
    logger.info("--- Executing Method A: Robust Statistical Anomaly Detection ---")
    t0_stat = time.perf_counter()

    # Pre-calculated empirical quantiles and IQR bounds on order_profit_per_order and order_item_total
    # Profit: Q25=6.91, Q75=64.79, IQR=57.88 -> Severe Loss bound: Q25 - 3*IQR = -166.73; Critical loss: -500.0
    # Total: Q25=104.38, Q75=247.40, IQR=143.02 -> High Value bound: Q75 + 3*IQR = 676.46
    # Discount: Q25=5.50, Q75=29.99, IQR=24.49 -> High Discount bound: Q75 + 3*IQR = 103.46

    PROFIT_SEVERE_LOSS = -166.73
    PROFIT_CRITICAL_LOSS = -500.00
    TOTAL_HIGH_OUTLIER = 676.46
    DISCOUNT_HIGH_OUTLIER = 103.46

    # Assign Statistical Anomaly Flags & Categories
    stat_df = working_df.withColumn(
        "stat_extreme_loss_flag",
        F.when(F.col("order_profit_per_order") <= PROFIT_SEVERE_LOSS, 1).otherwise(0)
    ).withColumn(
        "stat_high_value_flag",
        F.when(F.col("order_item_total") >= TOTAL_HIGH_OUTLIER, 1).otherwise(0)
    ).withColumn(
        "stat_excess_discount_flag",
        F.when(
            (F.col("order_item_discount") >= DISCOUNT_HIGH_OUTLIER) |
            ((F.col("order_item_discount_rate") >= 0.20) & (F.col("order_profit_per_order") < 0) & (F.col("order_item_total") >= 200.0)),
            1
        ).otherwise(0)
    ).withColumn(
        "stat_compound_inversion_flag",
        F.when(
            (F.col("order_item_quantity") >= 4) & (F.col("order_item_discount_rate") >= 0.20) & (F.col("order_profit_per_order") <= -50.0),
            1
        ).otherwise(0)
    )

    # Composite Statistical Anomaly Score and Overall Flag
    stat_df = stat_df.withColumn(
        "stat_anomaly_score",
        F.round(
            (F.col("stat_extreme_loss_flag") * 0.40) +
            (F.col("stat_excess_discount_flag") * 0.30) +
            (F.col("stat_compound_inversion_flag") * 0.20) +
            (F.col("stat_high_value_flag") * 0.10),
            3
        )
    ).withColumn(
        "method_a_flag",
        F.when(F.col("stat_anomaly_score") >= 0.20, 1).otherwise(0)
    )

    stat_duration = time.perf_counter() - t0_stat
    stat_flagged_count = stat_df.filter(F.col("method_a_flag") == 1).count()
    logger.info(f"Method A Complete in {stat_duration:.2f}s: Flagged {stat_flagged_count:,} records ({stat_flagged_count/total_records*100:.2f}%)")

    # 3. METHOD B: MULTIVARIATE DISTANCE-TO-CENTROID ANOMALY DETECTION (K-MEANS)
    logger.info("--- Executing Method B: Multivariate K-Means Distance Anomaly Detection ---")
    t0_mv = time.perf_counter()

    # Preprocessing: VectorAssembler -> StandardScaler
    assembler = VectorAssembler(inputCols=mv_num_cols, outputCol="raw_features")
    assembled_df = assembler.transform(stat_df)

    scaler = StandardScaler(inputCol="raw_features", outputCol="scaled_features", withMean=True, withStd=True)
    scaler_model = scaler.fit(assembled_df)
    scaled_df = scaler_model.transform(assembled_df)

    # Train K-Means (k=6 chosen based on commercial segmentation: apparel, fan shop, golf, high-margin, loss-leaders, luxury)
    K = 6
    kmeans = KMeans(featuresCol="scaled_features", predictionCol="cluster_id", k=K, seed=42, maxIter=25)
    kmeans_model = kmeans.fit(scaled_df)
    clustered_df = kmeans_model.transform(scaled_df)

    # Extract centroids
    centroids = kmeans_model.clusterCenters()
    logger.info(f"Trained K-Means model with K={K}. Cluster Centers computed.")

    # Compute Euclidean distance from scaled feature vector to assigned centroid
    # Broadcast centroids to executors
    centroids_bc = spark.sparkContext.broadcast([[float(val) for val in c] for c in centroids])

    def compute_distance(cluster_id, features_vec):
        if cluster_id is None or features_vec is None:
            return 0.0
        center = centroids_bc.value[int(cluster_id)]
        dist_sq = 0.0
        for i in range(len(center)):
            diff = float(features_vec[i]) - center[i]
            dist_sq += diff * diff
        return round(math.sqrt(dist_sq), 4)

    dist_udf = F.udf(compute_distance, DoubleType())
    distance_df = clustered_df.withColumn("centroid_distance", dist_udf(F.col("cluster_id"), F.col("scaled_features")))

    # Cache distance DataFrame for quantile calculations
    distance_df = distance_df.cache()

    # Compute empirical distance quantiles for thresholding
    quantiles = distance_df.approxQuantile("centroid_distance", [0.90, 0.95, 0.98, 0.99, 0.995, 0.999], 0.0005)
    d_p90, d_p95, d_p98, d_p99, d_p995, d_p999 = quantiles

    logger.info(f"Centroid Distance Quantiles: P90={d_p90:.3f}, P95={d_p95:.3f}, P98={d_p98:.3f}, P99={d_p99:.3f}, P99.5={d_p995:.3f}, P99.9={d_p999:.3f}")

    # Normalize distance to multivariate anomaly score [0.0, 1.0] using P99.9 as reference ceiling
    # dist_score = min(1.0, distance / d_p999)
    distance_df = distance_df.withColumn(
        "mv_anomaly_score",
        F.round(F.least(F.lit(1.0), F.col("centroid_distance") / F.lit(d_p999)), 4)
    ).withColumn(
        "method_b_flag",
        F.when(F.col("centroid_distance") >= d_p98, 1).otherwise(0)
    )

    mv_duration = time.perf_counter() - t0_mv
    mv_flagged_count = distance_df.filter(F.col("method_b_flag") == 1).count()
    logger.info(f"Method B Complete in {mv_duration:.2f}s: Flagged {mv_flagged_count:,} records ({mv_flagged_count/total_records*100:.2f}%) at P98 threshold")

    # 4. ENSEMBLE ANOMALY SCORE & SEVERITY CLASSIFICATION
    logger.info("--- Computing Ensemble Anomaly Scoring & Multi-Tier Severity ---")

    # Composite Ensemble Score: 50% Statistical + 50% Multivariate
    final_df = distance_df.withColumn(
        "composite_anomaly_score",
        F.round((F.col("stat_anomaly_score") * 0.50) + (F.col("mv_anomaly_score") * 0.50), 4)
    ).withColumn(
        "anomaly_flag",
        F.when((F.col("method_a_flag") == 1) | (F.col("method_b_flag") == 1), 1).otherwise(0)
    )

    # Categorical Anomaly Typology
    # Assign most prominent anomaly condition
    final_df = final_df.withColumn(
        "anomaly_category",
        F.when(F.col("order_profit_per_order") <= PROFIT_CRITICAL_LOSS, "Severe Profit Bleed")
         .when((F.col("method_a_flag") == 1) & (F.col("method_b_flag") == 1), "Compound Multi-Vector Anomaly")
         .when(F.col("stat_extreme_loss_flag") == 1, "Operational Margin Loss")
         .when(F.col("stat_excess_discount_flag") == 1, "Excessive Discount Inversion")
         .when(F.col("stat_high_value_flag") == 1, "High-Value Transaction Outlier")
         .when(F.col("method_b_flag") == 1, "Multivariate Distribution Outlier")
         .otherwise("Normal Transaction")
    )

    # Documented Severity Grading:
    # CRITICAL: Profit <= -500 OR (Method A + Method B flagged with distance >= P99.5)
    # HIGH: Composite score >= 0.50 OR centroid_distance >= P99
    # MEDIUM: Anomaly flagged by either method (stat_score >= 0.20 or distance >= P98)
    # LOW: centroid_distance between P95 and P98 (marginal deviation)
    # NORMAL: Otherwise
    final_df = final_df.withColumn(
        "severity",
        F.when((F.col("order_profit_per_order") <= PROFIT_CRITICAL_LOSS) |
               ((F.col("method_a_flag") == 1) & (F.col("centroid_distance") >= d_p995)), "CRITICAL")
         .when((F.col("composite_anomaly_score") >= 0.45) | (F.col("centroid_distance") >= d_p99), "HIGH")
         .when(F.col("anomaly_flag") == 1, "MEDIUM")
         .when(F.col("centroid_distance") >= d_p95, "LOW")
         .otherwise("NORMAL")
    )

    # Primary contributing reason explanation
    final_df = final_df.withColumn(
        "anomaly_reason",
        F.when(F.col("order_profit_per_order") <= PROFIT_CRITICAL_LOSS,
               F.concat(F.lit("Extreme negative profit: $"), F.round(F.col("order_profit_per_order"), 2)))
         .when((F.col("method_a_flag") == 1) & (F.col("method_b_flag") == 1),
               F.concat(F.lit("Joint statistical & multivariate outlier (dist="), F.round(F.col("centroid_distance"), 2), F.lit(", profit=$"), F.round(F.col("order_profit_per_order"), 2), F.lit(")")))
         .when(F.col("stat_extreme_loss_flag") == 1,
               F.concat(F.lit("Profit below IQR threshold: $"), F.round(F.col("order_profit_per_order"), 2)))
         .when(F.col("stat_excess_discount_flag") == 1,
               F.concat(F.lit("Disproportionate discount: $"), F.round(F.col("order_item_discount"), 2), F.lit(" ("), F.round(F.col("order_item_discount_rate")*100, 1), F.lit("%)")))
         .when(F.col("stat_high_value_flag") == 1,
               F.concat(F.lit("Unusually high transaction total: $"), F.round(F.col("order_item_total"), 2)))
         .when(F.col("method_b_flag") == 1,
               F.concat(F.lit("High multivariate centroid distance: "), F.round(F.col("centroid_distance"), 2)))
         .otherwise(F.lit("Within standard operational parameters"))
    )

    final_df = final_df.cache()

    # 5. AGGREGATIONS & EVALUATION METRICS
    total_flagged = final_df.filter(F.col("anomaly_flag") == 1).count()
    both_flagged = final_df.filter((F.col("method_a_flag") == 1) & (F.col("method_b_flag") == 1)).count()
    method_a_only = final_df.filter((F.col("method_a_flag") == 1) & (F.col("method_b_flag") == 0)).count()
    method_b_only = final_df.filter((F.col("method_a_flag") == 0) & (F.col("method_b_flag") == 1)).count()
    neither_flagged = final_df.filter((F.col("method_a_flag") == 0) & (F.col("method_b_flag") == 0)).count()

    jaccard_similarity = round(both_flagged / (method_a_only + method_b_only + both_flagged), 4)

    logger.info(f"Total Unique Anomalies Flagged: {total_flagged:,} ({total_flagged/total_records*100:.2f}%)")
    logger.info(f"Method Overlap -> Both: {both_flagged:,}, Method A Only: {method_a_only:,}, Method B Only: {method_b_only:,}, Jaccard: {jaccard_similarity}")

    # Severity distribution
    severity_counts = final_df.groupBy("severity").count().collect()
    severity_dict = {row["severity"]: row["count"] for row in severity_counts}
    for sev, cnt in sorted(severity_dict.items()):
        logger.info(f"Severity [{sev}]: {cnt:,} ({cnt/total_records*100:.2f}%)")

    # Category distribution
    cat_counts = final_df.groupBy("anomaly_category").count().orderBy(F.desc("count")).collect()
    category_summary_rows = [
        {"anomaly_category": r["anomaly_category"], "count": r["count"], "pct": round(r["count"]/total_records*100, 2)}
        for r in cat_counts
    ]

    # Chronological Stability: evaluate anomaly rate by calendar year
    yearly_stability = final_df.groupBy("order_year").agg(
        F.count("*").alias("total"),
        F.sum("anomaly_flag").alias("flagged"),
        F.round(F.mean("composite_anomaly_score"), 4).alias("mean_score")
    ).orderBy("order_year").collect()

    yearly_summary = [
        {
            "year": int(r["order_year"]),
            "total_records": r["total"],
            "flagged_anomalies": int(r["flagged"]),
            "anomaly_rate_pct": round(int(r["flagged"]) / r["total"] * 100, 2),
            "mean_anomaly_score": float(r["mean_score"])
        }
        for r in yearly_stability
    ]

    # 6. PERSIST MODEL ARTIFACTS
    logger.info(f"Saving KMeansModel to local mount: {LOCAL_MODEL_DIR}")
    kmeans_model.write().overwrite().save(LOCAL_MODEL_DIR)

    logger.info(f"Saving KMeansModel to HDFS: {HDFS_MODEL_DIR}")
    kmeans_model.write().overwrite().save(HDFS_MODEL_DIR)

    # Persist threshold and scaler parameters
    thresholds_payload = {
        "model_version": "anomaly_detection_v1",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_training_records": total_records,
        "features": mv_num_cols,
        "scaler": {
            "mean": [float(m) for m in scaler_model.mean.toArray()],
            "std": [float(s) for s in scaler_model.std.toArray()]
        },
        "kmeans": {
            "k": K,
            "cluster_centers": [[float(v) for v in c] for c in centroids]
        },
        "statistical_thresholds": {
            "profit_severe_loss": PROFIT_SEVERE_LOSS,
            "profit_critical_loss": PROFIT_CRITICAL_LOSS,
            "total_high_outlier": TOTAL_HIGH_OUTLIER,
            "discount_high_outlier": DISCOUNT_HIGH_OUTLIER
        },
        "multivariate_quantiles": {
            "p90": round(d_p90, 4),
            "p95": round(d_p95, 4),
            "p98": round(d_p98, 4),
            "p99": round(d_p99, 4),
            "p995": round(d_p995, 4),
            "p999": round(d_p999, 4)
        }
    }

    local_thresh_path = os.path.join(LOCAL_MODEL_DIR, "anomaly_thresholds.json")
    with open(local_thresh_path, "w", encoding="utf-8") as f:
        json.dump(thresholds_payload, f, indent=2)

    # 7. EXPORT CSV AND JSON DELIVERABLES
    logger.info("Exporting CSV and JSON deliverables...")

    # CSV 1: Category Summary
    cat_summary_csv = os.path.join(OUTPUT_DIR, "step2_anomaly_category_summary.csv")
    with open(cat_summary_csv, "w", encoding="utf-8") as f:
        f.write("anomaly_category,count,pct\n")
        for row in category_summary_rows:
            f.write(f"\"{row['anomaly_category']}\",{row['count']},{row['pct']}\n")

    # CSV 2: Method Comparison
    method_comp_csv = os.path.join(OUTPUT_DIR, "step2_anomaly_method_comparison.csv")
    with open(method_comp_csv, "w", encoding="utf-8") as f:
        f.write("detection_method,flagged_count,flagged_pct,description\n")
        f.write(f"\"Method A: Robust Statistical (IQR & Domain)\",{stat_flagged_count},{stat_flagged_count/total_records*100:.2f},\"Deterministic threshold rules over extreme profit loss, excessive discount, and transaction value outliers\"\n")
        f.write(f"\"Method B: Multivariate Distance-to-Centroid (K-Means)\",{mv_flagged_count},{mv_flagged_count/total_records*100:.2f},\"Euclidean distance to cluster centroids in 7D standardized feature space at P98 cutoff\"\n")
        f.write(f"\"Consensus Flags (Both Methods Agree)\",{both_flagged},{both_flagged/total_records*100:.2f},\"High-confidence anomalous events verified by both statistical and multivariate methods\"\n")
        f.write(f"\"Total Unique Anomalies (Ensemble Union)\",{total_flagged},{total_flagged/total_records*100:.2f},\"Comprehensive anomaly detection coverage capturing single-vector and multi-vector anomalies\"\n")

    # CSV 3: Top Flagged Records Sample (1,000 records sorted by composite anomaly score)
    # Avoid driver OOM: select top 1000 records only
    results_csv = os.path.join(OUTPUT_DIR, "step2_anomaly_results.csv")
    top_anomalies = final_df.filter(F.col("anomaly_flag") == 1) \
        .orderBy(F.desc("composite_anomaly_score"), F.desc("centroid_distance")) \
        .limit(1000) \
        .select(
            "order_item_id", "order_id", "order_date", "shipping_mode", "market",
            "department_name", "product_price", "order_item_quantity", "sales",
            "order_item_discount", "order_item_discount_rate", "order_item_total",
            "order_profit_per_order", "centroid_distance", "stat_anomaly_score",
            "mv_anomaly_score", "composite_anomaly_score", "anomaly_category",
            "severity", "anomaly_reason"
        ).collect()

    with open(results_csv, "w", encoding="utf-8") as f:
        headers = [
            "order_item_id", "order_id", "order_date", "shipping_mode", "market",
            "department_name", "product_price", "order_item_quantity", "sales",
            "order_item_discount", "order_item_discount_rate", "order_item_total",
            "order_profit_per_order", "centroid_distance", "stat_anomaly_score",
            "mv_anomaly_score", "composite_anomaly_score", "anomaly_category",
            "severity", "anomaly_reason"
        ]
        f.write(",".join(headers) + "\n")
        for row in top_anomalies:
            row_dict = row.asDict()
            vals = [f"\"{str(row_dict[h])}\"" if isinstance(row_dict[h], str) else str(row_dict[h]) for h in headers]
            f.write(",".join(vals) + "\n")

    # Summary JSON payload
    summary_payload = {
        "step": 2,
        "task": "Model 2: Supply-Chain Anomaly Detection",
        "dataset": {
            "total_records_analyzed": total_records,
            "features_used": mv_num_cols,
            "excluded_leakage_features": [
                "is_delayed", "late_delivery_risk", "delivery_status",
                "days_for_shipping_real", "transit_delay_days", "order_to_shipping_hours", "shipping_date"
            ]
        },
        "method_a_statistical": {
            "flagged_count": stat_flagged_count,
            "flagged_pct": round(stat_flagged_count / total_records * 100, 2),
            "execution_time_sec": round(stat_duration, 2),
            "thresholds": thresholds_payload["statistical_thresholds"]
        },
        "method_b_multivariate": {
            "algorithm": "K-Means Distance-to-Centroid",
            "k_clusters": K,
            "features_dimension": len(mv_num_cols),
            "flagged_count": mv_flagged_count,
            "flagged_pct": round(mv_flagged_count / total_records * 100, 2),
            "execution_time_sec": round(mv_duration, 2),
            "quantiles": thresholds_payload["multivariate_quantiles"]
        },
        "cross_method_overlap": {
            "both_flagged_consensus": both_flagged,
            "both_flagged_pct": round(both_flagged / total_records * 100, 2),
            "method_a_only": method_a_only,
            "method_b_only": method_b_only,
            "neither_flagged": neither_flagged,
            "jaccard_similarity": jaccard_similarity
        },
        "ensemble_results": {
            "total_flagged_anomalies": total_flagged,
            "total_flagged_pct": round(total_flagged / total_records * 100, 2),
            "severity_distribution": {
                sev: {"count": cnt, "pct": round(cnt / total_records * 100, 2)}
                for sev, cnt in sorted(severity_dict.items())
            },
            "category_distribution": category_summary_rows
        },
        "temporal_stability": yearly_summary,
        "artifacts": {
            "local_model_path": LOCAL_MODEL_DIR,
            "hdfs_model_path": HDFS_MODEL_DIR,
            "thresholds_file": local_thresh_path
        }
    }

    summary_json_path = os.path.join(OUTPUT_DIR, "step2_anomaly_summary.json")
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2)

    logger.info("Model 2 execution, evaluation, artifact persistence, and deliverable export complete.")
    spark.stop()


if __name__ == "__main__":
    run_pipeline()


"""
ChainSentinel - Phase 5: Machine Learning and Predictive Analytics
Model 2: Reusable Supply-Chain Anomaly Inference Script

Loads the trained KMeansModel and statistical threshold artifacts,
validates incoming transaction schema, executes dual-method anomaly scoring,
and generates multi-tier severity classifications with interpretable explanations.
"""

import sys
import os
import json
import math
import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType
)
from pyspark.ml.feature import VectorAssembler, StandardScaler, StandardScalerModel
from pyspark.ml.clustering import KMeansModel
from pyspark.ml.linalg import Vectors, DenseVector

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase5_Model2_Inference")

REQUIRED_NUMERICAL_FEATURES = [
    "product_price",
    "order_item_quantity",
    "order_item_discount",
    "order_item_discount_rate",
    "order_item_total",
    "order_profit_per_order",
    "days_for_shipment_scheduled"
]

FORBIDDEN_LEAKAGE_COLUMNS = [
    "is_delayed",
    "late_delivery_risk",
    "delivery_status",
    "days_for_shipping_real",
    "transit_delay_days",
    "order_to_shipping_hours",
    "shipping_date"
]


def validate_schema(df):
    """Validates that input DataFrame contains all required feature columns."""
    df_cols = set(df.columns)
    missing = [c for c in REQUIRED_NUMERICAL_FEATURES if c not in df_cols]
    if missing:
        raise ValueError(f"Input schema validation failed! Missing required features: {missing}")
    logger.info("Schema validation passed: All 7 required anomaly features are present.")


def create_sample_dataframe(spark):
    """Creates demonstration transactions representing diverse operational patterns."""
    data = [
        # Case 1: Catastrophic Operational Loss (Severe bleed anomaly)
        (
            "ITEM-001", "ORD-101", "2018-02-01", "First Class", "Europe", "Fan Shop",
            399.98, 2.0, 50.00, 0.06, 749.96, -650.00, 1.0
        ),
        # Case 2: Excessive Discount on High-Value Luxury Item (Margin inversion anomaly)
        (
            "ITEM-002", "ORD-102", "2018-02-02", "Standard Class", "LATAM", "Apparel",
            199.99, 4.0, 199.99, 0.25, 599.97, -180.50, 4.0
        ),
        # Case 3: Standard Healthy Transaction (Normal business pattern)
        (
            "ITEM-003", "ORD-103", "2018-02-03", "Second Class", "USCA", "Footwear",
            59.99, 1.0, 5.00, 0.08, 54.99, 24.50, 2.0
        )
    ]

    schema_fields = [
        StructField("order_item_id", StringType(), True),
        StructField("order_id", StringType(), True),
        StructField("order_date", StringType(), True),
        StructField("shipping_mode", StringType(), True),
        StructField("market", StringType(), True),
        StructField("department_name", StringType(), True)
    ] + [StructField(c, DoubleType(), True) for c in REQUIRED_NUMERICAL_FEATURES]

    return spark.createDataFrame(data, schema=StructType(schema_fields))


def main():
    parser = argparse.ArgumentParser(description="ChainSentinel Reusable Anomaly Detector")
    parser.add_argument(
        "--model-dir",
        default="/opt/spark-data/phase5_models/anomaly_detection_v1",
        help="Path to saved KMeansModel directory and anomaly_thresholds.json"
    )
    parser.add_argument(
        "--input-path",
        default=None,
        help="Optional path to input CSV or Parquet file for batch prediction"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run inference on demonstration sample transactions"
    )
    args = parser.parse_args()

    spark = SparkSession.builder \
        .appName("ChainSentinel-Phase5-Anomaly-Inference") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    # Load thresholds artifact
    thresh_file = os.path.join(args.model_dir, "anomaly_thresholds.json")
    if not os.path.exists(thresh_file):
        thresh_file = "/opt/spark-data/phase5_models/anomaly_detection_v1/anomaly_thresholds.json"

    logger.info(f"Loading anomaly thresholds from: {thresh_file}")
    with open(thresh_file, "r") as f:
        thresholds = json.load(f)

    # Statistical Thresholds
    stat_th = thresholds["statistical_thresholds"]
    PROFIT_SEVERE_LOSS = stat_th["profit_severe_loss"]
    PROFIT_CRITICAL_LOSS = stat_th["profit_critical_loss"]
    TOTAL_HIGH_OUTLIER = stat_th["total_high_outlier"]
    DISCOUNT_HIGH_OUTLIER = stat_th["discount_high_outlier"]

    # Multivariate Thresholds & Parameters
    mv_q = thresholds["multivariate_quantiles"]
    d_p95 = mv_q["p95"]
    d_p98 = mv_q["p98"]
    d_p99 = mv_q["p99"]
    d_p995 = mv_q["p995"]
    d_p999 = mv_q["p999"]

    scaler_mean = thresholds["scaler"]["mean"]
    scaler_std = thresholds["scaler"]["std"]
    cluster_centers = thresholds["kmeans"]["cluster_centers"]

    logger.info(f"Loaded {len(cluster_centers)} cluster centroids. P98 distance threshold = {d_p98:.3f}")

    # Prepare input data
    if args.input_path:
        logger.info(f"Reading input dataset from: {args.input_path}")
        if args.input_path.endswith(".parquet") or "parquet" in args.input_path:
            input_df = spark.read.parquet(args.input_path)
        else:
            input_df = spark.read.option("header", "true").option("inferSchema", "true").csv(args.input_path)
    else:
        logger.info("Generating demonstration sample transactions...")
        input_df = create_sample_dataframe(spark)

    # Validate Schema
    validate_schema(input_df)

    # Cast numericals
    for col in REQUIRED_NUMERICAL_FEATURES:
        input_df = input_df.withColumn(col, F.col(col).cast(DoubleType()))

    # Method A: Statistical Anomaly Scoring
    stat_df = input_df.withColumn(
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

    # Method B: Multivariate Standardized Distance to Centroid
    centers_bc = spark.sparkContext.broadcast(cluster_centers)
    mean_bc = spark.sparkContext.broadcast(scaler_mean)
    std_bc = spark.sparkContext.broadcast(scaler_std)

    def compute_min_centroid_distance(*features):
        scaled = []
        for i, val in enumerate(features):
            std_val = std_bc.value[i] if std_bc.value[i] != 0 else 1.0
            scaled.append((float(val) - mean_bc.value[i]) / std_val)
        
        min_dist = float("inf")
        for center in centers_bc.value:
            dist_sq = sum((scaled[j] - center[j]) ** 2 for j in range(len(scaled)))
            dist = math.sqrt(dist_sq)
            if dist < min_dist:
                min_dist = dist
        return round(min_dist, 4)

    min_dist_udf = F.udf(compute_min_centroid_distance, DoubleType())
    mv_df = stat_df.withColumn(
        "centroid_distance",
        min_dist_udf(*[F.col(c) for c in REQUIRED_NUMERICAL_FEATURES])
    ).withColumn(
        "mv_anomaly_score",
        F.round(F.least(F.lit(1.0), F.col("centroid_distance") / F.lit(d_p999)), 4)
    ).withColumn(
        "method_b_flag",
        F.when(F.col("centroid_distance") >= d_p98, 1).otherwise(0)
    )

    # Ensemble Combination & Severity Classification
    final_df = mv_df.withColumn(
        "composite_anomaly_score",
        F.round((F.col("stat_anomaly_score") * 0.50) + (F.col("mv_anomaly_score") * 0.50), 4)
    ).withColumn(
        "anomaly_flag",
        F.when((F.col("method_a_flag") == 1) | (F.col("method_b_flag") == 1), 1).otherwise(0)
    ).withColumn(
        "anomaly_category",
        F.when(F.col("order_profit_per_order") <= PROFIT_CRITICAL_LOSS, "Severe Profit Bleed")
         .when((F.col("method_a_flag") == 1) & (F.col("method_b_flag") == 1), "Compound Multi-Vector Anomaly")
         .when(F.col("stat_extreme_loss_flag") == 1, "Operational Margin Loss")
         .when(F.col("stat_excess_discount_flag") == 1, "Excessive Discount Inversion")
         .when(F.col("stat_high_value_flag") == 1, "High-Value Transaction Outlier")
         .when(F.col("method_b_flag") == 1, "Multivariate Distribution Outlier")
         .otherwise("Normal Transaction")
    ).withColumn(
        "severity",
        F.when((F.col("order_profit_per_order") <= PROFIT_CRITICAL_LOSS) |
               ((F.col("method_a_flag") == 1) & (F.col("centroid_distance") >= d_p995)), "CRITICAL")
         .when((F.col("composite_anomaly_score") >= 0.45) | (F.col("centroid_distance") >= d_p99), "HIGH")
         .when(F.col("anomaly_flag") == 1, "MEDIUM")
         .when(F.col("centroid_distance") >= d_p95, "LOW")
         .otherwise("NORMAL")
    ).withColumn(
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

    # Display results
    display_cols = [
        "order_item_id", "order_item_total", "order_profit_per_order",
        "composite_anomaly_score", "severity", "anomaly_category", "anomaly_reason"
    ]

    logger.info("===== REUSABLE ANOMALY INFERENCE RESULTS =====")
    final_df.select(display_cols).show(truncate=False)

    total_eval = final_df.count()
    flagged = final_df.filter(F.col("anomaly_flag") == 1).count()
    logger.info(f"Inference Completed: {flagged}/{total_eval} transactions flagged ({flagged/total_eval*100:.1f}%)")

    spark.stop()


if __name__ == "__main__":
    main()


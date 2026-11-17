"""
ChainSentinel - Phase 5: Machine Learning and Predictive Analytics
Model 1: Pre-Shipment Delivery Delay Inference Script

Loads the trained PipelineModel artifact from HDFS or local filesystem,
validates the input schema against required pre-shipment features,
and executes batch or single-record predictions with calibrated class probabilities.
"""

import sys
import os
import argparse
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType, IntegerType
)
from pyspark.ml import PipelineModel

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase5_Model1_Inference")

# Required feature columns for pre-shipment delay prediction
REQUIRED_CATEGORICAL = [
    "shipping_mode",
    "market",
    "order_region",
    "customer_segment",
    "payment_type",
    "department_name"
]

REQUIRED_NUMERICAL = [
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

FORBIDDEN_LEAKAGE_COLUMNS = [
    "delivery_status",
    "days_for_shipping_real",
    "transit_delay_days",
    "order_to_shipping_hours",
    "shipping_date",
    "late_delivery_risk",
    "order_status",
    "is_canceled"
]


def validate_schema(df):
    """Validates that input DataFrame contains all required feature columns."""
    df_cols = set(df.columns)
    missing = [col for col in REQUIRED_CATEGORICAL + REQUIRED_NUMERICAL if col not in df_cols]
    if missing:
        raise ValueError(
            f"Input schema validation failed! Missing required features: {missing}"
        )
    logger.info("Schema validation passed: All 20 pre-shipment feature columns are present.")


def create_sample_dataframe(spark):
    """Creates realistic sample pre-shipment orders for test inference."""
    data = [
        # Case 1: First Class shipping with tight 1-day SLA (High risk of delay)
        (
            "First Class", "LATAM", "South America", "Consumer", "DEBIT", "Apparel",
            1.0, 2018.0, 1.0, 3.0, 14.0, 129.99, 1.0, 129.99, 0.0, 0.0, 129.99, 32.50, -12.0464, -77.0428
        ),
        # Case 2: Standard Class with 4-day SLA (Low risk of delay)
        (
            "Standard Class", "Europe", "Western Europe", "Corporate", "TRANSFER", "Fan Shop",
            4.0, 2018.0, 1.0, 2.0, 10.0, 59.99, 2.0, 119.98, 5.0, 0.04, 114.98, 45.20, 48.8566, 2.3522
        ),
        # Case 3: Second Class with 2-day scheduled SLA (Moderate-to-high risk)
        (
            "Second Class", "USCA", "US Center", "Home Office", "PAYMENT", "Golf",
            2.0, 2018.0, 1.0, 5.0, 18.0, 199.99, 1.0, 199.99, 20.0, 0.10, 179.99, 58.00, 41.8781, -87.6298
        )
    ]

    cols = REQUIRED_CATEGORICAL + REQUIRED_NUMERICAL
    schema_fields = [StructField(c, StringType(), True) for c in REQUIRED_CATEGORICAL] + \
                    [StructField(c, DoubleType(), True) for c in REQUIRED_NUMERICAL]

    return spark.createDataFrame(data, schema=StructType(schema_fields))


def main():
    parser = argparse.ArgumentParser(description="ChainSentinel Pre-Shipment Delay Predictor")
    parser.add_argument(
        "--model-path",
        default="hdfs://namenode:8020/chainsentinel/models/phase5/delay_model_v1",
        help="Path to saved Spark PipelineModel artifact"
    )
    parser.add_argument(
        "--input-path",
        default=None,
        help="Optional path to input CSV or Parquet file for batch prediction"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Run inference on synthetic demonstration records"
    )
    args = parser.parse_args()

    spark = SparkSession.builder \
        .appName("ChainSentinel-Phase5-Delay-Inference") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading PipelineModel from: {args.model_path}")
    try:
        model = PipelineModel.load(args.model_path)
        logger.info("PipelineModel loaded successfully.")
    except Exception as e:
        logger.error(f"Failed to load PipelineModel from {args.model_path}: {e}")
        # Try local fallback if HDFS failed
        fallback = "/opt/spark-data/phase5_models/delay_model_v1"
        logger.info(f"Attempting fallback to local mount: {fallback}")
        model = PipelineModel.load(fallback)
        logger.info("Fallback PipelineModel loaded successfully.")

    # Prepare input data
    if args.input_path:
        logger.info(f"Reading input dataset from: {args.input_path}")
        if args.input_path.endswith(".parquet") or "parquet" in args.input_path:
            input_df = spark.read.parquet(args.input_path)
        else:
            input_df = spark.read.option("header", "true").option("inferSchema", "true").csv(args.input_path)
    else:
        logger.info("Generating demonstration sample data for inference...")
        input_df = create_sample_dataframe(spark)

    # Validate Schema
    validate_schema(input_df)

    # Ensure numerical types are properly cast
    for num_col in REQUIRED_NUMERICAL:
        input_df = input_df.withColumn(num_col, F.col(num_col).cast(DoubleType()))

    # Run inference
    logger.info("Executing prediction pipeline transformation...")
    predictions = model.transform(input_df)

    import math

    # Extract probability of class 1 (Late delivery)
    has_prob = "probability" in predictions.columns

    if has_prob:
        def extract_prob(prob_vec):
            try:
                return round(float(prob_vec[1]), 4)
            except Exception:
                return 0.5
        extract_prob_udf = F.udf(extract_prob, DoubleType())
        results_df = predictions.withColumn("delay_probability", extract_prob_udf(F.col("probability")))
    else:
        def extract_prob_from_raw(raw_vec):
            try:
                margin = float(raw_vec[1])
                return round(1.0 / (1.0 + math.exp(-2.0 * margin)), 4)
            except Exception:
                return 0.5
        extract_prob_udf = F.udf(extract_prob_from_raw, DoubleType())
        results_df = predictions.withColumn("delay_probability", extract_prob_udf(F.col("rawPrediction")))

    results_df = results_df.withColumn(
        "predicted_delay_label",
        F.when(F.col("prediction") == 1.0, "DELAYED").otherwise("ON-TIME")
    )

    # Display results
    display_cols = [
        "shipping_mode",
        "market",
        "days_for_shipment_scheduled",
        "sales",
        "predicted_delay_label",
        "delay_probability"
    ]
    
    logger.info("===== INFERENCE PREDICTION RESULTS =====")
    results_df.select(display_cols).show(truncate=False)

    total_pred = results_df.count()
    delayed_pred = results_df.filter(F.col("predicted_delay_label") == "DELAYED").count()
    logger.info(f"Inference complete: Total orders={total_pred}, Predicted Delayed={delayed_pred} ({delayed_pred/total_pred*100:.1f}%)")

    spark.stop()


if __name__ == "__main__":
    main()

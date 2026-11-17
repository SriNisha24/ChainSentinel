"""
ChainSentinel - Big Data Analytics Project
Phase 1.2: Data Cleaning and Spark ETL Pipeline

Reads raw DataCo supply chain transactions, validates schemas, eliminates redundant/empty/masked
fields, standardizes data types, derives analytical metrics, separates predictive features from
post-shipment targets, and writes clean Parquet data to HDFS.
"""

import sys
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, DoubleType, TimestampType
)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("ChainSentinelETL")


def build_spark_session():
    """Initializes and returns a configured Spark session."""
    return SparkSession.builder \
        .appName("ChainSentinel-DataCo-ETL-v1") \
        .config("spark.sql.parquet.compression.codec", "snappy") \
        .getOrCreate()


def run_pipeline():
    spark = build_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    # Local container mount input path explicitly using file:// scheme
    input_path = "file:///opt/spark-data/raw/DataCoSupplyChainDataset.csv"

    output_hdfs_path = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"

    logger.info(f"Reading raw DataCo CSV from: {input_path}")
    logger.info("Using encoding: ISO-8859-1")

    # 1. Ingest with ISO-8859-1 encoding and header
    raw_df = spark.read \
        .option("header", "true") \
        .option("encoding", "ISO-8859-1") \
        .csv(input_path)

    initial_row_count = raw_df.count()
    initial_col_count = len(raw_df.columns)
    logger.info(f"Raw dataset loaded. Rows: {initial_row_count}, Columns: {initial_col_count}")

    # 2. Column Pruning: Drop Empty, Masked PII, and Redundant Columns
    # - Empty: Product Description (100% null)
    # - Masked PII: Customer Email, Customer Password (100% 'XXXXXXXXX')
    # - Redundant duplicates:
    #     Benefit per order (identical to Order Profit Per Order)
    #     Sales per customer (identical to Order Item Total)
    #     Order Item Cardprod Id (identical to Product Card Id)
    #     Product Category Id (identical to Category Id)
    #     Order Customer Id (identical to Customer Id)
    #     Order Item Product Price (identical to Product Price)
    cols_to_drop = [
        "Product Description",
        "Customer Email",
        "Customer Password",
        "Benefit per order",
        "Sales per customer",
        "Order Item Cardprod Id",
        "Product Category Id",
        "Order Customer Id",
        "Order Item Product Price"
    ]

    pruned_df = raw_df.drop(*cols_to_drop)
    logger.info(f"Dropped {len(cols_to_drop)} redundant/empty/masked columns.")

    # 3. Column Renaming & Standardizing Data Types
    clean_df = pruned_df.select(
        # Identifiers
        F.col("Order Item Id").cast(IntegerType()).alias("order_item_id"),
        F.col("Order Id").cast(IntegerType()).alias("order_id"),
        F.col("Customer Id").cast(IntegerType()).alias("customer_id"),
        F.col("Department Id").cast(IntegerType()).alias("department_id"),
        F.col("Category Id").cast(IntegerType()).alias("category_id"),
        F.col("Product Card Id").cast(IntegerType()).alias("product_card_id"),

        # Order & Dispatch Timestamps (Parsed to TimestampType)
        F.to_timestamp(F.col("order date (DateOrders)"), "M/d/yyyy H:mm").alias("order_date"),
        F.to_timestamp(F.col("shipping date (DateOrders)"), "M/d/yyyy H:mm").alias("shipping_date"),

        # Fulfillment & SLA Metrics
        F.col("Type").alias("payment_type"),
        F.col("Shipping Mode").alias("shipping_mode"),
        F.col("Days for shipment (scheduled)").cast(IntegerType()).alias("days_for_shipment_scheduled"),
        F.col("Days for shipping (real)").cast(IntegerType()).alias("days_for_shipping_real"),
        F.col("Delivery Status").alias("delivery_status"),
        F.col("Late_delivery_risk").cast(IntegerType()).alias("late_delivery_risk"),
        F.col("Order Status").alias("order_status"),

        # Geography - Customer Origin
        F.col("Customer City").alias("customer_city"),
        F.col("Customer State").alias("customer_state"),
        F.col("Customer Country").alias("customer_country"),
        F.col("Customer Zipcode").alias("customer_zipcode"),
        F.col("Customer Street").alias("customer_street"),
        F.col("Customer Fname").alias("customer_fname"),
        F.col("Customer Lname").alias("customer_lname"),
        F.col("Customer Segment").alias("customer_segment"),
        F.col("Latitude").cast(DoubleType()).alias("latitude"),
        F.col("Longitude").cast(DoubleType()).alias("longitude"),

        # Geography - Order Destination
        F.col("Market").alias("market"),
        F.col("Order Region").alias("order_region"),
        F.col("Order Country").alias("order_country"),
        F.col("Order State").alias("order_state"),
        F.col("Order City").alias("order_city"),
        F.col("Order Zipcode").alias("order_zipcode"),

        # Product & Category Details
        F.col("Department Name").alias("department_name"),
        F.col("Category Name").alias("category_name"),
        F.col("Product Name").alias("product_name"),
        F.col("Product Price").cast(DoubleType()).alias("product_price"),
        F.col("Product Status").cast(IntegerType()).alias("product_status"),
        F.col("Product Image").alias("product_image"),

        # Financials & Order Item Economics
        F.col("Order Item Quantity").cast(IntegerType()).alias("order_item_quantity"),
        F.col("Sales").cast(DoubleType()).alias("sales"),
        F.col("Order Item Discount").cast(DoubleType()).alias("order_item_discount"),
        F.col("Order Item Discount Rate").cast(DoubleType()).alias("order_item_discount_rate"),
        F.col("Order Item Total").cast(DoubleType()).alias("order_item_total"),
        F.col("Order Profit Per Order").cast(DoubleType()).alias("order_profit_per_order"),
        F.col("Order Item Profit Ratio").cast(DoubleType()).alias("order_item_profit_ratio")
    )

    # 4. Feature Engineering: Derived Analytical Fields
    # - transit_delay_days: (real shipping days - scheduled days)
    # - is_delayed: binary flag (1 if delivery_status == 'Late delivery', else 0; prevents misclassifying canceled orders)
    # - is_canceled: binary flag indicating if delivery was canceled
    # - order temporal decomposition: order_year, order_month, order_day_of_week, order_hour
    # - order_to_shipping_hours: elapsed fulfillment duration (order placement to warehouse dispatch)
    #
    # =========================================================================
    # MACHINE LEARNING FEATURE GOVERNANCE & TARGET LEAKAGE PREVENTION:
    # -------------------------------------------------------------------------
    # The output dataset retains all 52 cleaned and derived attributes.
    # Downstream ML models for PRE-SHIPMENT RISK PREDICTION must strictly distinguish:
    #
    # A. VALID PRE-SHIPMENT PREDICTIVE FEATURES (Safe for ML Model Inputs):
    #    - Temporal: order_year, order_month, order_day_of_week, order_hour
    #    - Customer Origin: customer_city, customer_state, customer_country,
    #      customer_segment, latitude, longitude, customer_zipcode
    #    - Order Destination: market, order_region, order_country, order_state,
    #      order_city, order_zipcode
    #    - Product & Catalog: department_name, category_name, product_name,
    #      product_price, product_status, department_id, category_id, product_card_id
    #    - Order Economics & Terms: payment_type, shipping_mode, order_item_quantity,
    #      sales, order_item_discount, order_item_discount_rate, order_item_total,
    #      order_profit_per_order, order_item_profit_ratio, days_for_shipment_scheduled
    #
    # B. POST-SHIPMENT OUTCOMES & TARGETS (STRICTLY FORBIDDEN as ML Inputs - Leakage Risk):
    #    - Delivery Outcome Targets: late_delivery_risk, is_delayed, delivery_status
    #    - Order Disruption Targets: is_canceled, order_status
    #    - Post-Dispatch Actuals: days_for_shipping_real, transit_delay_days,
    #      shipping_date, order_to_shipping_hours
    # =========================================================================
    enriched_df = clean_df \
        .withColumn("transit_delay_days", F.col("days_for_shipping_real") - F.col("days_for_shipment_scheduled")) \
        .withColumn("is_delayed", F.when(F.col("delivery_status") == "Late delivery", 1).otherwise(0)) \
        .withColumn("is_canceled", F.when(F.col("delivery_status") == "Shipping canceled", 1).otherwise(0)) \
        .withColumn("order_year", F.year(F.col("order_date"))) \
        .withColumn("order_month", F.month(F.col("order_date"))) \
        .withColumn("order_day_of_week", F.dayofweek(F.col("order_date"))) \
        .withColumn("order_hour", F.hour(F.col("order_date"))) \
        .withColumn(
            "order_to_shipping_hours",
            (F.unix_timestamp("shipping_date") - F.unix_timestamp("order_date")) / 3600.0
        )

    # 5. Data Quality & Integrity Validations
    final_row_count = enriched_df.count()
    final_col_count = len(enriched_df.columns)
    unique_item_ids = enriched_df.select("order_item_id").distinct().count()

    logger.info(f"Cleaned dataset rows: {final_row_count}, columns: {final_col_count}")
    logger.info(f"Unique Order Item IDs: {unique_item_ids} (Matches total rows: {unique_item_ids == final_row_count})")

    # Delivery status summary
    status_summary = enriched_df.groupBy("delivery_status").count().collect()
    for row in status_summary:
        logger.info(f"Delivery status '{row['delivery_status']}': {row['count']} rows")

    # Category Electronics check
    elec_13 = enriched_df.filter((F.col("category_id") == 13) & (F.col("category_name") == "Electronics")).count()
    elec_37 = enriched_df.filter((F.col("category_id") == 37) & (F.col("category_name") == "Electronics")).count()
    logger.info(f"Preserved Electronics taxonomy: Cat 13 (Footwear): {elec_13}, Cat 37 (Outdoors): {elec_37}")

    # 6. Write Parquet to HDFS Destination
    logger.info(f"Writing cleaned Parquet dataset to: {output_hdfs_path}")
    enriched_df.write.mode("errorifexists").parquet(output_hdfs_path)
    logger.info("Successfully wrote clean Parquet dataset to HDFS!")

    # 7. Verification: Read back from HDFS
    logger.info("Verifying Parquet dataset by reading back from HDFS...")
    verify_df = spark.read.parquet(output_hdfs_path)
    verify_count = verify_df.count()
    logger.info(f"Verification successful: {verify_count} rows read back from HDFS.")

    spark.stop()
    return {
        "initial_rows": initial_row_count,
        "final_rows": final_row_count,
        "initial_cols": initial_col_count,
        "final_cols": final_col_count,
        "unique_order_items": unique_item_ids,
        "verified_read_rows": verify_count
    }


if __name__ == "__main__":
    run_pipeline()


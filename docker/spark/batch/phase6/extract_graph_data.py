"""
ChainSentinel - Phase 6: Supply-Chain Graph Construction
Step 4: Distributed Graph Data Extraction via Apache Spark

Extracts multi-echelon node entities and relational edges from the cleaned
DataCo dataset in HDFS, applies customer anonymization (zero PII exposure),
computes node/edge attributes (volumes, revenues, delay counts), and exports
normalized node and edge tables using native Spark CSV export.

Source Dataset:
    hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1
Output Path:
    /opt/spark-data/phase6/ (mapped to host E:\\BDA\\ChainSentinel\\data\\phase6\\)
"""

import os
import sys
import glob
import shutil
import logging
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("Phase6_GraphExtraction")

HDFS_DATASET = "hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1"
OUTPUT_DIR = "/opt/spark-data/phase6"

def save_single_csv(df, target_filename):
    """Saves a Spark DataFrame as a single CSV file without Pandas dependency."""
    temp_dir = os.path.join(OUTPUT_DIR, f"temp_{os.path.basename(target_filename)}")
    df.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"file://{temp_dir}")
    
    # Locate part file
    part_files = glob.glob(os.path.join(temp_dir, "part-*.csv"))
    if part_files:
        dest_file = os.path.join(OUTPUT_DIR, target_filename)
        shutil.copyfile(part_files[0], dest_file)
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Successfully saved: {dest_file}")
    else:
        logger.error(f"Failed to find part file in {temp_dir}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    spark = SparkSession.builder \
        .appName("ChainSentinel-Phase6-GraphExtraction") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    spark.sparkContext.setLogLevel("WARN")

    logger.info(f"Loading cleaned dataset from: {HDFS_DATASET}")
    df = spark.read.parquet(HDFS_DATASET)
    total_records = df.count()
    logger.info(f"Loaded {total_records:,} dataset records.")

    # =========================================================================
    # 1. NODE EXTRACTION (WITH PII SANITIZATION)
    # =========================================================================
    logger.info("Extracting node entities...")

    # Customer Nodes (Strictly No Names, Emails, Passwords, or Street Addresses)
    cust_df = df.groupBy("customer_id").agg(
        F.first("customer_segment").alias("segment"),
        F.first("customer_city").alias("city"),
        F.first("customer_state").alias("state"),
        F.first("customer_country").alias("country"),
        F.countDistinct("order_id").alias("total_orders"),
        F.round(F.sum("order_item_total"), 2).alias("total_spend"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.countDistinct(F.when(F.col("is_delayed") == 1, F.col("order_id"))).alias("delayed_orders")
    ).withColumn("node_id", F.concat(F.lit("CUST_"), F.col("customer_id").cast("string"))) \
     .withColumn("node_type", F.lit("Customer")) \
     .withColumn("label", F.col("node_id"))

    # Order Nodes
    order_df = df.groupBy("order_id").agg(
        F.first("order_date").alias("order_date"),
        F.first("order_status").alias("order_status"),
        F.first("shipping_mode").alias("shipping_mode"),
        F.first("market").alias("market"),
        F.first("order_region").alias("region"),
        F.first("order_country").alias("country"),
        F.round(F.sum("order_item_total"), 2).alias("order_total"),
        F.round(F.sum("order_profit_per_order"), 2).alias("order_profit"),
        F.max("is_delayed").alias("is_delayed"),
        F.max("late_delivery_risk").alias("late_delivery_risk"),
        F.count("order_item_id").alias("item_count")
    ).withColumn("node_id", F.concat(F.lit("ORD_"), F.col("order_id").cast("string"))) \
     .withColumn("node_type", F.lit("Order")) \
     .withColumn("label", F.col("node_id"))

    # Product Nodes
    prod_df = df.groupBy("product_card_id").agg(
        F.first("product_name").alias("product_name"),
        F.first("category_id").alias("category_id"),
        F.first("department_id").alias("department_id"),
        F.round(F.first("product_price"), 2).alias("price"),
        F.count("order_item_id").alias("units_ordered"),
        F.countDistinct("order_id").alias("order_count"),
        F.round(F.sum("order_item_total"), 2).alias("total_revenue"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.sum("is_delayed").alias("delay_count")
    ).withColumn("node_id", F.concat(F.lit("PROD_"), F.col("product_card_id").cast("string"))) \
     .withColumn("node_type", F.lit("Product")) \
     .withColumn("label", F.col("product_name"))

    # Category Nodes
    cat_df = df.groupBy("category_id").agg(
        F.first("category_name").alias("category_name"),
        F.first("department_id").alias("department_id"),
        F.countDistinct("product_card_id").alias("distinct_products"),
        F.countDistinct("order_id").alias("order_count"),
        F.round(F.sum("order_item_total"), 2).alias("total_revenue"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit")
    ).withColumn("node_id", F.concat(F.lit("CAT_"), F.col("category_id").cast("string"))) \
     .withColumn("node_type", F.lit("Category")) \
     .withColumn("label", F.col("category_name"))

    # Department Nodes
    dept_df = df.groupBy("department_id").agg(
        F.first("department_name").alias("department_name"),
        F.countDistinct("category_id").alias("distinct_categories"),
        F.countDistinct("product_card_id").alias("distinct_products"),
        F.countDistinct("order_id").alias("order_count"),
        F.round(F.sum("order_item_total"), 2).alias("total_revenue"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit")
    ).withColumn("node_id", F.concat(F.lit("DEPT_"), F.col("department_id").cast("string"))) \
     .withColumn("node_type", F.lit("Department")) \
     .withColumn("label", F.col("department_name"))

    # Market Nodes
    mkt_df = df.groupBy("market").agg(
        F.countDistinct("order_id").alias("order_count"),
        F.countDistinct("order_region").alias("region_count"),
        F.countDistinct("order_country").alias("country_count"),
        F.round(F.sum("order_item_total"), 2).alias("total_revenue"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.countDistinct(F.when(F.col("is_delayed") == 1, F.col("order_id"))).alias("delayed_orders")
    ).withColumn("node_id", F.concat(F.lit("MKT_"), F.regexp_replace(F.col("market"), " ", "_"))) \
     .withColumn("node_type", F.lit("Market")) \
     .withColumn("label", F.col("market"))

    # Region Nodes
    reg_df = df.groupBy("order_region").agg(
        F.first("market").alias("market"),
        F.countDistinct("order_country").alias("country_count"),
        F.countDistinct("order_id").alias("order_count"),
        F.round(F.sum("order_item_total"), 2).alias("total_revenue"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.countDistinct(F.when(F.col("is_delayed") == 1, F.col("order_id"))).alias("delayed_orders")
    ).withColumn("node_id", F.concat(F.lit("REG_"), F.regexp_replace(F.col("order_region"), " ", "_"))) \
     .withColumn("node_type", F.lit("Region")) \
     .withColumn("label", F.col("order_region"))

    # Country Nodes
    country_df = df.groupBy("order_country").agg(
        F.first("order_region").alias("region"),
        F.first("market").alias("market"),
        F.countDistinct("order_id").alias("order_count"),
        F.round(F.sum("order_item_total"), 2).alias("total_revenue"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.countDistinct(F.when(F.col("is_delayed") == 1, F.col("order_id"))).alias("delayed_orders")
    ).withColumn("node_id", F.concat(F.lit("CTRY_"), F.regexp_replace(F.col("order_country"), " ", "_"))) \
     .withColumn("node_type", F.lit("Country")) \
     .withColumn("label", F.col("order_country"))

    # Shipping Mode Nodes
    ship_df = df.groupBy("shipping_mode").agg(
        F.countDistinct("order_id").alias("order_count"),
        F.round(F.sum("order_item_total"), 2).alias("total_revenue"),
        F.round(F.sum("order_profit_per_order"), 2).alias("total_profit"),
        F.countDistinct(F.when(F.col("is_delayed") == 1, F.col("order_id"))).alias("delayed_orders")
    ).withColumn("node_id", F.concat(F.lit("SHIP_"), F.regexp_replace(F.col("shipping_mode"), " ", "_"))) \
     .withColumn("node_type", F.lit("Shipping_Mode")) \
     .withColumn("label", F.col("shipping_mode"))

    # Unified Node Table
    u_cust = cust_df.select("node_id", "node_type", "label", F.col("total_orders").alias("order_count"), "total_spend", "total_profit", "delayed_orders")
    u_ord = order_df.select("node_id", "node_type", "label", F.lit(1).alias("order_count"), F.col("order_total").alias("total_spend"), F.col("order_profit").alias("total_profit"), F.col("is_delayed").alias("delayed_orders"))
    u_prod = prod_df.select("node_id", "node_type", "label", "order_count", F.col("total_revenue").alias("total_spend"), "total_profit", F.col("delay_count").alias("delayed_orders"))
    u_cat = cat_df.select("node_id", "node_type", "label", "order_count", F.col("total_revenue").alias("total_spend"), "total_profit", F.lit(0).alias("delayed_orders"))
    u_dept = dept_df.select("node_id", "node_type", "label", "order_count", F.col("total_revenue").alias("total_spend"), "total_profit", F.lit(0).alias("delayed_orders"))
    u_mkt = mkt_df.select("node_id", "node_type", "label", "order_count", F.col("total_revenue").alias("total_spend"), "total_profit", "delayed_orders")
    u_reg = reg_df.select("node_id", "node_type", "label", "order_count", F.col("total_revenue").alias("total_spend"), "total_profit", "delayed_orders")
    u_ctry = country_df.select("node_id", "node_type", "label", "order_count", F.col("total_revenue").alias("total_spend"), "total_profit", "delayed_orders")
    u_ship = ship_df.select("node_id", "node_type", "label", "order_count", F.col("total_revenue").alias("total_spend"), "total_profit", "delayed_orders")

    all_nodes_df = u_cust.unionByName(u_ord) \
                         .unionByName(u_prod) \
                         .unionByName(u_cat) \
                         .unionByName(u_dept) \
                         .unionByName(u_mkt) \
                         .unionByName(u_reg) \
                         .unionByName(u_ctry) \
                         .unionByName(u_ship)

    total_nodes_count = all_nodes_df.count()
    logger.info(f"Total unified nodes: {total_nodes_count:,}")

    # =========================================================================
    # 2. EDGE EXTRACTION
    # =========================================================================
    logger.info("Extracting relational edges...")

    # Edge 1: Customer -> Order (PLACES)
    e_cust_ord = df.select("customer_id", "order_id").distinct() \
                   .withColumn("source", F.concat(F.lit("CUST_"), F.col("customer_id").cast("string"))) \
                   .withColumn("target", F.concat(F.lit("ORD_"), F.col("order_id").cast("string"))) \
                   .withColumn("relationship", F.lit("PLACES")) \
                   .withColumn("weight", F.lit(1.0)) \
                   .withColumn("volume", F.lit(1)) \
                   .withColumn("revenue", F.lit(0.0)) \
                   .select("source", "target", "relationship", "weight", "volume", "revenue")

    # Edge 2: Order -> Product (CONTAINS)
    e_ord_prod = df.groupBy("order_id", "product_card_id").agg(
        F.count("order_item_id").alias("item_qty"),
        F.round(F.sum("order_item_total"), 2).alias("item_revenue")
    ).withColumn("source", F.concat(F.lit("ORD_"), F.col("order_id").cast("string"))) \
     .withColumn("target", F.concat(F.lit("PROD_"), F.col("product_card_id").cast("string"))) \
     .withColumn("relationship", F.lit("CONTAINS")) \
     .withColumn("weight", F.col("item_qty").cast("double")) \
     .withColumn("volume", F.col("item_qty")) \
     .withColumn("revenue", F.col("item_revenue")) \
     .select("source", "target", "relationship", "weight", "volume", "revenue")

    # Edge 3: Product -> Category (BELONGS_TO)
    e_prod_cat = df.select("product_card_id", "category_id").distinct() \
                   .withColumn("source", F.concat(F.lit("PROD_"), F.col("product_card_id").cast("string"))) \
                   .withColumn("target", F.concat(F.lit("CAT_"), F.col("category_id").cast("string"))) \
                   .withColumn("relationship", F.lit("BELONGS_TO")) \
                   .withColumn("weight", F.lit(1.0)) \
                   .withColumn("volume", F.lit(1)) \
                   .withColumn("revenue", F.lit(0.0)) \
                   .select("source", "target", "relationship", "weight", "volume", "revenue")

    # Edge 4: Category -> Department (SUB_UNIT_OF)
    e_cat_dept = df.select("category_id", "department_id").distinct() \
                   .withColumn("source", F.concat(F.lit("CAT_"), F.col("category_id").cast("string"))) \
                   .withColumn("target", F.concat(F.lit("DEPT_"), F.col("department_id").cast("string"))) \
                   .withColumn("relationship", F.lit("SUB_UNIT_OF")) \
                   .withColumn("weight", F.lit(1.0)) \
                   .withColumn("volume", F.lit(1)) \
                   .withColumn("revenue", F.lit(0.0)) \
                   .select("source", "target", "relationship", "weight", "volume", "revenue")

    # Edge 5: Order -> Region (DELIVERS_TO)
    e_ord_reg = df.select("order_id", "order_region").distinct() \
                  .withColumn("source", F.concat(F.lit("ORD_"), F.col("order_id").cast("string"))) \
                  .withColumn("target", F.concat(F.lit("REG_"), F.regexp_replace(F.col("order_region"), " ", "_"))) \
                  .withColumn("relationship", F.lit("DELIVERS_TO")) \
                  .withColumn("weight", F.lit(1.0)) \
                  .withColumn("volume", F.lit(1)) \
                  .withColumn("revenue", F.lit(0.0)) \
                  .select("source", "target", "relationship", "weight", "volume", "revenue")

    # Edge 6: Region -> Market (LOCATED_IN)
    e_reg_mkt = df.select("order_region", "market").distinct() \
                  .withColumn("source", F.concat(F.lit("REG_"), F.regexp_replace(F.col("order_region"), " ", "_"))) \
                  .withColumn("target", F.concat(F.lit("MKT_"), F.regexp_replace(F.col("market"), " ", "_"))) \
                  .withColumn("relationship", F.lit("LOCATED_IN")) \
                  .withColumn("weight", F.lit(1.0)) \
                  .withColumn("volume", F.lit(1)) \
                  .withColumn("revenue", F.lit(0.0)) \
                  .select("source", "target", "relationship", "weight", "volume", "revenue")

    # Edge 7: Order -> Shipping Mode (FULFILLED_BY)
    e_ord_ship = df.select("order_id", "shipping_mode").distinct() \
                   .withColumn("source", F.concat(F.lit("ORD_"), F.col("order_id").cast("string"))) \
                   .withColumn("target", F.concat(F.lit("SHIP_"), F.regexp_replace(F.col("shipping_mode"), " ", "_"))) \
                   .withColumn("relationship", F.lit("FULFILLED_BY")) \
                   .withColumn("weight", F.lit(1.0)) \
                   .withColumn("volume", F.lit(1)) \
                   .withColumn("revenue", F.lit(0.0)) \
                   .select("source", "target", "relationship", "weight", "volume", "revenue")

    all_edges_df = e_cust_ord.unionByName(e_ord_prod) \
                             .unionByName(e_prod_cat) \
                             .unionByName(e_cat_dept) \
                             .unionByName(e_ord_reg) \
                             .unionByName(e_reg_mkt) \
                             .unionByName(e_ord_ship)

    total_edges_count = all_edges_df.count()
    logger.info(f"Total unified edges: {total_edges_count:,}")

    # =========================================================================
    # 3. EXPORT CLEAN NODE AND EDGE CSVs NATIVELY
    # =========================================================================
    logger.info("Exporting graph_nodes.csv and graph_edges.csv...")
    save_single_csv(all_nodes_df, "graph_nodes.csv")
    save_single_csv(all_edges_df, "graph_edges.csv")

    # =========================================================================
    # 4. EXPORT OPERATIONAL BACKBONE GRAPH (MACRO NETWORK)
    # =========================================================================
    logger.info("Computing operational backbone flows (Product <-> Region <-> Mode)...")
    prod_reg_df = df.groupBy("product_card_id", "order_region").agg(
        F.countDistinct("order_id").alias("order_count"),
        F.round(F.sum("order_item_total"), 2).alias("total_revenue")
    ).withColumn("source", F.concat(F.lit("PROD_"), F.col("product_card_id").cast("string"))) \
     .withColumn("target", F.concat(F.lit("REG_"), F.regexp_replace(F.col("order_region"), " ", "_"))) \
     .withColumn("relationship", F.lit("SUPPLIES_REGION")) \
     .withColumn("weight", F.col("order_count").cast("double")) \
     .withColumn("volume", F.col("order_count")) \
     .withColumn("revenue", F.col("total_revenue")) \
     .select("source", "target", "relationship", "weight", "volume", "revenue")

    backbone_edges_df = e_prod_cat.unionByName(e_cat_dept) \
                                  .unionByName(e_reg_mkt) \
                                  .unionByName(prod_reg_df)

    save_single_csv(backbone_edges_df, "graph_backbone_edges.csv")

    spark.stop()
    logger.info("Extraction pipeline finished successfully.")

if __name__ == "__main__":
    main()

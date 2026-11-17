"""
ChainSentinel — Phase 7 Real-Time Disruption Event Ingestion Engine
Script: docker/spark/streaming/disruption_ingestion.py

This module constitutes the production streaming ingestion engine for ChainSentinel.
It reads real-time disruption telemetry from Kafka, performs rigorous schema validation,
preserves transport-level Kafka metadata, separates clean events from malformed/invalid records,
applies bounded watermarking and deduplication, and streams verified incidents to HDFS.

NOTE: Do not launch this application without explicit core-allocation authorization.
"""

import sys
import os
import logging

# Set up structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ChainSentinel.DisruptionIngestion")

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp
)
from pyspark.sql.types import (
    StringType
)

# Import explicit schema and validation logic
from disruption_event_schema import (
    get_disruption_spark_schema,
    add_spark_validation_columns
)


# ==============================================================================
# PIPELINE CONFIGURATION CONSTANTS
# ==============================================================================

KAFKA_BOOTSTRAP_SERVERS = "chainsentinel-kafka:29092"
KAFKA_TOPIC = "disruption-events"

# Primary Authorized Storage Endpoints
HDFS_VALID_OUTPUT_PATH = "hdfs://namenode:8020/chainsentinel/streaming/disruption_ingestion"
HDFS_VALID_CHECKPOINT_PATH = "hdfs://namenode:8020/chainsentinel/checkpoints/disruption_ingestion_v2"

# Secondary Quarantine Endpoints (Pending Explicit Authorization)
HDFS_QUARANTINE_OUTPUT_PATH = "hdfs://namenode:8020/chainsentinel/streaming/disruptions/quarantine"
HDFS_QUARANTINE_CHECKPOINT_PATH = "hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events_quarantine"

# Watermark & Trigger Settings
WATERMARK_DELAY_THRESHOLD = "2 hours"
STREAM_TRIGGER_INTERVAL = "10 seconds"


# ==============================================================================
# SPARK SESSION CREATION
# ==============================================================================

def create_spark_session(app_name: str = "ChainSentinel-Disruption-Ingestion", max_cores: int = 4) -> SparkSession:
    """
    Initializes a resilient SparkSession configured with explicit core bounds
    to prevent worker starvation on standalone clusters.
    """
    logger.info(f"Initializing SparkSession: '{app_name}' (max_cores={max_cores})")
    
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.cores.max", str(max_cores)) \
        .config("spark.executor.cores", "2") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")
    return spark


# ==============================================================================
# INGESTION & TRANSFORMATION LOGIC
# ==============================================================================

def build_disruption_pipeline(spark: SparkSession, enable_quarantine: bool = False):
    """
    Constructs the end-to-end Structured Streaming query graph.
    
    Architecture Note on Multi-Sink Streaming:
    Spark Structured Streaming binds exactly one sink and one checkpoint per StreamingQuery.
    To support both clean ingestion and quarantine:
    1. Primary Query: filters `is_valid == True` and writes to HDFS_VALID_OUTPUT_PATH
       using HDFS_VALID_CHECKPOINT_PATH.
    2. Quarantine Query: filters `is_valid == False` and writes to HDFS_QUARANTINE_OUTPUT_PATH
       using HDFS_QUARANTINE_CHECKPOINT_PATH (activated only upon explicit authorization).
    """
    logger.info(f"Subscribing to Kafka topic: {KAFKA_TOPIC} at {KAFKA_BOOTSTRAP_SERVERS}")
    
    # 1. Read raw Kafka stream
    raw_kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("failOnDataLoss", "false") \
        .load()

    # 2. Extract payload and preserve Kafka metadata
    schema = get_disruption_spark_schema()
    
    parsed_stream_df = raw_kafka_df.select(
        col("partition").alias("kafka_partition"),
        col("offset").alias("kafka_offset"),
        col("timestamp").alias("kafka_timestamp"),
        col("value").cast(StringType()).alias("raw_payload"),
        from_json(col("value").cast(StringType()), schema).alias("event")
    )

    # 3. Flatten event attributes alongside transport metadata
    unpacked_df = parsed_stream_df.select(
        col("event.*"),
        col("kafka_partition"),
        col("kafka_offset"),
        col("kafka_timestamp"),
        col("raw_payload")
    )

    # 4. Apply rigorous Spark SQL validation
    validated_df = add_spark_validation_columns(unpacked_df, raw_payload_col="raw_payload")

    # 5. Add system processing timestamp
    enriched_df = validated_df.withColumn(
        "ingestion_timestamp", current_timestamp()
    )

    # 6. Apply Watermarking for bounded-state deduplication
    # Deduplication strategy: composite key [event_id, event_timestamp]
    # Distinguishes duplicate transport records from valid incident updates
    watermarked_df = enriched_df \
        .withWatermark("event_timestamp", WATERMARK_DELAY_THRESHOLD) \
        .dropDuplicates(["event_id", "event_timestamp"])

    # 7. Split clean records from invalid/malformed records
    valid_events_df = watermarked_df.filter(col("is_valid") == True).drop("raw_payload", "validation_errors")
    
    # 8. Start Primary Query (Valid Events to Authorized HDFS Sink)
    logger.info(f"Configuring Primary Valid Event Stream -> {HDFS_VALID_OUTPUT_PATH}")
    valid_query = valid_events_df.writeStream \
        .format("json") \
        .outputMode("append") \
        .trigger(processingTime=STREAM_TRIGGER_INTERVAL) \
        .option("path", HDFS_VALID_OUTPUT_PATH) \
        .option("checkpointLocation", HDFS_VALID_CHECKPOINT_PATH) \
        .queryName("ValidDisruptionsWriter") \
        .start()

    quarantine_query = None
    if enable_quarantine:
        logger.info(f"Configuring Quarantine Event Stream -> {HDFS_QUARANTINE_OUTPUT_PATH}")
        invalid_events_df = watermarked_df.filter(col("is_valid") == False)
        quarantine_query = invalid_events_df.writeStream \
            .format("json") \
            .outputMode("append") \
            .trigger(processingTime=STREAM_TRIGGER_INTERVAL) \
            .option("path", HDFS_QUARANTINE_OUTPUT_PATH) \
            .option("checkpointLocation", HDFS_QUARANTINE_CHECKPOINT_PATH) \
            .queryName("QuarantineDisruptionsWriter") \
            .start()
    else:
        logger.info("Quarantine stream is disabled (awaiting user infrastructure authorization).")

    return valid_query, quarantine_query


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

if __name__ == "__main__":
    logger.info("Starting ChainSentinel Disruption Ingestion Engine...")
    
    # Check command-line flags
    enable_quar = "--enable-quarantine" in sys.argv
    
    spark_session = create_spark_session()
    managed_queries = []
    try:
        primary_q, quar_q = build_disruption_pipeline(spark_session, enable_quarantine=enable_quar)
        managed_queries = [q for q in [primary_q, quar_q] if q is not None]
        logger.info(f"Monitoring {len(managed_queries)} active managed stream(s)...")
        
        # Concurrent query monitoring loop:
        # Replaces sequential blocking awaitTermination() with active monitoring of both queries.
        # Detects failure, exception, or termination on EITHER the primary or quarantine stream.
        while any(q.isActive for q in managed_queries):
            # Await any stream termination with a 2-second timeout to keep the inspection loop responsive
            spark_session.streams.awaitAnyTermination(timeout=2)
            
            # Check individual managed queries for failures or exceptions
            has_failure = False
            for q in managed_queries:
                exc = q.exception()
                if exc is not None:
                    logger.error(f"Managed query '{q.name}' (id: {q.id}) terminated with exception: {exc}")
                    has_failure = True
                elif not q.isActive:
                    logger.warning(f"Managed query '{q.name}' (id: {q.id}) stopped unexpectedly.")
                    has_failure = True
            
            if has_failure:
                break
                
        # Inspect and raise if any managed query failed
        for q in managed_queries:
            if q.exception() is not None:
                raise RuntimeError(f"Streaming query '{q.name}' failed: {q.exception()}")
            
    except KeyboardInterrupt:
        logger.info("Shutdown signal (SIGINT/SIGTERM) received. Terminating managed streams cleanly...")
    except Exception as e:
        logger.error(f"Fatal error in disruption ingestion engine: {e}", exc_info=True)
        # Note on Fault Recovery & Restart Policies:
        # Logging and detecting an exception alerts the system to failure, but does NOT provide
        # automatic in-flight state recovery. Automatic fault tolerance across task/driver failures
        # requires an external supervisor / orchestrator (e.g. container restart policy, Kubernetes
        # pod restart, or workflow scheduler) to relaunch the Spark application from its persistent HDFS checkpoints.
        sys.exit(1)
    finally:
        # Stop ONLY the queries managed by this script, avoiding stopping unrelated Spark streaming queries
        for q in managed_queries:
            if q.isActive:
                logger.info(f"Stopping managed query '{q.name}' (id: {q.id})...")
                try:
                    q.stop()
                except Exception as stop_err:
                    logger.warning(f"Error stopping query '{q.name}': {stop_err}")
                    
        spark_session.stop()
        logger.info("SparkSession stopped cleanly.")


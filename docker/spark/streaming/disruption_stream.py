from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType,
    IntegerType, DoubleType
)

# 1. Create Spark session with strict 4 cores allocation
spark = SparkSession.builder \
    .appName("ChainSentinel-Disruption-Streaming") \
    .config("spark.cores.max", "4") \
    .config("spark.executor.cores", "2") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# 2. Define Disruption Event Schema
# Supports all Phase 7 required attributes plus optional fields
disruption_schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("location", StringType(), True),
    StructField("timestamp", StringType(), True),
    StructField("impact_radius_km", DoubleType(), True),
    StructField("affected_mode", StringType(), True),
    StructField("source_confidence", DoubleType(), True),
    StructField("severity", StringType(), True),
    StructField("duration_hours", IntegerType(), True),
    StructField("description", StringType(), True)
])

# 3. Read events continuously from Kafka dedicated topic
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "chainsentinel-kafka:29092") \
    .option("subscribe", "disruption-events") \
    .option("startingOffsets", "earliest") \
    .option("failOnDataLoss", "false") \
    .load()

# 4. Parse incoming JSON value
raw_json_df = kafka_df.select(
    from_json(col("value").cast("string"), disruption_schema).alias("event"),
    col("value").cast("string").alias("raw_payload")
)

# 5. Extract fields and validate mandatory attributes
unpacked_df = raw_json_df.select("event.*", "raw_payload")

# Validation predicate: mandatory fields must be non-null and non-empty
valid_condition = (
    col("event_id").isNotNull() & (col("event_id") != "") &
    col("event_type").isNotNull() & (col("event_type") != "") &
    col("location").isNotNull() & (col("location") != "") &
    col("timestamp").isNotNull() &
    col("impact_radius_km").isNotNull() &
    col("affected_mode").isNotNull() &
    col("source_confidence").isNotNull()
)

valid_events_df = unpacked_df.filter(valid_condition).drop("raw_payload")

# 6. Append processing metadata
processed_df = valid_events_df.withColumn(
    "processed_at", current_timestamp()
)

# 7. Write valid disruption events continuously to isolated HDFS sink
query = processed_df.writeStream \
    .format("json") \
    .option(
        "path",
        "hdfs://namenode:8020/chainsentinel/streaming/disruptions"
    ) \
    .option(
        "checkpointLocation",
        "hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events"
    ) \
    .outputMode("append") \
    .start()

print("ChainSentinel Disruption Streaming Pipeline started successfully!")

query.awaitTermination()


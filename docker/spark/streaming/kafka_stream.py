from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, from_json, current_timestamp
)
from pyspark.sql.types import (
    StructType, StructField, StringType,
    IntegerType
)

# 1. Create Spark session with max 4 cores allocation
spark = SparkSession.builder \
    .appName("ChainSentinel-Kafka-Streaming") \
    .config("spark.cores.max", "4") \
    .config("spark.executor.cores", "2") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

# 2. Define incoming disruption event structure
schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("location", StringType(), True),
    StructField("severity", StringType(), True),
    StructField("duration_hours", IntegerType(), True),
    StructField("timestamp", StringType(), True)
])

# 3. Read events continuously from Kafka
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "chainsentinel-kafka:29092") \
    .option("subscribe", "supply-chain-events") \
    .option("startingOffsets", "latest") \
    .load()

# 4. Convert Kafka message value from bytes to JSON
events_df = kafka_df.select(
    from_json(
        col("value").cast("string"), schema
    ).alias("event")
).select("event.*")

# 5. Add processing timestamp
processed_df = events_df.withColumn(
    "processed_at", current_timestamp()
)

# 6. Write processed events continuously to HDFS
query = processed_df.writeStream \
    .format("json") \
    .option(
        "path",
        "hdfs://namenode:8020/chainsentinel/streaming/events"
    ) \
    .option(
        "checkpointLocation",
        "hdfs://namenode:8020/chainsentinel/checkpoints/kafka_events"
    ) \
    .outputMode("append") \
    .start()

print("ChainSentinel Kafka streaming pipeline started!")

query.awaitTermination()

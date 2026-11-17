from pyspark.sql import SparkSession
from pyspark.sql.functions import col, avg, count, when

# Create Spark session
spark = SparkSession.builder \
    .appName("ChainSentinel-Batch-Test") \
    .getOrCreate()

# Sample supply-chain shipment data
data = [
    ("S001", "Chennai", 3, 2),
    ("S002", "Mumbai", 5, 5),
    ("S003", "Delhi", 7, 4),
    ("S004", "Chennai", 6, 6),
    ("S005", "Mumbai", 4, 3),
    ("S006", "Delhi", 8, 5)
]

columns = [
    "shipment_id",
    "destination",
    "actual_delivery_days",
    "scheduled_delivery_days"
]

# Create Spark DataFrame
df = spark.createDataFrame(data, columns)

print("\n--- SUPPLY CHAIN SHIPMENT DATA ---")
df.show()

# Calculate delivery statistics
print("\n--- DELIVERY STATISTICS ---")

df.select(
    count("*").alias("total_shipments"),
    avg("actual_delivery_days").alias("average_delivery_days"),
    count(
        when(
            col("actual_delivery_days") >
            col("scheduled_delivery_days"), 1
        )
    ).alias("delayed_shipments")
).show()

# Stop Spark session
spark.stop()


from pyspark.sql import SparkSession

# Start Spark
spark = SparkSession.builder \
    .appName("ChainSentinel-HDFS-Test") \
    .getOrCreate()

# Sample shipment data
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

df = spark.createDataFrame(data, columns)

# HDFS destination
hdfs_path = "hdfs://namenode:8020/chainsentinel/processed/shipments_batch"

# Write data into HDFS
df.write.mode("overwrite").option("header", True).csv(hdfs_path)

print("SUCCESS: Data written to HDFS!")

# Read data back from HDFS
result = spark.read.option("header", True).csv(hdfs_path)

print("Reading data back from HDFS:")
result.show()

spark.stop()

# CHAINSENTINEL — PHASE 7: REAL-TIME DISRUPTION INGESTION
## Phase 7 Implementation Report: Real-Time Streaming Pipeline

**Date:** 2026-11-04  
**Project:** ChainSentinel (Big Data Analytics)  
**Location:** `E:\BDA\ChainSentinel`  
**Phase:** Phase 7 Task 2 — Real-Time Disruption Ingestion  
**Author:** Antigravity Advanced Agentic Assistant  

---

## 1. Executive Summary

Phase 7 Task 2 successfully establishes the real-time event ingestion infrastructure for ChainSentinel. This provides the continuous data plane required to detect disruption events in real time and feed them downstream into the Shockwave Engine and resilience optimization pipelines.

Key accomplishments:
1. **Dynamic Core Balancing:** Reconfigured the existing generic streaming application (`ChainSentinel-Kafka-Streaming`) to use 4 cores and allocated 4 cores to the new disruption streaming application (`ChainSentinel-Disruption-Streaming`), enabling true concurrent execution on the 8-core Spark Standalone cluster.
2. **Dedicated Kafka Ingestion Layer:** Created a dedicated Kafka topic `disruption-events` with 2 partitions, preserving `supply-chain-events` unmodified.
3. **Robust Disruption Event Schema:** Implemented a strongly-typed schema supporting all required Phase 7 attributes (`event_id`, `event_type`, `location`, `timestamp`, `impact_radius_km`, `affected_mode`, `source_confidence`) and backward-compatible fields.
4. **Isolated Storage Architecture:** Created isolated HDFS streaming sink `/chainsentinel/streaming/disruptions` and state checkpoint `/chainsentinel/checkpoints/disruption_events`.
5. **Resilient Streaming Engine:** Authored and deployed `disruption_stream.py` with malformed JSON quarantine/filtering, deterministic micro-batch commits, and fault-tolerant state recovery.

---

## 2. Infrastructure & Spark Resource Reconfiguration

### 2.1 Cluster Resource Allocation

Prior to Task 2, `app-20261103190004-0001` occupied all 8 cores of the Spark Standalone worker (`worker-20261103182020-172.18.0.5-44031`).

To achieve concurrent execution without resource starvation:
* The existing pipeline `ChainSentinel-Kafka-Streaming` was reconfigured with `--total-executor-cores 4 --executor-cores 2` and `.config("spark.cores.max", "4")`.
* The new pipeline `ChainSentinel-Disruption-Streaming` was configured with `--total-executor-cores 4 --executor-cores 2` and `.config("spark.cores.max", "4")`.

```
========================================================================================
Worker: worker-20261103182020-172.18.0.5-44031 (Total: 8 Cores, 7,168 MB RAM)
----------------------------------------------------------------------------------------
├── Application 1: ChainSentinel-Kafka-Streaming      --> 4 Cores, 2 Executors (1024 MB each)
└── Application 2: ChainSentinel-Disruption-Streaming --> 4 Cores, 2 Executors (1024 MB each)
Total Cores Used: 8 | Cores Free: 0 | Waiting Applications: 0 | Cluster State: HEALTHY
========================================================================================
```

### 2.2 Active Cluster Verification via Spark Master REST API
```json
{
  "activeapps": [
    {
      "id": "app-20261104085239-0002",
      "name": "ChainSentinel-Kafka-Streaming",
      "cores": 4,
      "state": "RUNNING"
    },
    {
      "id": "app-20261104090004-0004",
      "name": "ChainSentinel-Disruption-Streaming",
      "cores": 4,
      "state": "RUNNING"
    }
  ],
  "workers": [
    {
      "id": "worker-20261103182020-172.18.0.5-44031",
      "cores": 8,
      "coresused": 8,
      "coresfree": 0,
      "memory": 7168,
      "memoryused": 4096,
      "memoryfree": 3072,
      "state": "ALIVE"
    }
  ]
}
```

---

## 3. Kafka Messaging Architecture

### 3.1 Broker & Topic Configuration
* **Broker Version:** Apache Kafka 4.4.0 (KRaft mode).
* **Internal Listener:** `chainsentinel-kafka:29092` (Used by Spark executors inside Docker network).
* **External Listener:** `localhost:9092` (Used by host producers).

### 3.2 Topics Summary
1. **`disruption-events` (NEW):**
   * **Partitions:** 2 (`Partition 0`, `Partition 1`)
   * **Replication Factor:** 1
   * **Configs:** `min.insync.replicas=1`
   * **Purpose:** High-throughput, partitioned feed for real-time supply chain disruption incidents.
2. **`supply-chain-events` (PRESERVED):**
   * **Partitions:** 1 (`Partition 0`)
   * **Replication Factor:** 1
   * **Configs:** Unmodified
   * **Purpose:** Legacy generic operational supply chain telemetry.

---

## 4. Disruption Event Schema Specification

The disruption event schema was designed to interface directly with the Phase 6 graph network (`graph_nodes.csv` and `chainsentinel_graph.json`):

```python
disruption_schema = StructType([
    StructField("event_id", StringType(), True),           # Unique incident ID (e.g., DISR-2026-001)
    StructField("event_type", StringType(), True),         # Incident category (e.g., PORT_CONGESTION)
    StructField("location", StringType(), True),           # Geographic entity or Graph Node ID
    StructField("timestamp", StringType(), True),          # ISO 8601 UTC timestamp
    StructField("impact_radius_km", DoubleType(), True),   # Spatial impact radius in kilometers
    StructField("affected_mode", StringType(), True),      # Shipping mode impacted (e.g., Standard Class)
    StructField("source_confidence", DoubleType(), True),  # Data feed confidence score (0.0 to 1.0)
    StructField("severity", StringType(), True),           # Operational severity (CRITICAL, HIGH, etc.)
    StructField("duration_hours", IntegerType(), True),    # Expected duration in hours
    StructField("description", StringType(), True)         # Incident narrative summary
])
```

### Malformed Event Handling & Validation Rules
Incoming raw events are evaluated against a mandatory attribute predicate:
```python
valid_condition = (
    col("event_id").isNotNull() & (col("event_id") != "") &
    col("event_type").isNotNull() & (col("event_type") != "") &
    col("location").isNotNull() & (col("location") != "") &
    col("timestamp").isNotNull() &
    col("impact_radius_km").isNotNull() &
    col("affected_mode").isNotNull() &
    col("source_confidence").isNotNull()
)
```
Records failing this predicate (malformed JSON or missing required fields) are safely quarantined and excluded from the clean analytical HDFS store, preventing corrupt rows from propagating to graph analytics.

---

## 5. Storage Isolation Architecture (HDFS)

The storage layout guarantees strict zero-overlap separation between legacy and disruption streams:

```
hdfs://namenode:8020/chainsentinel/
├── checkpoints/
│   ├── kafka_events/               <-- Legacy checkpoint directory (offsets, commits, metadata)
│   └── disruption_events/          <-- Dedicated Phase 7 checkpoint directory
└── streaming/
    ├── events/                     <-- Legacy JSON event sink
    └── disruptions/                <-- Dedicated Phase 7 JSON disruption event sink
        ├── _spark_metadata/        <-- Streaming query transactional commit logs
        ├── part-*-c000.json        <-- Partitioned immutable JSON micro-batch output files
```

---

## 6. Spark Structured Streaming Application Design

* **Script Path:** `E:\BDA\ChainSentinel\docker\spark\streaming\disruption_stream.py`
* **Container Path:** `/tmp/disruption_stream.py`
* **Source:** Kafka `disruption-events` via `spark-sql-kafka-0-10_2.13:4.0.1`
* **Starting Offsets:** `earliest` (ensures zero data loss upon initial startup or restart)
* **Metadata Processing:** Automatically injects `processed_at` timestamp using `current_timestamp()`
* **Sink:** Append-mode JSON stream to `hdfs://namenode:8020/chainsentinel/streaming/disruptions`
* **Fault-Tolerant Checkpoint:** `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events`

---

## 7. Operational Workflow Summary

```
                      [ External Disruption Feeds ]
                                    │
                                    ▼ (localhost:9092)
           ┌──────────────────────────────────────────────────┐
           │        Kafka Topic: disruption-events            │
           │        (2 Partitions: Partition 0 & 1)           │
           └────────────────────────┬─────────────────────────┘
                                    │
                                    ▼ (chainsentinel-kafka:29092)
           ┌──────────────────────────────────────────────────┐
           │       Spark Structured Streaming Engine          │
           │       App: ChainSentinel-Disruption-Streaming    │
           │       (4 Cores, 2 Executors, starting: earliest) │
           └──────────────┬────────────────────┬──────────────┘
                          │                    │
        (Valid Events)    │                    │ (Offset / Commit Logs)
                          ▼                    ▼
     ┌────────────────────────────┐    ┌─────────────────────────────┐
     │ HDFS Streaming Sink:       │    │ HDFS Checkpoint Directory:  │
     │ /chainsentinel/streaming/  │    │ /chainsentinel/checkpoints/ │
     │ disruptions/               │    │ disruption_events/          │
     └────────────────────────────┘    └─────────────────────────────┘
```

The pipeline is live, validated, and fully operational.


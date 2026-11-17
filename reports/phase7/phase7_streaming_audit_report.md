# CHAINSENTINEL — PHASE 7: REAL-TIME DISRUPTION INGESTION
## Task 1: Read-Only Infrastructure and Streaming Pipeline Audit Report

**Date:** 2026-11-04  
**Project:** ChainSentinel (Big Data Analytics)  
**Location:** `E:\BDA\ChainSentinel`  
**Audit Type:** Independent, Read-Only Infrastructure & Streaming Verification  
**Auditor:** Antigravity Advanced Agentic Assistant  

---

## 1. Executive Summary

A comprehensive, strictly read-only technical audit of the real-time streaming infrastructure and the active Apache Spark Structured Streaming pipeline was conducted for **ChainSentinel Phase 7: Real-Time Disruption Ingestion**.

### Key Findings Summary:
1. **Infrastructure Health:** All five Docker containers (`chainsentinel-kafka`, `chainsentinel-namenode`, `chainsentinel-datanode`, `chainsentinel-spark-master`, `chainsentinel-spark-worker`) are running, healthy, and interconnected on the bridge network `hadoop_default` (`172.18.0.0/16`).
2. **Active Streaming Job:** A Spark Structured Streaming application named `ChainSentinel-Kafka-Streaming` (`app-20261103190004-0001`) has been running continuously for ~14 hours on Spark Master (`spark://spark-master:7077`).
3. **End-to-End Pipeline Execution Verified:** HDFS sink inspection confirmed that the pipeline successfully ingested, transformed, and committed record `EVT002` (`PORT_CLOSURE`, Chennai Port) into HDFS at `/chainsentinel/streaming/events/` via micro-batch commit 1.
4. **Critical Resource Starvation Bottleneck Identified:** The existing streaming application holds all 8 CPU cores of the standalone Spark worker (`coresused: 8`, `coresfree: 0`). Submitting any new Spark application without either killing `app-20261103190004-0001` or configuring core limits (`spark.cores.max`) will cause the new application to stall indefinitely in the `WAITING` queue.
5. **Architectural Isolation Requirement:** To support Phase 7 Real-Time Disruption Ingestion without corrupting existing streaming states, a dedicated Kafka topic (`disruption-events`), isolated checkpoint directory (`/chainsentinel/checkpoints/disruption_events`), and distinct HDFS storage sink (`/chainsentinel/streaming/disruptions`) are strictly required.

---

## 2. Infrastructure Health & Container Status

| Container Name | Status | Uptime | Port Mappings | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| `chainsentinel-kafka` | Up | >19 hours | `9092:9092`, `29092:29092` | **VERIFIED** |
| `chainsentinel-namenode` | Up | >14 hours | `8020:8020`, `9870:9870` | **VERIFIED** |
| `chainsentinel-datanode` | Up | >14 hours | `9864:9864` | **VERIFIED** |
| `chainsentinel-spark-master` | Up | >14 hours | `7077:7077`, `8080:8080` | **VERIFIED** |
| `chainsentinel-spark-worker` | Up | >14 hours | `8081:8081` | **VERIFIED** |

* **Network Inspection:** All 5 containers are joined to Docker network `hadoop_default` with subnet `172.18.0.0/16` and gateway `172.18.0.1`. Container hostnames resolve seamlessly via Docker embedded DNS (`chainsentinel-kafka`, `namenode`, `spark-master`, `spark-worker`).
* **Storage Mounting:** Host directory `E:\BDA\ChainSentinel\docker\spark\streaming` is mounted at `/opt/spark/streaming` in the Spark Master container.

---

## 3. Kafka Broker and Topic Verification

### 3.1 Broker Configuration
* **Internal Listener:** `PLAINTEXT://chainsentinel-kafka:29092` (Used by Spark executors inside Docker network).
* **External Listener:** `PLAINTEXT://localhost:9092` (Used by Windows host producers/tools).
* **Zookeeper / KRaft Mode:** KRaft metadata mode operational without external ZooKeeper container.

### 3.2 Topic Inspection: `supply-chain-events`
Inspection executed via Kafka CLI tools (`kafka-topics.sh` and `kafka-get-offsets.sh`):
* **Partition Count:** `1` (Partition ID: 0)
* **Replication Factor:** `1`
* **Leader Broker:** `1`
* **In-Sync Replicas (ISR):** `[1]`
* **Offset Range:**
  * Earliest Offset: `0`
  * Latest Offset: `1`
  * Total Messages on Broker: `1`
* **Verification Status:** **VERIFIED**

### 3.3 Consumer Groups
* Querying `kafka-consumer-groups.sh --bootstrap-server localhost:9092 --list` returned empty.
* **Technical Reason:** Spark Structured Streaming does not rely on Kafka's consumer group protocol for partition offset management; instead, Spark manages offsets directly via custom commit logs stored in its HDFS checkpoint directory (`/chainsentinel/checkpoints/kafka_events/offsets/`).
* **Verification Status:** **VERIFIED**

---

## 4. Existing Streaming Application Status

### 4.1 Master Cluster State
Inspected via Spark Master REST API (`http://localhost:8080/json/`):
* **Application ID:** `app-20261103190004-0001`
* **Application Name:** `ChainSentinel-Kafka-Streaming`
* **Application State:** `RUNNING`
* **Submission Timestamp:** `Tue Nov 03 19:00:04 UTC 2026`
* **Application Duration:** Active for >13 hours 50 minutes.
* **Verification Status:** **VERIFIED**

### 4.2 Resource Utilization and Allocation Breakdown
* **Worker:** `worker-20261103182020-172.18.0.5-44031`
* **Total Worker Capacity:** 8 CPU Cores, 7,168 MB RAM
* **Cores Allocated to Application:** **8 Cores (100% Saturation)**
* **Cores Remaining Available:** **0 Cores**
* **Memory Allocated to Application:** 4,096 MB (3,072 MB free)
* **Executor Allocation:** 4 Executors launched (`app-20261103190004-0001/0`, `1`, `2`, `3`), each utilizing 2 cores and 1,024 MB.
* **Verification Status:** **VERIFIED (RESOURCE WARNING)**

### 4.3 Streaming Code Analysis (`docker/spark/streaming/kafka_stream.py`)
```python
# Key parameters extracted from the active script:
schema = StructType([
    StructField("event_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("location", StringType(), True),
    StructField("severity", StringType(), True),
    StructField("duration_hours", IntegerType(), True),
    StructField("timestamp", StringType(), True)
])

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "chainsentinel-kafka:29092") \
    .option("subscribe", "supply-chain-events") \
    .option("startingOffsets", "latest") \
    .load()
```
* **Trigger Mode:** Default (continuous micro-batch as fast as previous batch finishes).
* **Error Handling:** None. Malformed JSON records fail silently into null fields via `from_json`.
* **Verification Status:** **VERIFIED**

---

## 5. HDFS Output and Checkpoint Verification

### 5.1 Storage Verification (`hdfs dfs -ls -R /chainsentinel/streaming/`)
* **HDFS Sink Path:** `/chainsentinel/streaming/events/`
* **Metadata Directory:** `/chainsentinel/streaming/events/_spark_metadata/`
  * Batch 0 metadata: `237 bytes` (2026-11-03 13:22 UTC)
  * Batch 1 metadata: `239 bytes` (2026-11-03 13:27 UTC)
* **Data Partitions:**
  * `part-00000-a8ae2655-11f5-47e0-a293-1b6adaced963-c000.json`: `0 bytes` (Batch 0 empty initialization).
  * `part-00000-fa50e9fc-75e6-4b33-9066-d8a517b64e3e-c000.json`: `190 bytes` (Batch 1 payload).
* **Payload Content:**
  ```json
  {"event_id":"EVT002","event_type":"PORT_CLOSURE","location":"Chennai Port","severity":"HIGH","duration_hours":48,"timestamp":"2026-11-03T18:45:00","processed_at":"2026-11-03T13:26:58.638Z"}
  ```
* **Verification Status:** **VERIFIED — End-to-end event delivery and HDFS JSON persistence proven.**

### 5.2 Checkpoint State (`hdfs dfs -ls -R /chainsentinel/checkpoints/kafka_events/`)
* **Metadata ID:** `b1285496-e244-42b3-9eb7-f5da11108a9c`
* **Commits:**
  * Commit 0: Completed at 2026-11-03 13:22 UTC.
  * Commit 1: Completed at 2026-11-03 13:27 UTC.
* **Offset Checkpoints:**
  * `/offsets/0`: `{"supply-chain-events":{"0":0}}`
  * `/offsets/1`: `{"supply-chain-events":{"0":1}}`
* **Verification Status:** **VERIFIED**

---

## 6. Schema Comparison: Existing vs Phase 7 Disruption Events

| Field | Existing `supply-chain-events` Schema | Phase 7 Disruption Ingestion Requirement | Schema Compatibility Assessment |
| :--- | :--- | :--- | :--- |
| `event_id` | String | String (Unique UUID/ID) | Compatible |
| `event_type` | String | String (`PORT_DISRUPTION`, `WEATHER_SEVERE`, etc.) | Compatible |
| `location` | String (Unstructured text) | String (Must match Phase 6 Graph Node IDs / Names) | Partially Compatible (Requires node mapping) |
| `severity` | String (`HIGH`, `MEDIUM`, etc.) | String or Float (`CRITICAL`, `0.0 - 1.0`) | Compatible |
| `duration_hours`| Integer | Integer / Float | Compatible |
| `timestamp` | String | ISO 8601 Timestamp String | Compatible |
| `impact_radius_km`| *Not Present* | Float (Required for Shockwave propagation) | **Missing in Existing Schema** |
| `affected_mode` | *Not Present* | String (`AIR`, `OCEAN`, `ROAD`, `RAIL`) | **Missing in Existing Schema** |
| `source_confidence`| *Not Present*| Float (0.0 - 1.0 reliability score) | **Missing in Existing Schema** |
| `description` | *Not Present* | Textual incident details | **Missing in Existing Schema** |

> [!WARNING]
> Ingesting Phase 7 disruption events into the existing topic `supply-chain-events` would drop all extended disruption attributes (`impact_radius_km`, `affected_mode`, etc.) because the active streaming query drops unrecognized fields during JSON schema parsing.

---

## 7. Identified Technical Risks and Architectural Bottlenecks

### Risk 1: Spark Worker Core Exhaustion (CRITICAL)
* **Description:** The running application `app-20261103190004-0001` has reserved `coresused: 8` out of `8` total worker cores.
* **Impact:** Any attempt to launch a second Spark Structured Streaming application or batch job on the cluster will remain indefinitely queued in `WAITING` status.
* **Mitigation:**
  - *Strategy A (Recommended):* Gracefully terminate `app-20261103190004-0001` before launching the Phase 7 disruption streaming engine.
  - *Strategy B (Multi-Tenant):* Relaunch both jobs with explicit `--total-executor-cores 4` (or `--conf spark.cores.max=4`) so each application receives 4 cores.

### Risk 2: Checkpoint Collisions and State Corruption (HIGH)
* **Description:** Spark Structured Streaming binds schema and source state irrevocably to the checkpoint directory.
* **Impact:** Reusing `/chainsentinel/checkpoints/kafka_events` with an extended disruption schema will result in an `AnalysisException` / `InvalidCheckpointException`.
* **Mitigation:** Dedicated checkpoint path `/chainsentinel/checkpoints/disruption_events` must be used.

### Risk 3: Starting Offsets = 'latest' Data Loss (MEDIUM)
* **Description:** The current configuration uses `.option("startingOffsets", "latest")`.
* **Impact:** Any event produced prior to application initialization or during brief restarts will never be processed or stored in HDFS.
* **Mitigation:** Phase 7 streaming should specify `.option("startingOffsets", "earliest")` to ensure full reproducibility, idempotency, and replay capabilities.

### Risk 4: Lack of Malformed Data Quarantine / DLQ (MEDIUM)
* **Description:** Invalid JSON payloads currently resolve to null rows without triggering warnings or quarantine.
* **Impact:** Silent ingestion of null records pollutes downstream graph shockwave analytics.
* **Mitigation:** Introduce filtering (`WHERE event_id IS NOT NULL`) and write malformed records to a Dead-Letter Queue (DLQ) topic or quarantine path.

---

## 8. Phase 7 Implementation Feasibility

| Dimension | Feasibility Assessment | Evidence / Justification |
| :--- | :--- | :--- |
| **Kafka Broker Ingestion** | **100% Ready** | Broker is active, accepting connections on ports 9092/29092, and supports instant creation of new topics. |
| **HDFS Storage Sink** | **100% Ready** | NameNode and DataNode are fully responsive with active replication and healthy disk allocations. |
| **Spark Streaming Engine** | **Ready with Reconfiguration** | Spark master/worker are operational; requires resolution of the 8-core allocation constraint. |
| **Graph Network Integration** | **100% Ready** | Phase 6 graph models and nodes (`graph_nodes.csv`, `chainsentinel_graph.json`) are readily available on the host for spatial/topological matching. |

---

## 9. Recommended Architecture for Phase 7

```
                     ┌──────────────────────────────────────┐
                     │ Windows Host / Python Disruption Pub │
                     │   (simulated or external feeds)      │
                     └──────────────────┬───────────────────┘
                                        │
                                        ▼ (localhost:9092)
                     ┌──────────────────────────────────────┐
                     │ Kafka Topic: `disruption-events`     │
                     │  - Partitions: 2                     │
                     │  - Replication: 1                    │
                     └──────────────────┬───────────────────┘
                                        │
                                        ▼ (chainsentinel-kafka:29092)
                     ┌──────────────────────────────────────┐
                     │ Spark Structured Streaming           │
                     │ App: `ChainSentinel-Disruption-Ingest│
                     │  - Cores: 4-8                        │
                     │  - startingOffsets: earliest         │
                     │  - Disruption Schema + DLQ filter    │
                     └─────────┬──────────────────┬─────────┘
                               │                  │
           (Sink to HDFS)      ▼                  ▼ (State Checkpoint)
  ┌─────────────────────────────────┐   ┌──────────────────────────────────┐
  │ HDFS Sink:                      │   │ HDFS Checkpoint:                 │
  │ /chainsentinel/streaming/       │   │ /chainsentinel/checkpoints/      │
  │ disruptions/                    │   │ disruption_events/               │
  └─────────────────────────────────┘   └──────────────────────────────────┘
```

---

## 10. Explicit Actions Requiring User Authorization

To adhere strictly to Mandatory Project Protection Rules, the following specific actions must receive user approval before Phase 7 implementation:
1. **Topic Creation:** Authorization to create Kafka topic `disruption-events` with 2 partitions.
2. **Spark Application Lifecycle:** Authorization to stop legacy application `app-20261103190004-0001` on Spark Master, freeing the 8 worker cores for the Phase 7 disruption ingestion pipeline.
3. **HDFS Directories:** Authorization to create checkpoint `/chainsentinel/checkpoints/disruption_events` and output sink `/chainsentinel/streaming/disruptions`.
4. **Disruption Producer Script:** Authorization to create and run a disruption generator script in the Windows Python virtual environment (`python-env`) publishing test disruptions to `localhost:9092`.

---

## 11. Final Audit Status

### Overall Status: **PASS (WITH RESOURCE RECONFIGURATION CONDITION)**

* **Infrastructure Status:** `VERIFIED`
* **Streaming Capability:** `VERIFIED` (Historical execution of `EVT002` demonstrated in HDFS)
* **Cluster Capacity:** `WARNING` (Worker core saturation requires app management before new streaming job submission)
* **Architectural Readiness:** `VERIFIED`

---
*Report compiled autonomously by Antigravity under zero-modification audit constraints.*


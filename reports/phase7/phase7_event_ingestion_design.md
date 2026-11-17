# CHAINSENTINEL — PHASE 7: REAL-TIME DISRUPTION INGESTION
## Disruption Event Ingestion Engine Architecture & Design Document

**Date:** 2026-11-04  
**Project:** ChainSentinel (Big Data Analytics)  
**Location:** `E:\BDA\ChainSentinel`  
**Phase:** Phase 7 Task 2B — Build the Disruption Event Ingestion Engine  
**Author:** Antigravity Advanced Agentic Assistant  

---

## 1. Architectural Overview & Event Flow

ChainSentinel requires an ultra-reliable, fault-tolerant, and schema-enforcing real-time ingestion engine to capture global supply-chain disruptions. This stream directly drives downstream shockwave propagation across the supply-chain graph constructed in Phase 6.

### High-Level Event Flow

```
   [ External Disruption Sources / Alerts ]
   (Maritime, Weather APIs, Logistics Syndicates)
                        │
                        ▼ (JSON payloads)
   ┌────────────────────────────────────────────────────────┐
   │ Kafka Topic: `disruption-events`                       │
   │ - Bootstrap: chainsentinel-kafka:29092                 │
   │ - 2 Partitions (Partition 0, Partition 1)              │
   │ - Replication Factor: 1                                │
   └────────────────────┬───────────────────────────────────┘
                        │
                        ▼ (Consumer Stream: startingOffsets=earliest)
   ┌────────────────────────────────────────────────────────┐
   │ Spark Structured Streaming Engine                      │
   │ App: `ChainSentinel-Disruption-Ingestion`              │
   │ Module: `docker/spark/streaming/disruption_ingestion.py`│
   │                                                        │
   │  1. Unpack JSON via StructType Schema                  │
   │  2. Preserve Kafka transport metadata (partition,      │
   │     offset, kafka_timestamp)                           │
   │  3. Vectorised Spark SQL Validation Predicate          │
   │  4. System Ingestion Timestamp Enrichment              │
   │  5. Stateful Watermark & Deduplication (2-hr window)   │
   │  6. Filter: Partition stream into Valid vs Quarantine   │
   └───────────────┬────────────────────────┬───────────────┘
                   │                        │
       (Valid Events: is_valid=True)        │ (Invalid/Malformed: is_valid=False)
                   │                        │
                   ▼                        ▼ [AWAITING USER AUTHORIZATION]
   ┌──────────────────────────────┐ ┌──────────────────────────────┐
   │ HDFS Clean Output Sink:      │ │ HDFS Quarantine Sink:        │
   │ /chainsentinel/streaming/    │ │ /chainsentinel/streaming/    │
   │ disruptions/                 │ │ disruptions/quarantine/      │
   ├──────────────────────────────┤ ├──────────────────────────────┤
   │ State Checkpoint:            │ │ State Checkpoint:            │
   │ /chainsentinel/checkpoints/  │ │ /chainsentinel/checkpoints/  │
   │ disruption_events/           │ │ disruption_events_quarantine │
   └──────────────────────────────┘ └──────────────────────────────┘
```

---

## 2. Strict Disruption Event Schema Specification

To eliminate ambiguity and prevent corrupt records from entering graph analytics, all disruption events must conform to the 15-field specification defined in `docker/spark/streaming/disruption_event_schema.py`.

| # | Field Name | Spark DataType | Required? | Description & Allowed Values |
| :- | :--- | :--- | :- | :--- |
| 1 | `event_id` | `StringType` | **YES** | Unique identifier (e.g. `SIM-DISR-2026-001`). Non-empty string. |
| 2 | `event_type` | `StringType` | **YES** | Lifecycle state: `DISRUPTION_ALERT`, `INCIDENT_REPORT`, `SITUATION_UPDATE`, `STATUS_CHANGE`, `DISRUPTION_RESOLVED`. |
| 3 | `disruption_type` | `StringType` | **YES** | Root cause: `PORT_CLOSURE`, `SEVERE_WEATHER`, `LABOR_STRIKE`, `CARRIER_CAPACITY_SHORTAGE`, `CUSTOMS_DELAY`, `GEOPOLITICAL_SANCTION`, `INFRASTRUCTURE_FAILURE`, `OTHER`. |
| 4 | `affected_market` | `StringType` | **YES** | Market entity matching Phase 6 graph nodes (e.g. `Pacific Asia`, `USMCA`, `Europe`, `LATAM`). |
| 5 | `affected_region` | `StringType` | OPTIONAL | Sub-regional geographic tier (e.g. `Central America`, `Western Europe`). |
| 6 | `affected_country`| `StringType` | OPTIONAL | Country of incident origin (e.g. `Puerto Rico`, `United States`). |
| 7 | `severity` | `StringType` | **YES** | Operational impact tier: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. |
| 8 | `start_time` | `TimestampType`| **YES** | Incident onset timestamp (ISO 8601 UTC). |
| 9 | `expected_duration_hours` | `DoubleType` | **YES** | Estimated disruption duration in hours (non-negative). |
| 10| `capacity_reduction_pct` | `DoubleType` | **YES** | Capacity loss percentage ($0.0 \le x \le 100.0$). |
| 11| `delay_estimate_hours` | `DoubleType` | **YES** | Direct operational delay estimate (non-negative). |
| 12| `source` | `StringType` | **YES** | Reporting body/sensor network identifier. Non-empty string. |
| 13| `source_confidence` | `DoubleType` | **YES** | Source reliability index ($0.0 \le x \le 1.0$). |
| 14| `description` | `StringType` | OPTIONAL | Unstructured operational summary narrative. |
| 15| `event_timestamp`| `TimestampType`| **YES** | Signal emission timestamp used for event-time watermarking. |

---

## 3. Data Validation & Quarantine Rules

Validation is executed via vectorised Spark SQL rules without fallback conversions. If any rule fails, the record is flagged with specific violation codes and diverted from the clean HDFS store.

| Rule ID | Checked Condition | Violation Code | Quarantine Action |
| :--- | :--- | :--- | :--- |
| **V1** | `event_id` is null or whitespace | `ERR_INVALID_EVENT_ID` | Quarantined |
| **V2** | `event_type` not in allowed enum set | `ERR_INVALID_EVENT_TYPE` | Quarantined |
| **V3** | `disruption_type` not in allowed enum set | `ERR_INVALID_DISRUPTION_TYPE` | Quarantined |
| **V4** | `affected_market` is null or whitespace | `ERR_MISSING_AFFECTED_MARKET` | Quarantined |
| **V5** | `severity` not in `{'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'}` | `ERR_INVALID_SEVERITY` | Quarantined |
| **V6** | `start_time` is null or invalid timestamp | `ERR_MISSING_START_TIME` | Quarantined |
| **V7** | `expected_duration_hours` < 0.0 or null | `ERR_INVALID_EXPECTED_DURATION` | Quarantined |
| **V8** | `capacity_reduction_pct` < 0.0 or > 100.0 | `ERR_INVALID_CAPACITY_REDUCTION` | Quarantined |
| **V9** | `delay_estimate_hours` < 0.0 or null | `ERR_INVALID_DELAY_ESTIMATE` | Quarantined |
| **V10** | `source` is null or whitespace | `ERR_MISSING_SOURCE` | Quarantined |
| **V11** | `source_confidence` < 0.0 or > 1.0 | `ERR_INVALID_SOURCE_CONFIDENCE` | Quarantined |
| **V12** | `event_timestamp` is null or unparseable | `ERR_MISSING_EVENT_TIMESTAMP` | Quarantined |
| **V13** | JSON unparseable / syntax corrupt | `ERR_MALFORMED_JSON` | Quarantined |

---

## 4. Duplicate Event Strategy & Limitations

### 4.1 Taxonomy of Duplicate Events
In real-time distributed supply-chain streaming, duplicates manifest in three distinct forms:
1. **Network Retransmission Duplicates:** Identical Kafka records produced multiple times due to producer retries.
2. **Kafka Replay Duplicates:** Re-reading committed offsets following streaming engine restarts.
3. **Event Updates (Conflicting Payloads):** Records sharing the same `event_id` but featuring modified attributes (e.g., a port closure escalating from `MEDIUM` to `CRITICAL` with extended duration).

### 4.2 Deduplication Implementation
* **Composite Deduplication Key:** `[event_id, event_timestamp]`.
  - Pure deduplication on `event_id` alone is defective because it discards legitimate incident updates (`SITUATION_UPDATE`, `DISRUPTION_RESOLVED`).
  - Combining `event_id` with `event_timestamp` ensures that true transport retransmissions (identical ID and timestamp) are suppressed while progressive status updates are preserved.
* **Bounded Watermark:** A 2-hour watermark threshold (`withWatermark("event_timestamp", "2 hours")`) is applied.

### 4.3 Technical Limitations of Stateful Deduplication
1. **State Store Memory Consumption:** Spark maintains state keys in the worker JVM heap (or RocksDB state store). An unbounded deduplication window would inevitably trigger `OutOfMemoryError`. The 2-hour watermark bounds memory consumption.
2. **Late-Arriving Events:** Events arriving later than the 2-hour watermark threshold are discarded by Spark's state store.
3. **Checkpoint Immutability:** Deduplication state is bound to the HDFS checkpoint. Modifying the deduplication key requires purging the checkpoint or versioning the pipeline.

---

## 5. Multi-Sink Architecture: Valid vs. Quarantine Streams

### Architectural Constraint in Spark Structured Streaming
A single Spark Structured Streaming query is fundamentally bound to **one sink** and **one checkpoint location**. Attempting to write valid events to `/chainsentinel/streaming/disruptions` and invalid events to `/chainsentinel/streaming/disruptions/quarantine` within a single `.writeStream` call is prohibited by Spark's execution engine.

### Approved Dual-Query Strategy
To achieve strict separation:
1. **Query 1 (Production Valid Stream):**
   * Filter: `col("is_valid") == True`
   * Sink: `hdfs://namenode:8020/chainsentinel/streaming/disruptions`
   * Checkpoint: `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events`
   * Status: **Authorized & Prepared**
2. **Query 2 (Quarantine Stream):**
   * Filter: `col("is_valid") == False`
   * Sink: `hdfs://namenode:8020/chainsentinel/streaming/disruptions/quarantine`
   * Checkpoint: `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events_quarantine`
   * Status: **Engineered in code, gated behind `--enable-quarantine` flag, awaiting user infrastructure authorization to create HDFS directories.**

---

## 6. Spark Resource Limitations & Deployment Prerequisites

### Spark Cluster Saturation Constraint
* The Spark Standalone Worker (`worker-20261103182020-172.18.0.5-44031`) has 8 total CPU cores.
* Submitting `disruption_ingestion.py` without core restrictions or while another application holds the cores will cause the new driver to stall indefinitely in `WAITING` state.

### Deployment Prerequisites for Future Launch:
1. **Resource Authorization:** Explicit user approval to configure core balancing (e.g. 4 cores for legacy streaming, 4 cores for disruption ingestion).
2. **Quarantine Directory Authorization:** Explicit user approval to create HDFS quarantine sink and checkpoint paths.
3. **Execution Command:** Launching via `spark-submit` with `--packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.1` and `--total-executor-cores 4`.


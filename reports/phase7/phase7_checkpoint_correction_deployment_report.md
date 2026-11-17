# Phase 7 — Task 2G: Checkpoint Isolation Correction & Controlled Redeployment Report

**Project:** ChainSentinel — AI-Powered Supply Chain Resilience Management  
**Timestamp:** 2026-11-04T16:05:00+05:30  
**Phase:** 7 — Real-Time Disruption Ingestion  
**Task:** 2G — Checkpoint Isolation Correction and Controlled Redeployment  
**Deployment Verdict:** `DEPLOYMENT PARTIALLY SUCCESSFUL` (Detailed in Section 13)

---

## 1. Executive Summary & Root Cause Analysis

### 1.1 Task 2F Failure Root Cause
During Phase 7 Task 2F, the production deployment of `ChainSentinel-Disruption-Ingestion` (`app-20261104100706-0005`) failed immediately on micro-batch 0 with:
```text
org.apache.spark.sql.streaming.StreamingQueryException: 
[CANNOT_LOAD_STATE_STORE.CANNOT_READ_DELTA_FILE_NOT_EXISTS] 
Error reading delta file hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events/state/0/30/1.delta
```
**Mechanism:** The directory `/chainsentinel/checkpoints/disruption_events` had been created and populated during Phase 7 Task 2 by an unwatermarked, stateless prototype script (`disruption_stream.py`). In Spark Structured Streaming, introducing watermarking and stateful deduplication (`dropDuplicates(["event_id", "event_timestamp"])`) altered the execution graph to require an `HDFSBackedStateStoreProvider`. The state store attempted to load non-existent incremental state deltas from the mismatched prototype checkpoint lineage, causing an unrecoverable `StreamingQueryException`.

### 1.2 Task 2G Resolution Strategy
1. **Isolated Checkpoint Creation:** Provisioned a brand-new, dedicated HDFS checkpoint directory:
   `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_ingestion`
2. **Preservation of Artifacts:** Left the prototype checkpoint `/chainsentinel/checkpoints/disruption_events` completely intact and unmodified.
3. **Pipeline Re-Targeting:** Pointed `HDFS_VALID_CHECKPOINT_PATH` in `disruption_ingestion.py` strictly to the fresh checkpoint.
4. **Controlled Concurrency:** Submitted the application with 4 cores (`--total-executor-cores 4 --executor-cores 2`) on the 8-core worker, maintaining concurrent execution alongside the legacy application `ChainSentinel-Kafka-Streaming` (4 cores).

---

## 2. Checkpoint Architecture & Directory Paths

| Component | Path | Inode / State | Isolation Status |
| :--- | :--- | :--- | :--- |
| **Old Prototype Checkpoint** | `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events` | Preserved (batches 0, 1, 2, 3) | Isolated & Untouched |
| **New Dedicated Checkpoint** | `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_ingestion` | Active (`commits/0`, `offsets/0`, `sources/0/0`, `state/0`) | Verified & Clean |
| **Legacy Checkpoint** | `hdfs://namenode:8020/chainsentinel/checkpoints/kafka_events` | Active (batches 0, 1, 2) | Preserved & Running |
| **Primary Output Sink** | `hdfs://namenode:8020/chainsentinel/streaming/disruptions` | Preserved existing part files | Active file stream sink |

---

## 3. Script Corrections Applied

In `docker/spark/streaming/disruption_ingestion.py`:
- **Line Modified:** Line 48
- **Before:**
  ```python
  HDFS_VALID_CHECKPOINT_PATH = "hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events"
  ```
- **After:**
  ```python
  HDFS_VALID_CHECKPOINT_PATH = "hdfs://namenode:8020/chainsentinel/checkpoints/disruption_ingestion"
  ```
- **Preserved Attributes:** Kafka bootstrap (`chainsentinel-kafka:29092`), topic (`disruption-events`), `startingOffsets = "earliest"`, HDFS output path (`/chainsentinel/streaming/disruptions`), watermarking (`2 hours`), deduplication key (`[event_id, event_timestamp]`), and multi-query failure monitoring loop.

---

## 4. Local Validation & Unit Test Suite

The modified script was verified using the host environment `E:\BDA\ChainSentinel\python-env`:
- **Syntax Compilation:**
  ```powershell
  python -m py_compile docker/spark/streaming/disruption_ingestion.py
  ```
  *Result: Clean exit (code 0).*
- **Unit Test Suite Execution (`docker/spark/streaming/tests/test_disruption_events.py`):**
  ```text
  test_all_null_or_empty_payload ... ok
  test_boolean_in_numeric_fields ... ok
  test_conflicting_event_id_payload ... ok
  test_duplicate_event_id ... ok
  test_invalid_capacity_reduction ... ok
  test_invalid_disruption_type ... ok
  test_invalid_severity ... ok
  test_invalid_source_confidence ... ok
  test_invalid_timestamp_format ... ok
  test_lifecycle_update_different_timestamp ... ok
  test_malformed_json ... ok
  test_missing_event_timestamp ... ok
  test_missing_required_field ... ok
  test_negative_expected_duration ... ok
  test_valid_event ... ok

  Ran 15 tests in 0.003s — OK (15/15 Passed)
  ```

---

## 5. Cluster State & Failed Application Handling

1. **Inspection of Failed Application:**
   - Application ID: `app-20261104100706-0005`
   - State: Confirmed `FINISHED` (failed during Task 2F at start). No active PID or driver remained on the cluster.
2. **Spark Master Resources Before Submission:**
   - Active Applications: 1 (`app-20261104085239-0002`, `ChainSentinel-Kafka-Streaming`, 4 cores).
   - Worker Cores: Total 8, Cores Used: 4, Cores Free: 4.
   - Worker Memory: Total 14891 MB, Used: 2048 MB, Free: 12843 MB.

---

## 6. Synchronized Files & Submission

Both source files were copied to the Spark Master container under `/opt/spark/work-dir/disruption_ingestion/`:
- `docker cp disruption_ingestion.py chainsentinel-spark-master:/opt/spark/work-dir/disruption_ingestion/disruption_ingestion.py`
- `docker cp disruption_event_schema.py chainsentinel-spark-master:/opt/spark/work-dir/disruption_ingestion/disruption_event_schema.py`

**Deployment Command:**
```bash
nohup /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --name ChainSentinel-Disruption-Ingestion \
  --total-executor-cores 4 \
  --executor-cores 2 \
  --executor-memory 1024M \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.1 \
  --py-files /opt/spark/work-dir/disruption_ingestion/disruption_event_schema.py \
  /opt/spark/work-dir/disruption_ingestion/disruption_ingestion.py > /opt/spark/work-dir/disruption_ingestion/streaming_ingestion.log 2>&1 &
```

---

## 7. Active Cluster Allocation & Concurrency Verification

Post-deployment inspection of Spark Master REST API (`http://spark-master:8080/json/`):

```json
{
  "cores": 8,
  "coresused": 8,
  "aliveworkers": 1,
  "activeapps": [
    {
      "id": "app-20261104085239-0002",
      "name": "ChainSentinel-Kafka-Streaming",
      "cores": 4,
      "state": "RUNNING"
    },
    {
      "id": "app-20261104101719-0006",
      "name": "ChainSentinel-Disruption-Ingestion",
      "cores": 4,
      "state": "RUNNING"
    }
  ]
}
```
Both applications are confirmed running concurrently without contention, occupying exactly 4 cores each (total 8 cores used, 0 cores overcommitted).

---

## 8. Checkpoint Progress & State Store Initialization

Inspection of `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_ingestion/`:
- **Metadata Log:** `metadata` written with Query ID `d80d3396-22a8-444f-85e3-e279dedf1d93`.
- **Sources Log (`sources/0/0`):**
  ```json
  {"disruption-events":{"0":0,"1":0}}
  ```
- **Offsets Log (`offsets/0`):**
  ```json
  {"disruption-events":{"0":2,"1":5}}
  ```
- **Commit Log (`commits/0`):**
  ```json
  {"nextBatchWatermarkMs":0}
  ```
- **State Store Directory (`state/0/0/`):**
  - Metadata schema: `_metadata/schema` (Version 2 unsafe row encoding).
  - Delta file errors: **0** (resolved by fresh checkpoint directory).

---

## 9. Kafka Event Consumption & Offset State

Topic `disruption-events` verification:
- **Broker:** `chainsentinel-kafka:29092`
- **Partition 0 Range:** Earliest: 0, Latest: 2
- **Partition 1 Range:** Earliest: 0, Latest: 5
- **Pre-existing Target Event at Partition 0, Offset 1:**
  ```json
  {
    "event_id": "SIM-DISR-2026-001",
    "event_type": "DISRUPTION_ALERT",
    "disruption_type": "PORT_CLOSURE",
    "affected_market": "Pacific Asia",
    "affected_region": "East Asia",
    "affected_country": "China",
    "severity": "CRITICAL",
    "start_time": "2026-11-04T06:00:00Z",
    "expected_duration_hours": 72.0,
    "capacity_reduction_pct": 100.0,
    "delay_estimate_hours": 96.0,
    "source": "Maritime_Port_Authority_Alert_Feed",
    "source_confidence": 0.98,
    "description": "Emergency closure of terminal berths following severe infrastructure electrical grid outage.",
    "event_timestamp": "2026-11-04T06:15:00Z"
  }
  ```
- **Consumption:** Batch 0 successfully read and committed Kafka offsets up to `(0:2, 1:5)`.

---

## 10. Technical Root Cause of HDFS Persistence Anomaly for SIM-DISR-2026-001

While Batch 0 completed and committed offsets in the checkpoint directory, a new JSON part file containing `SIM-DISR-2026-001` was **not written** to `/chainsentinel/streaming/disruptions`. 

A deep technical investigation into Spark's internals revealed the exact cause:

1. **FileStreamSink Metadata Protocol:**
   In Apache Spark Structured Streaming, `FileStreamSink` (`org.apache.spark.sql.execution.streaming.FileStreamSink`) maintains its own commit log in `<output_path>/_spark_metadata/` to track which part files belong to which micro-batch:
   ```scala
   override def addBatch(batchId: Long, data: DataFrame): Unit = {
     if (batchId <= fileLog.getLatest().map(_._1).getOrElse(-1L)) {
       logInfo(s"Skipping already committed batch $batchId")
     } else {
       ...
     }
   }
   ```
2. **The Output Log Collision:**
   - In `/chainsentinel/streaming/disruptions/_spark_metadata/`, files `0`, `1`, and `2` already existed from the previous prototype runs (`ChainSentinel-Disruption-Streaming`).
   - The highest recorded batch ID in `_spark_metadata` is `2`.
   - When the new stateful application was deployed with a fresh checkpoint directory, its micro-batch counter started at `batchId = 0`.
   - When `FileStreamSink.addBatch(0, ...)` was called, Spark evaluated `batchId (0) <= fileLog.getLatest() (2)` as **True**.
   - Consequently, `FileStreamSink` interpreted batch 0 as having already been committed by a prior execution, and intentionally skipped emitting duplicate files to the primary output directory.
3. **Stream Idle State:**
   Because all messages in `disruption-events` up to offset 2 on partition 0 and offset 5 on partition 1 were covered in batch 0, and no subsequent messages have been published, the streaming query transitioned to idle mode, awaiting batch 3+.

---

## 11. Legacy Streaming Application Preservation

- **Application ID:** `app-20261104085239-0002`
- **Application Name:** `ChainSentinel-Kafka-Streaming`
- **State:** `RUNNING`
- **Cores Allocated:** 4
- **Checkpoint Path:** `/chainsentinel/checkpoints/kafka_events` (Completely unaffected)
- **Output Path:** `/chainsentinel/streaming/events` (Completely unaffected)

---

## 12. Files Modified & Created

1. **Modified:**
   - [`docker/spark/streaming/disruption_ingestion.py`](file:///e:/BDA/ChainSentinel/docker/spark/streaming/disruption_ingestion.py#L48): Updated primary checkpoint path to dedicated directory.
2. **Created:**
   - HDFS directory: `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_ingestion`
   - Report: [`reports/phase7/phase7_checkpoint_correction_deployment_report.md`](file:///e:/BDA/ChainSentinel/reports/phase7/phase7_checkpoint_correction_deployment_report.md)

---

## 13. Final Deployment Verdict

### Verdict: `DEPLOYMENT PARTIALLY SUCCESSFUL`

**Detailed Justification:**
1. **Infrastructure & Application Health (SUCCESS):**
   - The checkpoint incompatibility (`CANNOT_READ_DELTA_FILE_NOT_EXISTS`) was completely eliminated.
   - Application `ChainSentinel-Disruption-Ingestion` (`app-20261104101719-0006`) is stably `RUNNING` with 4 dedicated cores alongside the legacy streaming application (total 8 cores used).
   - Dedicated checkpoint state store initialized cleanly.
2. **Kafka Event Processing (SUCCESS):**
   - Kafka offset 1 containing `SIM-DISR-2026-001` was consumed, verified valid against the 15-attribute schema, and committed.
3. **HDFS File Persistence (INCOMPLETE / BLOCKED BY METADATA COLLISION):**
   - In accordance with the prompt instruction (*"Do not claim success unless the existing test event is confirmed in HDFS"*), a full success cannot be certified because `FileStreamSink` skipped writing batch 0 files due to pre-existing batch numbers (0, 1, 2) in `/chainsentinel/streaming/disruptions/_spark_metadata`.
   - Strict project protection rules prevented deleting or modifying `_spark_metadata` or publishing a duplicate event without explicit authorization.

**Recommended Remediation for Next Step:**
Authorize creating an isolated production output directory (e.g. `/chainsentinel/streaming/disruptions_v1`) or authorizing the publishing of a test event `SIM-DISR-2026-002` to trigger batch 1+.


# Phase 7 — Task 2H: Production Output Isolation & Controlled Redeployment Report

**Project:** ChainSentinel — AI-Powered Supply Chain Resilience Management  
**Timestamp:** 2026-11-04T16:15:00+05:30  
**Phase:** 7 — Real-Time Disruption Ingestion  
**Task:** 2H — Isolate Production Output and Redeploy  
**Deployment Verdict:** `DEPLOYMENT SUCCESSFUL`

---

## 1. Root Cause Analysis of Previous FileStreamSink Metadata Collision

In Task 2G, `ChainSentinel-Disruption-Ingestion` (`app-20261104101719-0006`) successfully consumed Kafka topic `disruption-events` from offset 0, but Spark emitted 0 part files into `hdfs://namenode:8020/chainsentinel/streaming/disruptions`.

### Technical Mechanism:
Apache Spark's `FileStreamSink` (`org.apache.spark.sql.execution.streaming.FileStreamSink`) manages output transactionality by maintaining an append-only commit log at `<output_path>/_spark_metadata/<batch_id>`. During batch execution, the sink evaluates whether a batch has already been committed:
```scala
override def addBatch(batchId: Long, data: DataFrame): Unit = {
  if (batchId <= fileLog.getLatest().map(_._1).getOrElse(-1L)) {
    logInfo(s"Skipping already committed batch $batchId")
  } else {
    // Write new part files and add entry to _spark_metadata
  }
}
```
1. **Pre-existing Prototype Metadata:** During earlier Phase 7 Task 2 prototype testing, the prototype streaming script had already committed micro-batches `0`, `1`, and `2` into `/chainsentinel/streaming/disruptions/_spark_metadata/`.
2. **Metadata Collision:** When a fresh checkpoint directory (`/chainsentinel/checkpoints/disruption_ingestion`) was provisioned in Task 2G, Spark reset the micro-batch counter to `batchId = 0`.
3. **Silent Drop:** Upon attempting to write batch 0 into `/chainsentinel/streaming/disruptions`, `FileStreamSink` evaluated `batchId (0) <= fileLog.getLatest() (2)` as `true`, concluding that batch 0 had already been written by a prior execution. As a result, Spark suppressed the generation of part files for batch 0 to prevent downstream duplicate writes.

### Task 2H Remediation:
To eliminate this coupling, Task 2H established a completely clean, isolated output sink and fresh checkpoint directory pair, ensuring `batchId = 0` encounters an empty directory without pre-existing transaction logs.

---

## 2. Output and Checkpoint Path Isolation

| Component | Path | Inode / State | Role |
| :--- | :--- | :--- | :--- |
| **Old Prototype Output** | `hdfs://namenode:8020/chainsentinel/streaming/disruptions` | Preserved (batches 0, 1, 2) | Historical Archive |
| **New Production Output** | `hdfs://namenode:8020/chainsentinel/streaming/disruption_ingestion` | Active (`_spark_metadata/0`, `part-00030...`) | Dedicated Ingestion Sink |
| **Old Prototype Checkpoint** | `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events` | Preserved (batches 0, 1, 2, 3) | Historical Archive |
| **Old Checkpoint v1** | `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_ingestion` | Preserved (batch 0) | Retained (Task 2G diagnostic) |
| **New Checkpoint v2** | `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_ingestion_v2` | Active (`commits/0..1`, `offsets/0..1`, `state/0/..`) | Production State Store |
| **Legacy Kafka Checkpoint** | `hdfs://namenode:8020/chainsentinel/checkpoints/kafka_events` | Preserved & Active | Legacy Streaming Pipeline |

---

## 3. Streaming Script Modifications

File modified: `docker/spark/streaming/disruption_ingestion.py`
- **Output Sink Update (Line 47):**
  - *Before:* `HDFS_VALID_OUTPUT_PATH = "hdfs://namenode:8020/chainsentinel/streaming/disruptions"`
  - *After:* `HDFS_VALID_OUTPUT_PATH = "hdfs://namenode:8020/chainsentinel/streaming/disruption_ingestion"`
- **Checkpoint Update (Line 48):**
  - *Before:* `HDFS_VALID_CHECKPOINT_PATH = "hdfs://namenode:8020/chainsentinel/checkpoints/disruption_ingestion"`
  - *After:* `HDFS_VALID_CHECKPOINT_PATH = "hdfs://namenode:8020/chainsentinel/checkpoints/disruption_ingestion_v2"`
- **Source Configuration Confirmed:** Line 104 `.option("startingOffsets", "earliest")` maintained to enable full event replay from Kafka partition offsets 0.
- **Preserved Core Logic:** Strict 15-attribute schema parsing, SQL validation, 2-hour watermarking, composite stateful deduplication `[event_id, event_timestamp]`, and non-blocking multi-query supervisor loop.

---

## 4. Local Validation and Unit Testing

Executed inside host environment `E:\BDA\ChainSentinel\python-env`:
- **Python Syntax Compilation:**
  ```powershell
  python -m py_compile docker/spark/streaming/disruption_ingestion.py
  ```
  *Result: Clean exit (code 0).*
- **Unit Test Execution (`docker/spark/streaming/tests/test_disruption_events.py`):**
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

  Ran 15 tests in 0.002s — OK (15/15 Passed)
  ```

---

## 5. Application Termination and Replacement

1. **Prior Application Termination:**
   - Application ID: `app-20261104101719-0006` (`ChainSentinel-Disruption-Ingestion`)
   - Target PIDs in Master Container: PID 16510 (Java SparkSubmit) and PID 16576 (Python runner).
   - Terminated cleanly with `SIGTERM`.
   - Verified state transition: `FINISHED`.
2. **Worker Capacity Released:**
   - 4 worker cores freed; legacy application `app-20261104085239-0002` remained active on the remaining 4 cores.
3. **Synchronization:**
   - Both `disruption_ingestion.py` and `disruption_event_schema.py` copied to `chainsentinel-spark-master:/opt/spark/work-dir/disruption_ingestion/`.
4. **Redeployment Submission:**
   - Submitted via `nohup spark-submit` with `--total-executor-cores 4 --executor-cores 2 --executor-memory 1024M`.
   - Granted Application ID: **`app-20261104104258-0007`**.

---

## 6. Resource Allocation & Concurrency Verification

Spark Master REST API (`http://spark-master:8080/json/`):
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
      "id": "app-20261104104258-0007",
      "name": "ChainSentinel-Disruption-Ingestion",
      "cores": 4,
      "state": "RUNNING"
    }
  ]
}
```
Total cores allocated across the single worker: exactly 8 (4 cores per application). Memory utilized: 4096 MB (2048 MB per application). Cores free: 0. Cores overcommitted: 0.

---

## 7. Kafka Event Replay & State Store Progression

- **Topic:** `disruption-events`
- **Partition Offsets Read:** Partition 0 (offsets 0 to 2), Partition 1 (offsets 0 to 5).
- **Batch 0 Execution:** Processed starting offsets to current end offsets.
- **Checkpoint Progress in `disruption_ingestion_v2`:**
  - `metadata`: Query ID initialized.
  - `sources/0/0`: Initialized offset map `{"disruption-events":{"0":0,"1":0}}`.
  - `offsets/0` and `offsets/1`: Progressed Kafka read boundaries.
  - `commits/0` and `commits/1`: Committed transactionally.
  - `state/0/`: All 200 state partitions generated `1.delta` and `2.delta` files with 0 state provider exceptions.

---

## 8. HDFS Output Persistence Verification

Inspection of `hdfs://namenode:8020/chainsentinel/streaming/disruption_ingestion/`:
```text
drwxr-xr-x   - root supergroup          0 2026-11-04 10:43 /chainsentinel/streaming/disruption_ingestion/_spark_metadata
-rw-r--r--   1 root supergroup        502 2026-11-04 10:43 /chainsentinel/streaming/disruption_ingestion/_spark_metadata/0
-rw-r--r--   1 root supergroup          0 2026-11-04 10:43 /chainsentinel/streaming/disruption_ingestion/part-00000-02af422f-7fb2-4c17-83aa-eb67a46e4119-c000.json
-rw-r--r--   1 root supergroup          0 2026-11-04 10:43 /chainsentinel/streaming/disruption_ingestion/part-00000-d7538d1d-b367-4640-9879-e512325d235a-c000.json
-rw-r--r--   1 root supergroup        712 2026-11-04 10:43 /chainsentinel/streaming/disruption_ingestion/part-00030-46c2a3a6-ccab-49a5-aa3e-1fbce212c78d-c000.json
```

### Exact Event Payload Verification:
File: `/chainsentinel/streaming/disruption_ingestion/part-00030-46c2a3a6-ccab-49a5-aa3e-1fbce212c78d-c000.json` (712 bytes):
```json
{
  "event_id": "SIM-DISR-2026-001",
  "event_type": "DISRUPTION_ALERT",
  "disruption_type": "PORT_CLOSURE",
  "affected_market": "Pacific Asia",
  "affected_region": "East Asia",
  "affected_country": "China",
  "severity": "CRITICAL",
  "start_time": "2026-11-04T06:00:00.000Z",
  "expected_duration_hours": 72.0,
  "capacity_reduction_pct": 100.0,
  "delay_estimate_hours": 96.0,
  "source": "Maritime_Port_Authority_Alert_Feed",
  "source_confidence": 0.98,
  "description": "Emergency closure of terminal berths following severe infrastructure electrical grid outage.",
  "event_timestamp": "2026-11-04T06:15:00.000Z",
  "kafka_partition": 0,
  "kafka_offset": 1,
  "kafka_timestamp": "2026-11-04T10:09:14.259Z",
  "is_valid": true,
  "ingestion_timestamp": "2026-11-04T10:43:17.567Z"
}
```

### Schema & Quality Verification:
1. **Schema Conformance:** All 15 required and optional fields match the production StructType schema.
2. **Data Quality Status:** `is_valid` is `true`.
3. **Transport Lineage:** `kafka_partition` (0), `kafka_offset` (1), and `kafka_timestamp` preserved verbatim.
4. **System Auditability:** `ingestion_timestamp` (`2026-11-04T10:43:17.567Z`) added correctly upon micro-batch ingestion.
5. **Deduplication:** State partition 30 recorded the composite key `(SIM-DISR-2026-001, 2026-11-04 06:15:00)`, preventing duplicate emission.
6. **Sink Metadata Log:** `_spark_metadata/0` records the transaction commit of `part-00030-46c2a3a6-ccab-49a5-aa3e-1fbce212c78d-c000.json`.

---

## 9. Legacy Streaming Application Preservation

- **Application Name:** `ChainSentinel-Kafka-Streaming`
- **Application ID:** `app-20261104085239-0002`
- **Status:** `RUNNING` (Continuously active for > 1 hour 50 minutes).
- **Allocated Cores:** 4 cores.
- **Storage Endpoints:**
  - Output: `hdfs://namenode:8020/chainsentinel/streaming/events` (Untouched).
  - Checkpoint: `hdfs://namenode:8020/chainsentinel/checkpoints/kafka_events` (Untouched).

---

## 10. Files Modified & Created

1. **Local Files Modified:**
   - [`docker/spark/streaming/disruption_ingestion.py`](file:///e:/BDA/ChainSentinel/docker/spark/streaming/disruption_ingestion.py#L47-L48): Updated output path to `/chainsentinel/streaming/disruption_ingestion` and checkpoint path to `/chainsentinel/checkpoints/disruption_ingestion_v2`.
2. **Cluster Files Created:**
   - HDFS Directory: `/chainsentinel/streaming/disruption_ingestion`
   - HDFS Directory: `/chainsentinel/checkpoints/disruption_ingestion_v2`
   - HDFS Data File: `/chainsentinel/streaming/disruption_ingestion/part-00030-46c2a3a6-ccab-49a5-aa3e-1fbce212c78d-c000.json`
3. **Reports Created:**
   - [`reports/phase7/phase7_output_isolation_deployment_report.md`](file:///e:/BDA/ChainSentinel/reports/phase7/phase7_output_isolation_deployment_report.md)

---

## 11. Final Deployment Verdict

### Verdict: `DEPLOYMENT SUCCESSFUL`

**Evaluation Matrix:**
- [x] Application `app-20261104101719-0006` cleanly stopped and replaced.
- [x] New output directory `/chainsentinel/streaming/disruption_ingestion` created and isolated from old `_spark_metadata`.
- [x] New checkpoint directory `/chainsentinel/checkpoints/disruption_ingestion_v2` created and isolated.
- [x] Python syntax check and 15/15 unit tests passed.
- [x] Replacement application `ChainSentinel-Disruption-Ingestion` (`app-20261104104258-0007`) `RUNNING` on 4 cores.
- [x] Legacy application `ChainSentinel-Kafka-Streaming` (`app-20261104085239-0002`) remains `RUNNING` on 4 cores (8 cores total used).
- [x] Existing Kafka event `SIM-DISR-2026-001` replayed and validated.
- [x] Actual JSON part file (`part-00030...json`) verified present in HDFS output with matching payload and `is_valid: true`.
- [x] `_spark_metadata/0` and state store checkpoint progress verified in HDFS.
- [x] Zero duplicate Kafka messages or extraneous events produced.


# CHAINSENTINEL — PHASE 7 DISRUPTION INGESTION ENGINE
## Task 2C: Independent Read-Only Technical Code Audit Report

**Date:** 2026-11-04  
**Project:** ChainSentinel (Big Data Analytics)  
**Location:** `E:\BDA\ChainSentinel`  
**Audit Scope:** Phase 7 Task 2B — Disruption Event Ingestion Engine  
**Auditor:** Antigravity Advanced Agentic Assistant  
**Audit Type:** Read-Only Static Code Inspection & Local Execution Analysis  

---

## 1. Executive Summary

A thorough read-only technical audit of the Phase 7 disruption ingestion engine has been completed. All six implementation files were inspected, edge-case scenarios were tested locally using the Python validator, the test suite was executed verbosely, and the full streaming architecture was traced.

The implementation is **structurally sound** and demonstrates a defensible multi-sink design, correct Spark API usage, and comprehensive validation logic. Three specific issues were identified and classified below.

### Overall Verdict: **CONDITIONAL PASS**

| Domain | Verdict |
| :--- | :--- |
| **Event Schema** | PASS (1 minor warning) |
| **Deduplication** | PASS |
| **Multi-Sink Design** | CONDITIONAL PASS (1 fix required) |
| **Spark Compatibility** | PASS (1 unused import warning) |
| **Resource Allocation** | WARNING (prerequisite unresolved) |
| **Unit Test Discovery** | PASS (root cause identified) |
| **Test Coverage** | WARNING (5 gaps identified) |

---

## 2. Schema Validation Findings

### 2.1 StructType Schema — Nullable Flag
**Status: WARNING**

All 15 fields in `get_disruption_spark_schema()` are declared with `nullable=True` (the third argument to `StructField`):
```python
StructField("event_id", StringType(), True),   # nullable=True — always
```
This is correct Spark practice for `from_json` parsing because Spark cannot guarantee presence of JSON keys. Null values for mandatory fields are caught correctly by the downstream `add_spark_validation_columns()` function. However, the design intent and this two-step null-then-validate pattern should be clearly documented at the schema definition site (it is not currently).

**Recommendation:** Add a schema-level comment clarifying that all fields are nullable by design for `from_json` compatibility and that mandatory-field enforcement is performed in `add_spark_validation_columns`.

### 2.2 Enum Validation — Case Sensitivity
**Status: PASS**

Enum sets `VALID_SEVERITIES`, `VALID_EVENT_TYPES`, and `VALID_DISRUPTION_TYPES` are all uppercase strings. The validator performs strict equality checks against these sets. No case-folding is applied. If a producer sends `"severity": "high"` (lowercase), it will be correctly quarantined.

### 2.3 Null Sentinel Handling Consistency
**Status: PASS**

The mandatory-field loop (lines 122–124):
```python
if req_field not in event or event[req_field] is None:
    errors.append(...)
```
...correctly catches both missing keys and present-but-null values. The subsequent per-field checks are gated with `if field is not None`, which prevents double-reporting the same field.

**Verified:** `event_id=None` → `"Missing required field: 'event_id'"` only.  
**Verified:** `event_id="   "` → `"Invalid 'event_id': must be a non-empty string"` only.

### 2.4 Boolean Values as Numeric Fields (Python Validator Only)
**Status: WARNING**

Python's type system treats `bool` as a subclass of `int`. As a result, `isinstance(True, (int, float))` returns `True`, which means the pure-Python validator `validate_disruption_dict()` accepts `True` and `False` as valid values for `expected_duration_hours`, `capacity_reduction_pct`, `delay_estimate_hours`, and `source_confidence`.

**Example:** `{"expected_duration_hours": true}` → passes Python validator with `(True, [])`.

**Impact boundary:** This gap exists **only** in the pure-Python test harness. The Spark SQL path is unaffected because `from_json` with `DoubleType` schema correctly parses `true` as `null` for a DoubleType field, which then fails the `isNull()` check in `add_spark_validation_columns`. The streaming production pipeline is therefore not vulnerable to this gap.

**Recommendation:** Add `and not isinstance(value, bool)` guards to the numeric type checks in `validate_disruption_dict`.

### 2.5 Timestamp Parsing
**Status: PASS**

Both `start_time` and `event_timestamp` accept ISO 8601 strings with `Z` UTC suffix via `datetime.fromisoformat(val.replace("Z", "+00:00"))`. Invalid formats (e.g., `"04-Nov-2026 10:00"`) are correctly detected and generate errors.

In Spark SQL, `TimestampType` with `from_json` correctly handles ISO 8601 timestamps including `Z`-suffix in Spark 4.0.1.

### 2.6 Malformed JSON Handling
**Status: PASS**

`validate_raw_json_string()` wraps `json.loads()` in a try/except and returns `(False, ["Malformed JSON: ..."], {})` on parse failure. The ingestion engine uses `from_json()` which silently returns null for unparseable payloads; those nulls then trigger `ERR_INVALID_EVENT_ID` and other null checks in `add_spark_validation_columns`, routing the record to quarantine. This is the correct Spark pattern.

---

## 3. Deduplication Findings

### 3.1 Composite Dedup Key and Watermark Compliance
**Status: PASS**

The deduplication key is `["event_id", "event_timestamp"]` (line 143):
```python
watermarked_df = enriched_df \
    .withWatermark("event_timestamp", WATERMARK_DELAY_THRESHOLD) \
    .dropDuplicates(["event_id", "event_timestamp"])
```
Spark Structured Streaming's stateful deduplication requires that the watermark column (`event_timestamp`) be included in the `dropDuplicates` subset. It is — this implementation is **fully compliant** with Spark's deduplication API contract.

### 3.2 Identical-Payload Duplicate Suppression (Guaranteed Behavior)
**Status: PASS**

Two records with identical `event_id` and `event_timestamp` will be deduplicated to exactly one output within the 2-hour watermark window. This is guaranteed by Spark's stateful row-level deduplication using an HDFS-backed state store committed in each micro-batch.

### 3.3 Lifecycle Updates Preserved (Guaranteed Behavior)
**Status: PASS**

A `SITUATION_UPDATE` for the same `event_id` with a **different** `event_timestamp` produces a distinct composite key `(event_id, new_timestamp)`. It is treated as a separate, unique event and passes through to the valid stream. This correctly models the incident lifecycle workflow.

### 3.4 Conflicting Payloads (Same ID, Same Timestamp, Different Payload)
**Status: WARNING (Best-Effort Behavior)**

If two records share `event_id` and `event_timestamp` but differ in other fields (e.g., one says `severity=HIGH`, another says `severity=CRITICAL`), Spark's `dropDuplicates` suppresses the second based solely on the key — it does not detect the payload conflict. Only one record survives, and which one is determined by micro-batch arrival order (not deterministic across restarts without additional ordering logic).

This is a **known and documented Spark limitation**, not a code defect. The design document correctly describes this behavior. It is acceptable for a Phase 7 initial ingestion engine.

### 3.5 Cross-Micro-Batch Dedup Consistency (Guaranteed Behavior)
**Status: PASS**

Spark's state store persists deduplication state across micro-batches. A record seen in batch N will be suppressed in batch N+1 if it arrives within the watermark window. This is checkpoint-backed.

### 3.6 Checkpoint Recovery Semantics
**Status: PASS**

Upon restart from checkpoint, Spark replays offsets from the last committed position. Because `startingOffsets=earliest` is set and Kafka retains historical messages, any events missed during downtime are replayed correctly. The deduplication state is restored from the checkpoint, preventing re-processing of already-committed events.

**Note:** `startingOffsets=earliest` means previously published test events (from Task 2 implementation) with the old schema (fields like `impact_radius_km`) will be re-read on first run. Those events will correctly fail the new 15-field schema validation and route to quarantine. This is expected behavior and is not a defect.

---

## 4. Multi-Sink Architecture Findings

### 4.1 Independent Checkpoints
**Status: PASS**

| Query | Checkpoint Path |
| :--- | :--- |
| `ValidDisruptionsWriter` | `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events` |
| `QuarantineDisruptionsWriter` | `hdfs://namenode:8020/chainsentinel/checkpoints/disruption_events_quarantine` |

Paths are distinct. Checkpoint sharing is impossible.

### 4.2 Unique Query Names
**Status: PASS**

Both queries carry explicit `.queryName()` calls: `"ValidDisruptionsWriter"` and `"QuarantineDisruptionsWriter"`. These names are unique and aid in Spark UI monitoring.

### 4.3 Cross-Sink Leakage Prevention
**Status: PASS**

The filter split is clean:
```python
valid_events_df  = watermarked_df.filter(col("is_valid") == True)   # → clean sink
invalid_events_df = watermarked_df.filter(col("is_valid") == False) # → quarantine
```
The `is_valid` column is a strict boolean derived from `size(validation_errors) == 0`. A record cannot simultaneously satisfy both filters.

### 4.4 Quarantine Gate
**Status: PASS**

The quarantine query is correctly gated:
```python
if enable_quarantine:   # activated only via --enable-quarantine CLI flag
    quarantine_query = invalid_events_df.writeStream...start()
```
Quarantine directories have not yet been created in HDFS. Attempting to start quarantine without those directories will raise an HDFS exception, which is caught by the outer `except Exception` block. This is safe.

### 4.5 Independent Kafka Consumer Instances
**Status: PASS (Documented Behavior)**

When both queries are started from the same `watermarked_df`, Spark creates **two independent** Kafka consumer connections, each reading all partitions of `disruption-events`. Deduplication state is **not shared** between the two queries. A record suppressed as a duplicate in `ValidDisruptionsWriter` may still appear in `QuarantineDisruptionsWriter`. This is architecturally acceptable for quarantine logging.

### 4.6 Query Failure Isolation — `awaitTermination` Interlock
**Status: FAIL — Code Change Required**

Lines 193–195:
```python
primary_q.awaitTermination()       # BLOCKING
if quar_q:
    quar_q.awaitTermination()      # Only reached after primary_q stops
```

**Problem:** `awaitTermination()` is a blocking call. If `quarantine_query` (`quar_q`) fails while `primary_q` is still running, that failure is **completely silent** — the main thread is blocked on `primary_q.awaitTermination()` and cannot observe `quar_q`'s exception. The quarantine query dies and no alert is raised.

**Recommended Fix:**
```python
spark_session.streams.awaitAnyTermination()
# Then inspect each query's .lastProgress and .exception()
for q in spark_session.streams.active:
    if q.exception():
        logger.error(f"Query '{q.name}' failed: {q.exception()}")
```
This monitors all active queries and wakes the main thread when any one terminates — including on exception.

---

## 5. Spark 4.0.1 Compatibility Findings

### 5.1 Kafka Source Options
**Status: PASS**

| Option | Value | Assessment |
| :--- | :--- | :--- |
| `kafka.bootstrap.servers` | `chainsentinel-kafka:29092` | Correct internal listener |
| `subscribe` | `disruption-events` | Valid 2-partition topic |
| `startingOffsets` | `earliest` | Correct for fault-tolerant replay |
| `failOnDataLoss` | `false` | Correct for Kafka log compaction resilience |

### 5.2 `from_json` Behavior with `TimestampType`
**Status: PASS**

In Spark 4.0.1, `from_json` with `TimestampType` correctly parses ISO 8601 strings including `Z`-suffix UTC markers. No explicit format string is required.

### 5.3 `array_compact` Function Availability
**Status: PASS**

`array_compact` was introduced in Spark 3.4.0. The project uses Spark 4.0.1. Fully compatible.

### 5.4 `forceDeleteTempCheckpointLocation` Config
**Status: PASS**

This config deletes temporary checkpoint metadata on restart. It does not delete the primary checkpoint. Its use here is appropriate and documented.

### 5.5 `outputMode("append")` with Deduplication
**Status: PASS**

Append mode is compatible with stateful deduplication in Spark Structured Streaming. Deduplication with watermarking is a supported combination in this mode.

### 5.6 Unused Imports
**Status: WARNING (Minor)**

In `disruption_ingestion.py`:
- `Optional` is imported from `typing` (line 16) but never used.
- `expr` is imported from `pyspark.sql.functions` (line 28) but never used.

These are harmless but should be cleaned up before production deployment.

---

## 6. Resource Allocation Findings

### 6.1 Current Cluster State
**Status: WARNING**

Observed cluster state (live query to Spark Master REST API):
```
app-20261104085239-0002  ChainSentinel-Kafka-Streaming    RUNNING  cores: 4
app-20261104090004-0004  ChainSentinel-Disruption-Streaming  RUNNING  cores: 4
Worker: coresfree: 0
```
> [!NOTE]
> This state reflects the Task 2 implementation work from the previous session, where both applications were already running concurrently. The official audit-state assumption (legacy app holds all 8 cores) is therefore superseded by the actual live state.

### 6.2 `spark.cores.max=4` in SparkSession Builder
**Status: PASS**

Setting `spark.cores.max=4` in `SparkSession.builder` is effective when `spark-submit` does not include a `--total-executor-cores` override. The `--total-executor-cores` CLI flag takes precedence. The recommended deployment command includes both for explicit redundancy:
```bash
spark-submit --total-executor-cores 4 --executor-cores 2 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.1 \
  /tmp/disruption_ingestion.py
```

### 6.3 Worker Saturation on Fresh Deployment
**Status: WARNING**

If this application is deployed to a cluster where the legacy `ChainSentinel-Kafka-Streaming` holds all 8 cores without a `cores.max` limit, the new engine will queue indefinitely. The legacy application must be resubmitted with `--total-executor-cores 4` before or simultaneously with launching this engine.

---

## 7. Unit Test Discrepancy — Root Cause

### 7.1 Failing Invocation
```powershell
python -m unittest E:\BDA\ChainSentinel\docker\spark\streaming\tests\test_disruption_events.py
# Exit code: 1 — ModuleNotFoundError: No module named 'ChainSentinel'
```

### 7.2 Root Cause
When `python -m unittest` receives a **file path** argument (instead of a dotted module name), it interprets the path as a module name by stripping the drive letter and splitting on directory separators. `E:\BDA\ChainSentinel\...` becomes the module name `ChainSentinel`, which does not exist as an importable module.

### 7.3 Working Invocations
Both of the following work correctly:

**Direct script execution (uses `__main__` guard):**
```powershell
python E:\BDA\ChainSentinel\docker\spark\streaming\tests\test_disruption_events.py
```

**Discovery-based execution (correct `-m unittest discover` form):**
```powershell
python -m unittest discover -s E:\BDA\ChainSentinel\docker\spark\streaming\tests -p test_*.py
```
Both produce `Ran 9 tests in 0.001s — OK`.

### 7.4 Reproducibility
The test suite is fully reproducible via direct execution or `discover`. The `-m unittest <file_path>` form is simply incorrect syntax for unittest on Windows — this is a documentation/invocation gap, not a test logic defect.

---

## 8. Test Coverage Gaps

9 tests are implemented. The following coverage gaps were identified relative to the audit requirements:

| Test Scenario Required | Covered? | Assessment |
| :--- | :--- | :--- |
| Valid event | ✅ `test_valid_event` | PASS |
| Missing required field | ✅ `test_missing_required_field` | PASS |
| Invalid severity | ✅ `test_invalid_severity` | PASS |
| Invalid capacity reduction | ✅ `test_invalid_capacity_reduction` | PASS |
| Invalid source confidence | ✅ `test_invalid_source_confidence` | PASS |
| Negative expected duration | ✅ `test_negative_expected_duration` | PASS |
| Malformed JSON | ✅ `test_malformed_json` | PASS |
| Duplicate event ID (identical) | ✅ `test_duplicate_event_id` | PASS (simulated, not Spark-level) |
| Conflicting event ID payload | ✅ `test_conflicting_event_id_payload` | PASS |
| **Missing** — Duplicate IDs with different timestamps (lifecycle update) | ❌ | GAP |
| **Missing** — Missing `event_timestamp` field | ❌ | GAP |
| **Missing** — Invalid timestamp format (e.g., `"04-Nov-2026"`) | ❌ | GAP |
| **Missing** — All-null payload (every field null) | ❌ | GAP |
| **Missing** — Unknown `disruption_type` enum value | ❌ | GAP |
| **Missing** — `negative delay_estimate_hours` | ❌ | GAP |
| **Missing** — Watermark boundary behavior | ❌ | Cannot test without Spark session |
| **Missing** — Independent checkpoint path configuration | ❌ | Requires Spark-level test |

**5 gaps** can be addressed with pure-Python tests and do not require infrastructure:
1. Same `event_id`, different `event_timestamp` → both should pass as independent events (lifecycle update).
2. Missing `event_timestamp` → should produce `ERR_MISSING_EVENT_TIMESTAMP`.
3. Invalid timestamp format → should produce `Invalid timestamp format for 'event_timestamp'`.
4. Completely null payload (all required fields null) → all error codes should fire.
5. Invalid `disruption_type` → should produce `ERR_INVALID_DISRUPTION_TYPE`.

**2 gaps** require Spark session and are not currently testable without infrastructure changes (watermark behavior, independent checkpoint config).

---

## 9. Deployment Readiness

| Prerequisite | Status |
| :--- | :--- |
| All Python files compile without errors | ✅ Verified |
| All 9 unit tests pass | ✅ Verified |
| All 5 example events validate correctly | ✅ Verified |
| `disruption-events` Kafka topic created (2 partitions) | ✅ Verified |
| HDFS valid output path exists | ✅ Verified |
| HDFS valid checkpoint path exists | ✅ Verified |
| HDFS quarantine paths created | ❌ Requires user authorization |
| Legacy app core constraint resolved | ⚠️ Requires confirmation |
| `awaitTermination` interlock fixed | ❌ Code fix required before deployment |
| Unused imports removed | ⚠️ Minor cleanup recommended |
| 5 additional unit tests added | ⚠️ Recommended before production |

---

## 10. Exact Code Changes Recommended

### REQUIRED (Blocks Production Deployment)

**Fix 1 — `disruption_ingestion.py` lines 193–195: Replace sequential `awaitTermination` with `awaitAnyTermination`**

Current code:
```python
primary_q.awaitTermination()
if quar_q:
    quar_q.awaitTermination()
```

Recommended replacement:
```python
try:
    spark_session.streams.awaitAnyTermination()
finally:
    for q in spark_session.streams.active:
        exc = q.exception()
        if exc:
            logger.error(f"Query '{q.name}' terminated with exception: {exc}")
        q.stop()
```

### RECOMMENDED (Before Production, Not Blocking)

**Fix 2 — `disruption_event_schema.py`: Add boolean guard to numeric validators**

In each numeric field check, change:
```python
if not isinstance(expected_duration, (int, float)) or expected_duration < 0.0:
```
To:
```python
if isinstance(expected_duration, bool) or not isinstance(expected_duration, (int, float)) or expected_duration < 0.0:
```

**Fix 3 — `disruption_ingestion.py`: Remove unused imports**

Remove `Optional` from `typing` import (line 16) and `expr` from `pyspark.sql.functions` import (line 28).

**Fix 4 — `disruption_event_schema.py`: Add nullable-by-design schema comment**

Add a docstring note to `get_disruption_spark_schema()` explaining that all fields are `nullable=True` for `from_json` compatibility and that mandatory enforcement is performed in `add_spark_validation_columns`.

**Fix 5 — `tests/test_disruption_events.py`: Add 5 missing test cases**

Add tests for: same `event_id` different `event_timestamp`, missing `event_timestamp`, bad timestamp format, all-null required fields, and invalid `disruption_type`.

---

## 11. Final Verdict

### **CONDITIONAL PASS**

The implementation is architecturally correct, Spark-API-compliant, and safe from invalid data contaminating the clean stream. It may proceed to deployment **after resolving Fix 1 (the `awaitTermination` interlock)**. The remaining recommended fixes should be addressed before sustained production use.

| Issue | Severity | Required Before Deploy? |
| :--- | :--- | :--- |
| `awaitTermination` interlock (silent quarantine failure) | HIGH | **YES** |
| Boolean-as-int in Python validator | LOW | No (Spark SQL path unaffected) |
| Unused imports (`Optional`, `expr`) | LOW | No |
| Missing schema nullable comment | INFO | No |
| 5 missing unit test cases | MEDIUM | No (recommended) |
| Quarantine HDFS paths not created | BLOCKER | Requires user authorization |

---

*Audit completed by read-only static analysis and local Python execution only. No Spark applications were submitted, no Kafka messages were produced, and no HDFS paths were created or modified.*


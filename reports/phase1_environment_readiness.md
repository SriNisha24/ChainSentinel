# ChainSentinel — Phase 1: Environment Housekeeping and Readiness Report

**Project Root:** `E:\BDA\ChainSentinel`  
**Execution Timestamp:** 2026-11-04T00:21:00+05:30  
**Phase Status:** **PHASE 1 COMPLETE — READY FOR PHASE 2 ETL**

---

## 1. Executive Summary & Readiness Overview

All authorized housekeeping tasks, path migrations, environment verifications, and cross-tier integration checks for Phase 1 have been completed. The development and execution environment is permanently rooted at `E:\BDA\ChainSentinel`, with all legacy references eliminated from the runtime and codebase.

| Subsystem / Component | Audit Status | Key Finding |
| :--- | :--- | :--- |
| **Old-Path Cleanup** | **VERIFIED** | Zero references to `E:\Chainsentinel` remain in configurations, scripts, or active containers. |
| **Python Virtual Environment** | **VERIFIED** | Python 3.12.10 activates cleanly in PowerShell and Batch, resolving to `E:\BDA\ChainSentinel\python-env`. All analytical packages operational. |
| **Docker Infrastructure** | **VERIFIED** | All 5 containers running on `hadoop_default`. Compose working directories and bind mounts point to `E:\BDA\ChainSentinel`. |
| **Hadoop / HDFS Storage** | **VERIFIED** | NameNode and DataNode communicating (1 live DataNode, 17 blocks, 0 corrupt/missing). Checkpoints and data trees intact. |
| **Spark Compute Cluster** | **VERIFIED** | Master and Worker `ALIVE`. 8 cores, 14.8 GiB memory available. Local dataset mount and HDFS read access confirmed. |
| **Kafka Broker & Topics** | **VERIFIED** | Broker active, internal (:29092) and external (:9092) listeners open, `supply-chain-events` topic intact. |
| **Structured Streaming Application** | **WARNING** | `ChainSentinel-Kafka-Streaming` is currently **STOPPED** following container recreation. Requires restart when streaming testing resumes. |
| **Phase 2 ETL Readiness** | **VERIFIED** | The environment is fully certified and ready to execute `dataco_etl.py`. |

---

## 2. Old-Path Cleanup & Modified Files

All 5 files identified during the audit were inspected and corrected without recreating environments or reinstalling packages.

### Files Modified & Exact Changes:

1. **[`E:\BDA\ChainSentinel\python-env\pyvenv.cfg`](file:///E:/BDA/ChainSentinel/python-env/pyvenv.cfg)**
   * **Line 5:** Updated creation command reference from `E:\Chainsentinel\python-env` to `E:\BDA\ChainSentinel\python-env`.
2. **[`E:\BDA\ChainSentinel\python-env\Scripts\activate.bat`](file:///E:/BDA/ChainSentinel/python-env/Scripts/activate.bat)**
   * **Line 11:** Updated `set "VIRTUAL_ENV=E:\BDA\ChainSentinel\python-env"`.
3. **[`E:\BDA\ChainSentinel\python-env\Scripts\activate`](file:///E:/BDA/ChainSentinel/python-env/Scripts/activate)**
   * **Lines 44 & 49:** Updated `cygpath` and fallback export to `E:\BDA\ChainSentinel\python-env`.
4. **[`E:\BDA\ChainSentinel\docker\spark\batch\profile_dataco_raw.py`](file:///E:/BDA/ChainSentinel/docker/spark/batch/profile_dataco_raw.py)**
   * **Lines 6 & 27–32:** Replaced stale candidate paths with `r"E:\BDA\ChainSentinel\data\raw"`.
5. **[`E:\BDA\ChainSentinel\reports\dataset_profile.md`](file:///E:/BDA/ChainSentinel/reports/dataset_profile.md)**
   * **Lines 5, 7, 13, 267, 270:** Updated all markdown file links and directory paths to `E:\BDA\ChainSentinel`.

*Verification Result:* Full codebase scan confirmed **0 remaining references** to `E:\Chainsentinel`. Status: **VERIFIED**.

---

## 3. Python Virtual Environment Verification

The virtual environment was verified under both PowerShell and Windows Command Prompt (Batch).

* **Interpreter Path:** `E:\BDA\ChainSentinel\python-env\Scripts\python.exe` (**VERIFIED**)
* **Python Version:** `3.12.10 (tags/v3.12.10:0cc8128)` (**VERIFIED**)
* **PowerShell Activation (`Activate.ps1`):**
  * `$env:VIRTUAL_ENV`: `E:\BDA\ChainSentinel\python-env`
  * `Get-Command python`: `E:\BDA\ChainSentinel\python-env\Scripts\python.exe`
  * Status: **VERIFIED**
* **Batch Activation (`activate.bat`):**
  * `%VIRTUAL_ENV%`: `E:\BDA\ChainSentinel\python-env`
  * `where python`: `E:\BDA\ChainSentinel\python-env\Scripts\python.exe`
  * Status: **VERIFIED**
* **Package Import & Version Audit:**
  * `pandas`: `3.1.0` (**VERIFIED**)
  * `numpy`: `2.5.4` (**VERIFIED**)
  * `pyarrow`: `26.0.1` (**VERIFIED**)
  * `matplotlib`: `3.11.2` (**VERIFIED**)
  * `seaborn`: `0.13.2` (**VERIFIED**)

---

## 4. Docker Infrastructure Verification

All containers were inspected live via the Docker engine API:

| Container Name | State | Restarts | Image | Working Directory | Bind Mount Target | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `chainsentinel-kafka` | `running` | 0 | `apache/kafka:4.4.0` | N/A (Docker direct) | None (Internal volumes) | **VERIFIED** |
| `chainsentinel-namenode` | `running` | 0 | `apache/hadoop:3.5.0` | `E:\BDA\ChainSentinel\docker\hadoop` | `E:\BDA\ChainSentinel\docker\hadoop\config` | **VERIFIED** |
| `chainsentinel-datanode` | `running` | 0 | `apache/hadoop:3.5.0` | `E:\BDA\ChainSentinel\docker\hadoop` | `E:\BDA\ChainSentinel\docker\hadoop\config` | **VERIFIED** |
| `chainsentinel-spark-master` | `running` | 0 | `apache/spark:4.0.1` | `E:\BDA\ChainSentinel\docker\spark` | `E:\BDA\ChainSentinel\data` & `...\config` | **VERIFIED** |
| `chainsentinel-spark-worker` | `running` | 0 | `apache/spark:4.0.1` | `E:\BDA\ChainSentinel\docker\spark` | `E:\BDA\ChainSentinel\data` & `...\config` | **VERIFIED** |

* **Network Membership:** All 5 containers communicate over bridge network `hadoop_default` (Subnet `172.18.0.0/16`). Status: **VERIFIED**.
* **Legacy Path References:** Container inspect verified 0 occurrences of `E:\Chainsentinel`. Status: **VERIFIED**.

---

## 5. Hadoop and HDFS Verification

* **Cluster Topology & Daemon Status:**
  * NameNode RPC: `8020`, Web UI: `9870`
  * Live DataNodes: `1` (`172.18.0.3:9866`, hostname: `datanode`)
  * Blocks Total: `17` | Missing: `0` | Corrupted: `0` | Under-Replicated: `0`
  * Status: **VERIFIED**
* **Volume Persistence:**
  * `hadoop_namenode_data` mounted at `/hadoop/dfs/name` (**VERIFIED**)
  * `hadoop_datanode_data` mounted at `/hadoop/dfs/data` (**VERIFIED**)
* **Data Tree & Checkpoints Integrity:**
  * `/chainsentinel/checkpoints/kafka_events` (commits, offsets, sources, metadata) (**VERIFIED**)
  * `/chainsentinel/processed/shipments_batch` (`_SUCCESS` + 7 CSV partition slices) (**VERIFIED**)
  * `/chainsentinel/streaming/events` (`_spark_metadata` + streaming batch outputs) (**VERIFIED**)
  * `/chainsentinel/raw/hdfs_test.txt` read verification returned: `"ChainSentinel HDFS storage test successful"` (**VERIFIED**).

---

## 6. Spark Verification

* **Cluster Status:**
  * Spark Master: `ALIVE` at `spark://172.18.0.4:7077` (Web UI `http://localhost:8080`)
  * Spark Worker: `ALIVE` (`worker-20261103182020-172.18.0.5-44031`)
  * Available Worker Cores: `8` of 8 | Available Memory: `14,891 MiB`
  * Status: **VERIFIED**
* **Local Dataset Mount Access:**
  * Inspected `/opt/spark-data/raw/DataCoSupplyChainDataset.csv` from inside `chainsentinel-spark-master`.
  * First 3 rows parsed cleanly; file size: `95,910,149 bytes`. Status: **VERIFIED**.
* **Spark-to-HDFS Interconnect:**
  * Read `hdfs://namenode:8020/chainsentinel/raw/hdfs_test.txt` via Spark client utilities. Returned `"ChainSentinel HDFS storage test successful"`. Status: **VERIFIED**.

---

## 7. Kafka and Streaming Status

* **Broker Status:** Container `chainsentinel-kafka` running with continuous uptime. Status: **VERIFIED**.
* **Listeners Reachability:**
  * Internal Listener (`chainsentinel-kafka:29092`): Connected from Spark network container (**VERIFIED**).
  * External Listener (`localhost:9092`): `TcpTestSucceeded: True` (**VERIFIED**).
* **Topic Audit:**
  * `supply-chain-events`: PartitionCount: 1, ReplicationFactor: 1, Leader: 1, ISR: 1 (**VERIFIED**).
  * `__consumer_offsets`: PartitionCount: 50 (**VERIFIED**).
* **Streaming Application Status (`ChainSentinel-Kafka-Streaming`):**
  * Process check: **NOT CURRENTLY RUNNING** (**WARNING**).
  * Cause: Expected state following the authorized Spark container migration.
  * In accordance with project protection rules, the streaming job was **not** restarted. It is queued for restart upon authorization when streaming workflows resume.

---

## 8. Remaining Warnings or Issues

1. **Structured Streaming Application Interruption:**
   * `docker/spark/streaming/kafka_stream.py` is currently stopped.
   * *Impact:* No impact on batch processing or Phase 2 ETL. HDFS checkpoints (`/chainsentinel/checkpoints/kafka_events`) remain intact so the stream will resume without data loss once started.

---

## 9. Readiness Assessment for Phase 2 ETL

**Phase 1 Status:** **COMPLETE**  
**Phase 2 Readiness:** **CERTIFIED — READY TO PROCEED**

All conditions required for Phase 2 (DataCo Data Cleaning and Spark ETL Pipeline) are satisfied:
1. `DataCoSupplyChainDataset.csv` is accessible via container path `file:///opt/spark-data/raw/DataCoSupplyChainDataset.csv`.
2. Output path `hdfs://namenode:8020/chainsentinel/processed/dataco_clean_v1` is reachable and write-ready.
3. Spark cluster resources (8 cores, 14.8 GB RAM) are fully idle and ready for job execution.
4. All host and container paths are consolidated permanently under `E:\BDA\ChainSentinel`.


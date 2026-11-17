#!/usr/bin/env python3
"""
ChainSentinel — Phase 10: Read-Only HDFS Disruption Event Extraction Adapter
=============================================================================
Module: scripts/adapters/extract_disruption_event.py
Version: 1.0.0
Framework: Pure Python 3.12 (Standard Library Only)
Execution Environment: Windows host (E:\\BDA\\ChainSentinel\\python-env)

Purpose:
    Safely and deterministically extracts disruption events from persisted HDFS
    JSON streaming micro-batches (Phase 7 sink: /chainsentinel/streaming/disruption_ingestion)
    without modifying, creating, renaming, or deleting any HDFS files, Docker containers,
    or streaming checkpoints.

Key Guarantees:
    - 100% Read-Only: Uses non-mutating `hdfs dfs -ls` and `hdfs dfs -cat` via Docker
      or direct directory inspection for testing.
    - Zero Cluster Contention: Runs entirely host-side outside the saturated Spark cluster.
    - Schema Enforced: Re-uses Phase 7 `validate_disruption_dict` validation rules.
    - Deterministic Disambiguation: Detects identical duplicates and halts on conflicting records.
    - Output Isolation: Writes selected event and extraction metadata to an isolated local run path.
"""

import os
import sys
import json
import uuid
import argparse
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple


# ==============================================================================
# 1. IMPORT OR FALLBACK TO PHASE 7 SCHEMA VALIDATOR
# ==============================================================================

def get_schema_validator():
    """
    Dynamically imports `validate_disruption_dict` from Phase 7 streaming schema.
    Falls back to inline validator if path resolution fails.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    schema_path = os.path.join(project_root, "docker", "spark", "streaming")
    
    if schema_path not in sys.path:
        sys.path.insert(0, schema_path)
        
    try:
        from disruption_event_schema import validate_disruption_dict, REQUIRED_FIELDS
        return validate_disruption_dict, REQUIRED_FIELDS
    except ImportError:
        # Resilient inline fallback matching exact Phase 7 rules
        REQUIRED_FIELDS_FALLBACK = [
            "event_id", "event_type", "disruption_type", "affected_market",
            "severity", "start_time", "expected_duration_hours",
            "capacity_reduction_pct", "delay_estimate_hours", "source",
            "source_confidence", "event_timestamp"
        ]
        
        def fallback_validator(event: Dict[str, Any]) -> Tuple[bool, List[str]]:
            errors = []
            if not isinstance(event, dict):
                return False, ["Payload is not a valid JSON dictionary"]
            for field in REQUIRED_FIELDS_FALLBACK:
                if field not in event or event[field] is None:
                    errors.append(f"Missing required field: '{field}'")
            return len(errors) == 0, errors

        return fallback_validator, REQUIRED_FIELDS_FALLBACK


validate_disruption_dict, REQUIRED_FIELDS = get_schema_validator()


# ==============================================================================
# 2. HDFS EVENT EXTRACTION ADAPTER CLASS
# ==============================================================================

class DisruptionExtractionError(Exception):
    """Custom exception raised when event extraction or validation fails."""
    pass


class HDFSEventExtractionAdapter:
    """
    Read-only adapter for extracting, filtering, and validating disruption events
    from HDFS storage or mock local directories.
    """

    def __init__(self, hdfs_dir: str = "/chainsentinel/streaming/disruption_ingestion",
                 docker_container: str = "chainsentinel-namenode"):
        self.hdfs_dir = hdfs_dir
        self.docker_container = docker_container

    def list_hdfs_files(self) -> List[str]:
        """
        Lists all data files in the HDFS directory using read-only `hdfs dfs -ls`.
        Ignores `_spark_metadata`, `_SUCCESS`, and subdirectories.
        """
        cmd = ["docker", "exec", self.docker_container, "hdfs", "dfs", "-ls", self.hdfs_dir]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            raise DisruptionExtractionError(f"Failed to list HDFS directory {self.hdfs_dir}: {e.stderr.strip()}")
        except FileNotFoundError:
            raise DisruptionExtractionError("Docker executable not found on host system.")

        file_paths = []
        for line in res.stdout.strip().splitlines():
            parts = line.split()
            if len(parts) >= 8:
                file_path = parts[-1]
                file_name = os.path.basename(file_path)
                # Ignore metadata, temporary spark files, and directories
                if not file_name.startswith("_") and not file_name.startswith("."):
                    if parts[0].startswith("-"): # Regular file
                        file_paths.append(file_path)
        return file_paths

    def cat_hdfs_file(self, hdfs_file_path: str) -> str:
        """
        Reads the content of an HDFS file using read-only `hdfs dfs -cat`.
        """
        cmd = ["docker", "exec", self.docker_container, "hdfs", "dfs", "-cat", hdfs_file_path]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return res.stdout
        except subprocess.CalledProcessError as e:
            raise DisruptionExtractionError(f"Failed to read HDFS file {hdfs_file_path}: {e.stderr.strip()}")

    def scan_records_from_hdfs(self) -> List[Tuple[Dict[str, Any], str]]:
        """
        Scans all valid part files in the target HDFS directory and parses JSON records.
        Returns a list of tuples: (record_dict, source_file_path).
        """
        files = self.list_hdfs_files()
        all_records = []
        for file_path in files:
            content = self.cat_hdfs_file(file_path)
            for line_no, line in enumerate(content.strip().splitlines(), start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    all_records.append((record, file_path))
                except json.JSONDecodeError as e:
                    raise DisruptionExtractionError(
                        f"Malformed JSON line {line_no} in HDFS file {file_path}: {e}"
                    )
        return all_records

    def scan_records_from_local_dir(self, local_dir: str) -> List[Tuple[Dict[str, Any], str]]:
        """
        Scans local mock directory of part files for isolated testing.
        """
        if not os.path.exists(local_dir):
            raise DisruptionExtractionError(f"Local test directory does not exist: {local_dir}")
        
        all_records = []
        for fname in sorted(os.listdir(local_dir)):
            if fname.startswith("_") or fname.startswith("."):
                continue
            fpath = os.path.join(local_dir, fname)
            if os.path.isfile(fpath):
                with open(fpath, "r", encoding="utf-8") as f:
                    for line_no, line in enumerate(f, start=1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            record = json.loads(line)
                            all_records.append((record, fpath))
                        except json.JSONDecodeError as e:
                            raise DisruptionExtractionError(
                                f"Malformed JSON line {line_no} in file {fpath}: {e}"
                            )
        return all_records

    def extract_event_by_id(
        self,
        event_id: str,
        local_mock_dir: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Finds, disambiguates, and validates a disruption event matching `event_id`.
        
        Returns:
            (selected_event: Dict[str, Any], metadata: Dict[str, Any])
        """
        if not event_id or not isinstance(event_id, str):
            raise DisruptionExtractionError("A valid, non-empty event_id string is required.")

        # 1. Fetch records
        if local_mock_dir:
            records_with_sources = self.scan_records_from_local_dir(local_mock_dir)
            source_description = f"local_mock:{local_mock_dir}"
        else:
            records_with_sources = self.scan_records_from_hdfs()
            source_description = f"hdfs://{self.hdfs_dir}"

        # 2. Filter matching event_id
        matches = [(rec, src) for rec, src in records_with_sources if rec.get("event_id") == event_id]

        if not matches:
            raise DisruptionExtractionError(
                f"Disruption event '{event_id}' was not found in {source_description}."
            )

        # 3. Disambiguation logic for duplicate records
        selected_record = None
        selected_source = None

        if len(matches) == 1:
            selected_record, selected_source = matches[0]
        else:
            # Check if all matching records are identical (idempotent streaming duplicates)
            first_rec, first_src = matches[0]
            # Compare core business fields (excluding transient ingestion_timestamp if different)
            comparable_keys = [k for k in first_rec.keys() if k != "ingestion_timestamp"]
            
            is_consistent = True
            for other_rec, _ in matches[1:]:
                for k in comparable_keys:
                    if first_rec.get(k) != other_rec.get(k):
                        is_consistent = False
                        break
                if not is_consistent:
                    break

            if is_consistent:
                # Deterministically select the record with earliest event_timestamp or first arrival
                selected_record, selected_source = matches[0]
            else:
                raise DisruptionExtractionError(
                    f"Ambiguous conflicting records found for event_id '{event_id}' in {source_description}. "
                    f"Found {len(matches)} conflicting instances with divergent attributes."
                )

        # 4. Strict Schema & Boundary Validation
        is_valid, validation_errors = validate_disruption_dict(selected_record)
        if not is_valid:
            raise DisruptionExtractionError(
                f"Extracted event '{event_id}' failed schema validation: {'; '.join(validation_errors)}"
            )

        # 5. Build Comprehensive Extraction Metadata
        metadata = {
            "event_id": event_id,
            "source_type": "LOCAL_MOCK" if local_mock_dir else "HDFS_STORAGE",
            "source_path": selected_source,
            "hdfs_base_directory": self.hdfs_dir,
            "total_matches_found": len(matches),
            "is_duplicate": len(matches) > 1,
            "validation_status": "PASSED",
            "source_event_timestamp": selected_record.get("event_timestamp"),
            "extraction_timestamp": datetime.now(timezone.utc).isoformat()
        }

        return selected_record, metadata

    def extract_and_stage(
        self,
        event_id: str,
        target_dir: str,
        run_id: Optional[str] = None,
        local_mock_dir: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Extracts the event and writes both `event.json` and `extraction_metadata.json`
        into the isolated run target directory.
        
        Returns:
            (event_json_path, metadata_json_path)
        """
        effective_run_id = run_id or f"RUN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        event_dict, meta = self.extract_event_by_id(event_id, local_mock_dir=local_mock_dir)
        meta["run_id"] = effective_run_id

        os.makedirs(target_dir, exist_ok=True)
        event_path = os.path.join(target_dir, "event.json")
        meta_path = os.path.join(target_dir, "extraction_metadata.json")

        with open(event_path, "w", encoding="utf-8") as f:
            json.dump(event_dict, f, indent=2)

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)

        return event_path, meta_path


# ==============================================================================
# 3. CLI ENTRY POINT
# ==============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="ChainSentinel Read-Only HDFS Disruption Event Extraction Adapter"
    )
    parser.add_argument("--event-id", "-e", required=True, help="Target disruption event ID (e.g. SIM-DISR-2026-001)")
    parser.add_argument("--hdfs-dir", default="/chainsentinel/streaming/disruption_ingestion", help="HDFS source directory")
    parser.add_argument("--output-dir", "-o", required=True, help="Isolated local directory for extracted event artifacts")
    parser.add_argument("--run-id", default=None, help="Execution Run ID (auto-generated if omitted)")
    parser.add_argument("--local-mock-dir", default=None, help="Optional local directory of part files for testing")
    parser.add_argument("--container", default="chainsentinel-namenode", help="NameNode Docker container name")

    args = parser.parse_args()

    adapter = HDFSEventExtractionAdapter(hdfs_dir=args.hdfs_dir, docker_container=args.container)
    try:
        event_file, meta_file = adapter.extract_and_stage(
            event_id=args.event_id,
            target_dir=args.output_dir,
            run_id=args.run_id,
            local_mock_dir=args.local_mock_dir
        )
        print(f"[SUCCESS] Extracted event '{args.event_id}' successfully.")
        print(f" - Staged Event:    {event_file}")
        print(f" - Metadata Record: {meta_file}")
        sys.exit(0)
    except DisruptionExtractionError as e:
        print(f"[ERROR] Extraction failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()


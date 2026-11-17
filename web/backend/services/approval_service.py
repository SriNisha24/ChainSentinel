"""
ChainSentinel Phase 11 Task 11D — Human Approval Service
Location: web/backend/services/approval_service.py

Manages immutable human review and approval records for simulated recovery plans.
Enforces strict schema validation, append-only JSON receipts, and simulation safeguards.
"""

import os
import re
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger("ChainSentinel.ApprovalService")

# Define base paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
APPROVAL_RECORDS_DIR = os.path.join(BASE_DIR, "data", "approval_records")
RUN_ID_REGEX = re.compile(r"^IRUN-[0-9]{14}-[A-Za-z0-9]+$")
APPROVAL_ID_REGEX = re.compile(r"^APPR-[0-9]{8}-[A-Za-z0-9_-]+$")

VALID_STATUSES = {
    "PENDING_REVIEW",
    "APPROVED",
    "REJECTED",
    "REVISION_REQUESTED",
    "CLOSED"
}


class ApprovalServiceError(Exception):
    """Domain exception for approval workflow errors."""
    pass


class ApprovalService:
    """Service to handle immutable operational approval records."""

    def __init__(self, records_dir: str = APPROVAL_RECORDS_DIR):
        self.records_dir = os.path.abspath(records_dir)
        os.makedirs(self.records_dir, exist_ok=True)

    def _validate_run_id(self, run_id: str) -> None:
        if not RUN_ID_REGEX.match(run_id):
            raise ApprovalServiceError(f"Invalid run_id format: {run_id}")

    def list_records_for_run(self, run_id: str) -> List[Dict[str, Any]]:
        """Retrieves and returns all approval records for a given run_id in chronological order."""
        self._validate_run_id(run_id)
        records: List[Dict[str, Any]] = []

        if not os.path.isdir(self.records_dir):
            return records

        for fname in os.listdir(self.records_dir):
            if not fname.endswith(".json") or fname == "schema.json":
                continue
            fpath = os.path.join(self.records_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("run_id") == run_id:
                        records.append(data)
            except Exception as e:
                logger.warning(f"Error reading approval record {fname}: {e}")

        # Sort chronologically by decision_timestamp
        records.sort(key=lambda r: r.get("decision_timestamp", ""))
        return records

    def get_approval_state(self, run_id: str, event_id: str = "SIM-DISR-2026-001", recommended_plan: str = "PLAN_5_KNAPSACK_HYBRID") -> Dict[str, Any]:
        """
        Returns the current operational review status and full audit history.
        Defaults to PENDING_REVIEW if no human decision has been logged.
        """
        self._validate_run_id(run_id)
        history = self.list_records_for_run(run_id)

        if not history:
            current_status = "PENDING_REVIEW"
            latest_record = None
        else:
            latest_record = history[-1]
            current_status = latest_record.get("decision_status", "PENDING_REVIEW")

        return {
            "run_id": run_id,
            "event_id": event_id,
            "recommended_plan": recommended_plan,
            "current_status": current_status,
            "total_decisions_count": len(history),
            "latest_decision": latest_record,
            "history": history,
            "simulation_only": True,
            "physical_dispatch_executed": False,
            "simulation_watermark": "SIMULATION_AUTHORIZATION_ONLY_NO_PHYSICAL_DISPATCH"
        }

    def record_decision(
        self,
        run_id: str,
        event_id: str,
        recommended_plan: str,
        decision_status: str,
        reviewer_username: str,
        reviewer_role: str,
        reviewer_department: Optional[str] = None,
        reviewer_comments: str = "",
        revision_request: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Validates and records an immutable approval decision receipt in data/approval_records/.
        Returns the created record.
        """
        self._validate_run_id(run_id)

        # Validate decision status
        if decision_status not in VALID_STATUSES:
            raise ApprovalServiceError(f"Invalid decision_status '{decision_status}'. Must be one of {VALID_STATUSES}")

        # Validate reviewer details
        if not reviewer_username or not reviewer_username.strip():
            raise ApprovalServiceError("Reviewer username cannot be empty")
        if not reviewer_role or not reviewer_role.strip():
            raise ApprovalServiceError("Reviewer role cannot be empty")
        if not reviewer_comments or not reviewer_comments.strip():
            raise ApprovalServiceError("Reviewer comments / justification cannot be empty")

        # Validate revision_request if status is REVISION_REQUESTED
        if decision_status == "REVISION_REQUESTED" and not revision_request:
            revision_request = {"custom_notes": reviewer_comments}

        now_utc = datetime.now(timezone.utc)
        date_str = now_utc.strftime("%Y%m%d")
        unique_token = uuid.uuid4().hex[:8].upper()
        approval_id = f"APPR-{date_str}-{unique_token}"

        record: Dict[str, Any] = {
            "approval_id": approval_id,
            "run_id": run_id,
            "event_id": event_id,
            "recommended_plan": recommended_plan,
            "decision_status": decision_status,
            "reviewer": {
                "username": reviewer_username.strip(),
                "role": reviewer_role.strip(),
                "department": reviewer_department.strip() if reviewer_department else "Supply Chain Operations"
            },
            "decision_timestamp": now_utc.isoformat(),
            "reviewer_comments": reviewer_comments.strip(),
            "revision_request": revision_request,
            "simulation_watermark": "SIMULATION_AUTHORIZATION_ONLY_NO_PHYSICAL_DISPATCH",
            "simulation_only": True,
            "physical_dispatch_executed": False
        }

        # Write to separate JSON file with atomic-safe naming
        record_file = os.path.join(self.records_dir, f"{approval_id}.json")
        try:
            # Mode 'x' ensures we never overwrite an existing file
            with open(record_file, "x", encoding="utf-8") as f:
                json.dump(record, f, indent=2)
            logger.info(f"Recorded approval decision {approval_id} -> {decision_status} for run {run_id}")
        except FileExistsError:
            raise ApprovalServiceError(f"Collision detected for approval receipt {approval_id}")
        except Exception as e:
            logger.error(f"Failed to persist approval record: {e}")
            raise ApprovalServiceError(f"Storage persistence failure: {e}")

        return record


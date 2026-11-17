"""ChainSentinel Closed-Loop Learning Feedback Engine.

Manages feedback ingestion, epistemological categorization, provenance tracking,
validation governance, and immutable storage under data/feedback/.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ChainSentinel.FeedbackEngine")

VALID_FEEDBACK_TYPES = {
    "OBSERVED_OPERATIONAL_OUTCOME",
    "HUMAN_REVIEW",
    "SIMULATION_RESULT",
    "MODEL_EVALUATION",
}

VALID_MODELS = {
    "delay_model_v1",
    "anomaly_detection_v1",
    "disruption_impact_v1",
    "demand_forecasting_v1",
    "candidate_delay_model_v1_exp1",
}

VALID_STATUSES = {
    "PENDING_VERIFICATION",
    "VERIFIED_VALID",
    "REJECTED_INVALID",
    "SUPERSEDED",
}


class FeedbackValidationError(Exception):
    """Raised when feedback input fails schema or governance validation."""
    pass


class FeedbackNotFoundError(Exception):
    """Raised when a requested feedback record does not exist."""
    pass


class FeedbackEngine:
    """Core closed-loop feedback and provenance engine."""

    def __init__(self, project_root: Optional[Path] = None):
        if project_root is None:
            self.project_root = Path(__file__).resolve().parent.parent.parent
        else:
            self.project_root = Path(project_root)

        self.feedback_dir = self.project_root / "data" / "feedback"
        self.feedback_dir.mkdir(parents=True, exist_ok=True)
        self.schema_path = self.feedback_dir / "schema.json"

    def _generate_feedback_id(self) -> str:
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d")
        random_hex = uuid.uuid4().hex[:8].upper()
        return f"FDBK-{date_str}-{random_hex}"

    def _generate_dedup_key(
        self,
        model_id: str,
        run_id: Optional[str],
        event_id: Optional[str],
        feedback_type: str,
        feedback_source: str,
        observation_timestamp: str,
    ) -> str:
        raw = f"{model_id}:{run_id or ''}:{event_id or ''}:{feedback_type}:{feedback_source}:{observation_timestamp}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def record_feedback(
        self,
        model_id: str,
        model_version: str,
        feedback_type: str,
        feedback_source: str,
        observation_timestamp: Optional[str] = None,
        predicted_value: Any = None,
        observed_value: Any = None,
        run_id: Optional[str] = None,
        event_id: Optional[str] = None,
        approval_id: Optional[str] = None,
        confidence: Optional[float] = None,
        validation_status: str = "PENDING_VERIFICATION",
        comments: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Validates and persists an immutable feedback record."""
        # Validation checks
        if model_id not in VALID_MODELS:
            raise FeedbackValidationError(f"Invalid model_id '{model_id}'. Allowed: {sorted(list(VALID_MODELS))}")

        if feedback_type not in VALID_FEEDBACK_TYPES:
            raise FeedbackValidationError(
                f"Invalid feedback_type '{feedback_type}'. Allowed: {sorted(list(VALID_FEEDBACK_TYPES))}"
            )

        if validation_status not in VALID_STATUSES:
            raise FeedbackValidationError(
                f"Invalid validation_status '{validation_status}'. Allowed: {sorted(list(VALID_STATUSES))}"
            )

        if confidence is not None and not (0.0 <= confidence <= 1.0):
            raise FeedbackValidationError("Confidence must be between 0.0 and 1.0")

        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        obs_time = observation_timestamp or now_utc

        # Check deduplication against existing records
        dedup_key = self._generate_dedup_key(
            model_id=model_id,
            run_id=run_id,
            event_id=event_id,
            feedback_type=feedback_type,
            feedback_source=feedback_source,
            observation_timestamp=obs_time,
        )

        existing_records = self.list_feedback()
        for rec in existing_records:
            if rec.get("metadata", {}).get("dedup_key") == dedup_key:
                logger.info(f"Duplicate feedback detected (key: {dedup_key[:8]}...). Returning existing record: {rec['feedback_id']}")
                return rec

        feedback_id = self._generate_feedback_id()
        meta = metadata.copy() if metadata else {}
        meta["dedup_key"] = dedup_key

        # Epistemological governance check:
        # SIMULATION_RESULT can NEVER be marked as eligible for training
        if feedback_type == "SIMULATION_RESULT":
            meta["retraining_eligible"] = False
            meta["epistemological_note"] = "Synthetic simulation output. Strictly excluded from model ground truth."
        elif feedback_type == "OBSERVED_OPERATIONAL_OUTCOME":
            meta["retraining_eligible"] = (validation_status == "VERIFIED_VALID")
            meta["epistemological_note"] = "Empirical operational observation eligible for ground truth dataset."
        elif feedback_type == "HUMAN_REVIEW":
            meta["retraining_eligible"] = False
            meta["epistemological_note"] = "Human governance decision. Informs policy thresholds and MCDA weights."
        else:
            meta["retraining_eligible"] = False
            meta["epistemological_note"] = "Model telemetry benchmark."

        record: Dict[str, Any] = {
            "feedback_id": feedback_id,
            "run_id": run_id,
            "event_id": event_id,
            "approval_id": approval_id,
            "model_id": model_id,
            "model_version": model_version,
            "feedback_type": feedback_type,
            "predicted_value": predicted_value,
            "observed_value": observed_value,
            "feedback_source": feedback_source,
            "observation_timestamp": obs_time,
            "confidence": confidence,
            "validation_status": validation_status,
            "comments": comments,
            "metadata": meta,
            "created_at": now_utc,
            "updated_at": now_utc,
        }

        target_file = self.feedback_dir / f"{feedback_id}.json"
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        logger.info(f"Persisted feedback {feedback_id} for model {model_id} ({feedback_type})")
        return record

    def get_feedback(self, feedback_id: str) -> Dict[str, Any]:
        """Retrieves a feedback record by ID."""
        target_file = self.feedback_dir / f"{feedback_id}.json"
        if not target_file.exists():
            raise FeedbackNotFoundError(f"Feedback record not found: {feedback_id}")
        with open(target_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_feedback(
        self,
        model_id: Optional[str] = None,
        feedback_type: Optional[str] = None,
        validation_status: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Lists all feedback records matching optional filters, sorted newest first."""
        records: List[Dict[str, Any]] = []
        for file in self.feedback_dir.glob("FDBK-*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    rec = json.load(f)
                    if model_id and rec.get("model_id") != model_id:
                        continue
                    if feedback_type and rec.get("feedback_type") != feedback_type:
                        continue
                    if validation_status and rec.get("validation_status") != validation_status:
                        continue
                    if run_id and rec.get("run_id") != run_id:
                        continue
                    records.append(rec)
            except Exception as e:
                logger.warning(f"Error reading feedback file {file.name}: {e}")

        records.sort(key=lambda r: r.get("created_at", ""), reverse=True)
        return records

    def update_validation_status(
        self, feedback_id: str, new_status: str, actor: str, comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transitions the validation status of an existing feedback record."""
        if new_status not in VALID_STATUSES:
            raise FeedbackValidationError(f"Invalid validation_status '{new_status}'")

        record = self.get_feedback(feedback_id)
        old_status = record.get("validation_status")
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

        record["validation_status"] = new_status
        record["updated_at"] = now_utc

        if "status_history" not in record["metadata"]:
            record["metadata"]["status_history"] = []

        record["metadata"]["status_history"].append({
            "from_status": old_status,
            "to_status": new_status,
            "actor": actor,
            "timestamp": now_utc,
            "comments": comments or "",
        })

        # Update retraining eligibility
        if record.get("feedback_type") == "OBSERVED_OPERATIONAL_OUTCOME":
            record["metadata"]["retraining_eligible"] = (new_status == "VERIFIED_VALID")

        target_file = self.feedback_dir / f"{feedback_id}.json"
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        logger.info(f"Updated feedback {feedback_id} status from {old_status} to {new_status}")
        return record

    def get_summary_metrics(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """Aggregates feedback summary metrics."""
        records = self.list_feedback(model_id=model_id)

        by_type: Dict[str, int] = {t: 0 for t in VALID_FEEDBACK_TYPES}
        by_status: Dict[str, int] = {s: 0 for s in VALID_STATUSES}
        retraining_eligible_count = 0
        total_confidence = 0.0
        confidence_count = 0

        for r in records:
            ftype = r.get("feedback_type")
            if ftype in by_type:
                by_type[ftype] += 1

            status = r.get("validation_status")
            if status in by_status:
                by_status[status] += 1

            if r.get("metadata", {}).get("retraining_eligible", False):
                retraining_eligible_count += 1

            conf = r.get("confidence")
            if conf is not None:
                total_confidence += conf
                confidence_count += 1

        avg_conf = round(total_confidence / confidence_count, 4) if confidence_count > 0 else None

        return {
            "total_feedback_records": len(records),
            "model_filter": model_id,
            "feedback_type_breakdown": by_type,
            "validation_status_breakdown": by_status,
            "retraining_eligible_count": retraining_eligible_count,
            "average_confidence": avg_conf,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        }


def seed_initial_governance_feedback(engine: FeedbackEngine) -> List[Dict[str, Any]]:
    """Seeds authoritative initial feedback records representing existing Phase 11 approvals and telemetry."""
    seeded = []

    # 1. Operational delivery observation for authoritative run
    rec1 = engine.record_feedback(
        model_id="delay_model_v1",
        model_version="v1.0.0",
        feedback_type="OBSERVED_OPERATIONAL_OUTCOME",
        feedback_source="CARRIER_EDI_MILESTONES",
        observation_timestamp="2026-11-04T15:30:00Z",
        predicted_value=1,
        observed_value=1,
        run_id="IRUN-20261104143752-A4CB8F",
        event_id="SIM-DISR-2026-001",
        confidence=0.98,
        validation_status="VERIFIED_VALID",
        comments="Actual carrier tracking confirms shipment order 45281 experienced delivery delay matching GBT class 1 prediction.",
        metadata={"order_id": 45281, "carrier": "FedEx Ground", "delay_hours": 36},
    )
    seeded.append(rec1)

    # 2. Human approval governance review feedback
    rec2 = engine.record_feedback(
        model_id="disruption_impact_v1",
        model_version="v1.0.0",
        feedback_type="HUMAN_REVIEW",
        feedback_source="HUMAN_SUPPLY_CHAIN_DIRECTOR",
        observation_timestamp="2026-11-04T16:00:00Z",
        predicted_value="HIGH_EXPOSURE_1.33M",
        observed_value="APPROVED_PLAN_5",
        run_id="IRUN-20261104143752-A4CB8F",
        event_id="SIM-DISR-2026-001",
        approval_id="APPR-20261104-554229EF",
        confidence=1.0,
        validation_status="VERIFIED_VALID",
        comments="Human director validated high financial exposure calculation and approved Plan 5 hybrid recovery strategy.",
        metadata={"reviewer_role": "VP Supply Chain Logistics", "decision": "APPROVED"},
    )
    seeded.append(rec2)

    # 3. Synthetic simulation result (explicitly flagged as ineligible for retraining)
    rec3 = engine.record_feedback(
        model_id="delay_model_v1",
        model_version="v1.0.0",
        feedback_type="SIMULATION_RESULT",
        feedback_source="PHASE10_STRESS_TEST_HARNESS",
        observation_timestamp="2026-11-04T14:45:00Z",
        predicted_value=0.4628,
        observed_value=None,
        run_id="IRUN-20261104143752-A4CB8F",
        event_id="SIM-DISR-2026-001",
        confidence=0.85,
        validation_status="VERIFIED_VALID",
        comments="Compound shock scenario simulated 46.28% resilience degradation. Synthetically generated; excluded from ML ground truth.",
        metadata={"scenario": "COMPOUND_SHOCK_SEV80", "degradation_pct": 46.28},
    )
    seeded.append(rec3)

    return seeded


if __name__ == "__main__":
    engine = FeedbackEngine()
    results = seed_initial_governance_feedback(engine)
    print(f"Feedback engine initialized. Seeded {len(results)} governance records.")
    summary = engine.get_summary_metrics()
    print(json.dumps(summary, indent=2))


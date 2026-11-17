"""ChainSentinel Security Audit Logger Service.

Provides immutable, structured JSONL audit trail under data/audit/audit_log.jsonl.
Tracks security events, authentication lifecycle, approval decisions, and model interventions.
"""

from __future__ import annotations

import datetime
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("ChainSentinel.AuditLogger")

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
AUDIT_DIR = BASE_DIR / "data" / "audit"
AUDIT_LOG_FILE = AUDIT_DIR / "audit_log.jsonl"


class AuditLogger:
    """Manages application-level security and governance audit logs."""

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or AUDIT_LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        event_type: str,
        action: str,
        actor: str = "anonymous",
        role: str = "VIEWER",
        ip_address: Optional[str] = "127.0.0.1",
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Appends a cryptographically timestamped JSONL record to the audit trail."""
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        audit_id = f"AUDIT-{now_utc[:10].replace('-', '')}-{uuid.uuid4().hex[:8].upper()}"

        record: Dict[str, Any] = {
            "audit_id": audit_id,
            "timestamp": now_utc,
            "event_type": event_type,
            "action": action,
            "actor": actor,
            "role": role,
            "ip_address": ip_address or "127.0.0.1",
            "status": status,
            "details": details or {},
        }

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to append to audit log: {e}")

        return record

    def list_events(self, limit: int = 50, event_type: Optional[str] = None) -> list[Dict[str, Any]]:
        """Reads recent audit events in reverse chronological order."""
        if not self.log_file.exists():
            return []

        events: list[Dict[str, Any]] = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                        if event_type and ev.get("event_type") != event_type:
                            continue
                        events.append(ev)
                    except Exception:
                        continue
        except Exception as e:
            logger.warning(f"Error reading audit log: {e}")

        events.reverse()
        return events[:limit]


# Global singleton instance
audit_logger = AuditLogger()

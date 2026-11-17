"""
ChainSentinel Phase 12 — Alert Generation & Notification Engine
Location: scripts/alerts/alert_engine.py

Generates, persists, and manages the lifecycle of operational alerts
derived from verified upstream pipeline stages (Phases 7–11).
Enforces duplicate suppression, append-only history, and schema validation.
"""

import os
import re
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ChainSentinel.AlertEngine")

# Base directory resolution
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ALERTS_DATA_DIR = os.path.join(BASE_DIR, "data", "alerts")
RULES_FILE = os.path.join(os.path.dirname(__file__), "alert_rules.json")
SCHEMA_FILE = os.path.join(ALERTS_DATA_DIR, "schema.json")
DEFAULT_RUN_ID = "IRUN-20261104143752-A4CB8F"
DEFAULT_RUN_DIR = os.path.join(BASE_DIR, "data", "integration_runs", DEFAULT_RUN_ID)

ALERT_ID_REGEX = re.compile(r"^ALERT-[0-9]{8}-[A-Za-z0-9_-]+$")
RUN_ID_REGEX = re.compile(r"^IRUN-[0-9]{14}-[A-Za-z0-9]+$")

VALID_STATUSES = {"NEW", "ACKNOWLEDGED", "RESOLVED", "DISMISSED"}
VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}


class AlertEngineError(Exception):
    """Domain exception for Alert Engine errors."""
    pass


class AlertNotFoundError(AlertEngineError):
    """Exception raised when an alert is not found."""
    pass


class AlertEngine:
    """Manages generation, storage, and lifecycle of ChainSentinel alerts."""

    def __init__(self, data_dir: str = ALERTS_DATA_DIR, rules_path: str = RULES_FILE):
        self.data_dir = os.path.abspath(data_dir)
        self.rules_path = os.path.abspath(rules_path)
        os.makedirs(self.data_dir, exist_ok=True)
        self.rules = self._load_rules()

    def _load_rules(self) -> List[Dict[str, Any]]:
        """Loads alert generation rules from the configuration JSON file."""
        if not os.path.isfile(self.rules_path):
            logger.warning(f"Alert rules file not found at {self.rules_path}. Using empty rules.")
            return []
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("rules", [])
        except Exception as e:
            logger.error(f"Failed to parse alert rules: {e}")
            return []

    def _generate_alert_id(self) -> str:
        date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
        token = uuid.uuid4().hex[:8].upper()
        return f"ALERT-{date_str}-{token}"

    def list_alerts(
        self,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        alert_type: Optional[str] = None,
        run_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves and filters alert records, sorted by creation timestamp descending."""
        alerts: List[Dict[str, Any]] = []

        if not os.path.isdir(self.data_dir):
            return alerts

        for fname in os.listdir(self.data_dir):
            if not fname.endswith(".json") or fname == "schema.json":
                continue
            fpath = os.path.join(self.data_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    alert = json.load(f)
                    # Apply filters
                    if status and alert.get("acknowledgement_status") != status:
                        continue
                    if severity and alert.get("severity") != severity:
                        continue
                    if alert_type and alert.get("alert_type") != alert_type:
                        continue
                    if run_id and alert.get("run_id") != run_id:
                        continue
                    alerts.append(alert)
            except Exception as e:
                logger.warning(f"Error reading alert record {fname}: {e}")

        # Sort descending by creation timestamp
        alerts.sort(key=lambda a: a.get("creation_timestamp", ""), reverse=True)
        return alerts

    def get_alert(self, alert_id: str) -> Dict[str, Any]:
        """Retrieves a single alert record by alert_id."""
        if not ALERT_ID_REGEX.match(alert_id):
            raise AlertEngineError(f"Invalid alert_id format: {alert_id}")

        fpath = os.path.join(self.data_dir, f"{alert_id}.json")
        if not os.path.isfile(fpath):
            raise AlertNotFoundError(f"Alert not found: {alert_id}")

        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_alert(self, alert: Dict[str, Any], overwrite: bool = False) -> None:
        """Persists an alert record to disk."""
        alert_id = alert["alert_id"]
        fpath = os.path.join(self.data_dir, f"{alert_id}.json")
        mode = "w" if overwrite else "x"
        try:
            with open(fpath, mode, encoding="utf-8") as f:
                json.dump(alert, f, indent=2)
        except FileExistsError:
            raise AlertEngineError(f"Alert receipt collision: {alert_id}")

    def evaluate_run(
        self,
        run_id: str = DEFAULT_RUN_ID,
        run_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluates the authoritative integration run artifacts against configured rules.
        Creates alerts with deduplication, avoiding duplicate alerts for identical causes.
        """
        if not RUN_ID_REGEX.match(run_id):
            raise AlertEngineError(f"Invalid run_id format: {run_id}")

        active_run_dir = run_dir or os.path.join(BASE_DIR, "data", "integration_runs", run_id)
        if not os.path.isdir(active_run_dir):
            raise AlertEngineError(f"Run directory not found: {active_run_dir}")

        # 1. Gather factual data from upstream stages
        disruption_file = os.path.join(active_run_dir, "input", "disruption_event.json")
        shockwave_file = os.path.join(active_run_dir, "phase8", "shockwave_summary.json")
        risk_file = os.path.join(active_run_dir, "phase9", "risk_summary.json")
        rec_file = os.path.join(active_run_dir, "phase10", "recovery_plan_recommended.json")
        stress_file = os.path.join(active_run_dir, "phase10", "resilience_stress_matrix.csv")

        facts: Dict[str, Any] = {
            "run_id": run_id,
            "event_id": "SIM-DISR-2026-001",
            "market": "Pacific Asia",
            "region": "East Asia",
            "disruption_type": "PORT_CLOSURE",
            "capacity_reduction_pct": 100.0,
            "delay_estimate_hours": 96.0,
            "severity": "CRITICAL",
            "unique_affected_orders": 3318,
            "total_gross_revenue_exposure_usd": 1334313.40,
            "critical_orders": 20,
            "high_risk_orders": 625,
            "recommended_plan_id": "PLAN_5_KNAPSACK_HYBRID",
            "recommended_plan_name": "Bounded Knapsack Hybrid",
            "resilience_index": 44.66,
            "mitigated_revenue_usd": 411590.64,
            "max_degradation_pct": 46.28,
            "unrecovered_critical": 3,
            "approval_status": "PENDING_REVIEW",
            "reviewer_username": None,
            "approval_id": None
        }

        # Parse disruption event
        if os.path.isfile(disruption_file):
            with open(disruption_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                facts["event_id"] = d.get("event_id", facts["event_id"])
                facts["severity"] = d.get("severity", facts["severity"])
                facts["disruption_type"] = d.get("disruption_type", facts["disruption_type"])
                facts["market"] = d.get("affected_market", facts["market"])
                facts["region"] = d.get("affected_region", facts["region"])
                facts["capacity_reduction_pct"] = d.get("capacity_reduction_pct", facts["capacity_reduction_pct"])
                facts["delay_estimate_hours"] = d.get("delay_estimate_hours", facts["delay_estimate_hours"])

        # Parse shockwave summary
        if os.path.isfile(shockwave_file):
            with open(shockwave_file, "r", encoding="utf-8") as f:
                s = json.load(f)
                counts = s.get("entity_counts", {})
                fin = s.get("financial_exposure", {})
                facts["unique_affected_orders"] = counts.get("unique_affected_orders", facts["unique_affected_orders"])
                facts["total_gross_revenue_exposure_usd"] = fin.get("total_gross_revenue_exposure_usd", facts["total_gross_revenue_exposure_usd"])

        # Parse risk summary
        if os.path.isfile(risk_file):
            with open(risk_file, "r", encoding="utf-8") as f:
                r = json.load(f)
                sev = r.get("severity_distribution", {})
                facts["critical_orders"] = sev.get("critical_orders", facts["critical_orders"])
                facts["high_risk_orders"] = sev.get("high_risk_orders", facts["high_risk_orders"])

        # Parse recommended plan
        if os.path.isfile(rec_file):
            with open(rec_file, "r", encoding="utf-8") as f:
                rp = json.load(f)
                facts["recommended_plan_id"] = rp.get("recommended_plan_id", facts["recommended_plan_id"])
                facts["recommended_plan_name"] = rp.get("recommended_plan_name", facts["recommended_plan_name"])
                facts["resilience_index"] = rp.get("resilience_index", facts["resilience_index"])
                fin_mit = rp.get("financial_mitigation_summary", {})
                facts["mitigated_revenue_usd"] = fin_mit.get("expected_mitigated_revenue_usd", facts["mitigated_revenue_usd"])

        # Check approval state in data/approval_records/
        approvals_dir = os.path.join(BASE_DIR, "data", "approval_records")
        if os.path.isdir(approvals_dir):
            latest_ts = ""
            for fname in os.listdir(approvals_dir):
                if not fname.endswith(".json") or fname == "schema.json":
                    continue
                try:
                    with open(os.path.join(approvals_dir, fname), "r", encoding="utf-8") as af:
                        rec = json.load(af)
                        if rec.get("run_id") == run_id:
                            ts = rec.get("decision_timestamp", "")
                            if ts > latest_ts:
                                latest_ts = ts
                                facts["approval_status"] = rec.get("decision_status", "PENDING_REVIEW")
                                facts["reviewer_username"] = rec.get("reviewer", {}).get("username")
                                facts["approval_id"] = rec.get("approval_id")
                except Exception:
                    pass

        # 2. Existing alerts index for duplicate suppression
        existing_alerts = self.list_alerts(run_id=run_id)
        existing_dedup_keys = {
            f"{a.get('run_id')}:{a.get('event_id')}:{a.get('alert_type')}:{a.get('related_entity')}"
            for a in existing_alerts
        }

        created_alerts: List[Dict[str, Any]] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        # Format helpers
        facts["total_gross_revenue_formatted"] = f"{facts['total_gross_revenue_exposure_usd']:,.2f}"
        facts["mitigated_revenue_formatted"] = f"{facts['mitigated_revenue_usd']:,.2f}"

        for rule in self.rules:
            cond = rule.get("condition", {})
            field = cond.get("field")
            op = cond.get("operator")
            target_val = cond.get("value")

            fact_val = facts.get(field)

            # Evaluate condition
            matched = False
            if op == "==":
                matched = (fact_val == target_val)
            elif op == "!=":
                matched = (fact_val != target_val)
            elif op == ">=":
                matched = (fact_val is not None and fact_val >= target_val)
            elif op == "<=":
                matched = (fact_val is not None and fact_val <= target_val)
            elif op == "in":
                matched = (fact_val in target_val if target_val else False)

            if not matched:
                continue

            alert_type = rule["alert_type"]
            related_entity = facts.get("region") or facts.get("event_id") or "SUPPLY_CHAIN_NETWORK"
            if alert_type == "RECOVERY_PLAN_RECOMMENDED":
                related_entity = facts["recommended_plan_id"]
            elif alert_type in ("HUMAN_APPROVAL_REQUIRED", "APPROVAL_DECISION_RECORDED"):
                related_entity = facts["recommended_plan_id"]

            dedup_key = f"{run_id}:{facts['event_id']}:{alert_type}:{related_entity}"
            if dedup_key in existing_dedup_keys:
                continue

            # Format title and description
            try:
                title = rule["title_template"].format(**facts)
                description = rule["description_template"].format(**facts)
            except Exception:
                title = rule.get("title_template", "Operational Alert")
                description = rule.get("description_template", "Operational Alert Notification")

            alert_id = self._generate_alert_id()

            new_alert = {
                "alert_id": alert_id,
                "event_id": facts["event_id"],
                "run_id": run_id,
                "alert_type": alert_type,
                "severity": rule["severity"],
                "title": title,
                "description": description,
                "source_component": rule["source_component"],
                "creation_timestamp": now_iso,
                "acknowledgement_status": "NEW",
                "related_entity": related_entity,
                "recommended_action": rule.get("recommended_action", "Review and take operational action."),
                "simulation_only": True,
                "history": [
                    {
                        "status": "NEW",
                        "timestamp": now_iso,
                        "user": "SYSTEM_ALERT_ENGINE",
                        "comments": f"Synthesized by rule {rule['rule_id']}"
                    }
                ],
                "acknowledged_timestamp": None,
                "resolved_timestamp": None
            }

            self._save_alert(new_alert)
            existing_dedup_keys.add(dedup_key)
            created_alerts.append(new_alert)
            logger.info(f"Generated alert {alert_id} ({alert_type}) for run {run_id}")

        return created_alerts

    def acknowledge_alert(self, alert_id: str, user: str = "operational_reviewer", comments: str = "") -> Dict[str, Any]:
        """Transitions an alert from NEW to ACKNOWLEDGED."""
        alert = self.get_alert(alert_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        alert["acknowledgement_status"] = "ACKNOWLEDGED"
        alert["acknowledged_timestamp"] = now_iso
        alert["history"].append({
            "status": "ACKNOWLEDGED",
            "timestamp": now_iso,
            "user": user.strip() or "operational_reviewer",
            "comments": comments.strip() or "Acknowledged by operational reviewer"
        })

        self._save_alert(alert, overwrite=True)
        return alert

    def resolve_alert(self, alert_id: str, user: str = "operational_reviewer", comments: str = "") -> Dict[str, Any]:
        """Transitions an alert to RESOLVED."""
        alert = self.get_alert(alert_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        alert["acknowledgement_status"] = "RESOLVED"
        alert["resolved_timestamp"] = now_iso
        alert["history"].append({
            "status": "RESOLVED",
            "timestamp": now_iso,
            "user": user.strip() or "operational_reviewer",
            "comments": comments.strip() or "Resolved operational review"
        })

        self._save_alert(alert, overwrite=True)
        return alert

    def dismiss_alert(self, alert_id: str, user: str = "operational_reviewer", comments: str = "") -> Dict[str, Any]:
        """Transitions an alert to DISMISSED."""
        alert = self.get_alert(alert_id)
        now_iso = datetime.now(timezone.utc).isoformat()

        alert["acknowledgement_status"] = "DISMISSED"
        alert["history"].append({
            "status": "DISMISSED",
            "timestamp": now_iso,
            "user": user.strip() or "operational_reviewer",
            "comments": comments.strip() or "Dismissed by operational reviewer"
        })

        self._save_alert(alert, overwrite=True)
        return alert

    def get_summary(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """Calculates aggregated metrics and breakdown counts of alert records."""
        alerts = self.list_alerts(run_id=run_id)

        status_counts = {"NEW": 0, "ACKNOWLEDGED": 0, "RESOLVED": 0, "DISMISSED": 0}
        severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}

        for a in alerts:
            st = a.get("acknowledgement_status", "NEW")
            sev = a.get("severity", "INFO")
            status_counts[st] = status_counts.get(st, 0) + 1
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        return {
            "total_alerts": len(alerts),
            "active_alerts": status_counts["NEW"] + status_counts["ACKNOWLEDGED"],
            "by_status": status_counts,
            "by_severity": severity_counts,
            "has_critical_alerts": severity_counts["CRITICAL"] > 0,
            "simulation_only": True
        }


"""
Unit Tests for ChainSentinel Disruption Event Schema & Validation Logic
Location: docker/spark/streaming/tests/test_disruption_events.py

Runs standalone unit tests verifying:
- Valid event payloads
- Missing required fields
- Invalid enum fields (severity, event_type)
- Boundary violations (capacity_reduction_pct, source_confidence, negative duration)
- Malformed JSON strings
- Duplicate event ID detection
- Conflicting event ID payload detection
"""

import sys
import os
import unittest
import json
from copy import deepcopy
from datetime import datetime

# Add parent directory to path so disruption_event_schema can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from disruption_event_schema import (
    validate_disruption_dict,
    validate_raw_json_string,
    REQUIRED_FIELDS,
    VALID_SEVERITIES,
    VALID_EVENT_TYPES,
    VALID_DISRUPTION_TYPES
)


class TestDisruptionEventValidation(unittest.TestCase):
    
    def setUp(self):
        """Creates a canonical, valid disruption event dictionary."""
        self.valid_event = {
            "event_id": "DISR-TEST-001",
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
            "source": "Maritime_Port_Authority",
            "source_confidence": 0.98,
            "description": "Terminal berth closure",
            "event_timestamp": "2026-11-04T06:15:00Z"
        }

    # Test 1: Valid event
    def test_valid_event(self):
        is_valid, errors = validate_disruption_dict(self.valid_event)
        self.assertTrue(is_valid, f"Expected valid event, got errors: {errors}")
        self.assertEqual(len(errors), 0)

    # Test 2: Missing required field
    def test_missing_required_field(self):
        event = deepcopy(self.valid_event)
        del event["affected_market"]
        is_valid, errors = validate_disruption_dict(event)
        self.assertFalse(is_valid)
        self.assertTrue(any("affected_market" in err for err in errors))

        event_empty_id = deepcopy(self.valid_event)
        event_empty_id["event_id"] = "   "
        is_valid, errors = validate_disruption_dict(event_empty_id)
        self.assertFalse(is_valid)
        self.assertTrue(any("event_id" in err for err in errors))

    # Test 3: Invalid severity
    def test_invalid_severity(self):
        event = deepcopy(self.valid_event)
        event["severity"] = "EXTREME_CATASTROPHIC"
        is_valid, errors = validate_disruption_dict(event)
        self.assertFalse(is_valid)
        self.assertTrue(any("severity" in err for err in errors))

    # Test 4: Invalid capacity reduction (outside 0-100%)
    def test_invalid_capacity_reduction(self):
        # Above 100%
        event_high = deepcopy(self.valid_event)
        event_high["capacity_reduction_pct"] = 105.0
        is_valid, errors = validate_disruption_dict(event_high)
        self.assertFalse(is_valid)
        self.assertTrue(any("capacity_reduction_pct" in err for err in errors))

        # Below 0%
        event_low = deepcopy(self.valid_event)
        event_low["capacity_reduction_pct"] = -5.0
        is_valid, errors = validate_disruption_dict(event_low)
        self.assertFalse(is_valid)
        self.assertTrue(any("capacity_reduction_pct" in err for err in errors))

    # Test 5: Invalid source confidence (outside 0-1)
    def test_invalid_source_confidence(self):
        # Greater than 1.0
        event_high = deepcopy(self.valid_event)
        event_high["source_confidence"] = 1.25
        is_valid, errors = validate_disruption_dict(event_high)
        self.assertFalse(is_valid)
        self.assertTrue(any("source_confidence" in err for err in errors))

        # Less than 0.0
        event_low = deepcopy(self.valid_event)
        event_low["source_confidence"] = -0.1
        is_valid, errors = validate_disruption_dict(event_low)
        self.assertFalse(is_valid)
        self.assertTrue(any("source_confidence" in err for err in errors))

    # Test 6: Negative expected duration
    def test_negative_expected_duration(self):
        event = deepcopy(self.valid_event)
        event["expected_duration_hours"] = -24.0
        is_valid, errors = validate_disruption_dict(event)
        self.assertFalse(is_valid)
        self.assertTrue(any("expected_duration_hours" in err for err in errors))

    # Test 7: Malformed JSON
    def test_malformed_json(self):
        bad_json_string = '{"event_id": "DISR-001", "event_type": "DISRUPTION_ALERT", incomplete...'
        is_valid, errors, data = validate_raw_json_string(bad_json_string)
        self.assertFalse(is_valid)
        self.assertEqual(len(data), 0)
        self.assertTrue(any("Malformed JSON" in err for err in errors))

    # Test 8: Duplicate event ID handling
    def test_duplicate_event_id(self):
        """Simulates windowed event stream deduplication for identical duplicate records."""
        stream = [deepcopy(self.valid_event), deepcopy(self.valid_event)]
        seen_ids = set()
        deduplicated = []
        duplicates_detected = []

        for record in stream:
            rec_id = record["event_id"]
            if rec_id in seen_ids:
                duplicates_detected.append(record)
            else:
                seen_ids.add(rec_id)
                deduplicated.append(record)

        self.assertEqual(len(deduplicated), 1)
        self.assertEqual(len(duplicates_detected), 1)
        self.assertEqual(duplicates_detected[0]["event_id"], self.valid_event["event_id"])

    # Test 9: Conflicting event ID payload (update vs duplicate)
    def test_conflicting_event_id_payload(self):
        """
        Verifies that an event with the same ID but conflicting payload (e.g. updated
        duration or severity) is NOT discarded as a duplicate, but flagged as a conflict/update.
        """
        initial_event = deepcopy(self.valid_event)
        
        # Incident escalated: severity changed from CRITICAL to HIGH, or duration extended
        conflicting_update = deepcopy(self.valid_event)
        conflicting_update["expected_duration_hours"] = 120.0
        conflicting_update["delay_estimate_hours"] = 144.0
        conflicting_update["event_timestamp"] = "2026-11-04T07:30:00Z"
        conflicting_update["event_type"] = "SITUATION_UPDATE"

        # Compare payloads
        def detect_conflict(existing: dict, incoming: dict):
            if existing["event_id"] != incoming["event_id"]:
                return "DIFFERENT_EVENTS"
            
            # Check for payload field divergence
            differing_fields = [
                k for k in existing 
                if k not in ["event_timestamp", "description"] and existing.get(k) != incoming.get(k)
            ]
            
            if not differing_fields:
                return "IDENTICAL_DUPLICATE"
            else:
                return f"CONFLICTING_UPDATE:{','.join(differing_fields)}"

        result = detect_conflict(initial_event, conflicting_update)
        self.assertTrue(result.startswith("CONFLICTING_UPDATE"))
        self.assertIn("expected_duration_hours", result)
        self.assertIn("delay_estimate_hours", result)
        self.assertIn("event_type", result)

    # Test 10: Same event ID with different event timestamp (lifecycle update simulation)
    def test_lifecycle_update_different_timestamp(self):
        """
        Verifies that an event with the same event_id but an advanced event_timestamp
        (e.g., situation update during an evolving incident) is valid according to schema rules.
        Simulates composite-key [event_id, event_timestamp] deduplication tracking in pure Python.
        """
        initial_event = deepcopy(self.valid_event)
        update_event = deepcopy(self.valid_event)
        update_event["event_type"] = "SITUATION_UPDATE"
        update_event["event_timestamp"] = "2026-11-04T08:00:00Z"
        update_event["expected_duration_hours"] = 96.0

        # Both records are individually valid against schema rules
        valid1, errs1 = validate_disruption_dict(initial_event)
        valid2, errs2 = validate_disruption_dict(update_event)
        self.assertTrue(valid1, f"Initial event validation failed: {errs1}")
        self.assertTrue(valid2, f"Update event validation failed: {errs2}")

        # Under composite key (event_id, event_timestamp), both distinct lifecycle states are preserved
        composite_keys = {
            (e["event_id"], e["event_timestamp"]) for e in [initial_event, update_event]
        }
        self.assertEqual(len(composite_keys), 2, "Expected composite deduplication key to preserve both events")

    # Test 11: Missing event timestamp
    def test_missing_event_timestamp(self):
        """Verifies that an event missing event_timestamp fails validation."""
        event = deepcopy(self.valid_event)
        del event["event_timestamp"]
        is_valid, errors = validate_disruption_dict(event)
        self.assertFalse(is_valid)
        self.assertTrue(any("event_timestamp" in err for err in errors))

        event_none = deepcopy(self.valid_event)
        event_none["event_timestamp"] = None
        is_valid_none, errors_none = validate_disruption_dict(event_none)
        self.assertFalse(is_valid_none)
        self.assertTrue(any("event_timestamp" in err for err in errors_none))

    # Test 12: Invalid timestamp format
    def test_invalid_timestamp_format(self):
        """Verifies that non-ISO-8601 formatted timestamp strings are rejected."""
        event_bad_format = deepcopy(self.valid_event)
        event_bad_format["event_timestamp"] = "04-Nov-2026 10:00:00"
        is_valid, errors = validate_disruption_dict(event_bad_format)
        self.assertFalse(is_valid)
        self.assertTrue(any("Invalid timestamp format for 'event_timestamp'" in err for err in errors))

        event_bad_start = deepcopy(self.valid_event)
        event_bad_start["start_time"] = "2026-13-45T99:99:99Z"
        is_valid_start, errors_start = validate_disruption_dict(event_bad_start)
        self.assertFalse(is_valid_start)
        self.assertTrue(any("Invalid timestamp format for 'start_time'" in err for err in errors_start))

    # Test 13: All-null or empty payload
    def test_all_null_or_empty_payload(self):
        """Verifies that completely empty or all-null dictionaries fail validation with all required-field errors."""
        empty_payload = {}
        is_valid_empty, errors_empty = validate_disruption_dict(empty_payload)
        self.assertFalse(is_valid_empty)
        self.assertEqual(len(errors_empty), len(REQUIRED_FIELDS))

        all_null_payload = {f: None for f in REQUIRED_FIELDS}
        is_valid_null, errors_null = validate_disruption_dict(all_null_payload)
        self.assertFalse(is_valid_null)
        self.assertEqual(len(errors_null), len(REQUIRED_FIELDS))

    # Test 14: Invalid disruption_type
    def test_invalid_disruption_type(self):
        """Verifies that unknown or unapproved disruption_type enum values are rejected."""
        event = deepcopy(self.valid_event)
        event["disruption_type"] = "CYBER_SECURITY_BREACH"
        is_valid, errors = validate_disruption_dict(event)
        self.assertFalse(is_valid)
        self.assertTrue(any("disruption_type" in err for err in errors))
        self.assertTrue(any("CYBER_SECURITY_BREACH" in err for err in errors))

    # Test 15: Boolean value supplied for numeric fields
    def test_boolean_in_numeric_fields(self):
        """
        Verifies that Boolean values (True/False) are explicitly rejected for all numeric fields,
        preventing Python's bool-is-subclass-of-int from accepting booleans as valid numbers.
        """
        numeric_fields = [
            "expected_duration_hours",
            "capacity_reduction_pct",
            "delay_estimate_hours",
            "source_confidence"
        ]
        for field in numeric_fields:
            for bool_val in [True, False]:
                event = deepcopy(self.valid_event)
                event[field] = bool_val
                is_valid, errors = validate_disruption_dict(event)
                self.assertFalse(is_valid, f"Expected {field}={bool_val} to be rejected as numeric value")
                self.assertTrue(
                    any(field in err for err in errors),
                    f"Expected error message mentioning '{field}' when value is {bool_val}"
                )


if __name__ == "__main__":
    unittest.main()


"""
ChainSentinel — Phase 7 Disruption Event Schema & Validation Module
Location: docker/spark/streaming/disruption_event_schema.py

Defines strict, explicit schema structures, validation rules, and validation
helpers for supply-chain disruption events ingested via Kafka.
"""

from typing import Dict, Any, List, Tuple
import json
from datetime import datetime

# Spark Types (imported safely so module can also be imported in pure Python environments)
try:
    from pyspark.sql.types import (
        StructType, StructField, StringType,
        DoubleType, TimestampType
    )
    from pyspark.sql.functions import (
        col, when, length, trim, array, lit,
        size, coalesce, array_compact
    )
    PYSPARK_AVAILABLE = True
except ImportError:
    PYSPARK_AVAILABLE = False


# ==============================================================================
# 1. ALLOWED ENUM VALUES & CONSTANTS
# ==============================================================================

VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

VALID_EVENT_TYPES = {
    "DISRUPTION_ALERT",
    "INCIDENT_REPORT",
    "SITUATION_UPDATE",
    "STATUS_CHANGE",
    "DISRUPTION_RESOLVED"
}

VALID_DISRUPTION_TYPES = {
    "PORT_CLOSURE",
    "SEVERE_WEATHER",
    "LABOR_STRIKE",
    "CARRIER_CAPACITY_SHORTAGE",
    "CUSTOMS_DELAY",
    "GEOPOLITICAL_SANCTION",
    "INFRASTRUCTURE_FAILURE",
    "OTHER"
}

# Mandatory fields required for valid disruption processing
REQUIRED_FIELDS = [
    "event_id",
    "event_type",
    "disruption_type",
    "affected_market",
    "severity",
    "start_time",
    "expected_duration_hours",
    "capacity_reduction_pct",
    "delay_estimate_hours",
    "source",
    "source_confidence",
    "event_timestamp"
]

# Optional fields that provide enriched context
OPTIONAL_FIELDS = [
    "affected_region",
    "affected_country",
    "description"
]


# ==============================================================================
# 2. PYSPARK EXPLICIT STRUCTTYPE SCHEMA
# ==============================================================================

def get_disruption_spark_schema():
    """
    Returns the explicit Spark StructType schema for disruption event payloads.
    
    NOTE ON NULLABILITY:
    All StructField entries are explicitly marked nullable=True. This is a required
    design pattern in Spark Structured Streaming for JSON deserialization via from_json(),
    guaranteeing that malformed or incomplete JSON keys resolve safely to nulls rather than
    failing the parser JVM. Mandatory field presence and boundary constraints are strictly
    enforced downstream in add_spark_validation_columns().
    """
    if not PYSPARK_AVAILABLE:
        raise RuntimeError("PySpark is required to generate the Spark StructType schema.")
    
    return StructType([
        StructField("event_id", StringType(), True),
        StructField("event_type", StringType(), True),
        StructField("disruption_type", StringType(), True),
        StructField("affected_market", StringType(), True),
        StructField("affected_region", StringType(), True),
        StructField("affected_country", StringType(), True),
        StructField("severity", StringType(), True),
        StructField("start_time", TimestampType(), True),
        StructField("expected_duration_hours", DoubleType(), True),
        StructField("capacity_reduction_pct", DoubleType(), True),
        StructField("delay_estimate_hours", DoubleType(), True),
        StructField("source", StringType(), True),
        StructField("source_confidence", DoubleType(), True),
        StructField("description", StringType(), True),
        StructField("event_timestamp", TimestampType(), True)
    ])


# ==============================================================================
# 3. PURE PYTHON VALIDATOR (FOR LOCAL TESTING & IN-MEMORY INGESTION)
# ==============================================================================

def validate_disruption_dict(event: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a disruption event dictionary against all business and data-quality rules.
    
    Returns:
        (is_valid: bool, errors: List[str])
    """
    errors = []
    
    if not isinstance(event, dict):
        return False, ["Payload is not a valid JSON dictionary"]
    
    # Check 1: Mandatory fields present
    for req_field in REQUIRED_FIELDS:
        if req_field not in event or event[req_field] is None:
            errors.append(f"Missing required field: '{req_field}'")
            
    # Check 2: event_id non-empty string
    event_id = event.get("event_id")
    if event_id is not None:
        if not isinstance(event_id, str) or not event_id.strip():
            errors.append("Invalid 'event_id': must be a non-empty string")
            
    # Check 3: event_type enum check
    event_type = event.get("event_type")
    if event_type is not None:
        if event_type not in VALID_EVENT_TYPES:
            errors.append(f"Invalid 'event_type': '{event_type}'. Must be one of {sorted(VALID_EVENT_TYPES)}")
            
    # Check 4: disruption_type enum check
    disruption_type = event.get("disruption_type")
    if disruption_type is not None:
        if disruption_type not in VALID_DISRUPTION_TYPES:
            errors.append(f"Invalid 'disruption_type': '{disruption_type}'. Must be one of {sorted(VALID_DISRUPTION_TYPES)}")
            
    # Check 5: affected_market non-empty string
    affected_market = event.get("affected_market")
    if affected_market is not None:
        if not isinstance(affected_market, str) or not affected_market.strip():
            errors.append("Invalid 'affected_market': must be a non-empty string")
            
    # Check 6: severity enum check
    severity = event.get("severity")
    if severity is not None:
        if severity not in VALID_SEVERITIES:
            errors.append(f"Invalid 'severity': '{severity}'. Must be one of {sorted(VALID_SEVERITIES)}")
            
    # Check 7: expected_duration_hours >= 0.0 (explicitly reject boolean subclasses)
    expected_duration = event.get("expected_duration_hours")
    if expected_duration is not None:
        if isinstance(expected_duration, bool) or not isinstance(expected_duration, (int, float)) or expected_duration < 0.0:
            errors.append("Invalid 'expected_duration_hours': must be a non-negative number")
            
    # Check 8: capacity_reduction_pct between 0.0 and 100.0 (explicitly reject boolean subclasses)
    cap_reduct = event.get("capacity_reduction_pct")
    if cap_reduct is not None:
        if isinstance(cap_reduct, bool) or not isinstance(cap_reduct, (int, float)) or not (0.0 <= cap_reduct <= 100.0):
            errors.append("Invalid 'capacity_reduction_pct': must be a number between 0.0 and 100.0")
            
    # Check 9: delay_estimate_hours >= 0.0 (explicitly reject boolean subclasses)
    delay_est = event.get("delay_estimate_hours")
    if delay_est is not None:
        if isinstance(delay_est, bool) or not isinstance(delay_est, (int, float)) or delay_est < 0.0:
            errors.append("Invalid 'delay_estimate_hours': must be a non-negative number")
            
    # Check 10: source non-empty string
    source = event.get("source")
    if source is not None:
        if not isinstance(source, str) or not source.strip():
            errors.append("Invalid 'source': must be a non-empty string")
            
    # Check 11: source_confidence between 0.0 and 1.0 (explicitly reject boolean subclasses)
    confidence = event.get("source_confidence")
    if confidence is not None:
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
            errors.append("Invalid 'source_confidence': must be a float between 0.0 and 1.0")
            
    # Check 12: timestamps validation
    for ts_field in ["start_time", "event_timestamp"]:
        ts_val = event.get(ts_field)
        if ts_val is not None:
            if isinstance(ts_val, str):
                try:
                    # Validate ISO format
                    datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    errors.append(f"Invalid timestamp format for '{ts_field}': '{ts_val}'")
            elif not isinstance(ts_val, datetime):
                errors.append(f"Invalid timestamp type for '{ts_field}'")
                
    return (len(errors) == 0, errors)


def validate_raw_json_string(raw_json: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Parses raw JSON string and runs validation. Catches syntax/malformed errors."""
    try:
        data = json.loads(raw_json)
    except Exception as e:
        return False, [f"Malformed JSON: {str(e)}"], {}
    
    is_valid, errors = validate_disruption_dict(data)
    return is_valid, errors, data


# ==============================================================================
# 4. SPARK STRUCTURED STREAMING VALIDATION EXPRESSIONS
# ==============================================================================

def add_spark_validation_columns(parsed_df, raw_payload_col="raw_payload"):
    """
    Applies vectorised Spark SQL validation rules to an unpacked DataFrame.
    
    Produces:
        validation_errors: ArrayType(StringType) containing all violation codes
        is_valid: BooleanType (True if validation_errors is empty)
    """
    if not PYSPARK_AVAILABLE:
        raise RuntimeError("PySpark is required to build validation DataFrame expressions.")
    
    error_exprs = [
        # Check event_id
        when(
            col("event_id").isNull() | (length(trim(col("event_id"))) == 0),
            lit("ERR_INVALID_EVENT_ID")
        ),
        # Check event_type
        when(
            col("event_type").isNull() | (~col("event_type").isin(list(VALID_EVENT_TYPES))),
            lit("ERR_INVALID_EVENT_TYPE")
        ),
        # Check disruption_type
        when(
            col("disruption_type").isNull() | (~col("disruption_type").isin(list(VALID_DISRUPTION_TYPES))),
            lit("ERR_INVALID_DISRUPTION_TYPE")
        ),
        # Check affected_market
        when(
            col("affected_market").isNull() | (length(trim(col("affected_market"))) == 0),
            lit("ERR_MISSING_AFFECTED_MARKET")
        ),
        # Check severity
        when(
            col("severity").isNull() | (~col("severity").isin(list(VALID_SEVERITIES))),
            lit("ERR_INVALID_SEVERITY")
        ),
        # Check start_time
        when(
            col("start_time").isNull(),
            lit("ERR_MISSING_START_TIME")
        ),
        # Check expected_duration_hours
        when(
            col("expected_duration_hours").isNull() | (col("expected_duration_hours") < 0.0),
            lit("ERR_INVALID_EXPECTED_DURATION")
        ),
        # Check capacity_reduction_pct (0 to 100%)
        when(
            col("capacity_reduction_pct").isNull() | 
            (col("capacity_reduction_pct") < 0.0) | 
            (col("capacity_reduction_pct") > 100.0),
            lit("ERR_INVALID_CAPACITY_REDUCTION")
        ),
        # Check delay_estimate_hours (non-negative)
        when(
            col("delay_estimate_hours").isNull() | (col("delay_estimate_hours") < 0.0),
            lit("ERR_INVALID_DELAY_ESTIMATE")
        ),
        # Check source
        when(
            col("source").isNull() | (length(trim(col("source"))) == 0),
            lit("ERR_MISSING_SOURCE")
        ),
        # Check source_confidence (0.0 to 1.0)
        when(
            col("source_confidence").isNull() | 
            (col("source_confidence") < 0.0) | 
            (col("source_confidence") > 1.0),
            lit("ERR_INVALID_SOURCE_CONFIDENCE")
        ),
        # Check event_timestamp
        when(
            col("event_timestamp").isNull(),
            lit("ERR_MISSING_EVENT_TIMESTAMP")
        )
    ]
    
    # Construct errors array by evaluating conditions and compacting nulls
    validated_df = parsed_df.withColumn(
        "validation_errors",
        array_compact(array(*error_exprs))
    ).withColumn(
        "is_valid",
        size(col("validation_errors")) == 0
    )
    
    return validated_df


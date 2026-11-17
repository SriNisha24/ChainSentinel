"""
ChainSentinel Phase 11 — FastAPI Operational Review Backend
Location: web/backend/main.py

Provides read-only operational decision-support REST APIs consuming
completed integration run artifacts (IRUN-20261104143752-A4CB8F).
"""

import os
import sys
import re
import time
import math
import logging
from collections import defaultdict
from pathlib import Path
from typing import List, Dict, Any, Optional

# ==============================================================================
# 0. STARLETTE 1.x / FASTAPI COMPATIBILITY BRIDGE
# Resolves Starlette 1.x parameter signature evolution in FastAPI 0.110
# without modifying global packages or system environments.
# ==============================================================================
import starlette.routing
import starlette.applications

_orig_router_init = starlette.routing.Router.__init__
def _compat_router_init(self, *args, **kwargs):
    kwargs.pop("on_startup", None)
    kwargs.pop("on_shutdown", None)
    return _orig_router_init(self, *args, **kwargs)
starlette.routing.Router.__init__ = _compat_router_init

from fastapi import FastAPI, HTTPException, Query, status, Request, Depends, Header, UploadFile, File
from starlette.middleware.base import BaseHTTPMiddleware
FastAPI.max_body_size = None

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Resolve paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
for p in [CURRENT_DIR, PROJECT_ROOT]:
    if p not in sys.path:
        sys.path.insert(0, p)

from models.schemas import (
    HealthResponse,
    RunSummaryResponse,
    LineageResponse,
    DisruptionEventResponse,
    ShockwaveResponse,
    RiskSummaryResponse,
    RecoveryPlansResponse,
    RecommendedPlanResponse,
    StressTestsResponse,
    ApprovalRecord,
    ApprovalDecisionRequest,
    ApprovalStateResponse,
    AlertRecord,
    AlertActionRequest,
    AlertSummaryResponse,
    AlertListResponse,
    FeedbackCreateRequest,
    FeedbackStatusUpdateRequest,
    FeedbackRecordResponse,
    FeedbackSummaryResponse,
    ModelMetadataResponse,
    ModelDriftResponse,
    RetrainingExperimentRequest,
    RetrainingExperimentResponse,
    LoginRequest,
    LoginResponse,
    UserSessionResponse,
    AuditLogRecordResponse,
    DatasetMetadataResponse,
    DatasetPreviewResponse,
    DatasetUploadResponse,
    AnalysisRunSummary,
    AnalysisRunDetailResponse,
)
from services.data_loader import RunDataLoader, DataLoaderError, DEFAULT_RUN_ID
from services.approval_service import ApprovalService, ApprovalServiceError
from services.auth_service import auth_service, AuthenticationError, AuthorizationError
from services.audit_logger import audit_logger
from services.dataset_service import dataset_service, DatasetValidationError
from services.analysis_run_manager import analysis_run_manager
from scripts.alerts.alert_engine import AlertEngine, AlertEngineError, AlertNotFoundError
from scripts.feedback.feedback_engine import FeedbackEngine, FeedbackValidationError, FeedbackNotFoundError
from scripts.feedback.model_evaluator import ModelEvaluator
from scripts.feedback.retraining_pipeline import RetrainingPipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ChainSentinel.Backend")

# ==============================================================================
# SECURITY HEADERS & RATE LIMITING MIDDLEWARE (PHASE 14)
# ==============================================================================

# In-memory sliding-window rate limiter (180 req/minute per IP)
_RATE_LIMIT_STORE = defaultdict(list)
RATE_LIMIT_WINDOW = 60.0  # seconds
RATE_LIMIT_MAX_REQUESTS = 180  # requests per window

class SecurityAndRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Rate Limiting Check
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        # Prune old timestamps
        timestamps = [ts for ts in _RATE_LIMIT_STORE[client_ip] if now - ts < RATE_LIMIT_WINDOW]
        _RATE_LIMIT_STORE[client_ip] = timestamps

        if len(timestamps) >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"Rate limit exceeded for client IP: {client_ip}")
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Too many requests. Please slow down.", "error_type": "RATE_LIMIT_EXCEEDED"},
                headers={"Retry-After": "60"}
            )

        _RATE_LIMIT_STORE[client_ip].append(now)

        # 2. Process Request
        response = await call_next(request)

        # 3. Defensive Security Headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


def validate_safe_id(param_name: str, value: Optional[str]) -> None:
    if not value:
        return
    # Strictly reject path traversal sequences and illegal control characters
    if ".." in value or "/" in value or "\\" in value or "\0" in value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Security violation: Illegal path traversal characters in {param_name}.",
        )


# Initialize FastAPI application
app = FastAPI(
    title="ChainSentinel Operational Review API",
    description="Hardened decision-support REST backend serving disruption simulations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Attach Security and Rate Limiting Middleware
app.add_middleware(SecurityAndRateLimitMiddleware)

# Enable Hardened CORS (strictly local origins, no wildcard '*')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Instantiate singleton services
approval_service = ApprovalService()
alert_engine = AlertEngine()
feedback_engine = FeedbackEngine(Path(PROJECT_ROOT))
model_evaluator = ModelEvaluator(Path(PROJECT_ROOT))
retraining_pipeline = RetrainingPipeline(Path(PROJECT_ROOT))

# Automatically generate baseline alerts for authoritative integration run
try:
    alert_engine.evaluate_run(DEFAULT_RUN_ID)
    logger.info(f"Initialized alerts for run: {DEFAULT_RUN_ID}")
except Exception as e:
    logger.warning(f"Could not initialize alerts on startup: {e}")

try:
    data_loader = RunDataLoader(run_id=DEFAULT_RUN_ID)
    logger.info(f"Loaded primary integration run: {DEFAULT_RUN_ID}")
except Exception as e:
    logger.warning(f"Could not initialize primary run loader on startup: {e}")
    data_loader = None


# ==============================================================================
# GLOBAL EXCEPTION HANDLERS
# ==============================================================================

@app.exception_handler(DataLoaderError)
async def dataloader_exception_handler(request, exc: DataLoaderError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "error_type": "ARTIFACT_LOAD_ERROR"}
    )


@app.exception_handler(ApprovalServiceError)
async def approval_exception_handler(request, exc: ApprovalServiceError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_type": "APPROVAL_WORKFLOW_ERROR"}
    )


@app.exception_handler(AlertNotFoundError)
async def alert_not_found_exception_handler(request, exc: AlertNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "error_type": "ALERT_NOT_FOUND"}
    )


@app.exception_handler(AlertEngineError)
async def alert_engine_exception_handler(request, exc: AlertEngineError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_type": "ALERT_ENGINE_ERROR"}
    )


@app.exception_handler(FeedbackNotFoundError)
async def feedback_not_found_exception_handler(request, exc: FeedbackNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "error_type": "FEEDBACK_NOT_FOUND"}
    )


@app.exception_handler(FeedbackValidationError)
async def feedback_validation_exception_handler(request, exc: FeedbackValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_type": "FEEDBACK_VALIDATION_ERROR"}
    )


@app.exception_handler(AuthenticationError)
async def authentication_exception_handler(request, exc: AuthenticationError):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc), "error_type": "AUTHENTICATION_REQUIRED"},
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.exception_handler(AuthorizationError)
async def authorization_exception_handler(request, exc: AuthorizationError):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": str(exc), "error_type": "INSUFFICIENT_PERMISSIONS"},
    )


@app.exception_handler(DatasetValidationError)
async def dataset_validation_exception_handler(request, exc: DatasetValidationError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_type": "DATASET_VALIDATION_ERROR"},
    )


# ==============================================================================
# AUTHENTICATION & ACCESS CONTROL HELPERS (PHASE 14)
# ==============================================================================

async def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """Extracts session from Authorization Bearer header, or defaults to guest VIEWER."""
    if authorization:
        session = auth_service.validate_token(authorization)
        if session:
            return {**session, "authenticated": True}
    return {
        "username": "anonymous_viewer",
        "full_name": "Public Guest Viewer",
        "role": "VIEWER",
        "department": "External Operations",
        "authenticated": False,
    }


def require_role(min_role: str):
    async def _role_checker(user: Dict[str, Any] = Depends(get_current_user)):
        auth_service.require_role(user if user.get("authenticated") else None, min_role)
        return user
    return _role_checker


# ==============================================================================
# READ-ONLY REST ENDPOINTS
# ==============================================================================

@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def get_health():
    """Returns backend health status, active run identifier, and service metadata."""
    if not data_loader:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data loader not initialized")
    return HealthResponse(
        status="healthy",
        service="ChainSentinel Operational Review Backend",
        version="1.0.0",
        authoritative_run_id=data_loader.run_id,
        active_event_id="SIM-DISR-2026-001",
        data_source_directory=data_loader.run_dir
    )


@app.get("/api/run", response_model=RunSummaryResponse, tags=["Run & Lineage"])
async def get_run_summary():
    """Returns the executive run summary, completion status, gate outcomes, and execution duration."""
    if not data_loader:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data loader not initialized")
    return data_loader.get_run_summary()


@app.get("/api/lineage", response_model=LineageResponse, tags=["Run & Lineage"])
async def get_lineage():
    """Returns the comprehensive cryptographic provenance trace across all pipeline stages."""
    if not data_loader:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data loader not initialized")
    return data_loader.get_lineage()


@app.get("/api/disruption", response_model=DisruptionEventResponse, tags=["Disruption Telemetry"])
async def get_disruption():
    """Returns the validated Phase 7 disruption event payload with HDFS source metadata."""
    if not data_loader:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data loader not initialized")
    return data_loader.get_disruption_event()


@app.get("/api/shockwave", response_model=ShockwaveResponse, tags=["Shockwave Propagation"])
async def get_shockwave():
    """Returns the Phase 8 supply-chain graph shockwave propagation results, entity counts, and exposure."""
    if not data_loader:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data loader not initialized")
    return data_loader.get_shockwave_data()


@app.get("/api/risk", response_model=RiskSummaryResponse, tags=["Risk Analysis"])
async def get_risk(sample_limit: int = Query(default=50, ge=1, le=500)):
    """
    Returns the Phase 9 Multi-Criteria Decision Analysis (MCDA) risk scores,
    severity distributions, and a sample of prioritized review orders with PII masked.
    """
    if not data_loader:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data loader not initialized")
    return data_loader.get_risk_summary(sample_limit=sample_limit)


@app.get("/api/recovery/plans", response_model=RecoveryPlansResponse, tags=["Recovery Optimization"])
async def get_recovery_plans():
    """Returns the side-by-side trade-off matrix of all six candidate recovery strategies."""
    if not data_loader:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data loader not initialized")
    return data_loader.get_recovery_plans()


@app.get("/api/recovery/recommended", response_model=RecommendedPlanResponse, tags=["Recovery Optimization"])
async def get_recommended_plan():
    """
    Returns the Phase 10 recommended recovery plan (Plan 5 Knapsack Hybrid)
    with explainability rationale, resource allocations, and resilience scores.
    """
    if not data_loader:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data loader not initialized")
    return data_loader.get_recommended_plan()


@app.get("/api/recovery/stress-tests", response_model=StressTestsResponse, tags=["Recovery Optimization"])
async def get_stress_tests():
    """Returns the complete 30-scenario counterfactual stress evaluation matrix across 5 disruption scenarios."""
    if not data_loader:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Data loader not initialized")
    return data_loader.get_stress_tests()


# ==============================================================================
# OPERATIONAL APPROVAL WORKFLOW ENDPOINTS (TASK 11D)
# ==============================================================================

@app.get("/api/approvals/{run_id}", response_model=ApprovalStateResponse, tags=["Approval Workflow"])
async def get_approval_state(run_id: str):
    """
    Returns the human review and approval status, latest decision receipt,
    and chronological audit trail for the specified run.
    """
    event_id = "SIM-DISR-2026-001"
    if data_loader:
        try:
            ev = data_loader.get_disruption_event()
            event_id = ev.get("event_id", "SIM-DISR-2026-001")
        except Exception:
            pass
    recommended_plan = "PLAN_5_KNAPSACK_HYBRID"
    return approval_service.get_approval_state(
        run_id=run_id,
        event_id=event_id,
        recommended_plan=recommended_plan
    )


@app.post("/api/approvals/decision", response_model=ApprovalRecord, response_model_exclude_none=True, tags=["Approval Workflow"])
async def record_approval_decision(req: ApprovalDecisionRequest):
    """
    Records an immutable human-in-the-loop review receipt adhering to data/approval_records/schema.json.
    Supported states: PENDING_REVIEW, APPROVED, REJECTED, REVISION_REQUESTED, CLOSED.
    Enforces simulation safeguards: simulation_only=True, physical_dispatch_executed=False.
    """
    active_run_id = req.run_id or (data_loader.run_id if data_loader else DEFAULT_RUN_ID)
    validate_safe_id("run_id", active_run_id)
    
    revision_dict = None
    if req.revision_request:
        revision_dict = {k: v for k, v in req.revision_request.dict().items() if v is not None}
    
    record = approval_service.record_decision(
        run_id=active_run_id,
        event_id=req.event_id,
        recommended_plan=req.recommended_plan,
        decision_status=req.decision_status,
        reviewer_username=req.reviewer_username,
        reviewer_role=req.reviewer_role,
        reviewer_department=req.reviewer_department,
        reviewer_comments=req.reviewer_comments,
        revision_request=revision_dict
    )
    audit_logger.log_event(
        event_type="APPROVAL_DECISION",
        action=req.decision_status,
        actor=req.reviewer_username,
        role=req.reviewer_role,
        status="SUCCESS",
        details={"approval_id": record.get("approval_id"), "run_id": active_run_id, "plan": req.recommended_plan}
    )
    return record


@app.post("/api/approvals/approve", response_model=ApprovalRecord, response_model_exclude_none=True, tags=["Approval Workflow"])
async def approve_recovery_plan(req: ApprovalDecisionRequest):
    """Submits an APPROVED decision receipt for the recommended recovery plan."""
    req.decision_status = "APPROVED"
    return await record_approval_decision(req)


@app.post("/api/approvals/reject", response_model=ApprovalRecord, response_model_exclude_none=True, tags=["Approval Workflow"])
async def reject_recovery_plan(req: ApprovalDecisionRequest):
    """Submits a REJECTED decision receipt for the recommended recovery plan."""
    req.decision_status = "REJECTED"
    return await record_approval_decision(req)


@app.post("/api/approvals/request-revision", response_model=ApprovalRecord, response_model_exclude_none=True, tags=["Approval Workflow"])
async def request_plan_revision(req: ApprovalDecisionRequest):
    """Submits a REVISION_REQUESTED decision receipt with operational feedback."""
    req.decision_status = "REVISION_REQUESTED"
    return await record_approval_decision(req)


@app.post("/api/approvals/close", response_model=ApprovalRecord, response_model_exclude_none=True, tags=["Approval Workflow"])
async def close_review_session(req: ApprovalDecisionRequest):
    """Submits a CLOSED decision receipt concluding the review lifecycle."""
    req.decision_status = "CLOSED"
    return await record_approval_decision(req)


# ==============================================================================
# REAL-TIME ALERTING & NOTIFICATION ENDPOINTS (PHASE 12)
# ==============================================================================

@app.get("/api/alerts", response_model=List[AlertRecord], tags=["Alerting"])
async def list_alerts(
    status: Optional[str] = Query(default=None, description="Filter by acknowledgement status (NEW, ACKNOWLEDGED, RESOLVED, DISMISSED)"),
    severity: Optional[str] = Query(default=None, description="Filter by severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)"),
    alert_type: Optional[str] = Query(default=None, description="Filter by alert type"),
    run_id: Optional[str] = Query(default=None, description="Filter by run ID")
):
    """Returns a list of operational alerts filtered by status, severity, or run ID."""
    return alert_engine.list_alerts(
        status=status,
        severity=severity,
        alert_type=alert_type,
        run_id=run_id
    )


@app.get("/api/alerts/summary", response_model=AlertSummaryResponse, tags=["Alerting"])
async def get_alerts_summary(
    run_id: Optional[str] = Query(default=None, description="Optional run ID filter")
):
    """Returns aggregated summary metrics of active alerts and severity breakdown."""
    return alert_engine.get_summary(run_id=run_id)


@app.get("/api/alerts/{alert_id}", response_model=AlertRecord, tags=["Alerting"])
async def get_alert_detail(alert_id: str):
    """Returns full details and lifecycle audit history for a single alert record."""
    validate_safe_id("alert_id", alert_id)
    return alert_engine.get_alert(alert_id)


@app.post("/api/alerts/{alert_id}/acknowledge", response_model=AlertRecord, tags=["Alerting"])
async def acknowledge_alert_endpoint(alert_id: str, req: Optional[AlertActionRequest] = None):
    """Transitions an alert from NEW to ACKNOWLEDGED with reviewer commentary."""
    validate_safe_id("alert_id", alert_id)
    user = req.user if req else "operational_reviewer"
    comments = req.comments if req else ""
    rec = alert_engine.acknowledge_alert(alert_id=alert_id, user=user, comments=comments)
    audit_logger.log_event(
        event_type="ALERT_LIFECYCLE",
        action="ACKNOWLEDGE",
        actor=user,
        status="SUCCESS",
        details={"alert_id": alert_id, "comments": comments}
    )
    return rec


@app.post("/api/alerts/{alert_id}/resolve", response_model=AlertRecord, tags=["Alerting"])
async def resolve_alert_endpoint(alert_id: str, req: Optional[AlertActionRequest] = None):
    """Transitions an alert to RESOLVED with resolution commentary."""
    validate_safe_id("alert_id", alert_id)
    user = req.user if req else "operational_reviewer"
    comments = req.comments if req else ""
    rec = alert_engine.resolve_alert(alert_id=alert_id, user=user, comments=comments)
    audit_logger.log_event(
        event_type="ALERT_LIFECYCLE",
        action="RESOLVE",
        actor=user,
        status="SUCCESS",
        details={"alert_id": alert_id, "comments": comments}
    )
    return rec


@app.post("/api/alerts/{alert_id}/dismiss", response_model=AlertRecord, tags=["Alerting"])
async def dismiss_alert_endpoint(alert_id: str, req: Optional[AlertActionRequest] = None):
    """Transitions an alert to DISMISSED."""
    validate_safe_id("alert_id", alert_id)
    user = req.user if req else "operational_reviewer"
    comments = req.comments if req else ""
    rec = alert_engine.dismiss_alert(alert_id=alert_id, user=user, comments=comments)
    audit_logger.log_event(
        event_type="ALERT_LIFECYCLE",
        action="DISMISS",
        actor=user,
        status="SUCCESS",
        details={"alert_id": alert_id, "comments": comments}
    )
    return rec


@app.post("/api/alerts/evaluate", response_model=List[AlertRecord], tags=["Alerting"])
async def evaluate_alerts_endpoint(
    run_id: Optional[str] = Query(default=None, description="Run ID to evaluate against rules")
):
    """Evaluates upstream pipeline stages against alert rules and synthesizes new alerts."""
    target_run = run_id or (data_loader.run_id if data_loader else DEFAULT_RUN_ID)
    validate_safe_id("run_id", target_run)
    created = alert_engine.evaluate_run(target_run)
    return created


# ==============================================================================
# PHASE 13 — CLOSED-LOOP LEARNING AND MODEL MONITORING ENDPOINTS
# ==============================================================================

@app.get("/api/models", response_model=List[ModelMetadataResponse], tags=["Model Monitoring"])
async def list_models_endpoint():
    """Returns inventory of production models, baseline metrics, and hyperparameters."""
    return model_evaluator.get_registered_models()


@app.get("/api/models/{model_id}/drift", response_model=ModelDriftResponse, tags=["Model Monitoring"])
async def get_model_drift_endpoint(model_id: str):
    """Calculates PSI, feature drift, and stability metrics for a specified model."""
    return model_evaluator.evaluate_model_drift(model_id=model_id)


@app.get("/api/feedback", response_model=List[FeedbackRecordResponse], tags=["Closed-Loop Feedback"])
async def list_feedback_endpoint(
    model_id: Optional[str] = Query(default=None, description="Filter by model ID"),
    feedback_type: Optional[str] = Query(default=None, description="Filter by feedback type"),
    validation_status: Optional[str] = Query(default=None, description="Filter by validation status"),
    run_id: Optional[str] = Query(default=None, description="Filter by run ID"),
):
    """Returns feedback records matching optional filters, sorted newest first."""
    return feedback_engine.list_feedback(
        model_id=model_id,
        feedback_type=feedback_type,
        validation_status=validation_status,
        run_id=run_id,
    )


@app.get("/api/feedback/summary", response_model=FeedbackSummaryResponse, tags=["Closed-Loop Feedback"])
async def get_feedback_summary_endpoint(
    model_id: Optional[str] = Query(default=None, description="Filter by model ID")
):
    """Returns aggregated feedback metrics, breakdown by type, and retraining eligibility."""
    return feedback_engine.get_summary_metrics(model_id=model_id)


@app.get("/api/feedback/{feedback_id}", response_model=FeedbackRecordResponse, tags=["Closed-Loop Feedback"])
async def get_feedback_detail_endpoint(feedback_id: str):
    """Retrieves full details and provenance for a single feedback record."""
    validate_safe_id("feedback_id", feedback_id)
    return feedback_engine.get_feedback(feedback_id=feedback_id)


@app.post("/api/feedback", response_model=FeedbackRecordResponse, tags=["Closed-Loop Feedback"])
async def create_feedback_endpoint(req: FeedbackCreateRequest):
    """Ingests and persists a new feedback, observation, or governance review record."""
    rec = feedback_engine.record_feedback(
        model_id=req.model_id,
        model_version=req.model_version,
        feedback_type=req.feedback_type,
        feedback_source=req.feedback_source,
        observation_timestamp=req.observation_timestamp,
        predicted_value=req.predicted_value,
        observed_value=req.observed_value,
        run_id=req.run_id,
        event_id=req.event_id,
        approval_id=req.approval_id,
        confidence=req.confidence,
        validation_status=req.validation_status,
        comments=req.comments or "",
        metadata=req.metadata,
    )
    audit_logger.log_event(
        event_type="FEEDBACK_INGEST",
        action=req.feedback_type,
        actor=req.feedback_source,
        status="RECORDED",
        details={"feedback_id": rec.get("feedback_id"), "model_id": req.model_id}
    )
    return rec


@app.post("/api/feedback/{feedback_id}/status", response_model=FeedbackRecordResponse, tags=["Closed-Loop Feedback"])
async def update_feedback_status_endpoint(feedback_id: str, req: FeedbackStatusUpdateRequest):
    """Transitions validation status of an existing feedback record with actor tracking."""
    validate_safe_id("feedback_id", feedback_id)
    rec = feedback_engine.update_validation_status(
        feedback_id=feedback_id,
        new_status=req.validation_status,
        actor=req.actor,
        comments=req.comments,
    )
    audit_logger.log_event(
        event_type="FEEDBACK_STATUS_UPDATE",
        action=req.validation_status,
        actor=req.actor,
        status="UPDATED",
        details={"feedback_id": feedback_id, "comments": req.comments}
    )
    return rec


@app.get("/api/models/experiments", response_model=List[RetrainingExperimentResponse], tags=["Model Retraining"])
async def list_retraining_experiments_endpoint():
    """Lists completed candidate retraining experiments and challenger evaluations."""
    return retraining_pipeline.list_experiments()


@app.post("/api/models/retrain-experiment", response_model=RetrainingExperimentResponse, tags=["Model Retraining"])
async def trigger_retraining_experiment_endpoint(req: Optional[RetrainingExperimentRequest] = None):
    """Triggers an isolated candidate retraining experiment in models/phase13_experiments/."""
    base_id = req.base_model_id if req else "delay_model_v1"
    name = req.experiment_name if req else None
    params = req.hyperparameters if req else None
    trigger = req.triggered_by if req else "API_OPERATOR"
    res = retraining_pipeline.run_candidate_experiment(
        base_model_id=base_id,
        experiment_name=name,
        hyperparameters=params,
        triggered_by=trigger,
    )
    audit_logger.log_event(
        event_type="RETRAINING_EXPERIMENT",
        action="TRIGGER_EXPERIMENT",
        actor=trigger,
        status="SUCCESS",
        details={"experiment_id": res.get("experiment_id"), "verdict": res.get("challenger_verdict")}
    )
    return res


# ==============================================================================
# PHASE 14 — AUTHENTICATION, ACCESS CONTROL & AUDIT LOGGING
# ==============================================================================

@app.post("/api/auth/login", response_model=LoginResponse, tags=["Authentication"])
async def login_endpoint(req: LoginRequest, request: Request):
    """Authenticates credentials and issues a secure session token."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    session = auth_service.login(username=req.username, password=req.password, client_ip=client_ip)
    audit_logger.log_event(
        event_type="AUTH",
        action="LOGIN_SUCCESS",
        actor=session["username"],
        role=session["role"],
        ip_address=client_ip,
        status="SUCCESS",
        details={"department": session["department"]}
    )
    return session


@app.post("/api/auth/logout", tags=["Authentication"])
async def logout_endpoint(request: Request, authorization: Optional[str] = Header(None)):
    """Revokes an active session token."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    if authorization:
        auth_service.logout(authorization)
    audit_logger.log_event(
        event_type="AUTH",
        action="LOGOUT",
        actor="user",
        ip_address=client_ip,
        status="SUCCESS"
    )
    return {"status": "logged_out", "detail": "Session token revoked successfully."}


@app.get("/api/auth/me", response_model=UserSessionResponse, tags=["Authentication"])
async def get_me_endpoint(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns profile and role of currently authenticated session or guest."""
    return UserSessionResponse(
        username=user["username"],
        full_name=user["full_name"],
        role=user["role"],
        department=user["department"],
        authenticated=user.get("authenticated", False),
        expires_at=user.get("expires_at"),
    )


@app.get("/api/audit/logs", response_model=List[AuditLogRecordResponse], tags=["Audit Logging"])
async def get_audit_logs_endpoint(
    limit: int = Query(default=50, ge=1, le=500),
    event_type: Optional[str] = Query(default=None),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Returns recent structured audit events."""
    return audit_logger.list_events(limit=limit, event_type=event_type)


# ==============================================================================
# 9. DATASET INTELLIGENCE (WORKFLOW A)
# ==============================================================================

@app.get("/api/datasets", response_model=List[DatasetMetadataResponse], tags=["Dataset Intelligence"])
@app.get("/datasets", response_model=List[DatasetMetadataResponse], include_in_schema=False)
async def list_datasets_endpoint():
    """Lists all available datasets in the catalog (DataCo original + synthetic + user uploads)."""
    return dataset_service.list_datasets()


@app.get("/api/datasets/{dataset_id}", response_model=DatasetMetadataResponse, tags=["Dataset Intelligence"])
@app.get("/datasets/{dataset_id}", response_model=DatasetMetadataResponse, include_in_schema=False)
async def get_dataset_metadata_endpoint(dataset_id: str):
    """Retrieves metadata, profiling, and model compatibility diagnostics for a dataset."""
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")
    return dataset


@app.get("/api/datasets/{dataset_id}/preview", response_model=DatasetPreviewResponse, tags=["Dataset Intelligence"])
@app.get("/datasets/{dataset_id}/preview", response_model=DatasetPreviewResponse, include_in_schema=False)
async def get_dataset_preview_endpoint(
    dataset_id: str,
    limit: int = Query(default=15, ge=1, le=100)
):
    """Previews first N records and schema of the dataset."""
    try:
        return dataset_service.get_dataset_preview(dataset_id, limit=limit)
    except DatasetValidationError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error previewing dataset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview dataset: {str(e)}")


@app.get("/api/datasets/{dataset_id}/geo", tags=["Dataset Intelligence"])
@app.get("/datasets/{dataset_id}/geo", include_in_schema=False)
async def get_dataset_geo_endpoint(
    dataset_id: str,
    filter_type: str = Query(default="all"),
    max_records: int = Query(default=5000, ge=100, le=50000)
):
    """
    Extracts, verifies, and aggregates genuine geographic intelligence from the dataset.
    Supports filters: all, delayed, non_delayed, anomalies, disruptions, high_risk.
    """
    try:
        from services.geo_service import geo_service
        return geo_service.get_dataset_geo_features(
            dataset_id=dataset_id,
            filter_type=filter_type,
            max_records=max_records
        )
    except Exception as e:
        logger.error(f"Error extracting geo features for {dataset_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Geo processing failed: {str(e)}")


@app.post("/api/datasets/upload", response_model=DatasetUploadResponse, tags=["Dataset Intelligence"])
async def upload_dataset_endpoint(
    file: UploadFile = File(...),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Securely uploads a new CSV dataset with size validation, safe filename sanitization,
    schema profiling, and feature compatibility verification.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files (.csv) are accepted.")

    # Write to temp file with size check (< 120MB)
    import tempfile
    MAX_SIZE = 120 * 1024 * 1024  # 120 MB
    bytes_read = 0

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_file:
        temp_path = temp_file.name
        try:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                bytes_read += len(chunk)
                if bytes_read > MAX_SIZE:
                    raise HTTPException(status_code=413, detail="File exceeds maximum allowed size of 120 MB.")
                temp_file.write(chunk)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    try:
        entry = dataset_service.register_upload(temp_path, file.filename)
        # Log to audit trail
        audit_logger.log_event(
            event_type="DATASET_UPLOAD",
            action=f"UPLOAD_DATASET_{entry['dataset_id']}",
            actor=user.get("username", "anonymous"),
            role=user.get("role", "REVIEWER"),
            ip_address="127.0.0.1",
            details={"dataset_id": entry["dataset_id"], "filename": entry["filename"], "rows": entry["row_count"]},
            status="SUCCESS"
        )
        return DatasetUploadResponse(
            success=True,
            message=f"Dataset '{entry['name']}' uploaded and validated successfully.",
            dataset=entry
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


# ==============================================================================
# 10. ISOLATED ANALYSIS RUNS (WORKFLOW A)
# ==============================================================================

@app.post("/api/analysis/{dataset_id}/run", response_model=AnalysisRunDetailResponse, tags=["Analysis Runs"])
@app.get("/api/analysis/{dataset_id}/run", response_model=AnalysisRunDetailResponse, tags=["Analysis Runs"])
@app.post("/analysis/{dataset_id}/run", response_model=AnalysisRunDetailResponse, include_in_schema=False)
@app.get("/analysis/{dataset_id}/run", response_model=AnalysisRunDetailResponse, include_in_schema=False)
async def trigger_analysis_run_endpoint(
    dataset_id: str,
    max_rows: int = Query(default=5000, ge=100, le=50000),
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Executes an isolated, multi-model analysis run on the selected dataset.
    Executes compatible Phase 5 models (Delay, Anomaly, Disruption, Demand).
    Supports both POST and GET invocation for seamless workflow integration.
    """
    dataset = dataset_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    try:
        run_result = analysis_run_manager.execute_analysis(dataset_id, max_rows=max_rows)
        # Audit log
        audit_logger.log_event(
            event_type="ANALYSIS_EXECUTION",
            action=f"EXECUTE_RUN_{run_result['run_id']}",
            actor=user.get("username", "anonymous"),
            role=user.get("role", "REVIEWER"),
            ip_address="127.0.0.1",
            details={
                "run_id": run_result["run_id"],
                "dataset_id": dataset_id,
                "models": run_result["models_executed"],
                "records": run_result["total_records"]
            },
            status="SUCCESS"
        )
        return run_result
    except DatasetValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis execution failed: {str(e)}")


@app.get("/api/analysis/runs", response_model=List[AnalysisRunSummary], tags=["Analysis Runs"])
@app.get("/analysis/runs", response_model=List[AnalysisRunSummary], include_in_schema=False)
async def list_analysis_runs_endpoint(dataset_id: Optional[str] = Query(default=None)):
    """Lists all completed analysis runs, optionally filtered by dataset ID."""
    return analysis_run_manager.list_runs(dataset_id=dataset_id)


@app.get("/api/analysis/runs/{run_id}", response_model=AnalysisRunDetailResponse, tags=["Analysis Runs"])
@app.get("/analysis/runs/{run_id}", response_model=AnalysisRunDetailResponse, include_in_schema=False)
async def get_analysis_run_endpoint(run_id: str):
    """Retrieves full analysis results, model outputs, and metrics for a specific run."""
    run = analysis_run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Analysis run '{run_id}' not found.")
    return run


@app.get("/api/analysis/runs/{run_id}/records", tags=["Analysis Runs"])
@app.get("/analysis/runs/{run_id}/records", include_in_schema=False)
async def get_analysis_run_records_endpoint(
    run_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=5, le=200),
    task: str = Query(default="delay", regex="^(delay|anomaly)$"),
    filter_status: Optional[str] = Query(default=None)
):
    """Retrieves paginated sample prediction records from an analysis run for drill-down inspection."""
    run = analysis_run_manager.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Analysis run '{run_id}' not found.")

    results = run.get("results", {})
    if task == "delay":
        records = results.get("delay_prediction", {}).get("sample_predictions", [])
    else:
        records = results.get("anomaly_detection", {}).get("sample_anomalies", [])

    if filter_status:
        if task == "delay":
            records = [r for r in records if r.get("predicted_status") == filter_status or r.get("risk_tier") == filter_status]
        else:
            records = [r for r in records if r.get("anomaly_class") == filter_status or (filter_status == "ANOMALY" and r.get("is_anomaly"))]

    total = len(records)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_items = records[start_idx:end_idx]

    return {
        "run_id": run_id,
        "task": task,
        "total_records": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 1,
        "records": page_items
    }





# Entrypoint for standalone execution
if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 70)
    print("STARTING CHAINSENTINEL FASTAPI REVIEW BACKEND (PORT 8000)")
    print("=" * 70)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=False)

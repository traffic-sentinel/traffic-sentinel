"""
Traffic Sentinel — Health Check Router
GET /health  →  liveness probe used by Docker / load balancer.
GET /ready   →  readiness probe (checks model + disk).
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.config import settings

router = APIRouter(tags=["health"])

APP_VERSION = "1.1.0"
_STARTED_AT = datetime.now(tz=timezone.utc).isoformat()


class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_since: str
    timestamp: str


class ReadinessResponse(HealthResponse):
    model_available: bool
    output_dir_writable: bool


@router.get("/health", response_model=HealthResponse, summary="Liveness probe")
def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version=APP_VERSION,
        uptime_since=_STARTED_AT,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
    )


@router.get("/ready", response_model=ReadinessResponse, summary="Readiness probe")
def readiness() -> ReadinessResponse:
    model_path: Path = settings.models_dir / settings.yolo_model
    model_ok = model_path.exists()

    out_dir: Path = settings.output_results_dir
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        test_file = out_dir / ".write_test"
        test_file.write_text("ok")
        test_file.unlink()
        disk_ok = True
    except OSError:
        disk_ok = False

    return ReadinessResponse(
        status="ready" if (model_ok and disk_ok) else "degraded",
        version=APP_VERSION,
        uptime_since=_STARTED_AT,
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        model_available=model_ok,
        output_dir_writable=disk_ok,
    )
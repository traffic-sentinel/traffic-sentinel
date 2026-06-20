"""
Traffic Sentinel — Main API Router
Thin route handlers that delegate to service classes.
Import this router into main.py:
    from backend.app.api.routes import router as main_router
    app.include_router(main_router, prefix="/api")
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from backend.app.config import settings
from backend.app.services.video_processor import VideoProcessorService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.risk_predictor import RiskPredictor
from backend.app.utils.helpers import timestamp_now

logger = logging.getLogger("traffic_sentinel.api.routes")

router = APIRouter(tags=["traffic"])

# Service singletons (lightweight — no model loaded until first request)
_video_svc = VideoProcessorService()
_analytics_svc = AnalyticsService()
_risk_predictor = RiskPredictor()

SUPPORTED_EXTENSIONS = set(settings.supported_video_extensions)


# ── Upload ───────────────────────────────────────────────────────────────────

@router.post("/upload", summary="Upload a video file for processing")
async def upload_video(file: UploadFile = File(...)) -> Dict:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{ext}'. Accepted: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    dest = settings.input_video_dir / (file.filename or "upload.mp4")
    settings.input_video_dir.mkdir(parents=True, exist_ok=True)

    with open(dest, "wb") as fh:
        content = await file.read()
        fh.write(content)

    logger.info("Uploaded video: %s (%.1f MB)", dest.name, len(content) / 1_048_576)
    return {
        "message": "Upload successful",
        "filename": dest.name,
        "size_bytes": len(content),
        "timestamp": timestamp_now(),
    }


# ── Videos list ──────────────────────────────────────────────────────────────

@router.get("/videos", summary="List uploaded videos")
def list_videos() -> Dict:
    videos = _video_svc.list_available()
    return {
        "videos": [v.name for v in videos],
        "count": len(videos),
    }


# ── Process ──────────────────────────────────────────────────────────────────

@router.post("/process", summary="Process all uploaded videos (background)")
def process_videos(background_tasks: BackgroundTasks) -> Dict:
    videos = _video_svc.list_available()
    if not videos:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No videos found in input directory.",
        )
    background_tasks.add_task(_run_batch, videos)
    return {
        "message": f"Processing {len(videos)} video(s) in background",
        "queued": [v.name for v in videos],
        "timestamp": timestamp_now(),
    }


def _run_batch(videos: List[Path]) -> None:
    try:
        _video_svc.process_batch(videos)
    except Exception as exc:
        logger.error("Batch processing failed: %s", exc)


# ── Results ───────────────────────────────────────────────────────────────────

@router.get("/results", summary="Return all stored processing results")
def get_results() -> Dict:
    results = _video_svc.load_results()
    return {"results": results, "count": len(results)}


@router.delete("/results", summary="Clear all stored results")
def clear_results() -> Dict:
    out_dir = settings.output_results_dir
    removed = 0
    for f in out_dir.glob("*.json"):
        f.unlink(missing_ok=True)
        removed += 1
    return {"message": f"Cleared {removed} result file(s)", "timestamp": timestamp_now()}


# ── Predictions ───────────────────────────────────────────────────────────────

@router.post("/predict", summary="Run risk prediction on stored results")
def predict() -> Dict:
    results = _video_svc.load_results()
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No processing results found. Run /api/process first.",
        )
    predictions = _risk_predictor.batch_predict(results)
    summary = _risk_predictor.generate_summary(predictions)
    return {
        "predictions": predictions,
        "summary": summary,
        "timestamp": timestamp_now(),
    }


@router.get("/predict", summary="Return the latest predictions (alias)")
def get_predictions() -> Dict:
    return predict()


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", summary="Dashboard summary statistics")
def dashboard() -> Dict:
    results = _video_svc.load_results()
    summary = _analytics_svc.dashboard_summary(results)
    trend = _analytics_svc.vehicle_trend(results)
    hotspots = _analytics_svc.rank_hotspots(results)
    alerts = _analytics_svc.flag_alerts(results)
    return {
        **summary,
        "trend": trend,
        "hotspots": hotspots,
        "active_alerts": len(alerts),
    }


# ── Hotspots ─────────────────────────────────────────────────────────────────

@router.get("/hotspots", summary="Top accident risk hotspots")
def hotspots(top_n: int = 5) -> Dict:
    results = _video_svc.load_results()
    ranked = _analytics_svc.rank_hotspots(results, top_n=top_n)
    return {"hotspots": ranked, "count": len(ranked)}
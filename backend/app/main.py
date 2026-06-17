"""
Traffic Sentinel — FastAPI Backend
REST API for video processing, risk prediction, and dashboard data.
"""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from .config import (
    API_HOST,
    API_PORT,
    INPUT_VIDEO_DIR,
    OUTPUT_RESULTS_DIR,
    settings,
)
from .video_processor import VideoProcessor
from .risk_predictor import RiskPredictor

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, settings.log_level, logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("traffic_sentinel.api")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Traffic Sentinel API",
    description=(
        "AI-powered traffic intelligence and accident hotspot prediction "
        "for Uganda's urban road network."
    ),
    version="1.1.0",
    contact={
        "name": "Keith Ndiema Kissa",
        "email": "keith@must.ac.ug",
    },
    license_info={"name": "MIT"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singletons ────────────────────────────────────────────────────────────────
video_processor = VideoProcessor()
risk_predictor = RiskPredictor()

# ── Thread-safe processing state ─────────────────────────────────────────────
_state_lock = threading.Lock()
_processing_state: Dict[str, Any] = {
    "status": "idle",
    "progress": 0,
    "message": "Ready",
    "started_at": None,
    "completed_at": None,
}


def _update_state(**kwargs: Any) -> None:
    with _state_lock:
        _processing_state.update(kwargs)


def _get_state() -> Dict[str, Any]:
    with _state_lock:
        return dict(_processing_state)


# ── Pydantic models ───────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    uptime_note: str = "Use /docs for interactive API explorer"


class ProcessingStatusResponse(BaseModel):
    status: str
    progress: int = Field(ge=0, le=100)
    message: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class PipelineStartResponse(BaseModel):
    status: str
    message: str
    poll_at: str = "/api/status"
    results_at: str = "/api/results"
    predictions_at: str = "/api/predictions"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _load_result_files(pattern: str = "result_*.json") -> List[Dict]:
    """Load all JSON result files matching pattern from output dir."""
    results = []
    if not OUTPUT_RESULTS_DIR.exists():
        return results
    for f in sorted(OUTPUT_RESULTS_DIR.glob(pattern)):
        try:
            results.append(json.loads(f.read_text()))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Skipping malformed file %s: %s", f.name, exc)
    return results


def _require_results() -> List[Dict]:
    """Return results or raise 404."""
    results = _load_result_files()
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No video results found. POST /api/process first.",
        )
    return results


# ── Background tasks ──────────────────────────────────────────────────────────
async def _run_video_processing() -> None:
    _update_state(
        status="processing",
        progress=5,
        message="Scanning input directory…",
        started_at=datetime.now().isoformat(),
        completed_at=None,
    )
    try:
        results = await asyncio.get_event_loop().run_in_executor(
            None, video_processor.process_batch, INPUT_VIDEO_DIR
        )
        count = len(results) if results else 0
        _update_state(
            status="completed",
            progress=100,
            message=f"✅ Processed {count} video(s)" if count else "⚠️ No videos found in input directory",
            completed_at=datetime.now().isoformat(),
        )
        logger.info("Video processing complete — %d video(s)", count)
    except Exception as exc:
        logger.exception("Video processing failed: %s", exc)
        _update_state(
            status="failed",
            progress=0,
            message=f"Error: {exc}",
            completed_at=datetime.now().isoformat(),
        )


async def _run_full_pipeline() -> None:
    _update_state(
        status="processing",
        progress=5,
        message="Step 1/3 — Processing videos…",
        started_at=datetime.now().isoformat(),
        completed_at=None,
    )
    try:
        # Step 1
        results = await asyncio.get_event_loop().run_in_executor(
            None, video_processor.process_batch, INPUT_VIDEO_DIR
        )
        if not results:
            _update_state(
                status="completed",
                progress=100,
                message="⚠️ No videos found in input directory",
                completed_at=datetime.now().isoformat(),
            )
            return

        _update_state(progress=45, message=f"Step 2/3 — Predicting risk for {len(results)} video(s)…")

        # Step 2
        predictions = risk_predictor.batch_predict(results)
        summary = risk_predictor.generate_summary(predictions)

        _update_state(progress=85, message="Step 3/3 — Saving report…")

        # Step 3
        pipeline_output = {
            "pipeline_run_time": datetime.now().isoformat(),
            "total_videos_processed": len(results),
            "predictions": predictions,
            "summary": summary,
        }
        out_file = OUTPUT_RESULTS_DIR / "final_risk_predictions.json"
        out_file.write_text(json.dumps(pipeline_output, indent=2))

        _update_state(
            status="completed",
            progress=100,
            message=f"✅ Pipeline complete — {len(results)} videos · {len(predictions)} predictions",
            completed_at=datetime.now().isoformat(),
        )
        logger.info("Full pipeline complete")
    except Exception as exc:
        logger.exception("Pipeline failed: %s", exc)
        _update_state(
            status="failed",
            progress=0,
            message=f"Pipeline error: {exc}",
            completed_at=datetime.now().isoformat(),
        )


# ── Routes: info ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Info"])
async def root() -> Dict:
    return {
        "name": "Traffic Sentinel API",
        "version": "1.1.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Info"])
async def health() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        version="1.1.0",
        timestamp=datetime.now().isoformat(),
    )


# ── Routes: processing ────────────────────────────────────────────────────────
@app.get("/api/status", response_model=ProcessingStatusResponse, tags=["Processing"])
async def get_status() -> ProcessingStatusResponse:
    return ProcessingStatusResponse(**_get_state())


@app.post("/api/process", response_model=PipelineStartResponse, tags=["Processing"])
async def process_videos(background_tasks: BackgroundTasks) -> PipelineStartResponse:
    if _get_state()["status"] == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A processing job is already running. Poll /api/status.",
        )
    background_tasks.add_task(_run_video_processing)
    return PipelineStartResponse(status="started", message="Video processing started in background")


@app.get("/api/results", tags=["Processing"])
async def get_results(limit: int = Query(default=50, ge=1, le=200)) -> Dict:
    results = _load_result_files()
    return {
        "results": results[:limit],
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# ── Routes: upload ────────────────────────────────────────────────────────────
@app.post("/api/upload", tags=["Processing"])
async def upload_video(file: UploadFile = File(...)) -> Dict:
    """Upload a video file for processing."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.supported_video_extensions:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported format '{suffix}'. Use: {settings.supported_video_extensions}",
        )
    dest = INPUT_VIDEO_DIR / (file.filename or "upload.mp4")
    try:
        with dest.open("wb") as f:
            shutil.copyfileobj(file.file, f)
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"Could not save file: {exc}")
    return {
        "status": "uploaded",
        "filename": dest.name,
        "size_bytes": dest.stat().st_size,
        "next": "POST /api/process",
    }


# ── Routes: dashboard ─────────────────────────────────────────────────────────
@app.get("/api/dashboard", tags=["Dashboard"])
async def get_dashboard() -> Dict:
    results = _load_result_files()
    if not results:
        return {
            "total_videos": 0,
            "overall_avg_vehicles": 0,
            "peak_vehicles": 0,
            "total_detections": 0,
            "high_density_frames": 0,
            "peak_risk_period": "17:00 – 21:00",
            "results": [],
            "timestamp": datetime.now().isoformat(),
        }

    avg_list = [r.get("avg_vehicles_per_sample", 0) for r in results]
    peak_list = [r.get("peak_vehicles", 0) for r in results]
    hdf_list = [r.get("high_density_frames", 0) for r in results]

    return {
        "total_videos": len(results),
        "overall_avg_vehicles": round(sum(avg_list) / len(avg_list), 1) if avg_list else 0,
        "peak_vehicles": max(peak_list) if peak_list else 0,
        "total_detections": int(sum(avg_list) * 10),
        "high_density_frames": sum(hdf_list),
        "peak_risk_period": "17:00 – 21:00",
        "results": results[:5],
        "timestamp": datetime.now().isoformat(),
    }


# ── Routes: predictions ───────────────────────────────────────────────────────
@app.post("/api/predict", tags=["Prediction"])
async def predict_risk() -> Dict:
    video_results = _require_results()
    predictions = risk_predictor.batch_predict(video_results)
    summary = risk_predictor.generate_summary(predictions)
    output = {
        "pipeline_run_time": datetime.now().isoformat(),
        "total_videos_processed": len(video_results),
        "predictions": predictions,
        "summary": summary,
    }
    pred_file = OUTPUT_RESULTS_DIR / "final_risk_predictions.json"
    pred_file.write_text(json.dumps(output, indent=2))
    logger.info("Predictions generated for %d video(s)", len(video_results))
    return output


@app.get("/api/predictions", tags=["Prediction"])
async def get_predictions() -> Dict:
    pred_file = OUTPUT_RESULTS_DIR / "final_risk_predictions.json"
    if not pred_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No predictions yet. POST /api/predict to generate.",
        )
    try:
        return json.loads(pred_file.read_text())
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Predictions file is corrupted.")


# ── Routes: pipeline ──────────────────────────────────────────────────────────
@app.post("/api/pipeline", response_model=PipelineStartResponse, tags=["Pipeline"])
async def run_pipeline(background_tasks: BackgroundTasks) -> PipelineStartResponse:
    if _get_state()["status"] == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Processing already in progress.",
        )
    background_tasks.add_task(_run_full_pipeline)
    return PipelineStartResponse(
        status="started",
        message="Full pipeline (video processing + risk prediction) started",
    )


# ── Routes: utility ───────────────────────────────────────────────────────────
@app.get("/api/videos", tags=["Utility"])
async def list_videos() -> Dict:
    if not INPUT_VIDEO_DIR.exists():
        return {"videos": [], "count": 0, "input_directory": str(INPUT_VIDEO_DIR)}
    videos = [
        f.name
        for f in INPUT_VIDEO_DIR.iterdir()
        if f.suffix.lower() in settings.supported_video_extensions
    ]
    return {"videos": sorted(videos), "count": len(videos), "input_directory": str(INPUT_VIDEO_DIR)}


@app.get("/api/download/predictions", tags=["Utility"])
async def download_predictions() -> FileResponse:
    pred_file = OUTPUT_RESULTS_DIR / "final_risk_predictions.json"
    if not pred_file.exists():
        raise HTTPException(status_code=404, detail="No predictions file found.")
    return FileResponse(
        pred_file,
        filename=f"traffic_sentinel_predictions_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        media_type="application/json",
    )


@app.delete("/api/clear", tags=["Utility"])
async def clear_results() -> Dict:
    """Reset all output results and processing state. Useful for demo resets."""
    if OUTPUT_RESULTS_DIR.exists():
        shutil.rmtree(OUTPUT_RESULTS_DIR)
    OUTPUT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    _update_state(status="idle", progress=0, message="Ready", started_at=None, completed_at=None)
    return {"status": "cleared", "message": "All results removed. Ready for fresh demo."}


# Keep GET /api/clear for backward compat (Streamlit calls it with requests.get)
app.get("/api/clear", tags=["Utility"])(clear_results)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Traffic Sentinel API on %s:%s", API_HOST, API_PORT)
    uvicorn.run("backend.app.main:app", host=API_HOST, port=API_PORT, reload=settings.api_reload)
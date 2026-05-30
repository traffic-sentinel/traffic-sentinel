"""
Traffic Sentinel - FastAPI Backend
Main application entry point with REST API endpoints
"""

import logging
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from datetime import datetime

from .config import INPUT_VIDEO_DIR, OUTPUT_RESULTS_DIR, API_HOST, API_PORT
from .video_processor import VideoProcessor
from .risk_predictor import RiskPredictor
from .models import (
    ProcessingStatus,
    HealthCheck,
    VideoProcessingResult,
    RiskPrediction,
    PipelineOutput,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Traffic Sentinel API",
    description="AI-powered traffic intelligence and accident prediction system",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize processors
video_processor = VideoProcessor()
risk_predictor = RiskPredictor()

# Global state (for demo purposes)
processing_state = {"status": "idle", "progress": 0, "message": "Ready"}


# ============================================================================
# HEALTH & INFO ENDPOINTS
# ============================================================================


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Traffic Sentinel API",
        "version": "1.0.0",
        "description": "AI traffic intelligence and accident hotspot prediction",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "process_videos": "/api/process",
            "get_results": "/api/results",
            "get_predictions": "/api/predictions",
            "get_full_pipeline": "/api/pipeline",
        },
    }


@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat(),
    )


# ============================================================================
# VIDEO PROCESSING ENDPOINTS
# ============================================================================


@app.get("/api/status", response_model=ProcessingStatus, tags=["Processing"])
async def get_processing_status():
    """Get current processing status"""
    return ProcessingStatus(
        status=processing_state["status"],
        progress=processing_state["progress"],
        message=processing_state["message"],
    )


@app.post("/api/process", tags=["Processing"])
async def process_videos(background_tasks: BackgroundTasks):
    """
    Process all videos in the input directory

    Returns:
        Processing status and job info
    """
    if processing_state["status"] == "processing":
        raise HTTPException(status_code=409, detail="Processing already in progress")

    # Start background processing
    background_tasks.add_task(_run_video_processing)

    return {
        "status": "started",
        "message": "Video processing started in background",
        "check_status_at": "/api/status",
        "check_results_at": "/api/results",
    }


async def _run_video_processing():
    """Background task: Process all videos"""
    try:
        processing_state["status"] = "processing"
        processing_state["progress"] = 0
        processing_state["message"] = "Initializing video processing..."

        logger.info("Starting video processing pipeline...")

        # Process all videos
        results = video_processor.process_batch(INPUT_VIDEO_DIR)

        if not results:
            processing_state["status"] = "completed"
            processing_state["progress"] = 100
            processing_state["message"] = "No videos found to process"
            logger.warning("No videos found in input directory")
            return

        # Process each video (simulated progress)
        for idx, result in enumerate(results):
            processing_state["progress"] = int(((idx + 1) / len(results)) * 90)
            processing_state["message"] = f"Processing: {result['video_name']}"

        processing_state["progress"] = 100
        processing_state["status"] = "completed"
        processing_state["message"] = f"✅ Processed {len(results)} video(s)"

        logger.info(f"✅ Video processing complete: {len(results)} videos processed")

    except Exception as e:
        logger.error(f"Error during video processing: {e}")
        processing_state["status"] = "failed"
        processing_state["message"] = str(e)


@app.get("/api/results", tags=["Processing"])
async def get_video_results():
    """Get all video processing results"""
    results = []

    if not OUTPUT_RESULTS_DIR.exists():
        return {"results": [], "count": 0}

    # Load all result files
    for result_file in OUTPUT_RESULTS_DIR.glob("result_*.json"):
        try:
            with open(result_file, "r") as f:
                data = json.load(f)
                results.append(data)
        except json.JSONDecodeError:
            logger.warning(f"Could not parse {result_file}")

    return {
        "results": results,
        "count": len(results),
        "timestamp": datetime.now().isoformat(),
    }


# ============================================================================
# RISK PREDICTION ENDPOINTS
# ============================================================================


@app.post("/api/predict", tags=["Prediction"])
async def predict_risk(background_tasks: BackgroundTasks):
    """
    Predict risk for all processed videos

    Returns:
        Risk predictions and summary
    """
    # Load results
    results_file = OUTPUT_RESULTS_DIR / "processing_summary.json"

    if not results_file.exists():
        # Try to load individual result files
        video_results = []
        if OUTPUT_RESULTS_DIR.exists():
            for result_file in OUTPUT_RESULTS_DIR.glob("result_*.json"):
                try:
                    with open(result_file, "r") as f:
                        video_results.append(json.load(f))
                except json.JSONDecodeError:
                    pass
    else:
        try:
            with open(results_file, "r") as f:
                data = json.load(f)
                video_results = data.get("results", [])
        except json.JSONDecodeError:
            video_results = []

    if not video_results:
        raise HTTPException(
            status_code=404, detail="No video results found. Process videos first."
        )

    # Generate predictions
    predictions = risk_predictor.batch_predict(video_results)
    summary = risk_predictor.generate_summary(predictions)

    # Save predictions
    pipeline_output = {
        "pipeline_run_time": datetime.now().isoformat(),
        "total_videos_processed": len(video_results),
        "predictions": predictions,
        "summary": summary,
    }

    output_file = OUTPUT_RESULTS_DIR / "final_risk_predictions.json"
    with open(output_file, "w") as f:
        json.dump(pipeline_output, f, indent=2)

    logger.info(f"✅ Risk predictions generated: {len(predictions)} predictions")

    return pipeline_output


@app.get("/api/predictions", tags=["Prediction"])
async def get_predictions():
    """Get final risk predictions"""
    pred_file = OUTPUT_RESULTS_DIR / "final_risk_predictions.json"

    if not pred_file.exists():
        raise HTTPException(
            status_code=404, detail="No predictions available. Run /api/predict first."
        )

    try:
        with open(pred_file, "r") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Could not read predictions file")


# ============================================================================
# FULL PIPELINE ENDPOINT
# ============================================================================


@app.post("/api/pipeline", tags=["Pipeline"])
async def run_full_pipeline(background_tasks: BackgroundTasks):
    """
    Run the complete pipeline: video processing + risk prediction

    Returns:
        Pipeline execution info
    """
    if processing_state["status"] == "processing":
        raise HTTPException(status_code=409, detail="Processing already in progress")

    background_tasks.add_task(_run_full_pipeline)

    return {
        "status": "started",
        "message": "Full pipeline started in background",
        "steps": ["Video Processing", "Risk Prediction", "Report Generation"],
        "check_status_at": "/api/status",
        "check_results_at": "/api/results",
        "check_predictions_at": "/api/predictions",
    }


async def _run_full_pipeline():
    """Background task: Run complete pipeline"""
    try:
        processing_state["status"] = "processing"
        processing_state["progress"] = 0
        processing_state["message"] = "Starting full pipeline..."

        # Step 1: Video Processing
        logger.info("Step 1/3: Processing videos...")
        processing_state["message"] = "Step 1/3: Processing videos..."
        results = video_processor.process_batch(INPUT_VIDEO_DIR)

        if not results:
            processing_state["status"] = "completed"
            processing_state["message"] = "No videos found to process"
            return

        processing_state["progress"] = 40
        processing_state["message"] = f"Step 2/3: Generating predictions for {len(results)} video(s)..."

        # Step 2: Risk Prediction
        logger.info("Step 2/3: Predicting risk...")
        predictions = risk_predictor.batch_predict(results)
        summary = risk_predictor.generate_summary(predictions)

        processing_state["progress"] = 80
        processing_state["message"] = "Step 3/3: Saving report..."

        # Step 3: Save final report
        logger.info("Step 3/3: Generating final report...")
        pipeline_output = {
            "pipeline_run_time": datetime.now().isoformat(),
            "total_videos_processed": len(results),
            "predictions": predictions,
            "summary": summary,
        }

        output_file = OUTPUT_RESULTS_DIR / "final_risk_predictions.json"
        with open(output_file, "w") as f:
            json.dump(pipeline_output, f, indent=2)

        processing_state["progress"] = 100
        processing_state["status"] = "completed"
        processing_state["message"] = (
            f"✅ Pipeline complete: {len(results)} videos, {len(predictions)} predictions"
        )

        logger.info("✅ Full pipeline complete!")

    except Exception as e:
        logger.error(f"Pipeline error: {e}")
        processing_state["status"] = "failed"
        processing_state["message"] = str(e)


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================


@app.get("/api/videos", tags=["Utility"])
async def list_input_videos():
    """List all videos in the input directory"""
    if not INPUT_VIDEO_DIR.exists():
        return {"videos": [], "count": 0}

    videos = [
        f.name
        for f in INPUT_VIDEO_DIR.iterdir()
        if f.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv"]
    ]

    return {
        "videos": videos,
        "count": len(videos),
        "input_directory": str(INPUT_VIDEO_DIR),
    }


@app.get("/api/download/predictions", tags=["Utility"])
async def download_predictions():
    """Download final predictions as JSON"""
    pred_file = OUTPUT_RESULTS_DIR / "final_risk_predictions.json"

    if not pred_file.exists():
        raise HTTPException(status_code=404, detail="Predictions file not found")

    return FileResponse(
        pred_file, filename="traffic_sentinel_predictions.json", media_type="application/json"
    )


@app.get("/api/clear", tags=["Utility"])
async def clear_results():
    """Clear all processing results (for demo reset)"""
    import shutil

    if OUTPUT_RESULTS_DIR.exists():
        shutil.rmtree(OUTPUT_RESULTS_DIR)
    OUTPUT_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    processing_state["status"] = "idle"
    processing_state["progress"] = 0
    processing_state["message"] = "Ready"

    return {"status": "cleared", "message": "All results cleared"}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting Traffic Sentinel API on {API_HOST}:{API_PORT}")
    uvicorn.run(app, host=API_HOST, port=API_PORT)

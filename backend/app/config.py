"""
Traffic Sentinel - Configuration Module
Centralized configuration for the MVP backend
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
INPUT_VIDEO_DIR = DATA_DIR / "input_video"
OUTPUT_RESULTS_DIR = DATA_DIR / "output_results"
SAMPLE_FRAMES_DIR = DATA_DIR / "sample_framing"
MODELS_DIR = PROJECT_ROOT / "models"

# Create directories if they don't exist
for directory in [INPUT_VIDEO_DIR, OUTPUT_RESULTS_DIR, SAMPLE_FRAMES_DIR, MODELS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# API Configuration
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_RELOAD = os.getenv("API_RELOAD", "true").lower() == "true"

# Video Processing
VIDEO_SAMPLE_INTERVAL = 30  # Sample every 30 frames
VIDEO_FRAME_SAVE_INTERVAL = 90  # Save frame every 90 frames (3 seconds at 30fps)
MAX_VIDEO_DURATION_MINUTES = 30  # Max video length to process

# YOLO Configuration
YOLO_MODEL = "yolov8n.pt"  # Nano model for speed (lightweight MVP)
YOLO_CONFIDENCE_THRESHOLD = 0.5
VEHICLE_CLASSES = {
    0: "car",
    1: "truck",
    2: "bus",
    3: "motorcycle",
    5: "motorcycle",  # Class 5 is motorcycle in YOLO
}

# Risk Scoring (Uganda context)
HIGH_TRAFFIC_THRESHOLD = 20  # vehicles per sample
MEDIUM_TRAFFIC_THRESHOLD = 12
HIGH_RISK_HOURS = (17, 7)  # 5 PM to 7 AM (evening/night in Kampala)
HIGH_RISK_HOUR_BONUS = 15  # Additional risk points during peak hours

# Default locations (for demo - update with real GPS data)
DEFAULT_LOCATION = "Kampala Sample Junction"
SAMPLE_LOCATIONS = {
    "kampala_roundabout": {"name": "Kampala Roundabout", "lat": 0.3476, "lon": 32.5825},
    "mbarara_junction": {"name": "Mbarara Junction", "lat": -0.6123, "lon": 29.7597},
    "entebbe_road": {"name": "Entebbe Road", "lat": 0.2164, "lon": 32.4397},
}

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

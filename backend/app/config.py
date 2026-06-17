"""
Traffic Sentinel — Centralised Configuration
Reads from environment variables / .env file.
Usage: from backend.app.core.config import settings
"""

from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Tuple

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field

    class Settings(BaseSettings):
        # ── Project paths ────────────────────────────────────────────────
        project_root: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)

        @property
        def data_dir(self) -> Path:
            return self.project_root / "data"

        @property
        def input_video_dir(self) -> Path:
            return self.data_dir / "input_video"

        @property
        def output_results_dir(self) -> Path:
            return self.data_dir / "output_results"

        @property
        def sample_frames_dir(self) -> Path:
            return self.data_dir / "sample_framing"

        @property
        def models_dir(self) -> Path:
            return self.project_root / "models"

        # ── API ──────────────────────────────────────────────────────────
        api_host: str = Field(default="0.0.0.0", env="API_HOST")
        api_port: int = Field(default=8000, env="API_PORT")
        api_reload: bool = Field(default=True, env="API_RELOAD")
        api_workers: int = Field(default=1, env="API_WORKERS")

        # ── CORS ─────────────────────────────────────────────────────────
        cors_origins: List[str] = Field(
            default=["http://localhost:3000", "http://localhost:8501"],
            env="CORS_ORIGINS",
        )

        # ── Video processing ─────────────────────────────────────────────
        video_sample_interval: int = Field(default=30, env="VIDEO_SAMPLE_INTERVAL")
        video_frame_save_interval: int = Field(default=90, env="VIDEO_FRAME_SAVE_INTERVAL")
        max_video_duration_minutes: int = Field(default=30, env="MAX_VIDEO_DURATION_MINUTES")
        supported_video_extensions: List[str] = Field(
            default=[".mp4", ".avi", ".mov", ".mkv"]
        )

        # ── YOLO ─────────────────────────────────────────────────────────
        yolo_model: str = Field(default="yolov8n.pt", env="YOLO_MODEL")
        yolo_confidence_threshold: float = Field(default=0.5, env="YOLO_CONFIDENCE")
        yolo_iou_threshold: float = Field(default=0.45, env="YOLO_IOU")
        yolo_device: str = Field(default="cpu", env="YOLO_DEVICE")  # "cpu" | "0" (GPU)

        # COCO class IDs that map to vehicles (Uganda context: include boda-bodas)
        vehicle_class_ids: List[int] = Field(default=[2, 3, 5, 7])  # car, motorbike, bus, truck

        # ── Risk scoring ─────────────────────────────────────────────────
        high_traffic_threshold: int = Field(default=20, env="HIGH_TRAFFIC_THRESHOLD")
        medium_traffic_threshold: int = Field(default=12, env="MEDIUM_TRAFFIC_THRESHOLD")
        # (start_hour, end_hour) — risk hours are OUTSIDE this daytime window
        daytime_safe_hours: Tuple[int, int] = Field(default=(8, 17))
        high_risk_hour_bonus: int = Field(default=15, env="HIGH_RISK_HOUR_BONUS")
        night_risk_bonus: int = Field(default=20, env="NIGHT_RISK_BONUS")

        # ── Default locations (demo GPS pins) ────────────────────────────
        default_location: str = "Kampala Sample Junction"
        sample_locations: Dict[str, Dict] = Field(
            default={
                "kampala_roundabout": {
                    "name": "Clock Tower Roundabout",
                    "lat": 0.3131,
                    "lon": 32.5811,
                },
                "wandegeya": {
                    "name": "Wandegeya Junction",
                    "lat": 0.3437,
                    "lon": 32.5683,
                },
                "mbarara_junction": {
                    "name": "Mbarara Main Junction",
                    "lat": -0.6123,
                    "lon": 29.7597,
                },
                "entebbe_road": {
                    "name": "Entebbe Road Junction",
                    "lat": 0.2164,
                    "lon": 32.4397,
                },
            }
        )

        # ── Logging ──────────────────────────────────────────────────────
        log_level: str = Field(default="INFO", env="LOG_LEVEL")
        log_to_file: bool = Field(default=False, env="LOG_TO_FILE")
        log_file: Path = Field(default=Path("logs/traffic_sentinel.log"), env="LOG_FILE")

        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False

        def ensure_directories(self) -> None:
            """Create required directories if missing."""
            for d in [
                self.input_video_dir,
                self.output_results_dir,
                self.sample_frames_dir,
                self.models_dir,
            ]:
                d.mkdir(parents=True, exist_ok=True)

        @property
        def vehicle_classes(self) -> Dict[int, str]:
            """Map COCO class IDs to readable names."""
            coco_map = {
                2: "car",
                3: "motorcycle",
                5: "bus",
                7: "truck",
            }
            return {k: coco_map[k] for k in self.vehicle_class_ids if k in coco_map}

except ImportError:
    # Fallback: plain dataclass if pydantic-settings is not installed
    import logging
    logging.warning("pydantic-settings not installed — falling back to os.environ config")

    class Settings:  # type: ignore[no-redef]
        project_root = Path(__file__).parent.parent.parent
        data_dir = project_root / "data"
        input_video_dir = data_dir / "input_video"
        output_results_dir = data_dir / "output_results"
        sample_frames_dir = data_dir / "sample_framing"
        models_dir = project_root / "models"

        api_host: str = os.getenv("API_HOST", "0.0.0.0")
        api_port: int = int(os.getenv("API_PORT", "8000"))
        api_reload: bool = os.getenv("API_RELOAD", "true").lower() == "true"

        video_sample_interval: int = int(os.getenv("VIDEO_SAMPLE_INTERVAL", "30"))
        video_frame_save_interval: int = int(os.getenv("VIDEO_FRAME_SAVE_INTERVAL", "90"))
        max_video_duration_minutes: int = int(os.getenv("MAX_VIDEO_DURATION_MINUTES", "30"))
        supported_video_extensions = [".mp4", ".avi", ".mov", ".mkv"]

        yolo_model: str = os.getenv("YOLO_MODEL", "yolov8n.pt")
        yolo_confidence_threshold: float = float(os.getenv("YOLO_CONFIDENCE", "0.5"))
        yolo_iou_threshold: float = float(os.getenv("YOLO_IOU", "0.45"))
        yolo_device: str = os.getenv("YOLO_DEVICE", "cpu")
        vehicle_class_ids = [2, 3, 5, 7]

        high_traffic_threshold: int = int(os.getenv("HIGH_TRAFFIC_THRESHOLD", "20"))
        medium_traffic_threshold: int = int(os.getenv("MEDIUM_TRAFFIC_THRESHOLD", "12"))
        daytime_safe_hours = (8, 17)
        high_risk_hour_bonus: int = int(os.getenv("HIGH_RISK_HOUR_BONUS", "15"))
        night_risk_bonus: int = int(os.getenv("NIGHT_RISK_BONUS", "20"))

        default_location = "Kampala Sample Junction"
        log_level: str = os.getenv("LOG_LEVEL", "INFO")

        @property
        def vehicle_classes(self):
            return {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

        def ensure_directories(self):
            for d in [
                self.input_video_dir,
                self.output_results_dir,
                self.sample_frames_dir,
                self.models_dir,
            ]:
                d.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    s = Settings()
    s.ensure_directories()
    return s


# Module-level convenience exports (keep backward compat with existing imports)
settings = get_settings()

INPUT_VIDEO_DIR = settings.input_video_dir
OUTPUT_RESULTS_DIR = settings.output_results_dir
SAMPLE_FRAMES_DIR = settings.sample_frames_dir
MODELS_DIR = settings.models_dir
API_HOST = settings.api_host
API_PORT = settings.api_port
API_RELOAD = settings.api_reload
VIDEO_SAMPLE_INTERVAL = settings.video_sample_interval
VIDEO_FRAME_SAVE_INTERVAL = settings.video_frame_save_interval
YOLO_MODEL = settings.yolo_model
YOLO_CONFIDENCE_THRESHOLD = settings.yolo_confidence_threshold
VEHICLE_CLASSES = settings.vehicle_classes
HIGH_TRAFFIC_THRESHOLD = settings.high_traffic_threshold
MEDIUM_TRAFFIC_THRESHOLD = settings.medium_traffic_threshold
HIGH_RISK_HOURS = (settings.daytime_safe_hours[1], settings.daytime_safe_hours[0])
HIGH_RISK_HOUR_BONUS = settings.high_risk_hour_bonus
DEFAULT_LOCATION = settings.default_location
SAMPLE_LOCATIONS = settings.sample_locations
LOG_LEVEL = settings.log_level
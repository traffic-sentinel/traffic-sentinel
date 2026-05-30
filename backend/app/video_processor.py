"""
Traffic Sentinel - Video Processing Module
YOLO-based vehicle detection and traffic analysis
"""

import cv2
import numpy as np
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from ultralytics import YOLO
import logging

from .config import (
    VIDEO_SAMPLE_INTERVAL,
    VIDEO_FRAME_SAVE_INTERVAL,
    YOLO_MODEL,
    YOLO_CONFIDENCE_THRESHOLD,
    VEHICLE_CLASSES,
    OUTPUT_RESULTS_DIR,
    SAMPLE_FRAMES_DIR,
    MODELS_DIR,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VideoProcessor:
    """Process traffic videos with YOLO detection"""

    def __init__(self):
        """Initialize video processor with YOLO model"""
        self.model_path = MODELS_DIR / YOLO_MODEL
        self._ensure_model_downloaded()
        self.model = YOLO(str(self.model_path))
        logger.info(f"YOLO model loaded: {self.model_path}")

    def _ensure_model_downloaded(self):
        """Download YOLO model if not already present"""
        if not self.model_path.exists():
            logger.info(f"Downloading YOLO model to {self.model_path}...")
            YOLO(YOLO_MODEL)  # This downloads the model
            logger.info("Model download complete")

    def process_video(self, video_path: str) -> Dict:
        """
        Process a single video file with vehicle detection

        Args:
            video_path: Path to video file

        Returns:
            Dict with processing results
        """
        video_path = Path(video_path)
        if not video_path.exists():
            logger.error(f"Video not found: {video_path}")
            return None

        logger.info(f"Processing video: {video_path}")
        start_time = datetime.now()

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.error(f"Could not open video: {video_path}")
            return None

        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0

        features = []
        frame_number = 0
        vehicle_counts = []
        all_vehicle_classes = {}

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_number += 1

            # Sample every N frames to save computation
            if frame_number % VIDEO_SAMPLE_INTERVAL == 0:
                vehicle_count, class_counts = self._detect_vehicles(frame)
                vehicle_counts.append(vehicle_count)

                # Track class distribution
                for cls, count in class_counts.items():
                    all_vehicle_classes[cls] = all_vehicle_classes.get(cls, 0) + count

                features.append({
                    "frame": frame_number,
                    "timestamp": str(datetime.now()),
                    "vehicle_count": vehicle_count,
                    "vehicle_classes": class_counts,
                    "density": self._get_density_level(vehicle_count),
                })

                # Save sample frames periodically
                if frame_number % VIDEO_FRAME_SAVE_INTERVAL == 0:
                    self._save_sample_frame(frame, video_path, frame_number)

        cap.release()

        # Calculate statistics
        avg_vehicles = (
            sum(vehicle_counts) / len(vehicle_counts) if vehicle_counts else 0
        )
        peak_vehicles = max(vehicle_counts) if vehicle_counts else 0

        processing_time = (datetime.now() - start_time).total_seconds()

        result = {
            "video_name": video_path.name,
            "video_path": str(video_path),
            "duration_seconds": round(duration, 2),
            "total_frames": frame_count,
            "fps": fps,
            "avg_vehicles_per_sample": round(avg_vehicles, 2),
            "peak_vehicles": peak_vehicles,
            "vehicle_class_summary": all_vehicle_classes,
            "features": features[:20],  # Limit for output
            "processing_time_seconds": round(processing_time, 2),
            "timestamp": str(datetime.now()),
        }

        # Save result
        self._save_result(result)
        logger.info(
            f"✅ Completed: {video_path.name} | Avg vehicles: {avg_vehicles:.2f} | Time: {processing_time:.2f}s"
        )

        return result

    def _detect_vehicles(self, frame: np.ndarray) -> Tuple[int, Dict[str, int]]:
        """
        Detect vehicles in a frame using YOLO

        Args:
            frame: Input image frame

        Returns:
            Tuple of (vehicle_count, class_counts_dict)
        """
        results = self.model(frame, conf=YOLO_CONFIDENCE_THRESHOLD, verbose=False)

        vehicle_count = 0
        class_counts = {}

        for result in results:
            if result.boxes:
                for box in result.boxes:
                    class_id = int(box.cls[0])
                    class_name = VEHICLE_CLASSES.get(class_id, f"class_{class_id}")

                    # Count only vehicle classes (cars, trucks, buses, motorcycles)
                    if class_id in VEHICLE_CLASSES:
                        vehicle_count += 1
                        class_counts[class_name] = class_counts.get(class_name, 0) + 1

        return vehicle_count, class_counts

    def _get_density_level(self, vehicle_count: int) -> str:
        """Categorize traffic density"""
        if vehicle_count > 20:
            return "high"
        elif vehicle_count > 10:
            return "medium"
        else:
            return "low"

    def _save_sample_frame(
        self, frame: np.ndarray, video_path: Path, frame_number: int
    ):
        """Save a sample frame from the video"""
        frame_path = (
            SAMPLE_FRAMES_DIR / f"frame_{video_path.stem}_{frame_number}.jpg"
        )
        cv2.imwrite(str(frame_path), frame)

    def _save_result(self, result: Dict):
        """Save processing result to JSON"""
        output_file = OUTPUT_RESULTS_DIR / f"result_{result['video_name']}.json"
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        logger.info(f"Result saved to {output_file}")

    def process_batch(self, video_dir: Path) -> List[Dict]:
        """
        Process all videos in a directory

        Args:
            video_dir: Directory containing video files

        Returns:
            List of processing results
        """
        video_dir = Path(video_dir)
        if not video_dir.exists():
            logger.warning(f"Video directory not found: {video_dir}")
            return []

        video_files = [
            f
            for f in video_dir.iterdir()
            if f.suffix.lower() in [".mp4", ".avi", ".mov", ".mkv"]
        ]

        if not video_files:
            logger.info(f"No video files found in {video_dir}")
            return []

        logger.info(f"Found {len(video_files)} video(s) to process")

        results = []
        for video_file in video_files:
            result = self.process_video(str(video_file))
            if result:
                results.append(result)

        return results

"""
Traffic Sentinel — Detection Pydantic Models
Low-level schemas for YOLO frame-level outputs.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class DetectionBox(BaseModel):
    """Single bounding-box prediction from YOLO."""

    class_id: int = Field(..., description="COCO class ID (e.g. 2=car, 3=motorcycle)")
    class_name: str = Field(..., description="Human-readable class label")
    confidence: float = Field(..., ge=0.0, le=1.0)
    # xyxy format: [x1, y1, x2, y2] in pixel coordinates
    bbox: Tuple[float, float, float, float] = Field(
        ..., description="Bounding box [x1, y1, x2, y2]"
    )

    @property
    def area(self) -> float:
        x1, y1, x2, y2 = self.bbox
        return max(0.0, x2 - x1) * max(0.0, y2 - y1)


class FrameDetection(BaseModel):
    """All detections for a single video frame."""

    frame_index: int
    timestamp_seconds: float
    detections: List[DetectionBox] = Field(default_factory=list)

    @property
    def vehicle_count(self) -> int:
        return len(self.detections)

    @property
    def class_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for d in self.detections:
            counts[d.class_name] = counts.get(d.class_name, 0) + 1
        return counts

    @property
    def density_label(self) -> str:
        n = self.vehicle_count
        if n >= 20:
            return "high"
        if n >= 12:
            return "medium"
        return "low"


class VehicleCount(BaseModel):
    """Aggregated vehicle-count stats across a set of frames."""

    total_frames_sampled: int
    total_detections: int
    avg_vehicles_per_frame: float
    peak_vehicles: int
    high_density_frames: int
    class_totals: Dict[str, int] = Field(default_factory=dict)

    @classmethod
    def from_frame_detections(cls, frames: List[FrameDetection]) -> "VehicleCount":
        if not frames:
            return cls(
                total_frames_sampled=0,
                total_detections=0,
                avg_vehicles_per_frame=0.0,
                peak_vehicles=0,
                high_density_frames=0,
            )

        counts = [f.vehicle_count for f in frames]
        totals: Dict[str, int] = {}
        hdf = 0
        for f in frames:
            if f.density_label == "high":
                hdf += 1
            for cls_name, n in f.class_counts.items():
                totals[cls_name] = totals.get(cls_name, 0) + n

        return cls(
            total_frames_sampled=len(frames),
            total_detections=sum(counts),
            avg_vehicles_per_frame=sum(counts) / len(counts),
            peak_vehicles=max(counts),
            high_density_frames=hdf,
            class_totals=totals,
        )


class DetectionSession(BaseModel):
    """Full detection session for one video file."""

    session_id: str
    video_path: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    frames: List[FrameDetection] = Field(default_factory=list)
    summary: Optional[VehicleCount] = None

    def finalise(self) -> None:
        self.completed_at = datetime.utcnow()
        self.summary = VehicleCount.from_frame_detections(self.frames)

    @property
    def duration_seconds(self) -> float:
        if self.completed_at and self.started_at:
            return (self.completed_at - self.started_at).total_seconds()
        return 0.0
"""
Traffic Sentinel - Pydantic Models
Data validation and serialization schemas
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    """Risk severity levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class VehicleFeature(BaseModel):
    """Vehicle detection feature from a frame"""
    frame: int
    timestamp: str
    vehicle_count: int
    vehicle_classes: Optional[Dict[str, int]] = Field(default_factory=dict)
    density: str = Field(description="low, medium, or high")


class VideoProcessingResult(BaseModel):
    """Result from processing a single video"""
    video_name: str
    duration_seconds: float
    total_frames: int
    avg_vehicles_per_sample: float
    peak_vehicles: Optional[int] = None
    features: List[VehicleFeature]
    processing_time_seconds: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class RiskPrediction(BaseModel):
    """Risk prediction for a video/location"""
    video: str
    risk_level: RiskLevel
    risk_score: int = Field(ge=0, le=100)
    location: str
    timestamp: str
    recommendation: str
    factors: Optional[Dict[str, str]] = None


class PipelineOutput(BaseModel):
    """Final output from the complete pipeline"""
    pipeline_run_time: str
    total_videos_processed: int
    predictions: List[RiskPrediction]
    summary_stats: Optional[Dict[str, any]] = None


class ProcessingStatus(BaseModel):
    """Status of video processing"""
    status: str = Field(description="pending, processing, completed, failed")
    progress: int = Field(ge=0, le=100, description="Percentage complete")
    message: str
    video_name: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class HealthCheck(BaseModel):
    """API health status"""
    status: str
    version: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

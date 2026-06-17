"""
Traffic Sentinel — Risk Prediction Module
Spatio-temporal accident risk scoring for Uganda road junctions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import (
    DEFAULT_LOCATION,
    HIGH_RISK_HOUR_BONUS,
    HIGH_TRAFFIC_THRESHOLD,
    MEDIUM_TRAFFIC_THRESHOLD,
    OUTPUT_RESULTS_DIR,
    settings,
)

logger = logging.getLogger("traffic_sentinel.risk_predictor")

# Risk level thresholds (score → label)
_RISK_THRESHOLDS: List[Tuple[int, str]] = [
    (85, "CRITICAL"),
    (65, "HIGH"),
    (40, "MEDIUM"),
    (0,  "LOW"),
]

_RECOMMENDATIONS: Dict[str, str] = {
    "CRITICAL": "🚨 URGENT — Deploy additional traffic police immediately. Consider temporary junction closure.",
    "HIGH":     "⚠️ HIGH RISK — Increase patrol frequency. Erect additional signage and speed calming measures.",
    "MEDIUM":   "⚡ MODERATE — Monitor closely. Standard patrol recommended during peak hours.",
    "LOW":      "✅ NORMAL — Routine surveillance sufficient. No immediate action required.",
}


class RiskPredictor:
    """Rule-based risk scoring from YOLO-derived traffic features."""

    def __init__(self) -> None:
        logger.info("RiskPredictor initialised")

    # ── Public API ────────────────────────────────────────────────────────
    def predict_risk(
        self,
        video_result: Dict,
        location: Optional[str] = None,
        analysis_time: Optional[datetime] = None,
    ) -> Optional[Dict]:
        """
        Score accident risk for a single processed video.

        Args:
            video_result: Output dict from VideoProcessor.process_video().
            location: Human-readable junction name (overrides default).
            analysis_time: Override current time for testing / batch replay.

        Returns:
            Risk prediction dict, or None if input is invalid.
        """
        if not video_result:
            return None

        now = analysis_time or datetime.now()
        location = location or DEFAULT_LOCATION

        avg_vehicles: float = video_result.get("avg_vehicles_per_sample", 0)
        peak_vehicles: int = video_result.get("peak_vehicles", 0)
        high_density_frames: int = video_result.get("high_density_frames", 0)
        duration: float = video_result.get("duration_seconds", 0)

        # Component scores (0–100 each, weighted sum capped at 100)
        density_score = self._score_density(avg_vehicles, peak_vehicles)
        time_score = self._score_time(now)
        congestion_score = self._score_congestion(high_density_frames, duration)

        # Weighted aggregate
        raw_score = (
            density_score   * 0.55
            + time_score    * 0.25
            + congestion_score * 0.20
        )
        final_score = min(100, max(0, round(raw_score)))
        risk_level = self._score_to_level(final_score)

        return {
            "video": video_result.get("video_name", "unknown"),
            "location": location,
            "risk_level": risk_level,
            "risk_score": final_score,
            "timestamp": now.isoformat(),
            "recommendation": _RECOMMENDATIONS[risk_level],
            "factors": {
                "avg_vehicles_per_frame": round(avg_vehicles, 1),
                "peak_vehicles": peak_vehicles,
                "high_density_frames": high_density_frames,
                "time_period": self._time_label(now),
                "video_duration_seconds": duration,
            },
            "component_scores": {
                "traffic_density": round(density_score),
                "time_of_day": round(time_score),
                "congestion_events": round(congestion_score),
            },
        }

    def batch_predict(
        self,
        video_results: List[Dict],
        analysis_time: Optional[datetime] = None,
    ) -> List[Dict]:
        """Score risk for a list of video results."""
        predictions = []
        for result in video_results:
            pred = self.predict_risk(result, analysis_time=analysis_time)
            if pred:
                predictions.append(pred)
        logger.info("Generated %d risk prediction(s)", len(predictions))
        return predictions

    def generate_summary(self, predictions: List[Dict]) -> Dict:
        """Aggregate statistics across all predictions."""
        if not predictions:
            return {}

        scores = [p["risk_score"] for p in predictions]
        levels = [p["risk_level"] for p in predictions]
        highest = max(predictions, key=lambda p: p["risk_score"])

        return {
            "total_predictions": len(predictions),
            "average_risk_score": round(sum(scores) / len(scores), 1),
            "max_risk_score": max(scores),
            "min_risk_score": min(scores),
            "critical_areas": levels.count("CRITICAL"),
            "high_risk_areas": levels.count("HIGH"),
            "medium_risk_areas": levels.count("MEDIUM"),
            "low_risk_areas": levels.count("LOW"),
            "highest_risk_location": {
                "location": highest["location"],
                "video": highest["video"],
                "risk_score": highest["risk_score"],
                "risk_level": highest["risk_level"],
            },
            "generated_at": datetime.now().isoformat(),
        }

    # ── Scoring components ────────────────────────────────────────────────
    @staticmethod
    def _score_density(avg_vehicles: float, peak_vehicles: int) -> float:
        """
        Traffic density → 0–100.
        Uganda context: heavy boda-boda and matatu mix elevates risk faster than
        equivalent pure-car traffic.
        """
        if peak_vehicles >= HIGH_TRAFFIC_THRESHOLD and avg_vehicles >= 18:
            return 90.0
        if peak_vehicles >= HIGH_TRAFFIC_THRESHOLD:
            return 78.0
        if avg_vehicles >= MEDIUM_TRAFFIC_THRESHOLD:
            return 60.0
        if avg_vehicles >= 6:
            return 38.0
        return 20.0

    @staticmethod
    def _score_time(now: datetime) -> float:
        """
        Time-of-day risk → 0–100.
        Kampala peak risk: evening commute (17–21) and overnight (21–06).
        """
        h = now.hour
        if 17 <= h < 21:   # Evening rush
            return 85.0
        if h >= 21 or h < 6:  # Night
            return 75.0
        if 6 <= h < 8:     # Morning rush
            return 55.0
        return 30.0         # Daytime

    @staticmethod
    def _score_congestion(high_density_frames: int, duration_seconds: float) -> float:
        """
        Sustained congestion events → 0–100.
        Penalises junctions with frequent high-density spikes.
        """
        if duration_seconds <= 0:
            return 0.0
        # Normalise by video length (assume one sample per 30 frames ≈ 1 s)
        rate = high_density_frames / max(1, duration_seconds / 30)
        if rate >= 0.5:
            return 80.0
        if rate >= 0.25:
            return 55.0
        if rate >= 0.1:
            return 35.0
        return 15.0

    # ── Helpers ───────────────────────────────────────────────────────────
    @staticmethod
    def _score_to_level(score: int) -> str:
        for threshold, label in _RISK_THRESHOLDS:
            if score >= threshold:
                return label
        return "LOW"

    @staticmethod
    def _time_label(now: datetime) -> str:
        h = now.hour
        if 17 <= h < 21:
            return "Evening peak (17:00–21:00)"
        if h >= 21 or h < 6:
            return "Night hours (21:00–06:00) — HIGH RISK"
        if 6 <= h < 8:
            return "Morning rush (06:00–08:00)"
        return "Daytime (08:00–17:00)"
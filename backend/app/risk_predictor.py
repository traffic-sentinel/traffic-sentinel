"""
Traffic Sentinel - Risk Prediction Module
Spatio-temporal analysis for accident hotspot prediction
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

from .config import (
    HIGH_TRAFFIC_THRESHOLD,
    MEDIUM_TRAFFIC_THRESHOLD,
    HIGH_RISK_HOURS,
    HIGH_RISK_HOUR_BONUS,
    DEFAULT_LOCATION,
    OUTPUT_RESULTS_DIR,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskPredictor:
    """Predict traffic accident risk based on video features"""

    def __init__(self):
        """Initialize risk predictor"""
        self.base_score = 30
        logger.info("Risk predictor initialized")

    def predict_risk(self, video_result: Dict, location: str = None) -> Dict:
        """
        Calculate risk prediction from video analysis

        Args:
            video_result: Result from video processing
            location: Geographic location name

        Returns:
            Risk prediction dictionary
        """
        if not video_result:
            return None

        location = location or DEFAULT_LOCATION
        avg_vehicles = video_result.get("avg_vehicles_per_sample", 0)
        peak_vehicles = video_result.get("peak_vehicles", 0)

        # Calculate base risk from traffic density
        risk_score, risk_level = self._calculate_traffic_risk(
            avg_vehicles, peak_vehicles
        )

        # Add time-based risk factor
        time_bonus = self._calculate_time_bonus()
        risk_score = min(100, risk_score + time_bonus)

        # Adjust risk level if score changed
        risk_level = self._get_risk_level(risk_score)

        # Generate recommendation
        recommendation = self._get_recommendation(risk_score, risk_level)

        # Create factors breakdown
        factors = {
            "traffic_density": f"Avg {avg_vehicles:.1f} vehicles",
            "peak_congestion": f"Max {peak_vehicles} vehicles",
            "time_of_day": self._get_time_description(),
            "video_duration": f"{video_result.get('duration_seconds', 0)}s",
        }

        return {
            "video": video_result["video_name"],
            "risk_level": risk_level,
            "risk_score": risk_score,
            "location": location,
            "timestamp": str(datetime.now()),
            "recommendation": recommendation,
            "factors": factors,
        }

    def _calculate_traffic_risk(self, avg_vehicles: float, peak_vehicles: int) -> tuple:
        """
        Calculate risk based on traffic metrics

        Returns:
            Tuple of (risk_score, risk_level)
        """
        # Uganda context: High vehicle density correlates with higher accident risk
        if peak_vehicles > HIGH_TRAFFIC_THRESHOLD:
            if avg_vehicles > 18:
                score = 85
                level = "CRITICAL"
            else:
                score = 75
                level = "HIGH"
        elif avg_vehicles > MEDIUM_TRAFFIC_THRESHOLD:
            score = 60
            level = "MEDIUM"
        else:
            score = 35
            level = "LOW"

        return score, level

    def _calculate_time_bonus(self) -> int:
        """
        Add risk points based on time of day

        Uganda context: 5 PM to 7 AM sees higher accident rates
        """
        hour = datetime.now().hour

        # Peak risk hours: evening rush (17-21) and night (21-7)
        if hour >= HIGH_RISK_HOURS[0] or hour < HIGH_RISK_HOURS[1]:
            return HIGH_RISK_HOUR_BONUS
        # Morning rush (6-8)
        elif 6 <= hour < 8:
            return 8
        else:
            return 0

    def _get_risk_level(self, score: int) -> str:
        """Map risk score to risk level"""
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 40:
            return "MEDIUM"
        else:
            return "LOW"

    def _get_recommendation(self, score: int, risk_level: str) -> str:
        """Generate actionable recommendation"""
        recommendations = {
            "CRITICAL": "🚨 URGENT: Deploy additional patrols immediately",
            "HIGH": "⚠️ Increase police presence and traffic enforcement",
            "MEDIUM": "⚡ Monitor situation, standard patrols recommended",
            "LOW": "✓ Normal monitoring sufficient",
        }
        return recommendations.get(risk_level, "No specific recommendation")

    def _get_time_description(self) -> str:
        """Describe current time period"""
        hour = datetime.now().hour
        if 17 <= hour < 21:
            return "Evening peak (17:00-21:00)"
        elif 21 <= hour or hour < 7:
            return "Night hours (21:00-07:00) - HIGH RISK"
        elif 6 <= hour < 8:
            return "Morning rush (06:00-08:00)"
        else:
            return "Daytime hours"

    def batch_predict(self, video_results: List[Dict]) -> List[Dict]:
        """
        Predict risk for multiple video results

        Args:
            video_results: List of video processing results

        Returns:
            List of risk predictions
        """
        predictions = []
        for result in video_results:
            prediction = self.predict_risk(result)
            if prediction:
                predictions.append(prediction)

        return predictions

    def generate_summary(self, predictions: List[Dict]) -> Dict:
        """
        Generate summary statistics from predictions

        Args:
            predictions: List of risk predictions

        Returns:
            Summary statistics
        """
        if not predictions:
            return {}

        risk_levels = [p["risk_level"] for p in predictions]
        scores = [p["risk_score"] for p in predictions]

        critical_count = risk_levels.count("CRITICAL")
        high_count = risk_levels.count("HIGH")
        medium_count = risk_levels.count("MEDIUM")
        low_count = risk_levels.count("LOW")

        return {
            "total_predictions": len(predictions),
            "critical_areas": critical_count,
            "high_risk_areas": high_count,
            "medium_risk_areas": medium_count,
            "low_risk_areas": low_count,
            "average_risk_score": round(sum(scores) / len(scores), 2),
            "max_risk_score": max(scores),
            "min_risk_score": min(scores),
            "highest_risk_location": max(predictions, key=lambda x: x["risk_score"])
            if predictions
            else None,
        }

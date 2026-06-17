"""
Traffic Sentinel — Basic Test Suite
Run with: pytest tests/ -v
"""

import json
import sys
from pathlib import Path

import pytest

# Make backend importable from project root
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Unit tests: RiskPredictor ────────────────────────────────────────────────
class TestRiskPredictor:
    @pytest.fixture
    def predictor(self):
        from backend.app.risk_predictor import RiskPredictor
        return RiskPredictor()

    def _make_result(self, avg=15, peak=22, hdf=5, duration=60):
        return {
            "video_name": "test_clip.mp4",
            "avg_vehicles_per_sample": avg,
            "peak_vehicles": peak,
            "high_density_frames": hdf,
            "duration_seconds": duration,
        }

    def test_returns_dict(self, predictor):
        result = predictor.predict_risk(self._make_result())
        assert isinstance(result, dict)

    def test_required_keys(self, predictor):
        result = predictor.predict_risk(self._make_result())
        for key in ("risk_level", "risk_score", "recommendation", "factors", "timestamp"):
            assert key in result, f"Missing key: {key}"

    def test_score_in_range(self, predictor):
        result = predictor.predict_risk(self._make_result())
        assert 0 <= result["risk_score"] <= 100

    def test_risk_level_valid(self, predictor):
        result = predictor.predict_risk(self._make_result())
        assert result["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_high_traffic_yields_high_risk(self, predictor):
        result = predictor.predict_risk(self._make_result(avg=20, peak=30, hdf=20))
        assert result["risk_score"] >= 65

    def test_low_traffic_yields_low_risk(self, predictor):
        from datetime import datetime
        # Force analysis at a low-risk time (10 AM)
        safe_time = datetime.now().replace(hour=10, minute=0)
        result = predictor.predict_risk(
            self._make_result(avg=3, peak=5, hdf=0),
            analysis_time=safe_time,
        )
        assert result["risk_score"] < 65

    def test_none_input_returns_none(self, predictor):
        assert predictor.predict_risk(None) is None
        assert predictor.predict_risk({}) is None

    def test_batch_predict(self, predictor):
        results = [self._make_result(avg=i * 3) for i in range(1, 5)]
        predictions = predictor.batch_predict(results)
        assert len(predictions) == 4

    def test_summary_structure(self, predictor):
        results = [self._make_result(avg=5), self._make_result(avg=20, peak=30)]
        preds = predictor.batch_predict(results)
        summary = predictor.generate_summary(preds)
        for key in ("total_predictions", "average_risk_score", "max_risk_score", "highest_risk_location"):
            assert key in summary


# ── Unit tests: Config ───────────────────────────────────────────────────────
class TestConfig:
    def test_settings_importable(self):
        from backend.app.config import settings
        assert settings is not None

    def test_vehicle_classes_populated(self):
        from backend.app.config import settings
        assert len(settings.vehicle_classes) > 0

    def test_directories_created(self, tmp_path):
        """ensure_directories should not raise even on repeat calls"""
        from backend.app.config import settings
        settings.ensure_directories()  # idempotent


# ── API tests (requires httpx / FastAPI TestClient) ───────────────────────────
try:
    from fastapi.testclient import TestClient
    from backend.app.main import app

    @pytest.fixture(scope="module")
    def client():
        return TestClient(app)

    class TestAPI:
        def test_root(self, client):
            r = client.get("/")
            assert r.status_code == 200
            assert "name" in r.json()

        def test_health(self, client):
            r = client.get("/health")
            assert r.status_code == 200
            assert r.json()["status"] == "healthy"

        def test_status_idle(self, client):
            r = client.get("/api/status")
            assert r.status_code == 200
            d = r.json()
            assert "status" in d
            assert "progress" in d

        def test_list_videos_empty(self, client):
            r = client.get("/api/videos")
            assert r.status_code == 200
            assert "videos" in r.json()

        def test_results_empty(self, client):
            r = client.get("/api/results")
            assert r.status_code == 200
            assert r.json()["count"] >= 0

        def test_dashboard_structure(self, client):
            r = client.get("/api/dashboard")
            assert r.status_code == 200
            d = r.json()
            assert "total_videos" in d
            assert "overall_avg_vehicles" in d

        def test_clear_results(self, client):
            r = client.delete("/api/clear")
            assert r.status_code == 200
            assert r.json()["status"] == "cleared"

        def test_upload_invalid_type(self, client):
            r = client.post(
                "/api/upload",
                files={"file": ("test.txt", b"not a video", "text/plain")},
            )
            assert r.status_code == 415

        def test_predict_without_results_returns_404(self, client):
            # Clear first, then try to predict
            client.delete("/api/clear")
            r = client.post("/api/predict")
            assert r.status_code == 404

        def test_get_predictions_without_data_returns_404(self, client):
            client.delete("/api/clear")
            r = client.get("/api/predictions")
            assert r.status_code == 404

except ImportError:
    pass  # Skip API tests if httpx/FastAPI TestClient unavailable
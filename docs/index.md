# Traffic Sentinel — Documentation

> **AI-powered road safety intelligence for Uganda's urban junctions**



## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup & Installation](#setup--installation)
4. [API Reference](#api-reference)
5. [Configuration](#configuration)
6. [Data Pipeline](#data-pipeline)
7. [Risk Scoring Model](#risk-scoring-model)
8. [Deployment](#deployment)
9. [Contributing](#contributing)



## Overview

Traffic Sentinel is a data-driven traffic intelligence system built for Uganda's urban mobility challenges.
It uses **computer vision (YOLOv8)** and **spatio-temporal ML** to:

- Detect and count vehicles in traffic video footage
- Classify traffic density per junction per time window
- Score accident risk on a 0–100 scale with four severity labels (`LOW / MEDIUM / HIGH / CRITICAL`)
- Surface actionable insights through a web dashboard




## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend                           │
│        HTML / CSS / Vanilla JS dashboard                │
└─────────────────────┬───────────────────────────────────┘
                      │ REST (JSON)
┌─────────────────────▼───────────────────────────────────┐
│                  FastAPI Backend                         │
│  api/routes.py  ←→  services/  ←→  core VideoProcessor │
│  api/health.py                      RiskPredictor       │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   YOLOv8n        data/raw_csvs   data/output_results
 (ultralytics)    (accident CSV)    (JSON results)
```

### Key Modules

| Module | Role |
|---|---|
| `backend/app/main.py` | FastAPI app factory, middleware, global routes |
| `backend/app/api/routes.py` | Business-logic route handlers (`/api/*`) |
| `backend/app/api/health.py` | `/health` and `/ready` probes |
| `backend/app/services/detection_service.py` | YOLO session management |
| `backend/app/services/video_processor.py` | Service wrapper for batch video processing |
| `backend/app/services/analytics_service.py` | Dashboard aggregation and hotspot ranking |
| `backend/app/video_processor.py` | Core OpenCV + YOLO frame pipeline |
| `backend/app/risk_predictor.py` | Rule-based spatio-temporal risk scorer |
| `backend/app/config.py` | Centralised settings (env-driven) |
| `backend/app/core/logger.py` | Shared logger factory |
| `backend/app/models/detection_models.py` | Pydantic schemas for YOLO outputs |
| `backend/app/utils/video_utils.py` | OpenCV helper functions |
| `backend/app/utils/helpers.py` | General-purpose utilities |



## Setup & Installation

### Prerequisites

- Python 3.10+
- `pip` or `uv`
- (Optional) CUDA-capable GPU for faster YOLO inference

### Quick start

```bash
git clone https://github.com/traffic-sentinel/traffic-sentinel.git
cd traffic-sentinel

# Install dependencies
pip install -r requirements.txt

# Start the API
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Or use the one-command script:

```bash
chmod +x run.sh && ./run.sh
```

### Docker

```bash
docker build -t traffic-sentinel ./backend
docker run -p 8000:8000 traffic-sentinel
```



## API Reference

Base URL: `http://localhost:8000`

### Health

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe (model + disk checks) |

### Videos

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/upload` | Upload a video file (`.mp4`, `.avi`, `.mov`, `.mkv`) |
| GET | `/api/videos` | List all uploaded videos |

### Processing

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/process` | Queue batch processing of all uploaded videos |
| GET | `/api/results` | Retrieve stored processing results |
| DELETE | `/api/results` | Clear all stored results |

### Prediction & Analytics

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/predict` | Run risk prediction on stored results |
| GET | `/api/dashboard` | Dashboard summary + trend + hotspots |
| GET | `/api/hotspots?top_n=5` | Ranked accident risk hotspots |

Interactive docs: `http://localhost:8000/docs`



## Configuration

All settings are driven by environment variables (or a `.env` file at project root).

| Variable | Default | Description |
|---|---|---|
| `API_HOST` | `0.0.0.0` | Bind address |
| `API_PORT` | `8000` | Listen port |
| `YOLO_MODEL` | `yolov8n.pt` | YOLO weights file |
| `YOLO_CONFIDENCE` | `0.5` | Detection confidence threshold |
| `VIDEO_SAMPLE_INTERVAL` | `30` | Sample every N frames |
| `HIGH_TRAFFIC_THRESHOLD` | `20` | Vehicles/frame → high density |
| `MEDIUM_TRAFFIC_THRESHOLD` | `12` | Vehicles/frame → medium density |
| `HIGH_RISK_HOUR_BONUS` | `15` | Extra risk score points outside safe hours |
| `LOG_LEVEL` | `INFO` | Python logging level |



## Data Pipeline

```
Input video (MP4/AVI)
      │
      ▼
VideoProcessor.process_video()
      │   Sample every VIDEO_SAMPLE_INTERVAL frames
      │   Run YOLO inference per frame
      │   Extract vehicle counts + class breakdown
      ▼
Result JSON  →  data/output_results/<stem>_result.json
      │
      ▼
RiskPredictor.predict_risk()
      │   Score = f(avg_vehicles, peak, hdf, time_of_day)
      │   Label = CRITICAL | HIGH | MEDIUM | LOW
      ▼
Dashboard / API response
```



## Risk Scoring Model

The risk scorer is a transparent, interpretable rule-based model (no black box) suitable for government demonstrations.

**Score components (all clamped to 0–100):**

| Factor | Contribution |
|---|---|
| Average vehicles / frame | Up to +40 pts |
| Peak vehicle count | Up to +20 pts |
| High-density frames count | Up to +25 pts |
| Peak-hour / night bonus | +15 to +20 pts |

**Labels:**

| Score | Label |
|---|---|
| ≥ 85 | 🔴 CRITICAL |
| 65 – 84 | 🟠 HIGH |
| 40 – 64 | 🟡 MEDIUM |
| < 40 | 🟢 LOW |



## Deployment

### Production checklist

- [ ] Set `API_RELOAD=false` and `API_WORKERS=4` (or match CPU count)
- [ ] Restrict `CORS_ORIGINS` to your frontend domain
- [ ] Mount persistent volumes for `data/input_video` and `data/output_results`
- [ ] Enable `LOG_TO_FILE=true` and configure log rotation
- [ ] Use `YOLO_DEVICE=0` if a GPU is available

### Systemd unit (example)

```ini
[Unit]
Description=Traffic Sentinel API
After=network.target

[Service]
WorkingDirectory=/opt/traffic-sentinel
ExecStart=/opt/venv/bin/uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
EnvironmentFile=/opt/traffic-sentinel/.env

[Install]
WantedBy=multi-user.target
```



## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on submitting issues and pull requests.
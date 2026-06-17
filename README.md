# 🚦 Traffic Sentinel

> **AI-powered road safety intelligence for Uganda's urban junctions**  
> Computer Vision · YOLO · FastAPI · Streamlit · Uganda Ministry of ICT Showcase · June 2026

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688?logo=fastapi)
![YOLO](https://img.shields.io/badge/YOLOv8-Ultralytics-EE4C2C)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?logo=streamlit)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Problem

Uganda records over **20,000 road traffic accidents per year**, with Kampala accounting for a disproportionate share during evening peak hours. Traffic management is largely manual, reactive, and under-resourced. Traffic Sentinel provides a data-driven layer: it analyses local traffic footage, quantifies congestion risk per junction, and produces actionable intelligence for deployment decisions.

---

## What it does

| Capability | Detail |
|---|---|
| **Vehicle detection** | YOLOv8n detects cars, trucks, buses, and motorcycles (boda-bodas) frame by frame |
| **Risk scoring** | Weighted model combining traffic density, time-of-day, and congestion event frequency |
| **Hotspot mapping** | Pre-loaded Uganda RTA dataset + model outputs overlaid on junction coordinates |
| **REST API** | FastAPI backend — upload videos, trigger processing, poll status, download predictions |
| **Dashboard** | Streamlit + Plotly dashboard with real API integration, hourly risk chart, export |
| **Static frontend** | Zero-dependency HTML/JS dashboard (served by any static host or FastAPI) |

---

## Architecture

```
data/input_video/          ← Drop .mp4 / .avi / .mov files here
        │
        ▼
┌─────────────────────┐
│  VideoProcessor     │  OpenCV frame sampling → YOLOv8n detection
│  (video_processor)  │  → result_<name>.json per video
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│  RiskPredictor      │  Density score (55%) + Time score (25%) + Congestion score (20%)
│  (risk_predictor)   │  → final_risk_predictions.json
└─────────────────────┘
        │
        ▼
┌──────────────────────────────────────┐
│  FastAPI (main.py)                   │
│  GET  /health          POST /api/process   │
│  GET  /api/status      POST /api/predict   │
│  GET  /api/dashboard   POST /api/pipeline  │
│  GET  /api/results     GET  /api/videos    │
│  GET  /api/predictions POST /api/upload    │
└──────────────────────────────────────┘
        │
        ▼
┌──────────────────┐   ┌────────────────────────┐
│  Streamlit (app) │   │  HTML/JS frontend       │
│  Port 8501       │   │  frontend/index.html    │
└──────────────────┘   └────────────────────────┘
```

---

## Quick Start

### Option A — Local Python (recommended for development)

```bash
# 1. Clone
git clone https://github.com/your-org/traffic-sentinel.git
cd traffic-sentinel

# 2. Install deps (use minimal version to save data)
pip install -r requirements-minimal.txt

# 3. Copy env template
cp .env.example .env

# 4. Add sample videos
cp /path/to/your/traffic.mp4 data/input_video/

# 5. Start backend
uvicorn backend.app.main:app --reload --port 8000

# 6. Start dashboard (new terminal)
streamlit run backend/app/app.py --server.port 8501
```

Open:
- **Dashboard** → http://localhost:8501
- **API docs** → http://localhost:8000/docs
- **Frontend** → open `frontend/index.html` in a browser

### Option B — Docker (recommended for showcase/demo)

```bash
cp .env.example .env
./run.sh          # choose option 1
```

Then:
- Dashboard → http://localhost:8501
- API → http://localhost:8000/docs

### Option C — One-command pipeline (CLI)

```bash
python scripts/run_pipeline.py
# Outputs → data/output_results/final_risk_predictions.json
```

---

## Environment Variables

Copy `.env.example` to `.env` and edit as needed:

```env
API_HOST=0.0.0.0
API_PORT=8000
YOLO_MODEL=yolov8n.pt          # yolov8s.pt for better accuracy
YOLO_CONFIDENCE=0.5
YOLO_DEVICE=cpu                # "0" to use GPU
VIDEO_SAMPLE_INTERVAL=30       # sample every N frames
HIGH_TRAFFIC_THRESHOLD=20      # vehicles/frame → HIGH density
LOG_LEVEL=INFO
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | System health check |
| GET | `/api/status` | Current processing status + progress |
| POST | `/api/process` | Start video processing (background) |
| POST | `/api/upload` | Upload a new video file |
| GET | `/api/results` | All video processing results |
| POST | `/api/predict` | Generate risk predictions from results |
| GET | `/api/predictions` | Retrieve saved predictions |
| POST | `/api/pipeline` | Run full pipeline (process + predict) |
| GET | `/api/dashboard` | Aggregated KPIs for frontend |
| GET | `/api/videos` | List videos in input directory |
| GET | `/api/download/predictions` | Download predictions as JSON |
| DELETE | `/api/clear` | Reset all results (demo reset) |

Full interactive docs at `/docs` (Swagger) or `/redoc`.

---

## Risk Model

Risk is a weighted sum of three components:

| Component | Weight | Logic |
|---|---|---|
| Traffic density | 55% | Peak & avg vehicle count from YOLO |
| Time of day | 25% | Evening peak (17–21) and night (21–06) score higher |
| Congestion frequency | 20% | Fraction of frames exceeding HIGH_TRAFFIC_THRESHOLD |

Output: **score 0–100** → mapped to `LOW / MEDIUM / HIGH / CRITICAL`

---

## Project Structure

```
traffic-sentinel/
├── backend/app/
│   ├── main.py            ← FastAPI app + all endpoints
│   ├── config.py          ← Pydantic Settings (env / .env)
│   ├── video_processor.py ← YOLO vehicle detection pipeline
│   ├── risk_predictor.py  ← Risk scoring model
│   └── app.py             ← Streamlit dashboard
├── frontend/
│   ├── index.html         ← Static dashboard (Chart.js)
│   └── styles.css
├── scripts/
│   ├── run_pipeline.py    ← CLI pipeline runner
│   └── test_video.py      ← Standalone video test
├── data/
│   ├── input_video/       ← Drop videos here
│   ├── output_results/    ← JSON outputs (gitignored)
│   └── raw_csvs/          ← Uganda RTA dataset
├── configs/config.yaml    ← YAML config (optional override)
├── tests/test_basic.py    ← Basic pytest suite
├── .env.example
├── requirements.txt
├── requirements-minimal.txt
└── run.sh
```

---

## Performance

| Metric | Value |
|---|---|
| Detection model | YOLOv8n (3.2M params, ~6ms/frame on CPU) |
| Frame sampling | Every 30 frames (1 s @ 30 fps) — balances speed vs accuracy |
| Throughput | ~2–4 min of footage per minute of processing (CPU) |
| Fallback mode | Simulated detection if `ultralytics` not installed |

---

## Roadmap

- [ ] Real-time RTSP stream support (traffic cameras)
- [ ] GPS-tagged incident database integration
- [ ] SMS alert dispatch (Twilio / Africa's Talking)
- [ ] Multi-camera junction view
- [ ] Heatmap tile export for UNRA / KCCA GIS systems
- [ ] Containerised edge deployment on Raspberry Pi 4

---

## Government Impact

Traffic Sentinel directly supports Uganda's **National Road Safety Strategic Plan** and the Ministry of Works' mandate to reduce road fatalities by 50% by 2030. By surfacing junction-level risk in real time, it enables Uganda Police Traffic Directorate to pre-position resources before incidents occur — shifting from reactive to predictive enforcement.

---

## Built by

**Keith Ndiema Kissa** · Mbarara University of Science & Technology (MUST)  
Submitted to: **Ministry of ICT Government Systems Prototype Showcase — June 2026**

---

## License

MIT — see [LICENSE](LICENSE).
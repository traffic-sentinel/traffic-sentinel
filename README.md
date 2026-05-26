# Traffic Sentinel - AI Traffic Monitoring System

**An intelligent traffic monitoring and analytics system** built for Uganda's urban mobility challenges.

![Traffic Sentinel](https://via.placeholder.com/800x400?text=Traffic+Sentinel+Dashboard) <!-- Replace with actual screenshot later -->

## Problem Statement
Uganda faces increasing traffic congestion, road accidents, and inefficient traffic management in cities like Kampala. Traffic Sentinel uses **Computer Vision + AI** to automatically detect vehicles, analyze traffic flow, and identify violations in real-time.

## Key Features
- Vehicle detection and counting using YOLO
- Traffic density and congestion analysis
- Violation detection (speeding, wrong lane, etc.)
- Spatio-temporal hotspot analysis
- Web dashboard for visualization
- Video processing pipeline

## Tech Stack
- **Backend**: FastAPI (Python)
- **Computer Vision**: OpenCV + Ultralytics YOLO
- **Frontend**: HTML + JavaScript
- **Deployment**: Docker

## Quick Start (One Command)

```bash
# Clone and run
git clone https://github.com/traffic-sentinel/traffic-sentinel.git
cd traffic-sentinel
chmod +x run.sh
./run.sh
```

## Project Structure
```
traffic-sentinel/
├── backend/          # FastAPI application
├── frontend/         # Dashboard
├── scripts/          # Automation & testing
├── data/             # Input/output videos
├── models/           # Trained ML models
└── docs/             # Documentation
```

## Current MVP Status
- Basic video processing pipeline ready
- Vehicle detection service implemented
- Simple web dashboard
- Ready for extension with real-time analytics

## Government Impact
- Reduce road accidents through better enforcement
- Optimize traffic flow in Kampala and other cities
- Provide data-driven insights for urban planning
- Support digital transformation of transport sector

---

**Made for the Ministry of ICT & National Guidance - Government Systems Prototype Showcase (May/June 2026)**
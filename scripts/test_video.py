#!/usr/bin/env python3
"""
Traffic Sentinel — Video Processing Script
Processes Uganda traffic videos from data/input_video/ using YOLO.
Run from project root:
    python3 scripts/test_video.py
    python3 scripts/test_video.py --video data/input_video/clip.mp4
    python3 scripts/test_video.py --demo   # synthetic results (no video needed)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Allow imports from project root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── Paths ────────────────────────────────────────────────────────────────────
VIDEO_INPUT_DIR  = ROOT / "data" / "input_video"
OUTPUT_DIR       = ROOT / "data" / "output_results"
SAMPLE_FRAMES_DIR = ROOT / "data" / "sample_framing"
MODELS_DIR       = ROOT / "models"

for d in [OUTPUT_DIR, SAMPLE_FRAMES_DIR, MODELS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

SUPPORTED = {".mp4", ".avi", ".mov", ".mkv"}

# ── YOLO setup ───────────────────────────────────────────────────────────────
VEHICLE_CLASS_IDS = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
CONFIDENCE        = float(os.getenv("YOLO_CONFIDENCE", "0.5"))
YOLO_MODEL_NAME   = os.getenv("YOLO_MODEL", "yolov8n.pt")
SAMPLE_INTERVAL   = int(os.getenv("VIDEO_SAMPLE_INTERVAL", "30"))
FRAME_SAVE_EVERY  = int(os.getenv("VIDEO_FRAME_SAVE_INTERVAL", "90"))


def _load_yolo():
    """Load YOLO model, downloading weights if absent."""
    try:
        from ultralytics import YOLO  # type: ignore
        model_path = MODELS_DIR / YOLO_MODEL_NAME
        if not model_path.exists():
            print(f"  ⬇️  Downloading {YOLO_MODEL_NAME} …")
            model = YOLO(YOLO_MODEL_NAME)
        else:
            model = YOLO(str(model_path))
        print(f"  ✅ YOLO loaded: {YOLO_MODEL_NAME}")
        return model
    except ImportError:
        print("  ⚠️  ultralytics not installed — falling back to demo mode")
        return None


def process_video(video_path: Path, model=None) -> dict | None:
    """
    Process a single video file.
    If *model* is None, falls back to pixel-variance heuristic.
    Returns a result dict or None on failure.
    """
    try:
        import cv2
    except ImportError:
        print("  ❌ OpenCV not installed. Run: pip install opencv-python-headless")
        return None

    print(f"\n  📹 Processing: {video_path.name}")
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"  ❌ Cannot open video: {video_path}")
        return None

    fps         = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration    = frame_count / fps

    features      = []
    class_totals: dict[str, int] = {}
    frame_num     = 0
    t_start       = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_num += 1

        if frame_num % SAMPLE_INTERVAL != 0:
            continue

        # ── Detection ────────────────────────────────────────────────────────
        if model is not None:
            results = model(frame, conf=CONFIDENCE, verbose=False)
            vehicles = []
            for r in results:
                for i in range(len(r.boxes)):
                    cls_id = int(r.boxes.cls[i].item())
                    if cls_id in VEHICLE_CLASS_IDS:
                        name = VEHICLE_CLASS_IDS[cls_id]
                        vehicles.append(name)
                        class_totals[name] = class_totals.get(name, 0) + 1
            vehicle_count = len(vehicles)
            class_counts  = dict.fromkeys(set(vehicles), 0)
            for v in vehicles:
                class_counts[v] += 1
        else:
            # Heuristic fallback: pixel variance → proxy for activity level
            import numpy as np
            gray     = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            variance = float(np.var(gray))
            vehicle_count = min(30, int(variance / 400))
            class_counts  = {}

        density = (
            "high"   if vehicle_count >= 20 else
            "medium" if vehicle_count >= 12 else
            "low"
        )

        features.append({
            "frame":         frame_num,
            "timestamp_s":   round(frame_num / fps, 2),
            "vehicle_count": vehicle_count,
            "class_counts":  class_counts,
            "density":       density,
        })

        # ── Save sample frame ────────────────────────────────────────────────
        if frame_num % FRAME_SAVE_EVERY == 0:
            out_frame = SAMPLE_FRAMES_DIR / f"{video_path.stem}_f{frame_num:06d}.jpg"
            cv2.imwrite(str(out_frame), frame)

    cap.release()

    if not features:
        print("  ⚠️  No frames sampled — video may be too short")
        return None

    counts    = [f["vehicle_count"] for f in features]
    avg_count = sum(counts) / len(counts)
    peak      = max(counts)
    hdf       = sum(1 for f in features if f["density"] == "high")

    result = {
        "video_name":              video_path.name,
        "duration_seconds":        round(duration, 2),
        "total_frames":            frame_count,
        "frames_sampled":          len(features),
        "avg_vehicles_per_sample": round(avg_count, 2),
        "peak_vehicles":           peak,
        "high_density_frames":     hdf,
        "class_counts":            class_totals,
        "processing_time_s":       round(time.time() - t_start, 2),
        "timestamp":               datetime.utcnow().isoformat(),
        "features":                features,
    }

    out_file = OUTPUT_DIR / f"result_{video_path.stem}.json"
    with open(out_file, "w") as fh:
        json.dump(result, fh, indent=2, default=str)

    print(f"  ✅ Done | avg={avg_count:.1f} veh/frame | peak={peak} | hdf={hdf}")
    print(f"     → {out_file}")
    return result


def demo_result(name: str = "demo_clip.mp4") -> dict:
    """Generate a plausible synthetic result for demos without a real video."""
    import random
    random.seed(42)
    features = []
    for i in range(1, 31):
        vc = random.randint(4, 28)
        features.append({
            "frame":         i * 30,
            "timestamp_s":   round(i * 1.0, 2),
            "vehicle_count": vc,
            "class_counts":  {"car": vc // 2, "motorcycle": vc // 3},
            "density":       "high" if vc >= 20 else "medium" if vc >= 12 else "low",
        })
    counts = [f["vehicle_count"] for f in features]
    result = {
        "video_name":              name,
        "duration_seconds":        30.0,
        "total_frames":            900,
        "frames_sampled":          30,
        "avg_vehicles_per_sample": round(sum(counts) / len(counts), 2),
        "peak_vehicles":           max(counts),
        "high_density_frames":     sum(1 for f in features if f["density"] == "high"),
        "class_counts":            {"car": 120, "motorcycle": 80, "bus": 10, "truck": 5},
        "processing_time_s":       0.0,
        "timestamp":               datetime.utcnow().isoformat(),
        "features":                features,
        "_demo":                   True,
    }
    out_file = OUTPUT_DIR / f"result_{Path(name).stem}.json"
    with open(out_file, "w") as fh:
        json.dump(result, fh, indent=2)
    print(f"  🎭 Demo result written → {out_file}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Traffic Sentinel — Video Processor")
    parser.add_argument("--video",  type=Path, help="Process a single video file")
    parser.add_argument("--demo",   action="store_true", help="Generate synthetic demo results")
    parser.add_argument("--no-gpu", action="store_true", help="Force CPU inference")
    args = parser.parse_args()

    print("\n🚦 Traffic Sentinel — Video Processor")
    print("══════════════════════════════════════")

    if args.demo:
        print("\n🎭 Demo mode — generating synthetic results")
        demo_result("kampala_junction_demo.mp4")
        print("\n✅ Done. Check data/output_results/")
        return

    model = _load_yolo()

    if args.video:
        videos = [args.video]
    else:
        videos = [
            p for p in sorted(VIDEO_INPUT_DIR.iterdir())
            if p.is_file() and p.suffix.lower() in SUPPORTED
        ]

    if not videos:
        print(f"\n⚠️  No videos found in {VIDEO_INPUT_DIR}")
        print("    Add .mp4/.avi/.mov files or run with --demo")
        sys.exit(0)

    print(f"\n📂 Found {len(videos)} video(s)")
    all_results = []
    for vp in videos:
        r = process_video(vp, model=model)
        if r:
            all_results.append(r)

    summary = {
        "run_at":           datetime.utcnow().isoformat(),
        "videos_processed": len(all_results),
        "results":          all_results,
    }
    summary_file = OUTPUT_DIR / "processing_summary.json"
    with open(summary_file, "w") as fh:
        json.dump(summary, fh, indent=2, default=str)

    print(f"\n✅ Processing complete — {len(all_results)} video(s)")
    print(f"   Summary → {summary_file}")


if __name__ == "__main__":
    main()
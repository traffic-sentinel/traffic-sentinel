#!/usr/bin/env python3
"""
Traffic Sentinel — Full Pipeline Runner
Orchestrates: video processing → risk prediction → summary report.

Run from project root:
    python3 scripts/run_pipeline.py
    python3 scripts/run_pipeline.py --demo          # no video needed
    python3 scripts/run_pipeline.py --skip-video    # use existing results
    python3 scripts/run_pipeline.py --report pdf    # (future)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

OUTPUT_DIR = ROOT / "data" / "output_results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Colour helpers ────────────────────────────────────────────────────────────
RED    = "\033[0;31m"
GREEN  = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE   = "\033[0;34m"
CYAN   = "\033[0;36m"
BOLD   = "\033[1m"
NC     = "\033[0m"

def banner(text: str) -> None:
    print(f"\n{BLUE}{'═' * 55}{NC}")
    print(f"{BOLD}{BLUE}  {text}{NC}")
    print(f"{BLUE}{'═' * 55}{NC}")

def step(n: int, text: str) -> None:
    print(f"\n{CYAN}[Step {n}]{NC} {text}")

def ok(text: str) -> None:
    print(f"  {GREEN}✅{NC} {text}")

def warn(text: str) -> None:
    print(f"  {YELLOW}⚠️ {NC} {text}")

def err(text: str) -> None:
    print(f"  {RED}❌{NC} {text}", file=sys.stderr)


# ── Step 1: Video processing ─────────────────────────────────────────────────

def run_video_processing(demo: bool = False) -> list[dict]:
    """Process videos (or generate demo results) and return result list."""
    from scripts.test_video import main as tv_main, demo_result

    if demo:
        ok("Demo mode — generating synthetic video result")
        return [demo_result("kampala_junction_demo.mp4")]

    # Check for videos
    video_dir = ROOT / "data" / "input_video"
    videos = [
        p for p in sorted(video_dir.iterdir())
        if p.is_file() and p.suffix.lower() in {".mp4", ".avi", ".mov", ".mkv"}
    ] if video_dir.exists() else []

    if not videos:
        warn(f"No videos in {video_dir} — switching to demo mode")
        return [demo_result("kampala_junction_demo.mp4")]

    # Run the processor
    import importlib.util, subprocess
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "test_video.py")],
        check=True,
    )
    return load_results()


def load_results() -> list[dict]:
    """Load all result JSON files from output directory."""
    results = []
    for f in sorted(OUTPUT_DIR.glob("result_*.json")):
        try:
            with open(f) as fh:
                results.append(json.load(fh))
        except Exception as exc:
            warn(f"Could not read {f.name}: {exc}")
    return results


# ── Step 2: Risk prediction ───────────────────────────────────────────────────

def run_risk_prediction(results: list[dict]) -> list[dict]:
    """Run RiskPredictor over all video results."""
    try:
        from backend.app.risk_predictor import RiskPredictor
        predictor = RiskPredictor()
        predictions = predictor.batch_predict(results)
        ok(f"Risk prediction complete — {len(predictions)} predictions")
        return predictions
    except Exception as exc:
        warn(f"RiskPredictor unavailable ({exc}) — using fallback scoring")
        return [_fallback_risk(r) for r in results]


def _fallback_risk(result: dict) -> dict:
    """Minimal rule-based scorer used if the backend is not importable."""
    avg   = result.get("avg_vehicles_per_sample", 0)
    peak  = result.get("peak_vehicles", 0)
    hdf   = result.get("high_density_frames", 0)
    hour  = datetime.utcnow().hour

    score = 0
    score += 40 if avg >= 20 else 25 if avg >= 12 else 12 if avg >= 6 else 4
    score += 20 if peak >= 30 else 12 if peak >= 20 else 6 if peak >= 12 else 0
    score += min(25, hdf * 2)
    if hour < 6 or hour >= 22:
        score += 20
    elif hour < 8 or hour >= 17:
        score += 15
    score = max(0, min(100, score))

    level = (
        "CRITICAL" if score >= 85 else
        "HIGH"     if score >= 65 else
        "MEDIUM"   if score >= 40 else
        "LOW"
    )
    rec = {
        "CRITICAL": "🚨 Deploy additional traffic police immediately.",
        "HIGH":     "⚠️  Increase patrol frequency and add signage.",
        "MEDIUM":   "⚡ Monitor closely during peak hours.",
        "LOW":      "✅ Routine surveillance sufficient.",
    }[level]

    return {
        "video":          result.get("video_name", "unknown"),
        "location":       result.get("location", "Kampala Junction"),
        "risk_level":     level,
        "risk_score":     score,
        "recommendation": rec,
        "timestamp":      datetime.utcnow().isoformat(),
        "factors": {
            "avg_vehicles": str(round(avg, 1)),
            "peak_vehicles": str(peak),
            "high_density_frames": str(hdf),
        },
    }


# ── Step 3: Analytics summary ────────────────────────────────────────────────

def run_analytics(results: list[dict], predictions: list[dict]) -> dict:
    """Compute dashboard-level summary stats."""
    try:
        from backend.app.services.analytics_service import AnalyticsService
        svc = AnalyticsService()
        # Merge risk scores back into results for the analytics service
        merged = []
        pred_map = {p.get("video", ""): p for p in predictions}
        for r in results:
            m = {**r}
            p = pred_map.get(r.get("video_name", ""), {})
            m["risk_score"] = p.get("risk_score", 0)
            m["risk_level"] = p.get("risk_level", "LOW")
            m["location"]   = p.get("location", "Kampala Junction")
            merged.append(m)
        return svc.dashboard_summary(merged)
    except Exception as exc:
        warn(f"AnalyticsService unavailable ({exc}) — using basic summary")
        scores = [p.get("risk_score", 0) for p in predictions]
        return {
            "total_videos":           len(results),
            "overall_avg_risk_score": round(sum(scores) / len(scores), 1) if scores else 0,
            "max_risk_score":         max(scores, default=0),
        }


# ── Step 4: Save final output ────────────────────────────────────────────────

def save_final(results: list[dict], predictions: list[dict], summary: dict) -> Path:
    output = {
        "pipeline_run_time":     datetime.utcnow().isoformat(),
        "total_videos_processed": len(results),
        "predictions":           predictions,
        "summary":               summary,
    }
    out_file = OUTPUT_DIR / "final_risk_predictions.json"
    with open(out_file, "w") as fh:
        json.dump(output, fh, indent=2, default=str)
    return out_file


# ── Print report ─────────────────────────────────────────────────────────────

LEVEL_ICON = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}

def print_report(predictions: list[dict], summary: dict, out_file: Path) -> None:
    print(f"\n{BOLD}{'─' * 55}{NC}")
    print(f"{BOLD}  TRAFFIC SENTINEL — RISK REPORT{NC}")
    print(f"  Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"{BOLD}{'─' * 55}{NC}")

    for p in predictions:
        icon  = LEVEL_ICON.get(p.get("risk_level", "LOW"), "⬜")
        score = p.get("risk_score", 0)
        level = p.get("risk_level", "LOW")
        video = p.get("video", "unknown")
        loc   = p.get("location", "")
        rec   = p.get("recommendation", "")
        print(f"\n  {icon} {BOLD}{video}{NC}")
        if loc:
            print(f"     Location   : {loc}")
        print(f"     Risk       : {level} (score {score}/100)")
        print(f"     Action     : {rec}")

    print(f"\n{BOLD}{'─' * 55}{NC}")
    print(f"  Videos processed : {summary.get('total_videos', len(predictions))}")
    print(f"  Avg risk score   : {summary.get('overall_avg_risk_score', 'N/A')}")
    print(f"  Max risk score   : {summary.get('max_risk_score', 'N/A')}")
    print(f"\n  📁 Full output   → {out_file}")
    print(f"{BOLD}{'─' * 55}{NC}\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Traffic Sentinel — Pipeline Runner")
    parser.add_argument("--demo",       action="store_true", help="Run with synthetic demo data")
    parser.add_argument("--skip-video", action="store_true", help="Skip video processing, use existing results")
    args = parser.parse_args()

    banner("Traffic Sentinel — Pipeline Runner")
    t0 = time.time()

    # Step 1
    step(1, "Video processing")
    if args.skip_video:
        results = load_results()
        if not results:
            err("No existing results found. Run without --skip-video first.")
            sys.exit(1)
        ok(f"Loaded {len(results)} existing result(s)")
    else:
        results = run_video_processing(demo=args.demo)

    if not results:
        err("No results to process. Exiting.")
        sys.exit(1)

    # Step 2
    step(2, "Risk prediction")
    predictions = run_risk_prediction(results)

    # Step 3
    step(3, "Analytics summary")
    summary = run_analytics(results, predictions)
    ok("Summary computed")

    # Step 4
    step(4, "Saving final output")
    out_file = save_final(results, predictions, summary)
    ok(f"Saved → {out_file}")

    elapsed = round(time.time() - t0, 1)
    ok(f"Pipeline complete in {elapsed}s")

    print_report(predictions, summary, out_file)


if __name__ == "__main__":
    main()
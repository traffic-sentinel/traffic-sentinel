#!/usr/bin/env python3
"""
Traffic Sentinel - Main Pipeline Runner
Orchestrates video processing + risk prediction for Uganda traffic data.
"""

import os
import json
import pandas as pd
from datetime import datetime

# Import from existing scripts
from test_video import process_video  # Reuse the function we improved

# Paths
VIDEO_INPUT_DIR = "data/input_video"
OUTPUT_DIR = "data/output_results"
MODELS_DIR = "models"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)


def load_video_results():
    """Load processed video results from output folder."""
    results = []
    if os.path.exists(OUTPUT_DIR):
        for file in os.listdir(OUTPUT_DIR):
            if file.endswith('.json') and file.startswith('result_'):
                with open(os.path.join(OUTPUT_DIR, file), 'r') as f:
                    data = json.load(f)
                    results.append(data)
    return results


def calculate_risk_score(video_result):
    """Simple risk scoring based on video features (MVP version)."""
    avg_vehicles = video_result.get('avg_vehicles_per_sample', 0)
    
    # Uganda context: High boda/matatu density = higher risk
    if avg_vehicles > 20:
        risk_level = "HIGH"
        score = 85
    elif avg_vehicles > 12:
        risk_level = "MEDIUM"
        score = 60
    else:
        risk_level = "LOW"
        score = 30
    
    # Add time-based factor (placeholder - improve later)
    hour = datetime.now().hour
    if hour >= 17 or hour <= 7:  # Evening/Night risk in Kampala
        score = min(95, score + 15)
    
    return {
        "risk_level": risk_level,
        "risk_score": score,
        "location": "Kampala Sample Junction",  # Update with real location later
        "timestamp": str(datetime.now()),
        "recommendation": "Increase patrols" if score > 70 else "Normal monitoring"
    }


def run_full_pipeline():
    """Run the complete MVP pipeline."""
    print("🚦 Starting Traffic Sentinel Pipeline...")
    print("=" * 50)
    
    # Step 1: Process videos
    print("Step 1: Processing videos from data/input_video/")
    from test_video import main as process_videos_main
    process_videos_main()
    
    # Step 2: Load results
    print("\nStep 2: Loading processed video results...")
    video_results = load_video_results()
    
    if not video_results:
        print("No video results found. Run video processing first.")
        return
    
    # Step 3: Generate risk predictions
    print("Step 3: Calculating risk predictions...")
    risk_predictions = []
    
    for result in video_results:
        risk = calculate_risk_score(result)
        risk_predictions.append({
            "video": result["video_name"],
            **risk
        })
    
    # Step 4: Save final output
    final_output = {
        "pipeline_run_time": str(datetime.now()),
        "total_videos_processed": len(video_results),
        "predictions": risk_predictions
    }
    
    output_file = os.path.join(OUTPUT_DIR, "final_risk_predictions.json")
    with open(output_file, 'w') as f:
        json.dump(final_output, f, indent=2)
    
    # Print summary
    print("\n✅ Pipeline Completed Successfully!")
    print(f"📊 Total videos processed: {len(video_results)}")
    print("\nRisk Predictions:")
    for pred in risk_predictions:
        print(f"   • {pred['video']}: {pred['risk_level']} Risk ({pred['risk_score']}%)")
    
    print(f"\n📁 Full results saved to: {output_file}")
    print("\nNext: Run frontend or Streamlit dashboard for visualization.")


if __name__ == "__main__":
    run_full_pipeline()
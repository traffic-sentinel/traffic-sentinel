#!/usr/bin/env python3
"""
Traffic Sentinel - Video Processing Script
Processes local Uganda traffic videos from data/input_video/
Extracts basic features for risk prediction.
"""

import os
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
import json

# Paths (relative to project root)
VIDEO_INPUT_DIR = "data/input_video"
OUTPUT_DIR = "data/output_results"
SAMPLE_FRAMES_DIR = "data/sample_framing"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SAMPLE_FRAMES_DIR, exist_ok=True)

def process_video(video_path):
    """Process a single video file and extract traffic features."""
    print(f"Processing video: {video_path}")
    
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video {video_path}")
        return None
    
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    
    vehicle_count = 0
    frame_number = 0
    features = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_number += 1
        
        # Sample every 30 frames to save computation
        if frame_number % 30 == 0:
            # Basic motion detection / vehicle counting simulation
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # In real version: Add YOLO or background subtraction here
            
            # Placeholder vehicle count (replace with actual detection)
            current_vehicles = np.random.randint(5, 25)  # Simulate for now
            
            features.append({
                "frame": frame_number,
                "timestamp": str(datetime.now()),
                "vehicle_count": current_vehicles,
                "density": "high" if current_vehicles > 15 else "medium" if current_vehicles > 8 else "low"
            })
            
            # Save sample frame
            if frame_number % 90 == 0:  # Save every 3 seconds approx
                frame_path = os.path.join(SAMPLE_FRAMES_DIR, f"frame_{os.path.basename(video_path)}_{frame_number}.jpg")
                cv2.imwrite(frame_path, frame)
    
    cap.release()
    
    # Summary
    result = {
        "video_name": os.path.basename(video_path),
        "duration_seconds": round(duration, 2),
        "total_frames": frame_count,
        "avg_vehicles_per_sample": round(sum(f["vehicle_count"] for f in features) / len(features), 2) if features else 0,
        "features": features[:10]  # Limit for output
    }
    
    # Save output
    output_file = os.path.join(OUTPUT_DIR, f"result_{os.path.basename(video_path)}.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Completed: {os.path.basename(video_path)} | Avg vehicles: {result['avg_vehicles_per_sample']}")
    return result


def main():
    """Run video processing on all videos in input folder."""
    if not os.path.exists(VIDEO_INPUT_DIR):
        print(f"❌ Input directory not found: {VIDEO_INPUT_DIR}")
        print("Please create it and add your Uganda traffic videos.")
        return
    
    video_files = [f for f in os.listdir(VIDEO_INPUT_DIR) if f.endswith(('.mp4', '.avi', '.mov'))]
    
    if not video_files:
        print("No video files found in data/input_video/")
        return
    
    print(f"Found {len(video_files)} video(s) to process.")
    
    all_results = []
    for video in video_files:
        video_path = os.path.join(VIDEO_INPUT_DIR, video)
        result = process_video(video_path)
        if result:
            all_results.append(result)
    
    # Save overall summary
    summary = {"processed_videos": len(all_results), "results": all_results}
    with open(os.path.join(OUTPUT_DIR, "processing_summary.json"), 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\n🎉 Video processing completed! Check data/output_results/")


if __name__ == "__main__":
    main()
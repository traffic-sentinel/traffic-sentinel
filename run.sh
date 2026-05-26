#!/bin/bash
# =============================================
# Traffic Sentinel - MVP Runner Script
# One-command starter for the full pipeline
# =============================================

echo "🚦 Traffic Sentinel - Uganda Traffic Intelligence System"
echo "===================================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 is not installed. Please install it first."
    exit 1
fi

# Create necessary directories
echo "📁 Setting up directories..."
mkdir -p data/input_video
mkdir -p data/output_results
mkdir -p data/sample_framing
mkdir -p models

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found. Skipping dependency install."
fi

echo ""
echo "Choose what to run:"
echo "1) Full Pipeline (Video Processing + Risk Prediction)"
echo "2) Video Processing Only"
echo "3) Risk Prediction Pipeline Only"
echo "4) Exit"
read -p "Enter your choice (1-4): " choice

case $choice in
    1)
        echo "🚀 Running Full Pipeline..."
        python scripts/run_pipeline.py
        ;;
    2)
        echo "🎥 Running Video Processing Only..."
        python scripts/test_video.py
        ;;
    3)
        echo "📊 Running Risk Prediction Pipeline..."
        python scripts/run_pipeline.py
        ;;
    4)
        echo "👋 Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Running Full Pipeline by default..."
        python scripts/run_pipeline.py
        ;;
esac

echo ""
echo "✅ Done! Check data/output_results/ for outputs."
echo "📸 Don't forget to add screenshots to README.md for your MVP demo.”
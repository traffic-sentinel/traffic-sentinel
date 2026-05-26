#!/bin/bash
echo "🚦 Starting Traffic Sentinel MVP..."

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

pip install -r backend/requirements.txt --quiet

echo "✅ Starting FastAPI server..."
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
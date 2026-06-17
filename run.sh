#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════
# Traffic Sentinel — Run Script
# Uganda Road Safety Intelligence System
# ═══════════════════════════════════════════════════════════════════
set -euo pipefail

BLUE='\033[0;34m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
die()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

echo ""
echo -e "${BLUE}🚦 Traffic Sentinel — Uganda Road Safety Intelligence${NC}"
echo "═══════════════════════════════════════════════════════"

# ── 1. Resolve .env ──────────────────────────────────────────────
if [ ! -f ".env" ]; then
  if [ -f ".env.example" ]; then
    info "No .env found — copying from .env.example"
    cp .env.example .env
    ok ".env created. Edit it if needed."
  else
    die "No .env or .env.example found. Create one first (see README)."
  fi
fi

# shellcheck disable=SC2046
export $(grep -v '^#' .env | grep -v '^\s*$' | xargs) 2>/dev/null || true

API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-8501}"

# ── 2. Directory setup ───────────────────────────────────────────
info "Setting up data directories..."
mkdir -p data/input_video data/output_results data/sample_framing data/raw_csvs
mkdir -p models logs
ok "Directories ready."

# ── 3. Mode selection ─────────────────────────────────────────────
echo ""
echo "  How would you like to run Traffic Sentinel?"
echo ""
echo "  1) 🐍  Local Python — full pipeline (FastAPI + Streamlit)"
echo "  2) 🐍  Local Python — FastAPI backend only"
echo "  3) 📊  Local Python — Streamlit dashboard only"
echo "  4) 🎥  Video processing only (CLI)"
echo "  5) 📈  Risk prediction only (CLI, uses existing results)"
echo "  6) 🐳  Docker (full stack, recommended for demo)"
echo "  7) 🧪  Run tests"
echo "  8) 👋  Exit"
echo ""
read -rp "  Choice [1-8]: " choice

# ── Shared: check Python ─────────────────────────────────────────
check_python() {
  command -v python3 &>/dev/null || die "Python3 not found. Install from https://python.org"
  PYTHON_VER=$(python3 -c "import sys; print(sys.version_info >= (3,10))")
  [ "$PYTHON_VER" = "True" ] || warn "Python 3.10+ recommended. You have $(python3 --version)"
}

# ── Shared: install deps ─────────────────────────────────────────
install_deps() {
  info "Installing dependencies..."
  if [ -f "requirements-minimal.txt" ]; then
    pip install -q -r requirements-minimal.txt
  else
    pip install -q -r requirements.txt
  fi
  ok "Dependencies installed."
}

# ── Shared: check for videos ─────────────────────────────────────
check_videos() {
  VID_COUNT=$(find data/input_video -maxdepth 1 \( -name "*.mp4" -o -name "*.avi" -o -name "*.mov" -o -name "*.mkv" \) 2>/dev/null | wc -l)
  if [ "$VID_COUNT" -eq 0 ]; then
    warn "No videos found in data/input_video/."
    warn "Add .mp4/.avi/.mov files, then run again."
    warn "The system will still start — processing will return empty results."
  else
    ok "Found ${VID_COUNT} video(s) in data/input_video/."
  fi
}

case $choice in

1)
  check_python
  install_deps
  check_videos
  echo ""
  info "Starting FastAPI backend on port ${API_PORT}..."
  uvicorn backend.app.main:app --host 0.0.0.0 --port "${API_PORT}" --reload &
  BACKEND_PID=$!
  sleep 2

  info "Starting Streamlit dashboard on port ${UI_PORT}..."
  streamlit run backend/app/app.py --server.port "${UI_PORT}" --server.headless true &
  DASH_PID=$!

  ok "Traffic Sentinel is running!"
  echo ""
  echo "  📊 Dashboard  → http://localhost:${UI_PORT}"
  echo "  📡 API docs   → http://localhost:${API_PORT}/docs"
  echo "  📡 API health → http://localhost:${API_PORT}/health"
  echo ""
  echo "  Press Ctrl+C to stop all services."
  echo ""
  trap "kill $BACKEND_PID $DASH_PID 2>/dev/null; echo 'Stopped.'" INT TERM
  wait
  ;;

2)
  check_python
  install_deps
  check_videos
  info "Starting FastAPI backend on port ${API_PORT}..."
  ok "API docs → http://localhost:${API_PORT}/docs"
  uvicorn backend.app.main:app --host 0.0.0.0 --port "${API_PORT}" --reload
  ;;

3)
  check_python
  install_deps
  info "Starting Streamlit dashboard on port ${UI_PORT}..."
  ok "Dashboard → http://localhost:${UI_PORT}"
  streamlit run backend/app/app.py --server.port "${UI_PORT}"
  ;;

4)
  check_python
  install_deps
  check_videos
  info "Running video processing pipeline..."
  python3 scripts/test_video.py
  ok "Done. Check data/output_results/"
  ;;

5)
  check_python
  install_deps
  info "Running risk prediction on existing results..."
  python3 scripts/run_pipeline.py
  ok "Done. Check data/output_results/final_risk_predictions.json"
  ;;

6)
  command -v docker &>/dev/null   || die "Docker not found. Install from https://docs.docker.com/get-docker/"
  docker compose version &>/dev/null 2>&1 || die "Docker Compose v2 not found. Update Docker Desktop."
  info "Building and starting Docker stack..."
  docker compose up --build
  ok "Traffic Sentinel is running!"
  echo "  📊 Dashboard → http://localhost:${UI_PORT}"
  echo "  📡 API       → http://localhost:${API_PORT}/docs"
  ;;

7)
  check_python
  install_deps
  info "Running test suite..."
  python3 -m pytest tests/ -v --tb=short
  ;;

8)
  echo "Goodbye."
  exit 0
  ;;

*)
  warn "Invalid choice '${choice}'. Running full local pipeline by default."
  check_python
  install_deps
  check_videos
  uvicorn backend.app.main:app --host 0.0.0.0 --port "${API_PORT}" --reload &
  streamlit run backend/app/app.py --server.port "${UI_PORT}" &
  wait
  ;;

esac
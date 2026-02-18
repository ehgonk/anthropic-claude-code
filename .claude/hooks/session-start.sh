#!/bin/bash
set -euo pipefail

# Only run in remote Claude Code sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-/home/user/anthropic-claude-code}"
BACKEND_DIR="$PROJECT_DIR/broker/backend"
FRONTEND_DIR="$PROJECT_DIR/broker/frontend"

echo "=== Session Start Hook ==="

# ── Backend: Python venv + pip install ──────────────────────────────────────
echo "[1/4] Setting up Python venv..."
if [ ! -d "$BACKEND_DIR/.venv" ]; then
  python3 -m venv "$BACKEND_DIR/.venv"
fi

echo "[2/4] Installing backend dependencies..."
"$BACKEND_DIR/.venv/bin/pip" install -q -r "$BACKEND_DIR/requirements.txt"

# ── Frontend: npm install ────────────────────────────────────────────────────
echo "[3/4] Installing frontend dependencies..."
npm --prefix "$FRONTEND_DIR" install

# ── Start servers ────────────────────────────────────────────────────────────
echo "[4/4] Starting backend and frontend servers..."

# Backend (FastAPI on :8001)
pkill -f "uvicorn app.main:app" 2>/dev/null || true
sleep 1
nohup "$BACKEND_DIR/.venv/bin/uvicorn" app.main:app \
  --host 0.0.0.0 --port 8001 --reload \
  --app-dir "$BACKEND_DIR" \
  > /tmp/broker-backend.log 2>&1 &

# Frontend (Vite on :5174)
pkill -f "vite.*5174" 2>/dev/null || true
sleep 1
cd "$FRONTEND_DIR"
nohup node node_modules/.bin/vite --host 0.0.0.0 --port 5174 --force \
  > /tmp/broker-frontend.log 2>&1 &
cd "$PROJECT_DIR"

# Wait for backend to be ready
echo "Waiting for backend..."
for i in $(seq 1 20); do
  if curl -sf http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "Backend ready ✓"
    break
  fi
  sleep 1
done

echo "=== Session Start Hook complete ==="
echo "  Frontend: http://localhost:5174"
echo "  Backend:  http://localhost:8001"

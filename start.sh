#!/bin/bash
set -e

# ============================================================
# ChatBI — One-click start script (lite mode)
#
# Starts backend + frontend locally with SQLite + in-memory
# vector store. No Docker/PostgreSQL/Redis/Qdrant needed.
#
# Prerequisites:
#   - Python 3.11+
#   - Node.js 18+
#   - An LLM API key (OpenAI or Anthropic)
#
# Usage:
#   chmod +x start.sh && ./start.sh
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ── .env setup ──────────────────────────────────────────────
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cat > .env << 'ENVFILE'
# === Lite Mode (SQLite + in-memory vector store) ===
DB_MODE=sqlite
SQLITE_PATH=data/chatbi.db

# === Security (auto-generated) ===
SECRET_KEY=PLACEHOLDER_SECRET
ENCRYPTION_KEY=PLACEHOLDER_ENCRYPT

# === LLM Configuration ===
# Option A: OpenAI (uncomment and set your key)
# INTENT_MODEL_PROVIDER=openai_compatible
# INTENT_MODEL_BASE_URL=https://api.openai.com/v1
# INTENT_MODEL_NAME=gpt-4o-mini
# INTENT_MODEL_API_KEY=sk-...
# TEXT_TO_SQL_PROVIDER=openai_compatible
# TEXT_TO_SQL_BASE_URL=https://api.openai.com/v1
# TEXT_TO_SQL_MODEL_NAME=gpt-4o
# TEXT_TO_SQL_API_KEY=sk-...

# Option B: Anthropic (uncomment and set your key)
# BASE_MODEL_PROVIDER=anthropic
# BASE_MODEL_API_KEY=sk-ant-...
# BASE_MODEL_NAME=claude-sonnet-4-6
ENVFILE

    # Generate random secrets
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    ENCRYPT=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    sed -i "s/PLACEHOLDER_SECRET/$SECRET/" .env
    sed -i "s/PLACEHOLDER_ENCRYPT/$ENCRYPT/" .env

    echo ""
    echo "=== .env created ==="
    echo "IMPORTANT: Edit .env to add your LLM API keys before continuing."
    echo "Then re-run this script."
    echo ""
    exit 0
fi

echo "=== ChatBI Lite Mode ==="
echo ""

# ── Backend ─────────────────────────────────────────────────
echo "[1/3] Setting up backend..."
cd "$SCRIPT_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null

echo "[2/3] Starting backend (SQLite + in-memory vectors)..."
cd "$SCRIPT_DIR"
export $(grep -v '^#' .env | grep -v '^\s*$' | xargs)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend &
BACKEND_PID=$!
sleep 2

# ── Frontend ────────────────────────────────────────────────
echo "[3/3] Starting frontend..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    npm install --silent
fi
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=== ChatBI is running ==="
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  Login:    admin@chatbi.local / admin123"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait

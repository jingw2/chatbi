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

# Pick a Python that can run this codebase's modern type syntax.
PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
    for candidate in python3.12 python3.11 python3; do
        if command -v "$candidate" >/dev/null 2>&1; then
            if "$candidate" -c "import sys; raise SystemExit(sys.version_info < (3, 11))"; then
                PYTHON_BIN="$(command -v "$candidate")"
                break
            fi
        fi
    done
fi

if [ -z "$PYTHON_BIN" ]; then
    echo "Python 3.11+ is required. Set PYTHON_BIN=/path/to/python3.11 and rerun."
    exit 1
fi

# ── .env setup ──────────────────────────────────────────────
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    SECRET=$("$PYTHON_BIN" -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)
    ENCRYPT=$("$PYTHON_BIN" -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || openssl rand -hex 32)

    cat > .env << 'ENVFILE'
# === Lite Mode (SQLite + in-memory vector store) ===
DB_MODE=sqlite
SQLITE_PATH=data/chatbi.db

# === Security (auto-generated) ===
SECRET_KEY=__SECRET_KEY__
ENCRYPTION_KEY=__ENCRYPTION_KEY__

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

    # Portable placeholder replacement for macOS and Linux.
    "$PYTHON_BIN" -c "from pathlib import Path; p=Path('.env'); s=p.read_text(); s=s.replace('__SECRET_KEY__', '$SECRET').replace('__ENCRYPTION_KEY__', '$ENCRYPT'); p.write_text(s)"

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
    "$PYTHON_BIN" -m venv venv
fi
source venv/bin/activate
python -c "import sys; raise SystemExit(sys.version_info < (3, 11))" || {
    echo "Existing backend/venv uses Python < 3.11. Remove backend/venv or set PYTHON_BIN to Python 3.11+."
    exit 1
}
python -m pip install --disable-pip-version-check -r requirements.txt

echo "[2/3] Starting backend (SQLite + in-memory vectors)..."
cd "$SCRIPT_DIR"
set -a
source .env
set +a
uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend &
BACKEND_PID=$!
sleep 2
if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Backend failed to start. See the log above."
    exit 1
fi

# ── Frontend ────────────────────────────────────────────────
echo "[3/3] Starting frontend..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev -- --host 127.0.0.1 &
FRONTEND_PID=$!
sleep 2
if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    echo "Frontend failed to start. See the log above."
    kill "$BACKEND_PID" 2>/dev/null || true
    exit 1
fi

echo ""
echo "=== ChatBI is running ==="
echo "  Frontend: http://localhost:5173"
echo "  Backend:  http://localhost:8000"
echo "  Login:    admin@chatbi.local / admin123"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT TERM
wait

# ChatBI Deployment Guide

简体中文: [deployment.zh-CN.md](./deployment.zh-CN.md)

## Table of Contents

- [Deployment Modes](#deployment-modes)
- [Lite Mode (No Docker)](#lite-mode-no-docker)
- [Production Mode (Docker Compose)](#production-mode-docker-compose)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [LLM Configuration](#llm-configuration)
- [Local LLM with vLLM](#local-llm-with-vllm)
- [Production Checklist](#production-checklist)
- [Troubleshooting](#troubleshooting)

---

## Deployment Modes

ChatBI supports two deployment modes:

| | Lite Mode | Production Mode |
|---|-----------|-----------------|
| **Use case** | Development, trial, small teams | Production, enterprise |
| **Database** | SQLite (auto-created) | PostgreSQL 16 |
| **Vector store** | In-memory (numpy) | Qdrant |
| **Cache** | None | Redis (optional) |
| **Prerequisites** | Python 3.11+, Node.js 18+ | Docker 24+, Docker Compose v2 |
| **Setup time** | ~2 minutes | ~5 minutes |
| **Data persistence** | SQLite file (`data/chatbi.db`) | Docker volumes |

Switch between modes by setting `DB_MODE=sqlite` or `DB_MODE=postgres` in `.env`.

---

## Lite Mode (No Docker)

**Zero external dependencies.** Uses SQLite for data storage and an in-memory vector store (numpy-based cosine similarity). Ideal for local development, demos, and small-scale usage.

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python | 3.11+ |
| Node.js | 18+ |
| LLM API key | OpenAI or Anthropic |

### Quick Start

```bash
git clone https://github.com/jingw2/chatbi.git
cd chatbi

# Linux / macOS
chmod +x start.sh && ./start.sh

# Windows
.\start.ps1
```

On first run, the script:
1. Creates `.env` with auto-generated `SECRET_KEY` and `ENCRYPTION_KEY`
2. Prints instructions to add your LLM API key, then exits
3. On second run (after you edit `.env`): creates a Python venv, installs deps, starts backend + frontend

```
Frontend: http://localhost:5173
Backend:  http://localhost:8000
Login:    admin@chatbi.local / admin123
```

### How It Works

- **Database**: SQLite file at `data/chatbi.db` (auto-created). Uses WAL mode for concurrent reads.
- **Vector store**: In-memory numpy-based store. Data lives only while the backend is running — embeddings are re-computed on restart.
- **Admin user**: Auto-created on first startup (email: `admin@chatbi.local`, password: `admin123`).
- **Tables**: Auto-created from ORM metadata — no Alembic migrations needed.

### Manual Start (without scripts)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export DB_MODE=sqlite
export SQLITE_PATH=data/chatbi.db
export SECRET_KEY=$(openssl rand -hex 32)
export ENCRYPTION_KEY=$(openssl rand -hex 32)
# ... add LLM API keys ...

uvicorn app.main:app --host 0.0.0.0 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Lite Mode Limitations

- **Vector store is not persistent** — embeddings are lost on restart and must be re-indexed
- **No horizontal scaling** — SQLite supports a single writer at a time
- **No Redis caching** — all requests hit the database directly
- Best for teams of 1–5 concurrent users

---

## Production Mode (Docker Compose)

Uses PostgreSQL, Qdrant, and Redis for a fully persistent, scalable deployment.

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Docker | 24+ |
| Docker Compose | v2 (bundled with Docker Desktop) |
| NVIDIA GPU + drivers | (optional, for vLLM) |

### Quick Start

```bash
git clone https://github.com/jingw2/chatbi.git
cd chatbi

# 1. Configure
cp .env.example .env
# Edit .env: set DB_MODE=postgres, passwords, API keys

# 2. Start
docker compose up -d

# 3. Migrate database
docker compose exec backend alembic upgrade head

# 4. Create admin user
docker compose exec backend python -m app.scripts.create_admin

# 5. Visit http://localhost:3000
```

## Environment Variables

### Mode Selection

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_MODE` | No | `postgres` | `sqlite` for lite mode, `postgres` for production |
| `SQLITE_PATH` | No | `data/chatbi.db` | SQLite database path (lite mode only) |

### Infrastructure (Production Mode Only)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_DB` | No | `chatbi` | PostgreSQL database name |
| `POSTGRES_USER` | No | `chatbi` | PostgreSQL username |
| `POSTGRES_PASSWORD` | **Yes** | — | PostgreSQL password |
| `POSTGRES_HOST` | No | `postgres` | PostgreSQL hostname |
| `REDIS_PASSWORD` | **Yes** | — | Redis password |
| `QDRANT_URL` | No | `http://qdrant:6333` | Qdrant vector store URL |

### Security

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | **Yes** | — | JWT signing key. Generate with `openssl rand -hex 32` |
| `ENCRYPTION_KEY` | **Yes** | — | Database password encryption key. Generate with `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | JWT access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | `7` | Refresh token TTL |

### LLM — Intent Model

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INTENT_MODEL_PROVIDER` | No | `openai_compatible` | `openai_compatible` or `anthropic` |
| `INTENT_MODEL_BASE_URL` | No | — | API endpoint (e.g. `http://vllm:8001/v1` for local) |
| `INTENT_MODEL_NAME` | No | `Qwen2.5-7B-Instruct` | Model name |
| `INTENT_MODEL_API_KEY` | No | — | API key (use any non-empty string for local vLLM) |

### LLM — Text-to-SQL Model

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TEXT_TO_SQL_PROVIDER` | No | `openai_compatible` | `openai_compatible` or `anthropic` |
| `TEXT_TO_SQL_BASE_URL` | No | — | API endpoint |
| `TEXT_TO_SQL_MODEL_NAME` | No | `Qwen2.5-Coder-32B-Instruct` | Model name |
| `TEXT_TO_SQL_API_KEY` | No | — | API key |

### LLM — Base Model

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BASE_MODEL_PROVIDER` | No | `anthropic` | `openai_compatible` or `anthropic` |
| `BASE_MODEL_API_KEY` | No | — | API key (required for Anthropic) |
| `BASE_MODEL_NAME` | No | `claude-sonnet-4-6` | Model name |
| `BASE_MODEL_BASE_URL` | No | — | Override API endpoint |

## Database Migrations

ChatBI uses Alembic for database schema migrations.

```bash
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Check current migration version
docker compose exec backend alembic current

# Generate a new migration after model changes (development only)
docker compose exec backend alembic revision --autogenerate -m "description"
```

## LLM Configuration

### Option A: All Cloud APIs (simplest)

Use cloud providers for all three model roles. No GPU needed.

```bash
# .env
INTENT_MODEL_PROVIDER=openai_compatible
INTENT_MODEL_BASE_URL=https://api.openai.com/v1
INTENT_MODEL_NAME=gpt-4o-mini
INTENT_MODEL_API_KEY=sk-...

TEXT_TO_SQL_PROVIDER=openai_compatible
TEXT_TO_SQL_BASE_URL=https://api.openai.com/v1
TEXT_TO_SQL_MODEL_NAME=gpt-4o
TEXT_TO_SQL_API_KEY=sk-...

BASE_MODEL_PROVIDER=anthropic
BASE_MODEL_API_KEY=sk-ant-...
BASE_MODEL_NAME=claude-sonnet-4-6
```

### Option B: Local LLM + Cloud (recommended)

Run intent and SQL models locally via vLLM, use Anthropic for insights.

```bash
# .env
INTENT_MODEL_PROVIDER=openai_compatible
INTENT_MODEL_BASE_URL=http://vllm:8001/v1
INTENT_MODEL_NAME=Qwen2.5-7B-Instruct
INTENT_MODEL_API_KEY=none

TEXT_TO_SQL_PROVIDER=openai_compatible
TEXT_TO_SQL_BASE_URL=http://vllm:8001/v1
TEXT_TO_SQL_MODEL_NAME=Qwen2.5-Coder-32B-Instruct
TEXT_TO_SQL_API_KEY=none

BASE_MODEL_PROVIDER=anthropic
BASE_MODEL_API_KEY=sk-ant-...
BASE_MODEL_NAME=claude-sonnet-4-6
```

Then start with vLLM:

```bash
docker compose -f docker-compose.yml -f docker-compose.vllm.yml up -d
```

## Local LLM with vLLM

### Requirements

- NVIDIA GPU with sufficient VRAM (32B model needs ~40GB across GPUs)
- NVIDIA Container Toolkit installed
- Model weights downloaded locally

### vLLM Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VLLM_MODEL_PATH` | — | Local directory containing model weights |
| `VLLM_MODEL_NAME` | — | Directory name of the model inside `VLLM_MODEL_PATH` |
| `VLLM_TENSOR_PARALLEL` | `1` | Number of GPUs for tensor parallelism |
| `VLLM_MAX_MODEL_LEN` | `32768` | Maximum sequence length |
| `VLLM_SERVED_MODEL_NAME` | `chatbi-sql` | Model name exposed via the API |

### Download models

```bash
# Install huggingface-cli
pip install huggingface_hub

# Download models
huggingface-cli download Qwen/Qwen2.5-7B-Instruct --local-dir /models/Qwen2.5-7B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-32B-Instruct --local-dir /models/Qwen2.5-Coder-32B-Instruct
```

## Production Checklist

- [ ] Set strong, unique values for `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `SECRET_KEY`, `ENCRYPTION_KEY`
- [ ] Remove `--reload` from the backend command (already handled in Dockerfile CMD)
- [ ] Remove the `volumes: ./backend:/app` mount in `docker-compose.yml` (dev-only)
- [ ] Configure HTTPS via a reverse proxy (Nginx, Traefik, or Caddy) in front of port 3000
- [ ] Set `allow_origins` in `backend/app/main.py` to your actual domain instead of `localhost:3000`
- [ ] Back up PostgreSQL data volume regularly
- [ ] Monitor Qdrant storage volume growth
- [ ] Set up log aggregation for the backend container

## Troubleshooting

### Backend won't start

```bash
# Check logs
docker compose logs backend

# Common issues:
# - PostgreSQL not ready: backend depends on healthcheck, but verify with:
docker compose exec postgres pg_isready -U chatbi
```

### Database migration errors

```bash
# If migration state is inconsistent, check current version:
docker compose exec backend alembic current

# To see migration history:
docker compose exec backend alembic history
```

### vLLM GPU issues

```bash
# Verify NVIDIA runtime is available:
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Check vLLM logs:
docker compose -f docker-compose.yml -f docker-compose.vllm.yml logs vllm
```

### Frontend shows blank page

```bash
# Verify nginx is proxying correctly:
docker compose exec frontend cat /etc/nginx/conf.d/default.conf

# Check backend health:
curl http://localhost:8000/health
```

### Lite mode — backend won't start

```bash
# Check Python version (needs 3.11+):
python --version

# Verify .env has required keys:
grep -E "^(DB_MODE|SECRET_KEY|ENCRYPTION_KEY)" .env

# Check the SQLite data directory is writable:
ls -la data/

# Check health endpoint:
curl http://localhost:8000/health
# Should return: {"status": "ok", "mode": "lite"}
```

### Lite mode — "no such table" errors

The backend auto-creates tables on startup. If you see table errors, the startup may have failed silently. Check the backend output for import errors or missing dependencies:

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python -c "from app.core.database import Base; import app.models; print('Models OK')"
```

# ChatBI Deployment Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Database Migrations](#database-migrations)
- [LLM Configuration](#llm-configuration)
- [Local LLM with vLLM](#local-llm-with-vllm)
- [Production Checklist](#production-checklist)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Docker | 24+ |
| Docker Compose | v2 (bundled with Docker Desktop) |
| NVIDIA GPU + drivers | (optional, for vLLM) |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/your-github/chatbi.git
cd chatbi

# 2. Configure
cp .env.example .env
# Edit .env with your passwords and API keys

# 3. Start
docker compose up -d

# 4. Migrate database
docker compose exec backend alembic upgrade head

# 5. Create admin user
docker compose exec backend python -m app.scripts.create_admin

# 6. Visit http://localhost:3000
```

## Environment Variables

### Infrastructure

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `POSTGRES_DB` | No | `chatbi` | PostgreSQL database name |
| `POSTGRES_USER` | No | `chatbi` | PostgreSQL username |
| `POSTGRES_PASSWORD` | **Yes** | — | PostgreSQL password |
| `REDIS_PASSWORD` | **Yes** | — | Redis password |

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

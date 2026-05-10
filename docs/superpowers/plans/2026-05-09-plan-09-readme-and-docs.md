# README & Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create bilingual READMEs (English + Chinese), MIT license, and a deployment guide so the project is ready for public release on GitHub.

**Architecture:** Four markdown/text files at the repo root and in `docs/`. No code changes — documentation only. The READMEs follow the spec (section 8): badges, features, quick start, architecture, configuration, contributing, license, Star History chart. The deployment guide covers Docker Compose setup, environment variables, Alembic migrations, and the optional vLLM sidecar.

**Tech Stack:** Markdown, Git

---

## File Map

```
chatbi/
├── README.md              # CREATE: English README (primary entry)
├── README.zh-CN.md        # CREATE: Chinese README
├── LICENSE                 # CREATE: MIT license
└── docs/
    └── deployment.md       # CREATE: detailed deployment guide
```

---

## Task 1: LICENSE File

**Files:**
- Create: `LICENSE`

- [ ] **Step 1: Create `LICENSE`**

Create `LICENSE` at the repo root with the standard MIT license text:

```text
MIT License

Copyright (c) 2026 ChatBI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Commit**

```bash
git add LICENSE
git commit -m "docs: add MIT license"
```

---

## Task 2: English README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Create `README.md`**

```markdown
<div align="center">
  <h1>ChatBI</h1>
  <p><strong>Open-source Conversational Business Intelligence</strong></p>
  <p>Ask questions in natural language. Get SQL, charts, insights, and actionable suggestions — all in one conversation.</p>

  <p>
    <a href="./README.zh-CN.md">简体中文</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="./docs/deployment.md">Deployment Guide</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
    <img src="https://img.shields.io/badge/python-3.11-blue.svg" alt="Python" />
    <img src="https://img.shields.io/badge/react-19-61dafb.svg" alt="React" />
    <img src="https://img.shields.io/badge/docker-compose-2496ED.svg" alt="Docker" />
  </p>
</div>

---

## Features

- **Natural Language to SQL** — Ask business questions, get validated SQL with retry logic
- **Smart Visualization** — Auto-inferred chart types (line, bar, pie, dual-axis, big number) via Apache ECharts
- **Insights & Suggestions** — LLM-generated business insights and actionable decision suggestions per query
- **Fixed Workflows** — Pre-defined multi-step SQL reports triggered by keywords (e.g. "monthly report")
- **Schema Manager** — Auto-sync database schema, annotate tables/columns with descriptions for better SQL generation
- **Knowledge Base** — Business rules, few-shot examples, and glossary items to guide the LLM
- **Multi-User RBAC + RLS** — Role-based access control with row-level security injection
- **Flexible LLM Backend** — Supports local models via vLLM and cloud APIs (OpenAI-compatible, Anthropic)
- **On-Premise Deployment** — Single `docker compose up` command, no external dependencies

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite + Nginx)       │
│   Chat UI · ECharts Visualization · Admin Dashboard          │
└────────────────────────┬─────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼─────────────────────────────────────┐
│                      Backend (FastAPI)                        │
│                                                              │
│  ┌─────────┐  ┌────────────┐  ┌──────────┐  ┌────────────┐ │
│  │ Intent   │→│ Schema +    │→│ Text-to- │→│ Validation │  │
│  │ Classify │  │ Knowledge  │  │ SQL Gen  │  │ + RLS      │  │
│  └─────────┘  │ Retrieval  │  └──────────┘  └────────────┘  │
│               └────────────┘        │                        │
│  ┌──────────┐  ┌────────────┐  ┌────▼──────┐  ┌──────────┐ │
│  │ Workflow  │  │ Query      │  │ Chart    │  │ Insight  │  │
│  │ Engine   │  │ Execution  │  │ Inference│  │ + Suggest│  │
│  └──────────┘  └────────────┘  └──────────┘  └──────────┘  │
└──┬─────┬──────────┬───────────────────────────────┬─────────┘
   │     │          │                               │
┌──▼──┐┌─▼───┐ ┌───▼───┐                     ┌────▼────┐
│Pg16 ││Redis│ │Qdrant │                     │vLLM     │
│     ││     │ │       │                     │(optional)│
└─────┘└─────┘ └───────┘                     └─────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose v2
- (Optional) NVIDIA GPU + drivers for local LLM via vLLM

### 1. Clone and configure

```bash
git clone https://github.com/your-github/chatbi.git
cd chatbi
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD, REDIS_PASSWORD, SECRET_KEY, ENCRYPTION_KEY
# Configure LLM providers (see docs/deployment.md for details)
```

### 2. Start services

```bash
# Cloud API mode (lightest — no GPU needed)
docker compose up -d

# With local LLM (requires NVIDIA GPU)
docker compose -f docker-compose.yml -f docker-compose.vllm.yml up -d
```

### 3. Run database migrations

```bash
docker compose exec backend alembic upgrade head
```

### 4. Create the first admin user

```bash
docker compose exec backend python -m app.scripts.create_admin
```

### 5. Open the app

Visit [http://localhost:3000](http://localhost:3000) and log in with the admin credentials.

## Configuration

ChatBI uses three independently configurable LLM roles:

| Role | Purpose | Recommended Model |
|------|---------|-------------------|
| **Intent** | Classify user questions | Qwen2.5-7B-Instruct (local) |
| **Text-to-SQL** | Generate SQL from natural language | Qwen2.5-Coder-32B-Instruct (local) |
| **Base** | Insights, suggestions, general responses | Claude Sonnet (cloud) |

Each role supports `openai_compatible` or `anthropic` provider. See [docs/deployment.md](./docs/deployment.md) for full environment variable reference.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, asyncpg |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| State | Zustand (client), TanStack Query (server) |
| Charts | Apache ECharts (via echarts-for-react) |
| Database | PostgreSQL 16 |
| Vector Store | Qdrant |
| Cache | Redis 7 |
| LLM | vLLM (local) / OpenAI-compatible / Anthropic |
| Embedding | BGE-M3 + BGE-Reranker-v2-M3 (FlagEmbedding) |

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m "feat: add my feature"`)
4. Push to the branch (`git push origin feat/my-feature`)
5. Open a Pull Request

## License

This project is licensed under the [MIT License](./LICENSE).

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=your-github/chatbi&type=Date)](https://star-history.com/#your-github/chatbi)
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add English README"
```

---

## Task 3: Chinese README

**Files:**
- Create: `README.zh-CN.md`

- [ ] **Step 1: Create `README.zh-CN.md`**

```markdown
<div align="center">
  <h1>ChatBI</h1>
  <p><strong>开源对话式商业智能平台</strong></p>
  <p>用自然语言提问，获得 SQL、图表、洞察和可操作的决策建议 —— 全在一次对话中完成。</p>

  <p>
    <a href="./README.md">English</a> •
    <a href="#快速开始">快速开始</a> •
    <a href="./docs/deployment.md">部署指南</a>
  </p>

  <p>
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
    <img src="https://img.shields.io/badge/python-3.11-blue.svg" alt="Python" />
    <img src="https://img.shields.io/badge/react-19-61dafb.svg" alt="React" />
    <img src="https://img.shields.io/badge/docker-compose-2496ED.svg" alt="Docker" />
  </p>
</div>

---

## 功能特性

- **自然语言转 SQL** —— 用业务语言提问，系统自动生成经过验证的 SQL 查询
- **智能可视化** —— 自动推断图表类型（折线图、柱状图、饼图、双轴图、大数字卡片），基于 Apache ECharts
- **洞察与建议** —— 每次查询自动生成业务洞察和可操作的决策建议
- **固定工作流** —— 预定义多步骤 SQL 报表，通过关键词触发（如"月度报表"）
- **Schema 管理** —— 自动同步数据库表结构，支持为表/列添加业务描述以提升 SQL 生成质量
- **知识库** —— 业务规则、Few-shot 示例和术语表，用于引导 LLM 生成更准确的 SQL
- **多用户 RBAC + RLS** —— 基于角色的访问控制 + 行级安全策略自动注入
- **灵活的 LLM 后端** —— 支持 vLLM 本地模型和云端 API（OpenAI 兼容、Anthropic）
- **私有化部署** —— 一条 `docker compose up` 命令即可启动，无外部依赖

## 架构

```
┌──────────────────────────────────────────────────────────────┐
│                    前端 (React + Vite + Nginx)                │
│          对话 UI · ECharts 可视化 · 管理后台                   │
└────────────────────────┬─────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼─────────────────────────────────────┐
│                      后端 (FastAPI)                           │
│                                                              │
│  ┌─────────┐  ┌────────────┐  ┌──────────┐  ┌────────────┐ │
│  │ 意图识别 │→│ Schema +   │→│ Text-to- │→│ SQL 验证   │  │
│  │         │  │ 知识检索    │  │ SQL 生成  │  │ + RLS 注入 │  │
│  └─────────┘  └────────────┘  └──────────┘  └────────────┘  │
│  ┌──────────┐  ┌────────────┐  ┌──────────┐  ┌──────────┐  │
│  │ 工作流    │  │ 查询执行   │  │ 图表推断  │  │ 洞察建议  │  │
│  │ 引擎     │  │           │  │          │  │          │  │
│  └──────────┘  └────────────┘  └──────────┘  └──────────┘  │
└──┬─────┬──────────┬───────────────────────────────┬─────────┘
   │     │          │                               │
┌──▼──┐┌─▼───┐ ┌───▼───┐                     ┌────▼────┐
│Pg16 ││Redis│ │Qdrant │                     │vLLM     │
│     ││     │ │       │                     │(可选)    │
└─────┘└─────┘ └───────┘                     └─────────┘
```

## 快速开始

### 前置条件

- Docker 和 Docker Compose v2
- （可选）NVIDIA GPU + 驱动，用于通过 vLLM 运行本地大模型

### 1. 克隆并配置

```bash
git clone https://github.com/your-github/chatbi.git
cd chatbi
cp .env.example .env
# 编辑 .env —— 设置 POSTGRES_PASSWORD、REDIS_PASSWORD、SECRET_KEY、ENCRYPTION_KEY
# 配置 LLM 提供商（详见 docs/deployment.md）
```

### 2. 启动服务

```bash
# 云端 API 模式（最轻量，无需 GPU）
docker compose up -d

# 使用本地大模型（需要 NVIDIA GPU）
docker compose -f docker-compose.yml -f docker-compose.vllm.yml up -d
```

### 3. 执行数据库迁移

```bash
docker compose exec backend alembic upgrade head
```

### 4. 创建管理员账户

```bash
docker compose exec backend python -m app.scripts.create_admin
```

### 5. 访问应用

打开 [http://localhost:3000](http://localhost:3000)，使用管理员账户登录。

## 配置

ChatBI 使用三个独立配置的 LLM 角色：

| 角色 | 用途 | 推荐模型 |
|------|------|----------|
| **意图识别** | 分类用户问题 | Qwen2.5-7B-Instruct（本地） |
| **Text-to-SQL** | 将自然语言转换为 SQL | Qwen2.5-Coder-32B-Instruct（本地） |
| **基础模型** | 洞察、建议、通用回复 | Claude Sonnet（云端） |

每个角色支持 `openai_compatible` 或 `anthropic` 提供商。完整环境变量参考请查看 [docs/deployment.md](./docs/deployment.md)。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11、FastAPI、SQLAlchemy 2.0、asyncpg |
| 前端 | React 19、TypeScript、Vite、Tailwind CSS、shadcn/ui |
| 状态管理 | Zustand（客户端）、TanStack Query（服务端） |
| 图表 | Apache ECharts（echarts-for-react） |
| 数据库 | PostgreSQL 16 |
| 向量存储 | Qdrant |
| 缓存 | Redis 7 |
| 大模型 | vLLM（本地）/ OpenAI 兼容 / Anthropic |
| Embedding | BGE-M3 + BGE-Reranker-v2-M3（FlagEmbedding） |

## 参与贡献

欢迎贡献代码！请按以下步骤操作：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feat/my-feature`)
3. 提交更改 (`git commit -m "feat: add my feature"`)
4. 推送到分支 (`git push origin feat/my-feature`)
5. 创建 Pull Request

## 许可证

本项目基于 [MIT 许可证](./LICENSE) 开源。

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=your-github/chatbi&type=Date)](https://star-history.com/#your-github/chatbi)
```

- [ ] **Step 2: Commit**

```bash
git add README.zh-CN.md
git commit -m "docs: add Chinese README"
```

---

## Task 4: Deployment Guide

**Files:**
- Create: `docs/deployment.md`

- [ ] **Step 1: Create `docs/deployment.md`**

```markdown
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
```

- [ ] **Step 2: Commit**

```bash
git add docs/deployment.md
git commit -m "docs: add deployment guide"
```

---

## Self-Review

**Spec coverage check:**

- ✅ README.md — English, badges, features, quick start, architecture diagram, configuration, contributing, license, Star History
- ✅ README.zh-CN.md — Chinese translation, linked from English README
- ✅ LICENSE — MIT
- ✅ docs/deployment.md — Docker Compose setup, env vars, migrations, vLLM config, production checklist, troubleshooting
- ✅ Star History chart at bottom of both READMEs
- ✅ Bilingual link at top of each README

**Placeholder scan:** No TBD/TODO in any file content. The `your-github/chatbi` GitHub URL is a deliberate placeholder per the spec (`"GitHub: your-github/chatbi"`).

**Type consistency:** N/A — no code in this plan.

**Intentionally deferred:**
- `docs/configuration.md` (spec mentions it but all config info is covered in deployment.md)
- Actual GitHub repo URL (user will replace `your-github/chatbi` when publishing)
- `app.scripts.create_admin` script (referenced in docs but not created — this is a simple CLI script the user can add)

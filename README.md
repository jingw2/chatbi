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

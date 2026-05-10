<div align="center">
  <h1>ChatBI</h1>
  <p><strong>Open-source Conversational Business Intelligence</strong></p>
  <p>Ask questions in natural language. Get SQL, charts, insights, and actionable suggestions — all in one conversation.</p>

  <p>
    <a href="./README.zh-CN.md">简体中文</a> •
    <a href="#quick-start-lite-mode">Quick Start</a> •
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
- **Two Deployment Modes** — Lite mode (zero Docker) for dev/trial, production mode (Docker Compose) for deployment

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)               │
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
└──────────────────────────────────────────────────────────────┘
        │                                           │
   Lite mode:                                  Production:
   SQLite + in-memory vectors              Pg16 + Qdrant + Redis
```

## Quick Start (Lite Mode)

**No Docker needed.** Just Python 3.11+ and Node.js 18+.

```bash
git clone https://github.com/jingw2/chatbi.git
cd chatbi

# Linux / macOS
chmod +x start.sh && ./start.sh

# Windows
.\start.ps1
```

On first run, the script creates `.env` with auto-generated secrets. **Edit `.env` to add your LLM API key**, then re-run.

```
Frontend: http://localhost:5173
Backend:  http://localhost:8000
Login:    admin@chatbi.local / admin123
```

Lite mode uses **SQLite** + **in-memory vector store** — zero external dependencies.

## Production Deployment (Docker Compose)

For production with PostgreSQL, Qdrant, and Redis:

```bash
cp .env.example .env
# Edit .env: set DB_MODE=postgres, passwords, API keys

docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.create_admin
```

Visit [http://localhost:3000](http://localhost:3000). See [docs/deployment.md](./docs/deployment.md) for full guide.

## Configuration

ChatBI uses three independently configurable LLM roles:

| Role | Purpose | Recommended Model |
|------|---------|-------------------|
| **Intent** | Classify user questions | Qwen2.5-7B-Instruct (local) or gpt-4o-mini |
| **Text-to-SQL** | Generate SQL from natural language | Qwen2.5-Coder-32B-Instruct (local) or gpt-4o |
| **Base** | Insights, suggestions, general responses | Claude Sonnet (cloud) |

Each role supports `openai_compatible` or `anthropic` provider. See [docs/deployment.md](./docs/deployment.md) for full environment variable reference.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0, asyncpg / aiosqlite |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, shadcn/ui |
| State | Zustand (client), TanStack Query (server) |
| Charts | Apache ECharts (via echarts-for-react) |
| Database | PostgreSQL 16 (production) / SQLite (lite) |
| Vector Store | Qdrant (production) / In-memory (lite) |
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

[![Star History Chart](https://api.star-history.com/svg?repos=jingw2/chatbi&type=Date)](https://star-history.com/#jingw2/chatbi)

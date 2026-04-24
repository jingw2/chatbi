# ChatBI — System Design Spec
**Date:** 2026-04-16  
**Status:** Approved  
**Author:** Brainstorming session

---

## 1. Project Overview

ChatBI is an open-source, enterprise-grade Conversational Business Intelligence platform supporting on-premise private deployment. Users ask questions in natural language; the system completes the full pipeline: **intent recognition → schema retrieval → SQL generation → query execution → visualization → insights → actionable decision suggestions**.

**GitHub:** `your-github/chatbi`  
**License:** MIT

### Core Goals
- Full enterprise feature set: Text-to-SQL, Fixed Workflows, multi-user RBAC + RLS, schema management, knowledge base, audit logs
- On-premise deployment via Docker Compose (single command)
- Visualization charts + natural language insights + actionable decision suggestions per query
- Support both local LLM (vLLM) and cloud APIs (OpenAI-compatible, Anthropic-compatible)

---

## 2. Architecture

### Approach
**Modular Monolith** — single FastAPI application with clear internal module boundaries, separate containers only for infrastructure services. Chosen for minimal deployment complexity, contributor-friendliness, and a natural upgrade path to microservices when scaling to Kubernetes.

### Container Composition (docker-compose)

| Container | Technology | Responsibility |
|-----------|-----------|----------------|
| `frontend` | React 18 + TypeScript + Vite + Nginx | Chat UI, charts, admin dashboard |
| `backend` | Python 3.11 + FastAPI (async) | All business logic, REST API |
| `postgres` | PostgreSQL 16 | Users, permissions, datasources, audit, workflow metadata |
| `qdrant` | Qdrant | Schema embedding + few-shot example vector retrieval |
| `redis` | Redis 7 | Session cache, query result cache, rate limiting |
| `vllm` *(optional)* | vLLM | Local LLM inference, OpenAI API compatible |

> **Note on Embedding/Reranker:** `bge-m3` and `bge-reranker-v2-m3` run as Python libraries inside the `backend` container (CPU) in the MVP. For production scale, they can be extracted into a dedicated `embedder` container to avoid resource contention with the main application.

### Backend Module Layout

```
backend/app/
├── api/           # HTTP routing layer (FastAPI routers)
├── auth/          # Authentication, JWT, RBAC
├── query_engine/  # Core pipeline: intent → retrieval → prompt → SQL → execute → insight
├── llm_gateway/   # Unified LLM interface (OpenAI-compatible, Anthropic-compatible)
├── schema_mgr/    # Datasource connections, schema sync, annotation management
├── knowledge/     # Business rules, few-shot examples, glossary CRUD + embedding
├── workflow/      # Fixed Workflow definitions, intent routing, execution orchestration
├── viz/           # Chart type inference, ECharts config generation
└── audit/         # Query audit log writes and queries
```

### Frontend Page Structure

```
frontend/src/
├── pages/
│   ├── Chat/              # Main chat interface
│   └── Admin/
│       ├── DataSources/   # Database connection management
│       ├── Schema/        # Schema annotation management
│       ├── Knowledge/     # Business rules / few-shot / glossary
│       ├── Workflows/     # Fixed Workflow configuration
│       ├── Users/         # User and permission management
│       └── Audit/         # Audit log viewer
```

---

## 3. LLM Gateway

### Three Model Roles

| Role | Recommended Model | Pipeline Step | Notes |
|------|------------------|---------------|-------|
| **Intent Model** | `Qwen2.5-7B-Instruct` | Step 1: Intent recognition | Classification task, 7B sufficient, saves main model resources |
| **Text-to-SQL Model** | `Qwen2.5-Coder-32B-Instruct` | Step 4: SQL generation + Step 5: retry | Core model, SQL-specialized |
| **Base Model** | Reuse Coder-32B or configure separately | Step 9: Insights + decision suggestions | Can downgrade to 7B under high concurrency |

### Provider Types

| Provider | `api_key` | `base_url` | Notes |
|----------|-----------|------------|-------|
| `openai_compatible` | Optional | Required | Covers vLLM, Kimi, GLM, Azure, Qianwen, DeepSeek, etc. |
| `openai` | Required | Default official, overridable | Direct OpenAI service |
| `anthropic` | Required | Default official, overridable | Claude series and Anthropic-compatible endpoints |

vLLM uses `openai_compatible` with a local `base_url`. No `api_key` required for local deployment (pass `"none"` as placeholder when SDK requires non-empty value).

### Configuration (`.env`)

```bash
# Intent Model
INTENT_MODEL_PROVIDER=openai_compatible
INTENT_MODEL_BASE_URL=http://vllm:8000/v1
INTENT_MODEL_NAME=Qwen2.5-7B-Instruct
INTENT_MODEL_API_KEY=            # optional for local

# Text-to-SQL Model
TEXT_TO_SQL_PROVIDER=openai_compatible
TEXT_TO_SQL_BASE_URL=http://vllm:8000/v1
TEXT_TO_SQL_MODEL_NAME=Qwen2.5-Coder-32B-Instruct
TEXT_TO_SQL_API_KEY=             # optional for local

# Base Model
BASE_MODEL_PROVIDER=anthropic
BASE_MODEL_API_KEY=sk-ant-...
BASE_MODEL_NAME=claude-sonnet-4-6
# BASE_MODEL_BASE_URL=           # optional override for compatible endpoints
```

### Internal Interface

```python
# query_engine calls by role — no awareness of specific provider
intent   = await llm_gateway.intent("分析上周华东区出库量")
sql      = await llm_gateway.text_to_sql(prompt)
insight  = await llm_gateway.base("生成洞察和决策建议", data)
```

---

## 4. Core Query Pipeline

### 9-Step Request Chain

```
User Input
   │
   ▼
[1] Intent Recognition  (Intent Model)
   ├─ data_query      → full pipeline
   ├─ definition      → answer directly from glossary
   ├─ clarify         → ask user to clarify
   ├─ fixed_workflow  → route to workflow engine
   └─ chitchat        → politely decline, suggest data-related questions
   │
   ▼
[2] Schema Retrieval
   └─ bge-m3 embedding → Qdrant top-20 → bge-reranker top-5
   │
   ▼
[3] Prompt Construction
   └─ top-5 schema + relevant few-shot examples + business rules + user question
   │
   ▼
[4] SQL Generation  (Text-to-SQL Model)
   └─ outputs SQL + confidence indication
   │
   ▼
[5] SQL Validation  (sqlglot)
   ├─ SELECT only
   ├─ table whitelist check
   ├─ block system tables (information_schema, pg_catalog, sys)
   └─ on failure → retry with error message, max 3 attempts
   │
   ▼
[6] RLS Injection
   └─ execution layer forcibly appends user permission filter conditions
   │
   ▼
[7] Query Execution
   └─ read-only connection pool + forced LIMIT 10000 + 30s timeout
   │
   ▼
[8] Result Processing
   ├─ sanity check (negative values / magnitude anomalies trigger warnings)
   ├─ secondary injection filter (filter suspected instruction patterns before passing to LLM)
   └─ chart type inference (viz module)
   │
   ▼
[9] Insight + Decision Suggestions  (Base Model)
   └─ query results + original question → natural language insight + 2-3 actionable suggestions
```

### Query Response Card Structure (Frontend)

Each query result is rendered as a message card containing:
1. **Chart** — ECharts visualization, auto-inferred type, user can switch manually
2. **Data Table** — sortable, filterable, CSV export
3. **SQL** — collapsed by default, expandable, copyable
4. **Insight** — 1-2 paragraph natural language summary
5. **Actionable Suggestions** — 2-3 decision recommendations with icons, expandable detail

### Chart Type Inference Rules (viz module)

| Query Result Characteristics | Inferred Chart Type |
|------------------------------|-------------------|
| 1 dimension + 1 time series + 1 metric | Line chart |
| 1 dimension (≤10 categories) + 1 metric | Bar chart |
| 1 dimension (>10 categories) + 1 metric | Horizontal bar chart |
| 2 metrics comparison | Dual-axis line/bar |
| Share / proportion question | Pie / donut chart |
| Single aggregated value | Big number card |
| Multi-dimensional detail | Data table only (no chart) |

---

## 5. Security

### Prompt Injection Defense

| Priority | Measure |
|----------|---------|
| Highest | Architecture-level isolation: LLM never touches DB connection directly |
| High | SQL whitelist validation via sqlglot (SELECT only, table whitelist, no system tables) |
| Medium | Filter query results before passing to LLM (strip long strings, detect instruction-like patterns) |
| Auxiliary | System prompt reinforcement: treat user input and DB results as untrusted external data |

### Access Control

RLS is enforced at the execution layer — never rely on LLM to respect permission instructions in prompts.

**Application-layer RLS injection** (for databases without native RLS):
```python
def inject_rls(sql: str, user_context: dict) -> str:
    # Wrap as subquery and append WHERE filters from user_data_scopes
    filters = [f"{k} = '{v}'" for k, v in user_context["scopes"].items()]
    if filters and user_context["role"] != "superadmin":
        sql = f"SELECT * FROM ({sql}) AS _sub WHERE {' AND '.join(filters)}"
    return sql
```

**PostgreSQL native RLS** supported for PostgreSQL datasources.

### SQL Execution Safety
- Read-only dedicated DB user per datasource
- Forced `LIMIT 10000` if not present in generated SQL
- 30-second statement timeout
- Query result sanity checks (negative values, magnitude outliers)

---

## 6. Permission Model & Database Schema

### User Roles

| Role | Data Scope | Management Access |
|------|-----------|-------------------|
| `superadmin` | Full global access | All features |
| `admin` | Assigned datasources | Schema, Knowledge, Workflows, Users, Audit |
| `analyst` | Full data (no RLS restriction) | None |
| `viewer` | RLS-restricted data scope | None |

Menu items in the sidebar are filtered by role: `viewer` sees only Chat and history; `admin`/`superadmin` see all management menus.

### PostgreSQL Tables

```sql
-- Conversations (chat history sidebar)
conversations (id, user_id, datasource_id, title, created_at, updated_at)
-- title defaults to first 30 chars of opening question, renameable

-- Audit
users            (id, email, hashed_password, role, is_active, created_at)
user_data_scopes (user_id, scope_key, scope_value)
-- e.g. user_id=5, scope_key="region", scope_value="华南"

-- Datasources
datasources (id, name, db_type,          -- postgres/mysql/clickhouse/doris
             host, port, database,
             username, encrypted_password,
             readonly_user, readonly_password,
             created_by, created_at)

-- Schema & Knowledge
schema_tables  (id, datasource_id, table_name, description, is_active)
schema_columns (id, table_id, column_name, data_type,
                description, example_values, notes)
                -- embedding stored in Qdrant; raw text stored here

knowledge_items (id, datasource_id, type,    -- rule / fewshot / glossary
                 title, content,
                 embedding_id,               -- Qdrant point id
                 created_by, updated_at)

-- Fixed Workflows
workflows (id, name, datasource_id,
           trigger_keywords,               -- JSON array
           steps,                          -- JSON step definitions
           created_by, is_active)

-- Audit (linked to conversation)
query_logs (id, conversation_id, user_id, datasource_id,
            user_question, intent,
            generated_sql, execution_ms,
            row_count, error_msg,
            created_at)
```

---

## 7. Frontend Design

### Layout (Claude/Codex-style)

```
┌──────────────┬─────────────────────────────────────┐
│  LEFT SIDEBAR│  MAIN AREA                          │
│  (260px,     │                                     │
│   collapsible│                                     │
│              │                                     │
│ [+ New Chat] │  Chat / Admin pages                 │
│              │                                     │
│ ── History ──│                                     │
│  Today       │                                     │
│  · Q: 上周...│                                     │
│  Yesterday   │                                     │
│  · Q: Q3...  │                                     │
│  ...         │                                     │
│              │                                     │
│ ── Menu ──── │                                     │
│ 💬 Chat       │                                     │
│ ⚡ Workflows  │                                     │
│ 🗄  Datasources│                                   │
│ 📋 Schema    │                                     │
│ 📚 Knowledge │                                     │
│ 👥 Users     │                                     │
│ 📜 Audit     │                                     │
│              │                                     │
│ ── Bottom ───│                                     │
│ ⚙️ Settings  │                                     │
│ 👤 Username  │                                     │
└──────────────┴─────────────────────────────────────┘
```

- Conversation history grouped by date: Today / Yesterday / Past 7 days / Earlier
- Session title: first 30 chars of user's opening question, renameable
- Management menu items visible only to `admin` / `superadmin`
- Settings: LLM provider configuration, profile

### Tech Stack

| Concern | Choice |
|---------|--------|
| Framework | React 18 + TypeScript + Vite |
| UI components | shadcn/ui + Tailwind CSS |
| State management | Zustand |
| Data fetching | TanStack Query |
| Charts | Apache ECharts (via `echarts-for-react`) |

---

## 8. Deployment

### Docker Compose

```bash
# Cloud API mode (lightest)
docker compose up -d

# With local LLM
docker compose -f docker-compose.yml -f docker-compose.vllm.yml up -d
```

`docker-compose.vllm.yml` mounts local model weights directory via volume, no model bundled in image.

### Environment Variables

```bash
# Infrastructure
POSTGRES_PASSWORD=...
REDIS_PASSWORD=...

# Security
SECRET_KEY=...          # JWT signing key
ENCRYPTION_KEY=...      # DB password encryption key

# LLM — three roles independently configured
INTENT_MODEL_PROVIDER=openai_compatible
INTENT_MODEL_BASE_URL=http://vllm:8000/v1
INTENT_MODEL_NAME=Qwen2.5-7B-Instruct

TEXT_TO_SQL_PROVIDER=openai_compatible
TEXT_TO_SQL_BASE_URL=http://vllm:8000/v1
TEXT_TO_SQL_MODEL_NAME=Qwen2.5-Coder-32B-Instruct

BASE_MODEL_PROVIDER=anthropic
BASE_MODEL_API_KEY=sk-ant-...
BASE_MODEL_NAME=claude-sonnet-4-6
```

### Repository Structure

```
chatbi/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── auth/
│   │   ├── query_engine/
│   │   ├── llm_gateway/
│   │   ├── schema_mgr/
│   │   ├── knowledge/
│   │   ├── workflow/
│   │   ├── viz/
│   │   └── audit/
│   ├── tests/
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── Dockerfile
│   └── package.json
├── docs/
│   ├── superpowers/specs/
│   ├── deployment.md
│   └── configuration.md
├── docker-compose.yml
├── docker-compose.vllm.yml
├── .env.example
├── README.md           # English (default)
├── README.zh-CN.md     # Chinese (linked from README.md)
└── LICENSE             # MIT
```

### README Structure

- `README.md` (English, default entry): links to `README.zh-CN.md` at top
- Both versions include: badges, features, quick start, architecture diagram, configuration, contributing, license
- Bottom of both READMEs: Star History chart via `star-history.com` SVG API

```markdown
## Star History
[![Star History Chart](https://api.star-history.com/svg?repos=your-github/chatbi&type=Date)](https://star-history.com/#your-github/chatbi)
```

---

## 9. Decisions Not Made (Future)

| Topic | Current Decision | Future Option |
|-------|-----------------|---------------|
| Deployment | Docker Compose single-node | Kubernetes Helm Chart |
| Decision Suggestions | LLM auto-generated from results (MVP) | Rule + LLM hybrid, or user-configurable templates |
| Fine-tuning | Not in scope | LoRA/QLoRA for Text-to-SQL model after 1000+ annotated samples |
| Supported DBs | PostgreSQL, MySQL, ClickHouse, Apache Doris | Hive, Presto, Snowflake |

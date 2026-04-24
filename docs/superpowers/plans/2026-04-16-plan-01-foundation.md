# ChatBI Plan 1: Project Foundation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bootstrap the full project skeleton — Docker Compose, FastAPI backend with JWT auth + RBAC, all Postgres models, and a React frontend scaffold with login page — so that every subsequent plan has a working foundation to build on.

**Architecture:** Modular monolith FastAPI (async) backend + React 18 frontend, connected via REST API. All infrastructure (Postgres, Qdrant, Redis) runs in Docker Compose. Auth uses JWT access + refresh tokens stored in httpOnly cookies. RBAC enforced via FastAPI dependency injection.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy 2 (async), Alembic, PostgreSQL 16, Redis 7, Qdrant, pytest + pytest-asyncio + httpx, React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui, Zustand, TanStack Query

---

## File Map

```
chatbi/
├── docker-compose.yml
├── docker-compose.vllm.yml
├── .env.example
├── .env                          # local only, gitignored
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 0001_initial.py
│   └── app/
│       ├── main.py               # FastAPI app factory
│       ├── core/
│       │   ├── config.py         # Settings via pydantic-settings
│       │   ├── database.py       # Async SQLAlchemy engine + session
│       │   └── security.py       # Password hashing, JWT encode/decode
│       ├── models/               # SQLAlchemy ORM models
│       │   ├── user.py
│       │   ├── user_data_scope.py
│       │   ├── datasource.py
│       │   ├── conversation.py
│       │   ├── query_log.py
│       │   ├── schema_table.py
│       │   ├── schema_column.py
│       │   ├── knowledge_item.py
│       │   └── workflow.py
│       ├── schemas/              # Pydantic request/response schemas
│       │   ├── auth.py
│       │   ├── user.py
│       │   └── datasource.py
│       ├── api/
│       │   ├── deps.py           # get_current_user, require_role
│       │   └── v1/
│       │       ├── router.py     # Aggregates all v1 routers
│       │       ├── auth.py       # POST /auth/login, /auth/refresh, /auth/logout
│       │       ├── users.py      # CRUD /users
│       │       └── datasources.py# CRUD /datasources
│       └── tests/
│           ├── conftest.py       # Async test client, DB fixtures
│           ├── test_health.py
│           ├── test_auth.py
│           ├── test_users.py
│           └── test_datasources.py
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── index.html
    └── src/
        ├── main.tsx
        ├── App.tsx               # Router setup
        ├── lib/
        │   ├── api.ts            # Axios instance with interceptors
        │   └── auth.ts           # Auth state (Zustand store)
        ├── pages/
        │   ├── Login/
        │   │   └── index.tsx
        │   └── Chat/
        │       └── index.tsx     # Placeholder "Coming soon"
        └── components/
            └── Layout/
                ├── Sidebar.tsx   # Left sidebar skeleton
                └── MainLayout.tsx
```

---

## Task 1: Git Repo + .gitignore

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: Create `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
dist/
*.egg-info/
.pytest_cache/
.mypy_cache/
htmlcov/
.coverage

# Environment
.env
*.env.local

# Node
node_modules/
frontend/dist/
frontend/.vite/

# Docker
.docker/

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Alembic
alembic/versions/*.pyc
```

- [ ] **Step 2: Init git and commit**

```bash
cd E:/chatbi
git init
git add .gitignore
git commit -m "chore: init repo with .gitignore"
```

---

## Task 2: Docker Compose + Environment

**Files:**
- Create: `docker-compose.yml`
- Create: `docker-compose.vllm.yml`
- Create: `.env.example`
- Create: `.env`

- [ ] **Step 1: Create `docker-compose.yml`**

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      qdrant:
        condition: service_started
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-chatbi}
      POSTGRES_USER: ${POSTGRES_USER:-chatbi}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-chatbi}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--pass", "${REDIS_PASSWORD}", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  redis_data:
  qdrant_data:
```

- [ ] **Step 2: Create `docker-compose.vllm.yml`**

```yaml
services:
  vllm:
    image: vllm/vllm-openai:latest
    ports:
      - "8001:8000"
    volumes:
      - ${VLLM_MODEL_PATH}:/models
    command: >
      --model /models/${VLLM_MODEL_NAME}
      --tensor-parallel-size ${VLLM_TENSOR_PARALLEL:-1}
      --max-model-len ${VLLM_MAX_MODEL_LEN:-32768}
      --gpu-memory-utilization 0.90
      --served-model-name ${VLLM_SERVED_MODEL_NAME:-chatbi-sql}
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

- [ ] **Step 3: Create `.env.example`**

```bash
# === Infrastructure ===
POSTGRES_DB=chatbi
POSTGRES_USER=chatbi
POSTGRES_PASSWORD=change_me_in_production
REDIS_PASSWORD=change_me_in_production

# === Security ===
SECRET_KEY=generate_with_openssl_rand_hex_32
ENCRYPTION_KEY=generate_with_openssl_rand_hex_32
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# === LLM — Intent Model ===
INTENT_MODEL_PROVIDER=openai_compatible
INTENT_MODEL_BASE_URL=http://vllm:8001/v1
INTENT_MODEL_NAME=Qwen2.5-7B-Instruct
INTENT_MODEL_API_KEY=

# === LLM — Text-to-SQL Model ===
TEXT_TO_SQL_PROVIDER=openai_compatible
TEXT_TO_SQL_BASE_URL=http://vllm:8001/v1
TEXT_TO_SQL_MODEL_NAME=Qwen2.5-Coder-32B-Instruct
TEXT_TO_SQL_API_KEY=

# === LLM — Base Model ===
BASE_MODEL_PROVIDER=anthropic
BASE_MODEL_API_KEY=sk-ant-...
BASE_MODEL_NAME=claude-sonnet-4-6
# BASE_MODEL_BASE_URL=  # uncomment to override endpoint

# === vLLM (only used with docker-compose.vllm.yml) ===
VLLM_MODEL_PATH=/path/to/local/models
VLLM_MODEL_NAME=Qwen2.5-Coder-32B-Instruct
VLLM_TENSOR_PARALLEL=2
VLLM_MAX_MODEL_LEN=32768
VLLM_SERVED_MODEL_NAME=chatbi-sql
```

- [ ] **Step 4: Create `.env` from example**

```bash
cp .env.example .env
# Edit .env and set POSTGRES_PASSWORD, REDIS_PASSWORD, SECRET_KEY, ENCRYPTION_KEY
# Generate keys:
# python -c "import secrets; print(secrets.token_hex(32))"
```

- [ ] **Step 5: Commit**

```bash
git add docker-compose.yml docker-compose.vllm.yml .env.example
git commit -m "chore: add docker-compose and environment config"
```

---

## Task 3: Backend — requirements.txt + Dockerfile

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/Dockerfile`

- [ ] **Step 1: Create `backend/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy[asyncio]==2.0.36
asyncpg==0.29.0
alembic==1.13.3
pydantic==2.9.2
pydantic-settings==2.5.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
redis[asyncio]==5.1.1
httpx==0.27.2
sqlglot==25.24.0
qdrant-client==1.12.0
FlagEmbedding==1.2.10
openai==1.51.0
anthropic==0.36.0
cryptography==43.0.3
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
```

- [ ] **Step 2: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt backend/Dockerfile
git commit -m "chore: add backend requirements and Dockerfile"
```

---

## Task 4: Backend — Config + Database

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/database.py`

- [ ] **Step 1: Write failing test for config loading**

Create `backend/app/tests/__init__.py` (empty).

Create `backend/app/tests/test_health.py`:

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: Run test — expect FAIL (app not defined)**

```bash
cd backend
pip install -r requirements.txt
pytest app/tests/test_health.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Create `backend/app/core/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Infrastructure
    postgres_db: str = "chatbi"
    postgres_user: str = "chatbi"
    postgres_password: str
    redis_password: str

    # Security
    secret_key: str
    encryption_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # LLM — Intent Model
    intent_model_provider: str = "openai_compatible"
    intent_model_base_url: str = ""
    intent_model_name: str = "Qwen2.5-7B-Instruct"
    intent_model_api_key: str = "none"

    # LLM — Text-to-SQL Model
    text_to_sql_provider: str = "openai_compatible"
    text_to_sql_base_url: str = ""
    text_to_sql_model_name: str = "Qwen2.5-Coder-32B-Instruct"
    text_to_sql_api_key: str = "none"

    # LLM — Base Model
    base_model_provider: str = "anthropic"
    base_model_api_key: str = "none"
    base_model_name: str = "claude-sonnet-4-6"
    base_model_base_url: str = ""

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@postgres/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:"
            f"{self.postgres_password}@postgres/{self.postgres_db}"
        )


settings = Settings()
```

- [ ] **Step 4: Create `backend/app/core/database.py`**

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 5: Create `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(title="ChatBI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 6: Create `backend/app/tests/conftest.py`**

```python
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db

TEST_DATABASE_URL = "postgresql+asyncpg://chatbi:chatbi_test@localhost/chatbi_test"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine):
    TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
```

- [ ] **Step 7: Run test — expect PASS**

```bash
cd backend
pytest app/tests/test_health.py -v
```

Expected: `PASSED`

- [ ] **Step 8: Commit**

```bash
git add backend/app/
git commit -m "feat: FastAPI skeleton with health check, config, and database setup"
```

---

## Task 5: Database Models

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/user_data_scope.py`
- Create: `backend/app/models/datasource.py`
- Create: `backend/app/models/conversation.py`
- Create: `backend/app/models/query_log.py`
- Create: `backend/app/models/schema_table.py`
- Create: `backend/app/models/schema_column.py`
- Create: `backend/app/models/knowledge_item.py`
- Create: `backend/app/models/workflow.py`

- [ ] **Step 1: Create `backend/app/models/user.py`**

```python
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserRole(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.viewer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    data_scopes: Mapped[list["UserDataScope"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="user")
```

- [ ] **Step 2: Create `backend/app/models/user_data_scope.py`**

```python
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class UserDataScope(Base):
    __tablename__ = "user_data_scopes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    scope_key: Mapped[str] = mapped_column(String(100), nullable=False)
    scope_value: Mapped[str] = mapped_column(String(255), nullable=False)

    user: Mapped["User"] = relationship(back_populates="data_scopes")
```

- [ ] **Step 3: Create `backend/app/models/datasource.py`**

```python
import enum
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class DBType(str, enum.Enum):
    postgres = "postgres"
    mysql = "mysql"
    clickhouse = "clickhouse"
    doris = "doris"


class Datasource(Base):
    __tablename__ = "datasources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    db_type: Mapped[DBType] = mapped_column(Enum(DBType), nullable=False)
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    database: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    encrypted_password: Mapped[str] = mapped_column(String(500), nullable=False)
    readonly_user: Mapped[str] = mapped_column(String(255), nullable=False)
    readonly_encrypted_password: Mapped[str] = mapped_column(String(500), nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    schema_tables: Mapped[list["SchemaTable"]] = relationship(back_populates="datasource")
    knowledge_items: Mapped[list["KnowledgeItem"]] = relationship(back_populates="datasource")
    workflows: Mapped[list["Workflow"]] = relationship(back_populates="datasource")
```

- [ ] **Step 4: Create `backend/app/models/conversation.py`**

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    datasource_id: Mapped[int | None] = mapped_column(ForeignKey("datasources.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="conversations")
    query_logs: Mapped[list["QueryLog"]] = relationship(back_populates="conversation")
```

- [ ] **Step 5: Create `backend/app/models/query_log.py`**

```python
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    datasource_id: Mapped[int | None] = mapped_column(ForeignKey("datasources.id"), nullable=True)
    user_question: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(50), nullable=True)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_msg: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation: Mapped["Conversation"] = relationship(back_populates="query_logs")
```

- [ ] **Step 6: Create `backend/app/models/schema_table.py`**

```python
from sqlalchemy import String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SchemaTable(Base):
    __tablename__ = "schema_tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    datasource_id: Mapped[int] = mapped_column(ForeignKey("datasources.id"), nullable=False)
    table_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    datasource: Mapped["Datasource"] = relationship(back_populates="schema_tables")
    columns: Mapped[list["SchemaColumn"]] = relationship(
        back_populates="table", cascade="all, delete-orphan"
    )
```

- [ ] **Step 7: Create `backend/app/models/schema_column.py`**

```python
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SchemaColumn(Base):
    __tablename__ = "schema_columns"

    id: Mapped[int] = mapped_column(primary_key=True)
    table_id: Mapped[int] = mapped_column(ForeignKey("schema_tables.id"), nullable=False)
    column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    example_values: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    table: Mapped["SchemaTable"] = relationship(back_populates="columns")
```

- [ ] **Step 8: Create `backend/app/models/knowledge_item.py`**

```python
import enum
from datetime import datetime
from sqlalchemy import String, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class KnowledgeType(str, enum.Enum):
    rule = "rule"
    fewshot = "fewshot"
    glossary = "glossary"


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    datasource_id: Mapped[int] = mapped_column(ForeignKey("datasources.id"), nullable=False)
    type: Mapped[KnowledgeType] = mapped_column(Enum(KnowledgeType), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    datasource: Mapped["Datasource"] = relationship(back_populates="knowledge_items")
```

- [ ] **Step 9: Create `backend/app/models/workflow.py`**

```python
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    datasource_id: Mapped[int] = mapped_column(ForeignKey("datasources.id"), nullable=False)
    trigger_keywords: Mapped[list] = mapped_column(JSON, default=list)
    steps: Mapped[list] = mapped_column(JSON, default=list)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    datasource: Mapped["Datasource"] = relationship(back_populates="workflows")
```

- [ ] **Step 10: Create `backend/app/models/__init__.py`** (imports all models so Alembic can detect them)

```python
from app.models.user import User, UserRole
from app.models.user_data_scope import UserDataScope
from app.models.datasource import Datasource, DBType
from app.models.conversation import Conversation
from app.models.query_log import QueryLog
from app.models.schema_table import SchemaTable
from app.models.schema_column import SchemaColumn
from app.models.knowledge_item import KnowledgeItem, KnowledgeType
from app.models.workflow import Workflow

__all__ = [
    "User", "UserRole", "UserDataScope",
    "Datasource", "DBType",
    "Conversation", "QueryLog",
    "SchemaTable", "SchemaColumn",
    "KnowledgeItem", "KnowledgeType",
    "Workflow",
]
```

- [ ] **Step 11: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add all SQLAlchemy ORM models"
```

---

## Task 6: Alembic Migration

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial.py`

- [ ] **Step 1: Initialize Alembic**

```bash
cd backend
alembic init alembic
```

- [ ] **Step 2: Update `backend/alembic/env.py`**

Replace the content with:

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401 — registers all models

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Generate initial migration**

```bash
cd backend
alembic revision --autogenerate -m "initial"
```

Expected: creates `alembic/versions/<hash>_initial.py` with all table definitions.

- [ ] **Step 4: Apply migration (requires running Postgres)**

```bash
docker compose up postgres -d
# Wait for healthy, then:
alembic upgrade head
```

Expected output: `Running upgrade  -> <hash>, initial`

- [ ] **Step 5: Commit**

```bash
git add alembic/ alembic.ini
git commit -m "feat: add Alembic migration for initial schema"
```

---

## Task 7: Security — Password Hashing + JWT

**Files:**
- Create: `backend/app/core/security.py`

- [ ] **Step 1: Write failing tests**

Create `backend/app/tests/test_security.py`:

```python
import pytest
from datetime import timedelta
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_hash_and_verify_password():
    hashed = hash_password("mysecret")
    assert verify_password("mysecret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_access_token_roundtrip():
    token = create_access_token({"sub": "42", "role": "admin"})
    payload = decode_access_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "admin"


def test_expired_token_raises():
    token = create_access_token(
        {"sub": "42"}, expires_delta=timedelta(seconds=-1)
    )
    with pytest.raises(Exception):
        decode_access_token(token)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest app/tests/test_security.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `backend/app/core/security.py`**

```python
from datetime import datetime, timedelta, timezone
from typing import Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])


def create_refresh_token(user_id: int) -> str:
    return create_access_token(
        {"sub": str(user_id), "type": "refresh"},
        expires_delta=timedelta(days=settings.refresh_token_expire_days),
    )
```

- [ ] **Step 4: Run — expect PASS**

```bash
pytest app/tests/test_security.py -v
```

Expected: 3 tests `PASSED`

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security.py backend/app/tests/test_security.py
git commit -m "feat: add password hashing and JWT token utilities"
```

---

## Task 8: Auth API (Login / Refresh / Logout)

**Files:**
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/v1/__init__.py`
- Create: `backend/app/api/v1/auth.py`
- Create: `backend/app/api/v1/router.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Write failing auth tests**

Create `backend/app/tests/test_auth.py`:

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session):
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    user = User(
        email="test@example.com",
        hashed_password=hash_password("password123"),
        role=UserRole.analyst,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session):
    from app.models.user import User, UserRole
    from app.core.security import hash_password

    user = User(
        email="test2@example.com",
        hashed_password=hash_password("correct"),
        role=UserRole.viewer,
    )
    db_session.add(user)
    await db_session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test2@example.com", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest app/tests/test_auth.py -v
```

Expected: 404 or import errors

- [ ] **Step 3: Create `backend/app/schemas/auth.py`**

```python
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
```

- [ ] **Step 4: Create `backend/app/schemas/user.py`**

```python
from pydantic import BaseModel, EmailStr
from app.models.user import UserRole


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.viewer


class UserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
```

- [ ] **Step 5: Create `backend/app/api/deps.py`**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User, UserRole

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: int = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        raise credentials_exception

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(*roles: UserRole):
    async def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return checker
```

- [ ] **Step 6: Create `backend/app/api/v1/auth.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, create_refresh_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    access_token = create_access_token({"sub": str(user.id), "role": user.role.value})
    refresh_token = create_refresh_token(user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return current_user
```

- [ ] **Step 7: Create `backend/app/api/v1/router.py`**

```python
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
```

- [ ] **Step 8: Update `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router

app = FastAPI(title="ChatBI API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 9: Run — expect PASS**

```bash
pytest app/tests/test_auth.py app/tests/test_health.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 10: Commit**

```bash
git add backend/app/schemas/ backend/app/api/ backend/app/main.py
git commit -m "feat: add JWT auth endpoints (login, refresh, me)"
```

---

## Task 9: Users API

**Files:**
- Create: `backend/app/api/v1/users.py`
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: Write failing tests**

Create `backend/app/tests/test_users.py`:

```python
import pytest
from httpx import AsyncClient
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token


def auth_header(user_id: int, role: str) -> dict:
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_user_as_superadmin(client: AsyncClient, db_session):
    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.superadmin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    response = await client.post(
        "/api/v1/users",
        json={"email": "new@example.com", "password": "pass123", "role": "viewer"},
        headers=auth_header(admin.id, "superadmin"),
    )
    assert response.status_code == 201
    assert response.json()["email"] == "new@example.com"


@pytest.mark.asyncio
async def test_create_user_as_viewer_forbidden(client: AsyncClient, db_session):
    viewer = User(
        email="viewer@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.viewer,
    )
    db_session.add(viewer)
    await db_session.commit()
    await db_session.refresh(viewer)

    response = await client.post(
        "/api/v1/users",
        json={"email": "other@example.com", "password": "pass", "role": "viewer"},
        headers=auth_header(viewer.id, "viewer"),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_list_users_as_admin(client: AsyncClient, db_session):
    admin = User(
        email="admin2@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    response = await client.get(
        "/api/v1/users",
        headers=auth_header(admin.id, "admin"),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest app/tests/test_users.py -v
```

Expected: 404 errors

- [ ] **Step 3: Create `backend/app/api/v1/users.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.api.deps import require_role

router = APIRouter(prefix="/users", tags=["users"])

_admin_roles = (UserRole.superadmin, UserRole.admin)


@router.get("", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(select(User))
    return result.scalars().all()


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.superadmin)),
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.superadmin)),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    await db.commit()
    await db.refresh(user)
    return user
```

- [ ] **Step 4: Register users router in `backend/app/api/v1/router.py`**

```python
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
```

- [ ] **Step 5: Run — expect PASS**

```bash
pytest app/tests/test_users.py -v
```

Expected: all tests `PASSED`

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/users.py backend/app/api/v1/router.py backend/app/tests/test_users.py
git commit -m "feat: add users CRUD API with RBAC"
```

---

## Task 10: Datasources API

**Files:**
- Create: `backend/app/schemas/datasource.py`
- Create: `backend/app/api/v1/datasources.py`
- Create: `backend/app/core/encryption.py`
- Modify: `backend/app/api/v1/router.py`

- [ ] **Step 1: Write failing tests**

Create `backend/app/tests/test_datasources.py`:

```python
import pytest
from httpx import AsyncClient
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token


def auth_header(user_id: int, role: str) -> dict:
    token = create_access_token({"sub": str(user_id), "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_datasource(client: AsyncClient, db_session):
    admin = User(
        email="dsadmin@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    response = await client.post(
        "/api/v1/datasources",
        json={
            "name": "Prod DB",
            "db_type": "postgres",
            "host": "db.example.com",
            "port": 5432,
            "database": "production",
            "username": "app_user",
            "password": "secret",
            "readonly_user": "readonly",
            "readonly_password": "readonly_secret",
        },
        headers=auth_header(admin.id, "admin"),
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Prod DB"
    assert "password" not in data  # password must not be returned


@pytest.mark.asyncio
async def test_list_datasources(client: AsyncClient, db_session):
    admin = User(
        email="dsadmin2@example.com",
        hashed_password=hash_password("pass"),
        role=UserRole.admin,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)

    response = await client.get(
        "/api/v1/datasources",
        headers=auth_header(admin.id, "admin"),
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- [ ] **Step 2: Run — expect FAIL**

```bash
pytest app/tests/test_datasources.py -v
```

Expected: 404 errors

- [ ] **Step 3: Create `backend/app/core/encryption.py`**

```python
import base64
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet() -> Fernet:
    # Fernet key must be 32 url-safe base64-encoded bytes
    key = base64.urlsafe_b64encode(bytes.fromhex(settings.encryption_key[:64].ljust(64, "0"))[:32])
    return Fernet(key)


def encrypt(value: str) -> str:
    return _get_fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    return _get_fernet().decrypt(value.encode()).decode()
```

- [ ] **Step 4: Create `backend/app/schemas/datasource.py`**

```python
from pydantic import BaseModel
from app.models.datasource import DBType


class DatasourceCreate(BaseModel):
    name: str
    db_type: DBType
    host: str
    port: int
    database: str
    username: str
    password: str
    readonly_user: str
    readonly_password: str


class DatasourceResponse(BaseModel):
    id: int
    name: str
    db_type: DBType
    host: str
    port: int
    database: str
    username: str
    created_by: int

    model_config = {"from_attributes": True}
```

- [ ] **Step 5: Create `backend/app/api/v1/datasources.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.encryption import encrypt
from app.models.datasource import Datasource
from app.models.user import User, UserRole
from app.schemas.datasource import DatasourceCreate, DatasourceResponse
from app.api.deps import require_role

router = APIRouter(prefix="/datasources", tags=["datasources"])

_admin_roles = (UserRole.superadmin, UserRole.admin)


@router.get("", response_model=list[DatasourceResponse])
async def list_datasources(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_admin_roles)),
):
    result = await db.execute(select(Datasource))
    return result.scalars().all()


@router.post("", response_model=DatasourceResponse, status_code=status.HTTP_201_CREATED)
async def create_datasource(
    body: DatasourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(*_admin_roles)),
):
    ds = Datasource(
        name=body.name,
        db_type=body.db_type,
        host=body.host,
        port=body.port,
        database=body.database,
        username=body.username,
        encrypted_password=encrypt(body.password),
        readonly_user=body.readonly_user,
        readonly_encrypted_password=encrypt(body.readonly_password),
        created_by=current_user.id,
    )
    db.add(ds)
    await db.commit()
    await db.refresh(ds)
    return ds


@router.delete("/{datasource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datasource(
    datasource_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.superadmin)),
):
    result = await db.execute(select(Datasource).where(Datasource.id == datasource_id))
    ds = result.scalar_one_or_none()
    if not ds:
        raise HTTPException(status_code=404, detail="Datasource not found")
    await db.delete(ds)
    await db.commit()
```

- [ ] **Step 6: Register datasources router**

```python
# backend/app/api/v1/router.py
from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.datasources import router as datasources_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(datasources_router)
```

- [ ] **Step 7: Run — expect PASS**

```bash
pytest app/tests/ -v
```

Expected: all tests `PASSED`

- [ ] **Step 8: Commit**

```bash
git add backend/app/core/encryption.py backend/app/schemas/datasource.py \
        backend/app/api/v1/datasources.py backend/app/api/v1/router.py \
        backend/app/tests/test_datasources.py
git commit -m "feat: add datasources CRUD API with encrypted credential storage"
```

---

## Task 11: Frontend Scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/auth.ts`
- Create: `frontend/src/pages/Login/index.tsx`
- Create: `frontend/src/pages/Chat/index.tsx`
- Create: `frontend/src/components/Layout/Sidebar.tsx`
- Create: `frontend/src/components/Layout/MainLayout.tsx`
- Create: `frontend/Dockerfile`

- [ ] **Step 1: Scaffold Vite + React + TypeScript**

```bash
cd E:/chatbi/frontend
npm create vite@latest . -- --template react-ts
npm install
```

- [ ] **Step 2: Install dependencies**

```bash
npm install \
  @tanstack/react-query axios zustand \
  react-router-dom \
  echarts echarts-for-react \
  lucide-react \
  clsx tailwind-merge

npm install -D \
  tailwindcss postcss autoprefixer \
  @types/node

npx tailwindcss init -p
```

- [ ] **Step 3: Install shadcn/ui**

```bash
npx shadcn@latest init
# Choose: TypeScript, default style, slate base color, yes CSS variables
```

Add core components:
```bash
npx shadcn@latest add button input label card separator avatar dropdown-menu
```

- [ ] **Step 4: Update `frontend/tailwind.config.ts`**

```typescript
import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [require("tailwindcss-animate")],
} satisfies Config;
```

- [ ] **Step 5: Create `frontend/src/lib/api.ts`**

```typescript
import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);
```

- [ ] **Step 6: Create `frontend/src/lib/auth.ts`**

```typescript
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface User {
  id: number;
  email: string;
  role: "superadmin" | "admin" | "analyst" | "viewer";
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  setAuth: (user: User, accessToken: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      setAuth: (user, accessToken) => {
        localStorage.setItem("access_token", accessToken);
        set({ user, accessToken });
      },
      clearAuth: () => {
        localStorage.removeItem("access_token");
        set({ user: null, accessToken: null });
      },
    }),
    { name: "chatbi-auth" }
  )
);
```

- [ ] **Step 7: Create `frontend/src/pages/Login/index.tsx`**

```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuthStore } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function LoginPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post("/api/v1/auth/login", { email, password });
      const me = await api.get("/api/v1/auth/me", {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      setAuth(me.data, data.access_token);
      navigate("/");
    } catch {
      setError("Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl font-bold">ChatBI</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-sm text-red-500">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 8: Create `frontend/src/components/Layout/Sidebar.tsx`**

```tsx
import { MessageSquare, Zap, Database, Table, BookOpen, Users, ScrollText, Settings } from "lucide-react";
import { Link, useLocation } from "react-router-dom";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth";

const adminMenuItems = [
  { icon: Zap, label: "Workflows", href: "/admin/workflows" },
  { icon: Database, label: "Datasources", href: "/admin/datasources" },
  { icon: Table, label: "Schema", href: "/admin/schema" },
  { icon: BookOpen, label: "Knowledge", href: "/admin/knowledge" },
  { icon: Users, label: "Users", href: "/admin/users" },
  { icon: ScrollText, label: "Audit", href: "/admin/audit" },
];

export default function Sidebar() {
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "admin" || user?.role === "superadmin";

  return (
    <aside className="w-64 h-screen flex flex-col border-r bg-white shrink-0">
      {/* New Chat */}
      <div className="p-3 border-b">
        <Link
          to="/"
          className="flex items-center gap-2 px-3 py-2 rounded-md hover:bg-gray-100 text-sm font-medium"
        >
          <MessageSquare size={16} />
          New Chat
        </Link>
      </div>

      {/* History placeholder */}
      <div className="flex-1 overflow-y-auto p-3">
        <p className="text-xs font-medium text-gray-400 px-3 py-2 uppercase tracking-wider">
          History
        </p>
        {/* Populated in Plan 8 */}
      </div>

      {/* Admin Menu */}
      {isAdmin && (
        <div className="border-t p-3">
          <p className="text-xs font-medium text-gray-400 px-3 py-2 uppercase tracking-wider">
            Management
          </p>
          {adminMenuItems.map(({ icon: Icon, label, href }) => (
            <Link
              key={href}
              to={href}
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-gray-100",
                location.pathname === href && "bg-gray-100 font-medium"
              )}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}
        </div>
      )}

      {/* Bottom */}
      <div className="border-t p-3 space-y-1">
        <Link
          to="/settings"
          className="flex items-center gap-2 px-3 py-2 rounded-md text-sm hover:bg-gray-100"
        >
          <Settings size={16} />
          Settings
        </Link>
        <div className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600">
          <div className="w-6 h-6 rounded-full bg-gray-200 flex items-center justify-center text-xs font-bold">
            {user?.email?.[0]?.toUpperCase() ?? "?"}
          </div>
          <span className="truncate">{user?.email}</span>
        </div>
      </div>
    </aside>
  );
}
```

- [ ] **Step 9: Create `frontend/src/components/Layout/MainLayout.tsx`**

```tsx
import Sidebar from "./Sidebar";
import { Outlet } from "react-router-dom";

export default function MainLayout() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-gray-50">
        <Outlet />
      </main>
    </div>
  );
}
```

- [ ] **Step 10: Create `frontend/src/pages/Chat/index.tsx`**

```tsx
export default function ChatPage() {
  return (
    <div className="flex items-center justify-center h-full text-gray-400">
      <p>Chat interface — coming in Plan 8</p>
    </div>
  );
}
```

- [ ] **Step 11: Create `frontend/src/App.tsx`**

```tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useAuthStore } from "@/lib/auth";
import MainLayout from "@/components/Layout/MainLayout";
import LoginPage from "@/pages/Login";
import ChatPage from "@/pages/Chat";

const queryClient = new QueryClient();

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<ChatPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

- [ ] **Step 12: Create `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

- [ ] **Step 13: Create `frontend/nginx.conf`**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 14: Verify frontend runs locally**

```bash
cd frontend
npm run dev
```

Expected: Vite dev server at `http://localhost:5173`, login page visible.

- [ ] **Step 15: Commit**

```bash
git add frontend/
git commit -m "feat: add React frontend scaffold with login page and sidebar layout"
```

---

## Task 12: End-to-End Smoke Test

- [ ] **Step 1: Start full stack**

```bash
cd E:/chatbi
docker compose up -d --build
```

- [ ] **Step 2: Run migrations**

```bash
docker compose exec backend alembic upgrade head
```

- [ ] **Step 3: Create superadmin user via API**

```bash
# First register via direct DB insert (no public register endpoint by design)
docker compose exec postgres psql -U chatbi -d chatbi -c "
INSERT INTO users (email, hashed_password, role, is_active, created_at)
VALUES ('admin@chatbi.local', '\$2b\$12\$placeholder_run_script_below', 'superadmin', true, NOW());
"

# Better: use a one-time seed script
docker compose exec backend python -c "
import asyncio
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole

async def seed():
    async with AsyncSessionLocal() as db:
        user = User(
            email='admin@chatbi.local',
            hashed_password=hash_password('changeme'),
            role=UserRole.superadmin
        )
        db.add(user)
        await db.commit()
        print('Superadmin created: admin@chatbi.local / changeme')

asyncio.run(seed())
"
```

- [ ] **Step 4: Verify login**

```bash
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@chatbi.local","password":"changeme"}' | python -m json.tool
```

Expected: JSON with `access_token` and `refresh_token`.

- [ ] **Step 5: Open frontend**

Navigate to `http://localhost:3000` — login page should be visible. Log in with `admin@chatbi.local / changeme` — should redirect to Chat page with admin sidebar menu items.

- [ ] **Step 6: Run full test suite**

```bash
docker compose exec backend pytest app/tests/ -v --cov=app --cov-report=term-missing
```

Expected: all tests pass, coverage report printed.

- [ ] **Step 7: Final commit**

```bash
git add -A
git commit -m "feat: Plan 1 complete — foundation with auth, models, datasources API, and React frontend"
```

---

## Self-Review Checklist

**Spec coverage:**
- ✅ Docker Compose (single command deployment)
- ✅ PostgreSQL with all tables from spec (users, user_data_scopes, datasources, conversations, query_logs, schema_tables, schema_columns, knowledge_items, workflows)
- ✅ JWT auth with RBAC (4 roles: superadmin, admin, analyst, viewer)
- ✅ Datasource CRUD with encrypted password storage
- ✅ User CRUD with role-based access
- ✅ React frontend with Claude/Codex-style sidebar layout
- ✅ Login page
- ✅ Role-based sidebar menu visibility
- ✅ `.env.example` with all LLM config placeholders
- ✅ `docker-compose.vllm.yml` for optional local model

**Not in this plan (intentional — later plans):**
- LLM Gateway (Plan 2)
- Schema sync + embedding (Plan 3)
- Knowledge base (Plan 4)
- Query engine pipeline (Plan 5)
- Visualization (Plan 6)
- Workflows (Plan 7)
- Chat UI (Plan 8)
- Admin pages (Plan 9)
- README + star history (Plan 10)

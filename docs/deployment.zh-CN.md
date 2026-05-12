# ChatBI 部署指南

English: [deployment.md](./deployment.md)

## 目录

- [部署模式](#部署模式)
- [轻量模式（无需 Docker）](#轻量模式无需-docker)
- [生产模式（Docker Compose）](#生产模式docker-compose)
- [环境变量](#环境变量)
- [数据库迁移](#数据库迁移)
- [LLM 配置](#llm-配置)
- [使用 vLLM 部署本地 LLM](#使用-vllm-部署本地-llm)
- [生产检查清单](#生产检查清单)
- [故障排查](#故障排查)

---

## 部署模式

ChatBI 支持两种部署模式：

| | 轻量模式 | 生产模式 |
|---|---|---|
| **适用场景** | 开发、试用、小团队 | 生产环境、企业部署 |
| **数据库** | SQLite（自动创建） | PostgreSQL 16 |
| **向量存储** | 内存（numpy） | Qdrant |
| **缓存** | 无 | Redis（可选） |
| **前置依赖** | Python 3.11+、Node.js 18+ | Docker 24+、Docker Compose v2 |
| **部署耗时** | 约 2 分钟 | 约 5 分钟 |
| **数据持久化** | SQLite 文件（`data/chatbi.db`） | Docker volumes |

通过 `.env` 中的 `DB_MODE=sqlite` 或 `DB_MODE=postgres` 切换模式。

---

## 轻量模式（无需 Docker）

**零外部依赖。** 轻量模式使用 SQLite 存储应用数据，并使用基于 numpy 余弦相似度的内存向量库。适合本地开发、演示和小规模使用。

### 前置依赖

| 依赖 | 版本 |
|---|---|
| Python | 3.11+ |
| Node.js | 18+ |
| LLM API Key | OpenAI 或 Anthropic |

### 快速开始

```bash
git clone https://github.com/jingw2/chatbi.git
cd chatbi

# Linux / macOS
chmod +x start.sh && ./start.sh

# Windows
.\start.ps1
```

首次运行脚本时会：

1. 创建 `.env`，并自动生成 `SECRET_KEY` 和 `ENCRYPTION_KEY`
2. 提示你添加 LLM API Key，然后退出
3. 第二次运行时（编辑 `.env` 后）：创建 Python venv、安装依赖，并启动后端和前端

```text
前端: http://localhost:5173
后端: http://localhost:8000
登录: admin@chatbi.local / admin123
```

### 工作方式

- **数据库**：SQLite 文件位于 `data/chatbi.db`（自动创建），使用 WAL 模式支持并发读取。
- **向量存储**：基于 numpy 的内存向量库。数据只在后端进程运行期间存在，重启后需要重新索引 embedding。
- **管理员账号**：首次启动自动创建（邮箱：`admin@chatbi.local`，密码：`admin123`）。
- **数据表**：根据 ORM metadata 自动创建，无需 Alembic 迁移。

### 手动启动（不使用脚本）

```bash
# 后端
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 设置环境变量
export DB_MODE=sqlite
export SQLITE_PATH=data/chatbi.db
export SECRET_KEY=$(openssl rand -hex 32)
export ENCRYPTION_KEY=$(openssl rand -hex 32)
# ... 添加 LLM API Key ...

uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（另开一个终端）
cd frontend
npm install
npm run dev
```

### 轻量模式限制

- **向量库不持久化**：重启后 embedding 会丢失，需要重新索引
- **不适合水平扩展**：SQLite 同一时间只支持一个写入者
- **没有 Redis 缓存**：所有请求直接访问数据库
- 更适合 1 到 5 个并发用户的小团队

---

## 生产模式（Docker Compose）

生产模式使用 PostgreSQL、Qdrant 和 Redis，适合需要完整持久化和可扩展性的部署。

### 前置依赖

| 依赖 | 版本 |
|---|---|
| Docker | 24+ |
| Docker Compose | v2（Docker Desktop 已内置） |
| NVIDIA GPU + 驱动 | 可选，仅本地 vLLM 需要 |

### 快速开始

```bash
git clone https://github.com/jingw2/chatbi.git
cd chatbi

# 1. 配置
cp .env.example .env
# 编辑 .env：设置 DB_MODE=postgres、密码、API Key

# 2. 启动
docker compose up -d

# 3. 迁移数据库
docker compose exec backend alembic upgrade head

# 4. 创建管理员
docker compose exec backend python -m app.scripts.create_admin

# 5. 访问 http://localhost:3000
```

## 环境变量

### 模式选择

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `DB_MODE` | 否 | `postgres` | 轻量模式使用 `sqlite`，生产模式使用 `postgres` |
| `SQLITE_PATH` | 否 | `data/chatbi.db` | SQLite 数据库路径，仅轻量模式使用 |

### 基础设施（仅生产模式）

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `POSTGRES_DB` | 否 | `chatbi` | PostgreSQL 数据库名 |
| `POSTGRES_USER` | 否 | `chatbi` | PostgreSQL 用户名 |
| `POSTGRES_PASSWORD` | **是** | - | PostgreSQL 密码 |
| `POSTGRES_HOST` | 否 | `postgres` | PostgreSQL 主机名 |
| `REDIS_PASSWORD` | **是** | - | Redis 密码 |
| `QDRANT_URL` | 否 | `http://qdrant:6333` | Qdrant 向量库地址 |

### 安全配置

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `SECRET_KEY` | **是** | - | JWT 签名密钥。可用 `openssl rand -hex 32` 生成 |
| `ENCRYPTION_KEY` | **是** | - | 数据库密码加密密钥。可用 `openssl rand -hex 32` 生成 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 否 | `30` | JWT access token 有效期 |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 否 | `7` | refresh token 有效期 |

### LLM - 意图识别模型

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `INTENT_MODEL_PROVIDER` | 否 | `openai_compatible` | `openai_compatible` 或 `anthropic` |
| `INTENT_MODEL_BASE_URL` | 否 | - | API 地址，例如本地 vLLM 的 `http://vllm:8001/v1` |
| `INTENT_MODEL_NAME` | 否 | `Qwen2.5-7B-Instruct` | 模型名称 |
| `INTENT_MODEL_API_KEY` | 否 | - | API Key；本地 vLLM 可填任意非空字符串 |

### LLM - Text-to-SQL 模型

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `TEXT_TO_SQL_PROVIDER` | 否 | `openai_compatible` | `openai_compatible` 或 `anthropic` |
| `TEXT_TO_SQL_BASE_URL` | 否 | - | API 地址 |
| `TEXT_TO_SQL_MODEL_NAME` | 否 | `Qwen2.5-Coder-32B-Instruct` | 模型名称 |
| `TEXT_TO_SQL_API_KEY` | 否 | - | API Key |

### LLM - 基础模型

| 变量 | 必填 | 默认值 | 说明 |
|---|---|---|---|
| `BASE_MODEL_PROVIDER` | 否 | `anthropic` | `openai_compatible` 或 `anthropic` |
| `BASE_MODEL_API_KEY` | 否 | - | API Key；使用 Anthropic 时需要配置 |
| `BASE_MODEL_NAME` | 否 | `claude-sonnet-4-6` | 模型名称 |
| `BASE_MODEL_BASE_URL` | 否 | - | 自定义 API 地址 |

## 数据库迁移

ChatBI 使用 Alembic 管理数据库 schema 迁移。

```bash
# 应用所有待执行迁移
docker compose exec backend alembic upgrade head

# 查看当前迁移版本
docker compose exec backend alembic current

# 模型变更后生成新迁移（仅开发时使用）
docker compose exec backend alembic revision --autogenerate -m "description"
```

## LLM 配置

### 方案 A：全部使用云 API（最简单）

三个模型角色都使用云服务，无需 GPU。

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

### 方案 B：本地 LLM + 云 API（推荐）

用 vLLM 在本地运行意图识别和 SQL 模型，用 Anthropic 生成洞察。

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

然后使用 vLLM compose 文件启动：

```bash
docker compose -f docker-compose.yml -f docker-compose.vllm.yml up -d
```

## 使用 vLLM 部署本地 LLM

### 要求

- NVIDIA GPU，并有足够显存（32B 模型通常需要约 40GB，可跨多卡）
- 已安装 NVIDIA Container Toolkit
- 模型权重已下载到本地

### vLLM 环境变量

| 变量 | 默认值 | 说明 |
|---|---|---|
| `VLLM_MODEL_PATH` | - | 存放模型权重的本地目录 |
| `VLLM_MODEL_NAME` | - | `VLLM_MODEL_PATH` 下的模型目录名 |
| `VLLM_TENSOR_PARALLEL` | `1` | Tensor parallel 使用的 GPU 数量 |
| `VLLM_MAX_MODEL_LEN` | `32768` | 最大上下文长度 |
| `VLLM_SERVED_MODEL_NAME` | `chatbi-sql` | vLLM API 暴露的模型名称 |

### 下载模型

```bash
# 安装 huggingface-cli
pip install huggingface_hub

# 下载模型
huggingface-cli download Qwen/Qwen2.5-7B-Instruct --local-dir /models/Qwen2.5-7B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-32B-Instruct --local-dir /models/Qwen2.5-Coder-32B-Instruct
```

## 生产检查清单

- [ ] 为 `POSTGRES_PASSWORD`、`REDIS_PASSWORD`、`SECRET_KEY`、`ENCRYPTION_KEY` 设置强随机值，且每个环境唯一
- [ ] 移除后端启动命令中的 `--reload`（Dockerfile CMD 中已按生产方式处理）
- [ ] 移除 `docker-compose.yml` 里的 `volumes: ./backend:/app` 挂载（仅开发需要）
- [ ] 在 3000 端口前配置 HTTPS 反向代理（Nginx、Traefik 或 Caddy）
- [ ] 将 `backend/app/main.py` 中的 `allow_origins` 改为实际域名，不要只保留 `localhost:3000`
- [ ] 定期备份 PostgreSQL 数据卷
- [ ] 监控 Qdrant 存储卷增长
- [ ] 为后端容器配置日志采集

## 故障排查

### 后端无法启动

```bash
# 查看日志
docker compose logs backend

# 常见问题：
# - PostgreSQL 尚未就绪。后端已依赖 healthcheck，但仍可手动确认：
docker compose exec postgres pg_isready -U chatbi
```

### 数据库迁移报错

```bash
# 如果迁移状态不一致，先查看当前版本：
docker compose exec backend alembic current

# 查看迁移历史：
docker compose exec backend alembic history
```

### vLLM GPU 问题

```bash
# 确认 NVIDIA runtime 可用：
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# 查看 vLLM 日志：
docker compose -f docker-compose.yml -f docker-compose.vllm.yml logs vllm
```

### 前端空白页

```bash
# 确认 nginx 代理配置：
docker compose exec frontend cat /etc/nginx/conf.d/default.conf

# 检查后端健康状态：
curl http://localhost:8000/health
```

### 轻量模式：后端无法启动

```bash
# 检查 Python 版本（需要 3.11+）：
python --version

# 确认 .env 有必需配置：
grep -E "^(DB_MODE|SECRET_KEY|ENCRYPTION_KEY)" .env

# 确认 SQLite data 目录可写：
ls -la data/

# 检查健康接口：
curl http://localhost:8000/health
# 应返回：{"status": "ok", "mode": "lite"}
```

### 轻量模式：出现 "no such table" 错误

后端启动时会自动建表。如果看到 table 不存在的错误，通常说明启动过程静默失败了。检查后端输出里是否有 import error 或依赖缺失：

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python -c "from app.core.database import Base; import app.models; print('Models OK')"
```

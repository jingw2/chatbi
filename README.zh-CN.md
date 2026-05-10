<div align="center">
  <h1>ChatBI</h1>
  <p><strong>开源对话式商业智能平台</strong></p>
  <p>用自然语言提问，获得 SQL、图表、洞察和可操作的决策建议 —— 全在一次对话中完成。</p>

  <p>
    <a href="./README.md">English</a> •
    <a href="#快速开始轻量模式">快速开始</a> •
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
- **两种部署模式** —— 轻量模式（零 Docker 依赖）用于开发试用，生产模式（Docker Compose）用于正式部署

## 架构

```
┌──────────────────────────────────────────────────────────────┐
│                    前端 (React + Vite)                        │
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
└──────────────────────────────────────────────────────────────┘
        │                                           │
   轻量模式:                                    生产模式:
   SQLite + 内存向量库                       Pg16 + Qdrant + Redis
```

## 快速开始（轻量模式）

**无需 Docker。** 只需 Python 3.11+ 和 Node.js 18+。

```bash
git clone https://github.com/jingw2/chatbi.git
cd chatbi

# Linux / macOS
chmod +x start.sh && ./start.sh

# Windows
.\start.ps1
```

首次运行时，脚本会自动创建 `.env` 并生成安全密钥。**编辑 `.env` 添加你的 LLM API Key**，然后重新运行。

```
前端: http://localhost:5173
后端: http://localhost:8000
登录: admin@chatbi.local / admin123
```

轻量模式使用 **SQLite** + **内存向量库** —— 零外部依赖。

## 生产部署（Docker Compose）

使用 PostgreSQL、Qdrant 和 Redis 的生产环境：

```bash
cp .env.example .env
# 编辑 .env: 设置 DB_MODE=postgres、密码、API Key

docker compose up -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.create_admin
```

访问 [http://localhost:3000](http://localhost:3000)。详见 [docs/deployment.md](./docs/deployment.md)。

## 配置

ChatBI 使用三个独立配置的 LLM 角色：

| 角色 | 用途 | 推荐模型 |
|------|------|----------|
| **意图识别** | 分类用户问题 | Qwen2.5-7B-Instruct（本地）或 gpt-4o-mini |
| **Text-to-SQL** | 将自然语言转换为 SQL | Qwen2.5-Coder-32B-Instruct（本地）或 gpt-4o |
| **基础模型** | 洞察、建议、通用回复 | Claude Sonnet（云端） |

每个角色支持 `openai_compatible` 或 `anthropic` 提供商。完整环境变量参考请查看 [docs/deployment.md](./docs/deployment.md)。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.11、FastAPI、SQLAlchemy 2.0、asyncpg / aiosqlite |
| 前端 | React 19、TypeScript、Vite、Tailwind CSS、shadcn/ui |
| 状态管理 | Zustand（客户端）、TanStack Query（服务端） |
| 图表 | Apache ECharts（echarts-for-react） |
| 数据库 | PostgreSQL 16（生产）/ SQLite（轻量） |
| 向量存储 | Qdrant（生产）/ 内存（轻量） |
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

[![Star History Chart](https://api.star-history.com/svg?repos=jingw2/chatbi&type=Date)](https://star-history.com/#jingw2/chatbi)

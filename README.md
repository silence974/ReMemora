# ReMemora

ReMemora 是一个 Chat 项目 monorepo，当前包含：

- `apps/web`：Next.js 16 前端
- `apps/api`：FastAPI 后端（已提供最小 `/ping` 接口）
- `infra`：容器编排与部署文件
- `packages`：共享包目录（预留）

## 1. 目录结构

```text
ReMemora/
├─ apps/
│  ├─ api/
│  │  ├─ Dockerfile
│  │  ├─ main.py
│  │  └─ pyproject.toml
│  └─ web/
│     ├─ Dockerfile
│     ├─ app/
│     └─ package.json
├─ infra/
│  └─ docker-compose.dev.yml
├─ .dockerignore
├─ .env.example
├─ pnpm-lock.yaml
└─ pnpm-workspace.yaml
```

## 2. 环境要求

- Node.js `>=20.9.0`
- pnpm `>=10`
- Python `>=3.12`
- Docker + Docker Compose（容器化部署）

## 3. 本地开发

### 3.1 初始化

```bash
cp .env.example .env
corepack enable
pnpm install
```

如果你使用 `nvm`：

```bash
nvm use
```

### 3.2 启动前端

```bash
pnpm -C apps/web dev
```

访问 `http://localhost:3000`。

### 3.3 启动后端

```bash
cd apps/api
uv run python main.py
```

后端默认监听 `http://localhost:8152`（容器内仍为 `8000`）。

可用接口：

- `GET /`：基础服务信息
- `GET /ping`：探测 API / PostgreSQL / Redis

`/ping` 的行为：

- PostgreSQL + Redis 都可用时返回 `200`
- 任一不可用时返回 `503`，并附带具体错误信息

## 4. 容器化部署（已落地）

编排文件：`infra/docker-compose.dev.yml`

包含 4 个服务：

- `web`：Next.js 服务（端口 `3000`）
- `api`：FastAPI 服务（宿主机端口 `8152`，容器内 `8000`）
- `db`：PostgreSQL 16（端口 `5432`）
- `redis`：Redis 7（端口 `6379`）

`api` 容器启动流程为：`uv sync` -> `uv run uvicorn ... --reload`。  
同时挂载宿主机 `apps/api` 目录到容器内，所以你在本地改动 Python 代码会自动热更新生效。
为兼容部分主机环境的容器网络限制，`api` 默认通过 `host.docker.internal` 访问 PostgreSQL/Redis。

### 4.1 启动

在仓库根目录执行：

```bash
docker compose -f infra/docker-compose.dev.yml up --build -d
```

### 4.2 查看状态与日志

```bash
docker compose -f infra/docker-compose.dev.yml ps
docker compose -f infra/docker-compose.dev.yml logs -f api
```

### 4.3 停止并清理

```bash
docker compose -f infra/docker-compose.dev.yml down
```

如果你要连数据卷一起清理：

```bash
docker compose -f infra/docker-compose.dev.yml down -v
```

## 5. 维护指南

### 5.1 代码检查

前端：

```bash
pnpm -C apps/web lint
pnpm -C apps/web build
```

后端：

```bash
python3 -m py_compile apps/api/main.py
```

### 5.2 依赖维护

前端：

```bash
pnpm -C apps/web outdated
pnpm -C apps/web up
```

后端：

```bash
cd apps/api
uv sync
```

### 5.3 提交前建议

- 确认 `README` 与实际命令一致
- 新增环境变量时同步更新 `.env.example`
- 运行至少一次前后端基础检查

## 6. 环境变量

请基于 `.env.example` 配置。核心变量：

- `NEXT_PUBLIC_API_BASE_URL`
- `POSTGRES_HOST` / `POSTGRES_PORT` / `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB`
- `REDIS_URL`

## 7. 常见问题

### Q1: `pnpm build` 报 Node 版本不满足

Next.js 16 需要 Node `>=20.9.0`。

```bash
nvm install 20
nvm use 20
```

### Q2: `/ping` 返回 503

说明 API 能运行，但 DB 或 Redis 连接失败。优先检查：

- `db` / `redis` 容器是否 `healthy`
- `.env` 中数据库与 Redis 地址是否正确
- 端口是否被占用

### Q3: `load metadata for docker.io/library/python:3.12-slim` 超时

通常是当前 buildx builder 使用了 `docker-container` 驱动并尝试访问远端 registry。  
切回本地 `docker` builder 后重试：

```bash
docker buildx use default
docker compose -f infra/docker-compose.dev.yml build api --pull=false
```

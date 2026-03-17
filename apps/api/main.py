import asyncio
import os
from typing import Any

import asyncpg
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

app = FastAPI(title="ReMemora API")


def _env(name: str, default: str) -> str:
    return os.getenv(name, default).strip() or default


def build_database_url() -> str:
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit

    user = _env("POSTGRES_USER", "postgres")
    password = _env("POSTGRES_PASSWORD", "postgres")
    host = _env("POSTGRES_HOST", "db")
    port = _env("POSTGRES_PORT", "5432")
    db = _env("POSTGRES_DB", "rememora")
    return f"postgresql://{user}:{password}@{host}:{port}/{db}"


def build_redis_url() -> str:
    return _env("REDIS_URL", "redis://redis:6379/0")


async def check_postgres() -> dict[str, Any]:
    try:
        connection = await asyncpg.connect(build_database_url(), timeout=2)
        try:
            await connection.execute("SELECT 1")
        finally:
            await connection.close()
    except Exception as exc:
        return {"ok": False, "error": str(exc)}

    return {"ok": True}


async def check_redis() -> dict[str, Any]:
    client = Redis.from_url(
        build_redis_url(),
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )
    try:
        pong = await client.ping()
        if not pong:
            return {"ok": False, "error": "unexpected ping response"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    finally:
        await client.aclose()

    return {"ok": True}


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "ReMemora API", "status": "running"}


@app.get("/ping")
async def ping() -> JSONResponse:
    postgres, redis = await asyncio.gather(check_postgres(), check_redis())
    all_ok = postgres["ok"] and redis["ok"]

    body = {
        "status": "ok" if all_ok else "degraded",
        "checks": {
            "postgres": postgres,
            "redis": redis,
        },
    }
    return JSONResponse(status_code=200 if all_ok else 503, content=body)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=_env("API_HOST", "0.0.0.0"),
        port=int(_env("API_PORT", "8000")),
        reload=_env("API_RELOAD", "false").lower() == "true",
    )

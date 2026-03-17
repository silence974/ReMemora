FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /workspace/apps/api

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir uv

COPY apps/api/pyproject.toml ./pyproject.toml
COPY apps/api/README.md ./README.md

# Prime dependency environment in image layer for faster first startup.
RUN uv sync

COPY apps/api/ ./

EXPOSE 8000

CMD ["sh", "-c", "uv sync && uv run uvicorn main:app --host ${API_HOST:-0.0.0.0} --port ${API_PORT:-8000} --reload"]

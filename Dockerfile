FROM python:3.14-slim AS base

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY README.md ./
RUN uv sync --frozen --no-dev

ENV ECOM_AGENT_GRPC_HOST=0.0.0.0
ENV ECOM_AGENT_GRPC_PORT=50051
EXPOSE 50051

ENTRYPOINT ["uv", "run", "python", "-m", "ecom_agent.server"]

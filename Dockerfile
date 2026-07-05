FROM python:3.14-slim AS base

RUN pip install --no-cache-dir uv

WORKDIR /app

# BSR-hosted bitgn deps need buf.build auth. The buf_netrc secret is mounted at
# ~/.netrc for the duration of each uv sync that resolves them.
COPY pyproject.toml uv.lock ./
RUN --mount=type=secret,id=buf_netrc,target=/root/.netrc \
    uv sync --frozen --no-dev --no-install-project

COPY proto ./proto
COPY src ./src
COPY README.md Makefile ./

# Generate the agent gRPC stubs into src (they are gitignored, not vendored).
RUN uv run --no-project --with grpcio-tools python -m grpc_tools.protoc \
    -I proto \
    --python_out=src \
    --grpc_python_out=src \
    --pyi_out=src \
    proto/ecom_agent/v1/agent.proto

RUN --mount=type=secret,id=buf_netrc,target=/root/.netrc \
    uv sync --frozen --no-dev

ENV ECOM_AGENT_GRPC_HOST=0.0.0.0
ENV ECOM_AGENT_GRPC_PORT=50051
EXPOSE 50051

ENTRYPOINT ["uv", "run", "python", "-m", "ecom_agent.server"]

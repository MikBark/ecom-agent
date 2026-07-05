from collections import deque
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import grpc
import pytest_asyncio
from bitgn.vm.ecom import ecom_pb2, ecom_pb2_grpc
from pydantic import BaseModel

from ecom_agent.agent.llm import LLMClient, Message, SchemaT
from ecom_agent.health import build_health_servicer, mark_serving, register_health_service
from ecom_agent.observability import Observability
from ecom_agent.server import AGENT_SERVICE_FULL_NAME
from ecom_agent.service import AgentServicer
from ecom_agent.v1 import agent_pb2_grpc


class FakeEcomRuntimeServicer(ecom_pb2_grpc.EcomRuntimeServicer):
    """In-memory EcomRuntime used to test clients/servicers without a real Playground."""

    async def Read(
        self,
        request: ecom_pb2.ReadRequest,
        context: grpc.aio.ServicerContext[ecom_pb2.ReadRequest, ecom_pb2.ReadResponse],
    ) -> ecom_pb2.ReadResponse:
        return ecom_pb2.ReadResponse(path=request.path, content="fake content")

    async def Stat(
        self,
        request: ecom_pb2.StatRequest,
        context: grpc.aio.ServicerContext[ecom_pb2.StatRequest, ecom_pb2.StatResponse],
    ) -> ecom_pb2.StatResponse:
        return ecom_pb2.StatResponse(
            path=request.path, kind=ecom_pb2.NODE_KIND_FILE, writable=True
        )

    async def Tree(
        self,
        request: ecom_pb2.TreeRequest,
        context: grpc.aio.ServicerContext[ecom_pb2.TreeRequest, ecom_pb2.TreeResponse],
    ) -> ecom_pb2.TreeResponse:
        root = ecom_pb2.TreeResponse.Entry(name="/", kind=ecom_pb2.NODE_KIND_DIR)
        return ecom_pb2.TreeResponse(root=root)

    async def List(
        self,
        request: ecom_pb2.ListRequest,
        context: grpc.aio.ServicerContext[ecom_pb2.ListRequest, ecom_pb2.ListResponse],
    ) -> ecom_pb2.ListResponse:
        entry = ecom_pb2.ListResponse.Entry(
            name="a.txt", path=f"{request.path}/a.txt", kind=ecom_pb2.NODE_KIND_FILE
        )
        return ecom_pb2.ListResponse(path=request.path, entries=[entry])

    async def Find(
        self,
        request: ecom_pb2.FindRequest,
        context: grpc.aio.ServicerContext[ecom_pb2.FindRequest, ecom_pb2.FindResponse],
    ) -> ecom_pb2.FindResponse:
        return ecom_pb2.FindResponse(paths=[f"/{request.name}"])

    async def Search(
        self,
        request: ecom_pb2.SearchRequest,
        context: grpc.aio.ServicerContext[
            ecom_pb2.SearchRequest, ecom_pb2.SearchResponse
        ],
    ) -> ecom_pb2.SearchResponse:
        match = ecom_pb2.SearchResponse.Match(
            path="/a.txt", line=1, line_text=request.pattern
        )
        return ecom_pb2.SearchResponse(matches=[match])

    async def Exec(
        self,
        request: ecom_pb2.ExecRequest,
        context: grpc.aio.ServicerContext[ecom_pb2.ExecRequest, ecom_pb2.ExecResponse],
    ) -> ecom_pb2.ExecResponse:
        return ecom_pb2.ExecResponse(exit_code=0, stdout=request.path, stderr="")

    async def Write(
        self,
        request: ecom_pb2.WriteRequest,
        context: grpc.aio.ServicerContext[ecom_pb2.WriteRequest, ecom_pb2.WriteResponse],
    ) -> ecom_pb2.WriteResponse:
        return ecom_pb2.WriteResponse(path=request.path)

    async def Delete(
        self,
        request: ecom_pb2.DeleteRequest,
        context: grpc.aio.ServicerContext[
            ecom_pb2.DeleteRequest, ecom_pb2.DeleteResponse
        ],
    ) -> ecom_pb2.DeleteResponse:
        return ecom_pb2.DeleteResponse()


@pytest_asyncio.fixture
async def fake_env_server() -> AsyncIterator[str]:
    server = grpc.aio.server()
    ecom_pb2_grpc.add_EcomRuntimeServicer_to_server(  # type: ignore[no-untyped-call]
        FakeEcomRuntimeServicer(), server
    )
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()
    try:
        yield f"127.0.0.1:{port}"
    finally:
        await server.stop(None)


class FakeLLMClient:
    """Scripted LLMClient: returns queued responses keyed by requested schema type."""

    def __init__(self, responses: dict[type[BaseModel], deque[BaseModel]]) -> None:
        self._responses = responses
        self.calls: list[list[Message]] = []

    async def complete_structured(
        self, *, system_prompt: str, messages: list[Message], schema: type[SchemaT]
    ) -> SchemaT:
        del system_prompt
        self.calls.append(list(messages))
        parsed = self._responses[schema].popleft()
        assert isinstance(parsed, schema)
        return parsed


@asynccontextmanager
async def start_agent_server(llm_client: LLMClient) -> AsyncIterator[str]:
    """Assemble a real AgentService + health server, mirroring server.py's wiring."""
    server = grpc.aio.server()
    agent_pb2_grpc.add_AgentServiceServicer_to_server(  # type: ignore[no-untyped-call]
        AgentServicer(llm_client, Observability("off")), server
    )

    health_servicer = build_health_servicer()
    register_health_service(server, health_servicer)
    mark_serving(health_servicer, "")
    mark_serving(health_servicer, AGENT_SERVICE_FULL_NAME)

    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()
    try:
        yield f"127.0.0.1:{port}"
    finally:
        await server.stop(None)

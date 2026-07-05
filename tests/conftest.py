from collections.abc import AsyncIterator

import grpc
import pytest_asyncio

from ecom_agent.v1 import ecom_env_pb2, ecom_env_pb2_grpc


class FakeEcomEnvServicer(ecom_env_pb2_grpc.EcomEnvServicer):
    """In-memory EcomEnv used to test clients/servicers without a real Playground."""

    async def Read(
        self,
        request: ecom_env_pb2.ReadRequest,
        context: grpc.aio.ServicerContext[ecom_env_pb2.ReadRequest, ecom_env_pb2.ReadResponse],
    ) -> ecom_env_pb2.ReadResponse:
        return ecom_env_pb2.ReadResponse(path=request.path, content="fake content")

    async def Stat(
        self,
        request: ecom_env_pb2.StatRequest,
        context: grpc.aio.ServicerContext[ecom_env_pb2.StatRequest, ecom_env_pb2.StatResponse],
    ) -> ecom_env_pb2.StatResponse:
        return ecom_env_pb2.StatResponse(
            path=request.path, kind=ecom_env_pb2.NODE_KIND_FILE, writable=True
        )

    async def Tree(
        self,
        request: ecom_env_pb2.TreeRequest,
        context: grpc.aio.ServicerContext[ecom_env_pb2.TreeRequest, ecom_env_pb2.TreeResponse],
    ) -> ecom_env_pb2.TreeResponse:
        root = ecom_env_pb2.Entry(name="/", path="/", kind=ecom_env_pb2.NODE_KIND_DIR)
        return ecom_env_pb2.TreeResponse(root=root)


@pytest_asyncio.fixture
async def fake_env_server() -> AsyncIterator[str]:
    server = grpc.aio.server()
    ecom_env_pb2_grpc.add_EcomEnvServicer_to_server(  # type: ignore[no-untyped-call]
        FakeEcomEnvServicer(), server
    )
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()
    try:
        yield f"127.0.0.1:{port}"
    finally:
        await server.stop(None)

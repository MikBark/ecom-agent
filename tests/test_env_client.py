import grpc
import pytest

from ecom_agent.agent.env_client import EcomEnvClient
from ecom_agent.v1 import ecom_env_pb2, ecom_env_pb2_grpc


async def test_fake_server_responds_to_stat(fake_env_server: str) -> None:
    async with grpc.aio.insecure_channel(fake_env_server) as channel:
        stub = ecom_env_pb2_grpc.EcomEnvStub(channel)  # type: ignore[no-untyped-call]
        response = await stub.Stat(ecom_env_pb2.StatRequest(path="/a.txt"))
        assert response.kind == ecom_env_pb2.NODE_KIND_FILE
        assert response.writable is True


def test_env_client_constructs_without_connecting(fake_env_server: str) -> None:
    channel = grpc.aio.insecure_channel(fake_env_server)
    client = EcomEnvClient(channel, playground_id="pg-1")
    assert client._playground_id == "pg-1"


async def test_env_client_methods_are_unimplemented_stubs(fake_env_server: str) -> None:
    channel = grpc.aio.insecure_channel(fake_env_server)
    client = EcomEnvClient(channel, playground_id="pg-1")
    stub_calls = (
        lambda: client.read("/a.txt"),
        lambda: client.read_silent("/a.txt"),
        lambda: client.list_dir("/"),
        lambda: client.tree(),
        lambda: client.find("a.txt"),
        lambda: client.search("pattern"),
        lambda: client.stat("/a.txt"),
        lambda: client.exec("/bin/sql"),
        lambda: client.write("/a.txt", "content"),
        lambda: client.delete("/a.txt"),
        lambda: client.context(),
    )
    for call in stub_calls:
        with pytest.raises(NotImplementedError):
            await call()
    await channel.close()

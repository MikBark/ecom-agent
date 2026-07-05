from unittest.mock import AsyncMock, MagicMock, patch

import grpc
import pytest
from bitgn.vm.ecom import ecom_pb2, ecom_pb2_grpc

from ecom_agent.agent.runtime_client import EcomRuntimeClient


async def test_fake_server_responds_to_stat(fake_env_server: str) -> None:
    async with grpc.aio.insecure_channel(fake_env_server) as channel:
        stub = ecom_pb2_grpc.EcomRuntimeStub(channel)  # type: ignore[no-untyped-call]
        response = await stub.Stat(ecom_pb2.StatRequest(path="/a.txt"))
        assert response.kind == ecom_pb2.NODE_KIND_FILE
        assert response.writable is True


def test_runtime_client_constructs_without_connecting(fake_env_server: str) -> None:
    channel = grpc.aio.insecure_channel(fake_env_server)
    client = EcomRuntimeClient(channel)
    assert isinstance(client, EcomRuntimeClient)


def test_runtime_client_excludes_answer() -> None:
    assert not hasattr(EcomRuntimeClient, "answer")


def test_runtime_client_rejects_non_positive_timeout(fake_env_server: str) -> None:
    channel = grpc.aio.insecure_channel(fake_env_server)

    with pytest.raises(ValueError, match="greater than zero"):
        EcomRuntimeClient(channel, rpc_timeout_seconds=0)


async def test_runtime_client_sets_timeout_on_every_rpc() -> None:
    stub = MagicMock()
    responses = {
        "Read": ecom_pb2.ReadResponse(),
        "List": ecom_pb2.ListResponse(),
        "Tree": ecom_pb2.TreeResponse(),
        "Find": ecom_pb2.FindResponse(),
        "Search": ecom_pb2.SearchResponse(),
        "Stat": ecom_pb2.StatResponse(),
        "Exec": ecom_pb2.ExecResponse(),
        "Write": ecom_pb2.WriteResponse(),
        "Delete": ecom_pb2.DeleteResponse(),
    }
    for method, response in responses.items():
        setattr(stub, method, AsyncMock(return_value=response))

    with patch(
        "ecom_agent.agent.runtime_client.EcomRuntimeStub",
        return_value=stub,
    ):
        client = EcomRuntimeClient(MagicMock(), rpc_timeout_seconds=2.5)
        await client.read("/a.txt")
        await client.list_dir()
        await client.tree()
        await client.find("a.txt")
        await client.search("pattern")
        await client.stat("/a.txt")
        await client.exec("/bin/id")
        await client.write("/a.txt", "content")
        await client.delete("/a.txt")

    for method in responses:
        assert getattr(stub, method).await_args.kwargs["timeout"] == 2.5


@pytest.fixture
async def runtime_client(fake_env_server: str) -> EcomRuntimeClient:
    channel = grpc.aio.insecure_channel(fake_env_server)
    return EcomRuntimeClient(channel)


async def test_read(runtime_client: EcomRuntimeClient) -> None:
    response = await runtime_client.read("/a.txt")
    assert response.path == "/a.txt"
    assert response.content == "fake content"


async def test_list_dir(runtime_client: EcomRuntimeClient) -> None:
    response = await runtime_client.list_dir("/dir")
    assert response.path == "/dir"
    assert response.entries[0].path == "/dir/a.txt"


async def test_tree(runtime_client: EcomRuntimeClient) -> None:
    response = await runtime_client.tree()
    assert response.root.name == "/"
    assert response.root.kind == ecom_pb2.NODE_KIND_DIR


async def test_find(runtime_client: EcomRuntimeClient) -> None:
    response = await runtime_client.find("a.txt")
    assert response.paths == ["/a.txt"]


async def test_search(runtime_client: EcomRuntimeClient) -> None:
    response = await runtime_client.search("pattern")
    assert response.matches[0].line_text == "pattern"


async def test_stat(runtime_client: EcomRuntimeClient) -> None:
    response = await runtime_client.stat("/a.txt")
    assert response.kind == ecom_pb2.NODE_KIND_FILE
    assert response.writable is True


async def test_exec(runtime_client: EcomRuntimeClient) -> None:
    response = await runtime_client.exec("/bin/id")
    assert response.exit_code == 0
    assert response.stdout == "/bin/id"


async def test_write(runtime_client: EcomRuntimeClient) -> None:
    response = await runtime_client.write("/a.txt", "content")
    assert response.path == "/a.txt"


async def test_delete(runtime_client: EcomRuntimeClient) -> None:
    response = await runtime_client.delete("/a.txt")
    assert response == ecom_pb2.DeleteResponse()

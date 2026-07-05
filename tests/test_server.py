import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ecom_agent.config import Settings
from ecom_agent.server import main, serve


async def test_serve_starts_and_can_be_stopped() -> None:
    settings = Settings(grpc_host="127.0.0.1", grpc_port=0, default_model="test-model")
    serve_task = asyncio.create_task(serve(settings, llm_client=AsyncMock()))

    await asyncio.sleep(0.05)
    assert not serve_task.done()

    serve_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await serve_task


async def test_serve_fails_when_address_cannot_be_bound() -> None:
    settings = Settings(
        grpc_host="127.0.0.1", grpc_port=50051, default_model="test-model"
    )
    server = MagicMock()
    server.add_insecure_port.return_value = 0
    server.start = AsyncMock()
    observer = MagicMock()

    with (
        patch("ecom_agent.server.grpc.aio.server", return_value=server),
        pytest.raises(RuntimeError, match="failed to bind AgentService"),
    ):
        await serve(settings, llm_client=AsyncMock(), observability=observer)

    server.start.assert_not_awaited()
    observer.shutdown.assert_called_once_with()


async def test_serve_stops_server_after_termination() -> None:
    settings = Settings(
        grpc_host="127.0.0.1", grpc_port=50051, default_model="test-model"
    )
    server = MagicMock()
    server.add_insecure_port.return_value = 50051
    server.start = AsyncMock()
    server.wait_for_termination = AsyncMock()
    server.stop = AsyncMock()
    observer = MagicMock()

    with patch("ecom_agent.server.grpc.aio.server", return_value=server):
        await serve(settings, llm_client=AsyncMock(), observability=observer)

    server.stop.assert_awaited_once_with(5.0)
    observer.shutdown.assert_called_once_with()


def test_main_wires_openai_client_and_serves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ECOM_AGENT_DEFAULT_MODEL", "test-model")
    with (
        patch("ecom_agent.server.AsyncOpenAI") as mock_openai_cls,
        patch("ecom_agent.server.OpenAILLMClient") as mock_llm_cls,
        patch("ecom_agent.server.build_observability") as mock_build_observability,
        patch("ecom_agent.server.serve") as mock_serve,
        patch("ecom_agent.server.asyncio.run") as mock_run,
    ):
        main()

    mock_openai_cls.assert_called_once_with()
    mock_build_observability.assert_called_once_with(Settings())
    mock_llm_cls.assert_called_once_with(
        mock_openai_cls.return_value,
        "test-model",
        observability=mock_build_observability.return_value,
    )
    mock_serve.assert_called_once_with(
        Settings(), mock_llm_cls.return_value, mock_build_observability.return_value
    )

    mock_run.assert_called_once()
    coro = mock_run.call_args.args[0]
    assert asyncio.iscoroutine(coro)
    coro.close()

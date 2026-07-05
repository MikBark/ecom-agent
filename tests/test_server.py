import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from ecom_agent.config import Settings
from ecom_agent.server import main, serve


async def test_serve_starts_and_can_be_stopped() -> None:
    settings = Settings(grpc_host="127.0.0.1", grpc_port=0)
    serve_task = asyncio.create_task(serve(settings, llm_client=AsyncMock()))

    await asyncio.sleep(0.05)
    assert not serve_task.done()

    serve_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await serve_task


def test_main_wires_openai_client_and_serves() -> None:
    with (
        patch("ecom_agent.server.AsyncOpenAI") as mock_openai_cls,
        patch("ecom_agent.server.OpenAILLMClient") as mock_llm_cls,
        patch("ecom_agent.server.serve") as mock_serve,
        patch("ecom_agent.server.asyncio.run") as mock_run,
    ):
        main()

    mock_openai_cls.assert_called_once_with()
    mock_llm_cls.assert_called_once_with(mock_openai_cls.return_value, "gpt-5.5")
    mock_serve.assert_called_once_with(Settings(), mock_llm_cls.return_value)

    mock_run.assert_called_once()
    coro = mock_run.call_args.args[0]
    assert asyncio.iscoroutine(coro)
    coro.close()

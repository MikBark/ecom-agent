from unittest.mock import AsyncMock

import pytest

from ecom_agent.agent.core import Agent
from ecom_agent.v1 import agent_pb2


async def test_agent_run_is_unimplemented_stub() -> None:
    agent = Agent(env_client=AsyncMock(), llm_client=AsyncMock())
    with pytest.raises(NotImplementedError):
        async for _ in agent.run(agent_pb2.RunRequest(prompt="hi")):
            pass

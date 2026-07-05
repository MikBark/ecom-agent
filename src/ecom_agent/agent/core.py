from collections.abc import AsyncIterator

from ecom_agent.agent.env_client import EcomEnvClient
from ecom_agent.agent.llm import LLMClient
from ecom_agent.v1 import agent_pb2


class Agent:
    """Runs the staged SGR workflow against a playground. Internals out of scope."""

    def __init__(self, env_client: EcomEnvClient, llm_client: LLMClient) -> None:
        self._env_client = env_client
        self._llm_client = llm_client

    async def run(self, request: agent_pb2.RunRequest) -> AsyncIterator[agent_pb2.RunEvent]:
        raise NotImplementedError
        yield  # pragma: no cover - makes this an async generator for typing

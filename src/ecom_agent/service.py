from collections.abc import AsyncIterator

import grpc

from ecom_agent.agent.core import Agent
from ecom_agent.agent.env_client import EcomEnvClient
from ecom_agent.agent.llm import LLMClient
from ecom_agent.v1 import agent_pb2, agent_pb2_grpc


class AgentServicer(agent_pb2_grpc.AgentServiceServicer):
    """gRPC servicer wiring AgentService.Run to the Agent class."""

    def __init__(self, llm_client: LLMClient) -> None:
        self._llm_client = llm_client

    async def Run(
        self,
        request: agent_pb2.RunRequest,
        context: grpc.aio.ServicerContext[agent_pb2.RunRequest, agent_pb2.RunEvent],
    ) -> AsyncIterator[agent_pb2.RunEvent]:
        channel = grpc.aio.insecure_channel(request.playground_url)
        try:
            env_client = EcomEnvClient(channel, request.playground_id)
            agent = Agent(env_client, self._llm_client)
            async for event in agent.run(request):
                yield event
        finally:
            await channel.close()

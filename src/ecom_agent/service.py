"""gRPC servicer wiring AgentService.Run to the Agent workflow."""

from collections.abc import AsyncIterator

import grpc

from ecom_agent.agent.core import Agent
from ecom_agent.agent.llm import LLMClient
from ecom_agent.agent.runtime_client import EcomRuntimeClient
from ecom_agent.observability import Observability
from ecom_agent.runtime_channel import create_runtime_channel
from ecom_agent.v1 import agent_pb2, agent_pb2_grpc


class AgentServicer(agent_pb2_grpc.AgentServiceServicer):
    """gRPC servicer wiring AgentService.Run to the Agent class."""

    def __init__(
        self,
        llm_client: LLMClient,
        observability: Observability | None = None,
        *,
        runtime_rpc_timeout_seconds: float = 30.0,
    ) -> None:
        self._llm_client = llm_client
        self._observability = observability or Observability("off")
        self._runtime_rpc_timeout_seconds = runtime_rpc_timeout_seconds

    async def Run(
        self,
        request: agent_pb2.RunRequest,
        context: grpc.aio.ServicerContext[agent_pb2.RunRequest, agent_pb2.RunEvent],
    ) -> AsyncIterator[agent_pb2.RunEvent]:
        try:
            channel = create_runtime_channel(request.harness_url)
        except ValueError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            return
        try:
            runtime_client = EcomRuntimeClient(
                channel, rpc_timeout_seconds=self._runtime_rpc_timeout_seconds
            )
            agent = Agent(runtime_client, self._llm_client, self._observability)
            async for event in agent.run(request):
                yield event
        finally:
            await channel.close()

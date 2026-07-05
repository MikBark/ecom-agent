"""gRPC server bootstrap: wires the Agent servicer, health checks, and settings."""

import asyncio
import logging

import grpc
from openai import AsyncOpenAI

from ecom_agent.agent.llm import LLMClient
from ecom_agent.agent.openai_llm import OpenAILLMClient
from ecom_agent.config import Settings
from ecom_agent.health import build_health_servicer, mark_serving, register_health_service
from ecom_agent.observability import Observability, build_observability
from ecom_agent.service import AgentServicer
from ecom_agent.v1 import agent_pb2_grpc

logger = logging.getLogger(__name__)

AGENT_SERVICE_FULL_NAME = "ecom_agent.v1.AgentService"
_SHUTDOWN_GRACE_SECONDS = 5.0


async def serve(
    settings: Settings,
    llm_client: LLMClient,
    observability: Observability | None = None,
) -> None:
    observer = observability or Observability("off")
    server = grpc.aio.server()

    agent_pb2_grpc.add_AgentServiceServicer_to_server(  # type: ignore[no-untyped-call]
        AgentServicer(
            llm_client,
            observer,
            runtime_rpc_timeout_seconds=settings.runtime_rpc_timeout_seconds,
        ),
        server,
    )

    health_servicer = build_health_servicer()
    register_health_service(server, health_servicer)
    mark_serving(health_servicer, "")
    mark_serving(health_servicer, AGENT_SERVICE_FULL_NAME)

    started = False
    try:
        address = f"{settings.grpc_host}:{settings.grpc_port}"
        bound_port = server.add_insecure_port(address)
        if bound_port == 0:
            raise RuntimeError(f"failed to bind AgentService to {address}")

        logger.info("starting AgentService on %s", address)
        await server.start()
        started = True
        await server.wait_for_termination()
    finally:
        try:
            if started:
                await server.stop(_SHUTDOWN_GRACE_SECONDS)
        finally:
            await asyncio.to_thread(observer.shutdown)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()  # type: ignore[call-arg]  # populated from the environment
    observability = build_observability(settings)
    llm_client = OpenAILLMClient(
        AsyncOpenAI(), settings.default_model, observability=observability
    )
    asyncio.run(serve(settings, llm_client, observability))


if __name__ == "__main__":
    main()

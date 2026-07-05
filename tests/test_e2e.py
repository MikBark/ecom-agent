"""End-to-end tests: real gRPC server + client stubs for AgentService.Run and Health."""

from collections import deque

import grpc
from grpc_health.v1 import health_pb2, health_pb2_grpc

from ecom_agent.agent.sgr.schemas import (
    AuditRefsSchema,
    CompleteSchema,
    FinishDecision,
    NextStepSchema,
)
from ecom_agent.server import AGENT_SERVICE_FULL_NAME
from ecom_agent.v1 import agent_pb2, agent_pb2_grpc
from tests.conftest import FakeLLMClient, start_agent_server


async def test_run_happy_path_streams_final_answer(fake_env_server: str) -> None:
    llm = FakeLLMClient(
        {
            NextStepSchema: deque(
                [
                    NextStepSchema(
                        state_recap="nothing further required",
                        decision=FinishDecision(
                            next_step="finish_ok",
                            finish_explanation="task can finish immediately",
                        ),
                    )
                ]
            ),
            CompleteSchema: deque(
                [
                    CompleteSchema(
                        format_source="task",
                        required_shape="bare text",
                        outcome="ok",
                        message="done",
                    )
                ]
            ),
            AuditRefsSchema: deque([AuditRefsSchema(keep=[], refuse=[])]),
        }
    )

    async with (
        start_agent_server(llm) as address,
        grpc.aio.insecure_channel(address) as channel,
    ):
        stub = agent_pb2_grpc.AgentServiceStub(channel)
        request = agent_pb2.RunRequest(prompt="say hi", harness_url=fake_env_server)
        events = [event async for event in stub.Run(request)]

    event_kinds = [event.WhichOneof("event") for event in events]
    assert event_kinds[0] == "stage_started"
    assert event_kinds[-1] == "final_answer"
    stages = [
        event.stage_started.stage
        for event in events
        if event.WhichOneof("event") == "stage_started"
    ]
    assert stages == ["init", "next_step", "complete", "audit_refs"]
    final = events[-1].final_answer
    assert final.message == "done"
    assert final.outcome == agent_pb2.OUTCOME_OK


async def test_health_check_reports_serving() -> None:
    llm = FakeLLMClient({})

    async with (
        start_agent_server(llm) as address,
        grpc.aio.insecure_channel(address) as channel,
    ):
        stub = health_pb2_grpc.HealthStub(channel)
        for service_name in ("", AGENT_SERVICE_FULL_NAME):
            request = health_pb2.HealthCheckRequest(service=service_name)
            response = await stub.Check(request)
            assert response.status == health_pb2.HealthCheckResponse.SERVING

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import grpc

from ecom_agent.service import AgentServicer
from ecom_agent.v1 import agent_pb2


async def _scripted_events() -> AsyncIterator[agent_pb2.RunEvent]:
    yield agent_pb2.RunEvent(
        stage_started=agent_pb2.StageStarted(stage="bootstrap_classify")
    )
    yield agent_pb2.RunEvent(
        tool_call=agent_pb2.ToolCall(stage="evidence", tool="read", request_json="{}")
    )
    yield agent_pb2.RunEvent(
        final_answer=agent_pb2.FinalAnswer(
            message="done", outcome=agent_pb2.OUTCOME_OK, refs=["/a.txt"]
        )
    )


async def test_run_streams_events_from_agent(fake_env_server: str) -> None:
    servicer = AgentServicer(llm_client=AsyncMock(), runtime_rpc_timeout_seconds=2.5)
    request = agent_pb2.RunRequest(
        prompt="find product X",
        harness_url=fake_env_server,
    )
    context = AsyncMock(spec=grpc.aio.ServicerContext)

    with (
        patch("ecom_agent.service.Agent") as agent_cls,
        patch("ecom_agent.service.EcomRuntimeClient") as runtime_client_cls,
    ):
        agent_cls.return_value.run.return_value = _scripted_events()

        events = [event async for event in servicer.Run(request, context)]

    runtime_client_cls.assert_called_once()
    assert runtime_client_cls.call_args.kwargs == {"rpc_timeout_seconds": 2.5}

    assert [event.WhichOneof("event") for event in events] == [
        "stage_started",
        "tool_call",
        "final_answer",
    ]
    assert events[-1].final_answer.message == "done"
    assert events[-1].final_answer.outcome == agent_pb2.OUTCOME_OK

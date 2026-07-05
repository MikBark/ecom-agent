"""Agent workflow entrypoint: runs the staged SGR reasoning loop against a playground."""

import logging
from collections.abc import AsyncIterator

import grpc
from google.protobuf.json_format import MessageToJson

from ecom_agent.agent.llm import LLMClient, Message, SchemaT
from ecom_agent.agent.runtime_client import EcomRuntimeClient
from ecom_agent.agent.sgr.schemas import (
    AUDIT_REFS_PROMPT,
    COLLECT_PROMPT,
    COMPLETE_PROMPT,
    MODIFY_PROMPT,
    NEXT_STEP_PROMPT,
    SYSTEM_PROMPT,
    AuditRefsSchema,
    CollectSchema,
    CompleteSchema,
    ModifySchema,
    NextStepSchema,
)
from ecom_agent.agent.sgr.stages import WorkflowState
from ecom_agent.agent.sgr.tools import ToolCallError, call_modify_tool, call_read_tool
from ecom_agent.observability import Observability, Observation
from ecom_agent.v1 import agent_pb2

logger = logging.getLogger(__name__)

_DEFAULT_MAX_STEPS = 12

_OUTCOME_MAP: dict[str, agent_pb2.Outcome] = {
    "ok": agent_pb2.OUTCOME_OK,
    "denied_security": agent_pb2.OUTCOME_DENIED_SECURITY,
    "unclarified": agent_pb2.OUTCOME_NONE_CLARIFICATION,
    "unsupported": agent_pb2.OUTCOME_NONE_UNSUPPORTED,
    "err_internal": agent_pb2.OUTCOME_ERR_INTERNAL,
}


def _map_outcome(outcome: str | None) -> agent_pb2.Outcome:
    return _OUTCOME_MAP.get(outcome or "", agent_pb2.OUTCOME_ERR_INTERNAL)


def _reconcile_outcome(finish_outcome: str, complete_outcome: str) -> str:
    """Keep NextStep's outcome, except Complete may refine ok to unsupported."""
    if finish_outcome == "err_internal" or complete_outcome == "err_internal":
        return "err_internal"
    if finish_outcome in ("denied_security", "unclarified"):
        return finish_outcome
    if finish_outcome == "ok" and complete_outcome == "unsupported":
        return "unsupported"
    return finish_outcome


def _max_steps_exceeded_events() -> list[agent_pb2.RunEvent]:
    return [
        agent_pb2.RunEvent(error=agent_pb2.Error(message="max steps exceeded")),
        agent_pb2.RunEvent(
            final_answer=agent_pb2.FinalAnswer(
                message="workflow did not finish within the step budget",
                outcome=agent_pb2.OUTCOME_ERR_INTERNAL,
            )
        ),
    ]


def _internal_error_events() -> list[agent_pb2.RunEvent]:
    return [
        agent_pb2.RunEvent(error=agent_pb2.Error(message="internal error")),
        agent_pb2.RunEvent(
            final_answer=agent_pb2.FinalAnswer(
                message="internal error", outcome=agent_pb2.OUTCOME_ERR_INTERNAL
            )
        ),
    ]


def _tool_failure_events(exc: ToolCallError) -> list[agent_pb2.RunEvent]:
    message = str(exc)
    return [
        agent_pb2.RunEvent(error=agent_pb2.Error(message=message)),
        agent_pb2.RunEvent(
            final_answer=agent_pb2.FinalAnswer(
                message=message, outcome=agent_pb2.OUTCOME_ERR_INTERNAL
            )
        ),
    ]


def _update_run_observation(
    observation: Observation,
    observability: Observability,
    event: agent_pb2.RunEvent,
) -> None:
    event_type = event.WhichOneof("event")
    if event_type == "error":
        status = (
            event.error.message if observability.captures_content else "workflow_error"
        )
        observation.update(
            level="ERROR",
            status_message=status,
            metadata={"error_type": "workflow_error"},
        )
    elif event_type == "final_answer":
        observation.update(
            output=observability.content({"message": event.final_answer.message}),
            metadata={
                "outcome": agent_pb2.Outcome.Name(event.final_answer.outcome),
                "ref_count": len(event.final_answer.refs),
                "tool_count": len(event.final_answer.tool_trace),
            },
        )


def _max_steps(request: agent_pb2.RunRequest) -> int:
    raw = request.config.get("max_steps", "")
    if not raw:
        return _DEFAULT_MAX_STEPS
    try:
        return max(1, int(raw))
    except ValueError:
        return _DEFAULT_MAX_STEPS


class Agent:
    """Runs the staged SGR workflow against a playground. Internals out of scope."""

    def __init__(
        self,
        runtime_client: EcomRuntimeClient,
        llm_client: LLMClient,
        observability: Observability | None = None,
    ) -> None:
        self._runtime_client = runtime_client
        self._llm_client = llm_client
        self._observability = observability or Observability("off")

    async def run(
        self, request: agent_pb2.RunRequest
    ) -> AsyncIterator[agent_pb2.RunEvent]:
        metadata = {
            "max_steps": _max_steps(request),
            "prompt_characters": len(request.prompt),
        }
        with self._observability.observe(
            name="agent.run",
            as_type="agent",
            input_data=self._observability.content({"prompt": request.prompt}),
            metadata=metadata,
        ) as observation:
            try:
                async for event in self._run_steps(request):
                    _update_run_observation(observation, self._observability, event)
                    yield event
            except ToolCallError as exc:
                observation.fail(exc)
                logger.warning("agent tool call failed: %s", exc)
                for event in _tool_failure_events(exc):
                    yield event
            except Exception as exc:
                observation.fail(exc)
                logger.exception("agent run failed")
                for event in _internal_error_events():
                    yield event

    async def _run_steps(
        self, request: agent_pb2.RunRequest
    ) -> AsyncIterator[agent_pb2.RunEvent]:
        state = WorkflowState(prompt=request.prompt)
        max_steps = _max_steps(request)
        for event in await self._init(state):
            yield event
        finish_outcome, loop_events = await self._run_loop(state, max_steps)
        for event in loop_events:
            yield event
        if finish_outcome is None:
            for event in _max_steps_exceeded_events():
                yield event
            return
        for event in await self._finalize(state, finish_outcome):
            yield event

    async def _finalize(
        self, state: WorkflowState, finish_outcome: str
    ) -> list[agent_pb2.RunEvent]:
        events = await self._complete(state, finish_outcome)
        events.extend(await self._audit_refs(state))
        events.append(
            agent_pb2.RunEvent(
                final_answer=agent_pb2.FinalAnswer(
                    message=state.draft_message,
                    outcome=_map_outcome(state.outcome),
                    refs=state.kept_refs,
                    tool_trace=state.tool_trace,
                )
            )
        )
        return events

    async def _init(self, state: WorkflowState) -> list[agent_pb2.RunEvent]:
        with self._observability.observe(
            name="stage.init", as_type="chain", metadata={"stage": "init"}
        ):
            prefetch, prefetch_refs = await self._prefetch()
            state.collected_refs.extend(prefetch_refs)
            state.messages.append(
                Message(role="user", content=f"{state.prompt}\n\n{prefetch}")
            )
            return [
                agent_pb2.RunEvent(stage_started=agent_pb2.StageStarted(stage="init")),
                agent_pb2.RunEvent(log=agent_pb2.Log(message="prefetch complete")),
            ]

    async def _prefetch(self) -> tuple[str, list[str]]:
        sections = []
        refs = []
        for label, tool, request_data, fetch in (
            (
                "AGENTS.md",
                "read",
                {"path": "/AGENTS.md"},
                self._runtime_client.read("/AGENTS.md"),
            ),
            ("tree", "tree", {}, self._runtime_client.tree()),
            (
                "/bin/id",
                "exec",
                {"path": "/bin/id"},
                self._runtime_client.exec("/bin/id"),
            ),
        ):
            with self._observability.observe(
                name=f"tool.{tool}",
                as_type="tool",
                input_data=self._observability.content(request_data),
                metadata={"stage": "init", "tool": tool, "prefetch": True},
            ) as observation:
                try:
                    response = await fetch
                except grpc.RpcError as exc:
                    observation.fail(exc)
                    sections.append(f"## {label}\nerror: {exc}")
                else:
                    content = MessageToJson(response, preserving_proto_field_name=True)
                    observation.update(output=self._observability.content(content))
                    sections.append(f"## {label}\n{content}")
                    if label == "AGENTS.md":
                        refs.append("/AGENTS.md")
        return "\n\n".join(sections), refs

    async def _run_llm_step(
        self,
        state: WorkflowState,
        *,
        stage: str,
        prompt_text: str,
        schema_type: type[SchemaT],
    ) -> tuple[SchemaT, agent_pb2.RunEvent]:
        state.messages.append(Message(role="user", content=prompt_text))
        generation_input = {
            "system_prompt": SYSTEM_PROMPT,
            "messages": [message._asdict() for message in state.messages],
        }
        with self._observability.observe(
            name=f"llm.{stage}",
            as_type="generation",
            input_data=self._observability.content(generation_input),
            metadata={"stage": stage, "schema": schema_type.__name__},
        ) as observation:
            parsed = await self._llm_client.complete_structured(
                system_prompt=SYSTEM_PROMPT, messages=state.messages, schema=schema_type
            )
            schema_json = parsed.model_dump_json()
            observation.update(
                output=self._observability.content(parsed.model_dump(mode="json"))
            )
        state.messages.append(Message(role="assistant", content=schema_json))
        event = agent_pb2.RunEvent(
            schema_emitted=agent_pb2.SchemaEmitted(
                stage=stage, schema_name=schema_type.__name__, schema_json=schema_json
            )
        )
        return parsed, event

    async def _run_loop(
        self, state: WorkflowState, max_steps: int
    ) -> tuple[str | None, list[agent_pb2.RunEvent]]:
        events: list[agent_pb2.RunEvent] = []
        for _ in range(max_steps):
            next_step, step_events = await self._next_step(state)
            events.extend(step_events)
            decision = next_step.decision
            if decision.next_step == "collect":
                events.extend(await self._collect(state))
            elif decision.next_step == "modify":
                events.extend(await self._modify(state))
            else:
                return decision.outcome, events
        return None, events

    async def _next_step(
        self, state: WorkflowState
    ) -> tuple[NextStepSchema, list[agent_pb2.RunEvent]]:
        with self._observability.observe(
            name="stage.next_step",
            as_type="chain",
            metadata={"stage": "next_step"},
        ):
            parsed, schema_event = await self._run_llm_step(
                state,
                stage="next_step",
                prompt_text=NEXT_STEP_PROMPT,
                schema_type=NextStepSchema,
            )
            events = [
                agent_pb2.RunEvent(
                    stage_started=agent_pb2.StageStarted(stage="next_step")
                ),
                agent_pb2.RunEvent(
                    reasoning=agent_pb2.Reasoning(
                        stage="next_step", text=parsed.state_recap
                    )
                ),
                schema_event,
            ]
            return parsed, events

    async def _collect(self, state: WorkflowState) -> list[agent_pb2.RunEvent]:
        with self._observability.observe(
            name="stage.collect",
            as_type="chain",
            metadata={"stage": "collect"},
        ):
            parsed, schema_event = await self._run_llm_step(
                state,
                stage="collect",
                prompt_text=COLLECT_PROMPT,
                schema_type=CollectSchema,
            )
            events = [
                agent_pb2.RunEvent(stage_started=agent_pb2.StageStarted(stage="collect")),
                schema_event,
            ]
            for call in parsed.reads:
                request_json = call.model_dump_json()
                with self._observability.observe(
                    name=f"tool.{call.tool}",
                    as_type="tool",
                    input_data=self._observability.content(call.model_dump(mode="json")),
                    metadata={"stage": "collect", "tool": call.tool},
                ) as observation:
                    response_json, ref = await call_read_tool(self._runtime_client, call)
                    observation.update(output=self._observability.content(response_json))
                events.extend(
                    self._record_tool_call(
                        state,
                        stage="collect",
                        tool=call.tool,
                        request_json=request_json,
                        response_json=response_json,
                        ref=ref,
                    )
                )
            return events

    async def _modify(self, state: WorkflowState) -> list[agent_pb2.RunEvent]:
        with self._observability.observe(
            name="stage.modify",
            as_type="chain",
            metadata={"stage": "modify"},
        ):
            parsed, schema_event = await self._run_llm_step(
                state,
                stage="modify",
                prompt_text=MODIFY_PROMPT,
                schema_type=ModifySchema,
            )
            events = [
                agent_pb2.RunEvent(stage_started=agent_pb2.StageStarted(stage="modify")),
                schema_event,
            ]
            for call in parsed.mutations:
                request_json = call.model_dump_json()
                with self._observability.observe(
                    name=f"tool.{call.tool}",
                    as_type="tool",
                    input_data=self._observability.content(call.model_dump(mode="json")),
                    metadata={"stage": "modify", "tool": call.tool},
                ) as observation:
                    response_json, ref = await call_modify_tool(
                        self._runtime_client, call
                    )
                    observation.update(output=self._observability.content(response_json))
                events.extend(
                    self._record_tool_call(
                        state,
                        stage="modify",
                        tool=call.tool,
                        request_json=request_json,
                        response_json=response_json,
                        ref=ref,
                    )
                )
            return events

    def _record_tool_call(
        self,
        state: WorkflowState,
        *,
        stage: str,
        tool: str,
        request_json: str,
        response_json: str,
        ref: str | None,
    ) -> list[agent_pb2.RunEvent]:
        state.tool_trace.append(
            agent_pb2.ToolTrace(
                tool=tool, request_json=request_json, response_json=response_json
            )
        )
        if ref is not None:
            state.collected_refs.append(ref)
        state.messages.append(
            Message(role="user", content=f"tool_result[{tool}]: {response_json}")
        )
        return [
            agent_pb2.RunEvent(
                tool_call=agent_pb2.ToolCall(
                    stage=stage, tool=tool, request_json=request_json
                )
            ),
            agent_pb2.RunEvent(
                tool_result=agent_pb2.ToolResult(
                    stage=stage, tool=tool, response_json=response_json
                )
            ),
        ]

    async def _complete(
        self, state: WorkflowState, finish_outcome: str
    ) -> list[agent_pb2.RunEvent]:
        with self._observability.observe(
            name="stage.complete",
            as_type="chain",
            metadata={"stage": "complete"},
        ):
            parsed, schema_event = await self._run_llm_step(
                state,
                stage="complete",
                prompt_text=COMPLETE_PROMPT,
                schema_type=CompleteSchema,
            )
            state.draft_message = parsed.message
            state.outcome = _reconcile_outcome(finish_outcome, parsed.outcome)
            return [
                agent_pb2.RunEvent(
                    stage_started=agent_pb2.StageStarted(stage="complete")
                ),
                schema_event,
            ]

    async def _audit_refs(self, state: WorkflowState) -> list[agent_pb2.RunEvent]:
        refs_blob = ", ".join(state.collected_refs) or "(none)"
        prompt_text = (
            f"{AUDIT_REFS_PROMPT}\n\nDRAFT_MESSAGE: {state.draft_message}\n"
            f"OUTCOME: {state.outcome}\nCOLLECTED_REFS: {refs_blob}"
        )
        with self._observability.observe(
            name="stage.audit_refs",
            as_type="chain",
            metadata={"stage": "audit_refs"},
        ):
            parsed, schema_event = await self._run_llm_step(
                state,
                stage="audit_refs",
                prompt_text=prompt_text,
                schema_type=AuditRefsSchema,
            )
            collected = set(state.collected_refs)
            state.kept_refs = list(
                dict.fromkeys(kept.path for kept in parsed.keep if kept.path in collected)
            )
            return [
                agent_pb2.RunEvent(
                    stage_started=agent_pb2.StageStarted(stage="audit_refs")
                ),
                schema_event,
            ]

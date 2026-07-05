"""Step identifiers and the workflow state threaded across the SGR loop."""

from dataclasses import dataclass, field
from typing import Literal

from ecom_agent.agent.llm import Message
from ecom_agent.v1 import agent_pb2

Step = Literal["init", "next_step", "collect", "modify", "complete", "audit_refs"]


@dataclass
class WorkflowState:
    """Internal accumulator threaded across the SGR loop steps.

    This is code-side bookkeeping, not the model's memory: the LLM is stateless per
    call, and `messages` IS the single growing transcript rendered into every
    `complete_structured` call. The other fields just carry facts forward so nothing is
    re-fetched or re-derived.
    """

    prompt: str
    messages: list[Message] = field(default_factory=list)
    collected_refs: list[str] = field(default_factory=list)
    tool_trace: list[agent_pb2.ToolTrace] = field(default_factory=list)
    draft_message: str = ""
    outcome: str | None = None
    kept_refs: list[str] = field(default_factory=list)

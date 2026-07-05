from ecom_agent.agent.llm import Message
from ecom_agent.agent.sgr.stages import WorkflowState


def test_workflow_state_defaults() -> None:
    state = WorkflowState(prompt="find product X")
    assert state.prompt == "find product X"
    assert state.messages == []
    assert state.collected_refs == []
    assert state.tool_trace == []
    assert state.draft_message == ""
    assert state.outcome is None
    assert state.kept_refs == []


def test_workflow_state_messages_is_the_shared_transcript() -> None:
    state = WorkflowState(prompt="find product X")
    state.messages.append(Message(role="user", content="hello"))

    other = WorkflowState(prompt="a different task")

    assert state.messages != other.messages
    assert other.messages == []

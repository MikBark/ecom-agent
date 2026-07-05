import pytest

from ecom_agent.agent.sgr.stages import STAGE_ORDER, WorkflowState


def test_stage_order_is_fixed() -> None:
    assert STAGE_ORDER == (
        "bootstrap_classify",
        "policy_investigation",
        "security_check",
        "evidence",
        "trust_authorize",
        "mutation",
        "refs_audit",
        "finalize",
    )


def test_workflow_state_defaults() -> None:
    state = WorkflowState()
    assert state.decision is None
    assert state.authorized is False
    assert state.mutation_needed is False
    assert state.augmentations == []


class _StubStage:
    name = "bootstrap_classify"

    async def run(self, state: WorkflowState) -> WorkflowState:
        raise NotImplementedError


async def test_stage_protocol_stub_raises() -> None:
    stage = _StubStage()
    with pytest.raises(NotImplementedError):
        await stage.run(WorkflowState())

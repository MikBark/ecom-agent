import pytest
from pydantic import ValidationError

from ecom_agent.agent.sgr.schemas import (
    AuditRefsSchema,
    CollectSchema,
    CompleteSchema,
    ContinueDecision,
    DeleteCall,
    FinishDecision,
    FinishOutcome,
    FinishStep,
    KeptRef,
    ModifySchema,
    NextStepSchema,
    ReadCall,
    RefusedRef,
    StatCall,
    WriteCall,
)


def test_next_step_schema_round_trip() -> None:
    schema = NextStepSchema(
        state_recap="need order status",
        decision=ContinueDecision(
            task_gap="order status not yet read",
            next_step="collect",
        ),
    )
    assert NextStepSchema.model_validate(schema.model_dump()) == schema


def test_collect_schema_holds_read_calls() -> None:
    schema = CollectSchema(
        reads=[ReadCall(path="/orders/123.json", explanation="order status")]
    )
    assert schema.reads[0].tool == "read"


def test_collect_schema_discriminates_by_tool_from_json() -> None:
    schema = CollectSchema.model_validate(
        {
            "reads": [
                {"tool": "stat", "path": "/orders/123.json", "explanation": "check size"}
            ]
        }
    )
    assert isinstance(schema.reads[0], StatCall)


def test_modify_schema_requires_policy_grounding() -> None:
    call = WriteCall(
        path="/orders/123.json",
        content="{}",
        explanation="cancel the order",
        policy_grounding="/docs/policy/refunds.md#cancellation",
    )
    schema = ModifySchema(mutations=[call])
    assert schema.mutations[0].policy_grounding.startswith("/docs")


def test_modify_schema_discriminates_delete_from_json() -> None:
    schema = ModifySchema.model_validate(
        {
            "mutations": [
                {
                    "tool": "delete",
                    "path": "/orders/123.json",
                    "explanation": "remove stale order",
                    "policy_grounding": "/docs/policy/retention.md#deletion",
                }
            ]
        }
    )
    assert isinstance(schema.mutations[0], DeleteCall)


def test_complete_schema_validates_outcome_literal() -> None:
    schema = CompleteSchema(
        format_source="task instruction",
        required_shape="bare order status string",
        outcome="ok",
        message="shipped",
    )
    assert schema.outcome == "ok"


def test_complete_schema_validates_err_internal_outcome() -> None:
    schema = CompleteSchema(
        format_source="task instruction",
        required_shape="bare order status string",
        outcome="err_internal",
        message="internal error",
    )
    assert schema.outcome == "err_internal"


def test_next_step_schema_accepts_err_internal_finish_step() -> None:
    schema = NextStepSchema(
        state_recap="disk failure blocked evidence",
        decision=FinishDecision(
            next_step="finish_err_internal",
            finish_explanation="disk failure prevents collecting required evidence",
        ),
    )
    assert isinstance(schema.decision, FinishDecision)
    assert schema.decision.outcome == "err_internal"


@pytest.mark.parametrize(
    ("next_step", "outcome"),
    [
        ("finish_ok", "ok"),
        ("finish_denied_security", "denied_security"),
        ("finish_unclarified", "unclarified"),
        ("finish_err_internal", "err_internal"),
    ],
)
def test_finish_step_encodes_outcome(
    next_step: FinishStep, outcome: FinishOutcome
) -> None:
    decision = FinishDecision(
        next_step=next_step,
        finish_explanation="grounded finish explanation",
    )
    assert decision.outcome == outcome


def test_next_step_schema_rejects_finish_fields_on_continue_decision() -> None:
    with pytest.raises(ValidationError):
        NextStepSchema.model_validate(
            {
                "state_recap": "need order status",
                "decision": {
                    "next_step": "collect",
                    "task_gap": "order status not read",
                    "finish_outcome": "ok",
                },
            }
        )


def test_next_step_schema_requires_finish_explanation() -> None:
    with pytest.raises(ValidationError):
        NextStepSchema.model_validate(
            {
                "state_recap": "task is complete",
                "decision": {"next_step": "finish_ok"},
            }
        )


def test_audit_refs_schema_keep_and_refuse() -> None:
    schema = AuditRefsSchema(
        keep=[KeptRef(path="/orders/123.json", reason="grounds the status")],
        refuse=[RefusedRef(path="/proc/uptime", reason="not related to the answer")],
    )
    assert schema.keep[0].path == "/orders/123.json"
    assert schema.refuse[0].path == "/proc/uptime"

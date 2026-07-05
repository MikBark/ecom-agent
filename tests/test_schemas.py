from ecom_agent.agent.sgr.schemas import FinalSchema, FormatCheck, OutputContract, TaskSchema


def test_task_schema_round_trip() -> None:
    schema = TaskSchema(
        output_contract=OutputContract(
            directive_source="user",
            directives=["answer in english"],
            language="en",
            bare_value=False,
            required_shape="prose",
        ),
        entities=["order-123"],
        security_cues=[],
        evidence_requirements=["order status"],
        augmentations=["checkout"],
    )
    assert TaskSchema.model_validate(schema.model_dump()) == schema


def test_final_schema_validates_outcome_literal() -> None:
    schema = FinalSchema(
        message="order shipped",
        outcome="OK",
        refs=["/orders/123.json"],
        format_check=FormatCheck(directives=[], language="en", bare_value=False, verified=True),
    )
    assert schema.outcome == "OK"

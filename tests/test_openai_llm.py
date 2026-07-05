from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from ecom_agent.agent.llm import Message
from ecom_agent.agent.openai_llm import OpenAILLMClient, ParseRefusalError
from ecom_agent.observability import Observability


class _Schema(BaseModel):
    value: str


def _make_response(
    parsed: _Schema | None = None, refusal: str | None = None
) -> MagicMock:
    item = MagicMock()
    if refusal is not None:
        item.type = "refusal"
        item.refusal = refusal
    else:
        item.type = "output_text"
        item.parsed = parsed

    output = MagicMock()
    output.type = "message"
    output.content = [item]

    response = MagicMock()
    response.output = [output]
    response.usage = None
    return response


async def test_complete_structured_returns_parsed_schema() -> None:
    schema = _Schema(value="hi")
    client = MagicMock()
    client.responses.parse = AsyncMock(return_value=_make_response(parsed=schema))
    llm = OpenAILLMClient(client, "gpt-5.5")
    messages = [Message(role="user", content="msg")]

    result = await llm.complete_structured(
        system_prompt="sys", messages=messages, schema=_Schema
    )

    assert result == schema
    client.responses.parse.assert_awaited_once_with(
        model="gpt-5.5",
        instructions="sys",
        input=[{"role": "user", "content": "msg"}],
        text_format=_Schema,
    )


async def test_complete_structured_passes_the_full_transcript() -> None:
    client = MagicMock()
    client.responses.parse = AsyncMock(
        return_value=_make_response(parsed=_Schema(value="hi"))
    )
    llm = OpenAILLMClient(client, "gpt-5.5")
    messages = [
        Message(role="user", content="turn one"),
        Message(role="assistant", content='{"value": "hi"}'),
        Message(role="user", content="turn two"),
    ]

    await llm.complete_structured(system_prompt="sys", messages=messages, schema=_Schema)

    sent_input = client.responses.parse.call_args.kwargs["input"]
    assert sent_input == [
        {"role": "user", "content": "turn one"},
        {"role": "assistant", "content": '{"value": "hi"}'},
        {"role": "user", "content": "turn two"},
    ]


async def test_complete_structured_raises_on_refusal() -> None:
    client = MagicMock()
    client.responses.parse = AsyncMock(return_value=_make_response(refusal="nope"))
    llm = OpenAILLMClient(client, "gpt-5.5")

    with pytest.raises(ParseRefusalError, match="nope"):
        await llm.complete_structured(
            system_prompt="sys",
            messages=[Message(role="user", content="msg")],
            schema=_Schema,
        )


async def test_complete_structured_raises_when_nothing_parsed() -> None:
    response = MagicMock()
    response.output = []
    client = MagicMock()
    client.responses.parse = AsyncMock(return_value=response)
    llm = OpenAILLMClient(client, "gpt-5.5")

    with pytest.raises(ParseRefusalError):
        await llm.complete_structured(
            system_prompt="sys",
            messages=[Message(role="user", content="msg")],
            schema=_Schema,
        )


async def test_complete_structured_records_provider_token_usage() -> None:
    response = _make_response(parsed=_Schema(value="hi"))
    response.usage = MagicMock(
        input_tokens=100,
        output_tokens=40,
        total_tokens=140,
        input_tokens_details=MagicMock(cached_tokens=60),
        output_tokens_details=MagicMock(reasoning_tokens=25),
    )
    openai_client = MagicMock()
    openai_client.responses.parse = AsyncMock(return_value=response)
    langfuse_client = MagicMock()
    llm = OpenAILLMClient(
        openai_client,
        "gpt-5.5",
        observability=Observability("metadata", langfuse_client),
    )

    await llm.complete_structured(
        system_prompt="sys",
        messages=[Message(role="user", content="msg")],
        schema=_Schema,
    )

    langfuse_client.update_current_generation.assert_called_once_with(
        model="gpt-5.5",
        usage_details={
            "prompt_tokens": 100,
            "completion_tokens": 40,
            "total_tokens": 140,
            "prompt_tokens_details": {"cached_tokens": 60},
            "completion_tokens_details": {"reasoning_tokens": 25},
        },
    )

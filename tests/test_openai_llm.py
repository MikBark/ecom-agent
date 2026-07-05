from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from ecom_agent.agent.openai_llm import OpenAILLMClient, ParseRefusalError


class _Schema(BaseModel):
    value: str


def _make_response(parsed: _Schema | None = None, refusal: str | None = None) -> MagicMock:
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
    return response


async def test_complete_structured_returns_parsed_schema() -> None:
    schema = _Schema(value="hi")
    client = MagicMock()
    client.responses.parse = AsyncMock(return_value=_make_response(parsed=schema))
    llm = OpenAILLMClient(client, "gpt-5.5")

    result = await llm.complete_structured(system_prompt="sys", message="msg", schema=_Schema)

    assert result == schema
    client.responses.parse.assert_awaited_once_with(
        model="gpt-5.5", instructions="sys", input="msg", text_format=_Schema
    )


async def test_complete_structured_raises_on_refusal() -> None:
    client = MagicMock()
    client.responses.parse = AsyncMock(return_value=_make_response(refusal="nope"))
    llm = OpenAILLMClient(client, "gpt-5.5")

    with pytest.raises(ParseRefusalError, match="nope"):
        await llm.complete_structured(system_prompt="sys", message="msg", schema=_Schema)


async def test_complete_structured_raises_when_nothing_parsed() -> None:
    response = MagicMock()
    response.output = []
    client = MagicMock()
    client.responses.parse = AsyncMock(return_value=response)
    llm = OpenAILLMClient(client, "gpt-5.5")

    with pytest.raises(ParseRefusalError):
        await llm.complete_structured(system_prompt="sys", message="msg", schema=_Schema)

from openai import AsyncOpenAI

from ecom_agent.agent.llm import SchemaT


class ParseRefusalError(RuntimeError):
    """Raised when the model refuses to produce a structured output."""


class OpenAILLMClient:
    """LLMClient implementation backed by the OpenAI Responses API."""

    def __init__(self, client: AsyncOpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def complete_structured(
        self, *, system_prompt: str, message: str, schema: type[SchemaT]
    ) -> SchemaT:
        response = await self._client.responses.parse(
            model=self._model,
            instructions=system_prompt,
            input=message,
            text_format=schema,
        )

        for output in response.output:
            if output.type != "message":
                continue
            for item in output.content:
                if item.type == "refusal":
                    raise ParseRefusalError(item.refusal)
                if item.type == "output_text" and item.parsed is not None:
                    parsed: SchemaT = item.parsed
                    return parsed

        raise ParseRefusalError("model produced no parsed structured output")


__all__ = ["OpenAILLMClient", "ParseRefusalError"]

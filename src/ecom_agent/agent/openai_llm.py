"""LLMClient implementation backed by the OpenAI Responses API."""

from openai import AsyncOpenAI
from openai.types.responses import Response, ResponseInputParam

from ecom_agent.agent.llm import Message, SchemaT
from ecom_agent.observability import Observability


class ParseRefusalError(RuntimeError):
    """Raised when the model refuses to produce a structured output."""


class OpenAILLMClient:
    """LLMClient implementation backed by the OpenAI Responses API."""

    def __init__(
        self,
        client: AsyncOpenAI,
        model: str,
        *,
        observability: Observability | None = None,
    ) -> None:
        self._client = client
        self._model = model
        self._observability = observability or Observability("off")

    async def complete_structured(
        self, *, system_prompt: str, messages: list[Message], schema: type[SchemaT]
    ) -> SchemaT:
        input_items: ResponseInputParam = [
            {"role": message.role, "content": message.content} for message in messages
        ]
        response = await self._client.responses.parse(
            model=self._model,
            instructions=system_prompt,
            input=input_items,
            text_format=schema,
        )
        self._record_usage(response)

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

    def _record_usage(self, response: Response) -> None:
        usage = response.usage
        if usage is None:
            return
        self._observability.update_current_generation(
            model=self._model,
            usage_details={
                "prompt_tokens": usage.input_tokens,
                "completion_tokens": usage.output_tokens,
                "total_tokens": usage.total_tokens,
                "prompt_tokens_details": {
                    "cached_tokens": usage.input_tokens_details.cached_tokens
                },
                "completion_tokens_details": {
                    "reasoning_tokens": usage.output_tokens_details.reasoning_tokens
                },
            },
        )


__all__ = ["OpenAILLMClient", "ParseRefusalError"]

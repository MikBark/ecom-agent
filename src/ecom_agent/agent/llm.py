from typing import Protocol, TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMClient(Protocol):
    """Provider-agnostic structured-output (SGR) client. Internals out of scope."""

    async def complete_structured(
        self, *, system_prompt: str, message: str, schema: type[SchemaT]
    ) -> SchemaT:
        raise NotImplementedError

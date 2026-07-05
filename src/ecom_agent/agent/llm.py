"""Provider-agnostic structured-output (SGR) client protocol."""

from typing import Literal, NamedTuple, Protocol, TypeVar

from pydantic import BaseModel

SchemaT = TypeVar("SchemaT", bound=BaseModel)

Role = Literal["user", "assistant"]


class Message(NamedTuple):
    """A single turn in the shared conversation transcript threaded across steps."""

    role: Role
    content: str


class LLMClient(Protocol):
    """Provider-agnostic structured-output (SGR) client. Internals out of scope."""

    async def complete_structured(
        self, *, system_prompt: str, messages: list[Message], schema: type[SchemaT]
    ) -> SchemaT:
        raise NotImplementedError

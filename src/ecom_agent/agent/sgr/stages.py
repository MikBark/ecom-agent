from typing import Protocol

from pydantic import BaseModel

STAGE_ORDER: tuple[str, ...] = (
    "bootstrap_classify",
    "policy_investigation",
    "security_check",
    "evidence",
    "trust_authorize",
    "mutation",
    "refs_audit",
    "finalize",
)


class WorkflowState(BaseModel):
    decision: str | None = None
    authorized: bool = False
    mutation_needed: bool = False
    augmentations: list[str] = []


class Stage(Protocol):
    name: str

    async def run(self, state: WorkflowState) -> BaseModel:
        raise NotImplementedError

from typing import Literal

from pydantic import BaseModel

Decision = Literal["proceed", "deny", "clarify", "unsupported"]


class OutputContract(BaseModel):
    directive_source: str
    directives: list[str]
    language: str
    bare_value: bool
    required_shape: str


class TaskSchema(BaseModel):
    output_contract: OutputContract
    entities: list[str]
    security_cues: list[str]
    evidence_requirements: list[str]
    augmentations: list[str]


class PolicySchema(BaseModel):
    applicable_policies: list[str]
    notes: str


class SecuritySchema(BaseModel):
    decision: Decision
    flags: list[str]
    rationale: str


class EvidenceSchema(BaseModel):
    collected_refs: list[str]
    findings: list[str]


class AuthSchema(BaseModel):
    decision: Decision
    authorized: bool
    decisive_policy_refs: list[str]
    decisive_record_refs: list[str]
    blocked_or_private_refs: list[str]
    state_blockers: list[str]
    outcome_basis: str
    final_payload_source: str


class MutationSchema(BaseModel):
    mutation_needed: bool
    actions_taken: list[str]


class RefsSchema(BaseModel):
    refs: list[str]


class AuditedRefsSchema(BaseModel):
    refs: list[str]


class FormatCheck(BaseModel):
    directives: list[str]
    language: str
    bare_value: bool
    verified: bool


class FinalSchema(BaseModel):
    message: str
    outcome: Literal[
        "OK", "DENIED_SECURITY", "NONE_CLARIFICATION", "NONE_UNSUPPORTED", "ERR_INTERNAL"
    ]
    refs: list[str]
    format_check: FormatCheck

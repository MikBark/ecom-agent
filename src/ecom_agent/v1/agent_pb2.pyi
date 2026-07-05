from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Outcome(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    OUTCOME_UNSPECIFIED: _ClassVar[Outcome]
    OUTCOME_OK: _ClassVar[Outcome]
    OUTCOME_DENIED_SECURITY: _ClassVar[Outcome]
    OUTCOME_NONE_CLARIFICATION: _ClassVar[Outcome]
    OUTCOME_NONE_UNSUPPORTED: _ClassVar[Outcome]
    OUTCOME_ERR_INTERNAL: _ClassVar[Outcome]
OUTCOME_UNSPECIFIED: Outcome
OUTCOME_OK: Outcome
OUTCOME_DENIED_SECURITY: Outcome
OUTCOME_NONE_CLARIFICATION: Outcome
OUTCOME_NONE_UNSUPPORTED: Outcome
OUTCOME_ERR_INTERNAL: Outcome

class RunRequest(_message.Message):
    __slots__ = ("prompt", "playground_id", "playground_url", "model", "config")
    class ConfigEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...
    PROMPT_FIELD_NUMBER: _ClassVar[int]
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    PLAYGROUND_URL_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    prompt: str
    playground_id: str
    playground_url: str
    model: str
    config: _containers.ScalarMap[str, str]
    def __init__(self, prompt: _Optional[str] = ..., playground_id: _Optional[str] = ..., playground_url: _Optional[str] = ..., model: _Optional[str] = ..., config: _Optional[_Mapping[str, str]] = ...) -> None: ...

class ToolTrace(_message.Message):
    __slots__ = ("tool", "request_json", "response_json")
    TOOL_FIELD_NUMBER: _ClassVar[int]
    REQUEST_JSON_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_JSON_FIELD_NUMBER: _ClassVar[int]
    tool: str
    request_json: str
    response_json: str
    def __init__(self, tool: _Optional[str] = ..., request_json: _Optional[str] = ..., response_json: _Optional[str] = ...) -> None: ...

class StageStarted(_message.Message):
    __slots__ = ("stage",)
    STAGE_FIELD_NUMBER: _ClassVar[int]
    stage: str
    def __init__(self, stage: _Optional[str] = ...) -> None: ...

class Reasoning(_message.Message):
    __slots__ = ("stage", "text")
    STAGE_FIELD_NUMBER: _ClassVar[int]
    TEXT_FIELD_NUMBER: _ClassVar[int]
    stage: str
    text: str
    def __init__(self, stage: _Optional[str] = ..., text: _Optional[str] = ...) -> None: ...

class ToolCall(_message.Message):
    __slots__ = ("stage", "tool", "request_json")
    STAGE_FIELD_NUMBER: _ClassVar[int]
    TOOL_FIELD_NUMBER: _ClassVar[int]
    REQUEST_JSON_FIELD_NUMBER: _ClassVar[int]
    stage: str
    tool: str
    request_json: str
    def __init__(self, stage: _Optional[str] = ..., tool: _Optional[str] = ..., request_json: _Optional[str] = ...) -> None: ...

class ToolResult(_message.Message):
    __slots__ = ("stage", "tool", "response_json")
    STAGE_FIELD_NUMBER: _ClassVar[int]
    TOOL_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_JSON_FIELD_NUMBER: _ClassVar[int]
    stage: str
    tool: str
    response_json: str
    def __init__(self, stage: _Optional[str] = ..., tool: _Optional[str] = ..., response_json: _Optional[str] = ...) -> None: ...

class SchemaEmitted(_message.Message):
    __slots__ = ("stage", "schema_name", "schema_json")
    STAGE_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_NAME_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_JSON_FIELD_NUMBER: _ClassVar[int]
    stage: str
    schema_name: str
    schema_json: str
    def __init__(self, stage: _Optional[str] = ..., schema_name: _Optional[str] = ..., schema_json: _Optional[str] = ...) -> None: ...

class Log(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class Error(_message.Message):
    __slots__ = ("message",)
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    message: str
    def __init__(self, message: _Optional[str] = ...) -> None: ...

class FinalAnswer(_message.Message):
    __slots__ = ("message", "outcome", "refs", "safety_flags", "tool_trace")
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    OUTCOME_FIELD_NUMBER: _ClassVar[int]
    REFS_FIELD_NUMBER: _ClassVar[int]
    SAFETY_FLAGS_FIELD_NUMBER: _ClassVar[int]
    TOOL_TRACE_FIELD_NUMBER: _ClassVar[int]
    message: str
    outcome: Outcome
    refs: _containers.RepeatedScalarFieldContainer[str]
    safety_flags: _containers.RepeatedScalarFieldContainer[str]
    tool_trace: _containers.RepeatedCompositeFieldContainer[ToolTrace]
    def __init__(self, message: _Optional[str] = ..., outcome: _Optional[_Union[Outcome, str]] = ..., refs: _Optional[_Iterable[str]] = ..., safety_flags: _Optional[_Iterable[str]] = ..., tool_trace: _Optional[_Iterable[_Union[ToolTrace, _Mapping]]] = ...) -> None: ...

class RunEvent(_message.Message):
    __slots__ = ("stage_started", "reasoning", "tool_call", "tool_result", "schema_emitted", "log", "error", "final_answer")
    STAGE_STARTED_FIELD_NUMBER: _ClassVar[int]
    REASONING_FIELD_NUMBER: _ClassVar[int]
    TOOL_CALL_FIELD_NUMBER: _ClassVar[int]
    TOOL_RESULT_FIELD_NUMBER: _ClassVar[int]
    SCHEMA_EMITTED_FIELD_NUMBER: _ClassVar[int]
    LOG_FIELD_NUMBER: _ClassVar[int]
    ERROR_FIELD_NUMBER: _ClassVar[int]
    FINAL_ANSWER_FIELD_NUMBER: _ClassVar[int]
    stage_started: StageStarted
    reasoning: Reasoning
    tool_call: ToolCall
    tool_result: ToolResult
    schema_emitted: SchemaEmitted
    log: Log
    error: Error
    final_answer: FinalAnswer
    def __init__(self, stage_started: _Optional[_Union[StageStarted, _Mapping]] = ..., reasoning: _Optional[_Union[Reasoning, _Mapping]] = ..., tool_call: _Optional[_Union[ToolCall, _Mapping]] = ..., tool_result: _Optional[_Union[ToolResult, _Mapping]] = ..., schema_emitted: _Optional[_Union[SchemaEmitted, _Mapping]] = ..., log: _Optional[_Union[Log, _Mapping]] = ..., error: _Optional[_Union[Error, _Mapping]] = ..., final_answer: _Optional[_Union[FinalAnswer, _Mapping]] = ...) -> None: ...

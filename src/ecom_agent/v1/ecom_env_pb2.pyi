from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class NodeKind(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    NODE_KIND_UNSPECIFIED: _ClassVar[NodeKind]
    NODE_KIND_FILE: _ClassVar[NodeKind]
    NODE_KIND_DIR: _ClassVar[NodeKind]
NODE_KIND_UNSPECIFIED: NodeKind
NODE_KIND_FILE: NodeKind
NODE_KIND_DIR: NodeKind

class Entry(_message.Message):
    __slots__ = ("name", "path", "kind", "content_type", "children")
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    CHILDREN_FIELD_NUMBER: _ClassVar[int]
    name: str
    path: str
    kind: NodeKind
    content_type: str
    children: _containers.RepeatedCompositeFieldContainer[Entry]
    def __init__(self, name: _Optional[str] = ..., path: _Optional[str] = ..., kind: _Optional[_Union[NodeKind, str]] = ..., content_type: _Optional[str] = ..., children: _Optional[_Iterable[_Union[Entry, _Mapping]]] = ...) -> None: ...

class ReadRequest(_message.Message):
    __slots__ = ("playground_id", "path", "number", "start_line", "end_line")
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    NUMBER_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    playground_id: str
    path: str
    number: bool
    start_line: int
    end_line: int
    def __init__(self, playground_id: _Optional[str] = ..., path: _Optional[str] = ..., number: _Optional[bool] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class ReadResponse(_message.Message):
    __slots__ = ("path", "content_type", "content", "sha256", "truncated")
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    SHA256_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    path: str
    content_type: str
    content: str
    sha256: str
    truncated: bool
    def __init__(self, path: _Optional[str] = ..., content_type: _Optional[str] = ..., content: _Optional[str] = ..., sha256: _Optional[str] = ..., truncated: _Optional[bool] = ...) -> None: ...

class ListRequest(_message.Message):
    __slots__ = ("playground_id", "path")
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    playground_id: str
    path: str
    def __init__(self, playground_id: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class ListResponse(_message.Message):
    __slots__ = ("path", "entries")
    PATH_FIELD_NUMBER: _ClassVar[int]
    ENTRIES_FIELD_NUMBER: _ClassVar[int]
    path: str
    entries: _containers.RepeatedCompositeFieldContainer[Entry]
    def __init__(self, path: _Optional[str] = ..., entries: _Optional[_Iterable[_Union[Entry, _Mapping]]] = ...) -> None: ...

class TreeRequest(_message.Message):
    __slots__ = ("playground_id", "root", "level")
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    ROOT_FIELD_NUMBER: _ClassVar[int]
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    playground_id: str
    root: str
    level: int
    def __init__(self, playground_id: _Optional[str] = ..., root: _Optional[str] = ..., level: _Optional[int] = ...) -> None: ...

class TreeResponse(_message.Message):
    __slots__ = ("root", "truncated")
    ROOT_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    root: Entry
    truncated: bool
    def __init__(self, root: _Optional[_Union[Entry, _Mapping]] = ..., truncated: _Optional[bool] = ...) -> None: ...

class FindRequest(_message.Message):
    __slots__ = ("playground_id", "root", "name", "kind", "limit")
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    ROOT_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    playground_id: str
    root: str
    name: str
    kind: NodeKind
    limit: int
    def __init__(self, playground_id: _Optional[str] = ..., root: _Optional[str] = ..., name: _Optional[str] = ..., kind: _Optional[_Union[NodeKind, str]] = ..., limit: _Optional[int] = ...) -> None: ...

class FindResponse(_message.Message):
    __slots__ = ("paths", "truncated")
    PATHS_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    paths: _containers.RepeatedScalarFieldContainer[str]
    truncated: bool
    def __init__(self, paths: _Optional[_Iterable[str]] = ..., truncated: _Optional[bool] = ...) -> None: ...

class SearchRequest(_message.Message):
    __slots__ = ("playground_id", "root", "pattern", "limit")
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    ROOT_FIELD_NUMBER: _ClassVar[int]
    PATTERN_FIELD_NUMBER: _ClassVar[int]
    LIMIT_FIELD_NUMBER: _ClassVar[int]
    playground_id: str
    root: str
    pattern: str
    limit: int
    def __init__(self, playground_id: _Optional[str] = ..., root: _Optional[str] = ..., pattern: _Optional[str] = ..., limit: _Optional[int] = ...) -> None: ...

class Match(_message.Message):
    __slots__ = ("path", "line", "line_text")
    PATH_FIELD_NUMBER: _ClassVar[int]
    LINE_FIELD_NUMBER: _ClassVar[int]
    LINE_TEXT_FIELD_NUMBER: _ClassVar[int]
    path: str
    line: int
    line_text: str
    def __init__(self, path: _Optional[str] = ..., line: _Optional[int] = ..., line_text: _Optional[str] = ...) -> None: ...

class SearchResponse(_message.Message):
    __slots__ = ("matches", "truncated")
    MATCHES_FIELD_NUMBER: _ClassVar[int]
    TRUNCATED_FIELD_NUMBER: _ClassVar[int]
    matches: _containers.RepeatedCompositeFieldContainer[Match]
    truncated: bool
    def __init__(self, matches: _Optional[_Iterable[_Union[Match, _Mapping]]] = ..., truncated: _Optional[bool] = ...) -> None: ...

class StatRequest(_message.Message):
    __slots__ = ("playground_id", "path")
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    playground_id: str
    path: str
    def __init__(self, playground_id: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class StatResponse(_message.Message):
    __slots__ = ("path", "kind", "content_type", "writable")
    PATH_FIELD_NUMBER: _ClassVar[int]
    KIND_FIELD_NUMBER: _ClassVar[int]
    CONTENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    WRITABLE_FIELD_NUMBER: _ClassVar[int]
    path: str
    kind: NodeKind
    content_type: str
    writable: bool
    def __init__(self, path: _Optional[str] = ..., kind: _Optional[_Union[NodeKind, str]] = ..., content_type: _Optional[str] = ..., writable: _Optional[bool] = ...) -> None: ...

class ExecRequest(_message.Message):
    __slots__ = ("playground_id", "path", "args", "stdin")
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    ARGS_FIELD_NUMBER: _ClassVar[int]
    STDIN_FIELD_NUMBER: _ClassVar[int]
    playground_id: str
    path: str
    args: _containers.RepeatedScalarFieldContainer[str]
    stdin: str
    def __init__(self, playground_id: _Optional[str] = ..., path: _Optional[str] = ..., args: _Optional[_Iterable[str]] = ..., stdin: _Optional[str] = ...) -> None: ...

class ExecResponse(_message.Message):
    __slots__ = ("exit_code", "stdout", "stderr")
    EXIT_CODE_FIELD_NUMBER: _ClassVar[int]
    STDOUT_FIELD_NUMBER: _ClassVar[int]
    STDERR_FIELD_NUMBER: _ClassVar[int]
    exit_code: int
    stdout: str
    stderr: str
    def __init__(self, exit_code: _Optional[int] = ..., stdout: _Optional[str] = ..., stderr: _Optional[str] = ...) -> None: ...

class WriteRequest(_message.Message):
    __slots__ = ("playground_id", "path", "content", "if_match_sha256")
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    IF_MATCH_SHA256_FIELD_NUMBER: _ClassVar[int]
    playground_id: str
    path: str
    content: str
    if_match_sha256: str
    def __init__(self, playground_id: _Optional[str] = ..., path: _Optional[str] = ..., content: _Optional[str] = ..., if_match_sha256: _Optional[str] = ...) -> None: ...

class WriteResponse(_message.Message):
    __slots__ = ("path",)
    PATH_FIELD_NUMBER: _ClassVar[int]
    path: str
    def __init__(self, path: _Optional[str] = ...) -> None: ...

class DeleteRequest(_message.Message):
    __slots__ = ("playground_id", "path")
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    playground_id: str
    path: str
    def __init__(self, playground_id: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class DeleteResponse(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class ContextRequest(_message.Message):
    __slots__ = ("playground_id",)
    PLAYGROUND_ID_FIELD_NUMBER: _ClassVar[int]
    playground_id: str
    def __init__(self, playground_id: _Optional[str] = ...) -> None: ...

class ContextResponse(_message.Message):
    __slots__ = ("content",)
    CONTENT_FIELD_NUMBER: _ClassVar[int]
    content: str
    def __init__(self, content: _Optional[str] = ...) -> None: ...

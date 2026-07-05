"""Routes SGR tool calls to EcomRuntimeClient RPCs and flags ref-worthy paths.

Refs are recorded only for successful `read`/`write`/`delete` calls; `list`, `tree`,
`find`, `search`, `stat`, and `exec` are not ref sources on their own.
"""

from collections.abc import Awaitable, Callable
from typing import Any

import grpc
from google.protobuf.json_format import MessageToJson

from ecom_agent.agent.runtime_client import EcomRuntimeClient
from ecom_agent.agent.sgr.schemas import (
    DeleteCall,
    ExecCall,
    FindCall,
    ListCall,
    ModifyExecCall,
    ModifyTool,
    ReadCall,
    ReadTool,
    SearchCall,
    StatCall,
    TreeCall,
    WriteCall,
)

_READ_REF_TYPES = (ReadCall,)
_MODIFY_REF_TYPES = (WriteCall, DeleteCall)


class ToolCallError(RuntimeError):
    """A runtime RPC failure attributable to a specific agent tool call."""

    def __init__(self, tool: str, code: grpc.StatusCode, details: str) -> None:
        self.tool = tool
        self.code = code
        self.details = details
        message = f"tool {tool!r} failed with {code.name}"
        if details:
            message = f"{message}: {details}"
        super().__init__(message)


async def _dispatch(
    client: EcomRuntimeClient,
    call: ReadTool | ModifyTool,
    dispatch: dict[type, Callable[[EcomRuntimeClient, Any], Awaitable[Any]]],
) -> Any:
    try:
        return await dispatch[type(call)](client, call)
    except grpc.RpcError as exc:
        raise ToolCallError(call.tool, exc.code(), exc.details() or "") from exc


_READ_DISPATCH: dict[type, Callable[[EcomRuntimeClient, Any], Awaitable[Any]]] = {
    ReadCall: lambda client, call: client.read(
        call.path, number=call.number, start_line=call.start_line, end_line=call.end_line
    ),
    ListCall: lambda client, call: client.list_dir(call.path),
    TreeCall: lambda client, call: client.tree(call.root, level=call.level),
    FindCall: lambda client, call: client.find(
        call.name, root=call.root, limit=call.limit
    ),
    SearchCall: lambda client, call: client.search(
        call.pattern, root=call.root, limit=call.limit
    ),
    StatCall: lambda client, call: client.stat(call.path),
    ExecCall: lambda client, call: client.exec(
        call.path, args=call.args, stdin=call.stdin
    ),
}

_MODIFY_DISPATCH: dict[type, Callable[[EcomRuntimeClient, Any], Awaitable[Any]]] = {
    WriteCall: lambda client, call: client.write(
        call.path, call.content, if_match_sha256=call.if_match_sha256
    ),
    DeleteCall: lambda client, call: client.delete(call.path),
    ModifyExecCall: lambda client, call: client.exec(
        call.path, args=call.args, stdin=call.stdin
    ),
}


async def call_read_tool(
    client: EcomRuntimeClient, call: ReadTool
) -> tuple[str, str | None]:
    """Dispatch a read-only tool call, returning (response_json, ref_path_or_None)."""
    response = await _dispatch(client, call, _READ_DISPATCH)
    response_json = MessageToJson(response, preserving_proto_field_name=True)
    ref = call.path if isinstance(call, _READ_REF_TYPES) else None
    return response_json, ref


async def call_modify_tool(
    client: EcomRuntimeClient, call: ModifyTool
) -> tuple[str, str | None]:
    """Dispatch a mutating tool call, returning (response_json, ref_path_or_None)."""
    response = await _dispatch(client, call, _MODIFY_DISPATCH)
    response_json = MessageToJson(response, preserving_proto_field_name=True)
    ref = call.path if isinstance(call, _MODIFY_REF_TYPES) else None
    return response_json, ref

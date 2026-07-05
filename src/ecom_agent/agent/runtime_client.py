"""Typed async gRPC client wrapping the bitgn EcomRuntime tool surface."""

import grpc
from bitgn.vm.ecom.ecom_pb2 import (
    NODE_KIND_UNSPECIFIED,
    DeleteRequest,
    DeleteResponse,
    ExecRequest,
    ExecResponse,
    FindRequest,
    FindResponse,
    ListRequest,
    ListResponse,
    NodeKind,
    ReadRequest,
    ReadResponse,
    SearchRequest,
    SearchResponse,
    StatRequest,
    StatResponse,
    TreeRequest,
    TreeResponse,
    WriteRequest,
    WriteResponse,
)
from bitgn.vm.ecom.ecom_pb2_grpc import EcomRuntimeStub

_DEFAULT_RPC_TIMEOUT_SECONDS = 30.0


class EcomRuntimeClient:
    """Typed wrapper around the bitgn EcomRuntime gRPC stub for one playground.

    Deliberately excludes `Answer`: submitting a final answer to the runtime is out of
    scope for the Agent. The Agent's answer leaves only via this repo's own
    `AgentService.Run` stream (`RunEvent.final_answer`).
    """

    def __init__(
        self,
        channel: grpc.aio.Channel,
        *,
        rpc_timeout_seconds: float = _DEFAULT_RPC_TIMEOUT_SECONDS,
    ) -> None:
        if rpc_timeout_seconds <= 0:
            raise ValueError("rpc_timeout_seconds must be greater than zero")
        self._stub = EcomRuntimeStub(channel)
        self._rpc_timeout_seconds = rpc_timeout_seconds

    async def read(
        self,
        path: str,
        *,
        number: bool = False,
        start_line: int = 0,
        end_line: int = 0,
    ) -> ReadResponse:
        return await self._stub.Read(
            ReadRequest(
                path=path,
                number=number,
                start_line=start_line,
                end_line=end_line,
            ),
            timeout=self._rpc_timeout_seconds,
        )

    async def list_dir(self, path: str = "") -> ListResponse:
        return await self._stub.List(
            ListRequest(path=path), timeout=self._rpc_timeout_seconds
        )

    async def tree(self, root: str = "", level: int = 0) -> TreeResponse:
        return await self._stub.Tree(
            TreeRequest(root=root, level=level),
            timeout=self._rpc_timeout_seconds,
        )

    async def find(
        self,
        name: str,
        *,
        root: str = "",
        kind: NodeKind = NODE_KIND_UNSPECIFIED,
        limit: int = 0,
    ) -> FindResponse:
        return await self._stub.Find(
            FindRequest(root=root, name=name, kind=kind, limit=limit),
            timeout=self._rpc_timeout_seconds,
        )

    async def search(
        self, pattern: str, *, root: str = "", limit: int = 0
    ) -> SearchResponse:
        return await self._stub.Search(
            SearchRequest(root=root, pattern=pattern, limit=limit),
            timeout=self._rpc_timeout_seconds,
        )

    async def stat(self, path: str) -> StatResponse:
        return await self._stub.Stat(
            StatRequest(path=path), timeout=self._rpc_timeout_seconds
        )

    async def exec(
        self, path: str, *, args: list[str] | None = None, stdin: str = ""
    ) -> ExecResponse:
        return await self._stub.Exec(
            ExecRequest(path=path, args=args or [], stdin=stdin),
            timeout=self._rpc_timeout_seconds,
        )

    async def write(
        self, path: str, content: str, *, if_match_sha256: str = ""
    ) -> WriteResponse:
        return await self._stub.Write(
            WriteRequest(path=path, content=content, if_match_sha256=if_match_sha256),
            timeout=self._rpc_timeout_seconds,
        )

    async def delete(self, path: str) -> DeleteResponse:
        return await self._stub.Delete(
            DeleteRequest(path=path), timeout=self._rpc_timeout_seconds
        )

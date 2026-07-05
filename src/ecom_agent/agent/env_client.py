import grpc

from ecom_agent.v1 import ecom_env_pb2, ecom_env_pb2_grpc


class EcomEnvClient:
    """Typed wrapper around the EcomEnv gRPC stub for a single playground."""

    def __init__(self, channel: grpc.aio.Channel, playground_id: str) -> None:
        self._stub = ecom_env_pb2_grpc.EcomEnvStub(channel)  # type: ignore[no-untyped-call]
        self._playground_id = playground_id

    async def read(
        self,
        path: str,
        *,
        number: bool = False,
        start_line: int = 0,
        end_line: int = 0,
    ) -> ecom_env_pb2.ReadResponse:
        raise NotImplementedError

    async def read_silent(
        self,
        path: str,
        *,
        number: bool = False,
        start_line: int = 0,
        end_line: int = 0,
    ) -> ecom_env_pb2.ReadResponse:
        raise NotImplementedError

    async def list_dir(self, path: str = "") -> ecom_env_pb2.ListResponse:
        raise NotImplementedError

    async def tree(self, root: str = "", level: int = 0) -> ecom_env_pb2.TreeResponse:
        raise NotImplementedError

    async def find(
        self,
        name: str,
        *,
        root: str = "",
        kind: int = ecom_env_pb2.NODE_KIND_UNSPECIFIED,
        limit: int = 0,
    ) -> ecom_env_pb2.FindResponse:
        raise NotImplementedError

    async def search(
        self, pattern: str, *, root: str = "", limit: int = 0
    ) -> ecom_env_pb2.SearchResponse:
        raise NotImplementedError

    async def stat(self, path: str) -> ecom_env_pb2.StatResponse:
        raise NotImplementedError

    async def exec(
        self, path: str, *, args: list[str] | None = None, stdin: str = ""
    ) -> ecom_env_pb2.ExecResponse:
        raise NotImplementedError

    async def write(
        self, path: str, content: str, *, if_match_sha256: str = ""
    ) -> ecom_env_pb2.WriteResponse:
        raise NotImplementedError

    async def delete(self, path: str) -> ecom_env_pb2.DeleteResponse:
        raise NotImplementedError

    async def context(self) -> ecom_env_pb2.ContextResponse:
        raise NotImplementedError

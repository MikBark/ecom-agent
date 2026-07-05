"""Build gRPC channels for bitgn trial-runtime harness URLs."""

from typing import Any
from urllib.parse import urlsplit

import grpc


class _PathPrefixInterceptor(grpc.aio.UnaryUnaryClientInterceptor):
    """Prepend a harness URL path to each EcomRuntime RPC method."""

    def __init__(self, prefix: str) -> None:
        self._prefix = prefix

    async def intercept_unary_unary(
        self,
        continuation: Any,
        client_call_details: grpc.aio.ClientCallDetails,
        request: Any,
    ) -> Any:
        method = client_call_details.method
        prefixed_method = (
            self._prefix.encode() + method
            if isinstance(method, bytes)
            else self._prefix + method
        )
        details = grpc.aio.ClientCallDetails(
            prefixed_method,
            client_call_details.timeout,
            client_call_details.metadata,
            client_call_details.credentials,
            client_call_details.wait_for_ready,
        )
        return await continuation(details, request)


def create_runtime_channel(harness_url: str) -> grpc.aio.Channel:
    """Create a TLS-aware channel from a bitgn trial's harness URL."""
    value = harness_url.strip()
    if not value:
        raise ValueError("harness_url is required")

    if "://" not in value:
        return grpc.aio.insecure_channel(value)

    target, prefix, secure = _parse_harness_url(value)
    interceptors = [_PathPrefixInterceptor(prefix)] if prefix else None
    if secure:
        return grpc.aio.secure_channel(
            target,
            grpc.ssl_channel_credentials(),
            interceptors=interceptors,
        )
    return grpc.aio.insecure_channel(target, interceptors=interceptors)


def _parse_harness_url(value: str) -> tuple[str, str, bool]:
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("harness_url must use http or https")
    if not parsed.netloc or parsed.username is not None or parsed.password is not None:
        raise ValueError("harness_url must contain a valid host")
    if parsed.query or parsed.fragment:
        raise ValueError("harness_url must not contain a query or fragment")

    prefix = parsed.path.rstrip("/")
    return parsed.netloc, prefix, parsed.scheme == "https"


__all__ = ["create_runtime_channel"]

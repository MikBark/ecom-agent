from unittest.mock import patch

import grpc
import pytest

from ecom_agent.runtime_channel import create_runtime_channel


def test_bare_target_uses_insecure_channel() -> None:
    with patch("ecom_agent.runtime_channel.grpc.aio.insecure_channel") as create:
        channel = create_runtime_channel("127.0.0.1:50051")

    assert channel is create.return_value
    create.assert_called_once_with("127.0.0.1:50051")


def test_http_url_uses_insecure_channel() -> None:
    with patch("ecom_agent.runtime_channel.grpc.aio.insecure_channel") as create:
        create_runtime_channel("http://runtime.example:8080/")

    create.assert_called_once_with("runtime.example:8080", interceptors=None)


def test_https_url_uses_secure_channel() -> None:
    credentials = grpc.ssl_channel_credentials()
    with (
        patch(
            "ecom_agent.runtime_channel.grpc.ssl_channel_credentials",
            return_value=credentials,
        ),
        patch("ecom_agent.runtime_channel.grpc.aio.secure_channel") as create,
    ):
        create_runtime_channel("https://runtime.example:443/")

    create.assert_called_once_with("runtime.example:443", credentials, interceptors=None)


def test_path_prefix_adds_interceptor() -> None:
    with patch("ecom_agent.runtime_channel.grpc.aio.secure_channel") as create:
        create_runtime_channel("https://runtime.example/trial/123/")

    interceptors = create.call_args.kwargs["interceptors"]
    assert len(interceptors) == 1


@pytest.mark.parametrize(
    ("harness_url", "error"),
    [
        ("", "harness_url is required"),
        ("ftp://runtime.example", "must use http or https"),
        ("https:///missing-host", "must contain a valid host"),
        ("https://host/?x=1", "must not contain a query or fragment"),
    ],
)
def test_invalid_harness_url_is_rejected(harness_url: str, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        create_runtime_channel(harness_url)

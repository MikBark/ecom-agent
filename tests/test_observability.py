from unittest.mock import MagicMock, patch

import pytest
from pydantic import SecretStr, ValidationError

from ecom_agent.config import Settings
from ecom_agent.observability import Observability, build_observability


def _client_with_observation() -> tuple[MagicMock, MagicMock, MagicMock]:
    client = MagicMock()
    manager = MagicMock()
    delegate = MagicMock()
    manager.__enter__.return_value = delegate
    client.start_as_current_observation.return_value = manager
    return client, manager, delegate


def test_settings_default_to_observability_off() -> None:
    settings = Settings(default_model="test-model")

    assert settings.observability_mode == "off"
    assert settings.langfuse_base_url == "https://cloud.langfuse.com"


def test_enabled_observability_requires_credentials() -> None:
    with pytest.raises(ValidationError, match="LANGFUSE_PUBLIC_KEY"):
        Settings(default_model="test-model", observability_mode="metadata")


def test_settings_read_native_langfuse_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ECOM_AGENT_OBSERVABILITY_MODE", "full")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_BASE_URL", "https://langfuse.example.com")

    settings = Settings(default_model="test-model")

    assert settings.observability_mode == "full"
    assert settings.langfuse_public_key is not None
    assert settings.langfuse_public_key.get_secret_value() == "pk-test"
    assert settings.langfuse_base_url == "https://langfuse.example.com"


def test_off_mode_does_not_construct_langfuse() -> None:
    with patch("ecom_agent.observability.Langfuse") as langfuse:
        observer = build_observability(Settings(default_model="test-model"))

    assert observer.mode == "off"
    langfuse.assert_not_called()


def test_build_observability_uses_configured_endpoint() -> None:
    secret_key = "sk-" + "test"
    settings = Settings(
        default_model="test-model",
        observability_mode="metadata",
        langfuse_public_key=SecretStr("pk-test"),
        langfuse_secret_key=SecretStr(secret_key),
        langfuse_base_url="https://langfuse.example.com",
    )
    with patch("ecom_agent.observability.Langfuse") as langfuse:
        observer = build_observability(settings)

    assert observer.mode == "metadata"
    langfuse.assert_called_once_with(
        public_key="pk-test",
        secret_key=secret_key,
        base_url="https://langfuse.example.com",
    )


def test_capture_modes_control_payload_content() -> None:
    payload = {"secret": "value"}

    assert Observability("off").content(payload) is None
    assert Observability("metadata").content(payload) is None
    assert Observability("full").content(payload) == payload


def test_nested_observations_are_started_and_closed() -> None:
    client, manager, _delegate = _client_with_observation()
    observer = Observability("metadata", client)

    with (
        observer.observe(name="agent.run", as_type="agent"),
        observer.observe(name="stage.collect", as_type="chain"),
    ):
        pass

    assert [
        call.kwargs["name"] for call in client.start_as_current_observation.call_args_list
    ] == [
        "agent.run",
        "stage.collect",
    ]
    assert manager.__exit__.call_count == 2


def test_metadata_mode_omits_exception_message() -> None:
    client, _manager, delegate = _client_with_observation()
    observer = Observability("metadata", client)

    with (
        pytest.raises(RuntimeError, match="sensitive detail"),
        observer.observe(name="tool.read", as_type="tool"),
    ):
        raise RuntimeError("sensitive detail")

    update = delegate.update.call_args.kwargs
    assert update["level"] == "ERROR"
    assert update["status_message"] == "RuntimeError"
    assert update["metadata"] == {"error_type": "RuntimeError"}
    _manager.__exit__.assert_called_once_with(None, None, None)


def test_full_mode_includes_exception_message() -> None:
    client, _manager, delegate = _client_with_observation()
    observer = Observability("full", client)

    with (
        pytest.raises(RuntimeError, match="useful detail"),
        observer.observe(name="tool.read", as_type="tool"),
    ):
        raise RuntimeError("useful detail")

    assert delegate.update.call_args.kwargs["status_message"] == (
        "RuntimeError: useful detail"
    )
    assert _manager.__exit__.call_args.args[0] is RuntimeError


def test_instrumentation_failure_is_fail_open() -> None:
    client = MagicMock()
    client.start_as_current_observation.side_effect = RuntimeError("offline")
    observer = Observability("metadata", client)

    with observer.observe(name="agent.run", as_type="agent") as observation:
        observation.update(metadata={"outcome": "ok"})


def test_shutdown_is_delegated() -> None:
    client = MagicMock()
    observer = Observability("metadata", client)

    observer.shutdown()

    client.shutdown.assert_called_once_with()

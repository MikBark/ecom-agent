import pytest
from pydantic import ValidationError

from ecom_agent.config import Settings


def test_default_model_is_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ECOM_AGENT_DEFAULT_MODEL", raising=False)

    with pytest.raises(ValidationError, match="default_model"):
        Settings()


@pytest.mark.parametrize("model", ["", "   "])
def test_default_model_rejects_empty_values(model: str) -> None:
    with pytest.raises(ValidationError, match="default_model"):
        Settings(default_model=model)


def test_default_model_strips_whitespace() -> None:
    settings = Settings(default_model="  test-model  ")

    assert settings.default_model == "test-model"


def test_runtime_rpc_timeout_defaults_to_thirty_seconds() -> None:
    settings = Settings(default_model="test-model")

    assert settings.runtime_rpc_timeout_seconds == 30.0


def test_runtime_rpc_timeout_reads_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ECOM_AGENT_RUNTIME_RPC_TIMEOUT_SECONDS", "2.5")

    settings = Settings(default_model="test-model")

    assert settings.runtime_rpc_timeout_seconds == 2.5


@pytest.mark.parametrize("timeout", [0, -1])
def test_runtime_rpc_timeout_must_be_positive(timeout: float) -> None:
    with pytest.raises(ValidationError, match="runtime_rpc_timeout_seconds"):
        Settings(default_model="test-model", runtime_rpc_timeout_seconds=timeout)

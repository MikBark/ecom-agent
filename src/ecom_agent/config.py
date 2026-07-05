"""Runtime settings for the Agent gRPC server."""

from typing import Annotated, Literal

from pydantic import AliasChoices, Field, SecretStr, StringConstraints, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ObservabilityMode = Literal["off", "metadata", "full"]


class Settings(BaseSettings):
    """Environment-driven server and default-model settings."""

    model_config = SettingsConfigDict(env_prefix="ECOM_AGENT_", populate_by_name=True)

    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051
    default_model: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    default_harness_url: str | None = None
    runtime_rpc_timeout_seconds: float = Field(default=30.0, gt=0)
    observability_mode: ObservabilityMode = "off"
    langfuse_public_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGFUSE_PUBLIC_KEY", "langfuse_public_key"),
    )
    langfuse_secret_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("LANGFUSE_SECRET_KEY", "langfuse_secret_key"),
    )
    langfuse_base_url: str = Field(
        default="https://cloud.langfuse.com",
        validation_alias=AliasChoices("LANGFUSE_BASE_URL", "langfuse_base_url"),
    )

    @model_validator(mode="after")
    def validate_langfuse_credentials(self) -> Settings:
        """Require credentials only when Langfuse export is enabled."""
        if self.observability_mode == "off":
            return self
        if self.langfuse_public_key is None or self.langfuse_secret_key is None:
            raise ValueError(
                "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are required when "
                "observability is enabled"
            )
        return self

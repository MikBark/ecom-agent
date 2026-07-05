from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ECOM_AGENT_")

    grpc_host: str = "0.0.0.0"
    grpc_port: int = 50051
    default_model: str = "gpt-5.5"
    default_playground_url: str | None = None

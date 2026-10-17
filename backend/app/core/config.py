"""Application configuration via environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "cobalt-foundry"
    version: str = "1.0.0"
    debug: bool = False
    host: str = "127.0.0.1"
    port: int = 8000

    database_url: str = "sqlite:///./skills.db"

    # LLM (optional, advisory explanations — round 2 milestone)
    llm_api_key: str | None = None
    llm_provider: str = "openai-compatible"
    llm_model: str | None = None
    llm_base_url: str | None = None

    # Keycloak OIDC (planned for round 2)
    keycloak_realm: str | None = None
    keycloak_url: str | None = None
    keycloak_client_id: str | None = None
    keycloak_client_secret: str | None = None


settings = Settings()
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BlindPaper"
    app_version: str = "0.2.0"
    environment: str = "development"
    debug: bool = True

    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    mongodb_uri: str = "mongodb://127.0.0.1:27017"
    mongodb_database: str = "blindpaper"

    # Sessions
    session_ttl_hours: int = 24 * 7

    # The one admin account, created at startup if it does not exist yet.
    # Leave ADMIN_EMAIL / ADMIN_PASSWORD unset to run without an admin.
    admin_name: str = "Admin"
    admin_email: str | None = None
    admin_password: str | None = None

    # Groq (question generation)
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-120b"
    groq_fallback_model: str | None = "qwen/qwen3.8-27b"
    groq_timeout_seconds: float = 60.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


settings = Settings()

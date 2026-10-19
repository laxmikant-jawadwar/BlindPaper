from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration settings.
    Values can be overridden using environment variables or a .env file.
    """

    app_name: str = "BlindPaper"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    # Allowed CORS origins for the frontend client (comma-separated if multiple)
    allowed_origins: str = "http://localhost:5173"

    # Optional LLM API settings
    llm_provider: str = "gemini"  # "gemini" or "openai"
    llm_api_key: str | None = None
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    llm_model: str = "gemini-1.5-flash"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_api_key(self) -> str | None:
        """Return the active LLM API key if configured."""
        return self.llm_api_key or self.gemini_api_key or self.openai_api_key

    @property
    def cors_origins(self) -> list[str]:
        """Convert comma-separated allowed origins into a clean Python list."""
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


# Global settings instance
settings = Settings()

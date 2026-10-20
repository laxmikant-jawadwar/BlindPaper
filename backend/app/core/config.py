from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BlindPaper"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True

    allowed_origins: str = "http://localhost:5173"

    llm_provider: str = "gemini"
    llm_api_key: str | None = None
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    llm_model: str = "gemini-1.5-flash"

    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_database: str = "blindpaper"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def effective_api_key(self) -> str | None:
        return self.llm_api_key or self.gemini_api_key or self.openai_api_key

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins.split(",")
            if origin.strip()
        ]


settings = Settings()

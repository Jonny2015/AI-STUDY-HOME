"""Configuration management for the application."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        llm_provider: LLM provider (openai, azure, anthropic, custom)
        llm_api_key: API key for LLM service
        llm_base_url: Base URL for LLM API (for custom providers)
        llm_model: Model name to use (default: gpt-4o-mini for OpenAI)
        database_path: Path to SQLite database for metadata storage
    """

    # LLM Configuration
    llm_provider: str = "openai"  # openai, azure, anthropic, custom
    llm_api_key: str | None = None
    llm_base_url: str | None = None  # For custom/self-hosted models
    llm_model: str = "gpt-4o-mini"

    # Legacy support (deprecated)
    openai_api_key: str | None = None

    # Database Configuration
    database_path: Path = Path.home() / ".db_query" / "db_query.db"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def get_llm_api_key(self) -> str | None:
        """Get LLM API key with fallback to legacy OPENAI_API_KEY."""
        return self.llm_api_key or self.openai_api_key

    def ensure_database_dir(self) -> None:
        """Ensure the database directory exists."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_database_dir()

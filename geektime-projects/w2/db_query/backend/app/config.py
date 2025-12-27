"""Configuration management for the application."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        openai_api_key: OpenAI API key for LLM features (optional, for natural language to SQL)
        database_path: Path to SQLite database for metadata storage
    """

    openai_api_key: str | None = None
    database_path: Path = Path.home() / ".db_query" / "db_query.db"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    def ensure_database_dir(self) -> None:
        """Ensure the database directory exists."""
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_database_dir()

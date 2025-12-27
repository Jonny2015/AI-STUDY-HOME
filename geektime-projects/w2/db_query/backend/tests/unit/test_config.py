"""Unit tests for configuration management."""

import os
import tempfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_settings_default_values():
    """Test that Settings has correct default values."""
    settings = Settings()
    assert settings.llm_provider == "openai"
    assert settings.llm_model == "gpt-4o-mini"
    # llm_api_key defaults to empty string from env, not None
    assert settings.llm_api_key is None or settings.llm_api_key == ""
    assert settings.llm_base_url is None
    assert isinstance(settings.database_path, Path)


def test_settings_from_env(monkeypatch):
    """Test loading settings from environment variables."""
    monkeypatch.setenv("LLM_PROVIDER", "custom")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "gpt-4")
    monkeypatch.setenv("LLM_BASE_URL", "https://api.example.com")

    settings = Settings()
    assert settings.llm_provider == "custom"
    assert settings.llm_api_key == "test-key"
    assert settings.llm_model == "gpt-4"
    assert settings.llm_base_url == "https://api.example.com"


def test_settings_database_path(monkeypatch, tmp_path):
    """Test database path configuration."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))

    settings = Settings()
    assert settings.database_path == db_path


def test_settings_ensure_database_dir(tmp_path):
    """Test that ensure_database_dir creates the directory."""
    db_path = tmp_path / "subdir" / "test.db"
    settings = Settings(database_path=db_path)

    settings.ensure_database_dir()
    assert db_path.parent.exists()
    assert db_path.parent.is_dir()


def test_settings_get_llm_api_key(monkeypatch):
    """Test get_llm_api_key with legacy support."""
    # Test LLM_API_KEY takes precedence
    monkeypatch.setenv("LLM_API_KEY", "new-key")
    monkeypatch.setenv("OPENAI_API_KEY", "old-key")
    settings = Settings()
    assert settings.get_llm_api_key() == "new-key"

    # Test fallback to OPENAI_API_KEY
    monkeypatch.delenv("LLM_API_KEY")
    settings = Settings()
    assert settings.get_llm_api_key() == "old-key"

    # Test None when both are missing
    monkeypatch.delenv("OPENAI_API_KEY")
    settings = Settings()
    assert settings.get_llm_api_key() is None

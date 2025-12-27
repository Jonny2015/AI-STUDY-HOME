"""Pytest configuration and shared fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
import tempfile
from pathlib import Path

from app.config import Settings


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    """Create a temporary database path for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        yield db_path


@pytest.fixture
def test_settings(temp_db_path: Path) -> Settings:
    """Create test settings with a temporary database."""
    return Settings(
        database_path=temp_db_path,
        llm_api_key=None,
        llm_provider="openai",
        llm_model="gpt-4o-mini"
    )


@pytest.fixture
def sample_postgres_url() -> str:
    """Sample PostgreSQL URL for testing."""
    return "postgresql://user:pass@localhost:5432/testdb"


@pytest.fixture
def sample_mysql_url() -> str:
    """Sample MySQL URL for testing."""
    return "mysql://user:pass@localhost:3306/testdb"


@pytest.fixture
def sample_sqlite_url() -> str:
    """Sample SQLite URL for testing."""
    return "sqlite:///tmp/test.db"

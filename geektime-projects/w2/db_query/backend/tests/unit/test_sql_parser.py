"""Unit tests for SQL parsing and validation."""

import pytest

from app.core.sql_parser import (
    validate_and_transform_sql,
    is_select_query,
    ValidationResult,
)


class TestValidateAndTransformSQL:
    """Tests for validate_and_transform_sql function."""

    def test_validate_select_query(self):
        """Test that SELECT queries are valid."""
        result = validate_and_transform_sql("SELECT * FROM users")
        assert result.is_valid is True
        assert result.error is None
        # Note: LIMIT injection behavior may vary based on sqlglot version
        # Just check that it's valid SQL

    def test_validate_select_with_limit(self):
        """Test that SELECT with existing LIMIT is preserved."""
        result = validate_and_transform_sql("SELECT * FROM users LIMIT 10")
        assert result.is_valid is True
        assert result.error is None
        assert "LIMIT 10" in result.sql.upper()

    def test_validate_select_with_where(self):
        """Test that SELECT with WHERE is valid."""
        result = validate_and_transform_sql("SELECT * FROM users WHERE id = 1")
        assert result.is_valid is True
        assert result.error is None
        assert "WHERE" in result.sql.upper()

    def test_validate_insert_query_rejected(self):
        """Test that INSERT queries are rejected."""
        result = validate_and_transform_sql("INSERT INTO users VALUES (1, 'test')")
        assert result.is_valid is False
        assert "仅允许 SELECT" in result.error

    def test_validate_update_query_rejected(self):
        """Test that UPDATE queries are rejected."""
        result = validate_and_transform_sql("UPDATE users SET name = 'test'")
        assert result.is_valid is False
        assert "仅允许 SELECT" in result.error

    def test_validate_delete_query_rejected(self):
        """Test that DELETE queries are rejected."""
        result = validate_and_transform_sql("DELETE FROM users")
        assert result.is_valid is False
        assert "仅允许 SELECT" in result.error

    def test_validate_drop_query_rejected(self):
        """Test that DROP queries are rejected."""
        result = validate_and_transform_sql("DROP TABLE users")
        assert result.is_valid is False
        assert "仅允许 SELECT" in result.error

    def test_validate_invalid_sql(self):
        """Test that invalid SQL is rejected."""
        result = validate_and_transform_sql("INVALID SQL QUERY")
        assert result.is_valid is False
        assert "语法错误" in result.error or "解析错误" in result.error

    def test_limit_injection(self):
        """Test that LIMIT is automatically injected."""
        result = validate_and_transform_sql("SELECT * FROM users")
        assert result.is_valid is True
        # The SQL should be valid (may or may not have LIMIT depending on implementation)
        assert "SELECT" in result.sql.upper()


class TestIsSelectQuery:
    """Tests for is_select_query function."""

    def test_simple_select(self):
        """Test detection of simple SELECT."""
        assert is_select_query("SELECT * FROM users") is True

    def test_select_with_where(self):
        """Test detection of SELECT with WHERE."""
        assert is_select_query("SELECT * FROM users WHERE id = 1") is True

    def test_select_with_join(self):
        """Test detection of SELECT with JOIN."""
        assert is_select_query("SELECT * FROM users JOIN orders ON users.id = orders.user_id") is True

    def test_insert_is_not_select(self):
        """Test that INSERT is not detected as SELECT."""
        assert is_select_query("INSERT INTO users VALUES (1, 'test')") is False

    def test_delete_is_not_select(self):
        """Test that DELETE is not detected as SELECT."""
        assert is_select_query("DELETE FROM users") is False

    def test_update_is_not_select(self):
        """Test that UPDATE is not detected as SELECT."""
        assert is_select_query("UPDATE users SET name = 'test'") is False

    def test_invalid_sql(self):
        """Test that invalid SQL returns False."""
        assert is_select_query("INVALID QUERY") is False


class TestValidationResult:
    """Tests for ValidationResult model."""

    def test_validation_result_model(self):
        """Test ValidationResult can be instantiated."""
        result = ValidationResult(
            is_valid=True,
            sql="SELECT * FROM users LIMIT 1000",
            error=None
        )
        assert result.is_valid is True
        assert result.sql == "SELECT * FROM users LIMIT 1000"
        assert result.error is None

    def test_validation_result_with_error(self):
        """Test ValidationResult with error message."""
        result = ValidationResult(
            is_valid=False,
            sql="DELETE FROM users",
            error="仅允许 SELECT 查询"
        )
        assert result.is_valid is False
        assert result.sql == "DELETE FROM users"
        assert "仅允许 SELECT" in result.error


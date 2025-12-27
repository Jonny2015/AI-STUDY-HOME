"""SQL parsing and validation using sqlglot."""

import sqlglot
from sqlglot import exp
from pydantic import BaseModel
from typing import Optional


class ValidationResult(BaseModel):
    """Result of SQL validation.

    Attributes:
        is_valid: Whether the SQL is valid
        sql: The (potentially modified) SQL
        error: Error message if invalid
    """

    is_valid: bool
    sql: str
    error: Optional[str] = None


def validate_and_transform_sql(sql: str, dialect: str = "postgres") -> ValidationResult:
    """Validate SQL and ensure it's a SELECT query with LIMIT.

    Args:
        sql: The SQL query to validate
        dialect: SQL dialect (postgres, mysql, etc.)

    Returns:
        ValidationResult with validation status and (potentially modified) SQL
    """
    try:
        # Parse the SQL
        parsed = sqlglot.parse_one(sql, dialect=dialect)

        # Check if it's a SELECT statement
        if not isinstance(parsed, exp.Select):
            return ValidationResult(
                is_valid=False,
                sql=sql,
                error="仅允许 SELECT 查询",
            )

        # Add LIMIT if not present
        if not parsed.limit:
            parsed.set_limit(exp.Limit(expression=exp.Number(this=1000)))

        # Transform back to SQL
        transformed_sql = parsed.sql(dialect=dialect)

        return ValidationResult(
            is_valid=True,
            sql=transformed_sql,
            error=None,
        )

    except sqlglot.ParseError as e:
        return ValidationResult(
            is_valid=False,
            sql=sql,
            error=f"SQL 语法错误: {str(e)}",
        )
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            sql=sql,
            error=f"解析错误: {str(e)}",
        )


def is_select_query(sql: str, dialect: str = "postgres") -> bool:
    """Check if the SQL is a SELECT query.

    Args:
        sql: The SQL to check
        dialect: SQL dialect

    Returns:
        True if it's a SELECT query, False otherwise
    """
    try:
        parsed = sqlglot.parse_one(sql, dialect=dialect)
        return isinstance(parsed, exp.Select)
    except Exception:
        return False

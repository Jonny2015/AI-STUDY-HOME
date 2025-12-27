"""Query service for executing SQL queries with safety validation."""

import csv
import io
import time
from typing import Tuple

import aiosqlite
import sqlglot

from app.adapters.registry import AdapterRegistry
from app.core.db import db_manager
from app.models.query import QueryResult
from app.utils.logging import logger


class QueryService:
    """Service for SQL query execution with safety validation.

    Features:
    - SELECT-only enforcement
    - Automatic LIMIT injection
    - SQL syntax validation
    - 60-second timeout enforcement
    """

    # Default limit for queries without LIMIT clause
    DEFAULT_LIMIT = 1000

    # Query timeout in seconds
    QUERY_TIMEOUT = 60

    async def validate_sql(self, sql: str) -> Tuple[bool, str]:
        """Validate SQL query for safety.

        Checks:
        1. SQL syntax is valid
        2. Only SELECT statements allowed

        Args:
            sql: SQL query string

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse SQL to validate syntax
            parsed = sqlglot.parse_one(sql, error_level=sqlglot.Error.ErrorLevel.IMMEDIATE)

            # Check if it's a SELECT statement
            if not isinstance(parsed, sqlglot.exp.Select):
                return False, "仅允许 SELECT 查询"

            return True, ""

        except sqlglot.errors.ParseError as e:
            logger.error(f"SQL parse error: {e}")
            return False, f"SQL 语法错误: {str(e)}"
        except Exception as e:
            logger.error(f"SQL validation error: {e}")
            return False, f"SQL 验证失败: {str(e)}"

    def _inject_limit(self, sql: str) -> str:
        """Inject LIMIT clause into SQL if not present.

        Args:
            sql: SQL query string

        Returns:
            SQL with LIMIT clause
        """
        try:
            parsed = sqlglot.parse_one(sql)

            # Check if LIMIT already exists
            has_limit = any(
                isinstance(expr, sqlglot.exp.Limit)
                for expr in parsed.find_all(sqlglot.exp.Limit)
            )

            if not has_limit:
                # Inject LIMIT
                parsed = parsed.limit(str(self.DEFAULT_LIMIT))
                return parsed.sql()
            else:
                return sql

        except Exception as e:
            logger.warning(f"Failed to inject LIMIT, using original SQL: {e}")
            return sql

    async def execute_query(self, database_name: str, sql: str) -> QueryResult:
        """Execute SQL query on database.

        Args:
            database_name: Name of database connection
            sql: SQL query to execute

        Returns:
            QueryResult with execution results

        Raises:
            ValueError: If validation fails or database not found
            Exception: If query execution fails
        """
        # Validate SQL
        is_valid, error_msg = await self.validate_sql(sql)
        if not is_valid:
            raise ValueError(error_msg)

        # Inject LIMIT if needed
        sql = self._inject_limit(sql)

        try:
            # Get database connection info
            async with aiosqlite.connect(db_manager.db_path) as conn:
                cursor = await conn.execute(
                    "SELECT url, db_type FROM databases WHERE name = ?",
                    (database_name,),
                )
                row = await cursor.fetchone()

                if not row:
                    raise ValueError(f"数据库 '{database_name}' 不存在")

                url = row[0]
                db_type = row[1]

            # Get adapter and connect
            adapter = AdapterRegistry.get_adapter(db_type)
            connection = await adapter.connect(url)

            # Execute query with timeout
            start_time = time.time()
            result = await connection.execute_query(sql, timeout=self.QUERY_TIMEOUT)
            execution_time = int((time.time() - start_time) * 1000)  # Convert to ms

            await connection.connection.close()

            # Build result
            columns = [desc[0] for desc in result.description] if result.description else []
            rows = []

            async for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    row_dict[col] = row[i]
                rows.append(row_dict)

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=execution_time,
            )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Query execution failed for {database_name}: {e}")
            raise Exception(f"查询执行失败: {str(e)}") from e

    def export_to_csv(self, result: QueryResult) -> str:
        """Export query result to CSV format.

        Args:
            result: QueryResult to export

        Returns:
            CSV string
        """
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=result.columns)
        writer.writeheader()
        writer.writerows(result.rows)
        return output.getvalue()

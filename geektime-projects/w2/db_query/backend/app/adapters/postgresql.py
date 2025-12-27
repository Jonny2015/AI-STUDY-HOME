"""PostgreSQL database adapter implementation."""

import asyncio
import time
from datetime import datetime
from typing import Any, List

import asyncpg
from app.adapters.base import (
    ColumnMetadata,
    Connection,
    DatabaseAdapter,
    DatabaseMetadata,
    QueryResult,
    TableMetadata,
)


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter.

    Implements DatabaseAdapter for PostgreSQL databases.
    """

    def __init__(self, db_type: str = "postgresql") -> None:
        """Initialize PostgreSQL adapter.

        Args:
            db_type: Database type identifier
        """
        super().__init__(db_type)

    async def connect(self, url: str) -> Connection:
        """Establish a PostgreSQL database connection.

        Args:
            url: PostgreSQL connection URL

        Returns:
            Connection wrapper

        Raises:
            Exception: If connection fails
        """
        try:
            conn = await asyncpg.connect(url)
            return Connection(connection=conn, db_type=self.db_type)
        except Exception as e:
            raise Exception(f"PostgreSQL 连接失败: {str(e)}") from e

    async def get_metadata(self, connection: Connection) -> DatabaseMetadata:
        """Extract PostgreSQL database metadata.

        Args:
            connection: Database connection

        Returns:
            DatabaseMetadata with all tables and columns

        Raises:
            Exception: If metadata extraction fails
        """
        conn: asyncpg.Connection = connection.connection

        try:
            tables: List[TableMetadata] = []

            # Get all tables and views
            query = """
                SELECT
                    table_schema,
                    table_name,
                    table_type
                FROM information_schema.tables
                WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                ORDER BY table_schema, table_name
            """

            rows = await conn.fetch(query)

            for row in rows:
                schema_name = row["table_schema"]
                table_name = row["table_name"]
                table_type = row["table_type"]

                # Map table_type to our format
                if table_type == "BASE TABLE":
                    our_table_type = "table"
                elif table_type == "VIEW":
                    our_table_type = "view"
                else:
                    continue

                # Get column information
                column_query = """
                    SELECT
                        c.column_name,
                        c.data_type,
                        c.is_nullable,
                        CASE WHEN pk.column_name IS NOT NULL THEN 'true' ELSE 'false' END AS is_primary_key
                    FROM information_schema.columns c
                    LEFT JOIN (
                        SELECT ku.column_name, kc.table_schema, kc.table_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage ku
                            ON tc.constraint_name = ku.constraint_name
                        JOIN information_schema.key_column_usage kc
                            ON tc.constraint_name = kc.constraint_name
                        WHERE tc.constraint_type = 'PRIMARY KEY'
                    ) pk ON c.column_name = pk.column_name
                        AND c.table_schema = pk.table_schema
                        AND c.table_name = pk.table_name
                    WHERE c.table_schema = $1
                        AND c.table_name = $2
                    ORDER BY c.ordinal_position
                """

                columns_result = await conn.fetch(column_query, schema_name, table_name)

                columns = [
                    ColumnMetadata(
                        column_name=col["column_name"],
                        data_type=col["data_type"],
                        is_nullable=col["is_nullable"] == "YES",
                        is_primary_key=col["is_primary_key"] == "true",
                    )
                    for col in columns_result
                ]

                tables.append(
                    TableMetadata(
                        schema_name=schema_name,
                        table_name=table_name,
                        table_type=our_table_type,
                        columns=columns,
                    )
                )

            # Extract database name from connection
            db_name: str = await conn.fetchval("SELECT current_database()")

            return DatabaseMetadata(
                db_name=db_name,
                db_type=self.db_type,
                tables=tables,
                metadata_extracted_at=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            raise Exception(f"提取 PostgreSQL 元数据失败: {str(e)}") from e

    async def execute_query(
        self,
        connection: Connection,
        sql: str,
        timeout: int = 60,
    ) -> QueryResult:
        """Execute a SELECT query on PostgreSQL.

        Args:
            connection: Database connection
            sql: SQL query to execute
            timeout: Query timeout in seconds

        Returns:
            QueryResult with data

        Raises:
            Exception: If query execution fails
        """
        conn: asyncpg.Connection = connection.connection

        try:
            start_time = time.time()

            # Execute query with timeout
            result = await asyncio.wait_for(
                conn.fetch(sql),
                timeout=timeout,
            )

            execution_time = int((time.time() - start_time) * 1000)

            # Get column names
            if result:
                columns = list(result[0].keys())
                rows = [dict(row) for row in result]
            else:
                columns = []
                rows = []

            return QueryResult(
                columns=columns,
                rows=rows,
                row_count=len(rows),
                execution_time_ms=execution_time,
            )

        except asyncio.TimeoutError:
            raise Exception(f"查询超时（超过 {timeout} 秒）") from None
        except Exception as e:
            raise Exception(f"查询执行失败: {str(e)}") from e

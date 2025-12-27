"""MySQL database adapter implementation."""

import asyncio
import time
from datetime import datetime
from typing import Any, List

import aiomysql
from app.adapters.base import (
    ColumnMetadata,
    Connection,
    DatabaseAdapter,
    DatabaseMetadata,
    QueryResult,
    TableMetadata,
)


class MySQLAdapter(DatabaseAdapter):
    """MySQL database adapter.

    Implements DatabaseAdapter for MySQL databases.
    """

    def __init__(self, db_type: str = "mysql") -> None:
        """Initialize MySQL adapter.

        Args:
            db_type: Database type identifier
        """
        super().__init__(db_type)

    async def connect(self, url: str) -> Connection:
        """Establish a MySQL database connection.

        Args:
            url: MySQL connection URL

        Returns:
            Connection wrapper

        Raises:
            Exception: If connection fails
        """
        try:
            # Parse URL and create connection
            # Format: mysql://user:password@host:port/database
            conn = await aiomysql.connect(
                host=url.split("@")[1].split("/")[0].split(":")[0],
                port=int(url.split(":")[2].split("/")[0]) if ":" in url.split("@")[1] else 3306,
                user=url.split("://")[1].split(":")[0],
                password=url.split(":")[1].split("@")[0],
                db=url.split("/")[-1],
                autocommit=True,
            )
            return Connection(connection=conn, db_type=self.db_type)
        except Exception as e:
            raise Exception(f"MySQL 连接失败: {str(e)}") from e

    async def get_metadata(self, connection: Connection) -> DatabaseMetadata:
        """Extract MySQL database metadata.

        Args:
            connection: Database connection

        Returns:
            DatabaseMetadata with all tables and columns

        Raises:
            Exception: If metadata extraction fails
        """
        conn: aiomysql.Connection = connection.connection
        cursor = await conn.cursor()

        try:
            tables: List[TableMetadata] = []

            # Get all tables and views
            await cursor.execute("""
                SELECT
                    TABLE_SCHEMA as table_schema,
                    TABLE_NAME as table_name,
                    TABLE_TYPE as table_type
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA NOT IN ('mysql', 'information_schema', 'performance_schema')
                ORDER BY TABLE_SCHEMA, TABLE_NAME
            """)

            rows = await cursor.fetchall()

            for row in rows:
                schema_name = row[0]  # table_schema
                table_name = row[1]  # table_name
                table_type = row[2]  # table_type

                # Map table_type to our format
                if table_type == "BASE TABLE":
                    our_table_type = "table"
                elif table_type == "VIEW":
                    our_table_type = "view"
                else:
                    continue

                # Get column information
                await cursor.execute("""
                    SELECT
                        COLUMN_NAME as column_name,
                        DATA_TYPE as data_type,
                        IS_NULLABLE as is_nullable,
                        COLUMN_KEY as column_key
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s
                        AND TABLE_NAME = %s
                    ORDER BY ORDINAL_POSITION
                """, (schema_name, table_name))

                columns_result = await cursor.fetchall()

                columns = [
                    ColumnMetadata(
                        column_name=col[0],
                        data_type=col[1],
                        is_nullable=col[2] == "YES",
                        is_primary_key=col[3] == "PRI",
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

            # Get database name
            await cursor.execute("SELECT DATABASE()")
            db_row = await cursor.fetchone()
            db_name: str = db_row[0] if db_row else "unknown"

            return DatabaseMetadata(
                db_name=db_name,
                db_type=self.db_type,
                tables=tables,
                metadata_extracted_at=datetime.utcnow().isoformat(),
            )

        except Exception as e:
            raise Exception(f"提取 MySQL 元数据失败: {str(e)}") from e
        finally:
            await cursor.close()

    async def execute_query(
        self,
        connection: Connection,
        sql: str,
        timeout: int = 60,
    ) -> QueryResult:
        """Execute a SELECT query on MySQL.

        Args:
            connection: Database connection
            sql: SQL query to execute
            timeout: Query timeout in seconds

        Returns:
            QueryResult with data

        Raises:
            Exception: If query execution fails
        """
        conn: aiomysql.Connection = connection.connection
        cursor = await conn.cursor(aiomysql.DictCursor)

        try:
            start_time = time.time()

            # Execute query with timeout
            await asyncio.wait_for(
                cursor.execute(sql),
                timeout=timeout,
            )

            rows = await cursor.fetchall()
            execution_time = int((time.time() - start_time) * 1000)

            # Get column names
            if rows:
                columns = list(rows[0].keys())
            else:
                columns = []

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
        finally:
            await cursor.close()

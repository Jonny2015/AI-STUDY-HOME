"""Database service for managing database connections."""

import aiosqlite
from datetime import datetime
from pathlib import Path

from app.adapters.registry import AdapterRegistry
from app.config import settings
from app.core.db import db_manager
from app.core.security import is_valid_database_name, mask_url_password, validate_database_url
from app.models.database import DatabaseResponse, DatabaseListResponse, AddDatabaseRequest
from app.utils.logging import logger


class DatabaseService:
    """Service for database connection management.

    Provides facade for database operations following SOLID principles.
    """

    async def add_database(
        self,
        name: str,
        url: str,
    ) -> DatabaseResponse:
        """Add a new database connection.

        Args:
            name: Database connection name
            url: Database connection URL

        Returns:
            DatabaseResponse with connection details

        Raises:
            ValueError: If validation fails
            Exception: If connection or storage fails
        """
        # Validate database name
        if not is_valid_database_name(name):
            raise ValueError("无效的数据库名称（仅允许字母、数字、下划线、连字符，1-100字符）")

        # Validate URL and extract database type
        is_valid, db_type, error_msg = validate_database_url(url)
        if not is_valid:
            raise ValueError(error_msg)

        # Test connection
        try:
            adapter = AdapterRegistry.get_adapter(db_type)
            connection = await adapter.connect(url)
            await connection.connection.close()
            connection_status = "connected"
            last_connected_at = datetime.utcnow()
        except Exception as e:
            logger.error(f"Database connection test failed for {name}: {e}")
            connection_status = "failed"
            last_connected_at = None
            raise Exception(f"数据库连接失败: {str(e)}") from e

        # Store in SQLite database
        try:
            async with aiosqlite.connect(db_manager.db_path) as conn:
                created_at = datetime.utcnow()

                await conn.execute(
                    """
                    INSERT INTO databases (name, url, db_type, created_at, last_connected_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        name,
                        mask_url_password(url),
                        db_type,
                        created_at.isoformat(),
                        last_connected_at.isoformat() if last_connected_at else None,
                    ),
                )
                await conn.commit()

            return DatabaseResponse(
                database_name=name,
                db_type=db_type,
                created_at=created_at,
                connection_status=connection_status,
                last_connected_at=last_connected_at,
            )

        except Exception as e:
            # Check for duplicate name
            if "UNIQUE" in str(e):
                raise ValueError(f"数据库名称 '{name}' 已存在") from e
            raise Exception(f"保存数据库连接失败: {str(e)}") from e

    async def list_databases(self) -> DatabaseListResponse:
        """List all database connections.

        Returns:
            DatabaseListResponse with all databases
        """
        try:
            async with aiosqlite.connect(db_manager.db_path) as conn:
                cursor = await conn.execute(
                    """
                    SELECT name, db_type, created_at, last_connected_at
                    FROM databases
                    ORDER BY created_at DESC
                    """
                )

                rows = await cursor.fetchall()

                databases = [
                    DatabaseResponse(
                        database_name=row[0],
                        db_type=row[1],
                        created_at=datetime.fromisoformat(row[2]),
                        connection_status="connected",  # For now, assume connected
                        last_connected_at=datetime.fromisoformat(row[3]) if row[3] else None,
                    )
                    for row in rows
                ]

            return DatabaseListResponse(
                data=databases,
                total=len(databases),
            )

        except Exception as e:
            raise Exception(f"获取数据库列表失败: {str(e)}") from e

    async def delete_database(self, name: str) -> None:
        """Delete a database connection.

        Args:
            name: Database connection name

        Raises:
            ValueError: If database doesn't exist
            Exception: If deletion fails
        """
        try:
            async with aiosqlite.connect(db_manager.db_path) as conn:
                # Check if exists
                cursor = await conn.execute(
                    "SELECT name FROM databases WHERE name = ?",
                    (name,),
                )
                row = await cursor.fetchone()

                if not row:
                    raise ValueError(f"数据库 '{name}' 不存在")

                # Delete (CASCADE will delete related metadata)
                await conn.execute(
                    "DELETE FROM databases WHERE name = ?",
                    (name,),
                )
                await conn.commit()

        except ValueError:
            raise
        except Exception as e:
            raise Exception(f"删除数据库失败: {str(e)}") from e

    async def test_connection(self, url: str, db_type: str) -> bool:
        """Test a database connection without storing it.

        Args:
            url: Database connection URL
            db_type: Database type

        Returns:
            True if connection succeeds

        Raises:
            Exception: If connection fails
        """
        try:
            adapter = AdapterRegistry.get_adapter(db_type)
            connection = await adapter.connect(url)
            await connection.connection.close()
            return True
        except Exception:
            raise

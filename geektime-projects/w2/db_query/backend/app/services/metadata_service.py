"""Metadata service for extracting and caching database metadata."""

from datetime import datetime

import aiosqlite

from app.adapters.registry import AdapterRegistry
from app.core.db import db_manager
from app.models.metadata import (
    ColumnMetadata,
    DatabaseMetadataResponse,
)
from app.models.metadata import (
    TableMetadata as APITableMetadata,
)
from app.utils.logging import logger


class MetadataService:
    """Service for database metadata operations.

    Provides metadata extraction and caching with automatic refresh.
    """

    async def extract_metadata(self, name: str, url: str, db_type: str) -> DatabaseMetadataResponse:
        """Extract metadata from database and cache it.

        Args:
            name: Database connection name
            url: Database connection URL
            db_type: Type of database (postgresql or mysql)

        Returns:
            DatabaseMetadataResponse with extracted metadata

        Raises:
            Exception: If extraction fails
        """
        try:
            # Get metadata from database
            adapter = AdapterRegistry.get_adapter(db_type)
            connection = await adapter.connect(url)

            # Pass the Connection wrapper to get_metadata (not connection.connection)
            db_metadata = await adapter.get_metadata(connection)
            await connection.connection.close()

            # Convert adapter metadata to API metadata
            api_tables = [
                APITableMetadata(
                    table_name=table.table_name,
                    table_type=table.table_type,
                    schema_name=table.schema_name,
                    columns=[
                        ColumnMetadata(
                            column_name=col.column_name,
                            data_type=col.data_type,
                            is_nullable=col.is_nullable,
                            is_primary_key=col.is_primary_key,
                        )
                        for col in table.columns
                    ],
                )
                for table in db_metadata.tables
            ]

            # Cache in SQLite
            await self._cache_metadata(name, db_metadata)

            return DatabaseMetadataResponse(
                database_name=name,
                db_type=db_type,
                tables=api_tables,
                metadata_extracted_at=datetime.utcnow().isoformat(),
                is_cached=False,
            )

        except Exception as e:
            logger.error(f"Failed to extract metadata for {name}: {e}")
            raise Exception(f"提取元数据失败: {str(e)}") from e

    async def get_cached_metadata(self, name: str) -> DatabaseMetadataResponse | None:
        """Get cached metadata from SQLite.

        Args:
            name: Database connection name

        Returns:
            DatabaseMetadataResponse if cached, None otherwise
        """
        try:
            async with aiosqlite.connect(db_manager.db_path) as conn:
                # Get database info
                cursor = await conn.execute(
                    "SELECT db_type FROM databases WHERE name = ?",
                    (name,),
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                db_type = row[0]

                # Get metadata
                cursor = await conn.execute(
                    """
                    SELECT schema_name, table_name, table_type, column_name,
                           data_type, is_nullable, is_primary_key, metadata_extracted_at
                    FROM metadata
                    WHERE db_name = ?
                    ORDER BY schema_name, table_name, column_name
                    """,
                    (name,),
                )
                rows = await cursor.fetchall()

                if not rows:
                    return None

                # Build metadata from rows
                tables_map: dict[str, dict[str, list]] = {}

                for (
                    schema_name,
                    table_name,
                    table_type,
                    column_name,
                    data_type,
                    is_nullable,
                    is_primary_key,
                    metadata_extracted_at,
                ) in rows:
                    key = f"{schema_name}.{table_name}"

                    if key not in tables_map:
                        tables_map[key] = {
                            "table_name": table_name,
                            "table_type": table_type,
                            "schema_name": schema_name,
                            "columns": [],
                            "extracted_at": metadata_extracted_at,
                        }

                    tables_map[key]["columns"].append(
                        ColumnMetadata(
                            column_name=column_name,
                            data_type=data_type,
                            is_nullable=bool(is_nullable),
                            is_primary_key=bool(is_primary_key),
                        )
                    )

                tables = [
                    APITableMetadata(
                        table_name=v["table_name"],
                        table_type=v["table_type"],
                        schema_name=v["schema_name"],
                        columns=v["columns"],
                    )
                    for v in tables_map.values()
                ]

                # Get the most recent extraction time
                extracted_at = rows[0][7] if rows else datetime.utcnow().isoformat()

                return DatabaseMetadataResponse(
                    database_name=name,
                    db_type=db_type,
                    tables=tables,
                    metadata_extracted_at=extracted_at,
                    is_cached=True,
                )

        except Exception as e:
            logger.error(f"Failed to get cached metadata for {name}: {e}")
            return None

    async def refresh_metadata(self, name: str) -> DatabaseMetadataResponse:
        """Refresh metadata by re-extracting from database.

        Args:
            name: Database connection name

        Returns:
            DatabaseMetadataResponse with refreshed metadata

        Raises:
            ValueError: If database doesn't exist
            Exception: If refresh fails
        """
        try:
            # Get database connection info
            async with aiosqlite.connect(db_manager.db_path) as conn:
                cursor = await conn.execute(
                    "SELECT url, db_type FROM databases WHERE name = ?",
                    (name,),
                )
                row = await cursor.fetchone()

                if not row:
                    raise ValueError(f"数据库 '{name}' 不存在")

                url = row[0]
                db_type = row[1]

            # Re-extract metadata
            return await self.extract_metadata(name, url, db_type)

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to refresh metadata for {name}: {e}")
            raise Exception(f"刷新元数据失败: {str(e)}") from e

    async def _cache_metadata(self, name: str, metadata) -> None:
        """Cache metadata in SQLite.

        Args:
            name: Database connection name
            metadata: Metadata object with tables
        """
        try:
            async with aiosqlite.connect(db_manager.db_path) as conn:
                # Delete old metadata first
                await conn.execute(
                    "DELETE FROM metadata WHERE db_name = ?",
                    (name,),
                )
                await conn.commit()  # Commit delete before insert

                # Insert new metadata
                extracted_at = datetime.utcnow().isoformat()

                for table in metadata.tables:
                    for column in table.columns:
                        # Use INSERT OR REPLACE to handle any conflicts
                        await conn.execute(
                            """
                            INSERT OR REPLACE INTO metadata (
                                db_name, schema_name, table_name, table_type,
                                column_name, data_type, is_nullable, is_primary_key,
                                metadata_extracted_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                name,
                                table.schema_name,
                                table.table_name,
                                table.table_type,
                                column.column_name,
                                column.data_type,
                                1 if column.is_nullable else 0,
                                1 if column.is_primary_key else 0,
                                extracted_at,
                            ),
                        )

                await conn.commit()

        except Exception as e:
            logger.error(f"Failed to cache metadata for {name}: {e}")
            # Don't fail the operation if caching fails

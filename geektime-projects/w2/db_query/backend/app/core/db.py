"""SQLite database management for storing metadata and connections."""

import aiosqlite
from pathlib import Path
from typing import Optional

from app.config import settings


class DatabaseManager:
    """Manage SQLite database operations.

    Attributes:
        db_path: Path to the SQLite database file
    """

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize the database manager.

        Args:
            db_path: Path to the database file. Defaults to settings.database_path.
        """
        self.db_path = db_path or settings.database_path

    async def initialize_database(self) -> None:
        """Create database tables if they don't exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiosqlite.connect(self.db_path) as db:
            # Create databases table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS databases (
                    name TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    db_type TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    last_connected_at TEXT
                )
            """)

            # Create metadata table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    db_name TEXT NOT NULL,
                    schema_name TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    table_type TEXT NOT NULL,
                    column_name TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    is_nullable INTEGER NOT NULL,
                    is_primary_key INTEGER NOT NULL,
                    metadata_extracted_at TEXT NOT NULL,
                    PRIMARY KEY (db_name, schema_name, table_name, column_name),
                    FOREIGN KEY (db_name) REFERENCES databases(name) ON DELETE CASCADE
                )
            """)

            # Create indexes
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_metadata_db_name
                ON metadata(db_name)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_metadata_table_name
                ON metadata(table_name)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_metadata_schema_table
                ON metadata(schema_name, table_name)
            """)

            await db.commit()

    async def get_connection(self) -> aiosqlite.Connection:
        """Get a database connection.

        Returns:
            aiosqlite connection object
        """
        return await aiosqlite.connect(self.db_path)


# Global database manager instance
db_manager = DatabaseManager()

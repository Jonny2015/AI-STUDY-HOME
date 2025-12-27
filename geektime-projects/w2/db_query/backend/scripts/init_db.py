#!/usr/bin/env python3
"""Initialize the SQLite database for metadata storage.

This script creates the database file and tables if they don't exist.
Run this after installing dependencies or when setting up a new environment.
"""

import asyncio
from pathlib import Path

from app.core.db import db_manager


async def main() -> None:
    """Initialize database."""
    print("Initializing database...")
    print(f"Database path: {db_manager.db_path.expanduser()}")

    # Ensure parent directory exists
    db_manager.db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize database schema
    await db_manager.initialize_database()

    # Verify database was created
    if db_manager.db_path.expanduser().exists():
        size = db_manager.db_path.expanduser().stat().st_size
        print(f"✓ Database initialized successfully")
        print(f"  Location: {db_manager.db_path.expanduser()}")
        print(f"  Size: {size} bytes")
    else:
        print("✗ Database initialization failed")
        raise FileNotFoundError(f"Database file not created at {db_manager.db_path}")


if __name__ == "__main__":
    asyncio.run(main())

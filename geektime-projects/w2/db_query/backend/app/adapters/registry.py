"""Adapter registry for managing database adapters."""

from typing import Dict, List, Type

from app.adapters.base import DatabaseAdapter


class AdapterRegistry:
    """Registry for database adapters.

    Follows Registry pattern for managing adapter instances.
    Enables adding new database types without modifying existing code (Open/Closed Principle).
    """

    _adapters: Dict[str, Type[DatabaseAdapter]] = {}

    @classmethod
    def register(cls, db_type: str, adapter_class: Type[DatabaseAdapter]) -> None:
        """Register a database adapter.

        Args:
            db_type: Database type identifier (e.g., "postgresql", "mysql")
            adapter_class: Adapter class to register
        """
        cls._adapters[db_type] = adapter_class

    @classmethod
    def get_adapter(cls, db_type: str) -> DatabaseAdapter:
        """Get an adapter instance for the given database type.

        Args:
            db_type: Database type identifier

        Returns:
            DatabaseAdapter instance

        Raises:
            ValueError: If database type is not supported
        """
        adapter_class = cls._adapters.get(db_type)
        if not adapter_class:
            supported = ", ".join(cls._adapters.keys())
            raise ValueError(
                f"Unsupported database type: {db_type}. "
                f"Supported types: {supported}"
            )

        return adapter_class(db_type=db_type)

    @classmethod
    def supported_types(cls) -> List[str]:
        """Get list of supported database types.

        Returns:
            List of database type identifiers
        """
        return list(cls._adapters.keys())


# Register built-in adapters
from app.adapters.postgresql import PostgreSQLAdapter
from app.adapters.mysql import MySQLAdapter

AdapterRegistry.register("postgresql", PostgreSQLAdapter)
AdapterRegistry.register("mysql", MySQLAdapter)

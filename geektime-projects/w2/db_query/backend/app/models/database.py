"""Database connection models."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic.alias_generators import to_camel

DatabaseType = Literal["postgresql", "mysql"]
ConnectionStatus = Literal["connected", "failed", "pending"]


class DatabaseResponse(BaseModel):
    """Database connection response.

    Attributes:
        database_name: Name of the database connection
        db_type: Type of database (postgresql or mysql)
        created_at: Creation timestamp (ISO 8601)
        connection_status: Current connection status
        last_connected_at: Last successful connection timestamp (ISO 8601)
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    database_name: str = Field(alias="databaseName", description="Database connection name")
    db_type: DatabaseType = Field(alias="dbType", description="Database type")
    created_at: datetime = Field(alias="createdAt", description="Creation timestamp")
    connection_status: ConnectionStatus = Field(
        alias="connectionStatus",
        description="Connection status",
    )
    last_connected_at: datetime | None = Field(
        default=None,
        alias="lastConnectedAt",
        description="Last successful connection timestamp",
    )


class DatabaseListResponse(BaseModel):
    """List of database connections.

    Attributes:
        data: List of database connections (Refine format)
        total: Total number of databases (Refine format)
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    data: list[DatabaseResponse] = Field(alias="data", description="Database list")
    total: int = Field(alias="total", description="Total count")


class AddDatabaseRequest(BaseModel):
    """Request to add a database connection.

    Attributes:
        name: Database connection name (optional for POST endpoint)
        url: Database connection URL
    """

    name: str | None = Field(
        default=None,
        description="Database connection name",
    )
    url: str = Field(
        ...,
        description="Database connection string (e.g., postgresql://user:pass@host:port/db)",
        min_length=10,
        max_length=500,
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format.

        Args:
            v: URL to validate

        Returns:
            Validated URL

        Raises:
            ValueError: If URL format is invalid
        """
        if not v.startswith(("postgresql://", "postgres://", "mysql://")):
            raise ValueError("仅支持 PostgreSQL 和 MySQL 连接字符串")
        return v.strip()

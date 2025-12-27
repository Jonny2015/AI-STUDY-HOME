"""Abstract base class for database adapters."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class Connection:
    """Database connection wrapper.

    Attributes:
        connection: The underlying database connection
        db_type: Database type identifier
    """

    def __init__(self, connection: Any, db_type: str) -> None:
        """Initialize connection wrapper.

        Args:
            connection: The database connection object
            db_type: Database type (postgresql, mysql)
        """
        self.connection = connection
        self.db_type = db_type


class ColumnMetadata(BaseModel):
    """Column metadata information.

    Attributes:
        column_name: Name of the column
        data_type: Data type
        is_nullable: Whether NULL values are allowed
        is_primary_key: Whether this is a primary key
    """

    column_name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool


class TableMetadata(BaseModel):
    """Table or view metadata.

    Attributes:
        schema_name: Schema name
        table_name: Table or view name
        table_type: Type (table or view)
        columns: List of column metadata
    """

    schema_name: str
    table_name: str
    table_type: str  # "table" or "view"
    columns: list[ColumnMetadata]


class DatabaseMetadata(BaseModel):
    """Complete database metadata.

    Attributes:
        db_name: Database name
        db_type: Database type
        tables: List of tables and views
        metadata_extracted_at: Extraction timestamp
    """

    db_name: str
    db_type: str
    tables: list[TableMetadata]
    metadata_extracted_at: str


class QueryResult(BaseModel):
    """Result of a query execution.

    Attributes:
        columns: List of column names
        rows: List of data rows (as dictionaries)
        row_count: Number of rows
        execution_time_ms: Execution time in milliseconds
    """

    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    execution_time_ms: int


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters.

    Implementations must support PostgreSQL and MySQL.
    Follows SOLID principles - Open/Closed for extensibility.
    """

    def __init__(self, db_type: str) -> None:
        """Initialize the adapter.

        Args:
            db_type: Database type identifier
        """
        self.db_type = db_type

    @abstractmethod
    async def connect(self, url: str) -> Connection:
        """Establish a database connection.

        Args:
            url: Database connection URL

        Returns:
            Connection wrapper

        Raises:
            Exception: If connection fails
        """
        pass

    @abstractmethod
    async def get_metadata(self, connection: Connection) -> DatabaseMetadata:
        """Extract database metadata.

        Args:
            connection: Database connection

        Returns:
            DatabaseMetadata with all tables, views, and columns

        Raises:
            Exception: If metadata extraction fails
        """
        pass

    @abstractmethod
    async def execute_query(
        self,
        connection: Connection,
        sql: str,
        timeout: int = 60,
    ) -> QueryResult:
        """Execute a SELECT query.

        Args:
            connection: Database connection
            sql: SQL query to execute
            timeout: Query timeout in seconds

        Returns:
            QueryResult with data

        Raises:
            Exception: If query execution fails
        """
        pass

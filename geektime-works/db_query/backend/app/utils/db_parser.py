"""Database URL parser utility for detecting database type."""

from urllib.parse import urlparse
from app.models.database import DatabaseType


def validate_connection_url(url: str) -> None:
    """
    Validate database connection URL format.

    Args:
        url: Database connection URL

    Raises:
        ValueError: If URL format is invalid
    """
    parsed = urlparse(url)

    # Check if port is a valid number
    if parsed.port is not None and isinstance(parsed.port, int):
        # urlparse automatically converts port to int, so if we get here
        # and the port was not numeric, urlparse would have returned None
        pass

    # Additional validation
    if not parsed.hostname:
        raise ValueError("URL must contain a valid hostname")

    if not parsed.path or parsed.path == "/":
        raise ValueError("URL must contain a database name")


def detect_database_type(url: str) -> DatabaseType:
    """
    Detect database type from connection URL.

    Args:
        url: Database connection URL (e.g., postgresql://... or mysql://...)

    Returns:
        DatabaseType enum value

    Raises:
        ValueError: If database type cannot be determined or is unsupported
    """
    try:
        # Validate URL format first
        validate_connection_url(url)

        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        # Handle common PostgreSQL schemes
        if scheme in ("postgresql", "postgres"):
            return DatabaseType.POSTGRESQL

        # Handle common MySQL schemes
        if scheme in ("mysql", "mysql+pymysql", "mysql+aiomysql"):
            return DatabaseType.MYSQL

        raise ValueError(
            f"Unsupported database type: {scheme}. "
            f"Supported types: postgresql, postgres, mysql"
        )

    except ValueError as e:
        # Re-raise ValueError with our custom message
        raise e
    except Exception as e:
        raise ValueError(f"Failed to parse database URL: {str(e)}")

"""Security utilities for URL validation and password masking."""

import re
from urllib.parse import ParseResult, urlparse, urlunparse


def mask_url_password(url: str) -> str:
    """Mask the password in a database URL.

    Args:
        url: The database URL

    Returns:
        URL with password replaced by ****
    """
    try:
        parsed = urlparse(url)

        # Extract host, port, database from the URL
        # Format: protocol://user:password@host:port/database
        if "@" in parsed.netloc:
            auth, host_port = parsed.netloc.split("@", 1)
            if ":" in auth:
                user, _ = auth.split(":", 1)
                masked_netloc = f"{user}:****@{host_port}"
            else:
                masked_netloc = f"{auth}@{host_port}"
        else:
            masked_netloc = parsed.netloc

        # Reconstruct the URL
        masked_parsed = ParseResult(
            scheme=parsed.scheme,
            netloc=masked_netloc,
            path=parsed.path,
            params=parsed.params,
            query=parsed.query,
            fragment=parsed.fragment,
        )

        return urlunparse(masked_parsed)

    except Exception:
        # If parsing fails, return original
        return url


def validate_database_url(url: str) -> tuple[bool, str, str]:
    """Validate a database connection URL and extract the database type.

    Args:
        url: The database URL to validate

    Returns:
        Tuple of (is_valid, db_type, error_message)
    """
    # Check if URL starts with supported protocols
    supported_protocols = [
        "postgresql://",
        "postgres://",
        "mysql://",
    ]

    if not any(url.startswith(proto) for proto in supported_protocols):
        return False, "", "不支持的数据库类型，仅支持 PostgreSQL 和 MySQL"

    # Extract database type
    if url.startswith(("postgresql://", "postgres://")):
        db_type = "postgresql"
    elif url.startswith("mysql://"):
        db_type = "mysql"
    else:
        return False, "", "无法识别的数据库类型"

    # Basic URL structure validation
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False, "", "无效的连接字符串格式"

        return True, db_type, ""

    except Exception as e:
        return False, "", f"URL 解析错误: {str(e)}"


def is_valid_database_name(name: str) -> bool:
    """Validate a database connection name.

    Args:
        name: The database connection name

    Returns:
        True if valid, False otherwise
    """
    if not name or len(name) < 1 or len(name) > 100:
        return False

    # Only allow alphanumeric, underscore, and hyphen
    pattern = r"^[a-zA-Z0-9_-]+$"
    return re.match(pattern, name) is not None

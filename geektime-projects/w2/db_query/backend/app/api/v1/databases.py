"""API endpoints for database management."""

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.core.db import db_manager
from app.models.database import (
    AddDatabaseRequest,
    DatabaseListResponse,
    DatabaseResponse,
)
from app.models.metadata import DatabaseMetadataResponse
from app.services.database_service import DatabaseService
from app.services.metadata_service import MetadataService
from app.utils.logging import logger

router = APIRouter(prefix="/dbs", tags=["databases"])
database_service = DatabaseService()
metadata_service = MetadataService()


@router.get(
    "",
    response_model=DatabaseListResponse,
    summary="获取所有数据库",
    description="返回所有已添加的数据库连接列表",
)
async def list_databases() -> DatabaseListResponse:
    """Get all database connections.

    Returns:
        DatabaseListResponse with all databases
    """
    try:
        return await database_service.list_databases()
    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据库列表失败: {str(e)}",
        ) from e


@router.post(
    "",
    response_model=DatabaseResponse,
    summary="添加数据库连接 (POST)",
    description="添加一个新的数据库连接，系统会验证连接有效性",
)
async def add_database_post(request: AddDatabaseRequest) -> DatabaseResponse:
    """Add a new database connection via POST.

    Args:
        request: Request body containing url and optionally name

    Returns:
        DatabaseResponse with connection details

    Raises:
        HTTPException: If validation or connection fails
    """
    try:
        # Log the request for debugging
        logger.info(f"POST /dbs - name: {request.name}, url: {request.url[:20]}...")

        # Use provided name or generate a timestamp-based name
        import time

        name = request.name or f"db_{int(time.time())}"

        return await database_service.add_database(name, request.url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to add database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加数据库失败: {str(e)}",
        ) from e


@router.put(
    "/{name}",
    response_model=DatabaseResponse,
    summary="添加数据库连接",
    description="添加一个新的数据库连接，系统会验证连接有效性",
)
async def add_database(
    name: str = Path(..., description="数据库连接名称"),
    request: AddDatabaseRequest = None,
) -> DatabaseResponse:
    """Add a new database connection.

    Args:
        name: Database connection name
        request: Add database request with URL

    Returns:
        DatabaseResponse with connection details

    Raises:
        HTTPException: If validation or connection fails
    """
    try:
        return await database_service.add_database(name, request.url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to add database {name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加数据库失败: {str(e)}",
        ) from e


@router.get(
    "/{name}",
    response_model=DatabaseMetadataResponse,
    summary="获取数据库元数据",
    description="获取数据库的结构信息（表、视图、列），支持缓存和刷新",
)
async def get_database_metadata(
    name: str = Path(..., description="数据库名称"),
    refresh: bool = Query(False, description="是否强制刷新元数据"),
) -> DatabaseMetadataResponse:
    """Get database metadata with caching.

    Args:
        name: Database connection name
        refresh: Whether to force refresh metadata from database

    Returns:
        DatabaseMetadataResponse with tables and columns

    Raises:
        HTTPException: If database doesn't exist or retrieval fails
    """
    try:
        if refresh:
            # Force refresh from database
            return await metadata_service.refresh_metadata(name)
        else:
            # Try to get cached metadata first
            cached = await metadata_service.get_cached_metadata(name)

            if cached:
                return cached

            # No cache, extract and store
            # Get database connection info
            import aiosqlite

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

            return await metadata_service.extract_metadata(name, url, db_type)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to get metadata for {name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取元数据失败: {str(e)}",
        ) from e


@router.delete(
    "/{name}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除数据库连接",
    description="删除指定的数据库连接及其相关的元数据缓存",
)
async def delete_database(
    name: str = Path(..., description="数据库名称"),
) -> None:
    """Delete a database connection.

    Args:
        name: Database connection name

    Raises:
        HTTPException: If deletion fails
    """
    try:
        await database_service.delete_database(name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to delete database {name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除数据库失败: {str(e)}",
        ) from e

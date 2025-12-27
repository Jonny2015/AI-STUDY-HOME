"""API endpoints for query execution."""

from fastapi import APIRouter, HTTPException, Path, Query as FastQueryQuery, status
from fastapi.responses import Response

from app.models.query import (
    ExecuteQueryRequest,
    GeneratedSQLResponse,
    NaturalLanguageQueryRequest,
    QueryResult,
)
from app.services.llm_service import LLMService
from app.services.query_service import QueryService
from app.utils.logging import logger

router = APIRouter(prefix="/dbs", tags=["queries"])
query_service = QueryService()
llm_service = LLMService()


@router.post(
    "/{name}/query",
    response_model=QueryResult,
    summary="执行 SQL 查询",
    description="执行 SELECT 查询,自动添加 LIMIT 子句,只允许只读查询",
)
async def execute_query(
    name: str = Path(..., description="数据库连接名称"),
    request: ExecuteQueryRequest = None,
) -> QueryResult:
    """Execute SQL query on database.

    Args:
        name: Database connection name
        request: Query request with SQL

    Returns:
        QueryResult with execution results

    Raises:
        HTTPException: If validation or execution fails
    """
    try:
        return await query_service.execute_query(name, request.sql)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to execute query on {name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行查询失败: {str(e)}",
        ) from e


@router.post(
    "/{name}/query/export",
    summary="导出查询结果为 CSV",
    description="执行 SELECT 查询并导出结果为 CSV 文件",
)
async def export_query(
    name: str = Path(..., description="数据库连接名称"),
    request: ExecuteQueryRequest = None,
) -> Response:
    """Execute SQL query and export result as CSV.

    Args:
        name: Database connection name
        request: Query request with SQL

    Returns:
        CSV file download

    Raises:
        HTTPException: If validation or execution fails
    """
    try:
        result = await query_service.execute_query(name, request.sql)
        csv_data = query_service.export_to_csv(result)

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=query_result_{name}.csv"
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to export query on {name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导出查询失败: {str(e)}",
        ) from e


@router.post(
    "/{name}/query/natural",
    response_model=GeneratedSQLResponse,
    summary="自然语言生成 SQL",
    description="使用 AI 从自然语言生成 SQL 查询",
)
async def generate_sql(
    name: str = Path(..., description="数据库连接名称"),
    request: NaturalLanguageQueryRequest = None,
) -> GeneratedSQLResponse:
    """Generate SQL from natural language.

    Args:
        name: Database connection name
        request: Natural language request

    Returns:
        GeneratedSQLResponse with SQL and explanation

    Raises:
        HTTPException: If generation fails
    """
    try:
        return await llm_service.generate_sql(name, request.prompt)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Failed to generate SQL for {name}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成 SQL 失败: {str(e)}",
        ) from e

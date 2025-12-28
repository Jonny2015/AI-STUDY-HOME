"""Export API endpoints."""

import logging
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlmodel import Session, select

from app.adapters.registry import adapter_registry
from app.adapters.base import ConnectionConfig
from app.config import settings
from app.database import get_session
from app.models.database import DatabaseConnection
from app.models.export import ExportFormat, ExportScope
from app.models.schemas import (
    ExportRequest,
    ExportCheckRequest,
    ExportCheckResponse,
    TaskResponse,
)
from app.services.export import (
    ExportService,
    ExportError,
    FileSizeExceededError,
    ConcurrentTaskLimitError,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["exports"])

# User ID header (simple authentication for now)
UserId = Annotated[str, "X-User-ID"]


def get_user_id(user_id: str = "default") -> str:
    """Get user ID from request headers.

    Args:
        user_id: User ID from header (defaults to "default")

    Returns:
        User ID string
    """
    return user_id


@router.post("/dbs/{name}/export", response_model=TaskResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_export_task(
    name: str,
    request: ExportRequest,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_user_id),
) -> TaskResponse:
    """
    Create a new export task.

    Args:
        name: Database connection name
        request: Export request with SQL, format, and scope
        session: Database session
        user_id: User ID from headers

    Returns:
        TaskResponse with task ID and initial status

    Raises:
        HTTPException: If database not found or export constraints violated
    """
    # Get database connection
    statement = select(DatabaseConnection).where(DatabaseConnection.name == name)
    connection = session.exec(statement).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection '{name}' not found",
        )

    # Parse request parameters
    try:
        export_format = ExportFormat(request.format)
        export_scope = ExportScope.ALL_DATA if request.exportAll else ExportScope.CURRENT_PAGE
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid export format or scope: {str(e)}",
        )

    # Generate task ID
    task_id = str(uuid4())

    # Get database adapter
    config = ConnectionConfig(
        url=connection.url,
        name=name,
        min_pool_size=settings.db_pool_min_size,
        max_pool_size=settings.db_pool_max_size,
        command_timeout=settings.db_pool_command_timeout,
    )
    adapter = adapter_registry.get_adapter(connection.db_type, config)

    # Create export service
    export_service = ExportService(session)

    # Execute export asynchronously
    try:
        task_response = await export_service.execute_export(
            task_id=task_id,
            adapter=adapter,
            sql=request.sql,
            export_format=export_format,
            export_scope=export_scope,
            user_id=user_id,
            database_name=name,
        )
        logger.info(f"Created export task {task_id} for database {name}")
        return task_response

    except FileSizeExceededError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        )
    except ConcurrentTaskLimitError as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except ExportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/dbs/{name}/export/check", response_model=ExportCheckResponse)
async def check_export_file_size(
    name: str,
    request: ExportCheckRequest,
    session: Session = Depends(get_session),
) -> ExportCheckResponse:
    """
    Check export file size before creating task.

    Args:
        name: Database connection name
        request: Check request with SQL and format
        session: Database session

    Returns:
        ExportCheckResponse with size estimate and recommendation

    Raises:
        HTTPException: If database not found
    """
    # Get database connection
    statement = select(DatabaseConnection).where(DatabaseConnection.name == name)
    connection = session.exec(statement).first()

    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Database connection '{name}' not found",
        )

    # Parse request parameters
    try:
        export_format = ExportFormat(request.format)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid export format: {str(e)}",
        )

    # Get database adapter
    config = ConnectionConfig(
        url=connection.url,
        name=name,
        min_pool_size=settings.db_pool_min_size,
        max_pool_size=settings.db_pool_max_size,
        command_timeout=settings.db_pool_command_timeout,
    )
    adapter = adapter_registry.get_adapter(connection.db_type, config)

    # Create export service and check size
    export_service = ExportService(session)

    try:
        check_response = await export_service.check_export_size(
            adapter=adapter,
            sql=request.sql,
            export_format=export_format,
            db_type=connection.db_type,
            use_sampling=request.useSampling,
            sample_size=request.sampleSize,
        )
        return check_response

    except ExportError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    session: Session = Depends(get_session),
) -> TaskResponse:
    """
    Get export task status.

    Args:
        task_id: Task ID
        session: Database session

    Returns:
        TaskResponse with current task status

    Raises:
        HTTPException: If task not found
    """
    export_service = ExportService(session)
    task_response = await export_service.get_task(task_id)

    if not task_response:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found",
        )

    return task_response


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_export_task(
    task_id: str,
    session: Session = Depends(get_session),
) -> None:
    """
    Cancel export task.

    Args:
        task_id: Task ID
        session: Database session

    Raises:
        HTTPException: If task not found or cannot be cancelled
    """
    export_service = ExportService(session)
    cancelled = await export_service.cancel_task(task_id)

    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found or cannot be cancelled",
        )

    logger.info(f"Cancelled export task {task_id}")


@router.get("/exports/download/{filename}")
async def download_export_file(
    filename: str,
    session: Session = Depends(get_session),
) -> FileResponse:
    """
    Download exported file.

    Args:
        filename: Export filename
        session: Database session

    Returns:
        FileResponse with the exported file

    Raises:
        HTTPException: If file not found
    """
    # Validate filename format
    if not filename.startswith("export-") or "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename format",
        )

    # Build file path
    file_path = settings.export_temp_path / filename

    # Check if file exists
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Export file '{filename}' not found",
        )

    # Determine media type
    ext = filename.split(".")[-1].lower()
    media_types = {
        "csv": "text/csv",
        "json": "application/json",
        "md": "text/markdown",
    }
    media_type = media_types.get(ext, "application/octet-stream")

    logger.info(f"Downloading export file: {filename}")

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
    )


# AI Export Assistant Endpoints
from datetime import datetime
from app.models.export import ExportSuggestionResponse
from app.models.schemas import (
    ExportIntentAnalysisRequest,
    ExportIntentAnalysisResponse,
    ExportProactiveSuggestionRequest,
    ExportProactiveSuggestionResponse,
    ExportTrackResponseRequest,
    ExportTrackResponseResponse,
    ExportAnalyticsResponse,
)
from uuid import uuid4


@router.post("/export/analyze-intent", response_model=dict)
async def analyze_export_intent(
    request: dict,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_session),
) -> dict:
    """
    Analyze if export should be suggested based on query results.

    Args:
        request: Request containing databaseName, sqlText, and queryResult
        user_id: User ID from header
        session: Database session

    Returns:
        Analysis results with suggestion and confidence

    Raises:
        HTTPException: If request is invalid or analysis fails
    """
    try:
        # Extract request parameters
        database_name = request.get("databaseName")
        sql_text = request.get("sqlText")
        query_result = request.get("queryResult")

        if not all([database_name, sql_text, query_result]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="databaseName, sqlText, and queryResult are required",
            )

        # Initialize AI service and analyze
        from app.services.export import AIExportService
        ai_service = AIExportService()

        result = await ai_service.analyze_export_intent(
            database_name=database_name,
            sql_text=sql_text,
            query_result=query_result
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing export intent: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze export intent: {str(e)}",
        )


@router.post("/export/proactive-suggestion", response_model=dict)
async def get_proactive_suggestion(
    request: dict,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_session),
) -> dict:
    """
    Generate proactive export suggestion with quick actions.

    Args:
        request: Request containing databaseName, sqlText, queryResult, and intentAnalysis
        user_id: User ID from header
        session: Database session

    Returns:
        Suggestion text and quick actions

    Raises:
        HTTPException: If request is invalid or suggestion generation fails
    """
    try:
        # Extract request parameters
        database_name = request.get("databaseName")
        sql_text = request.get("sqlText")
        query_result = request.get("queryResult")
        intent_analysis = request.get("intentAnalysis")

        if not all([database_name, sql_text, query_result, intent_analysis]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="databaseName, sqlText, queryResult, and intentAnalysis are required",
            )

        # Initialize AI service and generate suggestion
        from app.services.export import AIExportService
        ai_service = AIExportService()

        result = await ai_service.generate_proactive_suggestion(
            database_name=database_name,
            sql_text=sql_text,
            query_result=query_result,
            intent_analysis=intent_analysis
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_204_NO_CONTENT,
                detail="No export suggestion available",
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating proactive suggestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate proactive suggestion: {str(e)}",
        )


@router.post("/export/track-response")
async def track_suggestion_response(
    request: dict,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_session),
) -> dict:
    """
    Track user response to AI export suggestion.

    Args:
        request: Request containing suggestion response data
        user_id: User ID from header
        session: Database session

    Returns:
        Success status message

    Raises:
        HTTPException: If request is invalid or tracking fails
    """
    try:
        # Extract request parameters
        suggestion_id = request.get("suggestionId") or str(uuid4())
        database_name = request.get("databaseName")
        suggestion_type = request.get("suggestionType")
        sql_context = request.get("sqlContext")
        row_count = request.get("rowCount")
        confidence = request.get("confidence")
        suggested_format = request.get("suggestedFormat")
        suggested_scope = request.get("suggestedScope")
        user_response = request.get("userResponse")
        response_time_ms = request.get("responseTimeMs", 0)
        suggested_at_str = request.get("suggestedAt")
        responded_at_str = request.get("respondedAt")

        # Validate required parameters
        required_fields = [
            "databaseName", "suggestionType", "sqlContext", "rowCount",
            "confidence", "suggestedFormat", "suggestedScope", "userResponse"
        ]

        missing_fields = [field for field in required_fields if not request.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required fields: {', '.join(missing_fields)}",
            )

        # Convert format and scope strings to enums
        from app.models.export import ExportFormat, ExportScope
        format_map = {
            'CSV': ExportFormat.CSV,
            'JSON': ExportFormat.JSON,
            'MARKDOWN': ExportFormat.MARKDOWN
        }
        scope_map = {
            'CURRENT_PAGE': ExportScope.CURRENT_PAGE,
            'ALL_DATA': ExportScope.ALL_DATA
        }

        export_format = format_map.get(suggested_format)
        export_scope = scope_map.get(suggested_scope)

        if not export_format:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid export format: {suggested_format}",
            )

        if not export_scope:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid export scope: {suggested_scope}",
            )

        # Convert string responses to enums
        response_map = {
            'ACCEPTED': ExportSuggestionResponse.ACCEPTED,
            'REJECTED': ExportSuggestionResponse.REJECTED,
            'IGNORED': ExportSuggestionResponse.IGNORED,
            'MODIFIED': ExportSuggestionResponse.MODIFIED
        }

        user_response_enum = response_map.get(user_response)
        if not user_response_enum:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid user response: {user_response}",
            )

        # Parse timestamps
        suggested_at = datetime.fromisoformat(suggested_at_str) if suggested_at_str else datetime.now()
        responded_at = datetime.fromisoformat(responded_at_str) if responded_at_str else datetime.now()

        # Initialize AI service and track response
        from app.services.export import AIExportService
        ai_service = AIExportService()

        success = await ai_service.track_suggestion_response(
            suggestion_id=suggestion_id,
            database_name=database_name,
            suggestion_type=suggestion_type,
            sql_context=sql_context,
            row_count=row_count,
            confidence=confidence,
            suggested_format=export_format,
            suggested_scope=export_scope,
            user_response=user_response_enum,
            response_time_ms=response_time_ms,
            suggested_at=suggested_at,
            responded_at=responded_at
        )

        if success:
            return {
                "success": True,
                "message": "Response tracked successfully"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track response",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking suggestion response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track suggestion response: {str(e)}",
        )


@router.get("/export/analytics", response_model=dict)
async def get_export_analytics(
    database_name: str,
    days: int = 7,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_session),
) -> dict:
    """
    Get export analytics data for AI suggestions.

    Args:
        database_name: Database name to filter analytics
        days: Number of days to look back (default: 7)
        user_id: User ID from header
        session: Database session

    Returns:
        Analytics statistics

    Raises:
        HTTPException: If analytics retrieval fails
    """
    try:
        # Validate days parameter
        if days < 1 or days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Days must be between 1 and 365",
            )

        # Initialize AI service and get analytics
        from app.services.export import AIExportService
        ai_service = AIExportService()

        result = await ai_service.get_export_analytics(
            database_name=database_name,
            days=days
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting export analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get export analytics: {str(e)}",
        )

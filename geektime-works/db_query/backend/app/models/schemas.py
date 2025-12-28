"""API request/response schemas with camelCase aliases."""

from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime
from app.models.query import QuerySource


# Database Connection Schemas
class DatabaseConnectionInput(BaseModel):
    """Input schema for creating/updating database connection."""

    url: str = Field(..., description="Database connection URL (PostgreSQL or MySQL)")
    db_type: str | None = Field(default=None, alias="dbType", description="Database type (postgresql or mysql). Auto-detected from URL if not provided.")
    description: str | None = Field(default=None, max_length=200)


class DatabaseConnectionResponse(BaseModel):
    """Response schema for database connection."""

    name: str
    url: str
    db_type: str = Field(..., alias="dbType")
    description: str | None
    created_at: datetime
    updated_at: datetime
    last_connected_at: datetime | None
    status: str


# Metadata Schemas
class ColumnMetadata(BaseModel):
    """Column metadata schema."""

    name: str = Field(..., max_length=63)
    data_type: str = Field(..., alias="dataType")
    nullable: bool
    primary_key: bool = Field(..., alias="primaryKey")
    unique: bool = False
    default_value: str | None = Field(default=None, alias="defaultValue")
    comment: str | None = None


class TableMetadata(BaseModel):
    """Table/View metadata schema."""

    name: str = Field(..., max_length=63)
    type: Literal["table", "view"]
    columns: list[ColumnMetadata]
    row_count: int | None = Field(default=None, alias="rowCount")
    schema_name: str = Field(default="public", alias="schemaName")


class DatabaseMetadataResponse(BaseModel):
    """Response schema for database metadata."""

    database_name: str = Field(..., alias="databaseName")
    tables: list[TableMetadata]
    views: list[TableMetadata]
    fetched_at: datetime = Field(..., alias="fetchedAt")
    is_stale: bool = Field(..., alias="isStale")


# Query Schemas
class QueryInput(BaseModel):
    """Input schema for SQL query execution."""

    sql: str = Field(..., min_length=1, description="SQL SELECT query to execute")


class QueryColumn(BaseModel):
    """Query result column schema."""

    name: str
    data_type: str = Field(..., alias="dataType")


class QueryResult(BaseModel):
    """Query result response schema."""

    columns: list[QueryColumn]
    rows: list[dict[str, Any]]
    row_count: int = Field(..., alias="rowCount")
    execution_time_ms: int = Field(..., alias="executionTimeMs")
    sql: str


class QueryHistoryEntry(BaseModel):
    """Query history entry schema."""

    id: int
    database_name: str = Field(..., alias="databaseName")
    sql_text: str = Field(..., alias="sqlText")
    executed_at: datetime = Field(..., alias="executedAt")
    execution_time_ms: int | None = Field(None, alias="executionTimeMs")
    row_count: int | None = Field(None, alias="rowCount")
    success: bool
    error_message: str | None = Field(None, alias="errorMessage")
    query_source: str = Field(..., alias="querySource")


# Natural Language Schemas
class NaturalLanguageInput(BaseModel):
    """Input schema for natural language to SQL conversion."""

    prompt: str = Field(..., min_length=5, max_length=500)


class GeneratedSqlResponse(BaseModel):
    """Response schema for generated SQL."""

    sql: str
    explanation: str


# Error Schema
class ErrorResponse(BaseModel):
    """Error response schema."""

    error: dict[str, Any]


# Export Schemas
class ExportRequest(BaseModel):
    """Input schema for creating export task."""

    sql: str = Field(..., description="SQL query to export")
    format: str = Field(..., pattern="^(csv|json|markdown)$", description="Export format")
    export_all: bool = Field(default=False, alias="exportAll", description="Export all data or current page")


class ExportCheckRequest(BaseModel):
    """Input schema for checking export file size."""

    sql: str = Field(..., description="SQL query to check")
    format: str = Field(..., pattern="^(csv|json|markdown)$", description="Export format")
    use_sampling: bool = Field(default=False, alias="useSampling", description="Use sampling for accurate estimation")
    sample_size: int = Field(default=100, ge=10, le=1000, alias="sampleSize", description="Sample size for estimation")


class SizeEstimate(BaseModel):
    """File size estimation schema."""

    estimated_bytes: int = Field(..., alias="estimatedBytes", description="Estimated file size in bytes")
    estimated_mb: float = Field(..., alias="estimatedMb", description="Estimated file size in MB")
    bytes_per_row: int = Field(..., alias="bytesPerRow", description="Average bytes per row")
    method: str = Field(..., pattern="^(metadata|sample|actual)$", description="Estimation method")
    confidence: str = Field(..., pattern="^(low|medium|high)$", description="Estimation confidence")
    sample_size: int | None = Field(None, alias="sampleSize", description="Sample size if using sampling method")


class ExportCheckResponse(BaseModel):
    """Response schema for export size check."""

    allowed: bool = Field(..., description="Whether export is allowed")
    estimated_size: SizeEstimate = Field(..., alias="estimatedSize", description="Estimated file size")
    warning: str | None = Field(None, description="Warning message if near limit")
    recommendation: str | None = Field(None, description="Recommendation message")


class TaskResponse(BaseModel):
    """Response schema for export task status."""

    task_id: str = Field(..., alias="taskId", description="Task ID")
    status: str = Field(..., pattern="^(pending|running|completed|failed|cancelled)$", description="Task status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    file_url: str | None = Field(None, alias="fileUrl", description="Download URL when completed")
    error: str | None = Field(None, description="Error message if failed")


class ExportIntentRequest(BaseModel):
    """Input schema for AI export intent analysis."""

    database_name: str = Field(..., alias="databaseName", description="Database name")
    sql_text: str = Field(..., alias="sqlText", description="SQL query text")
    row_count: int = Field(..., alias="rowCount", description="Query result row count")
    execution_time_ms: int = Field(..., alias="executionTimeMs", description="Query execution time in ms")


class ExportIntentResponse(BaseModel):
    """Response schema for AI export intent analysis."""

    should_suggest_export: bool = Field(..., alias="shouldSuggestExport", description="Whether to suggest export")
    confidence: str = Field(..., pattern="^(low|medium|high)$", description="AI confidence level")
    reason: str = Field(..., description="Reason for suggestion")
    suggested_format: str | None = Field(None, alias="suggestedFormat", pattern="^(csv|json|markdown)$", description="Suggested format")
    suggested_scope: str | None = Field(None, alias="suggestedScope", pattern="^(current_page|all_data)$", description="Suggested scope")
    clarification_question: str | None = Field(None, alias="clarificationQuestion", description="Question to ask user if unclear")


class GenerateSQLRequest(BaseModel):
    """Input schema for AI SQL generation."""

    database_name: str = Field(..., alias="databaseName", description="Database name")
    user_prompt: str = Field(..., alias="userPrompt", description="User's natural language request")
    db_type: str = Field(..., alias="dbType", pattern="^(postgresql|mysql)$", description="Database type")
    format_hint: str | None = Field(None, alias="formatHint", pattern="^(csv|json|markdown)$", description="Optional export format hint")


class GenerateSQLResponse(BaseModel):
    """Response schema for AI SQL generation."""

    sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Query logic explanation")
    estimated_rows: int = Field(..., alias="estimatedRows", description="Estimated result row count")
    performance_tips: list[str] = Field(default_factory=list, alias="performanceTips", description="Performance optimization tips")
    warnings: list[str] = Field(default_factory=list, description="Potential warnings")


class ProactiveSuggestionRequest(BaseModel):
    """Input schema for proactive export suggestion."""

    sql_text: str = Field(..., alias="sqlText", description="SQL query text")
    row_count: int = Field(..., alias="rowCount", description="Query result row count")
    columns: list[QueryColumn] = Field(..., description="Query result columns")
    execution_time_ms: int = Field(..., alias="executionTimeMs", description="Query execution time in ms")


class ProactiveSuggestionResponse(BaseModel):
    """Response schema for proactive export suggestion."""

    suggestion_text: str = Field(..., alias="suggestionText", description="Suggestion text (max 30 chars)")
    quick_actions: list[str] = Field(default_factory=list, alias="quickActions", description="Quick action button texts")
    value_proposition: str = Field(..., alias="valueProposition", description="Value proposition description")


class TrackResponseRequest(BaseModel):
    """Input schema for tracking AI suggestion response."""

    suggestion_id: str = Field(..., alias="suggestionId", description="Suggestion UUID")
    database_name: str = Field(..., alias="databaseName", description="Database name")
    response: str = Field(..., pattern="^(accepted|rejected|ignored|modified)$", description="User response")
    response_time_ms: int | None = Field(None, alias="responseTimeMs", description="Response time in milliseconds")


class AnalyticsResponse(BaseModel):
    """Response schema for AI export analytics."""

    total_suggestions: int = Field(..., alias="totalSuggestions", description="Total suggestions")
    accepted_count: int = Field(..., alias="acceptedCount", description="Accepted count")
    accept_rate: float = Field(..., alias="acceptRate", description="Accept rate percentage")
    target_accept_rate: float = Field(..., alias="targetAcceptRate", description="Target accept rate")
    response_distribution: dict[str, int] = Field(..., alias="responseDistribution", description="Response distribution")
    avg_response_time_ms: float = Field(..., alias="avgResponseTimeMs", description="Average response time in ms")
    days_analyzed: int = Field(..., alias="daysAnalyzed", description="Number of days analyzed")

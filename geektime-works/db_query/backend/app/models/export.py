"""Export-related models and enums."""

from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlmodel import SQLModel, Field, Column, Text, DateTime


class ExportFormat(str, Enum):
    """Export format options."""

    CSV = "csv"
    JSON = "json"
    MARKDOWN = "markdown"


class ExportScope(str, Enum):
    """Export scope options."""

    CURRENT_PAGE = "current_page"
    ALL_DATA = "all_data"


class TaskStatus(str, Enum):
    """Export task status options."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportSuggestionResponse(str, Enum):
    """AI export suggestion response types."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    IGNORED = "ignored"
    MODIFIED = "modified"


class ExportTask(SQLModel, table=True):
    """
    Export task entity for tracking export operations.

    Attributes:
        id: Primary key
        task_id: UUID task identifier
        user_id: User identifier
        database_name: Database connection name (FK)
        sql_text: SQL query text
        export_format: Export format (csv/json/markdown)
        export_scope: Export scope (current_page/all_data)
        file_name: Generated file name
        file_path: Server file storage path
        file_size_bytes: Actual file size in bytes
        row_count: Actual exported row count
        status: Task status (pending/running/completed/failed/cancelled)
        progress: Progress percentage (0-100)
        error_message: Error message if failed
        started_at: Task start time
        completed_at: Task completion/failure/cancellation time
        execution_time_ms: Execution duration in milliseconds
        created_at: Task creation timestamp
    """

    __tablename__ = "exporttasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(default_factory=lambda: str(uuid4()), unique=True, index=True)
    user_id: str = Field(index=True)
    database_name: str = Field(foreign_key="databaseconnections.name", index=True)
    sql_text: str = Field(sa_column=Column(Text))
    export_format: ExportFormat
    export_scope: ExportScope
    file_name: Optional[str] = None
    file_path: Optional[str] = None
    file_size_bytes: Optional[int] = Field(
        default=None, le=104_857_600
    )  # 100MB limit
    row_count: Optional[int] = None
    status: TaskStatus = Field(default=TaskStatus.PENDING, index=True)
    progress: int = Field(default=0, ge=0, le=100)
    error_message: Optional[str] = Field(sa_column=Column(Text), default=None)
    started_at: Optional[datetime] = Field(default=None, index=True)
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
        sa_column=Column(DateTime(timezone=False), index=True),
    )


class AISuggestionAnalytics(SQLModel, table=True):
    """
    AI suggestion analytics for tracking export recommendations.

    Attributes:
        id: Primary key
        suggestion_id: UUID suggestion identifier
        database_name: Database connection name
        suggestion_type: Suggestion type (export_intent/export_sql/proactive)
        sql_context: SQL query context
        row_count: Query result row count
        confidence: AI confidence level (high/medium/low)
        suggested_format: Suggested export format
        suggested_scope: Suggested export scope
        user_response: User response (accepted/rejected/ignored/modified)
        response_time_ms: User response time in milliseconds
        suggested_at: Suggestion generation timestamp
        responded_at: User response timestamp
    """

    __tablename__ = "aisuggestionanalytics"

    id: Optional[int] = Field(default=None, primary_key=True)
    suggestion_id: str = Field(default_factory=lambda: str(uuid4()), unique=True)
    database_name: str = Field(index=True)
    suggestion_type: str
    sql_context: Optional[str] = Field(sa_column=Column(Text), default=None)
    row_count: Optional[int] = None
    confidence: Optional[str] = None
    suggested_format: Optional[str] = None
    suggested_scope: Optional[str] = None
    user_response: ExportSuggestionResponse = Field(index=True)
    response_time_ms: Optional[int] = None
    suggested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None), index=True)
    responded_at: Optional[datetime] = None

    @property
    def is_accepted(self) -> bool:
        """Check if the suggestion was accepted by the user."""
        return self.user_response == ExportSuggestionResponse.ACCEPTED

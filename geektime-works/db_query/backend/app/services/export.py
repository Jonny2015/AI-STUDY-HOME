"""Export service for handling data export operations."""

import asyncio
import csv
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, AsyncGenerator, Optional
from uuid import uuid4

from app.adapters.base import DatabaseAdapter, QueryResult
from app.config import settings
from app.models.database import DatabaseConnection, DatabaseType
from app.models.export import ExportFormat, ExportScope, TaskStatus, ExportTask
from app.models.schemas import ExportCheckResponse, SizeEstimate, TaskResponse
from app.services.sql_validator import validate_sql
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


class ExportError(Exception):
    """Base exception for export errors."""

    pass


class FileSizeExceededError(ExportError):
    """Raised when export file size exceeds limit."""

    pass


class ConcurrentTaskLimitError(ExportError):
    """Raised when concurrent task limit is exceeded."""

    pass


class Task:
    """Internal task representation for tracking export operations."""

    def __init__(
        self,
        task_id: str,
        user_id: str,
        database_name: str,
        sql: str,
        export_format: ExportFormat,
        export_scope: ExportScope,
        file_path: Path,
    ):
        self.task_id = task_id
        self.user_id = user_id
        self.database_name = database_name
        self.sql = sql
        self.export_format = export_format
        self.export_scope = export_scope
        self.file_path = file_path
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.error: Optional[str] = None
        self.file_size_bytes: Optional[int] = None
        self.row_count: Optional[int] = None
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.execution_time_ms: Optional[int] = None
        self._cancel_event = asyncio.Event()

    def cancel(self) -> None:
        """Mark task for cancellation."""
        self._cancel_event.set()

    def is_cancelled(self) -> bool:
        """Check if task was cancelled."""
        return self._cancel_event.is_set()


class TaskManager:
    """Singleton task manager for tracking export operations."""

    _instance: Optional["TaskManager"] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> "TaskManager":
        """Ensure singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize task manager."""
        if self._initialized:
            return

        self._tasks: dict[str, Task] = {}
        self._semaphore = asyncio.Semaphore(settings.export_max_concurrent_per_user)
        self._initialized = True
        logger.info("TaskManager initialized")

    async def add_task(self, task: Task) -> None:
        """Add a new task to the queue.

        Args:
            task: Task to add

        Raises:
            ConcurrentTaskLimitError: If concurrent limit exceeded
        """
        active_count = self._get_active_task_count(task.user_id)

        if active_count >= settings.export_max_concurrent_per_user:
            raise ConcurrentTaskLimitError(
                f"Maximum {settings.export_max_concurrent_per_user} concurrent "
                f"export tasks per user allowed"
            )

        self._tasks[task.task_id] = task
        logger.info(
            f"Added task {task.task_id} for user {task.user_id} "
            f"(active: {active_count + 1})"
        )

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task if found, None otherwise
        """
        return self._tasks.get(task_id)

    async def update_task(
        self,
        task_id: str,
        status: Optional[TaskStatus] = None,
        progress: Optional[int] = None,
        error: Optional[str] = None,
        file_size_bytes: Optional[int] = None,
        row_count: Optional[int] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        execution_time_ms: Optional[int] = None,
    ) -> None:
        """Update task status.

        Args:
            task_id: Task ID
            status: New status
            progress: Progress percentage (0-100)
            error: Error message
            file_size_bytes: File size in bytes
            row_count: Number of rows exported
            started_at: Task start time
            completed_at: Task completion time
            execution_time_ms: Execution time in milliseconds
        """
        task = self._tasks.get(task_id)
        if not task:
            logger.warning(f"Task {task_id} not found for update")
            return

        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = progress
        if error is not None:
            task.error = error
        if file_size_bytes is not None:
            task.file_size_bytes = file_size_bytes
        if row_count is not None:
            task.row_count = row_count
        if started_at is not None:
            task.started_at = started_at
        if completed_at is not None:
            task.completed_at = completed_at
        if execution_time_ms is not None:
            task.execution_time_ms = execution_time_ms

        logger.debug(
            f"Updated task {task_id}: status={status}, progress={progress}%"
        )

    def remove_task(self, task_id: str) -> None:
        """Remove task from tracking.

        Args:
            task_id: Task ID
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            logger.info(f"Removed task {task_id}")

    def _get_active_task_count(self, user_id: str) -> int:
        """Get count of active tasks for user.

        Args:
            user_id: User ID

        Returns:
            Number of active (pending/running) tasks
        """
        return sum(
            1
            for task in self._tasks.values()
            if task.user_id == user_id
            and task.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
        )


class ExportService:
    """Service for managing data export operations.

    This service handles:
    - File size estimation
    - Export task execution (CSV/JSON/Markdown)
    - Task progress tracking
    - Concurrent task management
    """

    def __init__(self, session: AsyncSession):
        """Initialize export service.

        Args:
            session: Database session for persistence
        """
        self.session = session
        self.task_manager = TaskManager()
        self.export_dir = settings.export_temp_path
        self.max_file_size_bytes = settings.export_max_file_size_mb * 1024 * 1024
        self.timeout = settings.export_timeout_seconds

    async def estimate_file_size(
        self,
        adapter: DatabaseAdapter,
        sql: str,
        export_format: ExportFormat,
        db_type: DatabaseType,
        use_sampling: bool = False,
        sample_size: int = 100,
    ) -> SizeEstimate:
        """Estimate export file size using three methods.

        Methods:
        1. metadata: Use table statistics (fastest, lowest confidence)
        2. sample: Query sample rows (medium speed, medium confidence)
        3. actual: Full query execution (slowest, highest confidence)

        Args:
            adapter: Database adapter
            sql: SQL query
            export_format: Export format
            db_type: Database type
            use_sampling: If True, use sampling method
            sample_size: Number of rows for sampling

        Returns:
            SizeEstimate with file size information
        """
        # Validate SQL first
        is_valid, error_msg = validate_sql(sql, db_type)
        if not is_valid:
            raise ExportError(f"Invalid SQL: {error_msg}")

        if use_sampling:
            return await self._estimate_by_sampling(
                adapter, sql, export_format, sample_size
            )
        else:
            return await self._estimate_by_metadata(adapter, sql, export_format)

    async def _estimate_by_metadata(
        self,
        adapter: DatabaseAdapter,
        sql: str,
        export_format: ExportFormat,
    ) -> SizeEstimate:
        """Estimate file size using database metadata.

        This method queries table statistics for row count and
        estimates column sizes based on data types.

        Args:
            adapter: Database adapter
            sql: SQL query
            export_format: Export format

        Returns:
            SizeEstimate with low confidence
        """
        # For simplicity, use a rough estimate based on table statistics
        # In production, you'd parse the SQL and query information_schema

        # Execute COUNT(*) to get row count
        count_sql = f"SELECT COUNT(*) as total FROM ({sql}) AS subq"
        count_result = await adapter.execute_query(count_sql)
        row_count = count_result.rows[0]["total"]

        # Estimate average row size based on format
        avg_row_sizes = {
            ExportFormat.CSV: 100,  # bytes
            ExportFormat.JSON: 150,  # bytes (includes JSON overhead)
            ExportFormat.MARKDOWN: 120,  # bytes (includes table formatting)
        }

        bytes_per_row = avg_row_sizes.get(export_format, 100)
        estimated_bytes = row_count * bytes_per_row
        estimated_mb = estimated_bytes / (1024 * 1024)

        return SizeEstimate(
            estimated_bytes=estimated_bytes,
            estimated_mb=round(estimated_mb, 2),
            bytes_per_row=bytes_per_row,
            method="metadata",
            confidence="low",
            sample_size=None,
        )

    async def _estimate_by_sampling(
        self,
        adapter: DatabaseAdapter,
        sql: str,
        export_format: ExportFormat,
        sample_size: int,
    ) -> SizeEstimate:
        """Estimate file size by querying sample rows.

        This method executes the query with LIMIT to get actual rows
        and measures their size.

        Args:
            adapter: Database adapter
            sql: SQL query
            export_format: Export format
            sample_size: Number of sample rows

        Returns:
            SizeEstimate with medium confidence
        """
        # Add LIMIT to get sample rows
        sample_sql = f"{sql} LIMIT {sample_size}"
        result = await adapter.execute_query(sample_sql)

        # Calculate actual size for sample rows
        sample_bytes = 0
        for row in result.rows:
            if export_format == ExportFormat.CSV:
                sample_bytes += len(self._generate_csv_row(result.columns, row))
            elif export_format == ExportFormat.JSON:
                sample_bytes += len(self._generate_json_row(row))
            elif export_format == ExportFormat.MARKDOWN:
                sample_bytes += len(self._generate_markdown_row(result.columns, row))

        if result.row_count > 0:
            bytes_per_row = sample_bytes // result.row_count
        else:
            bytes_per_row = 100  # Default estimate

        # Get total row count
        count_sql = f"SELECT COUNT(*) as total FROM ({sql}) AS subq"
        count_result = await adapter.execute_query(count_sql)
        total_rows = count_result.rows[0]["total"]

        estimated_bytes = total_rows * bytes_per_row
        estimated_mb = estimated_bytes / (1024 * 1024)

        return SizeEstimate(
            estimated_bytes=estimated_bytes,
            estimated_mb=round(estimated_mb, 2),
            bytes_per_row=bytes_per_row,
            method="sample",
            confidence="medium",
            sample_size=result.row_count,
        )

    async def check_export_size(
        self,
        adapter: DatabaseAdapter,
        sql: str,
        export_format: ExportFormat,
        db_type: DatabaseType,
        use_sampling: bool = False,
        sample_size: int = 100,
    ) -> ExportCheckResponse:
        """Check if export is allowed based on file size.

        Args:
            adapter: Database adapter
            sql: SQL query
            export_format: Export format
            db_type: Database type
            use_sampling: Use sampling for estimation
            sample_size: Sample size for estimation

        Returns:
            ExportCheckResponse with allowance status and recommendations
        """
        estimate = await self.estimate_file_size(
            adapter, sql, export_format, db_type, use_sampling, sample_size
        )

        allowed = estimate.estimated_bytes <= self.max_file_size_bytes

        warning = None
        recommendation = None

        if not allowed:
            max_mb = self.max_file_size_bytes / (1024 * 1024)
            warning = (
                f"Estimated file size ({estimate.estimated_mb:.2f} MB) "
                f"exceeds maximum allowed ({max_mb:.2f} MB)"
            )
            recommendation = (
                "Consider adding WHERE clause to filter results or "
                "selecting specific columns"
            )
        elif estimate.estimated_mb > self.max_file_size_bytes / (1024 * 1024) * 0.8:
            warning = (
                f"Estimated file size ({estimate.estimated_mb:.2f} MB) "
                f"is close to maximum limit"
            )

        return ExportCheckResponse(
            allowed=allowed,
            estimatedSize=estimate,
            warning=warning,
            recommendation=recommendation,
        )

    async def execute_export(
        self,
        task_id: str,
        adapter: DatabaseAdapter,
        sql: str,
        export_format: ExportFormat,
        export_scope: ExportScope,
        user_id: str,
        database_name: str,
    ) -> TaskResponse:
        """Execute export task asynchronously.

        Args:
            task_id: Task ID
            adapter: Database adapter
            sql: SQL query
            export_format: Export format
            export_scope: Export scope
            user_id: User ID
            database_name: Database name

        Returns:
            TaskResponse with initial task status
        """
        # Generate file path
        filename = self._generate_filename(export_format)
        file_path = self.export_dir / filename

        # Create internal task
        task = Task(
            task_id=task_id,
            user_id=user_id,
            database_name=database_name,
            sql=sql,
            export_format=export_format,
            export_scope=export_scope,
            file_path=file_path,
        )

        # Add task to manager
        await self.task_manager.add_task(task)

        # Start export in background
        asyncio.create_task(
            self._execute_export_task(task, adapter, sql, export_format)
        )

        # Return initial response
        return TaskResponse(
            taskId=task_id,
            status=task.status,
            progress=task.progress,
            fileUrl=None,
            error=None,
        )

    async def _execute_export_task(
        self,
        task: Task,
        adapter: DatabaseAdapter,
        sql: str,
        export_format: ExportFormat,
    ) -> None:
        """Execute export task in background.

        Args:
            task: Internal task object
            adapter: Database adapter
            sql: SQL query
            export_format: Export format
        """
        started_at = datetime.now(timezone.utc).replace(tzinfo=None)

        try:
            # Update status to running
            await self.task_manager.update_task(
                task.task_id,
                status=TaskStatus.RUNNING,
                progress=0,
                started_at=started_at,
            )

            # Validate export constraints
            await self._validate_export_constraints(adapter, sql, export_format)

            # Execute export based on format
            if export_format == ExportFormat.CSV:
                await self._export_to_csv(task, adapter, sql)
            elif export_format == ExportFormat.JSON:
                await self._export_to_json(task, adapter, sql)
            elif export_format == ExportFormat.MARKDOWN:
                await self._export_to_markdown(task, adapter, sql)

            # Get file size
            file_size = task.file_path.stat().st_size

            # Calculate execution time
            completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            execution_time_ms = int((completed_at - started_at).total_seconds() * 1000)

            # Update task as completed
            await self.task_manager.update_task(
                task.task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                file_size_bytes=file_size,
                completed_at=completed_at,
                execution_time_ms=execution_time_ms,
            )

            logger.info(
                f"Export task {task.task_id} completed: "
                f"{task.row_count} rows, {file_size} bytes"
            )

        except asyncio.CancelledError:
            # Task was cancelled
            completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.task_manager.update_task(
                task.task_id,
                status=TaskStatus.CANCELLED,
                progress=task.progress,
                completed_at=completed_at,
            )
            logger.info(f"Export task {task.task_id} was cancelled")

        except Exception as e:
            # Task failed
            completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            error_msg = str(e)
            await self.task_manager.update_task(
                task.task_id,
                status=TaskStatus.FAILED,
                error=error_msg,
                completed_at=completed_at,
            )
            logger.error(f"Export task {task.task_id} failed: {error_msg}")

            # Clean up partial file
            if task.file_path.exists():
                task.file_path.unlink()

    async def _validate_export_constraints(
        self,
        adapter: DatabaseAdapter,
        sql: str,
        export_format: ExportFormat,
    ) -> None:
        """Validate export constraints before execution.

        Args:
            adapter: Database adapter
            sql: SQL query
            export_format: Export format

        Raises:
            FileSizeExceededError: If file size would exceed limit
        """
        # Quick estimate using metadata
        estimate = await self._estimate_by_metadata(adapter, sql, export_format)

        if estimate.estimated_bytes > self.max_file_size_bytes:
            max_mb = self.max_file_size_bytes / (1024 * 1024)
            raise FileSizeExceededError(
                f"Estimated file size ({estimate.estimated_mb:.2f} MB) "
                f"exceeds maximum allowed ({max_mb:.2f} MB)"
            )

    async def _export_to_csv(
        self,
        task: Task,
        adapter: DatabaseAdapter,
        sql: str,
    ) -> None:
        """Export data to CSV format.

        Args:
            task: Export task
            adapter: Database adapter
            sql: SQL query
        """
        # Execute query
        result = await adapter.execute_query(sql)
        task.row_count = result.row_count

        # Write CSV file
        with open(task.file_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)

            # Write header
            header = [col["name"] for col in result.columns]
            writer.writerow(header)

            # Write rows
            batch_size = 1000
            for idx, row in enumerate(result.rows):
                if task.is_cancelled():
                    raise asyncio.CancelledError()

                csv_row = self._generate_csv_row(result.columns, row)
                writer.writerow(csv_row)

                # Update progress
                if (idx + 1) % batch_size == 0:
                    progress = int((idx + 1) / result.row_count * 100)
                    await self.task_manager.update_task(task.task_id, progress=progress)

    async def _export_to_json(
        self,
        task: Task,
        adapter: DatabaseAdapter,
        sql: str,
    ) -> None:
        """Export data to JSON format.

        Args:
            task: Export task
            adapter: Database adapter
            sql: SQL query
        """
        # Execute query
        result = await adapter.execute_query(sql)
        task.row_count = result.row_count

        # Write JSON file
        with open(task.file_path, "w", encoding="utf-8") as f:
            f.write("[\n")

            batch_size = 1000
            for idx, row in enumerate(result.rows):
                if task.is_cancelled():
                    raise asyncio.CancelledError()

                json_row = self._generate_json_row(row)
                f.write(json_row)

                # Add comma if not last row
                if idx < result.row_count - 1:
                    f.write(",\n")
                else:
                    f.write("\n")

                # Update progress
                if (idx + 1) % batch_size == 0:
                    progress = int((idx + 1) / result.row_count * 100)
                    await self.task_manager.update_task(task.task_id, progress=progress)

            f.write("]\n")

    async def _export_to_markdown(
        self,
        task: Task,
        adapter: DatabaseAdapter,
        sql: str,
    ) -> None:
        """Export data to Markdown table format.

        Args:
            task: Export task
            adapter: Database adapter
            sql: SQL query
        """
        # Execute query
        result = await adapter.execute_query(sql)
        task.row_count = result.row_count

        # Write Markdown file
        with open(task.file_path, "w", encoding="utf-8") as f:
            # Write header
            header = [col["name"] for col in result.columns]
            f.write("| " + " | ".join(header) + " |\n")
            f.write("| " + " | ".join(["---"] * len(header)) + " |\n")

            # Write rows
            batch_size = 1000
            for idx, row in enumerate(result.rows):
                if task.is_cancelled():
                    raise asyncio.CancelledError()

                md_row = self._generate_markdown_row(result.columns, row)
                f.write(md_row + "\n")

                # Update progress
                if (idx + 1) % batch_size == 0:
                    progress = int((idx + 1) / result.row_count * 100)
                    await self.task_manager.update_task(task.task_id, progress=progress)

    def _generate_csv_row(
        self, columns: list[dict[str, str]], row: dict[str, Any]
    ) -> list[str]:
        """Generate CSV row from database row.

        Args:
            columns: Column definitions
            row: Database row

        Returns:
            List of string values for CSV
        """
        csv_row = []
        for col in columns:
            value = row.get(col["name"])
            csv_row.append(self._serialize_value(value))
        return csv_row

    def _generate_json_row(self, row: dict[str, Any]) -> str:
        """Generate JSON row from database row.

        Args:
            row: Database row

        Returns:
            JSON string
        """
        serialized = self._serialize_for_json(row)
        return json.dumps(serialized, ensure_ascii=False)

    def _generate_markdown_row(
        self, columns: list[dict[str, str]], row: dict[str, Any]
    ) -> str:
        """Generate Markdown table row from database row.

        Args:
            columns: Column definitions
            row: Database row

        Returns:
            Markdown table row string
        """
        values = []
        for col in columns:
            value = row.get(col["name"])
            serialized = self._serialize_value(value)
            # Escape pipe characters in Markdown
            serialized = serialized.replace("|", "\\|")
            values.append(serialized)
        return "| " + " | ".join(values) + " |"

    def _serialize_for_json(self, value: Any) -> Any:
        """Serialize value for JSON encoding.

        Args:
            value: Value to serialize

        Returns:
            Serialized value
        """
        if value is None:
            return None
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return float(value)
        elif isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        else:
            return value

    def _serialize_value(self, value: Any) -> str:
        """Serialize value to string.

        Args:
            value: Value to serialize

        Returns:
            String representation
        """
        if value is None:
            return ""
        elif isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, Decimal):
            return str(value)
        elif isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        else:
            return str(value)

    def _generate_filename(self, export_format: ExportFormat) -> str:
        """Generate unique filename for export.

        Args:
            export_format: Export format

        Returns:
            Filename in format: export-{uuid}.{ext}
        """
        ext = {
            ExportFormat.CSV: "csv",
            ExportFormat.JSON: "json",
            ExportFormat.MARKDOWN: "md",
        }[export_format]

        return f"export-{uuid4()}.{ext}"

    async def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """Get export task status.

        Args:
            task_id: Task ID

        Returns:
            TaskResponse if task exists, None otherwise
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            return None

        file_url = None
        if task.status == TaskStatus.COMPLETED:
            file_url = f"/api/v1/exports/download/{task.file_path.name}"

        return TaskResponse(
            taskId=task.task_id,
            status=task.status,
            progress=task.progress,
            fileUrl=file_url,
            error=task.error,
        )

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel export task.

        Args:
            task_id: Task ID

        Returns:
            True if task was cancelled, False if not found
        """
        task = self.task_manager.get_task(task_id)
        if not task:
            return False

        if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
            task.cancel()

            # Update status
            completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
            await self.task_manager.update_task(
                task.task_id,
                status=TaskStatus.CANCELLED,
                completed_at=completed_at,
            )

            # Clean up file if exists
            if task.file_path.exists():
                task.file_path.unlink()

            return True

        return False

    async def _cleanup_task(self, task: Task) -> None:
        """Clean up task resources.

        Args:
            task: Task to clean up
        """
        # Remove file if exists
        if task.file_path.exists():
            try:
                task.file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete file {task.file_path}: {e}")

        # Remove from task manager
        self.task_manager.remove_task(task.task_id)

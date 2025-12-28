"""
导出约束验证单元测试
验证文件大小限制和并发限制检查
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.export import ExportService, TaskManager, ExportTask
from app.models.export import ExportFormat, ExportScope, TaskStatus


class TestExportConstraints:
    """导出约束验证测试类"""

    @pytest.fixture
    def task_manager(self):
        """创建 TaskManager 实例"""
        return TaskManager()

    @pytest.fixture
    def export_service(self, task_manager):
        """创建 ExportService 实例"""
        with patch('app.services.export.TaskManager'):
            return ExportService(
                db_connection=MagicMock(),
                task_manager=task_manager
            )

    @pytest.fixture
    def mock_export_task(self):
        """创建导出任务模拟"""
        return ExportTask(
            task_id="test-task-id",
            user_id="user123",
            database_name="test_db",
            sql_text="SELECT * FROM users",
            export_format=ExportFormat.CSV,
            export_scope=ExportScope.ALL_DATA,
            file_name="test.csv",
            file_path="/tmp/test.csv",
            file_size_bytes=50 * 1024 * 1024,  # 50MB
            row_count=10000,
            status=TaskStatus.RUNNING,
            progress=50,
            started_at="2023-01-01T10:00:00",
            created_at="2023-01-01T10:00:00"
        )

    async def test_validate_export_size_within_limit(self, export_service):
        """测试文件大小在限制范围内"""
        # 设置估算结果在限制内 (100MB 限制)
        with patch.object(export_service, 'estimate_file_size') as mock_estimate:
            mock_estimate.return_value = AsyncMock(
                estimated_bytes=50 * 1024 * 1024,  # 50MB
                estimated_mb=50,
                confidence=0.9
            )

            # 验证应通过
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=50 * 1024 * 1024
            )

            assert result.is_valid is True
            assert result.warning_message is None

    async def test_validate_export_size_exceeds_limit(self, export_service):
        """测试文件大小超过限制"""
        # 设置估算结果超过限制
        with patch.object(export_service, 'estimate_file_size') as mock_estimate:
            mock_estimate.return_value = AsyncMock(
                estimated_bytes=150 * 1024 * 1024,  # 150MB
                estimated_mb=150,
                confidence=0.9
            )

            # 验证应拒绝
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=150 * 1024 * 1024
            )

            assert result.is_valid is False
            assert "文件大小超过限制" in result.warning_message

    async def test_validate_export_size_close_to_limit(self, export_service):
        """测试文件大小接近限制时显示警告"""
        # 设置估算结果接近限制
        with patch.object(export_service, 'estimate_file_size') as mock_estimate:
            mock_estimate.return_value = AsyncMock(
                estimated_bytes=95 * 1024 * 1024,  # 95MB
                estimated_mb=95,
                confidence=0.9
            )

            # 验证应通过但显示警告
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=95 * 1024 * 1024
            )

            assert result.is_valid is True
            assert "接近文件大小限制" in result.warning_message

    async def test_validate_export_size_with_sample_uncertainty(self, export_service):
        """测试样本不确定性时的警告"""
        # 设置低置信度的估算
        with patch.object(export_service, 'estimate_file_size') as mock_estimate:
            mock_estimate.return_value = AsyncMock(
                estimated_bytes=80 * 1024 * 1024,  # 80MB
                estimated_mb=80,
                confidence=0.3  # 低置信度
            )

            # 验证应通过但显示警告
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=80 * 1024 * 1024
            )

            assert result.is_valid is True
            assert "样本数据可能无法准确反映实际大小" in result.warning_message

    async def test_validate_concurrent_limit_within_limit(self, export_service, task_manager, mock_export_task):
        """测试并发数在限制范围内"""
        # 设置用户有2个活跃任务
        task_manager.tasks = {
            "task1": mock_export_task,
            "task2": mock_export_task
        }

        # 模拟任务更新活跃任务计数
        with patch.object(task_manager, 'get_active_task_count', return_value=2):
            # 验证应通过 (3个限制)
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=10 * 1024 * 1024
            )

            assert result.is_valid is True
            assert result.warning_message is None

    async def test_validate_concurrent_limit_exceeds(self, export_service, task_manager, mock_export_task):
        """测试并发数超过限制"""
        # 设置用户有3个活跃任务
        task_manager.tasks = {
            "task1": mock_export_task,
            "task2": mock_export_task,
            "task3": mock_export_task
        }

        with patch.object(task_manager, 'get_active_task_count', return_value=3):
            # 验证应拒绝
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=10 * 1024 * 1024
            )

            assert result.is_valid is False
            assert "并发任务数超过限制" in result.warning_message

    async def test_validate_concurrent_limit_with_completed_tasks(self, export_service, task_manager, mock_export_task):
        """测试已完成任务不影响并发限制"""
        # 设置用户有3个任务，其中1个已完成
        completed_task = mock_export_task.copy()
        completed_task.status = TaskStatus.COMPLETED

        task_manager.tasks = {
            "task1": mock_export_task,  # 运行中
            "task2": mock_export_task,  # 运行中
            "task3": completed_task     # 已完成
        }

        with patch.object(task_manager, 'get_active_task_count', return_value=2):
            # 验证应通过
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=10 * 1024 * 1024
            )

            assert result.is_valid is True

    async def test_validate_both_constraints_fail(self, export_service):
        """测试文件大小和并发限制都失败的情况"""
        # 超过文件大小限制
        with patch.object(export_service, 'estimate_file_size') as mock_estimate:
            mock_estimate.return_value = AsyncMock(
                estimated_bytes=150 * 1024 * 1024,  # 150MB
                estimated_mb=150,
                confidence=0.9
            )

            # 并发超过限制（模拟）
            with patch.object(export_service.task_manager, 'get_active_task_count', return_value=3):
                # 验证应拒绝，文件大小优先
                result = await export_service._validate_export_constraints(
                    user_id="user123",
                    estimated_size=150 * 1024 * 1024
                )

                assert result.is_valid is False
                assert "文件大小超过限制" in result.warning_message

    async def test_validate_large_file_with_warning(self, export_service):
        """测试大文件但未超过限制时的警告"""
        # 设置接近限制的文件大小
        with patch.object(export_service, 'estimate_file_size') as mock_estimate:
            mock_estimate.return_value = AsyncMock(
                estimated_bytes=90 * 1024 * 1024,  # 90MB
                estimated_mb=90,
                confidence=0.9
            )

            # 验证应通过但显示警告
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=90 * 1024 * 1024
            )

            assert result.is_valid is True
            assert "接近文件大小限制" in result.warning_message

    async def test_validate_export_size_zero_bytes(self, export_service):
        """测试零字节文件的处理"""
        with patch.object(export_service, 'estimate_file_size') as mock_estimate:
            mock_estimate.return_value = AsyncMock(
                estimated_bytes=0,
                estimated_mb=0,
                confidence=1.0
            )

            # 验证应通过（零字节文件有效）
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=0
            )

            assert result.is_valid is True
            assert result.warning_message is None

    async def test_validate_export_size_exact_limit(self, export_service):
        """测试正好等于限制的文件大小"""
        with patch.object(export_service, 'estimate_file_size') as mock_estimate:
            mock_estimate.return_value = AsyncMock(
                estimated_bytes=100 * 1024 * 1024,  # 正好 100MB
                estimated_mb=100,
                confidence=0.9
            )

            # 验证应通过（等于限制是允许的）
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=100 * 1024 * 1024
            )

            assert result.is_valid is True
            assert result.warning_message is None

    async def test_validate_export_uncertain_estimate(self, export_service):
        """测试不确定的估算结果"""
        with patch.object(export_service, 'estimate_file_size') as mock_estimate:
            mock_estimate.return_value = AsyncMock(
                estimated_bytes=50 * 1024 * 1024,  # 50MB
                estimated_mb=50,
                confidence=0.2  # 很低的置信度
            )

            # 验证应通过但显示警告
            result = await export_service._validate_export_constraints(
                user_id="user123",
                estimated_size=50 * 1024 * 1024
            )

            assert result.is_valid is True
            assert "样本数据可能无法准确反映实际大小" in result.warning_message
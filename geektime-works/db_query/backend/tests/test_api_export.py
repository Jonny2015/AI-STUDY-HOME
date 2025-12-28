"""
导出 API 端点集成测试
测试创建任务、查询状态、下载文件的完整流程
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import uuid4

from app.main import app
from app.services.export import ExportService, TaskManager
from app.models.export import ExportFormat, ExportScope, TaskStatus


class TestExportAPI:
    """导出 API 集成测试类"""

    @pytest.fixture
    def mock_export_service(self):
        """创建模拟的 ExportService"""
        with patch('app.api.v1.export.ExportService') as mock:
            service = AsyncMock(spec=ExportService)
            mock.return_value = service
            yield service

    @pytest.fixture
    def mock_task_manager(self):
        """创建模拟的 TaskManager"""
        with patch('app.services.export.TaskManager') as mock:
            manager = AsyncMock(spec=TaskManager)
            mock.return_value = manager
            yield manager

    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    async def test_create_export_task_success(self, client, mock_export_service, mock_task_manager):
        """测试成功创建导出任务"""
        # 设置模拟返回值
        mock_export_service.check_export_size.return_value = {
            "estimatedBytes": 50 * 1024 * 1024,
            "estimatedMb": 50,
            "bytesPerRow": 500,
            "method": "metadata",
            "confidence": 0.9
        }
        mock_export_service.execute_export.return_value = "task-id-123"

        # 发送请求
        response = await client.post(
            "/api/v1/dbs/test_db/export",
            json={
                "sql": "SELECT * FROM users",
                "format": "csv",
                "exportAll": True
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["taskId"] == "task-id-123"
        assert "task 创建成功" in data["message"]

    async def test_create_export_task_size_warning(self, client, mock_export_service, mock_task_manager):
        """测试创建导出任务时显示大小警告"""
        # 设置返回大小警告
        mock_export_service.check_export_size.return_value = {
            "estimatedBytes": 95 * 1024 * 1024,
            "estimatedMb": 95,
            "warningMessage": "接近文件大小限制",
            "shouldProceed": True
        }
        mock_export_service.execute_export.return_value = "task-id-123"

        # 发送请求
        response = await client.post(
            "/api/v1/dbs/test_db/export",
            json={
                "sql": "SELECT * FROM users",
                "format": "csv",
                "exportAll": True
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["taskId"] == "task-id-123"

    async def test_create_export_task_size_exceeded(self, client, mock_export_service, mock_task_manager):
        """测试文件大小超过限制时拒绝创建任务"""
        # 设置返回大小超过限制
        mock_export_service.check_export_size.return_value = {
            "estimatedBytes": 150 * 1024 * 1024,
            "estimatedMb": 150,
            "warningMessage": "文件大小超过限制",
            "shouldProceed": False
        }

        # 发送请求
        response = await client.post(
            "/api/v1/dbs/test_db/export",
            json={
                "sql": "SELECT * FROM users",
                "format": "csv",
                "exportAll": True
            }
        )

        # 验证响应
        assert response.status_code == 429
        data = response.json()
        assert "文件大小超过限制" in data["detail"]

    async def test_create_export_task_concurrent_limit(self, client, mock_export_service, mock_task_manager):
        """测试并发限制时拒绝创建任务"""
        # 设置返回并发限制错误
        mock_export_service.check_export_size.return_value = {
            "estimatedBytes": 10 * 1024 * 1024,
            "estimatedMb": 10,
            "warningMessage": "并发任务数超过限制",
            "shouldProceed": False
        }

        # 发送请求
        response = await client.post(
            "/api/v1/dbs/test_db/export",
            json={
                "sql": "SELECT * FROM users",
                "format": "csv",
                "exportAll": True
            }
        )

        # 验证响应
        assert response.status_code == 429
        data = response.json()
        assert "并发任务数超过限制" in data["detail"]

    async def test_get_task_status_success(self, client, mock_export_service, mock_task_manager):
        """测试成功获取任务状态"""
        # 设置模拟任务状态
        mock_export_service.get_task.return_value = {
            "taskId": "task-id-123",
            "status": "RUNNING",
            "progress": 50,
            "fileUrl": None,
            "error": None
        }

        # 发送请求
        response = await client.get("/api/v1/tasks/task-id-123")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["taskId"] == "task-id-123"
        assert data["status"] == "RUNNING"
        assert data["progress"] == 50

    async def test_get_task_status_not_found(self, client, mock_export_service, mock_task_manager):
        """测试获取不存在的任务状态"""
        # 设置返回 None
        mock_export_service.get_task.return_value = None

        # 发送请求
        response = await client.get("/api/v1/tasks/non-existent-task")

        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert "任务不存在" in data["detail"]

    async def test_cancel_task_success(self, client, mock_export_service, mock_task_manager):
        """测试成功取消任务"""
        # 设置模拟返回值
        mock_export_service.cancel_task.return_value = True

        # 发送请求
        response = await client.delete("/api/v1/tasks/task-id-123")

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "任务已取消" in data["message"]

    async def test_cancel_task_not_found(self, client, mock_export_service, mock_task_manager):
        """测试取消不存在的任务"""
        # 设置返回 False
        mock_export_service.cancel_task.return_value = False

        # 发送请求
        response = await client.delete("/api/v1/tasks/non-existent-task")

        # 验证响应
        assert response.status_code == 404
        data = response.json()
        assert "任务不存在" in data["detail"]

    async def test_download_file_success(self, client, mock_export_service, mock_task_manager):
        """测试成功下载文件"""
        # 设置文件内容
        file_content = b"id,name\n1,John\n2,Jane\n"

        with patch('builtins.open', mock_open(read_data=file_content)):
            # 发送请求
            response = await client.get("/api/v1/exports/download/test.csv")

            # 验证响应
            assert response.status_code == 200
            assert response.headers["content-disposition"] == 'attachment; filename="test.csv"'
            assert response.headers["content-type"] == "text/csv; charset=utf-8"
            assert await response.aread() == file_content

    async def test_download_file_not_found(self, client, mock_export_service, mock_task_manager):
        """测试下载不存在的文件"""
        # 模拟文件不存在
        with patch('builtins.open', side_effect=FileNotFoundError):
            # 发送请求
            response = await client.get("/api/v1/exports/download/nonexistent.csv")

            # 验证响应
            assert response.status_code == 404
            data = response.json()
            assert "文件不存在" in data["detail"]

    async def test_check_export_size(self, client, mock_export_service, mock_task_manager):
        """测试检查导出大小"""
        # 设置返回值
        mock_export_service.check_export_size.return_value = {
            "estimatedBytes": 50 * 1024 * 1024,
            "estimatedMb": 50,
            "bytesPerRow": 500,
            "method": "metadata",
            "confidence": 0.9,
            "warningMessage": None
        }

        # 发送请求
        response = await client.post(
            "/api/v1/dbs/test_db/export/check",
            json={
                "sql": "SELECT * FROM users",
                "format": "csv",
                "exportAll": True
            }
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["estimatedBytes"] == 50 * 1024 * 1024
        assert data["estimatedMb"] == 50
        assert data["confidence"] == 0.9

    async def test_invalid_database_name(self, client, mock_export_service, mock_task_manager):
        """测试无效的数据库名称"""
        # 发送无效请求
        response = await client.post(
            "/api/v1/dbs/invalid-db/export",
            json={
                "sql": "SELECT * FROM users",
                "format": "csv",
                "exportAll": True
            }
        )

        # 验证响应
        assert response.status_code == 404

    async def test_invalid_format(self, client, mock_export_service, mock_task_manager):
        """测试无效的导出格式"""
        # 发送无效格式
        response = await client.post(
            "/api/v1/dbs/test_db/export",
            json={
                "sql": "SELECT * FROM users",
                "format": "invalid_format",
                "exportAll": True
            }
        )

        # 验证响应
        assert response.status_code == 422  # Validation error

    async def test_sql_injection_attempt(self, client, mock_export_service, mock_task_manager):
        """测试 SQL 注入尝试"""
        # 发送包含 SQL 注入的请求
        response = await client.post(
            "/api/v1/dbs/test_db/export",
            json={
                "sql": "SELECT * FROM users; DROP TABLE users;",
                "format": "csv",
                "exportAll": True
            }
        )

        # 验证响应 - 应该被阻止
        assert response.status_code in [400, 422, 500]

    async def test_export_workflow_integration(self, client, mock_export_service, mock_task_manager):
        """测试完整的导出工作流集成"""
        # 1. 创建任务
        mock_export_service.check_export_size.return_value = {
            "estimatedBytes": 10 * 1024 * 1024,
            "estimatedMb": 10,
            "bytesPerRow": 500,
            "method": "metadata",
            "confidence": 0.9,
            "shouldProceed": True
        }
        mock_export_service.execute_export.return_value = "task-id-123"

        create_response = await client.post(
            "/api/v1/dbs/test_db/export",
            json={
                "sql": "SELECT * FROM users",
                "format": "csv",
                "exportAll": False
            }
        )

        assert create_response.status_code == 200
        task_id = create_response.json()["taskId"]

        # 2. 查询任务状态
        mock_export_service.get_task.return_value = {
            "taskId": task_id,
            "status": "RUNNING",
            "progress": 50,
            "fileUrl": None,
            "error": None
        }

        status_response = await client.get(f"/api/v1/tasks/{task_id}")
        assert status_response.status_code == 200
        assert status_response.json()["progress"] == 50

        # 3. 任务完成
        mock_export_service.get_task.return_value = {
            "taskId": task_id,
            "status": "COMPLETED",
            "progress": 100,
            "fileUrl": "/api/v1/exports/download/test.csv",
            "error": None
        }

        complete_response = await client.get(f"/api/v1/tasks/{task_id}")
        assert complete_response.status_code == 200
        assert complete_response.json()["status"] == "COMPLETED"
        assert complete_response.json()["progress"] == 100
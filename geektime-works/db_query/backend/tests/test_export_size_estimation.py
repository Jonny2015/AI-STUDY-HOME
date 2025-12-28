"""
导出文件大小估算单元测试
测试 metadata/sample/actual 三种估算方法
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.database import DatabaseConnection
from app.services.export import ExportService, TaskManager, ExportTask


class TestExportSizeEstimation:
    """导出文件大小估算测试类"""

    @pytest.fixture
    def export_service(self):
        """创建 ExportService 实例"""
        with patch('app.services.export.TaskManager'):
            return ExportService(
                db_connection=MagicMock(spec=DatabaseConnection),
                task_manager=MagicMock(spec=TaskManager)
            )

    @pytest.fixture
    def sample_data(self):
        """创建样本数据"""
        return [
            {
                "id": 1,
                "name": "张三",
                "email": "zhangsan@example.com",
                "age": 25,
                "salary": Decimal("10000.50"),
                "created_at": datetime(2023, 1, 1, 10, 0, 0),
                "is_active": True
            },
            {
                "id": 2,
                "name": "李四",
                "email": "lisi@example.com",
                "age": 30,
                "salary": Decimal("15000.75"),
                "created_at": datetime(2023, 1, 2, 10, 0, 0),
                "is_active": False
            }
        ]

    async def test_estimate_size_by_metadata_csv(self, export_service, sample_data):
        """测试 metadata 方式估算 CSV 文件大小"""
        # Mock 元数据获取
        export_service.db_connection.extract_metadata.return_value = {
            "users": {
                "columns": [
                    {"name": "id", "type": "integer", "max_length": None},
                    {"name": "name", "type": "varchar", "max_length": 50},
                    {"name": "email", "type": "varchar", "max_length": 100},
                    {"name": "age", "type": "integer", "max_length": None},
                    {"name": "salary", "type": "decimal", "precision": 10, "scale": 2},
                    {"name": "created_at", "type": "timestamp", "max_length": None},
                    {"name": "is_active", "type": "boolean", "max_length": None}
                ],
                "estimated_rows": 1000
            }
        }

        # 执行估算
        result = await export_service.estimate_file_size(
            table_name="users",
            format="csv",
            method="metadata"
        )

        # 验证结果
        assert result.method == "metadata"
        assert result.confidence > 0.7  # metadata 方法置信度较高
        assert result.estimated_bytes > 0
        assert result.sample_size == 0  # metadata 方法不使用样本

    async def test_estimate_size_by_sample_csv(self, export_service, sample_data):
        """测试 sample 方式估算 CSV 文件大小"""
        # Mock 数据获取
        export_service.db_connection.execute_query.return_value = sample_data

        # 执行估算
        result = await export_service.estimate_file_size(
            table_name="users",
            format="csv",
            method="sample"
        )

        # 验证结果
        assert result.method == "sample"
        assert result.sample_size == len(sample_data)
        assert result.confidence > 0.5
        assert result.estimated_bytes > 0
        assert result.bytes_per_row > 0

    async def test_estimate_size_by_actual_csv(self, export_service, sample_data):
        """测试 actual 方式估算 CSV 文件大小"""
        # Mock 数据获取
        export_service.db_connection.execute_query.return_value = sample_data

        # Mock 文件生成
        with patch.object(export_service, '_generate_csv_row') as mock_generate:
            mock_generate.side_effect = [
                "1,张三,zhangsan@example.com,25,10000.50,2023-01-01 10:00:00,True\n",
                "2,李四,lisi@example.com,30,15000.75,2023-01-02 10:00:00,False\n"
            ]

            # 执行估算
            result = await export_service.estimate_file_size(
                table_name="users",
                format="csv",
                method="actual"
            )

            # 验证结果
            assert result.method == "actual"
            assert result.sample_size == len(sample_data)
            assert result.confidence == 1.0  # actual 方法置信度最高
            assert result.estimated_bytes > 0

    async def test_estimate_size_json_format(self, export_service, sample_data):
        """测试 JSON 格式的文件大小估算"""
        # Mock 数据获取
        export_service.db_connection.execute_query.return_value = sample_data

        # Mock 文件生成
        with patch.object(export_service, '_serialize_for_json') as mock_serialize:
            mock_serialize.return_value = [
                '{"id": 1, "name": "张三", "email": "zhangsan@example.com"}',
                '{"id": 2, "name": "李四", "email": "lisi@example.com"}'
            ]

            # 执行估算
            result = await export_service.estimate_file_size(
                table_name="users",
                format="json",
                method="actual"
            )

            # 验证结果
            assert result.method == "actual"
            assert result.format_affected == True
            assert result.estimated_bytes > 0

    async def test_estimate_size_markdown_format(self, export_service, sample_data):
        """测试 Markdown 格式的文件大小估算"""
        # Mock 数据获取
        export_service.db_connection.execute_query.return_value = sample_data

        # Mock 文件生成
        with patch.object(export_service, '_generate_markdown_row') as mock_generate:
            mock_generate.return_value = "| 1 | 张三 | zhangsan@example.com |\n"

            # 执行估算
            result = await export_service.estimate_file_size(
                table_name="users",
                format="markdown",
                method="actual"
            )

            # 验证结果
            assert result.method == "actual"
            assert result.format_affected == True
            assert result.estimated_bytes > 0

    async def test_estimate_size_confidence_levels(self, export_service):
        """测试不同方法的置信度级别"""
        # metadata 方法 - 高置信度
        metadata_result = await export_service.estimate_file_size(
            table_name="users",
            format="csv",
            method="metadata"
        )
        assert metadata_result.confidence >= 0.8

        # sample 方法 - 中等置信度
        sample_result = await export_service.estimate_file_size(
            table_name="users",
            format="csv",
            method="sample"
        )
        assert 0.3 <= sample_result.confidence <= 0.8

        # actual 方法 - 最高置信度
        actual_result = await export_service.estimate_file_size(
            table_name="users",
            format="csv",
            method="actual"
        )
        assert actual_result.confidence == 1.0

    async def test_estimate_size_byte_calculation(self, export_service, sample_data):
        """测试字节数计算准确性"""
        # Mock 数据获取
        export_service.db_connection.execute_query.return_value = sample_data

        # Mock CSV 生成
        csv_lines = [
            "id,name,email,age,salary,created_at,is_active\n",
            "1,张三,zhangsan@example.com,25,10000.50,2023-01-01 10:00:00,True\n",
            "2,李四,lisi@example.com,30,15000.75,2023-01-02 10:00:00,False\n"
        ]

        with patch.object(export_service, '_generate_csv_row') as mock_generate:
            mock_generate.side_effect = csv_lines

            result = await export_service.estimate_file_size(
                table_name="users",
                format="csv",
                method="actual"
            )

            # 计算预期字节数
            expected_bytes = sum(len(line.encode('utf-8-sig')) for line in csv_lines)

            # 验证估算值接近实际值
            assert abs(result.estimated_bytes - expected_bytes) / expected_bytes < 0.1

    async def test_estimate_size_error_handling(self, export_service):
        """测试错误处理"""
        # Mock 数据库连接错误
        export_service.db_connection.execute_query.side_effect = Exception("Database error")

        # 测试 sample/actual 方法处理错误
        with pytest.raises(Exception):
            await export_service.estimate_file_size(
                table_name="users",
                format="csv",
                method="sample"
            )

        # metadata 方法不应该因为数据库错误而失败
        export_service.db_connection.extract_metadata.return_value = {}
        result = await export_service.estimate_file_size(
            table_name="users",
            format="csv",
            method="metadata"
        )
        assert result.method == "metadata"
        assert result.estimated_bytes > 0

    async def test_estimate_size_bytes_per_row_calculation(self, export_service, sample_data):
        """测试每行字节数计算"""
        # Mock 数据获取
        export_service.db_connection.execute_query.return_value = sample_data

        with patch.object(export_service, '_generate_csv_row') as mock_generate:
            # 生成不同长度的行
            mock_generate.side_effect = [
                "short\n",
                "this is a much longer line with more text data\n"
            ]

            result = await export_service.estimate_file_size(
                table_name="users",
                format="csv",
                method="actual"
            )

            assert result.bytes_per_row > 0
            assert len(result.bytes_per_row) == len(sample_data)
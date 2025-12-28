"""
CSV 格式转换单元测试
验证特殊字符、中文、换行符的正确转义
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.export import ExportService


class TestExportCSV:
    """CSV 导出格式转换测试类"""

    @pytest.fixture
    def export_service(self):
        """创建 ExportService 实例"""
        with patch('app.services.export.TaskManager'):
            with patch('app.services.export.ExportService'):
                return ExportService(
                    db_connection=MagicMock(),
                    task_manager=MagicMock()
                )

    @pytest.fixture
    def sample_row(self):
        """创建测试行数据"""
        return {
            "id": 1,
            "name": "张三",
            "email": "test@example.com",
            "description": "这是一段包含\"特殊字符\"的描述\n包含换行符",
            "price": Decimal("999.99"),
            "created_at": datetime(2023, 1, 1, 10, 30, 45),
            "is_active": True,
            "tags": ["tag1", "tag2", "tag3"]
        }

    def test_generate_csv_row_with_special_characters(self, export_service, sample_row):
        """测试包含特殊字符的 CSV 行生成"""
        row = sample_row.copy()

        # 添加更多特殊字符
        row["name"] = "测试,包含,逗号\"和\"引号\n还有换行符"
        row["description"] = "包含\t制表符\r\n回车换行和\"双引号\""

        csv_row = export_service._generate_csv_row(row, ["id", "name", "description"])

        # 验证 CSV 行格式正确
        assert csv_row.startswith("1,")
        assert '"测试,包含,逗号\"和\"引号\n还有换行符"' in csv_row
        assert '"包含\t制表符\r\n回车换行和\"双引号\""' in csv_row
        assert csv_row.endswith("\n")

    def test_generate_csv_row_with_chinese_characters(self, export_service, sample_row):
        """测试中文字符的 CSV 行生成"""
        csv_row = export_service._generate_csv_row(sample_row, ["name", "description"])

        # 验证中文字符正确编码
        assert "张三" in csv_row
        assert "这是一段包含\"特殊字符\"的描述\n包含换行符" in csv_row
        # 特殊字符应该被正确转义
        assert '"这是一段包含\"特殊字符\"的描述\n包含换行符"' in csv_row

    def test_generate_csv_row_with_numbers(self, export_service, sample_row):
        """测试数字类型的 CSV 行生成"""
        row = {
            "id": 1,
            "price": Decimal("1234.56"),
            "quantity": 100,
            "discount": 0.15
        }

        csv_row = export_service._generate_csv_row(row, ["id", "price", "quantity", "discount"])

        # 验证数字格式正确
        assert csv_row == "1,1234.56,100,0.15\n"

    def test_generate_csv_row_with_boolean(self, export_service, sample_row):
        """测试布尔值的 CSV 行生成"""
        row = {
            "is_active": True,
            "has_discount": False,
            "is_verified": True
        }

        csv_row = export_service._generate_csv_row(row, ["is_active", "has_discount", "is_verified"])

        # 验证布尔值转换为字符串
        assert "True,False,True\n" in csv_row

    def test_generate_csv_row_with_datetime(self, export_service, sample_row):
        """测试日期时间的 CSV 行生成"""
        row = {
            "created_at": datetime(2023, 12, 25, 15, 30, 45)
        }

        csv_row = export_service._generate_csv_row(row, ["created_at"])

        # 验证日期时间格式
        assert "2023-12-25 15:30:45" in csv_row

    def test_generate_csv_row_with_none_values(self, export_service):
        """测试空值的 CSV 行生成"""
        row = {
            "id": 1,
            "name": "test",
            "email": None,
            "phone": ""
        }

        csv_row = export_service._generate_csv_row(row, ["id", "name", "email", "phone"])

        # 验证空值处理
        assert "1,test,\n" in csv_row  # None 应该转为空字符串
        # 空字符串应该保留为空

    def test_generate_csv_row_with_comma_in_values(self, export_service):
        """测试值中包含逗号的情况"""
        row = {
            "id": 1,
            "name": "Doe, John",
            "address": "123 Main St, Apt 4",
            "description": "List: item1, item2, item3"
        }

        csv_row = export_service._generate_csv_row(row, ["id", "name", "address", "description"])

        # 验证逗号被正确转义
        parts = csv_row.split(',')
        assert len(parts) == 4  # 逗号分隔符不应该被计算在内
        assert '"Doe, John"' in csv_row
        assert '"123 Main St, Apt 4"' in csv_row
        assert '"List: item1, item2, item3"' in csv_row

    def test_generate_csv_row_with_quotes_in_values(self, export_service):
        """测试值中包含引号的情况"""
        row = {
            "id": 1,
            "quote": 'He said: "Hello World"',
            "nested": 'Quote inside: "Inner quote \'single\' quote"'
        }

        csv_row = export_service._generate_csv_row(row, ["id", "quote", "nested"])

        # 验证引号被正确转义
        assert '"He said: ""Hello World"""' in csv_row
        assert '"Quote inside: ""Inner quote \'single\' quote"""' in csv_row

    def test_generate_csv_row_with_newlines_in_values(self, export_service):
        """测试值中包含换行符的情况"""
        row = {
            "id": 1,
            "multiline": "Line 1\nLine 2\nLine 3",
            "paragraph": "Paragraph 1\r\nParagraph 2\r\nParagraph 3"
        }

        csv_row = export_service._generate_csv_row(row, ["id", "multiline", "paragraph"])

        # 验证换行符被正确转义
        assert '"Line 1\nLine 2\nLine 3"' in csv_row
        assert '"Paragraph 1\r\nParagraph 2\r\nParagraph 3"' in csv_row

    def test_generate_csv_header_row(self, export_service):
        """测试 CSV 头部行生成"""
        columns = ["id", "name", "email", "created_at"]
        header = export_service._generate_csv_row(columns, columns)

        # 验证头部行格式
        assert header == "id,name,email,created_at\n"

    def test_generate_csv_empty_row(self, export_service):
        """测试空行生成"""
        empty_row = {}
        csv_row = export_service._generate_csv_row(empty_row, [])

        # 验证空行处理
        assert csv_row == "\n"

    def test_generate_csv_unicode_characters(self, export_service):
        """测试 Unicode 字符（emoji、特殊符号）"""
        row = {
            "id": 1,
            "emoji": "Hello 🌍 World 🎉",
            "symbols": "©®™€£¥¢",
            "mixed": "中文English混合🌟"
        }

        csv_row = export_service._generate_csv_row(row, ["id", "emoji", "symbols", "mixed"])

        # 验证 Unicode 字符正确处理
        assert "Hello 🌍 World 🎉" in csv_row
        assert "©®™€£¥¢" in csv_row
        assert "中文English混合🌟" in csv_row

    def test_generate_csv_field_ordering(self, export_service, sample_row):
        """测试字段顺序正确性"""
        # 定义字段顺序
        field_order = ["created_at", "name", "email", "id"]

        csv_row = export_service._generate_csv_row(sample_row, field_order)

        # 验证字段顺序
        row_parts = csv_row.strip().split(',')
        assert "2023-01-01 10:30:45" in row_parts[0]  # created_at
        assert "张三" in row_parts[1]  # name
        assert "test@example.com" in row_parts[2]  # email
        assert "1" in row_parts[3]  # id
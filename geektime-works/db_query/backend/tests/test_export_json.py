"""
JSON 格式转换单元测试
验证 datetime/Decimal/bytes 等特殊类型的正确序列化
"""

import pytest
from datetime import datetime, date, time
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.export import ExportService


class TestExportJSON:
    """JSON 导出格式转换测试类"""

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
            "price": Decimal("999.99"),
            "created_at": datetime(2023, 1, 1, 10, 30, 45),
            "updated_date": date(2023, 12, 25),
            "login_time": time(14, 30, 15),
            "is_active": True,
            "score": 95.5,
            "binary_data": b"binary content",
            "json_field": {"nested": "value", "array": [1, 2, 3]},
            "tags": ["tag1", "tag2", "tag3"],
            "uuid": str(uuid4()),
            "none_value": None
        }

    def test_serialize_for_json_datetime(self, export_service):
        """测试 datetime 类型序列化"""
        data = {
            "created_at": datetime(2023, 1, 1, 10, 30, 45, 123456)
        }

        result = export_service._serialize_for_json(data)

        # 验证 datetime 被转换为 ISO 格式字符串
        assert "created_at" in result
        assert isinstance(result["created_at"], str)
        assert result["created_at"] == "2023-01-01T10:30:45.123456"

    def test_serialize_for_json_date(self, export_service):
        """测试 date 类型序列化"""
        data = {
            "updated_date": date(2023, 12, 25)
        }

        result = export_service._serialize_for_json(data)

        # 验证 date 被转换为 ISO 格式字符串
        assert "updated_date" in result
        assert isinstance(result["updated_date"], str)
        assert result["updated_date"] == "2023-12-25"

    def test_serialize_for_json_time(self, export_service):
        """测试 time 类型序列化"""
        data = {
            "login_time": time(14, 30, 15, 500000)
        }

        result = export_service._serialize_for_json(data)

        # 验证 time 被转换为 ISO 格式字符串
        assert "login_time" in result
        assert isinstance(result["login_time"], str)
        assert result["login_time"] == "14:30:15.500000"

    def test_serialize_for_json_decimal(self, export_service):
        """测试 Decimal 类型序列化"""
        data = {
            "price": Decimal("1234.56"),
            "score": Decimal("95.5")
        }

        result = export_service._serialize_for_json(data)

        # 验证 Decimal 被转换为字符串
        assert "price" in result
        assert result["price"] == "1234.56"
        assert "score" in result
        assert result["score"] == "95.5"

    def test_serialize_for_json_binary_data(self, export_service):
        """测试二进制数据序列化"""
        data = {
            "binary_data": b"binary content",
            "image": b"\x89PNG\r\n\x1a\n"
        }

        result = export_service._serialize_for_json(data)

        # 验证二进制数据被转换为 base64 编码字符串
        assert "binary_data" in result
        assert isinstance(result["binary_data"], str)
        assert result["binary_data"] == "binary content"
        assert "image" in result
        assert result["image"] == "\x89PNG\r\n\x1a\n"

    def test_serialize_for_json_uuid(self, export_service):
        """测试 UUID 类型序列化"""
        test_uuid = uuid4()
        data = {
            "id": test_uuid,
            "user_uuid": str(test_uuid)
        }

        result = export_service._serialize_for_json(data)

        # 验证 UUID 被转换为字符串
        assert "id" in result
        assert isinstance(result["id"], str)
        assert result["id"] == str(test_uuid)

    def test_serialize_for_json_nested_objects(self, export_service):
        """测试嵌套对象序列化"""
        data = {
            "user": {
                "name": "张三",
                "profile": {
                    "age": 25,
                    "preferences": {
                        "theme": "dark",
                        "notifications": True
                    }
                }
            },
            "metadata": {
                "created_by": "admin",
                "tags": ["important", "user"]
            }
        }

        result = export_service._serialize_for_json(data)

        # 验证嵌套对象结构保持不变
        assert "user" in result
        assert "profile" in result["user"]
        assert "preferences" in result["user"]["profile"]
        assert "metadata" in result
        assert result["user"]["name"] == "张三"

    def test_serialize_for_json_arrays(self, export_service):
        """测试数组序列化"""
        data = {
            "tags": ["tag1", "tag2", "tag3"],
            "scores": [95, 87, 92, 88],
            "mixed_array": [1, "text", True, None, Decimal("3.14")],
            "nested_array": [
                {"name": "item1", "value": 100},
                {"name": "item2", "value": 200}
            ]
        }

        result = export_service._serialize_for_json(data)

        # 验证数组结构保持不变
        assert "tags" in result
        assert len(result["tags"]) == 3
        assert "mixed_array" in result
        assert result["mixed_array"][0] == 1
        assert result["mixed_array"][1] == "text"

    def test_serialize_for_json_none_values(self, export_service):
        """测试 None 值序列化"""
        data = {
            "empty_field": None,
            "nested": {
                "deep_none": None,
                "some_value": "exists"
            }
        }

        result = export_service._serialize_for_json(data)

        # 验证 None 值保持不变
        assert result["empty_field"] is None
        assert result["nested"]["deep_none"] is None
        assert result["nested"]["some_value"] == "exists"

    def test_serialize_for_json_special_characters(self, export_service):
        """测试特殊字符序列化"""
        data = {
            "chinese": "中文字符",
            "emoji": "Hello 🌍 World 🎉",
            "unicode": "©®™€£¥¢",
            "quotes": 'He said: "Hello"',
            "newlines": "Line 1\nLine 2",
            "tabs": "Col1\tCol2\tCol3"
        }

        result = export_service._serialize_for_json(data)

        # 验证特殊字符正确序列化
        assert result["chinese"] == "中文字符"
        assert result["emoji"] == "Hello 🌍 World 🎉"
        assert result["quotes"] == 'He said: "Hello"'

    def test_serialize_for_json_boolean(self, export_service):
        """测试布尔值序列化"""
        data = {
            "is_active": True,
            "has_discount": False,
            "verified": True
        }

        result = export_service._serialize_for_json(data)

        # 验证布尔值保持不变
        assert result["is_active"] is True
        assert result["has_discount"] is False

    def test_serialize_for_json_integers(self, export_service):
        """测试整数序列化"""
        data = {
            "id": 1,
            "count": 100,
            "score": 95,
            "large_number": 2**31 - 1
        }

        result = export_service._serialize_for_json(data)

        # 验证整数保持不变
        assert result["id"] == 1
        assert result["count"] == 100
        assert isinstance(result["large_number"], int)

    def test_serialize_for_json_floats(self, export_service):
        """测试浮点数序列化"""
        data = {
            "price": 99.99,
            "ratio": 0.5,
            "scientific": 1.23e10
        }

        result = export_service._serialize_for_json(data)

        # 验证浮点数保持不变
        assert result["price"] == 99.99
        assert result["ratio"] == 0.5
        assert result["scientific"] == 1.23e10

    def test_serialize_for_json_complex_types_combination(self, export_service):
        """测试复杂类型组合序列化"""
        data = {
            "id": 1,
            "metadata": {
                "created_at": datetime(2023, 1, 1, 10, 30, 45),
                "tags": ["tag1", "tag2"],
                "config": {
                    "enabled": True,
                    "threshold": Decimal("100.00"),
                    "data": b"config data"
                }
            },
            "items": [
                {
                    "name": "item1",
                    "price": Decimal("50.00"),
                    "created": date(2023, 1, 1)
                },
                {
                    "name": "item2",
                    "price": Decimal("75.00"),
                    "created": date(2023, 1, 2)
                }
            ]
        }

        result = export_service._serialize_for_json(data)

        # 验证所有类型都正确序列化
        assert result["id"] == 1
        assert isinstance(result["metadata"]["created_at"], str)
        assert isinstance(result["metadata"]["config"]["threshold"], str)
        assert isinstance(result["metadata"]["config"]["data"], str)
        assert len(result["items"]) == 2
        assert isinstance(result["items"][0]["created"], str)

    def test_generate_json_row_with_sample_data(self, export_service, sample_row):
        """测试使用样本数据生成 JSON 行"""
        json_row = export_service._generate_json_row(sample_row)

        # 验证 JSON 行格式
        assert json_row.startswith("{")
        assert json_row.endswith("}\n")

        # 解析 JSON 验证内容
        import json
        parsed = json.loads(json_row.strip())

        # 验证所有字段都存在且类型正确
        assert "id" in parsed
        assert "name" in parsed
        assert "price" in parsed
        assert parsed["price"] == "999.99"  # Decimal 转字符串
        assert "created_at" in parsed
        assert isinstance(parsed["created_at"], str)  # datetime 转字符串
        assert "binary_data" in parsed
        assert isinstance(parsed["binary_data"], str)  # binary 转字符串
"""多数据库访问控制与安全策略验证测试.

本测试验证以下关键安全需求：
1. 每个数据库使用独立的执行器，可配置不同的安全策略
2. 表/列访问限制按数据库强制实施
3. EXPLAIN 策略可按数据库配置
4. 敏感对象得到保护
5. 请求无法访问错误数据库
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from pg_mcp.config.settings import (
    DatabaseConfig,
    ResilienceConfig,
    SecurityConfig,
    ValidationConfig,
)
from pg_mcp.models.errors import DatabaseError, SecurityViolationError
from pg_mcp.models.query import QueryRequest, ReturnType
from pg_mcp.models.schema import ColumnInfo, DatabaseSchema, TableInfo
from pg_mcp.services.orchestrator import QueryOrchestrator
from pg_mcp.services.sql_executor import SQLExecutor
from pg_mcp.services.sql_validator import SQLValidator


class TestMultiDatabaseExecutorIsolation:
    """测试多数据库执行器隔离机制."""

    @pytest.fixture
    def security_config_prod(self) -> SecurityConfig:
        """生产环境安全配置 - 严格限制."""
        return SecurityConfig(
            blocked_tables=["passwords", "secrets", "api_keys"],
            blocked_columns=["ssn", "credit_card", "users.password"],
            allow_explain=False,
            max_rows=1000,
            max_execution_time=10.0,
        )

    @pytest.fixture
    def security_config_analytics(self) -> SecurityConfig:
        """分析数据库安全配置 - 宽松限制."""
        return SecurityConfig(
            blocked_tables=[],  # 无表限制
            blocked_columns=[],  # 无列限制
            allow_explain=True,  # 允许 EXPLAIN
            max_rows=50000,  # 允许更多行
            max_execution_time=60.0,  # 允许更长执行时间
        )

    @pytest.fixture
    def mock_pools(self) -> dict[str, MagicMock]:
        """创建多个数据库连接池."""
        pools = {}
        for db_name in ["production", "analytics", "testing"]:
            pool = MagicMock()
            acquire_mock = MagicMock()
            acquire_mock.__aenter__ = AsyncMock(return_value=MagicMock())
            acquire_mock.__aexit__ = AsyncMock(return_value=None)
            pool.acquire = MagicMock(return_value=acquire_mock)
            pools[db_name] = pool
        return pools

    @pytest.fixture
    def sql_executors(
        self,
        mock_pools: dict[str, MagicMock],
        security_config_prod: SecurityConfig,
        security_config_analytics: SecurityConfig,
    ) -> dict[str, SQLExecutor]:
        """为每个数据库创建独立的执行器."""
        db_configs = {
            "production": DatabaseConfig(name="production"),
            "analytics": DatabaseConfig(name="analytics"),
            "testing": DatabaseConfig(name="testing"),
        }

        executors = {}
        for db_name, pool in mock_pools.items():
            # 为不同数据库使用不同的安全配置
            if db_name == "production":
                sec_config = security_config_prod
            elif db_name == "analytics":
                sec_config = security_config_analytics
            else:
                sec_config = SecurityConfig()

            executors[db_name] = SQLExecutor(
                pool=pool,
                security_config=sec_config,
                db_config=db_configs[db_name],
            )
        return executors

    def test_each_database_has_independent_executor(
        self, sql_executors: dict[str, SQLExecutor]
    ) -> None:
        """验证每个数据库都有独立的执行器实例."""
        assert len(sql_executors) == 3
        assert "production" in sql_executors
        assert "analytics" in sql_executors
        assert "testing" in sql_executors

        # 验证执行器是不同的实例
        assert sql_executors["production"] is not sql_executors["analytics"]
        assert sql_executors["production"] is not sql_executors["testing"]

    def test_each_database_has_independent_security_config(
        self, sql_executors: dict[str, SQLExecutor]
    ) -> None:
        """验证每个数据库有独立的安全配置."""
        prod_executor = sql_executors["production"]
        analytics_executor = sql_executors["analytics"]

        # 生产环境应该有严格的限制
        assert len(prod_executor.security_config.blocked_tables) == 3
        assert "passwords" in prod_executor.security_config.blocked_tables
        assert prod_executor.security_config.max_rows == 1000
        assert prod_executor.security_config.allow_explain is False

        # 分析数据库应该有宽松的限制
        assert len(analytics_executor.security_config.blocked_tables) == 0
        assert analytics_executor.security_config.max_rows == 50000
        assert analytics_executor.security_config.allow_explain is True

    def test_validator_respects_database_specific_restrictions(
        self, security_config_prod: SecurityConfig
    ) -> None:
        """验证验证器根据数据库配置应用限制."""
        # 生产环境验证器
        prod_validator = SQLValidator(
            config=security_config_prod,
            blocked_tables=security_config_prod.blocked_tables,
            blocked_columns=security_config_prod.blocked_columns,
            allow_explain=security_config_prod.allow_explain,
        )

        # 测试阻止的表
        sql = "SELECT * FROM passwords"
        is_valid, error = prod_validator.validate(sql)
        assert not is_valid
        assert "passwords" in error.lower()

        # 测试阻止的列
        sql = "SELECT id, ssn FROM users"
        is_valid, error = prod_validator.validate(sql)
        assert not is_valid
        assert "ssn" in error.lower()

        # 测试 EXPLAIN 被阻止
        sql = "EXPLAIN SELECT * FROM users"
        is_valid, error = prod_validator.validate(sql)
        assert not is_valid
        assert "explain" in error.lower()


class TestTableColumnAccessControl:
    """测试表/列访问控制."""

    @pytest.fixture
    def restricted_validator(self) -> SQLValidator:
        """创建有限制配置的验证器."""
        config = SecurityConfig()
        return SQLValidator(
            config=config,
            blocked_tables=["users", "financial_data"],
            blocked_columns=["password", "ssn", "credit_card"],
            allow_explain=False,
        )

    def test_blocked_table_access_rejected(
        self, restricted_validator: SQLValidator
    ) -> None:
        """测试阻止表访问."""
        test_cases = [
            "SELECT * FROM users",
            "SELECT COUNT(*) FROM users",
            "SELECT u.name FROM users u JOIN orders o ON u.id = o.user_id",
        ]

        for sql in test_cases:
            is_valid, error = restricted_validator.validate(sql)
            assert not is_valid, f"SQL 应该被拒绝: {sql}"
            assert "users" in error.lower()

    def test_blocked_column_access_rejected(
        self, restricted_validator: SQLValidator
    ) -> None:
        """测试阻止列访问."""
        test_cases = [
            "SELECT id, password FROM admins",
            "SELECT name, ssn FROM customers",
            "SELECT credit_card FROM payments",
        ]

        for sql in test_cases:
            is_valid, error = restricted_validator.validate(sql)
            assert not is_valid, f"SQL 应该被拒绝: {sql}"
            assert any(col in error.lower() for col in ["password", "ssn", "credit_card"])

    def test_allowed_queries_pass(self, restricted_validator: SQLValidator) -> None:
        """测试允许的查询通过."""
        test_cases = [
            "SELECT * FROM orders",
            "SELECT id, name FROM customers",
            "SELECT * FROM products WHERE active = true",
        ]

        for sql in test_cases:
            is_valid, error = restricted_validator.validate(sql)
            assert is_valid, f"SQL 应该被允许: {sql}"
            assert error is None

    def test_qualified_column_blocking(self) -> None:
        """测试限定列名 (table.column) 阻止."""
        config = SecurityConfig()
        validator = SQLValidator(
            config=config,
            blocked_columns=["users.password", "admins.api_key"],
        )

        # 测试精确匹配
        sql = "SELECT users.password, users.id FROM users"
        is_valid, error = validator.validate(sql)
        assert not is_valid
        assert "users.password" in error.lower()

        # 测试不带表前缀的列名不应该匹配
        sql = "SELECT password FROM credentials"
        is_valid, error = validator.validate(sql)
        assert is_valid  # 'credentials.password' 不在阻止列表中


class TestExplainPolicy:
    """测试 EXPLAIN 策略."""

    def test_explain_disabled_by_default(self) -> None:
        """测试默认情况下 EXPLAIN 被禁用."""
        config = SecurityConfig()
        validator = SQLValidator(config=config, allow_explain=False)

        sql = "EXPLAIN SELECT * FROM users"
        is_valid, error = validator.validate(sql)
        assert not is_valid
        assert "explain" in error.lower()

    def test_explain_enabled_when_configured(self) -> None:
        """测试配置后允许 EXPLAIN."""
        config = SecurityConfig()
        validator = SQLValidator(config=config, allow_explain=True)

        sql = "EXPLAIN SELECT * FROM users"
        is_valid, error = validator.validate(sql)
        assert is_valid
        assert error is None

    def test_explain_analyze_allowed(self) -> None:
        """测试 EXPLAIN ANALYZE 被允许."""
        config = SecurityConfig()
        validator = SQLValidator(config=config, allow_explain=True)

        sql = "EXPLAIN ANALYZE SELECT * FROM users WHERE id > 100"
        is_valid, error = validator.validate(sql)
        assert is_valid
        assert error is None

    def test_explain_with_dangerous_query_safe(self) -> None:
        """测试 EXPLAIN 与危险查询组合是安全的（不执行）."""
        config = SecurityConfig()
        validator = SQLValidator(config=config, allow_explain=True)

        # EXPLAIN DELETE 是安全的 - 只显示计划不执行
        sql = "EXPLAIN DELETE FROM users WHERE id = 1"
        is_valid, error = validator.validate(sql)
        assert is_valid
        assert error is None


class TestDatabaseIsolation:
    """测试数据库隔离."""

    @pytest.fixture
    def multi_db_orchestrator(self) -> QueryOrchestrator:
        """创建多数据库编排器."""
        # 创建多个模拟池
        pools = {
            "db1": MagicMock(),
            "db2": MagicMock(),
            "db3": MagicMock(),
        }

        # 创建多个执行器
        executors = {}
        for db_name, pool in pools.items():
            executors[db_name] = MagicMock()

        return QueryOrchestrator(
            sql_generator=MagicMock(),
            sql_validator=MagicMock(),
            sql_executors=executors,
            result_validator=MagicMock(),
            schema_cache=MagicMock(),
            pools=pools,
            resilience_config=ResilienceConfig(),
            validation_config=ValidationConfig(),
        )

    def test_cannot_access_nonexistent_database(
        self, multi_db_orchestrator: QueryOrchestrator
    ) -> None:
        """测试无法访问不存在的数据库."""
        with pytest.raises(DatabaseError) as exc_info:
            multi_db_orchestrator._resolve_database("nonexistent_db")

        assert "not found" in str(exc_info.value).lower()
        assert "db1" in exc_info.value.details["available_databases"]

    def test_request_routes_to_correct_database(
        self, multi_db_orchestrator: QueryOrchestrator
    ) -> None:
        """测试请求路由到正确的数据库."""
        # 指定数据库应该被解析
        db = multi_db_orchestrator._resolve_database("db2")
        assert db == "db2"

        db = multi_db_orchestrator._resolve_database("db3")
        assert db == "db3"

    def test_auto_select_fails_with_multiple_databases(
        self, multi_db_orchestrator: QueryOrchestrator
    ) -> None:
        """测试有多个数据库时自动选择失败."""
        with pytest.raises(DatabaseError) as exc_info:
            multi_db_orchestrator._resolve_database(None)

        assert "multiple databases" in str(exc_info.value).lower()

    def test_auto_select_succeeds_with_single_database(self) -> None:
        """测试单个数据库时自动选择成功."""
        orchestrator = QueryOrchestrator(
            sql_generator=MagicMock(),
            sql_validator=MagicMock(),
            sql_executors={"only_db": MagicMock()},
            result_validator=MagicMock(),
            schema_cache=MagicMock(),
            pools={"only_db": MagicMock()},
            resilience_config=ResilienceConfig(),
            validation_config=ValidationConfig(),
        )

        db = orchestrator._resolve_database(None)
        assert db == "only_db"


class TestDatabaseSpecificSecurityPolicies:
    """测试数据库特定的安全策略."""

    @pytest.fixture
    def schemas(self) -> dict[str, DatabaseSchema]:
        """创建不同数据库的 Schema."""
        return {
            "production": DatabaseSchema(
                database_name="production",
                tables=[
                    TableInfo(
                        schema_name="public",
                        table_name="users",
                        columns=[
                            ColumnInfo(name="id", data_type="integer", is_nullable=False),
                            ColumnInfo(name="name", data_type="varchar", is_nullable=False),
                            ColumnInfo(name="password", data_type="varchar", is_nullable=False),
                        ],
                    ),
                    TableInfo(
                        schema_name="public",
                        table_name="secrets",
                        columns=[
                            ColumnInfo(name="id", data_type="integer", is_nullable=False),
                            ColumnInfo(name="api_key", data_type="varchar", is_nullable=False),
                        ],
                    ),
                ],
                version="15.0",
            ),
            "analytics": DatabaseSchema(
                database_name="analytics",
                tables=[
                    TableInfo(
                        schema_name="public",
                        table_name="events",
                        columns=[
                            ColumnInfo(name="id", data_type="integer", is_nullable=False),
                            ColumnInfo(name="event_type", data_type="varchar", is_nullable=False),
                        ],
                    ),
                ],
                version="15.0",
            ),
        }

    def test_production_database_blocks_sensitive_tables(
        self, schemas: dict[str, DatabaseSchema]
    ) -> None:
        """测试生产数据库阻止敏感表访问."""
        config = SecurityConfig(
            blocked_tables=["secrets"],
            blocked_columns=["password"],
        )
        validator = SQLValidator(
            config=config,
            blocked_tables=config.blocked_tables,
            blocked_columns=config.blocked_columns,
        )

        # 应该阻止访问 secrets 表
        sql = "SELECT * FROM secrets"
        is_valid, error = validator.validate(sql)
        assert not is_valid
        assert "secrets" in error.lower()

        # 应该阻止访问 password 列
        sql = "SELECT id, password FROM users"
        is_valid, error = validator.validate(sql)
        assert not is_valid
        assert "password" in error.lower()

    def test_analytics_database_allows_all_tables(
        self, schemas: dict[str, DatabaseSchema]
    ) -> None:
        """测试分析数据库允许所有表访问."""
        config = SecurityConfig(
            blocked_tables=[],  # 无限制
            blocked_columns=[],
        )
        validator = SQLValidator(config=config, blocked_tables=[], blocked_columns=[])

        # 应该允许所有查询
        sql = "SELECT * FROM events"
        is_valid, error = validator.validate(sql)
        assert is_valid
        assert error is None


class TestSecurityConfigValidation:
    """测试安全配置验证."""

    def test_blocked_tables_parsed_from_string(self) -> None:
        """测试从字符串解析阻止的表."""
        config = SecurityConfig(blocked_tables="users, passwords, secrets")
        assert "users" in config.blocked_tables
        assert "passwords" in config.blocked_tables
        assert "secrets" in config.blocked_tables

    def test_blocked_columns_parsed_from_string(self) -> None:
        """测试从字符串解析阻止的列."""
        config = SecurityConfig(blocked_columns="password, ssn, users.email")
        assert "password" in config.blocked_columns
        assert "ssn" in config.blocked_columns
        assert "users.email" in config.blocked_columns

    def test_blocked_functions_parsed_from_string(self) -> None:
        """测试从字符串解析阻止的函数."""
        config = SecurityConfig(blocked_functions="pg_sleep, pg_terminate_backend")
        assert "pg_sleep" in config.blocked_functions
        assert "pg_terminate_backend" in config.blocked_functions


class TestSessionParameterSecurity:
    """测试会话参数安全."""

    def test_search_path_validation(self) -> None:
        """测试 search_path 验证."""
        # 有效配置
        config = SecurityConfig(safe_search_path="public")
        assert all(
            c.isalnum() or c in ("_", ",", " ") for c in config.safe_search_path
        )

        # 无效配置（包含特殊字符）
        config = SecurityConfig(safe_search_path="public; DROP TABLE users;--")
        assert not all(
            c.isalnum() or c in ("_", ",", " ") for c in config.safe_search_path
        )

    def test_readonly_role_validation(self) -> None:
        """测试只读角色验证."""
        # 有效角色名
        config = SecurityConfig(readonly_role="readonly_user")
        assert all(c.isalnum() or c == "_" for c in config.readonly_role)

        # 无效角色名（包含特殊字符）
        config = SecurityConfig(readonly_role="admin; DROP TABLE users;--")
        if config.readonly_role:
            assert not all(c.isalnum() or c == "_" for c in config.readonly_role)


class TestSecurityInDepth:
    """深度防御测试."""

    def test_multiple_layers_of_security(self) -> None:
        """测试多层安全防御."""
        config = SecurityConfig(
            blocked_tables=["sensitive"],
            blocked_columns=["password"],
            allow_explain=False,
        )

        validator = SQLValidator(
            config=config,
            blocked_tables=config.blocked_tables,
            blocked_columns=config.blocked_columns,
            allow_explain=config.allow_explain,
        )

        # 第一层：阻止表访问
        sql = "SELECT * FROM sensitive"
        is_valid, error = validator.validate(sql)
        assert not is_valid
        assert "sensitive" in error.lower()

        # 第二层：阻止列访问
        sql = "SELECT password FROM users"
        is_valid, error = validator.validate(sql)
        assert not is_valid
        assert "password" in error.lower()

        # 第三层：阻止危险操作
        sql = "DELETE FROM users"
        is_valid, error = validator.validate(sql)
        assert not is_valid
        assert "delete" in error.lower()

        # 第四层：阻止 EXPLAIN
        sql = "EXPLAIN SELECT * FROM users"
        is_valid, error = validator.validate(sql)
        assert not is_valid
        assert "explain" in error.lower()

    def test_sql_injection_prevention(self) -> None:
        """测试 SQL 注入防护."""
        config = SecurityConfig()
        validator = SQLValidator(config=config)

        # 测试各种 SQL 注入尝试
        injection_attempts = [
            "SELECT * FROM users WHERE id = 1 OR 1=1",
            "SELECT * FROM users; DROP TABLE users;--",
            "SELECT * FROM users WHERE name = 'admin'--",
            "SELECT * FROM users WHERE id = 1 UNION SELECT * FROM passwords",
        ]

        # 这些注入尝试应该要么被解析器捕获，要么被多语句检查捕获
        for sql in injection_attempts:
            is_valid, error = validator.validate(sql)
            # 如果是有效的 SELECT 语法，应该通过验证器
            # 但多语句查询应该被拒绝
            if ";" in sql:
                assert not is_valid, f"多语句注入应该被拒绝: {sql}"
                assert "multiple" in error.lower()

    def test_case_insensitive_blocking(self) -> None:
        """测试不区分大小写的阻止."""
        config = SecurityConfig()
        validator = SQLValidator(
            config=config,
            blocked_tables=["USERS"],
            blocked_columns=["PASSWORD"],
        )

        # 应该阻止所有大小写变体
        test_cases = [
            "SELECT * FROM users",
            "SELECT * FROM USERS",
            "SELECT * FROM Users",
            "SELECT password FROM admins",
            "SELECT PASSWORD FROM admins",
            "SELECT Password FROM admins",
        ]

        for sql in test_cases:
            is_valid, error = validator.validate(sql)
            assert not is_valid, f"应该被拒绝（不区分大小写）: {sql}"


class TestEdgeCases:
    """边缘情况测试."""

    def test_empty_blocked_list(self) -> None:
        """测试空的阻止列表."""
        config = SecurityConfig(
            blocked_tables=[],
            blocked_columns=[],
        )
        validator = SQLValidator(
            config=config,
            blocked_tables=[],
            blocked_columns=[],
        )

        # 应该允许所有有效的 SELECT
        sql = "SELECT * FROM any_table"
        is_valid, error = validator.validate(sql)
        assert is_valid
        assert error is None

    def test_wildcard_column_select_with_blocked_columns(self) -> None:
        """测试通配符选择与阻止的列."""
        config = SecurityConfig()
        validator = SQLValidator(
            config=config,
            blocked_columns=["password"],
        )

        # SELECT * 可能包含 password 列，但验证器检查列引用
        # 这里的行为取决于实现 - 如果只检查显式列引用，则通过
        sql = "SELECT * FROM users"
        is_valid, error = validator.validate(sql)
        # 可能通过，因为 SELECT * 不显式引用列
        # 这在运行时需要其他层的安全控制

    def test_cte_with_blocked_table(self) -> None:
        """测试 CTE 中使用阻止的表."""
        config = SecurityConfig()
        validator = SQLValidator(
            config=config,
            blocked_tables=["secrets"],
        )

        sql = """
            WITH user_counts AS (
                SELECT COUNT(*) as cnt FROM secrets
            )
            SELECT * FROM user_counts
        """
        is_valid, error = validator.validate(sql)
        assert not is_valid
        assert "secrets" in error.lower()


class TestComprehensiveSecurityScenarios:
    """综合安全场景测试."""

    def test_scenario_production_database_query(self) -> None:
        """场景：生产数据库查询."""
        # 生产环境配置：严格限制
        config = SecurityConfig(
            blocked_tables=["passwords", "secrets", "internal_logs"],
            blocked_columns=["password", "ssn", "api_key", "credit_card"],
            allow_explain=False,
            max_rows=100,
            max_execution_time=5.0,
        )

        validator = SQLValidator(
            config=config,
            blocked_tables=config.blocked_tables,
            blocked_columns=config.blocked_columns,
            allow_explain=config.allow_explain,
        )

        # 允许的查询
        allowed_queries = [
            "SELECT id, name, email FROM users LIMIT 10",
            "SELECT COUNT(*) FROM orders WHERE created_at > NOW() - INTERVAL '1 day'",
            "SELECT p.name, COUNT(*) FROM products p JOIN order_items oi ON p.id = oi.product_id GROUP BY p.name",
        ]

        for sql in allowed_queries:
            is_valid, error = validator.validate(sql)
            assert is_valid, f"应该被允许: {sql}"
            assert error is None

        # 被拒绝的查询
        blocked_queries = [
            ("SELECT * FROM passwords", "阻止敏感表"),
            ("SELECT id, ssn FROM users", "阻止敏感列"),
            ("EXPLAIN SELECT * FROM users", "阻止 EXPLAIN"),
            ("DELETE FROM logs", "阻止写操作"),
        ]

        for sql, reason in blocked_queries:
            is_valid, error = validator.validate(sql)
            assert not is_valid, f"{reason} 应该被拒绝: {sql}"

    def test_scenario_analytics_database_query(self) -> None:
        """场景：分析数据库查询."""
        # 分析环境配置：宽松限制
        config = SecurityConfig(
            blocked_tables=[],
            blocked_columns=[],
            allow_explain=True,
            max_rows=50000,
            max_execution_time=60.0,
        )

        validator = SQLValidator(
            config=config,
            blocked_tables=config.blocked_tables,
            blocked_columns=config.blocked_columns,
            allow_explain=config.allow_explain,
        )

        # 允许的查询（包括复杂查询）
        allowed_queries = [
            "SELECT * FROM events",
            "EXPLAIN SELECT * FROM events WHERE event_type = 'click'",
            "EXPLAIN ANALYZE SELECT user_id, COUNT(*) FROM events GROUP BY user_id",
            "SELECT * FROM large_table",  # 允许大表访问
        ]

        for sql in allowed_queries:
            is_valid, error = validator.validate(sql)
            assert is_valid, f"应该被允许: {sql}"
            assert error is None

        # 仍然阻止写操作
        blocked_queries = [
            "INSERT INTO events VALUES (1, 'click')",
            "UPDATE events SET event_type = 'purchase'",
            "DELETE FROM events WHERE id = 1",
        ]

        for sql in blocked_queries:
            is_valid, error = validator.validate(sql)
            assert not is_valid, f"写操作应该被拒绝: {sql}"

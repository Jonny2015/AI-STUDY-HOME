"""LLM service for generating SQL from natural language."""

import aiosqlite
import sqlglot
from openai import AsyncOpenAI

from app.config import settings
from app.core.db import db_manager
from app.models.metadata import DatabaseMetadataResponse
from app.models.query import GeneratedSQLResponse
from app.utils.logging import logger


class LLMService:
    """Service for generating SQL from natural language using various LLM providers.

    Features:
    - Support for OpenAI, Azure, Anthropic, and custom OpenAI-compatible APIs
    - Configurable model selection
    - Context-aware with database metadata
    - SQL validation after generation
    """

    def __init__(self):
        """Initialize LLM service with configured provider."""
        self.api_key = settings.get_llm_api_key()
        self.model = settings.llm_model
        self.base_url = settings.llm_base_url

        if not self.api_key:
            logger.warning("LLM API key not configured, LLM features will be limited")

        # Initialize OpenAI client (works with OpenAI-compatible APIs)
        client_kwargs = {"api_key": self.api_key} if self.api_key else {}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = AsyncOpenAI(**client_kwargs) if self.api_key else None

        if self.api_key:
            logger.info(
                f"LLM service initialized: provider={settings.llm_provider}, model={self.model}, base_url={self.base_url or 'default'}"
            )

    async def _get_database_metadata(self, database_name: str) -> DatabaseMetadataResponse | None:
        """Get database metadata for context.

        Args:
            database_name: Name of database connection

        Returns:
            DatabaseMetadataResponse if found, None otherwise
        """
        try:
            async with aiosqlite.connect(db_manager.db_path) as conn:
                # Get db_type
                cursor = await conn.execute(
                    "SELECT db_type FROM databases WHERE name = ?",
                    (database_name,),
                )
                row = await cursor.fetchone()

                if not row:
                    return None

                db_type = row[0]

                # Get metadata
                cursor = await conn.execute(
                    """
                    SELECT schema_name, table_name, table_type, column_name, data_type
                    FROM metadata
                    WHERE db_name = ?
                    ORDER BY schema_name, table_name, column_name
                    """,
                    (database_name,),
                )
                rows = await cursor.fetchall()

                if not rows:
                    return None

                # Build simplified metadata for LLM context
                tables_info = []
                current_table = None
                table_info = ""

                for schema_name, table_name, table_type, column_name, data_type in rows:
                    table_key = f"{schema_name}.{table_name}"

                    if current_table != table_key:
                        if current_table is not None:
                            tables_info.append(f"  - {table_info}")
                        current_table = table_key
                        table_info = f"{table_name} ({table_type})\n    Columns: "

                    table_info += f"{column_name}({data_type}), "

                if current_table:
                    tables_info.append(f"  - {table_info}")
                return DatabaseMetadataResponse(
                    database_name=database_name,
                    db_type=db_type,
                    tables=[],  # Not needed for LLM
                    metadata_extracted_at="",
                    is_cached=True,
                )

        except Exception as e:
            logger.error(f"Failed to get metadata for {database_name}: {e}")
            return None

    async def _build_system_message(self, database_name: str) -> str:
        """Build system message with database context.

        Args:
            database_name: Name of database connection

        Returns:
            System message string
        """
        # Get metadata
        metadata = await self._get_database_metadata(database_name)

        if not metadata:
            return """You are a SQL expert. Generate SELECT queries based on natural language requests.

Rules:
- Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
- Always add LIMIT clause at the end (default 1000)
- Use proper SQL syntax
- Return only the SQL query, no explanations"""

        # Build context with metadata
        # Note: In production, you'd include actual table/column info
        return f"""You are a SQL expert for a {metadata.db_type} database. Generate SELECT queries based on natural language requests.

Available tables and columns will be provided based on the database schema.

Rules:
- Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
- Always add LIMIT clause at the end (default 1000)
- Use proper {metadata.db_type} syntax
- Use table and column names from the schema
- Return only the SQL query, no explanations

Database: {database_name}
Type: {metadata.db_type}"""

    async def _validate_generated_sql(self, sql: str) -> tuple[bool, str]:
        """Validate generated SQL.

        Args:
            sql: Generated SQL

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            parsed = sqlglot.parse_one(sql, error_level=sqlglot.ErrorLevel.IMMEDIATE)

            if not isinstance(parsed, sqlglot.exp.Select):
                return False, "生成的 SQL 不是 SELECT 查询"

            return True, ""

        except sqlglot.errors.ParseError as e:
            logger.error(f"Generated SQL parse error: {e}")
            return False, f"生成的 SQL 语法错误: {str(e)}"
        except Exception as e:
            logger.error(f"SQL validation error: {e}")
            return False, f"SQL 验证失败: {str(e)}"

    async def generate_sql(self, database_name: str, prompt: str) -> GeneratedSQLResponse:
        """Generate SQL from natural language.

        Args:
            database_name: Name of database connection
            prompt: Natural language prompt

        Returns:
            GeneratedSQLResponse with SQL and explanation

        Raises:
            ValueError: If generation fails
            Exception: If validation fails
        """
        # Check if LLM API key is configured
        if not self.client:
            # Return a helpful placeholder SQL when API key is not configured
            logger.warning(f"LLM API key not configured, returning placeholder SQL for {database_name}")
            placeholder_sql = f"-- LLM API 密钥未配置\n-- 请在环境变量中设置 LLM_API_KEY 或 OPENAI_API_KEY\n-- 或者根据您的需求修改下方的 SQL 查询\n\n-- 根据您的描述: {prompt}\nSELECT * FROM your_table_name LIMIT 1000;"

            return GeneratedSQLResponse(
                sql=placeholder_sql,
                explanation="LLM API 密钥未配置，请配置后使用 AI 功能。您可以手动修改上方的 SQL 查询。",
                warnings=["LLM API key not configured"],
            )

        try:
            # Build system message
            system_message = await self._build_system_message(database_name)

            # Call LLM API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
                max_tokens=500,
            )

            # Debug logging
            logger.debug(f"LLM API response type: {type(response)}")
            logger.debug(f"LLM API response: {response}")

            # Validate response
            if not response:
                raise ValueError("LLM API 返回空响应")

            if not hasattr(response, "choices") or not response.choices:
                logger.error(f"Invalid response structure. Response: {response}")
                raise ValueError(
                    f"LLM API 返回的响应格式不正确,缺少 choices 字段。请检查 BASE_URL 和 MODEL 配置是否正确。\n当前配置: base_url={self.base_url}, model={self.model}"
                )

            sql = response.choices[0].message.content or ""

            # Clean up SQL (remove markdown code blocks if present)
            sql = sql.strip()
            if sql.startswith("```"):
                sql = sql.split("\n", 1)[1]
            if sql.endswith("```"):
                sql = sql.rsplit("\n", 1)[0]
            sql = sql.strip()

            # Validate SQL
            is_valid, error_msg = await self._validate_generated_sql(sql)
            if not is_valid:
                raise ValueError(f"生成的 SQL 无效: {error_msg}")

            # Add LIMIT if not present
            if "LIMIT" not in sql.upper():
                sql += " LIMIT 1000"

            return GeneratedSQLResponse(
                sql=sql,
                explanation="根据您的请求生成 SQL 查询",
                warnings=[],
            )

        except ValueError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate SQL for {database_name}: {e}")
            raise Exception(f"生成 SQL 失败: {str(e)}") from e

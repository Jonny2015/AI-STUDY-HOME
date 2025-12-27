"""Query request and response models."""

from typing import List, Dict, Any

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


class ExecuteQueryRequest(BaseModel):
    """SQL query execution request.

    Attributes:
        sql: SQL query string to execute
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    sql: str = Field(..., description="SQL query to execute", min_length=1)


class QueryResult(BaseModel):
    """SQL query execution result.

    Attributes:
        columns: List of column names
        rows: List of rows as dictionaries
        row_count: Total number of rows returned
        execution_time_ms: Query execution time in milliseconds
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    columns: List[str] = Field(alias="columns", description="Column names")
    rows: List[Dict[str, Any]] = Field(alias="rows", description="Row data")
    row_count: int = Field(alias="rowCount", description="Total row count")
    execution_time_ms: int = Field(alias="executionTimeMs", description="Execution time in milliseconds")


class NaturalLanguageQueryRequest(BaseModel):
    """Natural language to SQL generation request.

    Attributes:
        prompt: Natural language prompt
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    prompt: str = Field(..., description="Natural language prompt", min_length=1)


class GeneratedSQLResponse(BaseModel):
    """Generated SQL response.

    Attributes:
        sql: Generated SQL query
        explanation: Explanation of the generated SQL
        warnings: Optional warnings about the generated SQL
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    sql: str = Field(..., description="Generated SQL query")
    explanation: str = Field(..., description="Explanation of the SQL")
    warnings: List[str] = Field(default_factory=list, alias="warnings", description="Optional warnings")

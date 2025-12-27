"""Metadata models for database structure information."""

from typing import Literal

from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel

TableType = Literal["table", "view"]


class ColumnMetadata(BaseModel):
    """Column metadata information.

    Attributes:
        column_name: Name of the column
        data_type: SQL data type
        is_nullable: Whether the column accepts NULL values
        is_primary_key: Whether the column is part of primary key
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    column_name: str = Field(alias="columnName", description="Column name")
    data_type: str = Field(alias="dataType", description="SQL data type")
    is_nullable: bool = Field(alias="isNullable", description="Whether nullable")
    is_primary_key: bool = Field(alias="isPrimaryKey", description="Whether primary key")


class TableMetadata(BaseModel):
    """Table metadata information.

    Attributes:
        table_name: Name of the table
        table_type: Type (table or view)
        schema_name: Schema name (e.g., public, information_schema)
        columns: List of column metadata
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    table_name: str = Field(alias="tableName", description="Table name")
    table_type: TableType = Field(alias="tableType", description="Table type")
    schema_name: str = Field(alias="schemaName", description="Schema name")
    columns: list[ColumnMetadata] = Field(alias="columns", description="Column list")


class DatabaseMetadataResponse(BaseModel):
    """Database metadata response.

    Attributes:
        database_name: Name of the database connection
        db_type: Type of database (postgresql or mysql)
        tables: List of table metadata
        metadata_extracted_at: When metadata was extracted
        is_cached: Whether this is cached data
    """

    model_config = {
        "alias_generator": to_camel,
        "populate_by_name": True,
    }

    database_name: str = Field(alias="databaseName", description="Database name")
    db_type: str = Field(alias="dbType", description="Database type")
    tables: list[TableMetadata] = Field(alias="tables", description="Table list")
    metadata_extracted_at: str = Field(alias="metadataExtractedAt", description="Extraction timestamp")
    is_cached: bool = Field(alias="isCached", description="Whether from cache")

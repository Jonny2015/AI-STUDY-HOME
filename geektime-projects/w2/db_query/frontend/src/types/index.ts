/** TypeScript type definitions matching backend Pydantic models */

export interface Database {
  databaseName: string;
  dbType: "postgresql" | "mysql";
  createdAt: string; // ISO 8601
  connectionStatus: "connected" | "failed" | "pending";
  lastConnectedAt?: string; // ISO 8601
}

export interface DatabaseListResponse {
  databases: Database[];
  totalCount: number;
}

export interface ColumnMetadata {
  columnName: string;
  dataType: string;
  isNullable: boolean;
  isPrimaryKey: boolean;
}

export interface TableMetadata {
  schemaName: string;
  tableName: string;
  tableType: "table" | "view";
  columns: ColumnMetadata[];
}

export interface DatabaseMetadataResponse {
  databaseName: string;
  dbType: string;
  tables: TableMetadata[];
  metadataExtractedAt: string;
  isCached: boolean;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, unknown>[];
  rowCount: number;
  executionTimeMs: number;
}

export interface ErrorResponse {
  error: string;
  message: string;
  details?: Record<string, unknown> | null;
}

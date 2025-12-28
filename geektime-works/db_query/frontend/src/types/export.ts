/** Export-related types. */

export type ExportFormat = "csv" | "json" | "markdown";

export type ExportScope = "current_page" | "all_data";

export type TaskStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface ExportRequest {
  sql: string;
  format: ExportFormat;
  exportAll: boolean;
}

export interface ExportCheckRequest {
  sql: string;
  format: ExportFormat;
  useSampling: boolean;
  sampleSize: number;
}

export interface SizeEstimate {
  estimatedBytes: number;
  estimatedMb: number;
  bytesPerRow: number;
  method: "metadata" | "sample" | "actual";
  confidence: "low" | "medium" | "high";
  sampleSize?: number | null;
}

export interface ExportCheckResponse {
  allowed: boolean;
  estimatedSize: SizeEstimate;
  warning?: string | null;
  recommendation?: string | null;
}

export interface TaskResponse {
  taskId: string;
  status: TaskStatus;
  progress: number;
  fileUrl?: string | null;
  error?: string | null;
}

export interface ExportOptions {
  sql: string;
  format: ExportFormat;
  exportAll: boolean;
  onComplete?: (task: TaskResponse) => void;
  onError?: (error: string) => void;
}

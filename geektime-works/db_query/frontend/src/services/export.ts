/** Export service API client. */

import { apiClient } from "./api";
import type {
  ExportRequest,
  ExportCheckRequest,
  ExportCheckResponse,
  TaskResponse,
} from "../types/export";

/**
 * Export service for managing data export operations.
 */
export const exportService = {
  /**
   * Create a new export task.
   *
   * @param databaseName - Database connection name
   * @param request - Export request with SQL, format, and scope
   * @returns Promise resolving to task response with task ID
   */
  async createExportTask(
    databaseName: string,
    request: ExportRequest
  ): Promise<TaskResponse> {
    const response = await apiClient.post<TaskResponse>(
      `/api/v1/dbs/${databaseName}/export`,
      request
    );
    return response.data;
  },

  /**
   * Check export file size before creating task.
   *
   * @param databaseName - Database connection name
   * @param request - Check request with SQL and format
   * @returns Promise resolving to size check response
   */
  async checkExportSize(
    databaseName: string,
    request: ExportCheckRequest
  ): Promise<ExportCheckResponse> {
    const response = await apiClient.post<ExportCheckResponse>(
      `/api/v1/dbs/${databaseName}/export/check`,
      request
    );
    return response.data;
  },

  /**
   * Get export task status.
   *
   * @param taskId - Task ID
   * @returns Promise resolving to task response with current status
   */
  async getTaskStatus(taskId: string): Promise<TaskResponse> {
    const response = await apiClient.get<TaskResponse>(
      `/api/v1/tasks/${taskId}`
    );
    return response.data;
  },

  /**
   * Cancel export task.
   *
   * @param taskId - Task ID
   * @returns Promise resolving when task is cancelled
   */
  async cancelTask(taskId: string): Promise<void> {
    await apiClient.delete(`/api/v1/tasks/${taskId}`);
  },

  /**
   * Poll task status until completion.
   *
   * @param taskId - Task ID
   * @param onProgress - Callback for progress updates
   * @param interval - Polling interval in milliseconds (default: 1000)
   * @returns Promise resolving to final task response
   */
  async pollTaskStatus(
    taskId: string,
    onProgress?: (task: TaskResponse) => void,
    interval: number = 1000
  ): Promise<TaskResponse> {
    return new Promise((resolve, reject) => {
      const poll = async () => {
        try {
          const task = await this.getTaskStatus(taskId);

          // Call progress callback
          if (onProgress) {
            onProgress(task);
          }

          // Check if task is complete
          if (task.status === "completed") {
            resolve(task);
          } else if (task.status === "failed" || task.status === "cancelled") {
            reject(new Error(task.error || "Export failed"));
          } else {
            // Continue polling
            setTimeout(poll, interval);
          }
        } catch (error) {
          reject(error);
        }
      };

      poll();
    });
  },

  /**
   * Get download URL for exported file.
   *
   * @param filename - Export filename
   * @returns Full download URL
   */
  getDownloadUrl(filename: string): string {
    const baseURL = apiClient.defaults.baseURL;
    return `${baseURL}/api/v1/exports/download/${filename}`;
  },

  /**
   * Download exported file.
   *
   * @param filename - Export filename
   * @returns Promise resolving when download starts
   */
  downloadFile(filename: string): void {
    const url = this.getDownloadUrl(filename);
    window.open(url, "_blank");
  },

  // AI Export Assistant API methods

  /**
   * Analyze if export should be suggested based on query results.
   *
   * @param databaseName - Database connection name
   * @param sqlText - SQL query that was executed
   * @param queryResult - Query result with columns, rows, and row count
   * @returns Promise resolving to intent analysis results
   */
  async analyzeExportIntent({
    databaseName,
    sqlText,
    queryResult
  }: {
    databaseName: string;
    sqlText: string;
    queryResult: {
      columns: Array<{ name: string; type: string }>;
      rows: any[][];
      rowCount: number;
    };
  }): Promise<{
    shouldSuggestExport: boolean;
    confidence: number;
    reasoning: string;
    clarificationNeeded: boolean;
    clarificationQuestion: string | null;
    suggestedFormat: string;
    suggestedScope: string;
  }> {
    const response = await apiClient.post('/api/v1/export/analyze-intent', {
      databaseName,
      sqlText,
      queryResult
    });
    return response.data;
  },

  /**
   * Get proactive export suggestion with quick actions.
   *
   * @param databaseName - Database connection name
   * @param sqlText - SQL query that was executed
   * @param queryResult - Query result data
   * @param intentAnalysis - Results from analyzeExportIntent
   * @returns Promise resolving to suggestion text and quick actions
   */
  async getProactiveSuggestion({
    databaseName,
    sqlText,
    queryResult,
    intentAnalysis
  }: {
    databaseName: string;
    sqlText: string;
    queryResult: {
      columns: Array<{ name: string; type: string }>;
      rows: any[][];
      rowCount: number;
    };
    intentAnalysis: {
      shouldSuggestExport: boolean;
      confidence: number;
      reasoning: string;
      clarificationNeeded: boolean;
      clarificationQuestion: string | null;
      suggestedFormat: string;
      suggestedScope: string;
    };
  }): Promise<{
    suggestionText: string;
    quickActions: Array<{
      type: 'export' | 'filter' | 'clarification' | 'transform';
      label: string;
      action: string;
      format?: string;
      scope?: string;
      description?: string;
    }>;
    confidence: number;
    explanation: string;
  }> {
    const response = await apiClient.post('/api/v1/export/proactive-suggestion', {
      databaseName,
      sqlText,
      queryResult,
      intentAnalysis
    });
    return response.data;
  },

  /**
   * Track user response to AI export suggestion.
   *
   * @param params - Response tracking parameters
   * @returns Promise resolving when response is tracked
   */
  async trackSuggestionResponse(params: {
    suggestionId?: string;
    databaseName: string;
    suggestionType: string;
    sqlContext: string;
    rowCount: number;
    confidence: number;
    suggestedFormat: string;
    suggestedScope: string;
    userResponse: 'ACCEPTED' | 'REJECTED' | 'IGNORED' | 'MODIFIED';
    responseTimeMs?: number;
    suggestedAt?: string;
    respondedAt?: string;
  }): Promise<void> {
    await apiClient.post('/api/v1/export/track-response', params);
  },

  /**
   * Get export analytics data for AI suggestions.
   *
   * @param databaseName - Database name to filter analytics
   * @param days - Number of days to look back (default: 7)
   * @returns Promise resolving to analytics statistics
   */
  async getExportAnalytics(
    databaseName: string,
    days: number = 7
  ): Promise<{
    totalSuggestions: number;
    acceptanceRate: number;
    avgResponseTime: number;
    responsesByType: Record<string, { total: number; accepted: number }>;
    responsesByFormat: Record<string, { total: number; accepted: number }>;
  }> {
    const response = await apiClient.get('/api/v1/export/analytics', {
      params: {
        databaseName,
        days
      }
    });
    return response.data;
  },
};

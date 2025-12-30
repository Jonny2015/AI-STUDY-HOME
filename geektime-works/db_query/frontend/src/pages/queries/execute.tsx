// @ts-nocheck
/** Query execution page with SQL editor and result table. */

import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import { Card, Button, Space, Spin, Alert, List, Typography, Divider } from "antd";
import { PlayCircleOutlined, ReloadOutlined } from "@ant-design/icons";
import { apiClient } from "../../services/api";
import { QueryResult, QueryHistoryEntry, QueryInput } from "../../types/query";
import { SqlEditor } from "../../components/SqlEditor";
import { ResultTable } from "../../components/ResultTable";
import { ExportButton } from "../../components/query/ExportButton";
import { AiExportAssistant } from "../../components/AiExportAssistant";

const { Text } = Typography;

export const QueryExecute: React.FC = () => {
  const { databaseName } = useParams<{ databaseName: string }>();
  const [sql, setSql] = useState("SELECT * FROM ");
  const [result, setResult] = useState<QueryResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<QueryHistoryEntry[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Export related states
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showExportProgress, setShowExportProgress] = useState(false);
  const [exportTaskId, setExportTaskId] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  // AI Export Assistant states
  const [aiAssistantEnabled, setAiAssistantEnabled] = useState(true);

  useEffect(() => {
    if (databaseName) {
      loadHistory();
    }
  }, [databaseName]);

  const loadHistory = async () => {
    if (!databaseName) return;

    setLoadingHistory(true);
    try {
      const response = await apiClient.get<QueryHistoryEntry[]>(
        `/api/v1/dbs/${databaseName}/history`
      );
      setHistory(response.data);
    } catch (err) {
      console.error("Failed to load history:", err);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleExecute = async () => {
    if (!databaseName || !sql.trim()) {
      setError("Please enter a SQL query");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const input: QueryInput = { sql: sql.trim() };
      const response = await apiClient.post<QueryResult>(
        `/api/v1/dbs/${databaseName}/query`,
        input
      );
      setResult(response.data);
      // Reload history after successful query
      await loadHistory();
    } catch (err: any) {
      const errorMessage =
        err.response?.data?.detail || err.message || "Query execution failed";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleHistoryClick = (historyItem: QueryHistoryEntry) => {
    setSql(historyItem.sqlText);
    setError(null);
    setResult(null);
  };

  // Handle export from AI assistant
  const handleAiExport = (params: {
    format: string;
    scope: string;
    sql: string;
  }) => {
    setShowExportDialog(true);
  };

  // Export handlers
  const handleExportClick = () => {
    setShowExportDialog(true);
  };

  const handleExportConfirm = async (request: ExportRequest) => {
    setShowExportDialog(false);

    try {
      // Use the export service from ExportButton component
      const { exportService } = await import('../../services/export');

      // Check file size first
      const checkResponse = await exportService.checkExportSize(databaseName!, {
        sql: request.sql,
        format: request.format,
        useSampling: true,
        sampleSize: 100,
      });

      // Create export task
      const taskResponse = await exportService.createExportTask(
        databaseName!,
        {
          sql: request.sql,
          format: request.format,
          exportAll: true,
        }
      );

      setExportTaskId(taskResponse.taskId);
      setShowExportProgress(true);
    } catch (error: any) {
      setExportError(error.message || '导出失败');
      setShowExportProgress(true);
    }
  };

  const handleExportComplete = (fileUrl: string, fileName: string) => {
    setShowExportProgress(false);
    setExportTaskId(null);
    setExportError(null);
    // You can add additional completion logic here
  };

  const handleExportError = (error: string) => {
    setExportError(error);
    setShowExportProgress(false);
    setExportTaskId(null);
  };

  const handleExportProgressClose = () => {
    setShowExportProgress(false);
    setExportTaskId(null);
    setExportError(null);
  };

  return (
    <div style={{ padding: 24 }}>
      <Card
        title={`Execute Query - ${databaseName}`}
        extra={
          <Space>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleExecute}
              loading={loading}
            >
              Execute
            </Button>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadHistory}
              loading={loadingHistory}
            >
              Refresh History
            </Button>
            <ExportButton
              databaseName={databaseName!}
              sql={sql}
              disabled={!sql.trim() || !result}
            />
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: "100%" }} size="large">
          <div>
            <Card title="SQL Editor" size="small">
              <SqlEditor value={sql} onChange={(val) => setSql(val || "")} height="200px" />
            </Card>
          </div>

          {error && (
            <Alert
              message="Error"
              description={error}
              type="error"
              showIcon
              closable
              onClose={() => setError(null)}
            />
          )}

          {loading && (
            <div style={{ textAlign: "center", padding: "50px" }}>
              <Spin size="large" />
            </div>
          )}

          {result && (
            <>
              {/* AI Export Assistant */}
              {databaseName && (
                <AiExportAssistant
                  databaseName={databaseName}
                  sqlText={sql}
                  queryResult={{
                    columns: result.columns,
                    rows: result.rows,
                    rowCount: result.rowCount
                  }}
                  onExport={handleAiExport}
                  enabled={aiAssistantEnabled}
                />
              )}

              <Card title="Query Results" size="small">
                <ResultTable result={result} loading={loading} />
              </Card>
            </>
          )}
        </Space>
      </Card>

      <Card title="Query History" style={{ marginTop: 16 }}>
        {loadingHistory ? (
          <Spin />
        ) : (
          <List
            dataSource={history}
            renderItem={(item) => (
              <List.Item
                style={{
                  cursor: "pointer",
                  backgroundColor: item.success ? "transparent" : "#fff2f0",
                }}
                onClick={() => handleHistoryClick(item)}
              >
                <List.Item.Meta
                  title={
                    <Space>
                      <Text
                        code
                        style={{
                          maxWidth: "600px",
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          whiteSpace: "nowrap",
                          display: "inline-block",
                        }}
                      >
                        {item.sqlText}
                      </Text>
                      {item.success ? (
                        <Text type="success">
                          ✓ {item.rowCount} rows in {item.executionTimeMs}ms
                        </Text>
                      ) : (
                        <Text type="danger">✗ Failed</Text>
                      )}
                    </Space>
                  }
                  description={
                    <Text type="secondary">
                      {new Date(item.executedAt).toLocaleString()}
                    </Text>
                  }
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      {/* Export Dialog */}
      {databaseName && result && (
        <ExportDialog
          visible={showExportDialog}
          onOk={handleExportConfirm}
          onCancel={() => setShowExportDialog(false)}
          sql={sql}
          databaseName={databaseName}
          totalRows={result.rowCount}
          hasMoreData={false}
        />
      )}

      {/* Export Progress Dialog */}
      {showExportProgress && exportTaskId && (
        <ExportProgress
          visible={showExportProgress}
          taskId={exportTaskId}
          onCancel={handleExportProgressClose}
          onComplete={handleExportComplete}
          onError={handleExportError}
        />
      )}

      {/* Export Error Alert */}
      {exportError && (
        <Alert
          message="Export Error"
          description={exportError}
          type="error"
          showIcon
          closable
          onClose={() => setExportError(null)}
          style={{ marginTop: 16 }}
        />
      )}
    </div>
  );
};

/** Main page with integrated database management and query interface. */

import React, { useState, useEffect } from "react";
import {
  Card,
  Spin,
  Button,
  Input,
  Space,
  Table,
  Row,
  Col,
  Typography,
  Empty,
  Tabs,
  Modal,
  App,
  Switch,
  Progress,
  Divider,
  Tooltip,
} from "antd";
import {
  PlayCircleOutlined,
  SearchOutlined,
  DatabaseOutlined,
  ReloadOutlined,
  ExclamationCircleOutlined,
  BulbOutlined,
  DownloadOutlined,
  FileTextOutlined,
  CodeOutlined,
  FileMarkdownOutlined,
} from "@ant-design/icons";
import { apiClient } from "../services/api";
import { DatabaseMetadata, TableMetadata } from "../types/metadata";
import { MetadataTree } from "../components/MetadataTree";
import { SqlEditor } from "../components/SqlEditor";
import { DatabaseSidebar } from "../components/DatabaseSidebar";
import { NaturalLanguageInput } from "../components/NaturalLanguageInput";

const { Title, Text } = Typography;

interface QueryResult {
  columns: Array<{ name: string; dataType: string }>;
  rows: Array<Record<string, any>>;
  rowCount: number;
  executionTimeMs: number;
  sql: string;
}

export const Home: React.FC = () => {
  const { message } = App.useApp();
  const [selectedDatabase, setSelectedDatabase] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<DatabaseMetadata | null>(null);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [sql, setSql] = useState("SELECT * FROM ");
  const [executing, setExecuting] = useState(false);
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [activeTab, setActiveTab] = useState<"manual" | "natural">("manual");
  const [generatingSql, setGeneratingSql] = useState(false);
  const [nlError, setNlError] = useState<string | null>(null);

  // AI Assistant state
  const [aiAssistantEnabled, setAiAssistantEnabled] = useState(false);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportProgress, setExportProgress] = useState(0);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (selectedDatabase) {
      loadMetadata();
    }
  }, [selectedDatabase]);

  const loadMetadata = async () => {
    if (!selectedDatabase) return;

    setLoading(true);
    try {
      const response = await apiClient.get<DatabaseMetadata>(
        `/api/v1/dbs/${selectedDatabase}`
      );
      setMetadata(response.data);
    } catch (error) {
      console.error("Failed to load metadata:", error);
      message.error("Failed to load database metadata");
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteQuery = async () => {
    if (!selectedDatabase || !sql.trim()) {
      message.warning("Please enter a SQL query");
      return;
    }

    setExecuting(true);
    try {
      const response = await apiClient.post<QueryResult>(
        `/api/v1/dbs/${selectedDatabase}/query`,
        { sql: sql.trim() }
      );
      setQueryResult(response.data);
      message.success(
        `Query executed - ${response.data.rowCount} rows in ${response.data.executionTimeMs}ms`
      );

      // AI Assistant: Show export prompt if enabled and has results
      if (aiAssistantEnabled && response.data.rowCount > 0) {
        setTimeout(() => {
          setShowExportModal(true);
        }, 500);
      }
    } catch (error: any) {
      message.error(error.response?.data?.detail || "Query execution failed");
      setQueryResult(null);
    } finally {
      setExecuting(false);
    }
  };

  const handleTableClick = (table: TableMetadata) => {
    setSql(`SELECT * FROM ${table.schemaName}.${table.name} LIMIT 100`);
  };

  const handleRefreshMetadata = async () => {
    if (!selectedDatabase) return;
    try {
      await apiClient.post(`/api/v1/dbs/${selectedDatabase}/refresh`);
      message.success("Metadata refreshed");
      loadMetadata();
    } catch (error: any) {
      message.error("Failed to refresh metadata");
    }
  };

  const handleGenerateSQL = async (prompt: string) => {
    if (!selectedDatabase) return;

    setGeneratingSql(true);
    setNlError(null);
    try {
      const response = await apiClient.post<{ sql: string; explanation: string }>(
        `/api/v1/dbs/${selectedDatabase}/query/natural`,
        { prompt }
      );
      setSql(response.data.sql);
      setActiveTab("manual"); // Switch to manual tab to show generated SQL
      message.success("SQL generated successfully! You can now edit and execute it.");
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || "Failed to generate SQL";
      setNlError(errorMsg);
      message.error(errorMsg);
    } finally {
      setGeneratingSql(false);
    }
  };

  const handleExportCSV = () => {
    if (!queryResult || queryResult.rows.length === 0) {
      message.warning("No data to export");
      return;
    }

    // Warn if result is large
    if (queryResult.rows.length > 10000) {
      Modal.confirm({
        title: "Large Dataset Warning",
        icon: <ExclamationCircleOutlined />,
        content: `You are about to export ${queryResult.rowCount.toLocaleString()} rows. This may take a while and consume memory. Continue?`,
        onOk: () => exportToCSV(),
      });
    } else {
      exportToCSV();
    }
  };

  const exportToCSV = () => {
    if (!queryResult) return;

    // Generate CSV content
    const headers = queryResult.columns.map((col) => col.name);
    const csvRows = [headers.join(",")];

    queryResult.rows.forEach((row) => {
      const values = headers.map((header) => {
        const value = row[header];
        // Handle null/undefined
        if (value === null || value === undefined) return "";
        // Escape quotes and wrap in quotes if contains comma or quote
        const stringValue = String(value);
        if (stringValue.includes(",") || stringValue.includes('"') || stringValue.includes("\n")) {
          return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
      });
      csvRows.push(values.join(","));
    });

    const csvContent = csvRows.join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);
    link.href = URL.createObjectURL(blob);
    link.download = `${selectedDatabase}_${timestamp}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
    message.success(`Exported ${queryResult.rowCount} rows to CSV`);
  };

  const handleExportJSON = () => {
    if (!queryResult || queryResult.rows.length === 0) {
      message.warning("No data to export");
      return;
    }

    // Warn if result is large
    if (queryResult.rows.length > 10000) {
      Modal.confirm({
        title: "Large Dataset Warning",
        icon: <ExclamationCircleOutlined />,
        content: `You are about to export ${queryResult.rowCount.toLocaleString()} rows. This may take a while and consume memory. Continue?`,
        onOk: () => exportToJSON(),
      });
    } else {
      exportToJSON();
    }
  };

  const handleExportMarkdown = () => {
    if (!queryResult || queryResult.rows.length === 0) {
      message.warning("No data to export");
      return;
    }

    // Warn if result is large
    if (queryResult.rows.length > 10000) {
      Modal.confirm({
        title: "Large Dataset Warning",
        icon: <ExclamationCircleOutlined />,
        content: `You are about to export ${queryResult.rowCount.toLocaleString()} rows. Markdown will only include first 100 rows. Continue?`,
        onOk: () => exportToMarkdown(),
      });
    } else {
      exportToMarkdown();
    }
  };

  const exportToMarkdown = () => {
    if (!queryResult) return;

    // Generate Markdown content
    const headers = queryResult.columns.map((col) => col.name);
    let mdContent = `# Query Results\n\n`;
    mdContent += `**Database:** ${selectedDatabase}\n`;
    mdContent += `**Rows:** ${queryResult.rowCount}\n`;
    mdContent += `**Execution Time:** ${queryResult.executionTimeMs}ms\n\n`;
    mdContent += `## Data\n\n`;

    // Add table header
    mdContent += `| ${headers.join(" | ")} |\n`;
    mdContent += `| ${headers.map(() => "---").join(" | ")} |\n`;

    // Add table rows (limit to 100 for readability)
    const maxRows = Math.min(queryResult.rows.length, 100);
    for (let i = 0; i < maxRows; i++) {
      const row = queryResult.rows[i];
      const values = headers.map((header) => {
        const value = row[header];
        if (value === null || value === undefined) return "NULL";
        // Escape pipe characters
        return String(value).replace(/\|/g, "\\|");
      });
      mdContent += `| ${values.join(" | ")} |\n`;
    }

    if (queryResult.rows.length > 100) {
      mdContent += `\n*... and ${queryResult.rows.length - 100} more rows*\n`;
    }

    const blob = new Blob([mdContent], { type: "text/markdown;charset=utf-8;" });
    const link = document.createElement("a");
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);
    link.href = URL.createObjectURL(blob);
    link.download = `${selectedDatabase}_${timestamp}.md`;
    link.click();
    URL.revokeObjectURL(link.href);
    message.success(`Exported ${Math.min(queryResult.rowCount, 100)} rows to Markdown`);
  };

  // Handle export from AI assistant
  const handleAiExport = async (format: string = "csv", exportAll: boolean = false) => {
    if (!selectedDatabase || !sql.trim()) {
      return;
    }

    setShowExportModal(false);
    setExporting(true);
    setExportProgress(0);

    try {
      // Simulate progress
      const progressInterval = setInterval(() => {
        setExportProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      // Call export API
      const response = await fetch(`/api/v1/dbs/${selectedDatabase}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sql: sql.trim(),
          format: format,
          exportAll: exportAll
        })
      });

      if (!response.ok) {
        throw new Error('Export failed');
      }

      clearInterval(progressInterval);
      setExportProgress(100);

      // Get the blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `export-${Date.now()}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      message.success("数据导出完成");
    } catch (error: any) {
      message.error(`导出失败: ${error.message}`);
    } finally {
      setTimeout(() => {
        setExporting(false);
        setExportProgress(0);
      }, 1000);
    }
  };

  const exportToJSON = () => {
    if (!queryResult) return;

    const jsonContent = JSON.stringify(queryResult.rows, null, 2);
    const blob = new Blob([jsonContent], { type: "application/json;charset=utf-8;" });
    const link = document.createElement("a");
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -5);
    link.href = URL.createObjectURL(blob);
    link.download = `${selectedDatabase}_${timestamp}.json`;
    link.click();
    URL.revokeObjectURL(link.href);
    message.success(`Exported ${queryResult.rowCount} rows to JSON`);
  };

  const tableColumns =
    queryResult?.columns.map((col) => ({
      title: col.name,
      dataIndex: col.name,
      key: col.name,
      ellipsis: true,
    })) || [];

  // No database selected state
  if (!selectedDatabase) {
    return (
      <div style={{ display: "flex", height: "100vh" }}>
        <DatabaseSidebar
          selectedDatabase={selectedDatabase}
          onSelectDatabase={setSelectedDatabase}
        />
        <div
          style={{
            marginLeft: 280,
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "#F4EFEA",
          }}
        >
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <Space direction="vertical" size={16}>
                <Title level={3} style={{ textTransform: "uppercase" }}>
                  NO DATABASE SELECTED
                </Title>
                <Text type="secondary" style={{ fontSize: 15 }}>
                  Add a database from the sidebar to get started
                </Text>
              </Space>
            }
          />
        </div>
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div style={{ display: "flex", height: "100vh" }}>
        <DatabaseSidebar
          selectedDatabase={selectedDatabase}
          onSelectDatabase={setSelectedDatabase}
        />
        <div
          style={{
            marginLeft: 280,
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: "#F4EFEA",
          }}
        >
          <Spin size="large" />
        </div>
      </div>
    );
  }

  if (!metadata) {
    return null;
  }

  return (
    <div style={{ display: "flex", height: "100vh", background: "#F4EFEA" }}>
      {/* Database List Sidebar */}
      <DatabaseSidebar
        selectedDatabase={selectedDatabase}
        onSelectDatabase={setSelectedDatabase}
      />

      {/* Schema Sidebar - Full Height */}
      <div
        style={{
          width: 340,
          height: "100vh",
          background: "#FFFFFF",
          borderTop: "3px solid #000000",
          borderRight: "2px solid #000000",
          display: "flex",
          flexDirection: "column",
          position: "fixed",
          left: 280,
          top: 0,
        }}
      >
        {/* Database Name Top Bar - Sunbeam Yellow */}
        <div
          style={{
            padding: "16px 20px",
            background: "#FFDE00",
            borderBottom: "2px solid #000000",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            minHeight: 60,
          }}
        >
          <Space>
            <DatabaseOutlined style={{ fontSize: 20, fontWeight: 700 }} />
            <Title
              level={4}
              style={{
                margin: 0,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
                fontSize: 18,
                fontWeight: 700,
              }}
            >
              {selectedDatabase}
            </Title>
          </Space>
          <Space>
            {/* AI Assistant Switch */}
            <Space style={{ marginRight: 12 }}>
              <BulbOutlined
                style={{
                  fontSize: 18,
                  color: aiAssistantEnabled ? "#FFDE00" : "#D9D9D9",
                }}
              />
              <Text
                strong
                style={{
                  fontSize: 12,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                }}
              >
                AI 助手
              </Text>
              <Switch
                checked={aiAssistantEnabled}
                onChange={setAiAssistantEnabled}
                checkedChildren="开启"
                unCheckedChildren="关闭"
              />
            </Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={handleRefreshMetadata}
              style={{ borderWidth: 2, fontWeight: 700 }}
            >
              REFRESH
            </Button>
          </Space>
        </div>

        {/* Search Bar */}
        <div style={{ padding: "12px 16px", borderBottom: "1px solid #E4D6C3" }}>
          <Input
            placeholder="Search tables, columns..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            allowClear
            size="middle"
          />
        </div>

        {/* Schema Tree - Fills Remaining Height */}
        <div style={{ flex: 1, overflow: "auto", padding: "16px" }}>
          <MetadataTree
            metadata={metadata}
            searchText={searchText}
            onTableClick={handleTableClick}
          />
        </div>
      </div>

      {/* Main Content Area */}
      <div
        style={{
          marginLeft: 620,
          flex: 1,
          overflowY: "auto",
          overflowX: "hidden",
          padding: "24px",
          height: "100vh",
        }}
      >
        {/* Compact Metrics Row */}
        <Row gutter={12} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <div
              style={{
                padding: "12px",
                textAlign: "center",
                border: "2px solid #000000",
                borderRadius: 2,
                background: "#FFFFFF",
              }}
            >
              <Text
                type="secondary"
                style={{
                  fontSize: 10,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  display: "block",
                  marginBottom: 4,
                }}
              >
                TABLES
              </Text>
              <Text style={{ fontSize: 24, fontWeight: 700 }}>
                {metadata.tables.length}
              </Text>
            </div>
          </Col>
          <Col span={6}>
            <div
              style={{
                padding: "12px",
                textAlign: "center",
                border: "2px solid #000000",
                borderRadius: 2,
                background: "#FFFFFF",
              }}
            >
              <Text
                type="secondary"
                style={{
                  fontSize: 10,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  display: "block",
                  marginBottom: 4,
                }}
              >
                VIEWS
              </Text>
              <Text style={{ fontSize: 24, fontWeight: 700 }}>
                {metadata.views.length}
              </Text>
            </div>
          </Col>
          <Col span={6}>
            <div
              style={{
                padding: "12px",
                textAlign: "center",
                border: "2px solid #000000",
                borderRadius: 2,
                background: "#FFFFFF",
              }}
            >
              <Text
                type="secondary"
                style={{
                  fontSize: 10,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  display: "block",
                  marginBottom: 4,
                }}
              >
                ROWS
              </Text>
              <Text
                style={{
                  fontSize: 24,
                  fontWeight: 700,
                  color: queryResult ? "#16AA98" : "#A1A1A1",
                }}
              >
                {queryResult?.rowCount || 0}
              </Text>
            </div>
          </Col>
          <Col span={6}>
            <div
              style={{
                padding: "12px",
                textAlign: "center",
                border: "2px solid #000000",
                borderRadius: 2,
                background: "#FFFFFF",
              }}
            >
              <Text
                type="secondary"
                style={{
                  fontSize: 10,
                  textTransform: "uppercase",
                  letterSpacing: "0.04em",
                  display: "block",
                  marginBottom: 4,
                }}
              >
                TIME
              </Text>
              <Text
                style={{
                  fontSize: 24,
                  fontWeight: 700,
                  color: queryResult ? "#16AA98" : "#A1A1A1",
                }}
              >
                {queryResult ? `${queryResult.executionTimeMs}ms` : "-"}
              </Text>
            </div>
          </Col>
        </Row>

        {/* Query Editor with Tabs */}
        <Card
          title={
            <Text
              strong
              style={{
                fontSize: 13,
                textTransform: "uppercase",
                letterSpacing: "0.04em",
              }}
            >
              QUERY EDITOR
            </Text>
          }
          extra={
            activeTab === "manual" ? (
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleExecuteQuery}
                loading={executing}
                size="large"
                style={{
                  height: 40,
                  paddingLeft: 20,
                  paddingRight: 20,
                  fontWeight: 700,
                }}
              >
                EXECUTE
              </Button>
            ) : null
          }
          style={{ borderWidth: 2, borderColor: "#000000", marginBottom: 16 }}
        >
          <Tabs
            activeKey={activeTab}
            onChange={(key) => setActiveTab(key as "manual" | "natural")}
            items={[
              {
                key: "manual",
                label: (
                  <Text
                    strong
                    style={{
                      fontSize: 12,
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                    }}
                  >
                    MANUAL SQL
                  </Text>
                ),
                children: (
                  <SqlEditor
                    value={sql}
                    onChange={(value) => setSql(value || "")}
                    height="180px"
                  />
                ),
              },
              {
                key: "natural",
                label: (
                  <Text
                    strong
                    style={{
                      fontSize: 12,
                      textTransform: "uppercase",
                      letterSpacing: "0.04em",
                    }}
                  >
                    NATURAL LANGUAGE
                  </Text>
                ),
                children: (
                  <div style={{ padding: "12px 0" }}>
                    <NaturalLanguageInput
                      onGenerateSQL={handleGenerateSQL}
                      loading={generatingSql}
                      error={nlError}
                    />
                  </div>
                ),
              },
            ]}
            style={{
              marginTop: -16,
            }}
          />
        </Card>

        {/* Query Results */}
        {queryResult && (
          <Card
            title={
              <Space>
                <Text
                  strong
                  style={{
                    fontSize: 13,
                    textTransform: "uppercase",
                    letterSpacing: "0.04em",
                  }}
                >
                  RESULTS
                </Text>
                <Text type="secondary" style={{ fontSize: 12 }}>
                  • {queryResult.rowCount} rows •{" "}
                  {queryResult.executionTimeMs}ms
                </Text>
              </Space>
            }
            extra={
              <Space size={8}>
                <Tooltip title="Export as CSV - Compatible with Excel">
                  <Button
                    size="small"
                    icon={<FileTextOutlined />}
                    onClick={handleExportCSV}
                    style={{ fontSize: 12, fontWeight: 700 }}
                  >
                    CSV
                  </Button>
                </Tooltip>
                <Tooltip title="Export as JSON - For developers">
                  <Button
                    size="small"
                    icon={<CodeOutlined />}
                    onClick={handleExportJSON}
                    style={{ fontSize: 12, fontWeight: 700 }}
                  >
                    JSON
                  </Button>
                </Tooltip>
                <Tooltip title="Export as Markdown - For documentation">
                  <Button
                    size="small"
                    icon={<FileMarkdownOutlined />}
                    onClick={handleExportMarkdown}
                    style={{ fontSize: 12, fontWeight: 700 }}
                  >
                    MD
                  </Button>
                </Tooltip>
              </Space>
            }
            style={{ borderWidth: 2, borderColor: "#000000" }}
          >
            <Table
              columns={tableColumns}
              dataSource={queryResult.rows}
              rowKey={(record) => {
                // Generate a stable unique key based on record content
                const recordStr = JSON.stringify(record);
                const hash = recordStr.split('').reduce((acc, char) => {
                  return ((acc << 5) - acc) + char.charCodeAt(0);
                }, 0);
                return `row-${hash}`;
              }}
              pagination={{
                pageSize: 50,
                showSizeChanger: true,
                showTotal: (total) => `Total ${total} rows`,
                pageSizeOptions: [10, 20, 50, 100],
              }}
              scroll={{ x: "max-content", y: "calc(100vh - 520px)" }}
              size="middle"
              bordered
            />
          </Card>
        )}

        {/* Export Progress Modal */}
        <Modal
          title="数据导出中"
          open={exporting}
          footer={null}
          closable={false}
          centered
        >
          <Space direction="vertical" style={{ width: "100%" }} size="large">
            <div style={{ textAlign: "center" }}>
              <DownloadOutlined style={{ fontSize: 48, color: "#16AA98" }} />
            </div>
            <Progress
              percent={exportProgress}
              status={exportProgress === 100 ? "success" : "active"}
              strokeColor="#16AA98"
            />
            <Text type="secondary" style={{ textAlign: "center", display: "block" }}>
              {exportProgress < 100 ? "正在导出数据..." : "数据导出完成"}
            </Text>
          </Space>
        </Modal>

        {/* AI Export Prompt Modal */}
        <Modal
          title={
            <Space>
              <BulbOutlined style={{ color: "#FFDE00" }} />
              <Text strong>AI 导出助手</Text>
            </Space>
          }
          open={showExportModal}
          onCancel={() => setShowExportModal(false)}
          footer={null}
          centered
          width={520}
        >
          <Space direction="vertical" style={{ width: "100%" }} size="large">
            <div>
              <Title level={4} style={{ margin: 0 }}>
                需要将这次查询结果导出为文件吗？
              </Title>
              <Text type="secondary">
                查询返回 {queryResult?.rowCount || 0} 行数据
              </Text>
            </div>

            <Divider style={{ margin: "12px 0" }} />

            <div style={{ textAlign: "center" }}>
              <Text strong style={{ display: "block", marginBottom: 16 }}>
                选择导出格式：
              </Text>

              <Space size="large">
                {/* CSV 按钮 */}
                <Tooltip title="CSV 格式 - 适合 Excel 打开" placement="top">
                  <Button
                    type="primary"
                    size="large"
                    icon={<FileTextOutlined style={{ fontSize: 28 }} />}
                    onClick={() => handleAiExport("csv", false)}
                    style={{
                      width: 80,
                      height: 80,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Text style={{ fontSize: 12, fontWeight: 600, marginTop: 4 }}>CSV</Text>
                  </Button>
                </Tooltip>

                {/* JSON 按钮 */}
                <Tooltip title="JSON 格式 - 适合程序处理" placement="top">
                  <Button
                    size="large"
                    icon={<CodeOutlined style={{ fontSize: 28 }} />}
                    onClick={() => handleAiExport("json", false)}
                    style={{
                      width: 80,
                      height: 80,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Text style={{ fontSize: 12, fontWeight: 600, marginTop: 4 }}>JSON</Text>
                  </Button>
                </Tooltip>

                {/* Markdown 按钮 */}
                <Tooltip title="Markdown 格式 - 适合文档分享" placement="top">
                  <Button
                    size="large"
                    icon={<FileMarkdownOutlined style={{ fontSize: 28 }} />}
                    onClick={() => handleAiExport("markdown", false)}
                    style={{
                      width: 80,
                      height: 80,
                      display: "flex",
                      flexDirection: "column",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Text style={{ fontSize: 12, fontWeight: 600, marginTop: 4 }}>MD</Text>
                  </Button>
                </Tooltip>
              </Space>
            </div>

            {/* Ask about exporting all data if result is large */}
            {(queryResult?.rowCount || 0) > 100 && (
              <>
                <Divider style={{ margin: "12px 0" }} />
                <div style={{ textAlign: "center" }}>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    检测到大量数据（{queryResult?.rowCount || 0} 行）
                  </Text>
                  <br />
                  <Button
                    type="link"
                    onClick={() => {
                      setShowExportModal(false);
                      Modal.confirm({
                        title: "导出全部数据",
                        content: `查询结果包含 ${queryResult?.rowCount || 0} 行数据，是否导出全部数据？`,
                        okText: "导出全部",
                        cancelText: "仅导出当前页",
                        onOk: () => handleAiExport("csv", true),
                        onCancel: () => handleAiExport("csv", false),
                      });
                    }}
                    style={{ padding: 0 }}
                  >
                    <Text strong style={{ color: "#16AA98" }}>
                      点击此处导出全部数据 →
                    </Text>
                  </Button>
                </div>
              </>
            )}

            <Divider style={{ margin: "12px 0" }} />

            <Button
              block
              onClick={() => setShowExportModal(false)}
              style={{ fontWeight: 600 }}
            >
              不需要导出
            </Button>
          </Space>
        </Modal>
      </div>
    </div>
  );
};

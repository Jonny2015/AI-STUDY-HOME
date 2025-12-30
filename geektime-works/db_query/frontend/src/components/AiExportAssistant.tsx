/** AI Export Assistant - Proactive export suggestions based on query results. */

import React, { useState, useEffect } from "react";
import { Card, Alert, Button, Space, Typography, Spin, Tag } from "antd";
import {
  BulbOutlined,
  DownloadOutlined,
  CloseOutlined,
  ThunderboltOutlined,
} from "@ant-design/icons";
import { exportService } from "../services/export";

const { Text, Paragraph } = Typography;

interface QueryResult {
  columns: Array<{ name: string; dataType: string }>;
  rows: Array<Record<string, any>>;
  rowCount: number;
}

interface AiExportAssistantProps {
  databaseName: string;
  sqlText: string;
  queryResult: QueryResult;
  onExport: (params: { format: string; scope: string; sql: string }) => void;
  enabled?: boolean;
}

interface IntentAnalysis {
  shouldSuggestExport: boolean;
  confidence: number;
  reasoning: string;
  clarificationNeeded: boolean;
  clarificationQuestion: string | null;
  suggestedFormat: string;
  suggestedScope: string;
}

interface Suggestion {
  suggestionText: string;
  quickActions: Array<{
    type: "export" | "filter" | "clarification" | "transform";
    label: string;
    action: string;
    format?: string;
    scope?: string;
    description?: string;
  }>;
  confidence: number;
  explanation: string;
}

export const AiExportAssistant: React.FC<AiExportAssistantProps> = ({
  databaseName,
  sqlText,
  queryResult,
  onExport,
  enabled = true,
}) => {
  const [loading, setLoading] = useState(false);
  const [suggestion, setSuggestion] = useState<Suggestion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (enabled && !dismissed && queryResult.rowCount > 0) {
      analyzeAndSuggest();
    }
  }, [databaseName, sqlText, queryResult, enabled, dismissed]);

  const analyzeAndSuggest = async () => {
    setLoading(true);
    setError(null);

    try {
      // Step 1: Analyze export intent
      const analysis: IntentAnalysis = await exportService.analyzeExportIntent({
        databaseName,
        sqlText,
        queryResult: {
          columns: queryResult.columns.map((col) => ({
            name: col.name,
            type: col.dataType,
          })),
          rows: queryResult.rows.map((row) =>
            queryResult.columns.map((col) => row[col.name])
          ),
          rowCount: queryResult.rowCount,
        },
      });

      if (!analysis.shouldSuggestExport) {
        setLoading(false);
        return;
      }

      // Step 2: Get proactive suggestion
      const suggestionResult = await exportService.getProactiveSuggestion({
        databaseName,
        sqlText,
        queryResult: {
          columns: queryResult.columns.map((col) => ({
            name: col.name,
            type: col.dataType,
          })),
          rows: queryResult.rows.map((row) =>
            queryResult.columns.map((col) => row[col.name])
          ),
          rowCount: queryResult.rowCount,
        },
        intentAnalysis: analysis,
      });

      setSuggestion(suggestionResult);

      // Track suggestion impression
      await exportService.trackSuggestionResponse({
        databaseName,
        suggestionType: "proactive",
        sqlContext: sqlText,
        rowCount: queryResult.rowCount,
        confidence: analysis.confidence,
        suggestedFormat: analysis.suggestedFormat,
        suggestedScope: analysis.suggestedScope,
        userResponse: "IGNORED",
        suggestedAt: new Date().toISOString(),
      });
    } catch (err: any) {
      console.error("Failed to analyze export intent:", err);
      // Silently fail - don't show error to user as this is a nice-to-have feature
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAction = async (action: any) => {
    if (action.type === "export") {
      // Track acceptance
      if (suggestion) {
        await exportService.trackSuggestionResponse({
          databaseName,
          suggestionType: "proactive",
          sqlContext: sqlText,
          rowCount: queryResult.rowCount,
          confidence: suggestion.confidence,
          suggestedFormat: action.format || "csv",
          suggestedScope: action.scope || "current_page",
          userResponse: "ACCEPTED",
          suggestedAt: new Date().toISOString(),
          respondedAt: new Date().toISOString(),
        });
      }

      // Trigger export
      onExport({
        format: action.format || "csv",
        scope: action.scope || "current_page",
        sql: sqlText,
      });

      setDismissed(true);
    }
  };

  const handleDismiss = async () => {
    // Track rejection
    if (suggestion) {
      await exportService.trackSuggestionResponse({
        databaseName,
        suggestionType: "proactive",
        sqlContext: sqlText,
        rowCount: queryResult.rowCount,
        confidence: suggestion.confidence,
        suggestedFormat: "csv",
        suggestedScope: "current_page",
        userResponse: "REJECTED",
        suggestedAt: new Date().toISOString(),
        respondedAt: new Date().toISOString(),
      });
    }

    setDismissed(true);
  };

  if (!enabled || dismissed || loading) {
    return null;
  }

  if (!suggestion) {
    return null;
  }

  // Calculate confidence color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return "success";
    if (confidence >= 0.6) return "warning";
    return "default";
  };

  return (
    <Card
      size="small"
      style={{
        marginBottom: 16,
        borderLeft: "4px solid #FFDE00",
        backgroundColor: "#FFFBF0",
      }}
    >
      <Space direction="vertical" style={{ width: "100%" }}>
        {/* Header */}
        <Space style={{ width: "100%", justifyContent: "space-between" }}>
          <Space>
            <ThunderboltOutlined style={{ fontSize: 18, color: "#FFDE00" }} />
            <Text strong style={{ fontSize: 13, textTransform: "uppercase" }}>
              AI 导出建议
            </Text>
            <Tag color={getConfidenceColor(suggestion.confidence)}>
              {Math.round(suggestion.confidence * 100)}% 匹配
            </Tag>
          </Space>
          <Button
            type="text"
            size="small"
            icon={<CloseOutlined />}
            onClick={handleDismiss}
          />
        </Space>

        {/* Suggestion Text */}
        <Paragraph style={{ margin: 0, fontSize: 14 }}>
          <BulbOutlined style={{ marginRight: 8, color: "#FFA940" }} />
          {suggestion.suggestionText}
        </Paragraph>

        {/* Quick Actions */}
        {suggestion.quickActions && suggestion.quickActions.length > 0 && (
          <Space wrap>
            {suggestion.quickActions.map((action, index) => (
              <Button
                key={index}
                type={action.type === "export" ? "primary" : "default"}
                size="small"
                icon={action.type === "export" ? <DownloadOutlined /> : undefined}
                onClick={() => handleQuickAction(action)}
                style={{
                  fontWeight: 600,
                  fontSize: 12,
                }}
              >
                {action.label}
                {action.description && (
                  <Text type="secondary" style={{ marginLeft: 4, fontSize: 11 }}>
                    • {action.description}
                  </Text>
                )}
              </Button>
            ))}
          </Space>
        )}

        {/* Explanation */}
        {suggestion.explanation && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            {suggestion.explanation}
          </Text>
        )}
      </Space>
    </Card>
  );
};

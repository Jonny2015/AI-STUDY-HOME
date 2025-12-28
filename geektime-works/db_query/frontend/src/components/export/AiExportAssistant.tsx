import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, Space, Typography, Alert, Spin, Divider, Modal, App } from 'antd';
import { ExportOutlined, CloseOutlined, FilterOutlined, QuestionCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import type { ExportFormat, ExportScope } from '@/types/export';

const { Title, Text, Paragraph } = Typography;

interface QueryResult {
  columns: Array<{
    name: string;
    type: string;
  }>;
  rows: any[][];
  rowCount: number;
}

interface QuickAction {
  type: 'export' | 'filter' | 'clarification' | 'transform';
  label: string;
  action: string;
  format?: string;
  scope?: string;
  description?: string;
}

interface SuggestionData {
  suggestionText: string;
  quickActions: QuickAction[];
  confidence: number;
  explanation: string;
}

interface ExportIntent {
  shouldSuggestExport: boolean;
  confidence: number;
  reasoning: string;
  clarificationNeeded: boolean;
  clarificationQuestion: string | null;
  suggestedFormat: ExportFormat;
  suggestedScope: ExportScope;
}

interface AiExportAssistantProps {
  databaseName: string;
  sqlText: string;
  queryResult: QueryResult;
  onExport: (params: {
    format: ExportFormat;
    scope: ExportScope;
    sql: string;
  }) => void;
  enabled?: boolean;
  onClose?: () => void;
}

const AiExportAssistant: React.FC<AiExportAssistantProps> = ({
  databaseName,
  sqlText,
  queryResult,
  onExport,
  enabled = true,
  onClose
}) => {
  const { message } = App.useApp();
  const [loading, setLoading] = useState(false);
  const [intentAnalysis, setIntentAnalysis] = useState<ExportIntent | null>(null);
  const [suggestion, setSuggestion] = useState<SuggestionData | null>(null);
  const [showClarification, setShowClarification] = useState(false);
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat | null>(null);
  const [suggestionId, setSuggestionId] = useState<string | null>(null);
  const [showTime, setShowTime] = useState<Date | null>(null);

  // Analyze export intent when component mounts
  useEffect(() => {
    if (!enabled) {
      return;
    }

    analyzeExportIntent();
  }, [databaseName, sqlText, queryResult, enabled]);

  const analyzeExportIntent = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/export/analyze-intent', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          databaseName: databaseName,
          sqlText: sqlText,
          queryResult: queryResult
        })
      });

      if (!response.ok) {
        if (response.status === 404 || response.status === 204) {
          // No export needed
          setIntentAnalysis(null);
          return;
        }
        throw new Error(`Failed to analyze export intent: ${response.statusText}`);
      }

      const data = await response.json();
      setIntentAnalysis(data);

      // If export is suggested, get proactive suggestion
      if (data.shouldSuggestExport && !data.clarificationNeeded) {
        await getProactiveSuggestion(data);
      } else if (data.clarificationNeeded) {
        setShowClarification(true);
      }
    } catch (error) {
      console.error('Error analyzing export intent:', error);
      message.error('AI分析失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  }, [databaseName, sqlText, queryResult]);

  const getProactiveSuggestion = useCallback(async (intent: ExportIntent) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/export/proactive-suggestion', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          databaseName: databaseName,
          sqlText: sqlText,
          queryResult: queryResult,
          intentAnalysis: intent
        })
      });

      if (!response.ok) {
        if (response.status === 204) {
          setSuggestion(null);
          return;
        }
        throw new Error(`Failed to get suggestion: ${response.statusText}`);
      }

      const data = await response.json();
      setSuggestion(data);
      setShowTime(new Date());
    } catch (error) {
      console.error('Error getting proactive suggestion:', error);
      message.error('建议生成失败');
    } finally {
      setLoading(false);
    }
  }, [databaseName, sqlText, queryResult]);

  const handleQuickAction = useCallback(async (action: QuickAction) => {
    if (!suggestionId || !showTime) {
      // Generate new suggestion ID if not exists
      setSuggestionId(`suggestion-${Date.now()}`);
    }

    const currentSuggestionId = suggestionId || `suggestion-${Date.now()}`;
    const responseTime = showTime ? Date.now() - showTime.getTime() : 0;

    // Track user response
    try {
      await fetch('/api/v1/export/track-response', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          suggestionId: currentSuggestionId,
          databaseName: databaseName,
          suggestionType: 'PROACTIVE_SUGGESTION',
          sqlContext: sqlText,
          rowCount: queryResult.rowCount,
          confidence: suggestion?.confidence || 0,
          suggestedFormat: action.format || intentAnalysis?.suggestedFormat,
          suggestedScope: action.scope || intentAnalysis?.suggestedScope,
          userResponse: action.type === 'export' ? 'ACCEPTED' : 'IGNORED',
          responseTimeMs: responseTime,
          suggestedAt: showTime?.toISOString(),
          respondedAt: new Date().toISOString()
        })
      });
    } catch (error) {
      console.error('Error tracking response:', error);
    }

    // Handle action
    switch (action.type) {
      case 'export':
        if (action.format && action.scope) {
          onExport({
            format: action.format as ExportFormat,
            scope: action.scope as ExportScope,
            sql: sqlText
          });
          onClose?.();
        }
        break;
      case 'filter':
        // Handle filter action - could open a filter dialog
        Modal.info({
          title: '筛选导出',
          content: action.description || '请设置筛选条件后导出',
        });
        break;
      case 'clarification':
        if (action.value) {
          setSelectedFormat(action.value as ExportFormat);
          setShowClarification(true);
        }
        break;
    }
  }, [action, databaseName, sqlText, queryResult, suggestionId, showTime, suggestion, intentAnalysis, onExport, onClose]);

  const handleClarificationSubmit = useCallback((format: ExportFormat) => {
    if (intentAnalysis) {
      const updatedIntent = {
        ...intentAnalysis,
        clarificationNeeded: false,
        suggestedFormat: format
      };
      setIntentAnalysis(updatedIntent);
      getProactiveSuggestion(updatedIntent);
      setShowClarification(false);
      setSelectedFormat(null);
    }
  }, [intentAnalysis, getProactiveSuggestion]);

  const handleClose = useCallback(() => {
    if (suggestionId && showTime) {
      // Track as ignored
      const responseTime = Date.now() - showTime.getTime();

      fetch('/api/v1/export/track-response', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          suggestionId: suggestionId,
          databaseName: databaseName,
          suggestionType: 'PROACTIVE_SUGGESTION',
          sqlContext: sqlText,
          rowCount: queryResult.rowCount,
          confidence: suggestion?.confidence || 0,
          suggestedFormat: intentAnalysis?.suggestedFormat,
          suggestedScope: intentAnalysis?.suggestedScope,
          userResponse: 'IGNORED',
          responseTimeMs: responseTime,
          suggestedAt: showTime?.toISOString(),
          respondedAt: new Date().toISOString()
        })
      }).catch(error => console.error('Error tracking response:', error));
    }

    onClose?.();
  }, [suggestionId, showTime, databaseName, sqlText, queryResult, suggestion, intentAnalysis, onClose]);

  if (!enabled) {
    return null;
  }

  if (loading) {
    return (
      <Card
        size="small"
        style={{
          marginBottom: 16,
          borderLeft: '4px solid #1890ff',
          background: '#f0f8ff'
        }}
      >
        <div style={{ textAlign: 'center', padding: 20 }}>
          <Spin size="large" />
          <div style={{ marginTop: 16 }}>
            <Text>AI分析中...</Text>
          </div>
        </div>
      </Card>
    );
  }

  if (!intentAnalysis || !intentAnalysis.shouldSuggestExport) {
    return null;
  }

  return (
    <Card
      size="small"
      style={{
        marginBottom: 16,
        borderLeft: '4px solid #52c41a',
        background: '#f6ffed'
      }}
      extra={
        <Button
          type="text"
          size="small"
          icon={<CloseOutlined />}
          onClick={handleClose}
          style={{ color: '#666' }}
        />
      }
    >
      {showClarification && intentAnalysis.clarificationQuestion && (
        <div style={{ marginBottom: 16 }}>
          <Alert
            type="info"
            message={
              <div>
                <Text strong>{intentAnalysis.clarificationQuestion}</Text>
              </div>
            }
            action={
              <Space>
                <Button
                  size="small"
                  type="primary"
                  onClick={() => handleClarificationSubmit(selectedFormat || intentAnalysis.suggestedFormat)}
                >
                  确认
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    setShowClarification(false);
                    setSelectedFormat(null);
                  }}
                >
                  取消
                </Button>
              </Space>
            }
          />
        </div>
      )}

      {suggestion && (
        <>
          <div style={{ marginBottom: 16 }}>
            <Paragraph style={{ marginBottom: 0 }}>
              <Text>{suggestion.suggestionText}</Text>
            </Paragraph>
            <div style={{ marginTop: 8 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                {suggestion.explanation}
              </Text>
            </div>
          </div>

          <Divider style={{ margin: '12px 0' }} />

          <Space wrap>
            {suggestion.quickActions.map((action, index) => {
              let buttonType: 'primary' | 'default' = 'primary';
              let icon: React.ReactNode = null;

              switch (action.type) {
                case 'export':
                  icon = <ExportOutlined />;
                  break;
                case 'filter':
                  icon = <FilterOutlined />;
                  buttonType = 'default';
                  break;
                case 'clarification':
                  icon = <QuestionCircleOutlined />;
                  buttonType = 'default';
                  break;
                case 'transform':
                  icon = <CheckCircleOutlined />;
                  buttonType = 'default';
                  break;
              }

              return (
                <Button
                  key={index}
                  type={buttonType}
                  size="small"
                  icon={icon}
                  onClick={() => handleQuickAction(action)}
                  title={action.description}
                >
                  {action.label}
                </Button>
              );
            })}
          </Space>

          <div style={{ marginTop: 12 }}>
            <Text type="secondary" style={{ fontSize: 11 }}>
              置信度: {(suggestion.confidence * 100).toFixed(0)}%
            </Text>
          </div>
        </>
      )}
    </Card>
  );
};

export default AiExportAssistant;
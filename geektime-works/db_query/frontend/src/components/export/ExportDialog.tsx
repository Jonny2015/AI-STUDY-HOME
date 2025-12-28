/**
 * 导出配置对话框组件
 * 实现导出格式选择、导出范围选择、预估文件大小显示
 */

import React, { useState, useEffect } from 'react';
import { Modal, Form, Select, Radio, Button, Alert, Space, Divider, Typography, Row, Col } from 'antd';
import { ExportFormat, ExportScope } from '@/types/export';
import { useExportService } from '@/services/export';
import type { ExportRequest } from '@/types/export';

const { Option } = Select;
const { RadioGroup } = Radio;
const { Text, Paragraph } = Typography;

interface ExportDialogProps {
  visible: boolean;
  onOk: (request: ExportRequest) => void;
  onCancel: () => void;
  sql: string;
  databaseName: string;
  totalRows?: number;
  hasMoreData?: boolean;
}

export const ExportDialog: React.FC<ExportDialogProps> = ({
  visible,
  onOk,
  onCancel,
  sql,
  databaseName,
  totalRows = 0,
  hasMoreData = false,
}) => {
  const [form] = Form.useForm<ExportRequest>();
  const { checkExportSize, loading: checkingSize } = useExportService();
  const [sizeCheckResult, setSizeCheckResult] = useState<{
    estimatedBytes: number;
    estimatedMb: number;
    bytesPerRow: number;
    method: string;
    confidence: number;
    warningMessage: string | null;
    shouldProceed: boolean;
  } | null>(null);
  const [hasSizeWarning, setHasSizeWarning] = useState(false);

  // 格式选项
  const formatOptions = [
    {
      value: ExportFormat.CSV,
      label: 'CSV',
      description: '逗号分隔值文件，兼容 Excel 和其他工具',
      icon: '📊',
      extension: 'csv',
      mimeType: 'text/csv',
    },
    {
      value: ExportFormat.JSON,
      label: 'JSON',
      description: 'JSON 格式，适合程序处理和 API 集成',
      icon: '{ }',
      extension: 'json',
      mimeType: 'application/json',
    },
    {
      value: ExportFormat.MARKDOWN,
      label: 'Markdown',
      description: 'Markdown 表格格式，适合文档和报告',
      icon: '📝',
      extension: 'md',
      mimeType: 'text/markdown',
    },
  ];

  // 范围选项
  const scopeOptions = [
    {
      value: ExportScope.CURRENT_PAGE,
      label: '当前页数据',
      description: '只导出当前页显示的数据',
      rows: totalRows > 0 ? Math.min(totalRows, 100) : 0,
    },
    {
      value: ExportScope.ALL_DATA,
      label: '全部数据',
      description: hasMoreData ? '导出所有符合条件的记录（可能包含更多数据）' : '导出所有记录',
      rows: totalRows > 0 ? totalRows : '全部',
    },
  ];

  // 检查文件大小
  const handleCheckSize = async () => {
    if (!sql || !databaseName) return;

    try {
      const result = await checkExportSize(databaseName, sql, format, scope);
      setSizeCheckResult(result);

      // 检查是否有警告
      const hasWarning = result.warningMessage && !result.shouldProceed;
      const isLargeFile = result.estimatedMb > 50;
      const isUncertain = result.confidence < 0.5;

      setHasSizeWarning(hasWarning || isLargeFile || isUncertain);
    } catch (error) {
      console.error('检查文件大小失败:', error);
      setSizeCheckResult(null);
      setHasSizeWarning(false);
    }
  };

  // 当格式或范围改变时重新检查大小
  const format = Form.useWatch('format', form);
  const scope = Form.useWatch('scope', form);

  useEffect(() => {
    if (visible && format && scope) {
      // 延迟检查，避免频繁调用
      const timer = setTimeout(handleCheckSize, 500);
      return () => clearTimeout(timer);
    }
  }, [format, scope, visible]);

  // 选择格式选项
  const handleFormatChange = (value: ExportFormat) => {
    form.setFieldsValue({ format: value });
  };

  // 确认导出
  const handleOk = async () => {
    try {
      const values = await form.validateFields();
      onOk(values);
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // 获取置信度描述
  const getConfidenceDescription = (confidence: number): string => {
    if (confidence >= 0.8) return '高';
    if (confidence >= 0.5) return '中等';
    return '低';
  };

  return (
    <Modal
      title={
        <Space>
          <span>导出数据</span>
          {totalRows > 0 && (
            <Text type="secondary">({totalRows} 条记录)</Text>
          )}
        </Space>
      }
      open={visible}
      onOk={handleOk}
      onCancel={onCancel}
      width={640}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button
          key="check"
          type="default"
          onClick={handleCheckSize}
          loading={checkingSize}
          disabled={!format || !scope}
        >
          检查大小
        </Button>,
        <Button
          key="ok"
          type="primary"
          onClick={handleOk}
          disabled={!format || !scope}
          loading={checkingSize}
        >
          开始导出
        </Button>,
      ]}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{
          format: ExportFormat.CSV,
          scope: ExportScope.CURRENT_PAGE,
        }}
      >
        <Form.Item
          name="format"
          label="选择导出格式"
          rules={[{ required: true, message: '请选择导出格式' }]}
        >
          <RadioGroup>
            <Row gutter={[16, 16]}>
              {formatOptions.map((option) => (
                <Col span={8} key={option.value}>
                  <Radio
                    value={option.value}
                    className="export-format-option"
                  >
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 24, marginBottom: 8 }}>
                        {option.icon}
                      </div>
                      <div>{option.label}</div>
                      <div style={{ fontSize: 12, color: '#666' }}>
                        {option.description}
                      </div>
                    </div>
                  </Radio>
                </Col>
              ))}
            </Row>
          </RadioGroup>
        </Form.Item>

        <Form.Item
          name="scope"
          label="选择导出范围"
          rules={[{ required: true, message: '请选择导出范围' }]}
        >
          <RadioGroup>
            <Row gutter={[16, 16]}>
              {scopeOptions.map((option) => (
                <Col span={12} key={option.value}>
                  <Radio value={option.value}>
                    <div>
                      <div>{option.label}</div>
                      <div style={{ fontSize: 12, color: '#666' }}>
                        {option.description}
                      </div>
                      <div style={{ fontSize: 12, color: '#999' }}>
                        {option.rows} 条记录
                      </div>
                    </div>
                  </Radio>
                </Col>
              ))}
            </Row>
          </RadioGroup>
        </Form.Item>

        <Divider />

        {/* 文件大小预估 */}
        {sizeCheckResult && (
          <Form.Item>
            <Alert
              type={hasSizeWarning ? 'warning' : 'info'}
              showIcon
              style={{ marginBottom: 16 }}
            >
              <div>
                <Text strong>
                  预估文件大小: {formatFileSize(sizeCheckResult.estimatedBytes)}
                  ({sizeCheckResult.estimatedMb} MB)
                </Text>
                <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                  <Row gutter={16}>
                    <Col span={12}>
                      <Text>估算方法: {sizeCheckResult.method}</Text>
                    </Col>
                    <Col span={12}>
                      <Text>
                        置信度: {getConfidenceDescription(sizeCheckResult.confidence)}
                        ({Math.round(sizeCheckResult.confidence * 100)}%)
                      </Text>
                    </Col>
                  </Row>
                  <div style={{ marginTop: 4 }}>
                    平均每行: {formatFileSize(sizeCheckResult.bytesPerRow)}
                  </div>
                </div>
              </div>
            </Alert>

            {sizeCheckResult.warningMessage && (
              <Alert
                type="warning"
                showIcon
                message="注意"
                description={sizeCheckResult.warningMessage}
                style={{ marginBottom: 16 }}
              />
            )}

            {hasSizeWarning && (
              <Alert
                type="error"
                showIcon
                message="确认导出"
                description={
                  <div>
                    <div>导出文件较大或估算不确定，请确认是否继续导出？</div>
                    <div style={{ marginTop: 8 }}>
                      建议：
                      <ul style={{ margin: 0, paddingLeft: 20 }}>
                        <li>选择当前页数据范围</li>
                        <li>使用 CSV 格式（文件最小）</li>
                        <li>分批导出数据</li>
                      </ul>
                    </div>
                  </div>
                }
                style={{ marginBottom: 16 }}
              />
            )}
          </Form.Item>
        )}

        {/* 导出提示 */}
        <Alert
          type="info"
          showIcon
          message="导出提示"
          description={
            <div>
              <p>• 导出过程可能需要一些时间，请耐心等待</p>
              <p>• 大数据量导出建议在服务器负载较低时进行</p>
              <p>• 导出文件将在完成后自动下载</p>
              {hasMoreData && (
                <p style={{ color: '#fa8c16' }}>
                  • 注意：全部数据包含更多记录，实际文件大小可能大于预估
                </p>
              )}
            </div>
          }
        />
      </Form>
    </Modal>
  );
};
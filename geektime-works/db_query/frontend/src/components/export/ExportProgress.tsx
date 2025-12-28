/**
 * 导出进度显示组件
 * 实现进度条、百分比显示、取消按钮、完成提示
 */

import React, { useState, useEffect } from 'react';
import { Modal, Progress, Button, Alert, Space, Typography, Divider, Row, Col } from 'antd';
import { ExportFormat, ExportScope } from '@/types/export';
import { useExportService } from '@/services/export';
import type { TaskResponse } from '@/types/export';
import { DownloadOutlined, CloseOutlined, ReloadOutlined } from '@ant-design/icons';

const { Text, Paragraph } = Typography;

interface ExportProgressProps {
  visible: boolean;
  taskId: string;
  onCancel: () => void;
  onComplete: (fileUrl: string, fileName: string) => void;
  onError: (error: string) => void;
}

export const ExportProgress: React.FC<ExportProgressProps> = ({
  visible,
  taskId,
  onCancel,
  onComplete,
  onError,
}) => {
  const { getTaskStatus, cancelTask, downloadFile, loading } = useExportService();
  const [taskInfo, setTaskInfo] = useState<TaskResponse | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<'pending' | 'running' | 'completed' | 'failed' | 'cancelled'>('pending');
  const [pollingInterval, setPollingInterval] = useState<NodeJS.Timeout | null>(null);

  // 轮询任务状态
  const pollTaskStatus = async () => {
    try {
      const response = await getTaskStatus(taskId);
      setTaskInfo(response);
      setProgress(response.progress);
      setStatus(response.status.toLowerCase());

      if (response.status === 'COMPLETED') {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        handleComplete(response);
      } else if (response.status === 'FAILED') {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        handleError(response.error || '导出失败');
      }
    } catch (error) {
      console.error('获取任务状态失败:', error);
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
      handleError('获取任务状态失败');
    }
  };

  // 开始轮询
  useEffect(() => {
    if (visible && taskId) {
      // 立即查询一次
      pollTaskStatus();

      // 设置轮询间隔（1秒）
      const interval = setInterval(pollTaskStatus, 1000);
      setPollingInterval(interval);

      return () => {
        if (interval) {
          clearInterval(interval);
        }
      };
    }
  }, [visible, taskId]);

  // 处理完成
  const handleComplete = async (response: TaskResponse) => {
    if (response.fileUrl) {
      try {
        // 下载文件
        const blob = await downloadFile(response.fileUrl);
        const fileName = extractFileName(response.fileUrl);

        // 创建下载链接
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();

        // 清理
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        onComplete(response.fileUrl, fileName);
      } catch (error) {
        console.error('下载文件失败:', error);
        onError('下载文件失败');
      }
    }
  };

  // 处理错误
  const handleError = (error: string) => {
    onError(error);
    setStatus('failed');
  };

  // 取消任务
  const handleCancel = async () => {
    try {
      await cancelTask(taskId);
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
      setStatus('cancelled');
      onCancel();
    } catch (error) {
      console.error('取消任务失败:', error);
      onError('取消任务失败');
    }
  };

  // 重试导出
  const handleRetry = () => {
    setStatus('pending');
    setProgress(0);
    setTaskInfo(null);
    onCancel();
    // 这里应该触发重新导出，由父组件处理
  };

  // 获取状态描述
  const getStatusDescription = (status: string): string => {
    switch (status) {
      case 'PENDING':
        return '等待开始';
      case 'RUNNING':
        return '导出中';
      case 'COMPLETED':
        return '导出完成';
      case 'FAILED':
        return '导出失败';
      case 'CANCELLED':
        return '已取消';
      default:
        return '未知状态';
    }
  };

  // 获取状态颜色
  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'PENDING':
        return 'default';
      case 'RUNNING':
        return 'processing';
      case 'COMPLETED':
        return 'success';
      case 'FAILED':
        return 'error';
      case 'CANCELLED':
        return 'warning';
      default:
        return 'default';
    }
  };

  // 获取文件格式图标
  const getFormatIcon = (format: string): string => {
    switch (format) {
      case 'CSV':
        return '📊';
      case 'JSON':
        return '{ }';
      case 'MARKDOWN':
        return '📝';
      default:
        return '📄';
    }
  };

  // 从 URL 提取文件名
  const extractFileName = (url: string): string => {
    try {
      const urlObj = new URL(url);
      const pathname = urlObj.pathname;
      const filename = pathname.split('/').pop() || 'export';

      // 获取文件扩展名
      const ext = filename.split('.').pop();
      if (!ext) {
        // 根据文件类型添加扩展名
        switch (taskInfo?.exportFormat) {
          case 'CSV':
            return `${filename}.csv`;
          case 'JSON':
            return `${filename}.json`;
          case 'MARKDOWN':
            return `${filename}.md`;
          default:
            return filename;
        }
      }
      return filename;
    } catch (error) {
      return 'export.csv';
    }
  };

  // 格式化文件大小
  const formatFileSize = (bytes?: number): string => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (!visible) return null;

  const isCompleted = status === 'completed';
  const isFailed = status === 'failed';
  const isCancelled = status === 'cancelled';

  return (
    <Modal
      title={
        <Space>
          <span>导出进度</span>
          {taskInfo && (
            <Text type="secondary">
              {getFormatIcon(taskInfo.exportFormat)} {taskInfo.exportFormat}
            </Text>
          )}
        </Space>
      }
      open={visible}
      onCancel={isCompleted || isFailed || isCancelled ? undefined : onCancel}
      footer={null}
      width={500}
      closable={isCompleted || isFailed || isCancelled}
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 状态显示 */}
        <Row align="middle" gutter={16}>
          <Col span={12}>
            <Text strong>状态:</Text>
          </Col>
          <Col span={12}>
            <Text type={status === 'running' ? 'processing' : undefined}>
              {getStatusDescription(status.toUpperCase())}
            </Text>
          </Col>
        </Row>

        {/* 进度条 */}
        <Progress
          percent={progress}
          status={getStatusColor(status)}
          strokeColor={{
            '0%': '#108ee9',
            '100%': '#87d068',
          }}
          showInfo
        />

        {/* 任务信息 */}
        {taskInfo && (
          <>
            <Divider />

            <Row gutter={16}>
              <Col span={12}>
                <Text strong>文件名:</Text>
              </Col>
              <Col span={12}>
                <Text>{extractFileName(taskInfo.fileUrl || '')}</Text>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Text strong>导出格式:</Text>
              </Col>
              <Col span={12}>
                <Text>{taskInfo.exportFormat}</Text>
              </Col>
            </Row>

            <Row gutter={16}>
              <Col span={12}>
                <Text strong>导出范围:</Text>
              </Col>
              <Col span={12}>
                <Text>{taskInfo.exportScope}</Text>
              </Col>
            </Row>

            {taskInfo.rowCount && (
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>记录数:</Text>
                </Col>
                <Col span={12}>
                  <Text>{taskInfo.rowCount.toLocaleString()}</Text>
                </Col>
              </Row>
            )}

            {taskInfo.fileSizeBytes && (
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>文件大小:</Text>
                </Col>
                <Col span={12}>
                  <Text>{formatFileSize(taskInfo.fileSizeBytes)}</Text>
                </Col>
              </Row>
            )}

            {taskInfo.executionTimeMs && (
              <Row gutter={16}>
                <Col span={12}>
                  <Text strong>执行时间:</Text>
                </Col>
                <Col span={12}>
                  <Text>{(taskInfo.executionTimeMs / 1000).toFixed(2)} 秒</Text>
                </Col>
              </Row>
            )}
          </>
        )}

        {/* 操作按钮 */}
        <Divider />

        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          {isCompleted && (
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              onClick={() => {
                if (taskInfo?.fileUrl) {
                  window.open(taskInfo.fileUrl, '_blank');
                }
              }}
            >
              打开文件
            </Button>
          )}

          {isFailed && (
            <Button
              type="primary"
              icon={<ReloadOutlined />}
              onClick={handleRetry}
            >
              重新导出
            </Button>
          )}

          {!isCompleted && !isFailed && !isCancelled && (
            <Button
              danger
              icon={<CloseOutlined />}
              onClick={handleCancel}
              loading={loading}
            >
              取消导出
            </Button>
          )}

          {(isCompleted || isFailed || isCancelled) && (
            <Button type="default" onClick={() => onCancel()}>
              关闭
            </Button>
          )}
        </Space>

        {/* 错误信息 */}
        {taskInfo?.error && (
          <Alert
            type="error"
            message="错误信息"
            description={taskInfo.error}
            showIcon
            style={{ marginTop: 16 }}
          />
        )}

        {/* 完成提示 */}
        {isCompleted && (
          <Alert
            type="success"
            message="导出完成"
            description="文件已成功导出并自动下载"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}

        {/* 取消提示 */}
        {isCancelled && (
          <Alert
            type="warning"
            message="导出已取消"
            description="导出任务已成功取消"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Space>
    </Modal>
  );
};
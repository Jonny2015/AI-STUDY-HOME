/**
 * 导出按钮组件单元测试
 * 验证点击事件和格式选择逻辑
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ExportButton } from '@/components/query/ExportButton';
import { ExportFormat, ExportScope } from '@/types/export';

// Mock API services
jest.mock('@/services/export', () => ({
  createExport: jest.fn(),
  checkExportSize: jest.fn(),
  getTaskStatus: jest.fn(),
  cancelTask: jest.fn(),
  downloadFile: jest.fn(),
}));

const mockCreateExport = jest.requireMock('@/services/export').createExport;
const mockCheckExportSize = jest.requireMock('@/services/export').checkExportSize;
const mockGetTaskStatus = jest.requireMock('@/services/export').getTaskStatus;

describe('ExportButton', () => {
  const mockOnExportComplete = jest.fn();
  const mockOnError = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
    mockCreateExport.mockResolvedValue({ taskId: 'task-123' });
    mockCheckExportSize.mockResolvedValue({
      estimatedBytes: 1024000,
      estimatedMb: 1,
      warningMessage: null,
      shouldProceed: true,
    });
    mockGetTaskStatus.mockResolvedValue({
      taskId: 'task-123',
      status: 'COMPLETED' as const,
      progress: 100,
      fileUrl: '/api/v1/exports/download/test.csv',
      error: null,
    });
  });

  describe('基本渲染和交互', () => {
    it('应该正确渲染导出按钮', () => {
      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      const button = screen.getByRole('button', { name: /导出/i });
      expect(button).toBeInTheDocument();
      expect(button).toBeEnabled();
    });

    it('当没有 SQL 时应该禁用按钮', () => {
      render(
        <ExportButton
          sql=""
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      const button = screen.getByRole('button', { name: /导出/i });
      expect(button).toBeDisabled();
      expect(screen.getByText('无数据可导出')).toBeInTheDocument();
    });

    it('当没有数据库名称时应该禁用按钮', () => {
      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName=""
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      const button = screen.getByRole('button', { name: /导出/i });
      expect(button).toBeDisabled();
    });

    it('点击按钮应该显示格式选择下拉菜单', async () => {
      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      const button = screen.getByRole('button', { name: /导出/i });
      fireEvent.click(button);

      await waitFor(() => {
        expect(screen.getByText('CSV')).toBeInTheDocument();
        expect(screen.getByText('JSON')).toBeInTheDocument();
        expect(screen.getByText('Markdown')).toBeInTheDocument();
      });
    });
  });

  describe('格式选择', () => {
    it('选择 CSV 格式应该触发导出流程', async () => {
      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      // 点击按钮打开下拉菜单
      fireEvent.click(screen.getByRole('button', { name: /导出/i }));

      // 选择 CSV 格式
      const csvOption = await screen.findByText('CSV');
      fireEvent.click(csvOption);

      // 验证 createExport 被调用
      await waitFor(() => {
        expect(mockCreateExport).toHaveBeenCalledWith(
          'test_db',
          'SELECT * FROM users',
          ExportFormat.CSV,
          ExportScope.CURRENT_PAGE
        );
      });
    });

    it('选择 JSON 格式应该触发导出流程', async () => {
      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      // 点击按钮打开下拉菜单
      fireEvent.click(screen.getByRole('button', { name: /导出/i }));

      // 选择 JSON 格式
      const jsonOption = await screen.findByText('JSON');
      fireEvent.click(jsonOption);

      // 验证 createExport 被调用
      await waitFor(() => {
        expect(mockCreateExport).toHaveBeenCalledWith(
          'test_db',
          'SELECT * FROM users',
          ExportFormat.JSON,
          ExportScope.CURRENT_PAGE
        );
      });
    });

    it('选择 Markdown 格式应该触发导出流程', async () => {
      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      // 点击按钮打开下拉菜单
      fireEvent.click(screen.getByRole('button', { name: /导出/i }));

      // 选择 Markdown 格式
      const mdOption = await screen.findByText('Markdown');
      fireEvent.click(mdOption);

      // 验证 createExport 被调用
      await waitFor(() => {
        expect(mockCreateExport).toHaveBeenCalledWith(
          'test_db',
          'SELECT * FROM users',
          ExportFormat.MARKDOWN,
          ExportScope.CURRENT_PAGE
        );
      });
    });
  });

  describe('导出流程', () => {
    it('成功完成导出应该调用 onExportComplete', async () => {
      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      // 模拟任务完成
      mockGetTaskStatus.mockResolvedValueOnce({
        taskId: 'task-123',
        status: 'COMPLETED' as const,
        progress: 100,
        fileUrl: '/api/v1/exports/download/test.csv',
        error: null,
      });

      // 点击按钮选择 CSV 格式
      fireEvent.click(screen.getByRole('button', { name: /导出/i }));
      fireEvent.click(await screen.findByText('CSV'));

      // 验证 onExportComplete 被调用
      await waitFor(() => {
        expect(mockOnExportComplete).toHaveBeenCalledWith('task-123', 'test.csv');
      });
    });

    it('导出失败应该调用 onError', async () => {
      mockCreateExport.mockRejectedValue(new Error('导出失败'));

      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      // 点击按钮选择 CSV 格式
      fireEvent.click(screen.getByRole('button', { name: /导出/i }));
      fireEvent.click(await screen.findByText('CSV'));

      // 验证 onError 被调用
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith('导出失败');
      });
    });

    it('文件大小警告应该显示确认对话框', async () => {
      mockCheckExportSize.mockResolvedValue({
        estimatedBytes: 150 * 1024 * 1024, // 150MB
        estimatedMb: 150,
        warningMessage: '文件大小超过限制',
        shouldProceed: false,
      });

      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      // 模拟用户确认对话框
      window.confirm = jest.fn().mockReturnValue(false);

      // 点击按钮选择 CSV 格式
      fireEvent.click(screen.getByRole('button', { name: /导出/i }));
      fireEvent.click(await screen.findByText('CSV'));

      // 验证导出被取消
      await waitFor(() => {
        expect(mockCreateExport).not.toHaveBeenCalled();
      });
    });

    it('应该处理并发限制错误', async () => {
      mockCreateExport.mockRejectedValue(new Error('并发任务数超过限制'));

      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      // 点击按钮选择 CSV 格式
      fireEvent.click(screen.getByRole('button', { name: /导出/i }));
      fireEvent.click(await screen.findByText('CSV'));

      // 验证错误处理
      await waitFor(() => {
        expect(mockOnError).toHaveBeenCalledWith('并发任务数超过限制');
      });
    });
  });

  describe('加载状态', () => {
    it('导出过程中应该显示加载状态', async () => {
      // 模拟长时间运行的导出
      mockGetTaskStatus.mockImplementation(async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return {
          taskId: 'task-123',
          status: 'RUNNING' as const,
          progress: 50,
          fileUrl: null,
          error: null,
        };
      });

      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      // 点击按钮选择 CSV 格式
      fireEvent.click(screen.getByRole('button', { name: /导出/i }));
      fireEvent.click(await screen.findByText('CSV'));

      // 验证按钮被禁用
      expect(screen.getByRole('button', { name: /导出/i })).toBeDisabled();
      expect(screen.getByText('导出中...')).toBeInTheDocument();
    });

    it('应该支持取消导出', async () => {
      let cancelTaskCalled = false;
      jest.spyOn(require('@/services/export'), 'cancelTask').mockImplementation(() => {
        cancelTaskCalled = true;
        return Promise.resolve(true);
      });

      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      // 模拟导出进行中
      mockGetTaskStatus.mockResolvedValue({
        taskId: 'task-123',
        status: 'RUNNING' as const,
        progress: 50,
        fileUrl: null,
        error: null,
      });

      // 点击按钮选择 CSV 格式
      fireEvent.click(screen.getByRole('button', { name: /导出/i }));
      fireEvent.click(await screen.findByText('CSV'));

      // 取消导出
      fireEvent.click(screen.getByText('取消导出'));

      await waitFor(() => {
        expect(cancelTaskCalled).toBe(true);
      });
    });
  });

  describe('无数据场景', () => {
    it('查询结果为空时应该显示提示', () => {
      render(
        <ExportButton
          sql="SELECT * FROM users WHERE 1=0"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      const button = screen.getByRole('button', { name: /导出/i });
      expect(button).toBeDisabled();
      expect(screen.getByText('无数据可导出')).toBeInTheDocument();
    });

    it('应该处理大文件警告', async () => {
      mockCheckExportSize.mockResolvedValue({
        estimatedBytes: 95 * 1024 * 1024, // 95MB
        estimatedMb: 95,
        warningMessage: '接近文件大小限制',
        shouldProceed: true,
      });

      window.confirm = jest.fn().mockReturnValue(true);

      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      // 点击按钮选择 CSV 格式
      fireEvent.click(screen.getByRole('button', { name: /导出/i }));
      fireEvent.click(await screen.findByText('CSV'));

      // 验证确认对话框被调用
      expect(window.confirm).toHaveBeenCalledWith(
        expect.stringContaining('接近文件大小限制')
      );
    });
  });

  describe('无障碍性', () => {
    it('应该支持键盘导航', () => {
      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      const button = screen.getByRole('button', { name: /导出/i });

      // 测试 Enter 键
      fireEvent.keyDown(button, { key: 'Enter' });
      expect(screen.getByText('CSV')).toBeInTheDocument();

      // 测试 Escape 键关闭菜单
      fireEvent.keyDown(button, { key: 'Escape' });
      expect(screen.queryByText('CSV')).not.toBeInTheDocument();
    });

    it('应该有正确的 ARIA 属性', () => {
      render(
        <ExportButton
          sql="SELECT * FROM users"
          databaseName="test_db"
          onExportComplete={mockOnExportComplete}
          onError={mockOnError}
        />
      );

      const button = screen.getByRole('button', { name: /导出/i });
      expect(button).toHaveAttribute('aria-expanded', 'false');
      expect(button).toHaveAttribute('aria-haspopup', 'true');
    });
  });
});
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AiExportAssistant } from '@/components/export/AiExportAssistant';
import * as exportApi from '@/services/api';

// Mock the API module
jest.mock('@/services/api');
const mockedExportApi = exportApi as jest.Mocked<typeof exportApi>;

describe('AiExportAssistant', () => {
  const mockProps = {
    databaseName: 'test_db',
    sqlText: 'SELECT * FROM users',
    queryResult: {
      columns: [
        { name: 'id', type: 'integer' },
        { name: 'name', type: 'varchar' },
        { name: 'email', type: 'varchar' }
      ],
      rows: [
        [1, 'John Doe', 'john@example.com'],
        [2, 'Jane Smith', 'jane@example.com']
      ],
      rowCount: 2
    },
    onExport: jest.fn(),
    enabled: true
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render loading state when analyzing intent', () => {
      mockedExportApi.analyzeExportIntent.mockResolvedValue({
        shouldSuggestExport: true,
        confidence: 0.85,
        reasoning: 'test',
        clarificationNeeded: false,
        clarificationQuestion: null,
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      });

      render(<AiExportAssistant {...mockProps} />);

      expect(screen.getByText('AI分析中...')).toBeInTheDocument();
    });

    it('should not render when disabled', () => {
      render(<AiExportAssistant {...mockProps} enabled={false} />);

      expect(screen.queryByRole('companion')).not.toBeInTheDocument();
    });

    it('should not render when export is not suggested', async () => {
      mockedExportApi.analyzeExportIntent.mockResolvedValue({
        shouldSuggestExport: false,
        confidence: 0.3,
        reasoning: 'No export needed',
        clarificationNeeded: false,
        clarificationQuestion: null,
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      });

      render(<AiExportAssistant {...mockProps} />);

      await waitFor(() => {
        expect(screen.queryByRole('companion')).not.toBeInTheDocument();
      });
    });
  });

  describe('Suggestion Display', () => {
    it('should display AI suggestion when analysis is complete', async () => {
      const mockIntent = {
        shouldSuggestExport: true,
        confidence: 0.85,
        reasoning: ' substantial amount of data',
        clarificationNeeded: false,
        clarificationQuestion: null,
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      };

      const mockSuggestion = {
        suggestionText: '您查询了2条用户数据记录，这是一个不错的数据量级。',
        quickActions: [
          {
            type: 'export' as const,
            label: '立即导出为CSV',
            format: 'CSV',
            scope: 'ALL_DATA',
            action: 'export'
          }
        ],
        confidence: 0.85,
        explanation: '基于查询返回的数据量大小'
      };

      mockedExportApi.analyzeExportIntent.mockResolvedValue(mockIntent);
      mockedExportApi.getProactiveSuggestion.mockResolvedValue(mockSuggestion);

      render(<AiExportAssistant {...mockProps} />);

      await waitFor(() => {
        expect(screen.getByText('您查询了2条用户数据记录，这是一个不错的数据量级。')).toBeInTheDocument();
      });

      // Check for quick actions
      expect(screen.getByText('立即导出为CSV')).toBeInTheDocument();
    });

    it('should display clarification question when needed', async () => {
      const mockIntent = {
        shouldSuggestExport: true,
        confidence: 0.6,
        reasoning: 'Need clarification',
        clarificationNeeded: true,
        clarificationQuestion: 'How would you like to export this data?',
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      };

      mockedExportApi.analyzeExportIntent.mockResolvedValue(mockIntent);

      render(<AiExportAssistant {...mockProps} />);

      await waitFor(() => {
        expect(screen.getByText('How would you like to export this data?')).toBeInTheDocument();
      });
    });
  });

  describe('Quick Actions', () => {
    it('should call onExport when export action is clicked', async () => {
      const mockIntent = {
        shouldSuggestExport: true,
        confidence: 0.85,
        reasoning: 'test',
        clarificationNeeded: false,
        clarificationQuestion: null,
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      };

      const mockSuggestion = {
        suggestionText: 'Export suggestion',
        quickActions: [
          {
            type: 'export' as const,
            label: '立即导出为CSV',
            format: 'CSV',
            scope: 'ALL_DATA',
            action: 'export'
          }
        ],
        confidence: 0.85,
        explanation: 'test'
      };

      mockedExportApi.analyzeExportIntent.mockResolvedValue(mockIntent);
      mockedExportApi.getProactiveSuggestion.mockResolvedValue(mockSuggestion);

      render(<AiExportAssistant {...mockProps} />);

      await waitFor(() => {
        const exportButton = screen.getByText('立即导出为CSV');
        fireEvent.click(exportButton);
      });

      expect(mockProps.onExport).toHaveBeenCalledWith({
        format: 'CSV',
        scope: 'ALL_DATA',
        sql: 'SELECT * FROM users'
      });
    });

    it('should handle filter action', async () => {
      const mockIntent = {
        shouldSuggestExport: true,
        confidence: 0.9,
        reasoning: 'test',
        clarificationNeeded: false,
        clarificationQuestion: null,
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      };

      const mockSuggestion = {
        suggestionText: 'Large dataset',
        quickActions: [
          {
            type: 'filter' as const,
            label: '按时间筛选',
            action: 'filter',
            description: '选择时间范围进行导出'
          }
        ],
        confidence: 0.9,
        explanation: 'Large dataset'
      };

      mockedExportApi.analyzeExportIntent.mockResolvedValue(mockIntent);
      mockedExportApi.getProactiveSuggestion.mockResolvedValue(mockSuggestion);

      render(<AiExportAssistant {...mockProps} />);

      await waitFor(() => {
        const filterButton = screen.getByText('按时间筛选');
        fireEvent.click(filterButton);
      });

      // Should open filter dialog or similar
      expect(screen.getByText('选择时间范围进行导出')).toBeInTheDocument();
    });

    it('should handle clarification action', async () => {
      const mockIntent = {
        shouldSuggestExport: true,
        confidence: 0.7,
        reasoning: 'Need format clarification',
        clarificationNeeded: true,
        clarificationQuestion: 'What format do you prefer?',
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      };

      const mockSuggestion = {
        suggestionText: 'Need clarification',
        quickActions: [
          {
            type: 'clarification' as const,
            label: 'CSV格式',
            action: 'clarify',
            value: 'CSV',
            description: '表格格式，适合Excel打开'
          }
        ],
        confidence: 0.7,
        explanation: 'Need user preference'
      };

      mockedExportApi.analyzeExportIntent.mockResolvedValue(mockIntent);
      mockedExportApi.getProactiveSuggestion.mockResolvedValue(mockSuggestion);

      render(<AiExportAssistant {...mockProps} />);

      await waitFor(() => {
        const csvButton = screen.getByText('CSV格式');
        fireEvent.click(csvButton);
      });

      // Should proceed with CSV format
      expect(mockProps.onExport).toHaveBeenCalledWith({
        format: 'CSV',
        scope: 'ALL_DATA',
        sql: 'SELECT * FROM users'
      });
    });
  });

  describe('Response Tracking', () => {
    it('should track user response when action is clicked', async () => {
      const mockIntent = {
        shouldSuggestExport: true,
        confidence: 0.85,
        reasoning: 'test',
        clarificationNeeded: false,
        clarificationQuestion: null,
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      };

      const mockSuggestion = {
        suggestionText: 'Export suggestion',
        quickActions: [
          {
            type: 'export' as const,
            label: '立即导出为CSV',
            format: 'CSV',
            scope: 'ALL_DATA',
            action: 'export'
          }
        ],
        confidence: 0.85,
        explanation: 'test'
      };

      mockedExportApi.analyzeExportIntent.mockResolvedValue(mockIntent);
      mockedExportApi.getProactiveSuggestion.mockResolvedValue(mockSuggestion);
      mockedExportApi.trackSuggestionResponse.mockResolvedValue(true);

      render(<AiExportAssistant {...mockProps} />);

      const startTime = Date.now();
      await waitFor(() => {
        const exportButton = screen.getByText('立即导出为CSV');
        fireEvent.click(exportButton);
      });
      const endTime = Date.now();
      const responseTime = endTime - startTime;

      // Verify tracking API is called
      expect(mockedExportApi.trackSuggestionResponse).toHaveBeenCalledWith({
        suggestionId: expect.any(String),
        databaseName: 'test_db',
        suggestionType: 'EXPORT_INTENT',
        sqlContext: 'SELECT * FROM users',
        rowCount: 2,
        confidence: 0.85,
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA',
        userResponse: 'ACCEPTED',
        responseTimeMs: expect.any(Number),
        suggestedAt: expect.any(Date),
        respondedAt: expect.any(Date)
      });

      // Verify response time is reasonable
      expect(responseTime).toBeGreaterThan(0);
      expect(responseTime).toBeLessThan(5000); // Less than 5 seconds
    });

    it('should track rejection when user closes assistant', async () => {
      const mockIntent = {
        shouldSuggestExport: true,
        confidence: 0.85,
        reasoning: 'test',
        clarificationNeeded: false,
        clarificationQuestion: null,
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      };

      mockedExportApi.analyzeExportIntent.mockResolvedValue(mockIntent);
      mockedExportApi.getProactiveSuggestion.mockResolvedValue({
        suggestionText: 'Export suggestion',
        quickActions: [],
        confidence: 0.85,
        explanation: 'test'
      });
      mockedExportApi.trackSuggestionResponse.mockResolvedValue(true);

      render(<AiExportAssistant {...mockProps} />);

      await waitFor(() => {
        const closeButton = screen.getByRole('button', { name: /close/i });
        fireEvent.click(closeButton);
      });

      // Verify rejection is tracked
      expect(mockedExportApi.trackSuggestionResponse).toHaveBeenCalledWith(
        expect.objectContaining({
          userResponse: 'IGNORED'
        })
      );
    });
  });

  describe('Error Handling', () => {
    it('should show error message when intent analysis fails', async () => {
      mockedExportApi.analyzeExportIntent.mockRejectedValue(new Error('Analysis failed'));

      render(<AiExportAssistant {...mockProps} />);

      await waitFor(() => {
        expect(screen.getByText('AI分析失败')).toBeInTheDocument();
        expect(screen.getByText('请稍后重试')).toBeInTheDocument();
      });
    });

    it('should show error message when suggestion generation fails', async () => {
      const mockIntent = {
        shouldSuggestExport: true,
        confidence: 0.85,
        reasoning: 'test',
        clarificationNeeded: false,
        clarificationQuestion: null,
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      };

      mockedExportApi.analyzeExportIntent.mockResolvedValue(mockIntent);
      mockedExportApi.getProactiveSuggestion.mockRejectedValue(new Error('Suggestion failed'));

      render(<AiExportAssistant {...mockProps} />);

      await waitFor(() => {
        expect(screen.getByText('建议生成失败')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', async () => {
      const mockIntent = {
        shouldSuggestExport: true,
        confidence: 0.85,
        reasoning: 'test',
        clarificationNeeded: false,
        clarificationQuestion: null,
        suggestedFormat: 'CSV',
        suggestedScope: 'ALL_DATA'
      };

      const mockSuggestion = {
        suggestionText: 'Test suggestion',
        quickActions: [
          {
            type: 'export' as const,
            label: '导出',
            format: 'CSV',
            scope: 'ALL_DATA',
            action: 'export'
          }
        ],
        confidence: 0.85,
        explanation: 'test'
      };

      mockedExportApi.analyzeExportIntent.mockResolvedValue(mockIntent);
      mockedExportApi.getProactiveSuggestion.mockResolvedValue(mockSuggestion);

      render(<AiExportAssistant {...mockProps} />);

      await waitFor(() => {
        const assistant = screen.getByRole('companion');
        expect(assistant).toBeInTheDocument();

        const closeButton = screen.getByRole('button', { name: /关闭/i });
        expect(closeButton).toBeInTheDocument();
      });
    });
  });

  describe('Props Validation', () => {
    it('should render with minimal props', () => {
      const minimalProps = {
        databaseName: 'test_db',
        sqlText: 'SELECT 1',
        queryResult: {
          columns: [],
          rows: [],
          rowCount: 0
        },
        onExport: jest.fn(),
        enabled: true
      };

      render(<AiExportAssistant {...minimalProps} />);

      expect(screen.getByText('AI分析中...')).toBeInTheDocument();
    });

    it('should validate required props', () => {
      // @ts-ignore - Testing runtime validation
      const renderWithoutRequired = () => render(<AiExportAssistant {...{}} />);

      expect(renderWithoutRequired).toThrow();
    });
  });
});
"""
AI Proactive Suggestion Generation Tests

Tests the generation of friendly export suggestions and quick actions.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import openai

from app.services.export import AIExportService
from app.models.export import (
    ExportFormat,
    ExportScope,
    TaskStatus,
    AISuggestionAnalytics,
    ExportSuggestionResponse
)


@pytest.fixture
def ai_export_service():
    """Fixture for AIExportService"""
    return AIExportService()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client"""
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client

        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '''
        {
            "suggestionText": "您查询了150条用户数据记录，这是一个不错的数据量级。将数据导出为CSV格式可以方便地进行后续分析或备份。",
            "quickActions": [
                {
                    "type": "export",
                    "label": "立即导出为CSV",
                    "format": "CSV",
                    "scope": "ALL_DATA",
                    "action": "export"
                },
                {
                    "type": "export",
                    "label": "导出当前页面",
                    "format": "CSV",
                    "scope": "CURRENT_PAGE",
                    "action": "export"
                },
                {
                    "type": "export",
                    "label": "导出为Excel",
                    "format": "JSON",
                    "scope": "ALL_DATA",
                    "action": "export"
                }
            ],
            "confidence": 0.85,
            "explanation": "基于查询返回的数据量大小和用户历史使用模式，预测用户可能需要导出数据进行离线分析"
        }
        '''
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 200

        mock_client.chat.completions.create.return_value = mock_response
        yield mock_client


@pytest.mark.asyncio
async def test_generate_proactive_suggestion_basic(ai_export_service, mock_openai_client):
    """Test basic proactive suggestion generation"""
    # Test data
    intent_analysis = {
        'shouldSuggestExport': True,
        'confidence': 0.85,
        'reasoning': 'The query returned 150 rows which is a substantial amount',
        'clarificationNeeded': False,
        'clarificationQuestion': None,
        'suggestedFormat': ExportFormat.CSV,
        'suggestedScope': ExportScope.ALL_DATA
    }

    # Execute
    result = await ai_export_service.generate_proactive_suggestion(
        database_name='test_db',
        sql_text='SELECT * FROM users',
        query_result={
            'columns': [{'name': 'id', 'type': 'integer'}],
            'rows': [(i,) for i in range(150)],
            'row_count': 150
        },
        intent_analysis=intent_analysis
    )

    # Assert
    assert 'suggestionText' in result
    assert 'quickActions' in result
    assert len(result['quickActions']) == 3
    assert result['confidence'] == 0.85
    assert 'explanation' in result

    # Check quick actions
    action_types = [action['type'] for action in result['quickActions']]
    assert 'export' in action_types

    # Check CSV action
    csv_action = next(action for action in result['quickActions']
                     if action['format'] == ExportFormat.CSV)
    assert csv_action['label'] == '立即导出为CSV'


@pytest.mark.asyncio
async def test_generate_proactive_suggestion_large_dataset(ai_export_service, mock_openai_client):
    """Test suggestion for large dataset"""
    # Mock response for large dataset
    mock_response.choices[0].message.content = '''
    {
        "suggestionText": "您查询了10,000条销售记录，这是一个相当大的数据集。建议您考虑导出为CSV格式进行深度分析，或者按时间范围分批导出。",
        "quickActions": [
            {
                "type": "export",
                "label": "导出全部(10,000行)",
                "format": "CSV",
                "scope": "ALL_DATA",
                "action": "export"
            },
            {
                "type": "export",
                "label": "导出最新1,000行",
                "format": "CSV",
                "scope": "CURRENT_PAGE",
                "action": "export"
            },
            {
                "type": "filter",
                "label": "按时间筛选",
                "action": "filter",
                "description": "选择时间范围进行导出"
            }
        ],
        "confidence": 0.95,
        "explanation": "大数据集通常需要更谨慎的导出策略，提供分批导出选项"
    }
    '''

    # Test data - large dataset
    intent_analysis = {
        'shouldSuggestExport': True,
        'confidence': 0.95,
        'reasoning': 'Large dataset with 10000 rows',
        'clarificationNeeded': False,
        'clarificationQuestion': None,
        'suggestedFormat': ExportFormat.CSV,
        'suggestedScope': ExportScope.ALL_DATA
    }

    # Execute
    result = await ai_export_service.generate_proactive_suggestion(
        database_name='sales_db',
        sql_text='SELECT * FROM orders WHERE date >= "2024-01-01"',
        query_result={
            'columns': [
                {'name': 'id', 'type': 'bigint'},
                {'name': 'amount', 'type': 'decimal'},
                {'name': 'date', 'type': 'date'}
            ],
            'rows': [(i, 100.0 + i, f'2024-01-{i%30+1:02d}') for i in range(10000)],
            'row_count': 10000
        },
        intent_analysis=intent_analysis
    )

    # Assert
    assert '10,000条销售记录' in result['suggestionText']
    assert len(result['quickActions']) == 3

    # Check for filter action
    filter_action = next(action for action in result['quickActions']
                        if action['type'] == 'filter')
    assert filter_action['label'] == '按时间筛选'


@pytest.mark.asyncio
async def test_generate_proactive_suggestion_json_data(ai_export_service, mock_openai_client):
    """Test suggestion for JSON structured data"""
    # Mock response for JSON data
    mock_response.choices[0].message.content = '''
    {
        "suggestionText": "您的查询结果包含嵌套的JSON结构，使用JSON格式导出可以完整保留数据结构，便于后续处理。",
        "quickActions": [
            {
                "type": "export",
                "label": "导出为JSON",
                "format": "JSON",
                "scope": "ALL_DATA",
                "action": "export"
            },
            {
                "type": "export",
                "label": "导出为CSV(展开结构)",
                "format": "CSV",
                "scope": "ALL_DATA",
                "action": "export"
            },
            {
                "type": "transform",
                "label": "结构化查看",
                "action": "view",
                "description": "以树形结构查看JSON数据"
            }
        ],
        "confidence": 0.90,
        "explanation": "JSON格式最适合保持数据的原始结构完整性"
    }
    '''

    # Test data with JSON structure
    intent_analysis = {
        'shouldSuggestExport': True,
        'confidence': 0.90,
        'reasoning': 'Contains nested JSON structures',
        'clarificationNeeded': False,
        'clarificationQuestion': None,
        'suggestedFormat': ExportFormat.JSON,
        'suggestedScope': ExportScope.ALL_DATA
    }

    # Execute
    result = await ai_export_service.generate_proactive_suggestion(
        database_name='api_db',
        sql_text='SELECT id, metadata FROM events',
        query_result={
            'columns': [
                {'name': 'id', 'type': 'integer'},
                {'name': 'metadata', 'type': 'jsonb'}
            ],
            'rows': [
                (1, '{"user": {"id": 123, "name": "test"}, "event": "click"}')
            ],
            'row_count': 1
        },
        intent_analysis=intent_analysis
    )

    # Assert
    assert '嵌套的JSON结构' in result['suggestionText']
    assert 'JSON格式导出' in result['suggestionText']

    # Check for JSON action
    json_action = next(action for action in result['quickActions']
                       if action['format'] == ExportFormat.JSON)
    assert json_action['label'] == '导出为JSON'


@pytest.mark.asyncio
async def test_generate_proactive_suggestion_clarification_needed(ai_export_service, mock_openai_client):
    """Test suggestion when clarification is needed"""
    # Mock response for clarification
    mock_response.choices[0].message.content = '''
    {
        "suggestionText": "我需要了解更多关于您期望的导出格式，以便为您提供最佳建议。",
        "quickActions": [
            {
                "type": "clarification",
                "label": "CSV格式",
                "action": "clarify",
                "value": "CSV",
                "description": "表格格式，适合Excel打开"
            },
            {
                "type": "clarification",
                "label": "JSON格式",
                "action": "clarify",
                "value": "JSON",
                "description": "结构化数据格式"
            },
            {
                "type": "clarification",
                "label": "Markdown格式",
                "action": "clarify",
                "value": "MARKDOWN",
                "description": "文档格式，适合报告"
            }
        ],
        "confidence": 0.70,
        "explanation": "需要用户确认格式偏好"
    }
    '''

    # Test data needing clarification
    intent_analysis = {
        'shouldSuggestExport': True,
        'confidence': 0.70,
        'reasoning': 'Need user preference for format',
        'clarificationNeeded': True,
        'clarificationQuestion': 'What format would you prefer?',
        'suggestedFormat': ExportFormat.CSV,
        'suggestedScope': ExportScope.ALL_DATA
    }

    # Execute
    result = await ai_export_service.generate_proactive_suggestion(
        database_name='test_db',
        sql_text='SELECT * FROM products',
        query_result={
            'columns': [{'name': 'id', 'type': 'integer'}],
            'rows': [(1,), (2,)],
            'row_count': 2
        },
        intent_analysis=intent_analysis
    )

    # Assert
    assert '了解更多关于您期望的导出格式' in result['suggestionText']
    assert len(result['quickActions']) == 3

    # Check for clarification actions
    clarification_actions = [action for action in result['quickActions']
                            if action['type'] == 'clarification']
    assert len(clarification_actions) == 3


@pytest.mark.asyncio
async def test_generate_proactive_suggestion_error_handling(ai_export_service):
    """Test error handling in proactive suggestion generation"""
    # Mock OpenAI client to raise error
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API error")

        intent_analysis = {
            'shouldSuggestExport': True,
            'confidence': 0.8,
            'reasoning': 'Test error',
            'clarificationNeeded': False,
            'clarificationQuestion': None,
            'suggestedFormat': ExportFormat.CSV,
            'suggestedScope': ExportScope.ALL_DATA
        }

        # Execute and assert error
        with pytest.raises(Exception, match="OpenAI API error"):
            await ai_export_service.generate_proactive_suggestion(
                database_name='test_db',
                sql_text='SELECT * FROM test',
                query_result={
                    'columns': [{'name': 'id', 'type': 'integer'}],
                    'rows': [(1,)],
                    'row_count': 1
                },
                intent_analysis=intent_analysis
            )


@pytest.mark.asyncio
async def test_generate_proactive_suggestion_invalid_intent(ai_export_service, mock_openai_client):
    """Test handling of invalid intent analysis"""
    # Test with invalid intent analysis
    invalid_intent = {
        'shouldSuggestExport': False,
        'confidence': 0.0,
        'reasoning': 'No export needed'
    }

    # Execute should return empty suggestion
    result = await ai_export_service.generate_proactive_suggestion(
        database_name='test_db',
        sql_text='SELECT * FROM test',
        query_result={
            'columns': [{'name': 'id', 'type': 'integer'}],
            'rows': [(1,)],
            'row_count': 1
        },
        intent_analysis=invalid_intent
    )

    # Assert should return None or empty
    assert result is None or (not result.get('suggestionText') and not result.get('quickActions'))
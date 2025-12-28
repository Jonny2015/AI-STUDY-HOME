"""
AI Export Intent Analysis Tests

Tests the ability to analyze query results and determine if export suggestions should be made.
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
            "shouldSuggestExport": true,
            "confidence": 0.85,
            "reasoning": "The query returned 150 rows which is a substantial amount of data that would benefit from export",
            "clarificationNeeded": false,
            "clarificationQuestion": null,
            "suggestedFormat": "CSV",
            "suggestedScope": "ALL_DATA"
        }
        '''
        mock_response.choices[0].message.tool_calls = None
        mock_response.usage = MagicMock()
        mock_response.usage.total_tokens = 150

        mock_client.chat.completions.create.return_value = mock_response
        yield mock_client


@pytest.mark.asyncio
async def test_analyze_export_intent_should_suggest(ai_export_service, mock_openai_client):
    """Test case when AI suggests export should be offered"""
    # Test data
    query_result = {
        'columns': [
            {'name': 'id', 'type': 'integer'},
            {'name': 'name', 'type': 'varchar'},
            {'name': 'created_at', 'type': 'timestamp'}
        ],
        'rows': [
            (1, 'test1', '2024-01-01'),
            (2, 'test2', '2024-01-02')
        ],
        'row_count': 2
    }

    # Execute
    result = await ai_export_service.analyze_export_intent(
        database_name='test_db',
        sql_text='SELECT * FROM users',
        query_result=query_result
    )

    # Assert
    assert result['shouldSuggestExport'] is True
    assert result['confidence'] == 0.85
    assert 'substantial amount' in result['reasoning']
    assert result['clarificationNeeded'] is False
    assert result['suggestedFormat'] == ExportFormat.CSV
    assert result['suggestedScope'] == ExportScope.ALL_DATA


@pytest.mark.asyncio
async def test_analyze_export_intent_should_not_suggest(ai_export_service, mock_openai_client):
    """Test case when AI suggests export should not be offered"""
    # Mock a different response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''
    {
        "shouldSuggestExport": false,
        "confidence": 0.95,
        "reasoning": "The query returned only 5 rows which is trivial data size",
        "clarificationNeeded": false,
        "clarificationQuestion": null,
        "suggestedFormat": "CSV",
        "suggestedScope": "ALL_DATA"
    }
    '''
    mock_response.choices[0].message.tool_calls = None
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 100
    mock_openai_client.chat.completions.create.return_value = mock_response

    # Test data
    query_result = {
        'columns': [
            {'name': 'id', 'type': 'integer'}
        ],
        'rows': [(1,), (2,), (3,), (4,), (5,)],
        'row_count': 5
    }

    # Execute
    result = await ai_export_service.analyze_export_intent(
        database_name='test_db',
        sql_text='SELECT id FROM users LIMIT 5',
        query_result=query_result
    )

    # Assert
    assert result['shouldSuggestExport'] is False
    assert result['confidence'] == 0.95
    assert 'trivial data size' in result['reasoning']


@pytest.mark.asyncio
async def test_analyze_export_intent_with_clarification(ai_export_service, mock_openai_client):
    """Test case when AI needs clarification"""
    # Mock response needing clarification
    mock_response.choices[0].message.content = '''
    {
        "shouldSuggestExport": true,
        "confidence": 0.60,
        "reasoning": "Need clarification on user's preferences",
        "clarificationNeeded": true,
        "clarificationQuestion": "How would you like to export this data? As a complete dataset or filtered results?",
        "suggestedFormat": "CSV",
        "suggestedScope": "CURRENT_PAGE"
    }
    '''

    # Test data
    query_result = {
        'columns': [
            {'name': 'id', 'type': 'integer'},
            {'name': 'name', 'type': 'varchar'}
        ],
        'rows': [(1, 'test1'), (2, 'test2')],
        'row_count': 2
    }

    # Execute
    result = await ai_export_service.analyze_export_intent(
        database_name='test_db',
        sql_text='SELECT * FROM users WHERE active = true',
        query_result=query_result
    )

    # Assert
    assert result['shouldSuggestExport'] is True
    assert result['confidence'] == 0.60
    assert result['clarificationNeeded'] is True
    assert result['clarificationQuestion'] == "How would you like to export this data? As a complete dataset or filtered results?"


@pytest.mark.asyncio
async def test_analyze_export_intent_large_dataset(ai_export_service, mock_openai_client):
    """Test case with large dataset"""
    # Test data - simulate large dataset
    large_rows = list(range(1000))  # 1000 rows

    query_result = {
        'columns': [
            {'name': 'id', 'type': 'bigint'},
            {'name': 'description', 'type': 'text'}
        ],
        'rows': [(i, f'test_{i}') for i in large_rows],
        'row_count': 1000
    }

    # Execute
    result = await ai_export_service.analyze_export_intent(
        database_name='test_db',
        sql_text='SELECT * FROM large_table',
        query_result=query_result
    )

    # Assert
    assert result['shouldSuggestExport'] is True
    # Should have high confidence for large datasets
    assert result['confidence'] >= 0.8


@pytest.mark.asyncio
async def test_analyze_export_intent_error_handling(ai_export_service):
    """Test error handling in export intent analysis"""
    # Mock OpenAI client to raise error
    with patch('openai.AsyncOpenAI') as mock_openai:
        mock_client = AsyncMock()
        mock_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("OpenAI API error")

        # Test data
        query_result = {
            'columns': [{'name': 'id', 'type': 'integer'}],
            'rows': [(1,)],
            'row_count': 1
        }

        # Execute and assert error
        with pytest.raises(Exception, match="OpenAI API error"):
            await ai_export_service.analyze_export_intent(
                database_name='test_db',
                sql_text='SELECT id FROM test',
                query_result=query_result
            )


@pytest.mark.asyncio
async def test_analyze_export_intent_json_format_suggestion(ai_export_service, mock_openai_client):
    """Test AI suggests JSON format for certain data types"""
    # Mock response suggesting JSON
    mock_response.choices[0].message.content = '''
    {
        "shouldSuggestExport": true,
        "confidence": 0.90,
        "reasoning": "The data contains nested JSON structures, CSV format might not preserve structure",
        "clarificationNeeded": false,
        "clarificationQuestion": null,
        "suggestedFormat": "JSON",
        "suggestedScope": "ALL_DATA"
    }
    '''

    # Test data with complex structure
    query_result = {
        'columns': [
            {'name': 'id', 'type': 'integer'},
            {'name': 'metadata', 'type': 'jsonb'}
        ],
        'rows': [
            (1, '{"key": "value", "nested": {"inner": "data"}}')
        ],
        'row_count': 1
    }

    # Execute
    result = await ai_export_service.analyze_export_intent(
        database_name='test_db',
        sql_text='SELECT id, metadata FROM complex_data',
        query_result=query_result
    )

    # Assert
    assert result['shouldSuggestExport'] is True
    assert result['suggestedFormat'] == ExportFormat.JSON
    assert 'nested JSON structures' in result['reasoning']
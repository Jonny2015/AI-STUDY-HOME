"""
AI Export API Integration Tests

Tests the complete AI export API endpoints including intent analysis, suggestions, and response tracking.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.main import app
from app.models.export import ExportFormat, ExportScope, TaskStatus, ExportSuggestionResponse
from app.models.schemas import ExportIntentAnalysisRequest, ExportIntentAnalysisResponse


@pytest.fixture
def client():
    """Test client for AI Export API"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def mock_ai_service():
    """Mock AIExportService"""
    with patch('app.api.v1.export.AIExportService') as mock_service_class:
        mock_service = AsyncMock()
        mock_service_class.return_value = mock_service

        # Mock methods
        mock_service.analyze_export_intent.return_value = {
            'shouldSuggestExport': True,
            'confidence': 0.85,
            'reasoning': ' substantial amount of data',
            'clarificationNeeded': False,
            'clarificationQuestion': None,
            'suggestedFormat': ExportFormat.CSV,
            'suggestedScope': ExportScope.ALL_DATA
        }

        mock_service.generate_proactive_suggestion.return_value = {
            'suggestionText': '您查询了150条用户数据记录，这是一个不错的数据量级。',
            'quickActions': [
                {
                    'type': 'export',
                    'label': '立即导出为CSV',
                    'format': 'CSV',
                    'scope': 'ALL_DATA',
                    'action': 'export'
                }
            ],
            'confidence': 0.85,
            'explanation': '基于查询返回的数据量大小'
        }

        mock_service.track_suggestion_response.return_value = True
        mock_service.get_export_analytics.return_value = {
            'totalSuggestions': 10,
            'acceptanceRate': 70.0,
            'avgResponseTime': 5000,
            'responsesByType': {
                'EXPORT_INTENT': {'total': 8, 'accepted': 6},
                'PROACTIVE_SUGGESTION': {'total': 2, 'accepted': 1}
            },
            'responsesByFormat': {
                'CSV': {'total': 7, 'accepted': 5},
                'JSON': {'total': 3, 'accepted': 2}
            }
        }

        yield mock_service


def test_analyze_intent_endpoint_success(client, mock_ai_service):
    """Test successful intent analysis endpoint"""
    # Test data
    request_data = {
        'databaseName': 'test_db',
        'sqlText': 'SELECT * FROM users',
        'queryResult': {
            'columns': [{'name': 'id', 'type': 'integer'}],
            'rows': [(1,), (2,), (3,)],
            'rowCount': 3
        }
    }

    # Make request
    response = client.post('/api/v1/export/analyze-intent', json=request_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert 'shouldSuggestExport' in data
    assert 'confidence' in data
    assert 'reasoning' in data
    assert 'clarificationNeeded' in data
    assert 'suggestedFormat' in data
    assert 'suggestedScope' in data


def test_analyze_intent_endpoint_missing_fields(client):
    """Test intent analysis with missing fields"""
    request_data = {
        'databaseName': 'test_db'
        # Missing sqlText and queryResult
    }

    response = client.post('/api/v1/export/analyze-intent', json=request_data)

    # Should return 422 for validation error
    assert response.status_code == 422


def test_analyze_intent_endpoint_error(client, mock_ai_service):
    """Test intent analysis endpoint error handling"""
    # Mock service to raise error
    mock_ai_service.analyze_export_intent.side_effect = Exception("AI service error")

    request_data = {
        'databaseName': 'test_db',
        'sqlText': 'SELECT * FROM users',
        'queryResult': {
            'columns': [{'name': 'id', 'type': 'integer'}],
            'rows': [(1,)],
            'rowCount': 1
        }
    }

    response = client.post('/api/v1/export/analyze-intent', json=request_data)

    # Should return 500 for server error
    assert response.status_code == 500
    assert 'AI service error' in response.json()['detail']


def test_proactive_suggestion_endpoint_success(client, mock_ai_service):
    """Test successful proactive suggestion endpoint"""
    # Test data
    request_data = {
        'databaseName': 'test_db',
        'sqlText': 'SELECT * FROM users',
        'queryResult': {
            'columns': [{'name': 'id', 'type': 'integer'}],
            'rows': [(1,), (2,)],
            'rowCount': 2
        },
        'intentAnalysis': {
            'shouldSuggestExport': True,
            'confidence': 0.85,
            'reasoning': 'test'
        }
    }

    response = client.post('/api/v1/export/proactive-suggestion', json=request_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert 'suggestionText' in data
    assert 'quickActions' in data
    assert 'confidence' in data
    assert 'explanation' in data

    # Verify quick actions structure
    assert len(data['quickActions']) > 0
    action = data['quickActions'][0]
    assert 'type' in action
    assert 'label' in action
    assert 'action' in action


def test_proactive_suggestion_endpoint_missing_intent_analysis(client, mock_ai_service):
    """Test proactive suggestion without intent analysis"""
    request_data = {
        'databaseName': 'test_db',
        'sqlText': 'SELECT * FROM users',
        'queryResult': {
            'columns': [{'name': 'id', 'type': 'integer'}],
            'rows': [(1,)],
            'rowCount': 1
        }
        # Missing intentAnalysis
    }

    response = client.post('/api/v1/export/proactive-suggestion', json=request_data)

    # Should return 422 for validation error
    assert response.status_code == 422


def test_proactive_suggestion_endpoint_no_suggestion(client, mock_ai_service):
    """Test proactive suggestion when no suggestion should be made"""
    # Mock service to return None
    mock_ai_service.generate_proactive_suggestion.return_value = None

    request_data = {
        'databaseName': 'test_db',
        'sqlText': 'SELECT * FROM users',
        'queryResult': {
            'columns': [{'name': 'id', 'type': 'integer'}],
            'rows': [(1,)],
            'rowCount': 1
        },
        'intentAnalysis': {
            'shouldSuggestExport': False,
            'confidence': 0.5,
            'reasoning': 'No export needed'
        }
    }

    response = client.post('/api/v1/export/proactive-suggestion', json=request_data)

    # Should return 404 no content
    assert response.status_code == 204


def test_track_response_endpoint_success(client, mock_ai_service):
    """Test successful response tracking endpoint"""
    # Test data
    request_data = {
        'suggestionId': 'test-suggestion-123',
        'databaseName': 'test_db',
        'suggestionType': 'EXPORT_INTENT',
        'sqlContext': 'SELECT * FROM users',
        'rowCount': 150,
        'confidence': 0.85,
        'suggestedFormat': 'CSV',
        'suggestedScope': 'ALL_DATA',
        'userResponse': 'ACCEPTED',
        'responseTimeMs': 5000,
        'suggestedAt': '2024-12-28T10:00:00Z',
        'respondedAt': '2024-12-28T10:00:05Z'
    }

    response = client.post('/api/v1/export/track-response', json=request_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data['success'] is True
    assert data['message'] == 'Response tracked successfully'


def test_track_response_endpoint_invalid_enum_values(client):
    """Test response tracking with invalid enum values"""
    request_data = {
        'suggestionId': 'test-suggestion-123',
        'databaseName': 'test_db',
        'suggestionType': 'INVALID_TYPE',
        'sqlContext': 'SELECT * FROM users',
        'rowCount': 150,
        'confidence': 0.85,
        'suggestedFormat': 'CSV',
        'suggestedScope': 'ALL_DATA',
        'userResponse': 'INVALID_RESPONSE',
        'responseTimeMs': 5000,
        'suggestedAt': '2024-12-28T10:00:00Z',
        'respondedAt': '2024-12-28T10:00:05Z'
    }

    response = client.post('/api/v1/export/track-response', json=request_data)

    # Should return 422 for validation error
    assert response.status_code == 422


def test_track_response_endpoint_error(client, mock_ai_service):
    """Test response tracking error handling"""
    # Mock service to raise error
    mock_ai_service.track_suggestion_response.side_effect = Exception("Database error")

    request_data = {
        'suggestionId': 'test-suggestion-123',
        'databaseName': 'test_db',
        'suggestionType': 'EXPORT_INTENT',
        'sqlContext': 'SELECT * FROM users',
        'rowCount': 150,
        'confidence': 0.85,
        'suggestedFormat': 'CSV',
        'suggestedScope': 'ALL_DATA',
        'userResponse': 'ACCEPTED',
        'responseTimeMs': 5000,
        'suggestedAt': '2024-12-28T10:00:00Z',
        'respondedAt': '2024-12-28T10:00:05Z'
    }

    response = client.post('/api/v1/export/track-response', json=request_data)

    # Should return 500 for server error
    assert response.status_code == 500


def test_get_analytics_endpoint_success(client, mock_ai_service):
    """Test successful analytics endpoint"""
    response = client.get('/api/v1/export/analytics?databaseName=test_db&days=7')

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert 'totalSuggestions' in data
    assert 'acceptanceRate' in data
    assert 'avgResponseTime' in data
    assert 'responsesByType' in data
    assert 'responsesByFormat' in data

    # Verify data types and values
    assert isinstance(data['totalSuggestions'], int)
    assert isinstance(data['acceptanceRate'], float)
    assert isinstance(data['avgResponseTime'], int)


def test_get_analytics_endpoint_missing_database_name(client, mock_ai_service):
    """Test analytics without database name"""
    response = client.get('/api/v1/export/analytics?days=7')

    # Should return 422 for validation error
    assert response.status_code == 422


def test_get_analytics_endpoint_error(client, mock_ai_service):
    """Test analytics endpoint error handling"""
    # Mock service to raise error
    mock_ai_service.get_export_analytics.side_effect = Exception("Analytics error")

    response = client.get('/api/v1/export/analytics?databaseName=test_db&days=7')

    # Should return 500 for server error
    assert response.status_code == 500
    assert 'Analytics error' in response.json()['detail']


def test_get_analytics_endpoint_empty_data(client, mock_ai_service):
    """Test analytics with no data"""
    # Mock service to return empty analytics
    mock_ai_service.get_export_analytics.return_value = {
        'totalSuggestions': 0,
        'acceptanceRate': 0.0,
        'avgResponseTime': 0,
        'responsesByType': {},
        'responsesByFormat': {}
    }

    response = client.get('/api/v1/export/analytics?databaseName=test_db&days=7')

    # Should still return 200 with empty data
    assert response.status_code == 200
    data = response.json()
    assert data['totalSuggestions'] == 0
    assert data['acceptanceRate'] == 0.0


def test_analytics_endpoint_invalid_days(client, mock_ai_service):
    """Test analytics with invalid days parameter"""
    response = client.get('/api/v1/export/analytics?databaseName=test_db&days=invalid')

    # Should return 422 for validation error
    assert response.status_code == 422
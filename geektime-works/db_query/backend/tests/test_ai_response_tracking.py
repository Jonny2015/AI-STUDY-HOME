"""
AI Response Tracking Tests

Tests the tracking of user responses to AI export suggestions and analytics data collection.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

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
    with patch('app.database.get_session') as mock_session:
        mock_db_session = AsyncMock()
        mock_session.return_value = mock_db_session

        # Mock the async context manager
        async def mock_session_context():
            yield mock_db_session
        mock_session.return_value = mock_session_context()

        service = AIExportService()
        service.db_session = mock_db_session
        yield service


@pytest.fixture
def mock_analytics_data():
    """Mock analytics data for testing"""
    return {
        'suggestion_id': 'test-suggestion-123',
        'database_name': 'test_db',
        'suggestion_type': 'EXPORT_INTENT',
        'sql_context': 'SELECT * FROM users',
        'row_count': 150,
        'confidence': 0.85,
        'suggested_format': 'CSV',
        'suggested_scope': 'ALL_DATA',
        'user_response': 'ACCEPTED',
        'response_time_ms': 5000,
        'suggested_at': datetime.now(),
        'responded_at': datetime.now() + timedelta(seconds=5)
    }


@pytest.mark.asyncio
async def test_track_suggestion_response_accepted(ai_export_service, mock_analytics_data):
    """Test tracking accepted suggestion response"""
    # Mock database operations
    mock_analytics_record = MagicMock()
    ai_export_service.db_session.add.return_value = None
    ai_export_service.db_session.commit.return_value = None
    ai_export_service.db_session.refresh.return_value = None

    # Execute
    result = await ai_export_service.track_suggestion_response(
        suggestion_id='test-suggestion-123',
        database_name='test_db',
        suggestion_type='EXPORT_INTENT',
        sql_context='SELECT * FROM users',
        row_count=150,
        confidence=0.85,
        suggested_format=ExportFormat.CSV,
        suggested_scope=ExportScope.ALL_DATA,
        user_response=ExportSuggestionResponse.ACCEPTED,
        response_time_ms=5000,
        suggested_at=datetime.now(),
        responded_at=datetime.now() + timedelta(seconds=5)
    )

    # Assert
    assert result is True

    # Verify database operations
    ai_export_service.db_session.add.assert_called_once()
    ai_export_service.db_session.commit.assert_called_once()

    # Verify the record type
    added_record = ai_export_service.db_session.add.call_args[0][0]
    assert isinstance(added_record, AISuggestionAnalytics)


@pytest.mark.asyncio
async def test_track_suggestion_response_rejected(ai_export_service, mock_analytics_data):
    """Test tracking rejected suggestion response"""
    # Mock database operations
    ai_export_service.db_session.add.return_value = None
    ai_export_service.db_session.commit.return_value = None

    # Execute
    result = await ai_export_service.track_suggestion_response(
        suggestion_id='test-suggestion-124',
        database_name='test_db',
        suggestion_type='EXPORT_INTENT',
        sql_context='SELECT * FROM products',
        row_count=50,
        confidence=0.70,
        suggested_format=ExportFormat.JSON,
        suggested_scope=ExportScope.CURRENT_PAGE,
        user_response=ExportSuggestionResponse.REJECTED,
        response_time_ms=2000,
        suggested_at=datetime.now(),
        responded_at=datetime.now() + timedelta(seconds=2)
    )

    # Assert
    assert result is True

    # Verify the rejection was recorded
    added_record = ai_export_service.db_session.add.call_args[0][0]
    assert added_record.suggestion_type == 'EXPORT_INTENT'
    assert added_record.user_response == ExportSuggestionResponse.REJECTED


@pytest.mark.asyncio
async def test_track_suggestion_response_modified(ai_export_service, mock_analytics_data):
    """Test tracking modified suggestion response"""
    # Mock database operations
    ai_export_service.db_session.add.return_value = None
    ai_export_service.db_session.commit.return_value = None

    # Execute
    result = await ai_export_service.track_suggestion_response(
        suggestion_id='test-suggestion-125',
        database_name='sales_db',
        suggestion_type='PROACTIVE_SUGGESTION',
        sql_context='SELECT * FROM orders WHERE date >= "2024-01-01"',
        row_count=1000,
        confidence=0.90,
        suggested_format=ExportFormat.CSV,
        suggested_scope=ExportScope.ALL_DATA,
        user_response=ExportSuggestionResponse.MODIFIED,
        response_time_ms=8000,
        suggested_at=datetime.now(),
        responded_at=datetime.now() + timedelta(seconds=8)
    )

    # Assert
    assert result is True

    # Verify the modification was recorded
    added_record = ai_export_service.db_session.add.call_args[0][0]
    assert added_record.suggestion_type == 'PROACTIVE_SUGGESTION'
    assert added_record.user_response == ExportSuggestionResponse.MODIFIED
    assert added_record.response_time_ms == 8000


@pytest.mark.asyncio
async def test_track_suggestion_response_ignored(ai_export_service, mock_analytics_data):
    """Test tracking ignored suggestion response"""
    # Mock database operations
    ai_export_service.db_session.add.return_value = None
    ai_export_service.db_session.commit.return_value = None

    # Execute
    result = await ai_export_service.track_suggestion_response(
        suggestion_id='test-suggestion-126',
        database_name='analytics_db',
        suggestion_type='EXPORT_INTENT',
        sql_context='SELECT COUNT(*) FROM events',
        row_count=1,
        confidence=0.60,
        suggested_format=ExportFormat.CSV,
        suggested_scope=ExportScope.CURRENT_PAGE,
        user_response=ExportSuggestionResponse.IGNORED,
        response_time_ms=10000,
        suggested_at=datetime.now(),
        responded_at=datetime.now() + timedelta(seconds=10)
    )

    # Assert
    assert result is True

    # Verify the ignore was recorded
    added_record = ai_export_service.db_session.add.call_args[0][0]
    assert added_record.user_response == ExportSuggestionResponse.IGNORED
    assert added_record.response_time_ms == 10000


@pytest.mark.asyncio
async def test_track_suggestion_response_database_error(ai_export_service):
    """Test database error handling in response tracking"""
    # Mock database operations to raise error
    ai_export_service.db_session.add.side_effect = Exception("Database connection failed")

    # Execute and assert error
    with pytest.raises(Exception, match="Database connection failed"):
        await ai_export_service.track_suggestion_response(
            suggestion_id='test-suggestion-127',
            database_name='test_db',
            suggestion_type='EXPORT_INTENT',
            sql_context='SELECT * FROM test',
            row_count=10,
            confidence=0.80,
            suggested_format=ExportFormat.CSV,
            suggested_scope=ExportScope.ALL_DATA,
            user_response=ExportSuggestionResponse.ACCEPTED,
            response_time_ms=3000,
            suggested_at=datetime.now(),
            responded_at=datetime.now() + timedelta(seconds=3)
        )


@pytest.mark.asyncio
async def test_get_export_analytics_basic(ai_export_service):
    """Test basic analytics data retrieval"""
    # Mock database query results
    mock_analytics = [
        MagicMock(
            suggestion_type='EXPORT_INTENT',
            user_response='ACCEPTED',
            response_time_ms=5000,
            suggested_at=datetime.now() - timedelta(hours=1)
        ),
        MagicMock(
            suggestion_type='EXPORT_INTENT',
            user_response='REJECTED',
            response_time_ms=3000,
            suggested_at=datetime.now() - timedelta(hours=2)
        ),
        MagicMock(
            suggestion_type='PROACTIVE_SUGGESTION',
            user_response='ACCEPTED',
            response_time_ms=8000,
            suggested_at=datetime.now() - timedelta(hours=3)
        )
    ]

    # Mock query result
    mock_query = MagicMock()
    mock_query.all.return_value = mock_analytics
    ai_export_service.db_session.exec.return_value = mock_query

    # Execute
    result = await ai_export_service.get_export_analytics(
        database_name='test_db',
        days=7
    )

    # Assert
    assert 'totalSuggestions' in result
    assert 'acceptanceRate' in result
    assert 'avgResponseTime' in result
    assert 'responsesByType' in result
    assert 'responsesByFormat' in result

    # Verify calculations
    assert result['totalSuggestions'] == 3
    assert result['acceptanceRate'] == 66.67  # 2 out of 3 accepted


@pytest.mark.asyncio
async def test_get_export_analytics_empty_data(ai_export_service):
    """Test analytics with no data"""
    # Mock empty query result
    mock_query = MagicMock()
    mock_query.all.return_value = []
    ai_export_service.db_session.exec.return_value = mock_query

    # Execute
    result = await ai_export_service.get_export_analytics(
        database_name='empty_db',
        days=7
    )

    # Assert
    assert result['totalSuggestions'] == 0
    assert result['acceptanceRate'] == 0
    assert result['avgResponseTime'] == 0


@pytest.mark.asyncio
async def test_get_export_analytics_response_distribution(ai_export_service):
    """Test response distribution analytics"""
    # Mock detailed analytics data
    mock_analytics = [
        MagicMock(
            suggestion_type='EXPORT_INTENT',
            user_response='ACCEPTED',
            response_time_ms=5000,
            suggested_format='CSV'
        ),
        MagicMock(
            suggestion_type='EXPORT_INTENT',
            user_response='ACCEPTED',
            response_time_ms=6000,
            suggested_format='JSON'
        ),
        MagicMock(
            suggestion_type='EXPORT_INTENT',
            user_response='REJECTED',
            response_time_ms=2000,
            suggested_format='CSV'
        ),
        MagicMock(
            suggestion_type='PROACTIVE_SUGGESTION',
            user_response='ACCEPTED',
            response_time_ms=8000,
            suggested_format='CSV'
        )
    ]

    mock_query = MagicMock()
    mock_query.all.return_value = mock_analytics
    ai_export_service.db_session.exec.return_value = mock_query

    # Execute
    result = await ai_export_service.get_export_analytics(
        database_name='test_db',
        days=7
    )

    # Assert distribution calculations
    assert 'responsesByType' in result
    assert 'responsesByFormat' in result

    # Check type distribution
    type_distribution = result['responsesByType']
    assert type_distribution['EXPORT_INTENT']['total'] == 3
    assert type_distribution['EXPORT_INTENT']['accepted'] == 2
    assert type_distribution['PROACTIVE_SUGGESTION']['total'] == 1
    assert type_distribution['PROACTIVE_SUGGESTION']['accepted'] == 1

    # Check format distribution
    format_distribution = result['responsesByFormat']
    assert format_distribution['CSV']['total'] == 3
    assert format_distribution['CSV']['accepted'] == 2
    assert format_distribution['JSON']['total'] == 1
    assert format_distribution['JSON']['accepted'] == 1


@pytest.mark.asyncio
async def test_get_export_analytics_error_handling(ai_export_service):
    """Test error handling in analytics retrieval"""
    # Mock database query to raise error
    ai_export_service.db_session.exec.side_effect = Exception("Database query error")

    # Execute and assert error
    with pytest.raises(Exception, match="Database query error"):
        await ai_export_service.get_export_analytics(
            database_name='test_db',
            days=7
        )
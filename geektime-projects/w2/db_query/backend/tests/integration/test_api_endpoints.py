"""Integration tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestDatabaseEndpoints:
    """Tests for database management endpoints."""

    def test_list_databases(self, client: TestClient):
        """Test listing databases."""
        response = client.get("/api/v1/dbs")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)


class TestQueryEndpoints:
    """Tests for query execution endpoints."""

    def test_query_invalid_database(self, client: TestClient):
        """Test querying a non-existent database."""
        response = client.post(
            "/api/v1/nonexistent/query",
            json={"sql": "SELECT 1"}
        )
        # Should return an error (404 or 500)
        assert response.status_code in [404, 500]

    def test_query_non_select_rejected(self, client: TestClient):
        """Test that non-SELECT queries are rejected."""
        response = client.post(
            "/api/v1/test_db/query",
            json={"sql": "DELETE FROM users"}
        )
        # Should return an error
        assert response.status_code in [400, 404, 500]
        data = response.json()
        assert "detail" in data


class TestHealthEndpoint:
    """Tests for health check and documentation endpoints."""

    def test_api_docs_accessible(self, client: TestClient):
        """Test that API documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_accessible(self, client: TestClient):
        """Test that OpenAPI schema is accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_root_response(self, client: TestClient):
        """Test root endpoint response."""
        response = client.get("/")
        # May redirect or return 404, both are acceptable
        assert response.status_code in [200, 404]

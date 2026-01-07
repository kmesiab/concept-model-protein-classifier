"""
Tests for admin audit log query endpoints.
"""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_admin_token():
    """Create a mock JWT token for admin access."""
    # This should be a valid JWT token in the actual implementation
    # For testing, we'll mock the verification
    return "mock_admin_token_12345"


@pytest.fixture
def admin_headers(mock_admin_token):
    """Create headers with admin authorization."""
    return {"Authorization": f"Bearer {mock_admin_token}"}


class TestAuditLogsEndpoint:
    """Tests for the admin audit logs endpoint."""

    @patch("app.admin_routes.get_session_service")
    @patch("app.admin_routes.get_audit_log_service")
    def test_query_audit_logs_success(
        self, mock_audit_service, mock_session_service, client, admin_headers
    ):
        """Test successful audit log query."""
        # Mock session service to return valid user
        mock_session = MagicMock()
        mock_session.verify_access_token.return_value = {"email": "admin@example.com"}
        mock_session_service.return_value = mock_session

        # Mock audit log service to return sample logs
        mock_audit = MagicMock()
        sample_logs = [
            {
                "timestamp": "2024-01-01T10:00:00Z",
                "api_key": "****1234",
                "sequence_length": 250,
                "processing_time_ms": 45.5,
                "status": "success",
                "error_code": None,
                "ip_address": "192.168.1.0/24",
            }
        ]
        mock_audit.query_logs.return_value = (sample_logs, None)
        mock_audit_service.return_value = mock_audit

        # Make request
        start_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        end_time = datetime.now(timezone.utc).isoformat()

        response = client.get(
            "/admin/audit-logs",
            params={"start_time": start_time, "end_time": end_time},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "logs" in data
        assert "total" in data
        assert data["total"] == 1
        assert len(data["logs"]) == 1

        log = data["logs"][0]
        assert log["api_key"] == "****1234"
        assert log["status"] == "success"
        assert log["sequence_length"] == 250

    @patch("app.admin_routes.get_session_service")
    def test_query_audit_logs_unauthorized(self, mock_session_service, client):
        """Test audit log query without authorization."""
        response = client.get(
            "/admin/audit-logs",
            params={
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z",
            },
        )

        assert response.status_code == 401
        assert "authorization" in response.json()["detail"].lower()

    @patch("app.admin_routes.get_session_service")
    def test_query_audit_logs_invalid_token(self, mock_session_service, client, admin_headers):
        """Test audit log query with invalid token."""
        # Mock session service to return None (invalid token)
        mock_session = MagicMock()
        mock_session.verify_access_token.return_value = None
        mock_session_service.return_value = mock_session

        start_time = "2024-01-01T00:00:00Z"
        end_time = "2024-01-02T00:00:00Z"

        response = client.get(
            "/admin/audit-logs",
            params={"start_time": start_time, "end_time": end_time},
            headers=admin_headers,
        )

        assert response.status_code == 401

    @patch("app.admin_routes.get_session_service")
    @patch("app.admin_routes.get_audit_log_service")
    def test_query_audit_logs_with_filters(
        self, mock_audit_service, mock_session_service, client, admin_headers
    ):
        """Test audit log query with filters."""
        # Mock session service
        mock_session = MagicMock()
        mock_session.verify_access_token.return_value = {"email": "admin@example.com"}
        mock_session_service.return_value = mock_session

        # Mock audit log service
        mock_audit = MagicMock()
        mock_audit.query_logs.return_value = ([], None)
        mock_audit_service.return_value = mock_audit

        # Make request with filters
        response = client.get(
            "/admin/audit-logs",
            params={
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z",
                "api_key": "key_xyz789",
                "status": "success",
                "limit": 50,
            },
            headers=admin_headers,
        )

        assert response.status_code == 200

        # Verify the service was called with correct parameters
        mock_audit.query_logs.assert_called_once()
        call_args = mock_audit.query_logs.call_args
        assert call_args.kwargs["api_key_id"] == "key_xyz789"
        assert call_args.kwargs["status"] == "success"
        assert call_args.kwargs["limit"] == 50

    @patch("app.admin_routes.get_session_service")
    def test_query_audit_logs_invalid_time_format(
        self, mock_session_service, client, admin_headers
    ):
        """Test audit log query with invalid timestamp format."""
        # Mock session service
        mock_session = MagicMock()
        mock_session.verify_access_token.return_value = {"email": "admin@example.com"}
        mock_session_service.return_value = mock_session

        response = client.get(
            "/admin/audit-logs",
            params={
                "start_time": "invalid-timestamp",
                "end_time": "2024-01-02T00:00:00Z",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "timestamp" in response.json()["detail"].lower()

    @patch("app.admin_routes.get_session_service")
    def test_query_audit_logs_invalid_time_range(self, mock_session_service, client, admin_headers):
        """Test audit log query with invalid time range (start >= end)."""
        # Mock session service
        mock_session = MagicMock()
        mock_session.verify_access_token.return_value = {"email": "admin@example.com"}
        mock_session_service.return_value = mock_session

        response = client.get(
            "/admin/audit-logs",
            params={
                "start_time": "2024-01-02T00:00:00Z",
                "end_time": "2024-01-01T00:00:00Z",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "start_time must be before end_time" in response.json()["detail"]

    @patch("app.admin_routes.get_session_service")
    def test_query_audit_logs_invalid_status(self, mock_session_service, client, admin_headers):
        """Test audit log query with invalid status filter."""
        # Mock session service
        mock_session = MagicMock()
        mock_session.verify_access_token.return_value = {"email": "admin@example.com"}
        mock_session_service.return_value = mock_session

        response = client.get(
            "/admin/audit-logs",
            params={
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z",
                "status": "invalid_status",
            },
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "status must be" in response.json()["detail"]

    @patch("app.admin_routes.get_session_service")
    @patch("app.admin_routes.get_audit_log_service")
    def test_query_audit_logs_pagination(
        self, mock_audit_service, mock_session_service, client, admin_headers
    ):
        """Test audit log query with pagination."""
        # Mock session service
        mock_session = MagicMock()
        mock_session.verify_access_token.return_value = {"email": "admin@example.com"}
        mock_session_service.return_value = mock_session

        # Mock audit log service with pagination token
        mock_audit = MagicMock()
        next_token = json.dumps({"event_id": "next_page_token"})
        mock_audit.query_logs.return_value = ([], next_token)
        mock_audit_service.return_value = mock_audit

        # Make request
        response = client.get(
            "/admin/audit-logs",
            params={
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z",
                "limit": 100,
            },
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["next_token"] == next_token

    @patch("app.admin_routes.get_session_service")
    @patch("app.admin_routes.get_audit_log_service")
    def test_query_audit_logs_limit_validation(
        self, mock_audit_service, mock_session_service, client, admin_headers
    ):
        """Test audit log query with limit exceeding max."""
        # Mock session service
        mock_session = MagicMock()
        mock_session.verify_access_token.return_value = {"email": "admin@example.com"}
        mock_session_service.return_value = mock_session

        # Mock audit log service
        mock_audit = MagicMock()
        mock_audit.query_logs.return_value = ([], None)
        mock_audit_service.return_value = mock_audit

        # Make request with limit > 1000 (should be capped to 1000)
        response = client.get(
            "/admin/audit-logs",
            params={
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-02T00:00:00Z",
                "limit": 2000,
            },
            headers=admin_headers,
        )

        # Query parameter validation happens at FastAPI level
        # limit > 1000 should be rejected by FastAPI validation
        assert response.status_code == 422  # Unprocessable Entity


class TestAuditLogService:
    """Tests for audit log service methods."""

    def test_mask_api_key(self):
        """Test API key masking."""
        from app.audit_log_service import AuditLogService

        assert AuditLogService._mask_api_key("pk_live_1234567890") == "****7890"
        assert AuditLogService._mask_api_key("short") == "****hort"
        assert AuditLogService._mask_api_key("") == "****"
        assert AuditLogService._mask_api_key(None) == "****"

    def test_mask_ip_address(self):
        """Test IP address masking."""
        from app.audit_log_service import AuditLogService

        # IPv4
        assert AuditLogService._mask_ip("192.168.1.100") == "192.168.1.0/24"
        assert AuditLogService._mask_ip("10.0.0.1") == "10.0.0.0/24"

        # IPv6
        assert "2001:db8:1234" in AuditLogService._mask_ip("2001:db8:1234:5678:90ab:cdef:1234:5678")

        # Invalid
        assert AuditLogService._mask_ip("") == "unknown"
        assert AuditLogService._mask_ip(None) == "unknown"

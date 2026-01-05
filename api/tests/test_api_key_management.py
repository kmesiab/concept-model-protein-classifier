"""
Tests for API key management and authentication endpoints.
"""

import pytest
from app.main import app
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def mock_session_service():
    """Mock session service."""
    with patch("app.auth_routes.get_session_service") as mock:
        yield mock.return_value


@pytest.fixture
def mock_email_service():
    """Mock email service."""
    with patch("app.auth_routes.get_email_service") as mock:
        yield mock.return_value


@pytest.fixture
def mock_api_key_service():
    """Mock API key service."""
    with patch("app.api_key_routes.get_api_key_service") as mock:
        yield mock.return_value


class TestAuthenticationEndpoints:
    """Tests for authentication endpoints."""

    def test_login_success(self, client, mock_session_service, mock_email_service):
        """Test successful magic link login request."""
        mock_session_service.create_magic_link_token.return_value = "test-token"

        # Mock async method
        async def mock_send_email(*args, **kwargs):
            return True

        mock_email_service.send_magic_link = mock_send_email

        response = client.post("/api/v1/auth/login", json={"email": "test@example.com"})

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Magic link sent to your email"
        assert data["email"] == "test@example.com"

    def test_login_invalid_email(self, client):
        """Test login with invalid email format."""
        response = client.post("/api/v1/auth/login", json={"email": "invalid-email"})

        assert response.status_code == 400
        assert "Invalid email" in response.json()["detail"]

    def test_verify_token_success(self, client, mock_session_service):
        """Test successful token verification."""
        mock_session_service.verify_magic_link_token.return_value = "test@example.com"
        mock_session_service.create_session.return_value = {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "token_type": "bearer",
            "expires_in": 3600,
        }

        response = client.post("/api/v1/auth/verify", json={"token": "test-token"})

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_verify_token_invalid(self, client, mock_session_service):
        """Test token verification with invalid token."""
        mock_session_service.verify_magic_link_token.return_value = None

        response = client.post("/api/v1/auth/verify", json={"token": "invalid-token"})

        assert response.status_code == 400
        assert "Invalid or expired" in response.json()["detail"]

    def test_refresh_token_success(self, client, mock_session_service):
        """Test successful token refresh."""
        mock_session_service.refresh_access_token.return_value = {
            "access_token": "new-access-token",
            "token_type": "bearer",
            "expires_in": 3600,
        }

        response = client.post(
            "/api/v1/auth/refresh", headers={"X-Refresh-Token": "refresh-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_missing_header(self, client):
        """Test refresh without refresh token header."""
        response = client.post("/api/v1/auth/refresh")

        assert response.status_code == 401
        assert "Missing refresh token" in response.json()["detail"]


class TestAPIKeyManagementEndpoints:
    """Tests for API key management endpoints."""

    @pytest.fixture
    def auth_headers(self, mock_session_service):
        """Create authentication headers with mocked session."""
        with patch("app.api_key_routes.get_session_service") as mock:
            mock.return_value.verify_access_token.return_value = {
                "email": "test@example.com",
                "session_id": "test-session",
            }
            yield {"Authorization": "Bearer test-token"}

    def test_register_api_key_success(
        self, client, mock_api_key_service, mock_email_service, auth_headers
    ):
        """Test successful API key registration."""
        with patch("app.api_key_routes.get_session_service") as mock_session:
            mock_session.return_value.verify_access_token.return_value = {
                "email": "test@example.com",
                "session_id": "test-session",
            }

            mock_api_key_service.generate_api_key.return_value = {
                "api_key": "pk_live_test123",
                "api_key_id": "key_abc",
                "created_at": "2024-01-01T00:00:00Z",
                "label": "Test API Key",
            }

            # Mock async method
            async def mock_send_notification(*args, **kwargs):
                return True

            mock_email_service.send_api_key_created_notification = mock_send_notification

            response = client.post(
                "/api/v1/api-keys/register",
                json={"label": "Test API Key"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["api_key"] == "pk_live_test123"
            assert data["api_key_id"] == "key_abc"
            assert data["label"] == "Test API Key"

    def test_register_api_key_unauthorized(self, client):
        """Test API key registration without authentication."""
        response = client.post("/api/v1/api-keys/register", json={"label": "Test"})

        assert response.status_code == 401

    def test_list_api_keys_success(self, client, mock_api_key_service, auth_headers):
        """Test listing API keys."""
        with patch("app.api_key_routes.get_session_service") as mock_session:
            mock_session.return_value.verify_access_token.return_value = {
                "email": "test@example.com",
                "session_id": "test-session",
            }

            mock_api_key_service.list_api_keys.return_value = [
                {
                    "api_key_id": "key_abc",
                    "label": "Production API",
                    "status": "active",
                    "created_at": "2024-01-01T00:00:00Z",
                    "last_used_at": None,
                    "tier": "free",
                }
            ]

            response = client.get("/api/v1/api-keys/list", headers=auth_headers)

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1
            assert len(data["keys"]) == 1
            assert data["keys"][0]["api_key_id"] == "key_abc"

    def test_rotate_api_key_success(self, client, mock_api_key_service, auth_headers):
        """Test API key rotation."""
        with patch("app.api_key_routes.get_session_service") as mock_session:
            mock_session.return_value.verify_access_token.return_value = {
                "email": "test@example.com",
                "session_id": "test-session",
            }

            mock_api_key_service.rotate_api_key.return_value = {
                "api_key": "pk_live_new123",
                "api_key_id": "key_xyz",
                "created_at": "2024-01-01T00:00:00Z",
                "label": "Rotated API Key",
            }

            response = client.post(
                "/api/v1/api-keys/rotate",
                json={"api_key_id": "key_abc"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["api_key"] == "pk_live_new123"

    def test_revoke_api_key_success(
        self, client, mock_api_key_service, mock_email_service, auth_headers
    ):
        """Test API key revocation."""
        with patch("app.api_key_routes.get_session_service") as mock_session:
            mock_session.return_value.verify_access_token.return_value = {
                "email": "test@example.com",
                "session_id": "test-session",
            }

            mock_api_key_service.revoke_api_key.return_value = True
            mock_api_key_service.list_api_keys.return_value = [
                {
                    "api_key_id": "key_abc",
                    "label": "Revoked Key",
                    "status": "revoked",
                    "created_at": "2024-01-01T00:00:00Z",
                    "last_used_at": None,
                    "tier": "free",
                }
            ]

            # Mock async method
            async def mock_send_notification(*args, **kwargs):
                return True

            mock_email_service.send_api_key_revoked_notification = mock_send_notification

            response = client.post(
                "/api/v1/api-keys/revoke",
                json={"api_key_id": "key_abc"},
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["revoked"] is True
            assert data["api_key_id"] == "key_abc"

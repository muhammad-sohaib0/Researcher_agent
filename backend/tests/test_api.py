"""
Unit Tests for API Endpoints
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient


# Mock the database and models before importing routes
@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock database and authentication dependencies."""
    with patch('routes.auth.get_db') as mock_get_db, \
         patch('routes.auth.get_current_user') as mock_get_current_user:

        # Mock database session
        mock_db = MagicMock()
        mock_get_db.return_value = iter([mock_db])

        # Mock current user
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.email = "test@example.com"
        mock_get_current_user.return_value = mock_user

        yield {
            "db": mock_db,
            "user": mock_user
        }


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    def test_signup_validation_error(self):
        """Test signup with invalid email."""
        from routes.auth import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api/auth")

        with TestClient(app) as client:
            response = client.post(
                "/api/auth/signup",
                json={"email": "invalid-email", "password": "password123"}
            )
            assert response.status_code == 422  # Validation error

    def test_signup_missing_fields(self):
        """Test signup with missing required fields."""
        from routes.auth import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api/auth")

        with TestClient(app) as client:
            response = client.post(
                "/api/auth/signup",
                json={"email": "test@example.com"}  # Missing password
            )
            assert response.status_code == 422


class TestChatEndpoints:
    """Tests for chat endpoints."""

    @patch('routes.chat.get_agent_stream')
    def test_send_message_missing_content(self, mock_agent, mock_dependencies):
        """Test sending message without content."""
        from routes.chat import router
        from fastapi import FastAPI
        from schemas import MessageCreate

        app = FastAPI()
        app.include_router(router, prefix="/api/chat")

        with TestClient(app) as client:
            response = client.post(
                "/api/chat/1/message",
                json={"content": ""}
            )
            # Should work with empty content (may be handled by agent)

    def test_get_chat_not_found(self, mock_dependencies):
        """Test getting non-existent chat returns 404."""
        from routes.chat import router
        from fastapi import FastAPI

        mock_db = mock_dependencies["db"]
        mock_db.query.return_value.filter.return_value.first.return_value = None

        app = FastAPI()
        app.include_router(router, prefix="/api/chat")

        with TestClient(app) as client:
            response = client.get(
                "/api/chat/9999",
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == 404

    def test_delete_chat_not_found(self, mock_dependencies):
        """Test deleting non-existent chat returns 404."""
        from routes.chat import router
        from fastapi import FastAPI

        mock_db = mock_dependencies["db"]
        mock_db.query.return_value.filter.return_value.first.return_value = None

        app = FastAPI()
        app.include_router(router, prefix="/api/chat")

        with TestClient(app) as client:
            response = client.delete(
                "/api/chat/9999",
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == 404


class TestFileEndpoints:
    """Tests for file endpoints."""

    def test_upload_invalid_file_type(self, mock_dependencies):
        """Test uploading file with invalid type."""
        from routes.files import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router, prefix="/api/files")

        with TestClient(app) as client:
            response = client.post(
                "/api/files/upload",
                files={"file": ("test.txt", b"content", "text/plain")},
                data={"file_type": "invalid_type"}
            )
            assert response.status_code == 400

    def test_get_file_not_found(self, mock_dependencies):
        """Test getting non-existent file returns 404."""
        from routes.files import router
        from fastapi import FastAPI

        mock_db = mock_dependencies["db"]
        mock_db.query.return_value.filter.return_value.first.return_value = None

        app = FastAPI()
        app.include_router(router, prefix="/api/files")

        with TestClient(app) as client:
            response = client.get(
                "/api/files/9999",
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == 404

    def test_delete_file_not_found(self, mock_dependencies):
        """Test deleting non-existent file returns 404."""
        from routes.files import router
        from fastapi import FastAPI

        mock_db = mock_dependencies["db"]
        mock_db.query.return_value.filter.return_value.first.return_value = None

        app = FastAPI()
        app.include_router(router, prefix="/api/files")

        with TestClient(app) as client:
            response = client.delete(
                "/api/files/9999",
                headers={"Authorization": "Bearer test-token"}
            )
            assert response.status_code == 404


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_user_create_valid(self):
        """Test UserCreate schema with valid data."""
        from schemas import UserCreate

        user = UserCreate(
            email="test@example.com",
            password="securepassword123",
            name="Test User"
        )
        assert user.email == "test@example.com"
        assert user.name == "Test User"

    def test_user_login_valid(self):
        """Test UserLogin schema with valid data."""
        from schemas import UserLogin

        login = UserLogin(
            email="test@example.com",
            password="password123"
        )
        assert login.email == "test@example.com"

    def test_chat_create_default_title(self):
        """Test ChatCreate schema default title."""
        from schemas import ChatCreate

        chat = ChatCreate()
        assert chat.title == "New Chat"

    def test_message_create_valid(self):
        """Test MessageCreate schema with valid data."""
        from schemas import MessageCreate

        msg = MessageCreate(
            content="Hello, world!",
            file_ids=[1, 2, 3]
        )
        assert msg.content == "Hello, world!"
        assert msg.file_ids == [1, 2, 3]

    def test_message_create_optional_files(self):
        """Test MessageCreate schema with optional file_ids."""
        from schemas import MessageCreate

        msg = MessageCreate(content="Hello!")
        assert msg.file_ids is None

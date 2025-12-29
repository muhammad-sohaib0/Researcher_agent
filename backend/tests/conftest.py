"""Pytest configuration and fixtures."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def backend_path():
    """Return backend path."""
    return str(Path(__file__).parent.parent)


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    with patch('core.config.get_settings') as mock:
        settings = MagicMock()
        settings.database_url = "sqlite:///./test.db"
        settings.jwt_secret_key = "test-secret-key"
        settings.jwt_algorithm = "HS256"
        settings.access_token_expire_minutes = 60 * 24 * 7
        settings.log_level = "DEBUG"
        settings.rate_limit_requests = 100
        settings.rate_limit_window_seconds = 60
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = MagicMock()
    return session


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    user = MagicMock()
    user.id = 1
    user.email = "test@example.com"
    user.name = "Test User"
    return user


@pytest.fixture
def sample_chat():
    """Sample chat data."""
    chat = MagicMock()
    chat.id = 1
    chat.title = "Test Chat"
    chat.user_id = 1
    chat.created_at = "2024-01-01T00:00:00"
    chat.updated_at = "2024-01-01T00:00:00"
    return chat


@pytest.fixture
def sample_message():
    """Sample message data."""
    message = MagicMock()
    message.id = 1
    message.chat_id = 1
    message.role = "user"
    message.content = "Hello, world!"
    message.tool_outputs = None
    message.created_at = "2024-01-01T00:00:00"
    return message


@pytest.fixture
def sample_bookmark():
    """Sample bookmark data."""
    bookmark = MagicMock()
    bookmark.id = 1
    bookmark.user_id = 1
    bookmark.paper_title = "Test Paper"
    bookmark.paper_url = "https://example.com/paper"
    bookmark.paper_doi = "10.1234/test"
    bookmark.paper_authors = '["Author One", "Author Two"]'
    bookmark.paper_year = 2024
    bookmark.paper_citations = 10
    bookmark.notes = "Test notes"
    bookmark.tags = "machine-learning,ai"
    bookmark.created_at = "2024-01-01T00:00:00"
    return bookmark

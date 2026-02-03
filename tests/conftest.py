"""
Pytest configuration and fixtures.

Provides:
- Test database setup
- Mock Cosmos DB client
- Common test fixtures
"""

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock

from fastapi.testclient import TestClient

from src.config.settings import Settings, Environment


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Create test settings."""
    return Settings(
        environment=Environment.TESTING,
        debug=True,
        cosmos_use_emulator=True,
        llm_provider="openai",
        openai_api_key="test-key",
        rate_limit_enabled=False
    )


@pytest.fixture
def mock_cosmos_client():
    """Mock Cosmos DB client."""
    client = Mock()
    
    # Mock database
    database = Mock()
    client.get_database_client.return_value = database
    
    # Mock container
    container = Mock()
    database.get_container_client.return_value = container
    
    # Mock operations
    container.create_item = AsyncMock()
    container.read_item = AsyncMock()
    container.upsert_item = AsyncMock()
    container.delete_item = AsyncMock()
    container.query_items = Mock(return_value=[])
    
    return client


@pytest.fixture
def mock_user_data():
    """Sample user data for testing."""
    return {
        "id": "test-user-123",
        "userId": "test-user-123",
        "email": "test@example.com",
        "name": "Test User",
        "skills": ["Python", "FastAPI"],
        "experienceLevel": "Mid",
        "stats": {
            "totalInterviews": 5,
            "averageScore": 85.5
        }
    }


@pytest.fixture
def mock_session_data():
    """Sample session data for testing."""
    return {
        "id": "test-session-123",
        "sessionId": "test-session-123",
        "userId": "test-user-123",
        "sessionType": "interview",
        "status": "active",
        "messages": [],
        "config": {
            "difficulty": 3,
            "target_role": "Backend Engineer"
        }
    }


@pytest.fixture
async def test_client(test_settings) -> AsyncGenerator[TestClient, None]:
    """Create test client."""
    # Import here to avoid circular imports
    from app.main import app
    
    # Override settings
    app.dependency_overrides = {}
    
    with TestClient(app) as client:
        yield client


class MockCosmosContainer:
    """Mock Cosmos DB container for testing."""
    
    def __init__(self):
        self.items = {}
    
    async def create_item(self, body: dict):
        """Mock create item."""
        item_id = body.get("id")
        if item_id in self.items:
            raise Exception("Item already exists")
        
        self.items[item_id] = body
        return body
    
    async def read_item(self, item: str, partition_key: str):
        """Mock read item."""
        if item not in self.items:
            raise Exception("Item not found")
        
        return self.items[item]
    
    async def upsert_item(self, body: dict):
        """Mock upsert item."""
        item_id = body.get("id")
        self.items[item_id] = body
        return body
    
    async def delete_item(self, item: str, partition_key: str):
        """Mock delete item."""
        if item in self.items:
            del self.items[item]
    
    async def query_items(self, query: str, **kwargs):
        """Mock query items."""
        return list(self.items.values())


@pytest.fixture
def mock_cosmos_container():
    """Create mock Cosmos DB container."""
    return MockCosmosContainer()

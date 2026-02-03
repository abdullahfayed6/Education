"""
Unit tests for user repository.

Tests:
- CRUD operations
- Query operations
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, Mock

from src.repositories.user_repository import UserRepository, UserProfile


@pytest.mark.asyncio
class TestUserRepository:
    """Test user repository operations."""
    
    async def test_create_user(self, mock_cosmos_container):
        """Test creating a new user."""
        # Arrange
        repo = UserRepository()
        repo._container = mock_cosmos_container
        
        user = UserProfile(
            id="user123",
            userId="user123",
            email="test@example.com",
            name="Test User",
            skills=["Python", "FastAPI"]
        )
        
        # Act
        created_user = await repo.create(user)
        
        # Assert
        assert created_user.id == "user123"
        assert created_user.email == "test@example.com"
        assert "Python" in created_user.skills
    
    async def test_get_by_user_id(self, mock_cosmos_container, mock_user_data):
        """Test retrieving user by ID."""
        # Arrange
        repo = UserRepository()
        repo._container = mock_cosmos_container
        mock_cosmos_container.items["test-user-123"] = mock_user_data
        
        # Act
        user = await repo.get_by_user_id("test-user-123")
        
        # Assert
        assert user is not None
        assert user.userId == "test-user-123"
        assert user.email == "test@example.com"
    
    async def test_update_skills(self, mock_cosmos_container, mock_user_data):
        """Test updating user skills."""
        # Arrange
        repo = UserRepository()
        repo._container = mock_cosmos_container
        mock_cosmos_container.items["test-user-123"] = mock_user_data
        
        new_skills = ["Python", "FastAPI", "Azure", "Cosmos DB"]
        
        # Act
        updated_user = await repo.update_skills("test-user-123", new_skills)
        
        # Assert
        assert len(updated_user.skills) == 4
        assert "Azure" in updated_user.skills
        assert "Cosmos DB" in updated_user.skills
    
    async def test_increment_interview_count(self, mock_cosmos_container, mock_user_data):
        """Test incrementing interview count."""
        # Arrange
        repo = UserRepository()
        repo._container = mock_cosmos_container
        mock_cosmos_container.items["test-user-123"] = mock_user_data
        
        initial_count = mock_user_data["stats"]["totalInterviews"]
        
        # Act
        updated_user = await repo.increment_interview_count("test-user-123")
        
        # Assert
        assert updated_user.stats["totalInterviews"] == initial_count + 1
        assert updated_user.stats["lastActivityDate"] is not None
    
    async def test_update_stats(self, mock_cosmos_container, mock_user_data):
        """Test updating user statistics."""
        # Arrange
        repo = UserRepository()
        repo._container = mock_cosmos_container
        mock_cosmos_container.items["test-user-123"] = mock_user_data
        
        # Act
        updated_user = await repo.update_stats("test-user-123", new_score=90.0)
        
        # Assert
        assert updated_user.stats["totalInterviews"] == 6  # Was 5, now 6
        assert updated_user.stats["averageScore"] > 85.5  # Should increase
    
    async def test_user_not_found(self, mock_cosmos_container):
        """Test handling user not found."""
        # Arrange
        repo = UserRepository()
        repo._container = mock_cosmos_container
        
        # Act
        user = await repo.get_by_user_id("nonexistent-user")
        
        # Assert
        assert user is None

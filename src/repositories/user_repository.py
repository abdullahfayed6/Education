"""
User Repository for Azure Cosmos DB

Handles user profile data with:
- Partition key: /userId
- Embedded profile data (skills, preferences, history)
- Optimized queries for single-user access patterns
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from src.repositories.base_repository import BaseRepository
from src.config.settings import settings

logger = logging.getLogger(__name__)


class UserProfile(BaseModel):
    """User profile entity."""
    
    id: str = Field(..., description="User ID (also used as document ID)")
    userId: str = Field(..., description="User ID (partition key)")
    email: str
    name: str
    
    # Profile Information (Embedded for single-item retrieval)
    skills: list[str] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    experienceLevel: str = "Junior"  # Junior, Mid, Senior
    targetRoles: list[str] = Field(default_factory=list)
    
    # Preferences
    preferences: dict[str, Any] = Field(default_factory=dict)
    
    # Statistics (frequently accessed together)
    stats: dict[str, Any] = Field(
        default_factory=lambda: {
            "totalInterviews": 0,
            "totalSessions": 0,
            "averageScore": 0.0,
            "lastActivityDate": None
        }
    )
    
    # Metadata
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    isActive: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "user123",
                "userId": "user123",
                "email": "user@example.com",
                "name": "John Doe",
                "skills": ["Python", "FastAPI", "React"],
                "interests": ["AI", "Web Development"],
                "experienceLevel": "Mid",
                "targetRoles": ["Backend Engineer", "Full Stack Developer"]
            }
        }


class UserRepository(BaseRepository[UserProfile]):
    """Repository for user profile operations."""
    
    def __init__(self):
        """Initialize user repository."""
        super().__init__(
            container_name=settings.container_users,
            partition_key_path="/userId"
        )
    
    def to_dict(self, entity: UserProfile) -> dict[str, Any]:
        """Convert UserProfile to dictionary."""
        data = entity.model_dump(exclude_none=True)
        # Ensure id and userId are the same for simplicity
        data['id'] = entity.userId
        data['userId'] = entity.userId
        return data
    
    def from_dict(self, data: dict[str, Any]) -> UserProfile:
        """Convert dictionary to UserProfile."""
        return UserProfile(**data)
    
    async def get_by_user_id(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by user ID.
        
        Single-partition read (most efficient).
        
        Args:
            user_id: User ID
            
        Returns:
            UserProfile if found, None otherwise
        """
        return await self.read(item_id=user_id, partition_key=user_id)
    
    async def get_by_email(self, email: str) -> Optional[UserProfile]:
        """
        Get user profile by email.
        
        Note: This is a cross-partition query.
        Consider adding a secondary index or caching frequently accessed emails.
        
        Args:
            email: User email
            
        Returns:
            UserProfile if found, None otherwise
        """
        results = await self.find_by_field(
            field_name="email",
            field_value=email,
            max_items=1
        )
        return results[0] if results else None
    
    async def update_skills(self, user_id: str, skills: list[str]) -> UserProfile:
        """
        Update user skills.
        
        Args:
            user_id: User ID
            skills: New skills list
            
        Returns:
            Updated UserProfile
        """
        user = await self.get_by_user_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        user.skills = skills
        return await self.update(user)
    
    async def increment_interview_count(self, user_id: str) -> UserProfile:
        """
        Increment user's interview count.
        
        Args:
            user_id: User ID
            
        Returns:
            Updated UserProfile
        """
        user = await self.get_by_user_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        user.stats["totalInterviews"] = user.stats.get("totalInterviews", 0) + 1
        user.stats["lastActivityDate"] = datetime.utcnow().isoformat()
        
        return await self.update(user)
    
    async def update_stats(
        self,
        user_id: str,
        new_score: float
    ) -> UserProfile:
        """
        Update user statistics with new interview score.
        
        Args:
            user_id: User ID
            new_score: New interview score (0-100)
            
        Returns:
            Updated UserProfile
        """
        user = await self.get_by_user_id(user_id)
        if not user:
            raise ValueError(f"User not found: {user_id}")
        
        # Update statistics
        total_interviews = user.stats.get("totalInterviews", 0)
        current_avg = user.stats.get("averageScore", 0.0)
        
        # Calculate new average
        new_avg = ((current_avg * total_interviews) + new_score) / (total_interviews + 1)
        
        user.stats["totalInterviews"] = total_interviews + 1
        user.stats["averageScore"] = round(new_avg, 2)
        user.stats["lastActivityDate"] = datetime.utcnow().isoformat()
        
        return await self.update(user)

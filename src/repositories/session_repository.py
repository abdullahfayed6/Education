"""
Session Repository for Azure Cosmos DB

Handles interview/chat session data with:
- Hierarchical Partition Key: [/userId, /sessionId]
- Embedded conversation history (up to 2MB limit)
- TTL support for automatic cleanup
"""

from __future__ import annotations

import logging
from typing import Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

from src.repositories.base_repository import BaseRepository
from src.config.settings import settings

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """Session status types."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class SessionType(str, Enum):
    """Session type."""
    INTERVIEW = "interview"
    CAREER_ADVICE = "career_advice"
    CV_REVIEW = "cv_review"
    TASK_SIMULATION = "task_simulation"
    PROFILING = "profiling"


class Message(BaseModel):
    """Chat message in session."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    """Session entity with embedded conversation history."""
    
    id: str = Field(..., description="Session ID (document ID)")
    sessionId: str = Field(..., description="Session ID (partition key part 2)")
    userId: str = Field(..., description="User ID (partition key part 1)")
    
    # Session Info
    sessionType: SessionType
    status: SessionStatus = SessionStatus.ACTIVE
    title: Optional[str] = None
    
    # Configuration
    config: dict[str, Any] = Field(default_factory=dict)
    
    # Embedded Messages (access pattern: always retrieve full conversation)
    # Note: Monitor size - Cosmos DB has 2MB item limit
    messages: list[Message] = Field(default_factory=list)
    
    # Session State
    currentState: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    
    # Results/Metrics
    results: Optional[dict[str, Any]] = None
    score: Optional[float] = None
    
    # Timestamps
    startedAt: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completedAt: Optional[str] = None
    createdAt: Optional[str] = None
    updatedAt: Optional[str] = None
    
    # TTL for automatic cleanup (seconds since epoch)
    ttl: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "session123",
                "sessionId": "session123",
                "userId": "user123",
                "sessionType": "interview",
                "status": "active",
                "title": "Backend Engineer Interview",
                "config": {"difficulty": 3, "target_role": "Backend Engineer"}
            }
        }


class SessionRepository(BaseRepository[Session]):
    """Repository for session operations."""
    
    def __init__(self):
        """Initialize session repository."""
        super().__init__(
            container_name=settings.container_sessions,
            partition_key_path="/userId"  # Primary partition key
        )
        # Note: Hierarchical partition key [/userId, /sessionId] 
        # should be configured during container creation
    
    def to_dict(self, entity: Session) -> dict[str, Any]:
        """Convert Session to dictionary."""
        data = entity.model_dump(exclude_none=True)
        
        # Convert Message objects to dicts
        if 'messages' in data:
            data['messages'] = [
                msg.model_dump() if isinstance(msg, Message) else msg
                for msg in data['messages']
            ]
        
        return data
    
    def from_dict(self, data: dict[str, Any]) -> Session:
        """Convert dictionary to Session."""
        # Convert message dicts to Message objects
        if 'messages' in data:
            data['messages'] = [
                Message(**msg) if isinstance(msg, dict) else msg
                for msg in data['messages']
            ]
        
        return Session(**data)
    
    async def get_user_sessions(
        self,
        user_id: str,
        status: Optional[SessionStatus] = None,
        session_type: Optional[SessionType] = None,
        max_items: int = 50
    ) -> list[Session]:
        """
        Get all sessions for a user.
        
        Single-partition query (efficient).
        
        Args:
            user_id: User ID
            status: Filter by status
            session_type: Filter by type
            max_items: Maximum results
            
        Returns:
            List of sessions
        """
        query_parts = ["SELECT * FROM c WHERE c.userId = @userId"]
        parameters = [{"name": "@userId", "value": user_id}]
        
        if status:
            query_parts.append("AND c.status = @status")
            parameters.append({"name": "@status", "value": status.value})
        
        if session_type:
            query_parts.append("AND c.sessionType = @sessionType")
            parameters.append({"name": "@sessionType", "value": session_type.value})
        
        query_parts.append("ORDER BY c.startedAt DESC")
        query = " ".join(query_parts)
        
        return await self.query(
            query=query,
            parameters=parameters,
            partition_key=user_id,  # Single-partition query
            max_items=max_items
        )
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[Session]:
        """
        Get specific session.
        
        Args:
            session_id: Session ID
            user_id: User ID (partition key)
            
        Returns:
            Session if found
        """
        return await self.read(item_id=session_id, partition_key=user_id)
    
    async def add_message(
        self,
        session_id: str,
        user_id: str,
        message: Message
    ) -> Session:
        """
        Add message to session.
        
        Args:
            session_id: Session ID
            user_id: User ID
            message: Message to add
            
        Returns:
            Updated session
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.messages.append(message)
        
        # Check size warning (approaching 2MB limit)
        estimated_size = len(str(session.model_dump()))
        if estimated_size > 1_500_000:  # 1.5MB warning
            logger.warning(
                f"Session {session_id} approaching size limit: "
                f"{estimated_size / 1_000_000:.2f}MB. "
                "Consider archiving older messages."
            )
        
        return await self.update(session)
    
    async def update_status(
        self,
        session_id: str,
        user_id: str,
        status: SessionStatus,
        results: Optional[dict[str, Any]] = None
    ) -> Session:
        """
        Update session status.
        
        Args:
            session_id: Session ID
            user_id: User ID
            status: New status
            results: Final results (if completing)
            
        Returns:
            Updated session
        """
        session = await self.get_session(session_id, user_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")
        
        session.status = status
        
        if status == SessionStatus.COMPLETED:
            session.completedAt = datetime.utcnow().isoformat()
            if results:
                session.results = results
        
        return await self.update(session)
    
    async def get_active_sessions_count(self, user_id: str) -> int:
        """
        Count active sessions for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Count of active sessions
        """
        query = """
        SELECT VALUE COUNT(1) 
        FROM c 
        WHERE c.userId = @userId AND c.status = @status
        """
        parameters = [
            {"name": "@userId", "value": user_id},
            {"name": "@status", "value": SessionStatus.ACTIVE.value}
        ]
        
        results = await self.query(
            query=query,
            parameters=parameters,
            partition_key=user_id,
            max_items=1
        )
        
        return results[0] if results else 0

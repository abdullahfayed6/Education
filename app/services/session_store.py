"""Session store for managing interview sessions."""
from __future__ import annotations

from typing import Dict, Optional
from uuid import UUID

from app.models.interview_schemas import InterviewConfig, FinalReport
from app.services.orchestrator import InterviewOrchestrator


class InterviewSessionStore:
    """In-memory store for active interview sessions."""
    
    _instance: Optional["InterviewSessionStore"] = None
    
    def __new__(cls) -> "InterviewSessionStore":
        """Singleton pattern for session store."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._sessions = {}
            cls._instance._reports = {}
        return cls._instance
    
    def create_session(
        self,
        user_id: str,
        config: InterviewConfig,
    ) -> InterviewOrchestrator:
        """Create a new interview session."""
        orchestrator = InterviewOrchestrator(config=config, user_id=user_id)
        self._sessions[orchestrator.session_id] = orchestrator
        return orchestrator
    
    def get_session(self, session_id: UUID) -> Optional[InterviewOrchestrator]:
        """Get an existing session by ID."""
        return self._sessions.get(session_id)
    
    def remove_session(self, session_id: UUID) -> bool:
        """Remove a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def store_report(self, session_id: UUID, report: FinalReport) -> None:
        """Store a final report."""
        self._reports[session_id] = report
    
    def get_report(self, session_id: UUID) -> Optional[FinalReport]:
        """Get a stored report."""
        return self._reports.get(session_id)
    
    def list_sessions(self, user_id: Optional[str] = None) -> list:
        """List all sessions, optionally filtered by user."""
        sessions = []
        for session_id, orchestrator in self._sessions.items():
            if user_id is None or orchestrator.user_id == user_id:
                sessions.append({
                    "session_id": session_id,
                    "user_id": orchestrator.user_id,
                    "current_state": orchestrator.current_state,
                    "is_complete": orchestrator.is_complete,
                })
        return sessions
    
    def clear_all(self) -> None:
        """Clear all sessions (useful for testing)."""
        self._sessions.clear()
        self._reports.clear()


# Global session store instance
session_store = InterviewSessionStore()

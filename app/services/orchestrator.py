"""Interview Orchestrator - Coordinates all agents for interview flow."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from app.agents.interviewer import InterviewerAgent
from app.agents.answer_analyzer import AnswerAnalyzerAgent
from app.agents.communication_coach import CommunicationCoachAgent
from app.agents.difficulty_engine import DifficultyEngineAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.report_generator import ReportGeneratorAgent
from app.agents.session_manager import SessionManagerAgent
from app.models.interview_schemas import (
    AnswerEvaluation,
    CommunicationAnalysis,
    DifficultyAdjustment,
    FinalReport,
    InterviewConfig,
    InterviewMemory,
    InterviewSession,
    InterviewState,
    QuestionAnswer,
    StateTransition,
)
from app.graph.interview_state import STATE_QUESTION_LIMITS, get_next_state

logger = logging.getLogger(__name__)


class InterviewOrchestrator:
    """Orchestrates the multi-agent interview system."""
    
    def __init__(
        self,
        config: InterviewConfig,
        user_id: str,
        use_llm_for_transitions: bool = False,  # Use simple logic by default
    ):
        """Initialize the orchestrator with configuration."""
        self.config = config
        self.user_id = user_id
        self.use_llm_for_transitions = use_llm_for_transitions
        
        # Initialize session
        self.session = InterviewSession(
            session_id=uuid4(),
            user_id=user_id,
            config=config,
            current_state=InterviewState.INTRO,
            current_difficulty=config.difficulty,
        )
        
        # Track questions per state
        self._questions_per_state: Dict[InterviewState, int] = {
            state: 0 for state in InterviewState
        }
        
        # Initialize agents
        self.interviewer = InterviewerAgent()
        self.analyzer = AnswerAnalyzerAgent()
        self.coach = CommunicationCoachAgent()
        self.difficulty_engine = DifficultyEngineAgent()
        self.memory_agent = MemoryAgent()
        self.report_generator = ReportGeneratorAgent()
        self.session_manager = SessionManagerAgent()
    
    @property
    def session_id(self) -> UUID:
        """Get the session ID."""
        return self.session.session_id
    
    @property
    def current_state(self) -> InterviewState:
        """Get the current interview state."""
        return self.session.current_state
    
    @property
    def is_complete(self) -> bool:
        """Check if the interview is complete."""
        return self.session.is_complete
    
    def calculate_average_score(self) -> float:
        """Calculate average score from all evaluations."""
        if not self.session.evaluations:
            return 0.0
        return sum(e.average_score for e in self.session.evaluations) / len(self.session.evaluations)
    
    async def start_interview(self) -> str:
        """Start the interview and generate the first question."""
        logger.info(f"Starting interview session {self.session.session_id} for user {self.user_id}")
        
        # Generate first question
        question = await self.interviewer.generate_question(
            config=self.config,
            current_state=self.session.current_state,
            difficulty=self.session.current_difficulty,
            questions_asked=self.session.questions_asked,
            memory=self.session.memory,
        )
        
        logger.info(f"Generated first question: {question[:100]}...")
        return question
    
    def start_interview_sync(self) -> str:
        """Synchronous version of start_interview."""
        logger.info(f"Starting interview session {self.session.session_id} for user {self.user_id}")
        
        # Generate first question
        question = self.interviewer.generate_question_sync(
            config=self.config,
            current_state=self.session.current_state,
            difficulty=self.session.current_difficulty,
            questions_asked=self.session.questions_asked,
            memory=self.session.memory,
        )
        
        logger.info(f"Generated first question: {question[:100]}...")
        return question
    
    async def process_answer(
        self,
        question: str,
        answer: str,
    ) -> Dict:
        """Process a candidate's answer through the evaluation pipeline."""
        logger.info(f"Processing answer for session {self.session.session_id}")
        
        # 1. Analyze the answer
        evaluation = await self.analyzer.evaluate(
            question=question,
            answer=answer,
            config=self.config,
            difficulty=self.session.current_difficulty,
            current_state=self.session.current_state,
        )
        
        # 2. Store the Q&A pair
        qa_pair = QuestionAnswer(
            question=question,
            answer=answer,
            state=self.session.current_state,
            difficulty=self.session.current_difficulty,
            evaluation=evaluation,
        )
        self.session.answers.append(qa_pair)
        self.session.evaluations.append(evaluation)
        self.session.questions_asked += 1
        self._questions_per_state[self.session.current_state] += 1
        
        # 3. Update memory
        self.session.memory = self.memory_agent.update_simple(
            current_memory=self.session.memory,
            new_evaluation=evaluation,
            question=question,
            all_evaluations=self.session.evaluations,
        )
        
        # 4. Analyze communication patterns (if enough answers)
        comm_feedback = None
        if len(self.session.answers) >= 2:
            comm_feedback = await self.coach.analyze(
                answers=self.session.answers,
                communication_strictness=self.config.communication_strictness,
            )
        
        # 5. Adjust difficulty
        difficulty_adjustment = await self.difficulty_engine.adjust(
            evaluations=self.session.evaluations,
            current_difficulty=self.session.current_difficulty,
            current_state=self.session.current_state,
        )
        self.session.current_difficulty = difficulty_adjustment.new_difficulty
        
        # 6. Check state transition
        if self.use_llm_for_transitions:
            transition = await self.session_manager.check_transition(
                current_state=self.session.current_state,
                questions_in_state=self._questions_per_state[self.session.current_state],
                total_questions=self.session.questions_asked,
                average_score=self.calculate_average_score(),
                performance_trend=self.session.memory.performance_trend,
            )
        else:
            transition = self.session_manager.check_transition_simple(
                current_state=self.session.current_state,
                questions_in_state=self._questions_per_state[self.session.current_state],
            )
        
        # 7. Apply state transition if needed
        next_question = None
        if transition.should_transition:
            self.session.current_state = transition.next_state
            self._questions_per_state[transition.next_state] = 0
        
        # 8. Check if interview is complete
        if self.session.current_state == InterviewState.FEEDBACK:
            self.session.is_complete = True
            self.session.overall_score = self.calculate_average_score()
        else:
            # 9. Generate next question
            next_question = await self.interviewer.generate_question(
                config=self.config,
                current_state=self.session.current_state,
                difficulty=self.session.current_difficulty,
                questions_asked=self.session.questions_asked,
                memory=self.session.memory,
            )
        
        # Update session timestamp
        self.session.updated_at = datetime.utcnow()
        
        return {
            "evaluation": evaluation,
            "feedback": comm_feedback.recommendations if comm_feedback else evaluation.feedback,
            "difficulty_adjustment": difficulty_adjustment,
            "next_state": self.session.current_state,
            "next_question": next_question,
            "is_complete": self.session.is_complete,
        }
    
    def process_answer_sync(
        self,
        question: str,
        answer: str,
    ) -> Dict:
        """Synchronous version of process_answer."""
        logger.info(f"Processing answer for session {self.session.session_id}")
        
        # 1. Analyze the answer
        evaluation = self.analyzer.evaluate_sync(
            question=question,
            answer=answer,
            config=self.config,
            difficulty=self.session.current_difficulty,
            current_state=self.session.current_state,
        )
        
        # 2. Store the Q&A pair
        qa_pair = QuestionAnswer(
            question=question,
            answer=answer,
            state=self.session.current_state,
            difficulty=self.session.current_difficulty,
            evaluation=evaluation,
        )
        self.session.answers.append(qa_pair)
        self.session.evaluations.append(evaluation)
        self.session.questions_asked += 1
        self._questions_per_state[self.session.current_state] += 1
        
        # 3. Update memory
        self.session.memory = self.memory_agent.update_simple(
            current_memory=self.session.memory,
            new_evaluation=evaluation,
            question=question,
            all_evaluations=self.session.evaluations,
        )
        
        # 4. Analyze communication patterns (if enough answers)
        comm_feedback = None
        if len(self.session.answers) >= 2:
            comm_feedback = self.coach.analyze_sync(
                answers=self.session.answers,
                communication_strictness=self.config.communication_strictness,
            )
        
        # 5. Adjust difficulty
        difficulty_adjustment = self.difficulty_engine.adjust_sync(
            evaluations=self.session.evaluations,
            current_difficulty=self.session.current_difficulty,
            current_state=self.session.current_state,
        )
        self.session.current_difficulty = difficulty_adjustment.new_difficulty
        
        # 6. Check state transition
        transition = self.session_manager.check_transition_simple(
            current_state=self.session.current_state,
            questions_in_state=self._questions_per_state[self.session.current_state],
        )
        
        # 7. Apply state transition if needed
        next_question = None
        if transition.should_transition:
            self.session.current_state = transition.next_state
            self._questions_per_state[transition.next_state] = 0
        
        # 8. Check if interview is complete
        if self.session.current_state == InterviewState.FEEDBACK:
            self.session.is_complete = True
            self.session.overall_score = self.calculate_average_score()
        else:
            # 9. Generate next question
            next_question = self.interviewer.generate_question_sync(
                config=self.config,
                current_state=self.session.current_state,
                difficulty=self.session.current_difficulty,
                questions_asked=self.session.questions_asked,
                memory=self.session.memory,
            )
        
        # Update session timestamp
        self.session.updated_at = datetime.utcnow()
        
        return {
            "evaluation": evaluation,
            "feedback": comm_feedback.recommendations if comm_feedback else evaluation.feedback,
            "difficulty_adjustment": difficulty_adjustment,
            "next_state": self.session.current_state,
            "next_question": next_question,
            "is_complete": self.session.is_complete,
        }
    
    async def generate_final_report(self) -> FinalReport:
        """Generate the comprehensive final report."""
        logger.info(f"Generating final report for session {self.session.session_id}")
        
        report = await self.report_generator.generate(
            session_id=self.session.session_id,
            config=self.config,
            answers=self.session.answers,
            memory=self.session.memory,
        )
        
        return report
    
    def generate_final_report_sync(self) -> FinalReport:
        """Synchronous version of generate_final_report."""
        logger.info(f"Generating final report for session {self.session.session_id}")
        
        report = self.report_generator.generate_sync(
            session_id=self.session.session_id,
            config=self.config,
            answers=self.session.answers,
            memory=self.session.memory,
        )
        
        return report
    
    def get_session_status(self) -> Dict:
        """Get current session status."""
        return {
            "session_id": self.session.session_id,
            "current_state": self.session.current_state,
            "questions_asked": self.session.questions_asked,
            "average_score": self.calculate_average_score(),
            "current_difficulty": self.session.current_difficulty,
            "is_complete": self.session.is_complete,
            "performance_trend": self.session.memory.performance_trend,
        }

"""LangGraph workflow for the interview system."""
from __future__ import annotations

import logging
from typing import Annotated, Any, Dict, Literal

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from app.graph.interview_state import (
    InterviewGraphState,
    STATE_QUESTION_LIMITS,
    get_next_state,
)
from app.models.interview_schemas import (
    AnswerEvaluation,
    CommunicationAnalysis,
    DifficultyAdjustment,
    InterviewConfig,
    InterviewMemory,
    InterviewState,
    QuestionAnswer,
    StateTransition,
)
from app.agents.interviewer import InterviewerAgent
from app.agents.answer_analyzer import AnswerAnalyzerAgent
from app.agents.communication_coach import CommunicationCoachAgent
from app.agents.difficulty_engine import DifficultyEngineAgent
from app.agents.memory_agent import MemoryAgent
from app.agents.report_generator import ReportGeneratorAgent
from app.agents.session_manager import SessionManagerAgent

logger = logging.getLogger(__name__)

# Initialize agents (singleton pattern for efficiency)
interviewer_agent = InterviewerAgent()
analyzer_agent = AnswerAnalyzerAgent()
coach_agent = CommunicationCoachAgent()
difficulty_agent = DifficultyEngineAgent()
memory_agent = MemoryAgent()
report_agent = ReportGeneratorAgent()
session_agent = SessionManagerAgent()


def analyze_answer(state: InterviewGraphState) -> InterviewGraphState:
    """Node: Analyze the candidate's answer."""
    logger.info("Analyzing answer...")
    
    config = state["config"]
    
    evaluation = analyzer_agent.evaluate_sync(
        question=state["current_question"],
        answer=state["current_answer"],
        config=config,
        difficulty=state["current_difficulty"],
        current_state=state["current_state"],
    )
    
    # Create Q&A pair
    qa_pair = QuestionAnswer(
        question=state["current_question"],
        answer=state["current_answer"],
        state=state["current_state"],
        difficulty=state["current_difficulty"],
        evaluation=evaluation,
    )
    
    # Update lists
    answers = state.get("answers", [])
    evaluations = state.get("evaluations", [])
    answers.append(qa_pair)
    evaluations.append(evaluation)
    
    return {
        **state,
        "evaluation_result": evaluation,
        "answers": answers,
        "evaluations": evaluations,
        "questions_asked": state.get("questions_asked", 0) + 1,
    }


def update_memory(state: InterviewGraphState) -> InterviewGraphState:
    """Node: Update the interview memory."""
    logger.info("Updating memory...")
    
    current_memory = state.get("memory", InterviewMemory())
    evaluations = state.get("evaluations", [])
    
    updated_memory = memory_agent.update_simple(
        current_memory=current_memory,
        new_evaluation=state["evaluation_result"],
        question=state["current_question"],
        all_evaluations=evaluations,
    )
    
    # Calculate overall score
    overall_score = 0.0
    if evaluations:
        overall_score = sum(e.average_score for e in evaluations) / len(evaluations)
    
    return {
        **state,
        "memory": updated_memory,
        "overall_score": overall_score,
    }


def analyze_communication(state: InterviewGraphState) -> InterviewGraphState:
    """Node: Analyze communication patterns."""
    answers = state.get("answers", [])
    
    # Only analyze if we have enough answers
    if len(answers) < 2:
        return state
    
    logger.info("Analyzing communication patterns...")
    
    config = state["config"]
    
    comm_analysis = coach_agent.analyze_sync(
        answers=answers,
        communication_strictness=config.communication_strictness,
    )
    
    return {
        **state,
        "communication_analysis": comm_analysis,
    }


def adjust_difficulty(state: InterviewGraphState) -> InterviewGraphState:
    """Node: Adjust difficulty based on performance."""
    logger.info("Adjusting difficulty...")
    
    evaluations = state.get("evaluations", [])
    
    adjustment = difficulty_agent.adjust_sync(
        evaluations=evaluations,
        current_difficulty=state["current_difficulty"],
        current_state=state["current_state"],
    )
    
    return {
        **state,
        "difficulty_adjustment": adjustment,
        "current_difficulty": adjustment.new_difficulty,
    }


def check_state_transition(state: InterviewGraphState) -> InterviewGraphState:
    """Node: Check if we should transition to the next state."""
    logger.info("Checking state transition...")
    
    current_state = state["current_state"]
    questions_asked = state.get("questions_asked", 0)
    
    # Count questions in current state
    answers = state.get("answers", [])
    questions_in_state = sum(1 for a in answers if a.state == current_state)
    
    transition = session_agent.check_transition_simple(
        current_state=current_state,
        questions_in_state=questions_in_state,
    )
    
    new_state = current_state
    if transition.should_transition:
        new_state = transition.next_state
    
    # Check if complete
    is_complete = new_state == InterviewState.FEEDBACK
    
    return {
        **state,
        "state_transition": transition,
        "current_state": new_state,
        "is_complete": is_complete,
    }


def generate_next_question(state: InterviewGraphState) -> InterviewGraphState:
    """Node: Generate the next interview question."""
    logger.info("Generating next question...")
    
    config = state["config"]
    memory = state.get("memory", InterviewMemory())
    
    question = interviewer_agent.generate_question_sync(
        config=config,
        current_state=state["current_state"],
        difficulty=state["current_difficulty"],
        questions_asked=state.get("questions_asked", 0),
        memory=memory,
    )
    
    return {
        **state,
        "next_question": question,
    }


def generate_report(state: InterviewGraphState) -> InterviewGraphState:
    """Node: Generate the final interview report."""
    logger.info("Generating final report...")
    
    from uuid import UUID
    
    config = state["config"]
    answers = state.get("answers", [])
    memory = state.get("memory", InterviewMemory())
    
    report = report_agent.generate_sync(
        session_id=UUID(state["session_id"]) if isinstance(state["session_id"], str) else state["session_id"],
        config=config,
        answers=answers,
        memory=memory,
    )
    
    return {
        **state,
        "final_report": report,
        "is_complete": True,
    }


def should_continue(state: InterviewGraphState) -> Literal["generate_question", "generate_report"]:
    """Conditional edge: Determine if we should continue or generate report."""
    if state.get("is_complete", False) or state["current_state"] == InterviewState.FEEDBACK:
        return "generate_report"
    return "generate_question"


def create_interview_graph() -> StateGraph:
    """Create and return the compiled LangGraph interview workflow."""
    
    builder = StateGraph(InterviewGraphState)
    
    # Add nodes
    builder.add_node("analyze_answer", analyze_answer)
    builder.add_node("update_memory", update_memory)
    builder.add_node("analyze_communication", analyze_communication)
    builder.add_node("adjust_difficulty", adjust_difficulty)
    builder.add_node("check_state_transition", check_state_transition)
    builder.add_node("generate_question", generate_next_question)
    builder.add_node("generate_report", generate_report)
    
    # Define edges
    builder.add_edge(START, "analyze_answer")
    builder.add_edge("analyze_answer", "update_memory")
    builder.add_edge("update_memory", "analyze_communication")
    builder.add_edge("analyze_communication", "adjust_difficulty")
    builder.add_edge("adjust_difficulty", "check_state_transition")
    
    # Conditional edge based on state
    builder.add_conditional_edges(
        "check_state_transition",
        should_continue,
        {
            "generate_question": "generate_question",
            "generate_report": "generate_report",
        }
    )
    
    builder.add_edge("generate_question", END)
    builder.add_edge("generate_report", END)
    
    return builder.compile()


# Create the compiled graph
interview_graph = create_interview_graph()


class InterviewWorkflow:
    """Wrapper class for the interview graph workflow."""
    
    def __init__(self):
        self.graph = interview_graph
    
    def process_answer(
        self,
        session_id: str,
        user_id: str,
        config: InterviewConfig,
        current_state: InterviewState,
        current_difficulty: int,
        current_question: str,
        current_answer: str,
        answers: list[QuestionAnswer],
        evaluations: list[AnswerEvaluation],
        memory: InterviewMemory,
        questions_asked: int,
    ) -> Dict[str, Any]:
        """Process an answer through the graph workflow."""
        
        initial_state: InterviewGraphState = {
            "session_id": session_id,
            "user_id": user_id,
            "config": config,
            "current_state": current_state,
            "current_difficulty": current_difficulty,
            "current_question": current_question,
            "current_answer": current_answer,
            "answers": answers,
            "evaluations": evaluations,
            "memory": memory,
            "questions_asked": questions_asked,
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return final_state

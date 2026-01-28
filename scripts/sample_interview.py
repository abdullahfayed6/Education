"""Sample script to demonstrate the Interview System."""
import asyncio
import json
from uuid import UUID

from app.models.interview_schemas import (
    InterviewConfig,
    ExperienceLevel,
    CompanyType,
    InterviewType,
    Scale,
    LeadershipLevel,
)
from app.services.orchestrator import InterviewOrchestrator


def print_separator():
    print("\n" + "=" * 80 + "\n")


async def run_sample_interview():
    """Run a sample interview session."""
    
    # Configure the interview
    config = InterviewConfig(
        target_role="Backend Engineer",
        experience_level=ExperienceLevel.MID,
        company_type=CompanyType.STARTUP,
        interview_type=InterviewType.MIXED,
        difficulty=3,
        tech_stack=["Python", "FastAPI", "PostgreSQL", "Docker"],
        focus_area="System Design",
        allow_coding=False,
        scale=Scale.MEDIUM,
        leadership_level=LeadershipLevel.NONE,
        focus_traits=["Problem Solving", "Communication", "Technical Depth"],
        communication_strictness=3,
        allow_interruptions=False,
        time_pressure=False,
    )
    
    # Create orchestrator
    orchestrator = InterviewOrchestrator(
        config=config,
        user_id="sample_user_001",
    )
    
    print("=" * 80)
    print("INTERVIEW SYSTEM - SAMPLE RUN")
    print("=" * 80)
    print(f"\nSession ID: {orchestrator.session_id}")
    print(f"Role: {config.target_role}")
    print(f"Level: {config.experience_level.value}")
    print(f"Company Type: {config.company_type.value}")
    print(f"Tech Stack: {', '.join(config.tech_stack)}")
    
    # Sample answers for demonstration
    sample_answers = [
        # INTRO
        "I'm a backend engineer with 4 years of experience. I've worked primarily with Python and FastAPI, building RESTful APIs and microservices. I'm passionate about clean code and system design.",
        
        # WARMUP
        "REST stands for Representational State Transfer. It's an architectural style for designing networked applications. The key principles include statelessness, uniform interface, and resource-based URLs. For example, GET /users retrieves users, POST /users creates a new user.",
        
        # CORE_QUESTIONS (3 answers)
        "For a rate limiter, I would use a token bucket algorithm. Each user gets a bucket with a maximum number of tokens. Requests consume tokens, and tokens are refilled at a fixed rate. I'd use Redis for storing the bucket state across distributed servers. This handles burst traffic well while enforcing long-term rate limits.",
        
        "To optimize a slow database query, I would first analyze it with EXPLAIN to understand the execution plan. I'd look for missing indexes, full table scans, or inefficient joins. Then I'd consider adding appropriate indexes, denormalizing if needed, or implementing caching with Redis for frequently accessed data.",
        
        "I would design a notification system with a message queue like RabbitMQ or Kafka. The producer pushes notifications to topics based on type (email, SMS, push). Workers consume from these queues and handle delivery. This decouples the main application from notification delivery and allows for retries and dead letter queues.",
        
        # PRESSURE_ROUND (2 answers)
        "Under this constraint, I'd prioritize a simple in-memory solution. I'd use Python's built-in collections.Counter for word frequency. For the top K, I'd use heapq.nlargest which is O(n log k). The trade-off is no persistence, but it's simple and fast. For production, I might add a simple file-based checkpoint.",
        
        "With no Redis available, I'd implement caching using an in-process LRU cache with Python's functools.lru_cache or a manual implementation. For distributed scenarios without Redis, I'd consider SQLite as a lightweight cache store or even filesystem-based caching. The trade-off is reduced cache hit rates in distributed setups.",
        
        # COMMUNICATION_TEST
        "Think of an API like a waiter at a restaurant. You (the client) don't go into the kitchen to make your food. Instead, you tell the waiter what you want. The waiter takes your order to the kitchen, they prepare it, and the waiter brings it back. The API is that waiter - it takes your request, gets the data or performs the action, and brings back the result.",
        
        # CLOSING
        "I'm curious about the team structure and development practices. How do you handle code reviews? Also, what's the typical project lifecycle like at your company?",
    ]
    
    # Start the interview
    print_separator()
    print("STARTING INTERVIEW...")
    first_question = await orchestrator.start_interview()
    print(f"\n📋 Current State: {orchestrator.current_state.value}")
    print(f"❓ First Question: {first_question}")
    
    # Process each answer
    for i, answer in enumerate(sample_answers):
        if orchestrator.is_complete:
            break
            
        print_separator()
        print(f"📝 Answer #{i + 1}:")
        print(f"   {answer[:100]}..." if len(answer) > 100 else f"   {answer}")
        
        result = await orchestrator.process_answer(
            question=first_question if i == 0 else result["next_question"],
            answer=answer,
        )
        
        eval_result = result["evaluation"]
        print(f"\n📊 Evaluation:")
        print(f"   Technical: {eval_result.technical_score}/5")
        print(f"   Reasoning: {eval_result.reasoning_depth}/5")
        print(f"   Communication: {eval_result.communication_clarity}/5")
        print(f"   Structure: {eval_result.structure_score}/5")
        print(f"   Confidence: {eval_result.confidence_signals}/5")
        print(f"   Average: {eval_result.average_score:.2f}/5")
        
        if eval_result.issues_detected:
            print(f"   Issues: {', '.join(eval_result.issues_detected)}")
        
        print(f"\n💬 Feedback: {eval_result.feedback[:100]}..." if len(eval_result.feedback) > 100 else f"\n💬 Feedback: {eval_result.feedback}")
        
        diff_adj = result["difficulty_adjustment"]
        print(f"\n🎯 Difficulty: {diff_adj.new_difficulty}/5 ({diff_adj.reason[:50]}...)" if len(diff_adj.reason) > 50 else f"\n🎯 Difficulty: {diff_adj.new_difficulty}/5 ({diff_adj.reason})")
        
        print(f"\n📋 State: {result['next_state'].value if hasattr(result['next_state'], 'value') else result['next_state']}")
        
        if result["is_complete"]:
            print("\n✅ INTERVIEW COMPLETE!")
        elif result["next_question"]:
            print(f"\n❓ Next Question: {result['next_question'][:100]}..." if len(result["next_question"]) > 100 else f"\n❓ Next Question: {result['next_question']}")
    
    # Generate final report
    if orchestrator.is_complete:
        print_separator()
        print("GENERATING FINAL REPORT...")
        report = await orchestrator.generate_final_report()
        
        print("\n" + "=" * 80)
        print("FINAL INTERVIEW REPORT")
        print("=" * 80)
        print(f"\n📈 Overall Score: {report.overall_score}/5")
        print(f"🎓 Technical Level: {report.technical_level_estimate}")
        print(f"💬 Communication Profile: {report.communication_profile}")
        print(f"🧠 Behavioral Maturity: {report.behavioral_maturity}")
        
        print(f"\n✅ Strengths:")
        for strength in report.strengths:
            print(f"   • {strength}")
        
        print(f"\n⚠️ Weaknesses:")
        for weakness in report.weaknesses:
            print(f"   • {weakness}")
        
        if report.hiring_risks:
            print(f"\n🚨 Hiring Risks:")
            for risk in report.hiring_risks:
                print(f"   • {risk}")
        
        print(f"\n📝 Improvement Plan: {report.improvement_plan[:200]}..." if len(report.improvement_plan) > 200 else f"\n📝 Improvement Plan: {report.improvement_plan}")
        print(f"\n🎯 Recommendation: {report.recommendations}")
    
    print_separator()
    print("SESSION COMPLETE")
    print(f"Total Questions: {orchestrator.session.questions_asked}")
    print(f"Average Score: {orchestrator.calculate_average_score():.2f}/5")


if __name__ == "__main__":
    asyncio.run(run_sample_interview())

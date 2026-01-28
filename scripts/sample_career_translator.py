"""Sample script to demonstrate the Career Translator Agent."""
import asyncio
import json

from app.agents.career_translator import CareerTranslatorAgent
from app.models.career_schemas import LectureInput


def print_json(data, indent=2):
    """Pretty print JSON data."""
    if hasattr(data, 'model_dump'):
        data = data.model_dump()
    print(json.dumps(data, indent=indent, default=str))


async def run_career_translation():
    """Run sample career translations."""
    
    print("=" * 80)
    print("CAREER TRANSLATOR AGENT - SAMPLE RUN")
    print("=" * 80)
    
    # Initialize the agent
    translator = CareerTranslatorAgent()
    
    # Sample lectures to translate
    sample_lectures = [
        {
            "lecture_topic": "Binary Search Trees",
            "lecture_text": """
            A Binary Search Tree (BST) is a node-based binary tree data structure with the following properties:
            - The left subtree of a node contains only nodes with keys lesser than the node's key
            - The right subtree of a node contains only nodes with keys greater than the node's key
            - The left and right subtree each must also be a binary search tree
            
            Operations include insertion, deletion, and search, all with O(log n) average time complexity.
            """
        },
        {
            "lecture_topic": "REST API Design Principles",
            "lecture_text": None  # Test with no content - should generate based on topic
        },
        {
            "lecture_topic": "Database Indexing and Query Optimization",
            "lecture_text": """
            Database indexing is a technique to speed up data retrieval operations.
            Topics covered:
            - B-tree indexes
            - Hash indexes
            - Composite indexes
            - Query execution plans
            - EXPLAIN ANALYZE
            - Index maintenance and overhead
            """
        }
    ]
    
    for i, lecture in enumerate(sample_lectures, 1):
        print(f"\n{'=' * 80}")
        print(f"LECTURE {i}: {lecture['lecture_topic']}")
        print("=" * 80)
        
        lecture_input = LectureInput(
            lecture_topic=lecture["lecture_topic"],
            lecture_text=lecture["lecture_text"],
        )
        
        print("\n⏳ Translating to career value...\n")
        
        try:
            translation = await translator.translate(lecture_input)
            
            print("📚 LECTURE TOPIC:", translation.lecture_topic)
            
            print("\n🌍 REAL-WORLD RELEVANCE:")
            print("   Where Used:")
            for item in translation.real_world_relevance.where_used:
                print(f"     • {item}")
            print("   Problems Solved:")
            for item in translation.real_world_relevance.problems_it_solves:
                print(f"     • {item}")
            print(f"   Risk if Not Known: {translation.real_world_relevance.risk_if_not_known}")
            
            print("\n🏢 INDUSTRY USE CASES:")
            for uc in translation.industry_use_cases:
                print(f"   [{uc.domain}]")
                print(f"     Scenario: {uc.scenario}")
                print(f"     Application: {uc.how_concept_is_used}")
            
            print("\n💼 COMPANY-STYLE TASKS:")
            for task in translation.company_style_tasks:
                print(f"   📋 {task.task_title}")
                print(f"      Context: {task.company_context}")
                print(f"      Mission: {task.your_mission}")
                print(f"      Constraints: {', '.join(task.constraints)}")
                print(f"      Output: {task.expected_output}")
            
            print("\n🛠️ SKILLS BUILT:")
            print(f"   Technical: {', '.join(translation.skills_built.technical)}")
            print(f"   Engineering Thinking: {', '.join(translation.skills_built.engineering_thinking)}")
            print(f"   Problem Solving: {', '.join(translation.skills_built.problem_solving)}")
            print(f"   Team Relevance: {', '.join(translation.skills_built.team_relevance)}")
            
            print("\n🚀 CAREER IMPACT:")
            print(f"   Relevant Roles: {', '.join(translation.career_impact.relevant_roles)}")
            print(f"   Interview Relevance: {translation.career_impact.interview_relevance}")
            print(f"   Junior vs Senior: {translation.career_impact.junior_vs_senior_difference}")
            
            print("\n🏆 ADVANCED CHALLENGE:")
            print(f"   {translation.advanced_challenge.title}")
            print(f"   {translation.advanced_challenge.description}")
            
        except Exception as e:
            print(f"❌ Error translating lecture: {e}")
    
    print("\n" + "=" * 80)
    print("SAMPLE RUN COMPLETE")
    print("=" * 80)


async def run_api_example():
    """Show how to use the API."""
    
    print("\n" + "=" * 80)
    print("API USAGE EXAMPLE")
    print("=" * 80)
    
    print("""
To use the Career Translator via API:

1. Start the server:
   uvicorn app.main:app --reload

2. Make a POST request:
   
   curl -X POST "http://localhost:8000/api/career/translate" \\
     -H "Content-Type: application/json" \\
     -d '{
       "lecture_topic": "Binary Search Trees",
       "lecture_text": "A BST is a binary tree where..."
     }'

3. Response will be structured JSON:
   {
     "success": true,
     "data": {
       "lecture_topic": "Binary Search Trees",
       "real_world_relevance": {...},
       "industry_use_cases": [...],
       "company_style_tasks": [...],
       "skills_built": {...},
       "career_impact": {...},
       "advanced_challenge": {...}
     }
   }

4. For raw JSON output (agent-to-agent):
   POST /api/career/translate/raw
   
5. For batch translation:
   POST /api/career/batch
   Body: [{lecture_topic: "...", lecture_text: "..."}, ...]
""")


if __name__ == "__main__":
    asyncio.run(run_career_translation())
    asyncio.run(run_api_example())

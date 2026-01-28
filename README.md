# Education Platform - Multi-Agent Interview System & Opportunity Matcher

This project provides two main features:
1. **Multi-Agent Interview System** - An adaptive interview system with real-time evaluation, difficulty adjustment, and comprehensive reporting
2. **Internship Opportunity Matcher** - Matches students with internship opportunities

---

## 🎯 Multi-Agent Interview System

### Features
- **7 Specialized AI Agents** working together for comprehensive interviews
- **Adaptive Difficulty** - Questions adjust based on candidate performance
- **Real-time Evaluation** - 5-dimension scoring with immediate feedback
- **State Machine Flow** - 7-state interview progression (INTRO → WARMUP → CORE_QUESTIONS → PRESSURE_ROUND → COMMUNICATION_TEST → CLOSING → FEEDBACK)
- **Memory System** - Tracks weak/strong areas, prevents question repetition
- **Comprehensive Reports** - Hiring recommendations with detailed analysis

### The 7 Agents

| Agent | Purpose |
|-------|---------|
| **Interviewer** | Generates contextual questions based on role, experience, and performance |
| **Answer Analyzer** | Evaluates responses on 5 dimensions (technical, reasoning, communication, structure, confidence) |
| **Communication Coach** | Detects communication issues (rambling, lack of structure, complexity) |
| **Difficulty Engine** | Adjusts question complexity based on performance patterns |
| **Memory Agent** | Tracks performance history, weak/strong areas, prevents question repetition |
| **Report Generator** | Creates comprehensive final assessment with hiring recommendations |
| **Session Manager** | Orchestrates interview flow and state transitions |

### API Endpoints

#### Start Interview
```http
POST /api/interview/start
Content-Type: application/json

{
  "user_id": "user123",
  "config": {
    "target_role": "Backend Engineer",
    "experience_level": "Mid",
    "company_type": "Startup",
    "interview_type": "Mixed",
    "difficulty": 3,
    "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
    "focus_area": "System Design",
    "communication_strictness": 3
  }
}
```

#### Submit Answer
```http
POST /api/interview/answer
Content-Type: application/json

{
  "session_id": "uuid-here",
  "question": "Design a cache system",
  "answer": "I would use Redis with a write-through strategy..."
}
```

#### Get Session Status
```http
GET /api/interview/{session_id}
```

#### Get Final Report
```http
GET /api/interview/{session_id}/report
```

---

## 📋 Internship Opportunity Matcher

Phase 1 delivers a FastAPI backend, a multi-agent workflow, and basic testing to match students with internship opportunities.

### Features
- `/match` endpoint that normalizes profiles, builds queries, retrieves opportunities (mock or SerpAPI), scores, ranks, and returns top 5 matches.
- `/match/{run_id}` endpoint to fetch stored runs.
- Modular agents with caching and scoring rubric.
- Tests for normalization, scoring schema, ranking diversity, and workflow execution.

---

## 📁 Project Structure
```
/app
  /api
    match.py          # Opportunity matching endpoints
    interview.py      # Interview system endpoints
  /agents
    interviewer.py    # Question generation agent
    answer_analyzer.py # Response evaluation agent
    communication_coach.py # Communication analysis
    difficulty_engine.py   # Adaptive difficulty
    memory_agent.py       # Performance tracking
    report_generator.py   # Final report generation
    session_manager.py    # State management
    prompts.py           # Agent prompt templates
    base_agent.py        # Base agent class
  /graph
    interview_state.py    # Interview state definitions
    interview_workflow.py # LangGraph workflow
    workflow.py          # Matching workflow
  /models
    schemas.py           # Matching models
    interview_schemas.py # Interview models
  /services
    orchestrator.py      # Interview orchestrator
    session_store.py     # Session management
    openai_client.py     # OpenAI integration
  main.py
  config.py
/scripts
  sample_run.py         # Sample matching run
  sample_interview.py   # Sample interview demo
```

## 🚀 Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   # Windows
   .\.venv\Scripts\Activate.ps1
   # Linux/Mac
   source .venv/bin/activate
   
   pip install -r requirements.txt
   ```

2. Copy the environment template and adjust values:
   ```bash
   cp .env.example .env
   ```
   
3. Add your OpenAI API key to `.env`:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## ⚙️ Configuration
```
OPENAI_API_KEY=         # Required for interview system
SEARCH_API_KEY=         # For opportunity matching
SEARCH_PROVIDER=mock    # mock, google, bing
MAX_RESULTS=20
TOP_K=5
```

## ▶️ Run the API
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🧪 Run Sample Interview
```bash
python scripts/sample_interview.py
```

## Sample Run
```bash
python scripts/sample_run.py
```

## Notes
- Set `SEARCH_PROVIDER=serpapi` and `SEARCH_API_KEY` to use SerpAPI. Otherwise, the mock provider returns sample opportunities.
- OpenAI scoring is optional. If `OPENAI_API_KEY` is unset, scoring falls back to the deterministic rubric.

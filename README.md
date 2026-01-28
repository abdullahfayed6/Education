# Education Platform - Multi-Agent AI System

An intelligent education platform featuring AI-powered tools for career development:

1. **🎯 Multi-Agent Interview System** - Adaptive interview simulation with 7 specialized AI agents, real-time evaluation, and comprehensive reporting
2. **🎓 Career Translator Agent** - Converts academic lectures into industry-relevant career value, tasks, and real-world context
3. **🚀 Internship Opportunity Matcher** - Smart job matching using AI scoring and real-time LinkedIn scraping
4. **🎮 Task Simulation Engine** - Generate realistic internship tasks from 13 Egyptian tech companies

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-Workflow-purple.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange.svg)

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

#### Delete Session
```http
DELETE /api/interview/{session_id}
```

---

## 🎓 Career Translator Agent

An Industry Mentor AI that translates academic lectures into career-relevant content.

### Features
- **Real-World Relevance** - Where concepts are used, problems they solve, risks if not known
- **Industry Use Cases** - Domain-specific scenarios showing practical application
- **Company-Style Tasks** - Realistic assignments with constraints and deliverables
- **Skills Mapping** - Technical, engineering thinking, problem-solving, and team skills
- **Career Impact** - Relevant roles, interview relevance, junior vs senior differences
- **Production Challenges** - 7 real engineering challenges with professional solutions
- **Life Story Explanations** - Relatable analogies that make concepts intuitive
- **Prerequisite Knowledge** - 5 essential topics required before the lecture
- **Learning Success Advice** - 10 actionable tips to master the topic

### API Endpoints

#### Translate Lecture
```http
POST /api/career/translate
Content-Type: application/json

{
  "lecture_topic": "Binary Search Trees",
  "lecture_text": "Optional detailed lecture content...",
  "target_track": "Backend Developer"
}
```

#### Raw Translation (for agent-to-agent communication)
```http
POST /api/career/translate/raw
Content-Type: application/json

{
  "lecture_topic": "Database Indexing",
  "target_track": "Data Engineer"
}
```

#### Batch Translation
```http
POST /api/career/batch
Content-Type: application/json

[
  {"lecture_topic": "REST API Design"},
  {"lecture_topic": "SQL Joins"},
  {"lecture_topic": "Docker Containers"}
]
```

### Sample Output Structure
```json
{
  "lecture_topic": "Binary Search Trees",
  "real_world_relevance": {
    "where_used": ["Database indexing", "File systems", "Autocomplete systems"],
    "problems_it_solves": ["Fast lookups in sorted data", "Range queries"],
    "risk_if_not_known": "Inefficient searches in production, O(n) instead of O(log n)"
  },
  "industry_use_cases": [...],
  "company_style_tasks": [...],
  "skills_built": {...},
  "career_impact": {...},
  "advanced_challenge": {...},
  "production_challenges": [...],
  "life_story_explanation": {...},
  "prerequisite_knowledge": {...},
  "learning_success_advice": [...]
}
```

---

## 🚀 Internship Opportunity Matcher

### Features

#### Core Functionality
- **Smart Job Matching**: AI-powered scoring algorithm matching students with internships based on track, skills, academic level, and location preference
- **Real LinkedIn Scraping**: Uses SerpAPI to search LinkedIn jobs with `site:linkedin.com/jobs` operator
- **Multi-Query Search**: Makes 10 different searches with 8 results each for maximum coverage
- **AI-Generated Reasons**: OpenAI generates personalized explanations for why each job matches
- **Intern-Only Filter**: Automatically filters for intern/internship/trainee positions, excludes senior roles

#### API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/match` | POST | Match student profile with internship opportunities |

---

## 📊 Scoring Algorithm

Jobs are scored on a 100-point scale:

| Criteria | Points | Description |
|----------|--------|-------------|
| Track Alignment | 25 | Match with user's track/major |
| Skills Match | 30 | Overlap with user's skills |
| Academic Fit | 10 | Year level appropriateness |
| Location Preference | 15 | Egypt/Remote/Abroad match |
| Readiness Level | 10 | Intern vs Senior position |
| Platform Quality | 5 | Source reliability (LinkedIn = 5) |
| Company Reputation | 5 | Known tech companies bonus |

---

## 🔄 Opportunity Matcher Workflow Pipeline

The LangGraph workflow processes requests through 7 nodes:

```
┌─────────────────┐
│  User Profile   │
└────────┬────────┘
         ▼
┌─────────────────┐
│ 1. Normalize    │  → Categorize skills (hard/tools/soft)     [Rule-based]
└────────┬────────┘
         ▼
┌─────────────────┐
│ 2. Build Query  │  → Generate LinkedIn search queries        [Agent]
└────────┬────────┘
         ▼
┌─────────────────┐
│ 3. Retrieve     │  → 10 searches × 8 results = 80 max jobs   [Rule-based]
└────────┬────────┘
         ▼
┌─────────────────┐
│ 4. Clean        │  → Deduplicate and normalize data          [Rule-based]
└────────┬────────┘
         ▼
┌─────────────────┐
│ 5. Score        │  → Multi-criteria scoring (0-100)          [Rule-based]
│                 │  → AI generates match reasons               [Agent]
└────────┬────────┘
         ▼
┌─────────────────┐
│ 6. Rank         │  → Sort by score, diversify by company     [Rule-based]
└────────┬────────┘
         ▼
┌─────────────────┐
│ 7. Build Result │  → Final JSON response                     [Rule-based]
└─────────────────┘
```

---

## 🎮 Task Simulation Feature

Generate realistic internship task scenarios for interview preparation and skill assessment.

### API Endpoints
```http
GET /companies
```
Returns list of all available Egyptian tech companies.

```http
POST /task-simulation
Content-Type: application/json

{
  "company_name": "Instabug",
  "task_title": "Build a crash reporting SDK"
}
```

### Supported Companies (13 Egyptian Tech Companies)

| Company | Type | Focus Areas |
|---------|------|-------------|
| **Vodafone Egypt** | Telecommunications | Mobile services, IoT, digital payments |
| **Orange Egypt** | Telecommunications | Telecom infrastructure, cloud solutions |
| **Valeo Egypt** | Automotive Tech | Driver assistance systems, sensors |
| **IBM Egypt** | Enterprise Tech | Cloud computing, AI, enterprise software |
| **Microsoft Egypt** | Software & Cloud | Azure, Office 365, enterprise solutions |
| **Swvl** | Transportation Startup | Mass transit, route optimization |
| **Instabug** | Developer Tools SaaS | Mobile monitoring, bug reporting |
| **Fawry** | Fintech | Digital payments, e-commerce |
| **Paymob** | Payment Processing | Online payment gateway, merchant APIs |
| **Noon Academy** | EdTech | Online education, live classes |
| **Vezeeta** | HealthTech | Healthcare booking, telemedicine |
| **Elmenus** | FoodTech | Restaurant discovery, food delivery |
| **Dell Egypt** | Enterprise Hardware | IT infrastructure, support services |

---

## 📁 Project Structure

```
Education/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment configuration
│   │
│   ├── api/                 # API Endpoints
│   │   ├── match.py         # Internship matching endpoints
│   │   ├── interview.py     # Interview system endpoints
│   │   ├── career.py        # Career translator endpoints
│   │   └── task_simulation.py # Task simulation endpoints
│   │
│   ├── graph/               # LangGraph Workflows
│   │   ├── state.py         # Opportunity matcher state
│   │   ├── nodes.py         # 7 processing nodes for matcher
│   │   ├── workflow.py      # Opportunity matcher graph
│   │   ├── interview_state.py    # Interview state definitions
│   │   └── interview_workflow.py # Interview workflow graph
│   │
│   ├── models/              # Data Models
│   │   ├── schemas.py       # Opportunity matcher schemas
│   │   ├── interview_schemas.py # Interview models
│   │   └── career_schemas.py    # Career translator models
│   │
│   ├── services/            # External Services
│   │   ├── linkedin_client.py   # LinkedIn via SerpAPI
│   │   ├── openai_client.py     # AI reason generation
│   │   ├── search_client.py     # Search abstraction
│   │   ├── task_simulation.py   # Task generation service
│   │   ├── orchestrator.py      # Interview orchestrator
│   │   └── session_store.py     # Session management
│   │
│   └── agents/              # AI Agents
│       ├── base_agent.py        # Base agent class
│       ├── interviewer.py       # Question generation
│       ├── answer_analyzer.py   # Response evaluation
│       ├── communication_coach.py # Communication analysis
│       ├── difficulty_engine.py # Difficulty adjustment
│       ├── memory_agent.py      # Performance tracking
│       ├── report_generator.py  # Final report generation
│       ├── session_manager.py   # State transitions
│       ├── career_translator.py # Lecture translation
│       ├── prompts.py           # Interview prompts
│       └── career_prompts.py    # Career translator prompts
│
├── scripts/
│   ├── sample_run.py            # Sample matching workflow
│   ├── sample_interview.py      # Sample interview demo
│   └── sample_career_translator.py # Career translator demo
│
├── requirements.txt         # Python dependencies
└── README.md
```

---

## 🛠️ Tech Stack

### Backend Framework
- **FastAPI** - Modern, fast web framework for building APIs
- **Uvicorn** - Lightning-fast ASGI server
- **Pydantic** - Data validation using Python type annotations

### AI & Workflow
- **LangGraph** - Graph-based workflow orchestration
- **LangChain** - LLM application framework
- **OpenAI GPT-4o-mini** - AI-powered agents for interviews, career translation, and reason generation

### Job Search
- **SerpAPI** - Google Search API for LinkedIn job scraping
- **Requests** - HTTP library for API calls

### Data & Storage
- **Python Dataclasses** - Structured data models
- **In-memory Store** - Fast session and result caching

---

## ⚙️ Setup & Installation

### 1. Create Virtual Environment
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\Activate.ps1
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file with your API keys:

```env
# OpenAI API Key (required for all AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Search API Key (for opportunity matching with SerpAPI)
SEARCH_API_KEY=your_serpapi_key_here

# RapidAPI Key (optional - for LinkedIn API)
RAPIDAPI_KEY=your_rapidapi_key_here

# Search Provider (mock, serpapi)
SEARCH_PROVIDER=mock

# Max results for opportunity search
MAX_RESULTS=20

# Top K results to return
TOP_K=5
```

### 3. Run the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **Health Check**: `http://localhost:8000/health`

---

## 📝 API Usage Examples

### Interview System

**Start Interview:**
```bash
curl -X POST http://localhost:8000/api/interview/start \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "config": {
      "target_role": "Backend Engineer",
      "experience_level": "Mid",
      "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
    }
  }'
```

### Career Translator

**Translate Lecture:**
```bash
curl -X POST http://localhost:8000/api/career/translate \
  -H "Content-Type: application/json" \
  -d '{
    "lecture_topic": "Binary Search Trees",
    "target_track": "Backend Developer"
  }'
```

### Internship Matcher

**Match Profile:**
```bash
curl -X POST http://localhost:8000/match \
  -H "Content-Type: application/json" \
  -d '{
    "academic_year": 3,
    "preference": "egypt",
    "track": "data science",
    "skills": ["python", "sql", "pandas", "machine learning"],
    "notes": "Looking for summer internship"
  }'
```

### Task Simulation

**Generate Task:**
```bash
curl -X POST http://localhost:8000/task-simulation \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Instabug",
    "task_title": "Build crash analytics dashboard"
  }'
```

---

## 🧪 Run Sample Scripts

**Career Translator Demo:**
```bash
python scripts/sample_career_translator.py
```

**Interview Demo:**
```bash
python scripts/sample_interview.py
```

**Matching Demo:**
```bash
python scripts/sample_run.py
```

---

## 🔍 Search Strategy (Opportunity Matcher)

- ✅ Only `/jobs/view/` URLs (individual job pages)
- ✅ Posted in last month (`tbs: qdr:m`)
- ❌ Excludes senior/lead/manager positions
- ❌ Excludes search result pages

---

## 📋 Notes

- Set `SEARCH_PROVIDER=serpapi` and `SEARCH_API_KEY` to use SerpAPI. Otherwise, the mock provider returns sample opportunities.
- **OpenAI API Key** is required for:
  - Interview System (all 7 agents)
  - Career Translator Agent
  - AI-generated match reasons in Opportunity Matcher
- If `OPENAI_API_KEY` is unset, scoring falls back to deterministic rubric (no AI reasons).

---

## 📄 License

This project is for educational purposes.


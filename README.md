# Education Platform - Multi-Agent Interview System & Opportunity Matcher

An intelligent education platform featuring:
1. **Multi-Agent Interview System** - Adaptive interview system with real-time evaluation and comprehensive reporting
2. **AI-Powered Internship Opportunity Matcher** - Smart job matching using AI scoring and real-time LinkedIn scraping

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![LangGraph](https://img.shields.io/badge/LangGraph-Workflow-purple.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-orange.svg)

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
| `/match/{run_id}` | GET | Retrieve a previous match run by ID |
| `/task-simulation` | POST | Generate realistic internship task scenarios |

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

## 🔄 Workflow Pipeline

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
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Environment configuration
│   │
│   ├── api/                 # API Endpoints
│   │   ├── __init__.py
│   │   ├── match.py         # Internship matching endpoints
│   │   ├── interview.py     # Interview system endpoints
│   │   └── task_simulation.py
│   │
│   ├── graph/               # LangGraph Workflow
│   │   ├── __init__.py
│   │   ├── state.py         # Workflow state definition
│   │   ├── nodes.py         # 7 processing nodes
│   │   ├── workflow.py      # Graph compilation
│   │   ├── interview_state.py    # Interview state definitions
│   │   └── interview_workflow.py # Interview workflow
│   │
│   ├── models/              # Data Models
│   │   ├── __init__.py
│   │   ├── schemas.py       # Pydantic schemas
│   │   └── interview_schemas.py # Interview models
│   │
│   ├── services/            # External Services
│   │   ├── __init__.py
│   │   ├── linkedin_client.py   # LinkedIn via SerpAPI
│   │   ├── openai_client.py     # AI reason generation
│   │   ├── search_client.py     # Search abstraction
│   │   ├── task_simulation.py
│   │   ├── orchestrator.py      # Interview orchestrator
│   │   └── session_store.py     # Session management
│   │
│   └── agents/              # AI Agents
│       ├── __init__.py
│       ├── interviewer.py
│       ├── answer_analyzer.py
│       ├── communication_coach.py
│       ├── difficulty_engine.py
│       ├── memory_agent.py
│       ├── report_generator.py
│       ├── session_manager.py
│       ├── prompts.py
│       └── base_agent.py
│
├── scripts/
│   ├── sample_run.py         # Sample matching workflow
│   └── sample_interview.py   # Sample interview demo
│
├── .env                     # Environment variables (not in git)
├── .env.example             # Environment template
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
- **OpenAI GPT-4o-mini** - AI-powered reason generation and interview agents

### Job Search
- **SerpAPI** - Google Search API for LinkedIn job scraping
- **Requests** - HTTP library for API calls

### Data & Storage
- **Python Dataclasses** - Structured data models
- **In-memory Store** - Fast result caching

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
```bash
cp .env.example .env
```

Edit `.env` with your API keys:
```env
# OpenAI API Key (required for interview system and AI matching)
OPENAI_API_KEY=your_openai_api_key_here

# Search API Key (for opportunity matching)
SEARCH_API_KEY=your_search_api_key_here

# Search Provider (mock, google, bing)
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
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 📝 API Usage Examples

### Interview System

**Start Interview:**
```bash
POST /api/interview/start
Content-Type: application/json

{
  "user_id": "user123",
  "config": {
    "target_role": "Backend Engineer",
    "experience_level": "Mid",
    "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
  }
}
```

### Internship Matcher

**Match Endpoint:**
```bash
POST /match
Content-Type: application/json

{
  "academic_year": 3,
  "preference": "egypt",
  "track": "data science",
  "skills": ["python", "sql", "pandas", "machine learning", "data analysis"],
  "notes": "Looking for summer internship"
}
```

**Response:**
```json
{
  "run_id": "uuid",
  "created_at": "2026-01-28T00:00:00",
  "normalized_profile": {
    "year_level": "junior",
    "track": "data science",
    "location_preference": "egypt",
    "skills": {
      "hard": ["data analysis", "machine learning"],
      "tools": ["pandas", "python", "sql"],
      "soft": []
    }
  },
  "ranked_top5": [
    {
      "title": "Data Science Intern",
      "company": "talabat",
      "location": "Egypt",
      "url": "https://linkedin.com/jobs/view/...",
      "score": 85,
      "reasons": [
        "Perfect match for your Data Science track",
        "Your Python and SQL skills align with requirements"
      ]
    }
  ]
}
```

---

## 🧪 Run Sample Scripts

**Interview Demo:**
```bash
python scripts/sample_interview.py
```

**Matching Demo:**
```bash
python scripts/sample_run.py
```

---

## 🔍 Search Strategy

- ✅ Only `/jobs/view/` URLs (individual job pages)
- ✅ Posted in last month (`tbs: qdr:m`)
- ❌ Excludes senior/lead/manager positions
- ❌ Excludes search result pages

---

## 📋 Notes

- Set `SEARCH_PROVIDER=serpapi` and `SEARCH_API_KEY` to use SerpAPI. Otherwise, the mock provider returns sample opportunities.
- OpenAI scoring is optional. If `OPENAI_API_KEY` is unset, scoring falls back to the deterministic rubric.
- Interview system requires `OPENAI_API_KEY` to function.

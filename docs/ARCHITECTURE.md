# CareerForgeAI - Refactored Architecture Guide

## 🏗️ Project Structure

```
Education/
├── app/                          # Legacy application code (to be migrated)
│   ├── agents/                   # AI agents
│   ├── api/                      # API routes
│   ├── graph/                    # LangGraph workflows
│   ├── models/                   # Pydantic schemas
│   ├── providers/                # LLM providers
│   ├── services/                 # Business logic
│   ├── config.py                 # Legacy config
│   └── main.py                   # FastAPI app
│
├── src/                          # ✨ NEW: Refactored code
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py           # Pydantic settings with validation
│   │   └── cosmosdb.py           # Singleton Cosmos DB client
│   │
│   ├── repositories/             # Data access layer
│   │   ├── __init__.py
│   │   ├── base_repository.py   # Abstract base with CRUD
│   │   ├── user_repository.py   # User data operations
│   │   └── session_repository.py # Session/interview data
│   │
│   ├── middleware/               # Request/response middleware
│   │   ├── __init__.py
│   │   ├── error_handler.py     # Global exception handling
│   │   ├── logging.py            # Structured logging
│   │   └── rate_limit.py         # Rate limiting
│   │
│   └── core/                     # Core utilities
│       ├── __init__.py
│       └── utils.py              # Helper functions
│
├── tests/                        # ✨ NEW: Test suite
│   ├── conftest.py               # Pytest fixtures
│   ├── unit/                     # Unit tests
│   │   ├── test_user_repository.py
│   │   └── test_utils.py
│   └── integration/              # Integration tests
│
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # This file
│   ├── API_DOCS.md               # API documentation
│   ├── MIGRATION_GUIDE.md        # Migration steps
│   └── COSMOS_DB_SETUP.md        # Database setup guide
│
├── .github/                      # ✨ NEW: CI/CD
│   └── workflows/
│       └── ci-cd.yml             # GitHub Actions pipeline
│
├── Dockerfile                    # ✨ NEW: Multi-stage Docker build
├── docker-compose.yml            # ✨ NEW: Local development setup
├── .env.example                  # ✨ NEW: Environment template
├── .gitignore                    # ✨ NEW: Git ignore rules
├── setup.cfg                     # ✨ NEW: Tool configurations
├── pyproject.toml                # ✨ NEW: Python project config
├── requirements-new.txt          # ✨ NEW: Updated dependencies
├── requirements.txt              # Legacy requirements
└── README.md                     # Main documentation
```

## 🎯 Architecture Principles

### 1. **Layered Architecture**

```
┌─────────────────────────────────────────┐
│         API Layer (FastAPI)             │
│  (HTTP handlers, validation, routing)   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Service Layer (Business Logic)     │
│    (Agents, workflows, orchestration)   │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│   Repository Layer (Data Access)        │
│   (Cosmos DB operations, caching)       │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      Data Layer (Azure Cosmos DB)       │
│   (NoSQL database with partitioning)    │
└─────────────────────────────────────────┘
```

### 2. **Repository Pattern**

All database operations go through repositories:
- **Singleton CosmosClient** for connection pooling
- **Base repository** with common CRUD operations
- **Specific repositories** for each entity type
- **Retry logic** with exponential backoff for 429 errors
- **Diagnostic logging** for performance monitoring

### 3. **Azure Cosmos DB Best Practices**

#### Partition Key Strategy
- **Users Container**: `/userId` - Single partition key
- **Sessions Container**: Hierarchical `[/userId, /sessionId]` - HPK for scalability
- **Profiles Container**: `/userId` - User-scoped data

#### Data Modeling
- **Embedded Data**: Related data accessed together (e.g., user stats, session messages)
- **Referenced Data**: Large or independently accessed data (separate containers)
- **Size Limit**: Monitor 2MB item limit, warn at 1.5MB

#### Query Optimization
- **Single-partition queries** wherever possible
- **Parameterized queries** to prevent injection
- **Limit cross-partition queries** with warnings

## 🔧 Configuration Management

### Environment-Based Settings

```python
from src.config import settings

# Access settings anywhere
database_name = settings.cosmos_database_name
llm_provider = settings.llm_provider
is_production = settings.is_production
```

### Validation with Pydantic

All settings are validated:
- Type safety
- Required field checking
- Custom validators
- Environment-specific defaults

## 🛡️ Middleware Stack

### 1. **Error Handler**
- Catches all exceptions
- Returns consistent JSON responses
- Handles Cosmos DB specific errors (404, 409, 429)
- Production-safe error messages

### 2. **Logging Middleware**
- Request/response logging
- Correlation IDs for tracing
- Performance monitoring
- Slow request warnings (>1s)

### 3. **Rate Limiting**
- Per-IP rate limiting
- Configurable limits
- Rate limit headers
- Graceful degradation

## 📊 Cosmos DB Schema

### Users Container
```json
{
  "id": "user123",
  "userId": "user123",
  "email": "user@example.com",
  "name": "John Doe",
  "skills": ["Python", "FastAPI"],
  "stats": {
    "totalInterviews": 5,
    "averageScore": 85.5
  },
  "createdAt": "2026-02-03T10:00:00Z",
  "updatedAt": "2026-02-03T10:00:00Z"
}
```

### Sessions Container (HPK)
```json
{
  "id": "session123",
  "sessionId": "session123",
  "userId": "user123",
  "sessionType": "interview",
  "status": "active",
  "messages": [
    {
      "role": "assistant",
      "content": "Hello!",
      "timestamp": "2026-02-03T10:00:00Z"
    }
  ],
  "results": {...},
  "ttl": 2592000
}
```

## 🚀 Development Workflow

### Local Development

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Install dependencies
pip install -r requirements-new.txt

# 3. Start Cosmos DB Emulator with Docker
docker-compose up cosmosdb

# 4. Run application
uvicorn app.main:app --reload

# 5. Run tests
pytest tests/ --cov
```

### With Docker Compose

```bash
# Start all services (app + Cosmos DB emulator)
docker-compose up

# Access:
# - API: http://localhost:8000
# - Cosmos DB Explorer: https://localhost:8081/_explorer/
# - Streamlit: http://localhost:8501
```

## 📈 Testing Strategy

### Unit Tests
- Repository operations
- Utility functions
- Business logic

### Integration Tests
- API endpoints
- Database operations
- External API calls

### Mocking
- Mock Cosmos DB for fast tests
- Mock LLM providers
- Fixture-based test data

## 🔄 Migration Path

### Phase 1: Setup Infrastructure ✅
- ✅ Create new structure
- ✅ Add Cosmos DB configuration
- ✅ Implement repositories
- ✅ Add middleware
- ✅ Setup testing

### Phase 2: Migrate Data Layer (Next)
- Move session storage to Cosmos DB
- Migrate user profiles
- Update interview state management

### Phase 3: Refactor Services
- Update agents to use repositories
- Remove in-memory storage
- Add caching layer

### Phase 4: API Modernization
- Add versioning (`/api/v1`)
- Implement authentication
- Add comprehensive docs

### Phase 5: Production Readiness
- Performance testing
- Security audit
- Load testing
- Monitoring setup

## 🎓 Key Improvements

1. **Scalability**: Azure Cosmos DB with HPK supports unlimited scale
2. **Reliability**: Retry logic, error handling, health checks
3. **Maintainability**: Clean architecture, separation of concerns
4. **Testability**: Comprehensive test suite with >70% coverage
5. **DevOps**: Docker, CI/CD, automated testing
6. **Observability**: Structured logging, metrics, tracing
7. **Security**: Rate limiting, input validation, secret management

## 📚 Next Steps

1. Read [MIGRATION_GUIDE.md](./MIGRATION_GUIDE.md) for step-by-step migration
2. Read [COSMOS_DB_SETUP.md](./COSMOS_DB_SETUP.md) for database setup
3. Review [API_DOCS.md](./API_DOCS.md) for API documentation
4. Run tests: `pytest tests/ -v`
5. Start development: `docker-compose up`

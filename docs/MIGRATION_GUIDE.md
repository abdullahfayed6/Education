# Migration Guide: Legacy → Refactored Architecture

## 📋 Overview

This guide walks you through migrating the CareerForgeAI project from the current in-memory/file-based architecture to the new production-ready structure with Azure Cosmos DB.

---

## 🎯 Migration Phases

### Phase 1: Setup & Preparation ✅ COMPLETE

**Status**: ✅ Done

**What was created**:
- ✅ New `src/` directory structure
- ✅ Azure Cosmos DB integration
- ✅ Repository pattern implementation
- ✅ Middleware layer (logging, error handling, rate limiting)
- ✅ Testing infrastructure
- ✅ DevOps files (Docker, CI/CD)
- ✅ Documentation

**No changes to existing app/** - Your current application still works!

---

### Phase 2: Database Setup (Current Phase)

**Estimated Time**: 30 minutes

#### Step 1: Install Dependencies

```bash
# Backup current requirements
cp requirements.txt requirements-backup.txt

# Install new dependencies
pip install -r requirements-new.txt

# Or install specific new packages
pip install azure-cosmos azure-identity pydantic-settings
```

#### Step 2: Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
# For local development, use emulator:
COSMOS_USE_EMULATOR=true
```

#### Step 3: Start Cosmos DB Emulator

**Option A: Docker (Recommended)**
```bash
docker-compose up cosmosdb
```

**Option B: Windows Emulator**
- Download and install from: https://aka.ms/cosmosdb-emulator
- Run the emulator
- Accept self-signed certificate

#### Step 4: Initialize Database

```bash
# Create initialization script
python -c "
from src.config.cosmosdb import cosmos_db
from src.config.settings import settings

# Create database
db = cosmos_db.create_database_if_not_exists()
print(f'✓ Database {settings.cosmos_database_name} created')

# Create containers
cosmos_db.create_container_if_not_exists('users', '/userId')
cosmos_db.create_container_if_not_exists('sessions', '/userId')
cosmos_db.create_container_if_not_exists('interviews', '/userId')

print('✅ Database setup complete!')
"
```

---

### Phase 3: Migrate Session Storage

**Estimated Time**: 2-3 hours

Currently, sessions are stored in `app/services/session_store.py` (in-memory).
We'll migrate to Cosmos DB.

#### Step 1: Update Session Store

Create `app/services/cosmos_session_store.py`:

```python
from typing import Optional, Dict, Any
from src.repositories import SessionRepository, Session, SessionStatus, SessionType, Message
from src.core.utils import generate_id


class CosmosSessionStore:
    """Session store using Azure Cosmos DB."""
    
    def __init__(self):
        self.repository = SessionRepository()
    
    async def create_session(
        self,
        user_id: str,
        session_type: str,
        config: Dict[str, Any]
    ) -> Session:
        """Create new session."""
        session = Session(
            id=generate_id("session_"),
            sessionId=generate_id("session_"),
            userId=user_id,
            sessionType=SessionType(session_type),
            config=config
        )
        
        return await self.repository.create(session)
    
    async def get_session(self, session_id: str, user_id: str) -> Optional[Session]:
        """Get session by ID."""
        return await self.repository.get_session(session_id, user_id)
    
    async def add_message(
        self,
        session_id: str,
        user_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> Session:
        """Add message to session."""
        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )
        
        return await self.repository.add_message(session_id, user_id, message)
    
    async def complete_session(
        self,
        session_id: str,
        user_id: str,
        results: Dict[str, Any]
    ) -> Session:
        """Mark session as complete."""
        return await self.repository.update_status(
            session_id,
            user_id,
            SessionStatus.COMPLETED,
            results
        )
```

#### Step 2: Update API Endpoints

In `app/api/interview.py`, replace session store:

```python
# OLD
from app.services.session_store import session_store

# NEW
from app.services.cosmos_session_store import CosmosSessionStore

cosmos_store = CosmosSessionStore()

@router.post("/start")
async def start_interview(request: InterviewStartRequest):
    # OLD: session_store.create(...)
    # NEW:
    session = await cosmos_store.create_session(
        user_id=request.user_id,
        session_type="interview",
        config=request.config.dict()
    )
    
    return {"session_id": session.id, "status": "active"}
```

#### Step 3: Test Migration

```bash
# Run tests
pytest tests/unit/test_user_repository.py -v

# Test API endpoint
curl -X POST http://localhost:8000/api/interview/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test123", "config": {...}}'
```

---

### Phase 4: Migrate User Profiles

**Estimated Time**: 1-2 hours

#### Step 1: Create User Service

Create `app/services/user_service.py`:

```python
from typing import Optional
from src.repositories import UserRepository, UserProfile
from src.core.utils import generate_id


class UserService:
    """User management service."""
    
    def __init__(self):
        self.repository = UserRepository()
    
    async def get_or_create_user(
        self,
        user_id: str,
        email: str,
        name: str
    ) -> UserProfile:
        """Get existing user or create new one."""
        user = await self.repository.get_by_user_id(user_id)
        
        if not user:
            user = UserProfile(
                id=user_id,
                userId=user_id,
                email=email,
                name=name
            )
            user = await self.repository.create(user)
        
        return user
    
    async def update_after_interview(
        self,
        user_id: str,
        score: float
    ) -> UserProfile:
        """Update user stats after interview."""
        return await self.repository.update_stats(user_id, score)
```

#### Step 2: Update API Endpoints

```python
from app.services.user_service import UserService

user_service = UserService()

@router.post("/interview/answer")
async def submit_answer(request: AnswerRequest):
    # ... process answer ...
    
    # Update user stats
    await user_service.update_after_interview(
        user_id=request.user_id,
        score=calculated_score
    )
```

---

### Phase 5: Update Main Application

**Estimated Time**: 1 hour

#### Update app/main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# NEW: Import middleware
from src.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    setup_exception_handlers
)
from src.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

# NEW: Add middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# NEW: Setup exception handlers
setup_exception_handlers(app)

# Existing CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers
)

# Existing routes
from app.api import interview, career, recommender
# ... include routers ...

# NEW: Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment.value
    }
```

---

### Phase 6: Testing & Validation

**Estimated Time**: 2-3 hours

#### Step 1: Run Unit Tests

```bash
# Run all tests
pytest tests/ --cov

# Run specific tests
pytest tests/unit/test_user_repository.py -v
pytest tests/unit/test_utils.py -v
```

#### Step 2: Integration Testing

```bash
# Start services
docker-compose up

# Test endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/interview/start -X POST ...
```

#### Step 3: Load Testing (Optional)

```bash
# Install locust
pip install locust

# Create locustfile.py
# Run load test
locust -f tests/load/locustfile.py
```

---

### Phase 7: Deploy to Production

**Estimated Time**: 2-4 hours

#### Step 1: Setup Azure Cosmos DB

Follow [COSMOS_DB_SETUP.md](./COSMOS_DB_SETUP.md) to:
1. Create Cosmos DB account
2. Get credentials
3. Update production .env

#### Step 2: Build & Deploy

```bash
# Build Docker image
docker build -t careerforge-api:latest .

# Tag for registry
docker tag careerforge-api:latest your-registry/careerforge-api:latest

# Push to registry
docker push your-registry/careerforge-api:latest

# Deploy to Azure Web App / Container Instances / AKS
```

#### Step 3: Verify Deployment

```bash
# Check health
curl https://your-app.azurewebsites.net/health

# Check metrics
# Monitor in Azure Portal
```

---

## 🔄 Rollback Plan

If issues occur, rollback is simple:

### Option 1: Keep Both Systems Running

The new code in `src/` doesn't affect `app/`. You can run both:
- Legacy endpoints: `/api/interview/*` (old code)
- New endpoints: `/api/v1/interview/*` (new code)

### Option 2: Git Rollback

```bash
# Revert to previous commit
git revert HEAD

# Or checkout specific commit
git checkout <commit-hash>
```

### Option 3: Docker Rollback

```bash
# Redeploy previous image
docker pull your-registry/careerforge-api:previous-tag
docker run -p 8000:8000 your-registry/careerforge-api:previous-tag
```

---

## ✅ Checklist

### Pre-Migration
- [ ] Backup current code: `git commit -am "Pre-migration backup"`
- [ ] Review architecture docs: `docs/ARCHITECTURE.md`
- [ ] Install dependencies: `pip install -r requirements-new.txt`
- [ ] Setup .env file
- [ ] Start Cosmos DB emulator

### During Migration
- [ ] Initialize database
- [ ] Migrate session storage
- [ ] Migrate user profiles
- [ ] Update main application
- [ ] Run tests
- [ ] Test all endpoints

### Post-Migration
- [ ] Monitor error logs
- [ ] Check Cosmos DB metrics
- [ ] Verify all features working
- [ ] Update documentation
- [ ] Train team on new structure

---

## 🆘 Getting Help

### Common Issues

**Issue: Import errors**
```
ModuleNotFoundError: No module named 'src'
```
**Solution**: Add to PYTHONPATH: `export PYTHONPATH="${PYTHONPATH}:$(pwd)"`

**Issue: Cosmos DB connection failed**
**Solution**: Check .env configuration, verify emulator is running

**Issue: Tests failing**
**Solution**: Ensure test environment: `ENVIRONMENT=testing pytest tests/`

### Support Resources

- **Documentation**: See `docs/` folder
- **Examples**: See `tests/` for usage examples
- **Issues**: Create GitHub issue with `[migration]` tag

---

## 📊 Progress Tracking

Current Status: **Phase 2 - Database Setup**

- [x] Phase 1: Setup & Preparation
- [ ] Phase 2: Database Setup
- [ ] Phase 3: Migrate Session Storage
- [ ] Phase 4: Migrate User Profiles
- [ ] Phase 5: Update Main Application
- [ ] Phase 6: Testing & Validation
- [ ] Phase 7: Deploy to Production

---

## 🎓 Best Practices

1. **Incremental Migration**: Migrate one component at a time
2. **Test Continuously**: Run tests after each change
3. **Monitor Metrics**: Watch Cosmos DB RUs, latency
4. **Document Changes**: Update docs as you go
5. **Keep Communication**: Inform team of progress

---

## 📚 Additional Resources

- [Architecture Guide](./ARCHITECTURE.md)
- [Cosmos DB Setup](./COSMOS_DB_SETUP.md)
- [API Documentation](./API_DOCS.md)
- [Testing Guide](./TESTING.md)

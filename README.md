# Education - Internship Opportunity Matcher

Phase 1 delivers a FastAPI backend, a multi-agent workflow, and basic testing to match students with internship opportunities.

## Features
- `/match` endpoint that normalizes profiles, builds queries, retrieves opportunities (mock or SerpAPI), scores, ranks, and returns top 5 matches.
- `/match/{run_id}` endpoint to fetch stored runs.
- Modular agents with caching and scoring rubric.
- Tests for normalization, scoring schema, ranking diversity, and workflow execution.

## Project Structure
```
/app
  /api
  /agents
  /graph
  /models
  /services
  /tests
  main.py
  config.py
/scripts
  sample_run.py
```

## Setup
1. Create a virtual environment and install dependencies:
   ```bash
   pip install fastapi uvicorn pydantic requests pytest
   ```
2. Copy the environment template and adjust values:
   ```bash
   cp .env.example .env
   ```

## Configuration
```
OPENAI_API_KEY=
SEARCH_API_KEY=
SEARCH_PROVIDER=mock
MAX_RESULTS=20
TOP_K=5
```

## Run the API
```bash
uvicorn app.main:app --reload
```

## Sample Run
```bash
python scripts/sample_run.py
```

## Notes
- Set `SEARCH_PROVIDER=serpapi` and `SEARCH_API_KEY` to use SerpAPI. Otherwise, the mock provider returns sample opportunities.
- OpenAI scoring is optional. If `OPENAI_API_KEY` is unset, scoring falls back to the deterministic rubric.

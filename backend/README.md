# Oracle NL-SQL Management Backend

**Tier 2: FastAPI-based backend for Vector DB, Learning Engine, and PowerBuilder parsing**

## Features

- **Vector DB Integration**: ChromaDB for semantic search (<1 second response time)
- **Learning Engine**: Automatic SQL pattern storage and reuse
- **PowerBuilder Parser**: Extract SQL and business logic from .srw/.srd files
- **Background Tasks**: Async processing with Celery
- **REST API**: Full-featured API for frontend and MCP server

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run the Server

```bash
# Development mode with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the shortcut
python app/main.py
```

### 3. Access API Documentation

- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- Health Check: http://localhost:8000/api/health

## Architecture

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application
│   ├── api/                     # API endpoints
│   │   ├── metadata.py         # Metadata search endpoints
│   │   ├── patterns.py         # SQL pattern management
│   │   ├── upload.py           # File upload endpoints
│   │   └── databases.py        # Database connection management
│   ├── core/                    # Core business logic
│   │   ├── vector_store.py     # ChromaDB integration
│   │   ├── embedding_service.py # Text → Vector embeddings
│   │   ├── learning_engine.py  # SQL pattern learning
│   │   ├── pattern_matcher.py  # Pattern similarity matching
│   │   ├── powerbuilder_parser.py # PB file parser
│   │   └── legacy_analyzer.py  # Legacy code analysis
│   ├── models/                  # Pydantic models
│   │   ├── metadata.py
│   │   ├── pattern.py
│   │   └── database.py
│   ├── services/                # Business logic services
│   └── utils/                   # Utility functions
└── requirements.txt

```

## API Endpoints

### Metadata Search
- `GET /api/v1/metadata/search` - Vector DB semantic search
- `POST /api/v1/metadata/migrate` - Migrate JSON to Vector DB

### SQL Pattern Learning
- `POST /api/v1/patterns/learn` - Save successful SQL pattern
- `GET /api/v1/patterns/list` - List learned patterns
- `GET /api/v1/patterns/similar` - Find similar patterns
- `DELETE /api/v1/patterns/{id}` - Delete pattern

### File Upload
- `POST /api/v1/upload/pb-files` - Upload PowerBuilder files
- `POST /api/v1/upload/csv` - Upload CSV metadata
- `GET /api/v1/jobs/{id}/status` - Check upload job status

### Database Management
- `GET /api/v1/databases` - List databases
- `POST /api/v1/databases/connect` - Test connection
- `GET /api/v1/databases/{sid}/schemas` - List schemas

## Configuration

Create a `.env` file in the `backend/` directory:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Vector DB
CHROMA_DB_PATH=../vector_db
CHROMA_COLLECTION_PREFIX=oracle_nlsql

# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Background Tasks
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Oracle Database (shared with MCP server)
ORACLE_CREDENTIALS_PATH=../credentials
ORACLE_METADATA_PATH=../metadata
```

## Development

### Run Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

## Integration with MCP Server

The MCP server (Tier 1) calls this backend via HTTP:

```python
# In src/mcp_server.py
import httpx

async def get_table_summaries(question: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/metadata/search",
            params={"question": question, "limit": 5}
        )
        return response.json()
```

## Performance Targets (from PRD)

- Stage 1 response time: **<1 second** (vs. 5-10 seconds)
- SQL pattern reuse rate: **>70%**
- LLM API cost reduction: **60%**
- Initial setup time: **2-3 hours** (vs. 2-3 days)

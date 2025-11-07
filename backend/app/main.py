"""
FastAPI Main Application
Tier 2: Management Backend for Oracle NL-SQL MCP Server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Oracle NL-SQL Management Backend",
    description="Vector DB, Learning Engine, and PowerBuilder Parser API",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS configuration (allow React frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Oracle NL-SQL Management Backend...")

    # Initialize Vector DB
    try:
        from app.core.vector_store import VectorStore
        vector_store = VectorStore()
        await vector_store.initialize()
        app.state.vector_store = vector_store
        logger.info("✓ ChromaDB initialized")
    except Exception as e:
        logger.error(f"✗ ChromaDB initialization failed: {e}")

    # Initialize Embedding Service
    try:
        from app.core.embedding_service import EmbeddingService
        embedding_service = EmbeddingService()
        app.state.embedding_service = embedding_service
        logger.info("✓ Embedding service initialized")
    except Exception as e:
        logger.error(f"✗ Embedding service initialization failed: {e}")

    logger.info("Backend startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Oracle NL-SQL Management Backend...")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "Oracle NL-SQL Management Backend",
        "version": "2.0.0",
        "status": "running",
        "docs": "/api/docs"
    }


@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    health_status = {
        "api": "healthy",
        "vector_db": "unknown",
        "embedding_service": "unknown"
    }

    # Check Vector DB
    try:
        if hasattr(app.state, 'vector_store'):
            health_status["vector_db"] = "healthy"
    except:
        health_status["vector_db"] = "unhealthy"

    # Check Embedding Service
    try:
        if hasattr(app.state, 'embedding_service'):
            health_status["embedding_service"] = "healthy"
    except:
        health_status["embedding_service"] = "unhealthy"

    return health_status


# Import and include API routers
from app.api import metadata, patterns, powerbuilder

app.include_router(metadata.router, prefix="/api/v1/metadata", tags=["metadata"])
app.include_router(patterns.router, prefix="/api/v1/patterns", tags=["patterns"])
app.include_router(powerbuilder.router, prefix="/api/v1/powerbuilder", tags=["powerbuilder"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

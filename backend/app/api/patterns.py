"""
SQL Pattern API Endpoints
Handles learning and retrieving SQL patterns
"""

from fastapi import APIRouter, HTTPException, Request
from app.models.pattern import (
    LearnPatternRequest,
    LearnPatternResponse,
    FindSimilarPatternRequest,
    FindSimilarPatternResponse,
    PatternMatch,
    ListPatternsResponse,
    PatternInfo,
    PatternFeedbackRequest,
    PatternStatsResponse
)
from app.core.learning_engine import LearningEngine
import logging
import json

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/learn", response_model=LearnPatternResponse)
async def learn_pattern(request: LearnPatternRequest, req: Request):
    """
    Learn a new SQL pattern for future reuse

    Call this after successfully executing a SQL query to store it for future similar questions.
    """
    try:
        vector_store = req.app.state.vector_store
        embedding_service = req.app.state.embedding_service

        learning_engine = LearningEngine(vector_store, embedding_service)

        pattern_id = learning_engine.learn_sql_pattern(
            question=request.question,
            sql_query=request.sql_query,
            database_sid=request.database_sid,
            schema_name=request.schema_name,
            tables_used=request.tables_used,
            execution_success=request.execution_success,
            execution_time_ms=request.execution_time_ms,
            row_count=request.row_count,
            user_feedback=request.user_feedback
        )

        logger.info(f"Pattern learned: {pattern_id}")

        return LearnPatternResponse(
            success=True,
            pattern_id=pattern_id,
            message="SQL pattern learned successfully"
        )

    except Exception as e:
        logger.error(f"Learn pattern error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/find-similar", response_model=FindSimilarPatternResponse)
async def find_similar_pattern(request: FindSimilarPatternRequest, req: Request):
    """
    Find a similar pattern that can be reused

    Call this BEFORE generating SQL with LLM to check if a similar pattern already exists.
    If found, you can reuse the SQL (saving LLM API call).
    """
    try:
        vector_store = req.app.state.vector_store
        embedding_service = req.app.state.embedding_service

        learning_engine = LearningEngine(vector_store, embedding_service)

        match = learning_engine.find_similar_pattern(
            question=request.question,
            database_sid=request.database_sid,
            schema_name=request.schema_name,
            similarity_threshold=request.similarity_threshold,
            min_success_rate=request.min_success_rate
        )

        if match:
            return FindSimilarPatternResponse(
                found_match=True,
                pattern=PatternMatch(
                    pattern_id=match["pattern_id"],
                    question=match["question"],
                    sql_query=match["sql_query"],
                    similarity=match["similarity"],
                    success_rate=match["success_rate"],
                    overall_score=match["overall_score"],
                    use_count=match["use_count"]
                ),
                message="Similar pattern found and ready for reuse"
            )
        else:
            return FindSimilarPatternResponse(
                found_match=False,
                pattern=None,
                message="No similar pattern found, generate new SQL"
            )

    except Exception as e:
        logger.error(f"Find similar pattern error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=ListPatternsResponse)
async def list_patterns(
    req: Request,
    database_sid: str = None,
    schema_name: str = None,
    limit: int = 100
):
    """
    List all learned patterns (with optional filtering)
    """
    try:
        vector_store = req.app.state.vector_store
        all_patterns = vector_store.list_all_patterns(limit=limit)

        # Filter by database/schema if provided
        filtered_patterns = []
        for pattern in all_patterns:
            metadata = pattern.get("metadata", {})

            # Apply filters
            if database_sid and metadata.get("database_sid") != database_sid:
                continue
            if schema_name and metadata.get("schema_name") != schema_name:
                continue

            # Extract question and SQL
            document = pattern.get("document", "")
            parts = document.split("\n---\n")
            question = parts[0] if len(parts) > 0 else ""
            sql_query = parts[1] if len(parts) > 1 else ""

            # Calculate success rate
            use_count = metadata.get("use_count", 1)
            success_count = metadata.get("success_count", 0)
            success_rate = success_count / use_count if use_count > 0 else 0

            filtered_patterns.append(PatternInfo(
                pattern_id=pattern["id"],
                question=question,
                sql_query=sql_query,
                database_sid=metadata.get("database_sid", ""),
                schema_name=metadata.get("schema_name", ""),
                use_count=use_count,
                success_rate=round(success_rate, 4),
                avg_execution_time_ms=metadata.get("avg_execution_time_ms"),
                avg_user_rating=metadata.get("avg_user_rating"),
                learned_at=metadata.get("learned_at", ""),
                last_used_at=metadata.get("last_used_at")
            ))

        return ListPatternsResponse(
            patterns=filtered_patterns,
            total_count=len(filtered_patterns)
        )

    except Exception as e:
        logger.error(f"List patterns error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/feedback")
async def record_pattern_feedback(request: PatternFeedbackRequest, req: Request):
    """
    Record feedback for a pattern that was reused
    """
    try:
        vector_store = req.app.state.vector_store
        embedding_service = req.app.state.embedding_service

        learning_engine = LearningEngine(vector_store, embedding_service)

        learning_engine.record_pattern_feedback(
            pattern_id=request.pattern_id,
            execution_success=request.execution_success,
            user_rating=request.user_rating
        )

        return {
            "success": True,
            "message": "Feedback recorded successfully"
        }

    except Exception as e:
        logger.error(f"Record feedback error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{pattern_id}")
async def delete_pattern(pattern_id: str, req: Request):
    """
    Delete a SQL pattern
    """
    try:
        vector_store = req.app.state.vector_store
        embedding_service = req.app.state.embedding_service

        learning_engine = LearningEngine(vector_store, embedding_service)
        learning_engine.delete_pattern(pattern_id)

        return {
            "success": True,
            "message": f"Pattern {pattern_id} deleted successfully"
        }

    except Exception as e:
        logger.error(f"Delete pattern error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=PatternStatsResponse)
async def get_pattern_stats(req: Request):
    """
    Get statistics about learned patterns
    """
    try:
        vector_store = req.app.state.vector_store
        embedding_service = req.app.state.embedding_service

        learning_engine = LearningEngine(vector_store, embedding_service)
        stats = learning_engine.get_pattern_stats()

        return PatternStatsResponse(
            total_patterns=stats["total_patterns"],
            avg_success_rate=round(stats["avg_success_rate"], 4),
            total_reuses=stats["total_reuses"],
            estimated_llm_calls_saved=stats["estimated_llm_calls_saved"]
        )

    except Exception as e:
        logger.error(f"Pattern stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""Dashboard API endpoints"""

from fastapi import APIRouter, HTTPException, Request
from typing import List
import logging

from app.models.dashboard import (
    DashboardSummary,
    DatabaseListResponse,
    VectorDBStats,
    DatabaseInfo,
    PatternSummary,
    UploadedFile
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(request: Request):
    """
    Get comprehensive dashboard summary

    Returns:
        - Vector DB statistics
        - Registered databases
        - Recent patterns
        - Upload history
    """
    try:
        vector_store = request.app.state.vector_store

        # Get Vector DB statistics
        stats = vector_store.get_stats()
        vector_db_stats = VectorDBStats(
            metadata_count=stats["metadata_count"],
            patterns_count=stats["patterns_count"],
            business_rules_count=stats["business_rules_count"]
        )

        # Get registered databases from metadata
        databases_raw = vector_store.get_all_databases()
        registered_databases = [
            DatabaseInfo(
                database_sid=db["database_sid"],
                schema_name=db["schema_name"],
                table_count=db["table_count"],
                last_updated=db.get("last_updated"),
                connection_status="unknown"  # TODO: Implement actual connection check
            )
            for db in databases_raw
        ]

        # Get recent patterns
        patterns_raw = vector_store.get_recent_patterns(limit=10)
        recent_patterns = [
            PatternSummary(
                pattern_id=p["pattern_id"],
                question=p["question"],
                database_sid=p["database_sid"],
                schema_name=p["schema_name"],
                use_count=p["use_count"],
                success_rate=p["success_rate"],
                learned_at=p["learned_at"]
            )
            for p in patterns_raw
        ]

        # Get upload history from business rules collection
        upload_history_raw = vector_store.get_business_rules_summary()
        upload_history = [
            UploadedFile(
                file_name=upload["source"],
                file_type=upload["source_type"],
                upload_time=upload.get("last_updated", ""),
                file_size=0,  # Not stored in current implementation
                processing_status="completed",
                rules_extracted=upload["rule_count"]
            )
            for upload in upload_history_raw
        ]

        return DashboardSummary(
            vector_db_stats=vector_db_stats,
            registered_databases=registered_databases,
            recent_patterns=recent_patterns,
            upload_history=upload_history,
            total_databases=len(registered_databases),
            total_patterns=stats["patterns_count"],
            total_uploads=len(upload_history)
        )

    except Exception as e:
        logger.error(f"Failed to get dashboard summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases", response_model=DatabaseListResponse)
async def list_databases(request: Request):
    """
    List all registered databases

    Returns:
        List of databases with metadata statistics
    """
    try:
        vector_store = request.app.state.vector_store

        databases_raw = vector_store.get_all_databases()
        databases = [
            DatabaseInfo(
                database_sid=db["database_sid"],
                schema_name=db["schema_name"],
                table_count=db["table_count"],
                last_updated=db.get("last_updated"),
                connection_status="unknown"
            )
            for db in databases_raw
        ]

        return DatabaseListResponse(
            databases=databases,
            total_count=len(databases)
        )

    except Exception as e:
        logger.error(f"Failed to list databases: {e}")
        raise HTTPException(status_code=500, detail=str(e))

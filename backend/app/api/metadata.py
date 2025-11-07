"""
Metadata API Endpoints
Handles Vector DB search and metadata migration
"""

from fastapi import APIRouter, HTTPException, Request
from app.models.metadata import (
    MetadataSearchRequest,
    MetadataSearchResponse,
    MetadataSearchResult,
    MigrationRequest,
    MigrationResponse
)
from app.utils.metadata_migrator import MetadataMigrator
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/search", response_model=MetadataSearchResponse)
async def search_metadata(request: MetadataSearchRequest, req: Request):
    """
    Search for relevant tables using semantic search (Vector DB)

    This replaces the slow JSON file search in Stage 1 of the 2-stage process.
    """
    try:
        vector_store = req.app.state.vector_store
        embedding_service = req.app.state.embedding_service

        # Create embedding for the question
        query_embedding = embedding_service.embed_text(request.question)

        # Prepare filter
        filter_dict = None
        if request.database_sid and request.schema_name:
            filter_dict = {
                "database_sid": request.database_sid,
                "schema_name": request.schema_name
            }

        # Search Vector DB
        results = vector_store.search_metadata(
            query_embedding=query_embedding,
            n_results=request.limit,
            filter_dict=filter_dict
        )

        # Format results
        search_results = []
        for i, table_id in enumerate(results.get("ids", [])):
            metadata = results["metadatas"][i]
            distance = results["distances"][i]

            # Convert distance to similarity score (0-1, higher = more similar)
            similarity = max(0, 1 - (distance / 2))

            search_results.append(MetadataSearchResult(
                table_id=table_id,
                table_name=metadata.get("table_name", ""),
                schema_name=metadata.get("schema_name", ""),
                database_sid=metadata.get("database_sid", ""),
                korean_name=metadata.get("korean_name"),
                description=metadata.get("description"),
                similarity_score=round(similarity, 4),
                column_count=metadata.get("column_count", 0)
            ))

        logger.info(f"Metadata search: '{request.question}' -> {len(search_results)} results")

        return MetadataSearchResponse(
            results=search_results,
            total_found=len(search_results),
            query=request.question
        )

    except Exception as e:
        logger.error(f"Metadata search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/migrate", response_model=MigrationResponse)
async def migrate_metadata(request: MigrationRequest, req: Request):
    """
    Migrate JSON metadata files to Vector DB

    This is a one-time migration operation for existing projects.
    """
    try:
        vector_store = req.app.state.vector_store
        embedding_service = req.app.state.embedding_service

        migrator = MetadataMigrator(vector_store, embedding_service)

        result = await migrator.migrate_from_json(
            metadata_dir=request.metadata_dir,
            database_sid=request.database_sid,
            schema_name=request.schema_name
        )

        if result["success"]:
            return MigrationResponse(
                success=True,
                tables_migrated=result["tables_migrated"],
                database_sid=request.database_sid,
                schema_name=request.schema_name
            )
        else:
            return MigrationResponse(
                success=False,
                tables_migrated=0,
                database_sid=request.database_sid,
                schema_name=request.schema_name,
                error=result.get("error", "Unknown error")
            )

    except Exception as e:
        logger.error(f"Migration error: {e}")
        return MigrationResponse(
            success=False,
            tables_migrated=0,
            database_sid=request.database_sid,
            schema_name=request.schema_name,
            error=str(e)
        )


@router.get("/stats")
async def get_metadata_stats(req: Request):
    """Get Vector DB statistics"""
    try:
        vector_store = req.app.state.vector_store
        stats = vector_store.get_stats()

        return {
            "success": True,
            "metadata_count": stats["metadata_count"],
            "patterns_count": stats["patterns_count"],
            "business_rules_count": stats["business_rules_count"],
            "total_entries": sum(stats.values())
        }

    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

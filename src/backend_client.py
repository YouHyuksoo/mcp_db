"""
Backend API Client
HTTP client for MCP server to communicate with FastAPI backend
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class BackendClient:
    """Client for FastAPI backend"""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 30.0):
        """
        Initialize backend client

        Args:
            base_url: Base URL of the FastAPI backend
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

    async def check_health(self) -> Dict[str, Any]:
        """
        Check backend health

        Returns:
            Health status dict
        """
        try:
            response = await self.client.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Backend health check failed: {e}")
            return {"api": "unhealthy", "error": str(e)}

    async def search_metadata(
        self,
        question: str,
        database_sid: Optional[str] = None,
        schema_name: Optional[str] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Search for relevant tables using Vector DB (Stage 1)

        Args:
            question: Natural language question
            database_sid: Optional database filter
            schema_name: Optional schema filter
            limit: Number of results

        Returns:
            Dict with search results
        """
        try:
            payload = {
                "question": question,
                "limit": limit
            }

            if database_sid:
                payload["database_sid"] = database_sid
            if schema_name:
                payload["schema_name"] = schema_name

            response = await self.client.post(
                f"{self.base_url}/api/v1/metadata/search",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            raise

    async def find_similar_pattern(
        self,
        question: str,
        database_sid: str,
        schema_name: str,
        similarity_threshold: float = 0.85
    ) -> Dict[str, Any]:
        """
        Find a similar SQL pattern for reuse (Learning Engine)

        Args:
            question: Natural language question
            database_sid: Database SID
            schema_name: Schema name
            similarity_threshold: Similarity threshold (0-1)

        Returns:
            Dict with pattern match (or None)
        """
        try:
            payload = {
                "question": question,
                "database_sid": database_sid,
                "schema_name": schema_name,
                "similarity_threshold": similarity_threshold
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/patterns/find-similar",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Find similar pattern failed: {e}")
            raise

    async def learn_sql_pattern(
        self,
        question: str,
        sql_query: str,
        database_sid: str,
        schema_name: str,
        tables_used: List[str],
        execution_success: bool = True,
        execution_time_ms: Optional[float] = None,
        row_count: Optional[int] = None
    ) -> str:
        """
        Learn a new SQL pattern

        Args:
            question: Natural language question
            sql_query: Generated SQL
            database_sid: Database SID
            schema_name: Schema name
            tables_used: List of tables used
            execution_success: Whether query succeeded
            execution_time_ms: Execution time
            row_count: Number of rows returned

        Returns:
            Pattern ID
        """
        try:
            payload = {
                "question": question,
                "sql_query": sql_query,
                "database_sid": database_sid,
                "schema_name": schema_name,
                "tables_used": tables_used,
                "execution_success": execution_success
            }

            if execution_time_ms is not None:
                payload["execution_time_ms"] = execution_time_ms
            if row_count is not None:
                payload["row_count"] = row_count

            response = await self.client.post(
                f"{self.base_url}/api/v1/patterns/learn",
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result.get("pattern_id", "")

        except Exception as e:
            logger.error(f"Learn pattern failed: {e}")
            raise

    async def get_pattern_stats(self) -> Dict[str, Any]:
        """Get statistics about learned patterns"""
        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/patterns/stats"
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Get pattern stats failed: {e}")
            return {
                "total_patterns": 0,
                "avg_success_rate": 0,
                "total_reuses": 0,
                "estimated_llm_calls_saved": 0
            }

    async def migrate_metadata(
        self,
        metadata_dir: str,
        database_sid: str,
        schema_name: str
    ) -> Dict[str, Any]:
        """
        Migrate JSON metadata to Vector DB

        Args:
            metadata_dir: Path to metadata directory
            database_sid: Database SID
            schema_name: Schema name

        Returns:
            Migration result
        """
        try:
            payload = {
                "metadata_dir": metadata_dir,
                "database_sid": database_sid,
                "schema_name": schema_name
            }

            response = await self.client.post(
                f"{self.base_url}/api/v1/metadata/migrate",
                json=payload
            )
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Metadata migration failed: {e}")
            raise


# Singleton instance
_backend_client_instance: Optional[BackendClient] = None


def get_backend_client(base_url: str = "http://localhost:8000") -> BackendClient:
    """Get or create singleton backend client instance"""
    global _backend_client_instance

    if _backend_client_instance is None:
        _backend_client_instance = BackendClient(base_url)

    return _backend_client_instance

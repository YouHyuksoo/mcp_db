"""
Learning Engine
Automatically stores and learns from successful SQL query patterns
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import json

logger = logging.getLogger(__name__)


class LearningEngine:
    """SQL Pattern Learning Engine"""

    def __init__(self, vector_store, embedding_service):
        """
        Initialize learning engine

        Args:
            vector_store: VectorStore instance
            embedding_service: EmbeddingService instance
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service

    def learn_sql_pattern(
        self,
        question: str,
        sql_query: str,
        database_sid: str,
        schema_name: str,
        tables_used: List[str],
        execution_success: bool = True,
        execution_time_ms: Optional[float] = None,
        row_count: Optional[int] = None,
        user_feedback: Optional[int] = None  # 1-5 rating
    ) -> str:
        """
        Store a SQL pattern for future reuse

        Args:
            question: Natural language question
            sql_query: Generated/executed SQL query
            database_sid: Database SID
            schema_name: Schema name
            tables_used: List of tables used in the query
            execution_success: Whether the query executed successfully
            execution_time_ms: Execution time in milliseconds
            row_count: Number of rows returned
            user_feedback: Optional user rating (1-5)

        Returns:
            pattern_id: Unique ID of the stored pattern
        """
        # Generate unique pattern ID
        pattern_id = self._generate_pattern_id(question, sql_query, database_sid, schema_name)

        # Create embedding
        embedding = self.embedding_service.embed_sql_pattern(question, sql_query)

        # Prepare metadata
        metadata = {
            "database_sid": database_sid,
            "schema_name": schema_name,
            "tables_used": json.dumps(tables_used),
            "execution_success": execution_success,
            "learned_at": datetime.utcnow().isoformat(),
            "use_count": 1,
            "success_count": 1 if execution_success else 0
        }

        if execution_time_ms is not None:
            metadata["avg_execution_time_ms"] = execution_time_ms

        if row_count is not None:
            metadata["typical_row_count"] = row_count

        if user_feedback is not None:
            metadata["avg_user_rating"] = float(user_feedback)
            metadata["rating_count"] = 1

        # Check if pattern already exists
        existing_pattern = self.vector_store.get_pattern_by_id(pattern_id)

        if existing_pattern:
            # Update existing pattern statistics
            logger.info(f"Pattern already exists, updating statistics: {pattern_id}")
            self._update_pattern_statistics(
                pattern_id,
                existing_pattern,
                execution_success,
                execution_time_ms,
                user_feedback
            )
        else:
            # Store new pattern
            self.vector_store.add_sql_pattern(
                pattern_id=pattern_id,
                question=question,
                sql_query=sql_query,
                embedding=embedding,
                metadata=metadata
            )
            logger.info(f"New pattern learned: {pattern_id}")

        return pattern_id

    def find_similar_pattern(
        self,
        question: str,
        database_sid: str,
        schema_name: str,
        similarity_threshold: float = 0.85,
        min_success_rate: float = 0.8
    ) -> Optional[Dict[str, Any]]:
        """
        Find a similar pattern that can be reused

        Args:
            question: User's natural language question
            database_sid: Target database
            schema_name: Target schema
            similarity_threshold: Minimum similarity score (default: 0.85)
            min_success_rate: Minimum success rate (default: 0.8)

        Returns:
            Best matching pattern or None if no good match found
        """
        # Create embedding for the question
        question_embedding = self.embedding_service.embed_text(question)

        # Search for similar patterns
        results = self.vector_store.search_similar_patterns(
            query_embedding=question_embedding,
            similarity_threshold=similarity_threshold,
            n_results=5
        )

        if not results["ids"]:
            logger.info("No similar patterns found")
            return None

        # Filter by database/schema and success rate
        best_match = None
        best_score = 0

        for i, pattern_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i]
            similarity = results["similarities"][i]

            # Check if same database and schema
            if (metadata.get("database_sid") != database_sid or
                metadata.get("schema_name") != schema_name):
                continue

            # Calculate success rate
            use_count = metadata.get("use_count", 1)
            success_count = metadata.get("success_count", 0)
            success_rate = success_count / use_count if use_count > 0 else 0

            # Check minimum success rate
            if success_rate < min_success_rate:
                continue

            # Calculate overall score (weighted: 70% similarity, 30% success rate)
            score = 0.7 * similarity + 0.3 * success_rate

            if score > best_score:
                best_score = score
                # Parse the document to extract question and SQL
                document = results["documents"][i]
                parts = document.split("\n---\n")
                question_part = parts[0] if len(parts) > 0 else ""
                sql_part = parts[1] if len(parts) > 1 else metadata.get("sql", "")

                best_match = {
                    "pattern_id": pattern_id,
                    "question": question_part,
                    "sql_query": sql_part,
                    "similarity": similarity,
                    "success_rate": success_rate,
                    "overall_score": score,
                    "use_count": use_count,
                    "metadata": metadata
                }

        if best_match:
            logger.info(
                f"Found reusable pattern: {best_match['pattern_id']} "
                f"(similarity: {best_match['similarity']:.2f}, "
                f"success_rate: {best_match['success_rate']:.2f})"
            )
            # Increment use count
            self._increment_use_count(best_match["pattern_id"])

        return best_match

    def record_pattern_feedback(
        self,
        pattern_id: str,
        execution_success: bool,
        user_rating: Optional[int] = None
    ):
        """
        Record feedback for a pattern that was reused

        Args:
            pattern_id: Pattern ID
            execution_success: Whether execution succeeded
            user_rating: Optional user rating (1-5)
        """
        pattern = self.vector_store.get_pattern_by_id(pattern_id)

        if not pattern:
            logger.warning(f"Pattern not found: {pattern_id}")
            return

        self._update_pattern_statistics(
            pattern_id,
            pattern,
            execution_success,
            user_rating=user_rating
        )

    def delete_pattern(self, pattern_id: str):
        """Delete a pattern (e.g., if it's consistently failing)"""
        self.vector_store.delete_pattern(pattern_id)
        logger.info(f"Pattern deleted: {pattern_id}")

    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        patterns = self.vector_store.list_all_patterns()

        if not patterns:
            return {
                "total_patterns": 0,
                "avg_success_rate": 0,
                "total_reuses": 0
            }

        total_reuses = 0
        success_rates = []

        for pattern in patterns:
            metadata = pattern.get("metadata", {})
            use_count = metadata.get("use_count", 0)
            success_count = metadata.get("success_count", 0)

            total_reuses += use_count

            if use_count > 0:
                success_rates.append(success_count / use_count)

        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0

        return {
            "total_patterns": len(patterns),
            "avg_success_rate": avg_success_rate,
            "total_reuses": total_reuses,
            "estimated_llm_calls_saved": total_reuses
        }

    def _generate_pattern_id(
        self,
        question: str,
        sql_query: str,
        database_sid: str,
        schema_name: str
    ) -> str:
        """Generate unique pattern ID using hash"""
        content = f"{database_sid}:{schema_name}:{question.lower()}:{sql_query.lower()}"
        hash_obj = hashlib.sha256(content.encode())
        return f"pattern_{hash_obj.hexdigest()[:16]}"

    def _increment_use_count(self, pattern_id: str):
        """Increment use count for a pattern"""
        pattern = self.vector_store.get_pattern_by_id(pattern_id)
        if not pattern:
            return

        metadata = pattern.get("metadata", {})
        metadata["use_count"] = metadata.get("use_count", 0) + 1
        metadata["last_used_at"] = datetime.utcnow().isoformat()

        # Re-add to update metadata (ChromaDB upsert behavior)
        document = pattern.get("document", "")
        parts = document.split("\n---\n")
        question = parts[0] if len(parts) > 0 else ""
        sql_query = parts[1] if len(parts) > 1 else ""

        embedding = self.embedding_service.embed_sql_pattern(question, sql_query)

        self.vector_store.add_sql_pattern(
            pattern_id=pattern_id,
            question=question,
            sql_query=sql_query,
            embedding=embedding,
            metadata=metadata
        )

    def _update_pattern_statistics(
        self,
        pattern_id: str,
        pattern: Dict[str, Any],
        execution_success: bool,
        execution_time_ms: Optional[float] = None,
        user_rating: Optional[int] = None
    ):
        """Update pattern statistics with new execution data"""
        metadata = pattern.get("metadata", {})

        # Update counts
        use_count = metadata.get("use_count", 0) + 1
        success_count = metadata.get("success_count", 0) + (1 if execution_success else 0)

        metadata["use_count"] = use_count
        metadata["success_count"] = success_count

        # Update average execution time
        if execution_time_ms is not None:
            current_avg = metadata.get("avg_execution_time_ms", execution_time_ms)
            metadata["avg_execution_time_ms"] = (
                (current_avg * (use_count - 1) + execution_time_ms) / use_count
            )

        # Update average user rating
        if user_rating is not None:
            rating_count = metadata.get("rating_count", 0) + 1
            current_avg_rating = metadata.get("avg_user_rating", user_rating)
            metadata["avg_user_rating"] = (
                (current_avg_rating * (rating_count - 1) + user_rating) / rating_count
            )
            metadata["rating_count"] = rating_count

        metadata["last_used_at"] = datetime.utcnow().isoformat()

        # Re-add pattern with updated metadata
        document = pattern.get("document", "")
        parts = document.split("\n---\n")
        question = parts[0] if len(parts) > 0 else ""
        sql_query = parts[1] if len(parts) > 1 else ""

        embedding = self.embedding_service.embed_sql_pattern(question, sql_query)

        self.vector_store.add_sql_pattern(
            pattern_id=pattern_id,
            question=question,
            sql_query=sql_query,
            embedding=embedding,
            metadata=metadata
        )

        logger.debug(f"Updated statistics for pattern: {pattern_id}")

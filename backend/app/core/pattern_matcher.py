"""
Pattern Matcher
Advanced pattern matching and recommendation system
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PatternMatcher:
    """Advanced pattern matching for SQL query reuse"""

    def __init__(self, learning_engine, embedding_service):
        """
        Initialize pattern matcher

        Args:
            learning_engine: LearningEngine instance
            embedding_service: EmbeddingService instance
        """
        self.learning_engine = learning_engine
        self.embedding_service = embedding_service

    def suggest_alternative_questions(
        self,
        question: str,
        database_sid: str,
        schema_name: str,
        n_suggestions: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest alternative question formulations based on learned patterns

        Args:
            question: User's question
            database_sid: Database SID
            schema_name: Schema name
            n_suggestions: Number of suggestions

        Returns:
            List of alternative questions with their SQL queries
        """
        # Get similar patterns
        question_embedding = self.embedding_service.embed_text(question)
        results = self.learning_engine.vector_store.search_similar_patterns(
            query_embedding=question_embedding,
            similarity_threshold=0.70,  # Lower threshold for suggestions
            n_results=n_suggestions * 2  # Get more, then filter
        )

        suggestions = []
        seen_questions = set()

        for i, pattern_id in enumerate(results.get("ids", [])):
            metadata = results["metadatas"][i]

            # Filter by database/schema
            if (metadata.get("database_sid") != database_sid or
                metadata.get("schema_name") != schema_name):
                continue

            # Extract question
            document = results["documents"][i]
            parts = document.split("\n---\n")
            suggested_question = parts[0] if len(parts) > 0 else ""
            sql_query = parts[1] if len(parts) > 1 else ""

            # Avoid duplicates
            if suggested_question.lower() in seen_questions:
                continue

            seen_questions.add(suggested_question.lower())

            # Calculate success rate
            use_count = metadata.get("use_count", 1)
            success_count = metadata.get("success_count", 0)
            success_rate = success_count / use_count if use_count > 0 else 0

            suggestions.append({
                "question": suggested_question,
                "sql_preview": sql_query[:200] + "..." if len(sql_query) > 200 else sql_query,
                "similarity": results["similarities"][i],
                "success_rate": success_rate,
                "use_count": use_count
            })

            if len(suggestions) >= n_suggestions:
                break

        return suggestions

    def find_patterns_by_tables(
        self,
        tables: List[str],
        database_sid: str,
        schema_name: str
    ) -> List[Dict[str, Any]]:
        """
        Find patterns that use specific tables

        Args:
            tables: List of table names
            database_sid: Database SID
            schema_name: Schema name

        Returns:
            List of patterns using those tables
        """
        all_patterns = self.learning_engine.vector_store.list_all_patterns()
        matching_patterns = []

        for pattern in all_patterns:
            metadata = pattern.get("metadata", {})

            # Filter by database/schema
            if (metadata.get("database_sid") != database_sid or
                metadata.get("schema_name") != schema_name):
                continue

            # Check if any of the tables are used
            import json
            tables_used = json.loads(metadata.get("tables_used", "[]"))

            if any(table in tables_used for table in tables):
                # Extract question and SQL
                document = pattern.get("document", "")
                parts = document.split("\n---\n")
                question = parts[0] if len(parts) > 0 else ""
                sql_query = parts[1] if len(parts) > 1 else ""

                # Calculate success rate
                use_count = metadata.get("use_count", 1)
                success_count = metadata.get("success_count", 0)
                success_rate = success_count / use_count if use_count > 0 else 0

                matching_patterns.append({
                    "pattern_id": pattern["id"],
                    "question": question,
                    "sql_query": sql_query,
                    "tables_used": tables_used,
                    "success_rate": success_rate,
                    "use_count": use_count
                })

        # Sort by use count (most popular first)
        matching_patterns.sort(key=lambda x: x["use_count"], reverse=True)

        return matching_patterns

    def find_popular_patterns(
        self,
        database_sid: str,
        schema_name: str,
        limit: int = 10,
        min_use_count: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find most popular/frequently used patterns

        Args:
            database_sid: Database SID
            schema_name: Schema name
            limit: Maximum number of patterns to return
            min_use_count: Minimum use count

        Returns:
            List of popular patterns
        """
        all_patterns = self.learning_engine.vector_store.list_all_patterns()
        popular_patterns = []

        for pattern in all_patterns:
            metadata = pattern.get("metadata", {})

            # Filter by database/schema
            if (metadata.get("database_sid") != database_sid or
                metadata.get("schema_name") != schema_name):
                continue

            use_count = metadata.get("use_count", 0)
            if use_count < min_use_count:
                continue

            # Extract question and SQL
            document = pattern.get("document", "")
            parts = document.split("\n---\n")
            question = parts[0] if len(parts) > 0 else ""
            sql_query = parts[1] if len(parts) > 1 else ""

            # Calculate success rate
            success_count = metadata.get("success_count", 0)
            success_rate = success_count / use_count if use_count > 0 else 0

            popular_patterns.append({
                "pattern_id": pattern["id"],
                "question": question,
                "sql_query": sql_query,
                "use_count": use_count,
                "success_rate": success_rate,
                "avg_execution_time_ms": metadata.get("avg_execution_time_ms"),
                "avg_user_rating": metadata.get("avg_user_rating")
            })

        # Sort by use count
        popular_patterns.sort(key=lambda x: x["use_count"], reverse=True)

        return popular_patterns[:limit]

    def find_recently_used_patterns(
        self,
        database_sid: str,
        schema_name: str,
        days: int = 7,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find recently used patterns (last N days)

        Args:
            database_sid: Database SID
            schema_name: Schema name
            days: Number of days to look back
            limit: Maximum number of patterns

        Returns:
            List of recently used patterns
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        all_patterns = self.learning_engine.vector_store.list_all_patterns()
        recent_patterns = []

        for pattern in all_patterns:
            metadata = pattern.get("metadata", {})

            # Filter by database/schema
            if (metadata.get("database_sid") != database_sid or
                metadata.get("schema_name") != schema_name):
                continue

            # Check last used date
            last_used_str = metadata.get("last_used_at")
            if not last_used_str:
                continue

            try:
                last_used = datetime.fromisoformat(last_used_str)
                if last_used < cutoff_date:
                    continue
            except:
                continue

            # Extract question and SQL
            document = pattern.get("document", "")
            parts = document.split("\n---\n")
            question = parts[0] if len(parts) > 0 else ""
            sql_query = parts[1] if len(parts) > 1 else ""

            recent_patterns.append({
                "pattern_id": pattern["id"],
                "question": question,
                "sql_query": sql_query,
                "last_used_at": last_used_str,
                "use_count": metadata.get("use_count", 0)
            })

        # Sort by last used date (most recent first)
        recent_patterns.sort(
            key=lambda x: x["last_used_at"],
            reverse=True
        )

        return recent_patterns[:limit]

    def identify_failing_patterns(
        self,
        database_sid: str,
        schema_name: str,
        max_success_rate: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Identify patterns with low success rates (candidates for deletion)

        Args:
            database_sid: Database SID
            schema_name: Schema name
            max_success_rate: Maximum success rate to include (default: 0.5)

        Returns:
            List of failing patterns
        """
        all_patterns = self.learning_engine.vector_store.list_all_patterns()
        failing_patterns = []

        for pattern in all_patterns:
            metadata = pattern.get("metadata", {})

            # Filter by database/schema
            if (metadata.get("database_sid") != database_sid or
                metadata.get("schema_name") != schema_name):
                continue

            # Calculate success rate
            use_count = metadata.get("use_count", 1)
            success_count = metadata.get("success_count", 0)
            success_rate = success_count / use_count if use_count > 0 else 0

            if success_rate > max_success_rate:
                continue

            # Extract question and SQL
            document = pattern.get("document", "")
            parts = document.split("\n---\n")
            question = parts[0] if len(parts) > 0 else ""
            sql_query = parts[1] if len(parts) > 1 else ""

            failing_patterns.append({
                "pattern_id": pattern["id"],
                "question": question,
                "sql_query": sql_query,
                "success_rate": success_rate,
                "use_count": use_count,
                "recommendation": "Consider deleting or reviewing this pattern"
            })

        # Sort by success rate (worst first)
        failing_patterns.sort(key=lambda x: x["success_rate"])

        return failing_patterns

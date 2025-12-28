"""
ChromaDB Vector Store Integration
Provides semantic search capabilities for metadata, SQL patterns, and business rules.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

# ChromaDB telemetry 오류 필터링
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)

# ChromaDB telemetry 완전 비활성화 (환경 변수)
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


class VectorStore:
    """ChromaDB Vector Store for semantic search"""

    def __init__(self, persist_directory: Optional[str] = None):
        """
        Initialize ChromaDB client

        Args:
            persist_directory: Path to persist ChromaDB data (default: ../vector_db)
        """
        if persist_directory is None:
            # Default to data/vector_db directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            persist_directory = str(project_root / "data" / "vector_db")

        os.makedirs(persist_directory, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Collection names
        self.METADATA_COLLECTION = "oracle_metadata"
        self.PATTERNS_COLLECTION = "sql_patterns"
        self.BUSINESS_RULES_COLLECTION = "business_rules"

        # Collections will be initialized in async initialize method
        self.metadata_collection = None
        self.patterns_collection = None
        self.business_rules_collection = None

        logger.info(f"ChromaDB initialized at: {persist_directory}")

    async def initialize(self):
        """Initialize collections (async for consistency with FastAPI)"""
        # Metadata collection: table summaries for Stage 1
        self.metadata_collection = self.client.get_or_create_collection(
            name=self.METADATA_COLLECTION,
            metadata={"description": "Database table metadata for semantic search"}
        )

        # SQL patterns collection: learned successful queries
        self.patterns_collection = self.client.get_or_create_collection(
            name=self.PATTERNS_COLLECTION,
            metadata={"description": "Learned SQL query patterns"}
        )

        # Business rules collection: from CSV and PowerBuilder
        self.business_rules_collection = self.client.get_or_create_collection(
            name=self.BUSINESS_RULES_COLLECTION,
            metadata={"description": "Business rules and domain knowledge"}
        )

        logger.info(f"Collections initialized:")
        logger.info(f"  - {self.METADATA_COLLECTION}: {self.metadata_collection.count()} items")
        logger.info(f"  - {self.PATTERNS_COLLECTION}: {self.patterns_collection.count()} items")
        logger.info(f"  - {self.BUSINESS_RULES_COLLECTION}: {self.business_rules_collection.count()} items")

    def add_metadata(
        self,
        table_id: str,
        summary_text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ):
        """
        Add table metadata to vector store

        Args:
            table_id: Unique ID (e.g., "SCHEMA.TABLE_NAME")
            summary_text: Human-readable summary for the table
            embedding: Vector embedding of the summary
            metadata: Additional metadata (columns, descriptions, etc.)
        """
        self.metadata_collection.add(
            ids=[table_id],
            embeddings=[embedding],
            documents=[summary_text],
            metadatas=[metadata]
        )
        logger.debug(f"Added metadata for: {table_id}")

    def add_metadata_batch(
        self,
        table_ids: List[str],
        summary_texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]]
    ):
        """Batch add metadata for better performance"""
        self.metadata_collection.add(
            ids=table_ids,
            embeddings=embeddings,
            documents=summary_texts,
            metadatas=metadatas
        )
        logger.info(f"Batch added {len(table_ids)} metadata entries")

    def search_metadata(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_dict: Optional[Dict[str, Any]] = None,
        database_sid: Optional[str] = None,
        schema_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for relevant tables using semantic similarity

        ★ 중요: database_sid와 schema_name은 필수 권장 (다중 DB 관리)

        Args:
            query_embedding: Vector embedding of the user question
            n_results: Number of results to return (default: 5)
            filter_dict: Optional metadata filters (deprecated, use database_sid/schema_name)
            database_sid: Database SID (권장 필수)
            schema_name: Schema name (권장 필수)

        Returns:
            Dict with 'ids', 'documents', 'metadatas', 'distances'
        """
        # Build filter with database_sid and schema_name
        where_filter = filter_dict.copy() if filter_dict else {}

        # Add database_sid and schema_name to filter
        if database_sid:
            where_filter["database_sid"] = database_sid
        if schema_name:
            where_filter["schema_name"] = schema_name

        # Log warning if searching without DB/Schema filter (위험!)
        if not database_sid or not schema_name:
            logger.warning(
                "⚠️  Searching Vector DB without database_sid/schema_name filter! "
                "This may return results from wrong databases in multi-DB environment."
            )

        results = self.metadata_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter if where_filter else None
        )

        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else []
        }

    def add_sql_pattern(
        self,
        pattern_id: str,
        question: str,
        sql_query: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ):
        """
        Add learned SQL pattern

        Args:
            pattern_id: Unique ID for the pattern
            question: Natural language question
            sql_query: Generated SQL query
            embedding: Embedding of the question
            metadata: Additional info (database, schema, success rate, etc.)
        """
        document = f"{question}\n---\n{sql_query}"

        self.patterns_collection.add(
            ids=[pattern_id],
            embeddings=[embedding],
            documents=[document],
            metadatas=[{**metadata, "question": question, "sql": sql_query}]
        )
        logger.debug(f"Added SQL pattern: {pattern_id}")

    def search_similar_patterns(
        self,
        query_embedding: List[float],
        similarity_threshold: float = 0.85,
        n_results: int = 3
    ) -> Dict[str, Any]:
        """
        Search for similar SQL patterns (for reuse)

        Args:
            query_embedding: Embedding of the new question
            similarity_threshold: Minimum similarity (0-1, higher = more similar)
            n_results: Max number of results

        Returns:
            Dict with similar patterns
        """
        results = self.patterns_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        # Filter by similarity threshold
        # Note: ChromaDB returns distances (lower = more similar)
        # We convert distance to similarity score
        filtered_results = {
            "ids": [],
            "documents": [],
            "metadatas": [],
            "similarities": []
        }

        if results["ids"] and results["ids"][0]:
            for i, distance in enumerate(results["distances"][0]):
                # Convert L2 distance to similarity (1 - normalized_distance)
                # This is approximate; adjust based on your embedding model
                similarity = max(0, 1 - (distance / 2))

                if similarity >= similarity_threshold:
                    filtered_results["ids"].append(results["ids"][0][i])
                    filtered_results["documents"].append(results["documents"][0][i])
                    filtered_results["metadatas"].append(results["metadatas"][0][i])
                    filtered_results["similarities"].append(similarity)

        return filtered_results

    def add_business_rule(
        self,
        rule_id: str,
        rule_text: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ):
        """
        Add business rule from CSV or PowerBuilder

        Args:
            rule_id: Unique ID
            rule_text: Rule description or extracted logic
            embedding: Embedding of the rule
            metadata: Source, context, etc.
        """
        self.business_rules_collection.add(
            ids=[rule_id],
            embeddings=[embedding],
            documents=[rule_text],
            metadatas=[metadata]
        )
        logger.debug(f"Added business rule: {rule_id}")

    def search_business_rules(
        self,
        query_embedding: List[float],
        n_results: int = 5
    ) -> Dict[str, Any]:
        """Search for relevant business rules"""
        results = self.business_rules_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )

        return {
            "ids": results["ids"][0] if results["ids"] else [],
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else []
        }

    def delete_pattern(self, pattern_id: str):
        """Delete a SQL pattern"""
        self.patterns_collection.delete(ids=[pattern_id])
        logger.info(f"Deleted pattern: {pattern_id}")

    def get_pattern_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get pattern by ID"""
        result = self.patterns_collection.get(ids=[pattern_id])

        if result["ids"]:
            return {
                "id": result["ids"][0],
                "document": result["documents"][0] if result["documents"] else None,
                "metadata": result["metadatas"][0] if result["metadatas"] else None
            }
        return None

    def list_all_patterns(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all learned patterns"""
        result = self.patterns_collection.get(limit=limit)

        patterns = []
        if result["ids"]:
            for i, pattern_id in enumerate(result["ids"]):
                patterns.append({
                    "id": pattern_id,
                    "document": result["documents"][i] if result["documents"] else None,
                    "metadata": result["metadatas"][i] if result["metadatas"] else None
                })

        return patterns

    def get_stats(self) -> Dict[str, int]:
        """Get collection statistics"""
        return {
            "metadata_count": self.metadata_collection.count(),
            "patterns_count": self.patterns_collection.count(),
            "business_rules_count": self.business_rules_collection.count()
        }

    def get_all_databases(self) -> List[Dict[str, Any]]:
        """Get all registered databases from metadata collection"""
        result = self.metadata_collection.get()

        databases = {}
        if result["metadatas"]:
            for metadata in result["metadatas"]:
                db_sid = metadata.get("database_sid", "unknown")
                schema_name = metadata.get("schema_name", "unknown")
                db_key = f"{db_sid}.{schema_name}"

                if db_key not in databases:
                    databases[db_key] = {
                        "database_sid": db_sid,
                        "schema_name": schema_name,
                        "table_count": 0,
                        "last_updated": metadata.get("updated_at")
                    }

                databases[db_key]["table_count"] += 1

                # Keep most recent update timestamp
                existing_update = databases[db_key].get("last_updated")
                new_update = metadata.get("updated_at")
                if new_update and (not existing_update or new_update > existing_update):
                    databases[db_key]["last_updated"] = new_update

        return list(databases.values())

    def get_recent_patterns(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent SQL patterns sorted by learned_at timestamp"""
        result = self.patterns_collection.get(limit=limit)

        patterns = []
        if result["ids"]:
            for i, pattern_id in enumerate(result["ids"]):
                metadata = result["metadatas"][i] if result["metadatas"] else {}
                patterns.append({
                    "pattern_id": pattern_id,
                    "question": metadata.get("question", ""),
                    "database_sid": metadata.get("database_sid", "unknown"),
                    "schema_name": metadata.get("schema_name", "unknown"),
                    "use_count": metadata.get("use_count", 0),
                    "success_rate": metadata.get("success_rate", 0.0),
                    "learned_at": metadata.get("learned_at", "")
                })

        # Sort by learned_at timestamp (most recent first)
        patterns.sort(key=lambda x: x.get("learned_at", ""), reverse=True)
        return patterns[:limit]

    def get_business_rules_summary(self) -> List[Dict[str, Any]]:
        """Get business rules summary grouped by source"""
        result = self.business_rules_collection.get()

        rules_by_source = {}
        if result["metadatas"]:
            for metadata in result["metadatas"]:
                source = metadata.get("source", "unknown")
                source_type = metadata.get("source_type", "unknown")

                if source not in rules_by_source:
                    rules_by_source[source] = {
                        "source": source,
                        "source_type": source_type,
                        "rule_count": 0,
                        "last_updated": metadata.get("uploaded_at")
                    }

                rules_by_source[source]["rule_count"] += 1

        return list(rules_by_source.values())

    def list_all_metadata(
        self,
        database_sid: Optional[str] = None,
        schema_name: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        List all metadata entries (without search/ranking)

        Args:
            database_sid: Optional filter by database SID
            schema_name: Optional filter by schema name
            limit: Maximum number of results

        Returns:
            List of metadata items
        """
        # Build filter
        where_filter = {}
        if database_sid:
            where_filter["database_sid"] = database_sid
        if schema_name:
            where_filter["schema_name"] = schema_name

        # Get metadata
        result = self.metadata_collection.get(
            where=where_filter if where_filter else None,
            limit=limit
        )

        metadata_list = []
        if result["ids"]:
            for i, metadata_id in enumerate(result["ids"]):
                metadata = result["metadatas"][i] if result["metadatas"] else {}
                metadata_list.append({
                    "table_id": metadata_id,
                    "table_name": metadata.get("table_name", ""),
                    "table_comment": metadata.get("table_comment", ""),
                    "database_sid": metadata.get("database_sid", ""),
                    "schema_name": metadata.get("schema_name", ""),
                    "column_count": metadata.get("column_count", 0),
                    "created_at": metadata.get("created_at", "")
                })

        return metadata_list

    def reset_collection(self, collection_name: str):
        """Reset a collection (delete all data) - USE WITH CAUTION"""
        if collection_name == self.METADATA_COLLECTION:
            self.client.delete_collection(self.METADATA_COLLECTION)
            self.metadata_collection = self.client.create_collection(self.METADATA_COLLECTION)
            logger.warning(f"Reset collection: {collection_name}")
        elif collection_name == self.PATTERNS_COLLECTION:
            self.client.delete_collection(self.PATTERNS_COLLECTION)
            self.patterns_collection = self.client.create_collection(self.PATTERNS_COLLECTION)
            logger.warning(f"Reset collection: {collection_name}")
        elif collection_name == self.BUSINESS_RULES_COLLECTION:
            self.client.delete_collection(self.BUSINESS_RULES_COLLECTION)
            self.business_rules_collection = self.client.create_collection(self.BUSINESS_RULES_COLLECTION)
            logger.warning(f"Reset collection: {collection_name}")
        else:
            raise ValueError(f"Unknown collection: {collection_name}")

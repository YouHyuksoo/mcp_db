"""
Vector DB Direct Client for MCP Server
Backend 없이 ChromaDB에 직접 접근
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


class VectorDBClient:
    """MCP Server가 Vector DB에 직접 접근"""

    def __init__(self, vector_db_path: str = None):
        """
        Initialize ChromaDB client

        Args:
            vector_db_path: Vector DB 디렉토리 경로 (default: ../vector_db)
        """
        if vector_db_path is None:
            project_root = Path(__file__).parent.parent
            vector_db_path = str(project_root / "data" / "vector_db")

        try:
            self.client = chromadb.PersistentClient(
                path=vector_db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False  # Read-only for safety
                )
            )

            # Get collections (컬렉션이 없으면 생성하지 않고 None으로 설정)
            try:
                self.metadata_collection = self.client.get_collection("oracle_metadata")
                table_count = self.metadata_collection.count()
                logger.info(f"✓ Vector DB connected: {table_count} tables in oracle_metadata collection")
            except Exception as collection_error:
                # 컬렉션이 없는 경우
                logger.warning(f"⚠️ oracle_metadata collection not found: {collection_error}")
                logger.warning("   → Backend를 통해 먼저 데이터를 학습시켜야 합니다.")
                self.metadata_collection = None

        except Exception as e:
            logger.error(f"✗ Vector DB connection failed: {e}")
            self.client = None
            self.metadata_collection = None

    def is_available(self) -> bool:
        """Vector DB가 사용 가능한지 확인"""
        return self.metadata_collection is not None

    def search_tables(
        self,
        question: str,
        database_sid: str,
        schema_name: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        의미 기반 테이블 검색

        ★ 필수: database_sid와 schema_name으로 필터링 (다중 DB 관리)

        Args:
            question: 자연어 질문
            database_sid: 데이터베이스 SID (필수)
            schema_name: 스키마 이름 (필수)
            n_results: 결과 수

        Returns:
            관련 테이블 목록 (enhanced metadata 포함)
        """
        if not self.is_available():
            raise RuntimeError("Vector DB not available. Please run backend to initialize data.")

        # Query Vector DB with mandatory DB/Schema filter
        results = self.metadata_collection.query(
            query_texts=[question],
            n_results=n_results,
            where={
                "database_sid": database_sid,  # ★ 필수 필터
                "schema_name": schema_name      # ★ 필수 필터
            }
        )

        # Format results with enhanced metadata
        tables = []
        if results["ids"] and results["ids"][0]:
            for i, table_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]

                # Convert distance to similarity (0-1)
                similarity = max(0, 1 - (distance / 2))

                # Parse JSON fields if present
                import json
                key_columns = None
                related_tables = None
                business_rules = None

                if metadata.get("key_columns"):
                    try:
                        key_columns = json.loads(metadata["key_columns"])
                    except:
                        pass

                if metadata.get("related_tables"):
                    try:
                        related_tables = json.loads(metadata["related_tables"])
                    except:
                        pass

                if metadata.get("business_rules"):
                    try:
                        business_rules = json.loads(metadata["business_rules"])
                    except:
                        pass

                table_info = {
                    "table_id": table_id,
                    "table_name": metadata.get("table_name", ""),
                    "korean_name": metadata.get("korean_name", ""),
                    "description": metadata.get("description", ""),
                    "similarity": similarity,
                    "column_count": metadata.get("column_count", 0),
                    "has_primary_key": metadata.get("has_primary_key", False),
                    "has_foreign_keys": metadata.get("has_foreign_keys", False)
                }

                # Add enhanced fields if available
                if key_columns:
                    table_info["key_columns"] = key_columns
                if related_tables:
                    table_info["related_tables"] = related_tables
                if business_rules:
                    table_info["business_rules"] = business_rules

                tables.append(table_info)

        logger.info(
            f"Vector DB search: '{question}' in {database_sid}.{schema_name} "
            f"→ {len(tables)} tables found"
        )

        return tables

    def get_stats(self) -> Dict[str, int]:
        """Vector DB 통계"""
        if not self.is_available():
            return {"table_count": 0}

        return {
            "table_count": self.metadata_collection.count()
        }


# Singleton instance
_vector_db_client: Optional[VectorDBClient] = None


def get_vector_db() -> VectorDBClient:
    """Vector DB 클라이언트 싱글톤 가져오기"""
    global _vector_db_client

    if _vector_db_client is None:
        _vector_db_client = VectorDBClient()

    return _vector_db_client

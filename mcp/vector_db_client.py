"""
* @file mcp/vector_db_client.py
* @description
* 이 파일은 MCP 서버가 백엔드 서버 없이도 Vector DB(ChromaDB)에 직접 접근하여
* 의미 기반 검색을 수행할 수 있도록 돕는 클라이언트 모듈입니다.
* 백엔드와 동일한 임베딩 모델(all-MiniLM-L6-v2)을 내장하고 있습니다.
*
* 초보자 가이드:
* 1. **`search_tables` 함수**: 사용자의 자연어 질문을 벡터로 변환하여 
*    가장 관련 있는 Oracle 테이블들을 찾아줍니다. 반드시 DB SID와 스키마명으로 필터링합니다.
* 2. **임베딩 일관성**: 이 파일에서 사용하는 모델은 백엔드의 `EmbeddingService`와 동일해야 합니다.
*
* 유지보수 팁:
* - 검색 결과 수 조정: `search_tables`의 `n_results` 파라미터를 변경하세요.
* - 모델 변경 시: `backend/app/core/embedding_service.py`와 함께 수정해야 정확도가 유지됩니다.
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
        Initialize ChromaDB client and Embedding model
        """
        if vector_db_path is None:
            project_root = Path(__file__).parent.parent
            vector_db_path = str(project_root / "data" / "vector_db")

        # Load Embedding Model (Consistent with Backend)
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"✓ Embedding model loaded: {self.model_name}")
        except Exception as e:
            logger.error(f"✗ Failed to load embedding model: {e}")
            self.model = None

        try:
            self.client = chromadb.PersistentClient(
                path=vector_db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=False  # Read-only for safety
                )
            )

            # Get collections
            try:
                self.metadata_collection = self.client.get_collection("oracle_metadata")
                table_count = self.metadata_collection.count()
                logger.info(f"✓ Vector DB connected: {table_count} tables")
            except Exception as collection_error:
                logger.warning(f"⚠️ oracle_metadata collection not found: {collection_error}")
                self.metadata_collection = None

        except Exception as e:
            logger.error(f"✗ Vector DB connection failed: {e}")
            self.client = None
            self.metadata_collection = None

    def is_available(self) -> bool:
        """Vector DB와 임베딩 모델이 모두 사용 가능한지 확인"""
        return self.metadata_collection is not None and self.model is not None

    def search_tables(
        self,
        question: str,
        database_sid: str,
        schema_name: str,
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        의미 기반 테이블 검색 (백엔드와 동일한 임베딩 사용)
        """
        if not self.is_available():
            raise RuntimeError("Vector DB or Embedding model not available.")

        # 1. 태스크에 맞는 임베딩 생성 (백엔드와 동일한 로직)
        query_embedding = self.model.encode(question).tolist()

        # 2. 직접 생성한 임베딩으로 검색
        results = self.metadata_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={
                "database_sid": database_sid,
                "schema_name": schema_name
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

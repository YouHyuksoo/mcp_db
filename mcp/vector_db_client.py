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

            # ★ 컬럼 컬렉션 연결
            try:
                self.columns_collection = self.client.get_collection("oracle_columns")
                column_count = self.columns_collection.count()
                logger.info(f"✓ Columns collection connected: {column_count} columns")
            except Exception as collection_error:
                logger.warning(f"⚠️ oracle_columns collection not found: {collection_error}")
                self.columns_collection = None

        except Exception as e:
            logger.error(f"✗ Vector DB connection failed: {e}")
            self.client = None
            self.metadata_collection = None
            self.columns_collection = None

    def is_available(self) -> bool:
        """Vector DB와 임베딩 모델이 모두 사용 가능한지 확인"""
        return self.metadata_collection is not None and self.model is not None

    def search_tables(
        self,
        question: str,
        database_sid: str,
        schema_name: str,
        n_results: int = 10,
        weights: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        ★ 의미 기반 테이블 검색 (가중치 적용)

        Args:
            weights: 테이블별 가중치 {"TABLE_NAME": 0.92, ...}
                    피드백에서 계산된 가중치로 검색 결과 재정렬
        """
        if not self.is_available():
            raise RuntimeError("Vector DB or Embedding model not available.")

        # 1. 태스크에 맞는 임베딩 생성 (백엔드와 동일한 로직)
        query_embedding = self.model.encode(question).tolist()

        # 2. 직접 생성한 임베딩으로 검색 (더 많이 가져옴)
        results = self.metadata_collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results * 2, 50),  # 최대 50개, 가중치로 정렬 후 상위 반환
            where={
                "$and": [
                    {"database_sid": database_sid},
                    {"schema_name": schema_name}
                ]
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

                table_name = metadata.get("table_name", "")

                # ★ 가중치 적용 (피드백 기반)
                feedback_weight = 1.0  # 기본값
                if weights and table_name in weights:
                    feedback_weight = weights[table_name]

                # 최종 점수 = 의미 기반 유사도 × 피드백 가중치
                final_score = similarity * feedback_weight

                table_info = {
                    "table_id": table_id,
                    "table_name": table_name,
                    "korean_name": metadata.get("korean_name", ""),
                    "description": metadata.get("description", ""),
                    "similarity": similarity,
                    "feedback_weight": round(feedback_weight, 4),  # 가중치 표시
                    "final_score": round(final_score, 4),         # 최종 점수
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

            # ★ 최종 점수로 정렬
            tables.sort(key=lambda x: x["final_score"], reverse=True)

            # 요청한 개수만 반환
            tables = tables[:n_results]

        logger.info(
            f"Vector DB search: '{question}' in {database_sid}.{schema_name} "
            f"→ {len(tables)} tables found"
        )

        return tables

    def search_columns(
        self,
        query: str,
        database_sid: str,
        schema_name: str,
        table_name: Optional[str] = None,
        n_results: int = 10,
        table_weights: Optional[Dict[str, float]] = None,
        column_weights: Optional[Dict[str, Dict[str, float]]] = None
    ) -> List[Dict[str, Any]]:
        """
        ★ 의미 기반 컬럼 검색 (가중치 적용)

        Args:
            query: 자연어 검색어 (예: "라인", "일자", "수량")
            database_sid: DB SID
            schema_name: 스키마 이름
            table_name: 특정 테이블로 제한 (선택)
            n_results: 반환할 컬럼 수
            table_weights: 테이블별 가중치 {"TABLE_NAME": 0.92, ...}
            column_weights: 컬럼별 가중치 {"TABLE_NAME": {"COLUMN_NAME": 0.95, ...}, ...}

        Returns:
            관련 컬럼 정보 리스트
        """
        if self.columns_collection is None or self.model is None:
            raise RuntimeError("Columns collection or Embedding model not available.")

        # 쿼리 임베딩 생성
        query_embedding = self.model.encode(query).tolist()

        # 필터 조건 생성
        where_filter = {
            "$and": [
                {"database_sid": database_sid},
                {"schema_name": schema_name}
            ]
        }

        # 특정 테이블로 제한
        if table_name:
            where_filter["$and"].append({"table_name": table_name})

        # ChromaDB 검색 (더 많이 가져온 후 가중치 적용)
        results = self.columns_collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n_results * 2, 50),  # 최대 50개
            where=where_filter
        )

        # 결과 포맷팅 (가중치 적용)
        columns = []
        if results["ids"] and results["ids"][0]:
            for i, col_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                distance = results["distances"][0][i]
                similarity = max(0, 1 - (distance / 2))

                col_table_name = metadata.get("table_name", "")
                col_column_name = metadata.get("column_name", "")

                # ★ 가중치 적용
                table_weight = 1.0
                column_weight = 1.0

                if table_weights and col_table_name in table_weights:
                    table_weight = table_weights[col_table_name]

                if (column_weights and col_table_name in column_weights and
                    col_column_name in column_weights[col_table_name]):
                    column_weight = column_weights[col_table_name][col_column_name]

                # 최종 점수 = 유사도 × 테이블 가중치 × 컬럼 가중치
                final_score = similarity * table_weight * column_weight

                columns.append({
                    "column_id": col_id,
                    "table_name": col_table_name,
                    "column_name": col_column_name,
                    "korean_name": metadata.get("korean_name", ""),
                    "description": metadata.get("description", ""),
                    "data_type": metadata.get("data_type", ""),
                    "is_pk": metadata.get("is_pk", False),
                    "column_comment": metadata.get("column_comment", ""),
                    "table_comment": metadata.get("table_comment", ""),
                    "similarity": round(similarity * 100, 1),
                    "table_weight": round(table_weight, 4),
                    "column_weight": round(column_weight, 4),
                    "final_score": round(final_score * 100, 1)
                })

        # ★ 최종 점수로 정렬
        columns.sort(key=lambda x: x["final_score"], reverse=True)

        # 요청한 개수만 반환
        columns = columns[:n_results]

        logger.info(
            f"Vector DB column search: '{query}' in {database_sid}.{schema_name} "
            f"→ {len(columns)} columns found"
        )

        return columns

    def get_stats(self) -> Dict[str, int]:
        """Vector DB 통계"""
        if not self.is_available():
            return {"table_count": 0, "column_count": 0}

        stats = {
            "table_count": self.metadata_collection.count() if self.metadata_collection else 0,
            "column_count": self.columns_collection.count() if self.columns_collection else 0
        }

        return stats


# Singleton instance
_vector_db_client: Optional[VectorDBClient] = None


def get_vector_db() -> VectorDBClient:
    """Vector DB 클라이언트 싱글톤 가져오기"""
    global _vector_db_client

    if _vector_db_client is None:
        _vector_db_client = VectorDBClient()

    return _vector_db_client

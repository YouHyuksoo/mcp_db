"""
* @file mcp/feedback_manager.py
* @description
* 이 파일은 사용자 피드백을 ChromaDB에 저장하고 관리합니다.
* SQL 생성, 사용자 응답, 실행 결과를 모두 추적하여
* 나중에 분석 및 가중치 계산에 사용합니다.
*
* ChromaDB 컬렉션:
* - feedback_sql_generation: SQL 생성 이력
* - feedback_user_response: 사용자 피드백
* - feedback_execution_result: 실행 결과
* - weight_table_scores: 테이블 가중치
* - weight_column_scores: 컬럼 가중치
*
* 초보자 가이드:
* 1. **피드백 저장**: save_sql_generation() → save_user_feedback() → save_execution_result()
* 2. **가중치 계산**: calculate_weights() (피드백 받은 후 호출)
* 3. **분석**: query_feedback_summary() (나중에 검색/분석)
*
* @example
* manager = FeedbackManager(vector_db_client)
* manager.save_sql_generation(feedback_data)
* manager.save_user_feedback(feedback_id, action, suggestions)
* manager.save_execution_result(feedback_id, sql, status, row_count)
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


class FeedbackManager:
    """
    ★ 사용자 피드백 관리 시스템 (ChromaDB 기반)

    피드백 저장 흐름:
    1. SQL 생성 → save_sql_generation()
    2. 사용자 응답 → save_user_feedback()
    3. SQL 실행 → save_execution_result()
    4. 가중치 계산 → calculate_weights()
    """

    def __init__(self, vector_db_client):
        """
        Args:
            vector_db_client: ChromaDB Vector DB 클라이언트
        """
        self.vector_db = vector_db_client
        self.client = vector_db_client.client
        self._init_feedback_collections()

    def _init_feedback_collections(self):
        """피드백 관련 ChromaDB 컬렉션 생성 (존재하지 않으면)"""
        try:
            collection_names = [
                "feedback_sql_generation",
                "feedback_user_response",
                "feedback_execution_result",
                "weight_table_scores",
                "weight_column_scores"
            ]

            for name in collection_names:
                try:
                    self.client.get_collection(name)
                    logger.debug(f"✓ 컬렉션 이미 존재: {name}")
                except Exception:
                    # 컬렉션이 없으면 생성
                    self.client.create_collection(
                        name=name,
                        metadata={"hnsw:space": "cosine"}
                    )
                    logger.info(f"✓ 컬렉션 생성: {name}")

        except Exception as e:
            logger.warning(f"피드백 컬렉션 초기화 실패: {e}")

    def save_sql_generation(self, feedback_data: Dict[str, Any]) -> str:
        """
        ★ Step 1: SQL 생성 이력 저장

        Args:
            feedback_data: {
                "user_query": "Run Card의 당일 생산 계획수량...",
                "selected_table": "IPX_PLAN_RUN_CARD",
                "selected_columns": ["PLAN_QTY", "MODEL_CODE"],
                "generated_sql": "SELECT ...",
                "database_sid": "SMVNPDBext",
                "schema_name": "INFINITY21_JSMES",
                "created_by": "user123"
            }

        Returns:
            feedback_id (생성된 피드백 ID)
        """
        feedback_id = f"fb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

        try:
            collection = self.client.get_collection("feedback_sql_generation")

            # 선택된 컬럼들을 메타데이터에 저장
            selected_columns = feedback_data.get("selected_columns", [])
            if isinstance(selected_columns, list):
                columns_str = ",".join(selected_columns)
            else:
                columns_str = str(selected_columns)

            # ChromaDB에 저장
            collection.add(
                ids=[feedback_id],
                documents=[feedback_data.get("user_query", "")],
                metadatas=[{
                    "user_query": feedback_data.get("user_query", ""),
                    "selected_table": feedback_data.get("selected_table", ""),
                    "selected_columns": columns_str,
                    "generated_sql": feedback_data.get("generated_sql", ""),
                    "database_sid": feedback_data.get("database_sid", ""),
                    "schema_name": feedback_data.get("schema_name", ""),
                    "created_by": feedback_data.get("created_by", "system"),
                    "generation_time": datetime.now().isoformat(),
                    "type": "sql_generation"
                }]
            )

            logger.info(f"✓ SQL 생성 저장: {feedback_id}")
            return feedback_id

        except Exception as e:
            logger.error(f"SQL 생성 저장 실패: {e}")
            raise

    def save_user_feedback(
        self,
        feedback_id: str,
        action: str,
        suggestions: Optional[str] = None,
        user_confidence: float = 0.5
    ) -> bool:
        """
        ★ Step 2: 사용자 피드백 저장

        Args:
            feedback_id: 피드백 ID
            action: "approve", "modify", "reject"
            suggestions: 사용자 제안 (선택)
            user_confidence: 사용자 신뢰도 (0.0~1.0)

        Returns:
            성공 여부
        """
        now = datetime.now()

        try:
            collection = self.client.get_collection("feedback_user_response")

            # 피드백 데이터 저장
            collection.add(
                ids=[feedback_id],
                documents=[suggestions or ""],
                metadatas=[{
                    "action": action,
                    "suggestions": suggestions or "",
                    "user_confidence": user_confidence,
                    "feedback_date": now.date().isoformat(),
                    "feedback_hour": now.hour,
                    "feedback_week": now.isocalendar()[1],
                    "response_time": now.isoformat(),
                    "type": "user_response"
                }]
            )

            logger.info(f"✓ 사용자 피드백 저장: {feedback_id} ({action})")
            return True

        except Exception as e:
            logger.error(f"피드백 저장 실패: {e}")
            raise

    def save_execution_result(
        self,
        feedback_id: str,
        final_sql: str,
        execution_status: str,
        row_count: int = 0,
        execution_time_ms: float = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """
        ★ Step 3: SQL 실행 결과 저장

        Args:
            feedback_id: 피드백 ID
            final_sql: 최종 실행된 SQL
            execution_status: "success" 또는 "error"
            row_count: 조회된 행 수
            execution_time_ms: 실행 시간 (밀리초)
            error_message: 에러 메시지 (에러 시)

        Returns:
            성공 여부
        """
        try:
            collection = self.client.get_collection("feedback_execution_result")

            # 실행 결과 저장
            collection.add(
                ids=[feedback_id],
                documents=[final_sql],
                metadatas=[{
                    "final_sql": final_sql,
                    "execution_status": execution_status,
                    "row_count": row_count,
                    "execution_time_ms": execution_time_ms,
                    "error_message": error_message or "",
                    "executed_at": datetime.now().isoformat(),
                    "type": "execution_result"
                }]
            )

            logger.info(f"✓ 실행 결과 저장: {feedback_id} ({execution_status})")
            return True

        except Exception as e:
            logger.error(f"실행 결과 저장 실패: {e}")
            raise

    def calculate_weights(self) -> bool:
        """
        ★ 가중치 계산 (피드백 저장 후 호출)

        가중치 공식:
        calculated_weight = base_weight +
                           (approval_count × 0.15) -
                           (rejection_count × 0.10) +
                           (average_confidence × 0.05)

        Returns:
            성공 여부
        """
        try:
            # 1. 테이블 가중치 계산
            self._calculate_table_weights()

            # 2. 컬럼 가중치 계산
            self._calculate_column_weights()

            logger.info("✓ 가중치 계산 완료")
            return True

        except Exception as e:
            logger.error(f"가중치 계산 실패: {e}")
            raise

    def _calculate_table_weights(self):
        """테이블별 가중치 계산"""
        try:
            sql_gen_coll = self.client.get_collection("feedback_sql_generation")
            user_resp_coll = self.client.get_collection("feedback_user_response")
            weight_coll = self.client.get_collection("weight_table_scores")

            # 전체 SQL 생성 이력 조회
            all_sql_gen = sql_gen_coll.get()

            if not all_sql_gen["ids"]:
                logger.info("계산할 피드백이 없습니다")
                return

            # 테이블별 피드백 통계 계산
            table_stats = defaultdict(lambda: {
                "count": 0,
                "approve": 0,
                "reject": 0,
                "modify": 0,
                "confidence_sum": 0,
                "database_sid": "",
                "schema_name": ""
            })

            for i, feedback_id in enumerate(all_sql_gen["ids"]):
                metadata = all_sql_gen["metadatas"][i]
                table_name = metadata.get("selected_table", "")
                database_sid = metadata.get("database_sid", "")
                schema_name = metadata.get("schema_name", "")

                if not table_name:
                    continue

                key = f"{table_name}#{database_sid}#{schema_name}"
                table_stats[key]["database_sid"] = database_sid
                table_stats[key]["schema_name"] = schema_name
                table_stats[key]["count"] += 1

                # 해당 피드백의 사용자 응답 조회
                try:
                    user_feedback = user_resp_coll.get(
                        ids=[feedback_id],
                        where={"type": "user_response"}
                    )
                    if user_feedback["ids"]:
                        resp_meta = user_feedback["metadatas"][0]
                        action = resp_meta.get("action", "")
                        confidence = float(resp_meta.get("user_confidence", 0.5))

                        if action == "approve":
                            table_stats[key]["approve"] += 1
                        elif action == "reject":
                            table_stats[key]["reject"] += 1
                        elif action == "modify":
                            table_stats[key]["modify"] += 1

                        table_stats[key]["confidence_sum"] += confidence
                except Exception:
                    pass

            # 가중치 저장
            for key, stats in table_stats.items():
                table_name, database_sid, schema_name = key.split("#")

                # 가중치 계산
                avg_confidence = (stats["confidence_sum"] / stats["count"]) if stats["count"] > 0 else 0
                calculated_weight = (
                    0.5 +
                    (stats["approve"] * 0.15) -
                    (stats["reject"] * 0.10) +
                    (avg_confidence * 0.05)
                )

                # 최소/최대 범위 제한 (0.2 ~ 1.5)
                calculated_weight = max(0.2, min(1.5, calculated_weight))

                weight_id = f"wt_{table_name}_{database_sid}_{schema_name}"

                weight_coll.upsert(
                    ids=[weight_id],
                    documents=[table_name],
                    metadatas=[{
                        "table_name": table_name,
                        "database_sid": database_sid,
                        "schema_name": schema_name,
                        "approval_count": stats["approve"],
                        "rejection_count": stats["reject"],
                        "modify_count": stats["modify"],
                        "total_feedback": stats["count"],
                        "average_confidence": round(avg_confidence, 4),
                        "calculated_weight": round(calculated_weight, 4),
                        "last_updated": datetime.now().isoformat(),
                        "type": "table_weight"
                    }]
                )

            logger.info("테이블 가중치 계산 완료")

        except Exception as e:
            logger.error(f"테이블 가중치 계산 실패: {e}")
            raise

    def _calculate_column_weights(self):
        """컬럼별 가중치 계산"""
        try:
            sql_gen_coll = self.client.get_collection("feedback_sql_generation")
            user_resp_coll = self.client.get_collection("feedback_user_response")
            weight_coll = self.client.get_collection("weight_column_scores")

            # 전체 SQL 생성 이력 조회
            all_sql_gen = sql_gen_coll.get()

            if not all_sql_gen["ids"]:
                logger.info("계산할 피드백이 없습니다")
                return

            # 컬럼별 피드백 통계 계산
            column_stats = defaultdict(lambda: {
                "frequency": 0,
                "approve": 0,
                "reject": 0,
                "modify": 0,
                "confidence_sum": 0,
                "database_sid": "",
                "schema_name": "",
                "table_name": ""
            })

            for i, feedback_id in enumerate(all_sql_gen["ids"]):
                metadata = all_sql_gen["metadatas"][i]
                table_name = metadata.get("selected_table", "")
                database_sid = metadata.get("database_sid", "")
                schema_name = metadata.get("schema_name", "")
                columns_str = metadata.get("selected_columns", "")

                if not columns_str:
                    continue

                # 컬럼 파싱
                columns = [c.strip() for c in columns_str.split(",") if c.strip()]

                for column_name in columns:
                    key = f"{table_name}#{column_name}#{database_sid}#{schema_name}"
                    column_stats[key]["table_name"] = table_name
                    column_stats[key]["database_sid"] = database_sid
                    column_stats[key]["schema_name"] = schema_name
                    column_stats[key]["frequency"] += 1

                    # 해당 피드백의 사용자 응답 조회
                    try:
                        user_feedback = user_resp_coll.get(
                            ids=[feedback_id],
                            where={"type": "user_response"}
                        )
                        if user_feedback["ids"]:
                            resp_meta = user_feedback["metadatas"][0]
                            action = resp_meta.get("action", "")
                            confidence = float(resp_meta.get("user_confidence", 0.5))

                            if action == "approve":
                                column_stats[key]["approve"] += 1
                            elif action == "reject":
                                column_stats[key]["reject"] += 1
                            elif action == "modify":
                                column_stats[key]["modify"] += 1

                            column_stats[key]["confidence_sum"] += confidence
                    except Exception:
                        pass

            # 가중치 저장
            for key, stats in column_stats.items():
                table_name, column_name, database_sid, schema_name = key.split("#")

                # 가중치 계산
                avg_confidence = (stats["confidence_sum"] / stats["frequency"]) if stats["frequency"] > 0 else 0
                calculated_weight = (
                    0.5 +
                    (stats["approve"] * 0.15) -
                    (stats["reject"] * 0.10) +
                    (avg_confidence * 0.05) +
                    (min(stats["frequency"], 10) * 0.02)
                )

                # 최소/최대 범위 제한 (0.2 ~ 1.5)
                calculated_weight = max(0.2, min(1.5, calculated_weight))

                weight_id = f"wc_{table_name}_{column_name}_{database_sid}_{schema_name}"

                weight_coll.upsert(
                    ids=[weight_id],
                    documents=[column_name],
                    metadatas=[{
                        "table_name": table_name,
                        "column_name": column_name,
                        "database_sid": database_sid,
                        "schema_name": schema_name,
                        "approval_count": stats["approve"],
                        "rejection_count": stats["reject"],
                        "modify_count": stats["modify"],
                        "frequency": stats["frequency"],
                        "average_confidence": round(avg_confidence, 4),
                        "calculated_weight": round(calculated_weight, 4),
                        "last_updated": datetime.now().isoformat(),
                        "type": "column_weight"
                    }]
                )

            logger.info("컬럼 가중치 계산 완료")

        except Exception as e:
            logger.error(f"컬럼 가중치 계산 실패: {e}")
            raise

    def query_feedback_summary(
        self,
        limit: int = 100,
        action_filter: Optional[str] = None
    ) -> List[Dict]:
        """
        피드백 요약 조회 (분석용)

        Args:
            limit: 조회할 행 수
            action_filter: 필터 ("approve", "modify", "reject") - 선택

        Returns:
            피드백 목록
        """
        try:
            sql_gen_coll = self.client.get_collection("feedback_sql_generation")
            user_resp_coll = self.client.get_collection("feedback_user_response")
            exec_res_coll = self.client.get_collection("feedback_execution_result")

            # 모든 SQL 생성 이력 조회
            all_sql_gen = sql_gen_coll.get()

            results = []
            for i, feedback_id in enumerate(all_sql_gen["ids"][:limit]):
                sql_meta = all_sql_gen["metadatas"][i]

                # 사용자 응답 조회
                user_resp = None
                try:
                    user_feedback = user_resp_coll.get(ids=[feedback_id])
                    if user_feedback["ids"]:
                        user_resp = user_feedback["metadatas"][0]
                except Exception:
                    pass

                # 실행 결과 조회
                exec_res = None
                try:
                    exec_result = exec_res_coll.get(ids=[feedback_id])
                    if exec_result["ids"]:
                        exec_res = exec_result["metadatas"][0]
                except Exception:
                    pass

                # 필터 적용
                if action_filter and user_resp:
                    if user_resp.get("action") != action_filter:
                        continue

                # 결과 구성
                result = {
                    "feedback_id": feedback_id,
                    "user_query": sql_meta.get("user_query", ""),
                    "selected_table": sql_meta.get("selected_table", ""),
                    "action": user_resp.get("action") if user_resp else None,
                    "user_confidence": user_resp.get("user_confidence") if user_resp else None,
                    "execution_status": exec_res.get("execution_status") if exec_res else None,
                    "row_count": exec_res.get("row_count") if exec_res else None,
                    "execution_time_ms": exec_res.get("execution_time_ms") if exec_res else None,
                    "response_time": user_resp.get("response_time") if user_resp else None
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"피드백 요약 조회 실패: {e}")
            return []

    def get_table_weights(
        self,
        database_sid: str,
        schema_name: str
    ) -> Dict[str, float]:
        """
        테이블별 가중치 조회

        Returns:
            {"TABLE_NAME": 0.92, ...}
        """
        try:
            weight_coll = self.client.get_collection("weight_table_scores")

            weights = weight_coll.get(
                where={
                    "$and": [
                        {"database_sid": database_sid},
                        {"schema_name": schema_name},
                        {"type": "table_weight"}
                    ]
                }
            )

            result = {}
            for i, weight_id in enumerate(weights["ids"]):
                metadata = weights["metadatas"][i]
                table_name = metadata.get("table_name", "")
                calculated_weight = float(metadata.get("calculated_weight", 1.0))
                result[table_name] = calculated_weight

            logger.info(f"테이블 가중치 조회: {database_sid}.{schema_name} → {len(result)}개")
            return result

        except Exception as e:
            logger.warning(f"테이블 가중치 조회 실패: {e}")
            return {}

    def get_column_weights(
        self,
        table_name: str,
        database_sid: str,
        schema_name: str
    ) -> Dict[str, float]:
        """
        컬럼별 가중치 조회

        Returns:
            {"COLUMN_NAME": 0.96, ...}
        """
        try:
            weight_coll = self.client.get_collection("weight_column_scores")

            weights = weight_coll.get(
                where={
                    "$and": [
                        {"table_name": table_name},
                        {"database_sid": database_sid},
                        {"schema_name": schema_name},
                        {"type": "column_weight"}
                    ]
                }
            )

            result = {}
            for i, weight_id in enumerate(weights["ids"]):
                metadata = weights["metadatas"][i]
                column_name = metadata.get("column_name", "")
                calculated_weight = float(metadata.get("calculated_weight", 1.0))
                result[column_name] = calculated_weight

            logger.info(f"컬럼 가중치 조회: {table_name} → {len(result)}개")
            return result

        except Exception as e:
            logger.warning(f"컬럼 가중치 조회 실패: {e}")
            return {}

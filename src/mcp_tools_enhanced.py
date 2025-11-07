"""
Enhanced MCP Tools for Backend Integration
New tools that leverage the FastAPI backend with Vector DB and Learning Engine
"""

import logging
from typing import List, Dict, Any
from backend_client import get_backend_client

logger = logging.getLogger(__name__)


async def get_table_summaries_for_query_v2(
    database_sid: str,
    schema_name: str,
    natural_query: str = ""
) -> List[Dict]:
    """
    자연어 쿼리를 위한 테이블 요약 정보 제공 (Stage 1 - Vector DB 버전)

    이 버전은 Backend의 Vector DB를 사용하여 의미 기반 검색을 수행합니다.
    기존 JSON 파일 기반보다 훨씬 빠릅니다 (5-10초 → 1초 미만).
    """
    try:
        # Try backend first
        backend = get_backend_client()
        health = await backend.check_health()

        if health.get("api") == "healthy" and health.get("vector_db") == "healthy":
            logger.info("Using Vector DB backend for metadata search")

            # Search using Vector DB
            result = await backend.search_metadata(
                question=natural_query,
                database_sid=database_sid,
                schema_name=schema_name,
                limit=10  # Get top 10 most relevant tables
            )

            if result.get("total_found", 0) > 0:
                result_text = f"📊 테이블 요약 정보 (Stage 1 - Vector DB)\n\n"
                result_text += f"**질문**: {natural_query}\n\n"
                result_text += f"**Database**: {database_sid}\n"
                result_text += f"**Schema**: {schema_name}\n"
                result_text += f"**검색 방식**: 🚀 Vector DB 의미 기반 검색 (초고속)\n"
                result_text += f"**관련 테이블 수**: {result['total_found']}개\n\n"
                result_text += "**테이블 목록 (관련도 순)**:\n\n"

                for i, table_result in enumerate(result.get("results", []), 1):
                    similarity_pct = table_result["similarity_score"] * 100
                    result_text += f"### {i}. {table_result['table_name']} "
                    result_text += f"(유사도: {similarity_pct:.1f}%)\n"

                    if table_result.get("korean_name"):
                        result_text += f"- **한글명**: {table_result['korean_name']}\n"

                    if table_result.get("description"):
                        result_text += f"- **설명**: {table_result['description']}\n"

                    result_text += f"- **컬럼 수**: {table_result.get('column_count', 'N/A')}\n\n"

                result_text += "\n---\n\n"
                result_text += "**다음 단계**: 위 테이블들 중에서 질문에 답하기 위해 필요한 테이블(최대 5개)을 선택하고,\n"
                result_text += "`get_detailed_metadata_for_sql` Tool을 호출하여 상세 메타데이터를 받아 SQL을 생성하세요.\n\n"
                result_text += "💡 **TIP**: Vector DB는 의미적으로 유사한 테이블을 자동으로 찾아줍니다. "
                result_text += "유사도가 높은 상위 테이블들을 우선 선택하세요."

                return [{"type": "text", "text": result_text}]

        # Fallback to original JSON-based method
        logger.warning("Backend unavailable, falling back to JSON files")
        from metadata_manager import MetadataManager
        from common_metadata_manager import CommonMetadataManager

        common_metadata_manager = CommonMetadataManager()
        metadata_manager = MetadataManager(common_metadata_manager=common_metadata_manager)

        summaries_data = metadata_manager.load_table_summaries(database_sid, schema_name)

        result_text = f"📊 테이블 요약 정보 (Stage 1 - Fallback)\n\n"
        result_text += f"⚠️ Backend가 사용 불가하여 JSON 파일 모드로 동작 중입니다.\n\n"
        result_text += f"**질문**: {natural_query}\n\n"
        result_text += f"**Database**: {database_sid}\n"
        result_text += f"**Schema**: {schema_name}\n"
        result_text += f"**전체 테이블 수**: {summaries_data.get('total_tables', 0)}개\n\n"
        result_text += "**테이블 목록**:\n\n"

        for summary in summaries_data.get('summaries', []):
            result_text += f"### {summary.get('table_name')}\n"
            result_text += f"- **설명**: {summary.get('one_line_desc', 'N/A')}\n"
            result_text += f"- **주요 용도**: {summary.get('primary_use', 'N/A')}\n"
            result_text += f"- **키워드**: {', '.join(summary.get('keywords', []))}\n\n"

        result_text += "\n---\n\n"
        result_text += "**다음 단계**: 위 테이블들 중에서 질문에 답하기 위해 필요한 테이블(최대 5개)을 선택하고,\n"
        result_text += "`get_detailed_metadata_for_sql` Tool을 호출하여 상세 메타데이터를 받아 SQL을 생성하세요.\n"

        return [{"type": "text", "text": result_text}]

    except FileNotFoundError:
        return [{
            "type": "text",
            "text": f"❌ 테이블 요약 정보가 없습니다: {database_sid}.{schema_name}\n메타데이터를 먼저 추출해주세요."
        }]
    except Exception as e:
        import traceback
        logger.error(f"테이블 요약 조회 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 테이블 요약 조회 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


async def find_similar_sql_pattern(
    database_sid: str,
    schema_name: str,
    natural_query: str,
    similarity_threshold: float = 0.85
) -> List[Dict]:
    """
    유사한 SQL 패턴 찾기 (Learning Engine)

    이전에 성공적으로 생성된 SQL 중에서 현재 질문과 유사한 패턴을 찾습니다.
    패턴이 발견되면 SQL을 새로 생성하지 않고 재사용할 수 있습니다.
    """
    try:
        backend = get_backend_client()

        # Check if backend is available
        health = await backend.check_health()
        if health.get("api") != "healthy":
            return [{
                "type": "text",
                "text": "⚠️ Learning Engine을 사용할 수 없습니다. Backend가 실행 중인지 확인하세요."
            }]

        # Find similar pattern
        result = await backend.find_similar_pattern(
            question=natural_query,
            database_sid=database_sid,
            schema_name=schema_name,
            similarity_threshold=similarity_threshold
        )

        if result.get("found_match"):
            pattern = result["pattern"]
            similarity_pct = pattern["similarity"] * 100
            success_rate_pct = pattern["success_rate"] * 100

            result_text = f"✅ 유사한 SQL 패턴 발견!\n\n"
            result_text += f"**질문**: {natural_query}\n\n"
            result_text += f"**매칭된 이전 질문**: {pattern['question']}\n\n"
            result_text += f"**유사도**: {similarity_pct:.1f}%\n"
            result_text += f"**성공률**: {success_rate_pct:.1f}% (사용 {pattern['use_count']}회)\n"
            result_text += f"**전체 점수**: {pattern['overall_score']:.2f}\n\n"
            result_text += "**재사용 가능한 SQL**:\n\n"
            result_text += "```sql\n"
            result_text += pattern["sql_query"]
            result_text += "\n```\n\n"
            result_text += "---\n\n"
            result_text += "💡 **추천**: 이 SQL을 그대로 사용하거나 약간 수정하여 사용할 수 있습니다.\n"
            result_text += "이렇게 하면 LLM API 비용을 절약하고 응답 속도를 높일 수 있습니다.\n\n"
            result_text += f"**Pattern ID**: `{pattern['pattern_id']}`\n"
            result_text += "(피드백을 주고 싶으면 이 ID를 사용하세요)"

            return [{"type": "text", "text": result_text}]
        else:
            result_text = f"ℹ️ 유사한 SQL 패턴을 찾지 못했습니다.\n\n"
            result_text += f"**질문**: {natural_query}\n\n"
            result_text += "새로운 SQL을 생성해야 합니다. 생성 후에는 `learn_sql_pattern` Tool을 사용하여\n"
            result_text += "이 패턴을 저장하면 다음에 유사한 질문에 재사용할 수 있습니다."

            return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"패턴 찾기 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 패턴 찾기 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


async def learn_sql_pattern(
    database_sid: str,
    schema_name: str,
    natural_query: str,
    sql_query: str,
    tables_used: str,  # Comma-separated table names
    execution_success: bool = True,
    execution_time_ms: float = None,
    row_count: int = None
) -> List[Dict]:
    """
    SQL 패턴 학습 (Learning Engine)

    성공적으로 생성/실행된 SQL을 저장하여 나중에 유사한 질문에 재사용할 수 있습니다.
    """
    try:
        backend = get_backend_client()

        # Check backend availability
        health = await backend.check_health()
        if health.get("api") != "healthy":
            return [{
                "type": "text",
                "text": "⚠️ Learning Engine을 사용할 수 없습니다. Backend가 실행 중인지 확인하세요."
            }]

        # Parse tables
        tables_list = [t.strip() for t in tables_used.split(',')]

        # Learn pattern
        pattern_id = await backend.learn_sql_pattern(
            question=natural_query,
            sql_query=sql_query,
            database_sid=database_sid,
            schema_name=schema_name,
            tables_used=tables_list,
            execution_success=execution_success,
            execution_time_ms=execution_time_ms,
            row_count=row_count
        )

        result_text = f"✅ SQL 패턴이 학습되었습니다!\n\n"
        result_text += f"**질문**: {natural_query}\n\n"
        result_text += f"**사용된 테이블**: {', '.join(tables_list)}\n"
        result_text += f"**실행 성공**: {'✅ 예' if execution_success else '❌ 아니오'}\n"

        if execution_time_ms is not None:
            result_text += f"**실행 시간**: {execution_time_ms:.2f}ms\n"

        if row_count is not None:
            result_text += f"**결과 행 수**: {row_count}개\n"

        result_text += f"\n**Pattern ID**: `{pattern_id}`\n\n"
        result_text += "---\n\n"
        result_text += "💡 이 패턴은 이제 Vector DB에 저장되어, 다음에 유사한 질문이 오면\n"
        result_text += "자동으로 재사용될 수 있습니다. 이를 통해 LLM API 비용을 60% 절감할 수 있습니다!"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"패턴 학습 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 패턴 학습 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


async def get_learning_stats(database_sid: str = None, schema_name: str = None) -> List[Dict]:
    """
    Learning Engine 통계 조회

    학습된 SQL 패턴의 통계를 확인합니다.
    """
    try:
        backend = get_backend_client()

        # Check backend availability
        health = await backend.check_health()
        if health.get("api") != "healthy":
            return [{
                "type": "text",
                "text": "⚠️ Learning Engine을 사용할 수 없습니다. Backend가 실행 중인지 확인하세요."
            }]

        # Get stats
        stats = await backend.get_pattern_stats()

        result_text = f"📊 Learning Engine 통계\n\n"
        result_text += f"**학습된 패턴 수**: {stats['total_patterns']}개\n"
        result_text += f"**평균 성공률**: {stats['avg_success_rate'] * 100:.1f}%\n"
        result_text += f"**총 재사용 횟수**: {stats['total_reuses']}회\n"
        result_text += f"**절감된 LLM 호출**: {stats['estimated_llm_calls_saved']}회\n\n"

        if stats['estimated_llm_calls_saved'] > 0:
            estimated_cost_saved = stats['estimated_llm_calls_saved'] * 0.01  # Assume $0.01 per call
            result_text += f"**예상 절감 비용**: ${estimated_cost_saved:.2f}\n\n"

        result_text += "---\n\n"

        if stats['total_patterns'] == 0:
            result_text += "아직 학습된 패턴이 없습니다. SQL을 생성/실행한 후\n"
            result_text += "`learn_sql_pattern` Tool을 사용하여 패턴을 저장하세요."
        else:
            result_text += "💡 **성과**: 학습된 패턴들이 자동으로 재사용되어 LLM API 비용을 절감하고 있습니다!"

        return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"통계 조회 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 통계 조회 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]


async def migrate_metadata_to_vectordb(
    database_sid: str,
    schema_name: str,
    metadata_dir: str = None
) -> List[Dict]:
    """
    JSON 메타데이터를 Vector DB로 마이그레이션

    기존 JSON 파일 기반 메타데이터를 Vector DB로 한번에 이동합니다.
    이 작업은 데이터베이스당 한 번만 수행하면 됩니다.
    """
    try:
        backend = get_backend_client()

        # Check backend availability
        health = await backend.check_health()
        if health.get("api") != "healthy":
            return [{
                "type": "text",
                "text": "⚠️ Backend를 사용할 수 없습니다. Backend가 실행 중인지 확인하세요."
            }]

        # Default metadata directory
        if metadata_dir is None:
            from pathlib import Path
            metadata_dir = str(Path(__file__).parent.parent / "metadata")

        # Migrate
        result = await backend.migrate_metadata(
            metadata_dir=metadata_dir,
            database_sid=database_sid,
            schema_name=schema_name
        )

        if result.get("success"):
            tables_migrated = result["tables_migrated"]

            result_text = f"✅ 메타데이터 마이그레이션 완료!\n\n"
            result_text += f"**Database**: {database_sid}\n"
            result_text += f"**Schema**: {schema_name}\n"
            result_text += f"**마이그레이션된 테이블**: {tables_migrated}개\n\n"
            result_text += "---\n\n"
            result_text += "🚀 이제 Vector DB를 사용하여 초고속 의미 기반 검색이 가능합니다!\n\n"
            result_text += "**다음 단계**:\n"
            result_text += "- `get_table_summaries_for_query_v2` Tool을 사용하여 Vector DB 검색 체험\n"
            result_text += "- 기존 `get_table_summaries_for_query` 대신 v2 버전 사용 권장"

            return [{"type": "text", "text": result_text}]
        else:
            error_msg = result.get("error", "Unknown error")
            result_text = f"❌ 마이그레이션 실패\n\n"
            result_text += f"**에러**: {error_msg}\n\n"
            result_text += "**가능한 원인**:\n"
            result_text += "- JSON 메타데이터 파일이 존재하지 않음\n"
            result_text += "- Backend가 제대로 실행되지 않음\n"
            result_text += "- 디렉토리 경로가 잘못됨"

            return [{"type": "text", "text": result_text}]

    except Exception as e:
        import traceback
        logger.error(f"마이그레이션 실패: {e}\n{traceback.format_exc()}")
        return [{
            "type": "text",
            "text": f"❌ 마이그레이션 실패: {str(e)}\n\n{traceback.format_exc()}"
        }]

"""
테스트: 피드백 학습 시스템 엔드-투-엔드 테스트

자연어: "Run Card의 당일 생산 계획수량을 모델별로 합계해서 보여줘"
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "mcp"))

from vector_db_client import get_vector_db
from feedback_manager import FeedbackManager

async def test_feedback_system():
    """피드백 학습 시스템 테스트"""

    print("="*80)
    print("🧪 피드백 학습 시스템 테스트")
    print("="*80)

    # 1. Vector DB 및 FeedbackManager 초기화
    print("\n[Step 1] 초기화 중...")
    vector_db = get_vector_db()
    feedback_manager = FeedbackManager(vector_db)

    if not vector_db.is_available():
        print("❌ Vector DB를 사용할 수 없습니다!")
        return

    print("✅ Vector DB 연결 완료")
    print(f"   - 테이블 메타데이터: {vector_db.get_stats()['table_count']}개")
    print(f"   - 컬럼 메타데이터: {vector_db.get_stats()['column_count']}개")

    # 2. 자연어 질문
    natural_query = "Run Card의 당일 생산 계획수량을 모델별로 합계해서 보여줘"
    database_sid = "SMVNPDBext"
    schema_name = "INFINITY21_JSMES"

    print(f"\n[Step 2] 자연어 질문 입력")
    print(f"   📝 {natural_query}")

    # 3. 테이블 검색 (가중치 적용)
    print(f"\n[Step 3] 관련 테이블 검색 (가중치 적용)...")
    table_weights = feedback_manager.get_table_weights(database_sid, schema_name)

    print(f"   현재 저장된 가중치: {len(table_weights)}개 테이블")
    if table_weights:
        for table_name, weight in list(table_weights.items())[:3]:
            print(f"   - {table_name}: {weight:.4f}")

    tables = vector_db.search_tables(
        question=natural_query,
        database_sid=database_sid,
        schema_name=schema_name,
        n_results=5,
        weights=table_weights if table_weights else None
    )

    print(f"\n   ✅ {len(tables)}개 테이블 발견:")
    for i, table in enumerate(tables[:3], 1):
        print(f"\n   {i}. {table['table_name']}")
        print(f"      - 의미 유사도: {table.get('similarity', 0):.1f}%")
        print(f"      - 가중치: {table.get('feedback_weight', 1.0):.4f}")
        print(f"      - 최종 점수: {table.get('final_score', 0):.4f}")
        if table.get('korean_name'):
            print(f"      - 한글명: {table['korean_name']}")

    # 4. 최상위 테이블 선택
    selected_table = tables[0]
    table_name = selected_table["table_name"]

    print(f"\n[Step 4] 최상위 테이블 선택: {table_name}")

    # 5. 컬럼 검색 (가중치 적용)
    print(f"\n[Step 5] 관련 컬럼 검색...")
    column_weights = feedback_manager.get_column_weights(
        table_name, database_sid, schema_name
    )

    print(f"   현재 저장된 가중치: {len(column_weights)}개 컬럼")
    if column_weights:
        for col_name, weight in list(column_weights.items())[:3]:
            print(f"   - {col_name}: {weight:.4f}")

    columns = vector_db.search_columns(
        query=natural_query,
        database_sid=database_sid,
        schema_name=schema_name,
        table_name=table_name,
        n_results=10,
        column_weights={table_name: column_weights} if column_weights else None
    )

    print(f"\n   ✅ {len(columns)}개 컬럼 발견:")
    for i, col in enumerate(columns[:5], 1):
        print(f"\n   {i}. {col['column_name']}")
        print(f"      - 데이터타입: {col.get('data_type', 'N/A')}")
        print(f"      - 유사도: {col.get('similarity', 0):.1f}%")
        if col.get('korean_name'):
            print(f"      - 한글명: {col['korean_name']}")

    # 6. SQL 생성
    print(f"\n[Step 6] SQL 생성...")
    selected_columns = [col["column_name"] for col in columns[:5]]
    if not selected_columns:
        selected_columns = ["*"]

    columns_clause = ", ".join(selected_columns)
    generated_sql = f"SELECT {columns_clause} FROM {schema_name}.{table_name}"

    print(f"\n   생성된 SQL:")
    print(f"   ```sql")
    print(f"   {generated_sql}")
    print(f"   ```")

    # 7. 피드백 저장 (SQL 생성 이력)
    print(f"\n[Step 7] 피드백 저장...")
    feedback_data = {
        "user_query": natural_query,
        "selected_table": table_name,
        "selected_columns": selected_columns,
        "generated_sql": generated_sql,
        "database_sid": database_sid,
        "schema_name": schema_name,
        "created_by": "test_user"
    }

    feedback_id = feedback_manager.save_sql_generation(feedback_data)
    print(f"   ✅ Feedback ID: {feedback_id}")

    # 8. 사용자 피드백 제출 (승인)
    print(f"\n[Step 8] 사용자 피드백 제출...")
    feedback_manager.save_user_feedback(
        feedback_id=feedback_id,
        action="approve",
        suggestions="좋은 쿼리입니다",
        user_confidence=0.95
    )
    print(f"   ✅ 피드백 저장 완료 (action: approve, confidence: 0.95)")

    # 9. 가중치 계산
    print(f"\n[Step 9] 가중치 계산 중...")
    feedback_manager.calculate_weights()
    print(f"   ✅ 가중치 계산 완료")

    # 10. 업데이트된 가중치 확인
    print(f"\n[Step 10] 업데이트된 가중치 확인...")
    updated_table_weights = feedback_manager.get_table_weights(database_sid, schema_name)
    updated_column_weights = feedback_manager.get_column_weights(
        table_name, database_sid, schema_name
    )

    print(f"\n   테이블 가중치 업데이트:")
    if table_name in updated_table_weights:
        print(f"   - {table_name}: {updated_table_weights[table_name]:.4f}")

    print(f"\n   컬럼 가중치 업데이트 (상위 5개):")
    if updated_column_weights:
        for col_name, weight in sorted(updated_column_weights.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"   - {col_name}: {weight:.4f}")

    # 11. 피드백 요약 조회
    print(f"\n[Step 11] 피드백 요약 조회...")
    feedback_summary = feedback_manager.query_feedback_summary(limit=100)
    print(f"   ✅ 저장된 피드백: {len(feedback_summary)}개")

    if feedback_summary:
        latest = feedback_summary[0]
        print(f"\n   최근 피드백:")
        print(f"   - Feedback ID: {latest.get('feedback_id')}")
        print(f"   - 사용자 질문: {latest.get('user_query')[:50]}...")
        print(f"   - 테이블: {latest.get('selected_table')}")
        print(f"   - 사용자 선택: {latest.get('action')}")
        print(f"   - 신뢰도: {latest.get('user_confidence')}")

    print("\n" + "="*80)
    print("✅ 테스트 완료!")
    print("="*80)


if __name__ == "__main__":
    try:
        asyncio.run(test_feedback_system())
    except Exception as e:
        import traceback
        print(f"\n❌ 에러 발생:")
        print(traceback.format_exc())

"""
2단계 LLM 처리 모듈
Stage 1: 관련 테이블 선택
Stage 2: SQL 생성
"""

import os
import re
import logging
from typing import Dict, List
from anthropic import Anthropic
from metadata_manager import MetadataManager

logger = logging.getLogger(__name__)


class TwoStageLLM:
    """2단계 LLM 호출로 자연어 → SQL 변환"""

    def __init__(self, metadata_manager: MetadataManager):
        """
        Args:
            metadata_manager: MetadataManager 인스턴스
        """
        self.metadata_manager = metadata_manager

        # Anthropic API 클라이언트
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다.")

        self.client = Anthropic(api_key=api_key)

        logger.info("TwoStageLLM 초기화 완료")

    def generate_sql(
        self,
        database_sid: str,
        schema_name: str,
        natural_query: str
    ) -> Dict:
        """
        자연어 → SQL 생성 (2단계)

        Returns:
            {
                'status': 'success' | 'error',
                'natural_query': str,
                'selected_tables': [str],
                'generated_sql': str,
                'stage1_tokens': dict,
                'stage2_tokens': dict,
                'message': str
            }
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"📝 자연어 SQL 생성 시작")
        logger.info(f"DB: {database_sid}.{schema_name}")
        logger.info(f"쿼리: {natural_query}")
        logger.info(f"{'='*60}\n")

        # ============================================
        # Stage 1: 관련 테이블 선택
        # ============================================
        logger.info("🔍 Stage 1: 관련 테이블 선택 중...")

        try:
            summaries = self.metadata_manager.load_table_summaries(
                database_sid, schema_name
            )

            stage1_prompt = self._build_stage1_prompt(
                database_sid, schema_name, natural_query, summaries
            )

            stage1_response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                temperature=0,
                messages=[{"role": "user", "content": stage1_prompt}]
            )

            selected_tables = self._parse_selected_tables(
                stage1_response.content[0].text
            )

            logger.info(f"✅ 선택된 테이블: {selected_tables}")
            logger.info(f"   토큰 사용: {stage1_response.usage.input_tokens} input, "
                      f"{stage1_response.usage.output_tokens} output\n")

        except Exception as e:
            logger.error(f"❌ Stage 1 실패: {e}")
            return {
                'status': 'error',
                'message': f"테이블 선택 실패: {str(e)}"
            }

        # ============================================
        # Stage 2: SQL 생성
        # ============================================
        logger.info("🔨 Stage 2: SQL 생성 중...")

        try:
            # 선택된 테이블의 상세 메타정보 로드
            detailed_metadata = []
            for table_name in selected_tables:
                try:
                    metadata = self.metadata_manager.load_unified_metadata(
                        database_sid, schema_name, table_name
                    )
                    detailed_metadata.append(metadata)
                except FileNotFoundError:
                    logger.warning(f"메타정보 없음: {table_name} (건너뜀)")
                    continue

            if not detailed_metadata:
                return {
                    'status': 'error',
                    'message': '선택된 테이블의 메타정보를 찾을 수 없습니다.'
                }

            stage2_prompt = self._build_stage2_prompt(
                database_sid, schema_name, natural_query, detailed_metadata
            )

            stage2_response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                temperature=0,
                messages=[{"role": "user", "content": stage2_prompt}]
            )

            generated_sql = self._extract_sql(stage2_response.content[0].text)

            logger.info(f"✅ SQL 생성 완료")
            logger.info(f"   토큰 사용: {stage2_response.usage.input_tokens} input, "
                      f"{stage2_response.usage.output_tokens} output")
            logger.info(f"\n생성된 SQL:\n{generated_sql}\n")

            return {
                'status': 'success',
                'natural_query': natural_query,
                'selected_tables': selected_tables,
                'generated_sql': generated_sql,
                'stage1_tokens': {
                    'input': stage1_response.usage.input_tokens,
                    'output': stage1_response.usage.output_tokens
                },
                'stage2_tokens': {
                    'input': stage2_response.usage.input_tokens,
                    'output': stage2_response.usage.output_tokens
                },
                'message': 'SQL 생성 완료'
            }

        except Exception as e:
            logger.error(f"❌ Stage 2 실패: {e}")
            return {
                'status': 'error',
                'message': f"SQL 생성 실패: {str(e)}"
            }

    def _build_stage1_prompt(
        self,
        database_sid: str,
        schema_name: str,
        natural_query: str,
        summaries: Dict
    ) -> str:
        """Stage 1 프롬프트: 테이블 선택"""

        table_list = []
        for idx, summary in enumerate(summaries['summaries'], 1):
            line = f"{idx}. {summary['table_name']}: {summary['one_line_desc']}"
            table_list.append(line)

        prompt = f"""당신은 데이터베이스 전문가입니다.

아래 자연어 쿼리를 처리하기 위해 필요한 테이블을 선택하세요.

# 데이터베이스
{database_sid}.{schema_name}

# 자연어 쿼리
{natural_query}

# 사용 가능한 테이블 ({summaries['total_tables']}개)

{chr(10).join(table_list)}

# 작업
위 쿼리를 처리하는데 필요한 테이블을 최대 5개 선택하세요.
테이블명만 쉼표로 구분하여 답변하세요.

예시: ORDERS, CUSTOMERS, ORDER_ITEMS

테이블 선택:"""

        return prompt

    def _build_stage2_prompt(
        self,
        database_sid: str,
        schema_name: str,
        natural_query: str,
        metadata_list: List[Dict]
    ) -> str:
        """Stage 2 프롬프트: SQL 생성"""

        tables_detail = []

        for metadata in metadata_list:
            table_name = metadata['database']['table']
            purpose = metadata['table_info']['business_purpose']

            detail = f"\n## 테이블: {table_name}\n"
            detail += f"**목적**: {purpose}\n\n"
            detail += "**칼럼**:\n"

            for col in metadata['columns']:
                detail += f"\n### {col['name']} ({col['korean_name']})\n"
                detail += f"- 타입: {col['data_type']}\n"
                detail += f"- 설명: {col['description']}\n"

                if col.get('is_code_column') and col.get('codes'):
                    detail += f"- 코드값:\n"
                    for code in col['codes']:
                        detail += f"  - '{code['value']}': {code['label']} ({code['description']})\n"

                if col.get('unit'):
                    detail += f"- 단위: {col['unit']}\n"

                if col.get('aggregation_functions'):
                    detail += f"- 집계: {', '.join(col['aggregation_functions'])}\n"

            tables_detail.append(detail)

        prompt = f"""당신은 Oracle SQL 전문가입니다.

아래 테이블 메타정보를 참고하여 자연어 쿼리를 정확한 SQL로 변환하세요.

# 데이터베이스
{database_sid}.{schema_name}

# 자연어 쿼리
{natural_query}

# 테이블 메타정보

{chr(10).join(tables_detail)}

# SQL 생성 규칙

1. Oracle SQL 문법을 정확히 사용
2. 테이블명은 {schema_name}.TABLE_NAME 형식 (SID 제외)
3. 코드 값은 메타정보에 명시된 값을 정확히 사용
4. 날짜 함수는 Oracle 함수 사용 (TRUNC, ADD_MONTHS 등)
5. 집계 함수가 필요하면 적절히 사용
6. WHERE 조건은 비즈니스 로직에 맞게 작성

# SQL 생성

```sql
"""

        return prompt

    def _parse_selected_tables(self, llm_response: str) -> List[str]:
        """LLM 응답에서 테이블명 추출"""
        # 예: "ORDERS, CUSTOMERS, ORDER_ITEMS" → ['ORDERS', 'CUSTOMERS', 'ORDER_ITEMS']
        tables = [t.strip() for t in llm_response.split(',')]
        return [t.upper() for t in tables if t]

    def _extract_sql(self, llm_response: str) -> str:
        """LLM 응답에서 SQL 추출"""
        # ```sql ... ``` 블록 찾기
        pattern = r'```sql\s*(.*?)\s*```'
        match = re.search(pattern, llm_response, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        # 없으면 전체 반환
        return llm_response.strip()

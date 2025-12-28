"""
SQL 실행 모듈
"""

import logging
import re
from pathlib import Path
from typing import Dict, List
from oracle_connector import OracleConnector

logger = logging.getLogger(__name__)


class SQLExecutor:
    """SQL 쿼리 실행 및 결과 반환"""

    def __init__(self, connector: OracleConnector):
        """
        Args:
            connector: OracleConnector 인스턴스
        """
        self.connector = connector
        self.sql_rules_path = Path(__file__).parent.parent / "sql_rules.md"

    def load_sql_rules(self) -> str:
        """SQL 작성 규칙 로드"""
        try:
            if self.sql_rules_path.exists():
                with open(self.sql_rules_path, 'r', encoding='utf-8') as f:
                    return f.read()
            return ""
        except Exception as e:
            logger.warning(f"SQL 규칙 로드 실패: {e}")
            return ""

    def check_index_optimization(self, sql: str) -> Dict:
        """
        인덱스 최적화 규칙 위반 여부 체크

        Returns:
            {
                'violations': [str],  # 위반 사항 목록
                'warnings': [str]      # 경고 사항 목록
            }
        """
        violations = []
        warnings = []

        sql_upper = sql.upper()

        # 1. TRUNC 함수 사용 체크 (날짜 컬럼 변형)
        if re.search(r'WHERE\s+.*TRUNC\s*\(', sql_upper):
            violations.append(
                "❌ TRUNC() 함수로 날짜 컬럼 변형 감지\n"
                "   인덱스 사용 불가. 범위 검색으로 변경하세요.\n"
                "   예: WHERE date_col >= DATE '2025-01-01' AND date_col < DATE '2025-01-02'"
            )

        # 2. TO_CHAR 함수 사용 체크 (날짜를 문자열로 변환)
        if re.search(r'WHERE\s+.*TO_CHAR\s*\([^)]+,\s*[\'"]', sql_upper):
            violations.append(
                "❌ TO_CHAR()로 날짜 컬럼 변형 감지\n"
                "   인덱스 사용 불가. 날짜 비교를 직접 사용하세요.\n"
                "   예: WHERE date_col >= TO_DATE('2025-01-01', 'YYYY-MM-DD')"
            )

        # 3. UPPER/LOWER 함수 사용 체크
        if re.search(r'WHERE\s+.*(UPPER|LOWER)\s*\(', sql_upper):
            violations.append(
                "❌ UPPER/LOWER 함수로 문자열 컬럼 변형 감지\n"
                "   인덱스 사용 불가. 직접 비교하세요.\n"
                "   예: WHERE col = 'VALUE'"
            )

        # 4. 컬럼 왼쪽 연산자 체크
        if re.search(r'WHERE\s+\w+\s*[\*\+\-\/]\s*\d+\s*[=<>]', sql_upper):
            warnings.append(
                "⚠️ WHERE 절에서 컬럼 왼쪽에 연산자 사용 감지\n"
                "   인덱스 사용이 제한될 수 있습니다.\n"
                "   예: WHERE col > 100 / 1.1 (연산을 오른쪽으로)"
            )

        # 5. LIKE '%...%' 패턴 체크
        if re.search(r"LIKE\s+['\"]%.*%['\"]", sql_upper):
            warnings.append(
                "⚠️ LIKE '%...%' 패턴 감지 (중간/끝 와일드카드)\n"
                "   Full Table Scan 발생 가능성 높음.\n"
                "   가능하면 앞부분 고정 패턴 사용: LIKE 'ABC%'"
            )

        # 6. = NULL 체크
        if re.search(r'=\s*NULL|!=\s*NULL|<>\s*NULL', sql_upper):
            violations.append(
                "❌ = NULL 또는 != NULL 사용 감지\n"
                "   항상 FALSE를 반환합니다.\n"
                "   IS NULL 또는 IS NOT NULL을 사용하세요."
            )

        return {
            'violations': violations,
            'warnings': warnings
        }

    def execute_select(
        self,
        sql: str,
        max_rows: int = 1000
    ) -> Dict:
        """
        SELECT 쿼리 실행

        Args:
            sql: SQL 쿼리
            max_rows: 최대 반환 행 수

        Returns:
            {
                'status': 'success' | 'error',
                'sql': str,
                'columns': [str],
                'rows': [dict],
                'row_count': int,
                'message': str,
                'optimization_check': dict  # 인덱스 최적화 검사 결과
            }
        """
        try:
            # SELECT 쿼리만 허용
            if not sql.strip().upper().startswith('SELECT'):
                return {
                    'status': 'error',
                    'sql': sql,
                    'message': 'SELECT 쿼리만 실행 가능합니다.'
                }

            # 인덱스 최적화 규칙 검사
            optimization_check = self.check_index_optimization(sql)

            # 쿼리 실행
            results = self.connector.execute_query(sql)

            # 결과 제한
            if len(results) > max_rows:
                results = results[:max_rows]
                truncated = True
            else:
                truncated = False

            # 칼럼명 추출
            columns = list(results[0].keys()) if results else []

            message = f"✅ {len(results)}개 행 반환"
            if truncated:
                message += f" (최대 {max_rows}개로 제한됨)"

            return {
                'status': 'success',
                'sql': sql,
                'columns': columns,
                'rows': results,
                'row_count': len(results),
                'truncated': truncated,
                'message': message,
                'optimization_check': optimization_check
            }

        except Exception as e:
            logger.error(f"SQL 실행 에러: {e}")
            return {
                'status': 'error',
                'sql': sql,
                'message': f"SQL 실행 실패: {str(e)}"
            }

    def validate_sql(self, sql: str) -> Dict:
        """
        SQL 유효성 검증 (실행 X)

        Returns:
            {
                'valid': bool,
                'errors': [str],
                'warnings': [str]
            }
        """
        errors = []
        warnings = []

        sql_upper = sql.strip().upper()

        # 기본 검증
        if not any(op in sql_upper for op in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
            errors.append("유효한 SQL 연산자가 없습니다.")

        # 위험한 키워드 검사
        dangerous_keywords = ['DROP', 'TRUNCATE', 'ALTER', 'CREATE']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                warnings.append(f"위험한 연산 감지: {keyword}")

        # INSERT/UPDATE/DELETE 검사
        if any(op in sql_upper for op in ['INSERT', 'UPDATE', 'DELETE']):
            warnings.append("데이터 변경 쿼리입니다. 신중하게 실행하세요.")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }

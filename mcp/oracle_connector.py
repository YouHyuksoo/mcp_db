"""
Oracle Database 연결 모듈
oracledb를 사용하여 Oracle DB에 연결하고 쿼리를 실행합니다.
"""

import oracledb
import logging
from typing import Dict, List, Any, Optional
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class OracleConnector:
    """Oracle Database 연결 관리"""

    def __init__(self, host: str, port: int, service_name: str,
                 user: str, password: str):
        """
        Oracle DB 연결 초기화

        Args:
            host: 호스트 주소
            port: 포트 번호
            service_name: 서비스명
            user: 사용자명
            password: 비밀번호
        """
        self.host = host
        self.port = port
        self.service_name = service_name
        self.user = user
        self.password = password
        self.connection = None

        logger.info(f"OracleConnector 초기화: {host}:{port}/{service_name}")

    def connect(self) -> bool:
        """DB 연결"""
        try:
            dsn = f"{self.host}:{self.port}/{self.service_name}"

            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=dsn
            )

            logger.info(f"✅ Oracle DB 연결 성공: {self.service_name}")
            return True

        except Exception as e:
            logger.error(f"❌ Oracle DB 연결 실패: {e}")
            return False

    def disconnect(self):
        """DB 연결 종료"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Oracle DB 연결 종료")

    @contextmanager
    def get_cursor(self):
        """커서 컨텍스트 매니저"""
        if not self.connection:
            raise Exception("DB 연결이 없습니다. connect()를 먼저 호출하세요.")

        cursor = self.connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()

    def execute_query(self, query: str, params: Dict = None) -> List[Dict[str, Any]]:
        """
        SELECT 쿼리 실행

        Args:
            query: SQL SELECT 쿼리
            params: 바인딩 파라미터 (딕셔너리)

        Returns:
            결과 행의 리스트 (딕셔너리 형태)
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params or {})

                # 컬럼명 가져오기
                columns = [desc[0] for desc in cursor.description]

                # 결과를 딕셔너리 리스트로 변환
                results = []
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))

                return results

        except Exception as e:
            logger.error(f"쿼리 실행 에러: {e}")
            logger.error(f"쿼리: {query}")
            raise

    def execute_dml(self, sql: str, params: Dict = None, commit: bool = True) -> int:
        """
        INSERT/UPDATE/DELETE 실행

        Args:
            sql: DML 쿼리
            params: 바인딩 파라미터
            commit: 자동 커밋 여부

        Returns:
            영향받은 행 수
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(sql, params or {})
                rows_affected = cursor.rowcount

                if commit:
                    self.connection.commit()

                return rows_affected

        except Exception as e:
            if commit:
                self.connection.rollback()
            logger.error(f"DML 실행 에러: {e}")
            raise

    def extract_table_columns(self, schema_name: str, table_name: str) -> List[Dict]:
        """테이블 칼럼 정보 추출"""
        query = """
            SELECT
                c.COLUMN_NAME,
                c.COLUMN_ID,
                c.DATA_TYPE,
                c.DATA_LENGTH,
                c.DATA_PRECISION,
                c.DATA_SCALE,
                c.NULLABLE,
                c.DATA_DEFAULT,
                cc.COMMENTS
            FROM ALL_TAB_COLUMNS c
            LEFT JOIN ALL_COL_COMMENTS cc
                ON c.OWNER = cc.OWNER
                AND c.TABLE_NAME = cc.TABLE_NAME
                AND c.COLUMN_NAME = cc.COLUMN_NAME
            WHERE c.OWNER = :p_schema
              AND c.TABLE_NAME = :p_table
            ORDER BY c.COLUMN_ID
        """

        return self.execute_query(query, {
            'p_schema': schema_name.upper(),
            'p_table': table_name.upper()
        })

    def extract_primary_keys(self, schema_name: str, table_name: str) -> List[str]:
        """Primary Key 추출"""
        query = """
            SELECT cols.COLUMN_NAME
            FROM ALL_CONSTRAINTS cons
            JOIN ALL_CONS_COLUMNS cols
                ON cons.CONSTRAINT_NAME = cols.CONSTRAINT_NAME
                AND cons.OWNER = cols.OWNER
            WHERE cons.CONSTRAINT_TYPE = 'P'
              AND cons.OWNER = :p_schema
              AND cons.TABLE_NAME = :p_table
            ORDER BY cols.POSITION
        """

        results = self.execute_query(query, {
            'p_schema': schema_name.upper(),
            'p_table': table_name.upper()
        })

        return [row['COLUMN_NAME'] for row in results]

    def extract_foreign_keys(self, schema_name: str, table_name: str) -> List[Dict]:
        """Foreign Key 추출"""
        query = """
            SELECT
                a.COLUMN_NAME,
                c_pk.TABLE_NAME as REF_TABLE,
                b.COLUMN_NAME as REF_COLUMN,
                c.CONSTRAINT_NAME
            FROM ALL_CONS_COLUMNS a
            JOIN ALL_CONSTRAINTS c ON a.CONSTRAINT_NAME = c.CONSTRAINT_NAME
            JOIN ALL_CONSTRAINTS c_pk ON c.R_CONSTRAINT_NAME = c_pk.CONSTRAINT_NAME
            JOIN ALL_CONS_COLUMNS b ON c_pk.CONSTRAINT_NAME = b.CONSTRAINT_NAME
            WHERE c.CONSTRAINT_TYPE = 'R'
              AND a.OWNER = :p_schema
              AND a.TABLE_NAME = :p_table
        """

        return self.execute_query(query, {
            'p_schema': schema_name.upper(),
            'p_table': table_name.upper()
        })

    def extract_indexes(self, schema_name: str, table_name: str) -> List[Dict]:
        """인덱스 정보 추출"""
        query = """
            SELECT
                i.INDEX_NAME,
                i.INDEX_TYPE,
                i.UNIQUENESS,
                LISTAGG(ic.COLUMN_NAME, ', ')
                    WITHIN GROUP (ORDER BY ic.COLUMN_POSITION) as COLUMNS
            FROM ALL_INDEXES i
            JOIN ALL_IND_COLUMNS ic
                ON i.INDEX_NAME = ic.INDEX_NAME
                AND i.OWNER = ic.INDEX_OWNER
            WHERE i.TABLE_OWNER = :p_schema
              AND i.TABLE_NAME = :p_table
            GROUP BY i.INDEX_NAME, i.INDEX_TYPE, i.UNIQUENESS
        """

        return self.execute_query(query, {
            'p_schema': schema_name.upper(),
            'p_table': table_name.upper()
        })

    def get_table_comment(self, schema_name: str, table_name: str) -> str:
        """테이블 코멘트 조회"""
        query = """
            SELECT COMMENTS
            FROM ALL_TAB_COMMENTS
            WHERE OWNER = :p_schema
              AND TABLE_NAME = :p_table
        """

        result = self.execute_query(query, {
            'p_schema': schema_name.upper(),
            'p_table': table_name.upper()
        })

        return result[0]['COMMENTS'] if result and result[0]['COMMENTS'] else ""

    def list_schemas(self) -> List[str]:
        """모든 스키마 목록"""
        query = """
            SELECT DISTINCT OWNER
            FROM ALL_TABLES
            ORDER BY OWNER
        """

        results = self.execute_query(query)
        return [row['OWNER'] for row in results]

    def list_tables(self, schema_name: str, table_filter: str = None) -> List[Dict]:
        """
        스키마의 테이블 목록

        Args:
            schema_name: 스키마 이름
            table_filter: 테이블 이름 필터 (LIKE 패턴, 예: 'ISYS_%', '%_MASTER')
        """
        if table_filter:
            query = """
                SELECT
                    TABLE_NAME,
                    NUM_ROWS,
                    BLOCKS,
                    LAST_ANALYZED
                FROM ALL_TABLES
                WHERE OWNER = :p_schema
                  AND TABLE_NAME LIKE :p_filter
                ORDER BY TABLE_NAME
            """
            return self.execute_query(query, {
                'p_schema': schema_name.upper(),
                'p_filter': table_filter.upper()
            })
        else:
            query = """
                SELECT
                    TABLE_NAME,
                    NUM_ROWS,
                    BLOCKS,
                    LAST_ANALYZED
                FROM ALL_TABLES
                WHERE OWNER = :p_schema
                ORDER BY TABLE_NAME
            """
            return self.execute_query(query, {'p_schema': schema_name.upper()})

    def list_procedures(self, schema_name: str) -> List[Dict]:
        """프로시저/함수 목록"""
        query = """
            SELECT
                OBJECT_NAME,
                OBJECT_TYPE,
                CREATED,
                LAST_DDL_TIME,
                STATUS
            FROM ALL_OBJECTS
            WHERE OWNER = :p_schema
              AND OBJECT_TYPE IN ('PROCEDURE', 'FUNCTION')
            ORDER BY OBJECT_TYPE, OBJECT_NAME
        """

        return self.execute_query(query, {'p_schema': schema_name.upper()})

    def get_procedure_source(self, schema_name: str, procedure_name: str) -> str:
        """프로시저/함수 소스 코드"""
        query = """
            SELECT TEXT
            FROM ALL_SOURCE
            WHERE OWNER = :p_schema
              AND NAME = :p_procname
              AND TYPE IN ('PROCEDURE', 'FUNCTION', 'PACKAGE', 'PACKAGE BODY')
            ORDER BY TYPE, LINE
        """

        results = self.execute_query(query, {
            'p_schema': schema_name.upper(),
            'p_procname': procedure_name.upper()
        })

        return ''.join([row['TEXT'] for row in results])

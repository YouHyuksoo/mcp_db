"""
@file generate_table_column_csv.py
@description
이 파일은 Oracle DB에서 테이블별 컬럼 정보를 추출하고,
기존 column_definitions.csv의 한국어 설명을 매핑하여
새로운 table_column_definitions.csv를 생성합니다.

초보자 가이드:
1. **Oracle 메타데이터 조회**: ALL_TAB_COLUMNS, ALL_COL_COMMENTS에서 컬럼 정보 추출
2. **한국어 설명 매핑**: 기존 column_definitions.csv에서 컬럼명 → 한국어 설명 매핑
3. **결과 CSV**: table_name + column_name 조합으로 고유 식별

사용법:
    python generate_table_column_csv.py

출력 파일:
    data/SMVNPDBext/INFINITY21_JSMES/csv_uploads/table_column_definitions.csv

작성일: 2025-12-29
"""

import sys
import csv
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

# 프로젝트 경로 설정
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "mcp"))

import oracledb
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv(project_root / ".env")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TableColumnCSVGenerator:
    """
    테이블별 컬럼 정보 CSV 생성기

    ★ 핵심 기능:
    1. Oracle에서 테이블별 컬럼 정보 조회
    2. 기존 column_definitions.csv에서 한국어 설명 매핑
    3. 새 형식의 table_column_definitions.csv 생성
    """

    def __init__(self, database_sid: str, schema_name: str):
        self.database_sid = database_sid
        self.schema_name = schema_name

        # 경로 설정
        self.data_dir = project_root / "data" / database_sid / schema_name / "csv_uploads"
        self.old_csv_path = self.data_dir / "column_definitions.csv"
        self.new_csv_path = self.data_dir / "table_column_definitions.csv"

        # DB 연결
        self.db_connection = None

        # 기존 컬럼 정의 로드
        self.column_definitions = {}

    def load_existing_definitions(self) -> Dict[str, Dict[str, str]]:
        """
        기존 column_definitions.csv 로드

        Returns:
            {column_name: {korean_name, description, code_values}}
        """
        if not self.old_csv_path.exists():
            logger.warning(f"기존 컬럼 정의 파일 없음: {self.old_csv_path}")
            return {}

        definitions = {}
        encodings = ['utf-8-sig', 'utf-8', 'cp949']

        for enc in encodings:
            try:
                with open(self.old_csv_path, 'r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        col_name = row.get("column_name", "").strip().upper()
                        if col_name:
                            definitions[col_name] = {
                                "korean_name": row.get("korean_name", "").strip(),
                                "description": row.get("description", "").strip(),
                                "code_values": row.get("code_values", "").strip()
                            }
                logger.info(f"✓ 기존 컬럼 정의 {len(definitions)}개 로드")
                break
            except UnicodeDecodeError:
                continue

        return definitions

    def connect_oracle(self) -> bool:
        """Oracle DB 연결"""
        try:
            # credentials_manager 직접 import
            sys.path.insert(0, str(project_root / "mcp"))
            from credentials_manager import CredentialsManager

            credentials_dir = project_root / "data" / "credentials"
            cred_manager = CredentialsManager(str(credentials_dir))
            credentials = cred_manager.load_credentials(self.database_sid)

            dsn = oracledb.makedsn(
                host=credentials['host'],
                port=credentials['port'],
                service_name=credentials.get('service_name', credentials.get('database_sid'))
            )

            self.db_connection = oracledb.connect(
                user=credentials['user'],
                password=credentials['password'],
                dsn=dsn
            )

            logger.info(f"✓ Oracle 연결 성공: {self.database_sid}")
            return True

        except Exception as e:
            logger.error(f"Oracle 연결 실패: {e}")
            return False

    def fetch_table_columns(self) -> List[Dict[str, Any]]:
        """
        Oracle에서 테이블별 컬럼 정보 조회

        Returns:
            [
                {
                    table_name, column_name, data_type, data_length,
                    nullable, column_id, column_comment, table_comment
                },
                ...
            ]
        """
        if not self.db_connection:
            return []

        query = """
            SELECT
                c.TABLE_NAME,
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.DATA_LENGTH,
                c.DATA_PRECISION,
                c.DATA_SCALE,
                c.NULLABLE,
                c.COLUMN_ID,
                NVL(cc.COMMENTS, '') as COLUMN_COMMENT,
                NVL(tc.COMMENTS, '') as TABLE_COMMENT
            FROM ALL_TAB_COLUMNS c
            LEFT JOIN ALL_COL_COMMENTS cc
                ON c.OWNER = cc.OWNER
                AND c.TABLE_NAME = cc.TABLE_NAME
                AND c.COLUMN_NAME = cc.COLUMN_NAME
            LEFT JOIN ALL_TAB_COMMENTS tc
                ON c.OWNER = tc.OWNER
                AND c.TABLE_NAME = tc.TABLE_NAME
            WHERE c.OWNER = :schema_name
            ORDER BY c.TABLE_NAME, c.COLUMN_ID
        """

        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query, {'schema_name': self.schema_name})

            columns = []
            for row in cursor:
                columns.append({
                    'table_name': row[0],
                    'column_name': row[1],
                    'data_type': row[2],
                    'data_length': row[3],
                    'data_precision': row[4],
                    'data_scale': row[5],
                    'nullable': row[6],
                    'column_id': row[7],
                    'column_comment': row[8] or '',
                    'table_comment': row[9] or ''
                })

            cursor.close()
            logger.info(f"✓ Oracle에서 {len(columns)}개 컬럼 조회 완료")
            return columns

        except Exception as e:
            logger.error(f"컬럼 조회 실패: {e}")
            return []

    def fetch_primary_keys(self) -> Dict[str, List[str]]:
        """PK 정보 조회"""
        if not self.db_connection:
            return {}

        query = """
            SELECT
                acc.TABLE_NAME,
                acc.COLUMN_NAME
            FROM ALL_CONS_COLUMNS acc
            JOIN ALL_CONSTRAINTS ac
                ON acc.OWNER = ac.OWNER
                AND acc.CONSTRAINT_NAME = ac.CONSTRAINT_NAME
            WHERE ac.OWNER = :schema_name
            AND ac.CONSTRAINT_TYPE = 'P'
            ORDER BY acc.TABLE_NAME, acc.POSITION
        """

        try:
            cursor = self.db_connection.cursor()
            cursor.execute(query, {'schema_name': self.schema_name})

            pk_map = {}
            for row in cursor:
                table_name = row[0]
                column_name = row[1]

                if table_name not in pk_map:
                    pk_map[table_name] = []
                pk_map[table_name].append(column_name)

            cursor.close()
            logger.info(f"✓ PK 정보 조회: {len(pk_map)}개 테이블")
            return pk_map

        except Exception as e:
            logger.error(f"PK 조회 실패: {e}")
            return {}

    def generate_csv(self) -> int:
        """
        테이블별 컬럼 CSV 생성

        Returns:
            생성된 행 수
        """
        # 1. 기존 컬럼 정의 로드
        self.column_definitions = self.load_existing_definitions()

        # 2. Oracle 연결
        if not self.connect_oracle():
            return 0

        # 3. 컬럼 정보 조회
        columns = self.fetch_table_columns()
        if not columns:
            return 0

        # 4. PK 정보 조회
        pk_map = self.fetch_primary_keys()

        # 5. CSV 생성
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # CSV 헤더
        fieldnames = [
            'table_name',
            'column_name',
            'korean_name',           # 기존 column_definitions에서 매핑
            'description',           # 기존 column_definitions에서 매핑
            'data_type',
            'data_length',
            'nullable',
            'is_pk',
            'column_comment',        # Oracle에서 가져온 코멘트
            'table_comment',
            'code_values'            # 기존 column_definitions에서 매핑
        ]

        rows_written = 0

        with open(self.new_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for col in columns:
                table_name = col['table_name']
                column_name = col['column_name']

                # 기존 정의에서 한국어 설명 매핑
                existing_def = self.column_definitions.get(column_name.upper(), {})

                # 한국어 이름 우선순위: 기존 정의 > Oracle 코멘트 > 빈 값
                korean_name = existing_def.get('korean_name', '') or col['column_comment'] or ''
                description = existing_def.get('description', '') or col['column_comment'] or ''
                code_values = existing_def.get('code_values', '')

                # PK 여부
                is_pk = 'Y' if (table_name in pk_map and column_name in pk_map[table_name]) else 'N'

                # 데이터 타입 포맷팅
                data_type = col['data_type']
                if col['data_precision'] and col['data_scale'] is not None:
                    data_type = f"{data_type}({col['data_precision']},{col['data_scale']})"
                elif col['data_length'] and col['data_type'] in ('VARCHAR2', 'CHAR', 'NVARCHAR2'):
                    data_type = f"{data_type}({col['data_length']})"

                row = {
                    'table_name': table_name,
                    'column_name': column_name,
                    'korean_name': korean_name,
                    'description': description,
                    'data_type': data_type,
                    'data_length': col['data_length'] or '',
                    'nullable': col['nullable'],
                    'is_pk': is_pk,
                    'column_comment': col['column_comment'],
                    'table_comment': col['table_comment'],
                    'code_values': code_values
                }

                writer.writerow(row)
                rows_written += 1

                if rows_written % 1000 == 0:
                    logger.info(f"진행중... {rows_written}행 작성")

        # Oracle 연결 종료
        if self.db_connection:
            self.db_connection.close()

        logger.info(f"✓ CSV 생성 완료: {self.new_csv_path}")
        logger.info(f"  총 {rows_written}개 컬럼")

        return rows_written


def main():
    """메인 실행 함수"""
    database_sid = "SMVNPDBext"
    schema_name = "INFINITY21_JSMES"

    logger.info("=" * 60)
    logger.info("테이블별 컬럼 CSV 생성 시작")
    logger.info(f"Database: {database_sid}")
    logger.info(f"Schema: {schema_name}")
    logger.info("=" * 60)

    generator = TableColumnCSVGenerator(database_sid, schema_name)
    count = generator.generate_csv()

    logger.info("=" * 60)
    logger.info(f"완료: 총 {count}개 컬럼")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

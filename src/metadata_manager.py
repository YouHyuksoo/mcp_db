"""
메타정보 관리 모듈
DB 스키마 정보 + 공통 메타데이터를 통합하여 unified_metadata 생성
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging
import traceback

logger = logging.getLogger(__name__)


class MetadataManager:
    """통합 메타정보 관리"""

    def __init__(self, metadata_dir: str = "./metadata", common_metadata_manager=None):
        """
        Args:
            metadata_dir: 메타정보 저장 디렉토리
            common_metadata_manager: CommonMetadataManager 인스턴스
        """
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.common_metadata_manager = common_metadata_manager
        logger.info(f"MetadataManager 초기화: {self.metadata_dir}")

    def integrate_metadata(
        self,
        database_sid: str,
        schema_name: str,
        table_name: str,
        db_schema: Dict,
        table_info: Optional[Dict] = None
    ) -> Dict:
        """
        DB 스키마 + 공통 메타데이터 통합

        Args:
            database_sid: DB SID
            schema_name: 스키마명
            table_name: 테이블명
            db_schema: DB에서 추출한 스키마 정보
            table_info: 테이블별 비즈니스 정보 (선택사항)

        Returns:
            통합 메타정보
        """
        table_name_upper = table_name.upper()

        # 공통 메타데이터 로드 (DB별)
        common_columns = {}
        code_definitions = {}

        if self.common_metadata_manager:
            common_columns = self.common_metadata_manager.load_common_columns(database_sid)
            code_definitions = self.common_metadata_manager.load_code_definitions(database_sid)

        # 테이블 정보 (없으면 빈 dict)
        if table_info is None:
            table_info = {}

        # 통합 메타데이터 생성
        unified = {
            'database': {
                'sid': database_sid,
                'schema': schema_name,
                'table': table_name
            },
            'table_info': {
                'business_purpose': table_info.get('business_purpose', ''),
                'usage_scenarios': table_info.get('usage_scenarios', []),
                'related_tables': table_info.get('related_tables', []),
                'table_comment': db_schema.get('table_comment', '')
            },
            'columns': [],
            'relationships': {
                'primary_keys': db_schema.get('primary_keys', []),
                'foreign_keys': db_schema.get('foreign_keys', [])
            },
            'indexes': db_schema.get('indexes', []),
            'metadata_info': {
                'created_at': datetime.now().isoformat(),
                'version': '1.0'
            }
        }

        # 칼럼 통합 (DB 스키마 + 공통 칼럼 정보)
        for col in db_schema.get('columns', []):
            col_name = col['COLUMN_NAME']

            # 공통 칼럼 정보 매칭
            common_col = common_columns.get(col_name, {})

            column_data = {
                'name': col_name,
                'position': col['COLUMN_ID'],
                'data_type': self._format_data_type(col),
                'nullable': col['NULLABLE'] == 'Y',
                'default_value': col.get('DATA_DEFAULT'),
                'is_primary_key': col_name in db_schema.get('primary_keys', []),
                # 공통 칼럼 정보 사용
                'korean_name': common_col.get('korean_name', ''),
                'description': common_col.get('description', col.get('COMMENTS', '')),
                'business_rule': common_col.get('business_rule', ''),
                'sample_values': common_col.get('sample_values', ''),
                'unit': common_col.get('unit', ''),
                'is_code_column': common_col.get('is_code_column', False),
                'aggregation_functions': common_col.get('aggregation_functions', ''),
                'is_sensitive': common_col.get('is_sensitive', False)
            }

            # 코드 값 추가 (코드 칼럼인 경우)
            if column_data['is_code_column'] and col_name in code_definitions:
                # 코드 정의를 리스트 형태로 변환
                codes_dict = code_definitions[col_name]
                column_data['codes'] = [
                    {
                        'value': code_value,
                        'label': code_info.get('code_label', ''),
                        'description': code_info.get('code_description', ''),
                        'display_order': code_info.get('display_order', 999),
                        'is_active': code_info.get('is_active', True),
                        'parent_code': code_info.get('parent_code', ''),
                        'state_transition': code_info.get('state_transition', '')
                    }
                    for code_value, code_info in sorted(
                        codes_dict.items(),
                        key=lambda x: x[1].get('display_order', 999)
                    )
                ]

            unified['columns'].append(column_data)

        return unified

    def _format_data_type(self, col: Dict) -> str:
        """데이터 타입 포맷팅"""
        data_type = col['DATA_TYPE']

        if data_type == 'NUMBER':
            if col.get('DATA_PRECISION'):
                if col.get('DATA_SCALE'):
                    return f"NUMBER({col['DATA_PRECISION']},{col['DATA_SCALE']})"
                else:
                    return f"NUMBER({col['DATA_PRECISION']})"
            else:
                return "NUMBER"

        elif data_type in ['VARCHAR2', 'CHAR']:
            return f"{data_type}({col['DATA_LENGTH']})"

        else:
            return data_type

    def save_unified_metadata(
        self,
        database_sid: str,
        schema_name: str,
        table_name: str,
        metadata: Dict
    ):
        """통합 메타정보 저장"""
        table_dir = self.metadata_dir / database_sid / schema_name / table_name
        table_dir.mkdir(parents=True, exist_ok=True)

        file_path = table_dir / "unified_metadata.json"

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 통합 메타정보 저장: {database_sid}.{schema_name}.{table_name}")

    def load_unified_metadata(
        self,
        database_sid: str,
        schema_name: str,
        table_name: str
    ) -> Dict:
        """통합 메타정보 로드"""
        file_path = self.metadata_dir / database_sid / schema_name / table_name / "unified_metadata.json"

        if not file_path.exists():
            raise FileNotFoundError(f"메타정보가 없습니다: {database_sid}.{schema_name}.{table_name}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def generate_table_summaries(
        self,
        database_sid: str,
        schema_name: str
    ) -> Dict:
        """
        테이블 요약 정보 생성 (Stage 1용)

        Returns:
            {
                'database_sid': str,
                'schema_name': str,
                'total_tables': int,
                'summaries': [
                    {
                        'table_name': str,
                        'one_line_desc': str,
                        'keywords': [str],
                        'primary_use': str
                    }
                ]
            }
        """
        schema_dir = self.metadata_dir / database_sid / schema_name

        if not schema_dir.exists():
            return {
                'database_sid': database_sid,
                'schema_name': schema_name,
                'total_tables': 0,
                'summaries': []
            }

        summaries = []

        for table_dir in schema_dir.iterdir():
            if not table_dir.is_dir():
                continue

            metadata_file = table_dir / "unified_metadata.json"
            if not metadata_file.exists():
                continue

            try:
                metadata = self.load_unified_metadata(database_sid, schema_name, table_dir.name)

                # 주요 칼럼 추출 (상위 5개)
                key_columns = [col['name'] for col in metadata['columns'][:5]]

                # 키워드 추출
                keywords = []
                if metadata['table_info']['business_purpose']:
                    # 간단한 키워드 추출 (실제로는 더 정교한 처리 필요)
                    keywords = metadata['table_info']['business_purpose'].split()[:5]

                summaries.append({
                    'table_name': metadata['database']['table'],
                    'one_line_desc': f"{metadata['table_info']['business_purpose']} ({', '.join(key_columns)} 등 {len(metadata['columns'])}개 칼럼)",
                    'keywords': keywords,
                    'primary_use': ', '.join(metadata['table_info']['usage_scenarios'][:2])
                })

            except Exception as e:
                logger.error(f"테이블 요약 생성 실패 ({table_dir.name}): {e}\n{traceback.format_exc()}")
                continue

        result = {
            'database_sid': database_sid,
            'schema_name': schema_name,
            'total_tables': len(summaries),
            'summaries': summaries
        }

        # 저장
        summary_file = schema_dir / "table_summaries.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"✅ 테이블 요약 생성: {len(summaries)}개")

        return result

    def load_table_summaries(
        self,
        database_sid: str,
        schema_name: str
    ) -> Dict:
        """테이블 요약 로드"""
        file_path = self.metadata_dir / database_sid / schema_name / "table_summaries.json"

        if not file_path.exists():
            # 없으면 생성
            return self.generate_table_summaries(database_sid, schema_name)

        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def list_tables(self, database_sid: str, schema_name: str) -> List[str]:
        """스키마의 테이블 목록"""
        schema_dir = self.metadata_dir / database_sid / schema_name

        if not schema_dir.exists():
            return []

        tables = []
        for table_dir in schema_dir.iterdir():
            if table_dir.is_dir():
                tables.append(table_dir.name)

        return sorted(tables)

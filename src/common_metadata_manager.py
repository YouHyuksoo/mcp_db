"""
공통 메타데이터 관리자
사용자가 제공하는 공통 칼럼 정보와 코드 정보를 관리하고 CSV 생성
"""

import json
import csv
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import traceback


class CommonMetadataManager:
    """공통 메타데이터 관리"""

    def __init__(self, base_dir: str = None):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            self.base_dir = Path(__file__).parent.parent

        # 공통 메타데이터 저장 폴더 (DB별로 구분)
        self.common_metadata_dir = self.base_dir / "common_metadata"
        self.common_metadata_dir.mkdir(exist_ok=True)

    def _get_db_dir(self, database_sid: str) -> Path:
        """DB별 폴더 경로"""
        db_dir = self.common_metadata_dir / database_sid
        db_dir.mkdir(exist_ok=True)
        return db_dir

    def _get_common_columns_file(self, database_sid: str) -> Path:
        """DB별 공통 칼럼 파일 경로"""
        return self._get_db_dir(database_sid) / "common_columns.json"

    def _get_code_definitions_file(self, database_sid: str) -> Path:
        """DB별 코드 정의 파일 경로"""
        return self._get_db_dir(database_sid) / "code_definitions.json"

    # ============================================
    # 공통 칼럼 정보 관리
    # ============================================

    def save_common_columns(self, database_sid: str, columns: List[Dict]) -> bool:
        """
        공통 칼럼 정보 저장

        Args:
            columns: [
                {
                    'column_name': 'STATUS',
                    'korean_name': '상태',
                    'description': '처리 상태 코드',
                    'is_code_column': True,
                    'sample_values': '01|02|03',
                    'business_rule': '01→02→03 순서로 전이',
                    'unit': '',
                    'aggregation_functions': '',
                    'is_sensitive': False
                },
                ...
            ]
        """
        try:
            # 기존 데이터 로드
            existing = self.load_common_columns(database_sid)

            # 칼럼명을 키로 하는 딕셔너리로 변환
            columns_dict = {col['column_name']: col for col in columns}

            # 기존 데이터 업데이트
            existing.update(columns_dict)

            # 메타데이터 추가
            data = {
                'database_sid': database_sid,
                'last_updated': datetime.now().isoformat(),
                'column_count': len(existing),
                'columns': existing
            }

            # 저장
            file_path = self._get_common_columns_file(database_sid)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"공통 칼럼 정보 저장 실패: {e}\n{traceback.format_exc()}")
            return False

    def load_common_columns(self, database_sid: str) -> Dict[str, Dict]:
        """공통 칼럼 정보 로드"""
        file_path = self._get_common_columns_file(database_sid)
        if not file_path.exists():
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('columns', {})
        except Exception as e:
            print(f"공통 칼럼 정보 로드 실패: {e}\n{traceback.format_exc()}")
            return {}

    def get_column_info(self, database_sid: str, column_name: str) -> Optional[Dict]:
        """특정 칼럼 정보 조회"""
        columns = self.load_common_columns(database_sid)
        return columns.get(column_name)

    def delete_column(self, database_sid: str, column_name: str) -> bool:
        """칼럼 정보 삭제"""
        columns = self.load_common_columns(database_sid)
        if column_name in columns:
            del columns[column_name]

            data = {
                'database_sid': database_sid,
                'last_updated': datetime.now().isoformat(),
                'column_count': len(columns),
                'columns': columns
            }

            file_path = self._get_common_columns_file(database_sid)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        return False

    # ============================================
    # 코드 정보 관리
    # ============================================

    def save_code_definitions(self, database_sid: str, codes: List[Dict]) -> bool:
        """
        코드 정보 저장

        Args:
            codes: [
                {
                    'column_name': 'STATUS',
                    'code_value': '01',
                    'code_label': '접수',
                    'code_description': '접수된 상태',
                    'display_order': 1,
                    'is_active': True,
                    'parent_code': '',
                    'state_transition': '02'
                },
                ...
            ]
        """
        try:
            # 기존 데이터 로드
            existing = self.load_code_definitions(database_sid)

            # 칼럼명별로 그룹화
            for code in codes:
                column_name = code['column_name']
                code_value = code['code_value']

                if column_name not in existing:
                    existing[column_name] = {}

                existing[column_name][code_value] = code

            # 메타데이터 추가
            data = {
                'database_sid': database_sid,
                'last_updated': datetime.now().isoformat(),
                'code_column_count': len(existing),
                'definitions': existing
            }

            # 저장
            file_path = self._get_code_definitions_file(database_sid)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"코드 정보 저장 실패: {e}\n{traceback.format_exc()}")
            return False

    def load_code_definitions(self, database_sid: str) -> Dict[str, Dict[str, Dict]]:
        """코드 정보 로드"""
        file_path = self._get_code_definitions_file(database_sid)
        if not file_path.exists():
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('definitions', {})
        except Exception as e:
            print(f"코드 정보 로드 실패: {e}\n{traceback.format_exc()}")
            return {}

    def get_codes_for_column(self, database_sid: str, column_name: str) -> Dict[str, Dict]:
        """특정 칼럼의 코드 목록 조회"""
        definitions = self.load_code_definitions(database_sid)
        return definitions.get(column_name, {})

    def delete_code_column(self, database_sid: str, column_name: str) -> bool:
        """칼럼의 모든 코드 삭제"""
        definitions = self.load_code_definitions(database_sid)
        if column_name in definitions:
            del definitions[column_name]

            data = {
                'database_sid': database_sid,
                'last_updated': datetime.now().isoformat(),
                'code_column_count': len(definitions),
                'definitions': definitions
            }

            file_path = self._get_code_definitions_file(database_sid)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        return False

    # ============================================
    # 테이블 정보 관리
    # ============================================

    def save_table_info(self, database_sid: str, schema_name: str, tables_info: List[Dict]) -> bool:
        """
        테이블 정보 저장

        Args:
            database_sid: Database SID
            schema_name: 스키마 이름
            tables_info: [
                {
                    'table_name': 'CUSTOMERS',
                    'business_purpose': '고객 정보 관리',
                    'usage_scenarios': ['시나리오1', '시나리오2', '시나리오3'],
                    'related_tables': ['ORDERS', 'ADDRESSES']
                },
                ...
            ]
        """
        try:
            # 기존 데이터 로드
            existing = self.load_table_info(database_sid, schema_name)

            # 테이블명을 키로 하는 딕셔너리로 변환
            for table in tables_info:
                table_name = table['table_name']
                existing[table_name] = table

            # 메타데이터 추가
            data = {
                'database_sid': database_sid,
                'schema_name': schema_name,
                'last_updated': datetime.now().isoformat(),
                'table_count': len(existing),
                'tables': existing
            }

            # 저장
            file_path = self._get_table_info_file(database_sid, schema_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"테이블 정보 저장 실패: {e}\n{traceback.format_exc()}")
            return False

    def load_table_info(self, database_sid: str, schema_name: str) -> Dict[str, Dict]:
        """테이블 정보 로드"""
        file_path = self._get_table_info_file(database_sid, schema_name)
        if not file_path.exists():
            return {}

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('tables', {})
        except Exception as e:
            print(f"테이블 정보 로드 실패: {e}\n{traceback.format_exc()}")
            return {}

    def _get_table_info_file(self, database_sid: str, schema_name: str) -> Path:
        """DB/스키마별 테이블 정보 파일 경로"""
        schema_dir = self._get_db_dir(database_sid) / schema_name
        schema_dir.mkdir(exist_ok=True)
        return schema_dir / "table_info.json"

    # ============================================
    # CSV 생성
    # ============================================

    def generate_csv_files(
        self,
        database_sid: str,
        schema_name: str,
        tables_columns: Dict[str, List[Dict]],
        output_dir: Path = None
    ) -> Dict[str, str]:
        """
        DB 스키마 정보 + 공통 메타데이터 → CSV 파일 생성

        Args:
            database_sid: Database SID
            schema_name: 스키마 이름
            tables_columns: {
                'TABLE_NAME': [
                    {'name': 'COLUMN_NAME', 'data_type': 'VARCHAR2(50)', 'nullable': 'Y', ...},
                    ...
                ],
                ...
            }
            output_dir: CSV 저장 경로 (None이면 input/{DB_SID}/{SCHEMA}/)

        Returns:
            {
                'table_info': 'path/to/table_info.csv',
                'column_info': 'path/to/column_info.csv',
                'code_values': 'path/to/code_values.csv'
            }
        """
        if output_dir is None:
            output_dir = self.base_dir / "input" / database_sid / schema_name
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        # 공통 메타데이터 로드
        common_columns = self.load_common_columns()
        code_definitions = self.load_code_definitions()

        result = {}

        # 1. table_info.csv 생성
        table_info_path = output_dir / "table_info.csv"
        self._generate_table_info_csv(tables_columns.keys(), table_info_path)
        result['table_info'] = str(table_info_path)

        # 2. column_info.csv 생성
        column_info_path = output_dir / "column_info.csv"
        self._generate_column_info_csv(
            tables_columns, common_columns, column_info_path
        )
        result['column_info'] = str(column_info_path)

        # 3. code_values.csv 생성
        code_values_path = output_dir / "code_values.csv"
        self._generate_code_values_csv(
            tables_columns, code_definitions, code_values_path
        )
        result['code_values'] = str(code_values_path)

        return result

    def _generate_table_info_csv(self, table_names: List[str], output_path: Path):
        """table_info.csv 생성 (템플릿, 사용자가 채워야 함)"""
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # 헤더
            writer.writerow([
                'table_name',
                'business_purpose',
                'usage_scenario_1',
                'usage_scenario_2',
                'usage_scenario_3',
                'related_tables'
            ])

            # 각 테이블 (비워둠 - 사용자가 채워야 함)
            for table_name in sorted(table_names):
                writer.writerow([
                    table_name,
                    '',  # business_purpose (사용자 입력 필요)
                    '',  # usage_scenario_1
                    '',  # usage_scenario_2
                    '',  # usage_scenario_3
                    ''   # related_tables
                ])

    def _generate_column_info_csv(
        self,
        tables_columns: Dict[str, List[Dict]],
        common_columns: Dict[str, Dict],
        output_path: Path
    ):
        """column_info.csv 생성 (DB 정보 + 공통 칼럼 정보 매칭)"""
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # 헤더
            writer.writerow([
                'table_name',
                'column_name',
                'korean_name',
                'description',
                'business_rule',
                'sample_values',
                'unit',
                'is_code_column',
                'aggregation_functions',
                'is_sensitive'
            ])

            # 각 테이블의 칼럼
            for table_name in sorted(tables_columns.keys()):
                columns = tables_columns[table_name]

                for col in columns:
                    column_name = col['name']

                    # 공통 칼럼 정보 매칭
                    common_info = common_columns.get(column_name, {})

                    writer.writerow([
                        table_name,
                        column_name,
                        common_info.get('korean_name', ''),  # 공통 정보 사용
                        common_info.get('description', ''),  # 공통 정보 사용
                        common_info.get('business_rule', ''),
                        common_info.get('sample_values', ''),
                        common_info.get('unit', ''),
                        'Y' if common_info.get('is_code_column', False) else 'N',
                        common_info.get('aggregation_functions', ''),
                        'Y' if common_info.get('is_sensitive', False) else 'N'
                    ])

    def _generate_code_values_csv(
        self,
        tables_columns: Dict[str, List[Dict]],
        code_definitions: Dict[str, Dict[str, Dict]],
        output_path: Path
    ):
        """code_values.csv 생성 (코드 정보 매핑)"""
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # 헤더
            writer.writerow([
                'table_name',
                'column_name',
                'code_value',
                'code_label',
                'code_description',
                'display_order',
                'is_active',
                'parent_code',
                'state_transition'
            ])

            # 코드 칼럼 찾기
            written_columns = set()

            for table_name in sorted(tables_columns.keys()):
                columns = tables_columns[table_name]

                for col in columns:
                    column_name = col['name']

                    # 이미 작성된 칼럼은 스킵 (중복 방지)
                    if column_name in written_columns:
                        continue

                    # 코드 정의가 있는 칼럼만
                    if column_name in code_definitions:
                        codes = code_definitions[column_name]

                        for code_value, code_info in codes.items():
                            writer.writerow([
                                table_name,
                                column_name,
                                code_value,
                                code_info.get('code_label', ''),
                                code_info.get('code_description', ''),
                                code_info.get('display_order', ''),
                                'Y' if code_info.get('is_active', True) else 'N',
                                code_info.get('parent_code', ''),
                                code_info.get('state_transition', '')
                            ])

                        written_columns.add(column_name)

    # ============================================
    # 유틸리티
    # ============================================

    def get_statistics(self, database_sid: str) -> Dict:
        """저장된 메타데이터 통계"""
        common_columns = self.load_common_columns(database_sid)
        code_definitions = self.load_code_definitions(database_sid)

        # 코드 칼럼 수
        code_column_count = len(code_definitions)

        # 전체 코드 수
        total_codes = sum(len(codes) for codes in code_definitions.values())

        return {
            'database_sid': database_sid,
            'common_column_count': len(common_columns),
            'code_column_count': code_column_count,
            'total_code_count': total_codes
        }


if __name__ == "__main__":
    # 테스트
    manager = CommonMetadataManager()

    # 공통 칼럼 정보 저장
    columns = [
        {
            'column_name': 'STATUS',
            'korean_name': '상태',
            'description': '처리 상태 코드',
            'is_code_column': True,
            'sample_values': '01|02|03',
            'business_rule': '01→02→03 순서',
            'unit': '',
            'aggregation_functions': '',
            'is_sensitive': False
        }
    ]

    manager.save_common_columns(columns)
    print("✅ 공통 칼럼 정보 저장 완료")

    # 코드 정보 저장
    codes = [
        {
            'column_name': 'STATUS',
            'code_value': '01',
            'code_label': '접수',
            'code_description': '접수된 상태',
            'display_order': 1,
            'is_active': True,
            'parent_code': '',
            'state_transition': '02'
        }
    ]

    manager.save_code_definitions(codes)
    print("✅ 코드 정보 저장 완료")

    # 통계
    stats = manager.get_statistics()
    print(f"📊 통계: {stats}")

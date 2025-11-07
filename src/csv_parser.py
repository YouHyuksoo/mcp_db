"""
CSV 파일 파싱 모듈
사용자 제공 CSV 파일을 파싱하여 메타정보 생성
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List
import logging
import traceback

logger = logging.getLogger(__name__)


class CSVParser:
    """사용자 제공 CSV 파싱"""

    def __init__(self, input_base_dir: str = "./input"):
        """
        Args:
            input_base_dir: CSV 파일들이 저장된 기본 디렉토리
        """
        self.input_base_dir = Path(input_base_dir)
        logger.info(f"CSVParser 초기화: {self.input_base_dir}")

    def parse_table_info(self, database_sid: str, schema_name: str) -> Dict[str, Dict]:
        """
        table_info.csv 파싱

        Returns:
            {
                'TABLE_NAME': {
                    'business_purpose': str,
                    'usage_scenarios': [str],
                    'related_tables': [str]
                }
            }
        """
        csv_path = self.input_base_dir / database_sid / schema_name / "table_info.csv"

        if not csv_path.exists():
            logger.warning(f"table_info.csv가 없습니다: {csv_path}")
            return {}

        try:
            df = pd.read_csv(csv_path, encoding='utf-8')

            table_info = {}
            for _, row in df.iterrows():
                table_name = row['table_name'].upper()

                scenarios = []
                for i in [1, 2, 3]:
                    col = f'usage_scenario_{i}'
                    if col in row and pd.notna(row[col]):
                        scenarios.append(row[col])

                related = []
                if 'related_tables' in row and pd.notna(row['related_tables']):
                    related = [t.strip() for t in str(row['related_tables']).split('|')]

                table_info[table_name] = {
                    'business_purpose': row['business_purpose'],
                    'usage_scenarios': scenarios,
                    'related_tables': related
                }

            logger.info(f"✅ table_info.csv 파싱 완료: {len(table_info)}개 테이블")
            return table_info

        except Exception as e:
            logger.error(f"❌ table_info.csv 파싱 실패: {e}\n{traceback.format_exc()}")
            return {}

    def parse_column_info(self, database_sid: str, schema_name: str) -> Dict[str, Dict[str, Dict]]:
        """
        column_info.csv 파싱

        Returns:
            {
                'TABLE_NAME': {
                    'COLUMN_NAME': {
                        'korean_name': str,
                        'description': str,
                        'business_rule': str,
                        'sample_values': [str],
                        'unit': str,
                        'is_code_column': bool,
                        'aggregation_functions': [str],
                        'is_sensitive': bool
                    }
                }
            }
        """
        csv_path = self.input_base_dir / database_sid / schema_name / "column_info.csv"

        if not csv_path.exists():
            logger.warning(f"column_info.csv가 없습니다: {csv_path}")
            return {}

        try:
            df = pd.read_csv(csv_path, encoding='utf-8')

            column_info = {}
            for _, row in df.iterrows():
                table_name = row['table_name'].upper()
                column_name = row['column_name'].upper()

                if table_name not in column_info:
                    column_info[table_name] = {}

                # 샘플 값 파싱
                sample_values = []
                if 'sample_values' in row and pd.notna(row['sample_values']):
                    sample_values = [v.strip() for v in str(row['sample_values']).split('|')]

                # 집계 함수 파싱
                agg_functions = []
                if 'aggregation_functions' in row and pd.notna(row['aggregation_functions']):
                    agg_functions = [f.strip() for f in str(row['aggregation_functions']).split('|')]

                column_info[table_name][column_name] = {
                    'korean_name': row['korean_name'],
                    'description': row['description'],
                    'business_rule': row.get('business_rule', ''),
                    'sample_values': sample_values,
                    'unit': row.get('unit', ''),
                    'is_code_column': str(row['is_code_column']).upper() == 'Y',
                    'aggregation_functions': agg_functions,
                    'is_sensitive': str(row['is_sensitive']).upper() == 'Y'
                }

            logger.info(f"✅ column_info.csv 파싱 완료")
            return column_info

        except Exception as e:
            logger.error(f"❌ column_info.csv 파싱 실패: {e}\n{traceback.format_exc()}")
            return {}

    def parse_code_values(self, database_sid: str, schema_name: str) -> Dict[str, Dict[str, List[Dict]]]:
        """
        code_values.csv 파싱

        Returns:
            {
                'TABLE_NAME': {
                    'COLUMN_NAME': [
                        {
                            'value': str,
                            'label': str,
                            'description': str,
                            'display_order': int,
                            'is_active': bool,
                            'next_states': [str]
                        }
                    ]
                }
            }
        """
        csv_path = self.input_base_dir / database_sid / schema_name / "code_values.csv"

        if not csv_path.exists():
            logger.warning(f"code_values.csv가 없습니다: {csv_path}")
            return {}

        try:
            df = pd.read_csv(csv_path, encoding='utf-8')

            code_values = {}
            for _, row in df.iterrows():
                table_name = row['table_name'].upper()
                column_name = row['column_name'].upper()

                if table_name not in code_values:
                    code_values[table_name] = {}

                if column_name not in code_values[table_name]:
                    code_values[table_name][column_name] = []

                # 다음 상태 파싱
                next_states = []
                if 'next_states' in row and pd.notna(row['next_states']):
                    next_states = [s.strip() for s in str(row['next_states']).split('|')]

                code_values[table_name][column_name].append({
                    'value': str(row['code_value']),
                    'label': row['code_label'],
                    'description': row['code_description'],
                    'display_order': int(row.get('display_order', 999)),
                    'is_active': str(row.get('is_active', 'Y')).upper() == 'Y',
                    'next_states': next_states
                })

            logger.info(f"✅ code_values.csv 파싱 완료")
            return code_values

        except Exception as e:
            logger.error(f"❌ code_values.csv 파싱 실패: {e}\n{traceback.format_exc()}")
            return {}

    def parse_all(self, database_sid: str, schema_name: str) -> Dict:
        """
        모든 CSV 파일 파싱

        Returns:
            {
                'table_info': dict,
                'column_info': dict,
                'code_values': dict
            }
        """
        return {
            'table_info': self.parse_table_info(database_sid, schema_name),
            'column_info': self.parse_column_info(database_sid, schema_name),
            'code_values': self.parse_code_values(database_sid, schema_name)
        }

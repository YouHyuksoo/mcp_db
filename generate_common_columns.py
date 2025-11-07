"""
공통 컬럼 정보 CSV 생성 스크립트
ISYS_DUAL_LANGUAGE 테이블에서 영문-한글 매핑 데이터를 활용하여 컬럼 정보 생성
"""

import csv
import oracledb
import re
from pathlib import Path

def clean_and_convert_to_column_name(english_text: str) -> str:
    """
    영문 텍스트를 컬럼명으로 변환
    - 공백을 _로 변경
    - 특수문자 제거
    - 대문자로 변환
    - 연속된 _ 제거
    """
    # 앞뒤 공백 제거
    text = english_text.strip()

    # 특수문자를 공백으로 변경 (알파벳, 숫자, 공백만 남김)
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)

    # 여러 공백을 하나의 공백으로
    text = re.sub(r'\s+', ' ', text)

    # 공백을 _로 변경
    text = text.replace(' ', '_')

    # 대문자로 변환
    text = text.upper()

    # 연속된 _를 하나로
    text = re.sub(r'_+', '_', text)

    # 앞뒤 _ 제거
    text = text.strip('_')

    return text

def infer_column_properties(column_name: str, korean_name: str) -> dict:
    """
    컬럼명과 한글명으로부터 컬럼 속성 추론
    """
    column_upper = column_name.upper()
    korean_upper = korean_name.upper() if korean_name else ''

    # 코드 컬럼 판별
    is_code_column = False
    code_indicators = ['CODE', 'STATUS', 'TYPE', 'CLASS', 'FLAG', 'YN', 'GUBUN', '구분', '코드', '상태', '유형']
    for indicator in code_indicators:
        if indicator in column_upper or indicator in korean_upper:
            is_code_column = True
            break

    # 민감정보 판별
    is_sensitive = False
    sensitive_indicators = ['PASSWORD', 'PWD', 'SECRET', 'CARD', 'SSN', 'SOCIAL', '비밀번호', '주민번호', '카드']
    for indicator in sensitive_indicators:
        if indicator in column_upper or indicator in korean_upper:
            is_sensitive = True
            break

    # 집계 함수 추론
    aggregation_functions = ''
    if any(x in column_upper for x in ['QTY', 'QUANTITY', 'AMT', 'AMOUNT', 'CNT', 'COUNT', 'SUM', 'TOTAL', '수량', '금액', '개수']):
        aggregation_functions = 'SUM,AVG'
    elif any(x in column_upper for x in ['RATE', 'RATIO', 'PERCENT', '비율', '율']):
        aggregation_functions = 'AVG'
    elif any(x in column_upper for x in ['DATE', 'TIME', '일자', '시간']):
        aggregation_functions = 'MIN,MAX'

    # 단위 추론
    unit = ''
    if any(x in column_upper for x in ['QTY', 'QUANTITY', '수량']):
        unit = 'EA'
    elif any(x in column_upper for x in ['AMT', 'AMOUNT', 'PRICE', '금액', '가격']):
        unit = 'KRW'
    elif any(x in column_upper for x in ['RATE', 'RATIO', 'PERCENT', '비율', '율']):
        unit = '%'
    elif any(x in column_upper for x in ['WEIGHT', '중량']):
        unit = 'KG'
    elif any(x in column_upper for x in ['LENGTH', '길이']):
        unit = 'MM'

    # Description 생성 (한글명 기반으로 확장)
    description = korean_name
    if '코드' in korean_name or 'CODE' in column_upper:
        description += ' (코드 값)'
    elif '일자' in korean_name or 'DATE' in column_upper:
        description += ' (날짜)'
    elif '금액' in korean_name or 'AMOUNT' in column_upper or 'AMT' in column_upper:
        description += ' (금액)'
    elif '수량' in korean_name or 'QTY' in column_upper or 'QUANTITY' in column_upper:
        description += ' (수량)'

    return {
        'is_code_column': is_code_column,
        'is_sensitive': is_sensitive,
        'aggregation_functions': aggregation_functions,
        'unit': unit,
        'description': description
    }

def main():
    # DB 연결
    connection = oracledb.connect(
        user="INFINITY21_JSMES",
        password="INFINITY21_JSMES",
        host="113.160.149.212",
        port=1588,
        service_name="SMVNPDB"
    )

    cursor = connection.cursor()

    # ISYS_DUAL_LANGUAGE 데이터 조회
    cursor.execute("""
        SELECT DISTINCT ENGLISH_TEXT, KOREA_TEXT
        FROM ISYS_DUAL_LANGUAGE
        WHERE ENGLISH_TEXT IS NOT NULL
            AND KOREA_TEXT IS NOT NULL
            AND LENGTH(TRIM(ENGLISH_TEXT)) > 0
            AND LENGTH(TRIM(KOREA_TEXT)) > 0
        ORDER BY ENGLISH_TEXT
    """)

    rows = cursor.fetchall()

    # 컬럼명 중복 제거를 위한 딕셔너리
    columns_dict = {}

    for english_text, korea_text in rows:
        # 컬럼명 생성
        column_name = clean_and_convert_to_column_name(english_text)

        # 빈 컬럼명은 스킵
        if not column_name or len(column_name) < 2:
            continue

        # 숫자로만 이루어진 컬럼명은 스킵
        if column_name.isdigit():
            continue

        korean_name = korea_text.strip()

        # 이미 존재하는 컬럼이면 더 나은 한글명 선택 (더 긴 것)
        if column_name in columns_dict:
            existing_korean = columns_dict[column_name]['korean_name']
            if len(korean_name) > len(existing_korean):
                columns_dict[column_name]['korean_name'] = korean_name
        else:
            # 컬럼 속성 추론
            properties = infer_column_properties(column_name, korean_name)

            columns_dict[column_name] = {
                'column_name': column_name,
                'korean_name': korean_name,
                'description': properties['description'],
                'business_rule': '',  # 사용자가 입력
                'sample_values': '',  # 사용자가 입력
                'unit': properties['unit'],
                'is_code_column': 'Y' if properties['is_code_column'] else 'N',
                'aggregation_functions': properties['aggregation_functions'],
                'is_sensitive': 'Y' if properties['is_sensitive'] else 'N'
            }

    # CSV 파일 생성
    output_path = Path('d:/Project/mcp_db/common_metadata/common_columns_template.csv')

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        # 헤더
        writer.writerow([
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

        # 데이터 작성 (알파벳 순 정렬)
        for column_name in sorted(columns_dict.keys()):
            col_info = columns_dict[column_name]
            writer.writerow([
                col_info['column_name'],
                col_info['korean_name'],
                col_info['description'],
                col_info['business_rule'],
                col_info['sample_values'],
                col_info['unit'],
                col_info['is_code_column'],
                col_info['aggregation_functions'],
                col_info['is_sensitive']
            ])

    cursor.close()
    connection.close()

    print(f"✅ CSV 파일 생성 완료: {output_path}")
    print(f"📊 총 {len(columns_dict)}개 공통 컬럼 정보 작성됨")
    print(f"\n생성된 컬럼 예시 (처음 10개):")
    for i, column_name in enumerate(sorted(columns_dict.keys())[:10], 1):
        col_info = columns_dict[column_name]
        print(f"  {i}. {col_info['column_name']} → {col_info['korean_name']}")

    print(f"\n다음 단계:")
    print(f"1. {output_path} 파일을 열어서 내용 확인")
    print(f"2. 필요한 경우 business_rule, sample_values 등 추가 정보 입력")
    print(f"3. import_common_columns_csv 도구로 JSON 변환 및 저장")

if __name__ == "__main__":
    main()

"""
@file merge_column_definitions.py
@description
이 스크립트는 common_columns_template.csv와 code_definitions_template.csv를 통합하여
column_definitions.csv 파일을 생성합니다.

주요 기능:
1. common_columns_template.csv에서 column_name, korean_name, description 가져오기
2. code_definitions_template.csv에서 코드 정의 {code_value: code_label} 딕셔너리 생성
3. 두 데이터를 통합하여 column_definitions.csv 생성

출력 컬럼:
- column_name: 컬럼명
- korean_name: 한글명
- description: 설명
- code_values: JSON 형식의 코드 정의 (예: {"A": "Active", "I": "Inactive"})

@example
python merge_column_definitions.py
"""

import csv
import json
import os

# 파일 경로 설정
BASE_DIR = r'd:\Project\mcp_db\data\SMVNPDBext\INFINITY21_JSMES\csv_uploads'
COMMON_URI = os.path.join(BASE_DIR, 'common_columns_template.csv')
CODE_URI = os.path.join(BASE_DIR, 'code_definitions_template.csv')
OUTPUT_URI = os.path.join(BASE_DIR, 'column_definitions.csv')


def read_csv(path):
    """
    다양한 인코딩을 시도하여 CSV 파일을 읽습니다.

    @param path: CSV 파일 경로
    @return: CSV 데이터 리스트 (딕셔너리 형태)
    """
    encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr']
    for enc in encodings:
        try:
            with open(path, 'r', encoding=enc) as f:
                return list(csv.DictReader(f))
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Error reading {path} with {enc}: {e}")
    print(f"Failed to read {path}")
    return []


def main():
    """
    메인 함수: CSV 파일들을 읽고 통합하여 column_definitions.csv를 생성합니다.
    """
    print("=" * 60)
    print("CSV 파일 통합 시작...")
    print("=" * 60)

    # 파일 존재 확인
    if not os.path.exists(COMMON_URI):
        print(f"Error: {COMMON_URI} not found")
        return
    if not os.path.exists(CODE_URI):
        print(f"Error: {CODE_URI} not found")
        return

    # CSV 파일 읽기
    common_rows = read_csv(COMMON_URI)
    code_rows = read_csv(CODE_URI)

    print(f"✓ common_columns_template.csv: {len(common_rows)} 행 로드")
    print(f"✓ code_definitions_template.csv: {len(code_rows)} 행 로드")

    # 1. 코드 정의 처리: Map<ColumnName, Map<Code, Label>>
    code_map = {}
    for row in code_rows:
        cname = row.get('column_name', '').strip()
        if not cname:
            continue

        if cname not in code_map:
            code_map[cname] = {}

        val = row.get('code_value', '').strip()
        label = row.get('code_label', '').strip()
        if val:
            code_map[cname][val] = label

    print(f"✓ 코드 정의가 있는 컬럼 수: {len(code_map)}")

    # 2. 데이터 통합
    final_data = {}

    # Common Columns 내용 반영
    for row in common_rows:
        cname = row.get('column_name', '').strip()
        if not cname:
            continue

        # code_values는 해당 컬럼의 코드 정의가 있으면 JSON 문자열로 변환
        code_values_str = ''
        if cname in code_map and code_map[cname]:
            code_values_str = json.dumps(code_map[cname], ensure_ascii=False)

        final_data[cname] = {
            'column_name': cname,
            'korean_name': row.get('korean_name', '').strip(),
            'description': row.get('description', '').strip(),
            'code_values': code_values_str
        }

    # Code 정의만 있고 Common에는 없는 컬럼 추가
    added_from_code = 0
    for cname, codes in code_map.items():
        if cname not in final_data:
            final_data[cname] = {
                'column_name': cname,
                'korean_name': '',
                'description': '',
                'code_values': json.dumps(codes, ensure_ascii=False) if codes else ''
            }
            added_from_code += 1

    print(f"✓ Common에 없지만 Code에만 있는 컬럼 추가: {added_from_code}")
    print(f"✓ 최종 통합 컬럼 수: {len(final_data)}")

    # 3. CSV 파일 저장
    fieldnames = ['column_name', 'korean_name', 'description', 'code_values']

    with open(OUTPUT_URI, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        # column_name 기준으로 정렬하여 저장
        for cname in sorted(final_data.keys()):
            writer.writerow(final_data[cname])

    print("=" * 60)
    print(f"✓ 파일 저장 완료: {OUTPUT_URI}")
    print("=" * 60)

    # 샘플 데이터 출력 (코드 정의가 있는 항목 5개)
    print("\n[샘플 데이터 - 코드 정의가 있는 컬럼]")
    count = 0
    for cname in sorted(final_data.keys()):
        if final_data[cname]['code_values']:
            print(f"  - {cname}: {final_data[cname]['code_values'][:80]}...")
            count += 1
            if count >= 5:
                break


if __name__ == '__main__':
    main()

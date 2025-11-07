"""
코드 정의 정보 CSV 생성 스크립트
ISYS_BASECODE 테이블에서 코드 정의 데이터를 추출하여 CSV 생성
"""

import csv
import oracledb
import re
from pathlib import Path

def clean_and_convert_to_column_name(code_type: str) -> str:
    """
    CODE_TYPE을 컬럼명으로 변환
    - 공백을 _로 변경
    - 특수문자 제거
    - 대문자로 변환
    """
    # 앞뒤 공백 제거
    text = code_type.strip()

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

def infer_code_description(code_mean_kor: str, code_name_desc: str) -> str:
    """
    코드 설명 생성
    CODE_NAME_DESCRIPTION_KOR이 있으면 우선 사용, 없으면 CODE_MEAN_KOR 사용
    """
    if code_name_desc and code_name_desc.strip():
        return code_name_desc.strip()
    elif code_mean_kor and code_mean_kor.strip():
        return code_mean_kor.strip()
    else:
        return ''

def infer_display_order(code_name: str) -> int:
    """
    CODE_NAME으로부터 표시 순서 추론
    숫자면 숫자로 변환, 아니면 1000 + 알파벳 순서
    """
    try:
        # 숫자로 변환 가능하면 그대로 사용
        return int(code_name)
    except:
        # 알파벳이면 ASCII 코드 기반
        if code_name and len(code_name) > 0:
            return 1000 + ord(code_name[0].upper())
        return 9999

def infer_state_transition(column_name: str, code_name: str, code_mean: str) -> str:
    """
    상태 전이 추론 (STATUS, STATE 관련 컬럼)
    """
    if 'STATUS' not in column_name and 'STATE' not in column_name:
        return ''

    # 일반적인 상태 전이 패턴
    transitions = {
        'W': 'P',  # 대기 -> 처리중
        'P': 'C',  # 처리중 -> 완료
        'N': 'Y',  # No -> Yes
        'R': 'A',  # 요청 -> 승인
        'A': 'C',  # 승인 -> 완료
    }

    return transitions.get(code_name, '')

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

    # ISYS_BASECODE 데이터 조회
    cursor.execute("""
        SELECT
            CODE_TYPE,
            CODE_NAME,
            CODE_MEAN_KOR,
            CODE_TYPE_DESC_KOR,
            CODE_NAME_DESCRIPTION_KOR
        FROM ISYS_BASECODE
        WHERE CODE_TYPE IS NOT NULL
            AND CODE_NAME IS NOT NULL
        ORDER BY CODE_TYPE, CODE_NAME
    """)

    rows = cursor.fetchall()

    # CSV 파일 생성
    output_path = Path('d:/Project/mcp_db/common_metadata/code_definitions_template.csv')

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)

        # 헤더
        writer.writerow([
            'column_name',
            'code_value',
            'code_label',
            'code_description',
            'display_order',
            'is_active',
            'parent_code',
            'state_transition'
        ])

        # 각 코드 정의 작성
        for code_type, code_name, code_mean_kor, code_type_desc, code_name_desc in rows:
            # 컬럼명 생성 (CODE_TYPE을 컬럼명으로 변환)
            column_name = clean_and_convert_to_column_name(code_type)

            # CODE_NAME을 code_value로 사용
            code_value = code_name.strip() if code_name else ''

            # CODE_MEAN_KOR을 code_label로 사용
            code_label = code_mean_kor.strip() if code_mean_kor else ''

            # code_description 생성
            code_description = infer_code_description(code_mean_kor, code_name_desc)

            # display_order 추론
            display_order = infer_display_order(code_name)

            # is_active는 기본적으로 Y
            is_active = 'Y'

            # parent_code는 비워둠 (사용자가 필요시 입력)
            parent_code = ''

            # state_transition 추론
            state_transition = infer_state_transition(column_name, code_name, code_mean_kor)

            writer.writerow([
                column_name,
                code_value,
                code_label,
                code_description,
                display_order,
                is_active,
                parent_code,
                state_transition
            ])

    cursor.close()
    connection.close()

    print(f"✅ CSV 파일 생성 완료: {output_path}")
    print(f"📊 총 {len(rows)}개 코드 정의 작성됨")

    # 컬럼별 코드 수 통계
    from collections import Counter
    column_counts = Counter([clean_and_convert_to_column_name(row[0]) for row in rows])

    print(f"\n주요 코드 컬럼 (Top 20):")
    for i, (column_name, count) in enumerate(column_counts.most_common(20), 1):
        print(f"  {i}. {column_name}: {count}개 코드")

    print(f"\n다음 단계:")
    print(f"1. {output_path} 파일을 열어서 내용 확인")
    print(f"2. 필요한 경우 parent_code, state_transition 등 추가 정보 입력")
    print(f"3. import_code_definitions_csv 도구로 JSON 변환 및 저장")

if __name__ == "__main__":
    main()

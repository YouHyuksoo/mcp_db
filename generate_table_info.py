"""
테이블 정보 CSV 생성 스크립트
테이블 이름 패턴을 기반으로 비즈니스 목적 추론
"""

import csv
import oracledb
from pathlib import Path

# 테이블 prefix별 비즈니스 도메인 정의
PREFIX_BUSINESS_MAP = {
    'IQ': {
        'domain': 'Quality Management (품질 관리)',
        'purpose_pattern': '품질 검사 및 관리',
        'scenarios': ['품질 데이터 수집', '불량 분석', '검사 결과 조회']
    },
    'IP': {
        'domain': 'Production Management (생산 관리)',
        'purpose_pattern': '생산 공정 관리',
        'scenarios': ['생산 계획 수립', '생산 실적 집계', 'Work Order 관리']
    },
    'IM': {
        'domain': 'Inventory/Material Management (재고/자재 관리)',
        'purpose_pattern': '재고 및 자재 관리',
        'scenarios': ['입출고 관리', '재고 조회', '자재 소요량 계산']
    },
    'IMCN': {
        'domain': 'Machine/Maintenance Management (설비/보전 관리)',
        'purpose_pattern': '설비 및 유지보수 관리',
        'scenarios': ['설비 가동 현황', '예방 보전', '설비 이력 관리']
    },
    'ID': {
        'domain': 'Item/BOM Management (품목/BOM 관리)',
        'purpose_pattern': '품목 및 BOM 정보 관리',
        'scenarios': ['품목 정보 조회', 'BOM 구조 분석', '품목 원가 관리']
    },
    'IB': {
        'domain': 'SMT/Mounting Management (SMT 실장 관리)',
        'purpose_pattern': 'SMT 실장 공정 관리',
        'scenarios': ['실장 계획', 'Feeder 관리', '실장 데이터 모니터링']
    },
    'ICOM': {
        'domain': 'Common/Integration (공통/통합)',
        'purpose_pattern': '공통 데이터 관리',
        'scenarios': ['공통 코드 관리', '문서 관리', '고객/공급사 정보']
    },
    'ISYS': {
        'domain': 'System Management (시스템 관리)',
        'purpose_pattern': '시스템 설정 및 관리',
        'scenarios': ['사용자 관리', '권한 관리', '시스템 설정']
    },
    'ISAL': {
        'domain': 'Sales/Shipping Management (판매/출하 관리)',
        'purpose_pattern': '판매 및 출하 관리',
        'scenarios': ['출하 계획', '재고 관리', '배송 추적']
    },
    'INTF': {
        'domain': 'Interface (인터페이스)',
        'purpose_pattern': 'ERP 등 외부 시스템 연동',
        'scenarios': ['데이터 수신', '데이터 변환', '연동 이력 관리']
    }
}

# 특정 테이블명 패턴 매칭
SPECIFIC_PATTERNS = {
    'INVENTORY': '재고 정보',
    'MASTER': '마스터 정보',
    'HISTORY': '이력 정보',
    'RECEIPT': '입고 정보',
    'ISSUE': '출고 정보',
    'PLAN': '계획 정보',
    'RESULT': '실적 정보',
    'INSPECT': '검사 정보',
    'BARCODE': '바코드 정보',
    'ORDER': '오더 정보',
    'BOM': 'BOM 정보',
    'MACHINE': '설비 정보',
    'MOLD': '금형 정보',
    'JIG': '지그/공구 정보',
    'SENSOR': '센서 데이터',
    'TEMP': '임시 데이터',
    'BACKUP': '백업 데이터',
    'LOG': '로그 정보',
    'ERROR': '에러 정보'
}

def infer_business_purpose(table_name: str) -> dict:
    """테이블 이름으로부터 비즈니스 목적 추론"""

    # Prefix 추출
    parts = table_name.split('_')
    prefix = parts[0] if parts else ''

    # Prefix 기반 도메인 매칭
    domain_info = PREFIX_BUSINESS_MAP.get(prefix, {
        'domain': 'General',
        'purpose_pattern': '',
        'scenarios': ['데이터 조회', '데이터 등록/수정', '이력 관리']
    })

    # 테이블명에서 키워드 추출
    purpose_keywords = []
    for keyword, description in SPECIFIC_PATTERNS.items():
        if keyword in table_name.upper():
            purpose_keywords.append(description)

    # Business Purpose 생성
    if purpose_keywords:
        business_purpose = f"{domain_info['domain']} - {', '.join(purpose_keywords[:2])}"
    else:
        business_purpose = f"{domain_info['domain']}"

    return {
        'business_purpose': business_purpose,
        'scenarios': domain_info['scenarios'][:3],  # 최대 3개
        'domain': domain_info['domain']
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

    # 테이블 목록 조회
    cursor.execute("""
        SELECT table_name, comments
        FROM all_tab_comments
        WHERE owner = 'INFINITY21_JSMES'
            AND table_type = 'TABLE'
            AND table_name NOT LIKE 'BIN$%'
        ORDER BY table_name
    """)

    tables = cursor.fetchall()

    # CSV 파일 생성
    output_path = Path('d:/Project/mcp_db/common_metadata/table_info_template.csv')

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

        # 각 테이블 정보 추론 및 작성
        for table_name, comments in tables:
            info = infer_business_purpose(table_name)

            # Oracle 주석이 있으면 우선 사용
            business_purpose = comments if comments else info['business_purpose']

            scenarios = info['scenarios'] + ['', '', '']  # 3개 확보

            writer.writerow([
                table_name,
                business_purpose,
                scenarios[0],
                scenarios[1],
                scenarios[2],
                ''  # related_tables는 비워둠 (사용자가 필요시 입력)
            ])

    cursor.close()
    connection.close()

    print(f"✅ CSV 파일 생성 완료: {output_path}")
    print(f"📊 총 {len(tables)}개 테이블 정보 작성됨")
    print(f"\n다음 단계:")
    print(f"1. {output_path} 파일을 열어서 내용 확인")
    print(f"2. 필요한 경우 비즈니스 목적 및 시나리오 수정")
    print(f"3. import_table_info_csv 도구로 JSON 변환 및 저장")

if __name__ == "__main__":
    main()

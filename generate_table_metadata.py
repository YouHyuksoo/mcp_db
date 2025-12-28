"""
@file generate_table_metadata.py
@description
이 스크립트는 table_info_template.csv의 전체 테이블 정보를 기반으로
table_metadata_optimized.csv 형식의 메타데이터 파일을 생성합니다.

테이블명을 분석하여 의미 있는 한글/영문 설명을 자동 생성합니다.

출력 컬럼:
- table_name: 테이블명
- table_description_ko: 한글 설명
- table_description_en: 영문 설명
- domain: 도메인 분류
- keywords: 검색 키워드
- sample_queries: 샘플 자연어 쿼리

@example
python generate_table_metadata.py
"""

import csv
import os
import re

# 파일 경로 설정
BASE_DIR = r'd:\Project\mcp_db\data\SMVNPDBext\INFINITY21_JSMES\csv_uploads'
INPUT_URI = os.path.join(BASE_DIR, 'table_info_template.csv')
OUTPUT_URI = os.path.join(BASE_DIR, 'table_metadata.csv')

# 테이블 접두사별 도메인 매핑
PREFIX_DOMAIN_MAP = {
    'IB_': 'SMT/실장',
    'ICOM_': '공통',
    'ID_': 'BOM/설계',
    'IM_ITEM': '재고',
    'IMCN_': '설비/보전',
    'IP_': '생산',
    'IQ_': '품질',
    'ISYS_': '시스템',
    'IWH_': '물류/창고',
}

# 테이블명 키워드 → 한글/영문 변환 사전
KEYWORD_DICT = {
    # 공통
    'MASTER': ('마스터', 'Master'),
    'MST': ('마스터', 'Master'),
    'HISTORY': ('이력', 'History'),
    'HIST': ('이력', 'History'),
    'LOG': ('로그', 'Log'),
    'BACKUP': ('백업', 'Backup'),
    'TEMP': ('임시', 'Temporary'),
    'WORK': ('작업', 'Work'),
    'CONFIG': ('설정', 'Configuration'),
    'SETTING': ('설정', 'Setting'),
    'CODE': ('코드', 'Code'),
    'INFO': ('정보', 'Information'),
    'INFOR': ('정보', 'Information'),
    'DATA': ('데이터', 'Data'),
    'RESULT': ('실적/결과', 'Result'),
    'DETAIL': ('상세', 'Detail'),
    'SUMMARY': ('요약', 'Summary'),
    'STATUS': ('상태', 'Status'),
    'STATE': ('상태', 'State'),

    # SMT/실장 관련
    'SMT': ('SMT', 'SMT'),
    'MNT': ('실장', 'Mounting'),
    'MOUNT': ('실장', 'Mounting'),
    'FEEDER': ('피더', 'Feeder'),
    'REEL': ('릴', 'Reel'),
    'TRAY': ('트레이', 'Tray'),
    'NOZZLE': ('노즐', 'Nozzle'),
    'CHIP': ('칩', 'Chip'),
    'PARTS': ('부품', 'Parts'),
    'PART': ('부품', 'Part'),
    'PARTSLIB': ('부품 라이브러리', 'Parts Library'),
    'PARTLIB': ('부품 라이브러리', 'Part Library'),
    'POSITION': ('위치', 'Position'),
    'BLOCK': ('블록', 'Block'),
    'STOCK': ('재고', 'Stock'),
    'STEP': ('스텝', 'Step'),
    'TAPE': ('테이프', 'Tape'),
    'LINE': ('라인', 'Line'),
    'MACHINE': ('설비', 'Machine'),
    'LOCATION': ('위치', 'Location'),
    'MATERIAL': ('자재', 'Material'),
    'PLAN': ('계획', 'Plan'),
    'PLANDATA': ('계획 데이터', 'Plan Data'),
    'PRODUCT': ('제품', 'Product'),
    'MONITORING': ('모니터링', 'Monitoring'),
    'RECYCLE': ('재활용', 'Recycle'),
    'CHECK': ('검사/확인', 'Check'),
    'FULLCHECK': ('전수검사', 'Full Check'),
    'SHAFT': ('샤프트', 'Shaft'),
    'IMAGE': ('이미지', 'Image'),
    'CSV': ('CSV 데이터', 'CSV Data'),
    'YAMAHA': ('야마하', 'Yamaha'),
    'NMP': ('NMP', 'NMP'),
    'NPM': ('NPM', 'NPM'),
    'AI': ('AI', 'AI'),
    'BM': ('BM', 'BM'),

    # BOM/설계 관련
    'BOM': ('BOM', 'BOM'),
    'ENG': ('설계', 'Engineering'),
    'ITEM': ('품목', 'Item'),
    'DRAWING': ('도면', 'Drawing'),
    'SPEC': ('스펙', 'Specification'),
    'VERSION': ('버전', 'Version'),

    # 재고 관련
    'INVENTORY': ('재고', 'Inventory'),
    'RECEIPT': ('입고', 'Receipt'),
    'ISSUE': ('출고', 'Issue'),
    'TRANSFER': ('이동', 'Transfer'),
    'ADJUST': ('조정', 'Adjustment'),
    'PURCHASE': ('구매', 'Purchase'),
    'ORDER': ('발주', 'Order'),
    'LOT': ('LOT', 'Lot'),
    'BATCH': ('배치', 'Batch'),

    # 설비/보전 관련
    'JIG': ('지그', 'JIG'),
    'MOLD': ('금형', 'Mold'),
    'TOOL': ('공구', 'Tool'),
    'PM': ('예방보전', 'Preventive Maintenance'),
    'MAINT': ('보전', 'Maintenance'),
    'REPAIR': ('수리', 'Repair'),
    'INSPECT': ('검사', 'Inspection'),
    'CALIBRATION': ('교정', 'Calibration'),
    'ASSET': ('자산', 'Asset'),
    'SPARE': ('예비품', 'Spare Part'),

    # 생산 관련
    'RUN': ('런', 'Run'),
    'CARD': ('카드', 'Card'),
    'RUNCARD': ('작업지시서', 'Run Card'),
    'WORKSTAGE': ('공정', 'Work Stage'),
    'STAGE': ('스테이지', 'Stage'),
    'PROCESS': ('공정', 'Process'),
    'MODEL': ('모델', 'Model'),
    'DAILY': ('일일', 'Daily'),
    'MONTHLY': ('월간', 'Monthly'),
    'SCHEDULE': ('스케줄', 'Schedule'),
    'DELIVERY': ('출하', 'Delivery'),
    'SHIPMENT': ('출하', 'Shipment'),
    'WO': ('작업지시', 'Work Order'),
    'TARGET': ('목표', 'Target'),
    'ACTUAL': ('실적', 'Actual'),

    # 품질 관련
    'QC': ('품질관리', 'Quality Control'),
    'IQC': ('수입검사', 'Incoming QC'),
    'OQC': ('출하검사', 'Outgoing QC'),
    'FQC': ('최종검사', 'Final QC'),
    'AOI': ('AOI', 'AOI'),
    'SPI': ('SPI', 'SPI'),
    'DEFECT': ('불량', 'Defect'),
    'NG': ('불량', 'NG'),
    'QUALITY': ('품질', 'Quality'),
    'MSL': ('MSL', 'MSL'),
    'HUMIDITY': ('습도', 'Humidity'),
    'TEMP': ('온도', 'Temperature'),
    'BAKING': ('베이킹', 'Baking'),

    # 공통 마스터 관련
    'CUSTOMER': ('고객', 'Customer'),
    'SUPPLIER': ('공급업체', 'Supplier'),
    'VENDOR': ('벤더', 'Vendor'),
    'EMPLOYEE': ('직원', 'Employee'),
    'USER': ('사용자', 'User'),
    'USERS': ('사용자', 'Users'),
    'BASECODE': ('기준코드', 'Base Code'),
    'COMMON': ('공통', 'Common'),
    'SYSTEM': ('시스템', 'System'),
    'SYS': ('시스템', 'System'),
    'MENU': ('메뉴', 'Menu'),
    'AUTH': ('권한', 'Authority'),
    'ROLE': ('역할', 'Role'),
    'PERMISSION': ('권한', 'Permission'),

    # 물류/창고 관련
    'WAREHOUSE': ('창고', 'Warehouse'),
    'WH': ('창고', 'Warehouse'),
    'RACK': ('랙', 'Rack'),
    'BIN': ('빈', 'Bin'),
    'ZONE': ('구역', 'Zone'),
    'ARRIVAL': ('도착', 'Arrival'),
    'DISPATCH': ('출고', 'Dispatch'),

    # 기타
    'COMPARE': ('비교', 'Compare'),
    'COPY': ('복사', 'Copy'),
    'STANDARD': ('표준', 'Standard'),
    'LABEL': ('라벨', 'Label'),
    'BARCODE': ('바코드', 'Barcode'),
    'PRINT': ('인쇄', 'Print'),
    'REPORT': ('리포트', 'Report'),
    'ANALYSIS': ('분석', 'Analysis'),
    'ALARM': ('알람', 'Alarm'),
    'ALERT': ('경고', 'Alert'),
    'NOTIFICATION': ('알림', 'Notification'),
    'MESSAGE': ('메시지', 'Message'),
    'MSG': ('메시지', 'Message'),
    'ERROR': ('에러', 'Error'),
    'EXCEPTION': ('예외', 'Exception'),
}

# 도메인별 기본 키워드
DOMAIN_KEYWORDS = {
    'SMT/실장': ['SMT', '실장', '마운터', 'Mounting'],
    'BOM/설계': ['BOM', '설계', '부품구성', '자재명세'],
    '품목': ['품목', '아이템', '자재', 'Item'],
    '설비/보전': ['설비', '장비', '보전', 'Machine'],
    '재고': ['재고', '입고', '출고', '인벤토리'],
    '구매': ['구매', '발주', 'PO', 'Purchase'],
    '생산': ['생산', '라인', '공정', 'Production'],
    '생산계획': ['계획', '스케줄', 'Plan'],
    '생산실적': ['실적', '생산량', 'Result'],
    '품질': ['품질', '검사', 'QC', '불량'],
    '공통': ['마스터', '공통', '기준정보'],
    '시스템': ['시스템', '사용자', '설정'],
    '물류/창고': ['창고', '물류', '출하', '배송'],
    '이력': ['이력', '로그', 'History'],
    '기타': [],
}


def read_csv(path):
    """다양한 인코딩을 시도하여 CSV 파일을 읽습니다."""
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


def get_domain_from_prefix(table_name):
    """테이블 접두사에서 도메인을 추출합니다."""
    for prefix, domain in PREFIX_DOMAIN_MAP.items():
        if table_name.startswith(prefix):
            return domain
    return '기타'


def parse_table_name(table_name):
    """
    테이블명을 파싱하여 의미 있는 키워드들을 추출합니다.

    @param table_name: 테이블명
    @return: (prefix, keywords_ko, keywords_en)
    """
    # 접두사 분리
    parts = table_name.split('_')
    prefix = parts[0] if parts else ''

    keywords_ko = []
    keywords_en = []

    # 나머지 부분에서 키워드 추출
    for part in parts[1:]:
        part_upper = part.upper()

        if part_upper in KEYWORD_DICT:
            ko, en = KEYWORD_DICT[part_upper]
            keywords_ko.append(ko)
            keywords_en.append(en)
        elif len(part) >= 2:
            # 사전에 없는 키워드는 그대로 사용
            keywords_ko.append(part)
            keywords_en.append(part)

    return prefix, keywords_ko, keywords_en


def generate_description_ko(table_name, keywords_ko, domain):
    """
    테이블의 한글 설명을 생성합니다.

    @param table_name: 테이블명
    @param keywords_ko: 한글 키워드 리스트
    @param domain: 도메인
    @return: 한글 설명 문자열
    """
    if not keywords_ko:
        return f"{table_name} 테이블."

    # 키워드 조합으로 설명 생성
    main_keywords = keywords_ko[:3]  # 주요 키워드 3개

    # 마스터/데이터/이력 등 유형 키워드 찾기
    type_keyword = ''
    for kw in ['마스터', '이력', '로그', '데이터', '실적/결과', '백업', '임시']:
        if kw in keywords_ko:
            type_keyword = kw.replace('실적/결과', '실적')
            main_keywords = [k for k in main_keywords if k != kw]
            break

    if type_keyword == '마스터':
        desc = f"{' '.join(main_keywords)} {type_keyword} 테이블. "
        desc += f"{' '.join(main_keywords)} 정보를 관리한다."
    elif type_keyword == '이력' or type_keyword == '로그':
        desc = f"{' '.join(main_keywords)} {type_keyword} 테이블. "
        desc += f"{' '.join(main_keywords)} 변경/처리 이력을 기록한다."
    elif type_keyword == '실적':
        desc = f"{' '.join(main_keywords)} {type_keyword} 테이블. "
        desc += f"{' '.join(main_keywords)} 실적 데이터를 기록한다."
    elif type_keyword == '데이터':
        desc = f"{' '.join(main_keywords)} {type_keyword} 테이블. "
        desc += f"{' '.join(main_keywords)} 관련 데이터를 저장한다."
    elif type_keyword == '백업':
        desc = f"{' '.join(main_keywords)} {type_keyword} 테이블. "
        desc += f"변경 전 {' '.join(main_keywords)} 데이터를 보관한다."
    else:
        desc = f"{' '.join(keywords_ko[:4])} 테이블. "
        if '검사' in keywords_ko or '검사/확인' in keywords_ko:
            desc += f"{keywords_ko[0]} 검사 결과를 기록한다."
        elif '계획' in keywords_ko:
            desc += f"{keywords_ko[0]} 계획 정보를 관리한다."
        else:
            desc += f"{keywords_ko[0]} 관련 정보를 관리한다."

    return desc


def generate_description_en(table_name, keywords_en, domain):
    """
    테이블의 영문 설명을 생성합니다.

    @param table_name: 테이블명
    @param keywords_en: 영문 키워드 리스트
    @param domain: 도메인
    @return: 영문 설명 문자열
    """
    if not keywords_en:
        return f"{table_name} table."

    main_keywords = keywords_en[:3]

    # 유형 키워드 찾기
    type_keyword = ''
    for kw in ['Master', 'History', 'Log', 'Data', 'Result', 'Backup', 'Temporary']:
        if kw in keywords_en:
            type_keyword = kw
            main_keywords = [k for k in main_keywords if k != kw]
            break

    subject = ' '.join(main_keywords).lower()

    if type_keyword == 'Master':
        return f"{' '.join(main_keywords)} master table. Manages {subject} information."
    elif type_keyword in ['History', 'Log']:
        return f"{' '.join(main_keywords)} {type_keyword.lower()} table. Records {subject} change history."
    elif type_keyword == 'Result':
        return f"{' '.join(main_keywords)} result table. Stores {subject} result data."
    elif type_keyword == 'Data':
        return f"{' '.join(main_keywords)} data table. Stores {subject} data."
    elif type_keyword == 'Backup':
        return f"{' '.join(main_keywords)} backup table. Stores backup of {subject} data."
    else:
        return f"{' '.join(keywords_en[:3])} table. Manages {subject} information."


def generate_keywords(table_name, keywords_ko, domain):
    """
    검색용 키워드를 생성합니다.

    @param table_name: 테이블명
    @param keywords_ko: 한글 키워드 리스트
    @param domain: 도메인
    @return: 공백으로 구분된 키워드 문자열
    """
    all_keywords = set()

    # 한글 키워드 추가
    for kw in keywords_ko:
        if kw and len(kw) >= 2:
            all_keywords.add(kw.replace('실적/결과', '실적').replace('검사/확인', '검사'))

    # 도메인 기본 키워드 추가
    if domain in DOMAIN_KEYWORDS:
        for kw in DOMAIN_KEYWORDS[domain][:2]:
            all_keywords.add(kw)

    # 테이블명에서 영문 키워드 추가 (3자 이상)
    parts = table_name.split('_')
    for part in parts[1:]:
        if len(part) >= 3 and part.upper() not in ['THE', 'AND', 'FOR']:
            all_keywords.add(part)

    return ' '.join(sorted(all_keywords))


def generate_sample_queries(table_name, keywords_ko, domain):
    """
    샘플 자연어 쿼리를 생성합니다.

    @param table_name: 테이블명
    @param keywords_ko: 한글 키워드 리스트
    @param domain: 도메인
    @return: | 구분자로 연결된 샘플 쿼리 문자열
    """
    queries = []

    if not keywords_ko:
        return ''

    main_kw = keywords_ko[0].replace('실적/결과', '실적').replace('검사/확인', '검사')

    # 유형에 따른 쿼리 생성
    if '이력' in keywords_ko or '로그' in keywords_ko:
        queries.append(f"{main_kw} 이력 조회")
        queries.append(f"{main_kw} 변경 이력")
    elif '실적' in ' '.join(keywords_ko) or '결과' in ' '.join(keywords_ko):
        queries.append(f"{main_kw} 실적 조회")
        queries.append(f"일일 {main_kw} 실적")
    elif '계획' in keywords_ko:
        queries.append(f"{main_kw} 계획 조회")
        queries.append(f"당일 {main_kw} 계획")
    elif '마스터' in keywords_ko:
        queries.append(f"{main_kw} 정보 조회")
        queries.append(f"{main_kw} 목록")
    elif '검사' in ' '.join(keywords_ko):
        queries.append(f"{main_kw} 검사 결과")
        queries.append(f"{main_kw} 검사 현황")
    else:
        queries.append(f"{main_kw} 정보 조회")
        queries.append(f"{main_kw} 현황")

    # 도메인별 추가 쿼리
    if domain == 'SMT/실장':
        queries.append("SMT 현황")
    elif domain == '재고':
        queries.append("재고 현황 조회")
    elif domain == '품질':
        queries.append("품질 검사 현황")

    return '|'.join(queries[:3])


def main():
    """메인 함수: 전체 테이블에 대해 메타데이터를 생성합니다."""
    print("=" * 60)
    print("Table Metadata Optimized 생성 시작...")
    print("=" * 60)

    if not os.path.exists(INPUT_URI):
        print(f"Error: {INPUT_URI} not found")
        return

    input_rows = read_csv(INPUT_URI)
    print(f"✓ table_info_template.csv: {len(input_rows)} 행 로드")

    output_rows = []
    domain_stats = {}

    for row in input_rows:
        table_name = row.get('table_name', '').strip()
        if not table_name:
            continue

        # 테이블명 파싱
        prefix, keywords_ko, keywords_en = parse_table_name(table_name)

        # 도메인 결정
        domain = get_domain_from_prefix(table_name)

        # 설명 생성
        desc_ko = generate_description_ko(table_name, keywords_ko, domain)
        desc_en = generate_description_en(table_name, keywords_en, domain)

        # 키워드 생성
        keywords = generate_keywords(table_name, keywords_ko, domain)

        # 샘플 쿼리 생성
        sample_queries = generate_sample_queries(table_name, keywords_ko, domain)

        output_row = {
            'table_name': table_name,
            'table_description_ko': desc_ko,
            'table_description_en': desc_en,
            'domain': domain,
            'keywords': keywords,
            'sample_queries': sample_queries
        }
        output_rows.append(output_row)

        domain_stats[domain] = domain_stats.get(domain, 0) + 1

    print(f"✓ 변환 완료: {len(output_rows)} 테이블")

    # 도메인별 통계 출력
    print("\n[도메인별 테이블 수]")
    for domain, count in sorted(domain_stats.items(), key=lambda x: -x[1]):
        print(f"  - {domain}: {count}개")

    # CSV 파일 저장
    fieldnames = ['table_name', 'table_description_ko', 'table_description_en', 'domain', 'keywords', 'sample_queries']

    with open(OUTPUT_URI, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in sorted(output_rows, key=lambda x: x['table_name']):
            writer.writerow(row)

    print("\n" + "=" * 60)
    print(f"✓ 파일 저장 완료: {OUTPUT_URI}")
    print(f"✓ 총 {len(output_rows)}개 테이블 메타데이터 생성")
    print("=" * 60)

    # 샘플 데이터 출력
    print("\n[샘플 데이터]")
    for i, row in enumerate(sorted(output_rows, key=lambda x: x['table_name'])[:5]):
        print(f"\n{i+1}. {row['table_name']}")
        print(f"   한글: {row['table_description_ko']}")
        print(f"   영문: {row['table_description_en']}")
        print(f"   도메인: {row['domain']}")
        print(f"   키워드: {row['keywords']}")
        print(f"   샘플쿼리: {row['sample_queries']}")


if __name__ == '__main__':
    main()

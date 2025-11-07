# CSV 일괄 등록 기능 추가

**추가 날짜**: 2025-01-06
**추가 사유**: 1000개 이상의 대량 칼럼/코드 정보를 효율적으로 등록하기 위함

---

## 🎯 배경

### 문제점
- 기존 방식: JSON 형식으로 일일이 입력해야 함
- 1000개 이상의 칼럼을 대화로 등록하는 것은 비효율적
- 사용자가 이미 Excel/CSV로 정리한 데이터를 재입력해야 함

### 해결책
**CSV 파일을 직접 읽어서 일괄 등록하는 Tool 추가**

---

## ✅ 추가된 Tool

### Tool 8: `import_common_columns_csv`

**용도**: CSV 파일로부터 공통 칼럼 정보 일괄 등록

**파라미터**:
```
- database_sid: Database SID (예: "PROD_DB")
- csv_file_path: CSV 파일 경로 (예: "D:/data/columns.csv")
```

**CSV 형식**:
```csv
column_name,korean_name,description,is_code_column,sample_values,business_rule,unit,aggregation_functions,is_sensitive
STATUS,상태,처리 상태 코드,Y,01|02|03,01→02→03 순서로 전이,,COUNT|DISTINCT,N
CUSTOMER_ID,고객번호,고객 고유 식별 번호,N,10001|10002,시스템 자동 생성,,COUNT|DISTINCT,N
AMOUNT,금액,거래 금액,N,10000|50000,0 이상의 정수,원,SUM|AVG|MAX|MIN,N
```

**특징**:
- UTF-8 BOM 지원 (`utf-8-sig`)
- 헤더 자동 인식 (csv.DictReader)
- Y/N → True/False 자동 변환
- 1000개 이상 데이터도 한 번에 처리

---

### Tool 9: `import_code_definitions_csv`

**용도**: CSV 파일로부터 코드 정의 일괄 등록

**파라미터**:
```
- database_sid: Database SID (예: "PROD_DB")
- csv_file_path: CSV 파일 경로 (예: "D:/data/codes.csv")
```

**CSV 형식**:
```csv
column_name,code_value,code_label,code_description,display_order,is_active,parent_code,state_transition
STATUS,01,접수,접수된 상태,1,Y,,02
STATUS,02,처리중,처리 진행중인 상태,2,Y,,03
STATUS,03,완료,처리가 완료된 상태,3,Y,,,
GRADE,VIP,VIP,최근 1년간 구매 실적 1000만원 이상,1,Y,,,
GRADE,GOLD,골드,최근 1년간 구매 실적 500만원 이상,2,Y,,,
```

**특징**:
- 칼럼별 그룹화 자동 처리
- display_order 자동 변환 (문자열 → 정수)
- Y/N → True/False 자동 변환
- 수천 개 코드도 한 번에 처리

---

## 📋 사용 예시

### 시나리오: PROD_DB에 1500개 칼럼, 5000개 코드 등록

#### 1단계: CSV 파일 준비

**파일 위치**:
```
D:/metadata/
├── prod_common_columns.csv     (1500개 칼럼)
└── prod_code_definitions.csv   (5000개 코드)
```

#### 2단계: Claude Desktop에서 일괄 등록

**공통 칼럼 등록**:
```
"PROD_DB의 공통 칼럼을 등록해줘.
CSV 파일 경로는 D:/metadata/prod_common_columns.csv 야"
```

Claude가 `import_common_columns_csv` Tool 호출:
```
Tool: import_common_columns_csv
- database_sid: "PROD_DB"
- csv_file_path: "D:/metadata/prod_common_columns.csv"

✅ 결과:
- 등록된 칼럼 수: 1500개
- 저장 위치: common_metadata/PROD_DB/common_columns.json
```

**코드 정의 등록**:
```
"PROD_DB의 코드 정의를 등록해줘.
CSV 파일 경로는 D:/metadata/prod_code_definitions.csv 야"
```

Claude가 `import_code_definitions_csv` Tool 호출:
```
Tool: import_code_definitions_csv
- database_sid: "PROD_DB"
- csv_file_path: "D:/metadata/prod_code_definitions.csv"

✅ 결과:
- 등록된 코드 수: 5000개
- 코드 칼럼 수: 150개
- 저장 위치: common_metadata/PROD_DB/code_definitions.json
```

#### 3단계: 메타데이터 추출

```
"PROD_DB의 SCOTT 스키마 메타데이터를 추출해줘"
```

자동으로 1500개 칼럼 정보와 5000개 코드 정보가 매칭됨.

---

## 🔄 기존 방식 vs 새 방식

### 기존 방식 (JSON 직접 입력)

```
사용자: "칼럼 3개를 등록해줘. STATUS는 상태이고..."

Claude: register_common_columns 호출
        columns_data: '[{"column_name":"STATUS",...}]'

→ 1000개면 반복 불가능
```

### 새 방식 (CSV 일괄 등록)

```
사용자: "CSV 파일로 칼럼 1500개 등록해줘.
        경로는 D:/data/columns.csv 야"

Claude: import_common_columns_csv 호출
        csv_file_path: "D:/data/columns.csv"

→ 1500개도 한 번에 처리
```

---

## 💻 구현 상세

### CSV 읽기 처리

```python
# UTF-8 BOM 지원
with open(csv_path, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    for row in reader:
        column = {
            'column_name': row['column_name'],
            'korean_name': row.get('korean_name', ''),
            'description': row.get('description', ''),
            'is_code_column': row.get('is_code_column', 'N').upper() == 'Y',
            ...
        }
        columns.append(column)
```

### 자동 타입 변환

- `is_code_column`: `'Y'` → `True`, `'N'` → `False`
- `is_active`: `'Y'` → `True`, `'N'` → `False`
- `is_sensitive`: `'Y'` → `True`, `'N'` → `False`
- `display_order`: `'1'` → `1` (문자열 → 정수)

### 에러 처리

- 파일 없음 → 명확한 에러 메시지
- CSV 형식 오류 → traceback 포함
- UTF-8 인코딩 문제 → `utf-8-sig`로 BOM 처리

---

## 📂 출력 결과

### 공통 칼럼 등록 결과

```
✅ 공통 칼럼 CSV 일괄 등록 완료

**Database**: PROD_DB
**CSV 파일**: D:/metadata/prod_common_columns.csv
**등록된 칼럼 수**: 1500개
**전체 칼럼 수**: 1500개

**등록된 칼럼 목록**:
- STATUS: 상태
- CUSTOMER_ID: 고객번호
- ORDER_ID: 주문번호
- AMOUNT: 금액
- ORDER_DATE: 주문일자
- PAYMENT_METHOD: 결제수단
- SHIPPING_STATUS: 배송상태
- PRODUCT_ID: 상품번호
- QUANTITY: 수량
- PRICE: 가격
- ... 외 1490개
```

### 코드 정의 등록 결과

```
✅ 코드 정의 CSV 일괄 등록 완료

**Database**: PROD_DB
**CSV 파일**: D:/metadata/prod_code_definitions.csv
**등록된 코드 수**: 5000개
**코드 칼럼 수**: 150개

**칼럼별 코드 수**:
- GRADE: 4개
- ORDER_STATUS: 5개
- PAYMENT_METHOD: 8개
- PAYMENT_STATUS: 3개
- SHIPPING_STATUS: 6개
- ...
```

---

## 🎯 사용 시나리오

### 1. 초기 대량 등록

**상황**: 회사에서 1500개 칼럼, 5000개 코드 정보를 이미 Excel로 관리 중

**방법**:
1. Excel → CSV 저장
2. `import_common_columns_csv` 호출
3. `import_code_definitions_csv` 호출
4. 완료 (5분 소요)

---

### 2. 증분 업데이트

**상황**: 이미 1500개 등록됨, 10개 추가 필요

**방법 A** (CSV):
1. 10개만 포함된 CSV 작성
2. `import_common_columns_csv` 호출
3. 기존 데이터 + 10개 병합됨

**방법 B** (JSON):
```
"칼럼 10개 추가해줘.
NEW_FIELD1은 새필드1이고..."
```

---

### 3. 다른 DB에 동일 구조 적용

**상황**: PROD_DB 구조를 TEST_DB에도 적용

**방법**:
1. 같은 CSV 파일 사용
2. `import_common_columns_csv(database_sid="TEST_DB", ...)`
3. `import_code_definitions_csv(database_sid="TEST_DB", ...)`
4. 완료

---

## 📊 Tool 번호 재정렬

CSV 일괄 등록 Tool 추가로 Tool 번호가 변경되었습니다:

| Tool | 이름 | 설명 |
|------|------|------|
| 1 | register_database_credentials | DB 접속 정보 수동 등록 |
| 2 | load_tnsnames | tnsnames.ora 파일 파싱 |
| 3 | list_available_databases | tnsnames 캐시된 DB 목록 |
| 4 | connect_database | tnsnames DB 연결 |
| 5 | register_common_columns | 공통 칼럼 JSON 등록 |
| 6 | register_code_values | 코드 값 JSON 등록 |
| 7 | view_common_metadata | 공통 메타데이터 조회 |
| **8** | **import_common_columns_csv** | **공통 칼럼 CSV 일괄 등록 (신규)** |
| **9** | **import_code_definitions_csv** | **코드 정의 CSV 일괄 등록 (신규)** |
| 10 | generate_csv_from_schema | CSV 파일 자동 생성 |
| 11 | extract_and_integrate_metadata | 메타데이터 추출 및 통합 |
| 12 | show_databases | DB 목록 조회 |
| 13 | show_schemas | 스키마 목록 조회 |
| 14 | show_tables | 테이블 목록 조회 |
| 15 | get_table_summaries_for_query | Stage 1: 테이블 요약 |
| 16 | get_detailed_metadata_for_sql | Stage 2: 상세 메타데이터 |
| 17 | execute_sql | SQL 실행 |
| 18 | get_sql_execution_history | SQL 실행 이력 |

**총 Tool 수**: 18개 → 20개

---

## ✅ 체크리스트

CSV 일괄 등록 사용 시:

- [ ] CSV 파일이 UTF-8 인코딩인지 확인
- [ ] 헤더가 정확한지 확인 (템플릿 참고)
- [ ] `is_code_column`, `is_active`, `is_sensitive` 필드가 `Y` 또는 `N`인지 확인
- [ ] `display_order`가 숫자인지 확인
- [ ] CSV 파일 경로가 절대 경로인지 확인 (예: `D:/data/file.csv`)

---

**업데이트 완료 날짜**: 2025-01-06

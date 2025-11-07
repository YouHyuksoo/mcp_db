# 공통 메타데이터 관리 (DB별)

이 폴더는 **각 데이터베이스별로** 공통 칼럼 정보와 코드 정보를 관리합니다.

## 📁 구조

```
common_metadata/
├── common_columns_template.csv       # 공통 칼럼 정의 템플릿
├── code_definitions_template.csv     # 코드 정의 템플릿
├── table_info_template.csv           # 테이블 정보 템플릿
├── README.md                          # 이 파일
├── {DB_SID}/                          # DB별 폴더 (자동 생성)
│   ├── common_columns.json           # 해당 DB의 공통 칼럼 정보
│   ├── code_definitions.json         # 해당 DB의 코드 정보
│   └── {SCHEMA}/                     # 스키마별 폴더
│       └── table_info.json           # 해당 스키마의 테이블 정보
├── PROD_DB/
│   ├── common_columns.json
│   ├── code_definitions.json
│   └── SCOTT/
│       └── table_info.json
└── TEST_DB/
    ├── common_columns.json
    ├── code_definitions.json
    └── HR/
        └── table_info.json
```

## 🎯 개념

### DB별 공통 메타데이터

각 데이터베이스는 **고유한 공통 칼럼 정의와 코드 정의**를 가집니다.

**예시**:
- `PROD_DB`의 `STATUS` 칼럼: 01=접수, 02=처리중, 03=완료
- `TEST_DB`의 `STATUS` 칼럼: A=대기, B=처리중, C=완료 (다른 코드 체계)

### 공통 칼럼이란?

**같은 DB 내에서 같은 이름의 칼럼은 모든 테이블에서 같은 의미를 가진다**는 원칙에 따라 칼럼 정보를 한 번만 정의합니다.

**예시**:
- `CUSTOMER_ID`는 어느 테이블에 있든 "고객번호"를 의미
- `STATUS`는 어느 테이블에 있든 "상태 코드"를 의미
- `AMOUNT`는 어느 테이블에 있든 "금액"을 의미

### 코드 정의란?

코드 칼럼 (`is_code_column=Y`)의 코드 값과 레이블을 정의합니다.

**예시**:
- `STATUS` 칼럼: `01`=접수, `02`=처리중, `03`=완료
- `GRADE` 칼럼: `VIP`=VIP, `GOLD`=골드, `SILVER`=실버

## 📝 사용 방법

### ✅ 권장: CSV 일괄 등록 (1000개 이상)

대량의 칼럼/코드 정보는 **CSV 파일로 준비 → 일괄 등록**하는 것이 효율적입니다.

### 1단계: CSV 파일 작성

#### A. 테이블 정보 (`table_info_template.csv`)

```csv
table_name,business_purpose,usage_scenario_1,usage_scenario_2,usage_scenario_3,related_tables
CUSTOMERS,고객의 기본 정보 및 연락처를 관리하는 마스터 테이블,신규 고객 등록 및 정보 조회,고객 등급별 마케팅 대상 선정,고객 이력 추적 및 분석,ORDERS|ADDRESSES|CUSTOMER_NOTES
ORDERS,고객 주문 정보를 저장하고 주문 생명주기를 관리하는 핵심 테이블,온라인/오프라인 주문 접수 및 처리,주문 상태 추적 및 업데이트,주문 통계 및 매출 분석,CUSTOMERS|ORDER_ITEMS|PAYMENTS|SHIPMENTS
```

**필드 설명**:
- `table_name`: 테이블명 (대문자, 영어)
- `business_purpose`: 비즈니스 목적 (한 문장 설명)
- `usage_scenario_1/2/3`: 주요 사용 시나리오 (최대 3개)
- `related_tables`: 연관 테이블 (`|`로 구분)

#### B. 공통 칼럼 정보 (`common_columns_template.csv`)

```csv
column_name,korean_name,description,is_code_column,sample_values,business_rule,unit,aggregation_functions,is_sensitive
STATUS,상태,처리 상태 코드,Y,01|02|03,01→02→03 순서로 전이,,COUNT|DISTINCT,N
CUSTOMER_ID,고객번호,고객 고유 식별 번호,N,10001|10002,시스템 자동 생성,,COUNT|DISTINCT,N
```

**필드 설명**:
- `column_name`: 칼럼명 (대문자, 영어)
- `korean_name`: 한글명
- `description`: 설명
- `is_code_column`: 코드 칼럼 여부 (`Y` 또는 `N`)
- `sample_values`: 샘플 값 (`|`로 구분)
- `business_rule`: 비즈니스 규칙
- `unit`: 단위 (금액, 개수 등)
- `aggregation_functions`: 집계 함수 (`SUM|AVG|MAX|MIN|COUNT|DISTINCT`)
- `is_sensitive`: 민감 정보 여부 (`Y` 또는 `N`)

#### B. 코드 정의 (`code_definitions_template.csv`)

```csv
column_name,code_value,code_label,code_description,display_order,is_active,parent_code,state_transition
STATUS,01,접수,접수된 상태,1,Y,,02
STATUS,02,처리중,처리 진행중,2,Y,,03
STATUS,03,완료,처리 완료,3,Y,,,
```

**필드 설명**:
- `column_name`: 칼럼명 (코드 타입 이름)
- `code_value`: 코드 값
- `code_label`: 코드 레이블
- `code_description`: 코드 설명
- `display_order`: 표시 순서
- `is_active`: 활성 여부 (`Y` 또는 `N`)
- `parent_code`: 상위 코드 (계층 구조인 경우)
- `state_transition`: 다음 상태 (상태 전이가 있는 경우)

### 2단계: MCP Tool로 CSV 일괄 등록

#### A. 테이블 정보 CSV 일괄 등록

```
Tool: import_table_info_csv

Input:
- database_sid: "PROD_DB"
- schema_name: "SCOTT"
- csv_file_path: "D:/my_data/prod_scott_table_info.csv"

→ 100개 테이블 정보도 한 번에 등록됨
```

**사용 예시 (Claude Desktop)**:
```
"PROD_DB의 SCOTT 스키마 테이블 정보를 등록해줘.
CSV 파일 경로는 D:/my_data/prod_scott_table_info.csv 야"
```

#### B. 공통 칼럼 CSV 일괄 등록

```
Tool: import_common_columns_csv

Input:
- database_sid: "PROD_DB"
- csv_file_path: "D:/my_data/prod_common_columns.csv"

→ 1000개 칼럼도 한 번에 등록됨
```

**사용 예시 (Claude Desktop)**:
```
"PROD_DB의 공통 칼럼을 등록해줘.
CSV 파일 경로는 D:/my_data/prod_common_columns.csv 야"
```

#### C. 코드 정의 CSV 일괄 등록

```
Tool: import_code_definitions_csv

Input:
- database_sid: "PROD_DB"
- csv_file_path: "D:/my_data/prod_code_definitions.csv"

→ 수천 개 코드도 한 번에 등록됨
```

**사용 예시 (Claude Desktop)**:
```
"PROD_DB의 코드 정의를 등록해줘.
CSV 파일 경로는 D:/my_data/prod_code_definitions.csv 야"
```

---

### 대안: 소량 데이터 JSON 등록 (추가/수정용)

소량의 데이터를 추가하거나 수정할 때는 JSON 형식으로 직접 등록할 수도 있습니다.

#### A. 공통 칼럼 JSON 등록

```
Tool: register_common_columns

Input:
- database_sid: "PROD_DB"
- columns_data (JSON):
[
  {
    "column_name": "STATUS",
    "korean_name": "상태",
    "description": "처리 상태 코드",
    "is_code_column": true,
    "sample_values": "01|02|03",
    "business_rule": "01→02→03 순서로 전이",
    "unit": "",
    "aggregation_functions": "COUNT|DISTINCT",
    "is_sensitive": false
  }
]
```

#### B. 코드 값 JSON 등록

```
Tool: register_code_values

Input:
- database_sid: "PROD_DB"
- codes_data (JSON):
[
  {
    "column_name": "STATUS",
    "code_value": "01",
    "code_label": "접수",
    "code_description": "접수된 상태",
    "display_order": 1,
    "is_active": true,
    "parent_code": "",
    "state_transition": "02"
  }
]
```

### 3단계: 메타데이터 추출

```
Tool: extract_and_integrate_metadata

Input:
- database_sid: "PROD_DB"
- schema_name: "SCOTT"
```

**자동으로 수행되는 작업**:
1. DB에서 테이블/칼럼 스키마 추출
2. 등록된 공통 칼럼 정보와 자동 매칭
3. 등록된 코드 정보와 자동 매칭
4. `metadata/{DB_SID}/{SCHEMA}/{TABLE}/unified_metadata.json` 생성

## 🔄 전체 프로세스 (DB별)

### 방법 1: CSV 일괄 등록 (권장 - 대량 데이터)

```
1. CSV 파일 준비
   - prod_scott_table_info.csv (100개 테이블)
   - prod_common_columns.csv (1000개 칼럼)
   - prod_code_definitions.csv (5000개 코드)

2. CSV 일괄 등록 (순서 중요!)
   ① import_table_info_csv(database_sid="PROD_DB", schema_name="SCOTT", csv_file_path="...")
      → common_metadata/PROD_DB/SCOTT/table_info.json 생성

   ② import_common_columns_csv(database_sid="PROD_DB", csv_file_path="...")
      → common_metadata/PROD_DB/common_columns.json 생성

   ③ import_code_definitions_csv(database_sid="PROD_DB", csv_file_path="...")
      → common_metadata/PROD_DB/code_definitions.json 생성

3. DB 스키마 추출 + 자동 매칭
   extract_and_integrate_metadata(database_sid="PROD_DB", schema_name="SCOTT")
   → metadata/PROD_DB/SCOTT/{TABLE}/unified_metadata.json 생성
   → 테이블 정보, 칼럼 정보, 코드 정보 모두 자동 매칭됨

4. Stage 1: 테이블 요약 제공
   get_table_summaries_for_query(database_sid="PROD_DB", schema_name="SCOTT", ...)
   → Claude가 관련 테이블 선택

5. Stage 2: 상세 메타데이터 제공
   get_detailed_metadata_for_sql(database_sid="PROD_DB", schema_name="SCOTT", ...)
   → Claude가 SQL 생성

6. SQL 실행
   execute_sql(database_sid="PROD_DB", schema_name="SCOTT", ...)
```

### 방법 2: JSON 직접 등록 (소량 데이터)

```
1. JSON 형식으로 등록
   register_common_columns(database_sid="PROD_DB", columns_data=...)
   register_code_values(database_sid="PROD_DB", codes_data=...)

2. 이후 동일
```

## 📊 예시 시나리오

### 시나리오: 주문 관리 시스템

**1. 공통 칼럼 정의**:
- `CUSTOMER_ID`: 고객번호
- `ORDER_ID`: 주문번호
- `STATUS`: 상태
- `AMOUNT`: 금액
- `ORDER_DATE`: 주문일자

**2. 코드 정의**:
- `STATUS`: 01=접수, 02=처리중, 03=완료, 04=취소
- `GRADE`: VIP, GOLD, SILVER, BRONZE

**3. DB 구조**:
```
CUSTOMERS (CUSTOMER_ID, NAME, EMAIL, GRADE, ...)
ORDERS (ORDER_ID, CUSTOMER_ID, ORDER_DATE, STATUS, AMOUNT, ...)
ORDER_ITEMS (ORDER_ID, ITEM_ID, AMOUNT, ...)
```

**4. 등록 후**:
- `CUSTOMER_ID`는 CUSTOMERS, ORDERS 모두에서 "고객번호" 의미
- `STATUS`는 ORDERS에서 코드 값 01~04 사용
- `GRADE`는 CUSTOMERS에서 코드 값 VIP~BRONZE 사용
- `AMOUNT`는 ORDERS, ORDER_ITEMS 모두에서 "금액" 의미

**5. 자동 생성되는 메타데이터**:
```json
{
  "columns": [
    {
      "name": "STATUS",
      "korean_name": "상태",
      "description": "처리 상태 코드",
      "is_code_column": true,
      "codes": [
        {"value": "01", "label": "접수", "description": "접수된 상태"},
        {"value": "02", "label": "처리중", "description": "처리 진행중"},
        ...
      ]
    }
  ]
}
```

## 💡 장점

1. **중복 제거**: 칼럼 정보를 한 번만 정의
2. **일관성**: 모든 테이블에서 같은 의미 보장
3. **유지보수 용이**: 정의 변경 시 한 곳만 수정
4. **자동 매칭**: MCP가 자동으로 DB 스키마와 매칭
5. **토큰 절약**: Stage 1/2로 나눠서 필요한 정보만 전달

## 🔍 조회

### 등록된 메타데이터 확인 (DB별)

```
Tool: view_common_metadata

Input:
- database_sid: "PROD_DB"
- metadata_type: "all"

Output:
- 공통 칼럼 수
- 코드 칼럼 수
- 전체 코드 수
- 상세 정보
```

## ⚙️ 파일 저장 위치 (DB별)

각 DB별로 별도 폴더에 저장됩니다:

- `common_metadata/{DB_SID}/common_columns.json`: 해당 DB의 공통 칼럼 정의
- `common_metadata/{DB_SID}/code_definitions.json`: 해당 DB의 코드 정의

**자동 생성 내용**:
```json
{
  "database_sid": "PROD_DB",
  "last_updated": "2025-01-05T12:00:00",
  "column_count": 10,
  "columns": {
    "STATUS": {
      "column_name": "STATUS",
      "korean_name": "상태",
      ...
    }
  }
}
```

## 🚀 빠른 시작

### CSV 일괄 등록 방식 (권장)

1. **CSV 파일 작성** (3종)
   - `D:/my_data/prod_scott_table_info.csv` (테이블 정보)
   - `D:/my_data/prod_common_columns.csv` (칼럼 정보)
   - `D:/my_data/prod_code_definitions.csv` (코드 정보)

2. **Claude Desktop에 순서대로 요청**
   ```
   "PROD_DB의 SCOTT 스키마 테이블 정보를 등록해줘.
   CSV 파일은 D:/my_data/prod_scott_table_info.csv 야"

   "PROD_DB의 공통 칼럼을 등록해줘.
   CSV 파일은 D:/my_data/prod_common_columns.csv 야"

   "PROD_DB의 코드 정의를 등록해줘.
   CSV 파일은 D:/my_data/prod_code_definitions.csv 야"
   ```

3. **메타데이터 추출**
   ```
   "PROD_DB의 SCOTT 스키마 메타데이터를 추출해줘"
   ```

4. **완료!** 이제 자연어로 SQL 질의 가능

### JSON 등록 방식 (소량 데이터)

1. `register_common_columns(database_sid="PROD_DB", ...)` Tool 실행
2. `register_code_values(database_sid="PROD_DB", ...)` Tool 실행
3. `extract_and_integrate_metadata(database_sid="PROD_DB", ...)` Tool 실행
4. 완료!

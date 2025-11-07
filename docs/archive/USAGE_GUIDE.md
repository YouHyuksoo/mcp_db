# 📘 Oracle Database MCP 서버 사용 가이드

## 목차
1. [빠른 시작](#빠른-시작)
2. [CSV 파일 작성 가이드](#csv-파일-작성-가이드)
3. [MCP 서버 설정](#mcp-서버-설정)
4. [주요 워크플로우](#주요-워크플로우)
5. [Tool 사용 예제](#tool-사용-예제)
6. [문제 해결](#문제-해결)

---

## 빠른 시작

### 1. 환경 설정

```bash
# 프로젝트 클론 또는 다운로드 후
cd D:\Project\mcp_db

# 가상환경 활성화 (이미 생성되어 있음)
venv\Scripts\activate

# 환경변수 설정
copy .env.example .env
# .env 파일을 열어 ANTHROPIC_API_KEY 입력
```

### 2. Oracle Database 접속 정보 등록

```python
# Claude.ai에서 다음과 같이 요청:
"PROD_DB 데이터베이스 접속 정보를 등록해줘.
호스트: db.company.com
포트: 1521
SID: PROD
사용자: scott
비밀번호: tiger123"
```

MCP 서버가 `register_database_credentials` tool을 호출하여 암호화하여 저장합니다.

### 3. CSV 메타데이터 파일 준비

다음 위치에 3개의 CSV 파일을 작성합니다:

```
input/
  └── PROD_DB/              # Database SID
      └── SCOTT/            # Schema 이름
          ├── table_info.csv
          ├── column_info.csv
          └── code_values.csv
```

자세한 양식은 [CSV 파일 작성 가이드](#csv-파일-작성-가이드) 참조

### 4. 메타데이터 추출 및 통합

```python
# Claude.ai에서 요청:
"PROD_DB의 SCOTT 스키마 메타데이터를 추출하고 통합해줘"
```

MCP 서버가 자동으로:
- Oracle DB에서 스키마 정보 추출 (테이블, 칼럼, PK, FK, 인덱스)
- 사용자 제공 CSV 파일 파싱
- 통합 메타데이터 생성 및 저장

### 5. 자연어로 SQL 생성 및 실행

```python
# Claude.ai에서 자연어로 요청:
"최근 1개월간 주문 금액이 100만원 이상인 VIP 고객의 주문 내역을 보여줘"
```

MCP 서버가 자동으로:
- 2단계 LLM을 통해 SQL 생성
- SQL 실행
- 결과 반환

---

## CSV 파일 작성 가이드

### 1. table_info.csv

**목적**: 테이블의 비즈니스 목적과 활용 시나리오를 정의

**필수 칼럼**:
- `table_name`: 테이블명 (대문자)
- `business_purpose`: 테이블의 비즈니스 목적 (한 문장)
- `usage_scenario_1`: 주요 활용 시나리오 1
- `usage_scenario_2`: 주요 활용 시나리오 2
- `usage_scenario_3`: 주요 활용 시나리오 3
- `related_tables`: 연관 테이블 (파이프 구분: `TABLE1|TABLE2`)

**예시**:
```csv
table_name,business_purpose,usage_scenario_1,usage_scenario_2,usage_scenario_3,related_tables
ORDERS,고객 주문 정보를 저장하고 주문 생명주기를 관리하는 핵심 테이블,일별/월별 매출 집계,배송 상태별 주문 조회,고객별 주문 이력 분석,CUSTOMERS|ORDER_ITEMS|SHIPMENTS
CUSTOMERS,고객의 기본 정보 및 연락처를 관리하는 마스터 테이블,고객 정보 조회 및 수정,신규 고객 등록,고객 통계 분석,ORDERS|CUSTOMER_ADDRESSES
```

**작성 팁**:
- `business_purpose`는 LLM이 테이블 선택 시 참조하므로 명확하게 작성
- `usage_scenario`는 실제 업무에서 사용하는 패턴을 구체적으로 기술
- `related_tables`는 JOIN이 자주 발생하는 테이블들을 명시

---

### 2. column_info.csv

**목적**: 각 칼럼의 한글명, 비즈니스 의미, 규칙을 정의

**필수 칼럼**:
- `table_name`: 테이블명
- `column_name`: 칼럼명 (대문자)
- `korean_name`: 한글 칼럼명
- `description`: 칼럼 설명
- `business_rule`: 비즈니스 규칙 (선택)
- `sample_values`: 샘플 값 (파이프 구분: `value1|value2`)
- `unit`: 단위 (예: 원, 개, %)
- `is_code_column`: 코드 칼럼 여부 (`Y` 또는 `N`)
- `aggregation_functions`: 집계 함수 (예: `SUM|AVG|MIN|MAX`)
- `is_sensitive`: 민감정보 여부 (`Y` 또는 `N`)

**예시**:
```csv
table_name,column_name,korean_name,description,business_rule,sample_values,unit,is_code_column,aggregation_functions,is_sensitive
ORDERS,ORDER_ID,주문번호,각 주문을 고유하게 식별하는 일련번호,시스템이 자동으로 채번하며 변경 불가,1001|1002|1003,,N,,N
ORDERS,STATUS,주문상태,주문의 현재 처리 단계를 나타내는 코드,01→02→03 또는 99로 상태 전이,01|02|03|99,,Y,,N
ORDERS,AMOUNT,주문금액,주문의 총 결제 금액,0보다 큰 양수 값만 허용,50000|120000|75000,원,N,SUM|AVG|MIN|MAX,N
CUSTOMERS,EMAIL,이메일,고객 연락용 이메일 주소,이메일 형식 검증 필수,hong@example.com|kim@test.com,,N,,Y
```

**작성 팁**:
- `is_code_column=Y`인 경우 반드시 `code_values.csv`에 코드 정의 추가
- `business_rule`은 SQL 생성 시 WHERE 조건 참조용
- `aggregation_functions`는 집계 쿼리 생성 시 힌트로 사용
- `is_sensitive=Y`인 경우 민감정보 마스킹 처리 필요 (향후 기능)

---

### 3. code_values.csv

**목적**: 코드 칼럼의 값별 의미와 상태 전이 규칙 정의

**필수 칼럼**:
- `table_name`: 테이블명
- `column_name`: 칼럼명
- `code_value`: 코드 값
- `code_label`: 코드 한글명 (짧게)
- `code_description`: 코드 상세 설명
- `display_order`: 표시 순서
- `is_active`: 사용 여부 (`Y` 또는 `N`)
- `parent_code`: 부모 코드 (계층 구조 시)
- `state_transition`: 다음 상태로 전이 가능한 코드 (파이프 구분)

**예시**:
```csv
table_name,column_name,code_value,code_label,code_description,display_order,is_active,parent_code,state_transition
ORDERS,STATUS,01,주문접수,고객으로부터 주문이 접수된 초기 상태,1,Y,,02
ORDERS,STATUS,02,결제완료,결제가 정상적으로 완료된 상태,2,Y,01,03
ORDERS,STATUS,03,배송중,상품이 배송 중인 상태,3,Y,02,04
ORDERS,STATUS,99,주문취소,고객 요청 또는 시스템에 의해 주문이 취소된 상태,99,Y,01|02,
CUSTOMERS,GRADE,BRONZE,브론즈,신규 회원 또는 구매 실적 100만원 미만,1,Y,,SILVER
CUSTOMERS,GRADE,SILVER,실버,최근 1년간 구매 실적 100만원 이상,2,Y,BRONZE,GOLD
```

**작성 팁**:
- `state_transition`은 상태 코드의 경우 다음 가능한 상태를 명시
- `parent_code`는 계층적 코드 구조가 있을 때 사용 (예: 대분류|중분류)
- `is_active=N`인 코드는 과거 데이터 해석용으로만 사용

---

## MCP 서버 설정

### Claude Desktop 설정 파일 수정

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "oracle-db": {
      "command": "D:\\Project\\mcp_db\\venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "src.mcp_server"
      ],
      "cwd": "D:\\Project\\mcp_db",
      "env": {
        "PYTHONPATH": "D:\\Project\\mcp_db"
      }
    }
  }
}
```

**설정 후**: Claude Desktop 재시작

---

## 주요 워크플로우

### 워크플로우 1: 새 데이터베이스 추가

```
1. Oracle DB 접속 정보 등록
   → "MYDB 데이터베이스 접속 정보를 등록해줘"
   → register_database_credentials 호출

2. CSV 파일 작성
   → input/MYDB/SCOTT/ 폴더에 3개 CSV 작성

3. 메타데이터 추출 및 통합
   → "MYDB의 SCOTT 스키마 메타데이터를 추출해줘"
   → extract_and_integrate_metadata 호출

4. 확인
   → "SCOTT 스키마의 테이블 목록을 보여줘"
   → show_tables 호출
```

---

### 워크플로우 2: 자연어로 데이터 조회

```
1. 자연어 쿼리 요청
   → "최근 3개월간 VIP 고객의 총 주문 금액을 보여줘"

2. MCP 서버 처리
   → query_natural_language 호출
   → Stage 1: 관련 테이블 선택 (ORDERS, CUSTOMERS)
   → Stage 2: SQL 생성
   → SQL 실행
   → 결과 반환

3. 결과 확인 및 추가 질의
   → "위 고객들 중 이번 달 주문이 없는 고객을 찾아줘"
```

---

### 워크플로우 3: SQL만 생성 (실행 X)

```
1. SQL 생성 요청
   → "주문 상태별 건수를 집계하는 SQL을 생성해줘. 실행은 하지 말고 SQL만 보여줘"

2. MCP 서버 처리
   → generate_sql_only 호출
   → Stage 1: 테이블 선택
   → Stage 2: SQL 생성
   → SQL 반환 (실행 안 함)

3. SQL 검토 후 직접 실행
   → "위 SQL을 실행해줘"
   → execute_sql 호출
```

---

### 워크플로우 4: 데이터베이스 구조 탐색

```
1. 등록된 DB 확인
   → "등록된 데이터베이스 목록을 보여줘"
   → show_databases 호출

2. 스키마 확인
   → "PROD_DB의 스키마 목록을 보여줘"
   → show_schemas 호출

3. 테이블 구조 확인
   → "ORDERS 테이블 구조를 보여줘"
   → describe_table 호출

4. 프로시저 확인
   → "SCOTT 스키마의 프로시저 목록을 보여줘"
   → show_procedures 호출

5. 프로시저 소스 확인
   → "CALC_TOTAL_AMOUNT 프로시저의 소스를 보여줘"
   → show_procedure_source 호출
```

---

## Tool 사용 예제

### 1. register_database_credentials

**용도**: Oracle DB 접속 정보를 암호화하여 저장

**Claude.ai 요청 예시**:
```
"운영 DB 접속 정보를 등록해줘.
- Database SID: PROD_DB
- 호스트: db.company.com
- 포트: 1521
- 서비스명: PROD
- 사용자: scott
- 비밀번호: tiger123"
```

**저장 위치**: `credentials/PROD_DB.json.enc` (암호화됨)

---

### 2. extract_and_integrate_metadata

**용도**: DB 스키마 추출 + CSV 파싱 + 통합 메타데이터 생성

**Claude.ai 요청 예시**:
```
"PROD_DB의 SCOTT 스키마 메타데이터를 추출하고 통합해줘"
```

**생성 파일**:
- `metadata/PROD_DB/SCOTT/{TABLE_NAME}/unified_metadata.json`
- `metadata/PROD_DB/SCOTT/table_summaries.json`

**처리 과정**:
1. Oracle DB 연결
2. 테이블, 칼럼, PK, FK, 인덱스 추출
3. CSV 파일 파싱 (table_info, column_info, code_values)
4. DB 스키마 + CSV 통합
5. unified_metadata.json 생성 (각 테이블별)
6. table_summaries.json 생성 (Stage 1 LLM용 경량 요약)

---

### 3. query_natural_language

**용도**: 자연어 → SQL 생성 → 실행 → 결과 반환 (One-shot)

**Claude.ai 요청 예시**:
```
"최근 1개월간 주문 금액 상위 10명의 고객 정보를 보여줘"
```

**처리 과정**:
1. **Stage 1 LLM**: table_summaries.json에서 관련 테이블 선택
   - 입력: 전체 테이블 1줄 요약 + 자연어 쿼리
   - 출력: 관련 테이블 리스트 (최대 5개)

2. **Stage 2 LLM**: 선택된 테이블의 상세 메타데이터로 SQL 생성
   - 입력: 선택된 테이블의 unified_metadata.json + 자연어 쿼리
   - 출력: Oracle SQL

3. **SQL 실행**: SQLExecutor로 SELECT 쿼리 실행

4. **결과 반환**: 칼럼명, 행 데이터, 행 개수

**반환 예시**:
```json
{
  "status": "success",
  "selected_tables": ["CUSTOMERS", "ORDERS"],
  "generated_sql": "SELECT c.CUSTOMER_NAME, SUM(o.AMOUNT) as TOTAL...",
  "columns": ["CUSTOMER_NAME", "TOTAL_AMOUNT", "ORDER_COUNT"],
  "rows": [
    {"CUSTOMER_NAME": "홍길동", "TOTAL_AMOUNT": 5000000, "ORDER_COUNT": 12},
    ...
  ],
  "row_count": 10
}
```

---

### 4. generate_sql_only

**용도**: SQL만 생성하고 실행은 하지 않음 (검토용)

**Claude.ai 요청 예시**:
```
"최근 6개월간 월별 매출 추이를 조회하는 SQL을 생성해줘.
실행은 하지 말고 SQL만 보여줘"
```

**반환**:
```json
{
  "status": "success",
  "selected_tables": ["ORDERS"],
  "generated_sql": "SELECT TO_CHAR(ORDER_DATE, 'YYYY-MM') AS MONTH, SUM(AMOUNT) AS TOTAL_SALES FROM SCOTT.ORDERS WHERE ORDER_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -6) GROUP BY TO_CHAR(ORDER_DATE, 'YYYY-MM') ORDER BY MONTH"
}
```

---

### 5. execute_sql

**용도**: 직접 작성한 SQL을 실행

**Claude.ai 요청 예시**:
```
"다음 SQL을 실행해줘:
SELECT * FROM SCOTT.ORDERS WHERE STATUS = '03' AND ROWNUM <= 10"
```

**보안**:
- SELECT 쿼리만 허용
- INSERT/UPDATE/DELETE는 차단
- 최대 1000행 제한

---

### 6. show_tables

**용도**: 특정 스키마의 테이블 목록 조회

**Claude.ai 요청 예시**:
```
"SCOTT 스키마의 테이블 목록을 보여줘"
```

**반환**:
```json
{
  "schema": "SCOTT",
  "tables": [
    {"table_name": "ORDERS", "table_type": "TABLE"},
    {"table_name": "CUSTOMERS", "table_type": "TABLE"},
    {"table_name": "ORDER_VIEW", "table_type": "VIEW"}
  ],
  "table_count": 3
}
```

---

### 7. describe_table

**용도**: 테이블 상세 구조 (칼럼, PK, FK, 인덱스) 조회

**Claude.ai 요청 예시**:
```
"ORDERS 테이블의 구조를 자세히 보여줘"
```

**반환**:
```json
{
  "table": "ORDERS",
  "columns": [
    {
      "name": "ORDER_ID",
      "type": "NUMBER(10)",
      "nullable": "N",
      "default": null,
      "comments": "주문번호"
    },
    ...
  ],
  "primary_keys": ["ORDER_ID"],
  "foreign_keys": [
    {
      "column": "CUSTOMER_ID",
      "ref_table": "CUSTOMERS",
      "ref_column": "CUSTOMER_ID"
    }
  ],
  "indexes": [
    {
      "name": "IDX_ORDERS_DATE",
      "columns": "ORDER_DATE",
      "uniqueness": "NONUNIQUE"
    }
  ]
}
```

---

### 8. show_procedures

**용도**: 스키마의 프로시저/함수 목록 조회

**Claude.ai 요청 예시**:
```
"SCOTT 스키마의 프로시저와 함수 목록을 보여줘"
```

**반환**:
```json
{
  "schema": "SCOTT",
  "objects": [
    {
      "name": "CALC_ORDER_TOTAL",
      "type": "PROCEDURE",
      "status": "VALID"
    },
    {
      "name": "GET_CUSTOMER_GRADE",
      "type": "FUNCTION",
      "status": "VALID"
    }
  ]
}
```

---

### 9. get_table_metadata

**용도**: 특정 테이블의 통합 메타데이터 조회

**Claude.ai 요청 예시**:
```
"ORDERS 테이블의 메타데이터를 보여줘"
```

**반환**: `unified_metadata.json` 전체 내용 (DB 스키마 + CSV 정보)

---

## 문제 해결

### 1. "ANTHROPIC_API_KEY 환경 변수가 설정되지 않았습니다"

**원인**: `.env` 파일에 API 키가 없음

**해결**:
```bash
# .env 파일 생성
copy .env.example .env

# .env 파일 열어서 다음 추가:
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

---

### 2. "Oracle 연결 실패: ORA-12541: TNS:no listener"

**원인**: Oracle DB 호스트/포트가 잘못됨

**해결**:
1. DB 접속 정보 확인
2. `register_database_credentials`로 재등록
3. 방화벽/네트워크 확인

---

### 3. "CSV 파일을 찾을 수 없습니다"

**원인**: CSV 파일 경로가 잘못됨

**확인**:
```
input/
  └── {DB_SID}/          # 대문자로 정확히 일치
      └── {SCHEMA}/      # 대문자로 정확히 일치
          ├── table_info.csv
          ├── column_info.csv
          └── code_values.csv
```

**해결**:
- DB_SID와 SCHEMA 이름이 대문자인지 확인
- 파일명 철자 확인

---

### 4. "선택된 테이블의 메타정보를 찾을 수 없습니다"

**원인**: `extract_and_integrate_metadata`를 실행하지 않음

**해결**:
```
"PROD_DB의 SCOTT 스키마 메타데이터를 추출해줘"
```

---

### 5. SQL 생성이 부정확함

**원인**: CSV 메타데이터가 불충분하거나 부정확함

**해결**:
1. `column_info.csv`의 `description`, `business_rule` 상세히 작성
2. `code_values.csv`에 모든 코드 값 정의
3. `table_info.csv`의 `business_purpose` 명확히 작성
4. 메타데이터 재통합:
   ```
   "메타데이터를 다시 추출해줘"
   ```

---

### 6. "SELECT 쿼리만 실행 가능합니다"

**원인**: INSERT/UPDATE/DELETE 시도

**해결**:
- 현재는 SELECT만 지원 (읽기 전용)
- 데이터 변경이 필요하면 DB 관리 도구 사용

---

### 7. 토큰 사용량이 너무 많음

**원인**: 테이블이 너무 많거나 칼럼이 많음

**현재 처리**:
- 2단계 LLM으로 이미 최적화됨
- Stage 1: 전체 테이블 요약만 전송 (경량)
- Stage 2: 선택된 5개 테이블만 상세 전송

**추가 최적화 방법**:
- `table_info.csv`의 설명을 간결하게 작성
- 불필요한 테이블은 CSV에서 제외

---

## 고급 활용

### 1. 복잡한 비즈니스 로직 쿼리

```
"VIP 고객 중에서 최근 3개월간 주문이 없지만
이전 1년간 월평균 구매액이 50만원 이상인 고객을 찾아줘"
```

→ MCP 서버가 복잡한 서브쿼리와 날짜 함수를 자동 생성

---

### 2. 상태 전이 추적

```
"주문 상태가 '결제완료'에서 '배송중'으로 변경된 지
3일 이상 지났지만 '배송완료'가 안 된 주문을 찾아줘"
```

→ `code_values.csv`의 `state_transition` 정보 활용

---

### 3. 월별 트렌드 분석

```
"최근 12개월간 월별 신규 고객 수와 평균 주문 금액 추이를 보여줘"
```

→ Oracle 날짜 함수 (TO_CHAR, ADD_MONTHS) 자동 사용

---

### 4. 다중 테이블 JOIN

```
"전자제품 카테고리 상품을 3개 이상 구매한 실버 등급 이상 고객의
연락처를 보여줘"
```

→ PRODUCTS, ORDER_ITEMS, ORDERS, CUSTOMERS 자동 JOIN

---

## 다음 단계

1. **실제 DB 연결 테스트**
   - 운영/개발 DB 접속 정보 등록
   - 메타데이터 추출 실행

2. **CSV 파일 작성**
   - 주요 테이블부터 작성
   - 팀원과 협업하여 업무 로직 반영

3. **자연어 쿼리 테스트**
   - 간단한 조회부터 시작
   - 복잡한 비즈니스 로직 단계적 테스트

4. **메타데이터 개선**
   - SQL 생성 결과를 보며 부족한 정보 추가
   - 반복적으로 CSV 파일 업데이트

---

## 지원 및 문의

- **GitHub Issues**: 버그 리포트 및 기능 제안
- **Documentation**: README.md, PROJECT_SUMMARY.md 참조
- **로그 확인**: MCP 서버 실행 로그에서 상세 에러 확인

---

**마지막 업데이트**: 2025-01-05

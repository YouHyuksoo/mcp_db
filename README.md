# 🗄️ Oracle Database MCP Server

**자연어로 Oracle Database를 조회하고 탐색하는 MCP 서버**

Claude AI와 Oracle Database를 연결하여 자연어 질의를 SQL로 변환하고 실행하는 Model Context Protocol (MCP) 서버입니다.

---

## ✨ 핵심 기능

### 1️⃣ 메타정보 통합 관리
- **자동 스키마 추출**: Oracle DB에서 테이블, 칼럼, PK, FK, 인덱스 자동 추출
- **비즈니스 의미 통합**: 사용자 제공 CSV로 한글 칼럼명, 설명, 코드값 추가
- **통합 메타데이터 생성**: DB 기술 정보 + 비즈니스 의미를 하나로 통합

### 2️⃣ 자연어 SQL 생성 (핵심 기능)
- **2단계 메타데이터 제공**: 대용량 메타정보 효율적 처리
  - **Stage 1**: 경량 테이블 요약 제공 → Claude가 관련 테이블 선택 (최대 5개)
  - **Stage 2**: 선택된 테이블의 상세 메타데이터 제공 → Claude가 정확한 SQL 생성
- **Claude Desktop이 직접 SQL 생성**: MCP 서버는 메타데이터만 제공, 추론은 Claude가 수행
- **Oracle SQL 문법**: 날짜 함수, 계층 쿼리, 분석 함수 지원
- **코드값 자동 이해**: 메타데이터에 코드값 의미 포함

### 3️⃣ 데이터베이스 탐색
- 테이블 목록 및 상세 구조 조회
- 프로시저/함수 목록 및 소스 코드 조회
- Primary Key, Foreign Key, Index 정보 확인
- 다중 Database/Schema 관리

---

## 🚀 빠른 시작

### 1단계: 환경 설정

```bash
# 가상환경 활성화 (이미 생성되어 있음)
cd D:\Project\mcp_db
venv\Scripts\activate

# 환경변수 설정 (선택 사항)
copy .env.example .env
# .env 파일을 열어 ENCRYPTION_KEY 입력 (DB 접속정보 암호화용)
```

### 2단계: Claude Desktop 설정

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "oracle-db": {
      "command": "D:\\Project\\mcp_db\\venv\\Scripts\\python.exe",
      "args": ["-m", "src.mcp_server"],
      "cwd": "D:\\Project\\mcp_db",
      "env": {
        "PYTHONPATH": "D:\\Project\\mcp_db"
      }
    }
  }
}
```

**설정 후 Claude Desktop 재시작**

### 3단계: 데이터베이스 등록

#### 방법 A: 자동 (tnsnames.ora 사용) - 추천! 🆕

1. **tnsnames.ora 로드**
```
"tnsnames.ora 파일을 로드해줘"
→ Tool: load_tnsnames("D:\app\hsyou\...\tnsnames.ora")
```

2. **사용 가능한 DB 확인**
```
"사용 가능한 데이터베이스 목록을 보여줘"
→ Tool: list_available_databases()
→ SOLUM, JSTECH, EDISON 등 94개 DB 표시
```

3. **DB 연결**
```
"SOLUM DB에 연결하고 싶어. 사용자는 scott, 비밀번호는 tiger123"
→ Tool: connect_database("SOLUM", "scott", "tiger123")
→ 연결 테스트 후 자동 저장
```

#### 방법 B: 수동 (직접 입력)

```
"PROD_DB 데이터베이스 접속 정보를 등록해줘.
호스트: db.company.com
포트: 1521
서비스명: PROD
사용자: scott
비밀번호: tiger123"
→ Tool: register_database_credentials()
```

### 4단계: CSV 메타데이터 작성

`input/PROD_DB/SCOTT/` 폴더에 3개 CSV 파일 작성:
- `table_info.csv` - 테이블 목적 및 활용 시나리오
- `column_info.csv` - 칼럼 한글명, 설명, 비즈니스 규칙
- `code_values.csv` - 코드 칼럼의 값별 의미

📖 자세한 양식은 `input/EXAMPLE_DB/SCOTT/` 예시 참조

### 5단계: 메타데이터 추출

Claude.ai에서:
```
"PROD_DB의 SCOTT 스키마 메타데이터를 추출하고 통합해줘"
```

### 6단계: 자연어로 조회!

Claude.ai에서:
```
"최근 1개월간 주문 금액이 100만원 이상인 VIP 고객의 주문 내역을 보여줘"
```

---

## 🛠️ 제공되는 14개 MCP Tools

### 데이터베이스 관리 (5개)
| Tool | 설명 |
|------|------|
| `register_database_credentials` | 수동: Oracle DB 접속 정보 직접 입력하여 저장 |
| `load_tnsnames` 🆕 | 자동: tnsnames.ora 파일 파싱하여 DB 목록 추출 |
| `list_available_databases` 🆕 | 자동: tnsnames에서 추출한 DB 목록 조회 |
| `connect_database` 🆕 | 자동: tnsnames DB에 사용자명/비밀번호로 연결 |
| `extract_and_integrate_metadata` | DB 스키마 추출 + CSV 통합 + 메타데이터 생성 |

### 데이터베이스 탐색 (6개)
| Tool | 설명 |
|------|------|
| `show_databases` | 등록된 데이터베이스 목록 조회 |
| `show_schemas` | 특정 DB의 스키마 목록 조회 |
| `show_tables` | 스키마의 테이블/뷰 목록 조회 |
| `describe_table` | 테이블 구조 (칼럼, PK, FK, 인덱스) 상세 조회 |
| `show_procedures` | 프로시저/함수 목록 조회 |
| `show_procedure_source` | 프로시저/함수 소스 코드 조회 |

### 자연어 SQL (핵심, 2개)
| Tool | 설명 |
|------|------|
| `get_table_summaries_for_query` ⭐ | Stage 1: 테이블 요약 제공 (Claude가 관련 테이블 선택) |
| `get_detailed_metadata_for_sql` ⭐ | Stage 2: 상세 메타데이터 제공 (Claude가 SQL 생성) |

### SQL 실행 (1개)
| Tool | 설명 |
|------|------|
| `execute_sql` | 직접 작성한 SQL 실행 |

### 메타정보 조회 (1개)
| Tool | 설명 |
|------|------|
| `get_table_metadata` | 특정 테이블의 통합 메타데이터 조회 |

## 📝 CSV 파일 양식

사용자는 다음 3개의 CSV 파일을 작성하여 비즈니스 메타데이터를 제공해야 합니다.

### 1. table_info.csv (테이블 목적 및 활용)

**위치**: `input/{DB_SID}/{SCHEMA}/table_info.csv`

**필수 칼럼**:
```csv
table_name,business_purpose,usage_scenario_1,usage_scenario_2,usage_scenario_3,related_tables
ORDERS,고객 주문 정보를 저장하고 주문 생명주기를 관리하는 핵심 테이블,일별/월별 매출 집계,배송 상태별 주문 조회,고객별 주문 이력 분석,CUSTOMERS|ORDER_ITEMS|SHIPMENTS
```

### 2. column_info.csv (칼럼 설명 및 규칙)

**위치**: `input/{DB_SID}/{SCHEMA}/column_info.csv`

**필수 칼럼**:
```csv
table_name,column_name,korean_name,description,business_rule,sample_values,unit,is_code_column,aggregation_functions,is_sensitive
ORDERS,ORDER_ID,주문번호,각 주문을 고유하게 식별하는 일련번호,시스템이 자동으로 채번하며 변경 불가,1001|1002|1003,,N,,N
ORDERS,STATUS,주문상태,주문의 현재 처리 단계를 나타내는 코드,01→02→03 또는 99로 상태 전이,01|02|03|99,,Y,,N
ORDERS,AMOUNT,주문금액,주문의 총 결제 금액,0보다 큰 양수 값만 허용,50000|120000|75000,원,N,SUM|AVG|MIN|MAX,N
```

### 3. code_values.csv (코드값 의미)

**위치**: `input/{DB_SID}/{SCHEMA}/code_values.csv`

**필수 칼럼**:
```csv
table_name,column_name,code_value,code_label,code_description,display_order,is_active,parent_code,state_transition
ORDERS,STATUS,01,주문접수,고객으로부터 주문이 접수된 초기 상태,1,Y,,02
ORDERS,STATUS,02,결제완료,결제가 정상적으로 완료된 상태,2,Y,01,03
ORDERS,STATUS,99,주문취소,고객 요청 또는 시스템에 의해 주문이 취소된 상태,99,Y,01|02,
```

📖 **상세 양식 및 작성 가이드**: `USAGE_GUIDE.md` 참조
📁 **예시 파일**: `input/EXAMPLE_DB/SCOTT/` 폴더

---

## 💬 사용 예시

### 📊 데이터베이스 탐색

**사용자**: "등록된 데이터베이스 목록을 보여줘"
- Tool: `show_databases()`
- 결과: 암호화되어 저장된 모든 DB 목록

**사용자**: "PROD_DB의 SCOTT 스키마에 어떤 테이블이 있어?"
- Tool: `show_tables("PROD_DB", "SCOTT")`
- 결과: 테이블 및 뷰 목록

**사용자**: "ORDERS 테이블 구조를 자세히 보여줘"
- Tool: `describe_table("PROD_DB", "SCOTT", "ORDERS")`
- 결과: 칼럼, PK, FK, 인덱스 정보

---

### ✨ 자연어 SQL 생성 (핵심 기능)

**사용자**: "최근 1개월간 주문 금액이 100만원 이상인 VIP 고객의 주문 내역을 보여줘"

**처리 흐름**:

1. **Stage 1**: Claude가 `get_table_summaries_for_query` Tool 호출
   - MCP 서버가 전체 테이블 요약 반환
   - Claude가 메타데이터 보고 관련 테이블 선택: `CUSTOMERS`, `ORDERS`

2. **Stage 2**: Claude가 `get_detailed_metadata_for_sql` Tool 호출
   - 파라미터: `table_names="CUSTOMERS,ORDERS"`
   - MCP 서버가 선택된 2개 테이블의 상세 메타데이터 반환
   - Claude가 메타데이터 보고 SQL 생성:
   ```sql
   SELECT o.ORDER_ID, o.ORDER_DATE, c.CUSTOMER_NAME, o.AMOUNT
   FROM SCOTT.ORDERS o
   JOIN SCOTT.CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID
   WHERE c.GRADE = 'VIP'
     AND o.ORDER_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -1)
     AND o.AMOUNT >= 1000000
   ORDER BY o.ORDER_DATE DESC
   ```

3. **SQL 실행**: Claude가 `execute_sql` Tool 호출
   - MCP 서버가 SQL 실행 후 결과 반환

---

**핵심**: MCP 서버는 메타데이터만 제공하고, Claude Desktop이 직접 테이블 선택 및 SQL 생성을 수행합니다.

## 🏗️ 프로젝트 구조

```
D:\Project\mcp_db/
├─ input/                          # 사용자 제공 CSV 파일
│  └─ EXAMPLE_DB/
│     └─ SCOTT/
│        ├─ table_info.csv         # 테이블 목적 및 활용 시나리오
│        ├─ column_info.csv        # 칼럼 한글명, 설명, 규칙
│        └─ code_values.csv        # 코드값 의미 정의
│
├─ metadata/                       # 통합 메타데이터 (자동 생성)
│  └─ {DB_SID}/
│     └─ {SCHEMA}/
│        ├─ table_summaries.json   # 경량 테이블 요약 (Stage 1용)
│        └─ {TABLE}/
│           └─ unified_metadata.json  # 통합 메타데이터 (DB+CSV)
│
├─ credentials/                    # 암호화된 DB 접속 정보
│  └─ {DB_SID}.json.enc           # Fernet 암호화
│
├─ src/                            # 소스 코드
│  ├─ mcp_server.py               # MCP 서버 메인 (12개 Tools)
│  ├─ oracle_connector.py         # Oracle DB 연결 및 스키마 추출
│  ├─ metadata_manager.py         # 메타데이터 통합 관리
│  ├─ csv_parser.py               # CSV 파싱 (3종)
│  ├─ two_stage_llm.py            # 2단계 LLM 처리 (핵심)
│  ├─ sql_executor.py             # SQL 실행 및 검증
│  └─ credentials_manager.py      # 접속정보 암호화
│
├─ venv/                          # Python 가상환경
├─ requirements.txt               # 의존성
├─ .env.example                   # 환경변수 템플릿
├─ README.md                      # 프로젝트 개요
└─ USAGE_GUIDE.md                 # 상세 사용 가이드
```

---

## 🎯 핵심 특징

### ✅ 대용량 메타정보 처리
- **2단계 메타데이터 제공**으로 100개 이상 테이블 처리
- Stage 1: 경량 요약 제공 → Claude가 관련 테이블 선택 (토큰 절약)
- Stage 2: 선택된 테이블만 상세 메타데이터 제공 (정확도 향상)
- **외부 API 호출 없음**: Claude Desktop이 직접 추론 수행

### ✅ 비즈니스 컨텍스트 통합
- DB 기술 정보 + 사용자 제공 비즈니스 의미
- 한글 칼럼명, 비즈니스 규칙, 코드값 의미 통합
- Claude가 업무 로직을 이해하고 정확한 SQL 생성

### ✅ Oracle SQL 전문화
- Oracle 날짜 함수 (TRUNC, ADD_MONTHS, TO_CHAR)
- 계층 쿼리, 분석 함수 지원
- Schema.Table 형식 자동 적용

### ✅ 보안 및 안정성
- Fernet 암호화로 DB 접속 정보 저장
- SELECT 쿼리만 허용 (데이터 변경 방지)
- 결과 행 수 제한 (기본 1000행)
- SQL Injection 기본 방지

---

## 📦 기술 스택

| 카테고리 | 기술 |
|---------|------|
| **언어** | Python 3.9+ |
| **DB 드라이버** | oracledb 2.0+ (cx_Oracle 대체) |
| **MCP** | FastMCP SDK |
| **LLM** | Claude Desktop (외부 API 호출 없음) |
| **데이터 처리** | pandas |
| **암호화** | cryptography (Fernet) |
| **환경 관리** | python-dotenv |

---

## 🔧 문제 해결

### "ENCRYPTION_KEY 환경 변수가 설정되지 않았습니다"
```bash
# .env 파일 생성 및 암호화 키 추가
copy .env.example .env
# 암호화 키 생성:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# 출력된 키를 .env 파일에 ENCRYPTION_KEY= 로 추가
```

### "Oracle 연결 실패"
- DB 호스트/포트 확인
- 방화벽 설정 확인
- `register_database_credentials`로 재등록

### "CSV 파일을 찾을 수 없습니다"
- 경로 확인: `input/{DB_SID}/{SCHEMA}/`
- DB_SID와 SCHEMA 이름 대문자 확인
- 파일명 철자 확인 (table_info.csv, column_info.csv, code_values.csv)

### "선택된 테이블의 메타정보를 찾을 수 없습니다"
```
"메타데이터를 다시 추출해줘"
→ extract_and_integrate_metadata 재실행
```

### SQL 생성이 부정확함
- CSV 파일의 설명을 더 상세히 작성
- `business_rule` 칼럼에 비즈니스 로직 명시
- `code_values.csv`에 모든 코드값 정의
- 메타데이터 재통합

📖 **더 많은 문제 해결 방법**: `USAGE_GUIDE.md` 참조

---

## 📚 문서

- **README.md** (현재 문서): 프로젝트 개요 및 빠른 시작
- **USAGE_GUIDE.md**: 상세 사용 가이드 및 워크플로우
- **input/EXAMPLE_DB/SCOTT/**: CSV 파일 작성 예시

---

## 📄 라이선스

MIT License

---

## 🎉 다음 단계

1. ✅ 환경 설정 및 MCP 서버 연동
2. ✅ Oracle DB 접속 정보 등록
3. ✅ CSV 메타데이터 작성
4. ✅ 메타데이터 추출 및 통합
5. 🚀 **자연어로 데이터베이스 조회 시작!**

---

**Made with ❤️ for Oracle Database + Claude AI**

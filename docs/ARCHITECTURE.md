# 🏗️ 아키텍처

## 개요

Oracle Database MCP Server는 Claude Desktop이 자연어 질의를 Oracle SQL로 변환하고 실행할 수 있도록 지원하는 MCP(Model Context Protocol) 서버입니다.

---

## 핵심 설계 원칙

### MCP 서버의 역할
- ✅ **메타데이터 제공**: DB 스키마 정보, 비즈니스 의미 제공
- ✅ **SQL 실행**: Claude가 생성한 SQL 실행 및 결과 반환
- ✅ **DB 관리**: 연결, 인증, 탐색 기능 제공
- ❌ **LLM 추론 수행 안함**: SQL 생성은 Claude Desktop이 담당

---

## 2단계 메타데이터 제공 방식

대용량 데이터베이스의 경우 모든 테이블의 메타데이터를 한 번에 제공하면 컨텍스트가 너무 커집니다. 이를 해결하기 위해 2단계 방식을 사용합니다.

### 🔹 Stage 1: 테이블 선택

```
사용자: "지난 1개월간 VIP 고객 주문 내역 보여줘"
    ↓
Claude Desktop이 get_table_summaries_for_query 호출
    ↓
MCP 서버: 모든 테이블의 경량 요약 정보 제공
    - 테이블명, 한글명, 설명, 주요 칼럼 목록만
    ↓
Claude Desktop이 메타데이터 분석
    ↓
Claude: "CUSTOMERS, ORDERS 테이블이 필요함"
```

**제공 정보 (경량)**:
```json
{
  "table_name": "CUSTOMERS",
  "table_name_kr": "고객",
  "description": "고객 마스터 테이블",
  "key_columns": ["CUSTOMER_ID", "CUSTOMER_NAME", "GRADE"],
  "record_count": 15000
}
```

### 🔹 Stage 2: SQL 생성

```
Claude Desktop이 get_detailed_metadata_for_sql 호출
테이블 목록: ["CUSTOMERS", "ORDERS"]
    ↓
MCP 서버: 선택된 테이블의 상세 메타데이터 제공
    - 모든 칼럼, 타입, 제약조건, 관계, 코드값 등
    ↓
Claude Desktop이 정확한 SQL 생성
    ↓
Claude Desktop이 execute_sql 호출
    ↓
MCP 서버: SQL 실행 및 결과 반환
```

**제공 정보 (상세)**:
```json
{
  "table_name": "CUSTOMERS",
  "columns": [
    {
      "column_name": "GRADE",
      "data_type": "VARCHAR2(10)",
      "column_name_kr": "등급",
      "description": "고객 등급",
      "code_values": [
        {"code": "VIP", "name": "VIP고객"},
        {"code": "GOLD", "name": "골드고객"}
      ]
    }
  ],
  "primary_keys": ["CUSTOMER_ID"],
  "foreign_keys": [...],
  "indexes": [...]
}
```

---

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                      사용자 (자연어 질의)                        │
└────────────────────────────┬────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                     Claude Desktop                          │
│  - 자연어 이해                                                 │
│  - MCP Tool 호출 결정                                          │
│  - SQL 생성 (Stage 1, 2 기반)                                  │
│  - 결과 해석 및 응답                                             │
└────────────────────────────┬────────────────────────────────┘
                             ↓ MCP Protocol
┌─────────────────────────────────────────────────────────────┐
│                  Oracle NL-SQL MCP Server                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ MCP Server (mcp_server.py)                           │  │
│  │  - Tool 정의 및 핸들러                                   │  │
│  │  - Stage 1: get_table_summaries_for_query            │  │
│  │  - Stage 2: get_detailed_metadata_for_sql            │  │
│  │  - execute_sql                                        │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Metadata Manager                                      │  │
│  │  - 스키마 추출 (metadata_manager.py)                    │  │
│  │  - 공통 메타데이터 통합 (common_metadata_manager.py)     │  │
│  │  - 통합 메타데이터 저장/조회                              │  │
│  └───────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Oracle Connector                                      │  │
│  │  - DB 연결 관리 (oracle_connector.py)                  │  │
│  │  - SQL 실행 (sql_executor.py)                         │  │
│  │  - 접속정보 암호화 (credentials_manager.py)             │  │
│  │  - tnsnames.ora 파싱 (tnsnames_parser.py)             │  │
│  └───────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│                      Oracle Database                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 메타데이터 통합 흐름

```
1. DB 스키마 추출
   ↓
   [Oracle Database]
   ↓ ALL_TABLES, ALL_TAB_COLUMNS, ALL_CONSTRAINTS 등 조회
   ↓
   {
     "table_name": "CUSTOMERS",
     "columns": [
       {"column_name": "CUSTOMER_ID", "data_type": "NUMBER(10)"}
     ],
     "primary_keys": ["CUSTOMER_ID"]
   }

2. 공통 메타데이터 로드
   ↓
   [common_metadata/*.csv]
   ↓ CSV 파싱
   ↓
   {
     "common_columns": {...},
     "code_definitions": {...},
     "table_info": {...}
   }

3. 통합
   ↓
   [Metadata Integration]
   ↓ Merge
   ↓
   {
     "table_name": "CUSTOMERS",
     "table_name_kr": "고객",
     "description": "고객 마스터 테이블",
     "columns": [
       {
         "column_name": "CUSTOMER_ID",
         "column_name_kr": "고객ID",
         "data_type": "NUMBER(10)",
         "description": "고객 고유 식별자"
       }
     ]
   }

4. 저장
   ↓
   [metadata/{DB_SID}/{SCHEMA}/{TABLE}/unified_metadata.json]
```

---

## 디렉토리 구조 및 데이터 흐름

```
common_metadata/              ← 사용자 작성 (CSV)
└── SMVNPDBext/
    ├── common_columns.json   ← CSV에서 변환
    ├── code_definitions.json ← CSV에서 변환
    └── INFINITY21_JSMES/
        └── table_info.json   ← CSV에서 변환

metadata/                     ← 자동 생성 (JSON)
└── SMVNPDBext/
    └── INFINITY21_JSMES/
        └── CUSTOMERS/
            └── unified_metadata.json  ← DB 스키마 + 공통 메타데이터

credentials/                  ← 자동 생성 (암호화)
└── SMVNPDBext.json.enc       ← AES-256 암호화
```

---

## 기술 스택

| 구성 요소 | 기술 |
|----------|------|
| 프로토콜 | MCP (Model Context Protocol) |
| 언어 | Python 3.12+ |
| DB 드라이버 | cx_Oracle (Oracle Instant Client) |
| 암호화 | cryptography (AES-256) |
| 메타데이터 | JSON, CSV |
| 프레임워크 | MCP Python SDK |

---

## 보안 고려사항

1. **접속 정보 암호화**
   - AES-256-GCM 사용
   - `.env`의 `ENCRYPTION_KEY` 필수
   - `credentials/` 폴더에 암호화 저장

2. **민감 정보 관리**
   - `.gitignore`에 `.env`, `credentials/`, `metadata/` 포함
   - 비밀번호는 메모리에서만 처리, 로그에 기록 안함

3. **SQL Injection 방어**
   - 파라미터 바인딩 사용
   - 사용자 입력 검증

---

## 확장성

### 다른 데이터베이스 지원
현재 Oracle 전용이지만, 다음과 같이 확장 가능:

1. `oracle_connector.py` → `db_connector_base.py` (추상 클래스)
2. `oracle_connector.py`, `postgres_connector.py` 구현
3. 설정 파일에서 DB 타입 지정

### 추가 메타데이터
CSV 파일에 필드 추가:
- `business_rules`: 비즈니스 규칙
- `data_quality`: 데이터 품질 정보
- `sample_queries`: 샘플 쿼리

---

## 성능 최적화

1. **메타데이터 캐싱**
   - 추출된 메타데이터는 JSON 파일로 저장
   - 재추출 불필요

2. **2단계 방식**
   - 필요한 테이블만 상세 메타데이터 로드
   - 컨텍스트 크기 최소화

3. **연결 풀링**
   - cx_Oracle의 세션 풀 활용 가능 (향후)

---

## 참고 자료

- [MCP 공식 문서](https://modelcontextprotocol.io)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [cx_Oracle 문서](https://cx-oracle.readthedocs.io/)

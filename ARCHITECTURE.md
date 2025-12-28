# Oracle NL-SQL MCP Server - 아키텍처

**버전**: 3.0
**최종 수정**: 2025-01-09

---

## 🎯 핵심 설계 원칙

### MCP Server는 Backend 없이 완전 독립 동작

**MCP Server**: 완전 독립 - SQL 생성 및 실행의 모든 것
**Backend Server**: 선택적 관리 도구 - 데이터 학습 및 관리
**공유 디렉토리**: `data/` - MCP와 Backend가 공유

---

## 📐 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Desktop                           │
│                  (사용자 자연어 질문)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server                                │
│               (Backend 없이 독립 동작)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ 1. data/credentials/ → DB 접속 정보 읽기             │   │
│  │ 2. data/vector_db/ → 관련 테이블 검색 (의미 검색)    │   │
│  │ 3. LLM → SQL 생성                                   │   │
│  │ 4. Oracle DB 접속 → SQL 실행                        │   │
│  │ 5. 결과 반환                                        │   │
│  └──────────────────────────────────────────────────────┘   │
└───────────────┬──────────────────┬──────────────────────────┘
                │                  │
                │ ① Credentials    │ ② Metadata 검색
                │    (파일 읽기)    │    (ChromaDB 읽기)
                ▼                  ▼
        ┌──────────────┐  ┌──────────────────┐
        │    data/     │  │  data/vector_db/ │
        │ credentials/ │  │   (ChromaDB)     │
        │              │  │                  │
        │ • 암호화된   │  │ • Table Metadata │
        │   DB 접속정보│  │ • Embeddings     │
        │ • AES-256    │  │ • 의미 검색      │
        └──────▲───────┘  └────────▲─────────┘
               │                   │
               │ Backend는 학습용   │
               │ (선택적 실행)      │
               │                   │
        ┌──────┴───────────────────┴─────────┐
        │      Backend Server (선택적)        │
        │  • Web UI로 DB 등록                │
        │  • CSV → Vector DB 학습            │
        │  • 대시보드 통계                   │
        │  • 학습 완료 후 종료 가능           │
        └────────────────────────────────────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  Oracle DB   │
                  │              │
                  │ • 실제 데이터 │
                  │ • Schema     │
                  └──────────────┘
```

---

## 🔧 MCP Server 역할

### 핵심 원칙: Backend 없이 완전 독립 동작

**✅ MCP Server가 하는 일:**

1. **Credentials 직접 읽기**
   - `data/credentials/{db_sid}.json.enc` 파일 직접 읽기
   - AES-256 복호화
   - Backend API 호출 없음

2. **Vector DB 직접 검색 (읽기 전용)**
   - `data/vector_db/` ChromaDB 파일 직접 읽기
   - 의미 기반 테이블 검색
   - Backend 없이 독립 동작

3. **SQL 생성**
   - Vector DB에서 찾은 테이블 메타데이터 활용
   - LLM에게 컨텍스트 제공
   - Oracle SQL 생성

4. **DB 접속 및 SQL 실행**
   - OracleConnector로 DB 접속
   - SQL 실행 및 결과 반환
   - 트랜잭션 관리

5. **DB 상태 조회**
   - 스키마 목록 조회
   - 테이블 목록 조회
   - 테이블 구조 조회
   - 인덱스/제약조건 정보

**❌ MCP Server가 하지 않는 일:**
- Vector DB 쓰기 (임베딩 생성)
- Backend API 호출

### MCP Tools (17개) - SQL 생성/실행 전용

| Tool | 설명 | 데이터 소스 |
|------|------|------------|
| **DB 연결 관리 (3개)** | | |
| `register_database_credentials` | DB 접속 정보 등록 | data/credentials/ |
| `list_available_databases` | tnsnames에서 파싱된 DB 목록 | 캐시 |
| `connect_database` | DB 연결 (tnsnames 기반) | data/credentials/ |
| **DB 정보 조회 (7개)** | | |
| `show_databases` | 등록된 DB 목록 | data/credentials/ |
| `show_connection_status` | 접속 가능 DB 상태 | data/credentials/ |
| `show_schemas` | 스키마 목록 | Oracle DB |
| `show_tables` | 테이블 목록 | Oracle DB |
| `describe_table` | 테이블 구조 | Oracle DB |
| `show_procedures` | 프로시저 목록 | Oracle DB |
| `show_procedure_source` | 프로시저 소스 코드 | Oracle DB |
| **SQL 실행 및 검색 (5개)** | | |
| `execute_sql` | SQL 실행 | Oracle DB |
| `get_table_summaries_for_query` | Stage 1: 테이블 검색 (의미 검색) | data/vector_db/ |
| `check_vectordb_status` | Vector DB 상태 확인 | data/vector_db/ |
| `get_detailed_metadata_for_sql` | Stage 2: 상세 메타정보 | data/vector_db/ |
| `get_table_metadata` | 특정 테이블 통합 메타데이터 | data/vector_db/ |
| **SQL 규칙 관리 (2개)** | | |
| `view_sql_rules` | SQL 작성 규칙 조회 | data/sql_rules.md |
| `update_sql_rules` | SQL 작성 규칙 업데이트 | data/sql_rules.md |

**⚠️ Backend로 이관된 기능**:
- DB 관리 (`delete_database`, `load_tnsnames`) → Backend Web UI
- CSV 업로드 (`import_*_csv`) → Backend Web UI
- 공통 메타데이터 관리 (`register_common_columns`, `register_code_values`, `view_common_metadata`) → Backend Web UI
- 메타데이터 통합 (`generate_csv_from_schema`, `extract_and_integrate_metadata`) → Backend Web UI

---

## 🖥️ Backend Server 역할

### 핵심 원칙: 선택적 관리 도구 (학습 전용)

**✅ Backend Server가 하는 일:**

1. **Database Credentials 관리 (Web UI)**
   - 등록: Web UI → `data/credentials/{sid}.json.enc` 저장
   - 조회: Web UI로 목록 확인
   - 삭제: 파일 삭제
   - MCP는 파일을 직접 읽음 (API 호출 없음)

2. **Vector DB 학습 (Web UI)**
   - CSV 업로드
   - 임베딩 생성 (sentence-transformers)
   - `data/vector_db/` ChromaDB에 저장
   - MCP는 ChromaDB를 직접 읽음

3. **TNSNames 관리 (Web UI)**
   - tnsnames.ora 파싱
   - DB 목록 추출
   - 편리한 등록

4. **대시보드 및 통계**
   - 등록된 DB 목록
   - Vector DB 통계
   - 학습 현황

5. **PowerBuilder 파싱 (향후)**
   - 레거시 코드 분석
   - 테이블 연관 관계 추출

**❌ Backend Server가 하지 않는 일:**
- SQL 실행
- MCP에게 API 제공 (MCP는 파일 직접 읽기)
- 실시간 DB 조회

**Backend는 학습 완료 후 종료 가능!**

### Backend API Endpoints (Web UI용)

| Endpoint | Method | 설명 | 결과 저장 위치 |
|----------|--------|------|--------------|
| **Database Management** | | | |
| `/api/v1/databases/list` | GET | 등록된 DB 목록 | - |
| `/api/v1/databases/register` | POST | DB 등록 | data/credentials/ |
| `/api/v1/databases/{sid}` | DELETE | DB 삭제 | data/credentials/ |
| **TNSNames** | | | |
| `/api/v1/tnsnames/parse` | POST | tnsnames.ora 파싱 | - |
| `/api/v1/tnsnames/list` | GET | 파싱된 DB 목록 | - |
| `/api/v1/databases/register-from-tnsnames/{sid}` | POST | tnsnames로 등록 | data/credentials/ |
| **Metadata Management** | | | |
| `/api/v1/metadata/upload/csv` | POST | CSV 업로드 | data/vector_db/ |
| `/api/v1/metadata/stats` | GET | Vector DB 통계 | - |
| **SQL Rules Management** | | | |
| `/api/v1/sql-rules/view` | GET | SQL 규칙 조회 | - |
| `/api/v1/sql-rules/update` | POST | SQL 규칙 업데이트 | data/sql_rules.md |
| `/api/v1/sql-rules/backups` | GET | 백업 목록 조회 | - |
| `/api/v1/sql-rules/restore/{file}` | POST | 백업에서 복원 | data/sql_rules.md |
| `/api/v1/sql-rules/template` | GET | 규칙 템플릿 | - |
| **Dashboard** | | | |
| `/api/v1/dashboard/overview` | GET | 전체 통계 | - |
| **Health** | | | |
| `/api/health` | GET | 서버 상태 | - |

---

## 💾 공유 데이터 디렉토리: `data/`

### 구조

```
data/
├── credentials/                    # DB 접속 정보 (암호화)
│   ├── MYDB.json.enc              # Backend 쓰기, MCP 읽기
│   ├── PROD.json.enc
│   └── TEST.json.enc
│
├── vector_db/                      # ChromaDB (메타데이터)
│   ├── chroma.sqlite3              # Backend 쓰기, MCP 읽기
│   ├── *.parquet                   # 임베딩 벡터
│   └── ...
│
├── sql_rules.md                    # SQL 작성 규칙
│                                   # Backend 쓰기, MCP 읽기
│
└── sql_rules_backups/              # SQL 규칙 백업
    ├── sql_rules_20250109_120000.md
    ├── sql_rules_20250109_130000.md
    └── ...
```

### Credentials 파일 형식

```json
// data/credentials/MYDB.json.enc (암호화됨)
// 복호화 후:
{
  "host": "localhost",
  "port": 1521,
  "service_name": "ORCL",
  "user": "scott",
  "password": "tiger"  // 암호화되어 저장됨
}
```

### Vector DB 구조 (Enhanced)

```
Collections:
- oracle_metadata            # 테이블 메타데이터
  ├── id: {database_sid}.{schema_name}.{table_name}
  ├── embedding: [384 dimensions]
  ├── document: 검색용 요약 텍스트
  │   "[MYDB.SALES] CUSTOMERS (고객)
  │    설명: 고객 정보 관리 테이블
  │    핵심 컬럼: CUSTOMER_ID (고객ID), CUSTOMER_TYPE (고객유형)...
  │    비즈니스 로직: VIP 고객 20% 할인...
  │    연관 테이블: ORDERS (주문), CUSTOMER_ADDRESSES (배송지)..."
  │
  └── metadata: 구조화된 상세 정보
      ├── database_sid: "MYDB"           # ★ 필수 검색 필터
      ├── schema_name: "SALES"           # ★ 필수 검색 필터
      ├── table_name: "CUSTOMERS"
      ├── korean_name: "고객"
      ├── description: "고객 정보 관리 테이블"
      ├── column_count: 15
      ├── has_primary_key: true
      ├── has_foreign_keys: true
      ├── key_columns: [                 # JSON string
      │     {
      │       "name": "CUSTOMER_ID",
      │       "korean_name": "고객ID",
      │       "data_type": "NUMBER(10)",
      │       "is_pk": true,
      │       "nullable": false,
      │       "description": "고객 고유 식별자"
      │     },
      │     {
      │       "name": "CUSTOMER_TYPE",
      │       "korean_name": "고객유형",
      │       "data_type": "VARCHAR2(10)",
      │       "code_values": ["VIP", "GOLD", "SILVER"],
      │       "description": "고객 등급"
      │     }
      │   ]
      ├── related_tables: [              # JSON string
      │     {
      │       "table_name": "ORDERS",
      │       "korean_name": "주문",
      │       "relationship_type": "1:N",
      │       "foreign_key": "CUSTOMER_ID",
      │       "description": "고객의 주문 내역"
      │     }
      │   ]
      ├── business_rules: [              # JSON string
      │     {
      │       "rule": "VIP 고객 할인",
      │       "description": "VIP 고객은 전 품목 20% 할인"
      │     }
      │   ]
      ├── indexes: [                     # JSON string (optional)
      │     {
      │       "name": "PK_CUSTOMERS",
      │       "type": "PRIMARY KEY",
      │       "columns": ["CUSTOMER_ID"]
      │     }
      │   ]
      └── updated_at: "2025-01-09T12:00:00"
```

### Vector DB 검색 (필수 필터링)

```python
# ★ 중요: database_sid와 schema_name은 항상 필터 조건으로 사용
results = collection.query(
    query_texts=["고객 정보"],
    n_results=10,
    where={
        "database_sid": "MYDB",      # ★ 필수
        "schema_name": "SALES"       # ★ 필수
    }
)

# 다중 DB 환경에서 잘못된 DB의 테이블을 찾는 것 방지!
```

### 접근 방식

**MCP Server:**
- **Credentials**: `CredentialsManager(credentials_dir="data/credentials")` → 파일 직접 읽기
- **Vector DB**: `chromadb.PersistentClient(path="data/vector_db")` → 읽기 전용

**Backend Server:**
- **Credentials**: `CredentialsManager(credentials_dir="data/credentials")` → 파일 쓰기
- **Vector DB**: `chromadb.PersistentClient(path="data/vector_db")` → 읽기/쓰기

---

## 🔄 워크플로우

### 1. 초기 설정 (최초 1회)

```bash
# 1. Backend 시작 (학습용)
cd backend
python -m uvicorn app.main:app --reload

# 2. Frontend 시작 (선택)
cd frontend
npm run dev

# 3. Web UI 접속
# http://localhost:3000

# 4. DB 등록
#    - tnsnames.ora 파싱 후 등록
#    - 또는 수동 등록
#    → data/credentials/{sid}.json.enc 생성

# 5. CSV 메타데이터 업로드
#    → data/vector_db/ 학습

# 6. Backend 종료
#    Ctrl+C

# 7. MCP는 계속 동작 (data/ 폴더만 읽음)
```

### 2. 일상 사용 (Backend 불필요)

```
사용자: "지난 1개월간 생산 실적을 라인별로 집계해줘"
   ↓
Claude Desktop → MCP Server
   ↓
1️⃣ data/credentials/PROD.json.enc 읽기
   → DB 접속 정보 획득
   ↓
2️⃣ data/vector_db/ 검색 (직접 접근)
   → "생산 실적", "라인" 관련 테이블 찾기
   → PRODUCTION_RESULTS, LINE_MASTER 등 발견
   ↓
3️⃣ LLM에게 컨텍스트 제공
   → 테이블 구조, 칼럼 정보, 관계
   ↓
4️⃣ SQL 생성
   SELECT l.line_name,
          SUM(p.quantity) as total_qty
   FROM PRODUCTION_RESULTS p
   JOIN LINE_MASTER l ON p.line_id = l.line_id
   WHERE p.prod_date >= ADD_MONTHS(SYSDATE, -1)
   GROUP BY l.line_name
   ↓
5️⃣ Oracle DB 접속 (획득한 Credentials 사용)
   ↓
6️⃣ SQL 실행 및 결과 반환
   ↓
Claude Desktop → 사용자에게 결과 표시

※ Backend는 꺼져있어도 됨!
```

### 3. 메타데이터 추가/수정 (필요시만)

```bash
# Backend 시작
cd backend
python -m uvicorn app.main:app --reload

# Web UI에서 CSV 업로드
# → data/vector_db/ 자동 업데이트

# Backend 종료
# MCP는 계속 동작
```

---

## 📁 디렉토리 구조

```
mcp_db/
├── mcp/                              # MCP Server (독립 동작)
│   ├── mcp_server.py                 # 메인 서버 (15 tools)
│   ├── vector_db_client.py           # Vector DB 직접 접근
│   ├── oracle_connector.py           # Oracle DB 연결
│   ├── sql_executor.py               # SQL 실행
│   ├── credentials_manager.py        # Credentials 파일 읽기
│   └── tnsnames_parser.py            # TNSNames 파싱
│
├── backend/                          # Backend Server (학습 전용)
│   ├── app/
│   │   ├── main.py                   # FastAPI 메인
│   │   ├── api/
│   │   │   ├── databases.py          # DB 관리 API
│   │   │   ├── tnsnames.py           # TNSNames API
│   │   │   ├── metadata.py           # 메타데이터 API
│   │   │   └── dashboard.py          # 대시보드 API
│   │   ├── core/
│   │   │   ├── vector_store.py       # Vector DB 관리
│   │   │   ├── embedding_service.py  # 임베딩 생성
│   │   │   └── tnsnames_instance.py  # TNSNames 싱글톤
│   │   └── models/
│   │       ├── database.py
│   │       ├── metadata.py
│   │       └── dashboard.py
│   └── requirements.txt
│
├── frontend/                         # Frontend (Next.js)
│   ├── app/
│   │   ├── page.tsx                  # 대시보드
│   │   ├── databases/                # DB 관리 페이지
│   │   └── upload/                   # 메타데이터 업로드
│   └── components/
│
├── data/                             # 공유 데이터 디렉토리 ★★★
│   ├── credentials/                  # Backend 쓰기, MCP 읽기
│   │   └── {db_sid}.json.enc
│   └── vector_db/                    # Backend 쓰기, MCP 읽기
│       ├── chroma.sqlite3
│       └── *.parquet
│
├── .env                              # 환경 변수 (ENCRYPTION_KEY)
├── requirements.txt                  # MCP 의존성
├── ARCHITECTURE.md                   # 이 문서
└── README.md                         # 프로젝트 소개
```

---

## 🔐 보안

### Credentials 암호화

```python
# .env
ENCRYPTION_KEY=your-32-byte-key-here

# MCP와 Backend 모두 동일한 키 사용
# data/credentials/ 폴더는 파일 권한 제어 (600)

# 저장 (Backend)
credentials_manager.save_credentials(
    database_sid="MYDB",
    credentials={
        "host": "localhost",
        "port": 1521,
        "service_name": "ORCL",
        "user": "scott",
        "password": "tiger"
    }
)
# → data/credentials/MYDB.json.enc 생성

# 읽기 (MCP)
creds = credentials_manager.load_credentials("MYDB")
# → data/credentials/MYDB.json.enc 복호화
```

### Vector DB 보호

```python
# MCP: 읽기 전용
chromadb.PersistentClient(
    path="data/vector_db",
    settings=Settings(allow_reset=False)
)

# Backend: 읽기/쓰기
chromadb.PersistentClient(
    path="data/vector_db"
)
```

### 백업 전략

```bash
# Credentials 백업 (암호화된 상태)
tar -czf credentials_backup.tar.gz data/credentials/

# Vector DB 백업
tar -czf vectordb_backup.tar.gz data/vector_db/

# 복구
tar -xzf credentials_backup.tar.gz
tar -xzf vectordb_backup.tar.gz
```

---

## ⚡ 성능 최적화

### Vector DB 검색 속도

| 테이블 수 | 검색 시간 | 메모리 | MCP 독립 동작 |
|----------|----------|--------|--------------|
| 100 | <50ms | ~50MB | ✅ |
| 1,000 | <100ms | ~200MB | ✅ |
| 10,000 | <500ms | ~1GB | ✅ |
| 100,000 | <2s | ~5GB | ✅ |

### 캐싱 전략

**MCP Server:**
- DB Connector 캐싱 (연결 재사용)
- Vector DB Client 싱글톤
- Credentials 캐싱 (메모리)

**Backend Server:**
- TNSNames 파싱 결과 캐싱
- Embedding 모델 싱글톤

---

## 🚀 확장성

### 대용량 데이터 (100만 테이블+)

현재 ChromaDB 대신:
- **Qdrant**: 분산 Vector DB
- **Milvus**: GPU 가속 지원
- **Pinecone**: 클라우드 서비스

### 멀티 테넌시

```
data/
├── credentials/
│   ├── tenant1_db1.json.enc
│   ├── tenant1_db2.json.enc
│   ├── tenant2_db1.json.enc
│   └── ...
└── vector_db/
    └── chroma.sqlite3
    # 또는 테넌트별 분리:
    ├── tenant1/
    └── tenant2/
```

---

## 📊 모니터링

### MCP Server

```python
# 로그 위치
~/.config/claude/logs/mcp-server-oracle-nlsql.log

# 상태 확인 (MCP Tool)
Tool: check_vector_db_status
Tool: list_registered_databases
```

### Backend Server

```bash
# Health Check
curl http://localhost:8000/api/health

# Vector DB 통계
curl http://localhost:8000/api/v1/metadata/stats
```

---

## 🐛 트러블슈팅

### MCP가 Credentials 못 찾음

```bash
# data/credentials/ 확인
ls -la data/credentials/

# .env 확인 (ENCRYPTION_KEY 동일한지)
cat .env

# 파일 권한 확인
chmod 600 data/credentials/*.enc
```

### Vector DB 초기화 안됨

```bash
# data/vector_db/ 확인
ls -la data/vector_db/

# Backend로 재학습
cd backend
python -m uvicorn app.main:app --reload
# Web UI에서 CSV 재업로드
```

### MCP가 독립 동작 안함

```bash
# Backend 끄고 MCP 테스트
# Backend 종료: Ctrl+C

# Claude에게 질문:
"등록된 데이터베이스 목록 보여줘"
"Vector DB 상태 확인해줘"

# MCP가 data/ 폴더만 읽으면 정상
```

---

## 📚 핵심 개념 정리

### 1. MCP는 완전 독립
- Backend API 호출 **없음**
- `data/` 폴더만 읽기
- Backend가 꺼져도 동작

### 2. Backend는 학습 도구
- Web UI로 편리한 관리
- CSV → Vector DB 변환
- 학습 후 종료 가능

### 3. data/ 폴더로 공유
- Backend: 쓰기 (학습)
- MCP: 읽기 (운영)
- 파일 시스템으로 통신

### 4. 보안 분리
- Credentials: 암호화 파일 (AES-256)
- Vector DB: 메타데이터만 (민감정보 없음)

---

## 📚 참고 자료

- [MCP Protocol](https://modelcontextprotocol.io/)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Oracle SQL Reference](https://docs.oracle.com/en/database/oracle/oracle-database/21/sqlrf/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)

---

**최종 업데이트**: 2025-01-09
**아키텍처 버전**: 3.0 Final
**핵심 원칙**: MCP는 완전 독립, Backend는 선택적 관리 도구, data/ 폴더로 공유
